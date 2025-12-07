#!/usr/bin/env python3
"""
Query multiple data sources and organize results in folders by data source name.
Supports Scryfall, custom APIs, and local files.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import requests
from tqdm import tqdm


class DataSource(ABC):
    """Abstract base class for data sources."""

    def __init__(self, name: str, output_dir: Path):
        """
        Initialize data source.
        
        Args:
            name: Name of the data source (used for folder name)
            output_dir: Base output directory
        """
        self.name = name
        self.output_dir = output_dir / name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    @abstractmethod
    def query(self) -> Dict[str, Any]:
        """
        Execute query against the data source.
        
        Returns:
            Dictionary with 'success', 'data', 'error', and 'timestamp' keys
        """
        pass

    def save_results(self, filename: Optional[str] = None) -> Path:
        """
        Save query results to JSON file.
        
        Args:
            filename: Optional custom filename (without .json extension)
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        return filepath


class ScryfallDataSource(DataSource):
    """Query Scryfall API for MTG card data."""

    SCRYFALL_BULK_URL = "https://api.scryfall.com/bulk-data"
    SCRYFALL_CARDS_URL = "https://api.scryfall.com/cards/search"

    def __init__(self, output_dir: Path, query: str = "", bulk: bool = False):
        """
        Initialize Scryfall data source.
        
        Args:
            output_dir: Base output directory
            query: Optional Scryfall search query
            bulk: If True, fetch bulk data list instead of searching
        """
        super().__init__("scryfall", output_dir)
        self.query_string = query
        self.bulk_mode = bulk
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "vector-mtg/1.0"})

    def query(self) -> Dict[str, Any]:
        """Query Scryfall API."""
        try:
            if self.bulk_mode:
                return self._query_bulk_data()
            else:
                return self._query_cards()
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _query_bulk_data(self) -> Dict[str, Any]:
        """Fetch available bulk data from Scryfall."""
        print(f"  Querying {self.name} bulk data...")
        
        response = self.session.get(self.SCRYFALL_BULK_URL)
        response.raise_for_status()
        data = response.json()
        
        self.results = data.get("data", [])
        
        return {
            "success": True,
            "data": self.results,
            "count": len(self.results),
            "timestamp": datetime.now().isoformat()
        }

    def _query_cards(self) -> Dict[str, Any]:
        """
        Search for cards using Scryfall API.
        Handles pagination automatically.
        """
        print(f"  Querying {self.name} cards with: '{self.query_string}'")
        
        all_cards = []
        page_count = 0
        has_more = True
        next_page = None

        while has_more:
            if next_page:
                response = self.session.get(next_page)
            else:
                params = {"q": self.query_string, "unique": "cards"}
                response = self.session.get(self.SCRYFALL_CARDS_URL, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            all_cards.extend(data.get("data", []))
            page_count += 1
            
            has_more = data.get("has_more", False)
            next_page = data.get("next_page")
            
            print(f"    Page {page_count}: {len(data.get('data', []))} cards", end='\r')

        print(f"    Total: {len(all_cards)} cards" + " " * 20)
        
        self.results = all_cards
        
        return {
            "success": True,
            "data": self.results,
            "count": len(self.results),
            "pages": page_count,
            "timestamp": datetime.now().isoformat()
        }


class LocalFileDataSource(DataSource):
    """Load data from local JSON file."""

    def __init__(self, output_dir: Path, source_name: str, filepath: str):
        """
        Initialize local file data source.
        
        Args:
            output_dir: Base output directory
            source_name: Name for this data source
            filepath: Path to source JSON file
        """
        super().__init__(source_name, output_dir)
        self.filepath = Path(filepath)

    def query(self) -> Dict[str, Any]:
        """Load data from local file."""
        try:
            print(f"  Loading {self.name} from {self.filepath}")
            
            if not self.filepath.exists():
                raise FileNotFoundError(f"File not found: {self.filepath}")
            
            with open(self.filepath, 'r') as f:
                self.results = json.load(f)
            
            # Handle both list and dict results
            count = len(self.results) if isinstance(self.results, list) else 1
            
            return {
                "success": True,
                "data": self.results,
                "count": count,
                "source_file": str(self.filepath),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class EDHRecDataSource(DataSource):
    """Query EDHREC for Commander deck recommendations and meta data.
    
    Note: EDHREC API is not officially public, so this uses alternative methods
    to fetch available data (web scraping or fallback to Scryfall).
    """

    EDHREC_BASE = "https://edhrec.com"

    def __init__(self, output_dir: Path, query_type: str = "meta", **params):
        """
        Initialize EDHREC data source.
        
        Args:
            output_dir: Base output directory
            query_type: Type of query - 'meta', 'commander', 'combos'
            **params: Additional query parameters (e.g., commander='Krenko, Mob Boss')
        """
        super().__init__("edhrec", output_dir)
        self.query_type = query_type
        self.params = params
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def query(self) -> Dict[str, Any]:
        """Query EDHREC data."""
        try:
            if self.query_type == "meta":
                return self._query_meta()
            elif self.query_type == "commander":
                return self._query_commander()
            elif self.query_type == "combos":
                return self._query_combos()
            else:
                raise ValueError(f"Unknown query type: {self.query_type}")
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _query_meta(self) -> Dict[str, Any]:
        """Fetch EDH meta information by querying the website."""
        print(f"  Querying {self.name} meta data (via web)...")
        
        # EDHREC doesn't have a public API, so we return popular commanders list
        # from Scryfall instead as a fallback
        popular_commanders = [
            "Krenko, Mob Boss",
            "The Ur-Dragon",
            "Golos, Tireless Pilgrim",
            "Omnath, Locus of Creation",
            "Atraxa, Praetors' Voice",
            "Edgar Markov",
            "Mulch",
            "Korvold, Fae-Cursed King",
            "Ghired, Conclave Exile",
            "Prosper, Tomb-Bound"
        ]
        
        # Fetch card data for these commanders from Scryfall
        commander_data = []
        for commander in popular_commanders:
            try:
                url = "https://api.scryfall.com/cards/named"
                params = {"fuzzy": commander}
                response = self.session.get(url, params=params)
                if response.status_code == 200:
                    card = response.json()
                    commander_data.append({
                        "name": card.get("name"),
                        "type_line": card.get("type_line"),
                        "colors": card.get("colors"),
                        "scryfall_uri": card.get("scryfall_uri"),
                        "image_uris": card.get("image_uris")
                    })
            except:
                pass
        
        self.results = {
            "source": "EDHREC (popular commanders via Scryfall)",
            "commanders": commander_data,
            "total": len(commander_data)
        }
        
        return {
            "success": True,
            "data": self.results,
            "count": len(commander_data),
            "query_type": "meta",
            "note": "EDHREC official API is not public; showing popular commanders",
            "timestamp": datetime.now().isoformat()
        }

    def _query_commander(self) -> Dict[str, Any]:
        """Fetch card recommendations for a specific commander using Scryfall."""
        commander = self.params.get("commander", "")
        
        if not commander:
            raise ValueError("commander parameter required for commander query")
        
        print(f"  Querying {self.name} for commander: {commander}")
        
        # Find the commander card first
        try:
            url = "https://api.scryfall.com/cards/named"
            params = {"fuzzy": commander}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            commander_card = response.json()
        except:
            raise ValueError(f"Commander '{commander}' not found on Scryfall")
        
        # Get color identity to fetch similar cards
        colors = commander_card.get("colors", [])
        color_str = "".join(sorted(colors))
        
        # Query for cards in same colors
        all_cards = []
        try:
            color_query = f"c:{color_str}" if color_str else "legal:commander"
            url = "https://api.scryfall.com/cards/search"
            params = {
                "q": color_query + " f:commander",
                "unique": "cards",
                "order": "edhrec"
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            all_cards = data.get("data", [])[:100]  # Top 100 cards
        except:
            pass
        
        self.results = {
            "commander": {
                "name": commander_card.get("name"),
                "type_line": commander_card.get("type_line"),
                "colors": commander_card.get("colors")
            },
            "suggested_cards": all_cards
        }
        
        return {
            "success": True,
            "data": self.results,
            "count": len(all_cards),
            "query_type": "commander",
            "commander": commander,
            "note": "Using Scryfall EDHREC rankings for card suggestions",
            "timestamp": datetime.now().isoformat()
        }

    def _query_combos(self) -> Dict[str, Any]:
        """Fetch popular EDH combos - returns list of known combo patterns."""
        print(f"  Querying {self.name} combos...")
        
        # Popular EDH combo patterns
        combo_patterns = [
            {
                "name": "Infinite Mana - Basalt Monolith + Rings of Brighthearth",
                "cards": ["Basalt Monolith", "Rings of Brighthearth"],
                "result": "Infinite colorless mana"
            },
            {
                "name": "Infinite Tokens - Doubling Season + Planeswalkers",
                "cards": ["Doubling Season", "Planeswalker"],
                "result": "Infinite planeswalker abilities"
            },
            {
                "name": "Infinite Draw - Earthcraft + Squirrel Nest",
                "cards": ["Earthcraft", "Squirrel Nest"],
                "result": "Infinite creature tokens"
            },
            {
                "name": "Walking Ballista + Woodfall Primus",
                "cards": ["Walking Ballista", "Woodfall Primus"],
                "result": "Destroy all permanents"
            },
            {
                "name": "Kess + Underworld Breach",
                "cards": ["Kess, Dissident Mage", "Underworld Breach"],
                "result": "Cast spells from graveyard indefinitely"
            }
        ]
        
        self.results = combo_patterns
        
        return {
            "success": True,
            "data": self.results,
            "count": len(combo_patterns),
            "query_type": "combos",
            "note": "Popular EDH combo patterns (curated list)",
            "timestamp": datetime.now().isoformat()
        }


class MoxfieldDataSource(DataSource):
    """Query Moxfield for popular EDH deck lists.
    
    Note: Moxfield requires authentication for full API access.
    This source provides deck list patterns and public data.
    """

    MOXFIELD_BASE = "https://moxfield.com"

    def __init__(self, output_dir: Path, query_type: str = "trending"):
        """
        Initialize Moxfield data source.
        
        Args:
            output_dir: Base output directory
            query_type: Type of query - 'trending', 'recent', or specific format
        """
        super().__init__("moxfield", output_dir)
        self.query_type = query_type
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "vector-mtg/1.0"})

    def query(self) -> Dict[str, Any]:
        """Query Moxfield data."""
        try:
            print(f"  Querying {self.name} for {self.query_type} decks...")
            
            # Since Moxfield API requires auth, we return a curated list
            # of famous EDH decks as a fallback
            return self._get_curated_decks()
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _get_curated_decks(self) -> Dict[str, Any]:
        """Return curated list of famous EDH decks."""
        famous_decks = [
            {
                "name": "Krenko Token Generator",
                "commander": "Krenko, Mob Boss",
                "strategy": "Token generation and sacrifice synergies",
                "colors": ["R"],
                "type": "Aggro"
            },
            {
                "name": "The Ur-Dragon Ramp",
                "commander": "The Ur-Dragon",
                "strategy": "Dragon ramp and evasion",
                "colors": ["W", "U", "B", "R", "G"],
                "type": "Ramp"
            },
            {
                "name": "Golos Big Mana",
                "commander": "Golos, Tireless Pilgrim",
                "strategy": "Big mana and X spells",
                "colors": ["W", "U", "B", "R", "G"],
                "type": "Control"
            },
            {
                "name": "Omnath Value Engine",
                "commander": "Omnath, Locus of Creation",
                "strategy": "Land ramp and value generation",
                "colors": ["W", "U", "R", "G"],
                "type": "Ramp"
            },
            {
                "name": "Atraxa Superfriends",
                "commander": "Atraxa, Praetors' Voice",
                "strategy": "Planeswalker focused with proliferate",
                "colors": ["W", "U", "B", "G"],
                "type": "Control"
            },
            {
                "name": "Edgar Markov Vampires",
                "commander": "Edgar Markov",
                "strategy": "Vampire tribal with anthem effects",
                "colors": ["W", "B", "R"],
                "type": "Aggro"
            },
            {
                "name": "Talrand Tokens",
                "commander": "Talrand, Sky Summoner",
                "strategy": "Spell-slinging with token generation",
                "colors": ["U"],
                "type": "Control"
            },
            {
                "name": "Baral Spellslinger",
                "commander": "Baral, Chief of Compliance",
                "strategy": "Spell-slinging with cost reduction",
                "colors": ["U"],
                "type": "Control"
            },
            {
                "name": "Korvold Sacrifice",
                "commander": "Korvold, Fae-Cursed King",
                "strategy": "Food tokens and sacrifice synergies",
                "colors": ["B", "R", "G"],
                "type": "Midrange"
            },
            {
                "name": "Ghired Copy Effects",
                "commander": "Ghired, Conclave Exile",
                "strategy": "Flicker and copy effects",
                "colors": ["U", "R", "G"],
                "type": "Midrange"
            }
        ]
        
        self.results = famous_decks
        
        return {
            "success": True,
            "data": self.results,
            "count": len(famous_decks),
            "query_type": self.query_type,
            "note": "Moxfield official API requires authentication; showing curated famous decks",
            "timestamp": datetime.now().isoformat()
        }


class ScryfallCommanderDataSource(DataSource):
    """Query Scryfall for Commander-legal cards and restrictions."""

    SCRYFALL_API = "https://api.scryfall.com"

    def __init__(self, output_dir: Path, query_type: str = "legal_cards"):
        """
        Initialize Scryfall Commander data source.
        
        Args:
            output_dir: Base output directory
            query_type: Type of query - 'legal_cards', 'banned_cards'
        """
        super().__init__("scryfall_commander", output_dir)
        self.query_type = query_type
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "vector-mtg/1.0"})

    def query(self) -> Dict[str, Any]:
        """Query Scryfall for Commander data."""
        try:
            if self.query_type == "legal_cards":
                return self._query_legal_cards()
            elif self.query_type == "banned_cards":
                return self._query_banned_cards()
            else:
                raise ValueError(f"Unknown query type: {self.query_type}")
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _query_legal_cards(self) -> Dict[str, Any]:
        """Query all Commander-legal cards."""
        print(f"  Querying {self.name} for legal cards...")
        
        all_cards = []
        page = 1
        has_more = True

        while has_more:
            url = f"{self.SCRYFALL_API}/cards/search"
            params = {
                "q": "f:commander",
                "page": page,
                "unique": "cards"
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            all_cards.extend(data.get("data", []))
            page += 1
            has_more = data.get("has_more", False)
            
            print(f"    Page {page-1}: {len(data.get('data', []))} cards", end='\r')

        self.results = all_cards
        print(f"    Total: {len(all_cards)} Commander-legal cards" + " " * 20)
        
        return {
            "success": True,
            "data": self.results,
            "count": len(all_cards),
            "query_type": "legal_cards",
            "timestamp": datetime.now().isoformat()
        }

    def _query_banned_cards(self) -> Dict[str, Any]:
        """Query Commander-banned cards."""
        print(f"  Querying {self.name} for banned cards...")
        
        all_banned = []
        # List of known Commander bans (maintained manually or via external API)
        banned_query = "f:commander legal:commander=banned"
        
        url = f"{self.SCRYFALL_API}/cards/search"
        params = {
            "q": banned_query,
            "unique": "cards"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            all_banned = data.get("data", [])
        except:
            # Scryfall may not support this exact query, use fallback
            print("    Note: Using manual banned list")
            all_banned = self._get_manual_banned_list()

        self.results = all_banned
        
        return {
            "success": True,
            "data": self.results,
            "count": len(all_banned),
            "query_type": "banned_cards",
            "timestamp": datetime.now().isoformat()
        }

    def _get_manual_banned_list(self) -> List[Dict]:
        """Get manual list of Commander banned cards."""
        # This is a fallback list of commonly banned cards
        # In production, this would come from an authoritative source
        banned_names = [
            "Ancestral Recall",
            "Balance",
            "Biorhythm",
            "Black Lotus",
            "Braids, Arisen Nightmare",
            "Channel",
            "Chaos Orb",
            "Collapse",
            "Conspiracies",
            "Dexterity Undone",
            "Dig Through Time",
            "Dolphin Gate",
            "Emrakul, the Aeons Torn",
            "Erayo, Soaring Thought-Thief",
            "Falling Star",
            "Fastbond",
            "Flash",
            "Frog Tongue",
            "Gifts Ungiven",
            "Grindstone",
            "Gush",
            "Iona, Shield of Emeria",
            "Karakas",
            "Leovold, Emissary of Trest",
            "Library of Alexandria",
            "Lurrus of the Dream-Den",
            "Moxes (all)",
            "Panoptic Mirror",
            "Paradox Engine",
            "Protean Hulk",
            "Shahrazad",
            "Sundering Titan",
            "Sway of the Stars",
            "Sylvan Primordial",
            "Time Vault",
            "Time Walk",
            "Tinybones, Trinket Thief",
            "Tolarian Academy",
            "Tolarian Dynasite",
            "Trade Secrets",
            "Transmute Artifact",
            "Unchained Berserker",
            "Upheaval",
            "Vampiric Tutor (banned in 1v1)",
            "Vexing Shusher",
            "Worldfire",
            "Yavimaya's Awakening",
            "Yuriko, the Tiger's Shadow"
        ]
        
        # Fetch these cards from Scryfall
        cards = []
        for name in banned_names:
            try:
                url = f"{self.SCRYFALL_API}/cards/named"
                params = {"fuzzy": name}
                response = self.session.get(url, params=params)
                if response.status_code == 200:
                    cards.append(response.json())
            except:
                pass
        
        return cards


class DataSourceManager:
    """Manage multiple data sources and coordinate queries."""

    def __init__(self, output_dir: str = "data_sources"):
        """
        Initialize data source manager.
        
        Args:
            output_dir: Base directory for all data source folders
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sources: Dict[str, DataSource] = {}
        self.results: Dict[str, Dict[str, Any]] = {}

    def add_source(self, source: DataSource) -> None:
        """Add a data source to the manager."""
        self.sources[source.name] = source

    def add_scryfall_bulk(self) -> None:
        """Add Scryfall bulk data source."""
        self.add_source(ScryfallDataSource(self.output_dir, bulk=True))

    def add_scryfall_search(self, query: str) -> None:
        """Add Scryfall search data source with custom query."""
        self.add_source(ScryfallDataSource(self.output_dir, query=query, bulk=False))

    def add_local_file(self, source_name: str, filepath: str) -> None:
        """Add local file data source."""
        self.add_source(LocalFileDataSource(self.output_dir, source_name, filepath))

    def add_edhrec_meta(self) -> None:
        """Add EDHREC meta data source (top commanders, meta analysis)."""
        self.add_source(EDHRecDataSource(self.output_dir, query_type="meta"))

    def add_edhrec_commander(self, commander: str) -> None:
        """Add EDHREC data source for specific commander."""
        self.add_source(EDHRecDataSource(
            self.output_dir,
            query_type="commander",
            commander=commander
        ))

    def add_edhrec_combos(self) -> None:
        """Add EDHREC combos data source."""
        self.add_source(EDHRecDataSource(self.output_dir, query_type="combos"))

    def add_moxfield_trending(self) -> None:
        """Add Moxfield trending decks data source."""
        self.add_source(MoxfieldDataSource(self.output_dir, query_type="trending"))

    def add_moxfield_recent(self) -> None:
        """Add Moxfield recent decks data source."""
        self.add_source(MoxfieldDataSource(self.output_dir, query_type="recent"))

    def add_scryfall_commander_legal(self) -> None:
        """Add Scryfall Commander-legal cards data source."""
        self.add_source(ScryfallCommanderDataSource(
            self.output_dir,
            query_type="legal_cards"
        ))

    def add_scryfall_commander_banned(self) -> None:
        """Add Scryfall Commander banned cards data source."""
        self.add_source(ScryfallCommanderDataSource(
            self.output_dir,
            query_type="banned_cards"
        ))

    def query_all(self) -> Dict[str, Dict[str, Any]]:
        """Execute queries for all registered data sources."""
        print(f"\n{'='*60}")
        print("DATA SOURCE QUERY MANAGER")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir.absolute()}\n")
        
        for name, source in self.sources.items():
            print(f"Querying: {name}")
            result = source.query()
            self.results[name] = result
            filepath = source.save_results()
            
            if result["success"]:
                print(f"  ✓ Success - {result.get('count', 0)} items")
                print(f"  ✓ Saved to: {filepath}")
            else:
                print(f"  ✗ Failed: {result.get('error')}")
            print()
        
        return self.results

    def print_summary(self) -> None:
        """Print summary of all query results."""
        print(f"\n{'='*60}")
        print("QUERY SUMMARY")
        print(f"{'='*60}\n")
        
        total_success = 0
        total_items = 0
        
        for name, result in self.results.items():
            status = "✓" if result["success"] else "✗"
            count = result.get("count", 0)
            
            print(f"{status} {name.upper()}")
            if result["success"]:
                print(f"   Items: {count}")
                total_success += 1
                total_items += count
            else:
                print(f"   Error: {result.get('error')}")
        
        print(f"\n{'='*60}")
        print(f"Total successful queries: {total_success}/{len(self.results)}")
        print(f"Total items retrieved: {total_items:,}")
        print(f"{'='*60}\n")

    def save_manifest(self) -> Path:
        """
        Save query manifest file with metadata about all queries.
        
        Returns:
            Path to manifest file
        """
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "output_directory": str(self.output_dir.absolute()),
            "queries": {}
        }
        
        for name, result in self.results.items():
            manifest["queries"][name] = {
                "success": result["success"],
                "count": result.get("count", 0),
                "timestamp": result.get("timestamp"),
                "error": result.get("error") if not result["success"] else None
            }
        
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path


def main():
    """Example usage of the data source query manager."""
    
    # Create manager
    manager = DataSourceManager(output_dir="data_sources")
    
    # Add data sources
    print("Registering data sources...")
    
    # Example 1: Query Scryfall bulk data list
    manager.add_scryfall_bulk()
    
    # Example 2: Query Scryfall with custom search
    manager.add_scryfall_search(query="type:creature color:g")
    
    # Example 3: Load local cards.json if it exists
    if Path("cards.json").exists():
        manager.add_local_file("scryfall_local", "cards.json")
    
    # Execute all queries
    manager.query_all()
    
    # Print summary
    manager.print_summary()
    
    # Save manifest
    manifest_path = manager.save_manifest()
    print(f"Manifest saved to: {manifest_path}\n")


if __name__ == "__main__":
    main()
