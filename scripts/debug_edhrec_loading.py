#!/usr/bin/env python3
"""
Quick diagnostic to see how EDHREC combos page loads.
Tests slow scrolling with detailed logging.
"""

from playwright.sync_api import sync_playwright
import time

def test_edhrec_loading():
    url = "https://edhrec.com/combos/mono-white"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless mode
        page = browser.new_page()
        
        print(f"Loading: {url}")
        page.goto(url, wait_until='networkidle', timeout=60000)
        print("✓ Page loaded")
        
        time.sleep(3)
        
        # Initial count
        combos = page.query_selector_all('.ComboView_cardContainer__x029o')
        print(f"\nInitial combo count: {len(combos)}")
        
        # Try to find Load More button
        print("\nLooking for 'Load More' button...")
        load_more_button = page.query_selector('button:has-text("Load More")')
        
        if load_more_button:
            print(f"✓ Found 'Load More' button: {load_more_button.text_content()}")
            print("  Is visible?", load_more_button.is_visible())
            
            # Click it 5 times and watch count grow
            for i in range(5):
                print(f"\n--- Click {i+1} ---")
                load_more_button.click()
                print("  Clicked, waiting 4 seconds...")
                time.sleep(4)
                
                combos = page.query_selector_all('.ComboView_cardContainer__x029o')
                print(f"  Current count: {len(combos)}")
                
                # Check if button still exists
                load_more_button = page.query_selector('button:has-text("Load More")')
                if not load_more_button:
                    print("  Button disappeared - all combos loaded!")
                    break
        else:
            print("✗ No 'Load More' button found")
            print("\nLooking for other button text...")
            all_buttons = page.query_selector_all('button')
            for btn in all_buttons[:10]:  # First 10 buttons
                text = btn.text_content()
                if text:
                    print(f"  Button: '{text.strip()}'")
        
        print(f"\n\nFinal count: {len(page.query_selector_all('.ComboView_cardContainer__x029o'))} combos")
        print("Done!")
        
        browser.close()

if __name__ == '__main__':
    test_edhrec_loading()
