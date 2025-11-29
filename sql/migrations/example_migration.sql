-- Migration: Add performance index for card power/toughness queries
-- Created: 2025-11-22
-- Author: Example

BEGIN;

-- Add composite index for creature stats queries
CREATE INDEX IF NOT EXISTS idx_cards_creature_stats
ON cards(power, toughness)
WHERE type_line LIKE '%Creature%';

-- Add index for cards by release date (useful for set analysis)
CREATE INDEX IF NOT EXISTS idx_cards_released_name
ON cards(released_at DESC, name);

COMMIT;

-- ============================================
-- Rollback Instructions
-- ============================================
-- To undo this migration, run:
--
-- BEGIN;
-- DROP INDEX IF EXISTS idx_cards_creature_stats;
-- DROP INDEX IF EXISTS idx_cards_released_name;
-- COMMIT;
