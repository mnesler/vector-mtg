#!/usr/bin/env python3
"""
Extract EDHREC commander navigation menu hierarchy
Gets all categories and subcategories from the navbar
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def extract_commander_menu():
    """
    Extract the complete commander menu hierarchy from EDHREC
    
    Returns:
        Dictionary with hierarchical menu structure
    """
    url = "https://edhrec.com"
    
    print("="*70)
    print("Extracting EDHREC Commander Menu Hierarchy")
    print("="*70)
    print(f"\nURL: {url}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to homepage
            print("⏳ Loading page...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            print("✓ Page loaded\n")
            
            # Find and click the Commanders dropdown
            print("⏳ Opening Commanders menu...")
            commanders_link = page.locator('#navbar-commanders')
            commanders_link.click()
            
            # Wait for dropdown to appear
            page.wait_for_timeout(500)
            print("✓ Menu opened\n")
            
            # Get the dropdown menu
            dropdown = page.locator('#navbar-commanders').locator('xpath=following-sibling::div[1]')
            
            menu_structure = {
                "menu": "Commanders",
                "url": url,
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "categories": []
            }
            
            # Get all top-level menu items
            menu_items = dropdown.locator('a.dropdown-item, button.dropdown-item').all()
            
            print(f"Found {len(menu_items)} menu items\n")
            
            for idx, item in enumerate(menu_items, 1):
                try:
                    # Get text and check if it's expandable
                    item_text = item.inner_text().strip()
                    
                    if not item_text:
                        continue
                    
                    print(f"[{idx}] Processing: {item_text}")
                    
                    # Check if this item has a submenu (it's a button, not a link)
                    tag_name = item.evaluate("el => el.tagName")
                    has_submenu = tag_name.lower() == 'button'
                    
                    category = {
                        "name": item_text,
                        "has_submenu": has_submenu
                    }
                    
                    # If it's a link, get the href
                    if not has_submenu:
                        href = item.get_attribute('href')
                        if href:
                            category["url"] = href if href.startswith('http') else f"{url}{href}"
                    
                    # If it has a submenu, click to expand and get subcategories
                    if has_submenu:
                        print(f"    → Expanding submenu...")
                        
                        # Click to expand
                        item.click()
                        page.wait_for_timeout(300)
                        
                        # Find the submenu
                        # It should be the next sibling div
                        try:
                            submenu = item.locator('xpath=following-sibling::div[1]')
                            
                            # Get all links in submenu
                            sublinks = submenu.locator('a').all()
                            
                            subcategories = []
                            for sublink in sublinks:
                                subtext = sublink.inner_text().strip()
                                subhref = sublink.get_attribute('href')
                                
                                if subtext:
                                    subcategory = {
                                        "name": subtext,
                                        "url": subhref if subhref and subhref.startswith('http') else f"{url}{subhref}"
                                    }
                                    subcategories.append(subcategory)
                                    print(f"      • {subtext}")
                            
                            category["subcategories"] = subcategories
                            print(f"    ✓ Found {len(subcategories)} subcategories")
                            
                            # Click again to collapse (clean up for next iteration)
                            item.click()
                            page.wait_for_timeout(200)
                            
                        except Exception as e:
                            print(f"    ⚠ Could not extract submenu: {e}")
                            category["subcategories"] = []
                    
                    menu_structure["categories"].append(category)
                    print()
                    
                except Exception as e:
                    print(f"    ✗ Error processing item: {e}\n")
                    continue
            
            print("="*70)
            print(f"✓ Extraction Complete!")
            print(f"  Total categories: {len(menu_structure['categories'])}")
            
            # Count subcategories
            total_subcategories = sum(
                len(cat.get('subcategories', [])) 
                for cat in menu_structure['categories']
            )
            print(f"  Total subcategories: {total_subcategories}")
            print("="*70)
            
            return menu_structure
            
        finally:
            browser.close()


def save_menu_structure(menu_data, output_file="data_sources_comprehensive/edhrec_commander_menu.json"):
    """Save menu structure to JSON file"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving to: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(menu_data, f, indent=2, ensure_ascii=False)
    
    file_size = output_path.stat().st_size
    print(f"✓ Saved successfully ({file_size:,} bytes)\n")
    
    return output_path


def display_menu_structure(menu_data):
    """Display the menu structure in a readable format"""
    print("\n" + "="*70)
    print("EDHREC Commander Menu Structure")
    print("="*70)
    print(f"\nExtracted: {menu_data['extracted_at']}\n")
    
    for category in menu_data['categories']:
        if category.get('has_submenu'):
            print(f"📁 {category['name']}")
            for subcat in category.get('subcategories', []):
                print(f"   ├─ {subcat['name']}")
                print(f"   │  └─ {subcat.get('url', 'N/A')}")
        else:
            print(f"📄 {category['name']}")
            if 'url' in category:
                print(f"   └─ {category['url']}")
        print()


def main():
    """Main execution"""
    # Extract menu structure
    menu_data = extract_commander_menu()
    
    # Save to file
    output_file = save_menu_structure(menu_data)
    
    # Display structure
    display_menu_structure(menu_data)
    
    # Print sample JSON
    print("\n" + "="*70)
    print("Sample JSON Output:")
    print("="*70)
    print(json.dumps(menu_data['categories'][0], indent=2))
    
    print("\n" + "="*70)
    print(f"✓ Complete! Menu saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
