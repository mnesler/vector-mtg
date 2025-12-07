#!/usr/bin/env python3
"""
Enhanced MTG card loader with keyword extraction.
Loads cards from cards.json into PostgreSQL with extracted keywords.
"""

import ijson
import json
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from decimal import Decimal
import sys
import re

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

BATCH_SIZE = 1000
CARDS_FILE = 'cards.json'

# MTG Keyword Lists
EVERGREEN_KEYWORDS = [
    'flying', 'first strike', 'double strike', 'deathtouch',
    'defender', 'haste', 'hexproof', 'indestructible',
    'lifelink', 'menace', 'reach', 'trample', 'vigilance',
    'ward', 'flash', 'prowess'
]

COMMON_KEYWORDS = [
    'affinity', 'amplify', 'annihilator', 'battalion', 'bloodthirst',
    'cascade', 'champion', 'changeling', 'convoke', 'crew',
    'cycling', 'delve', 'devoid', 'echo', 'encore',
    'entwine', 'equip', 'escalate', 'evoke', 'exalted',
    'exploit', 'fabricate', 'fading', 'flanking', 'flashback',
    'forecast', 'fortify', 'frenzy', 'gravestorm', 'haunt',
    'hideaway', 'horsemanship', 'imprint', 'improvise', 'infect',
    'intimidate', 'kicker', 'landwalk', 'level up', 'living weapon',
    'madness', 'megamorph', 'miracle', 'modular', 'morph',
    'multikicker', 'myriad', 'ninjutsu', 'offering', 'outlast',
    'overload', 'persist', 'phasing', 'poisonous', 'proliferate',
    'protection', 'provoke', 'prowl', 'rampage', 'rebound',
    'recover', 'reinforce', 'renown', 'replicate', 'retrace',
    'riot', 'ripple', 'shadow', 'shroud', 'soulbond',
    'soulshift', 'split second', 'storm', 'sunburst', 'surge',
    'suspend', 'totem armor', 'transfigure', 'transmute', 'tribute',
    'undying', 'unearth', 'unleash', 'vanishing', 'wither'
]

ABILITY_WORDS = [
    'adamant', 'addendum', 'alliance', 'battalion', 'bloodrush',
    'channel', 'chroma', 'cohort', 'constellation', 'converge',
    "council's dilemma", 'coven', 'delirium', 'domain', 'eminence',
    'enrage', 'fateful hour', 'ferocious', 'formidable', 'grandeur',
    'hellbent', 'heroic', 'imprint', 'inspired', 'join forces',
    'kinship', 'landfall', 'lieutenant', 'magecraft', 'metalcraft',
    'morbid', 'pack tactics', 'parley', 'radiance', 'raid',
    'rally', 'revolt', 'spell mastery', 'strive', 'sweep',
    'tempting offer', 'threshold', 'undergrowth', 'will of the council'
]

# Ability patterns to extract
ABILITY_PATTERNS = [
    (r'enters the battlefield', 'etb'),
    (r'leaves the battlefield', 'ltb'),
    (r'when.*dies', 'dies_trigger'),
    (r'at the beginning of', 'beginning_trigger'),
    (r'at end of turn', 'end_trigger'),
    (r'destroy target', 'targeted_destruction'),
    (r'exile target', 'targeted_exile'),
    (r'draw.*card', 'card_draw'),
    (r'search.*library', 'tutor'),
    (r'return.*from.*graveyard', 'reanimation'),
    (r'create.*token', 'token_generation'),
    (r'deals.*damage', 'damage_dealer'),
    (r'gain.*life', 'life_gain'),
    (r'lose.*life', 'life_loss'),
    (r'counter target', 'counterspell'),
    (r'sacrifice', 'sacrifice'),
    (r'{T}:', 'activated_ability'),
    (r'whenever', 'triggered_ability'),
    (r'add.*mana', 'mana_production'),
    (r'put.*counter', 'counter_manipulation'),
    (r'mill', 'mill'),
    (r'scry', 'scry'),
    (r'surveil', 'surveil'),
]


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def extract_keywords(oracle_text, card_keywords=None):
    """
    Extract keywords and ability words from card text.
    Combines Scryfall's keywords with our extracted abilities.
    """
    if not oracle_text:
        return card_keywords if card_keywords else []

    keywords = set(card_keywords) if card_keywords else set()
    text_lower = oracle_text.lower()

    # Extract evergreen keywords
    for keyword in EVERGREEN_KEYWORDS:
        if keyword in text_lower:
            keywords.add(keyword)

    # Extract common keywords
    for keyword in COMMON_KEYWORDS:
        if keyword in text_lower:
            keywords.add(keyword)

    # Extract ability words
    for ability_word in ABILITY_WORDS:
        if ability_word in text_lower:
            keywords.add(ability_word)

    # Extract ability patterns
    for pattern, ability_name in ABILITY_PATTERNS:
        if re.search(pattern, text_lower):
            keywords.add(ability_name)

    return list(keywords)


def parse_date(date_str):
    """Parse date string to PostgreSQL date format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None


def extract_card_data(card):
    """Extract relevant fields from card object with keyword extraction."""
    # Extract and enhance keywords
    scryfall_keywords = card.get('keywords', [])
    oracle_text = card.get('oracle_text')
    all_keywords = extract_keywords(oracle_text, scryfall_keywords)

    # Get produced mana
    produced_mana = card.get('produced_mana', [])

    return (
        card.get('id'),
        card.get('name'),
        card.get('mana_cost'),
        card.get('cmc'),
        card.get('type_line'),
        oracle_text,
        card.get('colors'),
        card.get('color_identity'),
        card.get('rarity'),
        card.get('set'),
        parse_date(card.get('released_at')),
        card.get('power'),
        card.get('toughness'),
        card.get('loyalty'),
        all_keywords,  # Enhanced keywords
        produced_mana,
        json.dumps(card, cls=DecimalEncoder)  # Full JSON in JSONB column
    )


def create_schema(cursor):
    """Create the cards table using schema file."""
    print("Creating schema...")

    try:
        with open('schema_with_rules.sql', 'r') as f:
            schema_sql = f.read()

        cursor.execute(schema_sql)
        print("✓ Schema created from schema_with_rules.sql")
    except FileNotFoundError:
        print("⚠ schema_with_rules.sql not found, trying schema.sql...")
        try:
            with open('schema.sql', 'r') as f:
                schema_sql = f.read()
            cursor.execute(schema_sql)
            print("✓ Schema created from schema.sql")
        except FileNotFoundError:
            print("✗ No schema file found. Please create schema_with_rules.sql first.")
            sys.exit(1)


def drop_indexes(cursor):
    """Drop indexes before bulk load for better performance."""
    print("Dropping indexes for faster bulk load...")

    # Standard indexes
    indexes = [
        'idx_cards_name', 'idx_cards_name_lower', 'idx_cards_type',
        'idx_cards_set', 'idx_cards_rarity', 'idx_cards_colors',
        'idx_cards_color_identity', 'idx_cards_keywords',
        'idx_cards_data_gin', 'idx_cards_cmc', 'idx_cards_released'
    ]

    # Vector indexes (likely don't exist yet, but try anyway)
    vector_indexes = [
        'idx_cards_embedding', 'idx_cards_oracle_embedding',
        'idx_rules_embedding', 'idx_keywords_embedding'
    ]

    for idx in indexes + vector_indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx}")
        except Exception as e:
            print(f"  Note: {idx} doesn't exist (this is fine)")

    print("✓ Indexes dropped")


def recreate_indexes(cursor):
    """Recreate indexes after bulk load."""
    print("\nRecreating indexes (this may take several minutes)...")

    indexes = [
        "CREATE INDEX idx_cards_name ON cards(name)",
        "CREATE INDEX idx_cards_name_lower ON cards(LOWER(name))",
        "CREATE INDEX idx_cards_type ON cards(type_line)",
        "CREATE INDEX idx_cards_set ON cards(set_code)",
        "CREATE INDEX idx_cards_rarity ON cards(rarity)",
        "CREATE INDEX idx_cards_colors ON cards USING GIN(colors)",
        "CREATE INDEX idx_cards_color_identity ON cards USING GIN(color_identity)",
        "CREATE INDEX idx_cards_keywords ON cards USING GIN(keywords)",
        "CREATE INDEX idx_cards_data_gin ON cards USING GIN(data jsonb_path_ops)",
        "CREATE INDEX idx_cards_cmc ON cards(cmc)",
        "CREATE INDEX idx_cards_released ON cards(released_at)"
    ]

    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            idx_name = idx_sql.split()[2]
            print(f"  ✓ Created {idx_name}")
        except Exception as e:
            print(f"  ⚠ Error creating index: {e}")

    print("✓ All standard indexes created")
    print("\nNote: Vector indexes will be created after embeddings are generated")


def load_cards(cursor, conn):
    """Stream-parse cards.json and batch insert into PostgreSQL."""
    print(f"\nStreaming {CARDS_FILE}...")
    print(f"Batch size: {BATCH_SIZE} cards\n")

    batch = []
    total_inserted = 0
    total_skipped = 0
    start_time = datetime.now()

    try:
        with open(CARDS_FILE, 'rb') as f:
            # Parse JSON array items one at a time
            parser = ijson.items(f, 'item')

            for card in parser:
                # Skip digital-only cards if desired (optional)
                # if card.get('digital', False):
                #     total_skipped += 1
                #     continue

                batch.append(extract_card_data(card))

                # Insert batch when it reaches BATCH_SIZE
                if len(batch) >= BATCH_SIZE:
                    execute_batch(cursor, """
                        INSERT INTO cards (
                            id, name, mana_cost, cmc, type_line, oracle_text,
                            colors, color_identity, rarity, set_code, released_at,
                            power, toughness, loyalty, keywords, produced_mana, data
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            oracle_text = EXCLUDED.oracle_text,
                            keywords = EXCLUDED.keywords,
                            updated_at = NOW()
                    """, batch)

                    conn.commit()
                    total_inserted += len(batch)

                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = total_inserted / elapsed if elapsed > 0 else 0

                    print(f"Inserted {total_inserted:,} cards ({rate:.0f} cards/sec)", end='\r')
                    batch = []

            # Insert remaining cards
            if batch:
                execute_batch(cursor, """
                    INSERT INTO cards (
                        id, name, mana_cost, cmc, type_line, oracle_text,
                        colors, color_identity, rarity, set_code, released_at,
                        power, toughness, loyalty, keywords, produced_mana, data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        oracle_text = EXCLUDED.oracle_text,
                        keywords = EXCLUDED.keywords,
                        updated_at = NOW()
                """, batch)

                conn.commit()
                total_inserted += len(batch)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✓ Inserted {total_inserted:,} cards in {elapsed:.1f} seconds ({total_inserted/elapsed:.0f} cards/sec)")
        if total_skipped > 0:
            print(f"  Skipped {total_skipped:,} cards")

    except FileNotFoundError:
        print(f"\n✗ Error: {CARDS_FILE} not found!")
        print("Please ensure cards.json is in the current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during load: {e}")
        conn.rollback()
        raise


def show_stats(cursor):
    """Show database statistics after loading."""
    print("\n" + "=" * 60)
    print("Database Statistics")
    print("=" * 60)

    # Total cards
    cursor.execute("SELECT COUNT(*) FROM cards")
    total = cursor.fetchone()[0]
    print(f"Total cards: {total:,}")

    # Cards by type
    cursor.execute("""
        SELECT card_type, count
        FROM card_type_stats
        ORDER BY count DESC
    """)
    print("\nCards by type:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    # Cards with keywords
    cursor.execute("SELECT COUNT(*) FROM cards WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0")
    with_keywords = cursor.fetchone()[0]
    print(f"\nCards with keywords: {with_keywords:,} ({100*with_keywords/total:.1f}%)")

    # Most common keywords
    cursor.execute("""
        SELECT keyword, COUNT(*) as count
        FROM cards, unnest(keywords) as keyword
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT 15
    """)
    print("\nTop 15 keywords:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    # Unique sets
    cursor.execute("SELECT COUNT(DISTINCT set_code) FROM cards")
    sets = cursor.fetchone()[0]
    print(f"\nUnique sets: {sets:,}")

    print("=" * 60)


def main():
    """Main execution flow."""
    print("=" * 60)
    print("MTG Cards Loader - Enhanced with Keyword Extraction")
    print("=" * 60)

    try:
        # Connect to PostgreSQL
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")

        # Setup schema
        create_schema(cursor)
        conn.commit()

        # Drop indexes for faster bulk load
        drop_indexes(cursor)
        conn.commit()

        # Load cards with streaming
        load_cards(cursor, conn)

        # Recreate indexes
        recreate_indexes(cursor)
        conn.commit()

        # Show statistics
        show_stats(cursor)

        print("\n✓ Load complete!")
        print("\nNext steps:")
        print("  1. Seed rules: psql -U postgres -d vector_mtg -f seed_rules.sql")
        print("  2. Generate embeddings: python generate_embeddings_dual.py")
        print("  3. Extract rules: python extract_rules.py")

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
