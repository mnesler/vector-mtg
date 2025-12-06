# ✅ EDHREC Scraper - Playwright Solution Working

## Summary

**✅ PROBLEM SOLVED**: Bypassed Ubuntu's broken snap system by using **Playwright's bundled Chromium**

## What Changed

### ❌ Previous Problem
- Ubuntu's Chromium snap corrupted (revision 3320 empty)
- Ubuntu's Firefox snap corrupted (revision 7423 empty)
- Selenium required system-installed browsers
- **Could not run any browser automation**

### ✅ Solution
- Installed **Playwright** (`pip install playwright`)
- Downloaded **Playwright's own Chromium** (`playwright install chromium`)
- Chromium installed to `~/.cache/ms-playwright/chromium-1194/`
- **Completely independent of Ubuntu's snap system**

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| Playwright | ✅ Installed | Version 1.56.0 |
| Chromium | ✅ Working | Build 1194 (141.0.7390.37) |
| Scraper | ⚠️  Partial | Extracts cards but wrong data |
| Data Saver | ✅ Working | Atomic writes, verified |

## Test Results

```bash
$ ./venv/bin/python scripts/edhrec_playwright_scraper.py

============================================================
Scraping: atraxa-praetors-voice
============================================================

⏳ Loading page...
✓ Page loaded

⏳ Waiting for card elements to load...
✓ Cards detected

⏳ Extracting card data...
  Found 298 card containers
  Progress: 298/298 (100%)

✓ Extracted 298 cards

============================================================
✓ Scrape Complete!
  Total cards: 298
  Time: 7.04s
============================================================

✓ Saved successfully (32,706 bytes)
```

## What's Working

✅ Playwright launches Chromium  
✅ Loads EDHREC pages  
✅ Waits for dynamic content  
✅ Finds card elements (.CardLabel_container__3M9Zu)  
✅ Extracts 298 cards  
✅ Saves JSON to disk  
✅ Atomic file writes  
✅ Data verification  

## What Needs Fixing

⚠️ **Card name extraction is wrong** - Currently extracting percentages instead of names

### Current Output
```json
{
  "name": "64%",  ← WRONG (this is inclusion %)
  "raw_text": "64%\ninclusion\n24.6K decks\n38.3K decks\n26%\nsynergy"
}
```

### Should Be
```json
{
  "name": "Tek uthal, Inquiry Dominus",  ← Correct card name
  "inclusion": 64,
  "synergy": 26
}
```

## Next Steps

1. **Fix selector to get actual card names** (currently getting stats container)
2. **Extract card URLs** (`/cards/card-name`)
3. **Parse synergy/inclusion correctly**
4. **Test with multiple commanders**
5. **Build mass scraper** (for all ~1500 commanders)

## Files Created

- `scripts/edhrec_playwright_scraper.py` - Main scraper (needs selector fix)
- `data_sources_comprehensive/edhrec_scraped/atraxa-praetors-voice_*.json` - Test output
- `scripts/debug_edhrec_structure.py` - Page analysis tool
- `scripts/inspect_edhrec_page.py` - Selector testing tool

## Key Insight

**EDHREC's website structure changed** - Old selectors from previous sessions don't work:
- ❌ Old: `a.Card_card__item__1L7HG` (doesn't exist)  
- ✅ New: `.CardLabel_container__3M9Zu` (exists, but contains stats not names)

Need to find the correct element that contains the card name + link.

## Installation Commands

For future reference or other systems:

```bash
# Install Playwright
./venv/bin/pip install playwright pytest-playwright

# Download Playwright's Chromium (bypasses snap)
./venv/bin/playwright install chromium

# Test scraper
./venv/bin/python scripts/edhrec_playwright_scraper.py
```

## Performance

- **Page load:** ~2s  
- **Card extraction:** ~5s (298 cards)  
- **Total per commander:** ~7s  
- **Estimated for 1500 commanders:** ~3 hours

---

**Status:** Playwright working, scraper extracting data, just needs correct selectors for card names.
