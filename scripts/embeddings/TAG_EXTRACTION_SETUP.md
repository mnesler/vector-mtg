# Tag Extraction System - Setup Guide

**Status:** Phase 2 - LLM Extraction Function Complete ✅
**Created:** 2025-12-13

---

## What We Built

The LLM-based tag extraction system that analyzes MTG cards and extracts functional mechanics tags.

### Components Created:

1. **`extract_card_tags.py`** - Main extraction script
   - `CardTagExtractor` class - LLM-powered tag extraction
   - `test_extraction_on_known_cards()` - Test suite
   - Database integration for storing results

2. **Updated `requirements.txt`** - Added OpenAI dependency
3. **`.env.example`** - Environment configuration template

---

## Setup Instructions

### 1. Prerequisites

- ✅ PostgreSQL with tag schema deployed (completed)
- ✅ Python 3.14+ with virtual environment
- ⏳ OpenAI API key (you need to configure this)

### 2. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install OpenAI library (already done)
pip install openai==1.54.0

# Or install all requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
```

Add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 4. Load Environment Variables

```bash
# Option A: Export for current session
export $(cat .env | xargs)

# Option B: Use python-dotenv (recommended for scripts)
pip install python-dotenv
```

If using python-dotenv, add to extract_card_tags.py:
```python
from dotenv import load_dotenv
load_dotenv()  # Add at the top of the file
```

---

## Testing the Extraction System

### Test on Known Combo Cards

The script includes a test suite that validates extraction quality on 5 well-known combo cards:

```bash
# Activate venv and set API key
source venv/bin/activate
export OPENAI_API_KEY=sk-proj-...

# Run test suite
cd scripts/embeddings
python extract_card_tags.py
```

### Expected Output

The test will analyze these cards:
1. **Pemmin's Aura** - Untapper combo piece
2. **Sol Ring** - Mana rock
3. **Blood Artist** - Death trigger
4. **Ashnod's Altar** - Sacrifice outlet
5. **Thassa's Oracle** - Win condition

For each card, you'll see:
- ✅ Successfully extracted tags with confidence scores
- ⚠️ Comparison to expected tags
- 🎉 Perfect match or ❌ missing/extra tags

### Example Output:

```
================================================================================
Testing: Sol Ring
================================================================================
✅ Extraction successful

Extracted 3 tags:
  ✅ artifact: 1.00
  ✅ generates_mana: 1.00
  ✅ generates_colorless_mana: 1.00

Expected tags: artifact, generates_mana, generates_colorless_mana

🎉 Perfect match!
```

---

## Using the Extraction System

### Basic Usage

```python
from extract_card_tags import CardTagExtractor

# Initialize extractor
extractor = CardTagExtractor(
    llm_model="gpt-4o-mini",  # Recommended: cheap and fast
    api_key="sk-proj-..."      # Or set OPENAI_API_KEY env var
)

# Extract tags from a card
extraction = extractor.extract_tags(
    card_name="Lightning Bolt",
    oracle_text="Lightning Bolt deals 3 damage to any target.",
    type_line="Instant",
    card_id="abc-123-bolt"  # Optional: UUID from database
)

# Check results
if extraction.extraction_successful:
    for tag in extraction.tags:
        print(f"{tag.tag}: {tag.confidence:.2f}")
else:
    print(f"Error: {extraction.error_message}")
```

### Storing Tags in Database

```python
# Extract and store in one go
extraction = extractor.extract_tags(
    card_name="Sol Ring",
    oracle_text="{T}: Add {C}{C}.",
    type_line="Artifact",
    card_id="def-456-solring"
)

# Store in database (triggers will auto-update cache)
success = extractor.store_tags(
    extraction,
    extraction_prompt_version="1.0"
)

if success:
    print(f"✅ Tags stored for {extraction.card_name}")
    # Automatic side effects from trigger:
    # - cards.tag_cache updated
    # - cards.tag_confidence_avg calculated
    # - Added to review queue if avg < 0.7
```

---

## Performance & Cost Estimates

### Using GPT-4o-mini (Recommended)

**Cost:**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Per card: ~500 input + 100 output tokens
- Cost per card: ~$0.00013

**For 508K cards:**
- Total cost: ~$65-$70
- Processing time: ~1.5-2 hours
- Rate limit: 10,000 requests/minute

### Using GPT-4 (Higher Quality)

**Cost:**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Per card: ~500 input + 100 output tokens
- Cost per card: ~$0.0022

**For 508K cards:**
- Total cost: ~$1,100-$1,200
- Processing time: ~3-4 hours
- Better accuracy on edge cases

**Recommendation:** Start with GPT-4o-mini, use GPT-4 only for low-confidence re-extraction.

---

## Next Steps

### Option A: Validate on Sample Cards (Recommended First)

1. Run test suite: `python extract_card_tags.py`
2. Review accuracy and confidence scores
3. Adjust prompt if needed (in `_build_extraction_prompt()`)
4. Test on 100 random cards from database
5. Calculate accuracy metrics

### Option B: Build Batch Processing Script

Create `batch_tag_cards.py` to process all 508K cards:
```bash
scripts/embeddings/batch_tag_cards.py \
    --model gpt-4o-mini \
    --batch-size 100 \
    --start-index 0 \
    --end-index 508000
```

Features needed:
- Progress tracking (save state every 1000 cards)
- Error handling and retry logic
- Job tracking in `tagging_jobs` table
- Resume from interruption

### Option C: Build Review Interface

Before batch processing, build a UI to:
- View cards in review queue
- Manually adjust low-confidence tags
- Approve or reject LLM suggestions
- Export training data for fine-tuning

---

## Monitoring Extraction Quality

### After Running Test Suite

Check tag distribution:
```sql
SELECT
    t.display_name,
    COUNT(*) as card_count,
    AVG(ct.confidence) as avg_confidence,
    MIN(ct.confidence) as min_confidence,
    MAX(ct.confidence) as max_confidence
FROM card_tags ct
JOIN tags t ON ct.tag_id = t.id
WHERE ct.source = 'llm'
GROUP BY t.id, t.display_name
ORDER BY card_count DESC;
```

Check review queue:
```sql
SELECT
    reason,
    COUNT(*) as queue_count,
    AVG(c.tag_confidence_avg) as avg_confidence
FROM tagging_review_queue rq
JOIN cards c ON rq.card_id = c.id
WHERE rq.status = 'pending'
GROUP BY reason
ORDER BY queue_count DESC;
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"

```bash
source venv/bin/activate
pip install openai==1.54.0
```

### "Authentication error" or "Invalid API key"

Check your `.env` file:
```bash
cat .env | grep OPENAI_API_KEY
```

Make sure to export it:
```bash
export $(cat .env | xargs)
echo $OPENAI_API_KEY  # Should show your key
```

### "Failed to parse LLM response"

The LLM returned invalid JSON. Check the logs for the raw response.

Common causes:
- Model hallucinated tag names not in taxonomy
- Returned explanation instead of JSON
- Used incorrect JSON format

Fix: Lower temperature (currently 0.1) or add more examples to prompt.

### "Database connection failed"

Check PostgreSQL is running:
```bash
docker compose ps | grep postgres
```

Check connection string in `.env`:
```bash
POSTGRES_HOST=localhost  # Not 'postgres' when connecting from host
POSTGRES_PORT=5432
```

---

## Configuration Options

### Model Selection

```python
# Recommended for production
extractor = CardTagExtractor(llm_model="gpt-4o-mini")

# For higher quality (10x more expensive)
extractor = CardTagExtractor(llm_model="gpt-4-turbo")

# For testing (fastest, cheapest)
extractor = CardTagExtractor(llm_model="gpt-3.5-turbo")
```

### Confidence Thresholds

Default thresholds are set in the database schema:
- Production: 0.7 (use in searches)
- Review queue: < 0.7 (manual review)
- Very low: < 0.5 (urgent review)

To adjust, modify the trigger function in `tags_and_abstractions_v1.sql`.

### Prompt Versions

Track prompt iterations using `extraction_prompt_version`:
```python
extractor.store_tags(extraction, extraction_prompt_version="1.1")
```

This lets you:
- A/B test different prompts
- Re-extract cards with improved prompts
- Track which version extracted each tag

---

## File Structure

```
vector-mtg/
├── .env                          # Your API keys (DO NOT COMMIT)
├── .env.example                  # Template for .env
├── requirements.txt              # Python dependencies
├── venv/                         # Virtual environment
├── schema/
│   ├── tags_and_abstractions_v1.sql   # Schema (deployed)
│   └── seed_tag_taxonomy.sql          # 65 tags (deployed)
└── scripts/embeddings/
    ├── extract_card_tags.py      # LLM extraction (THIS FILE)
    ├── batch_tag_cards.py        # TODO: Batch processing
    └── TAG_EXTRACTION_SETUP.md   # This guide
```

---

## Ready to Extract! 🚀

**Completed:**
1. ✅ Schema deployed with 65 tags
2. ✅ LLM extraction function built
3. ✅ Test suite created
4. ✅ Dependencies installed

**Next:**
1. ⏳ Set OPENAI_API_KEY in .env
2. ⏳ Run test suite to validate quality
3. ⏳ Build batch processing script
4. ⏳ Process all 508K cards

Once you have your API key configured, run:
```bash
source venv/bin/activate
export OPENAI_API_KEY=sk-proj-...
python scripts/embeddings/extract_card_tags.py
```

This will test extraction on 5 known combo cards and show you the quality of results!
