#!/usr/bin/env python3
"""
Generate vector embeddings for MTG cards and rules using sentence-transformers.
Creates embeddings for semantic similarity search.
"""

import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import sys
from typing import List, Tuple

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

# Embedding model - using a smaller, faster model for local inference
# You can upgrade to 'all-mpnet-base-v2' for better quality but slower speed
MODEL_NAME = 'all-MiniLM-L6-v2'  # 384 dimensions, fast, good quality
BATCH_SIZE = 100

# Embedding vector dimension (must match model output)
EMBEDDING_DIM = 384


def setup_vector_extension(cursor):
    """Ensure pgvector extension is installed and configured."""
    print("Setting up pgvector extension...")

    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✓ pgvector extension ready")
    except Exception as e:
        print(f"✗ Error setting up pgvector: {e}")
        sys.exit(1)


def add_embedding_columns(cursor):
    """Add vector columns to cards and rules tables if they don't exist."""
    print("Adding embedding columns...")

    # Add columns to cards table
    try:
        # Full card embedding (name + type + oracle text + keywords)
        cursor.execute(f"""
            ALTER TABLE cards
            ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIM});
        """)

        # Oracle text only embedding (for ability matching)
        cursor.execute(f"""
            ALTER TABLE cards
            ADD COLUMN IF NOT EXISTS oracle_embedding vector({EMBEDDING_DIM});
        """)

        print("✓ Card embedding columns added")
    except Exception as e:
        print(f"✗ Error adding card columns: {e}")
        sys.exit(1)

    # Add column to rules table
    try:
        cursor.execute(f"""
            ALTER TABLE rules
            ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIM});
        """)
        print("✓ Rule embedding column added")
    except Exception as e:
        print(f"✗ Error adding rule column: {e}")
        sys.exit(1)


def create_vector_indexes(cursor):
    """Create HNSW indexes for fast vector similarity search."""
    print("\nCreating vector indexes (this may take several minutes)...")

    indexes = [
        ("idx_cards_embedding", "cards", "embedding"),
        ("idx_cards_oracle_embedding", "cards", "oracle_embedding"),
        ("idx_rules_embedding", "rules", "embedding")
    ]

    for idx_name, table, column in indexes:
        try:
            # Drop existing index if it exists
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name};")

            # Create HNSW index for cosine similarity
            # HNSW is faster than IVFFlat for most use cases
            cursor.execute(f"""
                CREATE INDEX {idx_name}
                ON {table}
                USING hnsw ({column} vector_cosine_ops);
            """)
            print(f"  ✓ Created {idx_name}")
        except Exception as e:
            print(f"  ⚠ Error creating {idx_name}: {e}")


def fetch_cards_for_embedding(cursor) -> List[Tuple]:
    """Fetch cards that need embeddings."""
    cursor.execute("""
        SELECT id, name, type_line, oracle_text, keywords
        FROM cards
        WHERE oracle_text IS NOT NULL
        ORDER BY id
    """)
    return cursor.fetchall()


def fetch_rules_for_embedding(cursor) -> List[Tuple]:
    """Fetch rules that need embeddings."""
    cursor.execute("""
        SELECT id, rule_name, rule_template, subcategory
        FROM rules
        ORDER BY id
    """)
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


def generate_card_embeddings(cursor, conn, model):
    """Generate and store embeddings for all cards."""
    print("\n" + "=" * 60)
    print("Generating Card Embeddings")
    print("=" * 60)

    # Fetch all cards
    cards = fetch_cards_for_embedding(cursor)
    total_cards = len(cards)
    print(f"Processing {total_cards:,} cards with oracle text...")

    if total_cards == 0:
        print("No cards to process!")
        return

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

        # Generate embeddings
        full_embeddings = model.encode(full_texts, show_progress_bar=False)
        oracle_embeddings = model.encode(oracle_texts, show_progress_bar=False)

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

    print(f"✓ Generated embeddings for {total_cards:,} cards")


def generate_rule_embeddings(cursor, conn, model):
    """Generate and store embeddings for all rules."""
    print("\n" + "=" * 60)
    print("Generating Rule Embeddings")
    print("=" * 60)

    # Fetch all rules
    rules = fetch_rules_for_embedding(cursor)
    total_rules = len(rules)
    print(f"Processing {total_rules:,} rules...")

    if total_rules == 0:
        print("No rules to process! Run 'psql -U postgres -d vector_mtg -f seed_rules.sql' first.")
        return

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

        # Generate embeddings
        embeddings = model.encode(rule_texts, show_progress_bar=False)

        # Store in database
        for j, rule_id in enumerate(rule_ids):
            emb = embeddings[j].tolist()

            cursor.execute("""
                UPDATE rules
                SET embedding = %s
                WHERE id = %s
            """, (emb, rule_id))

        conn.commit()

    print(f"✓ Generated embeddings for {total_rules:,} rules")


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
            c.mana_cost,
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
        for name, mana_cost, type_line, oracle_text, similarity in results:
            print(f"\n  {name} {mana_cost or ''}")
            print(f"  {type_line}")
            print(f"  Similarity: {similarity:.3f}")
            if oracle_text:
                print(f"  {oracle_text[:100]}...")

    print("\n" + "=" * 60)


def main():
    """Main execution flow."""
    print("=" * 60)
    print("MTG Vector Embeddings Generator")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Embedding dimension: {EMBEDDING_DIM}")
    print(f"Batch size: {BATCH_SIZE}")

    try:
        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")

        # Setup vector extension
        setup_vector_extension(cursor)
        conn.commit()

        # Add embedding columns
        add_embedding_columns(cursor)
        conn.commit()

        # Load embedding model
        print(f"\nLoading embedding model '{MODEL_NAME}'...")
        print("(This may download the model on first run)")
        model = SentenceTransformer(MODEL_NAME)
        print("✓ Model loaded")

        # Generate embeddings
        generate_card_embeddings(cursor, conn, model)
        generate_rule_embeddings(cursor, conn, model)

        # Create indexes
        create_vector_indexes(cursor)
        conn.commit()

        # Show stats
        show_embedding_stats(cursor)

        # Test similarity search
        test_similarity_search(cursor)

        print("\n✓ Embedding generation complete!")
        print("\nYou can now:")
        print("  - Run semantic similarity queries")
        print("  - Use extract_rules.py to match cards to rules")
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
    main()
