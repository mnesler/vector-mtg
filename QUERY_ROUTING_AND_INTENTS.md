# Query Routing & Intent Detection

**The Problem:** User doesn't say "combo" but wants combo data.

**Example Queries:**
- "Find cards that interact well with Thassa's Oracle"
- "What works with Sol Ring?"
- "What goes in a Krenko deck?"
- "Show me cards that synergize with aristocrats strategies"

These are all asking for **relationships**, not semantic similarity!

---

## Table of Contents

1. [The Three Query Types](#the-three-query-types)
2. [Intent Detection](#intent-detection)
3. [Query Routing Architecture](#query-routing-architecture)
4. [Relationship Queries Explained](#relationship-queries-explained)
5. [Implementation Examples](#implementation-examples)

---

## The Three Query Types

### Type 1: Card Discovery (Semantic)
**User wants:** Cards with specific properties/abilities

**Examples:**
- "Show me removal spells"
- "Find cards that draw when artifacts enter"
- "Budget ramp in green"

**Strategy:** Semantic search on card embeddings
**Data source:** `cards.embedding`

```sql
-- BERT search on cards
SELECT * FROM cards
ORDER BY embedding <=> :query_embedding
LIMIT 20;
```

---

### Type 2: Combo Discovery (Semantic)
**User wants:** Combos that do something

**Examples:**
- "Infinite mana combos in Simic"
- "2-card win conditions"
- "Budget combos under $50"

**Strategy:** Semantic search on combo embeddings
**Data source:** `combos.embedding`

```sql
-- BERT search on combos
SELECT * FROM combos
ORDER BY embedding <=> :query_embedding
LIMIT 20;
```

---

### Type 3: Relationship/Synergy Queries (Graph)
**User wants:** Cards that work WITH a specific card or strategy

**Examples:**
- "What works with Thassa's Oracle?"
- "Cards that go well with Sol Ring"
- "What synergizes with aristocrats?"
- "Combo pieces for Krenko"

**Strategy:** Graph lookup through relationship tables
**Data source:** `combo_cards` + `card_synergies` tables

```sql
-- Graph traversal, NOT semantic search!
SELECT other_cards FROM combo_cards
WHERE combo_id IN (
    SELECT combo_id FROM combo_cards
    WHERE card_id = :thassas_oracle_id
);
```

**KEY DIFFERENCE:** This is a **graph/relationship query**, not a semantic search!

---

## Why Embeddings Don't Work for Synergy Queries

### ❌ WRONG: Semantic Search for "What works with Thassa's Oracle?"

```python
query = "cards that work well with Thassa's Oracle"
query_emb = model.encode(query)

# Search card embeddings
results = db.query("""
    SELECT name, oracle_text,
           1 - (embedding <=> %s::vector) AS similarity
    FROM cards
    ORDER BY embedding <=> %s::vector
    LIMIT 10
""", (query_emb, query_emb))
```

**What you actually get:**
1. Thassa's Oracle (similarity 0.95) - The card itself
2. Jace, Wielder of Mysteries (similarity 0.82) - Similar win condition
3. Laboratory Maniac (similarity 0.81) - Similar win condition
4. Divining Witch (similarity 0.67) - Similar card type
5. Merfolk Looter (similarity 0.65) - Similar creature type

**What's wrong?**
- Returns cards SIMILAR to Thassa's Oracle
- Does NOT return cards that COMBO with Thassa's Oracle
- Misses: Demonic Consultation, Tainted Pact, Leveler, etc.

**Why?**
Embeddings measure **semantic similarity**, not **functional relationships**!

- Demonic Consultation has completely different text (exile library)
- Tainted Pact has completely different text (exile cards to find one)
- These are semantically DISSIMILAR but functionally SYNERGISTIC

---

## ✅ CORRECT: Graph Lookup for Synergy

```python
# Step 1: Find the card
card_id = db.query("""
    SELECT id FROM cards WHERE name = 'Thassa''s Oracle'
""")[0]

# Step 2: Find all combos containing this card
combos_with_card = db.query("""
    SELECT combo_id FROM combo_cards
    WHERE card_id = %s
""", (card_id,))

# Step 3: Get all OTHER cards in those combos
synergy_cards = db.query("""
    SELECT
        c.name,
        COUNT(*) as combo_count,
        AVG(co.popularity) as avg_popularity
    FROM combo_cards cc
    JOIN cards c ON cc.card_id = c.id
    JOIN combos co ON cc.combo_id = co.id
    WHERE cc.combo_id IN %s
      AND cc.card_id != %s  -- Exclude the original card
    GROUP BY c.id, c.name
    ORDER BY combo_count DESC, avg_popularity DESC
    LIMIT 20
""", (tuple(combos_with_card), card_id))
```

**What you get:**
1. Demonic Consultation (appears in 87 combos with Thassa's Oracle)
2. Tainted Pact (appears in 64 combos)
3. Leveler (appears in 23 combos)
4. Paradigm Shift (appears in 12 combos)
5. Divining Witch (appears in 8 combos)

**This is correct!** These are actual combo partners, not just similar cards.

---

## Intent Detection

### How to Know Which Query Type?

**Pattern matching + NLP:**

```python
def detect_intent(query: str) -> str:
    """
    Detect user's intent from natural language query
    Returns: 'card_discovery' | 'combo_discovery' | 'synergy'
    """

    query_lower = query.lower()

    # Synergy patterns (Type 3)
    synergy_keywords = [
        'works with',
        'goes well with',
        'synergizes with',
        'combos with',
        'pairs with',
        'interact with',
        'partners with',
        'complements'
    ]

    for keyword in synergy_keywords:
        if keyword in query_lower:
            return 'synergy'

    # Check if query mentions a specific card name
    # "what works with <CardName>"
    # This is tricky - need card name extraction
    if 'with' in query_lower:
        # Try to extract card name
        card_name = extract_card_name(query)
        if card_name and card_exists(card_name):
            return 'synergy'

    # Combo patterns (Type 2)
    combo_keywords = [
        'combo',
        'combos',
        'combination',
        'infinite',
        'win the game',
        'win condition'
    ]

    for keyword in combo_keywords:
        if keyword in query_lower:
            return 'combo_discovery'

    # Default to card discovery (Type 1)
    return 'card_discovery'
```

**Example classifications:**

```python
detect_intent("Find cards that draw cards")
# → 'card_discovery' (semantic search on cards)

detect_intent("2-card infinite combos")
# → 'combo_discovery' (semantic search on combos)

detect_intent("What works with Thassa's Oracle?")
# → 'synergy' (graph lookup)

detect_intent("Cards that synergize with aristocrats")
# → 'synergy' (hybrid: extract theme, find related cards)
```

---

## Query Routing Architecture

### The Router

```python
class QueryRouter:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.card_searcher = CardSearchEngine(db, model)
        self.combo_searcher = ComboSearchEngine(db, model)
        self.synergy_finder = SynergyFinder(db)

    def search(self, query: str, filters: dict = None):
        """
        Route query to appropriate search engine
        """
        intent = self.detect_intent(query)

        if intent == 'card_discovery':
            return self.card_searcher.search(query, filters)

        elif intent == 'combo_discovery':
            return self.combo_searcher.search(query, filters)

        elif intent == 'synergy':
            # Extract card name or theme from query
            target = self.extract_target(query)
            return self.synergy_finder.find_synergies(target, filters)

        else:
            # Fallback: try all and merge results
            return self.multi_search(query, filters)
```

---

## Relationship Queries Explained

### Query: "What works with Thassa's Oracle?"

**Step-by-Step Execution:**

#### 1. Extract Target Card

```python
query = "What works with Thassa's Oracle?"

# NLP to extract card name
card_name = extract_card_name(query)
# → "Thassa's Oracle"

# Verify card exists
card = db.query("""
    SELECT id, name FROM cards
    WHERE name ILIKE %s
""", (f"%{card_name}%",))
# → {id: "abc-123", name: "Thassa's Oracle"}
```

#### 2. Find Combos Containing This Card

```sql
SELECT
    co.id,
    co.description,
    co.popularity,
    co.color_identity
FROM combos co
JOIN combo_cards cc ON co.id = cc.combo_id
WHERE cc.card_id = 'abc-123'  -- Thassa's Oracle
ORDER BY co.popularity DESC;
```

**Results:** 127 combos containing Thassa's Oracle

#### 3. Extract Combo Partners

```sql
WITH target_combos AS (
    -- Combos containing Thassa's Oracle
    SELECT combo_id
    FROM combo_cards
    WHERE card_id = 'abc-123'
)
SELECT
    c.id,
    c.name,
    c.oracle_text,
    c.cmc,
    COUNT(DISTINCT cc.combo_id) as combo_count,
    AVG(co.popularity) as avg_popularity,
    ARRAY_AGG(DISTINCT f.name) as common_features
FROM combo_cards cc
JOIN cards c ON cc.card_id = c.id
JOIN combos co ON cc.combo_id = co.id
LEFT JOIN combo_features cf ON co.id = cf.combo_id
LEFT JOIN features f ON cf.feature_id = f.id
WHERE cc.combo_id IN (SELECT combo_id FROM target_combos)
  AND cc.card_id != 'abc-123'  -- Exclude Thassa's Oracle itself
GROUP BY c.id, c.name, c.oracle_text, c.cmc
ORDER BY combo_count DESC, avg_popularity DESC
LIMIT 20;
```

**Results:**
```
name                | combo_count | avg_popularity | common_features
--------------------|-------------|----------------|------------------
Demonic Consultation| 87          | 95             | [Win the game, Infinite mill]
Tainted Pact        | 64          | 92             | [Win the game, Infinite mill]
Leveler             | 23          | 78             | [Win the game, Empty library]
Paradigm Shift      | 12          | 71             | [Win the game, Empty library]
Divining Witch      | 8           | 68             | [Win the game]
Hermit Druid        | 6           | 82             | [Win the game, Mill]
```

**This is the answer!** These are cards that actually combo with Thassa's Oracle.

---

### Query: "What synergizes with aristocrats strategies?"

**This is different - no specific card, but a theme/strategy!**

#### Approach 1: Semantic Search on Cards + Theme Keywords

```python
# Aristocrats = sacrifice creatures for value
query = "sacrifice creatures for value"
query_emb = model.encode(query)

# Find cards semantically related to this theme
results = db.query("""
    SELECT
        id, name, oracle_text,
        1 - (embedding <=> %s::vector) AS similarity
    FROM cards
    ORDER BY embedding <=> %s::vector
    LIMIT 50
""", (query_emb, query_emb))
```

**Returns cards like:**
- Blood Artist
- Zulaport Cutthroat
- Viscera Seer
- Carrion Feeder
- Grave Pact

#### Approach 2: Find Combos with "Aristocrats" Features

```python
# Find combos tagged with sacrifice/death triggers
results = db.query("""
    SELECT c.*, co.description
    FROM combos co
    JOIN combo_features cf ON co.id = cf.combo_id
    JOIN features f ON cf.feature_id = f.id
    WHERE f.name ILIKE '%death trigger%'
       OR f.name ILIKE '%sacrifice%'
       OR f.name ILIKE '%dies%'
    ORDER BY co.popularity DESC
    LIMIT 20
""")

# Then extract all cards from these combos
```

#### Approach 3: Hybrid - Semantic + Graph Traversal

```python
# 1. Find "seed cards" for aristocrats theme
seed_cards = semantic_search("aristocrats sacrifice creatures")
# → [Blood Artist, Zulaport Cutthroat, ...]

# 2. Find combos containing these cards
combos = find_combos_with_cards(seed_cards)

# 3. Extract all OTHER cards from those combos
synergy_cards = extract_cards_from_combos(combos)

# 4. Rank by frequency
ranked = rank_by_combo_frequency(synergy_cards)
```

---

## The Synergy Table (Pre-computed)

### Why Pre-compute?

**Problem:** Graph traversal is fast but repetitive
- "What works with Sol Ring?" → Same query every time
- "What works with Lightning Bolt?" → Same query every time

**Solution:** Pre-compute synergies once, query instantly

### Schema

```sql
CREATE TABLE card_synergies (
    card_id_1 UUID REFERENCES cards(id),
    card_id_2 UUID REFERENCES cards(id),

    -- Metrics
    combo_count INTEGER,              -- How many combos they share
    avg_popularity NUMERIC,           -- Average popularity of shared combos
    synergy_score NUMERIC,            -- Computed score (0-1)

    -- Context
    common_features TEXT[],           -- What combos produce together
    sample_combos TEXT[],             -- Top 3 combo IDs as examples

    PRIMARY KEY (card_id_1, card_id_2),
    CHECK (card_id_1 < card_id_2)     -- Prevent duplicates
);

CREATE INDEX idx_card_synergies_card1 ON card_synergies(card_id_1);
CREATE INDEX idx_card_synergies_card2 ON card_synergies(card_id_2);
CREATE INDEX idx_card_synergies_score ON card_synergies(synergy_score DESC);
```

### How to Populate

```sql
INSERT INTO card_synergies (card_id_1, card_id_2, combo_count, avg_popularity, synergy_score)
SELECT
    LEAST(cc1.card_id, cc2.card_id) as card_id_1,
    GREATEST(cc1.card_id, cc2.card_id) as card_id_2,
    COUNT(DISTINCT cc1.combo_id) as combo_count,
    AVG(co.popularity) as avg_popularity,
    -- Synergy score formula
    (COUNT(DISTINCT cc1.combo_id) * AVG(co.popularity) / 1000.0) as synergy_score
FROM combo_cards cc1
JOIN combo_cards cc2 ON cc1.combo_id = cc2.combo_id
JOIN combos co ON cc1.combo_id = co.id
WHERE cc1.card_id < cc2.card_id  -- Avoid duplicates
GROUP BY card_id_1, card_id_2
HAVING COUNT(DISTINCT cc1.combo_id) >= 3  -- Must appear in at least 3 combos together
ORDER BY synergy_score DESC;
```

### Query Synergies (Instant!)

```sql
-- "What works with Thassa's Oracle?"
SELECT
    c.name,
    cs.combo_count,
    cs.synergy_score,
    cs.common_features
FROM card_synergies cs
JOIN cards c ON (
    CASE
        WHEN cs.card_id_1 = :thassas_oracle_id THEN cs.card_id_2
        ELSE cs.card_id_1
    END = c.id
)
WHERE :thassas_oracle_id IN (cs.card_id_1, cs.card_id_2)
ORDER BY cs.synergy_score DESC
LIMIT 20;
```

**Performance:**
- Without synergy table: 50-100ms (graph traversal)
- With synergy table: **0.5-2ms** (direct index lookup)

**50-100x faster!**

---

## Complete Implementation Example

### The Full Query Router

```python
class MTGSearchEngine:
    def __init__(self, db_connection):
        self.db = db_connection
        self.model = SentenceTransformer('all-mpnet-base-v2', device='cuda')

    def search(self, query: str, filters: dict = None):
        """
        Universal search handler with intent detection
        """
        intent = self.detect_intent(query)

        if intent == 'synergy':
            return self.handle_synergy_query(query, filters)
        elif intent == 'combo_discovery':
            return self.handle_combo_query(query, filters)
        else:  # card_discovery
            return self.handle_card_query(query, filters)

    def detect_intent(self, query: str) -> str:
        """Detect query intent"""
        query_lower = query.lower()

        # Synergy patterns
        if any(kw in query_lower for kw in [
            'works with', 'synergizes with', 'goes well with',
            'combos with', 'pairs with', 'interact with'
        ]):
            return 'synergy'

        # Combo patterns
        if any(kw in query_lower for kw in [
            'combo', 'infinite', 'win condition', 'win the game'
        ]):
            return 'combo_discovery'

        return 'card_discovery'

    def handle_synergy_query(self, query: str, filters: dict = None):
        """
        Handle: "What works with <card>?" or "Cards that synergize with <theme>"
        """
        # Extract target (card name or theme)
        target = self.extract_target(query)

        # Is target a card name?
        card = self.find_card(target)

        if card:
            # Specific card synergy
            return self.find_card_synergies(card['id'], filters)
        else:
            # Theme-based synergy
            return self.find_theme_synergies(target, filters)

    def find_card_synergies(self, card_id: str, filters: dict = None):
        """
        Find cards that combo with a specific card
        Uses pre-computed synergy table
        """
        sql = """
            SELECT
                c.id,
                c.name,
                c.oracle_text,
                c.colors,
                c.cmc,
                cs.combo_count,
                cs.synergy_score,
                cs.common_features
            FROM card_synergies cs
            JOIN cards c ON (
                CASE
                    WHEN cs.card_id_1 = %s THEN cs.card_id_2
                    ELSE cs.card_id_1
                END = c.id
            )
            WHERE %s IN (cs.card_id_1, cs.card_id_2)
        """

        params = [card_id, card_id]

        # Apply filters
        if filters:
            if 'colors' in filters:
                sql += " AND c.colors <@ %s::text[]"
                params.append(filters['colors'])

            if 'max_cmc' in filters:
                sql += " AND c.cmc <= %s"
                params.append(filters['max_cmc'])

        sql += " ORDER BY cs.synergy_score DESC LIMIT 20"

        cursor = self.db.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def find_theme_synergies(self, theme: str, filters: dict = None):
        """
        Find cards for a theme/strategy
        Uses semantic search
        """
        # Generate embedding for theme
        query_emb = self.model.encode(theme)
        embedding_str = '[' + ','.join(map(str, query_emb)) + ']'

        sql = """
            WITH semantic_matches AS (
                SELECT
                    id, name, oracle_text, colors, cmc,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM cards
                ORDER BY embedding <=> %s::vector
                LIMIT 100
            )
            SELECT * FROM semantic_matches
            WHERE 1=1
        """

        params = [embedding_str, embedding_str]

        # Apply filters
        if filters:
            if 'colors' in filters:
                sql += " AND colors <@ %s::text[]"
                params.append(filters['colors'])

            if 'max_cmc' in filters:
                sql += " AND cmc <= %s"
                params.append(filters['max_cmc'])

        sql += " ORDER BY similarity DESC LIMIT 20"

        cursor = self.db.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def handle_combo_query(self, query: str, filters: dict = None):
        """
        Handle: "Find <type> combos"
        Uses semantic search on combos
        """
        query_emb = self.model.encode(query)
        embedding_str = '[' + ','.join(map(str, query_emb)) + ']'

        # ... (combo search logic from previous examples)

    def handle_card_query(self, query: str, filters: dict = None):
        """
        Handle: "Find <type> cards"
        Uses semantic search on cards
        """
        query_emb = self.model.encode(query)
        embedding_str = '[' + ','.join(map(str, query_emb)) + ']'

        # ... (card search logic from previous examples)
```

### Usage Examples

```python
engine = MTGSearchEngine(db_connection)

# Synergy query - uses graph lookup
results = engine.search("What works with Thassa's Oracle?")
# → [Demonic Consultation, Tainted Pact, Leveler, ...]

# Combo query - uses combo embeddings
results = engine.search("2-card infinite mana combos")
# → [Sol Ring + Hullbreaker, Basalt + Rings, ...]

# Card query - uses card embeddings
results = engine.search("Draw cards when artifacts enter")
# → [Sram, Jhoira, Riddlesmith, ...]

# Synergy with filters
results = engine.search(
    "What works with Thassa's Oracle?",
    filters={"colors": ["U", "B"], "max_cmc": 3}
)
# → Only cheap Dimir combo pieces
```

---

## Summary

### The Problem
"Find cards that interact well with Thassa's Oracle" doesn't mention "combo" but needs combo data.

### The Solution
**Multi-strategy query routing:**

1. **Intent Detection** - Determine what the user is really asking for
   - Card properties? → Semantic search on cards
   - Combo outcomes? → Semantic search on combos
   - Card relationships? → Graph lookup through combo_cards

2. **Relationship Queries** - Use graph traversal, not embeddings
   - Find combos containing target card
   - Extract other cards from those combos
   - Rank by co-occurrence frequency

3. **Pre-computed Synergies** - Cache results for speed
   - card_synergies table with pre-calculated scores
   - 50-100x faster than on-the-fly graph traversal
   - Update periodically when combo data changes

4. **Hybrid Approach** - Combine multiple strategies
   - Use embeddings for discovery
   - Use graph for relationships
   - Use tags for filtering

### Key Insight

**Embeddings measure similarity, not relationships!**

- "Similar to Thassa's Oracle" → Jace, Lab Man (similar win conditions)
- "Combos with Thassa's Oracle" → Demonic Consultation, Tainted Pact (functional partners)

These require **different data structures**:
- Embeddings for similarity
- Graph relationships for synergy
- Intent detection to route correctly

