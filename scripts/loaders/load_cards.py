#!/usr/bin/env python3
"""
Stream-load MTG cards from cards.json into PostgreSQL without loading entire file into memory.
Uses ijson for streaming JSON parsing and psycopg2 for batch inserts.
"""

import ijson
import json
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from decimal import Decimal
import sys

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


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def create_schema(cursor):
    """Create the cards table and prepare for bulk load."""
    print("Creating schema...")

    # Read and execute schema file
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()

    cursor.execute(schema_sql)
    print("✓ Schema created")


def drop_indexes(cursor):
    """Drop indexes before bulk load for better performance."""
    print("Dropping indexes for faster bulk load...")

    indexes = ['idx_cards_name', 'idx_cards_type', 'idx_cards_set',
               'idx_cards_rarity', 'idx_cards_data_gin']

    for idx in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx}")
        except Exception as e:
            print(f"  Warning: Could not drop {idx}: {e}")

    print("✓ Indexes dropped")


def recreate_indexes(cursor):
    """Recreate indexes after bulk load."""
    print("\nRecreating indexes (this may take a few minutes)...")

    indexes = [
        "CREATE INDEX idx_cards_name ON cards(name)",
        "CREATE INDEX idx_cards_type ON cards(type_line)",
        "CREATE INDEX idx_cards_set ON cards(set_code)",
        "CREATE INDEX idx_cards_rarity ON cards(rarity)",
        "CREATE INDEX idx_cards_data_gin ON cards USING GIN(data jsonb_path_ops)"
    ]

    for idx_sql in indexes:
        cursor.execute(idx_sql)
        print(f"  ✓ Created {idx_sql.split()[2]}")

    print("✓ All indexes created")


def parse_date(date_str):
    """Parse date string to PostgreSQL date format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None


def extract_card_data(card):
    """Extract relevant fields from card object."""
    return (
        card.get('id'),
        card.get('name'),
        card.get('mana_cost'),
        card.get('cmc'),
        card.get('type_line'),
        card.get('oracle_text'),
        card.get('colors'),  # PostgreSQL will convert to TEXT[]
        card.get('color_identity'),
        card.get('rarity'),
        card.get('set'),
        parse_date(card.get('released_at')),
        json.dumps(card, cls=DecimalEncoder)  # Full JSON in JSONB column
    )


def load_cards(cursor, conn):
    """Stream-parse cards.json and batch insert into PostgreSQL."""
    print(f"\nStreaming {CARDS_FILE}...")
    print(f"Batch size: {BATCH_SIZE} cards\n")

    batch = []
    total_inserted = 0
    start_time = datetime.now()

    try:
        with open(CARDS_FILE, 'rb') as f:
            # Parse JSON array items one at a time
            parser = ijson.items(f, 'item')

            for card in parser:
                batch.append(extract_card_data(card))

                # Insert batch when it reaches BATCH_SIZE
                if len(batch) >= BATCH_SIZE:
                    execute_batch(cursor, """
                        INSERT INTO cards (
                            id, name, mana_cost, cmc, type_line, oracle_text,
                            colors, color_identity, rarity, set_code, released_at, data
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
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
                        colors, color_identity, rarity, set_code, released_at, data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, batch)

                conn.commit()
                total_inserted += len(batch)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✓ Inserted {total_inserted:,} cards in {elapsed:.1f} seconds ({total_inserted/elapsed:.0f} cards/sec)")

    except FileNotFoundError:
        print(f"\n✗ Error: {CARDS_FILE} not found!")
        print("Please ensure cards.json is in the current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during load: {e}")
        conn.rollback()
        raise


def main():
    """Main execution flow."""
    print("=" * 60)
    print("MTG Cards Loader - Streaming JSON to PostgreSQL")
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

        # Show summary
        cursor.execute("SELECT COUNT(*) FROM cards")
        count = cursor.fetchone()[0]

        print("\n" + "=" * 60)
        print(f"✓ Load complete! Total cards in database: {count:,}")
        print("=" * 60)

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
        sys.exit(1)


if __name__ == '__main__':
    main()
