#!/usr/bin/env python3
"""
Quick test of smart scraper - get first commander page and display results.
Uses Chromium browser directly without webdriver-manager.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, '/home/maxwell/vector-mtg/scripts')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service

# Import the smart content handler and data saver
from edhrec_smart_scraper import AdvancedDynamicContentHandler
from data_saver import EDHRecDataSaver


def setup_driver_chromium(headless=False):
    """Setup Chromium driver directly."""
    print("\n" + "="*70)
    print("INITIALIZING BROWSER")
    print("="*70)
    
    options = ChromeOptions()
    
    # Point to chromium binary
    chromium_path = "/usr/bin/chromium-browser"
    if not os.path.exists(chromium_path):
        print(f"✗ ERROR: Chromium not found at {chromium_path}")
        print("  Install with: sudo apt-get install chromium-browser")
        return None
    
    print(f"✓ Found Chromium: {chromium_path}")
    options.binary_location = chromium_path
    
    if headless:
        options.add_argument("--headless=new")
        print("  Mode: Headless (no visible window)")
    else:
        print("  Mode: Visible window")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Enable performance logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Disable images for speed
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    print("  Images: Disabled (faster)")
    
    # Find chromedriver - try common locations
    print("\nSearching for chromedriver...")
    chromedriver_paths = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "chromedriver"  # In PATH
    ]
    
    chromedriver = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            chromedriver = path
            print(f"✓ Found chromedriver: {path}")
            break
        elif path == "chromedriver":
            # Try to find in PATH
            import shutil
            chromedriver = shutil.which("chromedriver")
            if chromedriver:
                print(f"✓ Found chromedriver in PATH: {chromedriver}")
                break
    
    if not chromedriver:
        print("✗ ERROR: chromedriver not found!")
        print("\nTried these locations:")
        for path in chromedriver_paths:
            print(f"  - {path}")
        print("\nInstall with: sudo apt-get install chromium-chromedriver")
        return None
    
    try:
        print("\nStarting Chromium browser...")
        service = Service(chromedriver)
        driver = webdriver.Chrome(service=service, options=options)
        print("✓ Browser started successfully")
        print("="*70 + "\n")
        return driver
    except Exception as e:
        print(f"✗ ERROR: Failed to start Chromium")
        print(f"  Error details: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Chromium installation: chromium-browser --version")
        print("  2. Check chromedriver version: chromedriver --version")
        print("  3. Reinstall: sudo apt-get install --reinstall chromium-browser chromium-chromedriver")
        return None


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
    try:
        print("Navigating to page...")
        driver.get(url)
        print("✓ Page loaded successfully")
    except Exception as e:
        print(f"✗ ERROR loading page: {e}")
        raise
    
    # Create content handler
    try:
        print("Initializing content handler...")
        handler = AdvancedDynamicContentHandler(driver, timeout=10)
        print("✓ Content handler ready")
    except Exception as e:
        print(f"✗ ERROR creating content handler: {e}")
        raise
    
    # Wait for initial load
    try:
        print("\nWaiting for initial content to load...")
        handler.wait_for_loading_indicator_gone(max_wait=5)
        print("✓ Initial content ready")
    except Exception as e:
        print(f"⚠ WARNING: Loading indicator check failed: {e}")
        print("  Continuing anyway...")
    
    # Scroll and wait smartly
    print("\n" + "="*70)
    print("Starting infinite scroll (checking every 300ms)...")
    print("="*70)
    scroll_count = 0
    previous_card_count = 0
    no_change_count = 0
    max_scrolls = 30
    
    card_selector = "//a[contains(@href, '/cards/')]"
    
    for scroll in range(max_scrolls):
        # Scroll to bottom
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_count += 1
            print(f"\n[Scroll {scroll_count:2d}] ", end='', flush=True)
        except Exception as e:
            print(f"\n✗ ERROR scrolling: {e}")
            break
        
        # Wait for content using strategy
        try:
            if strategy == 'elements':
                print("Waiting for element count to stabilize...", end=' ', flush=True)
                current_count = handler.wait_for_element_count_stable(
                    selector=card_selector,
                    stable_time=0.3,
                    max_wait=5
                )
            elif strategy == 'combined':
                print("Using combined detection...", end=' ', flush=True)
                handler.wait_for_dynamic_content(
                    card_selector=card_selector,
                    strategy='combined',
                    max_wait=5
                )
                current_count = len(driver.find_elements(By.XPATH, card_selector))
            else:
                print(f"Using {strategy} strategy...", end=' ', flush=True)
                handler.wait_for_dynamic_content(
                    card_selector=card_selector,
                    strategy=strategy,
                    max_wait=5
                )
                current_count = len(driver.find_elements(By.XPATH, card_selector))
            
            print(f"→", end=' ', flush=True)
        except Exception as e:
            print(f"\n⚠ WARNING: Content detection error on scroll {scroll_count}: {e}")
            print("  Attempting to count cards anyway...")
            try:
                current_count = len(driver.find_elements(By.XPATH, card_selector))
            except:
                print("  ✗ Failed to count cards, stopping")
                break
        
        # Check if new cards appeared
        if current_count == previous_card_count:
            no_change_count += 1
            print(f"{current_count} cards (NO CHANGE #{no_change_count}/3)")
            if no_change_count >= 3:
                print(f"\n{'='*70}")
                print(f"✓ Scrolling complete: No new cards after 3 attempts")
                print(f"{'='*70}")
                break
        else:
            new_cards = current_count - previous_card_count
            print(f"{current_count} cards (+{new_cards} NEW) ✓")
            no_change_count = 0
            previous_card_count = current_count
    
    print(f"\n{'='*70}")
    print(f"Final count: {scroll_count} scrolls, {previous_card_count} card elements found")
    print(f"{'='*70}\n")
    
    # Extract all cards
    print("Extracting card data from page...")
    cards = []
    seen_names = set()
    extraction_errors = 0
    
    try:
        card_elements = driver.find_elements(By.XPATH, card_selector)
        print(f"Found {len(card_elements)} card elements to process")
    except Exception as e:
        print(f"✗ ERROR finding card elements: {e}")
        return []
    
    print(f"Processing cards", end='', flush=True)
    progress_marker = max(1, len(card_elements) // 20)  # Show progress every 5%
    
    for idx, elem in enumerate(card_elements):
        if idx % progress_marker == 0:
            print('.', end='', flush=True)
        
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
            except Exception as e:
                extraction_errors += 1
                cards.append({
                    'name': card_name,
                    'url': card_url,
                    'synergy': None,
                    'type': None
                })
        
        except Exception as e:
            extraction_errors += 1
            continue
    
    print(f" done")
    print(f"✓ Extracted {len(cards)} unique cards")
    if extraction_errors > 0:
        print(f"⚠ {extraction_errors} extraction errors (non-critical)")
    print()
    
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
    start_time = time.time()
    
    try:
        print(f"\n{'#'*70}")
        print(f"# EDHREC SMART SCRAPER TEST")
        print(f"# URL: {url}")
        print(f"# Strategy: {strategy}")
        print(f"# Headless: {headless}")
        print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}")
        
        # Setup
        driver = setup_driver_chromium(headless=headless)
        if not driver:
            print("\n✗ FAILED: Could not initialize browser")
            return None
        
        # Scrape
        try:
            cards = smart_scroll_and_extract(driver, url, strategy=strategy)
        except Exception as e:
            print(f"\n✗ ERROR during scraping: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            print(f"  Traceback:\n{traceback.format_exc()}")
            return None
        
        # Display results
        print_cards_table(cards, max_rows=50)
        
        # Summary statistics
        elapsed_time = time.time() - start_time
        print("="*70)
        print("SUMMARY STATISTICS")
        print("="*70)
        print(f"  Total unique cards: {len(cards)}")
        print(f"  Cards with synergy data: {sum(1 for c in cards if c.get('synergy'))}")
        print(f"  Cards with type data: {sum(1 for c in cards if c.get('type'))}")
        print(f"  Elapsed time: {elapsed_time:.1f} seconds")
        print(f"  Average: {elapsed_time/len(cards) if cards else 0:.2f} seconds per card")
        
        # Sample URLs
        if cards:
            print(f"\nSAMPLE DATA (first 3 cards):")
            for idx, card in enumerate(cards[:3], 1):
                print(f"  {idx}. {card['name']}")
                print(f"     URL: {card['url']}")
                print(f"     Synergy: {card.get('synergy', 'N/A')}")
                print(f"     Type: {card.get('type', 'N/A')}")
        
        # Save to file using robust saver
        saver = EDHRecDataSaver()
        saved_file = saver.save_commander_data(
            commander_url=url,
            cards=cards,
            strategy=strategy,
            elapsed_time=elapsed_time
        )
        
        if not saved_file:
            print("⚠ WARNING: Data was not saved to disk (kept in memory only)")
        
        print("\n" + "="*70)
        print("✓ SCRAPING COMPLETED SUCCESSFULLY")
        print("="*70)
        
        return cards
    
    except KeyboardInterrupt:
        print("\n\n⚠ INTERRUPTED by user (Ctrl+C)")
        return None
    
    except Exception as e:
        print(f"\n\n✗ UNEXPECTED ERROR: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        print(f"  Full traceback:\n{traceback.format_exc()}")
        return None
    
    finally:
        if driver:
            print("\nCleaning up...")
            try:
                driver.quit()
                print("✓ Browser closed successfully")
            except Exception as e:
                print(f"⚠ Warning: Error closing browser: {e}")


if __name__ == "__main__":
    # Parse arguments
    strategy = 'elements'  # default - best for EDHREC
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
