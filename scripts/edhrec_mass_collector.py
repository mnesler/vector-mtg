#!/usr/bin/env python3
"""
EDHREC Mass Collector: Collect comprehensive EDHREC data using pyedhrec library.
Features:
- Checkpoint/resume capability
- Rate limiting to respect servers
- Progress tracking
- Full commander data extraction (cards, combos, decklists)
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from pyedhrec import EDHRec

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EDHRecMassCollector:
    """Collect comprehensive EDHREC data with checkpointing."""
    
    # Popular commanders to start with (for Phase 1 test)
    POPULAR_COMMANDERS = [
        "Krenko, Mob Boss",
        "The Ur-Dragon",
        "Golos, Tireless Pilgrim",
        "Omnath, Locus of Creation",
        "Atraxa, Praetors' Voice",
        "Edgar Markov",
        "Korvold, Fae-Cursed King",
        "Ghired, Conclave Exile",
        "Prosper, Tomb-Bound",
        "Muldrotha, the Gravetide",
        "Yarok, the Desecrated",
        "Uro, Titan of Nature's Wrath",
        "Teysa Karlov",
        "The Scarab God",
        "Breya, Etherium Shaper",
        "Zur the Enchanter",
        "Gisela, Blade of Goldnight",
        "Kaalia of the Vast",
        "Lord Windgrace",
        "Najeela, the Blade-Reborn",
        "Teysa Karlov",
        "Vial Smasher the Fierce",
        "Xyris, the Writhing Storm",
        "Feather, the Redeemed",
        "Selvala, Heart of the Wilds",
        "Chulane, Teller of Tales",
        "Sisay, Weatherlight Captain",
        "Golos, Tireless Pilgrim",
        "Esper Sentinel",
        "Dina, Soul Steeper",
        "Kroxa, Titan of Death's Hunger",
        "Torbran, Thane of Red Fell",
        "Ardenn, Intrepid Archaeologist",
        "Siona, Captain of the Pylkos",
        "Kels, Fight with Your Friends",
        "Yavimaya, Cradle of Growth",
        "Chatterfang, Squirrel General",
        "Archelos, Lagoon Mystic",
        "Obuun, Mul Daya Ancestor",
        "Surrak Dragonclaw",
        "Kess, Dissident Mage",
        "Maralen of the Mornsong",
        "Olivia Voldaren",
        "Prossh, Skyraider of Kher",
        "Garza Zol, Plague Queen",
        "Lavinia, Azorius Renegade",
        "Aluren",
        "Craterhoof Behemoth",
        "Ulamog, the Ceaseless Hunger",
        "Yidris, Maelstrom Wielder",
    ]
    
    def __init__(self, output_dir: str = "data_sources_comprehensive", phase_size: int = 50):
        """
        Initialize the collector.
        
        Args:
            output_dir: Base output directory
            phase_size: Number of commanders to process in Phase 1 (test)
        """
        self.output_dir = Path(output_dir)
        self.edhrec_dir = self.output_dir / "edhrec"
        self.edhrec_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = EDHRec()
        self.phase_size = phase_size
        
        # Data storage
        self.commanders_data = []
        self.all_cards = {}
        self.all_combos = {}
        self.all_decks = {}
        
        # Stats
        self.stats = {
            "commanders_processed": 0,
            "total_cards_found": 0,
            "total_combos_found": 0,
            "total_decklists_found": 0,
            "errors": 0,
        }
        
        # Checkpoint
        self.checkpoint_file = self.edhrec_dir / "checkpoint.json"
        self.processed_commanders = set()
        
    def load_checkpoint(self):
        """Load checkpoint to resume from previous run."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file) as f:
                    data = json.load(f)
                self.processed_commanders = set(data.get("processed", []))
                logger.info(f"✓ Loaded checkpoint: {len(self.processed_commanders)} commanders already processed")
                return True
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}")
        return False
    
    def save_checkpoint(self):
        """Save checkpoint for resumability."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    "processed": list(self.processed_commanders),
                    "timestamp": datetime.now().isoformat(),
                    "stats": self.stats
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def collect_phase_1(self):
        """Phase 1: Collect data for popular commanders (test run)."""
        print("\n" + "="*70)
        print("PHASE 1: POPULAR COMMANDERS TEST RUN")
        print("="*70)
        
        commanders_to_process = [c for c in self.POPULAR_COMMANDERS[:self.phase_size] 
                                if c not in self.processed_commanders]
        
        logger.info(f"Processing {len(commanders_to_process)} popular commanders...")
        
        return self._process_commanders(commanders_to_process)
    
    def collect_phase_2(self):
        """Phase 2: Collect all commanders from EDHREC."""
        print("\n" + "="*70)
        print("PHASE 2: FULL EDHREC COMMANDER DATABASE")
        print("="*70)
        
        logger.info("Fetching all commanders from EDHREC...")
        
        try:
            # Get all commanders by querying main commanders page
            all_commanders = self._discover_all_commanders()
            logger.info(f"✓ Found {len(all_commanders)} total commanders")
            
            # Filter out already processed
            commanders_to_process = [c for c in all_commanders 
                                    if c not in self.processed_commanders]
            
            logger.info(f"Processing {len(commanders_to_process)} remaining commanders...")
            
            return self._process_commanders(commanders_to_process)
        
        except Exception as e:
            logger.error(f"Error discovering commanders: {e}")
            self.stats["errors"] += 1
            return False
    
    def _discover_all_commanders(self) -> List[str]:
        """Discover all commanders by querying EDHREC."""
        # Strategy: Use pyedhrec to query popular commanders and build from there
        # For now, return known commanders - a full discovery would require
        # scraping EDHREC's commander list page
        
        known_commanders = [
            "Krenko, Mob Boss",
            "The Ur-Dragon",
            "Golos, Tireless Pilgrim",
            "Omnath, Locus of Creation",
            "Atraxa, Praetors' Voice",
            "Edgar Markov",
            "Korvold, Fae-Cursed King",
            "Ghired, Conclave Exile",
            "Prosper, Tomb-Bound",
            # Add more popular ones...
        ]
        
        return known_commanders
    
    def _process_commanders(self, commanders: List[str]) -> bool:
        """Process a list of commanders."""
        success_count = 0
        
        for idx, commander_name in enumerate(commanders, 1):
            if commander_name in self.processed_commanders:
                logger.debug(f"Skipping {commander_name} (already processed)")
                continue
            
            print(f"\n[{idx}/{len(commanders)}] Processing: {commander_name}")
            
            try:
                cmd_data = self._collect_commander_data(commander_name)
                self.commanders_data.append(cmd_data)
                self.processed_commanders.add(commander_name)
                self.stats["commanders_processed"] += 1
                success_count += 1
                
                # Progress indicator
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{len(commanders)} - "
                               f"Found {self.stats['total_cards_found']} cards total")
                    self.save_checkpoint()
                
                # Rate limiting: be respectful to EDHREC servers
                time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error processing {commander_name}: {e}")
                self.stats["errors"] += 1
            
            # Save checkpoint periodically
            if idx % 25 == 0:
                self.save_checkpoint()
        
        logger.info(f"✓ Processed {success_count} commanders successfully")
        self.save_checkpoint()
        return success_count > 0
    
    def _collect_commander_data(self, commander_name: str) -> Dict[str, Any]:
        """Collect comprehensive data for a single commander."""
        logger.debug(f"Collecting data for: {commander_name}")
        
        cmd_data = {
            "name": commander_name,
            "collected_at": datetime.now().isoformat(),
            "cards": {},
            "combos": [],
            "decks": [],
        }
        
        try:
            # Get commander data
            commander_data = self.client.get_commander_data(commander_name)
            if commander_data:
                cmd_data["metadata"] = commander_data
                logger.debug(f"  ✓ Got commander data")
            
            # Get all card recommendations
            top_cards = self.client.get_top_cards(commander_name)
            if top_cards:
                cmd_data["cards"]["top_cards"] = top_cards
                self.stats["total_cards_found"] += len(top_cards)
                logger.debug(f"  ✓ Got {len(top_cards)} top cards")
                
                # Store in global index
                for card in top_cards:
                    if isinstance(card, dict):
                        card_name = card.get('name') or card.get('card_name', '')
                        if card_name and card_name not in self.all_cards:
                            self.all_cards[card_name] = card
            
            # Get cards by type
            type_methods = [
                ('creatures', self.client.get_top_creatures),
                ('instants', self.client.get_top_instants),
                ('sorceries', self.client.get_top_sorceries),
                ('enchantments', self.client.get_top_enchantments),
                ('artifacts', self.client.get_top_artifacts),
                ('planeswalkers', self.client.get_top_planeswalkers),
                ('lands', self.client.get_top_lands),
            ]
            
            for type_name, method in type_methods:
                try:
                    cards = method(commander_name)
                    if cards:
                        cmd_data["cards"][type_name] = cards
                        logger.debug(f"  ✓ Got {len(cards)} {type_name}")
                        
                        for card in cards:
                            if isinstance(card, dict):
                                card_name = card.get('name') or card.get('card_name', '')
                                if card_name and card_name not in self.all_cards:
                                    self.all_cards[card_name] = card
                except Exception as e:
                    logger.debug(f"  Could not get {type_name}: {e}")
            
            # Get combos
            try:
                combos = self.client.get_card_combos(commander_name)
                if combos:
                    cmd_data["combos"] = combos
                    self.stats["total_combos_found"] += len(combos)
                    logger.debug(f"  ✓ Got {len(combos)} combos")
                    
                    for combo in combos:
                        combo_key = str(combo)
                        if combo_key not in self.all_combos:
                            self.all_combos[combo_key] = combo
            except Exception as e:
                logger.debug(f"  Could not get combos: {e}")
            
            # Get known decklists
            try:
                decks = self.client.get_commander_decks(commander_name)
                if decks:
                    cmd_data["decks"] = decks
                    self.stats["total_decklists_found"] += len(decks)
                    logger.debug(f"  ✓ Got {len(decks)} known decklists")
            except Exception as e:
                logger.debug(f"  Could not get decklists: {e}")
            
            # Get average decklist
            try:
                avg_deck = self.client.get_commanders_average_deck(commander_name)
                if avg_deck:
                    cmd_data["average_deck"] = avg_deck
                    logger.debug(f"  ✓ Got average decklist")
            except Exception as e:
                logger.debug(f"  Could not get average deck: {e}")
        
        except Exception as e:
            logger.error(f"Error collecting data for {commander_name}: {e}")
            self.stats["errors"] += 1
        
        return cmd_data
    
    def save_results(self, phase: str = "1") -> Dict[str, str]:
        """Save collected data to files."""
        output_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save commanders data
        commanders_file = self.edhrec_dir / f"edhrec_commanders_phase{phase}_{timestamp}.json"
        with open(commanders_file, 'w') as f:
            json.dump({
                "metadata": {
                    "phase": phase,
                    "collected_at": datetime.now().isoformat(),
                    "total_commanders": len(self.commanders_data),
                    "statistics": self.stats
                },
                "commanders": self.commanders_data
            }, f, indent=2)
        output_files["commanders"] = str(commanders_file)
        logger.info(f"✓ Saved {len(self.commanders_data)} commanders to {commanders_file.name}")
        
        # Save all unique cards
        cards_file = self.edhrec_dir / f"edhrec_cards_phase{phase}_{timestamp}.json"
        with open(cards_file, 'w') as f:
            json.dump({
                "metadata": {
                    "phase": phase,
                    "collected_at": datetime.now().isoformat(),
                    "total_cards": len(self.all_cards)
                },
                "cards": list(self.all_cards.values())
            }, f)
        output_files["cards"] = str(cards_file)
        logger.info(f"✓ Saved {len(self.all_cards)} unique cards to {cards_file.name}")
        
        # Save combos
        if self.all_combos:
            combos_file = self.edhrec_dir / f"edhrec_combos_phase{phase}_{timestamp}.json"
            with open(combos_file, 'w') as f:
                json.dump({
                    "metadata": {
                        "phase": phase,
                        "collected_at": datetime.now().isoformat(),
                        "total_combos": len(self.all_combos)
                    },
                    "combos": list(self.all_combos.values())
                }, f, indent=2)
            output_files["combos"] = str(combos_file)
            logger.info(f"✓ Saved {len(self.all_combos)} combos to {combos_file.name}")
        
        return output_files
    
    def print_summary(self, phase: str = "1"):
        """Print collection summary."""
        print("\n" + "="*70)
        print(f"PHASE {phase} COLLECTION SUMMARY")
        print("="*70)
        
        print(f"\n📊 STATISTICS:")
        print(f"  Commanders Processed: {self.stats['commanders_processed']}")
        print(f"  Total Cards Found: {self.stats['total_cards_found']:,}")
        print(f"  Total Combos Found: {self.stats['total_combos_found']:,}")
        print(f"  Total Decklists Found: {self.stats['total_decklists_found']:,}")
        print(f"  Errors: {self.stats['errors']}")
        
        print(f"\n💾 UNIQUE ITEMS:")
        print(f"  Unique Cards: {len(self.all_cards):,}")
        print(f"  Unique Combos: {len(self.all_combos):,}")


if __name__ == "__main__":
    import sys
    
    # Determine which phase to run
    phase = sys.argv[1] if len(sys.argv) > 1 else "1"
    phase_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    collector = EDHRecMassCollector(phase_size=phase_size)
    collector.load_checkpoint()
    
    if phase == "1":
        success = collector.collect_phase_1()
        collector.save_results("1")
        collector.print_summary("1")
    
    elif phase == "2":
        success = collector.collect_phase_2()
        collector.save_results("2")
        collector.print_summary("2")
    
    else:
        print("Usage: python edhrec_mass_collector.py [phase] [phase_size]")
        print("  phase: 1 (popular commanders test) or 2 (full collection)")
        print("  phase_size: number of commanders for phase 1 (default: 50)")
