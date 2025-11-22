# MTG Card Visualization Project Guide

This comprehensive guide covers everything needed to build a vector-powered MTG card visualization system.

---

## 1. Embedding Generation Script

### Overview
Generate vector embeddings for all MTG cards using OpenAI or open-source models, then store them in PostgreSQL.

### Script: `generate_embeddings.py`

```python
#!/usr/bin/env python3
"""
Generate vector embeddings for MTG cards and update the database.
Supports both OpenAI API and local sentence-transformers models.
"""

import psycopg2
from psycopg2.extras import execute_batch
import sys
from datetime import datetime
import time

# Choose your embedding provider
EMBEDDING_PROVIDER = 'openai'  # Options: 'openai', 'sentence-transformers'

# OpenAI Configuration
OPENAI_API_KEY = 'your-api-key-here'  # Set this or use environment variable
OPENAI_MODEL = 'text-embedding-3-small'  # 1536 dimensions, $0.02/1M tokens
EMBEDDING_DIMENSION = 1536

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

BATCH_SIZE = 100  # Number of cards to process per batch


def get_openai_embeddings(texts):
    """Generate embeddings using OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.embeddings.create(
        input=texts,
        model=OPENAI_MODEL
    )

    return [item.embedding for item in response.data]


def get_local_embeddings(texts):
    """Generate embeddings using sentence-transformers (local, free)."""
    from sentence_transformers import SentenceTransformer

    # Load model once (cached after first run)
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
    # Alternative: 'all-mpnet-base-v2' (768 dim, better quality)

    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def extract_card_text(card_data):
    """
    Extract meaningful text from card for embedding generation.
    Combines name, type, and oracle text for semantic understanding.
    """
    parts = []

    if card_data.get('name'):
        parts.append(card_data['name'])

    if card_data.get('type_line'):
        parts.append(card_data['type_line'])

    if card_data.get('oracle_text'):
        parts.append(card_data['oracle_text'])

    # Optional: include mana cost for better clustering
    if card_data.get('mana_cost'):
        parts.append(f"Mana cost: {card_data['mana_cost']}")

    return ' | '.join(parts)


def generate_embeddings_for_batch(cards, provider='openai'):
    """Generate embeddings for a batch of cards."""
    texts = [extract_card_text(card) for card in cards]

    if provider == 'openai':
        return get_openai_embeddings(texts)
    else:
        return get_local_embeddings(texts)


def update_embeddings(cursor, conn):
    """Fetch cards, generate embeddings, and update database."""

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM cards WHERE embedding IS NULL")
    total_cards = cursor.fetchone()[0]

    if total_cards == 0:
        print("All cards already have embeddings!")
        return

    print(f"\nGenerating embeddings for {total_cards:,} cards...")
    print(f"Provider: {EMBEDDING_PROVIDER}")
    print(f"Batch size: {BATCH_SIZE}\n")

    processed = 0
    start_time = datetime.now()

    # Process in batches
    offset = 0

    while True:
        # Fetch batch of cards without embeddings
        cursor.execute("""
            SELECT id, name, type_line, oracle_text, mana_cost, data
            FROM cards
            WHERE embedding IS NULL
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset))

        rows = cursor.fetchall()

        if not rows:
            break

        # Prepare card data
        cards = []
        for row in rows:
            cards.append({
                'id': row[0],
                'name': row[1],
                'type_line': row[2],
                'oracle_text': row[3],
                'mana_cost': row[4],
                'data': row[5]
            })

        try:
            # Generate embeddings
            embeddings = generate_embeddings_for_batch(cards, EMBEDDING_PROVIDER)

            # Update database
            update_data = [
                (embeddings[i], cards[i]['id'])
                for i in range(len(cards))
            ]

            execute_batch(cursor, """
                UPDATE cards
                SET embedding = %s
                WHERE id = %s
            """, update_data)

            conn.commit()
            processed += len(cards)

            # Progress update
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total_cards - processed) / rate if rate > 0 else 0

            print(f"Progress: {processed:,}/{total_cards:,} ({100*processed/total_cards:.1f}%) "
                  f"| Rate: {rate:.0f} cards/sec | ETA: {eta/60:.1f} min", end='\r')

            # Rate limiting for OpenAI API (optional)
            if EMBEDDING_PROVIDER == 'openai':
                time.sleep(0.1)  # Avoid rate limits

        except Exception as e:
            print(f"\nError processing batch at offset {offset}: {e}")
            conn.rollback()
            raise

        offset += BATCH_SIZE

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n\n✓ Generated {processed:,} embeddings in {elapsed:.1f} seconds "
          f"({processed/elapsed:.0f} cards/sec)")


def create_vector_index(cursor):
    """Create optimized vector index for fast similarity search."""
    print("\nCreating vector index...")
    print("(This may take several minutes for large datasets)")

    # IVFFlat index - good balance of speed and accuracy
    # lists = sqrt(total_rows) is a good starting point
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cards_embedding_ivfflat
        ON cards
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    print("✓ Vector index created")

    # Optional: HNSW index (better quality, more memory)
    # cursor.execute("""
    #     CREATE INDEX IF NOT EXISTS idx_cards_embedding_hnsw
    #     ON cards
    #     USING hnsw (embedding vector_cosine_ops)
    #     WITH (m = 16, ef_construction = 64);
    # """)


def main():
    print("=" * 60)
    print("MTG Card Embedding Generator")
    print("=" * 60)

    try:
        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected")

        # Ensure pgvector extension exists
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        print("✓ pgvector extension enabled")

        # Check if embedding column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='cards' AND column_name='embedding'
        """)

        if not cursor.fetchone():
            print("\nAdding embedding column to cards table...")
            cursor.execute(f"ALTER TABLE cards ADD COLUMN embedding vector({EMBEDDING_DIMENSION})")
            conn.commit()
            print("✓ Embedding column added")

        # Generate embeddings
        update_embeddings(cursor, conn)

        # Create vector index
        create_vector_index(cursor)
        conn.commit()

        # Summary statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(embedding) as with_embeddings,
                COUNT(*) - COUNT(embedding) as missing
            FROM cards
        """)

        stats = cursor.fetchone()

        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  Total cards: {stats[0]:,}")
        print(f"  With embeddings: {stats[1]:,}")
        print(f"  Missing: {stats[2]:,}")
        print("=" * 60)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### Installation Requirements

```bash
# For OpenAI embeddings
pip install openai psycopg2-binary

# For local embeddings (free, no API key needed)
pip install sentence-transformers psycopg2-binary

# Update requirements.txt
cat >> requirements.txt << EOF
openai>=1.0.0
sentence-transformers>=2.2.0
EOF
```

### Usage

```bash
# Using OpenAI (fast, paid)
export OPENAI_API_KEY='your-key'
python generate_embeddings.py

# Using local model (free, slower first run for model download)
# Edit EMBEDDING_PROVIDER to 'sentence-transformers'
python generate_embeddings.py
```

---

## 2. Database Schema Updates

### Updated Schema: `schema_with_vectors.sql`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop table if exists
DROP TABLE IF EXISTS cards;

-- Create cards table with vector support
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mana_cost VARCHAR(100),
    cmc DECIMAL,
    type_line VARCHAR(255),
    oracle_text TEXT,
    colors TEXT[],
    color_identity TEXT[],
    rarity VARCHAR(20),
    set_code VARCHAR(10),
    released_at DATE,
    data JSONB,  -- Full card JSON for flexibility
    embedding vector(1536),  -- Vector embedding for semantic search
    created_at TIMESTAMP DEFAULT NOW()
);

-- Standard indexes (add after bulk load)
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_type ON cards(type_line);
CREATE INDEX idx_cards_set ON cards(set_code);
CREATE INDEX idx_cards_rarity ON cards(rarity);
CREATE INDEX idx_cards_colors ON cards USING GIN(colors);
CREATE INDEX idx_cards_data_gin ON cards USING GIN(data jsonb_path_ops);

-- Vector similarity index (IVFFlat - good for large datasets)
-- Note: Create this AFTER populating embeddings for best performance
-- CREATE INDEX idx_cards_embedding_ivfflat
-- ON cards USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Alternative: HNSW index (better recall, more memory intensive)
-- CREATE INDEX idx_cards_embedding_hnsw
-- ON cards USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Helpful view for card analysis
CREATE VIEW card_stats AS
SELECT
    COUNT(*) as total_cards,
    COUNT(DISTINCT set_code) as total_sets,
    COUNT(DISTINCT name) as unique_names,
    COUNT(embedding) as cards_with_embeddings
FROM cards;
```

### Migration Script for Existing Database

```sql
-- migration_add_vectors.sql
-- Run this if you already have cards loaded

BEGIN;

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column
ALTER TABLE cards ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- After running generate_embeddings.py, create the index:
-- CREATE INDEX idx_cards_embedding_ivfflat
-- ON cards USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMIT;
```

---

## 3. FastAPI Backend with Vector Search

### Backend: `api_server.py`

```python
#!/usr/bin/env python3
"""
FastAPI backend for MTG card vector search and visualization.
Provides endpoints for semantic search, similarity queries, and data for visualization.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from openai import OpenAI
import os

app = FastAPI(title="MTG Vector API", version="1.0.0")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}

OPENAI_CLIENT = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# Models
class Card(BaseModel):
    id: str
    name: str
    mana_cost: Optional[str]
    cmc: Optional[float]
    type_line: Optional[str]
    oracle_text: Optional[str]
    colors: Optional[List[str]]
    color_identity: Optional[List[str]]
    rarity: Optional[str]
    set_code: Optional[str]
    released_at: Optional[str]
    data: Dict[str, Any]


class SimilarCard(Card):
    similarity: float
    distance: float


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class VisualizationPoint(BaseModel):
    id: str
    name: str
    x: float
    y: float
    color: Optional[List[str]]
    type_line: Optional[str]
    rarity: Optional[str]


# Database helpers
def get_db():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def generate_query_embedding(text: str) -> List[float]:
    """Generate embedding for search query."""
    response = OPENAI_CLIENT.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )
    return response.data[0].embedding


# Endpoints

@app.get("/")
def root():
    """API health check."""
    return {"status": "ok", "message": "MTG Vector API"}


@app.get("/api/stats")
def get_stats():
    """Get database statistics."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_cards,
                    COUNT(DISTINCT set_code) as total_sets,
                    COUNT(embedding) as cards_with_embeddings,
                    COUNT(DISTINCT type_line) as unique_types
                FROM cards
            """)
            stats = cur.fetchone()

            return stats


@app.get("/api/cards", response_model=List[Card])
def search_cards(
    q: Optional[str] = None,
    type: Optional[str] = None,
    color: Optional[str] = None,
    set_code: Optional[str] = None,
    limit: int = Query(50, le=500)
):
    """
    Search cards by text, type, color, or set.
    Traditional search (not vector-based).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            query = "SELECT * FROM cards WHERE 1=1"
            params = []

            if q:
                query += " AND (name ILIKE %s OR oracle_text ILIKE %s)"
                params.extend([f"%{q}%", f"%{q}%"])

            if type:
                query += " AND type_line ILIKE %s"
                params.append(f"%{type}%")

            if color:
                query += " AND %s = ANY(colors)"
                params.append(color)

            if set_code:
                query += " AND set_code = %s"
                params.append(set_code)

            query += f" LIMIT {limit}"

            cur.execute(query, params)
            return cur.fetchall()


@app.get("/api/cards/{card_id}", response_model=Card)
def get_card(card_id: str):
    """Get a specific card by ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM cards WHERE id = %s", (card_id,))
            card = cur.fetchone()

            if not card:
                raise HTTPException(status_code=404, detail="Card not found")

            return card


@app.get("/api/cards/{card_id}/similar", response_model=List[SimilarCard])
def get_similar_cards(
    card_id: str,
    limit: int = Query(20, le=100)
):
    """
    Find cards most similar to the given card using vector similarity.
    Uses cosine distance for semantic similarity.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            # Check if card exists
            cur.execute("SELECT embedding FROM cards WHERE id = %s", (card_id,))
            result = cur.fetchone()

            if not result or not result['embedding']:
                raise HTTPException(
                    status_code=404,
                    detail="Card not found or has no embedding"
                )

            # Find similar cards using vector similarity
            cur.execute("""
                SELECT
                    *,
                    embedding <#> (SELECT embedding FROM cards WHERE id = %s) as distance,
                    1 - (embedding <#> (SELECT embedding FROM cards WHERE id = %s)) as similarity
                FROM cards
                WHERE id != %s
                    AND embedding IS NOT NULL
                ORDER BY embedding <#> (SELECT embedding FROM cards WHERE id = %s)
                LIMIT %s
            """, (card_id, card_id, card_id, card_id, limit))

            return cur.fetchall()


@app.post("/api/cards/semantic-search", response_model=List[SimilarCard])
def semantic_search(request: SearchRequest):
    """
    Search cards by semantic meaning using vector similarity.
    Query can be natural language like "destroy target creature" or "draw cards".
    """
    # Generate embedding for search query
    query_embedding = generate_query_embedding(request.query)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    *,
                    embedding <#> %s::vector as distance,
                    1 - (embedding <#> %s::vector) as similarity
                FROM cards
                WHERE embedding IS NOT NULL
                ORDER BY embedding <#> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, query_embedding, request.limit))

            return cur.fetchall()


@app.get("/api/cards/visualize/projection", response_model=List[VisualizationPoint])
def get_visualization_projection(
    limit: int = Query(5000, le=10000),
    color_filter: Optional[str] = None,
    type_filter: Optional[str] = None
):
    """
    Get card embeddings projected to 2D for visualization.
    Note: In production, pre-compute projections using UMAP/t-SNE and store them.
    This endpoint returns raw data for client-side projection.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, name, colors, type_line, rarity, embedding
                FROM cards
                WHERE embedding IS NOT NULL
            """
            params = []

            if color_filter:
                query += " AND %s = ANY(colors)"
                params.append(color_filter)

            if type_filter:
                query += " AND type_line ILIKE %s"
                params.append(f"%{type_filter}%")

            query += " ORDER BY RANDOM() LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            cards = cur.fetchall()

            # Extract embeddings for dimensionality reduction
            embeddings = np.array([card['embedding'] for card in cards])

            # Simple PCA projection (for demo - use UMAP/t-SNE for production)
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2)
            projections = pca.fit_transform(embeddings)

            # Combine with card metadata
            result = []
            for i, card in enumerate(cards):
                result.append({
                    'id': card['id'],
                    'name': card['name'],
                    'x': float(projections[i][0]),
                    'y': float(projections[i][1]),
                    'colors': card['colors'],
                    'type_line': card['type_line'],
                    'rarity': card['rarity']
                })

            return result


@app.get("/api/cards/cluster/kmeans")
def get_card_clusters(
    n_clusters: int = Query(10, ge=2, le=50),
    limit: int = Query(5000, le=20000)
):
    """
    Cluster cards using K-means on embeddings.
    Returns cluster assignments and centroids.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, type_line, embedding
                FROM cards
                WHERE embedding IS NOT NULL
                ORDER BY RANDOM()
                LIMIT %s
            """, (limit,))

            cards = cur.fetchall()

            if len(cards) < n_clusters:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough cards. Need at least {n_clusters}"
                )

            # Perform clustering
            from sklearn.cluster import KMeans

            embeddings = np.array([card['embedding'] for card in cards])
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(embeddings)

            # Organize results
            clusters = {}
            for i, card in enumerate(cards):
                cluster_id = int(labels[i])
                if cluster_id not in clusters:
                    clusters[cluster_id] = []

                clusters[cluster_id].append({
                    'id': card['id'],
                    'name': card['name'],
                    'type_line': card['type_line']
                })

            return {
                'n_clusters': n_clusters,
                'clusters': clusters,
                'total_cards': len(cards)
            }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the API

```bash
# Install dependencies
pip install fastapi uvicorn scikit-learn

# Run the server
python api_server.py

# API will be available at:
# - http://localhost:8000
# - Docs: http://localhost:8000/docs
# - OpenAPI: http://localhost:8000/openapi.json
```

### Example API Calls

```bash
# Get stats
curl http://localhost:8000/api/stats

# Search cards
curl "http://localhost:8000/api/cards?q=lightning&limit=10"

# Get similar cards
curl http://localhost:8000/api/cards/{card-id}/similar?limit=20

# Semantic search
curl -X POST http://localhost:8000/api/cards/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"query": "destroy target creature", "limit": 20}'
```

---

## 4. Example Vector Search Queries

### SQL Query Examples

```sql
-- ============================================
-- Basic Vector Similarity Queries
-- ============================================

-- 1. Find 10 most similar cards to "Lightning Bolt"
SELECT
    name,
    type_line,
    oracle_text,
    1 - (embedding <#> (
        SELECT embedding FROM cards WHERE name = 'Lightning Bolt'
    )) as similarity
FROM cards
WHERE embedding IS NOT NULL
    AND name != 'Lightning Bolt'
ORDER BY embedding <#> (SELECT embedding FROM cards WHERE name = 'Lightning Bolt')
LIMIT 10;


-- 2. Find cards similar to a specific card ID
SELECT
    c2.name,
    c2.mana_cost,
    c2.type_line,
    c2.oracle_text,
    c1.embedding <#> c2.embedding as distance
FROM cards c1
CROSS JOIN cards c2
WHERE c1.id = 'target-card-uuid'
    AND c2.id != c1.id
    AND c2.embedding IS NOT NULL
ORDER BY c1.embedding <#> c2.embedding
LIMIT 20;


-- ============================================
-- Filtered Vector Searches
-- ============================================

-- 3. Find similar red cards only
WITH target AS (
    SELECT embedding FROM cards WHERE name = 'Lightning Bolt'
)
SELECT
    name,
    mana_cost,
    oracle_text,
    1 - (embedding <#> target.embedding) as similarity
FROM cards, target
WHERE embedding IS NOT NULL
    AND 'R' = ANY(colors)
    AND name != 'Lightning Bolt'
ORDER BY embedding <#> target.embedding
LIMIT 15;


-- 4. Find similar creatures with CMC <= 3
WITH target AS (
    SELECT embedding FROM cards WHERE name = 'Tarmogoyf'
)
SELECT
    name,
    cmc,
    type_line,
    oracle_text,
    1 - (embedding <#> target.embedding) as similarity
FROM cards, target
WHERE embedding IS NOT NULL
    AND type_line LIKE '%Creature%'
    AND cmc <= 3
    AND name != 'Tarmogoyf'
ORDER BY embedding <#> target.embedding
LIMIT 20;


-- ============================================
-- Distance Thresholds
-- ============================================

-- 5. Find all cards within similarity threshold (e.g., > 0.8)
WITH target AS (
    SELECT embedding FROM cards WHERE name = 'Counterspell'
)
SELECT
    name,
    oracle_text,
    1 - (embedding <#> target.embedding) as similarity
FROM cards, target
WHERE embedding IS NOT NULL
    AND 1 - (embedding <#> target.embedding) > 0.8
    AND name != 'Counterspell'
ORDER BY similarity DESC;


-- ============================================
-- Semantic Search (requires embedding generation)
-- ============================================

-- 6. Search by concept embedding (generated from text like "destroy target creature")
-- Note: You need to generate the embedding vector externally first
WITH query_embedding AS (
    SELECT '[0.123, 0.456, ...]'::vector as emb  -- Replace with actual embedding
)
SELECT
    name,
    type_line,
    oracle_text,
    1 - (embedding <#> query_embedding.emb) as similarity
FROM cards, query_embedding
WHERE embedding IS NOT NULL
ORDER BY embedding <#> query_embedding.emb
LIMIT 25;


-- ============================================
-- Multi-Card Similarity (Find cards similar to a group)
-- ============================================

-- 7. Find cards similar to average of multiple cards (e.g., combo pieces)
WITH target_cards AS (
    SELECT AVG(embedding) as avg_embedding
    FROM cards
    WHERE name IN ('Dark Ritual', 'Cabal Ritual', 'Lotus Petal')
)
SELECT
    c.name,
    c.mana_cost,
    c.oracle_text,
    1 - (c.embedding <#> tc.avg_embedding) as similarity
FROM cards c, target_cards tc
WHERE c.embedding IS NOT NULL
    AND c.name NOT IN ('Dark Ritual', 'Cabal Ritual', 'Lotus Petal')
ORDER BY c.embedding <#> tc.avg_embedding
LIMIT 20;


-- ============================================
-- Deck Similarity Analysis
-- ============================================

-- 8. Compare a deck to cards in database (find similar cards for each deck card)
WITH deck_cards AS (
    SELECT unnest(ARRAY['Sol Ring', 'Mana Crypt', 'Chrome Mox']) as card_name
),
deck_embeddings AS (
    SELECT
        dc.card_name,
        c.embedding
    FROM deck_cards dc
    JOIN cards c ON c.name = dc.card_name
    WHERE c.embedding IS NOT NULL
)
SELECT
    de.card_name as deck_card,
    c.name as similar_card,
    c.oracle_text,
    1 - (c.embedding <#> de.embedding) as similarity
FROM deck_embeddings de
CROSS JOIN cards c
WHERE c.embedding IS NOT NULL
    AND c.name != de.card_name
ORDER BY de.card_name, c.embedding <#> de.embedding
LIMIT 100;


-- ============================================
-- Clustering Queries
-- ============================================

-- 9. Find cards in same neighborhood (useful for finding card archetypes)
WITH target AS (
    SELECT embedding FROM cards WHERE name = 'Brainstorm'
),
similar_cards AS (
    SELECT id, name, embedding
    FROM cards, target
    WHERE embedding IS NOT NULL
        AND 1 - (embedding <#> target.embedding) > 0.75
)
SELECT
    sc1.name as card1,
    sc2.name as card2,
    1 - (sc1.embedding <#> sc2.embedding) as similarity
FROM similar_cards sc1
CROSS JOIN similar_cards sc2
WHERE sc1.id < sc2.id
ORDER BY similarity DESC
LIMIT 50;


-- ============================================
-- Performance Analysis
-- ============================================

-- 10. Analyze embedding coverage
SELECT
    COUNT(*) as total_cards,
    COUNT(embedding) as with_embedding,
    COUNT(*) - COUNT(embedding) as without_embedding,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as coverage_percent
FROM cards;


-- 11. Find cards without embeddings that need processing
SELECT id, name, type_line, oracle_text
FROM cards
WHERE embedding IS NULL
LIMIT 100;


-- ============================================
-- Advanced: Reverse Search (find outliers)
-- ============================================

-- 12. Find cards least similar to a target (opposite effects)
WITH target AS (
    SELECT embedding FROM cards WHERE name = 'Wrath of God'
)
SELECT
    name,
    type_line,
    oracle_text,
    embedding <#> target.embedding as distance
FROM cards, target
WHERE embedding IS NOT NULL
    AND name != 'Wrath of God'
ORDER BY embedding <#> target.embedding DESC  -- Note: DESC for least similar
LIMIT 20;


-- ============================================
-- Color Identity Similarity
-- ============================================

-- 13. Find similar cards within same color identity
WITH target AS (
    SELECT embedding, color_identity
    FROM cards
    WHERE name = 'Atraxa, Praetors'' Voice'
)
SELECT
    c.name,
    c.color_identity,
    c.type_line,
    1 - (c.embedding <#> t.embedding) as similarity
FROM cards c, target t
WHERE c.embedding IS NOT NULL
    AND c.color_identity = t.color_identity
    AND c.name != 'Atraxa, Praetors'' Voice'
ORDER BY c.embedding <#> t.embedding
LIMIT 20;


-- ============================================
-- Set Analysis
-- ============================================

-- 14. Find cards from different sets with similar mechanics
WITH target AS (
    SELECT embedding, set_code
    FROM cards
    WHERE name = 'Siege Rhino'
)
SELECT
    c.name,
    c.set_code,
    c.type_line,
    c.oracle_text,
    1 - (c.embedding <#> t.embedding) as similarity
FROM cards c, target t
WHERE c.embedding IS NOT NULL
    AND c.set_code != t.set_code
    AND c.name != 'Siege Rhino'
ORDER BY c.embedding <#> t.embedding
LIMIT 20;
```

### Using pgvector Distance Operators

```sql
-- Operator reference:
-- <#>  : Cosine distance (0 = identical, 2 = opposite) - BEST for semantic similarity
-- <=>  : L2/Euclidean distance - GOOD for spatial similarity
-- <+>  : Inner product - GOOD when embeddings are normalized

-- Convert distance to similarity (0-1 scale):
-- Cosine similarity = 1 - cosine_distance
-- Example: 1 - (embedding <#> target_embedding)
```

---

## 5. Visualization Frontend Prototype

### HTML + D3.js Prototype: `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTG Card Vector Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
            overflow: hidden;
        }

        #app {
            display: flex;
            height: 100vh;
        }

        #sidebar {
            width: 300px;
            background: #2a2a2a;
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid #444;
        }

        #visualization {
            flex: 1;
            position: relative;
        }

        h1 {
            font-size: 20px;
            margin-bottom: 20px;
            color: #4a9eff;
        }

        .control-group {
            margin-bottom: 20px;
        }

        .control-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            color: #aaa;
        }

        input[type="text"], select {
            width: 100%;
            padding: 8px;
            background: #1a1a1a;
            border: 1px solid #444;
            border-radius: 4px;
            color: #fff;
            font-size: 14px;
        }

        button {
            width: 100%;
            padding: 10px;
            background: #4a9eff;
            border: none;
            border-radius: 4px;
            color: #fff;
            font-size: 14px;
            cursor: pointer;
            margin-top: 10px;
        }

        button:hover {
            background: #3a8eef;
        }

        .stats {
            background: #333;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
            font-size: 12px;
        }

        .stats div {
            margin-bottom: 8px;
        }

        .card-tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.95);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #4a9eff;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 300px;
            font-size: 12px;
            z-index: 1000;
        }

        .card-tooltip.visible {
            opacity: 1;
        }

        .card-name {
            font-weight: bold;
            color: #4a9eff;
            margin-bottom: 8px;
        }

        .card-type {
            color: #aaa;
            margin-bottom: 8px;
        }

        .card-text {
            font-size: 11px;
            line-height: 1.4;
            color: #ddd;
        }

        .color-legend {
            margin-top: 20px;
            padding: 15px;
            background: #333;
            border-radius: 4px;
        }

        .color-legend h3 {
            font-size: 14px;
            margin-bottom: 10px;
        }

        .color-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 12px;
        }

        .color-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 18px;
            color: #4a9eff;
        }

        circle {
            cursor: pointer;
            transition: r 0.2s;
        }

        circle:hover {
            stroke: #fff;
            stroke-width: 2;
        }

        .zoom-controls {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .zoom-btn {
            width: 40px;
            height: 40px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 4px;
            color: #fff;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .zoom-btn:hover {
            background: #3a3a3a;
        }
    </style>
</head>
<body>
    <div id="app">
        <div id="sidebar">
            <h1>MTG Card Explorer</h1>

            <div class="control-group">
                <label for="search">Search Cards</label>
                <input type="text" id="search" placeholder="Enter card name...">
                <button onclick="searchCard()">Search</button>
            </div>

            <div class="control-group">
                <label for="color-filter">Filter by Color</label>
                <select id="color-filter" onchange="filterCards()">
                    <option value="">All Colors</option>
                    <option value="W">White</option>
                    <option value="U">Blue</option>
                    <option value="B">Black</option>
                    <option value="R">Red</option>
                    <option value="G">Green</option>
                    <option value="">Colorless</option>
                </select>
            </div>

            <div class="control-group">
                <label for="type-filter">Filter by Type</label>
                <select id="type-filter" onchange="filterCards()">
                    <option value="">All Types</option>
                    <option value="Creature">Creature</option>
                    <option value="Instant">Instant</option>
                    <option value="Sorcery">Sorcery</option>
                    <option value="Enchantment">Enchantment</option>
                    <option value="Artifact">Artifact</option>
                    <option value="Planeswalker">Planeswalker</option>
                    <option value="Land">Land</option>
                </select>
            </div>

            <button onclick="loadVisualization()">Load Visualization</button>
            <button onclick="resetView()">Reset View</button>

            <div class="stats" id="stats">
                <div>Total Cards: <span id="total-cards">0</span></div>
                <div>Displayed: <span id="displayed-cards">0</span></div>
                <div>Selected: <span id="selected-card">None</span></div>
            </div>

            <div class="color-legend">
                <h3>Color Legend</h3>
                <div class="color-item">
                    <div class="color-dot" style="background: #F0E68C;"></div>
                    <span>White</span>
                </div>
                <div class="color-item">
                    <div class="color-dot" style="background: #1E90FF;"></div>
                    <span>Blue</span>
                </div>
                <div class="color-item">
                    <div class="color-dot" style="background: #333;"></div>
                    <span>Black</span>
                </div>
                <div class="color-item">
                    <div class="color-dot" style="background: #DC143C;"></div>
                    <span>Red</span>
                </div>
                <div class="color-item">
                    <div class="color-dot" style="background: #228B22;"></div>
                    <span>Green</span>
                </div>
                <div class="color-item">
                    <div class="color-dot" style="background: #FFD700;"></div>
                    <span>Multicolor</span>
                </div>
                <div class="color-item">
                    <div class="color-dot" style="background: #888;"></div>
                    <span>Colorless</span>
                </div>
            </div>
        </div>

        <div id="visualization">
            <div class="loading" id="loading">Loading cards...</div>
            <svg id="svg"></svg>
            <div class="card-tooltip" id="tooltip">
                <div class="card-name"></div>
                <div class="card-type"></div>
                <div class="card-text"></div>
            </div>
            <div class="zoom-controls">
                <button class="zoom-btn" onclick="zoomIn()">+</button>
                <button class="zoom-btn" onclick="zoomOut()">−</button>
            </div>
        </div>
    </div>

    <script>
        // Configuration
        const API_BASE = 'http://localhost:8000';
        const POINT_RADIUS = 4;
        const HIGHLIGHT_RADIUS = 8;

        // State
        let allCards = [];
        let displayedCards = [];
        let selectedCard = null;
        let svg, g, zoom;

        // Color mapping for MTG colors
        const colorMap = {
            'W': '#F0E68C',
            'U': '#1E90FF',
            'B': '#333',
            'R': '#DC143C',
            'G': '#228B22',
            'multicolor': '#FFD700',
            'colorless': '#888'
        };

        function getCardColor(card) {
            if (!card.colors || card.colors.length === 0) {
                return colorMap.colorless;
            }
            if (card.colors.length > 1) {
                return colorMap.multicolor;
            }
            return colorMap[card.colors[0]] || colorMap.colorless;
        }

        // Initialize visualization
        function initVisualization() {
            const container = document.getElementById('visualization');
            const width = container.clientWidth;
            const height = container.clientHeight;

            svg = d3.select('#svg')
                .attr('width', width)
                .attr('height', height);

            g = svg.append('g');

            // Setup zoom
            zoom = d3.zoom()
                .scaleExtent([0.5, 10])
                .on('zoom', (event) => {
                    g.attr('transform', event.transform);
                });

            svg.call(zoom);
        }

        // Load and display cards
        async function loadVisualization() {
            document.getElementById('loading').style.display = 'block';

            try {
                const colorFilter = document.getElementById('color-filter').value;
                const typeFilter = document.getElementById('type-filter').value;

                let url = `${API_BASE}/api/cards/visualize/projection?limit=5000`;
                if (colorFilter) url += `&color_filter=${colorFilter}`;
                if (typeFilter) url += `&type_filter=${typeFilter}`;

                const response = await fetch(url);
                allCards = await response.json();
                displayedCards = allCards;

                renderVisualization();
                updateStats();
            } catch (error) {
                console.error('Error loading visualization:', error);
                alert('Error loading cards. Make sure the API server is running.');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        function renderVisualization() {
            const container = document.getElementById('visualization');
            const width = container.clientWidth;
            const height = container.clientHeight;

            // Calculate scales
            const xExtent = d3.extent(displayedCards, d => d.x);
            const yExtent = d3.extent(displayedCards, d => d.y);

            const xScale = d3.scaleLinear()
                .domain(xExtent)
                .range([50, width - 50]);

            const yScale = d3.scaleLinear()
                .domain(yExtent)
                .range([50, height - 50]);

            // Clear previous visualization
            g.selectAll('*').remove();

            // Render points
            const circles = g.selectAll('circle')
                .data(displayedCards)
                .enter()
                .append('circle')
                .attr('cx', d => xScale(d.x))
                .attr('cy', d => yScale(d.y))
                .attr('r', POINT_RADIUS)
                .attr('fill', d => getCardColor(d))
                .attr('opacity', 0.7)
                .on('mouseover', showTooltip)
                .on('mouseout', hideTooltip)
                .on('click', selectCard);

            // Add entrance animation
            circles
                .attr('opacity', 0)
                .transition()
                .duration(500)
                .attr('opacity', 0.7);
        }

        function showTooltip(event, card) {
            const tooltip = document.getElementById('tooltip');

            tooltip.querySelector('.card-name').textContent = card.name;
            tooltip.querySelector('.card-type').textContent = card.type_line || 'Unknown Type';
            tooltip.querySelector('.card-text').textContent =
                card.oracle_text || 'No text available';

            tooltip.style.left = (event.pageX + 15) + 'px';
            tooltip.style.top = (event.pageY + 15) + 'px';
            tooltip.classList.add('visible');

            // Highlight point
            d3.select(event.target)
                .transition()
                .duration(200)
                .attr('r', HIGHLIGHT_RADIUS);
        }

        function hideTooltip(event) {
            document.getElementById('tooltip').classList.remove('visible');

            // Reset point size if not selected
            if (!selectedCard || event.target.__data__.id !== selectedCard.id) {
                d3.select(event.target)
                    .transition()
                    .duration(200)
                    .attr('r', POINT_RADIUS);
            }
        }

        async function selectCard(event, card) {
            selectedCard = card;
            document.getElementById('selected-card').textContent = card.name;

            // Highlight selected card
            g.selectAll('circle')
                .attr('r', POINT_RADIUS)
                .attr('opacity', 0.3);

            d3.select(event.target)
                .attr('r', HIGHLIGHT_RADIUS)
                .attr('opacity', 1);

            // Fetch and highlight similar cards
            try {
                const response = await fetch(`${API_BASE}/api/cards/${card.id}/similar?limit=20`);
                const similarCards = await response.json();
                const similarIds = new Set(similarCards.map(c => c.id));

                g.selectAll('circle')
                    .filter(d => similarIds.has(d.id))
                    .attr('opacity', 0.8)
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 1);
            } catch (error) {
                console.error('Error loading similar cards:', error);
            }
        }

        async function searchCard() {
            const query = document.getElementById('search').value;
            if (!query) return;

            try {
                const response = await fetch(`${API_BASE}/api/cards?q=${query}&limit=1`);
                const cards = await response.json();

                if (cards.length > 0) {
                    const card = cards[0];

                    // Find card in visualization
                    const visualCard = displayedCards.find(c => c.id === card.id);
                    if (visualCard) {
                        // Zoom to card
                        const container = document.getElementById('visualization');
                        const width = container.clientWidth;
                        const height = container.clientHeight;

                        const transform = d3.zoomIdentity
                            .translate(width / 2, height / 2)
                            .scale(2)
                            .translate(-visualCard.x, -visualCard.y);

                        svg.transition()
                            .duration(750)
                            .call(zoom.transform, transform);

                        // Highlight card
                        setTimeout(() => {
                            const circle = g.selectAll('circle')
                                .filter(d => d.id === card.id);
                            selectCard({ target: circle.node() }, visualCard);
                        }, 750);
                    } else {
                        alert('Card found but not in current visualization. Try adjusting filters.');
                    }
                } else {
                    alert('Card not found');
                }
            } catch (error) {
                console.error('Error searching card:', error);
            }
        }

        function filterCards() {
            loadVisualization();
        }

        function resetView() {
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity);

            g.selectAll('circle')
                .attr('r', POINT_RADIUS)
                .attr('opacity', 0.7)
                .attr('stroke', 'none');

            selectedCard = null;
            document.getElementById('selected-card').textContent = 'None';
        }

        function zoomIn() {
            svg.transition().call(zoom.scaleBy, 1.3);
        }

        function zoomOut() {
            svg.transition().call(zoom.scaleBy, 0.7);
        }

        function updateStats() {
            document.getElementById('total-cards').textContent = allCards.length.toLocaleString();
            document.getElementById('displayed-cards').textContent = displayedCards.length.toLocaleString();
        }

        // Initialize on load
        window.addEventListener('load', () => {
            initVisualization();
            loadVisualization();
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            const container = document.getElementById('visualization');
            const width = container.clientWidth;
            const height = container.clientHeight;

            d3.select('#svg')
                .attr('width', width)
                .attr('height', height);

            renderVisualization();
        });
    </script>
</body>
</html>
```

### Running the Visualization

```bash
# 1. Start the API server
python api_server.py

# 2. Serve the HTML file
# Option A: Python simple server
python -m http.server 8080

# Option B: Use any static file server
# Then open: http://localhost:8080/index.html
```

---

## Next Steps

### Implementation Checklist

1. **Set up vector support:**
   ```bash
   docker-compose up -d
   docker exec -it vector-mtg-postgres psql -U postgres -d vector_mtg -f schema_with_vectors.sql
   ```

2. **Generate embeddings:**
   ```bash
   pip install -r requirements.txt
   python generate_embeddings.py
   ```

3. **Start the API:**
   ```bash
   pip install fastapi uvicorn scikit-learn
   python api_server.py
   ```

4. **Launch visualization:**
   ```bash
   python -m http.server 8080
   # Open http://localhost:8080/index.html
   ```

### Performance Optimization Tips

- Use UMAP/t-SNE for better 2D projections (pre-compute and cache)
- Consider materialized views for common queries
- Add Redis caching for API responses
- Implement pagination for large result sets
- Use WebGL for rendering 10K+ points (via deck.gl or regl)

### Future Enhancements

- Add card images to tooltips (using Scryfall image URLs)
- Implement deck builder with similarity recommendations
- Add temporal analysis (card power creep over time)
- Create cluster naming using LLMs
- Build mobile-responsive UI
- Add export functionality (CSV, JSON)
