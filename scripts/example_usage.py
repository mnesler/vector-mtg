#!/usr/bin/env python3
"""
Example usage of the data source query script.
Demonstrates different ways to query and organize data by source.
Run from the scripts/ directory:
  python example_usage.py basic
  python example_usage.py searches
  python example_usage.py multiple
  python example_usage.py programmatic
"""

from pathlib import Path
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

from query_datasources import (
    DataSourceManager,
    ScryfallDataSource,
    LocalFileDataSource
)


def example_basic_usage():
    """Basic example: Query Scryfall bulk data and save results."""
    manager = DataSourceManager(output_dir="data_sources")
    
    # Query available Scryfall bulk data
    manager.add_scryfall_bulk()
    
    # Execute queries and display results
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def example_custom_searches():
    """Example: Query Scryfall with multiple custom searches."""
    manager = DataSourceManager(output_dir="data_sources")
    
    # Add multiple search queries
    searches = [
        ("green_creatures", "type:creature color:g"),
        ("blue_spells", "type:instant OR type:sorcery color:u"),
        ("artifacts", "type:artifact"),
        ("planeswalkers", "type:planeswalker"),
    ]
    
    for source_name, query in searches:
        # Custom source with specific name
        source = ScryfallDataSource(
            manager.output_dir,
            query=query,
            bulk=False
        )
        source.name = f"scryfall_{source_name}"
        manager.add_source(source)
    
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def example_multiple_sources():
    """Example: Combine multiple data sources (local + API)."""
    manager = DataSourceManager(output_dir="data_sources")
    
    # Add Scryfall bulk data
    manager.add_scryfall_bulk()
    
    # Add Scryfall search
    manager.add_scryfall_search(query="rarity:rare")
    
    # Add local file if it exists
    if Path("cards.json").exists():
        manager.add_local_file("scryfall_full", "cards.json")
    
    # Add other local data sources
    if Path("sql/seeds/seed_rules.sql").exists():
        # Note: This would need a custom loader for SQL files
        pass
    
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def example_programmatic_access():
    """Example: Access query results programmatically."""
    manager = DataSourceManager(output_dir="data_sources")
    
    manager.add_scryfall_bulk()
    results = manager.query_all()
    
    # Access results for scryfall source
    scryfall_result = results["scryfall"]
    
    if scryfall_result["success"]:
        # Results are in the source object
        source = manager.sources["scryfall"]
        print(f"\nScryfall has {len(source.results)} bulk datasets available:")
        for dataset in source.results:
            print(f"  - {dataset['name']}: {dataset['description']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        if example == "basic":
            example_basic_usage()
        elif example == "searches":
            example_custom_searches()
        elif example == "multiple":
            example_multiple_sources()
        elif example == "programmatic":
            example_programmatic_access()
        else:
            print(f"Unknown example: {example}")
            print("Available examples: basic, searches, multiple, programmatic")
    else:
        # Run basic example by default
        print("Running basic example...\n")
        example_basic_usage()
