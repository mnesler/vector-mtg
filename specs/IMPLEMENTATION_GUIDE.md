# MTG Rule Engine - Complete Implementation Guide

## Overview

This guide walks through implementing a complete MTG rule engine using vector embeddings to extract and classify card mechanics.

---

## What We've Built

### 1. **Enhanced Schema** (`schema_with_rules.sql`)
   - Production-ready schema using `CREATE IF NOT EXISTS` (no DROP CASCADE)
   - Safe to re-run without data loss
   - Cards table with dual embeddings (full card + oracle text only)
   - Rules table for extracted patterns
   - Rule categories for organization
   - Card-to-rule mappings with parameter bindings
   - Rule interactions table (combos, synergies)
   - Keyword abilities catalog
   - Helpful views and functions
   - Migration infrastructure in `migrations/` directory

### 2. **Card Loader** (`load_cards_with_keywords.py`)
   - Streams 2.3GB cards.json file
   - Extracts 100+ keywords and abilities from oracle text
   - Loads ~509K cards with enhanced metadata
   - Batch processing for performance

### 3. **Seed Rules** (`seed_rules.sql`)
   - 50+ manually crafted rule templates
   - 15+ rule categories (Removal, Card Draw, Counterspells, etc.)
   - Evergreen keyword definitions
   - Examples for each rule

### 4. **Remaining Scripts** (to be created):
   - `generate_embeddings_dual.py` - Generate embeddings for cards AND rules
   - `extract_rules.py` - Auto-discover rules from card clusters
   - `rule_engine.py` - Rule matching and classification engine
   - `api_server_rules.py` - REST API for rule engine

---

## Step-by-Step Implementation

### Step 1: Set Up Database

```bash
# Start PostgreSQL (if using Docker)
docker-compose up -d

# Wait for database to be ready
sleep 5

# Create initial schema (safe to re-run)
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < schema_with_rules.sql

# Or if running locally:
psql -U postgres -d vector_mtg -f schema_with_rules.sql

# Note: Schema uses CREATE IF NOT EXISTS, so it's safe to run multiple times
# Future schema changes should use migration scripts in migrations/ directory
```

### Step 2: Load Card Data

```bash
# Install Python dependencies
pip install ijson psycopg2-binary

# Load cards (takes 5-10 minutes for 509K cards)
python load_cards_with_keywords.py
```

**Expected output:**
```
Inserted 509,000 cards in 300 seconds (1,700 cards/sec)
Cards with keywords: 450,000 (88.4%)
Top keywords: flying, enters the battlefield, targeted_destruction, card_draw...
```

### Step 3: Seed Initial Rules

```bash
# Load seed rules
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg < seed_rules.sql

# Or locally:
psql -U postgres -d vector_mtg -f seed_rules.sql
```

**Expected output:**
```
Rule Categories: 24
Rules: 52
Keyword Abilities: 15
```

### Step 4: Generate Embeddings

**Note:** The remaining scripts (`generate_embeddings_dual.py`, `extract_rules.py`, `rule_engine.py`, `api_server_rules.py`) are outlined in `RULE_ENGINE_ARCHITECTURE.md` but need to be created as standalone files. Here's the implementation order:

```bash
# 1. Generate embeddings for cards and rules
python generate_embeddings_dual.py

# 2. Extract additional rules from card clusters
python extract_rules.py

# 3. Start the rule engine API
python api_server_rules.py
```

---

## Key Concepts

### Dual Embedding Strategy

Each card gets TWO embeddings:

1. **Full Card Embedding** (`cards.embedding`)
   - Input: name + type_line + oracle_text + mana_cost
   - Use: Finding similar cards holistically
   - Example: "Lightning Bolt" → finds other efficient burn spells

2. **Oracle Text Embedding** (`cards.oracle_embedding`)
   - Input: oracle_text only
   - Use: Matching cards to rules by mechanics
   - Example: "Destroy target creature" → finds all creature removal

### Rule Extraction Process

1. **Clustering**: Group cards with similar oracle text embeddings
2. **Pattern Extraction**: Find common text patterns in each cluster
3. **Template Generation**: Create generalized rule templates
4. **Parameter Binding**: Extract specific values from card text

Example:
```
Cluster: [Lightning Bolt, Shock, Searing Spear, ...]
Pattern: "deals? (\d+) damage to (?:any target|target .*)"
Template: "Deal N damage to target"
Parameters: {"damage_amount": "number", "target_type": "string"}
```

### Rule Matching

Cards are matched to rules using:
1. **Vector Similarity**: Oracle embedding similarity to rule embedding (threshold: 0.7)
2. **Regex Pattern**: Text pattern matching (if defined)
3. **Manual Assignment**: For edge cases

---

## Database Queries

### Find Cards by Rule

```sql
-- All creature removal spells with CMC <= 2
SELECT c.name, c.mana_cost, c.oracle_text
FROM cards c
JOIN card_rules cr ON c.id = cr.card_id
JOIN rules r ON cr.rule_id = r.id
WHERE r.rule_name = 'targeted_creature_destruction'
  AND c.cmc <= 2
ORDER BY c.cmc, c.name;
```

### Find Rules for a Card

```sql
-- What rules does Lightning Bolt follow?
SELECT r.rule_name, r.rule_template, cr.confidence, cr.parameter_bindings
FROM rules r
JOIN card_rules cr ON r.id = cr.rule_id
JOIN cards c ON cr.card_id = c.id
WHERE c.name = 'Lightning Bolt'
ORDER BY cr.confidence DESC;
```

### Discover Card Interactions

```sql
-- Find cards that combo with "Archangel of Thune"
WITH thune_rules AS (
    SELECT r.id
    FROM cards c
    JOIN card_rules cr ON c.id = cr.card_id
    JOIN rules r ON cr.rule_id = r.id
    WHERE c.name = 'Archangel of Thune'
)
SELECT
    c.name,
    r.rule_name,
    ri.interaction_type,
    ri.description
FROM thune_rules tr
JOIN rule_interactions ri ON (tr.id = ri.rule_a_id OR tr.id = ri.rule_b_id)
JOIN rules r ON (r.id = ri.rule_a_id OR r.id = ri.rule_b_id)
JOIN card_rules cr ON r.id = cr.rule_id
JOIN cards c ON cr.card_id = c.id
WHERE c.name != 'Archangel of Thune'
  AND ri.interaction_type IN ('synergy', 'combo')
ORDER BY ri.strength DESC;
```

### Analyze Deck Composition

```sql
-- Deck rule distribution
WITH deck AS (
    SELECT unnest(ARRAY[
        'Sol Ring', 'Command Tower', 'Lightning Bolt',
        'Swords to Plowshares', 'Counterspell'
    ]) AS card_name
)
SELECT
    rc.name AS category,
    COUNT(*) AS card_count,
    array_agg(d.card_name) AS cards
FROM deck d
JOIN cards c ON c.name = d.card_name
JOIN card_rules cr ON c.id = cr.card_id
JOIN rules r ON cr.rule_id = r.id
JOIN rule_categories rc ON r.category_id = rc.id
GROUP BY rc.name
ORDER BY card_count DESC;
```

---

## Rule Engine API

Once `api_server_rules.py` is implemented, you'll have these endpoints:

### Card Endpoints

```bash
# Get card with rules
GET /api/cards/{card_id}

# Search cards by rule
GET /api/cards?rule=targeted_creature_destruction&cmc_max=2

# Find similar cards
GET /api/cards/{card_id}/similar?limit=20
```

### Rule Endpoints

```bash
# List all rules
GET /api/rules

# Get rule details
GET /api/rules/{rule_id}

# Find cards matching rule
GET /api/rules/{rule_id}/cards?limit=50

# Classify new card text
POST /api/rules/classify
{
  "oracle_text": "Destroy target creature with flying."
}
```

### Analysis Endpoints

```bash
# Deck analysis
POST /api/analyze/deck
{
  "cards": ["Sol Ring", "Mana Crypt", "Lightning Bolt", ...]
}

# Card interactions
GET /api/interactions?card_a={id}&card_b={id}

# Rule statistics
GET /api/stats/rules
```

---

## Next Steps

### Immediate (Required for Rule Engine)

1. **Create `generate_embeddings_dual.py`**
   - Generate embeddings for all cards (both types)
   - Generate embeddings for all rules
   - Update database with embeddings
   - Create vector indexes

2. **Create `extract_rules.py`**
   - Cluster cards by oracle text similarity
   - Extract common patterns from clusters
   - Generate new rule templates
   - Populate card_rules junction table

3. **Create `rule_engine.py`**
   - Implement `MTGRuleEngine` class
   - Methods for classification, matching, interactions
   - Parameter extraction logic

4. **Create `api_server_rules.py`**
   - FastAPI server with rule endpoints
   - Integration with rule engine
   - Caching layer for performance

### Future Enhancements

- **LLM Integration**: Use GPT-4 to generate rule descriptions and detect nuanced patterns
- **Rule Validation**: Human-in-the-loop validation UI for auto-extracted rules
- **Combo Detection**: Automatically detect 2-card and 3-card combos
- **Meta Analysis**: Analyze tournament decks to find emerging rule patterns
- **Card Generation**: Generate new card ideas based on rule combinations
- **Format Analysis**: Analyze rule distribution across formats (Standard, Modern, Commander)

---

## Schema Changes & Migrations

### Making Schema Changes

**NEVER modify `schema_with_rules.sql` directly after initial setup!**

Instead, create a migration:

```bash
# 1. Create a new migration file
cat > migrations/$(date +%Y%m%d_%H%M)_your_change_description.sql << 'EOF'
-- Migration: Add complexity scoring for cards
-- Created: $(date +%Y-%m-%d)
-- Author: Your Name

BEGIN;

-- Add new column
ALTER TABLE cards ADD COLUMN IF NOT EXISTS complexity_score INTEGER;

-- Add index
CREATE INDEX IF NOT EXISTS idx_cards_complexity ON cards(complexity_score);

COMMIT;

-- Rollback:
-- BEGIN;
-- DROP INDEX IF EXISTS idx_cards_complexity;
-- ALTER TABLE cards DROP COLUMN IF EXISTS complexity_score;
-- COMMIT;
EOF

# 2. Apply the migration
psql -U postgres -d vector_mtg -f migrations/20251122_1430_your_change.sql
```

### Migration Best Practices

- **Always use `IF NOT EXISTS` / `IF EXISTS`** - Makes migrations idempotent
- **Wrap in transactions** - Use `BEGIN/COMMIT` for atomicity
- **Document rollback** - Show how to undo the migration
- **Test first** - Apply to a test database before production
- **One change per migration** - Easier to track and rollback
- **Never modify existing migrations** - Create new ones instead

See `migrations/README.md` for detailed guidelines.

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs vector-mtg-postgres

# Restart if needed
docker-compose restart
```

### Memory Issues During Load

If loading fails with memory errors:

```python
# In load_cards_with_keywords.py, reduce batch size:
BATCH_SIZE = 500  # Instead of 1000
```

### Slow Queries

```sql
# Check if indexes exist
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename IN ('cards', 'rules', 'card_rules')
ORDER BY tablename, indexname;

# Create missing indexes
CREATE INDEX idx_cards_embedding ON cards
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Embedding Generation Timeouts

If OpenAI API times out:

```python
# Use local model instead:
EMBEDDING_PROVIDER = 'sentence-transformers'  # Free, no API key needed
```

---

## Architecture Diagram

```
┌─────────────────┐
│  cards.json     │  (2.3GB, 509K cards)
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│  load_cards_with_keywords.py    │  Extract keywords + load data
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  PostgreSQL Database             │
│  ┌─────────────────────────┐    │
│  │ cards (509K rows)       │    │
│  │ - dual embeddings       │    │
│  │ - extracted keywords    │    │
│  └──────────┬──────────────┘    │
│             │                    │
│  ┌──────────v──────────────┐    │
│  │ rules (50+ templates)   │    │
│  │ - rule embeddings       │    │
│  │ - parameters schema     │    │
│  └──────────┬──────────────┘    │
│             │                    │
│  ┌──────────v──────────────┐    │
│  │ card_rules (mappings)   │    │
│  │ - confidence scores     │    │
│  │ - parameter bindings    │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  rule_engine.py                  │  Classification + Matching
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  api_server_rules.py             │  REST API
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  Frontend / Clients              │  Visualization + Analysis
└─────────────────────────────────┘
```

---

## File Checklist

- [x] `schema_with_rules.sql` - Enhanced database schema
- [x] `load_cards_with_keywords.py` - Card loader with keyword extraction
- [x] `seed_rules.sql` - Initial rule templates and categories
- [ ] `generate_embeddings_dual.py` - Dual embedding generator
- [ ] `extract_rules.py` - Auto rule discovery
- [ ] `rule_engine.py` - Rule matching engine
- [ ] `api_server_rules.py` - REST API server
- [x] `RULE_ENGINE_ARCHITECTURE.md` - Architecture documentation
- [x] `VISUALIZATION_GUIDE.md` - Visualization documentation
- [x] `IMPLEMENTATION_GUIDE.md` - This file

---

## Summary

You now have:
1. **A robust schema** that supports rule extraction and classification
2. **Data loaded** with enhanced keyword extraction
3. **Seed rules** representing 50+ common MTG mechanics
4. **Clear architecture** for the rule engine

The remaining work is:
1. Generate embeddings (cards + rules)
2. Auto-discover additional rules through clustering
3. Implement the rule engine class
4. Build the API server

This will give you a complete system for:
- Automatically classifying any MTG card
- Finding cards by mechanical similarity
- Detecting combos and synergies
- Analyzing deck composition
- Generating new card ideas

The rule engine becomes the foundation for understanding MTG at a mechanical level, not just a text level.
