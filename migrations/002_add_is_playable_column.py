#!/usr/bin/env python3
"""
Migration: Add is_playable column to cards table

This migration adds a boolean column to filter out non-playable cards
(tokens, planes, schemes, banned cards, etc.) based on Standard and Commander legality.

Date: 2025-11-25
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


def migrate_up(conn):
    """Apply the migration."""
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("MIGRATION: Add is_playable column")
    print("=" * 60)

    # Step 1: Add columns
    print("\n[1/4] Adding is_playable and legality_updated_at columns...")
    cur.execute("""
        ALTER TABLE cards
        ADD COLUMN IF NOT EXISTS is_playable BOOLEAN DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS legality_updated_at TIMESTAMP DEFAULT NOW()
    """)
    print("✓ Columns added")

    # Step 2: Populate is_playable based on legalities
    print("\n[2/4] Populating is_playable values...")
    print("      Rule: Card is playable if legal in Standard OR Commander")
    print("      Processing 508,686 cards...")

    cur.execute("""
        UPDATE cards
        SET is_playable = (
            data->'legalities'->>'standard' = 'legal' OR
            data->'legalities'->>'commander' = 'legal'
        ),
        legality_updated_at = NOW()
    """)

    rows_updated = cur.rowcount
    print(f"✓ Updated {rows_updated:,} cards")

    # Step 3: Create index for fast filtering
    print("\n[3/4] Creating partial index on is_playable...")
    print("      This will speed up queries that filter playable cards")

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cards_playable
        ON cards(is_playable)
        WHERE is_playable = TRUE
    """)
    print("✓ Index created")

    # Step 4: Verify results
    print("\n[4/4] Verifying migration results...")
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE is_playable = TRUE) as playable,
            COUNT(*) FILTER (WHERE is_playable = FALSE) as non_playable
        FROM cards
    """)
    result = cur.fetchone()
    total, playable, non_playable = result

    print(f"\n{'=' * 60}")
    print("MIGRATION RESULTS")
    print("=" * 60)
    print(f"Total cards:       {total:>10,}")
    print(f"Playable:          {playable:>10,} ({100*playable/total:>5.1f}%)")
    print(f"Non-playable:      {non_playable:>10,} ({100*non_playable/total:>5.1f}%)")
    print("=" * 60)

    # Show sample of non-playable cards
    print("\nSample non-playable cards:")
    cur.execute("""
        SELECT name, type_line,
               data->'legalities'->>'standard' as standard,
               data->'legalities'->>'commander' as commander
        FROM cards
        WHERE is_playable = FALSE
        LIMIT 10
    """)
    samples = cur.fetchall()
    for card in samples:
        print(f"  • {card[0]:30} {card[1]:35} (std:{card[2]:>10}, cmd:{card[3]:>10})")

    conn.commit()
    print("\n✓ Migration completed successfully!")
    print(f"  Timestamp: {datetime.now().isoformat()}\n")


def migrate_down(conn):
    """Rollback the migration."""
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("ROLLBACK: Remove is_playable column")
    print("=" * 60)

    print("\n[1/2] Dropping index...")
    cur.execute("DROP INDEX IF EXISTS idx_cards_playable")
    print("✓ Index dropped")

    print("\n[2/2] Removing columns...")
    cur.execute("""
        ALTER TABLE cards
        DROP COLUMN IF EXISTS is_playable,
        DROP COLUMN IF EXISTS legality_updated_at
    """)
    print("✓ Columns removed")

    conn.commit()
    print("\n✓ Rollback completed successfully!\n")


def main():
    """Run migration."""
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python migrations/002_add_is_playable_column.py up     # Apply migration")
        print("  python migrations/002_add_is_playable_column.py down   # Rollback migration")
        print()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command not in ['up', 'down']:
        print(f"\n✗ Invalid command: {command}")
        print("  Use 'up' to apply migration or 'down' to rollback\n")
        sys.exit(1)

    try:
        print("\nConnecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected to vector_mtg database\n")

        if command == 'up':
            migrate_up(conn)
        else:
            migrate_down(conn)

        conn.close()
        print("✓ Database connection closed\n")

    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection error: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker compose up -d\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
