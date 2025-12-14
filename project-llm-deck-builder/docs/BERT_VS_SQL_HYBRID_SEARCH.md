# BERT vs SQL: Hybrid Search Architecture

## Overview

This document explains the hybrid search architecture used in the MTG Vector Cube project, combining BERT-based semantic embeddings with traditional SQL filtering for optimal search performance and accuracy.

## Table of Contents

- [BERT Embeddings vs Relational Database](#bert-embeddings-vs-relational-database)
- [Real MTG Examples](#real-mtg-examples)
- [The Hybrid Pipeline](#the-hybrid-pipeline)
- [Implementation](#implementation)
- [Performance Considerations](#performance-considerations)
- [When to Use Each Approach](#when-to-use-each-approach)

---

## BERT Embeddings vs Relational Database

### Traditional Relational Database (SQL)

**How it works:**
```sql
-- Find cards with "draw" in the text
SELECT * FROM cards WHERE oracle_text ILIKE '%draw%';

-- Find creatures with power >= 5
SELECT * FROM cards WHERE type_line LIKE '%Creature%' AND power >= 5;

-- Exact keyword match
SELECT * FROM cards WHERE 'Flying' = ANY(keywords);
```

**Strengths:**
- **Exact matching** - Perfect for structured queries
- **Blazing fast** - Indexed lookups in microseconds
- **Precise filtering** - "Show me all red creatures with CMC exactly 3"
- **Aggregations** - Count, sum, group by
- **Complex logic** - Multiple conditions with AND/OR
- **Guaranteed results** - Deterministic, repeatable

**Weaknesses:**
- **Literal matching only** - Misses synonyms and related concepts
- **No semantic understanding** - Doesn't understand meaning
- **Keyword dependent** - User must know exact terms
- **Brittle** - Typos break searches
- **No similarity ranking** - Results are binary (match or no match)

### BERT Embeddings (Vector Search)

**How it works:**
```python
# User query: "cards that let me cheat big creatures into play"
query_embedding = model.encode("cards that let me cheat big creatures into play")
# Find cards with similar embeddings (cosine similarity)
similar_cards = vector_search(query_embedding, top_k=10)
```

**Strengths:**
- **Semantic understanding** - Understands meaning, not just keywords
- **Fuzzy matching** - Finds related concepts, synonyms, paraphrases
- **Similarity ranking** - Returns results sorted by relevance
- **Natural language queries** - Users describe what they want
- **Robust to variation** - Typos and different phrasings still work
- **Discovers unexpected matches** - Finds cards you didn't know to search for

**Weaknesses:**
- **Slower** - Vector similarity calculations take milliseconds
- **Approximate** - May return irrelevant results
- **Not deterministic** - Results can vary slightly
- **Harder to debug** - "Why did it return this card?"
- **No precise filtering** - Can't do "CMC exactly 3"
- **Resource intensive** - Requires embeddings storage and computation

---

## Real MTG Examples

### Example 1: Finding Card Draw

**SQL (Relational):**
```sql
SELECT * FROM cards WHERE oracle_text ILIKE '%draw%';
```

**Returns:**
- ✅ "Draw three cards"
- ✅ "You may draw a card"
- ❌ **Misses**: "Look at the top five cards of your library, put two into your hand" (no "draw" keyword)
- ❌ **Misses**: "Reveal cards until you reveal a creature card, put it into your hand" (filtering/selection, not "draw")
- ❌ **Misses**: "Each player's hand size is increased by two" (card advantage, but no "draw")

**BERT (Semantic):**
```python
query = "cards that give me more cards"
```

**Returns:**
- ✅ "Draw three cards" (exact match)
- ✅ "Look at the top five, put two into your hand" (selection effect)
- ✅ "Reveal until creature, put into hand" (tutoring/card advantage)
- ✅ "Each player's hand size is increased" (card advantage)
- ❌ **Might return**: "Gain 3 life" (false positive - "gain" sounds like "get more")

### Example 2: Finding Ramp Cards

**User wants:** "Cards that help me get more mana early"

**SQL approach:**
```sql
-- User has to know specific keywords
SELECT * FROM cards WHERE
  oracle_text ILIKE '%add%mana%' OR
  oracle_text ILIKE '%search your library for a land%' OR
  oracle_text ILIKE '%put a land%onto the battlefield%' OR
  type_line ILIKE '%land%' AND oracle_text ILIKE '%enters the battlefield%tap%';
```
You have to think of every possible phrasing!

**BERT approach:**
```python
query = "get more mana early game ramp"
# Automatically finds:
# - "Add {G}{G}{G}" (mana generation)
# - "Search for a Forest, put it onto battlefield" (land ramp)
# - "Whenever a land enters, add {1}" (mana multiplication)
# - "Lands enter untapped" (tempo advantage)
# All ranked by similarity!
```

### Example 3: Finding Combo Pieces

**User wants:** "Cards that untap permanents"

**SQL:**
```sql
SELECT * FROM cards WHERE oracle_text ILIKE '%untap%';
```

**Finds:**
- ✅ "Untap target permanent"
- ❌ **Misses**: "Return target permanent to its owner's hand, then they may put it onto the battlefield" (functionally untaps)
- ❌ **Misses**: "Exile target permanent, return it to battlefield" (blink effects untap)
- ❌ **Includes**: "Permanents don't untap during their controller's untap step" (OPPOSITE meaning!)

**BERT:**
```python
query = "untap my permanents to reuse them"
```

**Finds:**
- ✅ "Untap target permanent"
- ✅ Blink effects (flicker/exile+return)
- ✅ Bounce effects (return to hand, replay)
- ✅ **Correctly excludes**: "Permanents don't untap" (opposite semantic meaning)

### Example 4: Finding Protection

**User wants:** "Cards that protect my creatures from removal"

**SQL:**
- You'd need dozens of queries: indestructible, hexproof, shroud, protection, regenerate, exile then return, phase out, make a copy first...
- Many false positives from "destroy" (removal spells vs protection)

**BERT:**
```python
query = "protect my creatures from removal spells"
```

**Finds:**
- Indestructible grants
- Hexproof/shroud
- Counterspells (context: protecting creatures)
- "Regenerate target creature"
- "Creatures you control have ward {2}"
- "Sacrifice a creature: it gains indestructible"

All without explicitly listing every protection keyword!

---

## The Hybrid Pipeline

### Why Combine BERT and SQL?

The optimal approach uses **BERT first, then SQL filtering** on the results.

### Step 1: BERT Generates Vector (User Query)

```python
# User searches: "cards that give me card draw when I play artifacts"
user_query = "cards that give me card draw when I play artifacts"

# BERT/sentence-transformers converts text to vector
embedding = bert_model.encode(user_query)
# Result: [0.234, -0.891, 0.445, ..., 0.123]  (384 dimensions)
```

### Step 2: Vector Search in PostgreSQL

```sql
-- Find cards with similar embeddings using pgvector
SELECT
    id,
    name,
    oracle_text,
    type_line,
    mana_value,
    colors,
    -- Calculate cosine similarity between query embedding and card embeddings
    1 - (embedding <=> '[0.234, -0.891, 0.445, ...]') AS similarity
FROM cards
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.234, -0.891, 0.445, ...]'  -- cosine distance
LIMIT 100;  -- Get top 100 most similar cards
```

**What happens here:**
- pgvector uses HNSW index (super fast approximate nearest neighbor search)
- Returns top 100 cards ranked by semantic similarity
- Takes ~5-50ms depending on dataset size
- Returns cards like: Sram, Jhoira, Vedalken Archmage, Riddlesmith, etc.

**Result set at this point:**
```
id     | name                          | similarity | colors | mana_value
-------|-------------------------------|------------|--------|------------
a1b2   | Sram, Senior Edificer         | 0.89       | [W]    | 2
c3d4   | Jhoira, Weatherlight Captain  | 0.87       | [U,R]  | 4
e5f6   | Vedalken Archmage             | 0.85       | [U]    | 4
g7h8   | Riddlesmith                   | 0.83       | [U]    | 2
...    | (96 more cards)               | ...        | ...    | ...
```

### Step 3: SQL Filters Applied to Results

Now the user adds filters:
```python
filters = {
    "colors": ["U", "W"],      # Only blue and/or white
    "cmc_max": 3,              # CMC 3 or less
    "not_keywords": ["Cycling"] # Exclude cards with cycling
}
```

**SQL filters the BERT results:**

```sql
-- Take the top 100 from BERT, then apply SQL filters
WITH semantic_matches AS (
    SELECT
        id,
        name,
        oracle_text,
        type_line,
        mana_value,
        colors,
        keywords,
        1 - (embedding <=> '[0.234, -0.891, 0.445, ...]') AS similarity
    FROM cards
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> '[0.234, -0.891, 0.445, ...]'
    LIMIT 100  -- BERT: top 100 semantic matches
)
SELECT *
FROM semantic_matches
WHERE
    -- SQL filters applied to BERT results:
    mana_value <= 3                          -- CMC filter
    AND colors <@ ARRAY['U', 'W']::text[]    -- Color identity subset
    AND NOT ('Cycling' = ANY(keywords))      -- Keyword exclusion
ORDER BY similarity DESC;  -- Keep BERT's relevance ranking
```

**Final filtered results:**
```
id     | name                  | similarity | colors | mana_value
-------|-----------------------|------------|--------|------------
a1b2   | Sram, Senior Edificer | 0.89       | [W]    | 2
g7h8   | Riddlesmith           | 0.83       | [U]    | 2
i9j0   | Etherium Sculptor     | 0.79       | [U]    | 2
```

---

## Implementation

### Complete Python Implementation

```python
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor

class MTGCardSearch:
    def __init__(self):
        self.bert_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = psycopg2.connect("postgresql://...")

    def search(self, query: str, filters: dict = None) -> list:
        """
        Hybrid search: BERT for semantic matching, SQL for filtering

        Args:
            query: Natural language search query
            filters: Dict with optional keys:
                - colors: List of color codes (e.g., ['U', 'W'])
                - cmc_min: Minimum mana value
                - cmc_max: Maximum mana value
                - type_line: Card type to filter (e.g., 'Creature')
                - keywords: List of keywords that must be present
                - not_keywords: List of keywords to exclude

        Returns:
            List of card dictionaries with similarity scores
        """

        # STEP 1: Convert query to vector using BERT
        query_embedding = self.bert_model.encode(query)

        # Convert numpy array to PostgreSQL format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # STEP 2: Build SQL query with BERT vector search
        sql = """
            WITH semantic_matches AS (
                SELECT
                    id, name, oracle_text, type_line,
                    mana_value, colors, keywords,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM cards
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 100  -- BERT: Get top 100 semantic matches
            )
            SELECT * FROM semantic_matches
            WHERE 1=1  -- Base condition
        """

        params = [embedding_str, embedding_str]

        # STEP 3: Add SQL filters dynamically
        if filters:
            if 'colors' in filters:
                sql += " AND colors <@ %s::text[]"
                params.append(filters['colors'])

            if 'cmc_max' in filters:
                sql += " AND mana_value <= %s"
                params.append(filters['cmc_max'])

            if 'cmc_min' in filters:
                sql += " AND mana_value >= %s"
                params.append(filters['cmc_min'])

            if 'type_line' in filters:
                sql += " AND type_line ILIKE %s"
                params.append(f"%{filters['type_line']}%")

            if 'keywords' in filters:
                # Cards that have ANY of these keywords
                sql += " AND keywords && %s::text[]"
                params.append(filters['keywords'])

            if 'not_keywords' in filters:
                # Cards that DON'T have any of these keywords
                sql += " AND NOT (keywords && %s::text[])"
                params.append(filters['not_keywords'])

        # Keep BERT's relevance ranking
        sql += " ORDER BY similarity DESC LIMIT 20"

        # STEP 4: Execute the combined query
        with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()

        return results


# Usage example:
search_engine = MTGCardSearch()

results = search_engine.search(
    query="draw cards when I cast artifacts",  # BERT understands this semantically
    filters={
        "colors": ["U", "W"],     # SQL: Only blue/white
        "cmc_max": 4,             # SQL: CMC 4 or less
        "type_line": "Creature",  # SQL: Only creatures
    }
)

for card in results:
    print(f"{card['name']} (similarity: {card['similarity']:.2f})")
    print(f"  {card['oracle_text'][:100]}...")
```

### PostgreSQL Execution Flow

```sql
-- The WITH clause (CTE) runs FIRST
WITH semantic_matches AS (
    -- This is BERT's work: vector similarity search
    SELECT id, name, ...,
           1 - (embedding <=> '[...]') AS similarity
    FROM cards
    ORDER BY embedding <=> '[...]'  -- Uses HNSW index!
    LIMIT 100
)
-- Then SQL filters run on the CTE results
SELECT * FROM semantic_matches
WHERE mana_value <= 3
  AND colors <@ ARRAY['U','W']
ORDER BY similarity DESC;
```

**Execution plan:**
1. **Index scan** on HNSW vector index (finds 100 nearest neighbors) - ~10ms
2. **Filter** the 100 rows with SQL predicates - ~0.1ms
3. **Sort** by similarity (already mostly sorted) - ~0.1ms
4. **Return** final ~5-20 results

---

## Performance Considerations

### Option 1: BERT First, SQL Second (CORRECT ✅)

```python
# 1. BERT narrows semantic space (100k cards → 100 cards)
semantic_candidates = vector_search(query_embedding, limit=100)

# 2. SQL filters the small result set (100 → 5 cards)
filtered_results = sql_filter(semantic_candidates, filters)
```

**Performance:**
- BERT vector search: ~10-50ms (uses HNSW index, very efficient)
- SQL filtering 100 rows: ~1ms (tiny dataset, instant)
- **Total: ~11-51ms**

**Advantages:**
- BERT finds semantically relevant cards first
- SQL only processes 100 rows (tiny dataset, blazing fast)
- Results are ranked by semantic relevance
- You get the most relevant cards that match filters

### Option 2: SQL First, BERT Second (INEFFICIENT ❌)

```python
# 1. SQL filters down (100k cards → 10k cards matching filters)
sql_matches = db.query("SELECT * FROM cards WHERE colors <@ ['U','W'] AND mana_value <= 3")

# 2. Calculate BERT similarity for all 10k cards
for card in sql_matches:  # 10,000 iterations!
    similarity = cosine_similarity(query_embedding, card.embedding)
    card.similarity = similarity

# 3. Sort by similarity
results = sorted(sql_matches, key=lambda x: x.similarity, reverse=True)[:10]
```

**Performance:**
- SQL filter: ~50-200ms (scanning potentially large table)
- BERT similarity for 10k cards: ~500-2000ms (calculating cosine similarity 10k times)
- **Total: ~550-2200ms** (10-40x slower!)

**Disadvantages:**
- Wastes time calculating similarity for irrelevant cards
- Can't leverage HNSW index efficiently
- Much slower overall

### Visual Flow Diagram

```
User Query: "draw cards when I cast artifacts"
                    ↓
         [BERT Encoder Model]
                    ↓
      Vector: [0.234, -0.891, ...]
                    ↓
         [PostgreSQL + pgvector]
                    ↓
      ┌─────────────────────────┐
      │  HNSW Index Search      │
      │  (100,000 → 100 cards)  │ ← BERT's job
      │  ~10-50ms               │
      └─────────────────────────┘
                    ↓
            100 candidates
            [Sram, Jhoira,
             Vedalken Archmage,
             Riddlesmith, ...]
                    ↓
      ┌─────────────────────────┐
      │  SQL WHERE Filters      │
      │  (100 → 8 cards)        │ ← SQL's job
      │  colors, CMC, type, etc │
      │  ~0.1-1ms               │
      └─────────────────────────┘
                    ↓
          Final 8 results
          [Sram (0.89),
           Riddlesmith (0.83),
           Etherium Sculptor (0.79)]
```

---

## When to Use Each Approach

### Use Relational DB (SQL) for:

- ✅ **Exact filtering**: "Red creatures with CMC 3"
- ✅ **Structured queries**: "Cards printed in 2024"
- ✅ **Aggregations**: "How many cards have flying?"
- ✅ **Precise logic**: "Creatures with power > toughness"
- ✅ **Known keywords**: "Cards with 'Storm' keyword"
- ✅ **Faceted search**: Filter by color, type, rarity, set

### Use BERT Embeddings for:

- ✅ **Semantic search**: "Cards that let me sacrifice creatures for value"
- ✅ **Natural language**: "Budget removal for Commander"
- ✅ **Fuzzy matching**: "Find cards similar to Sol Ring"
- ✅ **Discovery**: "Cards that synergize with discard themes"
- ✅ **Concept search**: "Political cards for multiplayer"
- ✅ **Similarity ranking**: "Most similar combo pieces to Thassa's Oracle"

### Use Hybrid Approach (Best!) for:

```python
def search_cards(query, filters=None):
    # Step 1: Semantic search with BERT
    embedding = bert_model.encode(query)
    semantic_results = vector_search(embedding, top_k=100)

    # Step 2: Filter with SQL for exact requirements
    if filters:
        results = sql_filter(semantic_results,
            colors=filters.colors,
            cmc_range=filters.cmc_range,
            type_line=filters.type_line)

    return results
```

**Example query:**
```python
search_cards(
    query="ramp spells that find lands",  # Semantic (BERT)
    filters={
        "colors": ["G"],           # Exact (SQL)
        "cmc_range": [1, 3],       # Exact (SQL)
        "type_line": "Sorcery"     # Exact (SQL)
    }
)
```

This gives you:
- BERT's semantic understanding ("ramp spells that find lands")
- SQL's precise filtering (green sorceries, CMC 1-3)
- Best of both worlds!

---

## Why Not Just Use SQL for Everything?

**Without BERT, you'd need something like:**

```sql
SELECT * FROM cards WHERE
  -- Try to match "draw cards when I cast artifacts"
  (oracle_text ILIKE '%draw%' AND
   oracle_text ILIKE '%artifact%' AND
   oracle_text ILIKE '%cast%')
  OR
  (oracle_text ILIKE '%draw%' AND
   oracle_text ILIKE '%artifact%' AND
   oracle_text ILIKE '%spell%')
  OR
  (oracle_text ILIKE '%draw%' AND
   oracle_text ILIKE '%artifact%' AND
   oracle_text ILIKE '%play%')
  -- ... you'd need dozens more OR clauses!

  -- Plus you'd miss:
  -- "Whenever you cast a noncreature spell, if it's an artifact, draw a card"
  --   (uses "noncreature spell" instead of "artifact spell")
  -- "Whenever an artifact enters the battlefield under your control, draw a card"
  --   (no "cast" keyword, but same effect!)
```

BERT automatically understands all these variations without you listing them!

---

## Summary

### BERT's Job:

- Understand semantic meaning
- Find conceptually similar cards
- Narrow 100,000 cards → 100 candidates
- Use HNSW index for speed

### SQL's Job:

- Apply exact filters to the 100 candidates
- Filter by colors, CMC, type, keywords, etc.
- Narrow 100 candidates → 5-20 final results
- Lightning fast on small dataset

### Why This Order:

- BERT is good at fuzzy matching (semantic)
- SQL is good at exact matching (structured)
- Processing 100 rows with SQL is instant
- Best of both worlds: semantic understanding + precise control

**The key insight: BERT casts a wide semantic net, SQL refines it to exactly what you want.**

---

## Related Documentation

- [QWEN_TRAINING_FORMAT.md](./QWEN_TRAINING_FORMAT.md) - Training data format specification
- [QUICK_START.md](./QUICK_START.md) - Getting started guide
- [ADDING_NEW_DATA.md](./ADDING_NEW_DATA.md) - How to add new training data
