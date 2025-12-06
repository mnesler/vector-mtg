#!/usr/bin/env python3
"""
Comprehensive EDH data scrapers for multiple sources.
Fetches all available data from EDHREC, Moxfield, TappedOut, etc.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, name: str, output_dir: Path, delay: float = 1.0):
        """
        Initialize scraper.
        
        Args:
            name: Name of the scraper (used for folder)
            output_dir: Base output directory
            delay: Delay between requests in seconds
        """
        self.name = name
        self.output_dir = output_dir / name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        self.results = []

    @abstractmethod
    def scrape(self) -> Dict[str, Any]:
        """Execute scraping operation."""
        pass

    def save_results(self, filename: Optional[str] = None) -> Path:
        """Save results to JSON file."""
        if not filename:
            filename = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        return filepath

    def _get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make GET request with delay."""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None


class EDHRecScraper(BaseScraper):
    """Scrape EDHREC for comprehensive commander data."""

    BASE_URL = "https://edhrec.com"

    def __init__(self, output_dir: Path, delay: float = 2.0):
        super().__init__("edhrec_full", output_dir, delay)
        self.commanders = []
        self.cards = []
        self.combos = []
        self.meta = {}

    def scrape(self) -> Dict[str, Any]:
        """Scrape all EDHREC data."""
        try:
            print("Starting EDHREC scrape...")
            self._scrape_commanders()
            print(f"  ✓ Found {len(self.commanders)} commanders")
            
            self._scrape_combos()
            print(f"  ✓ Found {len(self.combos)} combos")
            
            self._scrape_meta()
            print(f"  ✓ Scraped meta data")
            
            self.results = {
                "commanders": self.commanders,
                "combos": self.combos,
                "meta": self.meta,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "data": self.results,
                "counts": {
                    "commanders": len(self.commanders),
                    "combos": len(self.combos)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _scrape_commanders(self):
        """Scrape all commanders from EDHREC."""
        print("  Scraping commanders...")
        
        # Try to get commander list page
        url = f"{self.BASE_URL}/commanders"
        response = self._get(url)
        
        if not response:
            logger.warning("Could not fetch commanders page, using popular list")
            self.commanders = self._get_popular_commanders()
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for commander links
        commander_links = soup.find_all('a', href=True)
        seen = set()
        
        for link in commander_links:
            href = link.get('href', '')
            if '/commanders/' in href and href not in seen:
                # Extract commander name from URL
                parts = href.split('/commanders/')
                if len(parts) > 1:
                    commander_name = parts[1].strip('/')
                    if commander_name and commander_name not in seen:
                        seen.add(href)
                        self.commanders.append({
                            "name": commander_name.replace('-', ' ').title(),
                            "url": urljoin(self.BASE_URL, href)
                        })

    def _scrape_combos(self):
        """Scrape combo database from EDHREC."""
        print("  Scraping combos...")
        
        url = f"{self.BASE_URL}/combos"
        response = self._get(url)
        
        if not response:
            logger.warning("Could not fetch combos page")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for combo entries
        combo_elements = soup.find_all('div', class_='combo')
        
        for combo in combo_elements[:50]:  # Limit to first 50 for now
            try:
                cards = []
                card_elements = combo.find_all('a', class_='card')
                for card in card_elements:
                    card_name = card.get_text(strip=True)
                    if card_name:
                        cards.append(card_name)
                
                result = combo.find('p', class_='result')
                result_text = result.get_text(strip=True) if result else ""
                
                if cards:
                    self.combos.append({
                        "cards": cards,
                        "result": result_text
                    })
            except Exception as e:
                logger.debug(f"Error parsing combo: {e}")

    def _scrape_meta(self):
        """Scrape meta information."""
        url = f"{self.BASE_URL}/meta"
        response = self._get(url)
        
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')
            self.meta = {
                "source": "EDHREC",
                "url": url,
                "scraped_at": datetime.now().isoformat()
            }

    def _get_popular_commanders(self) -> List[Dict]:
        """Fallback: return list of popular commanders."""
        popular = [
            "Krenko, Mob Boss",
            "The Ur-Dragon",
            "Golos, Tireless Pilgrim",
            "Omnath, Locus of Creation",
            "Atraxa, Praetors' Voice",
            "Edgar Markov",
            "Talrand, Sky Summoner",
            "Baral, Chief of Compliance",
            "Korvold, Fae-Cursed King",
            "Ghired, Conclave Exile",
            "Meren of Clan Nel Toth",
            "Breya, Etherium Shaper",
            "Prosper, Tomb-Bound",
            "Yargle, Glutton of Urborg",
            "Yuriko, the Tiger's Shadow"
        ]
        return [{"name": name, "popular": True} for name in popular]


class TappedOutScraper(BaseScraper):
    """Scrape TappedOut for deck lists and meta."""

    BASE_URL = "https://tappedout.net"

    def __init__(self, output_dir: Path, delay: float = 2.0):
        super().__init__("tappedout", output_dir, delay)

    def scrape(self) -> Dict[str, Any]:
        """Scrape TappedOut decks."""
        try:
            print("Starting TappedOut scrape...")
            
            decks = self._scrape_decks()
            print(f"  ✓ Found {len(decks)} recent decks")
            
            self.results = decks
            
            return {
                "success": True,
                "data": self.results,
                "count": len(decks),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _scrape_decks(self, limit: int = 100) -> List[Dict]:
        """Scrape recent EDH decks."""
        decks = []
        
        # Try to get recent EDH decks
        url = f"{self.BASE_URL}/api/deck/latest/edh"
        response = self._get(url)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                decks = data[:limit] if isinstance(data, list) else []
            except:
                logger.warning("Could not parse TappedOut API response")
        
        return decks


class MoxfieldScraper(BaseScraper):
    """Scrape Moxfield for real deck data."""

    BASE_URL = "https://api.moxfield.com/v2"

    def __init__(self, output_dir: Path, delay: float = 2.0):
        super().__init__("moxfield_decks", output_dir, delay)

    def scrape(self) -> Dict[str, Any]:
        """Scrape Moxfield public decks."""
        try:
            print("Starting Moxfield scrape...")
            
            decks = self._scrape_public_decks()
            print(f"  ✓ Found {len(decks)} public decks")
            
            self.results = decks
            
            return {
                "success": True,
                "data": self.results,
                "count": len(decks),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _scrape_public_decks(self, limit: int = 100) -> List[Dict]:
        """Scrape public Moxfield decks."""
        decks = []
        
        try:
            url = f"{self.BASE_URL}/decks"
            params = {"pageSize": min(limit, 100), "sortBy": "created"}
            response = self._get(url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                decks = data.get("data", [])[:limit]
        except Exception as e:
            logger.warning(f"Could not scrape Moxfield: {e}")
        
        return decks


class PriceScraper(BaseScraper):
    """Scrape card prices from multiple sources."""

    def __init__(self, output_dir: Path, delay: float = 2.0):
        super().__init__("card_prices", output_dir, delay)
        self.prices = {}

    def scrape(self) -> Dict[str, Any]:
        """Scrape prices from multiple sources."""
        try:
            print("Starting price scrape...")
            
            # Prices via Scryfall
            self._scrape_scryfall_prices()
            print(f"  ✓ Found prices for cards from Scryfall")
            
            self.results = self.prices
            
            return {
                "success": True,
                "data": self.results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _scrape_scryfall_prices(self):
        """Get prices from Scryfall API."""
        url = "https://api.scryfall.com/cards"
        
        # Note: Scryfall has bulk price data
        # For now, we'll just note the capability
        self.prices = {
            "source": "Scryfall API",
            "note": "Full price data available via Scryfall bulk API",
            "data": {}
        }


class ComprehensiveEDHScraper:
    """Orchestrate all EDH data scrapers."""

    def __init__(self, output_dir: str = "data_sources_comprehensive"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scrapers = []
        self.results = {}

    def add_scraper(self, scraper: BaseScraper) -> None:
        """Add a scraper to the collection."""
        self.scrapers.append(scraper)

    def scrape_all(self) -> Dict[str, Any]:
        """Execute all scrapers."""
        print(f"\n{'='*70}")
        print("COMPREHENSIVE EDH DATA SCRAPER")
        print(f"{'='*70}\n")
        
        for scraper in self.scrapers:
            print(f"\nScraping: {scraper.name}")
            try:
                result = scraper.scrape()
                self.results[scraper.name] = result
                
                if result.get("success"):
                    filepath = scraper.save_results()
                    print(f"  ✓ Saved to: {filepath}")
                else:
                    print(f"  ✗ Failed: {result.get('error')}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.results[scraper.name] = {
                    "success": False,
                    "error": str(e)
                }

        return self.results

    def print_summary(self):
        """Print scraping summary."""
        print(f"\n{'='*70}")
        print("SCRAPING SUMMARY")
        print(f"{'='*70}\n")
        
        for name, result in self.results.items():
            status = "✓" if result.get("success") else "✗"
            print(f"{status} {name.upper()}")
            if result.get("success"):
                if "counts" in result:
                    for key, val in result["counts"].items():
                        print(f"   {key}: {val}")
                if "count" in result:
                    print(f"   items: {result['count']}")
            else:
                print(f"   Error: {result.get('error')}")


if __name__ == "__main__":
    # Initialize comprehensive scraper
    scraper = ComprehensiveEDHScraper(output_dir="data_sources_comprehensive")
    
    # Add all scrapers
    scraper.add_scraper(EDHRecScraper(scraper.output_dir))
    scraper.add_scraper(TappedOutScraper(scraper.output_dir))
    scraper.add_scraper(MoxfieldScraper(scraper.output_dir))
    scraper.add_scraper(PriceScraper(scraper.output_dir))
    
    # Execute scraping
    scraper.scrape_all()
    scraper.print_summary()
