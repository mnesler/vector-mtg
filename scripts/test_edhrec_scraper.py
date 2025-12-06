#!/usr/bin/env python3
"""
Quick test of EDHREC scraper - scrapes 2 commanders to verify functionality.
"""

import sys
sys.path.insert(0, '/home/maxwell/vector-mtg/scripts')

from edhrec_infinite_scroll_scraper import EDHRecInfiniteScrollScraper

if __name__ == "__main__":
    print("Testing EDHREC Infinite Scroll Scraper")
    print("Scraping 2 commanders as a test...")
    print("-" * 70)
    
    scraper = EDHRecInfiniteScrollScraper(headless=True)
    scraper.scrape_all_commanders(limit=2)
