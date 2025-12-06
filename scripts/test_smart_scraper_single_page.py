#!/usr/bin/env python3
"""
Quick test of smart scraper - get first commander page and display results.
"""

import sys
import os
from pathlib import Path

# Add scripts to path
sys.path.insert(0, '/home/maxwell/vector-mtg/scripts')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

# Import the smart content handler
from edhrec_smart_scraper import AdvancedDynamicContentHandler


def setup_driver(headless=False):
    """Setup Chrome driver."""
    options = ChromeOptions()
    
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Enable performance logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Disable images for speed
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver


def smart_scroll_and_extract(driver, url, strategy='combined'):
    """
    Load page, scroll with smart detection, and extract cards.
    
    Args:
        driver: Selenium WebDriver
        url: Commander page URL
        strategy: Dynamic content detection strategy
        
    Returns:
        List of card dictionaries
    """
    print(f"\n{'='*70}")
    print(f"Loading: {url}")
    print(f"Strategy: {strategy}")
    print(f"{'='*70}\n")
    
    # Load page
    driver.get(url)
    print("✓ Page loaded")
    
    # Create content handler
    handler = AdvancedDynamicContentHandler(driver, timeout=10)
    
    # Wait for initial load
    print("Waiting for initial content...")
    handler.wait_for_loading_indicator_gone(max_wait=5)
    print("✓ Initial content ready")
    
    # Scroll and wait smartly
    print("\nStarting infinite scroll...")
    scroll_count = 0
    previous_card_count = 0
    no_change_count = 0
    max_scrolls = 30
    
    card_selector = "//a[contains(@href, '/cards/')]"
    
    for scroll in range(max_scrolls):
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        scroll_count += 1
        print(f"  Scroll {scroll_count}...", end='', flush=True)
        
        # Wait for content using strategy
        if strategy == 'elements':
            current_count = handler.wait_for_element_count_stable(
                selector=card_selector,
                stable_time=0.3,
                max_wait=5
            )
        elif strategy == 'combined':
            handler.wait_for_dynamic_content(
                card_selector=card_selector,
                strategy='combined',
                max_wait=5
            )
            current_count = len(driver.find_elements(By.XPATH, card_selector))
        else:
            # Other strategies
            handler.wait_for_dynamic_content(
                card_selector=card_selector,
                strategy=strategy,
                max_wait=5
            )
            current_count = len(driver.find_elements(By.XPATH, card_selector))
        
        # Check if new cards appeared
        if current_count == previous_card_count:
            no_change_count += 1
            print(f" {current_count} cards (no change #{no_change_count})")
            if no_change_count >= 3:
                print(f"\n✓ No new cards after 3 scrolls, stopping")
                break
        else:
            new_cards = current_count - previous_card_count
            print(f" {current_count} cards (+{new_cards} new)")
            no_change_count = 0
            previous_card_count = current_count
    
    print(f"\n{'='*70}")
    print(f"Scrolling complete: {scroll_count} scrolls, {previous_card_count} cards found")
    print(f"{'='*70}\n")
    
    # Extract all cards
    print("Extracting card data...")
    cards = []
    seen_names = set()
    
    card_elements = driver.find_elements(By.XPATH, card_selector)
    
    for elem in card_elements:
        try:
            # Get card name
            card_name = elem.text.strip()
            if not card_name:
                card_name = elem.get_attribute('title') or elem.get_attribute('data-name') or ''
                card_name = card_name.strip()
            
            if not card_name or card_name in seen_names:
                continue
            
            seen_names.add(card_name)
            
            # Get URL
            card_url = elem.get_attribute('href') or ''
            
            # Try to get additional data from parent/siblings
            try:
                parent = elem.find_element(By.XPATH, '..')
                parent_text = parent.text
                
                # Look for percentage (synergy)
                synergy = None
                if '%' in parent_text:
                    for part in parent_text.split():
                        if '%' in part:
                            synergy = part
                            break
                
                # Try to get card type from nearby text
                card_type = None
                try:
                    type_elem = parent.find_element(By.XPATH, ".//*[contains(@class, 'type')]")
                    card_type = type_elem.text.strip()
                except:
                    pass
                
                cards.append({
                    'name': card_name,
                    'url': card_url,
                    'synergy': synergy,
                    'type': card_type
                })
            except:
                cards.append({
                    'name': card_name,
                    'url': card_url,
                    'synergy': None,
                    'type': None
                })
        
        except Exception as e:
            continue
    
    print(f"✓ Extracted {len(cards)} unique cards\n")
    
    return cards


def print_cards_table(cards, max_rows=50):
    """Print cards in a nice table format."""
    print(f"\n{'='*100}")
    print(f"CARD RESULTS ({len(cards)} total cards, showing first {min(len(cards), max_rows)})")
    print(f"{'='*100}\n")
    
    # Table header
    print(f"{'#':<4} {'Card Name':<45} {'Synergy':<10} {'Type':<20}")
    print(f"{'-'*4} {'-'*45} {'-'*10} {'-'*20}")
    
    # Table rows
    for idx, card in enumerate(cards[:max_rows], 1):
        name = card['name'][:44] if len(card['name']) > 44 else card['name']
        synergy = card.get('synergy') or '-'
        card_type = card.get('type', '-') or '-'
        card_type = card_type[:19] if len(card_type) > 19 else card_type
        
        print(f"{idx:<4} {name:<45} {synergy:<10} {card_type:<20}")
    
    if len(cards) > max_rows:
        print(f"\n... and {len(cards) - max_rows} more cards")
    
    print(f"\n{'='*100}\n")


def test_commander_page(url, strategy='combined', headless=False):
    """Test scraping a single commander page."""
    driver = None
    
    try:
        print(f"\n{'#'*70}")
        print(f"# SMART SCRAPER TEST")
        print(f"# Strategy: {strategy}")
        print(f"# Headless: {headless}")
        print(f"{'#'*70}")
        
        # Setup
        driver = setup_driver(headless=headless)
        
        # Scrape
        cards = smart_scroll_and_extract(driver, url, strategy=strategy)
        
        # Display results
        print_cards_table(cards, max_rows=50)
        
        # Summary statistics
        print("SUMMARY STATISTICS:")
        print(f"  Total unique cards: {len(cards)}")
        print(f"  Cards with synergy data: {sum(1 for c in cards if c.get('synergy'))}")
        print(f"  Cards with type data: {sum(1 for c in cards if c.get('type'))}")
        
        # Sample URLs
        if cards:
            print(f"\nSAMPLE URLS (first 3):")
            for card in cards[:3]:
                print(f"  {card['name']}: {card['url']}")
        
        return cards
    
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
            print("✓ Browser closed")


if __name__ == "__main__":
    # Parse arguments
    strategy = 'combined'  # default
    headless = True
    commander_url = "https://edhrec.com/commanders/atraxa-praetors-voice"
    
    for arg in sys.argv[1:]:
        if arg.startswith('--strategy='):
            strategy = arg.split('=')[1]
        elif arg == '--no-headless':
            headless = False
        elif arg.startswith('--url='):
            commander_url = arg.split('=', 1)[1]
    
    print("\nAvailable strategies:")
    print("  - network: Monitor network activity")
    print("  - dom: Watch DOM mutations")
    print("  - elements: Element count stabilization (RECOMMENDED)")
    print("  - loading: Wait for loading indicators")
    print("  - combined: Multiple strategies (DEFAULT)")
    
    print(f"\nUsing: {strategy}")
    print(f"URL: {commander_url}")
    
    if not headless:
        print("\n⚠️  Browser will be VISIBLE (--no-headless mode)")
    
    # Run test
    test_commander_page(commander_url, strategy=strategy, headless=headless)
