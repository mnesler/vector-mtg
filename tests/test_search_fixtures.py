#!/usr/bin/env python3
"""
Test fixtures for search functionality.
Provides known queries with expected results for consistent testing.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from api.embedding_service import get_embedding_service


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


# Test fixtures with expected behavior
KEYWORD_SEARCH_FIXTURES = [
    {
        "query": "Lightning Bolt",
        "description": "Exact card name match",
        "expected_top_result": "Lightning Bolt",
        "min_results": 1
    },
    {
        "query": "flying",
        "description": "Common keyword ability",
        "expected_contains": ["flying", "Flying"],
        "min_results": 10
    },
    {
        "query": "destroy target creature",
        "description": "Common removal text",
        "expected_contains": ["destroy", "target", "creature"],
        "min_results": 10
    },
    {
        "query": "draw a card",
        "description": "Card draw effect",
        "expected_contains": ["draw"],
        "min_results": 10
    }
]


SEMANTIC_SEARCH_FIXTURES = [
    {
        "query": "red direct damage spells",
        "description": "Natural language query for red burn",
        "expected_colors": ["R"],
        "expected_types": ["Instant", "Sorcery"],
        "example_expected_cards": ["Lightning Bolt", "Shock", "Bolt", "Lava Spike"],
        "min_results": 5
    },
    {
        "query": "cards that remove creatures",
        "description": "Natural language for removal",
        "expected_text_contains": ["destroy", "exile", "damage"],
        "example_expected_cards": ["Murder", "Doom Blade", "Path to Exile"],
        "min_results": 5
    },
    {
        "query": "evasive flying creatures",
        "description": "Creatures with flying",
        "expected_keywords": ["flying"],
        "expected_types": ["Creature"],
        "min_results": 5
    },
    {
        "query": "counterspells",
        "description": "Counter magic",
        "expected_text_contains": ["counter", "spell"],
        "expected_colors": ["U"],
        "example_expected_cards": ["Counterspell", "Cancel", "Negate"],
        "min_results": 5
    },
    {
        "query": "mana ramp",
        "description": "Mana acceleration",
        "expected_text_contains": ["land", "mana", "search"],
        "example_expected_cards": ["Rampant Growth", "Cultivate", "Kodama's Reach"],
        "min_results": 5
    }
]


def run_keyword_search(query: str, limit: int = 10):
    """Run a keyword search query and return results."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    colors
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
            """, (f'%{query}%', f'%{query}%', f'{query}%', f'{query}%', limit))

            return cursor.fetchall()
    finally:
        conn.close()


def run_semantic_search(query: str, limit: int = 10):
    """Run a semantic search query and return results."""
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.generate_embedding(query)

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    colors,
                    1 - (embedding <=> %s::vector) as similarity
                FROM cards
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, limit))

            return cursor.fetchall()
    finally:
        conn.close()


def print_search_results(results, search_type: str, query: str):
    """Pretty print search results."""
    print(f"\n{'='*80}")
    print(f"{search_type.upper()} SEARCH: '{query}'")
    print(f"{'='*80}")
    print(f"Found {len(results)} results\n")

    for i, card in enumerate(results, 1):
        print(f"{i}. {card['name']}")
        if card.get('mana_cost'):
            print(f"   Mana Cost: {card['mana_cost']}")
        print(f"   Type: {card['type_line']}")
        if card.get('oracle_text'):
            oracle = card['oracle_text'][:100]
            if len(card['oracle_text']) > 100:
                oracle += "..."
            print(f"   Text: {oracle}")
        if card.get('similarity'):
            print(f"   Similarity: {card['similarity']:.3f}")
        if card.get('keywords'):
            print(f"   Keywords: {', '.join(card['keywords'])}")
        print()


def run_all_keyword_fixtures():
    """Run all keyword search fixtures and display results."""
    print("\n" + "="*80)
    print("KEYWORD SEARCH FIXTURES")
    print("="*80)

    for fixture in KEYWORD_SEARCH_FIXTURES:
        results = run_keyword_search(fixture['query'])
        print_search_results(results, "keyword", fixture['query'])

        # Validate expectations
        if len(results) < fixture.get('min_results', 0):
            print(f"⚠️  WARNING: Expected at least {fixture['min_results']} results, got {len(results)}")


def run_all_semantic_fixtures():
    """Run all semantic search fixtures and display results."""
    print("\n" + "="*80)
    print("SEMANTIC SEARCH FIXTURES")
    print("="*80)

    for fixture in SEMANTIC_SEARCH_FIXTURES:
        results = run_semantic_search(fixture['query'])
        print_search_results(results, "semantic", fixture['query'])

        # Validate expectations
        if len(results) < fixture.get('min_results', 0):
            print(f"⚠️  WARNING: Expected at least {fixture['min_results']} results, got {len(results)}")

        # Check if expected cards are in top results
        if 'example_expected_cards' in fixture:
            result_names = [r['name'].lower() for r in results[:10]]
            found_expected = [card for card in fixture['example_expected_cards']
                            if card.lower() in ' '.join(result_names)]
            if found_expected:
                print(f"✓ Found expected cards: {', '.join(found_expected)}")
            else:
                print(f"⚠️  None of the expected cards found in top 10: {fixture['example_expected_cards']}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run search test fixtures')
    parser.add_argument('--keyword', action='store_true', help='Run keyword search fixtures')
    parser.add_argument('--semantic', action='store_true', help='Run semantic search fixtures')
    parser.add_argument('--all', action='store_true', help='Run all fixtures')
    parser.add_argument('--query', type=str, help='Run a custom query')
    parser.add_argument('--type', choices=['keyword', 'semantic'], default='semantic',
                       help='Type of search for custom query')

    args = parser.parse_args()

    if args.query:
        # Run custom query
        if args.type == 'keyword':
            results = run_keyword_search(args.query)
            print_search_results(results, "keyword", args.query)
        else:
            results = run_semantic_search(args.query)
            print_search_results(results, "semantic", args.query)
    elif args.all or (not args.keyword and not args.semantic):
        # Run all by default
        run_all_keyword_fixtures()
        run_all_semantic_fixtures()
    else:
        if args.keyword:
            run_all_keyword_fixtures()
        if args.semantic:
            run_all_semantic_fixtures()
