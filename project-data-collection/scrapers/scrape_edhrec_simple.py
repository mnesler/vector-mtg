#!/usr/bin/env python3
"""
Simplified EDHREC scraper - clicks Load More as many times as possible,
then extracts whatever combos are loaded.
"""
from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

def scrape_mono_white():
    url = "https://edhrec.com/combos/mono-white"
    output_file = f"mono_white_combos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Loading {url}...")
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            print("✓ Page loaded")
        except Exception as e:
            print(f"✗ Page load failed: {e}")
            browser.close()
            return
        
        # Click Load More button up to 20 times with timeout protection
        clicks = 0
        max_clicks = 20
        
        for i in range(max_clicks):
            combos = page.query_selector_all('.ComboView_cardContainer__x029o')
            count = len(combos)
            print(f"\nAttempt {i+1}/{max_clicks}: {count} combos loaded")
            
            try:
                button = page.query_selector('button:has-text("Load More")')
                if not button or not button.is_visible():
                    print("No more button - extraction complete!")
                    break
                
                print("  Clicking Load More...")
                button.click()
                time.sleep(3)
                
                new_count = len(page.query_selector_all('.ComboView_cardContainer__x029o'))
                if new_count > count:
                    print(f"  ✓ Loaded more: {count} -> {new_count}")
                    clicks += 1
                else:
                    print(f"  No new combos, stopping")
                    break
                    
            except Exception as e:
                print(f"  Error: {e}")
                break
        
        # Extract all combos
        print(f"\n{'='*60}")
        print(f"Extracting combo data...")
        combo_elements = page.query_selector_all('.ComboView_cardContainer__x029o')
        total = len(combo_elements)
        print(f"Found {total} combo elements")
        
        combos = []
        for idx, elem in enumerate(combo_elements):
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx+1}/{total}...")
            
            try:
                # Extract card names
                card_links = elem.query_selector_all('a[href*="/cards/"]')
                cards = []
                for link in card_links:
                    name = link.text_content().strip()
                    # Remove prices
                    import re
                    name = re.sub(r'\$[\d,]+\.?\d*', '', name).strip()
                    if name and len(name) > 2:
                        cards.append(name)
                
                # Get combo text
                text = elem.text_content() or ""
                
                combos.append({
                    'id': idx + 1,
                    'cards': cards,
                    'raw_text': text[:500]
                })
            except Exception as e:
                print(f"  Error extracting combo {idx+1}: {e}")
        
        browser.close()
        
        # Save results
        data = {
            'category': 'Mono-White',
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'button_clicks': clicks,
            'combos_extracted': len(combos),
            'combos': combos
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ COMPLETE")
        print(f"  Button clicks: {clicks}")
        print(f"  Combos extracted: {len(combos)}")
        print(f"  Output file: {output_file}")
        print(f"{'='*60}")

if __name__ == '__main__':
    scrape_mono_white()
