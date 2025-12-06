#!/usr/bin/env python3
"""
Debug EDHREC page structure - get actual HTML
"""

from playwright.sync_api import sync_playwright

url = "https://edhrec.com/commanders/atraxa-praetors-voice"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Loading: {url}")
    page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Wait for content
    page.wait_for_timeout(3000)
    
    # Get all text content to see what's there
    content = page.content()
    
    # Look for card-related elements
    print("\n=== Looking for card elements ===\n")
    
    # Search in the HTML
    import re
    
    # Find card-related class names
    card_classes = set()
    for match in re.finditer(r'class="([^"]*card[^"]*)"', content, re.IGNORECASE):
        classes = match.group(1).split()
        for cls in classes:
            if 'card' in cls.lower():
                card_classes.add(cls)
    
    print(f"Found {len(card_classes)} unique card-related classes:\n")
    for cls in sorted(card_classes)[:20]:
        count = page.locator(f'.{cls}').count()
        print(f"  .{cls:50s} → {count:4d} elements")
    
    # Look for links to cards
    print("\n=== Card links ===\n")
    card_links = page.locator('a[href*="/cards/"]').all()
    print(f"Found {len(card_links)} links to /cards/")
    
    if card_links:
        print("\nFirst 3 card links:")
        for i, link in enumerate(card_links[:3]):
            href = link.get_attribute('href')
            text = link.inner_text()
            classes = link.get_attribute('class')
            print(f"  [{i+1}] {text[:40]:40s} → {href}")
            print(f"      class: {classes}")
    
    # Save page content for inspection
    with open('/tmp/edhrec_page.html', 'w') as f:
        f.write(content)
    print(f"\n✓ Saved full HTML to /tmp/edhrec_page.html")
    
    # Take screenshot
    page.screenshot(path='/tmp/edhrec_page.png', full_page=True)
    print(f"✓ Saved screenshot to /tmp/edhrec_page.png")
    
    browser.close()
