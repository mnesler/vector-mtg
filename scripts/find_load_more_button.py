#!/usr/bin/env python3
"""
Find the "Load More" button on EDHREC
"""

from playwright.sync_api import sync_playwright

url = "https://edhrec.com/commanders/atraxa-praetors-voice"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print(f"Loading: {url}\n")
    page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Scroll down to see the button
    print("Scrolling down...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    
    # Look for "Load More" button with different selectors
    button_selectors = [
        'button:has-text("Load More")',
        'button:has-text("load more")',
        'a:has-text("Load More")',
        'button[class*="load"]',
        'button[class*="more"]',
        '[class*="load"][class*="more"]',
        'button',  # All buttons
    ]
    
    print("\nSearching for Load More button:\n")
    for selector in button_selectors:
        try:
            elements = page.locator(selector).all()
            if selector == 'button':
                # Filter to only show potential load more buttons
                for elem in elements:
                    text = elem.inner_text().strip()
                    if text and ('load' in text.lower() or 'more' in text.lower() or 'show' in text.lower()):
                        classes = elem.get_attribute('class')
                        print(f"  Button text: '{text}'")
                        print(f"    class: {classes}\n")
            else:
                print(f"  {selector:40s} → {len(elements):4d} elements")
                if elements and len(elements) < 10:
                    for i, elem in enumerate(elements[:3]):
                        text = elem.inner_text()
                        classes = elem.get_attribute('class')
                        print(f"    [{i+1}] '{text}' (class: {classes})")
        except Exception as e:
            print(f"  {selector:40s} → ERROR: {e}")
    
    # Look at CardLabel elements - these seem to be the actual cards
    print("\n=== Card Elements ===\n")
    card_containers = page.locator('.CardLabel_container__3M9Zu').all()
    print(f"Found {len(card_containers)} cards (.CardLabel_container__3M9Zu)")
    
    if card_containers:
        print("\nFirst 3 cards:")
        for i, card in enumerate(card_containers[:3]):
            try:
                # Try to get card name
                html = card.evaluate("el => el.outerHTML")
                # Extract text content
                text = card.inner_text()
                print(f"  [{i+1}] {text[:100]}")
            except:
                pass
    
    print("\n\nKeeping browser open for 30 seconds for manual inspection...")
    print("Look for the Load More button at the bottom!")
    page.wait_for_timeout(30000)
    
    browser.close()
