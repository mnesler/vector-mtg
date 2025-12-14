# Compound Query Architecture

**Query Example:** "Infinite mana combos but not in black, blue, and green"

This document explains how semantic search (BERT embeddings) combines with SQL filtering for complex queries.

---

## Query Breakdown

**User Query:** "Infinite mana combos but not in black, blue, and green"

**Components:**
1. **Semantic:** "Infinite mana combos" (needs vector search)
2. **Filter:** "not in black, blue, and green" (needs SQL WHERE clause)

---

## Order of Operations

### The Golden Rule: **BERT First, SQL Second**

**Why?**
- BERT narrows 36,111 combos → 100 semantic matches (fast with HNSW index)
- SQL filters 100 combos → 10-20 final results (instant on small dataset)
- Reverse order would be slower and less accurate

---

## Execution Flow

### Step 1: Parse User Query

```python
query = "infinite mana combos but not in black, blue, and green"

# Split into components
semantic_query = "infinite mana combos"
filters = {
    "exclude_colors": ["B", "U", "G"],  # Black, Blue, Green
}
```

**Natural Language Processing (NLP) extracts:**
- **Intent:** Find combos
- **Semantic concept:** "infinite mana"
- **Filters:** Color exclusions

---

### Step 2: Generate Query Embedding (BERT)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2', device='cuda')

# Encode only the semantic part
query_embedding = model.encode("infinite mana combos")
# Result: [0.234, -0.891, ..., 0.445]  (768 dimensions)
```

**Important:** Only the semantic part gets embedded, not the filters!

---

### Step 3: Vector Search on Combos (BERT/pgvector)

```sql
-- This runs FIRST - semantic search with HNSW index
WITH semantic_matches AS (
    SELECT
        id,
        description,
        color_identity,
        card_count,
        mana_needed,
        popularity,
        -- Cosine similarity score
        1 - (embedding <=> '[0.234, -0.891, ..., 0.445]'::vector) AS similarity
    FROM combos
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> '[0.234, -0.891, ..., 0.445]'::vector  -- Cosine distance
    LIMIT 100  -- ← BERT narrows to top 100 most similar combos
)
SELECT * FROM semantic_matches;
```

**What happens:**
- pgvector's HNSW index does approximate nearest neighbor search
- Finds 100 combos most semantically similar to "infinite mana combos"
- Takes ~10-50ms even with 36,111 total combos

**Results at this stage:**
```
similarity | id        | description                                    | color_identity
-----------|-----------|------------------------------------------------|----------------
0.92       | combo-123 | Sol Ring + Hullbreaker Horror → infinite mana  | [U]
0.91       | combo-456 | Dramatic Reversal + Isochron Scepter + rocks   | [U]
0.89       | combo-789 | Basalt Monolith + Rings of Brighthearth       | [C]
0.88       | combo-234 | Palinchron + High Tide + 7 Islands            | [U]
0.87       | combo-567 | Bloom Tender + Pemmin's Aura                   | [U, G]  ← Has green!
0.86       | combo-890 | Cabal Coffers + Deserted Temple + Rings        | [B]     ← Has black!
...
(94 more combos)
```

---

### Step 4: Apply SQL Filters (PostgreSQL)

```sql
-- This runs SECOND - filter the 100 semantic matches
WITH semantic_matches AS (
    -- ... same as above, gets 100 combos ...
)
SELECT *
FROM semantic_matches
WHERE
    -- Filter: NOT in Black, Blue, or Green
    NOT (color_identity && ARRAY['B', 'U', 'G']::text[])
    -- (The && operator checks if arrays overlap)
ORDER BY similarity DESC  -- Keep BERT's relevance ranking
LIMIT 20;
```

**What this does:**
- Filters the 100 combos from BERT
- Removes any combo that includes Black, Blue, or Green
- Keeps BERT's similarity ranking

**PostgreSQL Array Operators:**
```sql
-- && means "arrays have any common elements"
['U'] && ['B', 'U', 'G']           = TRUE   (U is in both)
['W', 'R'] && ['B', 'U', 'G']      = FALSE  (no overlap)
['U', 'G'] && ['B', 'U', 'G']      = TRUE   (U and G overlap)
```

**Final Results:**
```
similarity | id        | description                                    | color_identity
-----------|-----------|------------------------------------------------|----------------
0.89       | combo-789 | Basalt Monolith + Rings of Brighthearth       | [C]     ✓ Colorless
0.84       | combo-321 | Grim Monolith + Power Artifact                | [C]     ✓ Colorless
0.82       | combo-654 | Karn, Silver Golem + Voltaic Construct        | [C]     ✓ Colorless
0.78       | combo-987 | Kogla + Hyrax Tower Scout                     | [W, R]  ✓ White/Red only
0.75       | combo-135 | Zirda + Basalt Monolith                       | [R]     ✓ Red only
...
(10-15 more combos)
```

**Filtered out:**
- ❌ Sol Ring + Hullbreaker Horror (has Blue)
- ❌ Dramatic Reversal + rocks (has Blue)
- ❌ Palinchron combos (has Blue)
- ❌ Bloom Tender combos (has Green)
- ❌ Cabal Coffers combos (has Black)

---

## Why This Order is Optimal

### Performance Comparison

#### ❌ BAD: SQL First, BERT Second

```sql
-- Step 1: SQL filter (scans all 36,111 combos)
SELECT * FROM combos
WHERE NOT (color_identity && ARRAY['B', 'U', 'G']::text[]);
-- Results: ~5,000 combos (no Blue, Black, or Green)

-- Step 2: Calculate similarity for 5,000 combos
-- (Must compute cosine distance 5,000 times!)
-- Takes 500-1000ms
```

**Problems:**
- SQL scans entire table (36,111 rows) without index help
- Then computes 5,000 vector similarities (slow)
- Can't use HNSW index efficiently
- Total time: **500-1000ms**

---

#### ✅ GOOD: BERT First, SQL Second (Recommended)

```sql
-- Step 1: BERT/HNSW gets top 100 (uses index, super fast)
-- Takes ~10-50ms

-- Step 2: SQL filters 100 rows (instant)
-- Takes ~0.1ms
```

**Advantages:**
- HNSW index does fast approximate search
- Only filters 100 rows (tiny dataset)
- Total time: **10-50ms** (10-20x faster!)

---

## Complex Query Examples

### Example 1: "2-card infinite combos under $50 in Boros"

**Semantic:** "infinite combos"
**Filters:**
- `card_count = 2`
- `price_usd <= 50`
- `color_identity <@ ['W', 'R']` (subset of White/Red)

**Execution:**
```sql
WITH semantic_matches AS (
    SELECT *, 1 - (embedding <=> :query_vec) AS similarity
    FROM combos
    ORDER BY embedding <=> :query_vec
    LIMIT 100  -- BERT first
)
SELECT *
FROM semantic_matches
WHERE
    card_count = 2
    AND price_usd <= 50
    AND color_identity <@ ARRAY['W', 'R']::text[]
ORDER BY similarity DESC;
```

---

### Example 2: "Win conditions that don't use the combat step in Sultai"

**Semantic:** "win conditions that don't use combat"
**Filters:**
- `color_identity <@ ['B', 'U', 'G']` (Sultai colors)
- Features include "Win the game" or similar

**Execution:**
```sql
WITH semantic_matches AS (
    SELECT c.*, 1 - (c.embedding <=> :query_vec) AS similarity
    FROM combos c
    ORDER BY c.embedding <=> :query_vec
    LIMIT 100  -- BERT first
)
SELECT DISTINCT sm.*
FROM semantic_matches sm
JOIN combo_features cf ON sm.id = cf.combo_id
JOIN features f ON cf.feature_id = f.id
WHERE
    sm.color_identity <@ ARRAY['B', 'U', 'G']::text[]
    AND (
        f.name ILIKE '%win%' OR
        f.name ILIKE '%lose%' OR
        f.name ILIKE '%mill%'
    )
ORDER BY sm.similarity DESC;
```

---

### Example 3: "Cards that draw cards when artifacts enter, under 3 CMC, in white or blue"

**Semantic:** "draw cards when artifacts enter"
**Filters:**
- `cmc <= 3`
- `colors && ['W', 'U']` (contains White OR Blue)

**Execution:**
```sql
WITH semantic_matches AS (
    SELECT *, 1 - (embedding <=> :query_vec) AS similarity
    FROM cards
    ORDER BY embedding <=> :query_vec
    LIMIT 100  -- BERT first
)
SELECT *
FROM semantic_matches
WHERE
    cmc <= 3
    AND colors && ARRAY['W', 'U']::text[]
ORDER BY similarity DESC;
```

---

## Filter Types & SQL Operators

### Color Filters

```sql
-- Exactly these colors (color identity matches exactly)
color_identity = ARRAY['W', 'U']::text[]

-- Subset (color identity is within these colors)
color_identity <@ ARRAY['W', 'U', 'B']::text[]
-- Example: [W, U] is subset of [W, U, B] ✓
-- Example: [W, R] is NOT subset of [W, U, B] ✗

-- Contains any (has at least one of these colors)
color_identity && ARRAY['B']::text[]
-- Example: [B, G] contains B ✓
-- Example: [W, U] doesn't contain B ✗

-- Excludes (does NOT contain these colors)
NOT (color_identity && ARRAY['B', 'U', 'G']::text[])
-- Example: [W, R] excludes B/U/G ✓
-- Example: [W, U] excludes B/U/G ✗ (has U)
```

### Numeric Filters

```sql
-- Exact
card_count = 2

-- Range
cmc BETWEEN 1 AND 3
price_usd <= 50

-- Comparison
popularity >= 100
```

### Text Filters (Use Sparingly)

```sql
-- Exact match on tags/features
f.name = 'Infinite mana'

-- Pattern match (slower, avoid if possible)
description ILIKE '%storm%'
```

### Relational Filters

```sql
-- Combos that include a specific card
EXISTS (
    SELECT 1 FROM combo_cards cc
    WHERE cc.combo_id = combos.id
    AND cc.card_id = 'specific-card-uuid'
)

-- Combos with specific number of features
(SELECT COUNT(*) FROM combo_features cf WHERE cf.combo_id = combos.id) >= 3
```

---

## Query Optimization Rules

### Rule 1: BERT Narrows, SQL Refines
Always use BERT/vector search first to narrow to ~100 candidates, then apply SQL filters.

### Rule 2: Use LIMIT 100 on Semantic Search
100 is a sweet spot:
- Large enough to find relevant results after filtering
- Small enough for SQL to be instant
- Can adjust based on filter selectivity

### Rule 3: Keep Semantic Query Pure
Don't include filters in the embedding query:
```python
# ✓ GOOD
query_embedding = model.encode("infinite mana combos")

# ✗ BAD
query_embedding = model.encode("infinite mana combos not in black blue green")
```

The model doesn't understand "not in" well - use SQL for negation.

### Rule 4: Filter Selectivity Matters

**Highly selective filters** (eliminate many results):
- Narrow LIMIT to 50-100 on BERT search

**Non-selective filters** (eliminate few results):
- Use LIMIT 200 on BERT search to ensure good coverage

**Example:**
```python
# Very specific: "5-card combos under $10 in mono-white"
# Filters eliminate 95%+ results → LIMIT 50 is enough

# Broad: "combos in blue or red"
# Filters eliminate only 30% → LIMIT 150 for better results
```

### Rule 5: Prefer Array Operators Over Joins
```sql
-- ✓ GOOD (fast, uses GIN index)
color_identity && ARRAY['U']::text[]

-- ✗ SLOWER (requires join)
EXISTS (SELECT 1 FROM combo_colors cc WHERE cc.combo_id = combos.id AND cc.color = 'U')
```

---

## Example API Implementation

```python
class ComboSearchEngine:
    def search(self, semantic_query: str, filters: dict = None):
        """
        Hybrid semantic + SQL search

        Args:
            semantic_query: Natural language query (e.g., "infinite mana combos")
            filters: Dict of SQL filters (e.g., {"exclude_colors": ["B", "U", "G"]})
        """

        # Step 1: Generate embedding for semantic part
        query_embedding = self.model.encode(semantic_query)
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Step 2: Build SQL with BERT first, filters second
        sql = """
            WITH semantic_matches AS (
                SELECT
                    id, description, color_identity, card_count,
                    price_usd, popularity,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM combos
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 100  -- BERT narrows to 100
            )
            SELECT * FROM semantic_matches
            WHERE 1=1  -- Base condition
        """

        params = [embedding_str, embedding_str]

        # Step 3: Add filters dynamically
        if filters:
            if 'exclude_colors' in filters:
                sql += " AND NOT (color_identity && %s::text[])"
                params.append(filters['exclude_colors'])

            if 'require_colors' in filters:
                # Subset - combo must be within these colors
                sql += " AND color_identity <@ %s::text[]"
                params.append(filters['require_colors'])

            if 'card_count' in filters:
                sql += " AND card_count = %s"
                params.append(filters['card_count'])

            if 'max_price' in filters:
                sql += " AND price_usd <= %s"
                params.append(filters['max_price'])

            if 'min_popularity' in filters:
                sql += " AND popularity >= %s"
                params.append(filters['min_popularity'])

        # Step 4: Keep BERT's ranking
        sql += " ORDER BY similarity DESC LIMIT 20"

        # Step 5: Execute
        cursor.execute(sql, params)
        return cursor.fetchall()


# Usage:
engine = ComboSearchEngine()

results = engine.search(
    semantic_query="infinite mana combos",
    filters={
        "exclude_colors": ["B", "U", "G"],
        "max_price": 100,
        "card_count": 2
    }
)
```

---

## Performance Characteristics

### Typical Query Times

| Query Type | BERT Time | SQL Time | Total |
|------------|-----------|----------|-------|
| Semantic only | 10-50ms | 0ms | 10-50ms |
| Semantic + 1 filter | 10-50ms | 0.1ms | 10-50ms |
| Semantic + 3 filters | 10-50ms | 0.5ms | 10-50ms |
| Semantic + join to features | 10-50ms | 2-5ms | 15-55ms |

**Bottleneck:** BERT vector search (10-50ms) - SQL filtering is negligible

### Scaling

| Combo Count | HNSW Search | Notes |
|-------------|-------------|-------|
| 10K combos | ~10ms | Current dataset (36K) |
| 100K combos | ~20ms | 3x larger |
| 1M combos | ~50ms | Future growth |

HNSW index scales logarithmically, not linearly!

---

## Summary

### Order of Operations for "Infinite mana combos not in black, blue, green":

1. **Parse:** Extract semantic ("infinite mana") + filters (exclude B/U/G)
2. **Embed:** Convert "infinite mana combos" → 768-dim vector
3. **BERT Search:** Use HNSW index to find 100 most similar combos (~10-50ms)
4. **SQL Filter:** Remove combos with Black/Blue/Green (~0.1ms)
5. **Rank:** Return top 20, sorted by similarity

**Total Time:** ~10-50ms

### Key Principles:

✅ **BERT narrows semantically** (36K → 100)
✅ **SQL refines precisely** (100 → 20)
✅ **Keep semantic queries pure** (no filters in embedding)
✅ **Use array operators** (fast, indexed)
✅ **Preserve similarity ranking** (ORDER BY similarity)

This architecture gives you the best of both worlds: semantic understanding from BERT + precise filtering from SQL.

