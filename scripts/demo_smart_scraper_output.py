#!/usr/bin/env python3
"""
Demo of smart scraper output - simulates what the real scraper would show.
This demonstrates the table format and data structure without needing Chrome.

To run the real scraper, first install Chrome/Chromium:
  sudo apt-get install chromium-browser
Then run: python scripts/test_smart_scraper_single_page.py
"""


def simulate_scraping():
    """Simulate scraping Atraxa commander page."""
    
    print(f"\n{'#'*70}")
    print(f"# SMART SCRAPER DEMO (SIMULATED DATA)")
    print(f"# This shows what the real scraper would output")
    print(f"{'#'*70}")
    
    print(f"\n{'='*70}")
    print(f"Loading: https://edhrec.com/commanders/atraxa-praetors-voice")
    print(f"Strategy: elements")
    print(f"{'='*70}\n")
    
    print("✓ Page loaded")
    print("Waiting for initial content...")
    print("✓ Initial content ready")
    
    print("\nStarting infinite scroll...")
    
    # Simulate scrolling
    scroll_data = [
        (1, 25, 25),
        (2, 50, 25),
        (3, 75, 25),
        (4, 100, 25),
        (5, 125, 25),
        (6, 150, 25),
        (7, 175, 25),
        (8, 200, 25),
        (9, 225, 25),
        (10, 245, 20),
        (11, 258, 13),
        (12, 265, 7),
        (13, 268, 3),
        (14, 268, 0),  # no change
        (15, 268, 0),  # no change
        (16, 268, 0),  # no change
    ]
    
    for scroll, total, new in scroll_data:
        if new > 0:
            print(f"  Scroll {scroll}... {total} cards (+{new} new)")
        else:
            change_num = scroll - 13
            print(f"  Scroll {scroll}... {total} cards (no change #{change_num})")
        
        if scroll >= 16:
            print(f"\n✓ No new cards after 3 scrolls, stopping")
            break
    
    print(f"\n{'='*70}")
    print(f"Scrolling complete: 16 scrolls, 268 cards found")
    print(f"{'='*70}\n")
    
    print("Extracting card data...")
    
    # Simulated card data based on actual EDHREC structure
    cards = [
        {'name': 'Doubling Season', 'synergy': '32%', 'type': 'Enchantment'},
        {'name': 'Winding Constrictor', 'synergy': '28%', 'type': 'Creature'},
        {'name': 'Corpsejack Menace', 'synergy': '27%', 'type': 'Creature'},
        {'name': 'Vorinclex, Monstrous Raider', 'synergy': '26%', 'type': 'Creature'},
        {'name': 'Teferi, Temporal Pilgrim', 'synergy': '25%', 'type': 'Planeswalker'},
        {'name': 'Tekuthal, Inquiry Dominus', 'synergy': '24%', 'type': 'Creature'},
        {'name': 'Myojin of Towering Might', 'synergy': '23%', 'type': 'Creature'},
        {'name': 'Pir, Imaginative Rascal', 'synergy': '23%', 'type': 'Creature'},
        {'name': 'Evolution Sage', 'synergy': '22%', 'type': 'Creature'},
        {'name': 'Flux Channeler', 'synergy': '21%', 'type': 'Creature'},
        {'name': 'Deepglow Skate', 'synergy': '21%', 'type': 'Creature'},
        {'name': 'Karn\'s Bastion', 'synergy': '20%', 'type': 'Land'},
        {'name': 'Grateful Apparition', 'synergy': '20%', 'type': 'Creature'},
        {'name': 'Sword of Truth and Justice', 'synergy': '19%', 'type': 'Artifact'},
        {'name': 'Planewide Celebration', 'synergy': '19%', 'type': 'Sorcery'},
        {'name': 'The Ozolith', 'synergy': '18%', 'type': 'Artifact'},
        {'name': 'Inexorable Tide', 'synergy': '18%', 'type': 'Enchantment'},
        {'name': 'Thrummingbird', 'synergy': '17%', 'type': 'Creature'},
        {'name': 'Hydra\'s Growth', 'synergy': '17%', 'type': 'Enchantment'},
        {'name': 'Contentious Plan', 'synergy': '16%', 'type': 'Sorcery'},
        # Staples (lower synergy but widely played)
        {'name': 'Sol Ring', 'synergy': '8%', 'type': 'Artifact'},
        {'name': 'Arcane Signet', 'synergy': '7%', 'type': 'Artifact'},
        {'name': 'Command Tower', 'synergy': '5%', 'type': 'Land'},
        {'name': 'Path to Exile', 'synergy': '6%', 'type': 'Instant'},
        {'name': 'Swords to Plowshares', 'synergy': '6%', 'type': 'Instant'},
        {'name': 'Cyclonic Rift', 'synergy': '7%', 'type': 'Instant'},
        {'name': 'Fierce Guardianship', 'synergy': '9%', 'type': 'Instant'},
        {'name': 'Heroic Intervention', 'synergy': '8%', 'type': 'Instant'},
        {'name': 'Cultivate', 'synergy': '5%', 'type': 'Sorcery'},
        {'name': 'Kodama\'s Reach', 'synergy': '5%', 'type': 'Sorcery'},
        {'name': 'Assassin\'s Trophy', 'synergy': '9%', 'type': 'Instant'},
        {'name': 'Nature\'s Lore', 'synergy': '6%', 'type': 'Sorcery'},
        {'name': 'Three Visits', 'synergy': '6%', 'type': 'Sorcery'},
        {'name': 'Rhystic Study', 'synergy': '10%', 'type': 'Enchantment'},
        {'name': 'Mystic Remora', 'synergy': '9%', 'type': 'Enchantment'},
        {'name': 'Smothering Tithe', 'synergy': '8%', 'type': 'Enchantment'},
        {'name': 'Esper Sentinel', 'synergy': '7%', 'type': 'Creature'},
        {'name': 'Birds of Paradise', 'synergy': '6%', 'type': 'Creature'},
        {'name': 'Sakura-Tribe Elder', 'synergy': '5%', 'type': 'Creature'},
        {'name': 'Eternal Witness', 'synergy': '7%', 'type': 'Creature'},
        {'name': 'Demonic Tutor', 'synergy': '8%', 'type': 'Sorcery'},
        {'name': 'Vampiric Tutor', 'synergy': '9%', 'type': 'Instant'},
        {'name': 'Enlightened Tutor', 'synergy': '10%', 'type': 'Instant'},
        {'name': 'Mystical Tutor', 'synergy': '8%', 'type': 'Instant'},
        {'name': 'Worldly Tutor', 'synergy': '7%', 'type': 'Instant'},
        {'name': 'Mana Crypt', 'synergy': '9%', 'type': 'Artifact'},
        {'name': 'Mana Vault', 'synergy': '7%', 'type': 'Artifact'},
        {'name': 'Chrome Mox', 'synergy': '6%', 'type': 'Artifact'},
        {'name': 'Mox Diamond', 'synergy': '7%', 'type': 'Artifact'},
        {'name': 'Toxic Deluge', 'synergy': '8%', 'type': 'Sorcery'},
    ]
    
    print(f"✓ Extracted {len(cards)} unique cards\n")
    
    return cards


def print_cards_table(cards, max_rows=50):
    """Print cards in a nice table format."""
    print(f"\n{'='*100}")
    print(f"CARD RESULTS ({len(cards)} total cards, showing first {min(len(cards), max_rows)})")
    print(f"{'='*100}\n")
    
    # Table header
    print(f"{'#':<4} {'Card Name':<45} {'Synergy':<10} {'Type':<20}")
    print(f"{'-'*4} {'-'*45} {'-'*10} {'-'*20}")
    
    # Table rows
    for idx, card in enumerate(cards[:max_rows], 1):
        name = card['name'][:44] if len(card['name']) > 44 else card['name']
        synergy = card.get('synergy') or '-'
        card_type = card.get('type', '-') or '-'
        card_type = card_type[:19] if len(card_type) > 19 else card_type
        
        print(f"{idx:<4} {name:<45} {synergy:<10} {card_type:<20}")
    
    if len(cards) > max_rows:
        print(f"\n... and {len(cards) - max_rows} more cards")
    
    print(f"\n{'='*100}\n")


def main():
    """Run demo."""
    cards = simulate_scraping()
    print_cards_table(cards, max_rows=50)
    
    # Summary statistics
    print("SUMMARY STATISTICS:")
    print(f"  Total unique cards: {len(cards)}")
    print(f"  Cards with synergy data: {sum(1 for c in cards if c.get('synergy'))}")
    print(f"  Cards with type data: {sum(1 for c in cards if c.get('type'))}")
    
    print("\n" + "="*70)
    print("HOW THE SMART SCRAPER WORKS:")
    print("="*70)
    print("""
1. LOAD PAGE
   - Navigates to commander page
   - Waits for initial loading indicators to disappear

2. INTELLIGENT SCROLLING
   - Scrolls to bottom of page
   - Counts card elements: a[href*='/cards/']
   - Waits until count stabilizes (no new cards for 300ms)
   - Repeats until no new cards appear (3 scrolls with same count)

3. ELEMENT COUNT STABILIZATION
   Instead of fixed delays (time.sleep), monitors actual cards:
   
   Current count: 100 cards → wait → 125 cards (still loading!)
   Current count: 125 cards → wait → 150 cards (still loading!)
   Current count: 150 cards → wait → 150 cards (stable for 300ms, done!)
   
   This adapts to:
   - Fast connections: waits less
   - Slow connections: waits longer
   - Always gets all content

4. DATA EXTRACTION
   - Finds all card links
   - Extracts name, URL, synergy %, type
   - Deduplicates by name
   - Returns structured data

5. ADVANTAGES OVER FIXED DELAYS
   ✓ No missed cards (waits until actually stable)
   ✓ No wasted time (stops as soon as stable)
   ✓ Adapts to network speed automatically
   ✓ More reliable than height-based detection
""")
    
    print("="*70)
    print("TO RUN THE REAL SCRAPER:")
    print("="*70)
    print("""
1. Install Chrome/Chromium:
   sudo apt-get install chromium-browser

2. Run test scraper:
   python scripts/test_smart_scraper_single_page.py

3. Options:
   --strategy=elements        Use element count (recommended)
   --strategy=combined        Use combined approach (default)
   --strategy=network         Monitor network activity
   --no-headless              Show browser window
   --url=https://...          Custom commander URL

Example:
   python scripts/test_smart_scraper_single_page.py --strategy=elements --no-headless
""")


if __name__ == "__main__":
    main()
