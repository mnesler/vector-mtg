# Quick Start Guide: Data Source Query Manager

## Overview

The Data Source Query Manager allows you to:
- Query multiple data sources (Scryfall API, local files, etc.)
- Organize results in folders by data source name
- Generate metadata manifests for tracking
- Extend with custom data sources

## Installation

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

The key dependency is `requests` (already installed in venv).

## Quickest Start: 30 Seconds

Run a demo:
```bash
source venv/bin/activate
python demo_datasources.py bulk
```

This queries Scryfall's bulk data list and saves results to `data_sources/scryfall/`.

## Output Folder Structure

Results are automatically organized by source:
```
data_sources/
├── scryfall/
│   ├── scryfall_20250103_142530.json
│   └── manifest.json
├── my_rules/
│   ├── my_rules_20250103_142530.json
│   └── manifest.json
└── manifest.json
```

## Usage Examples

### Example 1: Query Scryfall Bulk Data
```python
from scripts.query_datasources import DataSourceManager

manager = DataSourceManager(output_dir="data_sources")
manager.add_scryfall_bulk()
manager.query_all()
manager.print_summary()
```

### Example 2: Search for Specific Cards
```python
from scripts.query_datasources import DataSourceManager

manager = DataSourceManager(output_dir="data_sources")

# Search for creatures
manager.add_scryfall_search(query="type:creature color:g")

# Search for spells
manager.add_scryfall_search(query="type:instant OR type:sorcery")

# Search for expensive cards
manager.add_scryfall_search(query="mana:>{8}")

manager.query_all()
manager.print_summary()
manager.save_manifest()
```

### Example 3: Load Local Data
```python
from scripts.query_datasources import DataSourceManager

manager = DataSourceManager(output_dir="data_sources")

# Load from local JSON file
if Path("cards.json").exists():
    manager.add_local_file("scryfall_all", "cards.json")

manager.query_all()
manager.print_summary()
```

### Example 4: Combine Multiple Sources
```python
from scripts.query_datasources import DataSourceManager
from pathlib import Path

manager = DataSourceManager(output_dir="data_sources")

# Add API sources
manager.add_scryfall_bulk()
manager.add_scryfall_search(query="rarity:rare")

# Add local sources
if Path("cards.json").exists():
    manager.add_local_file("scryfall_full", "cards.json")

# Execute all at once
manager.query_all()
manager.print_summary()
manager.save_manifest()
```

## API Reference: Quick Lookup

### Create Manager
```python
manager = DataSourceManager(output_dir="data_sources")
```

### Add Data Sources
```python
# Scryfall bulk data list
manager.add_scryfall_bulk()

# Scryfall search
manager.add_scryfall_search(query="type:creature")

# Local JSON file
manager.add_local_file("my_source", "path/to/file.json")
```

### Execute Queries
```python
# Run all queries
results = manager.query_all()

# Print summary
manager.print_summary()

# Save metadata
manager.save_manifest()
```

## Running Demo Scripts

```bash
# Query Scryfall bulk data
python demo_datasources.py bulk

# Query with custom searches
python demo_datasources.py search

# Load from local files
python demo_datasources.py local

# Run all demos
python demo_datasources.py all
```

## Understanding the Output

### Results File
Each query creates a JSON file with results:
```json
[
  {
    "object": "card",
    "id": "abc123",
    "name": "Card Name",
    ...
  }
]
```

### Manifest File
Metadata about the query:
```json
{
  "timestamp": "2025-01-03T14:25:30.123456",
  "output_directory": "/home/maxwell/vector-mtg/data_sources",
  "queries": {
    "scryfall": {
      "success": true,
      "count": 2500,
      "timestamp": "2025-01-03T14:25:30.123456",
      "error": null
    }
  }
}
```

## Scryfall Search Examples

```python
# Creatures
manager.add_scryfall_search(query="type:creature")

# Green spells
manager.add_scryfall_search(query="(type:instant OR type:sorcery) color:g")

# Rare cards
manager.add_scryfall_search(query="rarity:rare")

# Specific set
manager.add_scryfall_search(query="set:bro")

# Mana cost > 5
manager.add_scryfall_search(query="mana:>{5}")

# Cards with specific text
manager.add_scryfall_search(query='oracle:"draw a card"')

# Legendary creatures
manager.add_scryfall_search(query="type:creature type:legendary")

# Modern legal
manager.add_scryfall_search(query="f:modern")
```

See full syntax: https://scryfall.com/docs/reference

## Troubleshooting

### ImportError
```bash
# Make sure you're in the venv
source venv/bin/activate

# Run from project root
cd /home/maxwell/vector-mtg
```

### Network Errors
- Check internet connection
- Check Scryfall API status
- Wait and retry (rate limits)

### File Not Found
- Ensure output directory is writable
- Check file paths are absolute or relative from project root

### Memory Issues with Large Files
- Use streaming loaders for files > 1GB
- Process in batches instead of all at once

## Next Steps

1. **Run the quickstart**: `python demo_datasources.py bulk`
2. **Try custom searches**: Modify `demo_datasources.py` with your own queries
3. **Integrate into your workflow**: Use `DataSourceManager` in your own scripts
4. **Extend with custom sources**: Create custom data source classes

## Full Documentation

See `DATASOURCE_QUERY_README.md` for complete API reference and advanced usage.

