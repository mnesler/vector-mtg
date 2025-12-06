#!/usr/bin/env python3
"""
Test EDHREC scraper using requests + BeautifulSoup (no browser needed).
This won't handle infinite scroll, but will show the initial page data.
"""

import requests
from bs4 import BeautifulSoup
import time

def scrape_edhrec_static(url):
    """
    Scrape EDHREC page using requests (no JavaScript execution).
    Shows initial loaded cards only (no infinite scroll).
    """
    print(f"\n{'='*70}")
    print(f"EDHREC Static Scraper (No Browser)")
    print(f"URL: {url}")
    print(f"{'='*70}\n")
    
    print("Note: This scrapes initial HTML only (no infinite scroll)")
    print("For full card list, Selenium with working Chrome/Chromium is needed.\n")
    
    # Fetch page
    print("Fetching page...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    print(f"✓ Page fetched ({len(response.content)} bytes)\n")
    
    # Parse HTML
    print("Parsing HTML...")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find cards - try multiple selectors
    cards = []
    seen_names = set()
    
    # Try different selectors EDHREC might use
    selectors = [
        ('a[href*="/cards/"]', 'href'),
        ('a.card-link', 'href'),
        ('.card-name', 'text'),
        ('a[data-card-name]', 'data-card-name'),
    ]
    
    for selector, attr_type in selectors:
        elements = soup.select(selector)
        print(f"  Found {len(elements)} elements matching '{selector}'")
        
        for elem in elements:
            try:
                if attr_type == 'text':
                    card_name = elem.get_text(strip=True)
                elif attr_type == 'href':
                    card_name = elem.get_text(strip=True)
                    if not card_name:
                        # Try to get from title or aria-label
                        card_name = elem.get('title') or elem.get('aria-label', '')
                else:
                    card_name = elem.get(attr_type, '')
                
                if not card_name or len(card_name) < 2 or card_name in seen_names:
                    continue
                
                # Skip if it's a category/nav link
                if any(x in card_name.lower() for x in ['commanders', 'themes', 'tribes', 'view all']):
                    continue
                
                seen_names.add(card_name)
                
                # Get URL
                card_url = elem.get('href', '')
                if card_url and not card_url.startswith('http'):
                    card_url = 'https://edhrec.com' + card_url
                
                # Try to find synergy %
                synergy = None
                parent = elem.parent
                if parent:
                    parent_text = parent.get_text()
                    if '%' in parent_text:
                        for part in parent_text.split():
                            if '%' in part:
                                synergy = part
                                break
                
                cards.append({
                    'name': card_name,
                    'url': card_url,
                    'synergy': synergy,
                    'type': None
                })
            
            except Exception as e:
                continue
    
    print(f"\n✓ Extracted {len(cards)} unique cards")
    
    return cards


def print_cards_table(cards, max_rows=50):
    """Print cards in a nice table format."""
    print(f"\n{'='*100}")
    print(f"CARD RESULTS ({len(cards)} total cards, showing first {min(len(cards), max_rows)})")
    print(f"{'='*100}\n")
    
    # Table header
    print(f"{'#':<4} {'Card Name':<50} {'Synergy':<10} {'URL':<35}")
    print(f"{'-'*4} {'-'*50} {'-'*10} {'-'*35}")
    
    # Table rows
    for idx, card in enumerate(cards[:max_rows], 1):
        name = card['name'][:49] if len(card['name']) > 49 else card['name']
        synergy = card.get('synergy') or '-'
        url = card.get('url', '')[:34] if card.get('url') else '-'
        
        print(f"{idx:<4} {name:<50} {synergy:<10} {url:<35}")
    
    if len(cards) > max_rows:
        print(f"\n... and {len(cards) - max_rows} more cards")
    
    print(f"\n{'='*100}\n")


if __name__ == "__main__":
    import sys
    
    url = "https://edhrec.com/commanders/atraxa-praetors-voice"
    
    for arg in sys.argv[1:]:
        if arg.startswith('--url='):
            url = arg.split('=', 1)[1]
    
    print("\n⚠️  STATIC SCRAPER - NO SELENIUM")
    print("This version doesn't require Chrome/Chromium")
    print("It shows initial page HTML only (no infinite scroll)")
    print("For complete data, fix Chromium installation\n")
    
    cards = scrape_edhrec_static(url)
    print_cards_table(cards)
    
    print("\nSUMMARY:")
    print(f"  Cards found: {len(cards)}")
    print(f"  With synergy: {sum(1 for c in cards if c.get('synergy'))}")
    
    print("\n" + "="*70)
    print("TO GET ALL CARDS (with infinite scroll):")
    print("="*70)
    print("""
Chromium appears to have a snap issue. To fix:

1. Remove broken Chromium:
   sudo snap remove chromium

2. Install from apt:
   sudo apt-get update
   sudo apt-get install chromium-browser chromium-chromedriver

3. Then run:
   python scripts/test_chromium_scraper.py --strategy=elements

Or use the demo to see expected output:
   python scripts/demo_smart_scraper_output.py
""")
