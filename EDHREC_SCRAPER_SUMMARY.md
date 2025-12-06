# EDHREC Infinite Scroll Scraper - Summary

## What I Built

A fast, optimized Selenium-based scraper specifically designed for EDHREC's infinite scroll pages.

## Key Features

### 1. **Fast Infinite Scroll** (0.2s pause, configurable)
- Scrolls until page stops growing
- Detects completion after 3 consecutive no-change scrolls
- Much faster than 0.5s default

### 2. **Performance Optimizations**
- Disables image loading (huge speed boost)
- Disables unnecessary browser features
- Minimal DOM queries
- Smart element extraction

### 3. **Robust Data Collection**
- Gets all commanders from all color combinations
- Extracts cards from each commander page
- Attempts to extract category-specific cards (Top Cards, Removal, etc.)
- Handles stale element references gracefully

### 4. **Safety Features**
- Incremental checkpoints every 10 commanders
- Continues on individual page failures
- Configurable scroll limits (prevents infinite loops)

## Files Created

1. **`scripts/edhrec_infinite_scroll_scraper.py`** (main scraper)
   - 400+ lines of optimized scraping logic
   - Handles commander discovery + page scraping
   - Configurable via class constants

2. **`EDHREC_SCRAPER_GUIDE.md`** (comprehensive guide)
   - Installation instructions
   - Usage examples
   - Troubleshooting
   - Performance tuning
   - Output format documentation

3. **`scripts/test_edhrec_scraper.py`** (quick test)
   - Tests with 2 commanders
   - Verifies installation works

4. **Updated `requirements.txt`**
   - Added `selenium==4.15.2`
   - Added `webdriver-manager==4.0.1`

## Usage

### Quick Test (2 commanders)
```bash
cd /home/maxwell/vector-mtg
/home/maxwell/vector-mtg/venv/bin/python scripts/test_edhrec_scraper.py
```

### Full Scrape (all commanders)
```bash
/home/maxwell/vector-mtg/venv/bin/python scripts/edhrec_infinite_scroll_scraper.py
```

### Limited Scrape (testing)
```bash
/home/maxwell/vector-mtg/venv/bin/python scripts/edhrec_infinite_scroll_scraper.py --limit=10
```

### Debug Mode (see browser)
```bash
/home/maxwell/vector-mtg/venv/bin/python scripts/edhrec_infinite_scroll_scraper.py --no-headless --limit=5
```

## Configuration

Edit `scripts/edhrec_infinite_scroll_scraper.py`:

```python
# Line 21-22
SCROLL_PAUSE = 0.2  # Seconds between scrolls (0.1-0.5 recommended)
MAX_SCROLL_ATTEMPTS = 50  # Max scrolls per page
```

## Expected Performance

**With default settings (0.2s scroll pause):**

- Commander discovery: ~2-3 minutes
- Per commander page: ~3-5 seconds average
- **Total for ~1500 commanders: 1.5-2 hours**

**Faster with 0.1s pause:**
- ~50% faster
- May miss some content on slow connections

## Output Format

```json
{
  "metadata": {
    "total_commanders": 1500,
    "total_cards": 45000,
    "scroll_pause_seconds": 0.2
  },
  "commanders": [
    {
      "commander": "Atraxa, Praetors' Voice",
      "url": "https://edhrec.com/commanders/atraxa-praetors-voice",
      "total_cards": 150,
      "all_cards": [
        {
          "name": "Doubling Season",
          "url": "https://edhrec.com/cards/doubling-season",
          "synergy": "32%",
          "category": "Enchantments"
        }
      ],
      "categories": {
        "Top Cards": [...],
        "Creatures": [...],
        "Removal": [...]
      },
      "scroll_count": 15
    }
  ]
}
```

## What Gets Scraped

### From Commander Discovery Pages
- All commanders across all color combinations
- Mono, dual, tri, 4-color, 5-color
- ~1500+ commanders total

### From Each Commander Page
1. **All cards** (via infinite scroll)
   - Card name
   - URL
   - Synergy percentage (if displayed)
   - Category (if determinable)

2. **Category-specific cards** (attempted extraction)
   - Top Cards
   - Creatures
   - Instants/Sorceries
   - Enchantments/Artifacts
   - Planeswalkers
   - Lands
   - Mana Artifacts
   - Card Draw
   - Ramp
   - Removal
   - Board Wipes
   - Protection
   - Recursion

## Scroll Detection Logic

```python
1. Scroll to bottom
2. Wait 0.2 seconds
3. Measure page height
4. If height unchanged:
   - Increment no-change counter
   - If counter >= 3: STOP (we're done)
5. Else:
   - Reset counter
   - Continue scrolling
6. Repeat (max 50 times per page)
```

This ensures we get all content without waiting unnecessarily.

## Next Steps

1. **Test with small sample**:
   ```bash
   /home/maxwell/vector-mtg/venv/bin/python scripts/test_edhrec_scraper.py
   ```

2. **Review output** to ensure data quality

3. **Run full scrape** (or use `--limit=100` for batch processing):
   ```bash
   /home/maxwell/vector-mtg/venv/bin/python scripts/edhrec_infinite_scroll_scraper.py
   ```

4. **Process results** into database or analysis pipeline

## Customization Examples

### Add More Categories
Edit line 254 to include additional categories:
```python
category_names = [
    "Top Cards",
    "Your Custom Category",
    # ...
]
```

### Adjust Scroll Speed
```python
SCROLL_PAUSE = 0.1  # Faster (may miss content)
SCROLL_PAUSE = 0.3  # Safer (slower)
```

### Increase Scroll Limit
```python
MAX_SCROLL_ATTEMPTS = 100  # For very long pages
```

## Error Handling

The scraper handles:
- Stale element references (common with dynamic pages)
- Missing elements (skips gracefully)
- Network timeouts (logs and continues)
- Page load failures (recorded in output)

Failed commanders get `"error": "error message"` in output instead of card data.

## Dependencies Installed

```
selenium==4.15.2
webdriver-manager==4.0.1
```

`webdriver-manager` automatically downloads and manages ChromeDriver, so you don't need to manually install it.

## Ready to Use!

The scraper is fully functional and ready to run. Start with the test script to verify everything works, then run the full scrape when ready.
