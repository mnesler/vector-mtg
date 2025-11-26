#!/usr/bin/env python3
"""
MTG Rule Engine REST API Server
FastAPI server exposing rule engine capabilities via HTTP endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn
from contextlib import asynccontextmanager

from rule_engine import MTGRuleEngine


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


# Database connection pool
db_conn = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle."""
    global db_conn
    print("Starting API server...")
    db_conn = psycopg2.connect(**DB_CONFIG)
    print("✓ Database connected")
    yield
    print("Shutting down API server...")
    if db_conn:
        db_conn.close()
    print("✓ Database disconnected")


# Initialize FastAPI app
app = FastAPI(
    title="MTG Rule Engine API",
    description="REST API for MTG card classification and rule matching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class CardResponse(BaseModel):
    id: str
    name: str
    mana_cost: Optional[str]
    cmc: Optional[float]
    type_line: str
    oracle_text: Optional[str]
    keywords: Optional[List[str]]


class RuleResponse(BaseModel):
    id: str
    rule_name: str
    rule_template: str
    category: Optional[str]
    confidence: Optional[float]
    parameter_bindings: Optional[Dict[str, Any]]


class CardWithRulesResponse(CardResponse):
    rules: List[RuleResponse]


class SimilarCardResponse(CardResponse):
    similarity: float


class DeckAnalysisRequest(BaseModel):
    cards: List[str] = Field(..., description="List of card names")


class DeckAnalysisResponse(BaseModel):
    deck_size: int
    cards_found: int
    cards_with_rules: int
    rule_distribution: List[Dict[str, Any]]
    category_summary: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    total_rules: int
    total_mappings: int
    total_cards: int
    cards_with_rules: int
    coverage_percentage: float
    avg_rules_per_card: float
    top_rules: List[Dict[str, Any]]


# Helper function to get engine
def get_engine():
    """Get rule engine instance."""
    return MTGRuleEngine(db_conn)


# ============================================
# Card Endpoints
# ============================================

@app.get("/", tags=["Info"])
async def root():
    """API information."""
    return {
        "name": "MTG Rule Engine API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "cards": "/api/cards",
            "rules": "/api/rules",
            "stats": "/api/stats",
            "docs": "/docs"
        }
    }


@app.get("/api/cards/search", tags=["Cards"])
async def search_cards(
    name: Optional[str] = Query(None, description="Card name search (partial match, returns multiple)"),
    rule: Optional[str] = Query(None, description="Filter by rule name"),
    limit: int = Query(50, ge=1, le=500),
    include_nonplayable: bool = Query(False, description="Include non-playable cards (tokens, schemes, banned cards)")
):
    """
    Search for cards by name or rule.

    By default, only returns cards legal in Standard or Commander.
    Set include_nonplayable=true to show all cards including tokens, planes, etc.

    Examples:
    - /api/cards/search?name=Lightning&limit=20  (returns playable cards with "Lightning" in name)
    - /api/cards/search?name=Birds of Paradise  (returns playable cards matching the pattern)
    - /api/cards/search?rule=flying_keyword&limit=20
    - /api/cards/search?name=Warrior&include_nonplayable=true  (includes token creatures)
    """
    engine = get_engine()

    if name:
        # Search for multiple cards matching the name pattern
        cards = engine.search_cards_by_name(name, limit=limit, include_nonplayable=include_nonplayable)

        # For each card, get its rules
        result_cards = []
        for card in cards:
            rules = engine.get_card_rules(card['id'])
            result_cards.append({
                **dict(card),
                "rules": [dict(r) for r in rules]
            })

        return {
            "search_term": name,
            "count": len(result_cards),
            "cards": result_cards
        }

    if rule:
        cards = engine.find_cards_by_rule(rule, limit=limit, include_nonplayable=include_nonplayable)

        # Add rules to each card
        result_cards = []
        for card in cards:
            rules = engine.get_card_rules(card['id'])
            result_cards.append({
                **dict(card),
                "rules": [dict(r) for r in rules]
            })

        return {
            "rule": rule,
            "count": len(result_cards),
            "cards": result_cards
        }

    raise HTTPException(status_code=400, detail="Must provide either 'name' or 'rule' parameter")


@app.get("/api/cards/{card_id}", tags=["Cards"], response_model=CardWithRulesResponse)
async def get_card(card_id: str):
    """Get a card by ID with all its matched rules."""
    engine = get_engine()

    card = engine.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Card with ID '{card_id}' not found")

    rules = engine.get_card_rules(card_id)

    return {
        **dict(card),
        "rules": [dict(r) for r in rules]
    }


@app.get("/api/cards/{card_id}/similar", tags=["Cards"])
async def get_similar_cards(
    card_id: str,
    limit: int = Query(20, ge=1, le=100),
    rule_filter: Optional[str] = Query(None, description="Filter by rule name"),
    include_nonplayable: bool = Query(False, description="Include non-playable cards (tokens, schemes, banned cards)")
):
    """
    Find cards similar to the given card using vector embeddings.

    By default, only returns cards legal in Standard or Commander.
    """
    engine = get_engine()

    # Verify card exists
    card = engine.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Card with ID '{card_id}' not found")

    similar = engine.find_similar_cards(
        card_id,
        limit=limit,
        rule_filter=rule_filter,
        include_nonplayable=include_nonplayable
    )

    return {
        "card_id": card_id,
        "card_name": card['name'],
        "rule_filter": rule_filter,
        "count": len(similar),
        "similar_cards": [dict(c) for c in similar]
    }


# ============================================
# Rule Endpoints
# ============================================

@app.get("/api/rules", tags=["Rules"])
async def list_rules(
    category: Optional[str] = Query(None, description="Filter by category name"),
    limit: int = Query(100, ge=1, le=500)
):
    """List all rules, optionally filtered by category."""
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        query = """
            SELECT
                r.id,
                r.rule_name,
                r.rule_template,
                r.rule_pattern,
                rc.name as category,
                COUNT(cr.card_id) as card_count
            FROM rules r
            LEFT JOIN rule_categories rc ON r.category_id = rc.id
            LEFT JOIN card_rules cr ON r.id = cr.rule_id
        """
        params = []

        if category:
            query += " WHERE rc.name = %s"
            params.append(category)

        query += """
            GROUP BY r.id, r.rule_name, r.rule_template, r.rule_pattern, rc.name
            ORDER BY card_count DESC
            LIMIT %s
        """
        params.append(limit)

        cursor.execute(query, tuple(params))
        rules = cursor.fetchall()

        return {
            "category_filter": category,
            "count": len(rules),
            "rules": [dict(r) for r in rules]
        }


@app.get("/api/rules/{rule_name}/cards", tags=["Rules"])
async def get_cards_for_rule(
    rule_name: str,
    limit: int = Query(50, ge=1, le=500),
    include_nonplayable: bool = Query(False, description="Include non-playable cards (tokens, schemes, banned cards)")
):
    """
    Get all cards that match a specific rule.

    By default, only returns cards legal in Standard or Commander.
    """
    engine = get_engine()

    cards = engine.find_cards_by_rule(rule_name, limit=limit, include_nonplayable=include_nonplayable)

    if not cards:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found or has no matching cards")

    return {
        "rule_name": rule_name,
        "count": len(cards),
        "cards": [dict(c) for c in cards]
    }


@app.get("/api/categories", tags=["Rules"])
async def list_categories():
    """List all rule categories with card counts."""
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                rc.id,
                rc.name,
                rc.description,
                COUNT(DISTINCT cr.card_id) as card_count,
                COUNT(DISTINCT r.id) as rule_count
            FROM rule_categories rc
            LEFT JOIN rules r ON rc.id = r.category_id
            LEFT JOIN card_rules cr ON r.id = cr.rule_id
            GROUP BY rc.id, rc.name, rc.description
            ORDER BY card_count DESC
        """)
        categories = cursor.fetchall()

        return {
            "count": len(categories),
            "categories": [dict(c) for c in categories]
        }


# ============================================
# Analysis Endpoints
# ============================================

@app.post("/api/analyze/deck", tags=["Analysis"], response_model=DeckAnalysisResponse)
async def analyze_deck(request: DeckAnalysisRequest):
    """
    Analyze a deck's rule composition.

    Provide a list of card names and get back rule distribution,
    category analysis, and suggestions.
    """
    engine = get_engine()

    analysis = engine.analyze_deck(request.cards)

    if 'error' in analysis:
        raise HTTPException(status_code=404, detail=analysis['error'])

    return analysis


@app.get("/api/stats", tags=["Analysis"], response_model=StatsResponse)
async def get_statistics():
    """Get overall rule engine statistics."""
    engine = get_engine()

    stats = engine.get_rule_statistics()

    return stats


@app.get("/api/stats/rules", tags=["Analysis"])
async def get_rule_statistics():
    """Get detailed statistics about each rule."""
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                r.rule_name,
                rc.name as category,
                COUNT(cr.card_id) as card_count,
                ROUND(AVG(cr.confidence)::numeric, 3) as avg_confidence,
                MIN(cr.confidence) as min_confidence,
                MAX(cr.confidence) as max_confidence
            FROM rules r
            LEFT JOIN rule_categories rc ON r.category_id = rc.id
            LEFT JOIN card_rules cr ON r.id = cr.rule_id
            GROUP BY r.id, r.rule_name, rc.name
            HAVING COUNT(cr.card_id) > 0
            ORDER BY card_count DESC
        """)
        rule_stats = cursor.fetchall()

        return {
            "count": len(rule_stats),
            "rules": [dict(r) for r in rule_stats]
        }


# ============================================
# Health Check
# ============================================

@app.get("/health", tags=["Info"])
async def health_check():
    """Health check endpoint."""
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================
# Main Entry Point
# ============================================

def main():
    """Run the API server."""
    print("=" * 60)
    print("MTG Rule Engine API Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == '__main__':
    main()
