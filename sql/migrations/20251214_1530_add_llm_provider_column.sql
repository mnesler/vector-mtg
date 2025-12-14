-- Migration: Add llm_provider column to card_tags for comparing different LLM sources
-- Created: 2024-12-14
-- Author: OpenCode
-- Purpose: Track which LLM provider (Claude, OpenAI, Ollama) generated each tag
--          to enable comparison of extraction quality across providers

BEGIN;

-- Add llm_provider column
ALTER TABLE card_tags 
ADD COLUMN IF NOT EXISTS llm_provider TEXT;

-- Create index for filtering by provider
CREATE INDEX IF NOT EXISTS idx_card_tags_llm_provider 
ON card_tags(llm_provider);

-- Add comment
COMMENT ON COLUMN card_tags.llm_provider IS 
'LLM provider that generated this tag: anthropic, openai, ollama, or other';

-- Update existing records to infer provider from llm_model
UPDATE card_tags
SET llm_provider = CASE
    WHEN llm_model LIKE 'claude%' THEN 'anthropic'
    WHEN llm_model LIKE 'gpt%' THEN 'openai'
    WHEN llm_model LIKE 'qwen%' OR llm_model LIKE 'llama%' OR llm_model LIKE 'mistral%' THEN 'ollama'
    ELSE 'unknown'
END
WHERE llm_provider IS NULL;

COMMIT;

-- Rollback (if needed)
-- BEGIN;
-- DROP INDEX IF EXISTS idx_card_tags_llm_provider;
-- ALTER TABLE card_tags DROP COLUMN IF EXISTS llm_provider;
-- COMMIT;
