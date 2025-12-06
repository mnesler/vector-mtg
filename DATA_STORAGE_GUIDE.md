# Data Storage Guide - EDHREC Scraper

## Where Data is Stored

### Test Script (Single Commander)

**Script:** `scripts/test_chromium_scraper.py`

**Output Location:**
```
/home/maxwell/vector-mtg/data_sources_comprehensive/edhrec_scraped/
```

**File Format:**
```
{commander-slug}_{timestamp}.json
```

**Example:**
```
data_sources_comprehensive/edhrec_scraped/atraxa-praetors-voice_20241206_103045.json
```

### File Structure

```json
{
  "metadata": {
    "commander_url": "https://edhrec.com/commanders/atraxa-praetors-voice",
    "commander_slug": "atraxa-praetors-voice",
    "strategy_used": "elements",
    "scraped_at": "2024-12-06T10:30:45.123456",
    "elapsed_seconds": 12.3,
    "total_cards": 268,
    "cards_with_synergy": 245,
    "cards_with_type": 180
  },
  "cards": [
    {
      "name": "Doubling Season",
      "url": "https://edhrec.com/cards/doubling-season",
      "synergy": "32%",
      "type": "Enchantment"
    },
    {
      "name": "Winding Constrictor",
      "url": "https://edhrec.com/cards/winding-constrictor",
      "synergy": "28%",
      "type": "Creature"
    }
    // ... 266 more cards
  ]
}
```

## Directory Structure

```
data_sources_comprehensive/
├── edhrec_scraped/           # NEW - Smart scraper output
│   ├── atraxa-praetors-voice_20241206_103045.json
│   ├── edgar-markov_20241206_103100.json
│   └── ...
├── edhrec_full/              # Full scraper (all commanders)
├── edhrec/                   # Old scrapers
├── edhrec_comprehensive/     # Old scrapers
├── moxfield_decks/
├── scryfall/
└── ...
```

## After Running Test Script

```bash
python scripts/test_chromium_scraper.py --strategy=elements
```

**Console Output:**
```
======================================================================
SAVING RESULTS
======================================================================
✓ Data saved to: data_sources_comprehensive/edhrec_scraped/atraxa-praetors-voice_20241206_103045.json
  File size: 45.2 KB

======================================================================
✓ SCRAPING COMPLETED SUCCESSFULLY
======================================================================
```

## Accessing the Data

### 1. View the JSON File

```bash
# Pretty-print the JSON
cat data_sources_comprehensive/edhrec_scraped/atraxa-*.json | jq '.'

# View metadata only
cat data_sources_comprehensive/edhrec_scraped/atraxa-*.json | jq '.metadata'

# Count cards
cat data_sources_comprehensive/edhrec_scraped/atraxa-*.json | jq '.cards | length'

# Get first 5 cards
cat data_sources_comprehensive/edhrec_scraped/atraxa-*.json | jq '.cards[:5]'
```

### 2. Load in Python

```python
import json

# Load the data
with open('data_sources_comprehensive/edhrec_scraped/atraxa-praetors-voice_20241206_103045.json') as f:
    data = json.load(f)

# Access metadata
print(f"Commander: {data['metadata']['commander_slug']}")
print(f"Total cards: {data['metadata']['total_cards']}")
print(f"Scraped: {data['metadata']['scraped_at']}")

# Access cards
for card in data['cards'][:10]:
    print(f"{card['name']} - {card.get('synergy', 'N/A')}")
```

### 3. Merge Multiple Commander Files

```python
import json
from pathlib import Path

# Load all commander files
commanders_data = []
scrape_dir = Path('data_sources_comprehensive/edhrec_scraped')

for json_file in scrape_dir.glob('*.json'):
    with open(json_file) as f:
        commanders_data.append(json.load(f))

print(f"Loaded {len(commanders_data)} commanders")

# Get all unique cards across commanders
all_cards = set()
for commander in commanders_data:
    for card in commander['cards']:
        all_cards.add(card['name'])

print(f"Total unique cards: {len(all_cards)}")
```

## Full Scraper (All Commanders)

For the full scraper that gets all ~1500 commanders, it would use:

**Main output:**
```
data_sources_comprehensive/edhrec_full/edhrec_commanders_{timestamp}.json
```

**Checkpoints (every 10 commanders):**
```
data_sources_comprehensive/edhrec_full/checkpoint_10.json
data_sources_comprehensive/edhrec_full/checkpoint_20.json
...
```

## File Naming Convention

**Pattern:**
```
{commander-slug}_{YYYYMMDD_HHMMSS}.json
```

**Examples:**
- `atraxa-praetors-voice_20241206_103045.json`
- `edgar-markov_20241206_103100.json`
- `ur-dragon_20241206_103115.json`

**Why this format:**
- ✅ Commander name clearly visible
- ✅ Timestamp prevents overwriting
- ✅ Sortable by name or time
- ✅ Easy to find specific commanders

## Data Retention

**Keep:**
- ✅ Latest scrape for each commander
- ✅ Historical scrapes if tracking changes over time

**Clean up:**
```bash
# Find old scrapes (older than 7 days)
find data_sources_comprehensive/edhrec_scraped -name "*.json" -mtime +7

# Delete old scrapes (keep latest only)
# This keeps only the most recent file per commander
cd data_sources_comprehensive/edhrec_scraped
for commander in $(ls *.json | cut -d'_' -f1-4 | sort -u); do
    ls -t ${commander}* | tail -n +2 | xargs rm -f
done
```

## Storage Estimates

**Per Commander:**
- Average file size: 40-60 KB (250-300 cards)
- Large commanders (400+ cards): 80-100 KB
- Small commanders (100 cards): 15-25 KB

**All Commanders (~1500):**
- Total size: ~75-90 MB
- Compressed: ~15-20 MB

## Backup Strategy

```bash
# Backup scraped data
tar -czf edhrec_scraped_backup_$(date +%Y%m%d).tar.gz \
    data_sources_comprehensive/edhrec_scraped/

# Restore from backup
tar -xzf edhrec_scraped_backup_20241206.tar.gz
```

## Integration with Database

To load scraped data into PostgreSQL:

```python
import json
import psycopg2
from pathlib import Path

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    database='vector_mtg',
    user='postgres',
    password='postgres'
)
cursor = conn.cursor()

# Load commander data
scrape_dir = Path('data_sources_comprehensive/edhrec_scraped')

for json_file in scrape_dir.glob('*.json'):
    with open(json_file) as f:
        data = json.load(f)
    
    commander_slug = data['metadata']['commander_slug']
    
    for card in data['cards']:
        # Insert or update card popularity
        cursor.execute("""
            INSERT INTO card_popularity (card_name, commander, synergy, scraped_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (card_name, commander) 
            DO UPDATE SET synergy = EXCLUDED.synergy, scraped_at = EXCLUDED.scraped_at
        """, (
            card['name'],
            commander_slug,
            card.get('synergy'),
            data['metadata']['scraped_at']
        ))

conn.commit()
```

## Viewing Scraped Data

### List All Scraped Commanders

```bash
cd data_sources_comprehensive/edhrec_scraped
ls -lh *.json
```

### Count Cards Per Commander

```bash
for file in data_sources_comprehensive/edhrec_scraped/*.json; do
    count=$(jq '.cards | length' "$file")
    echo "$(basename $file): $count cards"
done
```

### Find Commanders with Most Cards

```bash
for file in data_sources_comprehensive/edhrec_scraped/*.json; do
    count=$(jq '.cards | length' "$file")
    echo "$count $(basename $file)"
done | sort -rn | head -10
```

## Summary

**✅ Data is automatically saved to:**
```
data_sources_comprehensive/edhrec_scraped/{commander-slug}_{timestamp}.json
```

**✅ Each file contains:**
- Metadata (commander, timestamp, stats)
- Complete card list with synergy & type
- JSON format (easy to load/process)

**✅ No manual saving needed** - happens automatically after successful scrape!

**✅ Location displayed in console output:**
```
✓ Data saved to: data_sources_comprehensive/edhrec_scraped/...
```
