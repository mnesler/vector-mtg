#!/usr/bin/env python3
"""
Migrate Standard set cards using INSERT...SELECT within same database server.
"""
import psycopg2
import time

# Standard set codes
STANDARD_SETS = ['woe', 'lci', 'mkm', 'otj', 'blb', 'dsk', 'fdn', 'dft', 'tdm', 'fin', 'eoe', 'spm']

def migrate_cards():
    """Migrate Standard cards using direct SQL INSERT...SELECT."""
    # Connect to source database
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="vector_mtg",
        user="postgres",
        password="postgres"
    )

    try:
        cur = conn.cursor()

        # Get total count
        print("Counting Standard set cards...")
        cur.execute("""
            SELECT COUNT(*) FROM cards WHERE set_code IN %s
        """, (tuple(STANDARD_SETS),))
        total = cur.fetchone()[0]
        print(f"Found {total:,} Standard cards to migrate\n")

        # Process in batches of 100
        batch_size = 100
        offset = 0
        start_time = time.time()

        print(f"Migrating in batches of {batch_size}...\n")

        while offset < total:
            batch_start = time.time()

            # Use pg_temp to transfer data
            cur.execute(f"""
                WITH batch AS (
                    SELECT * FROM cards
                    WHERE set_code IN %s
                    ORDER BY id
                    LIMIT {batch_size} OFFSET {offset}
                )
                INSERT INTO dblink('dbname=vector_mtg_standard', '
                    SELECT id, name, mana_cost, cmc, type_line, oracle_text,
                           colors, color_identity, rarity, set_code, released_at,
                           power, toughness, loyalty, keywords, produced_mana,
                           data, created_at, updated_at, embedding, oracle_embedding,
                           is_playable, legality_updated_at
                    FROM batch
                ')
            """, (tuple(STANDARD_SETS),))

            conn.commit()

            batch_time = time.time() - batch_start
            offset += batch_size
            progress = min(offset, total)
            elapsed = time.time() - start_time
            cards_per_sec = progress / elapsed if elapsed > 0 else 0
            percent = progress * 100 / total

            # Estimate time remaining
            if progress < total:
                remaining = total - progress
                eta_seconds = remaining / cards_per_sec if cards_per_sec > 0 else 0
                eta_str = f"ETA: {eta_seconds:.0f}s"
            else:
                eta_str = "Complete!"

            batch_num = offset // batch_size
            total_batches = (total + batch_size - 1) // batch_size
            print(f"Batch {batch_num}/{total_batches}: Inserted {progress:,}/{total:,} cards ({percent:.1f}%) | {cards_per_sec:.0f} cards/sec | Batch time: {batch_time:.2f}s | {eta_str}")

        total_time = time.time() - start_time

        # Verify count
        cur.execute("SELECT COUNT(*) FROM dblink('dbname=vector_mtg_standard', 'SELECT COUNT(*) FROM cards') AS t(count bigint)")
        final_count = cur.fetchone()[0]

        print(f"\n✓ Migration complete!")
        print(f"  Total cards migrated: {final_count:,}")
        print(f"  Total time: {total_time:.2f}s")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_cards()
