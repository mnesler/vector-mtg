#!/usr/bin/env python3
"""
Debug Next.js JSON structure
"""

import json
from playwright.sync_api import sync_playwright

url = "https://edhrec.com/commanders/atraxa-praetors-voice"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print(f"Loading: {url}\n")
    page.goto(url, wait_until="networkidle", timeout=30000)
    
    # Extract __NEXT_DATA__
    script_content = page.locator('script#__NEXT_DATA__').inner_text()
    data = json.loads(script_content)
    
    # Save to file for inspection
    with open('/tmp/next_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✓ Saved to /tmp/next_data.json\n")
    
    # Navigate structure
    print("JSON Structure:")
    print(f"  Root keys: {list(data.keys())}\n")
    
    if 'props' in data:
        props = data['props']
        print(f"  props keys: {list(props.keys())}\n")
        
        if 'pageProps' in props:
            page_props = props['pageProps']
            print(f"  pageProps keys: {list(page_props.keys())}\n")
            
            if 'data' in page_props:
                data_obj = page_props['data']
                print(f"  data keys: {list(data_obj.keys())}\n")
                
                if 'data' in data_obj:
                    data_data = data_obj['data']
                    print(f"  data.data keys: {list(data_data.keys())}\n")
                    
                    if 'cards' in data_data:
                        cards = data_data['cards']
                        print(f"  data.data.cards type: {type(cards)}")
                        print(f"  data.data.cards length: {len(cards) if isinstance(cards, list) else 'N/A'}\n")
                        
                        if isinstance(cards, list) and len(cards) > 0:
                            print(f"  First card category keys: {list(cards[0].keys())}\n")
    
    browser.close()
