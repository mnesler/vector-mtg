# Tags vs Embeddings: When to Use Each

**Core Question:** Should we embed everything or use some data as exact-match tags?

**TL;DR:** Tags are for **categorical/exact matching**, embeddings are for **semantic similarity**. Use both!

---

## Table of Contents

1. [What Are Tags?](#what-are-tags)
2. [What Are Embeddings?](#what-are-embeddings)
3. [When to Use Each](#when-to-use-each)
4. [How They Work Together](#how-they-work-together)
5. [Implementation Examples](#implementation-examples)
6. [Performance Comparison](#performance-comparison)

---

## What Are Tags?

### Definition
**Tags** are categorical labels stored as plain data (text, arrays, enums) that enable **exact matching**.

### Examples in MTG Context

#### Card Tags:
```sql
-- Colors (array of exact values)
colors = ['W', 'U']  -- White, Blue

-- Keywords (array of exact abilities)
keywords = ['Flying', 'Haste', 'Vigilance']

-- Rarity (enum)
rarity = 'Rare'  -- Common, Uncommon, Rare, Mythic

-- Card types (array)
types = ['Creature', 'Legendary']
```

#### Combo Tags:
```sql
-- Features (what the combo produces)
features = ['Infinite mana', 'Infinite storm count']

-- Color identity (exact color requirements)
color_identity = ['U', 'G']  -- Simic

-- Card count (exact number)
card_count = 2

-- Status (categorical)
status = 'ok'  -- ok, needs_review, deprecated
```

### How Tags Are Stored

```sql
CREATE TABLE combos (
    id TEXT PRIMARY KEY,
    description TEXT,

    -- Tags stored as data types
    color_identity TEXT[],           -- Array tag
    card_count INTEGER,              -- Numeric tag
    status TEXT,                     -- Text tag
    price_range TEXT                 -- Enum tag: 'budget', 'mid', 'expensive'
);

-- Junction table for many-to-many tags
CREATE TABLE combo_features (
    combo_id TEXT,
    feature_id INTEGER,              -- References features table
    PRIMARY KEY (combo_id, feature_id)
);

CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,                -- Tag value: "Infinite mana"
    category TEXT                    -- Tag category: "mana", "life", "tokens"
);
```

### How Tag Matching Works

**Exact matching with SQL WHERE clauses:**

```sql
-- Match exact color
SELECT * FROM combos WHERE color_identity = ARRAY['U', 'G'];
-- Returns ONLY Simic combos (exactly U and G)

-- Match contains color
SELECT * FROM combos WHERE 'U' = ANY(color_identity);
-- Returns any combo with Blue in it

-- Match card count
SELECT * FROM combos WHERE card_count = 2;
-- Returns ONLY 2-card combos

-- Match feature tag
SELECT * FROM combos c
JOIN combo_features cf ON c.id = cf.combo_id
JOIN features f ON cf.feature_id = f.id
WHERE f.name = 'Infinite mana';
-- Returns combos tagged with exactly "Infinite mana"
```

### Characteristics of Tags

✅ **Pros:**
- **Exact matching** - No ambiguity, perfect precision
- **Fast** - Uses B-tree or GIN indexes (microseconds)
- **Efficient storage** - Just a few bytes per tag
- **Easy to understand** - Simple SQL WHERE clauses
- **Easy to update** - Just change the value
- **Aggregatable** - Can COUNT, GROUP BY, etc.

❌ **Cons:**
- **No fuzzy matching** - "Infinite mana" ≠ "Unlimited mana"
- **No semantic understanding** - Can't find related concepts
- **Exact spelling required** - Typos break searches
- **No similarity** - Can't rank by "how similar"
- **Brittle** - Need to know exact tag values

---

## What Are Embeddings?

### Definition
**Embeddings** are high-dimensional vectors (768 floats) that capture **semantic meaning** and enable **similarity search**.

### Examples in MTG Context

```python
# Card embedding (768-dimensional vector)
"Lightning Bolt | Instant | Lightning Bolt deals 3 damage to any target."
↓ BERT model
[0.234, -0.891, 0.445, ..., 0.123]  (768 numbers)

# Similar cards have similar vectors
"Shock" → [0.221, -0.884, 0.438, ..., 0.119]  (close to Lightning Bolt)
"Giant Growth" → [0.012, 0.334, -0.677, ..., 0.891]  (far from Lightning Bolt)
```

### How Embeddings Are Stored

```sql
CREATE TABLE combos (
    id TEXT PRIMARY KEY,
    description TEXT,

    -- Embedding stored as vector type
    embedding VECTOR(768),           -- 768 floats = 3KB per combo

    CONSTRAINT check_embedding_dims CHECK (vector_dims(embedding) = 768)
);

-- HNSW index for fast approximate search
CREATE INDEX idx_combos_embedding
ON combos
USING hnsw (embedding vector_cosine_ops);
```

### How Embedding Matching Works

**Semantic similarity with vector distance:**

```sql
-- Find combos similar to "infinite mana"
SELECT
    id,
    description,
    1 - (embedding <=> :query_embedding) AS similarity
FROM combos
ORDER BY embedding <=> :query_embedding  -- Cosine distance
LIMIT 10;

-- Results ranked by similarity:
-- 0.95 - "Basalt Monolith + Rings of Brighthearth"
-- 0.92 - "Sol Ring + Hullbreaker Horror"
-- 0.89 - "Dramatic Reversal + Isochron Scepter"
-- 0.76 - "Palinchron + High Tide" (different but related)
```

### Characteristics of Embeddings

✅ **Pros:**
- **Fuzzy matching** - "Infinite mana" finds "Unlimited mana"
- **Semantic understanding** - Finds concepts, not just keywords
- **Similarity ranking** - Results sorted by relevance
- **Typo-tolerant** - "Infinte manna" still works
- **Discovers unexpected matches** - Finds related concepts you didn't think of

❌ **Cons:**
- **Approximate** - May return some irrelevant results
- **Slower** - Vector search takes milliseconds vs microseconds
- **Storage intensive** - 3KB per embedding vs bytes for tags
- **Hard to debug** - "Why did this match?" is unclear
- **Can't aggregate** - Can't COUNT or GROUP BY embeddings
- **Not exact** - Can't filter to exactly "2 cards"

---

## When to Use Each

### Decision Framework

```
Is the data categorical with discrete values?
    YES → Use TAGS
    NO → Continue

Do users need EXACT matching?
    YES → Use TAGS
    NO → Continue

Is it a numeric value (count, price, CMC)?
    YES → Use TAGS (stored as numbers)
    NO → Continue

Is it a concept/meaning/description?
    YES → Use EMBEDDINGS
    NO → Use TAGS
```

### MTG-Specific Examples

| Data | Type | Why |
|------|------|-----|
| **Colors** | TAG | Discrete values (W/U/B/R/G/C), exact matching needed |
| **Card Count** | TAG | Exact number, users want "exactly 2 cards" |
| **Price** | TAG | Numeric value, exact filtering ($10-$50) |
| **Features** | TAG | Exact outcomes ("Infinite mana"), not semantic |
| **Rarity** | TAG | Enum (Common/Uncommon/Rare/Mythic) |
| **Card Type** | TAG | Discrete categories (Creature, Instant, etc.) |
| **Format Legality** | TAG | Boolean/Enum (Legal, Banned, Restricted) |
| | | |
| **Card Description** | EMBEDDING | Natural language, semantic search needed |
| **Combo Description** | EMBEDDING | How it works, fuzzy matching helps |
| **Oracle Text** | EMBEDDING | Abilities/effects, many ways to phrase same thing |
| **Deck Theme** | EMBEDDING | Concepts like "aristocrats", "voltron", "storm" |

---

## How They Work Together

### The Hybrid Approach: BERT + Tags

**Example Query:** "2-card infinite mana combos in Boros under $50"

**Semantic Part:** "infinite mana combos"
**Tag Filters:**
- card_count = 2 (exact)
- color_identity ⊆ ['W', 'R'] (exact)
- price_usd <= 50 (exact)

```sql
WITH semantic_matches AS (
    -- EMBEDDINGS: Semantic search
    SELECT
        id, description, color_identity, card_count, price_usd,
        1 - (embedding <=> :query_embedding) AS similarity
    FROM combos
    ORDER BY embedding <=> :query_embedding
    LIMIT 100  -- Top 100 semantically similar
)
SELECT *
FROM semantic_matches
WHERE
    -- TAGS: Exact filtering
    card_count = 2
    AND color_identity <@ ARRAY['W', 'R']::text[]
    AND price_usd <= 50
ORDER BY similarity DESC;
```

**How it works:**
1. **BERT** finds combos that are semantically about "infinite mana" (fuzzy, broad)
2. **Tags** filter to exactly what the user specified (precise, narrow)
3. Best of both worlds!

---

## Implementation Examples

### Example 1: Features as Tags (Recommended)

**Scenario:** Combo features like "Infinite mana", "Win the game", etc.

**Why Tags?**
- Finite set of outcomes (~200-300 unique features)
- Users want EXACT matches: "Show me combos that win the game"
- No semantic fuzzy matching needed ("Win game" = "Win the game" exactly)
- Easy to aggregate: "How many combos produce infinite mana?"

**Schema:**
```sql
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,       -- Tag: "Infinite mana"
    category TEXT,                   -- Tag category: "mana"
    -- NO embedding column!
);

CREATE TABLE combo_features (
    combo_id TEXT REFERENCES combos(id),
    feature_id INTEGER REFERENCES features(id),
    PRIMARY KEY (combo_id, feature_id)
);

CREATE INDEX idx_features_name ON features(name);  -- B-tree index
CREATE INDEX idx_combo_features_feature_id ON combo_features(feature_id);
```

**Query:**
```sql
-- Find combos that produce "Infinite mana"
SELECT c.*
FROM combos c
JOIN combo_features cf ON c.id = cf.combo_id
JOIN features f ON cf.feature_id = f.id
WHERE f.name = 'Infinite mana';  -- Exact tag match

-- Fast: Uses B-tree index, returns in microseconds
```

**Storage:**
- Feature name: ~20 bytes
- Junction table: 8 bytes per combo-feature pair
- **Total:** ~30 bytes vs 3KB for embedding (100x smaller!)

---

### Example 2: Combo Descriptions as Embeddings (Recommended)

**Scenario:** How the combo works (description text)

**Why Embeddings?**
- Natural language descriptions
- Many ways to describe same concept
- Users use fuzzy queries: "combos that bounce and recast"
- Semantic similarity helps find related combos

**Schema:**
```sql
CREATE TABLE combos (
    id TEXT PRIMARY KEY,
    description TEXT,                -- "Cast Sol Ring, bounce with Hullbreaker..."

    -- Embed the description
    embedding VECTOR(768),

    -- Tags for filtering
    color_identity TEXT[],
    card_count INTEGER,
    price_usd NUMERIC
);

CREATE INDEX idx_combos_embedding ON combos USING hnsw (embedding vector_cosine_ops);
```

**Embedding Text:**
```python
# Generate embedding from description
combo_text = f"Cards: {card_names} | {description} | Produces: {feature_names}"
embedding = model.encode(combo_text)
```

**Query:**
```python
# User: "combos that bounce permanents to generate mana"
query_emb = model.encode("combos that bounce permanents to generate mana")

# Find similar combos
cursor.execute("""
    SELECT id, description,
           1 - (embedding <=> %s::vector) AS similarity
    FROM combos
    ORDER BY embedding <=> %s::vector
    LIMIT 10
""", (query_emb, query_emb))

# Returns:
# - Hullbreaker Horror + Sol Ring (0.92 similarity)
# - Emiel + dorks (0.87 similarity)
# - Temur Sabertooth combos (0.84 similarity)
```

---

### Example 3: Hybrid Card Search

**Scenario:** Find cards with specific abilities in certain colors

**Query:** "Cards that draw when artifacts enter, in white or blue, under 3 CMC"

```python
# Semantic part
semantic_query = "draw when artifacts enter"
query_emb = model.encode(semantic_query)

# Tag filters
filters = {
    "colors": ["W", "U"],      # Tag: exact color match
    "max_cmc": 3               # Tag: numeric filter
}
```

```sql
WITH semantic_matches AS (
    -- EMBEDDING: Semantic search
    SELECT
        id, name, oracle_text, colors, cmc,
        1 - (embedding <=> :query_emb) AS similarity
    FROM cards
    ORDER BY embedding <=> :query_emb
    LIMIT 100
)
SELECT *
FROM semantic_matches
WHERE
    -- TAGS: Exact filtering
    colors && ARRAY['W', 'U']::text[]  -- Has White OR Blue
    AND cmc <= 3
ORDER BY similarity DESC
LIMIT 20;
```

**Results:**
- Sram, Senior Edificer (White, CMC 2, similarity 0.89)
- Riddlesmith (Blue, CMC 2, similarity 0.83)
- Etherium Sculptor (Blue, CMC 2, similarity 0.79)

---

## Performance Comparison

### Tag Lookup (Exact Match)

```sql
SELECT * FROM combos
WHERE card_count = 2
AND 'U' = ANY(color_identity);
```

**Performance:**
- Uses B-tree or GIN index
- Time: **0.1-1ms** (microseconds)
- Scans: Index only (no table scan)
- Result: Exact matches

---

### Embedding Search (Semantic)

```sql
SELECT * FROM combos
ORDER BY embedding <=> :query_emb
LIMIT 100;
```

**Performance:**
- Uses HNSW index
- Time: **10-50ms** (milliseconds)
- Scans: Approximate nearest neighbors
- Result: Ranked by similarity

---

### Hybrid (BERT + Tags)

```sql
WITH semantic_matches AS (
    SELECT *, 1 - (embedding <=> :query_emb) AS similarity
    FROM combos
    ORDER BY embedding <=> :query_emb
    LIMIT 100  -- BERT: 10-50ms
)
SELECT * FROM semantic_matches
WHERE card_count = 2
AND 'U' = ANY(color_identity);  -- Tag filter: 0.1ms
-- Total: ~10-50ms (BERT dominates)
```

**Performance:**
- BERT search: 10-50ms
- Tag filtering: 0.1ms (negligible)
- **Total: ~10-50ms**

Tag filtering is so fast it's basically free!

---

## Storage Comparison

### Tags

```sql
-- Features table
id (4 bytes) + name (avg 20 bytes) + category (10 bytes)
= ~34 bytes per feature

-- Junction table
combo_id (8 bytes) + feature_id (4 bytes)
= 12 bytes per combo-feature relationship

-- Example: 36K combos × 3 features average
= 36,000 × 3 × 12 bytes
= 1.3 MB
```

---

### Embeddings

```sql
-- Combo embeddings
embedding VECTOR(768)
= 768 floats × 4 bytes
= 3,072 bytes (3 KB) per combo

-- Example: 36K combos
= 36,000 × 3 KB
= 108 MB

-- Plus HNSW index (roughly 2x size)
= 216 MB total
```

**Ratio:** Embeddings are **~160x larger** than tags

---

## Best Practices

### Use Tags For:

✅ **Categorical Data**
- Colors, rarity, card types
- Format legality (Legal/Banned)
- Combo status (OK/Needs Review)

✅ **Numeric Values**
- CMC, power, toughness
- Card count, combo price
- Popularity scores

✅ **Exact Matching Requirements**
- "Show me exactly 2-card combos"
- "Only legal in Commander"
- "Colorless only"

✅ **Aggregation Needs**
- "Count combos by color"
- "Average price by card count"
- "Group by rarity"

---

### Use Embeddings For:

✅ **Natural Language Text**
- Card oracle text
- Combo descriptions
- Strategy explanations

✅ **Fuzzy/Semantic Matching**
- "Cards that draw cards" (many phrasings)
- "Combos that win the game" (various win conditions)
- "Ramp spells" (mana acceleration concepts)

✅ **Similarity Ranking**
- "Find cards similar to Lightning Bolt"
- "Show me combos like this one"
- "Related strategies"

✅ **Concept Discovery**
- "Token generators"
- "Graveyard recursion"
- "Combo protection"

---

### Combine Both For:

✅ **Complex Queries**
```
"2-card infinite combos in Boros under $50"
    ↓
Embedding: "infinite combos"
Tags: card_count=2, colors⊆[W,R], price<=$50
```

✅ **Filtered Discovery**
```
"Budget removal spells in black"
    ↓
Embedding: "removal spells"
Tags: colors=[B], price<=$5
```

✅ **Theme-Based Deck Building**
```
"Aristocrats cards in Orzhov"
    ↓
Embedding: "sacrifice creatures for value"
Tags: colors⊆[W,B]
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Embedding Everything

```sql
-- BAD: Embedding categorical data
CREATE TABLE combos (
    card_count_embedding VECTOR(768),  -- NO! Use INTEGER
    color_embedding VECTOR(768),       -- NO! Use TEXT[]
    status_embedding VECTOR(768)       -- NO! Use TEXT
);
```

**Why bad:**
- Wastes storage (3KB vs 4 bytes)
- Slower queries (50ms vs 0.1ms)
- Loses exact matching
- Can't aggregate

---

### ❌ Mistake 2: Tagging Everything

```sql
-- BAD: Tagging free-form text
CREATE TABLE cards (
    oracle_text TEXT,
    -- Then searching with:
    -- WHERE oracle_text LIKE '%draw%'
);
```

**Why bad:**
- Misses semantic variations ("draw a card" vs "put into hand")
- Brittle keyword matching
- No similarity ranking
- Can't handle typos

---

### ❌ Mistake 3: Mixing Tags Into Embeddings

```python
# BAD: Including filter criteria in semantic query
query = "infinite mana combos not in black under $50"
embedding = model.encode(query)
```

**Why bad:**
- BERT doesn't understand "not" or "$50" well
- Pollutes semantic meaning
- Tags are better for exact filtering

**GOOD: Separate concerns**
```python
semantic_query = "infinite mana combos"
filters = {"exclude_colors": ["B"], "max_price": 50}
```

---

## Real-World Example

### Query: "Budget 2-card combos that win the game in non-blue colors"

**Decomposition:**

```python
# Semantic (embedding)
semantic = "combos that win the game"

# Tags (exact filtering)
tags = {
    "card_count": 2,                    # Exact count
    "exclude_colors": ["U"],            # Not blue
    "max_price": 20                     # Budget threshold
}
```

**SQL:**
```sql
WITH semantic_matches AS (
    -- EMBEDDING: Find win-condition combos
    SELECT c.*, 1 - (c.embedding <=> :query_emb) AS similarity
    FROM combos c
    JOIN combo_features cf ON c.id = cf.combo_id
    JOIN features f ON cf.feature_id = f.id
    WHERE f.name ILIKE '%win%'  -- Tag pre-filter for "win" features
    ORDER BY c.embedding <=> :query_emb
    LIMIT 100
)
SELECT *
FROM semantic_matches
WHERE
    -- TAGS: Exact filtering
    card_count = 2
    AND NOT (color_identity && ARRAY['U']::text[])
    AND price_usd <= 20
ORDER BY similarity DESC
LIMIT 20;
```

**Results:**
1. Heliod + Walking Ballista (W, 2 cards, $15, similarity 0.94)
2. Kiki-Jiki + Zealous Conscripts (R, 2 cards, $18, similarity 0.91)
3. Exquisite Blood + Sanguine Bond (B, 2 cards, $8, similarity 0.89)

**Why this works:**
- **Embedding** finds "win the game" semantically (includes instant wins, damage loops, etc.)
- **Tags** filter precisely (exactly 2 cards, no blue, under $20)
- **Fast** (~10-50ms total)
- **Accurate** (both semantic and precise)

---

## Summary

### Tags (Exact Matching)
- **What:** Categorical labels, enums, numbers
- **How:** SQL WHERE clauses with B-tree/GIN indexes
- **Speed:** 0.1-1ms (microseconds)
- **Storage:** Bytes
- **Use for:** Colors, counts, prices, exact values

### Embeddings (Semantic Matching)
- **What:** High-dimensional vectors from text
- **How:** Vector similarity with HNSW index
- **Speed:** 10-50ms (milliseconds)
- **Storage:** 3KB per item
- **Use for:** Descriptions, abilities, concepts

### The Hybrid Approach
**BERT narrows semantically** → **Tags filter precisely**

This gives you:
- ✅ Natural language queries
- ✅ Exact filtering
- ✅ Similarity ranking
- ✅ Fast performance
- ✅ Best of both worlds

---

## Decision Checklist

When designing your schema, ask for each field:

1. ☑️ Is it categorical/discrete? → **TAG**
2. ☑️ Is it numeric? → **TAG**
3. ☑️ Do users need exact matching? → **TAG**
4. ☑️ Is it free-form text? → **EMBEDDING**
5. ☑️ Are there multiple ways to phrase it? → **EMBEDDING**
6. ☑️ Do users search semantically? → **EMBEDDING**

**When in doubt:** Use tags for filtering, embeddings for discovery.

