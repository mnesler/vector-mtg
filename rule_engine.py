#!/usr/bin/env python3
"""
MTG Rule Engine - Card classification and rule matching system.
Uses vector embeddings and extracted rules to understand card mechanics.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional, Tuple
import sys


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


class MTGRuleEngine:
    """
    Rule engine for evaluating MTG card mechanics and interactions.
    """

    def __init__(self, conn):
        self.conn = conn
        self.rule_cache = {}
        self.keyword_cache = {}

    def get_card(self, card_id: str) -> Optional[Dict]:
        """Fetch a card by ID."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, name, mana_cost, cmc, type_line, oracle_text,
                       keywords, embedding, oracle_embedding
                FROM cards
                WHERE id = %s
            """, (card_id,))
            return cursor.fetchone()

    def get_card_by_name(self, name: str) -> Optional[Dict]:
        """Fetch a card by name (supports partial/fuzzy matching)."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Try exact match first
            cursor.execute("""
                SELECT id, name, mana_cost, cmc, type_line, oracle_text,
                       keywords, embedding, oracle_embedding
                FROM cards
                WHERE name = %s
                LIMIT 1
            """, (name,))
            result = cursor.fetchone()

            # If no exact match, try case-insensitive exact
            if not result:
                cursor.execute("""
                    SELECT id, name, mana_cost, cmc, type_line, oracle_text,
                           keywords, embedding, oracle_embedding
                    FROM cards
                    WHERE LOWER(name) = LOWER(%s)
                    LIMIT 1
                """, (name,))
                result = cursor.fetchone()

            # If still no match, tokenize and search for words
            if not result:
                # Split search into words and create pattern for each word
                words = [w.strip() for w in name.split() if w.strip()]
                if words:
                    # Build WHERE clause with ILIKE for each word
                    where_conditions = " AND ".join([f"name ILIKE %s" for _ in words])
                    word_patterns = [f'%{word}%' for word in words]

                    cursor.execute(f"""
                        SELECT id, name, mana_cost, cmc, type_line, oracle_text,
                               keywords, embedding, oracle_embedding
                        FROM cards
                        WHERE {where_conditions}
                        ORDER BY
                            CASE
                                WHEN name ILIKE %s THEN 1  -- Starts with full search term
                                ELSE 2                      -- Contains all words
                            END,
                            LENGTH(name),  -- Prefer shorter names
                            name
                        LIMIT 1
                    """, (*word_patterns, f'{name}%'))
                    result = cursor.fetchone()

            return result

    def search_cards_by_name(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search for multiple cards by name pattern.
        Returns all cards matching the search term (deduplicated by name, most recent).
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Tokenize search term
            words = [w.strip() for w in search_term.split() if w.strip()]

            if not words:
                return []

            # Build WHERE clause with ILIKE for each word
            where_conditions = " AND ".join([f"name ILIKE %s" for _ in words])
            word_patterns = [f'%{word}%' for word in words]

            cursor.execute(f"""
                SELECT DISTINCT ON (name)
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    set_code,
                    released_at,
                    keywords,
                    data->'image_uris'->>'small' as image_small,
                    data->'image_uris'->>'normal' as image_normal,
                    data->'image_uris'->>'large' as image_large
                FROM cards
                WHERE {where_conditions}
                ORDER BY name, released_at DESC NULLS LAST
                LIMIT %s
            """, (*word_patterns, limit))
            return cursor.fetchall()

    def get_card_rules(self, card_id: str) -> List[Dict]:
        """Get all rules associated with a card."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    r.id,
                    r.rule_name,
                    r.rule_template,
                    r.category_id,
                    rc.name as category_name,
                    cr.confidence,
                    cr.parameter_bindings
                FROM card_rules cr
                JOIN rules r ON cr.rule_id = r.id
                LEFT JOIN rule_categories rc ON r.category_id = rc.id
                WHERE cr.card_id = %s
                ORDER BY cr.confidence DESC
            """, (card_id,))
            return cursor.fetchall()

    def find_cards_by_rule(self, rule_name: str, limit: int = 50) -> List[Dict]:
        """
        Find all cards that match a specific rule.
        Returns only one printing per unique card name (most recent).

        Example:
            find_cards_by_rule('flying_keyword')
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT DISTINCT ON (c.name)
                    c.id,
                    c.name,
                    c.mana_cost,
                    c.cmc,
                    c.type_line,
                    c.oracle_text,
                    c.set_code,
                    c.released_at,
                    c.data->'image_uris'->>'small' as image_small,
                    c.data->'image_uris'->>'normal' as image_normal,
                    c.data->'image_uris'->>'large' as image_large,
                    cr.confidence,
                    cr.parameter_bindings
                FROM cards c
                JOIN card_rules cr ON c.id = cr.card_id
                JOIN rules r ON cr.rule_id = r.id
                WHERE r.rule_name = %s
                ORDER BY c.name, c.released_at DESC NULLS LAST, cr.confidence DESC
                LIMIT %s
            """, (rule_name, limit))
            return cursor.fetchall()

    def find_similar_cards(self, card_id: str, limit: int = 20,
                          rule_filter: Optional[str] = None) -> List[Dict]:
        """
        Find cards similar to the given card using vector embeddings.
        Returns only one printing per unique card name (most recent).
        Optionally filter by a specific rule.
        """
        card = self.get_card(card_id)
        if not card or not card['embedding']:
            return []

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Use subquery to get most recent printing per card name
            query = """
                WITH unique_cards AS (
                    SELECT DISTINCT ON (c.name)
                        c.id,
                        c.name,
                        c.mana_cost,
                        c.cmc,
                        c.type_line,
                        c.oracle_text,
                        c.embedding
                    FROM cards c
                    WHERE c.id != %s
                      AND c.embedding IS NOT NULL
            """
            params = [card_id]

            if rule_filter:
                query += """
                        AND EXISTS (
                            SELECT 1
                            FROM card_rules cr
                            JOIN rules r ON cr.rule_id = r.id
                            WHERE cr.card_id = c.id
                              AND r.rule_name = %s
                        )
                """
                params.append(rule_filter)

            query += """
                    ORDER BY c.name, c.released_at DESC NULLS LAST
                )
                SELECT
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    1 - (embedding <=> %s::vector) as similarity
                FROM unique_cards
                ORDER BY similarity DESC
                LIMIT %s
            """
            params.extend([card['embedding'], limit])

            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def analyze_deck(self, card_names: List[str]) -> Dict:
        """
        Analyze a deck's rule composition.

        Args:
            card_names: List of card names in the deck

        Returns:
            Dictionary with rule distribution and analysis
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get card IDs
            cursor.execute("""
                SELECT DISTINCT ON (name) id, name
                FROM cards
                WHERE name = ANY(%s)
            """, (card_names,))
            cards = cursor.fetchall()
            card_ids = [c['id'] for c in cards]

            if not card_ids:
                return {'error': 'No cards found'}

            # Get rule distribution
            cursor.execute("""
                SELECT
                    r.rule_name,
                    rc.name as category,
                    COUNT(*) as card_count,
                    ROUND(AVG(cr.confidence)::numeric, 3) as avg_confidence,
                    array_agg(DISTINCT c.name) as cards
                FROM card_rules cr
                JOIN rules r ON cr.rule_id = r.id
                LEFT JOIN rule_categories rc ON r.category_id = rc.id
                JOIN cards c ON cr.card_id = c.id
                WHERE cr.card_id = ANY(%s::uuid[])
                GROUP BY r.rule_name, rc.name
                ORDER BY card_count DESC
            """, (card_ids,))
            rule_distribution = cursor.fetchall()

            # Get category summary
            cursor.execute("""
                SELECT
                    rc.name as category,
                    COUNT(DISTINCT cr.card_id) as unique_cards,
                    COUNT(*) as total_matches
                FROM card_rules cr
                JOIN rules r ON cr.rule_id = r.id
                LEFT JOIN rule_categories rc ON r.category_id = rc.id
                WHERE cr.card_id = ANY(%s::uuid[])
                GROUP BY rc.name
                ORDER BY unique_cards DESC
            """, (card_ids,))
            category_summary = cursor.fetchall()

            return {
                'deck_size': len(card_names),
                'cards_found': len(cards),
                'cards_with_rules': len([c for c in cards if c['id'] in card_ids]),
                'rule_distribution': rule_distribution,
                'category_summary': category_summary
            }

    def get_rule_statistics(self) -> Dict:
        """Get overall statistics about rules and card coverage."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Total rules
            cursor.execute("SELECT COUNT(*) as total FROM rules")
            total_rules = cursor.fetchone()['total']

            # Total card-rule mappings
            cursor.execute("SELECT COUNT(*) as total FROM card_rules")
            total_mappings = cursor.fetchone()['total']

            # Cards with rules
            cursor.execute("SELECT COUNT(DISTINCT card_id) as total FROM card_rules")
            cards_with_rules = cursor.fetchone()['total']

            # Total cards
            cursor.execute("SELECT COUNT(*) as total FROM cards")
            total_cards = cursor.fetchone()['total']

            # Average rules per card
            cursor.execute("""
                SELECT ROUND(AVG(rule_count)::numeric, 2) as avg_rules
                FROM (
                    SELECT card_id, COUNT(*) as rule_count
                    FROM card_rules
                    GROUP BY card_id
                ) subq
            """)
            avg_rules_per_card = cursor.fetchone()['avg_rules']

            # Top 10 rules
            cursor.execute("""
                SELECT
                    r.rule_name,
                    rc.name as category,
                    COUNT(*) as card_count
                FROM card_rules cr
                JOIN rules r ON cr.rule_id = r.id
                LEFT JOIN rule_categories rc ON r.category_id = rc.id
                GROUP BY r.rule_name, rc.name
                ORDER BY card_count DESC
                LIMIT 10
            """)
            top_rules = cursor.fetchall()

            return {
                'total_rules': total_rules,
                'total_mappings': total_mappings,
                'total_cards': total_cards,
                'cards_with_rules': cards_with_rules,
                'coverage_percentage': round(100 * cards_with_rules / total_cards, 2),
                'avg_rules_per_card': float(avg_rules_per_card) if avg_rules_per_card else 0,
                'top_rules': top_rules
            }


def demo_rule_engine():
    """Demonstrate rule engine capabilities."""
    print("=" * 60)
    print("MTG Rule Engine Demo")
    print("=" * 60)

    # Connect to database
    print("\nConnecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    engine = MTGRuleEngine(conn)
    print("✓ Connected")

    # Get statistics
    print("\n" + "=" * 60)
    print("Rule Engine Statistics")
    print("=" * 60)
    stats = engine.get_rule_statistics()
    print(f"Total rules: {stats['total_rules']:,}")
    print(f"Total card-rule mappings: {stats['total_mappings']:,}")
    print(f"Cards with rules: {stats['cards_with_rules']:,} / {stats['total_cards']:,} ({stats['coverage_percentage']}%)")
    print(f"Average rules per card: {stats['avg_rules_per_card']}")

    print("\nTop 10 Rules:")
    for rule in stats['top_rules']:
        category = rule['category'] or 'Uncategorized'
        print(f"  {rule['rule_name']:35} {category:20} {rule['card_count']:6,} cards")

    # Example 1: Find a specific card and show its rules
    print("\n" + "=" * 60)
    print("Example 1: Card Classification")
    print("=" * 60)

    card = engine.get_card_by_name("Lightning Bolt")
    if card:
        print(f"\nCard: {card['name']}")
        print(f"Type: {card['type_line']}")
        print(f"Oracle Text: {card['oracle_text']}")

        rules = engine.get_card_rules(card['id'])
        print(f"\nMatched Rules ({len(rules)}):")
        for rule in rules:
            category = rule['category_name'] or 'Uncategorized'
            print(f"  • {rule['rule_name']:35} ({category}) - {rule['confidence']:.3f}")

    # Example 2: Find cards by rule
    print("\n" + "=" * 60)
    print("Example 2: Find Cards by Rule")
    print("=" * 60)
    print("\nFinding cards with 'flying_keyword'...")

    flying_cards = engine.find_cards_by_rule('flying_keyword', limit=10)
    print(f"\nFound {len(flying_cards)} cards (showing first 10):")
    for card in flying_cards[:10]:
        print(f"  {card['name']:30} {card['mana_cost'] or '':10} {card['type_line']}")

    # Example 3: Find similar cards
    print("\n" + "=" * 60)
    print("Example 3: Similar Cards")
    print("=" * 60)

    if card:
        print(f"\nFinding cards similar to '{card['name']}'...")
        similar = engine.find_similar_cards(card['id'], limit=5)
        print(f"\nTop 5 similar cards:")
        for sim_card in similar:
            print(f"  {sim_card['name']:30} (similarity: {sim_card['similarity']:.3f})")
            print(f"    {sim_card['oracle_text'][:80]}...")

    # Example 4: Analyze a sample deck
    print("\n" + "=" * 60)
    print("Example 4: Deck Analysis")
    print("=" * 60)

    sample_deck = [
        "Lightning Bolt",
        "Counterspell",
        "Swords to Plowshares",
        "Brainstorm",
        "Dark Ritual",
        "Sol Ring",
        "Mana Crypt",
        "Birds of Paradise"
    ]

    print(f"\nAnalyzing sample deck ({len(sample_deck)} cards):")
    for card_name in sample_deck:
        print(f"  - {card_name}")

    analysis = engine.analyze_deck(sample_deck)

    print(f"\n✓ Found {analysis['cards_found']}/{analysis['deck_size']} cards")
    print(f"\nCategory Distribution:")
    for cat in analysis['category_summary'][:10]:
        category = cat['category'] or 'Uncategorized'
        print(f"  {category:25} {cat['unique_cards']:2} cards, {cat['total_matches']:3} matches")

    print(f"\nTop Rules in Deck:")
    for rule in analysis['rule_distribution'][:10]:
        category = rule['category'] or 'Uncategorized'
        print(f"  {rule['rule_name']:30} ({category}) - {rule['card_count']} cards")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

    conn.close()


def main():
    """Main entry point."""
    try:
        demo_rule_engine()
    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection error: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker compose up -d")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
