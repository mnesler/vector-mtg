"""
Tests for embeddings.prompt_builder module.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.embeddings.prompt_builder import build_tag_extraction_prompt
from .fixtures import sample_card_data, sample_tags


class TestBuildTagExtractionPrompt:
    """Test suite for prompt building logic."""

    def test_builds_valid_prompt_structure(self, sample_card_data, sample_tags):
        """Test that prompt includes all required sections."""
        prompt = build_tag_extraction_prompt(
            card_name=sample_card_data['name'],
            oracle_text=sample_card_data['oracle_text'],
            type_line=sample_card_data['type_line'],
            available_tags=sample_tags
        )

        # Check required sections present
        assert "CARD TO ANALYZE:" in prompt
        assert "AVAILABLE TAGS:" in prompt
        assert "INSTRUCTIONS:" in prompt
        assert "OUTPUT FORMAT:" in prompt
        assert "EXAMPLES:" in prompt

    def test_includes_card_information(self, sample_card_data, sample_tags):
        """Test that prompt includes card details."""
        prompt = build_tag_extraction_prompt(
            card_name=sample_card_data['name'],
            oracle_text=sample_card_data['oracle_text'],
            type_line=sample_card_data['type_line'],
            available_tags=sample_tags
        )

        assert sample_card_data['name'] in prompt
        assert sample_card_data['oracle_text'] in prompt
        assert sample_card_data['type_line'] in prompt

    def test_organizes_tags_by_category(self, sample_tags):
        """Test that tags are grouped by category."""
        prompt = build_tag_extraction_prompt(
            card_name="Test Card",
            oracle_text="Test text",
            type_line="Artifact",
            available_tags=sample_tags
        )

        # Check category headers present
        assert "**Card Types:**" in prompt
        assert "**Resource Generation:**" in prompt

    def test_shows_tag_hierarchy(self, sample_tags):
        """Test that child tags are indented under parents."""
        prompt = build_tag_extraction_prompt(
            card_name="Test Card",
            oracle_text="Test text",
            type_line="Artifact",
            available_tags=sample_tags
        )

        # Child tag should be indented
        assert "generates_mana" in prompt
        assert "generates_colorless_mana" in prompt
        
        # Check parent reference
        assert "(child of generates_mana)" in prompt

    def test_handles_empty_oracle_text(self, sample_tags):
        """Test that prompt handles cards with no text."""
        prompt = build_tag_extraction_prompt(
            card_name="Vanilla Creature",
            oracle_text="",
            type_line="Creature — Human",
            available_tags=sample_tags
        )

        assert "(No text)" in prompt

    def test_includes_confidence_scoring_guidelines(self, sample_tags):
        """Test that confidence score guidelines are included."""
        prompt = build_tag_extraction_prompt(
            card_name="Test Card",
            oracle_text="Test text",
            type_line="Artifact",
            available_tags=sample_tags
        )

        # Check confidence guidelines present
        assert "0.95-1.0" in prompt
        assert "Explicitly stated" in prompt
        assert "confidence" in prompt.lower()

    def test_includes_json_examples(self, sample_tags):
        """Test that prompt includes properly formatted JSON examples."""
        prompt = build_tag_extraction_prompt(
            card_name="Test Card",
            oracle_text="Test text",
            type_line="Artifact",
            available_tags=sample_tags
        )

        # Check for JSON structure in examples
        assert '"tag":' in prompt or '{"tag"' in prompt
        assert '"confidence":' in prompt

    def test_handles_special_characters_in_card_text(self, sample_tags):
        """Test that prompt handles mana symbols and special characters."""
        prompt = build_tag_extraction_prompt(
            card_name="Lightning Bolt",
            oracle_text="{R}: Deal 3 damage to any target.",
            type_line="Instant",
            available_tags=sample_tags
        )

        # Should not crash and should include the text
        assert "{R}" in prompt
        assert "Lightning Bolt" in prompt

    def test_prompt_is_non_empty(self, sample_card_data, sample_tags):
        """Test that prompt generates non-empty string."""
        prompt = build_tag_extraction_prompt(
            card_name=sample_card_data['name'],
            oracle_text=sample_card_data['oracle_text'],
            type_line=sample_card_data['type_line'],
            available_tags=sample_tags
        )

        assert len(prompt) > 100  # Should be substantial
        assert isinstance(prompt, str)

    def test_handles_large_tag_taxonomy(self):
        """Test that prompt handles many tags efficiently."""
        # Create a large tag set
        large_tag_set = []
        for i in range(100):
            large_tag_set.append({
                'name': f'tag_{i}',
                'display_name': f'Tag {i}',
                'description': f'Description for tag {i}',
                'category': f'Category {i % 10}',
                'depth': i % 3,
                'parent_tag_id': None,
                'parent_tag_name': None
            })

        prompt = build_tag_extraction_prompt(
            card_name="Test Card",
            oracle_text="Test text",
            type_line="Artifact",
            available_tags=large_tag_set
        )

        # Should handle many tags without error
        assert len(prompt) > 0
        assert "tag_0" in prompt
        assert "tag_99" in prompt
