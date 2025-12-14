# Schema Deployment Complete ✅

**Deployed:** 2025-12-13
**Database:** vector_mtg
**Status:** Ready for LLM extraction

---

## Deployment Summary

### Tables Created (6 new tables)
1. ✅ `tag_categories` - 10 categories seeded
2. ✅ `tags` - 65 tags seeded with hierarchy
3. ✅ `card_tags` - Ready for card-tag assignments
4. ✅ `card_abstractions` - Ready for abstract rules
5. ✅ `tagging_review_queue` - Ready to track low-confidence cards
6. ✅ `tagging_jobs` - Ready to track bulk operations

### Cards Table Modified
✅ Added 4 new columns:
- `tag_cache` (TEXT[]) - Denormalized tag array for fast queries
- `tag_cache_updated_at` (TIMESTAMP) - Cache freshness tracking
- `tag_confidence_avg` (NUMERIC) - Average confidence across all tags
- `needs_tag_review` (BOOLEAN) - Flag for manual review

### Functions Created (4)
1. ✅ `get_card_tags_with_hierarchy(card_id)` - Get tags including parents
2. ✅ `get_cards_by_tag(tag_name, min_confidence, include_children)` - Find cards by tag
3. ✅ `update_tag_paths()` - Recalculate hierarchy paths
4. ✅ `update_card_tag_cache()` - Auto-maintain cache (trigger function)

### Views Created (3)
1. ✅ `cards_with_quality_tags` - Cards with >= 0.7 confidence tags
2. ✅ `tag_usage_stats` - Tag usage statistics
3. ✅ `review_queue_summary` - Review queue aggregates

### Triggers Created
✅ `update_card_tag_cache_trigger` - Auto-updates cache on card_tags changes

---

## Tag Taxonomy Seeded

### 10 Categories, 65 Tags

**Breakdown by category:**
- Resource Generation: 11 tags (includes 1 parent + 6 color children)
- Resource Costs: 8 tags
- State Changes: 7 tags
- Triggers: 8 tags
- Effects: 6 tags
- Card Types: 9 tags
- Combo Enablers: 4 tags
- Win Conditions: 4 tags
- Protection: 4 tags
- Removal: 4 tags

**Tag Hierarchy Example:**
```
Generates Mana (parent)
  ├─ Generates White Mana
  ├─ Generates Blue Mana
  ├─ Generates Black Mana
  ├─ Generates Red Mana
  ├─ Generates Green Mana
  └─ Generates Colorless Mana
```

---

## Verification Tests Passed

✅ **Table Creation:**
```sql
SELECT COUNT(*) FROM tags;
-- Result: 65 tags
```

✅ **Tag Hierarchy:**
```sql
SELECT LPAD('', depth * 2, ' ') || display_name
FROM tags
WHERE path[1] = 'generates_mana';
-- Result: 7 rows (1 parent + 6 children)
```

✅ **New Columns:**
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'cards'
AND column_name LIKE 'tag%';
-- Result: tag_cache, tag_cache_updated_at, tag_confidence_avg
```

---

## Next Steps: Build LLM Extraction (Phase 2)

Now that the schema is deployed, we'll build the extraction pipeline **incrementally**.

### Step 1: Create Tag Extraction Function

**File:** `scripts/embeddings/extract_card_tags.py`

**Purpose:** Use LLM to extract functional tags from card text

**Function signature:**
```python
def extract_tags_from_card(
    card_name: str,
    oracle_text: str,
    type_line: str,
    available_tags: list[dict]
) -> list[dict]:
    """
    Extract functional tags from a card using LLM.

    Args:
        card_name: Card name
        oracle_text: Card rules text
        type_line: Card type (e.g., "Creature — Human Wizard")
        available_tags: List of {name, display_name, description}

    Returns:
        [
            {'tag': 'generates_mana', 'confidence': 0.95},
            {'tag': 'untaps_permanents', 'confidence': 0.88},
            ...
        ]
    """
    pass
```

### Step 2: LLM Prompt Design

**Key requirements:**
1. Give LLM the full tag taxonomy with descriptions
2. Ask for functional mechanics, not flavor
3. Request confidence scores (0.0 - 1.0)
4. Return JSON format

**Example prompt structure:**
```
You are an MTG rules expert. Extract functional tags from this card.

Available tags:
- generates_mana: Produces mana of any type
- untaps_permanents: Untaps one or more permanents
- triggers_on_etb: Triggers when permanents enter battlefield
...

Card: Pemmin's Aura
Type: Enchantment — Aura
Text: {U}: Enchanted creature gains flying until end of turn.
       {U}: Untap enchanted creature.
       {1}: Enchanted creature gets +1/-1 or -1/+1 until end of turn.

Extract only tags that apply based on the card's actual mechanics.
Return JSON: [{"tag": "tag_name", "confidence": 0.0-1.0}]
```

### Step 3: Test on Sample Cards

Before processing 508K cards, test on known combos:

**Test cases:**
1. Pemmin's Aura - Should get: untaps_permanents, grants_abilities, infinite_enabler
2. Sol Ring - Should get: generates_mana, generates_colorless_mana, artifact
3. Blood Artist - Should get: triggers_on_death, drains_life, gains_life
4. Ashnod's Altar - Should get: sacrifices_creatures, generates_mana, artifact
5. Thassa's Oracle - Should get: triggers_on_etb, wins_with_empty_library, alternate_win_con

**Validation script:**
```python
def test_extraction():
    test_cards = load_test_cards()
    for card in test_cards:
        tags = extract_tags_from_card(
            card['name'],
            card['oracle_text'],
            card['type_line'],
            load_available_tags()
        )
        print(f"\n{card['name']}:")
        for tag in tags:
            print(f"  - {tag['tag']}: {tag['confidence']}")
```

### Step 4: Store Tags in Database

**Function:** `store_card_tags(card_id, tags)`

```python
def store_card_tags(card_id: str, tags: list[dict]):
    """
    Store extracted tags for a card.

    The trigger will automatically:
    - Update cards.tag_cache[]
    - Calculate cards.tag_confidence_avg
    - Add to review queue if confidence < 0.7
    """
    with get_db_connection() as conn:
        for tag in tags:
            conn.execute("""
                INSERT INTO card_tags (
                    card_id,
                    tag_id,
                    confidence,
                    source,
                    llm_model,
                    extraction_prompt_version
                )
                SELECT
                    %s,
                    t.id,
                    %s,
                    'llm',
                    'gpt-4o-mini',  -- or your chosen model
                    '1.0'
                FROM tags t
                WHERE t.name = %s
            """, (card_id, tag['confidence'], tag['tag']))
        conn.commit()
```

### Step 5: Batch Processing Script

**File:** `scripts/embeddings/batch_tag_cards.py`

```python
def batch_tag_all_cards(
    batch_size: int = 100,
    llm_model: str = 'gpt-4o-mini'
):
    """
    Process all cards in batches.
    """
    # Create job record
    job_id = create_tagging_job(llm_model)

    # Get all cards without tags
    cards = fetch_untagged_cards(batch_size)

    # Load taxonomy once
    available_tags = load_available_tags()

    for card in cards:
        try:
            tags = extract_tags_from_card(
                card['name'],
                card['oracle_text'],
                card['type_line'],
                available_tags
            )
            store_card_tags(card['id'], tags)
            update_job_progress(job_id, success=True)
        except Exception as e:
            log_error(card['id'], str(e))
            update_job_progress(job_id, success=False)
```

---

## Performance Estimates

### LLM Costs (GPT-4o-mini)
- Cards to process: 508,000
- Tokens per card: ~500 input + 100 output
- Cost per 1M tokens: $0.15 input, $0.60 output
- **Total cost: ~$70-$100**

### Time Estimates
- Rate limit: 10,000 requests/min (GPT-4o-mini)
- Processing rate: ~100 cards/sec with batching
- **Total time: ~1.5-2 hours**

### Storage Impact
- card_tags table: ~10-15 MB (508K × 5 tags avg)
- card_abstractions: Not yet populated
- **Total: ~15 MB**

---

## Configuration Ready

### Confidence Thresholds (Currently Set)
```python
PRODUCTION_THRESHOLD = 0.7   # Use in searches
REVIEW_THRESHOLD = 0.7        # Auto-add to review queue
```

### Review Queue Priorities (Auto-set by trigger)
```python
confidence < 0.5  → priority 10 (urgent)
confidence < 0.6  → priority 5  (high)
confidence < 0.7  → priority 1  (low)
no tags extracted → priority 10 (urgent)
```

---

## What to Build Next

**Option A: Start with extraction function** (Recommended)
- Create `extract_card_tags.py`
- Test on 10 sample cards
- Validate confidence scores
- Adjust prompt if needed

**Option B: Build abstraction extractor first**
- Extract abstract rules (JSONB patterns)
- Build pattern matching before tags
- More complex, but could inform tag design

**Option C: Build review interface**
- Web UI to manually review low-confidence cards
- Before bulk processing, build safety net

---

## Current Schema Status

✅ **Deployed and ready for:**
1. Tag extraction from cards
2. Abstraction extraction from cards
3. Review queue management
4. Bulk tagging jobs
5. Tag-based card queries
6. Confidence filtering

⏳ **Waiting for:**
1. LLM extraction function implementation
2. Prompt engineering and testing
3. Batch processing pipeline
4. Initial data population

---

## Monitoring Queries Available Now

### Check schema health:
```sql
-- Tag coverage (currently 0, schema is empty)
SELECT
    COUNT(*) FILTER (WHERE tag_cache IS NOT NULL) as cards_with_tags,
    COUNT(*) FILTER (WHERE tag_cache IS NULL) as cards_without_tags,
    AVG(tag_confidence_avg) as avg_confidence
FROM cards;
```

### View tag taxonomy:
```sql
SELECT
    tc.display_name as category,
    COUNT(*) as tag_count
FROM tags t
JOIN tag_categories tc ON t.category_id = tc.id
GROUP BY tc.display_name
ORDER BY tc.sort_order;
```

### Check combo-relevant tags:
```sql
SELECT display_name
FROM tags
WHERE is_combo_relevant = true
ORDER BY display_name;
```

---

## Schema Deployed Successfully! 🎉

**Ready to move to Phase 2: LLM Tag Extraction**

The incremental build approach means we can:
1. Build extraction function
2. Test on sample cards
3. Validate quality
4. Iterate on prompts
5. Then batch process all 508K cards

Let me know which next step you want to tackle first!
