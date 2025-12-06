#!/usr/bin/env python3
"""
EDHREC Selenium-based scraper for JavaScript-rendered content.
Uses Selenium to load pages and extract card recommendations.
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EDHRecSeleniumScraper:
    """Scrape EDHREC using Selenium for JavaScript rendering."""
    
    BASE_URL = "https://edhrec.com"
    
    def __init__(self, output_dir: str = "data_sources_comprehensive", headless: bool = True):
        """
        Initialize the EDHREC Selenium scraper.
        
        Args:
            output_dir: Output directory for results
            headless: Run browser in headless mode (no GUI)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.headless = headless
        self.driver = None
        self.commanders_data = []
        self.cards_by_commander = {}
        self.combos = []
        
    def _setup_driver(self):
        """Setup Selenium WebDriver."""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("✓ Chrome WebDriver initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def _close_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("✓ WebDriver closed")
    
    def scrape(self) -> Dict[str, Any]:
        """Run the full EDHREC scraping process."""
        print("\n" + "=" * 70)
        print("EDHREC SELENIUM SCRAPER")
        print("=" * 70)
        
        if not self._setup_driver():
            return {
                "success": False,
                "error": "Failed to initialize WebDriver",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            print("\nPhase 1: Discovering commanders...")
            self._discover_commanders_selenium()
            print(f"  ✓ Found {len(self.commanders_data)} commanders")
            
            print("\nPhase 2: Fetching card recommendations for each commander...")
            self._get_cards_for_commanders()
            total_cards = sum(len(cards) for cards in self.cards_by_commander.values())
            print(f"  ✓ Found {total_cards:,} card recommendations")
            
            print("\nPhase 3: Scraping combo database...")
            self._scrape_combos_selenium()
            print(f"  ✓ Found {len(self.combos)} combos")
            
            # Save results
            output_file = self._save_results()
            
            return {
                "success": True,
                "output_file": str(output_file),
                "counts": {
                    "commanders": len(self.commanders_data),
                    "cards": total_cards,
                    "combos": len(self.combos)
                },
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        finally:
            self._close_driver()
    
    def _discover_commanders_selenium(self):
        """Discover all commanders by visiting commander pages."""
        # Strategy: Visit main commanders page and extract all color combos
        color_combos = [
            '', 'w', 'u', 'b', 'r', 'g',  # Mono
            'wu', 'wb', 'ub', 'ur', 'br', 'bg', 'rg', 'rw', 'gw', 'gu',  # Dual
            'wub', 'wbr', 'bru', 'rgu', 'guw', 'wur', 'bgu', 'brg', 'rgw', 'ubw',  # Tri
            'wubr', 'wubg', 'wurg', 'wbrg', 'ubrg', 'wubrg'  # 4+
        ]
        
        seen = set()
        
        for combo in color_combos:
            url = f"{self.BASE_URL}/commanders"
            if combo:
                url += f"/{combo}"
            
            try:
                logger.info(f"Loading: {url}")
                self.driver.get(url)
                
                # Wait for page to load
                time.sleep(2)
                
                # Get all commander links
                links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/commanders/')]")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        
                        if href and '/commanders/' in href:
                            # Extract commander slug
                            parts = href.split('/commanders/')
                            if len(parts) > 1:
                                cmd_slug = parts[1].strip('/')
                                
                                if cmd_slug not in seen and cmd_slug and '-' in cmd_slug:
                                    seen.add(cmd_slug)
                                    self.commanders_data.append({
                                        "name": text or cmd_slug.replace('-', ' ').title(),
                                        "url_slug": cmd_slug,
                                        "url": href,
                                        "discovered_at": datetime.now().isoformat()
                                    })
                    except Exception as e:
                        logger.debug(f"Error processing commander link: {e}")
                
                time.sleep(1)  # Rate limiting
            
            except Exception as e:
                logger.warning(f"Error discovering commanders for {combo}: {e}")
    
    def _get_cards_for_commanders(self):
        """Fetch card recommendations for each commander."""
        for idx, commander in enumerate(self.commanders_data, 1):
            if idx % 10 == 0:
                print(f"  Processing commander {idx}/{len(self.commanders_data)}...")
            
            url = commander["url"]
            
            try:
                logger.debug(f"Loading commander page: {url}")
                self.driver.get(url)
                
                # Wait for cards to load
                time.sleep(2)
                
                cards = []
                
                # Try to find card recommendations in various possible containers
                # EDHREC uses different layouts, so try multiple selectors
                card_selectors = [
                    "//a[contains(@href, '/cards/')]",
                    "//div[contains(@class, 'card')]//a",
                    "//a[contains(@data-name, '')]",
                ]
                
                for selector in card_selectors:
                    try:
                        card_elements = self.driver.find_elements(By.XPATH, selector)
                        
                        for card_elem in card_elements[:100]:  # Top 100 cards
                            try:
                                card_name = card_elem.text.strip()
                                card_url = card_elem.get_attribute('href')
                                
                                if card_name and len(card_name) > 1 and not card_name.startswith('/'):
                                    # Avoid links, focus on card names
                                    if 'edhrec.com' in str(card_url):
                                        cards.append({
                                            "name": card_name,
                                            "url": card_url
                                        })
                            except Exception as e:
                                logger.debug(f"Error extracting card: {e}")
                        
                        if cards:
                            break  # If we found cards, don't try other selectors
                    
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                
                if cards:
                    # Deduplicate
                    seen_cards = set()
                    unique_cards = []
                    for card in cards:
                        if card["name"] not in seen_cards:
                            seen_cards.add(card["name"])
                            unique_cards.append(card)
                    
                    self.cards_by_commander[commander["name"]] = unique_cards[:100]
                
                time.sleep(0.5)  # Rate limiting
            
            except Exception as e:
                logger.warning(f"Error fetching cards for {commander['name']}: {e}")
    
    def _scrape_combos_selenium(self):
        """Scrape combo database from EDHREC."""
        url = f"{self.BASE_URL}/combos"
        
        try:
            logger.info(f"Loading combos page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(2)
            
            # Try to extract combo information
            combo_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'combo')]")
            
            for combo_elem in combo_elements[:100]:  # First 100 combos
                try:
                    combo_text = combo_elem.text.strip()
                    combo_url = combo_elem.find_element(By.TAG_NAME, 'a').get_attribute('href') if combo_elem.find_elements(By.TAG_NAME, 'a') else None
                    
                    if combo_text:
                        self.combos.append({
                            "combo": combo_text,
                            "url": combo_url,
                            "scraped_at": datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error extracting combo: {e}")
        
        except Exception as e:
            logger.warning(f"Error scraping combos: {e}")
    
    def _save_results(self) -> Path:
        """Save scraping results to JSON file."""
        output_path = self.output_dir / "edhrec_selenium"
        output_path.mkdir(parents=True, exist_ok=True)
        
        total_cards = sum(len(cards) for cards in self.cards_by_commander.values())
        
        data = {
            "metadata": {
                "source": "EDHREC (Selenium)",
                "scraped_at": datetime.now().isoformat(),
                "total_commanders": len(self.commanders_data),
                "total_cards": total_cards,
                "total_combos": len(self.combos),
                "method": "Selenium WebDriver with JavaScript rendering"
            },
            "commanders": self.commanders_data,
            "cards_by_commander": self.cards_by_commander,
            "combos": self.combos
        }
        
        output_file = output_path / f"edhrec_selenium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Results saved to: {output_file}")
        return output_file


if __name__ == "__main__":
    scraper = EDHRecSeleniumScraper(headless=True)
    result = scraper.scrape()
    
    if result["success"]:
        print(f"\n{'='*70}")
        print("SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"✓ Output: {result['output_file']}")
        print(f"  Commanders: {result['counts']['commanders']:,}")
        print(f"  Cards: {result['counts']['cards']:,}")
        print(f"  Combos: {result['counts']['combos']:,}")
    else:
        print(f"\n✗ Error: {result['error']}")
