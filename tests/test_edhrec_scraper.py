#!/usr/bin/env python3
"""
Test suite for EDHREC Playwright Scraper
Tests URL slug generation and data extraction without making web requests
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from edhrec_playwright_scraper import EDHRECPlaywrightScraper


class TestURLSlugGeneration:
    """Test card name to URL slug conversion"""
    
    def test_simple_name(self):
        """Test simple card name with spaces"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Rhystic Study") == "rhystic-study"
    
    def test_apostrophe_removal(self):
        """Test removal of apostrophes"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Jeska's Will") == "jeskas-will"
    
    def test_comma_removal(self):
        """Test removal of commas"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Atraxa, Praetors' Voice") == "atraxa-praetors-voice"
    
    def test_multiple_punctuation(self):
        """Test removal of multiple punctuation marks"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Teferi, Time Raveler") == "teferi-time-raveler"
    
    def test_special_characters(self):
        """Test removal of special characters"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Æther Vial") == "ther-vial"
    
    def test_numbers_removed(self):
        """Test that numbers are removed"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Force of Will") == "force-of-will"
    
    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("The  Gitrog  Monster") == "the-gitrog-monster"
    
    def test_leading_trailing_spaces(self):
        """Test trimming of leading/trailing spaces"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("  Sol Ring  ") == "sol-ring"
    
    def test_parentheses_removal(self):
        """Test removal of parentheses"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Lightning Bolt (Promo)") == "lightning-bolt-promo"
    
    def test_hyphenated_name(self):
        """Test card with existing hyphens"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Jace, the Mind Sculptor") == "jace-the-mind-sculptor"
    
    def test_all_caps(self):
        """Test uppercase conversion"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("COUNTERSPELL") == "counterspell"
    
    def test_mixed_case(self):
        """Test mixed case conversion"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("CyClOnIc RiFt") == "cyclonic-rift"
    
    def test_double_slash_name(self):
        """Test card with // (split cards)"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Fire // Ice") == "fire-ice"
    
    def test_complex_name(self):
        """Test complex card name with multiple special chars"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Urza's Saga") == "urzas-saga"
    
    def test_very_long_name(self):
        """Test very long card name"""
        name = "The Gitrog Monster"
        expected = "the-gitrog-monster"
        assert EDHRECPlaywrightScraper.card_name_to_url_slug(name) == expected
    
    def test_empty_string(self):
        """Test empty string"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("") == ""
    
    def test_only_special_chars(self):
        """Test string with only special characters"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("!!!") == ""
    
    def test_planeswalker_name(self):
        """Test planeswalker name format"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Vraska, Betrayal's Sting") == "vraska-betrayals-sting"
    
    def test_legendary_creature(self):
        """Test legendary creature name"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Tekuthal, Inquiry Dominus") == "tekuthal-inquiry-dominus"
    
    def test_land_name(self):
        """Test land card name"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Command Tower") == "command-tower"
    
    def test_artifact_name(self):
        """Test artifact card name"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Sol Ring") == "sol-ring"
    
    def test_instant_name(self):
        """Test instant card name"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Swords to Plowshares") == "swords-to-plowshares"
    
    def test_sorcery_name(self):
        """Test sorcery card name"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Demonic Tutor") == "demonic-tutor"
    
    def test_enchantment_name(self):
        """Test enchantment card name"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Doubling Season") == "doubling-season"
    
    def test_consecutive_dashes(self):
        """Test that multiple consecutive dashes are collapsed"""
        # Input with multiple spaces/special chars should produce single dashes
        assert EDHRECPlaywrightScraper.card_name_to_url_slug("Card  -  Name") == "card-name"


class TestScraperInit:
    """Test scraper initialization"""
    
    def test_default_init(self):
        """Test scraper with default settings"""
        scraper = EDHRECPlaywrightScraper()
        assert scraper.headless == True
        assert scraper.output_dir.name == "edhrec_scraped"
    
    def test_custom_output_dir(self):
        """Test scraper with custom output directory"""
        custom_dir = "/tmp/test_edhrec"
        scraper = EDHRECPlaywrightScraper(output_dir=custom_dir)
        assert str(scraper.output_dir) == custom_dir
    
    def test_headless_false(self):
        """Test scraper with headless=False"""
        scraper = EDHRECPlaywrightScraper(headless=False)
        assert scraper.headless == False


class TestRealWorldExamples:
    """Test with real card names from EDHREC"""
    
    @pytest.mark.parametrize("card_name,expected_slug", [
        ("Tekuthal, Inquiry Dominus", "tekuthal-inquiry-dominus"),
        ("Evolution Sage", "evolution-sage"),
        ("Karn's Bastion", "karns-bastion"),
        ("Ezuri, Stalker of Spheres", "ezuri-stalker-of-spheres"),
        ("Vraska, Betrayal's Sting", "vraska-betrayals-sting"),
        ("Rhystic Study", "rhystic-study"),
        ("Cyclonic Rift", "cyclonic-rift"),
        ("Sol Ring", "sol-ring"),
        ("Command Tower", "command-tower"),
        ("Swords to Plowshares", "swords-to-plowshares"),
        ("Abandoned Air Temple", "abandoned-air-temple"),
        ("Wan Shi Tong, Librarian", "wan-shi-tong-librarian"),
        ("Tale of Katara and Toph", "tale-of-katara-and-toph"),
        ("Toph, Earthbending Master", "toph-earthbending-master"),
        ("Atraxa, Praetors' Voice", "atraxa-praetors-voice"),
        ("Atraxa, Grand Unifier", "atraxa-grand-unifier"),
        ("Tamiyo, Field Researcher", "tamiyo-field-researcher"),
        ("Ajani, Sleeper Agent", "ajani-sleeper-agent"),
        ("The Gitrog Monster", "the-gitrog-monster"),
        ("Urza's Saga", "urzas-saga"),
        ("Teferi's Protection", "teferis-protection"),
        ("Edgar Markov", "edgar-markov"),
        ("K'rrik, Son of Yawgmoth", "krrik-son-of-yawgmoth"),
        ("Korvold, Fae-Cursed King", "korvold-fae-cursed-king"),
        ("Muldrotha, the Gravetide", "muldrotha-the-gravetide"),
        ("Kinnan, Bonder Prodigy", "kinnan-bonder-prodigy"),
        ("Yuriko, the Tiger's Shadow", "yuriko-the-tigers-shadow"),
        ("Chulane, Teller of Tales", "chulane-teller-of-tales"),
        ("Golos, Tireless Pilgrim", "golos-tireless-pilgrim"),
        ("Zur the Enchanter", "zur-the-enchanter"),
    ])
    def test_real_card_names(self, card_name, expected_slug):
        """Test conversion of real EDHREC card names"""
        assert EDHRECPlaywrightScraper.card_name_to_url_slug(card_name) == expected_slug


def run_tests():
    """Run all tests and print results"""
    print("="*70)
    print("EDHREC Scraper - Test Suite")
    print("="*70)
    
    # Run pytest
    import pytest
    exit_code = pytest.main([
        __file__, 
        "-v",
        "--tb=short",
        "-k", "test_"
    ])
    
    return exit_code


if __name__ == "__main__":
    exit(run_tests())
