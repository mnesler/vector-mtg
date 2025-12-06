#!/usr/bin/env python3
"""
EDHREC Scraper using Playwright - DOM scraping approach
Waits for cards to load dynamically
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Page


class EDHRECPlaywrightScraper:
    """Scrapes EDHREC using Playwright by scraping DOM elements"""
    
    def __init__(self, headless: bool = True, output_dir: str = "data_sources_comprehensive/edhrec_scraped"):
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def card_name_to_url_slug(card_name: str) -> str:
        """
        Convert card name to EDHREC URL slug format
        
        Rules:
        - Convert to lowercase
        - Replace spaces with dashes
        - Keep only a-z and dashes
        - Remove all other characters (including apostrophes, commas, etc.)
        
        Examples:
            "Rhystic Study" -> "rhystic-study"
            "Atraxa, Praetors' Voice" -> "atraxa-praetors-voice"
            "Jeska's Will" -> "jeskas-will"
        
        Args:
            card_name: Original card name
            
        Returns:
            URL slug (lowercase, dashes, a-z only)
        """
        # Convert to lowercase
        slug = card_name.lower()
        
        # Replace spaces with dashes
        slug = slug.replace(' ', '-')
        
        # Remove all characters except a-z and dashes
        slug = re.sub(r'[^a-z\-]', '', slug)
        
        # Replace multiple consecutive dashes with single dash
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing dashes
        slug = slug.strip('-')
        
        return slug
        
    def scrape_commander(self, commander_slug: str, timeout_seconds: int = 30) -> Dict:
        """
        Scrape a single commander page
        
        Args:
            commander_slug: URL slug like 'atraxa-praetors-voice'
            timeout_seconds: Page load timeout
            
        Returns:
            Dictionary with metadata and cards
        """
        start_time = time.time()
        url = f"https://edhrec.com/commanders/{commander_slug}"
        
        print(f"\n{'='*60}")
        print(f"Scraping: {commander_slug}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            try:
                # Navigate to page
                print("⏳ Loading page...")
                page.goto(url, wait_until="networkidle", timeout=timeout_seconds * 1000)
                print("✓ Page loaded\n")
                
                # Wait for cards to appear (they're loaded dynamically)
                print("⏳ Waiting for card elements to load...")
                page.wait_for_selector('.Card_container__Ng56K', timeout=15000)
                print("✓ Cards detected\n")
                
                # Wait a bit more to ensure all cards are loaded
                print("⏳ Waiting for all cards to load...")
                time.sleep(2)
                
                # Extract card data
                print("⏳ Extracting card data...")
                cards = self._extract_cards(page)
                
                elapsed = time.time() - start_time
                
                # Build result
                result = {
                    "metadata": {
                        "commander_url": url,
                        "commander_slug": commander_slug,
                        "scraped_at": datetime.now().isoformat(),
                        "elapsed_seconds": round(elapsed, 2),
                        "total_cards": len(cards),
                        "extraction_method": "dom"
                    },
                    "cards": cards
                }
                
                print(f"\n{'='*60}")
                print(f"✓ Scrape Complete!")
                print(f"  Total cards: {len(cards)}")
                print(f"  Time: {elapsed:.2f}s")
                print(f"{'='*60}\n")
                
                return result
                
            finally:
                browser.close()
    
    def _extract_cards(self, page: Page) -> List[Dict]:
        """
        Extract all card data from the page, organized by category
        
        Args:
            page: Playwright page object
            
        Returns:
            List of card dictionaries
        """
        cards = []
        
        # Get all category sections (e.g., "newcards", "highsynergycards", "topcards", etc.)
        category_sections = page.locator('.Grid_cardlist__AXXsz').all()
        
        print(f"  Found {len(category_sections)} category sections\n")
        
        for section in category_sections:
            try:
                # Get category ID (e.g., "highsynergycards")
                category_id = section.get_attribute('id')
                
                # Get category title (e.g., "High Synergy Cards")
                try:
                    title_elem = section.locator('.Grid_header__iAPM8').first
                    category_title = title_elem.inner_text(timeout=2000).strip() if title_elem else (category_id or "Unknown")
                except:
                    # No title element or timeout - use ID or "Unknown"
                    category_title = category_id or "Unknown"
                
                # Get all cards in this category
                card_containers = section.locator('.Card_container__Ng56K').all()
                
                if not card_containers:
                    continue
                
                print(f"  [{category_id or 'unknown'}] {category_title}: {len(card_containers)} cards")
                
                for container in card_containers:
                    try:
                        # Extract card name
                        name_elem = container.locator('.Card_name__Mpa7S').first
                        name = name_elem.inner_text().strip() if name_elem else None
                        
                        if not name:
                            continue
                        
                        card_data = {
                            "name": name,
                            "url_slug": self.card_name_to_url_slug(name),
                            "category": category_id or "unknown",
                            "category_title": category_title
                        }
                        
                        # Extract stats from CardLabel container
                        stats_container = container.locator('.CardLabel_container__3M9Zu').first
                        if stats_container:
                            stats_text = stats_container.inner_text()
                            
                            # Parse inclusion percentage (e.g., "64%")
                            inclusion_match = re.search(r'(\d+(?:\.\d+)?)%\s*inclusion', stats_text, re.IGNORECASE)
                            if inclusion_match:
                                card_data['inclusion'] = float(inclusion_match.group(1))
                            
                            # Parse synergy percentage (e.g., "+26%" or "-6%")
                            synergy_match = re.search(r'([+-]?\d+)%\s*synergy', stats_text, re.IGNORECASE)
                            if synergy_match:
                                card_data['synergy'] = int(synergy_match.group(1))
                            
                            # Parse deck counts (e.g., "24.6K decks" out of "38.3K decks")
                            deck_counts = re.findall(r'([\d.]+K?)\s*decks', stats_text, re.IGNORECASE)
                            if len(deck_counts) >= 2:
                                card_data['num_decks'] = deck_counts[0]
                                card_data['total_decks'] = deck_counts[1]
                        
                        cards.append(card_data)
                        
                    except Exception as e:
                        print(f"    ⚠ Warning: Failed to extract card in {category_id}: {e}")
                        continue
                        
            except Exception as e:
                print(f"  ⚠ Warning: Failed to process category section: {e}")
                continue
        
        print(f"\n✓ Extracted {len(cards)} total cards across {len(category_sections)} categories\n")
        return cards
    
    def save_results(self, data: Dict, commander_slug: str) -> Path:
        """
        Save scrape results to JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{commander_slug}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        print(f"💾 Saving to: {filepath}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        file_size = filepath.stat().st_size
        print(f"✓ Saved successfully ({file_size:,} bytes)\n")
        
        return filepath


def main():
    """Test the scraper"""
    scraper = EDHRECPlaywrightScraper(headless=True)
    
    commander_slug = "atraxa-praetors-voice"
    
    try:
        result = scraper.scrape_commander(commander_slug)
        filepath = scraper.save_results(result, commander_slug)
        
        print(f"\n{'='*60}")
        print("✓ TEST SUCCESSFUL!")
        print(f"  File: {filepath}")
        print(f"  Cards: {result['metadata']['total_cards']}")
        print(f"{'='*60}\n")
        
        # Show first 3 cards
        if result['cards']:
            print("First 3 cards:")
            for i, card in enumerate(result['cards'][:3], 1):
                print(f"  [{i}] {card.get('name', 'UNKNOWN')}")
                print(f"      {card.get('raw_text', '')[:80]}...")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise


if __name__ == "__main__":
    main()
