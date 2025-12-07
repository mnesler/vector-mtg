-- Commander Spellbook PostgreSQL Schema
-- Based on API structure from https://backend.commanderspellbook.com/
-- This schema is idempotent - safe to run multiple times

-- ============================================================================
-- OPTIONAL: Uncomment to drop all existing tables and start fresh
-- WARNING: This will delete ALL data!
-- ============================================================================
/*
DROP TABLE IF EXISTS variant_update_suggestions CASCADE;
DROP TABLE IF EXISTS variant_suggestions CASCADE;
DROP TABLE IF EXISTS variant_aliases CASCADE;
DROP TABLE IF EXISTS variant_prices CASCADE;
DROP TABLE IF EXISTS card_prices CASCADE;
DROP TABLE IF EXISTS variant_legalities CASCADE;
DROP TABLE IF EXISTS card_legalities CASCADE;
DROP TABLE IF EXISTS variant_prerequisites CASCADE;
DROP TABLE IF EXISTS card_features CASCADE;
DROP TABLE IF EXISTS variant_features CASCADE;
DROP TABLE IF EXISTS variant_cards CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS templates CASCADE;
DROP TABLE IF EXISTS variants CASCADE;
DROP TABLE IF EXISTS features CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS properties CASCADE;
*/

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Cards table - stores all MTG cards
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    oracle_id TEXT,
    identity TEXT[], -- Array of color codes: W, U, B, R, G, C
    type_line TEXT,
    oracle_text TEXT,
    keywords TEXT[],
    mana_value NUMERIC,

    -- Card properties (boolean flags)
    spoiler BOOLEAN DEFAULT FALSE,
    reserved BOOLEAN DEFAULT FALSE,
    game_changer BOOLEAN DEFAULT FALSE,
    tutor BOOLEAN DEFAULT FALSE,
    mass_land_denial BOOLEAN DEFAULT FALSE,
    extra_turn BOOLEAN DEFAULT FALSE,
    reprinted BOOLEAN DEFAULT FALSE,

    -- Metadata
    variant_count INTEGER DEFAULT 0,
    latest_printing_set TEXT,

    -- Image URIs (front face)
    image_uri_front_png TEXT,
    image_uri_front_large TEXT,
    image_uri_front_normal TEXT,
    image_uri_front_small TEXT,
    image_uri_front_art_crop TEXT,

    -- Image URIs (back face for double-faced cards)
    image_uri_back_png TEXT,
    image_uri_back_large TEXT,
    image_uri_back_normal TEXT,
    image_uri_back_small TEXT,
    image_uri_back_art_crop TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cards
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_oracle_id ON cards(oracle_id);
CREATE INDEX IF NOT EXISTS idx_cards_identity ON cards USING GIN(identity);
CREATE INDEX IF NOT EXISTS idx_cards_type_line ON cards(type_line);
CREATE INDEX IF NOT EXISTS idx_cards_keywords ON cards USING GIN(keywords);


-- Features table - combo outcomes/effects
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    uncountable BOOLEAN DEFAULT FALSE,
    status CHAR(2), -- H (Helper), S (Standalone), C (Contextual), PU (Public Utility)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_features_name ON features(name);
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);


-- Variants table - card combinations/combos
CREATE TABLE IF NOT EXISTS variants (
    id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'OK', -- OK, NeedsReview, etc.
    identity TEXT[], -- Color identity array
    mana_needed TEXT,
    description TEXT, -- Step-by-step combo explanation
    variant_count INTEGER DEFAULT 0,
    popularity INTEGER DEFAULT 0,

    -- Metadata
    spoiler BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_variants_identity ON variants USING GIN(identity);
CREATE INDEX IF NOT EXISTS idx_variants_status ON variants(status);
CREATE INDEX IF NOT EXISTS idx_variants_popularity ON variants(popularity DESC);


-- Templates table - combo templates
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Users table - for community features
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);


-- ============================================================================
-- RELATIONSHIP TABLES (Many-to-Many)
-- ============================================================================

-- Cards used in variants (with additional context)
CREATE TABLE IF NOT EXISTS variant_cards (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,

    -- Usage details
    quantity INTEGER DEFAULT 1,
    zone TEXT, -- battlefield, hand, graveyard, command zone, etc.
    zone_locations TEXT[], -- specific locations within zone
    battlefield_card_state TEXT, -- tapped, untapped, etc.
    must_be_commander BOOLEAN DEFAULT FALSE,

    UNIQUE(variant_id, card_id, zone)
);

CREATE INDEX IF NOT EXISTS idx_variant_cards_variant ON variant_cards(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_cards_card ON variant_cards(card_id);
CREATE INDEX IF NOT EXISTS idx_variant_cards_zone ON variant_cards(zone);


-- Features produced by variants
CREATE TABLE IF NOT EXISTS variant_features (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,

    UNIQUE(variant_id, feature_id)
);

CREATE INDEX IF NOT EXISTS idx_variant_features_variant ON variant_features(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_features_feature ON variant_features(feature_id);


-- Features associated with cards
CREATE TABLE IF NOT EXISTS card_features (
    id SERIAL PRIMARY KEY,
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,

    UNIQUE(card_id, feature_id)
);

CREATE INDEX IF NOT EXISTS idx_card_features_card ON card_features(card_id);
CREATE INDEX IF NOT EXISTS idx_card_features_feature ON card_features(feature_id);


-- ============================================================================
-- PREREQUISITE AND REQUIREMENT TABLES
-- ============================================================================

-- Prerequisites for variants (what needs to be set up)
CREATE TABLE IF NOT EXISTS variant_prerequisites (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    prerequisite TEXT NOT NULL, -- e.g., "Hullbreaker Horror on the battlefield"
    prerequisite_type TEXT, -- mana, card_state, game_state, etc.

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_variant_prerequisites_variant ON variant_prerequisites(variant_id);


-- ============================================================================
-- LEGALITY TABLES
-- ============================================================================

-- Format legalities for cards
CREATE TABLE IF NOT EXISTS card_legalities (
    id SERIAL PRIMARY KEY,
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    format TEXT NOT NULL, -- commander, legacy, modern, vintage, standard, pauper, etc.
    is_legal BOOLEAN DEFAULT FALSE,

    UNIQUE(card_id, format)
);

CREATE INDEX IF NOT EXISTS idx_card_legalities_card ON card_legalities(card_id);
CREATE INDEX IF NOT EXISTS idx_card_legalities_format ON card_legalities(format);


-- Format legalities for variants
CREATE TABLE IF NOT EXISTS variant_legalities (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    format TEXT NOT NULL,
    is_legal BOOLEAN DEFAULT FALSE,

    UNIQUE(variant_id, format)
);

CREATE INDEX IF NOT EXISTS idx_variant_legalities_variant ON variant_legalities(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_legalities_format ON variant_legalities(format);


-- ============================================================================
-- PRICING TABLES
-- ============================================================================

-- Card prices from various vendors
CREATE TABLE IF NOT EXISTS card_prices (
    id SERIAL PRIMARY KEY,
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    vendor TEXT NOT NULL, -- tcgplayer, cardkingdom, cardmarket
    price_usd NUMERIC(10, 2),
    price_eur NUMERIC(10, 2),
    currency TEXT DEFAULT 'USD',

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(card_id, vendor)
);

CREATE INDEX IF NOT EXISTS idx_card_prices_card ON card_prices(card_id);
CREATE INDEX IF NOT EXISTS idx_card_prices_vendor ON card_prices(vendor);


-- Variant prices (total combo cost)
CREATE TABLE IF NOT EXISTS variant_prices (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    vendor TEXT NOT NULL, -- tcgplayer, cardkingdom, cardmarket
    price_usd NUMERIC(10, 2),
    price_eur NUMERIC(10, 2),
    currency TEXT DEFAULT 'USD',

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(variant_id, vendor)
);

CREATE INDEX IF NOT EXISTS idx_variant_prices_variant ON variant_prices(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_prices_vendor ON variant_prices(vendor);


-- ============================================================================
-- COMMUNITY/USER-GENERATED CONTENT TABLES
-- ============================================================================

-- Variant suggestions from users
CREATE TABLE IF NOT EXISTS variant_suggestions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    suggested_cards TEXT[], -- Array of card names
    suggested_features TEXT[], -- Array of feature names
    description TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_variant_suggestions_user ON variant_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_variant_suggestions_status ON variant_suggestions(status);


-- Variant update suggestions
CREATE TABLE IF NOT EXISTS variant_update_suggestions (
    id SERIAL PRIMARY KEY,
    variant_id TEXT REFERENCES variants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    suggested_changes JSONB, -- Flexible JSON structure for proposed changes
    reason TEXT,
    status TEXT DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_variant_update_suggestions_variant ON variant_update_suggestions(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_update_suggestions_user ON variant_update_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_variant_update_suggestions_status ON variant_update_suggestions(status);


-- Variant aliases (alternative names for combos)
CREATE TABLE IF NOT EXISTS variant_aliases (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(variant_id, alias)
);

CREATE INDEX IF NOT EXISTS idx_variant_aliases_variant ON variant_aliases(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_aliases_alias ON variant_aliases(alias);


-- ============================================================================
-- PROPERTIES TABLE (Generic key-value attributes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    property_type TEXT, -- card_property, combo_property, etc.

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- UTILITY VIEWS
-- ============================================================================

-- View for complete variant information
CREATE VIEW variant_details AS
SELECT
    v.id,
    v.status,
    v.identity,
    v.mana_needed,
    v.description,
    v.popularity,
    json_agg(DISTINCT jsonb_build_object(
        'card_id', c.id,
        'card_name', c.name,
        'quantity', vc.quantity,
        'zone', vc.zone
    )) FILTER (WHERE c.id IS NOT NULL) AS cards,
    json_agg(DISTINCT jsonb_build_object(
        'feature_id', f.id,
        'feature_name', f.name
    )) FILTER (WHERE f.id IS NOT NULL) AS features
FROM variants v
LEFT JOIN variant_cards vc ON v.id = vc.variant_id
LEFT JOIN cards c ON vc.card_id = c.id
LEFT JOIN variant_features vf ON v.id = vf.variant_id
LEFT JOIN features f ON vf.feature_id = f.id
GROUP BY v.id;


-- View for card combo count
CREATE VIEW card_combo_stats AS
SELECT
    c.id,
    c.name,
    c.identity,
    COUNT(DISTINCT vc.variant_id) AS combo_count
FROM cards c
LEFT JOIN variant_cards vc ON c.id = vc.card_id
GROUP BY c.id, c.name, c.identity;


-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist (safe to run multiple times)
DROP TRIGGER IF EXISTS update_cards_updated_at ON cards;
DROP TRIGGER IF EXISTS update_variants_updated_at ON variants;
DROP TRIGGER IF EXISTS update_features_updated_at ON features;

CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variants_updated_at BEFORE UPDATE ON variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_features_updated_at BEFORE UPDATE ON features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE cards IS 'Stores all Magic: The Gathering card data';
COMMENT ON TABLE variants IS 'Stores combo variants with their properties';
COMMENT ON TABLE features IS 'Stores combo effects and outcomes (e.g., "Infinite mana")';
COMMENT ON TABLE variant_cards IS 'Many-to-many relationship between variants and cards with usage context';
COMMENT ON TABLE variant_features IS 'Many-to-many relationship between variants and the features they produce';
COMMENT ON TABLE card_legalities IS 'Format legality information for cards';
COMMENT ON TABLE variant_legalities IS 'Format legality information for combos';
COMMENT ON TABLE card_prices IS 'Current pricing data from various vendors for individual cards';
COMMENT ON TABLE variant_prices IS 'Total combo pricing from various vendors';
