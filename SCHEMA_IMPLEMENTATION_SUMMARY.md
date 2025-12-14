# Schema Implementation Summary

**Created:** 2025-12-13
**Status:** Ready for deployment

---

## What We Built

### ✅ Complete Tag & Abstraction System

**Files created:**
1. `/home/maxwell/vector-mtg/schema/tags_and_abstractions_v1.sql` - Full schema
2. `/home/maxwell/vector-mtg/schema/seed_tag_taxonomy.sql` - Initial tags (~70 tags)

---

## Key Features Implemented

### 1. ✅ Tag Hierarchy Support

**Parent/Child Relationships:**
```
generates_mana (parent)
  ├── generates_white_mana (child)
  ├── generates_blue_mana (child)
  ├── generates_colorless_mana (child)
  └── ...
```

**Database columns:**
- `parent_tag_id` - Points to parent tag
- `depth` - How deep in hierarchy (0 = root)
- `path` - Full path array for efficient queries

**Helper function:**
```sql
-- Get all tags including inherited parent tags
SELECT * FROM get_card_tags_with_hierarchy('card-uuid');
```

### 2. ✅ Confidence Threshold Filtering

**Confidence scores everywhere:**
- `card_tags.confidence` (0-1 score per tag assignment)
- `cards.tag_confidence_avg` (average across all tags)
- Default filter: `>= 0.7` in views

**Automatic filtering:**
```sql
-- Only shows tags >= 0.7 confidence
SELECT * FROM cards_with_quality_tags;
```

### 3. ✅ Review Queue for Low-Confidence Cards

**Automatic flagging:**
- Cards with `confidence < 0.7` → Auto-added to review queue
- Cards with no tags → Flagged for review
- Cards with extraction errors → Queued

**Review queue table:**
```sql
tagging_review_queue:
  - card_id
  - reason ('low_confidence', 'no_tags_extracted', 'extraction_error')
  - priority (1-10, higher = more urgent)
  - status ('pending', 'in_review', 'completed')
```

**View for monitoring:**
```sql
SELECT * FROM review_queue_summary;
-- Shows: reason, count, avg_confidence, oldest_entry
```

### 4. ✅ Automated Cache Maintenance

**Trigger system:**
When you insert/update/delete card tags:
1. Updates `cards.tag_cache[]` array (for fast queries)
2. Calculates `cards.tag_confidence_avg`
3. Sets `cards.needs_tag_review` flag if needed
4. Adds to review queue if confidence < 0.7

**No manual cache management needed!**

### 5. ✅ Full Audit Trail

**Tracks everything:**
- `source` - 'llm', 'manual', 'pattern', 'community'
- `llm_model` - Which LLM extracted the tag
- `extraction_prompt_version` - Track prompt iterations
- `extracted_at` - When tag was added
- `reviewed_at` / `reviewed_by` - Manual review tracking

### 6. ✅ Abstraction Storage (JSONB)

**Flexible structure for rules:**
```jsonb
{
  "type": "activated_ability",
  "cost": {"mana": "{U}"},
  "effect": {
    "action": "untap",
    "target": "permanent",
    "scope": "enchanted"
  },
  "repeatable": true
}
```

**Auto-generates pattern hash for deduplication**

### 7. ✅ Job Tracking

**Monitor bulk tagging operations:**
```sql
tagging_jobs:
  - total_cards, processed_cards, successful_cards
  - failed_cards, review_queue_cards
  - status, started_at, estimated_completion
```

---

## Tag Taxonomy Seeded

### 10 Categories, ~70 Tags

**Categories:**
1. Resource Generation (6 parent tags + 6 color-specific children)
2. Resource Costs (8 tags)
3. State Changes (7 tags) - Crucial for combos
4. Triggers (8 tags) - Very important for combos
5. Effects (6 tags)
6. Combo Enablers (4 tags) - Meta tags
7. Win Conditions (4 tags)
8. Protection (4 tags)
9. Removal (4 tags)
10. Card Types (9 tags)

**Key combo-relevant tags:**
- `untaps_permanents`
- `generates_mana` (+ color variants)
- `triggers_on_etb`, `triggers_on_death`, `triggers_on_cast`
- `creates_tokens`
- `blinks_creatures`
- `bounces_permanents`
- `sacrifices_creatures`
- `infinite_enabler`

---

## Database Tables Created

### Core Tables:
1. **`tag_categories`** - Categories for organizing tags
2. **`tags`** - Tag definitions with hierarchy
3. **`card_tags`** - Card-to-tag assignments (with confidence)
4. **`card_abstractions`** - Extracted abstract rules
5. **`tagging_review_queue`** - Cards needing review
6. **`tagging_jobs`** - Bulk operation tracking

### Modifications to Existing:
7. **`cards`** - Added columns:
   - `tag_cache[]` - Denormalized array
   - `tag_cache_updated_at`
   - `tag_confidence_avg`
   - `needs_tag_review`

---

## Helper Functions

### 1. `get_card_tags_with_hierarchy(card_id)`
Returns tags + inherited parent tags for a card

### 2. `get_cards_by_tag(tag_name, min_confidence, include_children)`
Find cards by tag, optionally including child tags

### 3. `update_tag_paths()`
Recalculate hierarchy paths (call after bulk tag updates)

### 4. `update_card_tag_cache()` (trigger)
Auto-maintains cache when tags change

---

## Views Created

### 1. `cards_with_quality_tags`
Cards with tags >= 0.7 confidence (filtered, production-ready)

### 2. `tag_usage_stats`
Shows:
- How many cards have each tag
- Average confidence per tag
- High/low confidence counts

### 3. `review_queue_summary`
Aggregated view of review queue by reason/status

---

## How Confidence Filtering Works

### Automatic Flagging:

```
Card tagged → Calculate avg confidence
                     ↓
            Is avg < 0.7?
                     ↓
              Yes ─→ Add to review queue
                     Set needs_tag_review = true
                     Priority based on how low:
                       < 0.5 = priority 10 (urgent)
                       < 0.6 = priority 5
                       < 0.7 = priority 1
```

### Query Examples:

```sql
-- Get all high-confidence tags for a card
SELECT * FROM cards_with_quality_tags WHERE id = 'card-uuid';

-- Get cards that need review
SELECT * FROM cards WHERE needs_tag_review = true ORDER BY tag_confidence_avg;

-- Get review queue ordered by priority
SELECT * FROM tagging_review_queue WHERE status = 'pending' ORDER BY priority DESC;

-- Get cards with specific tag, min confidence 0.8
SELECT * FROM get_cards_by_tag('generates_mana', 0.8, true);
```

---

## How Tag Hierarchy Works

### Example Hierarchy:

```
generates_mana (root)
  ├── generates_white_mana
  ├── generates_blue_mana
  ├── generates_black_mana
  ├── generates_red_mana
  ├── generates_green_mana
  └── generates_colorless_mana
```

### Querying:

```sql
-- Find cards that generate ANY mana (includes all children)
SELECT * FROM get_cards_by_tag('generates_mana', 0.7, true);
-- Returns cards tagged with generates_mana OR any child tag

-- Find cards that specifically generate blue mana
SELECT * FROM get_cards_by_tag('generates_blue_mana', 0.7, false);
-- Returns only cards with exact tag
```

### Adding to Hierarchy:

```sql
-- Add a new child tag
INSERT INTO tags (name, display_name, category_id, parent_tag_id)
VALUES (
    'generates_treasure_tokens',
    'Generates Treasure Tokens',
    (SELECT id FROM tag_categories WHERE name = 'resource_generation'),
    (SELECT id FROM tags WHERE name = 'generates_mana')
);

-- Update paths
SELECT update_tag_paths();
```

---

## Next Steps

### Phase 1: Deploy Schema (Today)

```bash
# 1. Apply schema
psql -U postgres -d vector_mtg -f schema/tags_and_abstractions_v1.sql

# 2. Seed taxonomy
psql -U postgres -d vector_mtg -f schema/seed_tag_taxonomy.sql

# 3. Verify
psql -U postgres -d vector_mtg -c "SELECT COUNT(*) FROM tags;"
# Should return ~70 tags
```

### Phase 2: Build LLM Extraction Function (Next)

**Create:**
```python
def extract_tags_from_card(card_name: str, oracle_text: str) -> list:
    """
    Use LLM to extract tags from a card
    Returns: [
        {'tag': 'generates_mana', 'confidence': 0.95},
        {'tag': 'untaps_permanents', 'confidence': 0.88},
        ...
    ]
    """
    # LLM prompt here
    pass
```

### Phase 3: Test on Sample Cards

```python
# Test cards
test_cards = [
    ("Pemmin's Aura", "{1}{U}", "..."),  # Untapper
    ("Sol Ring", "{1}", "..."),           # Mana rock
    ("Blood Artist", "{1}{B}", "..."),    # Death trigger
    ("Ashnod's Altar", "{3}", "...")      # Sac outlet
]

for card in test_cards:
    tags = extract_tags_from_card(card[0], card[2])
    print(f"{card[0]}: {tags}")
```

### Phase 4: Batch Process All Cards

```python
# Process all 508K cards
job = create_tagging_job(
    llm_model="gpt-4",
    confidence_threshold=0.7
)

for card in all_cards:
    tags = extract_tags_from_card(card.name, card.oracle_text)
    store_card_tags(card.id, tags)
    update_job_progress(job.id)
```

### Phase 5: Review Low-Confidence Cards

```sql
-- Get cards needing review
SELECT c.name, c.oracle_text, c.tag_confidence_avg
FROM cards c
JOIN tagging_review_queue rq ON c.id = rq.card_id
WHERE rq.status = 'pending'
ORDER BY rq.priority DESC
LIMIT 100;
```

### Phase 6: Extract Abstractions

After tags are working, extract abstract rules for pattern matching.

---

## Configuration Settings

### Confidence Thresholds (Recommended):

```python
CONFIDENCE_THRESHOLDS = {
    'production': 0.7,      # Use for searches, combo discovery
    'review': 0.5,          # Flag for manual review
    'discard': 0.3          # Too low, re-extract
}
```

### Review Queue Priorities:

```python
REVIEW_PRIORITIES = {
    'no_tags': 10,          # Highest - card has no tags at all
    'very_low_conf': 10,    # avg < 0.5
    'low_conf': 5,          # avg < 0.6
    'medium_conf': 1,       # avg < 0.7
}
```

---

## Performance Expectations

### With 508K Cards Tagged:

**Storage:**
- Tags table: ~50 KB (70 tags)
- card_tags: ~10-15 MB (508K cards × 5 tags avg × 30 bytes)
- card_abstractions: ~150-200 MB (508K × 2 abstractions avg × 200 bytes)
- Total: ~200 MB

**Query Performance:**
- Get tags for one card: < 1ms (uses cached array)
- Get cards by tag: 5-10ms (GIN index)
- Tag hierarchy traversal: 10-20ms
- Review queue query: 2-5ms

---

## Monitoring Queries

### Daily Health Check:

```sql
-- Tags coverage
SELECT
    COUNT(*) FILTER (WHERE tag_cache IS NOT NULL) as cards_with_tags,
    COUNT(*) FILTER (WHERE tag_cache IS NULL) as cards_without_tags,
    AVG(tag_confidence_avg) as avg_confidence,
    COUNT(*) FILTER (WHERE needs_tag_review = true) as needs_review
FROM cards;

-- Review queue status
SELECT * FROM review_queue_summary;

-- Tag distribution
SELECT * FROM tag_usage_stats ORDER BY card_count DESC LIMIT 20;

-- Recent extraction jobs
SELECT * FROM tagging_jobs ORDER BY created_at DESC LIMIT 5;
```

---

## Schema Ready for Deployment! ✅

**What we have:**
1. ✅ Full schema with hierarchy support
2. ✅ Confidence filtering built-in
3. ✅ Review queue for low-confidence cards
4. ✅ Automated cache maintenance
5. ✅ 70 initial tags seeded
6. ✅ Helper functions and views
7. ✅ Job tracking system

**Ready to deploy?** Run the SQL files in order:
1. `tags_and_abstractions_v1.sql`
2. `seed_tag_taxonomy.sql`

Then we'll build the LLM extraction function!
