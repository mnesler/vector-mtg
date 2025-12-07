#!/usr/bin/env python3
"""
Enrich existing combo JSON files with detailed card data from EDHREC API.

Usage:
    python scripts/enrich_combos_with_card_data.py <combo_file.json> [--delay=2]
    
Example:
    python scripts/enrich_combos_with_card_data.py edhrec_combos_detailed_20251206_171119/mono-white.json
"""

import json
import sys
import argparse
import time
import re
from datetime import datetime
from tqdm import tqdm
import os
import requests

# Global card cache
CARD_CACHE = {}
RATE_LIMIT_FILE = "edhrec_rate_limit_enrich.json"

def wait_for_rate_limit(delay_seconds=2.0):
    """Enforce minimum delay between requests"""
    if not os.path.exists(RATE_LIMIT_FILE):
        rate_data = {
            'last_request_time': datetime.now().isoformat(),
            'requests_count': 1
        }
        with open(RATE_LIMIT_FILE, 'w') as f:
            json.dump(rate_data, f, indent=2)
        return
    
    with open(RATE_LIMIT_FILE, 'r') as f:
        data = json.load(f)
    
    last_time = datetime.fromisoformat(data['last_request_time'])
    elapsed = (datetime.now() - last_time).total_seconds()
    
    if elapsed < delay_seconds:
        wait_time = delay_seconds - elapsed
        time.sleep(wait_time)
    
    rate_data = {
        'last_request_time': datetime.now().isoformat(),
        'requests_count': data.get('requests_count', 0) + 1
    }
    with open(RATE_LIMIT_FILE, 'w') as f:
        json.dump(rate_data, f, indent=2)


def clean_card_name(name):
    """Remove prices and artifacts from card names"""
    name = re.sub(r'\$[\d.,]+', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def slugify_card_name(name):
    """Convert card name to EDHREC URL slug"""
    cleaned = clean_card_name(name)
    slug = cleaned.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def fetch_card_details(card_name, delay_seconds=2.0):
    """Fetch card data from EDHREC API with caching"""
    if card_name in CARD_CACHE:
        return CARD_CACHE[card_name]
    
    slug = slugify_card_name(card_name)
    url = f"https://json.edhrec.com/cards/{slug}"
    
    try:
        wait_for_rate_limit(delay_seconds)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            card_data = response.json()
            CARD_CACHE[card_name] = card_data
            return card_data
        elif response.status_code == 404:
            CARD_CACHE[card_name] = None
            return None
        else:
            return None
    except Exception as e:
        print(f"  Error fetching {card_name}: {e}")
        return None


def enrich_combo_file(input_file, output_file=None, delay_seconds=2.0, skip_existing=True):
    """Enrich a combo JSON file with card details"""
    print(f"Reading: {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    combos = data.get('combos', [])
    print(f"Found {len(combos)} combos")
    
    # Collect unique card names
    unique_cards = set()
    for combo in combos:
        for card in combo.get('cards', []):
            card_name = card.get('name')
            if card_name:
                if skip_existing and 'details' in card:
                    continue
                unique_cards.add(card_name)
    
    print(f"Unique cards to fetch: {len(unique_cards)}")
    print(f"Estimated time: ~{len(unique_cards) * delay_seconds / 60:.1f} minutes")
    print()
    
    # Fetch card details
    card_details_map = {}
    
    with tqdm(total=len(unique_cards), desc="Fetching card data", unit="card") as pbar:
        for card_name in unique_cards:
            details = fetch_card_details(card_name, delay_seconds=delay_seconds)
            card_details_map[card_name] = details
            pbar.update(1)
            
            if len(card_details_map) % 50 == 0:
                successful = sum(1 for v in card_details_map.values() if v is not None)
                print(f"\n  Progress: {len(card_details_map)}/{len(unique_cards)} cards | Success: {successful} | Cache: {len(CARD_CACHE)}")
    
    # Apply details to combos
    print("\nApplying card details to combos...")
    enriched_count = 0
    failed_count = 0
    
    for combo in combos:
        for card in combo.get('cards', []):
            card_name = card.get('name')
            if card_name and card_name in card_details_map:
                details = card_details_map[card_name]
                if details:
                    card['details'] = details
                    enriched_count += 1
                else:
                    failed_count += 1
    
    # Update metadata
    if 'metadata' in data:
        data['metadata']['enriched_at'] = datetime.now().isoformat()
        data['metadata']['enriched_cards'] = enriched_count
        data['metadata']['failed_cards'] = failed_count
        data['metadata']['card_cache_size'] = len(CARD_CACHE)
    
    # Save
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_enriched{ext}"
    
    print(f"\nSaving enriched data to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Summary
    print("\n" + "=" * 60)
    print("ENRICHMENT COMPLETE")
    print("=" * 60)
    print(f"Input file:      {input_file}")
    print(f"Output file:     {output_file}")
    print(f"Total combos:    {len(combos)}")
    print(f"Unique cards:    {len(unique_cards)}")
    print(f"Cards enriched:  {enriched_count}")
    print(f"Cards failed:    {failed_count}")
    if enriched_count + failed_count > 0:
        print(f"Success rate:    {enriched_count / (enriched_count + failed_count) * 100:.1f}%")
    print(f"File size:       {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
    print("=" * 60)
    
    # Cleanup
    if os.path.exists(RATE_LIMIT_FILE):
        os.remove(RATE_LIMIT_FILE)
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Enrich combo JSON files with detailed card data from EDHREC API'
    )
    parser.add_argument('input_file', 
                       help='Path to combo JSON file to enrich')
    parser.add_argument('--output', '-o', 
                       help='Output file path (default: input_enriched.json)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='API rate limit delay in seconds (default: 2.0)')
    parser.add_argument('--force', action='store_true',
                       help='Re-fetch cards even if they already have details')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)
    
    enrich_combo_file(
        args.input_file,
        output_file=args.output,
        delay_seconds=args.delay,
        skip_existing=not args.force
    )


if __name__ == '__main__':
    main()
