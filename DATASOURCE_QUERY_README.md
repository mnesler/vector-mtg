# Data Source Query Manager

A Python utility for querying multiple data sources (APIs, local files) and organizing results in organized folders by data source name.

## Features

- **Multiple Data Sources**: Support for Scryfall API, local JSON files, and extensible architecture for custom sources
- **Organized Output**: Results automatically saved in folders named after the data source (e.g., `data_sources/scryfall/`)
- **Batch Processing**: Query multiple sources in a single run
- **Pagination Support**: Automatically handles paginated API responses
- **Manifest File**: Generates metadata about all queries for tracking and auditing
- **Type-Safe**: Full type hints for IDE support and error checking

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

The script requires:
- `requests` - HTTP client for API queries
- `tqdm` - Progress bars
- `ijson` - JSON streaming (for large files)

## Usage

### Basic Example: Query Scryfall Bulk Data

```python
from scripts.query_datasources import DataSourceManager

manager = DataSourceManager(output_dir="data_sources")
manager.add_scryfall_bulk()
manager.query_all()
manager.print_summary()
manager.save_manifest()
```

Output:
```
data_sources/
└── scryfall/
    ├── scryfall_YYYYMMDD_HHMMSS.json
    └── manifest.json
```

### Custom Scryfall Search

Query for specific cards using Scryfall's search syntax:

```python
manager = DataSourceManager(output_dir="data_sources")

# Add custom searches
manager.add_scryfall_search(query="type:creature color:g")
manager.add_scryfall_search(query="type:instant OR type:sorcery")
manager.add_scryfall_search(query="rarity:rare")

manager.query_all()
manager.print_summary()
```

### Local File Source

Load data from a local JSON file:

```python
manager = DataSourceManager(output_dir="data_sources")
manager.add_local_file("my_rules", "/path/to/rules.json")
manager.add_local_file("card_data", "cards.json")
manager.query_all()
```

### Multiple Sources

Combine multiple sources in one query run:

```python
manager = DataSourceManager(output_dir="data_sources")

# Add Scryfall sources
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

## API Reference

### DataSourceManager

Main class for coordinating queries across multiple data sources.

**Methods:**
- `add_source(source: DataSource)` - Register a data source
- `add_scryfall_bulk()` - Add Scryfall bulk data list
- `add_scryfall_search(query: str)` - Add Scryfall search query
- `add_local_file(source_name: str, filepath: str)` - Add local file source
- `query_all()` - Execute all registered queries
- `print_summary()` - Print results summary
- `save_manifest()` - Save metadata manifest

### ScryfallDataSource

Query the Scryfall Magic: The Gathering API.

**Parameters:**
- `name: str` - Folder name for results
- `query: str` - Scryfall search query (empty for bulk data)
- `bulk: bool` - If True, fetch bulk data list instead of searching

**Example:**
```python
source = ScryfallDataSource(
    output_dir=Path("data_sources"),
    query="type:creature color:g",
    bulk=False
)
result = source.query()
```

### LocalFileDataSource

Load data from a local JSON file.

**Parameters:**
- `source_name: str` - Folder name for results
- `filepath: str` - Path to source JSON file

**Example:**
```python
source = LocalFileDataSource(
    output_dir=Path("data_sources"),
    source_name="my_data",
    filepath="cards.json"
)
result = source.query()
```

## Output Structure

Query results are organized by data source:

```
data_sources/
├── scryfall/
│   ├── scryfall_20250103_142530.json      # Query results
│   ├── scryfall_20250103_150000.json      # Another query
│   └── manifest.json                       # Metadata
├── local_rules/
│   ├── local_rules_20250103_142530.json
│   └── manifest.json
└── manifest.json                           # Global manifest
```

### JSON Output Format

Each query result file contains an array of items or a single object:

```json
[
  {
    "object": "card",
    "id": "...",
    "name": "...",
    ...
  }
]
```

### Manifest Format

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

## Running Examples

The `example_usage.py` script includes several runnable examples:

```bash
# Run basic example (Scryfall bulk data)
python scripts/example_usage.py basic

# Run custom searches example
python scripts/example_usage.py searches

# Run multiple sources example
python scripts/example_usage.py multiple

# Run programmatic access example
python scripts/example_usage.py programmatic
```

## Extending with Custom Sources

Create custom data sources by extending `DataSource`:

```python
from scripts.query_datasources import DataSource
from pathlib import Path

class MyCustomSource(DataSource):
    def __init__(self, output_dir: Path, **kwargs):
        super().__init__("my_source", output_dir)
        # Custom initialization
    
    def query(self) -> Dict[str, Any]:
        """Implement your data fetching logic."""
        try:
            # Fetch data
            self.results = fetch_my_data()
            
            return {
                "success": True,
                "data": self.results,
                "count": len(self.results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Use it
manager = DataSourceManager()
manager.add_source(MyCustomSource(manager.output_dir))
manager.query_all()
```

## Performance Considerations

- **Scryfall Rate Limiting**: The Scryfall API has rate limits. Avoid rapid consecutive requests.
- **Large Files**: Local files are loaded entirely into memory. For files >1GB, consider using streaming loaders.
- **Pagination**: Scryfall searches are automatically paginated. Large searches may take time.

## Error Handling

The script handles errors gracefully:

- API failures are caught and reported in results
- Missing files are reported with clear error messages
- All results include error messages for failed queries
- Manifest tracks success/failure for auditing

## Scryfall Query Syntax

Some example Scryfall queries:

- `type:creature color:g` - Green creatures
- `type:instant OR type:sorcery` - Instant or sorcery spells
- `rarity:rare` - Rare cards
- `set:bro` - Cards from a specific set
- `mana:>{5}` - Cards with mana cost > 5
- `oracle:"{text_pattern}"` - Cards with oracle text containing pattern

See [Scryfall Advanced Search](https://scryfall.com/docs/reference) for full query syntax.

## Troubleshooting

**Import Error**: Ensure you're running from the project root and have installed requirements:
```bash
pip install -r requirements.txt
```

**Scryfall API Errors**: Check your network connection and Scryfall API status.

**Permission Error**: Ensure write permissions for the output directory.

**Memory Issues**: For large datasets, consider streaming loaders or pagination.

