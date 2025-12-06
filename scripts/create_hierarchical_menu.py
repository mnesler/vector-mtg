#!/usr/bin/env python3
"""
Convert flat EDHREC commander list into hierarchical menu structure
Organizes by color identity: Mono, 2-Color (guilds), 3-Color, 4-Color, 5-Color
"""

import json
from pathlib import Path
from datetime import datetime


def create_hierarchical_menu(commanders_list):
    """
    Create hierarchical menu structure from flat commander list
    
    Returns:
        Hierarchical menu structure matching EDHREC navbar
    """
    
    # Define the hierarchical structure
    menu = {
        "menu": "Commanders",
        "source": "EDHREC",
        "extracted_at": datetime.now().isoformat(),
        "categories": []
    }
    
    # Top Commanders (link to main commanders page)
    menu["categories"].append({
        "name": "Top Commanders",
        "url": "https://edhrec.com/commanders",
        "has_submenu": False
    })
    
    # Partners (link to partners page)
    menu["categories"].append({
        "name": "Partners",
        "url": "https://edhrec.com/partners",
        "has_submenu": False
    })
    
    # Mono Color
    mono_colors = []
    for cmd in commanders_list:
        if cmd["name"] in ["Mono White", "Mono Blue", "Mono Black", "Mono Red", "Mono Green", "Colorless"]:
            mono_colors.append({
                "name": cmd["name"],
                "url": cmd["url"]
            })
    
    menu["categories"].append({
        "name": "Mono",
        "has_submenu": True,
        "subcategories": mono_colors
    })
    
    # 2-Color (Guilds)
    two_color_guilds = [
        "Azorius", "Dimir", "Rakdos", "Gruul", "Selesnya",
        "Orzhov", "Izzet", "Golgari", "Boros", "Simic"
    ]
    
    two_color = []
    for guild in two_color_guilds:
        for cmd in commanders_list:
            if cmd["name"] == guild:
                two_color.append({
                    "name": cmd["name"],
                    "url": cmd["url"]
                })
                break
    
    menu["categories"].append({
        "name": "2 Color",
        "has_submenu": True,
        "subcategories": two_color
    })
    
    # 3-Color (Shards and Wedges)
    three_color_names = [
        "Esper", "Grixis", "Jund", "Naya", "Bant",  # Shards
        "Abzan", "Jeskai", "Sultai", "Mardu", "Temur"  # Wedges
    ]
    
    three_color = []
    for name in three_color_names:
        for cmd in commanders_list:
            if cmd["name"] == name:
                three_color.append({
                    "name": cmd["name"],
                    "url": cmd["url"]
                })
                break
    
    menu["categories"].append({
        "name": "3 Color",
        "has_submenu": True,
        "subcategories": three_color
    })
    
    # 4-Color (Nephilim)
    four_color_names = [
        "Yore Tiller",  # WUBR (no Green)
        "Glint Eye",     # UBRG (no White)
        "Dune Brood",    # BRGW (no Blue)
        "Ink Treader",   # RGWU (no Black)
        "Witch Maw"      # GWUB (no Red)
    ]
    
    four_color = []
    for name in four_color_names:
        for cmd in commanders_list:
            if cmd["name"] == name:
                four_color.append({
                    "name": cmd["name"],
                    "url": cmd["url"]
                })
                break
    
    menu["categories"].append({
        "name": "4 Color",
        "has_submenu": True,
        "subcategories": four_color
    })
    
    # 5-Color
    five_color = []
    for cmd in commanders_list:
        if cmd["name"] == "Five Color":
            five_color.append({
                "name": cmd["name"],
                "url": cmd["url"]
            })
    
    menu["categories"].append({
        "name": "5 Color",
        "has_submenu": True,
        "subcategories": five_color
    })
    
    return menu


def display_hierarchical_menu(menu):
    """Display the menu in a tree-like format"""
    print("\n" + "="*70)
    print("EDHREC Commander Menu Hierarchy")
    print("="*70)
    print(f"\nExtracted: {menu['extracted_at']}\n")
    
    for category in menu['categories']:
        if category.get('has_submenu'):
            print(f"📁 {category['name']}")
            for subcat in category.get('subcategories', []):
                print(f"   ├─ {subcat['name']}")
                print(f"   │  └─ {subcat['url']}")
        else:
            print(f"📄 {category['name']}")
            if 'url' in category:
                print(f"   └─ {category['url']}")
        print()
    
    # Summary
    total_subcategories = sum(
        len(cat.get('subcategories', [])) 
        for cat in menu['categories']
    )
    
    print("="*70)
    print(f"Total categories: {len(menu['categories'])}")
    print(f"Total subcategories: {total_subcategories}")
    print("="*70)


def main():
    """Main execution"""
    # Load the flat commander list
    input_file = Path("data_sources_comprehensive/edhrec_full/edhrec_full_20251204_071721.json")
    
    print("="*70)
    print("Converting EDHREC Commander List to Hierarchical Menu")
    print("="*70)
    print(f"\nInput: {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    commanders_list = data.get('commanders', [])
    print(f"Loaded {len(commanders_list)} commanders\n")
    
    # Create hierarchical structure
    print("Creating hierarchical menu structure...")
    menu = create_hierarchical_menu(commanders_list)
    
    # Display the structure
    display_hierarchical_menu(menu)
    
    # Save to file
    output_file = Path("data_sources_comprehensive/edhrec_commander_menu_hierarchical.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(menu, f, indent=2, ensure_ascii=False)
    
    file_size = output_file.stat().st_size
    print(f"✓ Saved successfully ({file_size:,} bytes)\n")
    
    # Show sample JSON
    print("\n" + "="*70)
    print("Sample JSON Structure (2 Color category):")
    print("="*70)
    
    two_color_cat = next(cat for cat in menu['categories'] if cat['name'] == '2 Color')
    print(json.dumps(two_color_cat, indent=2))
    
    print("\n" + "="*70)
    print(f"✓ Complete! Hierarchical menu saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    main()
