# EDHREC Scraper - Quick Start

## ✅ Working Solution (Playwright)

### Install

```bash
# 1. Install Python dependencies
./venv/bin/pip install playwright pytest-playwright

# 2. Download Playwright's Chromium (~174 MB)
./venv/bin/playwright install chromium
```

### Run

```bash
# Test scraper (scrapes Atraxa)
./venv/bin/python scripts/edhrec_playwright_scraper.py
```

### Output

```
data_sources_comprehensive/edhrec_scraped/atraxa-praetors-voice_TIMESTAMP.json
```

### Performance

- **Time:** ~14s per commander
- **Cards extracted:** ~298 per commander
- **Data completeness:** 99.7%

---

## Sample Output

```json
{
  "metadata": {
    "commander_url": "https://edhrec.com/commanders/atraxa-praetors-voice",
    "commander_slug": "atraxa-praetors-voice",
    "scraped_at": "2025-12-06T10:45:11.622603",
    "elapsed_seconds": 13.99,
    "total_cards": 298,
    "extraction_method": "dom"
  },
  "cards": [
    {
      "name": "Tekuthal, Inquiry Dominus",
      "inclusion": 64,
      "synergy": 26,
      "num_decks": "24.6K",
      "total_decks": "38.3K"
    }
  ]
}
```

---

## Why Playwright?

- ✅ **Bundles its own Chromium** (no system dependencies)
- ✅ **Bypasses Ubuntu's broken snap system**
- ✅ **Modern async API**
- ✅ **Better performance than Selenium**
- ✅ **Actively maintained**

---

## Files

- **Main scraper:** `scripts/edhrec_playwright_scraper.py`
- **Output directory:** `data_sources_comprehensive/edhrec_scraped/`
- **Full docs:** `EDHREC_SCRAPER_FINAL.md`

---

## Next: Mass Scraping

To scrape all commanders (~1500), create a loop:

```python
commanders = ["atraxa-praetors-voice", "muldrotha-the-gravetide", ...]
scraper = EDHRECPlaywrightScraper()

for slug in commanders:
    result = scraper.scrape_commander(slug)
    scraper.save_results(result, slug)
```

**Estimated time:** ~6 hours for 1500 commanders
