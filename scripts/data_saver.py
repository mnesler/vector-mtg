#!/usr/bin/env python3
"""
Robust data saving utility for EDHREC scraper.
This ensures data is always saved correctly with proper error handling.
"""

import json
import os
from pathlib import Path
from datetime import datetime


class EDHRecDataSaver:
    """Handles saving scraped data with robust error handling and verification."""
    
    def __init__(self, base_dir="/home/maxwell/vector-mtg/data_sources_comprehensive/edhrec_scraped"):
        """
        Initialize data saver.
        
        Args:
            base_dir: Base directory for saving scraped data
        """
        self.base_dir = Path(base_dir)
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure output directory exists with proper permissions."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self.base_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            print(f"✓ Output directory ready: {self.base_dir}")
        except Exception as e:
            print(f"✗ ERROR: Cannot write to {self.base_dir}")
            print(f"  Error: {e}")
            raise
    
    def save_commander_data(self, commander_url, cards, strategy="unknown", elapsed_time=0):
        """
        Save scraped commander data to JSON file.
        
        Args:
            commander_url: URL of the commander page
            cards: List of card dictionaries
            strategy: Scraping strategy used
            elapsed_time: Time taken to scrape
            
        Returns:
            Path to saved file, or None if failed
        """
        # Extract commander slug from URL
        try:
            commander_slug = commander_url.split('/commanders/')[-1].strip('/')
            if not commander_slug:
                commander_slug = "unknown_commander"
        except Exception as e:
            print(f"⚠ Warning: Could not extract commander slug from URL: {e}")
            commander_slug = "unknown_commander"
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{commander_slug}_{timestamp}.json"
        output_file = self.base_dir / filename
        
        # Prepare data structure
        data = {
            "metadata": {
                "commander_url": commander_url,
                "commander_slug": commander_slug,
                "strategy_used": strategy,
                "scraped_at": datetime.now().isoformat(),
                "elapsed_seconds": round(elapsed_time, 2),
                "total_cards": len(cards),
                "cards_with_synergy": sum(1 for c in cards if c.get('synergy')),
                "cards_with_type": sum(1 for c in cards if c.get('type')),
                "cards_with_url": sum(1 for c in cards if c.get('url'))
            },
            "cards": cards
        }
        
        # Save with error handling and verification
        print(f"\n{'='*70}")
        print(f"SAVING DATA")
        print(f"{'='*70}")
        print(f"Commander: {commander_slug}")
        print(f"Cards: {len(cards)}")
        print(f"Output: {output_file}")
        
        try:
            # Write to temporary file first
            temp_file = output_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Verify file was written
            if not temp_file.exists():
                raise IOError(f"Temporary file was not created: {temp_file}")
            
            file_size = temp_file.stat().st_size
            if file_size == 0:
                raise IOError("File was created but is empty (0 bytes)")
            
            # Verify JSON is valid by reading it back
            with open(temp_file, 'r', encoding='utf-8') as f:
                verified_data = json.load(f)
            
            if len(verified_data.get('cards', [])) != len(cards):
                raise ValueError(f"Card count mismatch: wrote {len(cards)}, read back {len(verified_data.get('cards', []))}")
            
            # Move temp file to final location (atomic operation)
            temp_file.replace(output_file)
            
            # Final verification
            if not output_file.exists():
                raise IOError(f"Final file does not exist after move: {output_file}")
            
            final_size = output_file.stat().st_size
            
            print(f"✓ Data saved successfully")
            print(f"  Path: {output_file}")
            print(f"  Size: {final_size / 1024:.1f} KB ({final_size:,} bytes)")
            print(f"  Cards: {len(cards)}")
            print(f"  Verified: JSON valid, card count matches")
            print(f"{'='*70}\n")
            
            return output_file
        
        except Exception as e:
            print(f"✗ ERROR saving data: {e}")
            print(f"  Error type: {type(e).__name__}")
            
            # Try to clean up temp file
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    print(f"  Cleaned up temporary file")
            except:
                pass
            
            # Try to save to backup location
            try:
                backup_dir = Path("/tmp/edhrec_scraped_backup")
                backup_dir.mkdir(exist_ok=True)
                backup_file = backup_dir / filename
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                print(f"⚠ Data saved to BACKUP location: {backup_file}")
                return backup_file
            
            except Exception as backup_error:
                print(f"✗ Backup save also failed: {backup_error}")
                print(f"  Data is LOST - returning in-memory only")
                return None
    
    def list_saved_files(self):
        """List all saved commander files."""
        try:
            files = sorted(self.base_dir.glob("*.json"))
            if files:
                print(f"\nSaved files in {self.base_dir}:")
                for f in files:
                    size_kb = f.stat().st_size / 1024
                    print(f"  - {f.name} ({size_kb:.1f} KB)")
            else:
                print(f"\nNo files found in {self.base_dir}")
            return files
        except Exception as e:
            print(f"✗ Error listing files: {e}")
            return []


def test_saver():
    """Test the data saver with sample data."""
    print("="*70)
    print("TESTING EDHREC DATA SAVER")
    print("="*70)
    
    # Create saver
    saver = EDHRecDataSaver()
    
    # Sample data
    sample_url = "https://edhrec.com/commanders/atraxa-praetors-voice"
    sample_cards = [
        {"name": "Doubling Season", "url": "https://edhrec.com/cards/doubling-season", "synergy": "32%", "type": "Enchantment"},
        {"name": "Winding Constrictor", "url": "https://edhrec.com/cards/winding-constrictor", "synergy": "28%", "type": "Creature"},
        {"name": "Corpsejack Menace", "url": "https://edhrec.com/cards/corpsejack-menace", "synergy": "27%", "type": "Creature"},
    ]
    
    # Save data
    saved_file = saver.save_commander_data(
        commander_url=sample_url,
        cards=sample_cards,
        strategy="test",
        elapsed_time=1.23
    )
    
    if saved_file:
        print(f"✓ TEST PASSED: File saved to {saved_file}")
        
        # Verify we can read it back
        with open(saved_file, 'r') as f:
            loaded_data = json.load(f)
        
        print(f"✓ TEST PASSED: File can be read back")
        print(f"  Cards in file: {len(loaded_data['cards'])}")
        print(f"  Metadata present: {bool(loaded_data.get('metadata'))}")
        
        # Show first card
        if loaded_data['cards']:
            print(f"\nFirst card in file:")
            print(f"  {json.dumps(loaded_data['cards'][0], indent=4)}")
        
        return True
    else:
        print(f"✗ TEST FAILED: Could not save file")
        return False


if __name__ == "__main__":
    success = test_saver()
    exit(0 if success else 1)
