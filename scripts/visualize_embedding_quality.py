#!/usr/bin/env python3
"""
Visual Embedding Quality Analyzer

Creates ASCII histograms and distributions to help visualize embedding quality.
No external plotting libraries required.

Usage:
    python scripts/visualize_embedding_quality.py --query "counterspells"
    python scripts/visualize_embedding_quality.py --distribution
"""

import sys
import os
from typing import List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import functions we need
try:
    from test_embedding_quality import semantic_search, run_benchmark_suite
except ImportError:
    # Fallback: define minimal versions here
    def semantic_search(query: str, limit: int = 20) -> List[Dict]:
        from api.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_embedding(query)
        
        DB_CONFIG = {
            'host': 'localhost',
            'port': 5432,
            'database': 'vector_mtg',
            'user': 'postgres',
            'password': 'postgres'
        }
        
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id, name, mana_cost, cmc, type_line, oracle_text,
                        keywords, colors,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM cards
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                return cursor.fetchall()
        finally:
            conn.close()
    
    def run_benchmark_suite(verbose: bool = True) -> Dict:
        print("Benchmark suite not available in standalone mode")
        return {'valid_similarities': [], 'invalid_similarities': []}


def create_histogram(values: List[float], bins: int = 20, width: int = 50, title: str = "Distribution"):
    """Create an ASCII histogram."""
    if not values:
        print("No data to plot")
        return
    
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    
    if range_val == 0:
        print(f"All values are {min_val:.3f}")
        return
    
    # Create bins
    bin_edges = [min_val + (range_val * i / bins) for i in range(bins + 1)]
    bin_counts = [0] * bins
    
    for val in values:
        bin_idx = min(int((val - min_val) / range_val * bins), bins - 1)
        bin_counts[bin_idx] += 1
    
    # Find max count for scaling
    max_count = max(bin_counts)
    
    print(f"\n{title}")
    print("=" * 70)
    
    for i, count in enumerate(bin_counts):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        
        # Scale bar
        bar_length = int((count / max_count) * width) if max_count > 0 else 0
        bar = "█" * bar_length
        
        # Format
        label = f"{bin_start:.3f}-{bin_end:.3f}"
        print(f"{label:20} │{bar:<{width}} {count:>4}")
    
    print("=" * 70)
    print(f"Total: {len(values)} samples")
    print(f"Range: {min_val:.3f} - {max_val:.3f}")
    print(f"Mean: {sum(values)/len(values):.3f}")


def analyze_query_distribution(query: str, limit: int = 100):
    """Analyze and visualize similarity distribution for a query."""
    print(f"\nAnalyzing query: '{query}'")
    print("=" * 70)
    
    results = semantic_search(query, limit=limit)
    
    # Deduplicate by name
    seen = {}
    for card in results:
        name = card['name']
        if name not in seen or card['similarity'] > seen[name]['similarity']:
            seen[name] = card
    
    deduped = sorted(seen.values(), key=lambda x: x['similarity'], reverse=True)
    
    # Extract similarities
    similarities = [r['similarity'] for r in deduped]
    
    # Show top results
    print(f"\nTop 10 Results:")
    print(f"{'Rank':<6} {'Name':<40} {'Type':<20} {'Sim':<8}")
    print("-" * 76)
    for i, card in enumerate(deduped[:10], 1):
        print(f"{i:<6} {card['name']:<40} {card['type_line'][:18]:<20} {card['similarity']:.3f}")
    
    # Create histogram
    create_histogram(similarities, bins=20, title=f"Similarity Distribution (n={len(similarities)})")
    
    # Percentile analysis
    print(f"\nPercentile Analysis:")
    print(f"{'Percentile':<12} {'Similarity':<12} {'Interpretation'}")
    print("-" * 60)
    
    percentiles = [100, 90, 75, 50, 25, 10]
    for p in percentiles:
        idx = min(int(len(deduped) * p / 100), len(deduped) - 1)
        sim = deduped[idx]['similarity']
        
        if sim >= 0.60:
            interp = "Excellent"
        elif sim >= 0.45:
            interp = "Very Good"
        elif sim >= 0.30:
            interp = "Good"
        elif sim >= 0.20:
            interp = "Fair"
        else:
            interp = "Poor"
        
        print(f"{p}th{'':<9} {sim:.3f}{'':<8} {interp}")
    
    # Recommendation
    print(f"\nRecommendation:")
    top_10_mean = sum(r['similarity'] for r in deduped[:10]) / min(10, len(deduped))
    
    if top_10_mean >= 0.55:
        print(f"  ✓ Excellent query - top results are highly relevant (mean={top_10_mean:.3f})")
        print(f"  → Use threshold: 0.30+")
    elif top_10_mean >= 0.40:
        print(f"  ✓ Good query - results are relevant (mean={top_10_mean:.3f})")
        print(f"  → Use threshold: 0.25-0.30")
    elif top_10_mean >= 0.30:
        print(f"  ⚠ Moderate query - some relevant results (mean={top_10_mean:.3f})")
        print(f"  → Use threshold: 0.20-0.25, or rephrase query")
    else:
        print(f"  ✗ Poor query - results may not be relevant (mean={top_10_mean:.3f})")
        print(f"  → Rephrase query or use keyword search instead")


def compare_valid_vs_invalid_distribution():
    """Compare similarity distributions for valid vs invalid results from benchmark."""
    print("\nRunning benchmark to analyze valid vs invalid distributions...")
    print("=" * 70)
    
    results = run_benchmark_suite(verbose=False)
    
    valid_sims = results['valid_similarities']
    invalid_sims = results['invalid_similarities']
    
    print(f"\n{'='*70}")
    print("VALID RESULTS DISTRIBUTION")
    create_histogram(valid_sims, bins=20, title=f"Valid Results (n={len(valid_sims)})")
    
    print(f"\n{'='*70}")
    print("INVALID RESULTS DISTRIBUTION")
    create_histogram(invalid_sims, bins=20, title=f"Invalid Results (n={len(invalid_sims)})")
    
    # Overlap analysis
    print(f"\n{'='*70}")
    print("OVERLAP ANALYSIS")
    print("=" * 70)
    
    if valid_sims and invalid_sims:
        valid_mean = sum(valid_sims) / len(valid_sims)
        invalid_mean = sum(invalid_sims) / len(invalid_sims)
        
        print(f"\nMean Similarities:")
        print(f"  Valid:   {valid_mean:.3f}")
        print(f"  Invalid: {invalid_mean:.3f}")
        print(f"  Delta:   {valid_mean - invalid_mean:.3f}")
        
        if valid_mean - invalid_mean > 0.10:
            print(f"\n✓ Good separation! Valid results score significantly higher.")
        elif valid_mean - invalid_mean > 0.05:
            print(f"\n⚠ Moderate separation. Consider using filters in addition to similarity.")
        else:
            print(f"\n✗ Poor separation. Valid and invalid results have similar scores.")
            print(f"  → Consider using a better embedding model or adding filters")
        
        # Find optimal threshold
        print(f"\nOptimal Threshold Analysis:")
        print(f"{'Threshold':<12} {'Valid Keep %':<15} {'Invalid Keep %':<15} {'Separation'}")
        print("-" * 60)
        
        for threshold in [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]:
            valid_keep = sum(1 for s in valid_sims if s >= threshold) / len(valid_sims) * 100
            invalid_keep = sum(1 for s in invalid_sims if s >= threshold) / len(invalid_sims) * 100
            separation = valid_keep - invalid_keep
            
            marker = " ← RECOMMENDED" if separation > 40 and valid_keep > 60 else ""
            print(f"{threshold:<12.2f} {valid_keep:<15.1f} {invalid_keep:<15.1f} {separation:>+.1f}{marker}")


def show_model_characteristics():
    """Show expected characteristics of different embedding models."""
    print("\n" + "="*70)
    print("EMBEDDING MODEL CHARACTERISTICS")
    print("="*70)
    
    models = [
        {
            "name": "all-MiniLM-L6-v2",
            "dims": 384,
            "speed": "★★★★★",
            "quality": "★★★☆☆",
            "typical_scores": "0.35-0.75",
            "use_case": "Development, fast iteration",
            "notes": "Currently used model - good balance"
        },
        {
            "name": "all-MiniLM-L12-v2",
            "dims": 384,
            "speed": "★★★★☆",
            "quality": "★★★★☆",
            "typical_scores": "0.38-0.78",
            "use_case": "Better quality, still fast",
            "notes": "Slightly better than L6, minimal slowdown"
        },
        {
            "name": "all-mpnet-base-v2",
            "dims": 768,
            "speed": "★★★☆☆",
            "quality": "★★★★★",
            "typical_scores": "0.40-0.82",
            "use_case": "Production, best quality",
            "notes": "Highest quality, worth the slowdown"
        }
    ]
    
    for model in models:
        print(f"\n{model['name']}")
        print("-" * 70)
        print(f"  Dimensions:     {model['dims']}")
        print(f"  Speed:          {model['speed']}")
        print(f"  Quality:        {model['quality']}")
        print(f"  Typical Scores: {model['typical_scores']}")
        print(f"  Use Case:       {model['use_case']}")
        print(f"  Notes:          {model['notes']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize embedding quality')
    parser.add_argument('--query', type=str, help='Analyze similarity distribution for a query')
    parser.add_argument('--distribution', action='store_true', help='Compare valid vs invalid distributions')
    parser.add_argument('--models', action='store_true', help='Show model characteristics')
    parser.add_argument('--limit', type=int, default=100, help='Number of results to analyze')
    
    args = parser.parse_args()
    
    if args.query:
        analyze_query_distribution(args.query, limit=args.limit)
    elif args.distribution:
        compare_valid_vs_invalid_distribution()
    elif args.models:
        show_model_characteristics()
    else:
        # Default: show distributions
        compare_valid_vs_invalid_distribution()


if __name__ == '__main__':
    main()
