#!/usr/bin/env python3
"""
Migrate Standard set cards from vector_mtg to vector_mtg_standard database.
"""
import psycopg2
import psycopg2.extras
import json
import time

# Register adapter for dict to JSONB
psycopg2.extras.register_default_jsonb()

# Standard set codes
STANDARD_SETS = ['woe', 'lci', 'mkm', 'otj', 'blb', 'dsk', 'fdn', 'dft', 'tdm', 'fin', 'eoe', 'spm']

def migrate_cards():
    """Migrate Standard cards between databases."""
    # Connect to source database
    source_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="vector_mtg",
        user="postgres",
        password="postgres"
    )

    # Connect to destination database
    dest_conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="vector_mtg_standard",
        user="postgres",
        password="postgres"
    )

    try:
        source_cur = source_conn.cursor()
        dest_cur = dest_conn.cursor()

        # Get total count
        print("Counting Standard set cards...")
        source_cur.execute("""
            SELECT COUNT(*) FROM cards WHERE set_code IN %s
        """, (tuple(STANDARD_SETS),))
        total = source_cur.fetchone()[0]
        print(f"Found {total:,} Standard cards to migrate\n")

        # Process in batches
        batch_size = 100
        offset = 0
        start_time = time.time()

        print(f"Migrating in batches of {batch_size}...\n")

        while offset < total:
            batch_start = time.time()

            # Fetch next batch
            source_cur.execute("""
                SELECT id, name, mana_cost, cmc, type_line, oracle_text,
                       colors, color_identity, rarity, set_code, released_at,
                       power, toughness, loyalty, keywords, produced_mana,
                       data, created_at, updated_at, embedding, oracle_embedding,
                       is_playable, legality_updated_at
                FROM cards
                WHERE set_code IN %s
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (tuple(STANDARD_SETS), batch_size, offset))

            batch = source_cur.fetchall()

            # Convert JSONB data field to JSON string for insertion
            batch_data = []
            for row in batch:
                row_list = list(row)
                # Convert dict at index 16 (data column) to JSON string
                if row_list[16] is not None:
                    row_list[16] = json.dumps(row_list[16])
                batch_data.append(tuple(row_list))

            # Use executemany for efficient batch insert
            dest_cur.executemany("""
                INSERT INTO cards (
                    id, name, mana_cost, cmc, type_line, oracle_text,
                    colors, color_identity, rarity, set_code, released_at,
                    power, toughness, loyalty, keywords, produced_mana,
                    data, created_at, updated_at, embedding, oracle_embedding,
                    is_playable, legality_updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s
                )
            """, batch_data)

            dest_conn.commit()

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
        dest_cur.execute("SELECT COUNT(*) FROM cards")
        final_count = dest_cur.fetchone()[0]

        print(f"\n✓ Migration complete!")
        print(f"  Total cards migrated: {final_count:,}")
        print(f"  Total time: {total_time:.2f}s")

    except Exception as e:
        print(f"Error during migration: {e}")
        dest_conn.rollback()
        raise
    finally:
        source_cur.close()
        dest_cur.close()
        source_conn.close()
        dest_conn.close()

if __name__ == "__main__":
    migrate_cards()
