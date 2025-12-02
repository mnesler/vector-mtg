#!/usr/bin/env python3
"""
Embedding Quality Testing Tool

Tests the accuracy and quality of vector embeddings for MTG card search.
Provides detailed metrics, similarity distributions, and false positive analysis.

Usage:
    python scripts/test_embedding_quality.py --all
    python scripts/test_embedding_quality.py --query "counterspells"
    python scripts/test_embedding_quality.py --benchmark
    python scripts/test_embedding_quality.py --compare-models
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os
from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from api.embedding_service import get_embedding_service

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


# Test cases with known good results
QUALITY_TEST_CASES = [
    {
        "query": "Lightning Bolt",
        "expected_names": ["Lightning Bolt"],
        "category": "Exact Match",
        "min_similarity": 0.85,
        "description": "Should find exact card name with very high similarity"
    },
    {
        "query": "destroy target creature",
        "expected_keywords": ["destroy", "creature"],
        "exclude_types": ["Creature"],  # Should return removal spells, not creatures
        "category": "Removal",
        "min_similarity": 0.35,
        "expected_count": 10,
        "description": "Should find creature removal spells"
    },
    {
        "query": "counterspells that cost 2 mana",
        "expected_colors": ["U"],
        "expected_keywords": ["counter"],
        "expected_cmc": [2.0],
        "category": "Counterspell",
        "min_similarity": 0.30,
        "expected_count": 5,
        "description": "Should find 2-mana blue counterspells"
    },
    {
        "query": "red instant that deals 3 damage",
        "expected_colors": ["R"],
        "expected_types": ["Instant"],
        "expected_keywords": ["damage", "3"],
        "category": "Burn",
        "min_similarity": 0.30,
        "expected_count": 5,
        "description": "Should find red burn spells dealing 3 damage"
    },
    {
        "query": "creatures with flying",
        "expected_types": ["Creature"],
        "expected_keywords": ["flying"],
        "category": "Flying Creatures",
        "min_similarity": 0.35,
        "expected_count": 10,
        "description": "Should find flying creatures"
    },
    {
        "query": "cards that draw cards",
        "expected_keywords": ["draw"],
        "category": "Card Draw",
        "min_similarity": 0.30,
        "expected_count": 10,
        "description": "Should find card draw effects"
    },
    {
        "query": "ramp spells that search for lands",
        "expected_keywords": ["search", "land"],
        "expected_colors": ["G"],
        "category": "Ramp",
        "min_similarity": 0.25,
        "expected_count": 5,
        "description": "Should find green ramp spells"
    },
    {
        "query": "planeswalker removal",
        "expected_keywords": ["planeswalker"],
        "exclude_types": ["Planeswalker"],
        "category": "Planeswalker Removal",
        "min_similarity": 0.25,
        "expected_count": 5,
        "description": "Should find spells that can remove planeswalkers"
    }
]


def semantic_search(query: str, limit: int = 20, use_oracle_embedding: bool = False) -> List[Dict]:
    """
    Run semantic search and return detailed results.
    
    Args:
        query: Search query
        limit: Maximum results (note: will fetch more to account for duplicate printings)
        use_oracle_embedding: If True, search against oracle_embedding instead of full embedding
    """
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.generate_embedding(query)
    
    embedding_column = "oracle_embedding" if use_oracle_embedding else "embedding"
    
    # Fetch many more results since cards have multiple printings
    # We'll deduplicate later
    fetch_limit = limit * 100  # Fetch 100x more to account for reprints
    
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Set higher ef_search for better HNSW index recall
            try:
                cursor.execute("SET LOCAL hnsw.ef_search = 400;")
            except:
                pass  # Older pgvector versions don't support this
            
            cursor.execute(f"""
                SELECT
                    id,
                    name,
                    mana_cost,
                    cmc,
                    type_line,
                    oracle_text,
                    keywords,
                    colors,
                    1 - ({embedding_column} <=> %s::vector) as similarity
                FROM cards
                WHERE {embedding_column} IS NOT NULL
                ORDER BY {embedding_column} <=> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, fetch_limit))
            
            return cursor.fetchall()
    finally:
        conn.close()


def validate_result(card: Dict, test_case: Dict) -> Tuple[bool, List[str]]:
    """
    Validate if a card result matches test case expectations.
    
    Returns:
        (is_valid, reasons)
    """
    reasons = []
    is_valid = True
    
    # Check expected names
    if "expected_names" in test_case:
        if card['name'] not in test_case['expected_names']:
            is_valid = False
            reasons.append(f"Name '{card['name']}' not in expected {test_case['expected_names']}")
    
    # Check expected keywords in oracle text
    if "expected_keywords" in test_case:
        oracle_text = (card.get('oracle_text') or "").lower()
        missing_keywords = []
        for keyword in test_case['expected_keywords']:
            if keyword.lower() not in oracle_text:
                missing_keywords.append(keyword)
        if missing_keywords:
            is_valid = False
            reasons.append(f"Missing keywords: {missing_keywords}")
    
    # Check expected types
    if "expected_types" in test_case:
        type_line = card.get('type_line', '')
        has_type = any(t in type_line for t in test_case['expected_types'])
        if not has_type:
            is_valid = False
            reasons.append(f"Type '{type_line}' doesn't contain {test_case['expected_types']}")
    
    # Check excluded types
    if "exclude_types" in test_case:
        type_line = card.get('type_line', '')
        has_excluded = any(t in type_line for t in test_case['exclude_types'])
        if has_excluded:
            is_valid = False
            reasons.append(f"Type '{type_line}' contains excluded type {test_case['exclude_types']}")
    
    # Check expected colors
    if "expected_colors" in test_case:
        colors = card.get('colors') or []
        if not any(c in colors for c in test_case['expected_colors']):
            is_valid = False
            reasons.append(f"Colors {colors} don't contain {test_case['expected_colors']}")
    
    # Check expected CMC
    if "expected_cmc" in test_case:
        cmc = card.get('cmc')
        if cmc not in test_case['expected_cmc']:
            is_valid = False
            reasons.append(f"CMC {cmc} not in expected {test_case['expected_cmc']}")
    
    # Check minimum similarity
    if "min_similarity" in test_case:
        similarity = card.get('similarity', 0)
        if similarity < test_case['min_similarity']:
            is_valid = False
            reasons.append(f"Similarity {similarity:.3f} < {test_case['min_similarity']:.3f}")
    
    return is_valid, reasons


def run_quality_test(test_case: Dict, verbose: bool = True) -> Dict:
    """
    Run a single quality test and return detailed results.
    """
    results = semantic_search(test_case['query'], limit=20)
    
    # Deduplicate by name (take highest similarity)
    seen_names = {}
    deduped_results = []
    for card in results:
        name = card['name']
        if name not in seen_names or card['similarity'] > seen_names[name]['similarity']:
            seen_names[name] = card
    
    deduped_results = list(seen_names.values())
    deduped_results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Validate results
    valid_results = []
    invalid_results = []
    
    for card in deduped_results:
        is_valid, reasons = validate_result(card, test_case)
        if is_valid:
            valid_results.append(card)
        else:
            invalid_results.append({
                'card': card,
                'reasons': reasons
            })
    
    # Calculate metrics
    total_results = len(deduped_results)
    valid_count = len(valid_results)
    precision = valid_count / total_results if total_results > 0 else 0
    
    # Check if we got expected count
    expected_count = test_case.get('expected_count', 5)
    recall_met = valid_count >= expected_count
    
    # Similarity statistics
    similarities = [r['similarity'] for r in deduped_results]
    valid_similarities = [r['similarity'] for r in valid_results]
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"Test: {test_case['query']}")
        print(f"Category: {test_case['category']}")
        print(f"Description: {test_case['description']}")
        print(f"{'='*80}")
        print(f"\nResults: {total_results} unique cards")
        print(f"Valid: {valid_count} ({precision*100:.1f}% precision)")
        print(f"Expected: ≥{expected_count} valid results - {'✓ PASS' if recall_met else '✗ FAIL'}")
        
        if similarities:
            print(f"\nSimilarity Scores:")
            print(f"  Mean: {np.mean(similarities):.3f}")
            print(f"  Median: {np.median(similarities):.3f}")
            print(f"  Range: {min(similarities):.3f} - {max(similarities):.3f}")
        
        if valid_similarities:
            print(f"\nValid Results Similarity:")
            print(f"  Mean: {np.mean(valid_similarities):.3f}")
            print(f"  Min: {min(valid_similarities):.3f}")
        
        # Show top valid results
        print(f"\n✓ Valid Results (Top {min(10, len(valid_results))}):")
        for i, card in enumerate(valid_results[:10], 1):
            print(f"  {i}. {card['name']:<40} [{card.get('mana_cost', ''):<10}] {card['similarity']:.3f}")
            if card.get('oracle_text'):
                text = card['oracle_text'][:80].replace('\n', ' ')
                print(f"     {text}...")
        
        # Show invalid results
        if invalid_results:
            print(f"\n✗ Invalid Results (Top {min(5, len(invalid_results))}):")
            for i, item in enumerate(invalid_results[:5], 1):
                card = item['card']
                print(f"  {i}. {card['name']:<40} [{card.get('mana_cost', ''):<10}] {card['similarity']:.3f}")
                for reason in item['reasons']:
                    print(f"     → {reason}")
    
    return {
        'query': test_case['query'],
        'category': test_case['category'],
        'total_results': total_results,
        'valid_count': valid_count,
        'precision': precision,
        'recall_met': recall_met,
        'similarities': similarities,
        'valid_similarities': valid_similarities,
        'valid_results': valid_results,
        'invalid_results': invalid_results
    }


def run_benchmark_suite(verbose: bool = True) -> Dict:
    """
    Run complete benchmark suite and return aggregate metrics.
    """
    print("\n" + "="*80)
    print("EMBEDDING QUALITY BENCHMARK")
    print("="*80)
    
    results = []
    for test_case in QUALITY_TEST_CASES:
        result = run_quality_test(test_case, verbose=verbose)
        results.append(result)
    
    # Aggregate metrics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['recall_met'])
    avg_precision = np.mean([r['precision'] for r in results])
    
    all_valid_sims = []
    all_invalid_sims = []
    
    for r in results:
        all_valid_sims.extend(r['valid_similarities'])
        all_invalid_sims.extend([item['card']['similarity'] for item in r['invalid_results']])
    
    print(f"\n{'='*80}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*80}")
    print(f"Tests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Average Precision: {avg_precision*100:.1f}%")
    
    if all_valid_sims:
        print(f"\nValid Results Similarity Distribution:")
        print(f"  Mean: {np.mean(all_valid_sims):.3f}")
        print(f"  Median: {np.median(all_valid_sims):.3f}")
        print(f"  Std Dev: {np.std(all_valid_sims):.3f}")
        print(f"  Range: {min(all_valid_sims):.3f} - {max(all_valid_sims):.3f}")
        
        # Show percentiles
        percentiles = [10, 25, 50, 75, 90]
        print(f"\n  Percentiles:")
        for p in percentiles:
            val = np.percentile(all_valid_sims, p)
            print(f"    {p}th: {val:.3f}")
    
    if all_invalid_sims:
        print(f"\nInvalid Results Similarity Distribution:")
        print(f"  Mean: {np.mean(all_invalid_sims):.3f}")
        print(f"  Median: {np.median(all_invalid_sims):.3f}")
        print(f"  Range: {min(all_invalid_sims):.3f} - {max(all_invalid_sims):.3f}")
    
    # Breakdown by category
    print(f"\nResults by Category:")
    category_results = defaultdict(list)
    for r in results:
        category_results[r['category']].append(r)
    
    for category, cat_results in category_results.items():
        passed = sum(1 for r in cat_results if r['recall_met'])
        total = len(cat_results)
        avg_prec = np.mean([r['precision'] for r in cat_results])
        print(f"  {category:<25} {passed}/{total} passed, {avg_prec*100:.1f}% precision")
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'avg_precision': avg_precision,
        'results': results,
        'valid_similarities': all_valid_sims,
        'invalid_similarities': all_invalid_sims
    }


def analyze_similarity_threshold(verbose: bool = True):
    """
    Analyze what similarity threshold should be used for filtering results.
    """
    print("\n" + "="*80)
    print("SIMILARITY THRESHOLD ANALYSIS")
    print("="*80)
    
    results = run_benchmark_suite(verbose=False)
    
    valid_sims = results['valid_similarities']
    invalid_sims = results['invalid_similarities']
    
    if not valid_sims or not invalid_sims:
        print("Insufficient data for threshold analysis")
        return
    
    print(f"\nAnalyzing {len(valid_sims)} valid and {len(invalid_sims)} invalid results...")
    
    # Test different thresholds
    thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    
    print(f"\n{'Threshold':<12} {'Valid %':<12} {'Invalid %':<12} {'Precision':<12}")
    print("-" * 48)
    
    for threshold in thresholds:
        valid_above = sum(1 for s in valid_sims if s >= threshold)
        invalid_above = sum(1 for s in invalid_sims if s >= threshold)
        total_above = valid_above + invalid_above
        
        valid_pct = (valid_above / len(valid_sims)) * 100
        invalid_pct = (invalid_above / len(invalid_sims)) * 100
        precision = (valid_above / total_above * 100) if total_above > 0 else 0
        
        print(f"{threshold:<12.2f} {valid_pct:<12.1f} {invalid_pct:<12.1f} {precision:<12.1f}")
    
    print("\nRecommendation:")
    print("  - Threshold 0.30+: Good balance of precision and recall")
    print("  - Threshold 0.35+: Higher precision, may miss some valid results")
    print("  - Threshold 0.40+: Very high precision, significant recall loss")


def compare_embedding_approaches():
    """
    Compare full card embedding vs oracle-text-only embedding.
    """
    print("\n" + "="*80)
    print("EMBEDDING APPROACH COMPARISON")
    print("="*80)
    
    test_queries = [
        "destroy target creature",
        "counterspells",
        "cards that draw cards",
        "flying creatures"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        # Full embedding
        full_results = semantic_search(query, limit=10, use_oracle_embedding=False)
        oracle_results = semantic_search(query, limit=10, use_oracle_embedding=True)
        
        print(f"\nFull Embedding (name + type + text):")
        for i, card in enumerate(full_results[:5], 1):
            print(f"  {i}. {card['name']:<40} {card['similarity']:.3f}")
        
        print(f"\nOracle Text Only Embedding:")
        for i, card in enumerate(oracle_results[:5], 1):
            print(f"  {i}. {card['name']:<40} {card['similarity']:.3f}")


def interactive_test():
    """
    Interactive mode for testing custom queries.
    """
    print("\n" + "="*80)
    print("INTERACTIVE EMBEDDING TEST")
    print("="*80)
    print("Enter queries to test semantic search (Ctrl+C to exit)")
    
    try:
        while True:
            query = input("\nQuery: ").strip()
            if not query:
                continue
            
            results = semantic_search(query, limit=15)
            
            # Deduplicate
            seen = {}
            for card in results:
                name = card['name']
                if name not in seen or card['similarity'] > seen[name]['similarity']:
                    seen[name] = card
            
            deduped = sorted(seen.values(), key=lambda x: x['similarity'], reverse=True)
            
            print(f"\nResults for '{query}':")
            print(f"{'#':<3} {'Name':<45} {'Type':<25} {'Similarity':<10}")
            print("-" * 90)
            
            for i, card in enumerate(deduped[:15], 1):
                print(f"{i:<3} {card['name']:<45} {card['type_line']:<25} {card['similarity']:.3f}")
                if card.get('oracle_text'):
                    text = card['oracle_text'][:100].replace('\n', ' ')
                    print(f"    {text}...")
            
            # Basic stats
            sims = [c['similarity'] for c in deduped]
            print(f"\nSimilarity: mean={np.mean(sims):.3f}, median={np.median(sims):.3f}, range=[{min(sims):.3f}, {max(sims):.3f}]")
            
    except KeyboardInterrupt:
        print("\n\nExiting interactive mode.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test embedding quality and accuracy')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark suite')
    parser.add_argument('--threshold', action='store_true', help='Analyze similarity thresholds')
    parser.add_argument('--compare', action='store_true', help='Compare embedding approaches')
    parser.add_argument('--interactive', action='store_true', help='Interactive testing mode')
    parser.add_argument('--query', type=str, help='Test a specific query')
    
    args = parser.parse_args()
    
    if args.query:
        # Test specific query
        test_case = {
            'query': args.query,
            'category': 'Custom',
            'description': 'User-provided query',
            'expected_count': 5,
            'min_similarity': 0.25
        }
        run_quality_test(test_case, verbose=True)
    elif args.benchmark:
        run_benchmark_suite(verbose=True)
    elif args.threshold:
        analyze_similarity_threshold()
    elif args.compare:
        compare_embedding_approaches()
    elif args.interactive:
        interactive_test()
    elif args.all:
        run_benchmark_suite(verbose=True)
        analyze_similarity_threshold()
        compare_embedding_approaches()
    else:
        # Default: run benchmark
        run_benchmark_suite(verbose=True)
