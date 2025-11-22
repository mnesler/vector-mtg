# MTG Rule Engine Architecture

## Overview

This document describes the architecture for extracting generalized rules from MTG card data using vector embeddings, then using those rules to power a rule engine that can understand, categorize, and reason about any MTG card.

---

## Core Concept

Instead of just finding similar cards, we want to:

1. **Extract common patterns** from card text (e.g., "destroy target creature", "draw N cards", "deals N damage")
2. **Create standardized rules** that describe these patterns
3. **Map cards to rules** they follow
4. **Use vector embeddings** to match cards to rules semantically
5. **Power a rule engine** that can evaluate card interactions, legality, and mechanics

---

## Database Schema

### Enhanced Schema with Rules Support

```sql
-- ============================================
-- Core Tables
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cards table (enhanced for rule extraction)
DROP TABLE IF EXISTS cards CASCADE;
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
    power VARCHAR(10),              -- For creatures
    toughness VARCHAR(10),          -- For creatures
    loyalty VARCHAR(10),            -- For planeswalkers
    keywords TEXT[],                -- Extracted keywords: ["flying", "trample", "haste"]
    data JSONB,                     -- Full card JSON
    embedding vector(1536),         -- Card embedding (name + oracle text + type)
    oracle_embedding vector(1536),  -- Oracle text only embedding (for rule matching)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- ============================================
-- Rule Tables
-- ============================================

-- Rule categories (high-level groupings)
DROP TABLE IF EXISTS rule_categories CASCADE;
CREATE TABLE rule_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES rule_categories(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example categories:
-- - Card Draw
-- - Removal (Creature, Permanent, Planeswalker)
-- - Mana Production
-- - Life Gain/Loss
-- - Token Generation
-- - Counterspells
-- - Tutors
-- - Graveyard Interaction
-- - Combat Mechanics
-- - Triggered Abilities
-- - Activated Abilities


-- Rules table (extracted patterns)
DROP TABLE IF EXISTS rules CASCADE;
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) NOT NULL,
    rule_template TEXT NOT NULL,           -- Template: "Destroy target [card_type]"
    rule_pattern TEXT NOT NULL,            -- Regex or pattern: "destroy.+target.+(creature|permanent)"
    category_id UUID REFERENCES rule_categories(id),
    parameters JSONB,                      -- {"target_type": "creature", "conditions": [...]}
    examples TEXT[],                       -- Example card texts that match this rule
    card_count INTEGER DEFAULT 0,          -- Number of cards using this rule
    confidence DECIMAL DEFAULT 1.0,        -- Confidence score (0-1)
    embedding vector(1536),                -- Embedding of the rule concept
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example rules:
-- {
--   "rule_name": "targeted_creature_removal",
--   "rule_template": "Destroy target creature",
--   "rule_pattern": "destroy.+target.+creature",
--   "parameters": {
--     "target_type": "creature",
--     "action": "destroy",
--     "conditions": []
--   }
-- }


-- ============================================
-- Junction Tables
-- ============================================

-- Many-to-many: Cards can follow multiple rules
DROP TABLE IF EXISTS card_rules CASCADE;
CREATE TABLE card_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    confidence DECIMAL NOT NULL DEFAULT 1.0,     -- How well the card matches this rule (0-1)
    parameter_bindings JSONB,                    -- Specific parameter values for this card
    extracted_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(card_id, rule_id)
);

-- Example binding:
-- Card: "Lightning Bolt"
-- Rule: "direct_damage_spell"
-- parameter_bindings: {
--   "damage_amount": 3,
--   "target_type": "any_target",
--   "cost": "{R}"
-- }


-- ============================================
-- Rule Interactions (Advanced)
-- ============================================

-- Store known rule interactions/combinations
DROP TABLE IF EXISTS rule_interactions CASCADE;
CREATE TABLE rule_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_a_id UUID NOT NULL REFERENCES rules(id),
    rule_b_id UUID NOT NULL REFERENCES rules(id),
    interaction_type VARCHAR(50) NOT NULL,  -- 'synergy', 'counter', 'combo', 'replacement'
    description TEXT,
    strength DECIMAL DEFAULT 0.5,           -- Interaction strength (0-1)
    examples JSONB,                         -- Example card pairs
    created_at TIMESTAMP DEFAULT NOW(),

    CHECK (rule_a_id != rule_b_id)
);


-- ============================================
-- Card Type Definitions
-- ============================================

-- Standardized card type hierarchies
DROP TABLE IF EXISTS card_type_definitions CASCADE;
CREATE TABLE card_type_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type_name VARCHAR(100) NOT NULL UNIQUE,
    supertype VARCHAR(50),                  -- 'basic', 'legendary', 'snow', etc.
    type_category VARCHAR(50) NOT NULL,     -- 'creature', 'spell', 'permanent', 'land'
    subtype_pattern TEXT,                   -- Pattern for matching subtypes
    rules_text TEXT,                        -- Comprehensive rules reference
    inherent_rules UUID[],                  -- Rules that apply to all cards of this type
    created_at TIMESTAMP DEFAULT NOW()
);


-- ============================================
-- Keyword Abilities
-- ============================================

-- Comprehensive keyword ability definitions
DROP TABLE IF EXISTS keyword_abilities CASCADE;
CREATE TABLE keyword_abilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    rules_text TEXT NOT NULL,               -- Official comprehensive rules text
    is_evergreen BOOLEAN DEFAULT FALSE,     -- Appears in most sets
    introduced_set VARCHAR(10),
    parameters JSONB,                       -- Some keywords have parameters (e.g., "Prowess 2")
    embedding vector(1536),                 -- Embedding for semantic matching
    created_at TIMESTAMP DEFAULT NOW()
);


-- ============================================
-- Indexes
-- ============================================

-- Card indexes
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_type ON cards(type_line);
CREATE INDEX idx_cards_set ON cards(set_code);
CREATE INDEX idx_cards_rarity ON cards(rarity);
CREATE INDEX idx_cards_colors ON cards USING GIN(colors);
CREATE INDEX idx_cards_keywords ON cards USING GIN(keywords);
CREATE INDEX idx_cards_data_gin ON cards USING GIN(data jsonb_path_ops);

-- Vector indexes (create AFTER loading embeddings)
-- CREATE INDEX idx_cards_embedding ON cards USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_cards_oracle_embedding ON cards USING ivfflat (oracle_embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_rules_embedding ON cards USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
-- CREATE INDEX idx_keywords_embedding ON keyword_abilities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);

-- Rule indexes
CREATE INDEX idx_rules_category ON rules(category_id);
CREATE INDEX idx_rules_confidence ON rules(confidence);
CREATE INDEX idx_card_rules_card ON card_rules(card_id);
CREATE INDEX idx_card_rules_rule ON card_rules(rule_id);
CREATE INDEX idx_card_rules_confidence ON card_rules(confidence);

-- Interaction indexes
CREATE INDEX idx_rule_interactions_a ON rule_interactions(rule_a_id);
CREATE INDEX idx_rule_interactions_b ON rule_interactions(rule_b_id);
CREATE INDEX idx_rule_interactions_type ON rule_interactions(interaction_type);


-- ============================================
-- Helpful Views
-- ============================================

-- View: Cards with their rules
CREATE VIEW cards_with_rules AS
SELECT
    c.id,
    c.name,
    c.type_line,
    c.oracle_text,
    c.mana_cost,
    c.colors,
    array_agg(DISTINCT r.rule_name) as rules,
    array_agg(DISTINCT rc.name) as rule_categories,
    c.keywords
FROM cards c
LEFT JOIN card_rules cr ON c.id = cr.card_id
LEFT JOIN rules r ON cr.rule_id = r.id
LEFT JOIN rule_categories rc ON r.category_id = rc.id
GROUP BY c.id, c.name, c.type_line, c.oracle_text, c.mana_cost, c.colors, c.keywords;


-- View: Rules with card counts
CREATE VIEW rules_with_stats AS
SELECT
    r.id,
    r.rule_name,
    r.rule_template,
    rc.name as category,
    COUNT(cr.card_id) as card_count,
    AVG(cr.confidence) as avg_confidence,
    array_agg(c.name ORDER BY cr.confidence DESC) FILTER (WHERE c.name IS NOT NULL) as example_cards
FROM rules r
LEFT JOIN rule_categories rc ON r.category_id = rc.id
LEFT JOIN card_rules cr ON r.id = cr.rule_id
LEFT JOIN cards c ON cr.card_id = c.id
GROUP BY r.id, r.rule_name, r.rule_template, rc.name;


-- View: Card type distribution
CREATE VIEW card_type_stats AS
SELECT
    CASE
        WHEN type_line LIKE '%Creature%' THEN 'Creature'
        WHEN type_line LIKE '%Instant%' THEN 'Instant'
        WHEN type_line LIKE '%Sorcery%' THEN 'Sorcery'
        WHEN type_line LIKE '%Enchantment%' THEN 'Enchantment'
        WHEN type_line LIKE '%Artifact%' THEN 'Artifact'
        WHEN type_line LIKE '%Planeswalker%' THEN 'Planeswalker'
        WHEN type_line LIKE '%Land%' THEN 'Land'
        ELSE 'Other'
    END as card_type,
    COUNT(*) as count,
    COUNT(embedding) as with_embeddings,
    array_agg(DISTINCT rarity) as rarities
FROM cards
GROUP BY card_type
ORDER BY count DESC;
```

---

## Rule Extraction Strategy

### Phase 1: Keyword Extraction

Extract standardized MTG keywords from oracle text:

```python
# Common MTG keywords to extract
EVERGREEN_KEYWORDS = [
    'flying', 'first strike', 'double strike', 'deathtouch',
    'defender', 'haste', 'hexproof', 'indestructible',
    'lifelink', 'menace', 'reach', 'trample', 'vigilance',
    'ward', 'flash', 'prowess'
]

ABILITY_KEYWORDS = [
    'enters the battlefield', 'leaves the battlefield',
    'when.*dies', 'at the beginning', 'at end of turn',
    'destroy target', 'exile target', 'draw.*card',
    'search.*library', 'return.*from.*graveyard',
    'create.*token', 'deals.*damage', 'gain.*life',
    'counter target', 'sacrifice', 'tap', 'untap'
]

def extract_keywords(oracle_text):
    """Extract keywords and abilities from card text."""
    if not oracle_text:
        return []

    keywords = []
    text_lower = oracle_text.lower()

    # Extract evergreen keywords
    for keyword in EVERGREEN_KEYWORDS:
        if keyword in text_lower:
            keywords.append(keyword)

    # Extract ability patterns (using regex)
    import re
    for pattern in ABILITY_KEYWORDS:
        if re.search(pattern, text_lower):
            keywords.append(pattern.replace('.*', ' '))

    return list(set(keywords))
```

### Phase 2: Rule Template Extraction

Use vector clustering to find common patterns:

```python
# Pseudo-code for rule extraction
def extract_rules_from_cards(cards):
    """
    Cluster cards by oracle text similarity,
    then extract common rule templates from each cluster.
    """

    # 1. Generate embeddings for oracle texts
    oracle_embeddings = [
        generate_embedding(card['oracle_text'])
        for card in cards
        if card['oracle_text']
    ]

    # 2. Cluster similar oracle texts
    from sklearn.cluster import DBSCAN
    clustering = DBSCAN(eps=0.15, min_samples=5, metric='cosine')
    labels = clustering.fit_predict(oracle_embeddings)

    # 3. For each cluster, extract common template
    rules = []
    for cluster_id in set(labels):
        if cluster_id == -1:  # Noise
            continue

        cluster_cards = [
            cards[i] for i, label in enumerate(labels)
            if label == cluster_id
        ]

        # Extract common pattern
        rule_template = extract_common_pattern(cluster_cards)

        rules.append({
            'rule_template': rule_template,
            'examples': [c['oracle_text'] for c in cluster_cards[:5]],
            'card_count': len(cluster_cards),
            'embedding': np.mean([oracle_embeddings[i] for i, l in enumerate(labels) if l == cluster_id], axis=0)
        })

    return rules


def extract_common_pattern(cards):
    """
    Extract common text pattern from similar cards.
    Uses LLM or rule-based extraction.
    """
    # Example: Use LLM to extract pattern
    oracle_texts = [c['oracle_text'] for c in cards[:10]]

    prompt = f"""
    Analyze these MTG card texts and extract a generalized rule template:

    {chr(10).join(f"- {text}" for text in oracle_texts)}

    Extract a template in this format:
    - Template: "[ACTION] [TARGET] [CONDITIONS]"
    - Parameters: list of variable parts
    - Category: type of effect
    """

    # Call LLM or use pattern matching
    # Return extracted template
    pass
```

### Phase 3: Parameter Binding

Map specific cards to rule templates with parameter values:

```python
def bind_card_to_rule(card, rule):
    """
    Extract specific parameter values from card text
    based on rule template.
    """
    parameters = {}

    # Example: "Destroy target creature" rule
    if rule['rule_template'] == "Destroy target [card_type]":
        # Extract card type from oracle text
        import re
        match = re.search(r'destroy target (\w+)', card['oracle_text'], re.IGNORECASE)
        if match:
            parameters['card_type'] = match.group(1)

    # Example: "Draw N cards" rule
    if rule['rule_template'] == "Draw [N] cards":
        match = re.search(r'draw (\d+|\w+) cards?', card['oracle_text'], re.IGNORECASE)
        if match:
            parameters['N'] = match.group(1)

    return parameters
```

---

## Dual Embedding Strategy

### Why Two Embeddings Per Card?

1. **Full Card Embedding** (`embedding`):
   - Includes: name + type_line + oracle_text + mana_cost
   - Use for: Finding similar cards holistically
   - Example: "Lightning Bolt" → finds other efficient red burn spells

2. **Oracle Text Embedding** (`oracle_embedding`):
   - Includes: oracle_text only
   - Use for: Matching cards to rules based on mechanics
   - Example: "Destroy target creature" → finds all creature removal regardless of name/cost

### Embedding Generation

```python
def generate_card_embeddings(card):
    """Generate both embeddings for a card."""

    # Full card embedding (for similarity search)
    full_text = ' | '.join(filter(None, [
        card.get('name'),
        card.get('type_line'),
        card.get('mana_cost'),
        card.get('oracle_text')
    ]))

    # Oracle embedding (for rule matching)
    oracle_text = card.get('oracle_text', '')

    embeddings = client.embeddings.create(
        input=[full_text, oracle_text],
        model='text-embedding-3-small'
    )

    return {
        'embedding': embeddings.data[0].embedding,
        'oracle_embedding': embeddings.data[1].embedding
    }
```

---

## Rule Engine Architecture

### Rule Engine Components

```python
class MTGRuleEngine:
    """
    Rule engine for evaluating MTG card mechanics and interactions.
    """

    def __init__(self, db_connection):
        self.db = db_connection
        self.rule_cache = {}
        self.keyword_cache = {}

    def classify_card(self, card_id):
        """
        Classify a card by matching it to known rules.
        Returns list of applicable rules with confidence scores.
        """
        # Get card's oracle embedding
        card = self.get_card(card_id)
        oracle_emb = card['oracle_embedding']

        # Find matching rules using vector similarity
        matching_rules = self.db.execute("""
            SELECT
                id,
                rule_name,
                rule_template,
                parameters,
                1 - (embedding <#> %s::vector) as confidence
            FROM rules
            WHERE 1 - (embedding <#> %s::vector) > 0.7  -- Threshold
            ORDER BY confidence DESC
            LIMIT 10
        """, (oracle_emb, oracle_emb))

        # Extract parameters for each matching rule
        results = []
        for rule in matching_rules:
            params = self.extract_parameters(card, rule)
            results.append({
                'rule': rule,
                'parameters': params,
                'confidence': rule['confidence']
            })

        return results

    def find_cards_by_rule(self, rule_name, parameter_constraints=None):
        """
        Find all cards that match a specific rule with given parameters.

        Example:
            find_cards_by_rule(
                'targeted_removal',
                {'target_type': 'creature', 'cost_cmc_lte': 2}
            )
        """
        query = """
            SELECT c.*
            FROM cards c
            JOIN card_rules cr ON c.id = cr.card_id
            JOIN rules r ON cr.rule_id = r.id
            WHERE r.rule_name = %s
        """
        params = [rule_name]

        # Add parameter constraints
        if parameter_constraints:
            for key, value in parameter_constraints.items():
                query += f" AND cr.parameter_bindings->>'{key}' = %s"
                params.append(str(value))

        return self.db.execute(query, params)

    def check_interaction(self, card_a_id, card_b_id):
        """
        Check if two cards have known interactions (combo, synergy, counter).
        """
        # Get rules for both cards
        rules_a = self.get_card_rules(card_a_id)
        rules_b = self.get_card_rules(card_b_id)

        # Check for known rule interactions
        interactions = []
        for rule_a in rules_a:
            for rule_b in rules_b:
                interaction = self.db.execute("""
                    SELECT *
                    FROM rule_interactions
                    WHERE (rule_a_id = %s AND rule_b_id = %s)
                       OR (rule_a_id = %s AND rule_b_id = %s)
                """, (rule_a['id'], rule_b['id'], rule_b['id'], rule_a['id']))

                if interaction:
                    interactions.append(interaction)

        return interactions

    def suggest_similar_cards(self, card_id, rule_filter=None):
        """
        Suggest cards similar to the given card,
        optionally filtered by specific rules.
        """
        card = self.get_card(card_id)

        query = """
            SELECT
                c.*,
                1 - (c.embedding <#> %s::vector) as similarity
            FROM cards c
            WHERE c.id != %s
        """
        params = [card['embedding'], card_id]

        if rule_filter:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM card_rules cr
                    JOIN rules r ON cr.rule_id = r.id
                    WHERE cr.card_id = c.id
                      AND r.rule_name = %s
                )
            """
            params.append(rule_filter)

        query += " ORDER BY similarity DESC LIMIT 20"

        return self.db.execute(query, params)

    def validate_deck(self, deck_card_ids):
        """
        Validate a deck and suggest improvements based on rules.
        """
        # Analyze deck composition by rules
        rule_distribution = self.db.execute("""
            SELECT
                r.rule_name,
                rc.name as category,
                COUNT(*) as count
            FROM card_rules cr
            JOIN rules r ON cr.rule_id = r.id
            JOIN rule_categories rc ON r.category_id = rc.id
            WHERE cr.card_id = ANY(%s)
            GROUP BY r.rule_name, rc.name
            ORDER BY count DESC
        """, (deck_card_ids,))

        # Check for missing essential categories
        essential_categories = ['Card Draw', 'Removal', 'Mana Production']
        present_categories = {row['category'] for row in rule_distribution}
        missing = set(essential_categories) - present_categories

        return {
            'rule_distribution': rule_distribution,
            'missing_categories': list(missing),
            'suggestions': self.suggest_cards_for_categories(missing, deck_card_ids)
        }
```

---

## Example Rule Definitions

### Seed Rules to Start With

```sql
-- Insert rule categories
INSERT INTO rule_categories (name, description) VALUES
    ('Removal', 'Effects that remove permanents or creatures'),
    ('Card Draw', 'Effects that draw cards'),
    ('Mana Production', 'Effects that produce mana'),
    ('Life Manipulation', 'Effects that gain or lose life'),
    ('Token Generation', 'Effects that create tokens'),
    ('Counterspells', 'Effects that counter spells'),
    ('Tutors', 'Effects that search library for cards'),
    ('Graveyard Interaction', 'Effects that interact with graveyard'),
    ('Combat Mechanics', 'Effects related to combat'),
    ('Tribal Synergy', 'Effects that benefit specific creature types');

-- Insert example rules
WITH removal_cat AS (
    SELECT id FROM rule_categories WHERE name = 'Removal'
),
draw_cat AS (
    SELECT id FROM rule_categories WHERE name = 'Card Draw'
)
INSERT INTO rules (rule_name, rule_template, rule_pattern, category_id, parameters) VALUES
    (
        'targeted_creature_destruction',
        'Destroy target creature',
        'destroy.+target.+creature',
        (SELECT id FROM removal_cat),
        '{"action": "destroy", "target_type": "creature", "target_count": 1}'::jsonb
    ),
    (
        'board_wipe',
        'Destroy all creatures',
        'destroy.+all.+creatures',
        (SELECT id FROM removal_cat),
        '{"action": "destroy", "target_type": "creature", "target_count": "all"}'::jsonb
    ),
    (
        'card_draw_fixed',
        'Draw N cards',
        'draw.+(\\d+|a|one|two|three).+cards?',
        (SELECT id FROM draw_cat),
        '{"action": "draw", "quantity_type": "fixed"}'::jsonb
    ),
    (
        'card_draw_conditional',
        'Draw cards based on condition',
        'draw.+cards?.+(equal|for each)',
        (SELECT id FROM draw_cat),
        '{"action": "draw", "quantity_type": "conditional"}'::jsonb
    );
```

---

## Next Steps

1. **Implement rule extraction pipeline**
2. **Generate embeddings for cards AND rules**
3. **Build rule matching system using vector similarity**
4. **Create rule engine API endpoints**
5. **Build UI for exploring rules and card classifications**

This architecture will allow you to:
- Automatically classify new cards based on learned rules
- Find cards that follow specific mechanical patterns
- Build a deck validator based on rule composition
- Discover card interactions through rule relationships
- Generate new card ideas based on rule combinations
