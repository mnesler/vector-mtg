-- Analysis queries for LLM provider tracking
-- Created: 2025-12-14
-- Purpose: Compare tag extraction quality between different LLM providers

-- 1. Count tags by provider
SELECT 
    llm_provider,
    COUNT(*) as tag_count,
    COUNT(DISTINCT card_id) as card_count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence
FROM card_tags
WHERE source = 'llm'
GROUP BY llm_provider
ORDER BY tag_count DESC;

-- 2. Compare providers by model
SELECT 
    llm_provider,
    llm_model,
    COUNT(*) as tag_count,
    COUNT(DISTINCT card_id) as card_count,
    AVG(confidence) as avg_confidence
FROM card_tags
WHERE source = 'llm'
GROUP BY llm_provider, llm_model
ORDER BY llm_provider, tag_count DESC;

-- 3. Find cards tagged by multiple providers (for comparison)
SELECT 
    c.name,
    c.type_line,
    array_agg(DISTINCT ct.llm_provider) as providers,
    COUNT(DISTINCT ct.llm_provider) as provider_count,
    COUNT(*) as total_tags
FROM cards c
JOIN card_tags ct ON c.id = ct.card_id
WHERE ct.source = 'llm'
GROUP BY c.id, c.name, c.type_line
HAVING COUNT(DISTINCT ct.llm_provider) > 1
ORDER BY provider_count DESC, total_tags DESC
LIMIT 50;

-- 4. Tag distribution by provider
SELECT 
    ct.llm_provider,
    t.name as tag_name,
    t.display_name,
    COUNT(*) as usage_count,
    AVG(ct.confidence) as avg_confidence
FROM card_tags ct
JOIN tags t ON ct.tag_id = t.id
WHERE ct.source = 'llm'
GROUP BY ct.llm_provider, t.name, t.display_name
ORDER BY ct.llm_provider, usage_count DESC;

-- 5. Recent extractions by provider
SELECT 
    ct.llm_provider,
    ct.llm_model,
    c.name as card_name,
    t.name as tag_name,
    ct.confidence,
    ct.extracted_at
FROM card_tags ct
JOIN cards c ON ct.card_id = c.id
JOIN tags t ON ct.tag_id = t.id
WHERE ct.source = 'llm'
ORDER BY ct.extracted_at DESC
LIMIT 50;

-- 6. Provider performance: low confidence tags
SELECT 
    ct.llm_provider,
    c.name as card_name,
    t.name as tag_name,
    ct.confidence
FROM card_tags ct
JOIN cards c ON ct.card_id = c.id
JOIN tags t ON ct.tag_id = t.id
WHERE ct.source = 'llm' 
  AND ct.confidence < 0.7
ORDER BY ct.confidence ASC, ct.llm_provider
LIMIT 100;
