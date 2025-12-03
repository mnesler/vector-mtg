#!/usr/bin/env python3
"""
Manual tests for hybrid search functionality.
Tests exact card name matching, query classification, and threshold filtering.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.api.hybrid_search_service import HybridSearchService
import psycopg2


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


def test_query_classification():
    """Test query classification logic."""
    print("\n" + "="*60)
    print("TEST: Query Classification")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    service = HybridSearchService(conn)
    
    tests = [
        # (query, expected_method)
        ("Lightning Bolt", "keyword"),
        ("Counterspell", "keyword"),
        ("Birds of Paradise", "keyword"),
        ("Sol Ring", "keyword"),
        ("counterspells", "semantic"),
        ("cards that draw cards", "semantic"),
        ("flying creatures", "semantic"),
        ("board wipes", "semantic"),
        ("zombies cmc > 3", "advanced"),
        ("dragons not black", "advanced"),
        ("rare elves", "advanced"),
        ("creatures power > 4", "advanced"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in tests:
        result = service.classify_query(query)
        if result == expected:
            print(f"✓ '{query}' → {result}")
            passed += 1
        else:
            print(f"✗ '{query}' → {result} (expected {expected})")
            failed += 1
    
    conn.close()
    print(f"\nPassed: {passed}/{passed+failed}")
    return failed == 0


def test_exact_name_matching():
    """Test exact card name matching and boosting."""
    print("\n" + "="*60)
    print("TEST: Exact Card Name Matching")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    service = HybridSearchService(conn)
    
    test_cards = [
        "Lightning Bolt",
        "Counterspell",
        "Sol Ring",
        "Path to Exile"
    ]
    
    passed = 0
    failed = 0
    
    for card_name in test_cards:
        result = service.search(card_name, limit=5)
        
        if result['count'] == 0:
            print(f"✗ '{card_name}' - NO RESULTS FOUND")
            failed += 1
            continue
        
        top_card = result['cards'][0]
        method = result['method']
        
        # Check if top result is the exact card
        if top_card['name'] == card_name:
            # Check similarity score
            if top_card['similarity'] >= 0.95:
                print(f"✓ '{card_name}' → {top_card['name']} (score: {top_card['similarity']:.3f}, method: {method})")
                passed += 1
            else:
                print(f"⚠ '{card_name}' → {top_card['name']} (score: {top_card['similarity']:.3f} < 0.95)")
                failed += 1
        else:
            print(f"✗ '{card_name}' → {top_card['name']} (expected exact match)")
            failed += 1
    
    conn.close()
    print(f"\nPassed: {passed}/{passed+failed}")
    return failed == 0


def test_threshold_filtering():
    """Test similarity threshold filtering."""
    print("\n" + "="*60)
    print("TEST: Similarity Threshold Filtering")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    service = HybridSearchService(conn)
    
    query = "counterspells"
    thresholds = [0.40, 0.50, 0.60]
    
    passed = 0
    failed = 0
    
    for threshold in thresholds:
        result = service.search(query, limit=20, threshold=threshold)
        
        # Check all results meet threshold
        violations = []
        for card in result['cards']:
            if card['similarity'] < threshold:
                violations.append(f"{card['name']} ({card['similarity']:.3f})")
        
        if not violations:
            print(f"✓ Threshold {threshold:.2f}: {result['count']} cards, all >= {threshold:.2f}")
            passed += 1
        else:
            print(f"✗ Threshold {threshold:.2f}: Found {len(violations)} violations")
            for v in violations[:3]:
                print(f"  - {v}")
            failed += 1
    
    # Test that higher threshold returns fewer results
    result_low = service.search(query, limit=50, threshold=0.40)
    result_mid = service.search(query, limit=50, threshold=0.50)
    result_high = service.search(query, limit=50, threshold=0.60)
    
    if result_high['count'] <= result_mid['count'] <= result_low['count']:
        print(f"✓ Higher threshold reduces results: {result_low['count']} → {result_mid['count']} → {result_high['count']}")
        passed += 1
    else:
        print(f"✗ Threshold ordering wrong: {result_low['count']} → {result_mid['count']} → {result_high['count']}")
        failed += 1
    
    conn.close()
    print(f"\nPassed: {passed}/{passed+failed}")
    return failed == 0


def test_name_boosting():
    """Test automatic name match boosting."""
    print("\n" + "="*60)
    print("TEST: Name Match Boosting")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    service = HybridSearchService(conn)
    
    passed = 0
    failed = 0
    
    # Test 1: Exact match boosting
    result = service.search("Lightning Bolt", limit=10, auto_boost=True)
    bolt_cards = [c for c in result['cards'] if c['name'] == 'Lightning Bolt']
    
    if bolt_cards and bolt_cards[0]['similarity'] == 1.0:
        print(f"✓ Exact match boost: Lightning Bolt → {bolt_cards[0]['similarity']:.3f}")
        passed += 1
    else:
        print(f"✗ Exact match boost failed")
        failed += 1
    
    # Test 2: Partial match boosting
    result = service.search("counterspells", limit=20, auto_boost=True)
    counterspell_cards = [c for c in result['cards'] if c['name'] == 'Counterspell']
    
    if counterspell_cards and counterspell_cards[0]['similarity'] >= 0.85:
        print(f"✓ Partial match boost: Counterspell → {counterspell_cards[0]['similarity']:.3f}")
        passed += 1
    else:
        print(f"✗ Partial match boost failed")
        failed += 1
    
    conn.close()
    print(f"\nPassed: {passed}/{passed+failed}")
    return failed == 0


def test_regression_lightning_bolt():
    """
    Regression test: Lightning Bolt exact name should now work.
    Previous issue: Semantic search gave similarity 0.618 < 0.85 threshold.
    """
    print("\n" + "="*60)
    print("REGRESSION TEST: Lightning Bolt Fix")
    print("="*60)
    print("Issue: Previously scored 0.618 in semantic search")
    print("Fix: Use keyword search + boosting for exact names")
    print()
    
    conn = psycopg2.connect(**DB_CONFIG)
    service = HybridSearchService(conn)
    
    result = service.search("Lightning Bolt", limit=5)
    
    if result['count'] == 0:
        print("✗ FAILED: No results found")
        conn.close()
        return False
    
    top_card = result['cards'][0]
    
    print(f"Top Result: {top_card['name']}")
    print(f"Similarity: {top_card['similarity']:.3f}")
    print(f"Method: {result['method']}")
    print(f"Boost Reason: {top_card.get('boost_reason', 'none')}")
    
    if top_card['name'] == 'Lightning Bolt' and top_card['similarity'] >= 0.95:
        print("\n✓ PASSED: Lightning Bolt now works correctly!")
        conn.close()
        return True
    else:
        print(f"\n✗ FAILED: Expected Lightning Bolt with score >= 0.95")
        conn.close()
        return False


def test_case_insensitive():
    """Test case-insensitive matching."""
    print("\n" + "="*60)
    print("TEST: Case-Insensitive Matching")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    service = HybridSearchService(conn)
    
    queries = [
        "lightning bolt",
        "Lightning Bolt",
        "LIGHTNING BOLT",
        "LiGhTnInG bOlT"
    ]
    
    passed = 0
    failed = 0
    
    for query in queries:
        result = service.search(query, limit=5)
        if result['count'] > 0 and result['cards'][0]['name'] == 'Lightning Bolt':
            print(f"✓ '{query}' → Lightning Bolt ({result['cards'][0]['similarity']:.3f})")
            passed += 1
        else:
            print(f"✗ '{query}' → {result['cards'][0]['name'] if result['cards'] else 'NO RESULTS'}")
            failed += 1
    
    conn.close()
    print(f"\nPassed: {passed}/{passed+failed}")
    return failed == 0


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "="*60)
    print("HYBRID SEARCH TEST SUITE")
    print("="*60)
    
    tests = [
        ("Query Classification", test_query_classification),
        ("Exact Name Matching", test_exact_name_matching),
        ("Threshold Filtering", test_threshold_filtering),
        ("Name Boosting", test_name_boosting),
        ("Case Insensitive", test_case_insensitive),
        ("Lightning Bolt Regression", test_regression_lightning_bolt),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ TEST CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed_count}/{total_count} test suites passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test suite(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
