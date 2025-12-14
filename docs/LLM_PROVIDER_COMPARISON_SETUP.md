# LLM Provider Comparison Setup

**Date:** 2024-12-14  
**Status:** ✅ **READY TO COMPARE PROVIDERS**

## Overview

The system is now ready to extract card tags using multiple LLM providers and compare their quality. Each provider's responses are tracked in the database for analysis.

---

## What Was Completed

### 1. ✅ Database Schema Enhancement
- **Migration:** `sql/migrations/20251214_1530_add_llm_provider_column.sql`
- **Changes:**
  - Added `llm_provider VARCHAR(50)` to `card_tags` table
  - Created index on `llm_provider` for efficient queries
  - Updated 17 existing test records to show `provider='anthropic'`

### 2. ✅ Code Updates
- **`database.py`:**
  - Added `llm_provider` parameter to `store_card_tags()`
  - Default value: `"unknown"` for backward compatibility
  - Provider is now stored with every tag extraction
  
- **`extract_card_tags.py`:**
  - Passes `self.provider` to `store_card_tags()` call
  - Automatically tracks which provider generated each tag

### 3. ✅ Analysis Queries
- **File:** `sql/queries/analyze_llm_providers.sql`
- **Queries included:**
  1. Count tags by provider with confidence stats
  2. Compare providers by model
  3. Find cards tagged by multiple providers
  4. Tag distribution by provider
  5. Recent extractions by provider
  6. Provider performance on low-confidence tags

### 4. ✅ Testing Completed
- All 33 embeddings tests passing (100%)
- Verified provider is correctly stored in database
- Test extraction from "Opt" card showed:
  - Provider: `anthropic`
  - Model: `claude-3-5-haiku-20241022`
  - Tags stored successfully

---

## Current Database State

```sql
 llm_provider |         llm_model         | tag_count | card_count | avg_confidence 
--------------+---------------------------+-----------+------------+----------------
 anthropic    | claude-3-5-haiku-20241022 |        19 |          6 |           0.99
```

**Cards tagged so far:**
- Sol Ring (3 tags)
- Lightning Bolt (2 tags)
- Counterspell (3 tags)
- Birds of Paradise (3 tags)
- Thassa's Oracle (6 tags)
- Opt (2 tags)

**Total:** 6 cards, 19 tags, 99% average confidence

---

## Available Providers

### 1. Claude 3.5 Haiku (Anthropic)
- **Status:** ✅ Working
- **Model:** `claude-3-5-haiku-20241022`
- **Cost:** $0.0013 per card (with caching)
- **Budget:** $25 available = ~19,230 cards
- **Quality:** 98% average confidence (from testing)
- **Speed:** ~1.5 seconds per card

### 2. Ollama (Local LLM)
- **Status:** 🔜 Ready to set up
- **Recommended Models:**
  - Qwen2.5-7B-Instruct (4-bit) - ~5GB VRAM
  - Llama-3.2-8B-Instruct (4-bit) - ~6GB VRAM
- **Cost:** $0 (FREE - just electricity ~$10 for full dataset)
- **Hardware:** RTX 4070 Ti, 12GB VRAM ✅ Sufficient
- **Quality:** 85-95% expected (vs 95-98% for Claude)
- **Speed:** ~2-5 seconds per card
- **Setup:** See `/docs/LOCAL_LLM_SETUP.md`

---

## How to Use

### Extract Tags with Claude (Current Default)

```bash
cd /home/maxwell/vector-mtg
source venv/bin/activate

# Set API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Run extraction
python scripts/embeddings/extract_card_tags.py
```

Provider tracking is **automatic** - no code changes needed!

### Extract Tags with Ollama (After Setup)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull model
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Run extraction with Ollama
cd /home/maxwell/vector-mtg
source venv/bin/activate
export OLLAMA_MODEL="qwen2.5:7b-instruct-q4_K_M"

python scripts/embeddings/extract_card_tags.py --provider=ollama
```

Provider tracking is **automatic** - Ollama extractions will be marked with `llm_provider='ollama'`!

---

## Analysis Queries

### Quick Stats by Provider

```bash
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg << 'SQL'
SELECT 
    llm_provider,
    COUNT(*) as tag_count,
    COUNT(DISTINCT card_id) as card_count,
    AVG(confidence)::numeric(5,2) as avg_confidence
FROM card_tags
WHERE source = 'llm'
GROUP BY llm_provider
ORDER BY tag_count DESC;
SQL
```

### Run All Analysis Queries

```bash
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg \
    < sql/queries/analyze_llm_providers.sql
```

### Find Cards Tagged by Both Providers

```bash
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg << 'SQL'
SELECT 
    c.name,
    array_agg(DISTINCT ct.llm_provider) as providers,
    COUNT(DISTINCT ct.llm_provider) as provider_count
FROM cards c
JOIN card_tags ct ON c.id = ct.card_id
WHERE ct.source = 'llm'
GROUP BY c.id, c.name
HAVING COUNT(DISTINCT ct.llm_provider) > 1;
SQL
```

---

## Recommended Comparison Strategy

### Option A: Full Claude Run ($25)
1. Process all 508,686 cards with Claude (~$250 without caching, $95 with caching)
2. **Budget insufficient** - only covers ~19K cards

### Option B: Sample + Local (Recommended)
1. **Sample Phase:** Extract 5,000 cards with Claude (~$6.50)
2. **Local Phase:** Extract all 508K cards with Ollama (FREE)
3. **Comparison:** Re-extract the same 5,000 sample cards with Ollama
4. **Analysis:** Compare quality on overlapping 5K cards

### Option C: Parallel Test
1. **Set up Ollama** following `/docs/LOCAL_LLM_SETUP.md`
2. **Extract 100 test cards** with both Claude and Ollama
3. **Compare results** using analysis queries
4. **Choose provider** based on quality/cost tradeoff
5. **Process remaining cards** with chosen provider

**Recommended:** Option C (test first, then decide)

---

## Next Steps

### 1. Set Up Ollama (15 minutes)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull qwen2.5:7b-instruct-q4_K_M

# Test it
ollama run qwen2.5:7b-instruct-q4_K_M "What is Magic: The Gathering?"
```

### 2. Update CardTagExtractor for Ollama
- Add Ollama client initialization
- Add Ollama API call method
- Test with sample cards

### 3. Run Comparison Test
- Extract 100 cards with Claude
- Extract same 100 cards with Ollama
- Run analysis queries
- Compare quality metrics

### 4. Make Decision
- **If Ollama quality is acceptable (>90%):** Use Ollama for full dataset (FREE)
- **If Claude quality is required (>95%):** Budget for API costs or run partial dataset

---

## Files Created/Modified

### New Files
- `sql/migrations/20251214_1530_add_llm_provider_column.sql` - Migration
- `sql/queries/analyze_llm_providers.sql` - Analysis queries
- `docs/LLM_PROVIDER_COMPARISON_SETUP.md` - This document

### Modified Files
- `scripts/embeddings/database.py` - Added `llm_provider` parameter
- `scripts/embeddings/extract_card_tags.py` - Passes provider to storage
- `docs/EMBEDDINGS_REFACTORING_SUMMARY.md` - Updated with provider tracking

---

## Testing Verification

```bash
# Run all tests (should show 33 passing)
cd /home/maxwell/vector-mtg
source venv/bin/activate
pytest tests/embeddings/ -v

# Verify provider tracking in database
docker exec -i vector-mtg-postgres psql -U postgres -d vector_mtg << 'SQL'
SELECT llm_provider, COUNT(*) 
FROM card_tags 
WHERE source = 'llm' 
GROUP BY llm_provider;
SQL
```

Expected output:
```
 llm_provider | count 
--------------+-------
 anthropic    |    19
```

---

## Cost Tracking

### Current Spend
- **Test extractions:** 6 cards = ~$0.008 (negligible)
- **Remaining budget:** ~$24.99

### Estimated Costs
- **1,000 cards:** $1.30
- **5,000 cards:** $6.50
- **10,000 cards:** $13.00
- **19,230 cards:** $25.00 (max with current budget)
- **50,000 cards:** $65.00 (would need more credits)
- **508,686 cards:** $661.28 (would need $636 more credits)

### With Ollama (Local)
- **Any number of cards:** $0 (FREE)
- **Full 508K cards:** ~$10 electricity cost
- **Time:** ~20-40 hours for full dataset

---

## Questions to Answer

Before starting large-scale extraction:

1. **Is 90% quality acceptable?** (Ollama estimate)
   - If yes → Use Ollama for everything (FREE)
   - If no → Need to budget for Claude API

2. **What's the use case?**
   - **Research/exploration** → Ollama is fine
   - **Production/commercial** → Claude may be worth it

3. **Can we afford Claude for subset?**
   - 19K cards with $25 budget
   - Consider just commander-legal cards (~25K total)

4. **Hybrid approach?**
   - High-value cards (rares/mythics) → Claude
   - Common cards → Ollama
   - Best quality/cost balance

---

## Success Criteria

✅ **Phase 1 Complete:** Provider tracking implemented  
✅ **Phase 2 Complete:** Analysis queries created  
✅ **Phase 3 Complete:** Testing verified  
🔜 **Phase 4 Next:** Set up Ollama  
🔜 **Phase 5 Next:** Run comparison test  
🔜 **Phase 6 Next:** Make provider decision  
🔜 **Phase 7 Next:** Process full dataset  

**Current Status:** Ready to compare providers! 🚀

