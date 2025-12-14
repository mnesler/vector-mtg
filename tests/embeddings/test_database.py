"""
Tests for embeddings.database module.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.embeddings.database import (
    get_default_db_connection_string,
    load_tag_taxonomy,
    store_card_tags
)
from scripts.embeddings.models import CardTagExtraction, TagResult
from .fixtures import sample_tags, mock_db_connection, mock_db_cursor


class TestGetDefaultDbConnectionString:
    """Test suite for database connection string generation."""

    def test_uses_default_values_when_env_not_set(self):
        """Test that default values are used when env vars are not set."""
        with patch.dict(os.environ, {}, clear=True):
            conn_str = get_default_db_connection_string()
            
            assert "postgresql://" in conn_str
            assert "postgres:postgres" in conn_str
            assert "localhost:5432" in conn_str
            assert "vector_mtg" in conn_str

    def test_uses_environment_variables(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_HOST': 'testhost',
            'POSTGRES_PORT': '5433',
            'POSTGRES_DB': 'testdb'
        }):
            conn_str = get_default_db_connection_string()
            
            assert "testuser:testpass" in conn_str
            assert "testhost:5433" in conn_str
            assert "testdb" in conn_str

    def test_returns_valid_postgres_url_format(self):
        """Test that returned string is valid PostgreSQL URL format."""
        conn_str = get_default_db_connection_string()
        
        assert conn_str.startswith("postgresql://")
        assert "@" in conn_str
        assert "/" in conn_str


class TestLoadTagTaxonomy:
    """Test suite for tag taxonomy loading."""

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_loads_tags_from_database(self, mock_connect, mock_db_connection, mock_db_cursor, sample_tags):
        """Test that tags are loaded from database correctly."""
        # Setup mock
        mock_cursor_instance = MagicMock()
        mock_cursor_instance.fetchall = Mock(return_value=sample_tags)
        mock_cursor_instance.__enter__ = Mock(return_value=mock_cursor_instance)
        mock_cursor_instance.__exit__ = Mock(return_value=False)
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor = Mock(return_value=mock_cursor_instance)
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        
        mock_connect.return_value = mock_conn_instance

        # Execute
        tags = load_tag_taxonomy("postgresql://test")

        # Verify
        assert len(tags) == 3
        assert tags[0]['name'] == 'artifact'
        assert tags[1]['name'] == 'generates_mana'
        mock_connect.assert_called_once()

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_returns_empty_list_when_no_tags(self, mock_connect):
        """Test that empty list is returned when no tags exist."""
        # Setup mock
        mock_cursor_instance = MagicMock()
        mock_cursor_instance.fetchall = Mock(return_value=[])
        mock_cursor_instance.__enter__ = Mock(return_value=mock_cursor_instance)
        mock_cursor_instance.__exit__ = Mock(return_value=False)
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor = Mock(return_value=mock_cursor_instance)
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        
        mock_connect.return_value = mock_conn_instance

        # Execute
        tags = load_tag_taxonomy("postgresql://test")

        # Verify
        assert tags == []

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_includes_all_required_fields(self, mock_connect, sample_tags):
        """Test that all required fields are present in returned tags."""
        # Setup mock
        mock_cursor_instance = MagicMock()
        mock_cursor_instance.fetchall = Mock(return_value=sample_tags)
        mock_cursor_instance.__enter__ = Mock(return_value=mock_cursor_instance)
        mock_cursor_instance.__exit__ = Mock(return_value=False)
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor = Mock(return_value=mock_cursor_instance)
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        
        mock_connect.return_value = mock_conn_instance

        # Execute
        tags = load_tag_taxonomy("postgresql://test")

        # Verify required fields
        required_fields = ['name', 'display_name', 'description', 'category',
                          'is_combo_relevant', 'depth', 'parent_tag_id', 'parent_tag_name']
        
        for tag in tags:
            for field in required_fields:
                assert field in tag


class TestStoreCardTags:
    """Test suite for storing card tags."""

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_stores_tags_successfully(self, mock_connect):
        """Test that tags are stored in database correctly."""
        # Setup mock
        mock_cursor_instance = MagicMock()
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor = Mock(return_value=mock_cursor_instance)
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_cursor_instance.__enter__ = Mock(return_value=mock_cursor_instance)
        mock_cursor_instance.__exit__ = Mock(return_value=False)
        
        mock_connect.return_value = mock_conn_instance

        # Create extraction
        extraction = CardTagExtraction(
            card_id='test-uuid-123',
            card_name='Sol Ring',
            tags=[
                TagResult(tag='artifact', confidence=1.0),
                TagResult(tag='generates_mana', confidence=1.0)
            ],
            extraction_successful=True
        )

        # Execute
        result = store_card_tags(
            extraction=extraction,
            db_conn_string="postgresql://test",
            llm_model="claude-3-5-haiku-20241022",
            extraction_prompt_version="1.0"
        )

        # Verify
        assert result is True
        mock_connect.assert_called_once()
        # Should execute DELETE + 2 INSERT statements
        assert mock_cursor_instance.execute.call_count == 3

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_returns_false_when_extraction_failed(self, mock_connect):
        """Test that function returns False when extraction was unsuccessful."""
        extraction = CardTagExtraction(
            card_id='test-uuid-123',
            card_name='Sol Ring',
            tags=[],
            extraction_successful=False,
            error_message="API error"
        )

        result = store_card_tags(
            extraction=extraction,
            db_conn_string="postgresql://test",
            llm_model="claude-3-5-haiku-20241022"
        )

        assert result is False
        mock_connect.assert_not_called()

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_returns_false_when_no_card_id(self, mock_connect):
        """Test that function returns False when card_id is missing."""
        extraction = CardTagExtraction(
            card_id='',
            card_name='Sol Ring',
            tags=[TagResult(tag='artifact', confidence=1.0)],
            extraction_successful=True
        )

        result = store_card_tags(
            extraction=extraction,
            db_conn_string="postgresql://test",
            llm_model="claude-3-5-haiku-20241022"
        )

        assert result is False
        mock_connect.assert_not_called()

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_deletes_existing_tags_before_inserting(self, mock_connect):
        """Test that existing tags are deleted before new ones are inserted."""
        # Setup mock
        mock_cursor_instance = MagicMock()
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor = Mock(return_value=mock_cursor_instance)
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_cursor_instance.__enter__ = Mock(return_value=mock_cursor_instance)
        mock_cursor_instance.__exit__ = Mock(return_value=False)
        
        mock_connect.return_value = mock_conn_instance

        extraction = CardTagExtraction(
            card_id='test-uuid-123',
            card_name='Sol Ring',
            tags=[TagResult(tag='artifact', confidence=1.0)],
            extraction_successful=True
        )

        store_card_tags(
            extraction=extraction,
            db_conn_string="postgresql://test",
            llm_model="claude-3-5-haiku-20241022"
        )

        # First call should be DELETE
        first_call = mock_cursor_instance.execute.call_args_list[0]
        assert "DELETE" in first_call[0][0]

    @patch('scripts.embeddings.database.psycopg2.connect')
    def test_handles_database_errors_gracefully(self, mock_connect):
        """Test that database errors are handled and return False."""
        # Setup mock to raise error
        mock_connect.side_effect = Exception("Database connection failed")

        extraction = CardTagExtraction(
            card_id='test-uuid-123',
            card_name='Sol Ring',
            tags=[TagResult(tag='artifact', confidence=1.0)],
            extraction_successful=True
        )

        result = store_card_tags(
            extraction=extraction,
            db_conn_string="postgresql://test",
            llm_model="claude-3-5-haiku-20241022"
        )

        assert result is False
