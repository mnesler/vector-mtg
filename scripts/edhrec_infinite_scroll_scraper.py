#!/usr/bin/env python3
"""
EDHREC Infinite Scroll Scraper - Optimized for Speed
Scrapes all commanders with their top cards and categories using fast infinite scroll.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EDHRecInfiniteScrollScraper:
    """Fast EDHREC scraper with optimized infinite scroll handling."""
    
    BASE_URL = "https://edhrec.com"
    SCROLL_PAUSE = 0.2  # Fast scroll pause (200ms)
    MAX_SCROLL_ATTEMPTS = 50  # Maximum scroll attempts per page
    
    def __init__(self, output_dir: str = "data_sources_comprehensive/edhrec_full", headless: bool = True):
        """
        Initialize the EDHREC scraper.
        
        Args:
            output_dir: Output directory for results
            headless: Run browser in headless mode
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # Data storage
        self.commanders_data = []
        self.cards_by_commander = {}
        self.categories_data = {}
        
    def _setup_driver(self):
        """Setup optimized Selenium WebDriver."""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # Performance optimizations
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-images")  # Don't load images (faster)
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable unnecessary features for speed
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 10)
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
    
    def _scroll_to_bottom_fast(self, max_attempts: int = None) -> int:
        """
        Scroll to bottom of page using fast infinite scroll technique.
        
        Args:
            max_attempts: Maximum scroll attempts (default: MAX_SCROLL_ATTEMPTS)
            
        Returns:
            Number of successful scrolls performed
        """
        if max_attempts is None:
            max_attempts = self.MAX_SCROLL_ATTEMPTS
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        no_change_count = 0
        
        for attempt in range(max_attempts):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Short pause to let content load
            time.sleep(self.SCROLL_PAUSE)
            
            # Calculate new height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                no_change_count += 1
                # If height hasn't changed 3 times in a row, we're done
                if no_change_count >= 3:
                    logger.debug(f"Scroll complete after {scroll_count} scrolls")
                    break
            else:
                no_change_count = 0
                scroll_count += 1
                last_height = new_height
        
        return scroll_count
    
    def _extract_cards_from_page(self) -> List[Dict[str, Any]]:
        """
        Extract all card data from current page after scrolling.
        
        Returns:
            List of card dictionaries with name, category, synergy, etc.
        """
        cards = []
        seen_names = set()
        
        # Try multiple selectors to find cards
        selectors = [
            "//div[contains(@class, 'card-list')]//a[contains(@href, '/cards/')]",
            "//a[contains(@href, '/cards/')]",
            "//div[@class='card']//a",
            "//span[@class='card-name']",
        ]
        
        for selector in selectors:
            try:
                card_elements = self.driver.find_elements(By.XPATH, selector)
                
                for elem in card_elements:
                    try:
                        # Get card name
                        card_name = elem.text.strip()
                        if not card_name or len(card_name) < 2:
                            # Try getting from title or data attribute
                            card_name = elem.get_attribute('title') or elem.get_attribute('data-name') or ''
                            card_name = card_name.strip()
                        
                        if not card_name or card_name in seen_names:
                            continue
                        
                        # Get card URL
                        card_url = elem.get_attribute('href') or ''
                        
                        # Skip non-card links
                        if '/cards/' not in card_url and not card_name:
                            continue
                        
                        seen_names.add(card_name)
                        
                        # Try to get additional context (synergy %, category, etc.)
                        parent = elem.find_element(By.XPATH, '..')
                        synergy = None
                        category = None
                        
                        try:
                            # Look for synergy percentage
                            synergy_elem = parent.find_element(By.XPATH, ".//*[contains(text(), '%')]")
                            synergy_text = synergy_elem.text.strip()
                            if '%' in synergy_text:
                                synergy = synergy_text
                        except:
                            pass
                        
                        try:
                            # Look for category
                            category_elem = parent.find_element(By.XPATH, ".//*[@class='category' or contains(@class, 'section')]")
                            category = category_elem.text.strip()
                        except:
                            pass
                        
                        cards.append({
                            "name": card_name,
                            "url": card_url,
                            "synergy": synergy,
                            "category": category,
                            "scraped_at": datetime.now().isoformat()
                        })
                    
                    except (StaleElementReferenceException, NoSuchElementException) as e:
                        logger.debug(f"Element error: {e}")
                        continue
                
                if cards:
                    break  # If we found cards, no need to try other selectors
            
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
        
        logger.info(f"  Extracted {len(cards)} unique cards")
        return cards
    
    def _extract_category_cards(self, category_name: str) -> List[Dict[str, Any]]:
        """
        Extract cards from a specific category section.
        
        Args:
            category_name: Name of the category
            
        Returns:
            List of cards in that category
        """
        cards = []
        seen_names = set()
        
        try:
            # Find the category section
            section_xpath = f"//h2[contains(text(), '{category_name}')]/.."
            section = self.driver.find_element(By.XPATH, section_xpath)
            
            # Get all card links within this section
            card_links = section.find_elements(By.XPATH, ".//a[contains(@href, '/cards/')]")
            
            for link in card_links:
                try:
                    card_name = link.text.strip() or link.get_attribute('title') or link.get_attribute('data-name') or ''
                    card_name = card_name.strip()
                    
                    if card_name and card_name not in seen_names:
                        seen_names.add(card_name)
                        cards.append({
                            "name": card_name,
                            "url": link.get_attribute('href'),
                            "category": category_name
                        })
                except:
                    continue
        
        except NoSuchElementException:
            logger.debug(f"Category '{category_name}' not found on page")
        
        return cards
    
    def scrape_commander_page(self, commander_url: str, commander_name: str) -> Dict[str, Any]:
        """
        Scrape a single commander page with infinite scroll.
        
        Args:
            commander_url: Full URL to commander page
            commander_name: Name of the commander
            
        Returns:
            Dictionary with commander data and all cards
        """
        logger.info(f"Scraping: {commander_name}")
        
        try:
            self.driver.get(commander_url)
            time.sleep(0.3)  # Brief pause for initial load
            
            # Perform infinite scroll
            scroll_count = self._scroll_to_bottom_fast()
            logger.info(f"  Scrolled {scroll_count} times")
            
            # Extract all cards after scrolling
            all_cards = self._extract_cards_from_page()
            
            # Try to extract category-specific cards
            categories = {}
            category_names = [
                "Top Cards",
                "Creatures",
                "Instants",
                "Sorceries",
                "Enchantments",
                "Artifacts",
                "Planeswalkers",
                "Lands",
                "Mana Artifacts",
                "Card Draw",
                "Ramp",
                "Removal",
                "Board Wipes",
                "Protection",
                "Recursion"
            ]
            
            for cat_name in category_names:
                cat_cards = self._extract_category_cards(cat_name)
                if cat_cards:
                    categories[cat_name] = cat_cards
            
            return {
                "commander": commander_name,
                "url": commander_url,
                "total_cards": len(all_cards),
                "all_cards": all_cards,
                "categories": categories,
                "scroll_count": scroll_count,
                "scraped_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scraping {commander_name}: {e}")
            return {
                "commander": commander_name,
                "url": commander_url,
                "error": str(e),
                "scraped_at": datetime.now().isoformat()
            }
    
    def discover_commanders(self) -> List[Dict[str, str]]:
        """
        Discover all commanders from the commanders page.
        
        Returns:
            List of commander dictionaries with name and URL
        """
        commanders = []
        seen_urls = set()
        
        # Color combinations to check
        color_combos = [
            '', 'w', 'u', 'b', 'r', 'g',  # Mono
            'wu', 'wb', 'ub', 'ur', 'br', 'bg', 'rg', 'rw', 'gw', 'gu',  # Dual
            'wub', 'ubr', 'brg', 'rgw', 'gwu', 'wbr', 'urg', 'bgu', 'rwb', 'gur',  # Tri
            'wubr', 'ubrg', 'brgw', 'rgwu', 'gwub',  # 4-color
            'wubrg'  # 5-color
        ]
        
        for combo in color_combos:
            url = f"{self.BASE_URL}/commanders"
            if combo:
                url += f"/{combo}"
            
            logger.info(f"Discovering commanders: {url}")
            
            try:
                self.driver.get(url)
                time.sleep(0.3)
                
                # Scroll to load all commanders
                scroll_count = self._scroll_to_bottom_fast(max_attempts=20)
                logger.info(f"  Scrolled {scroll_count} times")
                
                # Find all commander links
                links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/commanders/')]")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.text.strip() or link.get_attribute('title') or ''
                        
                        if href and href not in seen_urls and '/commanders/' in href:
                            # Filter out non-commander pages
                            parts = href.split('/commanders/')
                            if len(parts) > 1:
                                slug = parts[1].strip('/').split('/')[0]
                                
                                # Skip index pages
                                if slug and slug not in ['w', 'u', 'b', 'r', 'g', 'wu', 'wb', 'ub', 'ur', 'br', 'bg', 'rg', 'rw', 'gw', 'gu']:
                                    seen_urls.add(href)
                                    commanders.append({
                                        "name": text or slug.replace('-', ' ').title(),
                                        "url": href,
                                        "slug": slug
                                    })
                    except:
                        continue
                
                logger.info(f"  Found {len(commanders)} total commanders so far")
                time.sleep(0.2)  # Brief rate limit
            
            except Exception as e:
                logger.warning(f"Error discovering commanders for {combo}: {e}")
        
        return commanders
    
    def scrape_all_commanders(self, limit: Optional[int] = None):
        """
        Scrape all commanders and their cards.
        
        Args:
            limit: Optional limit on number of commanders to scrape (for testing)
        """
        if not self._setup_driver():
            logger.error("Failed to setup driver")
            return
        
        try:
            # Phase 1: Discover all commanders
            print("\n" + "=" * 70)
            print("PHASE 1: DISCOVERING COMMANDERS")
            print("=" * 70)
            
            commanders = self.discover_commanders()
            logger.info(f"✓ Discovered {len(commanders)} unique commanders")
            
            if limit:
                commanders = commanders[:limit]
                logger.info(f"  Limiting to first {limit} commanders")
            
            # Phase 2: Scrape each commander's page
            print("\n" + "=" * 70)
            print(f"PHASE 2: SCRAPING {len(commanders)} COMMANDER PAGES")
            print("=" * 70)
            
            for idx, commander in enumerate(commanders, 1):
                print(f"\n[{idx}/{len(commanders)}] {commander['name']}")
                
                result = self.scrape_commander_page(commander['url'], commander['name'])
                self.commanders_data.append(result)
                
                # Save incrementally every 10 commanders
                if idx % 10 == 0:
                    self._save_checkpoint(idx)
            
            # Phase 3: Save final results
            print("\n" + "=" * 70)
            print("PHASE 3: SAVING RESULTS")
            print("=" * 70)
            
            output_file = self._save_results()
            
            # Print summary
            total_cards = sum(r.get('total_cards', 0) for r in self.commanders_data)
            successful = sum(1 for r in self.commanders_data if 'error' not in r)
            
            print(f"\n{'=' * 70}")
            print("SCRAPING COMPLETE")
            print(f"{'=' * 70}")
            print(f"✓ Output: {output_file}")
            print(f"  Commanders scraped: {successful}/{len(commanders)}")
            print(f"  Total cards: {total_cards:,}")
        
        finally:
            self._close_driver()
    
    def _save_checkpoint(self, checkpoint_num: int):
        """Save intermediate checkpoint."""
        checkpoint_file = self.output_dir / f"checkpoint_{checkpoint_num}.json"
        
        data = {
            "metadata": {
                "checkpoint": checkpoint_num,
                "scraped_at": datetime.now().isoformat(),
                "commanders_count": len(self.commanders_data)
            },
            "commanders": self.commanders_data
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"  ✓ Checkpoint saved: {checkpoint_file}")
    
    def _save_results(self) -> Path:
        """Save final scraping results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"edhrec_commanders_{timestamp}.json"
        
        total_cards = sum(r.get('total_cards', 0) for r in self.commanders_data)
        
        data = {
            "metadata": {
                "source": "EDHREC (Infinite Scroll)",
                "scraped_at": datetime.now().isoformat(),
                "total_commanders": len(self.commanders_data),
                "total_cards": total_cards,
                "scroll_pause_seconds": self.SCROLL_PAUSE,
                "method": "Selenium with optimized infinite scroll"
            },
            "commanders": self.commanders_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Results saved to: {output_file}")
        return output_file


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    headless = '--no-headless' not in sys.argv
    limit = None
    
    for arg in sys.argv[1:]:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
    
    scraper = EDHRecInfiniteScrollScraper(headless=headless)
    scraper.scrape_all_commanders(limit=limit)
