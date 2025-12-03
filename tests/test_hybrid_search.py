#!/usr/bin/env python3
"""
Tests for hybrid search functionality.
Tests exact card name matching, query classification, threshold filtering, and result boosting.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.api.hybrid_search_service import HybridSearchService
import psycopg2
from psycopg2.extras import RealDictCursor


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vector_mtg',
    'user': 'postgres',
    'password': 'postgres'
}


@pytest.fixture(scope='module')
def db_conn():
    """Create database connection for tests."""
    conn = psycopg2.connect(**DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope='module')
def hybrid_service(db_conn):
    """Create hybrid search service instance."""
    return HybridSearchService(db_conn)


class TestQueryClassification:
    """Test query classification logic."""
    
    def test_exact_card_name_detection(self, hybrid_service):
        """Test detection of exact card names."""
        # Exact card names (title case, short)
        assert hybrid_service.classify_query("Lightning Bolt") == 'keyword'
        assert hybrid_service.classify_query("Counterspell") == 'keyword'
        assert hybrid_service.classify_query("Birds of Paradise") == 'keyword'
        assert hybrid_service.classify_query("Jace, the Mind Sculptor") == 'keyword'
        assert hybrid_service.classify_query("Sol Ring") == 'keyword'
    
    def test_natural_language_detection(self, hybrid_service):
        """Test detection of natural language queries."""
        # Natural language queries (lowercase, descriptive)
        assert hybrid_service.classify_query("counterspells") == 'semantic'
        assert hybrid_service.classify_query("cards that draw cards") == 'semantic'
        assert hybrid_service.classify_query("flying creatures") == 'semantic'
        assert hybrid_service.classify_query("board wipes") == 'semantic'
        assert hybrid_service.classify_query("removal spells") == 'semantic'
    
    def test_advanced_filter_detection(self, hybrid_service):
        """Test detection of queries with advanced filters."""
        # Queries with CMC filters
        assert hybrid_service.classify_query("zombies cmc > 3") == 'advanced'
        assert hybrid_service.classify_query("dragons more than 5 mana") == 'advanced'
        assert hybrid_service.classify_query("creatures less than 2 mana") == 'advanced'
        
        # Queries with color filters
        assert hybrid_service.classify_query("zombies not black") == 'advanced'
        assert hybrid_service.classify_query("elves only green") == 'advanced'
        assert hybrid_service.classify_query("dragons without blue") == 'advanced'
        
        # Queries with rarity filters
        assert hybrid_service.classify_query("rare zombies") == 'advanced'
        assert hybrid_service.classify_query("mythic dragons") == 'advanced'
        
        # Queries with power/toughness filters
        assert hybrid_service.classify_query("creatures power > 4") == 'advanced'
        assert hybrid_service.classify_query("3/3 creatures") == 'advanced'


class TestExactNameMatching:
    """Test exact card name matching and boosting."""
    
    def test_lightning_bolt_exact_match(self, hybrid_service):
        """Test that Lightning Bolt returns exact match with score 1.0."""
        result = hybrid_service.search("Lightning Bolt", limit=5)
        
        assert result['count'] > 0, "Should find Lightning Bolt"
        assert result['method'] == 'keyword', "Should use keyword search"
        
        # First result should be Lightning Bolt with perfect score
        top_card = result['cards'][0]
        assert top_card['name'] == 'Lightning Bolt'
        assert top_card['similarity'] == 1.0, f"Expected 1.0, got {top_card['similarity']}"
        assert top_card.get('boost_reason') == 'exact_name_match'
    
    def test_counterspell_exact_match(self, hybrid_service):
        """Test that Counterspell returns exact match."""
        result = hybrid_service.search("Counterspell", limit=5)
        
        assert result['count'] > 0
        top_card = result['cards'][0]
        assert top_card['name'] == 'Counterspell'
        assert top_card['similarity'] == 1.0
    
    def test_partial_name_match(self, hybrid_service):
        """Test partial name matching (e.g., 'Lightning' should find 'Lightning Bolt')."""
        result = hybrid_service.search("Lightning", limit=10)
        
        assert result['count'] > 0
        # Should find cards with 'Lightning' in name
        card_names = [c['name'] for c in result['cards']]
        assert any('Lightning' in name for name in card_names)
        
        # Lightning Bolt should be boosted near the top
        lightning_bolt_cards = [c for c in result['cards'] if c['name'] == 'Lightning Bolt']
        if lightning_bolt_cards:
            assert lightning_bolt_cards[0]['similarity'] >= 0.90
    
    def test_case_insensitive_matching(self, hybrid_service):
        """Test that name matching is case-insensitive."""
        result1 = hybrid_service.search("lightning bolt", limit=5)
        result2 = hybrid_service.search("Lightning Bolt", limit=5)
        result3 = hybrid_service.search("LIGHTNING BOLT", limit=5)
        
        # All should find Lightning Bolt as top result
        assert result1['cards'][0]['name'] == 'Lightning Bolt'
        assert result2['cards'][0]['name'] == 'Lightning Bolt'
        assert result3['cards'][0]['name'] == 'Lightning Bolt'
        
        # All should have perfect score
        assert result1['cards'][0]['similarity'] == 1.0
        assert result2['cards'][0]['similarity'] == 1.0
        assert result3['cards'][0]['similarity'] == 1.0


class TestThresholdFiltering:
    """Test similarity threshold filtering."""
    
    def test_semantic_search_with_threshold_050(self, hybrid_service):
        """Test semantic search with default threshold 0.50."""
        result = hybrid_service.search("counterspells", limit=20, threshold=0.50)
        
        assert result['count'] > 0
        assert result['method'] == 'semantic'
        assert result['threshold'] == 0.50
        
        # All results should have similarity >= 0.50
        for card in result['cards']:
            assert card['similarity'] >= 0.50, \
                f"Card '{card['name']}' has similarity {card['similarity']} < 0.50"
    
    def test_semantic_search_with_threshold_060(self, hybrid_service):
        """Test semantic search with higher threshold 0.60."""
        result = hybrid_service.search("counterspells", limit=20, threshold=0.60)
        
        # All results should have similarity >= 0.60
        for card in result['cards']:
            assert card['similarity'] >= 0.60, \
                f"Card '{card['name']}' has similarity {card['similarity']} < 0.60"
    
    def test_threshold_reduces_result_count(self, hybrid_service):
        """Test that higher threshold reduces result count."""
        result_low = hybrid_service.search("flying creatures", limit=50, threshold=0.40)
        result_mid = hybrid_service.search("flying creatures", limit=50, threshold=0.50)
        result_high = hybrid_service.search("flying creatures", limit=50, threshold=0.60)
        
        # Higher threshold should return fewer or equal results
        assert result_high['count'] <= result_mid['count']
        assert result_mid['count'] <= result_low['count']
    
    def test_threshold_improves_precision(self, hybrid_service):
        """Test that higher threshold improves result quality."""
        result = hybrid_service.search("cards that draw cards", limit=20, threshold=0.50)
        
        # Check that top results are actually card draw effects
        card_draw_keywords = ['draw', 'cards', 'look at']
        top_5 = result['cards'][:5]
        
        relevant_count = 0
        for card in top_5:
            oracle_text = (card.get('oracle_text') or '').lower()
            if any(keyword in oracle_text for keyword in card_draw_keywords):
                relevant_count += 1
        
        # At least 80% of top 5 should be relevant
        precision = relevant_count / len(top_5) if top_5 else 0
        assert precision >= 0.80, f"Precision {precision:.2f} < 0.80 for top 5 results"


class TestNameBoosting:
    """Test automatic name match boosting."""
    
    def test_boost_exact_name_match(self, hybrid_service):
        """Test that exact name matches get boosted to 1.0."""
        # Use a natural language query that would normally use semantic search
        # but includes a card name
        result = hybrid_service.search("counterspells", limit=20, auto_boost=True)
        
        # Find "Counterspell" card in results
        counterspell_cards = [c for c in result['cards'] if c['name'] == 'Counterspell']
        
        if counterspell_cards:
            # Should be boosted to near 1.0
            assert counterspell_cards[0]['similarity'] >= 0.90
    
    def test_boost_name_starts_with(self, hybrid_service):
        """Test boosting when query matches start of card name."""
        result = hybrid_service.search("flying creatures", limit=20, auto_boost=True)
        
        # Cards with 'Flying' in name should get boosted
        flying_named_cards = [c for c in result['cards'] if 'flying' in c['name'].lower()]
        
        if flying_named_cards:
            # Should have high similarity
            for card in flying_named_cards[:3]:
                assert card['similarity'] >= 0.70
    
    def test_no_boosting_when_disabled(self, hybrid_service):
        """Test that boosting can be disabled."""
        result_boosted = hybrid_service.search("Lightning Bolt", limit=5, auto_boost=True)
        result_no_boost = hybrid_service.search("Lightning Bolt", limit=5, auto_boost=False)
        
        # With boosting disabled, might not get perfect 1.0 score
        # (though keyword search would still prioritize exact matches)
        assert 'cards' in result_no_boost
        assert len(result_no_boost['cards']) > 0


class TestHybridSearchIntegration:
    """Integration tests for complete hybrid search flow."""
    
    def test_keyword_route_exact_names(self, hybrid_service):
        """Test that exact card names route to keyword search."""
        test_cards = [
            "Sol Ring",
            "Command Tower", 
            "Path to Exile",
            "Swords to Plowshares"
        ]
        
        for card_name in test_cards:
            result = hybrid_service.search(card_name, limit=5)
            assert result['method'] == 'keyword', \
                f"{card_name} should use keyword search, got {result['method']}"
            assert result['cards'][0]['name'] == card_name, \
                f"Expected {card_name} as top result"
            assert result['cards'][0]['similarity'] == 1.0
    
    def test_semantic_route_natural_language(self, hybrid_service):
        """Test that natural language queries route to semantic search."""
        test_queries = [
            "counterspells",
            "board wipes",
            "card draw",
            "flying creatures",
            "removal spells"
        ]
        
        for query in test_queries:
            result = hybrid_service.search(query, limit=10)
            assert result['method'] == 'semantic', \
                f"'{query}' should use semantic search, got {result['method']}"
            assert result['count'] > 0
    
    def test_advanced_route_with_filters(self, hybrid_service):
        """Test that queries with filters route to advanced search."""
        test_queries = [
            "zombies not black",
            "dragons cmc > 5",
            "creatures power >= 4",
            "rare elves"
        ]
        
        for query in test_queries:
            result = hybrid_service.search(query, limit=10)
            assert result['method'] == 'advanced', \
                f"'{query}' should use advanced search, got {result['method']}"
    
    def test_deduplication_by_name(self, hybrid_service):
        """Test that results are deduplicated by card name."""
        result = hybrid_service.search("Lightning Bolt", limit=10)
        
        card_names = [c['name'] for c in result['cards']]
        unique_names = set(card_names)
        
        # Should not have duplicate card names
        assert len(card_names) == len(unique_names), \
            f"Found duplicate cards: {[name for name in card_names if card_names.count(name) > 1]}"
    
    def test_pagination(self, hybrid_service):
        """Test pagination with offset."""
        # Get first page
        result1 = hybrid_service.search("creatures", limit=10, offset=0)
        # Get second page
        result2 = hybrid_service.search("creatures", limit=10, offset=10)
        
        # Should have different results
        names1 = set(c['name'] for c in result1['cards'])
        names2 = set(c['name'] for c in result2['cards'])
        
        # Pages should not overlap (mostly)
        overlap = names1 & names2
        assert len(overlap) < 3, f"Pages have too much overlap: {overlap}"


class TestRegressionTests:
    """Regression tests for known issues from test results."""
    
    def test_lightning_bolt_now_works(self, hybrid_service):
        """
        Regression test: Lightning Bolt exact name should now work.
        Previous issue: Semantic search gave similarity 0.618 < 0.85 threshold.
        Solution: Use keyword search + boosting for exact names.
        """
        result = hybrid_service.search("Lightning Bolt", limit=5)
        
        top_card = result['cards'][0]
        assert top_card['name'] == 'Lightning Bolt'
        assert top_card['similarity'] >= 0.95, \
            f"Lightning Bolt should score >= 0.95, got {top_card['similarity']}"
    
    def test_counterspells_high_precision(self, hybrid_service):
        """
        Test that 'counterspells' query returns actual counterspells.
        Previous pass rate: Good (semantic search works well for archetypes)
        """
        result = hybrid_service.search("counterspells", limit=10, threshold=0.50)
        
        # Check that most results are actual counterspells
        counter_keywords = ['counter target', 'counter spell', 'counter that']
        relevant_count = 0
        
        for card in result['cards']:
            oracle_text = (card.get('oracle_text') or '').lower()
            type_line = (card.get('type_line') or '').lower()
            name = card['name'].lower()
            
            # Count as relevant if it's likely a counterspell
            if any(keyword in oracle_text for keyword in counter_keywords) or \
               'counter' in name:
                relevant_count += 1
        
        precision = relevant_count / len(result['cards']) if result['cards'] else 0
        assert precision >= 0.70, \
            f"Counterspells precision {precision:.2f} < 0.70"
    
    def test_flying_creatures_perfect_precision(self, hybrid_service):
        """
        Test that 'flying creatures' returns only flying creatures.
        Previous test result: 100% precision
        """
        result = hybrid_service.search("creatures with flying", limit=10, threshold=0.50)
        
        # All results should be creatures with flying
        for card in result['cards']:
            oracle_text = (card.get('oracle_text') or '').lower()
            keywords = card.get('keywords') or []
            type_line = (card.get('type_line') or '').lower()
            
            # Should be a creature
            assert 'creature' in type_line, \
                f"'{card['name']}' is not a creature: {type_line}"
            
            # Should have flying
            has_flying = 'flying' in oracle_text or \
                        any('flying' in str(k).lower() for k in keywords)
            assert has_flying, \
                f"'{card['name']}' doesn't have flying"


def run_test_suite():
    """Run all tests and print summary."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_test_suite()
