#!/usr/bin/env python3
"""
Quick start demo for data source query manager.
Shows the simplest way to get started with all available data sources.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from query_datasources import DataSourceManager


def demo_scryfall_bulk():
    """Demo 1: Query Scryfall bulk data list."""
    print("=" * 70)
    print("DEMO 1: Query Scryfall Bulk Data Available")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    manager.add_scryfall_bulk()
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def demo_edh_meta():
    """Demo 2: Query EDHREC meta data."""
    print("\n" + "=" * 70)
    print("DEMO 2: Query EDHREC Meta Data (Top Commanders)")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    manager.add_edhrec_meta()
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def demo_edh_commander():
    """Demo 3: Query EDHREC for specific commander."""
    print("\n" + "=" * 70)
    print("DEMO 3: Query EDHREC for Specific Commander")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    
    # Add a few popular commanders
    manager.add_edhrec_commander("Krenko, Mob Boss")
    manager.add_edhrec_commander("The Ur-Dragon")
    manager.add_edhrec_commander("Golos, Tireless Pilgrim")
    
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def demo_edh_combos():
    """Demo 4: Query EDHREC combos."""
    print("\n" + "=" * 70)
    print("DEMO 4: Query EDHREC Popular Combos")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    manager.add_edhrec_combos()
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def demo_moxfield_decks():
    """Demo 5: Query Moxfield trending decks."""
    print("\n" + "=" * 70)
    print("DEMO 5: Query Moxfield Trending Decks")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    manager.add_moxfield_trending()
    manager.add_moxfield_recent()
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def demo_commander_legality():
    """Demo 6: Query Scryfall Commander legality data."""
    print("\n" + "=" * 70)
    print("DEMO 6: Query Scryfall Commander-Legal Cards & Bans")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    manager.add_scryfall_commander_legal()
    manager.add_scryfall_commander_banned()
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


def demo_all_edh():
    """Demo 7: Query all EDH data sources."""
    print("\n" + "=" * 70)
    print("DEMO 7: Query ALL EDH Data Sources")
    print("=" * 70)
    
    manager = DataSourceManager(output_dir="data_sources")
    
    # EDHREC sources
    print("\nAdding EDHREC sources...")
    manager.add_edhrec_meta()
    manager.add_edhrec_combos()
    
    # Popular commanders
    print("Adding specific commanders...")
    manager.add_edhrec_commander("Krenko, Mob Boss")
    manager.add_edhrec_commander("The Ur-Dragon")
    
    # Moxfield
    print("Adding Moxfield sources...")
    manager.add_moxfield_trending()
    
    # Scryfall Commander data
    print("Adding Scryfall Commander sources...")
    manager.add_scryfall_commander_banned()
    
    manager.query_all()
    manager.print_summary()
    manager.save_manifest()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Data Source Query Manager Demo - EDH/Commander Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_datasources.py bulk            # Scryfall bulk data
  python demo_datasources.py edh-meta        # EDHREC top commanders
  python demo_datasources.py edh-commander   # Specific commanders
  python demo_datasources.py edh-combos      # Popular combos
  python demo_datasources.py moxfield        # Trending decks
  python demo_datasources.py legality        # Commander legality
  python demo_datasources.py all             # All sources
        """
    )
    parser.add_argument(
        "demo",
        nargs="?",
        choices=["bulk", "edh-meta", "edh-commander", "edh-combos", 
                 "moxfield", "legality", "all"],
        default="bulk",
        help="Which demo to run (default: bulk)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.demo == "bulk":
            demo_scryfall_bulk()
        elif args.demo == "edh-meta":
            demo_edh_meta()
        elif args.demo == "edh-commander":
            demo_edh_commander()
        elif args.demo == "edh-combos":
            demo_edh_combos()
        elif args.demo == "moxfield":
            demo_moxfield_decks()
        elif args.demo == "legality":
            demo_commander_legality()
        elif args.demo == "all":
            demo_all_edh()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
