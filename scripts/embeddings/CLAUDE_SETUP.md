# Using Claude (Anthropic) for Tag Extraction

**Updated:** 2025-12-13
**Status:** Ready to use with Claude API ✅

---

## Overview

The tag extraction system now supports **Claude (Anthropic)** as the primary LLM provider. This is perfect since you already use Claude!

### Why Claude?

- **You already use it** - No need for OpenAI account
- **Fast and cheap** - Claude 3.5 Haiku is optimized for this task
- **High quality** - Excellent at structured output (JSON)
- **Cost effective** - Similar pricing to GPT-4o-mini

---

## Setup Instructions

### 1. Get Your Anthropic API Key

1. Go to: https://console.anthropic.com/settings/keys
2. Sign in (or create account if needed)
3. Click "Create Key"
4. Copy your API key (starts with `sk-ant-`)

### 2. Add API Key to .env File

The `.env` file is located at: `/home/maxwell/vector-mtg/.env`

Edit the file and add your API key:

```bash
# Edit the .env file
nano /home/maxwell/vector-mtg/.env
```

Replace this line:
```bash
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

With your actual key:
```bash
ANTHROPIC_API_KEY=sk-ant-api01-abc123...your-real-key...
```

Save and exit (Ctrl+X, then Y, then Enter).

### 3. Load Environment Variables

```bash
cd /home/maxwell/vector-mtg
export $(cat .env | xargs)

# Verify it's loaded
echo $ANTHROPIC_API_KEY  # Should show your key
```

---

## Testing the Extraction

Run the test suite to validate extraction quality:

```bash
# Activate virtual environment
source venv/bin/activate

# Run test on 5 known combo cards
cd scripts/embeddings
python extract_card_tags.py
```

This will test extraction on:
1. **Pemmin's Aura** - Untapper
2. **Sol Ring** - Mana rock
3. **Blood Artist** - Death trigger
4. **Ashnod's Altar** - Sacrifice outlet
5. **Thassa's Oracle** - Win condition

Expected output:
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

## Model Options

### Default: Claude 3.5 Haiku (Recommended)

```python
extractor = CardTagExtractor()  # Auto-uses Haiku
```

**Pricing:**
- Input: $0.80 per MTok
- Output: $4.00 per MTok
- Per card: ~500 input + 100 output tokens
- **Cost per card: ~$0.0008**
- **For 508K cards: ~$400**

**Performance:**
- Fast (~150ms per card)
- Excellent accuracy
- Good at following JSON format

### Alternative: Claude 3.5 Sonnet (Higher Quality)

```python
extractor = CardTagExtractor(llm_model="claude-3-5-sonnet-20241022")
```

**Pricing:**
- Input: $3.00 per MTok
- Output: $15.00 per MTok
- **Cost per card: ~$0.003**
- **For 508K cards: ~$1,500**

**Performance:**
- Slower (~300ms per card)
- Best accuracy
- Better at edge cases

### Budget Option: Claude 3 Haiku (Older, Cheaper)

```python
extractor = CardTagExtractor(llm_model="claude-3-haiku-20240307")
```

**Pricing:**
- Input: $0.25 per MTok
- Output: $1.25 per MTok
- **Cost per card: ~$0.00025**
- **For 508K cards: ~$125**

**Performance:**
- Fast
- Good accuracy (slightly lower than 3.5)
- May need more review queue entries

---

## Cost Comparison

### For 508,000 cards:

| Model | Input Cost | Output Cost | Total Cost | Time |
|-------|-----------|-------------|------------|------|
| **Claude 3.5 Haiku** | $320 | $80 | **~$400** | ~1.5 hrs |
| Claude 3 Haiku | $100 | $25 | ~$125 | ~1.5 hrs |
| Claude 3.5 Sonnet | $1,200 | $300 | ~$1,500 | ~3 hrs |
| GPT-4o-mini | $50 | $20 | ~$70 | ~1.5 hrs |

**Recommendation:** Start with Claude 3.5 Haiku. It's the sweet spot of quality and cost.

---

## Using the Extractor

### Basic Usage

```python
from extract_card_tags import CardTagExtractor

# Initialize (auto-detects Claude from ANTHROPIC_API_KEY)
extractor = CardTagExtractor()

# Extract tags from a card
extraction = extractor.extract_tags(
    card_name="Lightning Bolt",
    oracle_text="Lightning Bolt deals 3 damage to any target.",
    type_line="Instant",
    card_id="abc-123"  # Optional: UUID from database
)

# Check results
if extraction.extraction_successful:
    print(f"Extracted {len(extraction.tags)} tags:")
    for tag in extraction.tags:
        print(f"  - {tag.tag}: {tag.confidence:.2f}")
else:
    print(f"Error: {extraction.error_message}")
```

### Storing in Database

```python
# Extract and store
extraction = extractor.extract_tags(
    card_name="Sol Ring",
    oracle_text="{T}: Add {C}{C}.",
    type_line="Artifact",
    card_id="def-456"
)

# Store in database (triggers auto-update cache and review queue)
success = extractor.store_tags(extraction, extraction_prompt_version="1.0")

if success:
    print(f"✅ Tags stored for {extraction.card_name}")
```

---

## Provider Auto-Detection

The extractor automatically detects which API to use:

1. If `ANTHROPIC_API_KEY` is set → Uses Claude
2. Else if `OPENAI_API_KEY` is set → Uses OpenAI
3. Else → Raises error

You can also explicitly specify:

```python
# Force Claude
extractor = CardTagExtractor(provider="anthropic")

# Force OpenAI (if you have key)
extractor = CardTagExtractor(provider="openai")
```

---

## Troubleshooting

### "No API key found"

Make sure your `.env` file has the API key:
```bash
cat .env | grep ANTHROPIC_API_KEY
```

And export it:
```bash
export $(cat .env | xargs)
```

### "anthropic package not installed"

```bash
source venv/bin/activate
pip install anthropic==0.39.0
```

### "Authentication error"

Your API key might be invalid. Check:
1. Key starts with `sk-ant-`
2. Key is not expired
3. You have API credits remaining

### Rate Limits

Claude has generous rate limits:
- Tier 1: 50 requests/min
- Tier 2: 1,000 requests/min
- Tier 3: 2,000 requests/min

For batch processing 508K cards, you'll need Tier 2+ or add delays.

---

## Next Steps

1. **✅ Get Anthropic API key** (from https://console.anthropic.com/settings/keys)
2. **✅ Add to .env file**
3. **✅ Export environment variables**
4. **→ Run test suite** (`python extract_card_tags.py`)
5. **→ Review results and adjust prompt if needed**
6. **→ Build batch processing script**
7. **→ Process all 508K cards**

---

## Files Updated

- `/home/maxwell/vector-mtg/.env` - Added ANTHROPIC_API_KEY
- `/home/maxwell/vector-mtg/requirements.txt` - Added anthropic package
- `/home/maxwell/vector-mtg/scripts/embeddings/extract_card_tags.py` - Supports both providers
- This guide: `CLAUDE_SETUP.md`

---

## Ready to Test! 🚀

Once you have your ANTHROPIC_API_KEY in the .env file:

```bash
cd /home/maxwell/vector-mtg
source venv/bin/activate
export $(cat .env | xargs)
cd scripts/embeddings
python extract_card_tags.py
```

This will test Claude's tag extraction on 5 known combo cards!
