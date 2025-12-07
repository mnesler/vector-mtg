-- Commander Spellbook PostgreSQL Schema - OPTIMIZED
-- Based on API structure from https://backend.commanderspellbook.com/
-- This schema is idempotent - safe to run multiple times
-- OPTIMIZATIONS: Added composite indexes, covering indexes, partial indexes,
-- materialized views, and query-specific optimizations

-- ============================================================================
-- OPTIONAL: Uncomment to drop all existing tables and start fresh
-- WARNING: This will delete ALL data!
-- ============================================================================
/*
DROP MATERIALIZED VIEW IF EXISTS mv_popular_combos CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_card_combo_summary CASCADE;
DROP VIEW IF EXISTS variant_details CASCADE;
DROP VIEW IF EXISTS card_combo_stats CASCADE;
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

-- OPTIMIZED Indexes for cards
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_oracle_id ON cards(oracle_id);
CREATE INDEX IF NOT EXISTS idx_cards_identity ON cards USING GIN(identity);
CREATE INDEX IF NOT EXISTS idx_cards_type_line ON cards(type_line);
CREATE INDEX IF NOT EXISTS idx_cards_keywords ON cards USING GIN(keywords);

-- NEW: Covering index for common queries that fetch card basic info
CREATE INDEX IF NOT EXISTS idx_cards_name_covering ON cards(name)
INCLUDE (id, identity, type_line, mana_value);

-- NEW: Index on boolean flags for filtering power cards
CREATE INDEX IF NOT EXISTS idx_cards_power_flags ON cards(game_changer, tutor, extra_turn)
WHERE game_changer = TRUE OR tutor = TRUE OR extra_turn = TRUE;

-- NEW: Composite index for identity + mana_value (common filter combination)
CREATE INDEX IF NOT EXISTS idx_cards_identity_mana ON cards USING GIN(identity)
INCLUDE (mana_value, name);

-- NEW: Index on variant_count for finding popular cards
CREATE INDEX IF NOT EXISTS idx_cards_variant_count ON cards(variant_count DESC)
WHERE variant_count > 0;


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

-- NEW: Partial index for active features (likely most queried)
CREATE INDEX IF NOT EXISTS idx_features_active ON features(id, name)
WHERE status IN ('S', 'PU');


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

-- NEW: Composite index for filtering by status + identity (common query pattern)
CREATE INDEX IF NOT EXISTS idx_variants_status_identity ON variants(status)
INCLUDE (identity, popularity);

-- NEW: Partial index for approved/OK combos only (most common query)
CREATE INDEX IF NOT EXISTS idx_variants_approved ON variants(popularity DESC, identity)
WHERE status = 'OK';

-- NEW: Index for recent combos (for "new combos" queries)
CREATE INDEX IF NOT EXISTS idx_variants_recent ON variants(created_at DESC)
WHERE status = 'OK';

-- NEW: Composite index for identity + popularity (deck building queries)
CREATE INDEX IF NOT EXISTS idx_variants_identity_popularity ON variants USING GIN(identity)
INCLUDE (popularity, mana_needed);


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
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;


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

-- OPTIMIZED: Keep existing indexes
CREATE INDEX IF NOT EXISTS idx_variant_cards_variant ON variant_cards(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_cards_card ON variant_cards(card_id);
CREATE INDEX IF NOT EXISTS idx_variant_cards_zone ON variant_cards(zone);

-- NEW: Composite index for reverse lookups (find all combos using a card)
CREATE INDEX IF NOT EXISTS idx_variant_cards_card_variant ON variant_cards(card_id, variant_id);

-- NEW: Partial index for commander-specific queries
CREATE INDEX IF NOT EXISTS idx_variant_cards_commanders ON variant_cards(card_id)
WHERE must_be_commander = TRUE;

-- NEW: Covering index for common join patterns
CREATE INDEX IF NOT EXISTS idx_variant_cards_covering ON variant_cards(variant_id)
INCLUDE (card_id, zone, quantity);


-- Features produced by variants
CREATE TABLE IF NOT EXISTS variant_features (
    id SERIAL PRIMARY KEY,
    variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,

    UNIQUE(variant_id, feature_id)
);

CREATE INDEX IF NOT EXISTS idx_variant_features_variant ON variant_features(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_features_feature ON variant_features(feature_id);

-- NEW: Composite index for reverse feature search (find all combos with a feature)
CREATE INDEX IF NOT EXISTS idx_variant_features_feature_variant ON variant_features(feature_id, variant_id);


-- Features associated with cards
CREATE TABLE IF NOT EXISTS card_features (
    id SERIAL PRIMARY KEY,
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,

    UNIQUE(card_id, feature_id)
);

CREATE INDEX IF NOT EXISTS idx_card_features_card ON card_features(card_id);
CREATE INDEX IF NOT EXISTS idx_card_features_feature ON card_features(feature_id);

-- NEW: Composite index for reverse lookup
CREATE INDEX IF NOT EXISTS idx_card_features_feature_card ON card_features(feature_id, card_id);


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

-- NEW: Index on prerequisite type for filtering
CREATE INDEX IF NOT EXISTS idx_variant_prerequisites_type ON variant_prerequisites(prerequisite_type)
WHERE prerequisite_type IS NOT NULL;


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

-- NEW: Composite index for format queries (find all legal cards in a format)
CREATE INDEX IF NOT EXISTS idx_card_legalities_format_legal ON card_legalities(format, card_id)
WHERE is_legal = TRUE;

-- NEW: Covering index for common queries
CREATE INDEX IF NOT EXISTS idx_card_legalities_covering ON card_legalities(card_id)
INCLUDE (format, is_legal);


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

-- NEW: Partial index for legal combos by format (most common query)
CREATE INDEX IF NOT EXISTS idx_variant_legalities_format_legal ON variant_legalities(format, variant_id)
WHERE is_legal = TRUE;

-- NEW: Covering index
CREATE INDEX IF NOT EXISTS idx_variant_legalities_covering ON variant_legalities(variant_id)
INCLUDE (format, is_legal);


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

-- NEW: Index on USD price for budget queries
CREATE INDEX IF NOT EXISTS idx_card_prices_usd ON card_prices(price_usd)
WHERE price_usd IS NOT NULL;

-- NEW: Composite index for vendor + price range queries
CREATE INDEX IF NOT EXISTS idx_card_prices_vendor_usd ON card_prices(vendor, price_usd)
WHERE price_usd IS NOT NULL;


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

-- NEW: Index for budget combo searches
CREATE INDEX IF NOT EXISTS idx_variant_prices_usd ON variant_prices(price_usd)
WHERE price_usd IS NOT NULL;

-- NEW: Composite index for vendor + price
CREATE INDEX IF NOT EXISTS idx_variant_prices_vendor_usd ON variant_prices(vendor, price_usd)
WHERE price_usd IS NOT NULL;


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

-- NEW: Partial index for pending suggestions (most active queries)
CREATE INDEX IF NOT EXISTS idx_variant_suggestions_pending ON variant_suggestions(created_at DESC)
WHERE status = 'pending';


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

-- NEW: GIN index on JSONB for querying suggested changes
CREATE INDEX IF NOT EXISTS idx_variant_update_suggestions_changes ON variant_update_suggestions
USING GIN(suggested_changes);

-- NEW: Partial index for pending updates
CREATE INDEX IF NOT EXISTS idx_variant_update_suggestions_pending ON variant_update_suggestions(created_at DESC)
WHERE status = 'pending';


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

-- NEW: Text search index for fuzzy alias matching
CREATE INDEX IF NOT EXISTS idx_variant_aliases_alias_trgm ON variant_aliases
USING GIN(alias gin_trgm_ops);


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
-- MATERIALIZED VIEWS (Pre-computed for performance)
-- ============================================================================

-- Materialized view for popular combos with full details
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_combos AS
SELECT
    v.id,
    v.status,
    v.identity,
    v.mana_needed,
    v.description,
    v.popularity,
    v.created_at,
    array_agg(DISTINCT c.name ORDER BY c.name) FILTER (WHERE c.name IS NOT NULL) AS card_names,
    array_agg(DISTINCT f.name ORDER BY f.name) FILTER (WHERE f.name IS NOT NULL) AS feature_names,
    COUNT(DISTINCT vc.card_id) AS card_count
FROM variants v
LEFT JOIN variant_cards vc ON v.id = vc.variant_id
LEFT JOIN cards c ON vc.card_id = c.id
LEFT JOIN variant_features vf ON v.id = vf.variant_id
LEFT JOIN features f ON vf.feature_id = f.id
WHERE v.status = 'OK'
GROUP BY v.id, v.status, v.identity, v.mana_needed, v.description, v.popularity, v.created_at;

-- Indexes on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_popular_combos_popularity ON mv_popular_combos(popularity DESC);
CREATE INDEX IF NOT EXISTS idx_mv_popular_combos_identity ON mv_popular_combos USING GIN(identity);
CREATE INDEX IF NOT EXISTS idx_mv_popular_combos_card_count ON mv_popular_combos(card_count);


-- Materialized view for card statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_card_combo_summary AS
SELECT
    c.id,
    c.name,
    c.identity,
    c.type_line,
    c.mana_value,
    COUNT(DISTINCT vc.variant_id) AS combo_count,
    MAX(v.popularity) AS max_combo_popularity,
    array_agg(DISTINCT f.name ORDER BY f.name) FILTER (WHERE f.name IS NOT NULL) AS common_features
FROM cards c
LEFT JOIN variant_cards vc ON c.id = vc.card_id
LEFT JOIN variants v ON vc.variant_id = v.id AND v.status = 'OK'
LEFT JOIN card_features cf ON c.id = cf.card_id
LEFT JOIN features f ON cf.feature_id = f.id
GROUP BY c.id, c.name, c.identity, c.type_line, c.mana_value;

-- Indexes on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_card_combo_summary_count ON mv_card_combo_summary(combo_count DESC);
CREATE INDEX IF NOT EXISTS idx_mv_card_combo_summary_name ON mv_card_combo_summary(name);
CREATE INDEX IF NOT EXISTS idx_mv_card_combo_summary_identity ON mv_card_combo_summary USING GIN(identity);


-- ============================================================================
-- REGULAR VIEWS (For convenience)
-- ============================================================================

-- View for complete variant information (use for detailed queries)
CREATE OR REPLACE VIEW variant_details AS
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


-- View for card combo count (use materialized view for better performance)
CREATE OR REPLACE VIEW card_combo_stats AS
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
DROP TRIGGER IF EXISTS update_card_prices_updated_at ON card_prices;
DROP TRIGGER IF EXISTS update_variant_prices_updated_at ON variant_prices;

CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variants_updated_at BEFORE UPDATE ON variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_features_updated_at BEFORE UPDATE ON features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_card_prices_updated_at BEFORE UPDATE ON card_prices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variant_prices_updated_at BEFORE UPDATE ON variant_prices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- EXTENSIONS (Enable if needed)
-- ============================================================================

-- Enable pg_trgm for fuzzy text search (optional)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable btree_gin for composite GIN indexes (optional)
-- CREATE EXTENSION IF NOT EXISTS btree_gin;


-- ============================================================================
-- MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_combos;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_card_combo_summary;
END;
$$ LANGUAGE plpgsql;

-- Create unique indexes to enable CONCURRENT refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_popular_combos_id ON mv_popular_combos(id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_card_combo_summary_id ON mv_card_combo_summary(id);


-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE cards IS 'Stores all Magic: The Gathering card data with optimized indexes for identity, keywords, and power level queries';
COMMENT ON TABLE variants IS 'Stores combo variants with optimized indexes for popularity, identity, and status filtering';
COMMENT ON TABLE features IS 'Stores combo effects and outcomes (e.g., "Infinite mana") with partial indexes for active features';
COMMENT ON TABLE variant_cards IS 'Many-to-many relationship with covering indexes for common join patterns';
COMMENT ON TABLE variant_features IS 'Many-to-many relationship with bidirectional composite indexes';
COMMENT ON TABLE card_legalities IS 'Format legality with partial indexes for legal cards only';
COMMENT ON TABLE variant_legalities IS 'Format legality with partial indexes for legal combos only';
COMMENT ON TABLE card_prices IS 'Pricing data with indexes for budget queries';
COMMENT ON TABLE variant_prices IS 'Total combo pricing with budget query optimization';
COMMENT ON MATERIALIZED VIEW mv_popular_combos IS 'Pre-computed popular combos with full details - refresh periodically';
COMMENT ON MATERIALIZED VIEW mv_card_combo_summary IS 'Pre-computed card statistics - refresh periodically';

-- ============================================================================
-- PERFORMANCE NOTES
-- ============================================================================

-- To keep materialized views fresh, run periodically (e.g., via cron):
-- SELECT refresh_all_materialized_views();

-- To analyze table statistics (run after bulk inserts):
-- ANALYZE cards;
-- ANALYZE variants;
-- ANALYZE variant_cards;

-- To check index usage:
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan DESC;

-- To find missing indexes:
-- SELECT schemaname, tablename, seq_scan, seq_tup_read
-- FROM pg_stat_user_tables
-- WHERE seq_scan > 0
-- ORDER BY seq_tup_read DESC
-- LIMIT 25;
