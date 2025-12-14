# MTG Vector Database - Data Integration Strategy

**Purpose:** Strategic plan for merging card data, combo data, and rules into a unified, searchable vector database.

**Status:** Planning Phase - No code written yet

**Date:** 2025-12-13

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Use Cases & Search Scenarios](#use-cases--search-scenarios)
3. [Data Relationships](#data-relationships)
4. [Embedding Strategy](#embedding-strategy)
5. [Proposed Schema Design](#proposed-schema-design)
6. [Implementation Phases](#implementation-phases)
7. [Open Questions](#open-questions)

---

## Current State Analysis

### Data Sources Inventory

| Source | Format | Size | Records | Status |
|--------|--------|------|---------|--------|
| **Scryfall Cards** | JSON file | 2.23 GB | ~508,690 cards | ✅ Loaded in DB |
| **Commander Spellbook** | JSON file | 1.14 GB | 36,111 combos | ❌ Not loaded |
| **EDHREC Combos** | JSON files | 0 MB | 0 | ❌ Not scraped yet |
| **MTG Rules** | Database | 2.7 MB | 45 rules | ✅ Loaded in DB |

### Current Database Schema

**Tables:**
- `cards` (508,686 rows, 7.7 GB) - Individual MTG cards from Scryfall
- `card_rules` (425,594 rows, 105 MB) - Card-to-rule mappings
- `rules` (45 rows, 2.7 MB) - MTG comprehensive rules
- `keyword_abilities` (15 rows) - Keyword definitions
- `rule_categories` (24 rows) - Rule categorization

**Current Embeddings:**
- `cards.embedding` - 384 dims (old) or 768 dims (new, partial)
- `cards.oracle_embedding` - Oracle text only
- `rules.embedding` - Rule text embeddings

**Missing:**
- No combo data in database
- No card-to-combo relationships
- No combo embeddings
- No synergy/interaction embeddings

---

## Use Cases & Search Scenarios

### Primary Use Cases

#### 1. **Card Discovery** (Individual Card Search)
*"I need cards that do X"*

**Examples:**
- "Show me cards that draw when artifacts enter"
- "Find removal spells that exile"
- "Tutors for enchantments under 3 CMC"

**Current Support:** ✅ Good (card embeddings work)
**Query Type:** Semantic search on `cards.embedding`

---

#### 2. **Combo Discovery** (Multi-Card Interaction Search)
*"I need combos that produce X"*

**Examples:**
- "Show me infinite mana combos in Simic colors"
- "Find 2-card combos that win immediately"
- "Budget combos under $50 that draw infinite cards"

**Current Support:** ❌ Not supported (no combo data)
**Query Type:** Semantic search on combo descriptions + filtering

---

#### 3. **Synergy Search** (Card Compatibility)
*"What works well with card X?"*

**Examples:**
- "What cards synergize with Thassa's Oracle?"
- "Show me cards that go in an artifact sacrifice deck"
- "What works with graveyard recursion strategies?"

**Current Support:** ⚠️ Partial (can find similar cards, not combo partners)
**Query Type:** Combo relationships + semantic similarity

---

#### 4. **Deck Building** (Theme-Based)
*"Build me a deck around X theme"*

**Examples:**
- "Build a landfall deck in Gruul"
- "Create a storm deck with budget constraints"
- "Commander deck around sacrifice triggers"

**Current Support:** ⚠️ LLM can generate, but lacks combo knowledge
**Query Type:** Multi-step: theme → cards → combos → balance

---

#### 5. **Rules & Interaction Queries**
*"How does X work with Y?"*

**Examples:**
- "Does First Strike work with Deathtouch?"
- "Can I respond to a triggered ability?"
- "What happens when two replacement effects conflict?"

**Current Support:** ✅ Good (rules embeddings exist)
**Query Type:** Semantic search on `rules.embedding`

---

#### 6. **Combo Validation** (Does This Work?)
*"Can I combo these cards?"*

**Examples:**
- "Do these three cards combo?"
- "What's missing from this combo?"
- "How does this interaction resolve?"

**Current Support:** ❌ Not supported
**Query Type:** Graph search + rules validation

---

### Search Patterns Analysis

| Pattern | Frequency | Requires |
|---------|-----------|----------|
| Single card properties | High | Card embeddings |
| Card similarity | Medium | Card embeddings |
| Combo outcomes | High | Combo embeddings |
| Card-to-combo lookup | High | Relationship table |
| Synergy discovery | Medium | Combo + card embeddings |
| Rules interpretation | Low | Rules embeddings |
| Price-aware search | Medium | Price data + filters |

---

## Data Relationships

### Entity Relationship Model

```
┌─────────────────┐
│     CARDS       │ (Individual cards)
│  - id           │
│  - name         │
│  - oracle_text  │
│  - embedding    │ ← 768-dim vector
└────────┬────────┘
         │
         │ Many-to-Many
         ├────────────────────────────────┐
         │                                │
         ▼                                ▼
┌─────────────────┐              ┌─────────────────┐
│   COMBO_CARDS   │              │   CARD_RULES    │
│  - combo_id     │              │  - card_id      │
│  - card_id      │              │  - rule_id      │
│  - quantity     │              └─────────────────┘
│  - zone         │
└────────┬────────┘
         │
         │ Many-to-One
         ▼
┌─────────────────┐
│     COMBOS      │ (Multi-card interactions)
│  - id           │
│  - description  │
│  - mana_needed  │
│  - color_id     │
│  - embedding    │ ← 768-dim vector (NEW)
└────────┬────────┘
         │
         │ Many-to-Many
         ▼
┌─────────────────┐
│   COMBO_RESULTS │ (What the combo produces)
│  - combo_id     │
│  - feature_id   │
└────────┬────────┘
         │
         │ Many-to-One
         ▼
┌─────────────────┐
│    FEATURES     │ ("Infinite mana", "Win game")
│  - id           │
│  - name         │
│  - embedding    │ ← 768-dim vector (NEW)
└─────────────────┘
```

### Key Relationships

1. **Card ↔ Combo** (Many-to-Many)
   - A card appears in multiple combos
   - A combo uses multiple cards
   - Junction: `combo_cards` with metadata (quantity, zone, state)

2. **Combo ↔ Features** (Many-to-Many)
   - A combo produces multiple outcomes
   - A feature can be produced by many combos
   - Junction: `combo_results`

3. **Card ↔ Rules** (Many-to-Many)
   - Already exists in database
   - Enables rules-based validation

---

## Embedding Strategy

### Core Principle: **Multi-Level Semantic Search**

Different search scenarios require different embedding types. We need a **layered approach**:

### Layer 1: Card Embeddings (Individual)
**Purpose:** Find individual cards by properties/abilities

**Embedding Text:**
```python
card_text = f"{name} | {type_line} | {oracle_text} | Keywords: {keywords}"
```

**Example:**
```
"Lightning Bolt | Instant | Lightning Bolt deals 3 damage to any target. | Keywords: damage_dealer"
```

**Use Case:**
- "Find burn spells"
- "Show me instant-speed removal"

**Status:** ✅ Partially complete (upgrading to 768 dims)

---

### Layer 2: Combo Embeddings (Interactions)
**Purpose:** Find combos by what they do, not just which cards are in them

**Embedding Text Option A (Outcome-focused):**
```python
combo_text = f"Produces: {features} | Colors: {color_identity} | Cards needed: {card_count}"
```

**Example:**
```
"Produces: Infinite colorless mana, Infinite storm count | Colors: U | Cards needed: 2"
```

**Embedding Text Option B (Description-focused):**
```python
combo_text = f"{description} | Produces: {features} | Colors: {color_identity}"
```

**Example:**
```
"Cast Sol Ring, bounce it with Hullbreaker Horror, repeat infinitely | Produces: Infinite colorless mana | Colors: U"
```

**Embedding Text Option C (Hybrid - RECOMMENDED):**
```python
combo_text = f"Cards: {card_names} | {description} | Produces: {features} | Colors: {color_identity} | Mana: {mana_needed}"
```

**Example:**
```
"Cards: Sol Ring, Hullbreaker Horror | Cast Sol Ring, bounce it with Hullbreaker Horror trigger, repeat | Produces: Infinite colorless mana, Infinite storm | Colors: U | Mana: {1}"
```

**Use Case:**
- "Find infinite mana combos in blue"
- "2-card combos that win the game"

**Status:** ❌ Not implemented

**Recommendation:** **Option C (Hybrid)** - Includes cards, description, and outcomes for maximum searchability

---

### Layer 3: Feature Embeddings (Outcomes)
**Purpose:** Cluster combos by what they achieve

**Embedding Text:**
```python
feature_text = f"{feature_name}"
```

**Examples:**
```
"Infinite mana"
"Infinite damage"
"Win the game"
"Infinite creature tokens"
```

**Use Case:**
- Group similar combo outcomes
- Find combos that achieve the same goal
- Recommend alternatives

**Status:** ❌ Not implemented

**Alternative:** Could skip separate embeddings and just use feature names as tags/filters

---

### Layer 4: Enriched Card Embeddings (Context-Aware)
**Purpose:** Enhance card embeddings with combo/synergy context

**Embedding Text:**
```python
enriched_card_text = f"{name} | {type_line} | {oracle_text} | Keywords: {keywords} | Combos with: {top_combo_partners} | Appears in {combo_count} combos | Common themes: {themes}"
```

**Example:**
```
"Thassa's Oracle | Enchantment Creature — Merfolk | ETB: Scry X, if library empty, win | Keywords: win_condition | Combos with: Demonic Consultation, Tainted Pact, Leveler | Appears in 127 combos | Common themes: self-mill, instant-win"
```

**Use Case:**
- "Cards that combo with Thassa's Oracle"
- "Show me win conditions in Dimir"

**Status:** ❌ Not implemented

**Concern:** May dilute card's individual semantic meaning

**Alternative:** Keep card embeddings pure, use separate relationship tables for combos

---

### Embedding Strategy Decision Matrix

| Embedding Type | Create? | Dimensions | When to Use |
|---------------|---------|------------|-------------|
| **Card (pure)** | ✅ Yes | 768 | Individual card search |
| **Card (enriched)** | ⚠️ Maybe | 768 | Combo-aware card search |
| **Combo** | ✅ Yes | 768 | Combo discovery |
| **Feature** | ❌ No | - | Use as tags/filters instead |
| **Oracle-only** | ✅ Yes | 768 | Ability matching |

**Rationale:**
- **Pure card embeddings** = Precise individual card semantics
- **Combo embeddings** = Essential for combo discovery
- **Features as tags** = More efficient than embeddings for exact matching
- **Enriched cards** = Useful but may create confusion, evaluate later

---

## Proposed Schema Design

### Option A: Separate Card and Combo Embeddings (RECOMMENDED)

**Pros:**
- Clean separation of concerns
- Cards remain semantically pure
- Combos are searchable independently
- Easy to update one without affecting the other

**Cons:**
- Two separate search queries needed
- More complex application logic

**Schema:**

```sql
-- CARDS TABLE (existing, minimal changes)
CREATE TABLE cards (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    type_line TEXT,
    oracle_text TEXT,
    keywords TEXT[],
    colors TEXT[],
    cmc NUMERIC,

    -- Pure card embeddings (no combo context)
    embedding VECTOR(768),           -- Full card text
    oracle_embedding VECTOR(768),    -- Oracle text only

    -- Metadata
    price_usd NUMERIC,
    legality JSONB,
    data JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- COMBOS TABLE (new)
CREATE TABLE combos (
    id TEXT PRIMARY KEY,
    description TEXT,                  -- How the combo works
    mana_needed TEXT,                  -- Mana cost to execute
    color_identity TEXT[],             -- Color requirements
    card_count INTEGER,                -- Number of cards in combo
    status TEXT,                       -- ok, needs_review, etc.
    popularity INTEGER,                -- Popularity score

    -- Combo embedding (cards + description + outcomes)
    embedding VECTOR(768),             -- NEW: Semantic combo search

    -- Metadata
    price_usd NUMERIC,                 -- Total combo price
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- FEATURES TABLE (combo outcomes)
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,         -- "Infinite mana", "Win game"
    category TEXT,                     -- "mana", "life", "win", "tokens"
    uncountable BOOLEAN DEFAULT FALSE,

    -- NOTE: No embedding - use as exact match tags

    created_at TIMESTAMP DEFAULT NOW()
);

-- COMBO_CARDS (junction table)
CREATE TABLE combo_cards (
    id SERIAL PRIMARY KEY,
    combo_id TEXT REFERENCES combos(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,

    quantity INTEGER DEFAULT 1,
    zone TEXT,                         -- battlefield, hand, graveyard, command
    zone_locations TEXT[],             -- specific zone requirements
    battlefield_state TEXT,            -- tapped, untapped, etc.
    must_be_commander BOOLEAN DEFAULT FALSE,

    UNIQUE(combo_id, card_id)
);

-- COMBO_FEATURES (junction table)
CREATE TABLE combo_features (
    id SERIAL PRIMARY KEY,
    combo_id TEXT REFERENCES combos(id) ON DELETE CASCADE,
    feature_id INTEGER REFERENCES features(id) ON DELETE CASCADE,

    UNIQUE(combo_id, feature_id)
);

-- CARD_SYNERGIES (derived table - optional)
-- Pre-computed synergy scores between cards based on combo co-occurrence
CREATE TABLE card_synergies (
    card_id_1 UUID REFERENCES cards(id),
    card_id_2 UUID REFERENCES cards(id),
    synergy_score NUMERIC,             -- Based on combo count, popularity
    combo_count INTEGER,               -- How many combos they share
    avg_popularity NUMERIC,            -- Average popularity of shared combos

    PRIMARY KEY (card_id_1, card_id_2),
    CHECK (card_id_1 < card_id_2)      -- Prevent duplicates (A,B) and (B,A)
);

-- INDEXES
CREATE INDEX idx_cards_embedding ON cards USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_cards_oracle_embedding ON cards USING hnsw (oracle_embedding vector_cosine_ops);
CREATE INDEX idx_combos_embedding ON combos USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_combos_color_identity ON combos USING GIN(color_identity);
CREATE INDEX idx_combos_card_count ON combos(card_count);
CREATE INDEX idx_combo_cards_card_id ON combo_cards(card_id);
CREATE INDEX idx_combo_cards_combo_id ON combo_cards(combo_id);
CREATE INDEX idx_features_name ON features(name);
CREATE INDEX idx_card_synergies_card1 ON card_synergies(card_id_1);
CREATE INDEX idx_card_synergies_card2 ON card_synergies(card_id_2);
```

---

### Option B: Enriched Card Embeddings Only

**Pros:**
- Single search query
- Cards already include combo context
- Simpler application logic

**Cons:**
- Card embeddings polluted with combo info
- Harder to find "just the card" semantics
- Must re-embed all cards when combos change

**Schema:**
```sql
CREATE TABLE cards (
    -- ... existing fields ...

    -- Enriched embeddings (includes combo context)
    embedding VECTOR(768),               -- Card + combo context
    oracle_embedding VECTOR(768),        -- Oracle text only
    combo_context TEXT,                  -- Text used to enrich embedding

    -- Computed fields
    combo_count INTEGER DEFAULT 0,
    top_combo_partners TEXT[],           -- Top 5 cards this combos with
    common_themes TEXT[]                 -- Extracted themes
);

-- COMBOS TABLE (still needed for combo data)
-- But no embedding column
CREATE TABLE combos (
    -- ... same as Option A, but NO embedding column ...
);
```

**Recommendation:** ❌ **Do not use** - Too much coupling

---

### Option C: Hybrid Approach (ALTERNATIVE)

**Both pure and enriched embeddings:**

```sql
CREATE TABLE cards (
    -- ... existing fields ...

    -- Pure embeddings (individual card)
    embedding_pure VECTOR(768),          -- Just the card
    oracle_embedding VECTOR(768),        -- Just oracle text

    -- Enriched embeddings (with combo context)
    embedding_enriched VECTOR(768),      -- Card + combo context
);

CREATE TABLE combos (
    -- ... with embedding ...
    embedding VECTOR(768),
);
```

**Pros:**
- Maximum flexibility
- Can choose pure or enriched per query

**Cons:**
- 3 embeddings per card (expensive storage/compute)
- Confusing which to use when

**Recommendation:** ⚠️ **Evaluate later** - Only if pure embeddings prove insufficient

---

## Implementation Phases

### Phase 1: Load Combo Data (No Embeddings Yet)
**Goal:** Get combo data into database, establish relationships

**Tasks:**
1. Create combo schema tables (combos, combo_cards, combo_features, features)
2. Load Commander Spellbook JSON → PostgreSQL
3. Link combo cards to existing cards table (UUID matching)
4. Validate data integrity (all cards exist, no orphans)
5. Create basic indexes (non-vector)

**Deliverable:** Queryable combo database with relationships

**Time Estimate:** 4-8 hours

**Success Criteria:**
- All 36,111 combos loaded
- All cards linked properly
- Can query: "Show me all combos containing Sol Ring"

---

### Phase 2: Generate Combo Embeddings
**Goal:** Make combos semantically searchable

**Tasks:**
1. Define combo embedding text format (Hybrid Option C recommended)
2. Generate embeddings for all combos using MPNet model
3. Store in `combos.embedding` column
4. Create HNSW index for fast similarity search
5. Test combo search queries

**Deliverable:** Semantic combo search functionality

**Time Estimate:** 2-4 hours (36K combos, fast on GPU)

**Success Criteria:**
- Can query: "Find infinite mana combos in blue"
- Returns relevant combos ranked by similarity

---

### Phase 3: Complete Card Embeddings Upgrade
**Goal:** Finish upgrading all card embeddings to 768 dims

**Tasks:**
1. Run full embedding regeneration (pure cards, no combo context)
2. Process all 508,686 cards
3. Create indexes
4. Validate search quality

**Deliverable:** All cards have high-quality 768-dim embeddings

**Time Estimate:** 5-6 hours (already scripted)

**Success Criteria:**
- All cards embedded with MPNet
- Card search quality improved over MiniLM

---

### Phase 4: Build Synergy Table (Optional)
**Goal:** Pre-compute card synergies for fast lookup

**Tasks:**
1. Analyze combo co-occurrence patterns
2. Calculate synergy scores
3. Populate `card_synergies` table
4. Create indexes

**Deliverable:** "What combos with X?" queries are instant

**Time Estimate:** 2-3 hours

**Success Criteria:**
- Can query: "What cards synergize with Thassa's Oracle?"
- Returns top combo partners instantly

---

### Phase 5: Integration & Testing
**Goal:** Unified search API

**Tasks:**
1. Build hybrid search API (cards + combos)
2. Implement filter logic (price, colors, card count)
3. Test all use cases
4. Optimize query performance
5. Document API

**Deliverable:** Production-ready search system

**Time Estimate:** 8-12 hours

---

## Open Questions

### Questions Needing Decisions

1. **Card Embedding Purity:**
   - Q: Keep card embeddings pure (no combo context)?
   - Recommendation: **Yes** - Use separate combo embeddings + relationship tables
   - Trade-off: More complex queries, but cleaner semantics

2. **Feature Embeddings:**
   - Q: Embed feature names or use as exact-match tags?
   - Recommendation: **Tags only** - Features are categorical, not semantic
   - Trade-off: Can't search for "similar outcomes", but exact matches are cleaner

3. **Combo Embedding Text Format:**
   - Q: Which text format for combo embeddings?
   - Recommendation: **Hybrid (Option C)** - Cards + description + outcomes
   - Trade-off: Longer text, but maximum searchability

4. **Enriched Card Embeddings:**
   - Q: Should cards include combo context?
   - Recommendation: **Not initially** - Evaluate after Phase 3 testing
   - Trade-off: May improve "synergy search" but pollutes individual card meaning

5. **Price Integration:**
   - Q: Include price in embeddings or just filter?
   - Recommendation: **Filter only** - Price is numeric, not semantic
   - Trade-off: Can't search "budget combos" semantically, must filter

6. **Combo Validation:**
   - Q: Use rules engine to validate combos?
   - Recommendation: **Phase 6 feature** - Focus on search first
   - Trade-off: Some combos may be outdated/invalid

7. **Multiple Databases:**
   - Q: One database for everything or separate for combos?
   - Recommendation: **Single database** - Easier relationships
   - Trade-off: Larger database, but simpler architecture

8. **Incremental Updates:**
   - Q: How to handle new cards/combos?
   - Recommendation: **Plan for it** - Design with update scripts in mind
   - Trade-off: More infrastructure, but essential for production

---

## Recommended Path Forward

### Immediate Next Steps:

1. **Review & Approve This Strategy** ✋ (You are here)
   - Discuss any questions or concerns
   - Decide on open questions
   - Finalize approach

2. **Phase 1: Load Combo Data**
   - Implement schema (Option A recommended)
   - Load Commander Spellbook data
   - Validate relationships

3. **Phase 2: Generate Combo Embeddings**
   - Define embedding format (Hybrid Option C)
   - Generate embeddings with GPU
   - Test combo search

4. **Phase 3: Complete Card Embeddings**
   - Finish 768-dim card embedding upgrade
   - Keep cards pure (no combo context)

5. **Phase 4+: Integration & Optimization**
   - Build unified search API
   - Add synergy tables if needed
   - Optimize performance

---

## Success Metrics

### How We'll Know This Works:

1. **Search Quality**
   - "Infinite mana combos" → Returns Dramatic Reversal combos, Sol Ring loops, etc.
   - "Budget removal" → Returns cheap cards first
   - "Cards that draw when artifacts enter" → Returns Sram, Jhoira, etc.

2. **Performance**
   - Card search: < 100ms
   - Combo search: < 200ms
   - Hybrid search: < 300ms

3. **Coverage**
   - All 508,686 cards searchable
   - All 36,111 combos searchable
   - All card-combo relationships mapped

4. **User Queries**
   - Natural language queries work (no exact keywords needed)
   - Filters work (colors, price, card count)
   - Results ranked by relevance

---

## Next: Review & Decision

**Please review this strategy and provide feedback on:**

1. ✅ Overall approach (separate card + combo embeddings)?
2. ✅ Schema design (Option A recommended)?
3. ✅ Embedding formats (Hybrid combo text)?
4. ✅ Implementation order (Phases 1-5)?
5. ❓ Any open questions to resolve?

Once approved, we'll proceed to Phase 1 implementation.

