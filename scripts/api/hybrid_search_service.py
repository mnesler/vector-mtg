#!/usr/bin/env python3
"""
Hybrid Search Service - Combines keyword, semantic, and advanced search
Automatically routes queries to the best search method and boosts results.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from psycopg2.extras import RealDictCursor
from difflib import SequenceMatcher

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.embedding_service import get_embedding_service
from api.advanced_query_parser import get_advanced_parser


class HybridSearchService:
    """Service for intelligent hybrid search combining multiple strategies."""
    
    def __init__(self, db_conn):
        """
        Initialize hybrid search service.
        
        Args:
            db_conn: PostgreSQL database connection
        """
        self.db_conn = db_conn
        self.embedding_service = get_embedding_service()
        self.advanced_parser = get_advanced_parser()
    
    def classify_query(self, query: str) -> str:
        """
        Classify query to determine best search method.
        
        Args:
            query: Search query string
            
        Returns:
            Search method: 'keyword', 'advanced', or 'semantic'
        """
        query_lower = query.lower().strip()
        
        # Check for exact card name patterns
        # Card names are typically title-cased with specific patterns
        if self._looks_like_card_name(query):
            return 'keyword'
        
        # Check for advanced filters (CMC, colors, types, etc.)
        # Keywords: "cmc", "mana", "only", "not", "without", specific numbers
        advanced_keywords = [
            r'\bcmc\b', r'\bmana\b', r'\bonly\b', r'\bnot\b', r'\bwithout\b',
            r'\bmore than\b', r'\bless than\b', r'\bgreater than\b', r'\bfewer than\b',
            r'\brare\b', r'\bmythic\b', r'\buncommon\b', r'\bcommon\b',
            r'\bpower\b', r'\btoughness\b', r'\b\d+/\d+\b'
        ]
        
        for pattern in advanced_keywords:
            if re.search(pattern, query_lower):
                return 'advanced'
        
        # Default to semantic for natural language queries
        return 'semantic'
    
    def _looks_like_card_name(self, query: str) -> bool:
        """
        Heuristic to detect if query looks like a card name.
        
        Card names typically:
        - Start with capital letters
        - Have 1-5 words
        - May include "of", "the", "and"
        - Don't contain search operators
        
        Args:
            query: Search query string
            
        Returns:
            True if query looks like a card name
        """
        # Remove common articles and prepositions
        words = query.strip().split()
        
        # Too many words is likely a natural language query
        if len(words) > 5:
            return False
        
        # Check if most words are capitalized (typical for card names)
        capitalized_count = sum(1 for word in words if word and word[0].isupper())
        
        # At least 50% of words should be capitalized
        if len(words) > 0 and capitalized_count / len(words) >= 0.5:
            # Make sure it doesn't contain obvious search terms
            search_terms = ['with', 'has', 'having', 'that', 'which', 'deals', 'destroys']
            if not any(term in query.lower() for term in search_terms):
                return True
        
        return False
    
    def _similarity_ratio(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        threshold: float = 0.50,
        auto_boost: bool = True
    ) -> Dict[str, Any]:
        """
        Execute hybrid search with intelligent routing and boosting.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Pagination offset
            threshold: Minimum similarity threshold for semantic results
            auto_boost: Whether to boost exact/partial name matches
            
        Returns:
            Dictionary with search results and metadata
        """
        if not query or not query.strip():
            return {
                "query": query,
                "method": "none",
                "count": 0,
                "offset": offset,
                "limit": limit,
                "threshold": threshold,
                "cards": []
            }
        
        # Classify query
        method = self.classify_query(query)
        
        # Execute appropriate search
        if method == 'keyword':
            results = self._keyword_search(query, limit, offset)
        elif method == 'advanced':
            results = self._advanced_search(query, limit, offset, threshold)
        else:  # semantic
            results = self._semantic_search(query, limit, offset, threshold)
        
        # Boost exact name matches if enabled
        if auto_boost:
            results = self._boost_name_matches(query, results)
        
        # Sort by boosted similarity
        results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)
        
        return {
            "query": query,
            "method": method,
            "count": len(results),
            "offset": offset,
            "limit": limit,
            "threshold": threshold if method in ['semantic', 'advanced'] else None,
            "has_more": len(results) == limit,
            "cards": results
        }
    
    def _keyword_search(
        self,
        query: str,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """
        Execute keyword search with exact/partial text matching.
        
        Args:
            query: Search query
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of matching cards with similarity scores
        """
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Search in name and oracle text, prioritizing exact name matches
            cursor.execute("""
                SELECT DISTINCT ON (name)
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    released_at,
                    CASE
                        WHEN LOWER(name) = LOWER(%s) THEN 1.0
                        WHEN LOWER(name) LIKE LOWER(%s) THEN 0.95
                        WHEN LOWER(oracle_text) LIKE LOWER(%s) THEN 0.75
                        ELSE 0.5
                    END as similarity
                FROM cards
                WHERE
                    name ILIKE %s
                    OR oracle_text ILIKE %s
                ORDER BY name, released_at DESC NULLS LAST
                LIMIT %s
                OFFSET %s
            """, (query, f'{query}%', f'%{query}%', f'%{query}%', f'%{query}%', limit, offset))
            
            cards = cursor.fetchall()
            return [dict(c) for c in cards]
    
    def _semantic_search(
        self,
        query: str,
        limit: int,
        offset: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic search with vector similarity.
        
        Args:
            query: Search query
            limit: Maximum results
            offset: Pagination offset
            threshold: Minimum similarity score
            
        Returns:
            List of matching cards with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query)
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Vector similarity search with deduplication
            cursor.execute("""
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
                  AND similarity >= %s
                ORDER BY similarity DESC
                LIMIT %s
                OFFSET %s
            """, (query_embedding, threshold, limit * 3, offset))  # Fetch 3x for boosting
            
            cards = cursor.fetchall()
            return [dict(c) for c in cards]
    
    def _advanced_search(
        self,
        query: str,
        limit: int,
        offset: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Execute advanced search with complex filters.
        
        Args:
            query: Search query
            limit: Maximum results
            offset: Pagination offset
            threshold: Minimum similarity score for semantic component
            
        Returns:
            List of matching cards with similarity scores
        """
        # Parse query for filters
        parsed = self.advanced_parser.parse(query)
        
        # Generate embedding if we have positive terms
        query_embedding = None
        if parsed.positive_terms:
            query_embedding = self.embedding_service.generate_embedding(parsed.positive_terms)
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build SQL WHERE clause from filters
            filter_where, filter_params = self.advanced_parser.to_sql_where_clause(parsed)
            
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
                        similarity
                    FROM ranked_cards
                    WHERE rn = 1
                      AND similarity >= %s
                    ORDER BY similarity DESC
                    LIMIT %s
                    OFFSET %s
                """
                params = [query_embedding] + filter_params + [threshold, limit * 3, offset]
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
                        0.8 as similarity
                    FROM cards
                    WHERE {filter_where}
                    ORDER BY name, released_at DESC NULLS LAST
                    LIMIT %s
                    OFFSET %s
                """
                params = filter_params + [limit, offset]
            
            cursor.execute(query_sql, params)
            cards = cursor.fetchall()
            return [dict(c) for c in cards]
    
    def _boost_name_matches(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Boost cards with names matching the query.
        
        Args:
            query: Original search query
            results: List of search results
            
        Returns:
            Results with boosted similarity scores
        """
        query_lower = query.lower().strip()
        
        for card in results:
            name_lower = card['name'].lower()
            
            # Convert similarity to float (PostgreSQL returns Decimal)
            original_sim = float(card.get('similarity', 0))
            
            # Exact match - set to 1.0
            if name_lower == query_lower:
                card['similarity'] = 1.0
                card['boost_reason'] = 'exact_name_match'
            
            # Query is at start of name - boost significantly
            elif name_lower.startswith(query_lower):
                card['similarity'] = min(1.0, original_sim + 0.25)
                card['boost_reason'] = 'name_starts_with'
            
            # Query appears in name - boost moderately
            elif query_lower in name_lower:
                card['similarity'] = min(1.0, original_sim + 0.15)
                card['boost_reason'] = 'name_contains'
            
            # High similarity ratio (fuzzy match) - boost slightly
            elif self._similarity_ratio(query, card['name']) > 0.7:
                card['similarity'] = min(1.0, original_sim + 0.10)
                card['boost_reason'] = 'name_similar'
        
        return results


def get_hybrid_search_service(db_conn):
    """
    Get hybrid search service instance.
    
    Args:
        db_conn: Database connection
        
    Returns:
        HybridSearchService instance
    """
    return HybridSearchService(db_conn)
