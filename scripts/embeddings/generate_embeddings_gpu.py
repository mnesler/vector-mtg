#!/usr/bin/env python3
"""
GPU-Accelerated Vector Embeddings Generator for MTG Cards
Uses all-mpnet-base-v2 for higher quality embeddings (768 dimensions)
Optimized for NVIDIA GPU with CUDA support
"""

import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import sys
import torch
from typing import List, Tuple
import time

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

# Upgraded embedding model - better quality, GPU-optimized
MODEL_NAME = 'all-mpnet-base-v2'  # 768 dimensions, excellent quality
EMBEDDING_DIM = 768  # Updated from 384 to 768

# GPU-optimized batch size (much larger than CPU)
BATCH_SIZE = 256  # Process 256 cards at once on GPU

# Device configuration
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def setup_vector_extension(cursor):
    """Ensure pgvector extension is installed and configured."""
    print("Setting up pgvector extension...")

    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✓ pgvector extension ready")
    except Exception as e:
        print(f"✗ Error setting up pgvector: {e}")
        sys.exit(1)


def update_embedding_columns(cursor):
    """Update vector columns to new dimension size."""
    print(f"Updating embedding columns to {EMBEDDING_DIM} dimensions...")

    try:
        # Drop old columns and create new ones with correct dimensions
        # This is necessary because pgvector doesn't support changing dimensions

        print("  Backing up old embeddings...")
        cursor.execute("""
            ALTER TABLE cards RENAME COLUMN embedding TO embedding_old;
        """)
        cursor.execute("""
            ALTER TABLE cards RENAME COLUMN oracle_embedding TO oracle_embedding_old;
        """)

        print("  Creating new embedding columns...")
        cursor.execute(f"""
            ALTER TABLE cards
            ADD COLUMN embedding vector({EMBEDDING_DIM});
        """)
        cursor.execute(f"""
            ALTER TABLE cards
            ADD COLUMN oracle_embedding vector({EMBEDDING_DIM});
        """)

        print("✓ Card embedding columns updated")
        print("  (Old embeddings preserved as embedding_old, oracle_embedding_old)")
    except psycopg2.errors.DuplicateColumn:
        print("✓ Columns already exist with correct dimensions")
    except Exception as e:
        # If columns don't exist yet, create them
        if "does not exist" in str(e):
            print("  Creating new embedding columns...")
            cursor.execute(f"""
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIM});
            """)
            cursor.execute(f"""
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS oracle_embedding vector({EMBEDDING_DIM});
            """)
            print("✓ Card embedding columns created")
        else:
            print(f"✗ Error updating card columns: {e}")
            sys.exit(1)

    # Update rules table
    try:
        print("  Updating rules embedding column...")
        cursor.execute("""
            ALTER TABLE rules RENAME COLUMN embedding TO embedding_old;
        """)
        cursor.execute(f"""
            ALTER TABLE rules
            ADD COLUMN embedding vector({EMBEDDING_DIM});
        """)
        print("✓ Rule embedding column updated")
    except psycopg2.errors.DuplicateColumn:
        print("✓ Rules column already exists with correct dimensions")
    except Exception as e:
        if "does not exist" in str(e):
            cursor.execute(f"""
                ALTER TABLE rules
                ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIM});
            """)
            print("✓ Rule embedding column created")
        else:
            print(f"⚠ Rules table update: {e}")


def create_vector_indexes(cursor):
    """Create HNSW indexes for fast vector similarity search."""
    print("\nCreating vector indexes (this may take several minutes)...")

    indexes = [
        ("idx_cards_embedding_v2", "cards", "embedding"),
        ("idx_cards_oracle_embedding_v2", "cards", "oracle_embedding"),
        ("idx_rules_embedding_v2", "rules", "embedding")
    ]

    for idx_name, table, column in indexes:
        try:
            # Drop existing index if it exists
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name};")

            # Create HNSW index for cosine similarity
            cursor.execute(f"""
                CREATE INDEX {idx_name}
                ON {table}
                USING hnsw ({column} vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """)
            print(f"  ✓ Created {idx_name}")
        except Exception as e:
            print(f"  ⚠ Error creating {idx_name}: {e}")


def fetch_cards_for_embedding(cursor, limit=None) -> List[Tuple]:
    """Fetch cards that need embeddings."""
    query = """
        SELECT id, name, type_line, oracle_text, keywords
        FROM cards
        WHERE oracle_text IS NOT NULL
        ORDER BY id
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    return cursor.fetchall()


def fetch_rules_for_embedding(cursor, limit=None) -> List[Tuple]:
    """Fetch rules that need embeddings."""
    query = """
        SELECT id, rule_name, rule_template, subcategory
        FROM rules
        ORDER BY id
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    return cursor.fetchall()


def create_card_text(name: str, type_line: str, oracle_text: str, keywords: List[str]) -> str:
    """Create a comprehensive text representation of a card for embedding."""
    parts = [name, type_line]

    if oracle_text:
        parts.append(oracle_text)

    if keywords:
        parts.append(f"Keywords: {', '.join(keywords)}")

    return " | ".join(parts)


def create_rule_text(rule_name: str, rule_template: str, subcategory: str) -> str:
    """Create a text representation of a rule for embedding."""
    parts = [rule_name, rule_template]

    if subcategory:
        parts.append(f"Category: {subcategory}")

    return " | ".join(parts)


def generate_card_embeddings(cursor, conn, model, limit=None):
    """Generate and store embeddings for all cards using GPU acceleration."""
    print("\n" + "=" * 60)
    print("Generating Card Embeddings (GPU-Accelerated)")
    print("=" * 60)

    # Fetch all cards
    cards = fetch_cards_for_embedding(cursor, limit=limit)
    total_cards = len(cards)
    print(f"Processing {total_cards:,} cards with oracle text...")

    if total_cards == 0:
        print("No cards to process!")
        return

    # Track performance
    start_time = time.time()

    # Process in batches
    for i in tqdm(range(0, total_cards, BATCH_SIZE), desc="Embedding cards"):
        batch = cards[i:i + BATCH_SIZE]

        # Prepare texts
        card_ids = []
        full_texts = []
        oracle_texts = []

        for card_id, name, type_line, oracle_text, keywords in batch:
            card_ids.append(card_id)

            # Full card embedding
            full_text = create_card_text(name, type_line or "", oracle_text or "", keywords or [])
            full_texts.append(full_text)

            # Oracle text only embedding
            oracle_texts.append(oracle_text or "")

        # Generate embeddings on GPU (this is where the magic happens!)
        full_embeddings = model.encode(
            full_texts,
            show_progress_bar=False,
            batch_size=BATCH_SIZE,
            convert_to_numpy=True
        )
        oracle_embeddings = model.encode(
            oracle_texts,
            show_progress_bar=False,
            batch_size=BATCH_SIZE,
            convert_to_numpy=True
        )

        # Store in database
        for j, card_id in enumerate(card_ids):
            full_emb = full_embeddings[j].tolist()
            oracle_emb = oracle_embeddings[j].tolist()

            cursor.execute("""
                UPDATE cards
                SET embedding = %s, oracle_embedding = %s
                WHERE id = %s
            """, (full_emb, oracle_emb, card_id))

        conn.commit()

    elapsed_time = time.time() - start_time
    cards_per_second = total_cards / elapsed_time

    print(f"✓ Generated embeddings for {total_cards:,} cards")
    print(f"  Time: {elapsed_time:.1f}s ({cards_per_second:.0f} cards/sec)")


def generate_rule_embeddings(cursor, conn, model, limit=None):
    """Generate and store embeddings for all rules using GPU acceleration."""
    print("\n" + "=" * 60)
    print("Generating Rule Embeddings (GPU-Accelerated)")
    print("=" * 60)

    # Fetch all rules
    rules = fetch_rules_for_embedding(cursor, limit=limit)
    total_rules = len(rules)
    print(f"Processing {total_rules:,} rules...")

    if total_rules == 0:
        print("No rules to process!")
        return

    # Track performance
    start_time = time.time()

    # Process in batches
    for i in tqdm(range(0, total_rules, BATCH_SIZE), desc="Embedding rules"):
        batch = rules[i:i + BATCH_SIZE]

        # Prepare texts
        rule_ids = []
        rule_texts = []

        for rule_id, rule_name, rule_template, subcategory in batch:
            rule_ids.append(rule_id)
            rule_text = create_rule_text(rule_name, rule_template, subcategory or "")
            rule_texts.append(rule_text)

        # Generate embeddings on GPU
        embeddings = model.encode(
            rule_texts,
            show_progress_bar=False,
            batch_size=BATCH_SIZE,
            convert_to_numpy=True
        )

        # Store in database
        for j, rule_id in enumerate(rule_ids):
            emb = embeddings[j].tolist()

            cursor.execute("""
                UPDATE rules
                SET embedding = %s
                WHERE id = %s
            """, (emb, rule_id))

        conn.commit()

    elapsed_time = time.time() - start_time
    rules_per_second = total_rules / elapsed_time

    print(f"✓ Generated embeddings for {total_rules:,} rules")
    print(f"  Time: {elapsed_time:.1f}s ({rules_per_second:.0f} rules/sec)")


def show_embedding_stats(cursor):
    """Show statistics about generated embeddings."""
    print("\n" + "=" * 60)
    print("Embedding Statistics")
    print("=" * 60)

    # Card embeddings
    cursor.execute("SELECT COUNT(*) FROM cards WHERE embedding IS NOT NULL")
    cards_with_full = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cards WHERE oracle_embedding IS NOT NULL")
    cards_with_oracle = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cards")
    total_cards = cursor.fetchone()[0]

    print(f"Cards with full embeddings: {cards_with_full:,} / {total_cards:,} ({100*cards_with_full/total_cards:.1f}%)")
    print(f"Cards with oracle embeddings: {cards_with_oracle:,} / {total_cards:,} ({100*cards_with_oracle/total_cards:.1f}%)")

    # Rule embeddings
    cursor.execute("SELECT COUNT(*) FROM rules WHERE embedding IS NOT NULL")
    rules_with_emb = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rules")
    total_rules = cursor.fetchone()[0]

    if total_rules > 0:
        print(f"Rules with embeddings: {rules_with_emb:,} / {total_rules:,} ({100*rules_with_emb/total_rules:.1f}%)")
    else:
        print("Rules with embeddings: 0 (no rules seeded yet)")

    print("=" * 60)


def test_similarity_search(cursor):
    """Test similarity search with a sample query."""
    print("\n" + "=" * 60)
    print("Testing Similarity Search")
    print("=" * 60)

    # Check if we have embeddings
    cursor.execute("SELECT COUNT(*) FROM cards WHERE embedding IS NOT NULL")
    if cursor.fetchone()[0] == 0:
        print("No embeddings to test!")
        return

    print("\nExample: Finding cards similar to 'Lightning Bolt'")
    cursor.execute("""
        WITH target_card AS (
            SELECT embedding
            FROM cards
            WHERE name = 'Lightning Bolt'
            LIMIT 1
        )
        SELECT
            c.name,
            c.type_line,
            c.oracle_text,
            1 - (c.embedding <=> t.embedding) as similarity
        FROM cards c, target_card t
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> t.embedding
        LIMIT 5
    """)

    results = cursor.fetchall()
    if results:
        for name, type_line, oracle_text, similarity in results:
            print(f"\n  {name}")
            print(f"  {type_line}")
            print(f"  Similarity: {similarity:.4f}")
            if oracle_text:
                print(f"  {oracle_text[:100]}...")

    print("\n" + "=" * 60)


def show_gpu_info():
    """Display GPU information."""
    print("\n" + "=" * 60)
    print("GPU Information")
    print("=" * 60)

    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print(f"Current Memory Usage: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    else:
        print("CUDA not available - running on CPU")
        print("⚠ Warning: CPU mode will be significantly slower!")

    print("=" * 60)


def main(test_mode=False):
    """Main execution flow."""
    print("=" * 60)
    print("MTG GPU-Accelerated Vector Embeddings Generator")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Embedding dimension: {EMBEDDING_DIM}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Device: {DEVICE}")

    if test_mode:
        print("\n⚠ TEST MODE - Processing only 1000 cards")

    try:
        # Show GPU info
        show_gpu_info()

        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")

        # Setup vector extension
        setup_vector_extension(cursor)
        conn.commit()

        # Update embedding columns
        update_embedding_columns(cursor)
        conn.commit()

        # Load embedding model on GPU
        print(f"\nLoading embedding model '{MODEL_NAME}' on {DEVICE.upper()}...")
        print("(This may download the model on first run)")
        model = SentenceTransformer(MODEL_NAME, device=DEVICE)
        print(f"✓ Model loaded on {DEVICE.upper()}")

        # Generate embeddings
        limit = 1000 if test_mode else None
        generate_card_embeddings(cursor, conn, model, limit=limit)
        generate_rule_embeddings(cursor, conn, model, limit=limit)

        if not test_mode:
            # Create indexes (skip in test mode)
            create_vector_indexes(cursor)
            conn.commit()

        # Show stats
        show_embedding_stats(cursor)

        # Test similarity search
        test_similarity_search(cursor)

        print("\n✓ Embedding generation complete!")

        if test_mode:
            print("\n⚠ This was a TEST RUN")
            print("  To process all cards, run:")
            print("  python generate_embeddings_gpu.py")
        else:
            print("\nYou can now:")
            print("  - Run semantic similarity queries")
            print("  - Use improved embeddings for better search results")
            print("  - Query similar cards in pgAdmin")

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
    # Check for test mode flag
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    main(test_mode=test_mode)
