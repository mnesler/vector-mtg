#!/usr/bin/env python3
"""
Scrape EDHREC combo data using Playwright.
Extracts combo counts by color identity from edhrec.com/combos.
"""

from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time
import re


def scrape_edhrec_combos():
    """
    Scrape combo data from EDHREC combos page using Playwright.
    
    Returns:
        dict: Combo data organized by color identity with counts
    """
    url = "https://edhrec.com/combos"
    
    print(f"Fetching data from {url}...")
    print("Using Playwright (headless browser)...")
    
    combo_data = {
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'total_combos': None,
        'combos_by_color': {},
        'color_categories': [],
        'raw_data': []
    }
    
    with sync_playwright() as p:
        browser = None
        try:
            # Launch browser
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to page
            print(f"Navigating to {url}...")
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for content to load
            print("Waiting for dynamic content to load...")
            time.sleep(3)
            
            # Scroll down to load all content
            print("Scrolling to load all content...")
            for i in range(5):  # Scroll multiple times to ensure all content loads
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(0.5)
            
            # Scroll back to top
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            # Get page title
            title = page.title()
            combo_data['page_title'] = title
            print(f"✓ Page loaded: {title}")
            
            # Try to find total combo count
            # Look for elements that might contain the total
            total_elements = page.query_selector_all('text=/\\d+.*combo/i')
            if total_elements:
                for element in total_elements:
                    text = element.text_content() or ""
                    numbers = re.findall(r'(\d+)', text)
                    if numbers:
                        count = int(numbers[0])
                        if count > 100:  # Likely the total
                            combo_data['total_combos'] = count
                            print(f"✓ Found total combos: {count:,}")
                            break
            
            # Look for color filter buttons/sections
            # EDHREC typically uses color identity filters
            print("Looking for color identity sections...")
            
            # Try to find color filter elements
            color_filters = page.query_selector_all('[class*="color"], [class*="identity"], [data-color], button')
            
            color_mapping = {
                'w': 'White',
                'u': 'Blue',
                'b': 'Black',
                'r': 'Red',
                'g': 'Green',
                'c': 'Colorless',
                'white': 'White',
                'blue': 'Blue',
                'black': 'Black',
                'red': 'Red',
                'green': 'Green',
                'colorless': 'Colorless'
            }
            
            # Extract all visible text that might contain combo counts
            body_text = page.inner_text('body')
            
            # Look for EDHREC's specific format: "ColorName### combos"
            # Example: "Colorless669 combos", "Esper850 combos", "Yore-Tiller199 combos"
            # Also match formats like "1.7K combos", "3.2K combos"
            # Match hyphenated names and single words
            
            # Pattern 1: Direct number format (e.g., "Esper 850 combos")
            color_combo_pattern = r'([A-Z][a-z]+(?:-[A-Z][a-z]+)?)(\d+)\s*combos?'
            matches = re.findall(color_combo_pattern, body_text)
            
            for color_name, count_str in matches:
                count = int(count_str)
                if count > 0 and count < 50000:
                    combo_data['combos_by_color'][color_name] = count
                    combo_data['color_categories'].append({
                        'category': color_name,
                        'count': count,
                        'raw_text': f"{color_name}{count_str} combos"
                    })
                    print(f"  Found {color_name}: {count:,}")
            
            # Pattern 2: K format (e.g., "Mono-Blue 3.2K combos")
            color_combo_pattern_k = r'([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s*([\d.]+)K\s*combos?'
            matches_k = re.findall(color_combo_pattern_k, body_text, re.IGNORECASE)
            
            for color_name, count_str in matches_k:
                count = int(float(count_str) * 1000)
                if count > 0 and count < 100000:
                    if color_name not in combo_data['combos_by_color']:
                        combo_data['combos_by_color'][color_name] = count
                        combo_data['color_categories'].append({
                            'category': color_name,
                            'count': count,
                            'raw_text': f"{color_name} {count_str}K combos"
                        })
                        print(f"  Found {color_name}: {count:,}")
            
            # Pattern 3: Standard format with spaces (e.g., "Esper 850 combos")
            color_combo_pattern2 = r'([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s+(\d+)\s*combos?'
            matches2 = re.findall(color_combo_pattern2, body_text)
            
            for color_name, count_str in matches2:
                count = int(count_str)
                if count > 0 and count < 50000:
                    if color_name not in combo_data['combos_by_color']:
                        combo_data['combos_by_color'][color_name] = count
                        combo_data['color_categories'].append({
                            'category': color_name,
                            'count': count,
                            'raw_text': f"{color_name} {count_str} combos"
                        })
                        print(f"  Found {color_name}: {count:,}")
            
            # Old pattern matching code (keep as fallback)
            # Look for patterns like "W: 1234" or "White: 1234"
            lines = body_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for color indicators with numbers
                for key, color_name in color_mapping.items():
                    pattern = rf'\b{key}\b.*?(\d+)|{color_name}.*?(\d+)'
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        count = int(match.group(1) or match.group(2))
                        if count > 0 and count < 50000:  # Sanity check
                            if color_name not in combo_data['combos_by_color']:
                                combo_data['combos_by_color'][color_name] = count
                                combo_data['color_categories'].append({
                                    'category': color_name,
                                    'count': count,
                                    'raw_text': line
                                })
                                print(f"  Found {color_name}: {count:,}")
            
            # Try to find filter buttons or tabs
            print("Looking for filter elements...")
            filter_buttons = page.query_selector_all('button, a[role="button"], [role="tab"]')
            
            for button in filter_buttons:
                text = button.text_content()
                if text:
                    text = text.strip()
                    # Check if this looks like a color filter
                    for key, color_name in color_mapping.items():
                        if key.lower() in text.lower() or color_name.lower() in text.lower():
                            # Try to find associated count
                            numbers = re.findall(r'(\d+)', text)
                            if numbers:
                                count = int(numbers[0])
                                if count > 0 and count < 50000:
                                    if color_name not in combo_data['combos_by_color']:
                                        combo_data['combos_by_color'][color_name] = count
                                        combo_data['color_categories'].append({
                                            'category': color_name,
                                            'count': count,
                                            'raw_text': text
                                        })
                                        print(f"  Found {color_name}: {count:,}")
            
            # Look for specific EDHREC combo card elements
            print("Looking for combo cards...")
            combo_cards = page.query_selector_all('[class*="combo"], [class*="card-container"]')
            print(f"Found {len(combo_cards)} potential combo elements")
            
            # Extract data from combo cards
            for i, card in enumerate(combo_cards[:10]):  # Sample first 10
                try:
                    card_text = card.text_content() or ""
                    card_html = card.inner_html()
                    
                    combo_data['raw_data'].append({
                        'index': i,
                        'text': card_text.strip()[:200],  # First 200 chars
                        'has_color_indicator': 'color' in card_html.lower()
                    })
                except:
                    pass
            
            # Get full page HTML for analysis
            print("Capturing page structure...")
            
            # Look for any element with numbers that might be combo counts
            all_numbers = page.query_selector_all('text=/\\d+/')
            number_contexts = []
            
            for elem in all_numbers[:50]:  # Check first 50 number elements
                try:
                    text = elem.text_content() or ""
                    text = text.strip()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        count = int(numbers[0])
                        if count > 10 and count < 50000:
                            # Get parent context
                            parent = elem.evaluate('element => element.parentElement.textContent')
                            number_contexts.append({
                                'number': count,
                                'context': parent.strip()[:100] if parent else text
                            })
                except:
                    pass
            
            combo_data['number_contexts'] = number_contexts[:20]  # Store sample
            
            # Take a screenshot for debugging
            screenshot_path = f"edhrec_combos_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            combo_data['screenshot'] = screenshot_path
            print(f"✓ Screenshot saved: {screenshot_path}")
            
            browser.close()
            print("✓ Browser closed")
            
            return combo_data
            
        except Exception as e:
            print(f"✗ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            if browser:
                try:
                    browser.close()
                except:
                    pass
            return combo_data


def generate_report(combo_data):
    """
    Generate a human-readable report from combo data.
    
    Args:
        combo_data (dict): Scraped combo data
        
    Returns:
        str: Formatted report
    """
    if not combo_data:
        return "No data available to generate report."
    
    report = []
    report.append("=" * 80)
    report.append("EDHREC COMBO DATA REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Page info
    if 'page_title' in combo_data:
        report.append(f"Page Title: {combo_data['page_title']}")
    
    report.append(f"URL: {combo_data['url']}")
    report.append(f"Scraped: {combo_data['scraped_at']}")
    report.append("")
    
    # Total combos
    report.append("-" * 80)
    report.append("TOTAL COMBOS")
    report.append("-" * 80)
    if combo_data['total_combos']:
        report.append(f"Total Combos Found: {combo_data['total_combos']:,}")
    else:
        report.append("Total Combos Found: Unknown (not detected)")
    report.append("")
    
    # Combos by color
    report.append("-" * 80)
    report.append("COMBOS BY COLOR IDENTITY")
    report.append("-" * 80)
    
    if combo_data['color_categories']:
        # Sort by count (descending)
        sorted_colors = sorted(combo_data['color_categories'], 
                              key=lambda x: x['count'], reverse=True)
        
        report.append(f"{'Category':<20} {'Count':>10}  {'Source'}")
        report.append("-" * 80)
        
        for color_cat in sorted_colors:
            category = color_cat['category']
            count = color_cat['count']
            raw_text = color_cat.get('raw_text', '')[:40]
            report.append(f"{category:<20} {count:>10,}  {raw_text}")
        
        report.append("")
        report.append(f"Total Color Categories Found: {len(combo_data['color_categories'])}")
    else:
        report.append("No color-specific combo data found.")
        report.append("")
        report.append("This might indicate:")
        report.append("  - The page structure has changed")
        report.append("  - Data is loaded via JavaScript after initial page load")
        report.append("  - Additional interaction required to reveal combo data")
    
    report.append("")
    
    # Number contexts (debugging info)
    if combo_data.get('number_contexts'):
        report.append("-" * 80)
        report.append("NUMBERS FOUND ON PAGE (for debugging)")
        report.append("-" * 80)
        for ctx in combo_data['number_contexts'][:10]:
            report.append(f"  {ctx['number']:>6,}: {ctx['context']}")
        report.append("")
    
    # Screenshot info
    if combo_data.get('screenshot'):
        report.append(f"Screenshot saved: {combo_data['screenshot']}")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def save_report(report, combo_data, filename_prefix="edhrec_combos_report"):
    """
    Save report to file.
    
    Args:
        report (str): Report text
        combo_data (dict): Raw combo data
        filename_prefix (str): Prefix for output filenames
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save text report
    txt_filename = f"{filename_prefix}_{timestamp}.txt"
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Report saved to: {txt_filename}")
    
    # Save JSON data
    json_filename = f"{filename_prefix}_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(combo_data, f, indent=2)
    print(f"✓ JSON data saved to: {json_filename}")
    
    return txt_filename, json_filename


if __name__ == "__main__":
    print("EDHREC Combo Scraper (Playwright)")
    print("=" * 80)
    print()
    
    # Scrape data
    combo_data = scrape_edhrec_combos()
    
    if combo_data:
        print()
        print("✓ Data extraction complete")
        print()
        
        # Generate report
        report = generate_report(combo_data)
        
        # Print report to console
        print(report)
        print()
        
        # Save to files
        save_report(report, combo_data)
        
        print()
        print("✓ Scraping complete!")
    else:
        print()
        print("✗ Failed to scrape data")
