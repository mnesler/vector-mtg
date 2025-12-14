-- ============================================================================
-- MTG Card Tags & Abstractions Schema v1
-- ============================================================================
-- Purpose: Tag cards with functional mechanics and extract abstract rules
-- for AI-powered combo discovery
--
-- Features:
-- - Hierarchical tag taxonomy with parent/child relationships
-- - Confidence scoring with threshold filtering
-- - Review queue for low-confidence extractions
-- - Cached arrays for performance
-- - Full audit trail
-- ============================================================================

-- ============================================================================
-- TAG CATEGORIES
-- ============================================================================

CREATE TABLE tag_categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- 'resource_generation'
    display_name TEXT NOT NULL,              -- 'Resource Generation'
    description TEXT,
    parent_category_id INTEGER REFERENCES tag_categories(id),
    sort_order INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE tag_categories IS 'Categories for organizing tags (e.g., resource_generation, triggers, effects)';

-- ============================================================================
-- TAGS (with hierarchy support)
-- ============================================================================

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- 'generates_mana'
    display_name TEXT NOT NULL,              -- 'Generates Mana'
    category_id INTEGER REFERENCES tag_categories(id),
    description TEXT,

    -- Hierarchy support
    parent_tag_id INTEGER REFERENCES tags(id),  -- NULL for root tags
    depth INTEGER DEFAULT 0,                 -- 0 for root, 1 for children, etc.
    path TEXT[],                            -- Full path from root: ['resource_gen', 'generates_mana', 'generates_green_mana']

    -- Tag metadata
    is_combo_relevant BOOLEAN DEFAULT true,  -- Should this tag be used for combo discovery?
    requires_validation BOOLEAN DEFAULT false, -- Does this tag need manual verification?

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE tags IS 'Tag definitions with hierarchical relationships';
COMMENT ON COLUMN tags.parent_tag_id IS 'Parent tag for hierarchy (e.g., generates_green_mana -> generates_mana)';
COMMENT ON COLUMN tags.path IS 'Full path from root for efficient hierarchy queries';

-- Indexes
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category_id);
CREATE INDEX idx_tags_parent ON tags(parent_tag_id);
CREATE INDEX idx_tags_depth ON tags(depth);
CREATE INDEX idx_tags_path ON tags USING GIN(path);
CREATE INDEX idx_tags_combo_relevant ON tags(is_combo_relevant) WHERE is_combo_relevant = true;

-- ============================================================================
-- CARD TAGS (with confidence and provenance)
-- ============================================================================

CREATE TABLE card_tags (
    id SERIAL PRIMARY KEY,
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

    -- Confidence and quality
    confidence NUMERIC NOT NULL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    needs_review BOOLEAN DEFAULT false,      -- Flag for manual review

    -- Provenance
    source TEXT NOT NULL DEFAULT 'llm',      -- 'llm', 'manual', 'pattern', 'community', 'rules_engine'
    llm_model TEXT,                          -- Which LLM extracted this? 'gpt-4', 'qwen-2.5', etc.
    extraction_prompt_version TEXT,          -- Track prompt versions for debugging

    -- Metadata
    extracted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,

    UNIQUE(card_id, tag_id)
);

COMMENT ON TABLE card_tags IS 'Junction table linking cards to tags with confidence scores';
COMMENT ON COLUMN card_tags.confidence IS 'Confidence score 0-1, filter low scores for quality';
COMMENT ON COLUMN card_tags.needs_review IS 'Flag cards for manual verification';

-- Indexes
CREATE INDEX idx_card_tags_card_id ON card_tags(card_id);
CREATE INDEX idx_card_tags_tag_id ON card_tags(tag_id);
CREATE INDEX idx_card_tags_source ON card_tags(source);
CREATE INDEX idx_card_tags_confidence ON card_tags(confidence);
CREATE INDEX idx_card_tags_needs_review ON card_tags(needs_review) WHERE needs_review = true;
CREATE INDEX idx_card_tags_llm_model ON card_tags(llm_model);

-- ============================================================================
-- CARD ABSTRACTIONS (generalized rules)
-- ============================================================================

CREATE TABLE card_abstractions (
    id SERIAL PRIMARY KEY,
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,

    -- Abstraction type
    abstraction_type TEXT NOT NULL,         -- 'activated_ability', 'triggered_ability', 'static_effect', 'etb_effect', 'replacement_effect'

    -- Structured pattern (JSONB for flexibility)
    pattern JSONB NOT NULL,
    /*
    Example patterns:

    Activated ability:
    {
        "type": "activated_ability",
        "cost": {
            "mana": "{U}",
            "tap": false,
            "sacrifice": [],
            "other": []
        },
        "effect": {
            "action": "untap",
            "target": "permanent",
            "scope": "enchanted",
            "amount": 1
        },
        "repeatable": true
    }

    Triggered ability:
    {
        "type": "triggered_ability",
        "trigger": {
            "event": "dies",
            "source": ["creature"],
            "scope": "any"
        },
        "effect": {
            "action": "drain_life",
            "target": "opponent",
            "amount": 1
        }
    }
    */

    -- Human-readable version
    abstraction_text TEXT NOT NULL,         -- "Pay {U}: Untap enchanted creature"

    -- Pattern matching
    pattern_hash TEXT GENERATED ALWAYS AS (md5(pattern::text)) STORED,

    -- Quality
    confidence NUMERIC DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    needs_review BOOLEAN DEFAULT false,

    -- Provenance
    source TEXT DEFAULT 'llm',
    llm_model TEXT,
    extraction_prompt_version TEXT,

    extracted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,

    UNIQUE(card_id, pattern_hash)
);

COMMENT ON TABLE card_abstractions IS 'Abstract rule patterns extracted from cards for combo matching';
COMMENT ON COLUMN card_abstractions.pattern IS 'JSONB structure representing the abstracted ability';
COMMENT ON COLUMN card_abstractions.pattern_hash IS 'MD5 hash of pattern for deduplication and fast lookup';

-- Indexes
CREATE INDEX idx_card_abstractions_card_id ON card_abstractions(card_id);
CREATE INDEX idx_card_abstractions_type ON card_abstractions(abstraction_type);
CREATE INDEX idx_card_abstractions_pattern ON card_abstractions USING GIN(pattern);
CREATE INDEX idx_card_abstractions_hash ON card_abstractions(pattern_hash);
CREATE INDEX idx_card_abstractions_confidence ON card_abstractions(confidence);
CREATE INDEX idx_card_abstractions_needs_review ON card_abstractions(needs_review) WHERE needs_review = true;

-- ============================================================================
-- CACHED TAGS (denormalized for performance)
-- ============================================================================

-- Add columns to existing cards table
ALTER TABLE cards
ADD COLUMN tag_cache TEXT[],                     -- Cached array of tag names
ADD COLUMN tag_cache_updated_at TIMESTAMP,
ADD COLUMN tag_confidence_avg NUMERIC,           -- Average confidence of all tags
ADD COLUMN needs_tag_review BOOLEAN DEFAULT false;  -- Flag for review queue

COMMENT ON COLUMN cards.tag_cache IS 'Denormalized array of tag names for fast queries';
COMMENT ON COLUMN cards.tag_confidence_avg IS 'Average confidence score across all tags for this card';
COMMENT ON COLUMN cards.needs_tag_review IS 'Flag indicating card needs manual tag review';

-- Index for tag cache
CREATE INDEX idx_cards_tag_cache ON cards USING GIN(tag_cache);
CREATE INDEX idx_cards_tag_confidence ON cards(tag_confidence_avg);
CREATE INDEX idx_cards_needs_tag_review ON cards(needs_tag_review) WHERE needs_tag_review = true;

-- ============================================================================
-- REVIEW QUEUE (cards that need attention)
-- ============================================================================

CREATE TABLE tagging_review_queue (
    id SERIAL PRIMARY KEY,
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,

    -- Why is this in review queue?
    reason TEXT NOT NULL,                   -- 'low_confidence', 'no_tags_extracted', 'conflicting_tags', 'extraction_error'
    details JSONB,                          -- Additional context about the issue

    -- Status
    status TEXT DEFAULT 'pending',          -- 'pending', 'in_review', 'completed', 'skipped'
    priority INTEGER DEFAULT 0,             -- Higher = more urgent

    -- Resolution
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    resolution_notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(card_id)
);

COMMENT ON TABLE tagging_review_queue IS 'Queue of cards that need manual review due to low confidence or extraction issues';

-- Indexes
CREATE INDEX idx_review_queue_status ON tagging_review_queue(status);
CREATE INDEX idx_review_queue_priority ON tagging_review_queue(priority DESC);
CREATE INDEX idx_review_queue_reason ON tagging_review_queue(reason);
CREATE INDEX idx_review_queue_created ON tagging_review_queue(created_at);

-- ============================================================================
-- EXTRACTION JOBS (track bulk tagging operations)
-- ============================================================================

CREATE TABLE tagging_jobs (
    id SERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    description TEXT,

    -- Configuration
    llm_model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    confidence_threshold NUMERIC DEFAULT 0.7,

    -- Progress
    status TEXT DEFAULT 'pending',          -- 'pending', 'running', 'completed', 'failed'
    total_cards INTEGER DEFAULT 0,
    processed_cards INTEGER DEFAULT 0,
    successful_cards INTEGER DEFAULT 0,
    failed_cards INTEGER DEFAULT 0,
    review_queue_cards INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_completion TIMESTAMP,

    -- Results
    error_log JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE tagging_jobs IS 'Track bulk tagging jobs for monitoring and debugging';

-- ============================================================================
-- TRIGGERS (maintain cache and review queue)
-- ============================================================================

-- Update tag cache when card_tags changes
CREATE OR REPLACE FUNCTION update_card_tag_cache()
RETURNS TRIGGER AS $$
DECLARE
    avg_conf NUMERIC;
    tag_count INTEGER;
    low_conf_count INTEGER;
BEGIN
    -- Get tag names and stats
    WITH tag_stats AS (
        SELECT
            ARRAY_AGG(t.name) as tags,
            AVG(ct.confidence) as avg_confidence,
            COUNT(*) as total_tags,
            COUNT(*) FILTER (WHERE ct.confidence < 0.7) as low_conf_tags
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE ct.card_id = COALESCE(NEW.card_id, OLD.card_id)
    )
    UPDATE cards c
    SET
        tag_cache = COALESCE(ts.tags, ARRAY[]::TEXT[]),
        tag_cache_updated_at = NOW(),
        tag_confidence_avg = ts.avg_confidence,
        needs_tag_review = (ts.avg_confidence < 0.7 OR ts.low_conf_tags > 0)
    FROM tag_stats ts
    WHERE c.id = COALESCE(NEW.card_id, OLD.card_id);

    -- Add to review queue if needed
    SELECT tag_confidence_avg INTO avg_conf
    FROM cards
    WHERE id = COALESCE(NEW.card_id, OLD.card_id);

    IF avg_conf < 0.7 THEN
        INSERT INTO tagging_review_queue (card_id, reason, details, priority)
        VALUES (
            COALESCE(NEW.card_id, OLD.card_id),
            'low_confidence',
            jsonb_build_object('avg_confidence', avg_conf),
            CASE
                WHEN avg_conf < 0.5 THEN 10
                WHEN avg_conf < 0.6 THEN 5
                ELSE 1
            END
        )
        ON CONFLICT (card_id) DO UPDATE
        SET
            reason = EXCLUDED.reason,
            details = EXCLUDED.details,
            priority = EXCLUDED.priority;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_card_tag_cache
AFTER INSERT OR UPDATE OR DELETE ON card_tags
FOR EACH ROW
EXECUTE FUNCTION update_card_tag_cache();

COMMENT ON FUNCTION update_card_tag_cache IS 'Automatically update tag cache and review queue when tags change';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get all tags for a card (including parent tags)
CREATE OR REPLACE FUNCTION get_card_tags_with_hierarchy(p_card_id UUID)
RETURNS TABLE (
    tag_id INTEGER,
    tag_name TEXT,
    tag_depth INTEGER,
    tag_path TEXT[],
    confidence NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE tag_hierarchy AS (
        -- Direct tags
        SELECT
            t.id,
            t.name,
            t.depth,
            t.path,
            ct.confidence,
            0 as inheritance_level
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE ct.card_id = p_card_id

        UNION ALL

        -- Parent tags
        SELECT
            t.id,
            t.name,
            t.depth,
            t.path,
            th.confidence * 0.9 as confidence,  -- Reduce confidence for inherited tags
            th.inheritance_level + 1
        FROM tag_hierarchy th
        JOIN tags t ON t.id = (
            SELECT parent_tag_id FROM tags WHERE id = th.tag_id
        )
        WHERE t.id IS NOT NULL
    )
    SELECT DISTINCT ON (id)
        id,
        name,
        depth,
        path,
        confidence
    FROM tag_hierarchy
    ORDER BY id, inheritance_level;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_card_tags_with_hierarchy IS 'Get all tags for a card including inherited parent tags';

-- Get cards by tag (including child tags)
CREATE OR REPLACE FUNCTION get_cards_by_tag(
    p_tag_name TEXT,
    p_min_confidence NUMERIC DEFAULT 0.7,
    p_include_children BOOLEAN DEFAULT true
)
RETURNS TABLE (
    card_id UUID,
    card_name TEXT,
    tag_name TEXT,
    confidence NUMERIC
) AS $$
BEGIN
    IF p_include_children THEN
        -- Include cards tagged with this tag OR any child tag
        RETURN QUERY
        WITH RECURSIVE tag_tree AS (
            SELECT id, name FROM tags WHERE name = p_tag_name
            UNION ALL
            SELECT t.id, t.name
            FROM tags t
            JOIN tag_tree tt ON t.parent_tag_id = tt.id
        )
        SELECT
            c.id,
            c.name,
            t.name,
            ct.confidence
        FROM card_tags ct
        JOIN cards c ON ct.card_id = c.id
        JOIN tags t ON ct.tag_id = t.id
        WHERE t.id IN (SELECT id FROM tag_tree)
          AND ct.confidence >= p_min_confidence
        ORDER BY ct.confidence DESC;
    ELSE
        -- Only exact tag match
        RETURN QUERY
        SELECT
            c.id,
            c.name,
            t.name,
            ct.confidence
        FROM card_tags ct
        JOIN cards c ON ct.card_id = c.id
        JOIN tags t ON ct.tag_id = t.id
        WHERE t.name = p_tag_name
          AND ct.confidence >= p_min_confidence
        ORDER BY ct.confidence DESC;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_cards_by_tag IS 'Find cards by tag name with confidence threshold and optional child tag inclusion';

-- Update tag hierarchy path (call after inserting/updating tags)
CREATE OR REPLACE FUNCTION update_tag_paths()
RETURNS void AS $$
BEGIN
    WITH RECURSIVE tag_paths AS (
        -- Root tags
        SELECT
            id,
            ARRAY[name] as path,
            0 as depth
        FROM tags
        WHERE parent_tag_id IS NULL

        UNION ALL

        -- Child tags
        SELECT
            t.id,
            tp.path || t.name,
            tp.depth + 1
        FROM tags t
        JOIN tag_paths tp ON t.parent_tag_id = tp.id
    )
    UPDATE tags t
    SET
        path = tp.path,
        depth = tp.depth
    FROM tag_paths tp
    WHERE t.id = tp.id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_tag_paths IS 'Recalculate path and depth for all tags in hierarchy';

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Cards with all tags (confidence filtered)
CREATE VIEW cards_with_quality_tags AS
SELECT
    c.id,
    c.name,
    c.oracle_text,
    c.tag_cache,
    c.tag_confidence_avg,
    c.needs_tag_review,
    (
        SELECT json_agg(json_build_object(
            'tag', t.name,
            'category', tc.name,
            'confidence', ct.confidence,
            'source', ct.source,
            'needs_review', ct.needs_review
        ) ORDER BY ct.confidence DESC)
        FROM card_tags ct
        JOIN tags t ON ct.tag_id = t.id
        LEFT JOIN tag_categories tc ON t.category_id = tc.id
        WHERE ct.card_id = c.id
          AND ct.confidence >= 0.7  -- Default threshold
    ) as tags_detail
FROM cards c;

COMMENT ON VIEW cards_with_quality_tags IS 'Cards with high-confidence tags (>= 0.7)';

-- Tag usage statistics
CREATE VIEW tag_usage_stats AS
SELECT
    t.id,
    t.name,
    t.display_name,
    tc.name as category,
    t.depth,
    COUNT(ct.card_id) as card_count,
    AVG(ct.confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE ct.needs_review) as needs_review_count,
    COUNT(*) FILTER (WHERE ct.confidence >= 0.9) as high_confidence_count,
    COUNT(*) FILTER (WHERE ct.confidence < 0.7) as low_confidence_count
FROM tags t
LEFT JOIN card_tags ct ON t.id = ct.tag_id
LEFT JOIN tag_categories tc ON t.category_id = tc.id
GROUP BY t.id, t.name, t.display_name, tc.name, t.depth
ORDER BY card_count DESC NULLS LAST;

COMMENT ON VIEW tag_usage_stats IS 'Statistics about tag usage and quality';

-- Review queue summary
CREATE VIEW review_queue_summary AS
SELECT
    reason,
    status,
    COUNT(*) as count,
    AVG((details->>'avg_confidence')::NUMERIC) as avg_confidence,
    MIN(created_at) as oldest_entry,
    MAX(priority) as max_priority
FROM tagging_review_queue
GROUP BY reason, status
ORDER BY count DESC;

COMMENT ON VIEW review_queue_summary IS 'Summary of cards in review queue by reason and status';

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed for your setup)
-- ============================================================================

-- Grant read access to views
-- GRANT SELECT ON cards_with_quality_tags TO your_read_role;
-- GRANT SELECT ON tag_usage_stats TO your_read_role;
-- GRANT SELECT ON review_queue_summary TO your_read_role;
