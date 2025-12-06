# EDH/Commander Data Sources - Complete Guide

## Overview

This guide explains how to query all major EDH/Commander data sources and organize results by source.

## Available Data Sources

### 1. EDHREC (Commander Recommendations)
**Folder:** `data_sources/edhrec/`

Query popular commanders, deck recommendations, and combos.

```python
manager = DataSourceManager()

# Top commanders and meta analysis
manager.add_edhrec_meta()

# Specific commander recommendations
manager.add_edhrec_commander("Krenko, Mob Boss")
manager.add_edhrec_commander("The Ur-Dragon")

# Popular combos
manager.add_edhrec_combos()

manager.query_all()
```

**Output Files:**
- `edhrec_YYYYMMDD_HHMMSS.json` - Query results

### 2. Moxfield (Deck Lists)
**Folder:** `data_sources/moxfield/`

Get trending and recent EDH deck lists.

```python
manager = DataSourceManager()

# Trending decks
manager.add_moxfield_trending()

# Recent decks
manager.add_moxfield_recent()

manager.query_all()
```

**Output Files:**
- `moxfield_YYYYMMDD_HHMMSS.json` - Deck list data

### 3. Scryfall Commander Data
**Folder:** `data_sources/scryfall_commander/`

Query Commander-legal cards and banned list.

```python
manager = DataSourceManager()

# All Commander-legal cards
manager.add_scryfall_commander_legal()

# Commander banned cards
manager.add_scryfall_commander_banned()

manager.query_all()
```

**Output Files:**
- `scryfall_commander_YYYYMMDD_HHMMSS.json` - Commander data

## Quick Start

### Run a Single EDH Source

```bash
source venv/bin/activate
python demo_datasources.py edh-meta
```

### Run Specific Commands

```bash
# EDHREC meta (top commanders)
python demo_datasources.py edh-meta

# Specific commander recommendations
python demo_datasources.py edh-commander

# Popular combos
python demo_datasources.py edh-combos

# Moxfield trending decks
python demo_datasources.py moxfield

# Commander legality data
python demo_datasources.py legality

# All EDH sources at once
python demo_datasources.py all
```

## Detailed Usage Examples

### Example 1: Query EDHREC Meta

Get the top commanders and meta breakdown:

```python
from scripts.query_datasources import DataSourceManager

manager = DataSourceManager(output_dir="data_sources")
manager.add_edhrec_meta()
manager.query_all()
manager.print_summary()
```

Creates: `data_sources/edhrec/edhrec_20250103_142530.json`

### Example 2: Multiple Commanders

Get recommendations for several commanders:

```python
manager = DataSourceManager(output_dir="data_sources")

# Green commanders
manager.add_edhrec_commander("Omnath, Locus of Creation")
manager.add_edhrec_commander("Elvish Archdruid")

# Red commanders
manager.add_edhrec_commander("Krenko, Mob Boss")
manager.add_edhrec_commander("Feldon of the Third Path")

# Blue commanders
manager.add_edhrec_commander("Baral, Chief of Compliance")
manager.add_edhrec_commander("Talrand, Sky Summoner")

manager.query_all()
manager.print_summary()
```

Creates separate files for each commander in `data_sources/edhrec/`

### Example 3: Meta Analysis + Combos

Get meta data and combos in one run:

```python
manager = DataSourceManager(output_dir="data_sources")

manager.add_edhrec_meta()
manager.add_edhrec_combos()
manager.add_moxfield_trending()

manager.query_all()
manager.print_summary()
manager.save_manifest()
```

Creates:
- `data_sources/edhrec/edhrec_*.json` - Meta and combos
- `data_sources/moxfield/moxfield_*.json` - Trending decks
- `data_sources/manifest.json` - Metadata

### Example 4: Complete EDH Analysis

Query all sources for comprehensive EDH data:

```python
manager = DataSourceManager(output_dir="data_sources")

# EDHREC sources
manager.add_edhrec_meta()
manager.add_edhrec_combos()

# Top commanders
popular_commanders = [
    "Krenko, Mob Boss",
    "The Ur-Dragon",
    "Golos, Tireless Pilgrim",
    "Omnath, Locus of Creation",
    "Atraxa, Praetors' Voice"
]

for commander in popular_commanders:
    manager.add_edhrec_commander(commander)

# Deck lists
manager.add_moxfield_trending()
manager.add_moxfield_recent()

# Legality data
manager.add_scryfall_commander_legal()
manager.add_scryfall_commander_banned()

manager.query_all()
manager.print_summary()
manager.save_manifest()
```

Creates comprehensive folder structure:
```
data_sources/
├── edhrec/
│   ├── edhrec_*.json (meta, combos, individual commanders)
│   └── manifest.json
├── moxfield/
│   ├── moxfield_*.json (trending, recent decks)
│   └── manifest.json
├── scryfall_commander/
│   ├── scryfall_commander_*.json (legal/banned)
│   └── manifest.json
└── manifest.json (global)
```

## Output Data Format

### EDHREC Meta
```json
{
  "commanders": [
    {
      "name": "Krenko, Mob Boss",
      "rank": 1,
      "uses": 12345,
      "synergies": [...]
    }
  ]
}
```

### EDHREC Commander
```json
{
  "cards": [
    {
      "name": "Goblin Recruiter",
      "inclusions": 8765,
      "synergy": 2.45
    }
  ],
  "creatures": [...],
  "instants": [...],
  "sorceries": [...]
}
```

### EDHREC Combos
```json
[
  {
    "id": "combo_1",
    "uses": 5432,
    "cards": ["Card 1", "Card 2", "Card 3"],
    "result": "Effect description"
  }
]
```

### Moxfield Decks
```json
[
  {
    "id": "deck_id",
    "name": "Deck Name",
    "commander": ["Commander Name"],
    "format": "Commander",
    "created": "2025-01-03T...",
    "cards": {...}
  }
]
```

### Scryfall Commander Data
```json
[
  {
    "object": "card",
    "id": "...",
    "name": "Card Name",
    "legalities": {
      "commander": "legal"
    }
  }
]
```

## Manifest File Format

Each query run creates a manifest tracking results:

```json
{
  "timestamp": "2025-01-03T14:25:30.123456",
  "output_directory": "/home/maxwell/vector-mtg/data_sources",
  "queries": {
    "edhrec": {
      "success": true,
      "count": 50,
      "timestamp": "2025-01-03T14:25:30.123456",
      "error": null
    },
    "moxfield": {
      "success": true,
      "count": 50,
      "timestamp": "2025-01-03T14:25:30.123456",
      "error": null
    }
  }
}
```

## API Reference

### Manager Methods

```python
# EDHREC
manager.add_edhrec_meta()                          # Top commanders
manager.add_edhrec_commander(name)                 # Specific commander
manager.add_edhrec_combos()                        # Popular combos

# Moxfield
manager.add_moxfield_trending()                    # Trending decks
manager.add_moxfield_recent()                      # Recent decks

# Scryfall Commander
manager.add_scryfall_commander_legal()             # Legal cards
manager.add_scryfall_commander_banned()            # Banned cards

# Execute
manager.query_all()                                # Run all queries
manager.print_summary()                            # Show results
manager.save_manifest()                            # Save metadata
```

## Performance Notes

- **EDHREC:** Fast responses (< 1s per query)
- **Moxfield:** Moderate (1-2s per query)
- **Scryfall:** Slower for large result sets (Commander-legal query may return 10k+ cards)

For large queries, results are paginated automatically.

## Troubleshooting

### API Rate Limiting
EDHREC and Moxfield have rate limits. If you get errors:
- Wait a minute before retrying
- Batch queries in a single run instead of multiple runs

### Network Timeouts
For Scryfall Commander-legal query (returns 10k+ cards):
- May take 30-60 seconds
- Results will be saved even if slow

### Missing Data
Some APIs may return empty results:
- Check API status online
- Verify commander names are spelled correctly
- Try alternative spellings (e.g., "Krenko, Mob Boss" vs "Krenko Mob Boss")

## Extending with More Sources

Add your own EDH data source:

```python
from scripts.query_datasources import DataSource

class MyEDHSource(DataSource):
    def __init__(self, output_dir: Path):
        super().__init__("my_edh_source", output_dir)
    
    def query(self) -> Dict[str, Any]:
        # Fetch your EDH data
        self.results = fetch_data()
        
        return {
            "success": True,
            "data": self.results,
            "count": len(self.results),
            "timestamp": datetime.now().isoformat()
        }

# Use it
manager = DataSourceManager()
manager.add_source(MyEDHSource(manager.output_dir))
manager.query_all()
```

## Real-World Use Cases

### Deck Building Assistant
```python
manager = DataSourceManager()
manager.add_edhrec_commander("Your Commander")
manager.add_moxfield_trending()
manager.query_all()
# Results show popular cards + decks for reference
```

### Meta Analysis
```python
manager = DataSourceManager()
manager.add_edhrec_meta()
manager.add_edhrec_combos()
manager.query_all()
# Results show top commanders and popular combos
```

### Legality Compliance
```python
manager = DataSourceManager()
manager.add_scryfall_commander_legal()
manager.add_scryfall_commander_banned()
manager.query_all()
# Results show all legal/banned cards
```

### Combo Research
```python
manager = DataSourceManager()
manager.add_edhrec_combos()
manager.query_all()
# Results show popular 2-3 card combos in EDH
```

