# Tags & Rules Schema Design

**Goal:** Build a system to tag cards with functional mechanics and extract abstract rules for combo discovery.

**Approach:** Incremental, LLM-based, one function at a time

---

## Table of Contents

1. [Conceptual Model](#conceptual-model)
2. [Schema Design Options](#schema-design-options)
3. [Recommended Schema](#recommended-schema)
4. [Tag Taxonomy](#tag-taxonomy)
5. [Rule Abstraction Format](#rule-abstraction-format)
6. [Implementation Plan](#implementation-plan)

---

## Conceptual Model

### Three Layers of Card Understanding

```
Layer 1: TAGS (Functional Mechanics)
    ↓ What the card DOES
    Examples: generates_mana, untaps_permanents, triggers_on_death

Layer 2: ABSTRACTIONS (Generalized Rules)
    ↓ HOW the card does it (abstracted)
    Examples: "Pay {U}: Untap target permanent", "ETB: Draw cards equal to artifacts you control"

Layer 3: ORACLE TEXT (Specific Implementation)
    ↓ Exact card text
    Examples: "Pemmin's Aura: {U}: Untap enchanted creature"
```

### Relationships

```
CARD
  │
  ├─── has many ───> TAGS
  │                  (generates_mana, untaps_permanents)
  │
  ├─── has many ───> ABSTRACTIONS
  │                  (Cost-reducer, Untap effect, Draw engine)
  │
  └─── maps to ───> MTG RULES
                    (Comprehensive rules from rulebook)
```

---

## Schema Design Options

### Option A: Tags as Array (Simple, Fast)

```sql
-- Add tags column to existing cards table
ALTER TABLE cards
ADD COLUMN tags TEXT[];

ALTER TABLE cards
ADD COLUMN abstractions JSONB;

-- Example data
{
    "id": "abc-123",
    "name": "Pemmin's Aura",
    "tags": ["untaps_permanents", "grants_ability", "aura"],
    "abstractions": [
        {
            "type": "activated_ability",
            "cost": "{U}",
            "effect": "untap_target_permanent",
            "scope": "enchanted_creature"
        }
    ]
}

-- Index for tag searches
CREATE INDEX idx_cards_tags ON cards USING GIN(tags);
```

**Pros:**
- Simple schema
- Fast queries (GIN index)
- Easy to update
- No joins needed

**Cons:**
- No tag metadata (descriptions, categories)
- Hard to rename tags globally
- Can't aggregate tag usage
- No tag relationships

---

### Option B: Tags as Normalized Table (Structured, Scalable)

```sql
-- Tag definitions
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- "generates_mana"
    display_name TEXT,                       -- "Generates Mana"
    category TEXT,                           -- "resource_generation"
    description TEXT,                        -- "Card produces mana of any type"

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Card-to-tag assignments (junction table)
CREATE TABLE card_tags (
    id SERIAL PRIMARY KEY,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,

    -- Optional: Context about this specific assignment
    confidence NUMERIC DEFAULT 1.0,          -- 0-1, how confident is this tag?
    source TEXT,                             -- "llm", "manual", "pattern_match"

    UNIQUE(card_id, tag_id)
);

-- Indexes
CREATE INDEX idx_card_tags_card_id ON card_tags(card_id);
CREATE INDEX idx_card_tags_tag_id ON card_tags(tag_id);
CREATE INDEX idx_tags_category ON tags(category);

-- View for easy querying
CREATE VIEW cards_with_tags AS
SELECT
    c.*,
    ARRAY_AGG(t.name) as tag_names,
    ARRAY_AGG(t.category) as tag_categories
FROM cards c
LEFT JOIN card_tags ct ON c.id = ct.card_id
LEFT JOIN tags t ON ct.tag_id = t.id
GROUP BY c.id;
```

**Pros:**
- Tag metadata (descriptions, categories)
- Easy to rename tags globally
- Can track tag usage stats
- Can define tag hierarchies/relationships
- Confidence scores per assignment
- Audit trail (source, timestamps)

**Cons:**
- Requires joins
- More complex queries
- More tables to manage

---

### Option C: Hybrid (Best of Both) ⭐ RECOMMENDED

```sql
-- Tag definitions (normalized)
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    category TEXT,
    description TEXT,
    parent_tag_id INTEGER REFERENCES tags(id),  -- For hierarchies

    created_at TIMESTAMP DEFAULT NOW()
);

-- Card-to-tag assignments (normalized)
CREATE TABLE card_tags (
    id SERIAL PRIMARY KEY,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,

    confidence NUMERIC DEFAULT 1.0,
    source TEXT DEFAULT 'llm',
    extracted_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(card_id, tag_id)
);

-- Denormalized cache on cards table for fast queries
ALTER TABLE cards
ADD COLUMN tag_cache TEXT[],                     -- Array of tag names
ADD COLUMN tag_cache_updated_at TIMESTAMP;

-- Trigger to update cache when card_tags changes
CREATE OR REPLACE FUNCTION update_card_tag_cache()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cards
    SET
        tag_cache = (
            SELECT ARRAY_AGG(t.name)
            FROM card_tags ct
            JOIN tags t ON ct.tag_id = t.id
            WHERE ct.card_id = NEW.card_id
        ),
        tag_cache_updated_at = NOW()
    WHERE id = NEW.card_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_card_tag_cache
AFTER INSERT OR UPDATE OR DELETE ON card_tags
FOR EACH ROW
EXECUTE FUNCTION update_card_tag_cache();

-- Indexes
CREATE INDEX idx_card_tags_card_id ON card_tags(card_id);
CREATE INDEX idx_card_tags_tag_id ON card_tags(tag_id);
CREATE INDEX idx_cards_tag_cache ON cards USING GIN(tag_cache);
```

**Pros:**
- Fast queries (uses cached array)
- Rich metadata (normalized tables)
- Best of both worlds

**Cons:**
- More complex schema
- Cache needs maintenance

---

## Recommended Schema

### Full Schema (Tags + Abstractions)

```sql
-- ============================================================================
-- TAGS: Functional mechanics
-- ============================================================================

-- Tag definitions and categories
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- "generates_mana"
    display_name TEXT,                       -- "Generates Mana"
    category TEXT NOT NULL,                  -- "resource_generation"
    description TEXT,
    parent_tag_id INTEGER REFERENCES tags(id),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tag categories (optional - for better organization)
CREATE TABLE tag_categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- "resource_generation"
    display_name TEXT,                       -- "Resource Generation"
    description TEXT,
    sort_order INTEGER DEFAULT 0
);

-- Card-to-tag assignments
CREATE TABLE card_tags (
    id SERIAL PRIMARY KEY,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,

    -- Confidence and provenance
    confidence NUMERIC DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    source TEXT DEFAULT 'llm',              -- 'llm', 'manual', 'pattern', 'community'
    extracted_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(card_id, tag_id)
);

-- Cached tags on cards table (for performance)
ALTER TABLE cards
ADD COLUMN tag_cache TEXT[],
ADD COLUMN tag_cache_updated_at TIMESTAMP;

-- Indexes
CREATE INDEX idx_tags_category ON tags(category);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_card_tags_card_id ON card_tags(card_id);
CREATE INDEX idx_card_tags_tag_id ON card_tags(tag_id);
CREATE INDEX idx_card_tags_source ON card_tags(source);
CREATE INDEX idx_cards_tag_cache ON cards USING GIN(tag_cache);

-- ============================================================================
-- ABSTRACTIONS: Generalized rules extracted from cards
-- ============================================================================

CREATE TABLE card_abstractions (
    id SERIAL PRIMARY KEY,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,

    -- Abstraction details
    abstraction_type TEXT NOT NULL,         -- 'activated_ability', 'triggered_ability', 'static_effect', 'etb_effect'

    -- Abstracted components (JSONB for flexibility)
    pattern JSONB NOT NULL,                 -- Structured representation of the ability
    /*
    Example pattern:
    {
        "type": "activated_ability",
        "cost": {
            "mana": "{U}",
            "tap": false,
            "additional": []
        },
        "effect": {
            "action": "untap",
            "target": "permanent",
            "scope": "enchanted"
        },
        "restrictions": []
    }
    */

    -- Human-readable abstraction
    abstraction_text TEXT,                  -- "Pay {U}: Untap enchanted creature"

    -- Metadata
    confidence NUMERIC DEFAULT 1.0,
    source TEXT DEFAULT 'llm',
    extracted_at TIMESTAMP DEFAULT NOW(),

    -- For pattern matching
    pattern_hash TEXT,                      -- Hash of pattern for quick lookup

    UNIQUE(card_id, pattern_hash)
);

-- Indexes
CREATE INDEX idx_card_abstractions_card_id ON card_abstractions(card_id);
CREATE INDEX idx_card_abstractions_type ON card_abstractions(abstraction_type);
CREATE INDEX idx_card_abstractions_pattern ON card_abstractions USING GIN(pattern);
CREATE INDEX idx_card_abstractions_hash ON card_abstractions(pattern_hash);

-- ============================================================================
-- VIEWS: Convenient querying
-- ============================================================================

-- Cards with all their tags
CREATE VIEW cards_with_tags AS
SELECT
    c.*,
    COALESCE(c.tag_cache, ARRAY[]::TEXT[]) as tags,
    (
        SELECT json_agg(json_build_object(
            'id', t.id,
            'name', t.name,
            'category', t.category,
            'confidence', ct.confidence
        ))
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE ct.card_id = c.id
    ) as tag_details
FROM cards c;

-- Cards with all their abstractions
CREATE VIEW cards_with_abstractions AS
SELECT
    c.*,
    (
        SELECT json_agg(json_build_object(
            'type', ca.abstraction_type,
            'pattern', ca.pattern,
            'text', ca.abstraction_text,
            'confidence', ca.confidence
        ))
        FROM card_abstractions ca
        WHERE ca.card_id = c.id
    ) as abstractions
FROM cards c;

-- Tag usage statistics
CREATE VIEW tag_stats AS
SELECT
    t.id,
    t.name,
    t.category,
    COUNT(ct.card_id) as card_count,
    AVG(ct.confidence) as avg_confidence
FROM tags t
LEFT JOIN card_tags ct ON t.id = ct.id
GROUP BY t.id, t.name, t.category
ORDER BY card_count DESC;
```

---

## Tag Taxonomy

### Proposed Tag Categories

```sql
-- Seed tag categories
INSERT INTO tag_categories (name, display_name, description, sort_order) VALUES
('resource_generation', 'Resource Generation', 'Cards that generate resources (mana, cards, tokens)', 1),
('resource_cost', 'Resource Costs', 'Cards that require specific costs or sacrifices', 2),
('state_change', 'State Changes', 'Cards that modify game state (untap, blink, bounce)', 3),
('triggers', 'Triggers', 'Cards with triggered abilities', 4),
('effects', 'Effects', 'Specific effects cards create', 5),
('card_types', 'Card Types', 'Structural card type tags', 6),
('combo_enablers', 'Combo Enablers', 'Cards that enable infinite loops', 7),
('win_conditions', 'Win Conditions', 'Cards that win or end the game', 8);
```

### Seed Tags (Starter Set)

```sql
-- RESOURCE GENERATION
INSERT INTO tags (name, display_name, category, description) VALUES
('generates_mana', 'Generates Mana', 'resource_generation', 'Produces mana of any type'),
('draws_cards', 'Draws Cards', 'resource_generation', 'Draws one or more cards'),
('creates_tokens', 'Creates Tokens', 'resource_generation', 'Creates creature or other tokens'),
('searches_library', 'Searches Library', 'resource_generation', 'Tutors cards from library'),
('reanimates', 'Reanimates', 'resource_generation', 'Returns creatures from graveyard to battlefield'),
('ramps', 'Ramps', 'resource_generation', 'Accelerates mana production'),

-- RESOURCE COSTS
('sacrifices_creatures', 'Sacrifices Creatures', 'resource_cost', 'Requires sacrificing creatures'),
('sacrifices_artifacts', 'Sacrifices Artifacts', 'resource_cost', 'Requires sacrificing artifacts'),
('sacrifices_permanents', 'Sacrifices Permanents', 'resource_cost', 'Sacrifices any permanent type'),
('discards_cards', 'Discards Cards', 'resource_cost', 'Requires discarding cards'),
('pays_life', 'Pays Life', 'resource_cost', 'Costs life to activate/cast'),
('taps_permanents', 'Taps Permanents', 'resource_cost', 'Requires tapping permanents'),

-- STATE CHANGES
('untaps_permanents', 'Untaps Permanents', 'state_change', 'Untaps one or more permanents'),
('blinks_creatures', 'Blinks Creatures', 'state_change', 'Exiles and returns creatures'),
('bounces_permanents', 'Bounces Permanents', 'state_change', 'Returns permanents to hand/library'),
('copies_spells', 'Copies Spells', 'state_change', 'Creates copies of spells'),
('reduces_costs', 'Reduces Costs', 'state_change', 'Makes spells/abilities cost less'),
('grants_abilities', 'Grants Abilities', 'state_change', 'Gives abilities to other cards'),

-- TRIGGERS
('triggers_on_etb', 'Triggers on ETB', 'triggers', 'Triggers when permanents enter battlefield'),
('triggers_on_death', 'Triggers on Death', 'triggers', 'Triggers when creatures die'),
('triggers_on_cast', 'Triggers on Cast', 'triggers', 'Triggers when spells are cast'),
('triggers_on_draw', 'Triggers on Draw', 'triggers', 'Triggers when drawing cards'),
('triggers_on_attack', 'Triggers on Attack', 'triggers', 'Triggers when attacking'),
('triggers_on_tap', 'Triggers on Tap', 'triggers', 'Triggers when permanents become tapped'),

-- EFFECTS
('drains_life', 'Drains Life', 'effects', 'Causes opponents to lose life'),
('gains_life', 'Gains Life', 'effects', 'Causes controller to gain life'),
('mills_library', 'Mills Library', 'effects', 'Puts cards from library to graveyard'),
('deals_damage', 'Deals Damage', 'effects', 'Directly deals damage'),
('destroys_permanents', 'Destroys Permanents', 'effects', 'Destroys permanents'),
('exiles_cards', 'Exiles Cards', 'effects', 'Exiles cards from any zone'),

-- COMBO ENABLERS
('infinite_enabler', 'Infinite Enabler', 'combo_enablers', 'Commonly enables infinite combos'),
('loop_component', 'Loop Component', 'combo_enablers', 'Part of common loops'),
('cost_reducer', 'Cost Reducer', 'combo_enablers', 'Makes combos cheaper to execute'),

-- WIN CONDITIONS
('alternate_win_con', 'Alternate Win Condition', 'win_conditions', 'Wins through alternate means'),
('wins_with_empty_library', 'Wins with Empty Library', 'win_conditions', 'Wins when library is empty'),
('wins_with_condition', 'Wins with Condition', 'win_conditions', 'Wins when specific condition met'),

-- CARD TYPES
('creature', 'Creature', 'card_types', 'Creature card'),
('artifact', 'Artifact', 'card_types', 'Artifact card'),
('enchantment', 'Enchantment', 'card_types', 'Enchantment card'),
('instant', 'Instant', 'card_types', 'Instant card'),
('sorcery', 'Sorcery', 'card_types', 'Sorcery card'),
('planeswalker', 'Planeswalker', 'card_types', 'Planeswalker card'),
('land', 'Land', 'card_types', 'Land card'),
('aura', 'Aura', 'card_types', 'Aura subtype'),
('equipment', 'Equipment', 'card_types', 'Equipment subtype');
```

---

## Rule Abstraction Format

### Abstraction Structure (JSONB)

```jsonb
{
    "type": "activated_ability",
    "cost": {
        "mana": "{U}",
        "tap": false,
        "sacrifice": [],
        "discard": 0,
        "life": 0,
        "other": []
    },
    "effect": {
        "action": "untap",          // untap, draw, create_token, etc.
        "target": "permanent",      // permanent, creature, player, etc.
        "scope": "enchanted",       // enchanted, all, target, etc.
        "amount": 1,
        "restrictions": []
    },
    "conditions": [],
    "repeatable": true
}
```

### Examples

**Pemmin's Aura:**
```jsonb
{
    "type": "activated_ability",
    "cost": {"mana": "{U}"},
    "effect": {
        "action": "untap",
        "target": "creature",
        "scope": "enchanted"
    },
    "repeatable": true
}
```

**Ashnod's Altar:**
```jsonb
{
    "type": "activated_ability",
    "cost": {
        "sacrifice": ["creature"]
    },
    "effect": {
        "action": "add_mana",
        "mana_type": "colorless",
        "amount": 2
    },
    "repeatable": true
}
```

**Blood Artist:**
```jsonb
{
    "type": "triggered_ability",
    "trigger": {
        "event": "dies",
        "source": ["creature"],
        "scope": "any"
    },
    "effect": {
        "actions": [
            {
                "action": "lose_life",
                "target": "opponent",
                "amount": 1
            },
            {
                "action": "gain_life",
                "target": "controller",
                "amount": 1
            }
        ]
    }
}
```

---

## Implementation Plan

### Phase 1: Schema Setup (Week 1)

**Tasks:**
1. Create tables (tags, card_tags, card_abstractions)
2. Seed initial tag taxonomy (~50-100 tags)
3. Add indexes
4. Create views
5. Write helper functions

**Deliverables:**
- Schema deployed
- Tag taxonomy seeded
- Ready for data population

---

### Phase 2: Tag Extraction (Week 2-3)

**Tasks:**
1. Write LLM tag extraction function
2. Test on 100 sample cards
3. Refine prompts based on results
4. Batch process all cards (508K)
5. Validate extraction quality

**Deliverables:**
- All cards tagged
- Quality metrics (% coverage, confidence scores)

---

### Phase 3: Abstraction Extraction (Week 4-5)

**Tasks:**
1. Design abstraction patterns
2. Write LLM abstraction extraction
3. Test on complex cards
4. Batch process all cards
5. Build pattern matching system

**Deliverables:**
- Cards have abstract rules
- Pattern database built

---

### Phase 4: Pattern Matching (Week 6)

**Tasks:**
1. Define combo patterns using tags + abstractions
2. Implement pattern matching algorithm
3. Test on known combos
4. Discover new combos
5. Build confidence scoring

**Deliverables:**
- Working combo discovery system
- New combos found

---

## Next Steps

1. **Review and approve schema** ✋ (You are here)
2. **Generate SQL migration script**
3. **Seed tag taxonomy**
4. **Build first LLM extraction function**

What do you think of this schema design? Any changes you'd like before we proceed?

