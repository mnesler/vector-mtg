#!/usr/bin/env python3
"""
Debug script to inspect the commanders dropdown structure
"""

from playwright.sync_api import sync_playwright
import time

url = "https://edhrec.com"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print(f"Loading: {url}\n")
    page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Click commanders dropdown
    print("Clicking commanders menu...")
    commanders_link = page.locator('#navbar-commanders')
    commanders_link.click()
    page.wait_for_timeout(1000)
    
    # Get the parent nav item
    nav_item = page.locator('#navbar-commanders').locator('xpath=..')
    
    print("\nNav item HTML:")
    html = nav_item.evaluate("el => el.outerHTML")
    print(html[:2000])
    
    # Try to find all dropdown content
    print("\n\nSearching for dropdown items...")
    
    # Try different selectors
    selectors = [
        '#navbar-commanders + .dropdown-menu',
        '#navbar-commanders ~ .dropdown-menu',
        '.nav-item.dropdown:has(#navbar-commanders) .dropdown-menu',
        'a#navbar-commanders ~ div',
    ]
    
    for selector in selectors:
        print(f"\nTrying: {selector}")
        try:
            elements = page.locator(selector).all()
            print(f"  Found {len(elements)} elements")
            if elements:
                for i, elem in enumerate(elements[:1]):
                    text = elem.inner_text()
                    print(f"  Text preview: {text[:300]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n\nKeeping browser open for 30 seconds for manual inspection...")
    page.wait_for_timeout(30000)
    
    browser.close()
