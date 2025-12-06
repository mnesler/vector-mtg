# Where Data is Stored - Quick Reference

## Automatic Storage Location

```
/home/maxwell/vector-mtg/data_sources_comprehensive/edhrec_scraped/
```

## File Format

```
{commander-slug}_{timestamp}.json
```

**Example:**
```
atraxa-praetors-voice_20241206_103045.json
```

## After Running Test

```bash
python scripts/test_chromium_scraper.py --strategy=elements
```

**You'll see:**
```
======================================================================
SAVING RESULTS
======================================================================
✓ Data saved to: data_sources_comprehensive/edhrec_scraped/atraxa-praetors-voice_20241206_103045.json
  File size: 45.2 KB
```

## View Your Data

```bash
# List all scraped commanders
ls data_sources_comprehensive/edhrec_scraped/

# View the latest file
cat data_sources_comprehensive/edhrec_scraped/atraxa-*.json | jq '.metadata'

# Count cards
cat data_sources_comprehensive/edhrec_scraped/atraxa-*.json | jq '.cards | length'
```

## JSON Structure

```json
{
  "metadata": {
    "commander_slug": "atraxa-praetors-voice",
    "total_cards": 268,
    "scraped_at": "2024-12-06T10:30:45",
    "elapsed_seconds": 12.3
  },
  "cards": [
    {
      "name": "Doubling Season",
      "url": "https://edhrec.com/cards/doubling-season",
      "synergy": "32%",
      "type": "Enchantment"
    },
    // ... more cards
  ]
}
```

## Summary

✅ **Automatic** - No manual saving needed  
✅ **JSON Format** - Easy to process  
✅ **Timestamped** - Won't overwrite  
✅ **Organized** - One directory for all scraped data  
✅ **Console Output** - Shows exact file path  

The data is saved automatically every time you run the scraper!
