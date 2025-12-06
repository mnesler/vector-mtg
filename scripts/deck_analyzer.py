#!/usr/bin/env python3
"""
Deck Analyzer: Extract card recommendations and statistics from real EDH decks.
Analyzes TappedOut and other deck sources to generate card frequency statistics,
combos, and recommendations.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Counter
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeckAnalyzer:
    """Analyze real EDH decks to extract card recommendations and statistics."""
    
    def __init__(self, output_dir: str = "data_sources_comprehensive"):
        """Initialize the deck analyzer."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.decks = []
        self.cards_frequency = defaultdict(int)
        self.commander_frequency = defaultdict(int)
        self.color_frequency = defaultdict(int)
        self.card_combos = []
        self.deck_archetypes = defaultdict(list)
        
    def load_tappedout_decks(self, filepath: str) -> bool:
        """Load TappedOut decks from JSON file."""
        try:
            with open(filepath) as f:
                self.decks = json.load(f)
            logger.info(f"✓ Loaded {len(self.decks)} TappedOut decks")
            return True
        except Exception as e:
            logger.error(f"Failed to load TappedOut decks: {e}")
            return False
    
    def load_comprehensive_decks(self, filepath: str) -> bool:
        """Load comprehensive decks from JSON file."""
        try:
            with open(filepath) as f:
                data = json.load(f)
                if isinstance(data, dict) and "decks" in data:
                    self.decks.extend(data["decks"])
                elif isinstance(data, list):
                    self.decks.extend(data)
            logger.info(f"✓ Loaded {len(self.decks)} total decks")
            return True
        except Exception as e:
            logger.error(f"Failed to load comprehensive decks: {e}")
            return False
    
    def analyze(self) -> Dict[str, Any]:
        """Run full deck analysis."""
        print("\n" + "=" * 70)
        print("DECK ANALYZER - EXTRACTING CARD RECOMMENDATIONS")
        print("=" * 70)
        
        # Extract card data from decks
        print("\nPhase 1: Extracting cards from decks...")
        self._extract_cards()
        print(f"  ✓ Found {len(self.cards_frequency):,} unique cards")
        print(f"  ✓ Total card inclusions: {sum(self.cards_frequency.values()):,}")
        
        # Analyze commanders
        print("\nPhase 2: Analyzing commanders...")
        self._analyze_commanders()
        print(f"  ✓ Found {len(self.commander_frequency)} unique commanders")
        print(f"  ✓ Most popular: {self._get_top_items(self.commander_frequency, 1)[0] if self.commander_frequency else 'N/A'}")
        
        # Find common card combinations
        print("\nPhase 3: Finding card combinations...")
        self._find_combos()
        print(f"  ✓ Found {len(self.card_combos)} potential combos")
        
        # Categorize by archetype
        print("\nPhase 4: Categorizing by archetype...")
        self._categorize_archetypes()
        print(f"  ✓ Found {len(self.deck_archetypes)} distinct archetypes")
        
        # Save results
        output_file = self._save_results()
        
        total_cards = sum(self.cards_frequency.values())
        
        return {
            "success": True,
            "output_file": str(output_file),
            "counts": {
                "decks_analyzed": len(self.decks),
                "unique_cards": len(self.cards_frequency),
                "total_card_inclusions": total_cards,
                "unique_commanders": len(self.commander_frequency),
                "combos_found": len(self.card_combos),
                "archetypes": len(self.deck_archetypes)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_cards(self):
        """Extract all cards from decks."""
        for deck in self.decks:
            # Try different deck data structures
            cards = None
            
            if isinstance(deck, dict):
                # Try common keys for card lists
                for key in ['cards', 'mainboard', 'deck_list', 'cardlist', 'card_list', 'content']:
                    if key in deck:
                        cards = deck[key]
                        break
                
                # If still no cards, try to parse deck content if it's a string
                if not cards and 'content' in deck:
                    cards = self._parse_deck_content(deck['content'])
            
            if cards:
                if isinstance(cards, dict):
                    # {card_name: quantity, ...}
                    for card_name, quantity in cards.items():
                        if card_name and isinstance(quantity, (int, str)):
                            try:
                                qty = int(quantity) if isinstance(quantity, str) else quantity
                                self.cards_frequency[card_name.strip()] += qty
                            except ValueError:
                                pass
                
                elif isinstance(cards, list):
                    # [card_name, card_name, ...]
                    for card in cards:
                        if isinstance(card, str):
                            self.cards_frequency[card.strip()] += 1
                        elif isinstance(card, dict) and 'name' in card:
                            qty = card.get('quantity', 1)
                            self.cards_frequency[card['name'].strip()] += qty
    
    def _parse_deck_content(self, content: str) -> Dict[str, int]:
        """Parse deck content string format."""
        cards = {}
        
        if not isinstance(content, str):
            return cards
        
        # Try to parse deck list format: "quantity card_name"
        pattern = r'^(\d+)\s+(.+)$'
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue
            
            match = re.match(pattern, line)
            if match:
                qty = int(match.group(1))
                card_name = match.group(2).strip()
                if card_name:
                    cards[card_name] = cards.get(card_name, 0) + qty
            else:
                # Try simple card name
                if len(line) > 2 and not any(c in line for c in [':', '=']):
                    cards[line] = cards.get(line, 0) + 1
        
        return cards
    
    def _analyze_commanders(self):
        """Analyze commander preferences."""
        for deck in self.decks:
            if isinstance(deck, dict):
                # Try common commander keys
                commander = None
                for key in ['commander', 'commander_name', 'general', 'leader']:
                    if key in deck:
                        commander = deck[key]
                        break
                
                if commander:
                    if isinstance(commander, dict) and 'name' in commander:
                        self.commander_frequency[commander['name']] += 1
                    elif isinstance(commander, str):
                        self.commander_frequency[commander] += 1
    
    def _find_combos(self):
        """Find common card combinations (cards that appear together frequently)."""
        # Find cards that appear in multiple decks together
        deck_card_sets = []
        
        for deck in self.decks:
            cards = set()
            
            if isinstance(deck, dict):
                for key in ['cards', 'mainboard', 'deck_list', 'cardlist']:
                    if key in deck:
                        deck_cards = deck[key]
                        if isinstance(deck_cards, dict):
                            cards.update(deck_cards.keys())
                        elif isinstance(deck_cards, list):
                            cards.update([c if isinstance(c, str) else c.get('name', '') for c in deck_cards if c])
                        break
            
            if cards:
                deck_card_sets.append(cards)
        
        # Find pairs of cards that appear together frequently
        combo_count = defaultdict(int)
        
        for deck_cards in deck_card_sets:
            card_list = sorted(list(deck_cards))
            for i in range(len(card_list)):
                for j in range(i + 1, min(i + 5, len(card_list))):
                    combo_key = (card_list[i], card_list[j])
                    combo_count[combo_key] += 1
        
        # Filter combos that appear in at least 2 decks
        for (card1, card2), count in sorted(combo_count.items(), key=lambda x: x[1], reverse=True):
            if count >= 2 and card1 and card2:
                self.card_combos.append({
                    "cards": [card1, card2],
                    "frequency": count,
                    "decks": count
                })
        
        logger.info(f"Found {len(self.card_combos)} card combos")
    
    def _categorize_archetypes(self):
        """Categorize decks by archetype based on card patterns."""
        # Simple archetype detection based on color and card patterns
        color_patterns = {
            'token': ['Doubling Season', 'Parallel Lives', 'Cathars\' Crusade', 'Ashnod\'s Altar'],
            'reanimator': ['Animate Dead', 'Necromancy', 'Dance of the Dead', 'Reanimate'],
            'control': ['Counterspell', 'Cancel', 'Mana Drain', 'Force of Will'],
            'aggro': ['Lightning Bolt', 'Goblin Guide', 'Earthshaker Khenra', 'Goblin Bushwhacker'],
            'combo': ['Artifact Tutor', 'Demonic Tutor', 'Imperial Tutor'],
        }
        
        for deck in self.decks:
            archetype = 'unknown'
            
            if isinstance(deck, dict):
                deck_name = deck.get('name', '').lower()
                
                # Check for archetype keywords in deck name
                for arch, keywords in color_patterns.items():
                    if any(keyword.lower() in deck_name for keyword in keywords):
                        archetype = arch
                        break
            
            self.deck_archetypes[archetype].append(deck)
    
    def _get_top_items(self, freq_dict: dict, n: int = 10) -> List[tuple]:
        """Get top N items from frequency dict."""
        return sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def _save_results(self) -> Path:
        """Save analysis results to JSON file."""
        output_path = self.output_dir / "deck_analysis"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Prepare top cards
        top_cards = self._get_top_items(self.cards_frequency, 1000)
        top_commanders = self._get_top_items(self.commander_frequency, 100)
        
        data = {
            "metadata": {
                "source": "Deck Analysis (TappedOut + Comprehensive)",
                "analyzed_at": datetime.now().isoformat(),
                "decks_analyzed": len(self.decks),
                "analysis_type": "Card frequency and combo detection"
            },
            "statistics": {
                "unique_cards": len(self.cards_frequency),
                "total_card_inclusions": sum(self.cards_frequency.values()),
                "unique_commanders": len(self.commander_frequency),
                "combos_found": len(self.card_combos),
                "archetypes": len(self.deck_archetypes)
            },
            "top_cards": [{"name": name, "frequency": freq} for name, freq in top_cards],
            "top_commanders": [{"name": name, "frequency": freq} for name, freq in top_commanders],
            "card_combos": self.card_combos[:500],  # Top 500 combos
            "archetypes": {arch: len(decks) for arch, decks in self.deck_archetypes.items()}
        }
        
        output_file = output_path / f"deck_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Analysis results saved to: {output_file}")
        return output_file


if __name__ == "__main__":
    analyzer = DeckAnalyzer()
    
    # Load deck data
    tappedout_file = "data_sources_comprehensive/tappedout/tappedout_20251204_071724.json"
    comp_decks_file = "data_sources_comprehensive/comprehensive_decks/comprehensive_decks_20251204_072058.json"
    
    if Path(tappedout_file).exists():
        analyzer.load_tappedout_decks(tappedout_file)
    
    if Path(comp_decks_file).exists():
        analyzer.load_comprehensive_decks(comp_decks_file)
    
    # Run analysis
    result = analyzer.analyze()
    
    if result["success"]:
        print(f"\n{'='*70}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*70}")
        print(f"✓ Output: {result['output_file']}")
        print(f"  Decks Analyzed: {result['counts']['decks_analyzed']}")
        print(f"  Unique Cards: {result['counts']['unique_cards']:,}")
        print(f"  Total Inclusions: {result['counts']['total_card_inclusions']:,}")
        print(f"  Unique Commanders: {result['counts']['unique_commanders']}")
        print(f"  Combos Found: {result['counts']['combos_found']}")
        print(f"  Archetypes: {result['counts']['archetypes']}")
    else:
        print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
