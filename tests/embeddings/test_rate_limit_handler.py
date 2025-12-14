"""
Tests for Rate Limit Handler
=============================
Tests the rate limiting detection and retry logic for the Claude API.

Run with: pytest test_rate_limit_handler.py -v
"""

import pytest
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from anthropic import RateLimitError

# Import from embeddings module
from scripts.embeddings.extract_card_tags import CardTagExtractor
from scripts.embeddings.rate_limit_handler import handle_rate_limit


class TestRateLimitHandler:
    """Test suite for rate limit handling"""

    def test_handle_rate_limit_with_retry_after_header(self):
        """Test that we correctly parse retry-after header and wait"""
        # Create a mock RateLimitError with retry-after header
        mock_response = Mock()
        mock_response.headers = {
            'retry-after': '5',  # Wait 5 seconds
            'x-ratelimit-limit-requests': '50',
            'x-ratelimit-remaining-requests': '0',
            'x-ratelimit-reset-requests': str(int(time.time()) + 60)
        }

        error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error", "message": "Rate limit exceeded"}}
        )

        # Mock time.sleep to avoid actual waiting in tests
        with patch('time.sleep') as mock_sleep:
            wait_time = handle_rate_limit(error)

            # Should return the wait time
            assert wait_time == 5

            # Should have called sleep with 5 seconds + 1 second buffer
            mock_sleep.assert_called_once_with(6)

    def test_handle_rate_limit_with_reset_timestamp(self):
        """Test that we calculate wait time from reset timestamp if no retry-after"""
        current_time = time.time()
        reset_time = current_time + 30  # Reset in 30 seconds

        mock_response = Mock()
        mock_response.headers = {
            'x-ratelimit-limit-requests': '50',
            'x-ratelimit-remaining-requests': '0',
            'x-ratelimit-reset-requests': str(reset_time)
        }

        error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        with patch('time.sleep') as mock_sleep, \
             patch('time.time', return_value=current_time):
            wait_time = handle_rate_limit(error)

            # Should calculate from reset timestamp
            assert wait_time == pytest.approx(30, abs=1)

            # Should sleep for calculated time + buffer
            assert mock_sleep.call_args[0][0] == pytest.approx(31, abs=1)

    def test_handle_rate_limit_with_no_headers(self):
        """Test fallback to default wait time when no headers present"""
        mock_response = Mock()
        mock_response.headers = {}

        error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        with patch('time.sleep') as mock_sleep:
            wait_time = handle_rate_limit(error, default_wait=60)

            # Should use default wait time
            assert wait_time == 60

            # Should sleep for default + buffer
            mock_sleep.assert_called_once_with(61)

    def test_handle_rate_limit_respects_custom_buffer(self):
        """Test that custom buffer is applied correctly"""
        mock_response = Mock()
        mock_response.headers = {'retry-after': '10'}

        error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        with patch('time.sleep') as mock_sleep:
            wait_time = handle_rate_limit(error, buffer_seconds=5)

            assert wait_time == 10
            # Should add 5 second buffer instead of default 1
            mock_sleep.assert_called_once_with(15)


class TestCardTagExtractorWithRateLimit:
    """Test CardTagExtractor handles rate limits correctly during extraction"""

    @pytest.fixture
    def mock_extractor(self):
        """Create a CardTagExtractor with mocked API client"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test-key'}), \
             patch('scripts.embeddings.extract_card_tags.Anthropic') as mock_anthropic_class:

            # Mock the Anthropic client class to return a mock instance
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client

            # Create extractor (will use the mocked Anthropic class)
            extractor = CardTagExtractor()

            # Set up mock data
            extractor.tag_taxonomy_loaded = True
            extractor.available_tags = [
                {
                    'name': 'artifact',
                    'display_name': 'Artifact',
                    'description': 'Artifact card',
                    'category': 'Card Types',
                    'is_combo_relevant': False,
                    'depth': 0,
                    'parent_tag_id': None,
                    'parent_tag_name': None
                },
                {
                    'name': 'generates_mana',
                    'display_name': 'Generates Mana',
                    'description': 'Produces mana',
                    'category': 'Resource Generation',
                    'is_combo_relevant': True,
                    'depth': 0,
                    'parent_tag_id': None,
                    'parent_tag_name': None
                }
            ]
            yield extractor

    def test_extraction_succeeds_on_first_try(self, mock_extractor):
        """Test normal extraction without rate limit"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.content = [Mock(text='[{"tag": "artifact", "confidence": 1.0}]')]
        mock_extractor.client.messages.create.return_value = mock_response

        result = mock_extractor.extract_tags(
            card_name="Sol Ring",
            oracle_text="{T}: Add {C}{C}.",
            type_line="Artifact"
        )

        assert result.extraction_successful
        assert len(result.tags) == 1
        assert result.tags[0].tag == "artifact"
        assert result.tags[0].confidence == 1.0

        # Should have called API once
        assert mock_extractor.client.messages.create.call_count == 1

    def test_extraction_retries_on_rate_limit(self, mock_extractor):
        """Test that extraction retries after rate limit and succeeds"""
        # First call raises RateLimitError, second succeeds
        mock_response = Mock()
        mock_response.headers = {'retry-after': '2'}

        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        success_response = Mock()
        success_response.content = [Mock(text='[{"tag": "generates_mana", "confidence": 0.95}]')]

        mock_extractor.client.messages.create.side_effect = [
            rate_limit_error,  # First call fails
            success_response   # Second call succeeds
        ]

        with patch('time.sleep') as mock_sleep:
            result = mock_extractor.extract_tags(
                card_name="Test Card",
                oracle_text="Add {C}.",
                type_line="Artifact"
            )

        # Should succeed on retry
        assert result.extraction_successful
        assert len(result.tags) == 1
        assert result.tags[0].tag == "generates_mana"

        # Should have called API twice (initial + retry)
        assert mock_extractor.client.messages.create.call_count == 2

        # Should have slept for rate limit duration
        mock_sleep.assert_called_once_with(3)  # 2 seconds + 1 buffer

    def test_extraction_retries_multiple_times(self, mock_extractor):
        """Test that extraction retries multiple times on repeated rate limits"""
        mock_response = Mock()
        mock_response.headers = {'retry-after': '1'}

        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        success_response = Mock()
        success_response.content = [Mock(text='[{"tag": "artifact", "confidence": 1.0}]')]

        # Fail twice, then succeed
        mock_extractor.client.messages.create.side_effect = [
            rate_limit_error,
            rate_limit_error,
            success_response
        ]

        with patch('time.sleep') as mock_sleep:
            result = mock_extractor.extract_tags(
                card_name="Test Card",
                oracle_text="Test text",
                type_line="Artifact"
            )

        # Should eventually succeed
        assert result.extraction_successful

        # Should have called API 3 times
        assert mock_extractor.client.messages.create.call_count == 3

        # Should have slept twice
        assert mock_sleep.call_count == 2

    def test_extraction_fails_after_max_retries(self, mock_extractor):
        """Test that extraction gives up after max retries"""
        mock_response = Mock()
        mock_response.headers = {'retry-after': '1'}

        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        # Always fail with rate limit
        mock_extractor.client.messages.create.side_effect = rate_limit_error

        with patch('time.sleep'):
            result = mock_extractor.extract_tags(
                card_name="Test Card",
                oracle_text="Test text",
                type_line="Artifact",
                max_retries=3
            )

        # Should fail after max retries
        assert not result.extraction_successful
        assert "Rate limit exceeded after 3 retries" in result.error_message

        # Should have tried max_retries + 1 times (initial + retries)
        assert mock_extractor.client.messages.create.call_count == 4

    def test_extraction_logs_rate_limit_info(self, mock_extractor, caplog):
        """Test that rate limit encounters are logged"""
        import logging
        caplog.set_level(logging.INFO)  # Changed from WARNING to capture INFO logs too

        mock_response = Mock()
        mock_response.headers = {
            'retry-after': '5',
            'x-ratelimit-limit-requests': '50',
            'x-ratelimit-remaining-requests': '0'
        }

        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"type": "rate_limit_error"}}
        )

        success_response = Mock()
        success_response.content = [Mock(text='[{"tag": "artifact", "confidence": 1.0}]')]

        mock_extractor.client.messages.create.side_effect = [
            rate_limit_error,
            success_response
        ]

        with patch('time.sleep'):
            result = mock_extractor.extract_tags(
                card_name="Test Card",
                oracle_text="Test",
                type_line="Artifact"
            )

        # Should have logged the rate limit
        assert any("Rate limit hit" in record.message for record in caplog.records)
        assert any("Waiting 5s" in record.message for record in caplog.records)


class TestRateLimitHeaderParsing:
    """Test parsing of different rate limit header formats"""

    def test_parse_integer_retry_after(self):
        """Test parsing retry-after as integer seconds"""
        mock_response = Mock()
        mock_response.headers = {'retry-after': '30'}

        error = RateLimitError(
            message="Rate limit",
            response=mock_response,
            body={}
        )

        with patch('time.sleep'):
            wait_time = handle_rate_limit(error)
            assert wait_time == 30

    def test_parse_float_reset_timestamp(self):
        """Test parsing reset timestamp as float"""
        current_time = 1234567890.5
        reset_time = current_time + 45.3

        mock_response = Mock()
        mock_response.headers = {
            'x-ratelimit-reset-requests': str(reset_time)
        }

        error = RateLimitError(
            message="Rate limit",
            response=mock_response,
            body={}
        )

        with patch('time.sleep'), \
             patch('time.time', return_value=current_time):
            wait_time = handle_rate_limit(error)
            assert wait_time == pytest.approx(45.3, abs=0.5)

    def test_handle_malformed_headers(self):
        """Test graceful handling of malformed header values"""
        mock_response = Mock()
        mock_response.headers = {
            'retry-after': 'invalid',  # Non-numeric
            'x-ratelimit-reset-requests': 'also-invalid'
        }

        error = RateLimitError(
            message="Rate limit",
            response=mock_response,
            body={}
        )

        with patch('time.sleep'):
            # Should fall back to default
            wait_time = handle_rate_limit(error, default_wait=60)
            assert wait_time == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
