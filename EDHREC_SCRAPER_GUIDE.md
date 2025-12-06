# EDHREC Infinite Scroll Scraper

Fast, optimized scraper for EDHREC commander pages with infinite scroll support.

## Features

- **Fast scrolling**: 200ms pause between scrolls (configurable)
- **Smart scroll detection**: Stops when page stops growing
- **Category extraction**: Gets cards organized by category (Top Cards, Creatures, Removal, etc.)
- **Incremental saves**: Checkpoints every 10 commanders
- **Optimized browser**: Disables images and unnecessary features for speed
- **Robust error handling**: Continues on individual page failures

## Installation

```bash
source venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `selenium==4.15.2`
- `webdriver-manager==4.0.1` (auto-manages ChromeDriver)

## Usage

### Basic Usage (All Commanders)

```bash
source venv/bin/activate
python scripts/edhrec_infinite_scroll_scraper.py
```

### Test with Limited Commanders

```bash
# Scrape only first 5 commanders (for testing)
python scripts/edhrec_infinite_scroll_scraper.py --limit=5
```

### Run with Visible Browser (Debug Mode)

```bash
# See the browser in action (not headless)
python scripts/edhrec_infinite_scroll_scraper.py --no-headless
```

### Combined Options

```bash
# Test with 10 commanders, visible browser
python scripts/edhrec_infinite_scroll_scraper.py --limit=10 --no-headless
```

## Output

### File Location

Results saved to: `data_sources_comprehensive/edhrec_full/edhrec_commanders_YYYYMMDD_HHMMSS.json`

Checkpoints saved to: `data_sources_comprehensive/edhrec_full/checkpoint_N.json`

### Output Format

```json
{
  "metadata": {
    "source": "EDHREC (Infinite Scroll)",
    "scraped_at": "2024-12-04T20:00:00",
    "total_commanders": 1500,
    "total_cards": 45000,
    "scroll_pause_seconds": 0.2,
    "method": "Selenium with optimized infinite scroll"
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
          "category": "Enchantments",
          "scraped_at": "2024-12-04T20:00:00"
        }
      ],
      "categories": {
        "Top Cards": [...],
        "Creatures": [...],
        "Removal": [...]
      },
      "scroll_count": 15,
      "scraped_at": "2024-12-04T20:00:00"
    }
  ]
}
```

## Performance Tuning

### Adjust Scroll Speed

Edit `scripts/edhrec_infinite_scroll_scraper.py`:

```python
# Line 21-22
SCROLL_PAUSE = 0.2  # Change this value (seconds)
MAX_SCROLL_ATTEMPTS = 50  # Max scrolls per page
```

**Recommendations:**
- `0.1s` - Very fast, may miss content on slow connections
- `0.2s` - **Default**, good balance
- `0.3s` - Safer for slower connections
- `0.5s` - Conservative, very reliable

### Disable Image Loading

Images are already disabled by default for maximum speed. If you need to enable them:

```python
# Remove these lines (around line 57-58)
options.add_argument("--disable-images")
options.add_argument("--blink-settings=imagesEnabled=false")
```

## Expected Runtime

**Estimated times** (with 0.2s scroll pause):

- **Discovery phase**: ~2-3 minutes (finds all commanders)
- **Per commander**: ~3-5 seconds average
  - 2 seconds: Simple commanders with few cards
  - 10 seconds: Popular commanders with many cards (Atraxa, Urza, etc.)
- **1500 commanders**: ~1.5 - 2 hours total

**Faster with adjustments:**
- Reduce `SCROLL_PAUSE` to `0.1s`: ~50% faster
- Increase `MAX_SCROLL_ATTEMPTS` if pages aren't fully loading

## Troubleshooting

### ChromeDriver Issues

**Error**: `ChromeDriver not found`

**Solution**: `webdriver-manager` auto-downloads ChromeDriver. If it fails:

```bash
# Install Chrome/Chromium first
sudo apt-get install chromium-browser  # Linux
# OR
brew install --cask google-chrome      # Mac
```

### Selenium Not Installed

**Error**: `ModuleNotFoundError: No module named 'selenium'`

**Solution**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Script Hangs or Times Out

**Possible causes:**
1. Slow internet connection → Increase `SCROLL_PAUSE` to `0.3s` or `0.5s`
2. EDHREC is slow/down → Wait and try again
3. Page structure changed → Check logs for errors

### Memory Issues

If scraping 1500+ commanders causes memory issues:

1. **Use checkpoints**: Script saves every 10 commanders
2. **Run in batches**: Use `--limit=100` and combine results later
3. **Increase system memory**: Close other applications

## Advanced: Scraping Specific Categories

The scraper attempts to extract these categories from the left sidebar:

- Top Cards
- Creatures
- Instants
- Sorceries
- Enchantments
- Artifacts
- Planeswalkers
- Lands
- Mana Artifacts
- Card Draw
- Ramp
- Removal
- Board Wipes
- Protection
- Recursion

**To add more categories**, edit line 254:

```python
category_names = [
    "Top Cards",
    "Your New Category Here",
    # ...
]
```

## Example: Process Results

```python
import json

# Load scraped data
with open('data_sources_comprehensive/edhrec_full/edhrec_commanders_20241204_200000.json') as f:
    data = json.load(f)

# Get all commanders
commanders = data['commanders']

# Find a specific commander
atraxa = next(c for c in commanders if 'atraxa' in c['commander'].lower())
print(f"Atraxa has {atraxa['total_cards']} cards")

# Get all cards in "Removal" category
removal_cards = atraxa['categories'].get('Removal', [])
print(f"Removal cards: {len(removal_cards)}")

# Get top cards by synergy
top_cards = sorted(
    atraxa['all_cards'],
    key=lambda x: int(x['synergy'].rstrip('%')) if x.get('synergy') else 0,
    reverse=True
)[:10]

for card in top_cards:
    print(f"  {card['name']} - {card.get('synergy', 'N/A')}")
```

## Tips

1. **Start small**: Test with `--limit=5` first to verify it works
2. **Monitor progress**: Watch console output for errors
3. **Use checkpoints**: If script crashes, you can resume from checkpoint files
4. **Rate limiting**: 0.2s between scrolls + 0.3s page load = gentle on EDHREC servers
5. **Combine results**: Merge checkpoint files if you run in batches

## Next Steps

After scraping, you can:

1. **Load into database**:
   ```bash
   python scripts/loaders/load_edhrec_data.py
   ```

2. **Analyze card popularity**:
   ```bash
   python scripts/deck_analyzer.py
   ```

3. **Merge with other data sources**:
   ```bash
   python scripts/data_merger.py
   ```
