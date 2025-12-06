#!/usr/bin/env python3
"""
Data Merger: Combine and deduplicate all collected data sources.
Merges Scryfall, EDHREC, TappedOut, Moxfield, and other sources into a unified database.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMerger:
    """Merge and deduplicate data from multiple sources."""
    
    def __init__(self, output_dir: str = "data_sources_comprehensive"):
        """Initialize the data merger."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.all_cards = {}  # {card_id: card_data}
        self.all_decks = []
        self.all_commanders = set()
        self.source_stats = defaultdict(int)
        
    def merge_all(self) -> Dict[str, Any]:
        """Run full merge process."""
        print("\n" + "=" * 70)
        print("DATA MERGER - COMBINING ALL SOURCES")
        print("=" * 70)
        
        print("\nPhase 1: Loading Scryfall database...")
        self._load_scryfall()
        
        print("Phase 2: Loading additional card sources...")
        self._load_additional_cards()
        
        print("Phase 3: Loading deck data...")
        self._load_decks()
        
        print("Phase 4: Extracting commanders...")
        self._extract_commanders()
        
        print("Phase 5: Generating statistics...")
        stats = self._generate_statistics()
        
        print("Phase 6: Saving merged data...")
        output_files = self._save_merged_data()
        
        return {
            "success": True,
            "output_files": output_files,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def _load_scryfall(self):
        """Load Scryfall default cards database."""
        scryfall_file = self.output_dir / "scryfall_bulk" / "scryfall_default_cards_20251204.json"
        
        if not scryfall_file.exists():
            logger.warning(f"Scryfall file not found: {scryfall_file}")
            return
        
        try:
            with open(scryfall_file) as f:
                cards = json.load(f)
            
            for card in cards:
                card_id = card.get('id') or card.get('name', 'unknown').lower()
                self.all_cards[card_id] = card
                self.source_stats['scryfall'] += 1
            
            logger.info(f"✓ Loaded {len(cards):,} cards from Scryfall")
        except Exception as e:
            logger.error(f"Error loading Scryfall: {e}")
    
    def _load_additional_cards(self):
        """Load cards from other sources (EDHREC queries, etc.)."""
        card_sources = [
            self.output_dir / "scryfall" / "scryfall_edh_20251204_072151.json",
            self.output_dir / "edhrec_comprehensive" / "edhrec_comprehensive_20251204_072055.json",
        ]
        
        for filepath in card_sources:
            if not filepath.exists():
                continue
            
            try:
                with open(filepath) as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    # Direct list of cards
                    for card in data:
                        if isinstance(card, dict):
                            card_id = card.get('id') or card.get('name', '').lower()
                            if card_id and card_id not in self.all_cards:
                                self.all_cards[card_id] = card
                                self.source_stats[filepath.parent.name] += 1
                
                elif isinstance(data, dict):
                    # Handle nested structures
                    if 'cards_by_commander' in data:
                        # EDHREC comprehensive format
                        for commander, cards in data.get('cards_by_commander', {}).items():
                            if isinstance(cards, list):
                                for card in cards:
                                    if isinstance(card, dict):
                                        card_name = card.get('name', '').lower()
                                        if card_name and card_name not in self.all_cards:
                                            self.all_cards[card_name] = card
                                            self.source_stats['edhrec'] += 1
            
            except Exception as e:
                logger.debug(f"Error loading {filepath}: {e}")
    
    def _load_decks(self):
        """Load deck data from TappedOut and other sources."""
        deck_sources = [
            (self.output_dir / "tappedout" / "tappedout_20251204_071724.json", "tappedout"),
            (self.output_dir / "comprehensive_decks" / "comprehensive_decks_20251204_072058.json", "comprehensive"),
        ]
        
        for filepath, source in deck_sources:
            if not filepath.exists():
                continue
            
            try:
                with open(filepath) as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    self.all_decks.extend(data)
                    self.source_stats[source] += len(data)
                
                elif isinstance(data, dict):
                    if 'decks' in data:
                        decks = data['decks']
                        self.all_decks.extend(decks)
                        self.source_stats[source] += len(decks)
            
            except Exception as e:
                logger.debug(f"Error loading {filepath}: {e}")
    
    def _extract_commanders(self):
        """Extract commander names from various sources."""
        # From comprehensive decks
        comp_decks_file = self.output_dir / "comprehensive_decks" / "comprehensive_decks_20251204_072058.json"
        if comp_decks_file.exists():
            try:
                with open(comp_decks_file) as f:
                    data = json.load(f)
                    for deck in data.get('decks', []):
                        if isinstance(deck, dict) and 'commander_name' in deck:
                            cmd = deck['commander_name']
                            if cmd:
                                self.all_commanders.add(cmd)
            except Exception as e:
                logger.debug(f"Error extracting commanders: {e}")
        
        # From EDHREC
        edhrec_file = self.output_dir / "edhrec_comprehensive" / "edhrec_comprehensive_20251204_072055.json"
        if edhrec_file.exists():
            try:
                with open(edhrec_file) as f:
                    data = json.load(f)
                    for cmd in data.get('commanders', []):
                        if isinstance(cmd, dict) and 'name' in cmd:
                            self.all_commanders.add(cmd['name'])
            except Exception as e:
                logger.debug(f"Error extracting EDHREC commanders: {e}")
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive statistics."""
        # Count cards by type
        card_types = defaultdict(int)
        edh_legal_count = 0
        edh_banned_count = 0
        
        for card in self.all_cards.values():
            if isinstance(card, dict):
                # Count by type
                card_type = card.get('type_line', 'Unknown')
                card_types[card_type] += 1
                
                # Count EDH legality
                legalities = card.get('legalities', {})
                if legalities.get('commander') == 'legal':
                    edh_legal_count += 1
                elif legalities.get('commander') == 'banned':
                    edh_banned_count += 1
        
        # Get top card types
        top_types = sorted(card_types.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_unique_cards": len(self.all_cards),
            "edh_legal_cards": edh_legal_count,
            "edh_banned_cards": edh_banned_count,
            "total_decks": len(self.all_decks),
            "total_commanders": len(self.all_commanders),
            "top_card_types": [{"type": t, "count": c} for t, c in top_types],
            "source_breakdown": dict(self.source_stats)
        }
    
    def _save_merged_data(self) -> Dict[str, str]:
        """Save merged data to files."""
        output_files = {}
        merge_dir = self.output_dir / "merged_data"
        merge_dir.mkdir(parents=True, exist_ok=True)
        
        # Save cards
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. EDH legal cards only
        edh_cards = {}
        for card_id, card in self.all_cards.items():
            if isinstance(card, dict):
                legalities = card.get('legalities', {})
                if legalities.get('commander') == 'legal':
                    edh_cards[card_id] = card
        
        edh_file = merge_dir / f"edh_legal_cards_{timestamp}.json"
        with open(edh_file, 'w') as f:
            json.dump(list(edh_cards.values()), f)
        output_files['edh_cards'] = str(edh_file)
        logger.info(f"✓ Saved {len(edh_cards):,} EDH legal cards to {edh_file.name}")
        
        # 2. All merged cards (with metadata)
        all_cards_file = merge_dir / f"all_merged_cards_{timestamp}.json"
        with open(all_cards_file, 'w') as f:
            json.dump({
                "metadata": {
                    "total_cards": len(self.all_cards),
                    "merged_at": datetime.now().isoformat(),
                    "sources": list(set(self.source_stats.keys()))
                },
                "cards": list(self.all_cards.values())
            }, f)
        output_files['all_cards'] = str(all_cards_file)
        logger.info(f"✓ Saved {len(self.all_cards):,} merged cards to {all_cards_file.name}")
        
        # 3. Decks
        decks_file = merge_dir / f"merged_decks_{timestamp}.json"
        with open(decks_file, 'w') as f:
            json.dump({
                "metadata": {
                    "total_decks": len(self.all_decks),
                    "merged_at": datetime.now().isoformat()
                },
                "decks": self.all_decks
            }, f)
        output_files['decks'] = str(decks_file)
        logger.info(f"✓ Saved {len(self.all_decks)} decks to {decks_file.name}")
        
        # 4. Commanders
        commanders_file = merge_dir / f"merged_commanders_{timestamp}.json"
        with open(commanders_file, 'w') as f:
            json.dump({
                "metadata": {
                    "total_commanders": len(self.all_commanders),
                    "merged_at": datetime.now().isoformat()
                },
                "commanders": sorted(list(self.all_commanders))
            }, f)
        output_files['commanders'] = str(commanders_file)
        logger.info(f"✓ Saved {len(self.all_commanders)} commanders to {commanders_file.name}")
        
        # 5. Master index
        master_file = merge_dir / f"master_index_{timestamp}.json"
        with open(master_file, 'w') as f:
            json.dump({
                "metadata": {
                    "merged_at": datetime.now().isoformat(),
                    "total_cards": len(self.all_cards),
                    "edh_legal_cards": sum(1 for c in self.all_cards.values() 
                                          if isinstance(c, dict) and 
                                          c.get('legalities', {}).get('commander') == 'legal'),
                    "total_decks": len(self.all_decks),
                    "total_commanders": len(self.all_commanders)
                },
                "files": output_files
            }, f)
        output_files['master'] = str(master_file)
        logger.info(f"✓ Created master index at {master_file.name}")
        
        return output_files


if __name__ == "__main__":
    merger = DataMerger()
    result = merger.merge_all()
    
    if result["success"]:
        print(f"\n{'='*70}")
        print("MERGE COMPLETE")
        print(f"{'='*70}\n")
        
        stats = result['statistics']
        print("STATISTICS:")
        print(f"  Total Unique Cards: {stats['total_unique_cards']:,}")
        print(f"  EDH Legal Cards: {stats['edh_legal_cards']:,}")
        print(f"  EDH Banned Cards: {stats['edh_banned_cards']:,}")
        print(f"  Total Decks: {stats['total_decks']}")
        print(f"  Total Commanders: {stats['total_commanders']}")
        
        print(f"\nSOURCE BREAKDOWN:")
        for source, count in sorted(stats['source_breakdown'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count:,}")
        
        print(f"\nOUTPUT FILES:")
        for name, filepath in result['output_files'].items():
            size_kb = Path(filepath).stat().st_size / 1024
            print(f"  {name}: {filepath} ({size_kb:.1f} KB)")
    else:
        print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
