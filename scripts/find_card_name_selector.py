#!/usr/bin/env python3
"""
Inspect card element structure to find correct selectors
"""

from playwright.sync_api import sync_playwright

url = "https://edhrec.com/commanders/atraxa-praetors-voice"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Loading: {url}\n")
    page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Wait for cards
    page.wait_for_selector('.CardLabel_container__3M9Zu', timeout=15000)
    
    # Get first card container
    first_card = page.locator('.CardLabel_container__3M9Zu').first
    
    print("First card container HTML:")
    print("="*60)
    html = first_card.evaluate("el => el.outerHTML")
    print(html[:2000])  # First 2000 chars
    print("="*60)
    
    # Try to find all links within the first card
    print("\nLinks within first card:")
    links = first_card.locator('a').all()
    for i, link in enumerate(links[:5]):
        href = link.get_attribute('href')
        text = link.inner_text()
        print(f"  [{i+1}] href={href}")
        print(f"      text={text[:50]}")
    
    # Look for specific class patterns
    print("\nLooking for card name classes...")
    
    # Try different selectors
    selectors_to_try = [
        'a[href^="/cards/"]',
        '.CardLabel_label',
        '[class*="name"]',
        '[class*="Name"]',
        'a[class*="card"]'
    ]
    
    for selector in selectors_to_try:
        try:
            elem = first_card.locator(selector).first
            if elem:
                text = elem.inner_text()
                href = elem.get_attribute('href')
                print(f"\n  {selector}")
                print(f"    text: {text[:80]}")
                print(f"    href: {href}")
        except:
            print(f"\n  {selector} - not found")
    
    browser.close()
