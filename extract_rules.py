#!/usr/bin/env python3
"""
Extract and match MTG rules to cards using both regex patterns and vector similarity.
Populates the card_rules junction table with matches and confidence scores.
"""

import psycopg2
from psycopg2.extras import execute_batch
import re
from typing import List, Dict, Tuple, Optional
from tqdm import tqdm
import sys
import json

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

BATCH_SIZE = 500
VECTOR_SIMILARITY_THRESHOLD = 0.6  # Minimum similarity to consider a match (0-1)
TOP_K_SIMILAR = 10  # Number of similar rules to consider per card


class RuleExtractor:
    """Handles extraction and matching of rules to cards."""

    def __init__(self, cursor, conn):
        self.cursor = cursor
        self.conn = conn
        self.rules_cache = []
        self.stats = {
            'total_cards': 0,
            'cards_with_matches': 0,
            'total_matches': 0,
            'regex_matches': 0,
            'vector_matches': 0,
        }

    def load_rules(self):
        """Load all rules from database into memory."""
        print("Loading rules from database...")

        self.cursor.execute("""
            SELECT id, rule_name, rule_template, rule_pattern, parameters
            FROM rules
            ORDER BY rule_name
        """)

        self.rules_cache = self.cursor.fetchall()
        print(f"✓ Loaded {len(self.rules_cache):,} rules")

    def extract_parameters_from_text(self, oracle_text: str, rule_pattern: str,
                                     parameters: Dict) -> Optional[Dict]:
        """
        Extract parameter values from oracle text using regex pattern.
        Returns dict of parameter names to values.
        """
        if not rule_pattern or not oracle_text:
            return None

        try:
            # Look for pattern in oracle text (case-insensitive)
            match = re.search(rule_pattern, oracle_text, re.IGNORECASE)
            if not match:
                return None

            # Extract named groups from regex
            extracted = match.groupdict()

            # Simple extraction for common patterns
            param_values = {}

            # Extract numbers (damage, card count, etc.)
            number_match = re.search(r'(\d+)', match.group(0))
            if number_match and parameters:
                # Try to infer parameter type from schema
                for param_name, param_type in parameters.items():
                    if param_type in ['number', 'integer']:
                        param_values[param_name] = int(number_match.group(1))

            # Extract target types (creature, artifact, etc.)
            if 'target' in oracle_text.lower():
                target_match = re.search(r'target\s+(\w+)', oracle_text, re.IGNORECASE)
                if target_match:
                    param_values['target_type'] = target_match.group(1)

            return param_values if param_values else None

        except re.error:
            return None

    def find_regex_matches(self, card_id: str, oracle_text: str) -> List[Tuple]:
        """Find rule matches using regex patterns."""
        matches = []

        if not oracle_text:
            return matches

        for rule_id, rule_name, rule_template, rule_pattern, parameters in self.rules_cache:
            if not rule_pattern:
                continue

            try:
                # Check if pattern matches
                if re.search(rule_pattern, oracle_text, re.IGNORECASE):
                    # Extract parameter values
                    param_values = self.extract_parameters_from_text(
                        oracle_text, rule_pattern, parameters or {}
                    )

                    matches.append({
                        'card_id': card_id,
                        'rule_id': rule_id,
                        'confidence': 0.95,  # High confidence for regex matches
                        'parameter_bindings': param_values or {},
                        'extraction_method': 'regex'
                    })

            except re.error:
                # Skip invalid regex patterns
                continue

        return matches

    def find_vector_matches(self, card_id: str, batch_card_ids: List[str]) -> List[Tuple]:
        """Find rule matches using vector similarity (batch processing)."""
        matches = []

        # Check if embeddings exist
        self.cursor.execute("SELECT COUNT(*) FROM rules WHERE embedding IS NOT NULL")
        if self.cursor.fetchone()[0] == 0:
            return matches

        # Use vector similarity to find top K similar rules for each card
        # This is more efficient than checking all cards individually
        self.cursor.execute(f"""
            WITH card_embeddings AS (
                SELECT id, oracle_embedding
                FROM cards
                WHERE id = ANY(%s::uuid[])
                AND oracle_embedding IS NOT NULL
            )
            SELECT
                ce.id as card_id,
                r.id as rule_id,
                1 - (r.embedding <=> ce.oracle_embedding) as similarity
            FROM card_embeddings ce
            CROSS JOIN LATERAL (
                SELECT id, embedding
                FROM rules
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> ce.oracle_embedding
                LIMIT {TOP_K_SIMILAR}
            ) r
            WHERE 1 - (r.embedding <=> ce.oracle_embedding) >= %s
        """, (batch_card_ids, VECTOR_SIMILARITY_THRESHOLD))

        results = self.cursor.fetchall()

        for card_id_result, rule_id, similarity in results:
            if card_id_result == card_id:  # Only return matches for current card
                matches.append({
                    'card_id': card_id,
                    'rule_id': rule_id,
                    'confidence': float(similarity),
                    'parameter_bindings': {},
                    'extraction_method': 'vector_similarity'
                })

        return matches

    def merge_matches(self, regex_matches: List[Dict], vector_matches: List[Dict]) -> List[Dict]:
        """Merge regex and vector matches, preferring regex when both exist."""
        # Create a dict keyed by (card_id, rule_id)
        merged = {}

        # Add regex matches first (higher confidence)
        for match in regex_matches:
            key = (match['card_id'], match['rule_id'])
            merged[key] = match

        # Add vector matches only if not already matched by regex
        for match in vector_matches:
            key = (match['card_id'], match['rule_id'])
            if key not in merged:
                merged[key] = match

        return list(merged.values())

    def store_matches(self, matches: List[Dict]):
        """Store rule matches in database."""
        if not matches:
            return

        # Prepare data for batch insert
        values = [
            (
                m['card_id'],
                m['rule_id'],
                m['confidence'],
                json.dumps(m['parameter_bindings']),
                m['extraction_method']
            )
            for m in matches
        ]

        # Insert with conflict handling
        execute_batch(self.cursor, """
            INSERT INTO card_rules (card_id, rule_id, confidence, parameter_bindings, extraction_method)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (card_id, rule_id) DO UPDATE SET
                confidence = EXCLUDED.confidence,
                parameter_bindings = EXCLUDED.parameter_bindings,
                extraction_method = EXCLUDED.extraction_method,
                extracted_at = NOW()
        """, values)

    def process_cards(self):
        """Process all cards and extract rule matches."""
        print("\n" + "=" * 60)
        print("Extracting Rule Matches")
        print("=" * 60)

        # Get total count
        self.cursor.execute("SELECT COUNT(*) FROM cards WHERE oracle_text IS NOT NULL")
        total_cards = self.cursor.fetchone()[0]
        self.stats['total_cards'] = total_cards

        print(f"Processing {total_cards:,} cards...")

        # Fetch cards in batches
        self.cursor.execute("""
            SELECT id, oracle_text
            FROM cards
            WHERE oracle_text IS NOT NULL
            ORDER BY id
        """)

        batch = []
        all_matches = []

        for card_id, oracle_text in tqdm(self.cursor.fetchall(), desc="Matching rules"):
            batch.append((card_id, oracle_text))

            # Process batch
            if len(batch) >= BATCH_SIZE:
                matches = self.process_batch(batch)
                all_matches.extend(matches)

                # Store matches
                if all_matches:
                    self.store_matches(all_matches)
                    self.conn.commit()
                    all_matches = []

                batch = []

        # Process remaining cards
        if batch:
            matches = self.process_batch(batch)
            all_matches.extend(matches)

        # Store final matches
        if all_matches:
            self.store_matches(all_matches)
            self.conn.commit()

    def process_batch(self, batch: List[Tuple]) -> List[Dict]:
        """Process a batch of cards."""
        all_matches = []
        batch_card_ids = [card_id for card_id, _ in batch]

        for card_id, oracle_text in batch:
            # Find matches using regex
            regex_matches = self.find_regex_matches(card_id, oracle_text)

            # Find matches using vector similarity (batch optimized)
            vector_matches = self.find_vector_matches(card_id, batch_card_ids)

            # Merge and deduplicate
            merged = self.merge_matches(regex_matches, vector_matches)

            # Update stats
            if merged:
                self.stats['cards_with_matches'] += 1
                self.stats['total_matches'] += len(merged)

                for m in merged:
                    if m['extraction_method'] == 'regex':
                        self.stats['regex_matches'] += 1
                    else:
                        self.stats['vector_matches'] += 1

            all_matches.extend(merged)

        return all_matches

    def show_statistics(self):
        """Display extraction statistics."""
        print("\n" + "=" * 60)
        print("Extraction Statistics")
        print("=" * 60)

        print(f"Total cards processed: {self.stats['total_cards']:,}")
        print(f"Cards with rule matches: {self.stats['cards_with_matches']:,} "
              f"({100*self.stats['cards_with_matches']/max(self.stats['total_cards'],1):.1f}%)")
        print(f"Total rule matches: {self.stats['total_matches']:,}")
        print(f"  - Regex matches: {self.stats['regex_matches']:,}")
        print(f"  - Vector matches: {self.stats['vector_matches']:,}")

        # Get top rules
        self.cursor.execute("""
            SELECT r.rule_name, COUNT(*) as match_count
            FROM card_rules cr
            JOIN rules r ON cr.rule_id = r.id
            GROUP BY r.rule_name
            ORDER BY match_count DESC
            LIMIT 10
        """)

        print("\nTop 10 most matched rules:")
        for rule_name, count in self.cursor.fetchall():
            print(f"  {rule_name}: {count:,} cards")

        print("=" * 60)

    def show_examples(self):
        """Show example card-rule matches."""
        print("\n" + "=" * 60)
        print("Example Matches")
        print("=" * 60)

        # Get a few example cards with multiple rules
        self.cursor.execute("""
            SELECT
                c.name,
                c.oracle_text,
                r.rule_name,
                cr.confidence,
                cr.extraction_method
            FROM cards c
            JOIN card_rules cr ON c.id = cr.card_id
            JOIN rules r ON cr.rule_id = r.id
            WHERE c.oracle_text IS NOT NULL
            ORDER BY c.name, cr.confidence DESC
            LIMIT 15
        """)

        current_card = None
        for name, oracle_text, rule_name, confidence, method in self.cursor.fetchall():
            if name != current_card:
                print(f"\n{name}")
                if oracle_text:
                    print(f"  Text: {oracle_text[:100]}...")
                current_card = name

            print(f"    → {rule_name} ({confidence:.2f}, {method})")

        print("\n" + "=" * 60)


def clear_existing_matches(cursor, conn):
    """Clear existing card_rules to allow re-extraction."""
    print("Clearing existing rule matches...")
    cursor.execute("DELETE FROM card_rules")
    conn.commit()
    print("✓ Cleared")


def main():
    """Main execution flow."""
    print("=" * 60)
    print("MTG Rule Extractor")
    print("=" * 60)

    try:
        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")

        # Clear existing matches
        clear_existing_matches(cursor, conn)

        # Initialize extractor
        extractor = RuleExtractor(cursor, conn)

        # Load rules
        extractor.load_rules()

        # Process cards
        extractor.process_cards()

        # Show statistics
        extractor.show_statistics()

        # Show examples
        extractor.show_examples()

        print("\n✓ Rule extraction complete!")
        print("\nYou can now query cards by rules in pgAdmin:")
        print("  SELECT * FROM cards_with_rules WHERE rule_names @> ARRAY['targeted_creature_destruction'];")

        # Cleanup
        cursor.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection error: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker-compose up -d")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
