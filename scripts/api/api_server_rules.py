#!/usr/bin/env python3
"""
MTG Rule Engine REST API Server
FastAPI server exposing rule engine capabilities via HTTP endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn
from contextlib import asynccontextmanager
import sys
import os
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rule_engine import MTGRuleEngine
from api.embedding_service import get_embedding_service
from api.query_parser_service import get_query_parser
from api.advanced_query_parser import get_advanced_parser


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
    """Manage database connection and embedding service lifecycle."""
    global db_conn
    print("Starting API server...")
    db_conn = psycopg2.connect(**DB_CONFIG)
    print("✓ Database connected")
    # Initialize embedding service (loads model into memory)
    print("Loading embedding model...")
    get_embedding_service()
    print("✓ Embedding service ready")
    # Initialize query parser (loads LLM into memory)
    print("Loading query parser LLM...")
    get_query_parser()
    print("✓ Query parser ready")
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


@app.get("/api/cards/keyword", tags=["Cards"])
async def keyword_search(
    query: str = Query(..., description="Keyword to search for in card names and oracle text"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip for pagination")
):
    """
    Keyword search for cards by exact or partial text match.
    Searches in card name and oracle text.

    Examples:
    - /api/cards/keyword?query=lightning&limit=10
    - /api/cards/keyword?query=flying
    - /api/cards/keyword?query=lightning&limit=10&offset=10 (pagination)
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")

    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT
                id,
                name,
                mana_cost,
                cmc,
                type_line,
                oracle_text,
                keywords
            FROM cards
            WHERE
                name ILIKE %s
                OR oracle_text ILIKE %s
            ORDER BY
                CASE
                    WHEN name ILIKE %s THEN 1
                    WHEN oracle_text ILIKE %s THEN 2
                    ELSE 3
                END,
                name
            LIMIT %s
            OFFSET %s
        """, (f'%{query}%', f'%{query}%', f'{query}%', f'{query}%', limit, offset))

        cards = cursor.fetchall()

    return {
        "query": query,
        "search_type": "keyword",
        "count": len(cards),
        "offset": offset,
        "limit": limit,
        "has_more": len(cards) == limit,
        "cards": [dict(c) for c in cards]
    }




def parse_query_with_negations(query: str) -> Tuple[str, List[str]]:
    """
    Parse query to extract positive search terms and negative exclusions.
    
    Supports patterns:
    - "not X", "no X", "without X", "exclude X"
    - "with no X", "having no X"
    - Multiple exclusions: "vampires, no landfall, without haste"
    
    Returns:
        Tuple of (positive_query, list_of_exclusions)
    
    Examples:
        "vampires with no black" -> ("vampires", ["black"])
        "not vivi" -> ("", ["vivi"])
        "not vivi but red blue wizards" -> ("red blue wizards", ["vivi"])
        "legendary planeswalker blue, no landfall" -> ("legendary planeswalker blue", ["landfall"])
    """
    exclusions = []
    
    # Patterns to detect negations (case insensitive)
    # Match single words or short phrases (up to 3 words) after negation keywords
    negation_patterns = [
        r'\b(?:with\s+)?no\s+([a-zA-Z][a-zA-Z0-9]*(?:\s+[a-zA-Z][a-zA-Z0-9]*){0,2})(?:\s+but\s+|\s*,\s*|$)',
        r'\bwithout\s+([a-zA-Z][a-zA-Z0-9]*(?:\s+[a-zA-Z][a-zA-Z0-9]*){0,2})(?:\s+but\s+|\s*,\s*|$)',
        r'\bnot\s+([a-zA-Z][a-zA-Z0-9]*(?:\s+[a-zA-Z][a-zA-Z0-9]*){0,2})(?:\s+but\s+|\s*,\s*|$)',
        r'\bexclude\s+([a-zA-Z][a-zA-Z0-9]*(?:\s+[a-zA-Z][a-zA-Z0-9]*){0,2})(?:\s+but\s+|\s*,\s*|$)',
        r'\bhaving\s+no\s+([a-zA-Z][a-zA-Z0-9]*(?:\s+[a-zA-Z][a-zA-Z0-9]*){0,2})(?:\s+but\s+|\s*,\s*|$)',
    ]
    
    # Extract all exclusions
    query_cleaned = query
    for pattern in negation_patterns:
        matches = list(re.finditer(pattern, query, re.IGNORECASE))
        for match in matches:
            exclusion = match.group(1).strip()
            if exclusion:
                exclusions.append(exclusion)
            # Remove this negation phrase from query
            query_cleaned = query_cleaned.replace(match.group(0), ' ', 1)
    
    # Clean up the positive query
    positive_query = re.sub(r'\s+', ' ', query_cleaned).strip()
    positive_query = re.sub(r',\s*,', ',', positive_query)  # Remove double commas
    positive_query = positive_query.strip(',').strip()
    
    return positive_query, exclusions


@app.get("/api/cards/semantic", tags=["Cards"])
async def semantic_search(
    query: str = Query(..., description="Natural language query for semantic search"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip for pagination")
):
    """
    Semantic search for cards using natural language queries and vector similarity.

    Uses vector embeddings to find cards semantically similar to your query.
    Works with natural language descriptions of card mechanics.

    Examples:
    - /api/cards/semantic?query=cards that deal damage to creatures
    - /api/cards/semantic?query=artifact removal
    - /api/cards/semantic?query=flying creatures
    - /api/cards/semantic?query=counterspells&limit=10&offset=10 (pagination)
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")

    # Parse query using LLM
    parser = get_query_parser()
    parsed = parser.parse_query(query)
    
    positive_query = parsed.get('positive_query', '').strip()
    exclusions = parsed.get('exclusions', [])
    
    # If no positive query left, return error
    if not positive_query and exclusions:
        raise HTTPException(
            status_code=400, 
            detail=f"Query only contains exclusions: {', '.join(exclusions)}. Please provide what to search for."
        )
    
    # If no positive query and no exclusions, return empty
    if not positive_query:
        return {
            "query": query,
            "search_type": "semantic",
            "count": 0,
            "offset": offset,
            "limit": limit,
            "has_more": False,
            "exclusions": exclusions,
            "cards": []
        }

    # Generate embedding for the positive query
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.generate_embedding(positive_query)

    # Perform vector similarity search with deduplication and exclusions
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Build exclusion conditions
        # Map color names to mana symbols
        color_to_symbol = {
            'white': 'W',
            'blue': 'U',
            'black': 'B',
            'red': 'R',
            'green': 'G'
        }

        exclusion_conditions = []
        exclusion_params = []

        for exclusion in exclusions:
            exclusion_lower = exclusion.lower()
            # Check mana_cost for color symbols if exclusion is a color
            if exclusion_lower in color_to_symbol:
                symbol = color_to_symbol[exclusion_lower]
                exclusion_conditions.append("(mana_cost NOT LIKE %s AND oracle_text NOT ILIKE %s AND name NOT ILIKE %s AND type_line NOT ILIKE %s)")
                exclusion_params.extend([f'%{{{symbol}}}%', f'%{exclusion}%', f'%{exclusion}%', f'%{exclusion}%'])
            else:
                exclusion_conditions.append("(oracle_text NOT ILIKE %s AND name NOT ILIKE %s AND type_line NOT ILIKE %s)")
                exclusion_params.extend([f'%{exclusion}%', f'%{exclusion}%', f'%{exclusion}%'])

        # Combine exclusion conditions with AND
        exclusion_sql = " AND ".join(exclusion_conditions) if exclusion_conditions else "TRUE"
        
        query_sql = f"""
            WITH ranked_cards AS (
                SELECT
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    released_at,
                    1 - (embedding <=> %s::vector) as similarity,
                    ROW_NUMBER() OVER (PARTITION BY name ORDER BY released_at DESC NULLS LAST) as rn
                FROM cards
                WHERE embedding IS NOT NULL
                  AND {exclusion_sql}
            )
            SELECT
                id,
                name,
                mana_cost,
                cmc,
                type_line,
                oracle_text,
                keywords,
                similarity
            FROM ranked_cards
            WHERE rn = 1
            ORDER BY similarity DESC
            LIMIT %s
            OFFSET %s
        """
        
        # Combine all parameters
        all_params = [query_embedding] + exclusion_params + [limit, offset]
        
        cursor.execute(query_sql, all_params)
        cards = cursor.fetchall()

    return {
        "query": query,
        "positive_query": positive_query,
        "exclusions": exclusions,
        "search_type": "semantic",
        "count": len(cards),
        "offset": offset,
        "limit": limit,
        "has_more": len(cards) == limit,
        "cards": [dict(c) for c in cards]
    }


@app.get("/api/cards/advanced", tags=["Cards"])
async def advanced_search(
    query: str = Query(..., description="Natural language query with complex filters"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip for pagination"),
    include_nonplayable: bool = Query(False, description="Include non-playable cards (tokens, schemes, banned cards)")
):
    """
    Advanced search with support for complex filters.
    
    Supports:
    - Creature types: "zombies", "dragons", "vampires"
    - Color filters: "blue", "not black", "only red"
    - CMC filters: "more than 3 mana", "cmc < 4", "2 mana or less"
    - Type filters: "creatures", "instants", "artifacts"
    - Keyword filters: "with flying", "no haste"
    - Rarity filters: "rare", "mythic"
    - Power/Toughness: "power > 4", "3/3 or bigger"
    
    Examples:
    - /api/cards/advanced?query=zombies but not black more than 3 mana
    - /api/cards/advanced?query=blue dragons cmc <= 5 with flying
    - /api/cards/advanced?query=rare creatures only red power >= 4
    - /api/cards/advanced?query=instants 2 mana or less not blue
    - /api/cards/advanced?query=vampires without lifelink cmc > 2
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")
    
    # Parse query using advanced parser
    parser = get_advanced_parser()
    parsed = parser.parse(query)
    
    # Generate embedding for semantic search if we have positive terms
    query_embedding = None
    if parsed.positive_terms:
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_embedding(parsed.positive_terms)
    
    # Build SQL query with filters
    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get SQL WHERE clause from parsed filters
        filter_where, filter_params = parser.to_sql_where_clause(parsed)
        
        # Add playability filter
        if not include_nonplayable:
            filter_where += " AND is_playable = TRUE"
        
        if query_embedding:
            # Semantic search with filters
            query_sql = f"""
                WITH ranked_cards AS (
                    SELECT
                        id,
                        name,
                        mana_cost,
                        cmc,
                        type_line,
                        oracle_text,
                        keywords,
                        colors,
                        power,
                        toughness,
                        rarity,
                        released_at,
                        1 - (embedding <=> %s::vector) as similarity,
                        ROW_NUMBER() OVER (PARTITION BY name ORDER BY released_at DESC NULLS LAST) as rn
                    FROM cards
                    WHERE embedding IS NOT NULL
                      AND ({filter_where})
                )
                SELECT
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    colors,
                    power,
                    toughness,
                    rarity,
                    similarity
                FROM ranked_cards
                WHERE rn = 1
                ORDER BY similarity DESC
                LIMIT %s
                OFFSET %s
            """
            params = [query_embedding] + filter_params + [limit, offset]
        else:
            # Filter-only search (no semantic component)
            query_sql = f"""
                SELECT DISTINCT ON (name)
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    colors,
                    power,
                    toughness,
                    rarity
                FROM cards
                WHERE {filter_where}
                ORDER BY name, released_at DESC NULLS LAST
                LIMIT %s
                OFFSET %s
            """
            params = filter_params + [limit, offset]
        
        cursor.execute(query_sql, params)
        cards = cursor.fetchall()
    
    return {
        "query": query,
        "parsed": {
            "positive_terms": parsed.positive_terms,
            "exclusions": parsed.exclusions,
            "filters": parsed.filters
        },
        "search_type": "advanced",
        "count": len(cards),
        "offset": offset,
        "limit": limit,
        "has_more": len(cards) == limit,
        "cards": [dict(c) for c in cards]
    }


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
