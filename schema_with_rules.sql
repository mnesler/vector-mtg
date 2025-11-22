-- ============================================
-- MTG Vector Database Schema with Rule Engine Support
-- ============================================
-- This schema supports:
-- 1. Card data storage with dual embeddings
-- 2. Rule extraction and classification
-- 3. Card-to-rule mapping with parameter binding
-- 4. Rule interaction detection (combos, synergies)
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================
-- CORE TABLES
-- ============================================

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
    produced_mana TEXT[],           -- Mana colors this card can produce
    data JSONB,                     -- Full card JSON for flexibility
    embedding vector(1536),         -- Card embedding (name + oracle text + type)
    oracle_embedding vector(1536),  -- Oracle text only embedding (for rule matching)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE cards IS 'MTG card data with dual embeddings for similarity search and rule matching';
COMMENT ON COLUMN cards.embedding IS 'Full card embedding: name + type + oracle text + mana cost';
COMMENT ON COLUMN cards.oracle_embedding IS 'Oracle text only embedding for semantic rule matching';
COMMENT ON COLUMN cards.keywords IS 'Extracted keywords and ability words from card text';


-- ============================================
-- RULE TABLES
-- ============================================

-- Rule categories (hierarchical organization)
DROP TABLE IF EXISTS rule_categories CASCADE;
CREATE TABLE rule_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES rule_categories(id),
    icon VARCHAR(50),               -- Optional icon identifier
    color VARCHAR(7),                -- Optional hex color for visualization
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE rule_categories IS 'Hierarchical categories for organizing MTG rules';

CREATE INDEX idx_rule_categories_parent ON rule_categories(parent_category_id);


-- Rules table (extracted patterns and templates)
DROP TABLE IF EXISTS rules CASCADE;
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) NOT NULL UNIQUE,
    rule_template TEXT NOT NULL,           -- Template: "Destroy target [card_type]"
    rule_pattern TEXT,                     -- Regex pattern for matching
    category_id UUID REFERENCES rule_categories(id),
    subcategory VARCHAR(100),              -- Optional subcategory within main category
    parameters JSONB DEFAULT '{}'::jsonb,  -- Parameter schema: {"target_type": "string", "damage": "number"}
    examples TEXT[],                       -- Example oracle texts that match this rule
    card_count INTEGER DEFAULT 0,          -- Cached count of cards using this rule
    confidence DECIMAL DEFAULT 1.0,        -- Confidence score (0-1) for auto-extracted rules
    is_manual BOOLEAN DEFAULT FALSE,       -- TRUE if manually defined, FALSE if auto-extracted
    embedding vector(1536),                -- Embedding of the rule concept
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE rules IS 'Extracted rule templates representing common MTG mechanics';
COMMENT ON COLUMN rules.rule_template IS 'Human-readable rule template with [parameters]';
COMMENT ON COLUMN rules.rule_pattern IS 'Regex pattern for text-based rule matching';
COMMENT ON COLUMN rules.parameters IS 'JSON schema defining extractable parameters';
COMMENT ON COLUMN rules.embedding IS 'Vector embedding for semantic rule matching';

CREATE INDEX idx_rules_category ON rules(category_id);
CREATE INDEX idx_rules_confidence ON rules(confidence);
CREATE INDEX idx_rules_card_count ON rules(card_count DESC);


-- ============================================
-- JUNCTION TABLES
-- ============================================

-- Card-to-Rule mappings (many-to-many)
DROP TABLE IF EXISTS card_rules CASCADE;
CREATE TABLE card_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    confidence DECIMAL NOT NULL DEFAULT 1.0,     -- Match confidence (0-1)
    parameter_bindings JSONB DEFAULT '{}'::jsonb, -- Actual parameter values for this card
    extraction_method VARCHAR(50),               -- 'vector_similarity', 'regex', 'manual'
    extracted_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(card_id, rule_id)
);

COMMENT ON TABLE card_rules IS 'Maps cards to applicable rules with parameter bindings';
COMMENT ON COLUMN card_rules.parameter_bindings IS 'Extracted parameter values specific to this card';
COMMENT ON COLUMN card_rules.extraction_method IS 'How this rule was matched to the card';

CREATE INDEX idx_card_rules_card ON card_rules(card_id);
CREATE INDEX idx_card_rules_rule ON card_rules(rule_id);
CREATE INDEX idx_card_rules_confidence ON card_rules(confidence DESC);


-- ============================================
-- RULE INTERACTIONS
-- ============================================

-- Rule interaction patterns (combos, synergies, counters)
DROP TABLE IF EXISTS rule_interactions CASCADE;
CREATE TABLE rule_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_a_id UUID NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    rule_b_id UUID NOT NULL REFERENCES rules(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL,  -- 'synergy', 'counter', 'combo', 'replacement', 'amplifies'
    description TEXT,
    strength DECIMAL DEFAULT 0.5,           -- Interaction strength (0-1)
    examples JSONB,                         -- Example card pairs demonstrating this interaction
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (rule_a_id != rule_b_id),
    CHECK (strength >= 0 AND strength <= 1)
);

COMMENT ON TABLE rule_interactions IS 'Known interactions between rule patterns (combos, synergies, counters)';

CREATE INDEX idx_rule_interactions_a ON rule_interactions(rule_a_id);
CREATE INDEX idx_rule_interactions_b ON rule_interactions(rule_b_id);
CREATE INDEX idx_rule_interactions_type ON rule_interactions(interaction_type);
CREATE INDEX idx_rule_interactions_strength ON rule_interactions(strength DESC);


-- ============================================
-- KEYWORD ABILITIES
-- ============================================

-- Comprehensive keyword ability definitions
DROP TABLE IF EXISTS keyword_abilities CASCADE;
CREATE TABLE keyword_abilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    rules_text TEXT,                        -- Official comprehensive rules text
    is_evergreen BOOLEAN DEFAULT FALSE,     -- Appears in most sets
    is_ability_word BOOLEAN DEFAULT FALSE,  -- Ability word (e.g., "Landfall") vs keyword
    has_parameter BOOLEAN DEFAULT FALSE,    -- Some keywords have parameters (e.g., "Ward {2}")
    parameter_type VARCHAR(50),             -- 'mana_cost', 'number', 'power_toughness', etc.
    introduced_set VARCHAR(10),
    reminder_text TEXT,                     -- Standard reminder text
    embedding vector(1536),                 -- Embedding for semantic matching
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE keyword_abilities IS 'Standardized MTG keyword abilities and ability words';

CREATE INDEX idx_keywords_evergreen ON keyword_abilities(is_evergreen);


-- ============================================
-- CARD TYPE DEFINITIONS
-- ============================================

-- Standardized card type hierarchies
DROP TABLE IF EXISTS card_type_definitions CASCADE;
CREATE TABLE card_type_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type_name VARCHAR(100) NOT NULL UNIQUE,
    supertype VARCHAR(50),                  -- 'Basic', 'Legendary', 'Snow', etc.
    type_category VARCHAR(50) NOT NULL,     -- 'Creature', 'Spell', 'Permanent', 'Land'
    is_permanent BOOLEAN DEFAULT FALSE,
    subtype_pattern TEXT,                   -- Pattern for matching subtypes
    rules_text TEXT,                        -- Comprehensive rules reference
    inherent_rules UUID[],                  -- Rules that apply to all cards of this type
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE card_type_definitions IS 'Card type taxonomy and inherent rules';

CREATE INDEX idx_card_types_category ON card_type_definitions(type_category);


-- ============================================
-- INDEXES
-- ============================================

-- Standard card indexes
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_name_lower ON cards(LOWER(name));
CREATE INDEX idx_cards_type ON cards(type_line);
CREATE INDEX idx_cards_set ON cards(set_code);
CREATE INDEX idx_cards_rarity ON cards(rarity);
CREATE INDEX idx_cards_colors ON cards USING GIN(colors);
CREATE INDEX idx_cards_color_identity ON cards USING GIN(color_identity);
CREATE INDEX idx_cards_keywords ON cards USING GIN(keywords);
CREATE INDEX idx_cards_data_gin ON cards USING GIN(data jsonb_path_ops);
CREATE INDEX idx_cards_cmc ON cards(cmc);
CREATE INDEX idx_cards_released ON cards(released_at);

-- Vector indexes (create AFTER loading embeddings for optimal performance)
-- Uncomment after embeddings are generated:
-- CREATE INDEX idx_cards_embedding ON cards USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_cards_oracle_embedding ON cards USING ivfflat (oracle_embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_rules_embedding ON rules USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
-- CREATE INDEX idx_keywords_embedding ON keyword_abilities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);


-- ============================================
-- HELPFUL VIEWS
-- ============================================

-- View: Cards with their associated rules
CREATE OR REPLACE VIEW cards_with_rules AS
SELECT
    c.id,
    c.name,
    c.type_line,
    c.oracle_text,
    c.mana_cost,
    c.cmc,
    c.colors,
    c.color_identity,
    c.keywords,
    c.rarity,
    c.set_code,
    array_agg(DISTINCT r.rule_name ORDER BY r.rule_name) FILTER (WHERE r.rule_name IS NOT NULL) as rules,
    array_agg(DISTINCT rc.name ORDER BY rc.name) FILTER (WHERE rc.name IS NOT NULL) as rule_categories,
    COUNT(DISTINCT cr.rule_id) as rule_count
FROM cards c
LEFT JOIN card_rules cr ON c.id = cr.card_id
LEFT JOIN rules r ON cr.rule_id = r.id
LEFT JOIN rule_categories rc ON r.category_id = rc.id
GROUP BY c.id, c.name, c.type_line, c.oracle_text, c.mana_cost, c.cmc,
         c.colors, c.color_identity, c.keywords, c.rarity, c.set_code;

COMMENT ON VIEW cards_with_rules IS 'Cards enriched with their associated rule classifications';


-- View: Rules with statistics
CREATE OR REPLACE VIEW rules_with_stats AS
SELECT
    r.id,
    r.rule_name,
    r.rule_template,
    r.category_id,
    rc.name as category_name,
    r.subcategory,
    r.confidence,
    r.is_manual,
    COUNT(cr.card_id) as card_count,
    AVG(cr.confidence) as avg_match_confidence,
    array_agg(c.name ORDER BY cr.confidence DESC)
        FILTER (WHERE c.name IS NOT NULL)
        LIMIT 10 as example_cards
FROM rules r
LEFT JOIN rule_categories rc ON r.category_id = rc.id
LEFT JOIN card_rules cr ON r.id = cr.rule_id
LEFT JOIN cards c ON cr.card_id = c.id
GROUP BY r.id, r.rule_name, r.rule_template, r.category_id, rc.name,
         r.subcategory, r.confidence, r.is_manual;

COMMENT ON VIEW rules_with_stats IS 'Rules with card counts and example cards';


-- View: Card type distribution
CREATE OR REPLACE VIEW card_type_stats AS
SELECT
    CASE
        WHEN type_line LIKE '%Creature%' THEN 'Creature'
        WHEN type_line LIKE '%Instant%' THEN 'Instant'
        WHEN type_line LIKE '%Sorcery%' THEN 'Sorcery'
        WHEN type_line LIKE '%Enchantment%' THEN 'Enchantment'
        WHEN type_line LIKE '%Artifact%' THEN 'Artifact'
        WHEN type_line LIKE '%Planeswalker%' THEN 'Planeswalker'
        WHEN type_line LIKE '%Land%' THEN 'Land'
        WHEN type_line LIKE '%Battle%' THEN 'Battle'
        ELSE 'Other'
    END as card_type,
    COUNT(*) as count,
    COUNT(embedding) as with_full_embeddings,
    COUNT(oracle_embedding) as with_oracle_embeddings,
    array_agg(DISTINCT rarity ORDER BY rarity) as rarities
FROM cards
GROUP BY card_type
ORDER BY count DESC;

COMMENT ON VIEW card_type_stats IS 'Card type distribution and embedding coverage';


-- View: Rule category hierarchy
CREATE OR REPLACE VIEW rule_category_tree AS
WITH RECURSIVE category_tree AS (
    -- Root categories
    SELECT
        id,
        name,
        description,
        parent_category_id,
        name as path,
        0 as depth
    FROM rule_categories
    WHERE parent_category_id IS NULL

    UNION ALL

    -- Child categories
    SELECT
        rc.id,
        rc.name,
        rc.description,
        rc.parent_category_id,
        ct.path || ' > ' || rc.name as path,
        ct.depth + 1 as depth
    FROM rule_categories rc
    INNER JOIN category_tree ct ON rc.parent_category_id = ct.id
)
SELECT * FROM category_tree
ORDER BY path;

COMMENT ON VIEW rule_category_tree IS 'Hierarchical view of rule categories with full path';


-- View: Database statistics
CREATE OR REPLACE VIEW database_stats AS
SELECT
    (SELECT COUNT(*) FROM cards) as total_cards,
    (SELECT COUNT(*) FROM cards WHERE embedding IS NOT NULL) as cards_with_embeddings,
    (SELECT COUNT(*) FROM cards WHERE oracle_embedding IS NOT NULL) as cards_with_oracle_embeddings,
    (SELECT COUNT(DISTINCT name) FROM cards) as unique_card_names,
    (SELECT COUNT(DISTINCT set_code) FROM cards) as total_sets,
    (SELECT COUNT(*) FROM rules) as total_rules,
    (SELECT COUNT(*) FROM rules WHERE is_manual = TRUE) as manual_rules,
    (SELECT COUNT(*) FROM rule_categories) as total_categories,
    (SELECT COUNT(*) FROM card_rules) as total_card_rule_mappings,
    (SELECT COUNT(*) FROM rule_interactions) as total_rule_interactions,
    (SELECT COUNT(*) FROM keyword_abilities) as total_keywords;

COMMENT ON VIEW database_stats IS 'Overall database statistics dashboard';


-- ============================================
-- FUNCTIONS
-- ============================================

-- Function: Update rule card counts (call after inserting card_rules)
CREATE OR REPLACE FUNCTION update_rule_card_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE rules
    SET card_count = (
        SELECT COUNT(DISTINCT card_id)
        FROM card_rules
        WHERE rule_id = NEW.rule_id
    ),
    updated_at = NOW()
    WHERE id = NEW.rule_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update rule card counts
DROP TRIGGER IF EXISTS trigger_update_rule_card_counts ON card_rules;
CREATE TRIGGER trigger_update_rule_card_counts
    AFTER INSERT OR DELETE ON card_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_rule_card_counts();


-- Function: Find similar cards by vector
CREATE OR REPLACE FUNCTION find_similar_cards(
    target_card_id UUID,
    similarity_threshold DECIMAL DEFAULT 0.7,
    result_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    name VARCHAR(255),
    type_line VARCHAR(255),
    similarity DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.type_line,
        (1 - (c.embedding <#> (SELECT embedding FROM cards WHERE id = target_card_id)))::DECIMAL as similarity
    FROM cards c
    WHERE c.id != target_card_id
        AND c.embedding IS NOT NULL
        AND (1 - (c.embedding <#> (SELECT embedding FROM cards WHERE id = target_card_id))) > similarity_threshold
    ORDER BY c.embedding <#> (SELECT embedding FROM cards WHERE id = target_card_id)
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_similar_cards IS 'Find cards similar to target card using vector embeddings';


-- ============================================
-- COMPLETION MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MTG Vector Database Schema Created';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables: cards, rules, rule_categories, card_rules, rule_interactions, keyword_abilities, card_type_definitions';
    RAISE NOTICE 'Views: cards_with_rules, rules_with_stats, card_type_stats, rule_category_tree, database_stats';
    RAISE NOTICE 'Functions: update_rule_card_counts(), find_similar_cards()';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Load cards: python load_cards_with_keywords.py';
    RAISE NOTICE '2. Seed rules: psql -U postgres -d vector_mtg -f seed_rules.sql';
    RAISE NOTICE '3. Generate embeddings: python generate_embeddings_dual.py';
    RAISE NOTICE '4. Extract rules: python extract_rules.py';
    RAISE NOTICE '========================================';
END $$;
