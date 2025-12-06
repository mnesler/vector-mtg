#!/usr/bin/env python3
"""
Inspect EDHREC page structure to find correct selectors
"""

from playwright.sync_api import sync_playwright

url = "https://edhrec.com/commanders/atraxa-praetors-voice"

print(f"Inspecting: {url}\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("Loading page...")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    print("✓ Page loaded\n")
    
    # Wait for content
    page.wait_for_timeout(5000)
    
    # Get page title
    title = page.title()
    print(f"Page title: {title}\n")
    
    # Try to find cards with different selectors
    selectors_to_try = [
        'a.Card_card__item__1L7HG',  # Original
        '.Card_card__item__1L7HG',
        'a[class*="Card_card"]',
        'div[class*="Card"]',
        'a[href*="/cards/"]',
        '.card',
        '[class*="card"]'
    ]
    
    print("Trying different selectors:\n")
    for selector in selectors_to_try:
        try:
            count = page.locator(selector).count()
            print(f"  {selector:40s} → {count:4d} elements")
            if count > 0 and count < 100:
                # Show first element's HTML
                first = page.locator(selector).first
                html = first.evaluate("el => el.outerHTML")
                print(f"    First element: {html[:200]}...")
        except Exception as e:
            print(f"  {selector:40s} → ERROR: {e}")
    
    print("\n\nPress Ctrl+C to close browser...")
    input()
    
    browser.close()
