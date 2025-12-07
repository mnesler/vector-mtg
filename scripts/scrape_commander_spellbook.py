#!/usr/bin/env python3
"""
Commander Spellbook API scraper - fetches complete combo data.

This scraper uses the official Commander Spellbook REST API to download
all 72K+ combo variants with complete data including:
- Card names and zones
- Results (what the combo achieves)
- Prerequisites (setup requirements)
- Steps (detailed description)
- Legalities, prices, popularity

API Documentation: https://backend.commanderspellbook.com/
"""

import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class CommanderSpellbookScraper:
    """Scraper for Commander Spellbook REST API."""
    
    BASE_URL = "https://backend.commanderspellbook.com"
    
    def __init__(self, output_dir: str = "commander_spellbook_data"):
        """Initialize scraper.
        
        Args:
            output_dir: Directory to save combo data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MTG-Vector-DB-Scraper/1.0'
        })
        
    def fetch_combos(self, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch combos from API with pagination.
        
        Args:
            limit: Number of combos per request
            offset: Starting position
            
        Returns:
            API response dict with 'count', 'results', 'next', 'previous'
        """
        url = f"{self.BASE_URL}/variants/"
        params = {'limit': limit, 'offset': offset}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching combos: {e}")
            return None
            
    def scrape_all(self, batch_size: int = 100, max_combos: Optional[int] = None,
                   save_interval: int = 1000) -> List[Dict[str, Any]]:
        """Scrape all combos from the API with progress tracking.
        
        Args:
            batch_size: Number of combos per API request
            max_combos: Maximum combos to fetch (None = all)
            save_interval: Save progress every N combos
            
        Returns:
            List of all combo data
        """
        all_combos = []
        offset = 0
        total_count = None
        start_time = time.time()
        
        print("Starting Commander Spellbook API scrape...")
        print(f"Batch size: {batch_size}")
        
        while True:
            # Fetch batch
            print(f"\nFetching combos {offset + 1}-{offset + batch_size}...", end=" ", flush=True)
            data = self.fetch_combos(limit=batch_size, offset=offset)
            
            if not data or 'results' not in data:
                print("ERROR: No data received")
                break
                
            # Get total count on first request
            if total_count is None:
                total_count = data['count']
                print(f"\nTotal combos available: {total_count:,}")
                if max_combos:
                    print(f"Will fetch maximum: {max_combos:,}")
                    
            # Add combos to collection
            combos = data['results']
            all_combos.extend(combos)
            print(f"✓ Got {len(combos)} combos")
            
            # Progress stats
            elapsed = time.time() - start_time
            combos_per_sec = len(all_combos) / elapsed if elapsed > 0 else 0
            print(f"Progress: {len(all_combos):,}/{total_count:,} ({len(all_combos)/total_count*100:.1f}%) | "
                  f"Rate: {combos_per_sec:.1f} combos/sec | "
                  f"Elapsed: {elapsed:.0f}s")
            
            # Save progress periodically
            if len(all_combos) % save_interval == 0:
                self._save_progress(all_combos, len(all_combos))
                
            # Check stopping conditions
            if max_combos and len(all_combos) >= max_combos:
                print(f"\nReached maximum combo limit: {max_combos}")
                break
                
            if not data['next']:
                print(f"\nReached end of data")
                break
                
            # Move to next batch
            offset += batch_size
            
            # Rate limiting - be nice to the API
            time.sleep(0.5)
            
        # Final save
        print(f"\n{'='*80}")
        print(f"Scrape complete!")
        print(f"Total combos fetched: {len(all_combos):,}")
        print(f"Total time: {time.time() - start_time:.1f}s")
        
        return all_combos
        
    def _save_progress(self, combos: List[Dict[str, Any]], count: int):
        """Save progress to file.
        
        Args:
            combos: List of combo data
            count: Number of combos (for filename)
        """
        filename = self.output_dir / f"combos_progress_{count}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(combos, f, indent=2)
            print(f"  💾 Progress saved: {filename}")
        except Exception as e:
            print(f"  ⚠️  Failed to save progress: {e}")
            
    def save_combos(self, combos: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """Save combos to JSON file.
        
        Args:
            combos: List of combo data
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"commander_spellbook_combos_{timestamp}.json"
            
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(combos, f, indent=2)
            
        print(f"\n✓ Saved {len(combos):,} combos to: {filepath}")
        print(f"  File size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
        
        return filepath
        
    def generate_summary(self, combos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for scraped combos.
        
        Args:
            combos: List of combo data
            
        Returns:
            Summary dict with statistics
        """
        if not combos:
            return {}
            
        # Color identity distribution
        color_counts = {}
        for combo in combos:
            identity = combo.get('identity', 'C')
            color_counts[identity] = color_counts.get(identity, 0) + 1
            
        # Result distribution (top 20)
        result_counts = {}
        for combo in combos:
            for result in combo.get('produces', []):
                name = result['feature']['name']
                result_counts[name] = result_counts.get(name, 0) + 1
                
        top_results = sorted(result_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Cards used (top 20)
        card_counts = {}
        for combo in combos:
            for use in combo.get('uses', []):
                name = use['card']['name']
                card_counts[name] = card_counts.get(name, 0) + 1
                
        top_cards = sorted(card_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Legality stats
        legality_counts = {
            'commander': 0,
            'vintage': 0,
            'legacy': 0,
            'modern': 0,
            'pioneer': 0,
            'standard': 0
        }
        
        for combo in combos:
            for format_name in legality_counts.keys():
                if combo.get('legalities', {}).get(format_name, False):
                    legality_counts[format_name] += 1
                    
        summary = {
            'total_combos': len(combos),
            'timestamp': datetime.now().isoformat(),
            'color_distribution': dict(sorted(color_counts.items(), key=lambda x: x[1], reverse=True)),
            'top_results': [{'name': name, 'count': count} for name, count in top_results],
            'top_cards': [{'name': name, 'count': count} for name, count in top_cards],
            'legality_counts': legality_counts,
            'avg_cards_per_combo': sum(len(c.get('uses', [])) for c in combos) / len(combos),
            'avg_results_per_combo': sum(len(c.get('produces', [])) for c in combos) / len(combos),
        }
        
        return summary
        
    def save_summary(self, combos: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """Generate and save summary statistics.
        
        Args:
            combos: List of combo data
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved summary file
        """
        summary = self.generate_summary(combos)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.json"
            
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n✓ Summary saved to: {filepath}")
        
        # Print summary to console
        print(f"\n{'='*80}")
        print("SUMMARY STATISTICS")
        print(f"{'='*80}")
        print(f"Total combos: {summary['total_combos']:,}")
        print(f"Avg cards per combo: {summary['avg_cards_per_combo']:.2f}")
        print(f"Avg results per combo: {summary['avg_results_per_combo']:.2f}")
        
        print(f"\nTop 10 Color Identities:")
        for color, count in list(summary['color_distribution'].items())[:10]:
            print(f"  {color:6s}: {count:6,} combos")
            
        print(f"\nTop 10 Results:")
        for result in summary['top_results'][:10]:
            print(f"  {result['name']:40s}: {result['count']:6,} combos")
            
        print(f"\nTop 10 Cards:")
        for card in summary['top_cards'][:10]:
            print(f"  {card['name']:40s}: {card['count']:6,} combos")
            
        print(f"\nLegality Counts:")
        for format_name, count in summary['legality_counts'].items():
            print(f"  {format_name:15s}: {count:6,} combos")
        
        return filepath


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Commander Spellbook API")
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of combos to fetch (default: all)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of combos per API request (default: 100)')
    parser.add_argument('--output-dir', type=str, default='commander_spellbook_data',
                       help='Output directory (default: commander_spellbook_data)')
    parser.add_argument('--save-interval', type=int, default=1000,
                       help='Save progress every N combos (default: 1000)')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = CommanderSpellbookScraper(output_dir=args.output_dir)
    
    # Scrape combos
    combos = scraper.scrape_all(
        batch_size=args.batch_size,
        max_combos=args.limit,
        save_interval=args.save_interval
    )
    
    if combos:
        # Save final data
        scraper.save_combos(combos)
        scraper.save_summary(combos)
    else:
        print("No combos fetched!")
        sys.exit(1)


if __name__ == '__main__':
    main()
