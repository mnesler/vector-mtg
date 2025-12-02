#!/usr/bin/env python3
"""
Tests for the Advanced Query Parser.
"""

import pytest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from api.advanced_query_parser import AdvancedQueryParser, ParsedQuery


@pytest.fixture
def parser():
    """Create a parser instance for testing."""
    return AdvancedQueryParser()


class TestCMCFilters:
    """Test CMC/mana cost filter extraction."""
    
    def test_more_than_x_mana(self, parser):
        result = parser.parse("zombies more than 3 mana")
        assert result.filters.get('cmc_gt') == 3
        assert 'zombie' in result.positive_terms.lower()
    
    def test_less_than_x_mana(self, parser):
        result = parser.parse("dragons less than 5 mana")
        assert result.filters.get('cmc_lt') == 5
    
    def test_x_mana_or_more(self, parser):
        result = parser.parse("creatures 4 mana or more")
        assert result.filters.get('cmc_gte') == 4
    
    def test_x_mana_or_less(self, parser):
        result = parser.parse("removal 2 mana or less")
        assert result.filters.get('cmc_lte') == 2
    
    def test_exactly_x_mana(self, parser):
        result = parser.parse("exactly 3 mana counterspells")
        assert result.filters.get('cmc_eq') == 3
    
    def test_cmc_operator_syntax(self, parser):
        result = parser.parse("vampires cmc > 4")
        assert result.filters.get('cmc_gt') == 4
        
        result = parser.parse("elves cmc <= 2")
        assert result.filters.get('cmc_lte') == 2


class TestColorFilters:
    """Test color filter extraction."""
    
    def test_exclude_single_color(self, parser):
        result = parser.parse("zombies but not black")
        assert 'B' in result.filters.get('exclude_colors', [])
        assert 'black' in result.exclusions
    
    def test_exclude_multiple_colors(self, parser):
        result = parser.parse("creatures not black not red")
        assert 'B' in result.filters.get('exclude_colors', [])
        assert 'R' in result.filters.get('exclude_colors', [])
    
    def test_only_color_constraint(self, parser):
        result = parser.parse("zombies but only blue")
        assert 'U' in result.filters.get('only_colors', [])
        # Should exclude all other colors
        exclude_colors = result.filters.get('exclude_colors', [])
        assert 'W' in exclude_colors
        assert 'B' in exclude_colors
        assert 'R' in exclude_colors
        assert 'G' in exclude_colors
    
    def test_include_color(self, parser):
        result = parser.parse("blue dragons")
        assert 'U' in result.filters.get('include_colors', [])
    
    def test_without_color(self, parser):
        result = parser.parse("vampires without red")
        assert 'R' in result.filters.get('exclude_colors', [])


class TestComplexQueries:
    """Test complex multi-filter queries."""
    
    def test_zombies_not_black_more_than_3_mana(self, parser):
        """The main use case from the user."""
        result = parser.parse("zombies but not black more than 3 mana")
        
        # Should find zombies
        assert 'zombie' in result.positive_terms.lower()
        
        # Should exclude black
        assert 'B' in result.filters.get('exclude_colors', [])
        assert 'black' in result.exclusions
        
        # Should filter CMC > 3
        assert result.filters.get('cmc_gt') == 3
    
    def test_blue_red_wizards_cmc_4_or_less(self, parser):
        result = parser.parse("blue and red wizards 4 mana or less")
        
        assert 'wizard' in result.positive_terms.lower()
        assert result.filters.get('cmc_lte') == 4
        # Note: "blue and red" might be in positive_terms or include_colors
        # depending on implementation
    
    def test_rare_dragons_only_red_power_5_plus(self, parser):
        result = parser.parse("rare dragons only red power >= 5")
        
        assert 'dragon' in result.positive_terms.lower()
        assert result.filters.get('rarity') == 'rare'
        assert 'R' in result.filters.get('only_colors', [])
        assert result.filters.get('power_gte') == 5
    
    def test_creatures_no_flying_3_mana_or_less(self, parser):
        result = parser.parse("creatures without flying 3 mana or less")
        
        assert 'creature' in result.filters.get('type_line_contains', [])
        assert 'flying' in result.filters.get('exclude_keywords', [])
        assert result.filters.get('cmc_lte') == 3


class TestTypeFilters:
    """Test card type filter extraction."""
    
    def test_creature_type(self, parser):
        result = parser.parse("creatures with flying")
        assert 'creature' in result.filters.get('type_line_contains', [])
    
    def test_instant_type(self, parser):
        result = parser.parse("blue instants")
        assert 'instant' in result.filters.get('type_line_contains', [])
    
    def test_artifact_type(self, parser):
        result = parser.parse("artifacts cmc < 3")
        assert 'artifact' in result.filters.get('type_line_contains', [])


class TestKeywordFilters:
    """Test keyword ability filters."""
    
    def test_with_keyword(self, parser):
        result = parser.parse("creatures with flying")
        assert 'flying' in result.filters.get('include_keywords', [])
    
    def test_without_keyword(self, parser):
        result = parser.parse("zombies without haste")
        assert 'haste' in result.filters.get('exclude_keywords', [])
    
    def test_multiple_keywords(self, parser):
        result = parser.parse("dragons with flying and haste")
        # Should detect at least flying
        assert 'flying' in result.filters.get('include_keywords', [])


class TestRarityFilters:
    """Test rarity filter extraction."""
    
    def test_rare_filter(self, parser):
        result = parser.parse("rare zombies")
        assert result.filters.get('rarity') == 'rare'
    
    def test_mythic_rare_filter(self, parser):
        result = parser.parse("mythic rare dragons")
        assert result.filters.get('rarity') == 'mythicrare'
    
    def test_uncommon_filter(self, parser):
        result = parser.parse("uncommon removal")
        assert result.filters.get('rarity') == 'uncommon'


class TestPowerToughnessFilters:
    """Test power/toughness filter extraction."""
    
    def test_power_greater_than(self, parser):
        result = parser.parse("creatures power > 4")
        assert result.filters.get('power_gt') == 4
    
    def test_toughness_less_than(self, parser):
        result = parser.parse("zombies toughness < 3")
        assert result.filters.get('toughness_lt') == 3
    
    def test_power_toughness_combo(self, parser):
        result = parser.parse("3/3 or bigger creatures")
        assert result.filters.get('power_gte') == 3
        assert result.filters.get('toughness_gte') == 3


class TestSQLGeneration:
    """Test SQL WHERE clause generation."""
    
    def test_cmc_filter_sql(self, parser):
        result = parser.parse("cards more than 5 mana")
        where, params = parser.to_sql_where_clause(result)
        
        assert "cmc >" in where
        assert 5 in params
    
    def test_color_exclusion_sql(self, parser):
        result = parser.parse("zombies not black")
        where, params = parser.to_sql_where_clause(result)
        
        assert "mana_cost NOT LIKE" in where
        assert '%{B}%' in params
    
    def test_complex_query_sql(self, parser):
        result = parser.parse("zombies but not black more than 3 mana")
        where, params = parser.to_sql_where_clause(result)
        
        # Should have both CMC and color filters
        assert "cmc >" in where
        assert "mana_cost NOT LIKE" in where
        assert 3 in params
        assert '%{B}%' in params
    
    def test_type_filter_sql(self, parser):
        result = parser.parse("creatures")
        where, params = parser.to_sql_where_clause(result)
        
        assert "type_line ILIKE" in where
        assert '%creature%' in params


class TestEdgeCases:
    """Test edge cases and unusual inputs."""
    
    def test_empty_query(self, parser):
        result = parser.parse("")
        assert result.positive_terms == ""
        assert result.filters == {} or all(v is None for v in result.filters.values())
    
    def test_only_exclusions(self, parser):
        result = parser.parse("not black not red")
        assert 'B' in result.filters.get('exclude_colors', [])
        assert 'R' in result.filters.get('exclude_colors', [])
    
    def test_case_insensitive(self, parser):
        result1 = parser.parse("ZOMBIES NOT BLACK")
        result2 = parser.parse("zombies not black")
        
        assert result1.filters.get('exclude_colors') == result2.filters.get('exclude_colors')
    
    def test_extra_whitespace(self, parser):
        result = parser.parse("  zombies   more  than   3   mana  ")
        assert result.filters.get('cmc_gt') == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
