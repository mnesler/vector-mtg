#!/usr/bin/env python3
"""
Tests for the MTG API search endpoints (keyword and semantic search).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Mock the database connection and embedding service during lifespan
    with patch('api.api_server_rules.psycopg2.connect') as mock_connect, \
         patch('api.api_server_rules.get_embedding_service'):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        from api.api_server_rules import app

        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def mock_db_cursor():
    """Mock database cursor for testing."""
    cursor = MagicMock()
    cursor.fetchall = Mock(return_value=[])
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    return cursor


class TestKeywordSearch:
    """Test suite for keyword search endpoint."""

    def test_keyword_search_empty_query_returns_400(self, client):
        """Test that empty query returns 400 error."""
        with patch('api.api_server_rules.db_conn') as mock_conn:
            response = client.get("/api/cards/keyword?query=")
            assert response.status_code == 400
            assert "cannot be empty" in response.json()["detail"]

    def test_keyword_search_whitespace_query_returns_400(self, client):
        """Test that whitespace-only query returns 400 error."""
        with patch('api.api_server_rules.db_conn') as mock_conn:
            response = client.get("/api/cards/keyword?query=   ")
            assert response.status_code == 400

    def test_keyword_search_valid_query_returns_200(self, client, mock_db_cursor):
        """Test that valid query returns 200 with results."""
        mock_cards = [
            {
                'id': '123',
                'name': 'Lightning Bolt',
                'mana_cost': '{R}',
                'cmc': 1.0,
                'type_line': 'Instant',
                'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
                'keywords': []
            }
        ]
        mock_db_cursor.fetchall.return_value = mock_cards

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/keyword?query=lightning&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert data['query'] == 'lightning'
            assert data['search_type'] == 'keyword'
            assert data['count'] == 1
            assert len(data['cards']) == 1
            assert data['cards'][0]['name'] == 'Lightning Bolt'

    def test_keyword_search_no_results(self, client, mock_db_cursor):
        """Test keyword search with no matching results."""
        mock_db_cursor.fetchall.return_value = []

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/keyword?query=nonexistentcard")

            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 0
            assert data['cards'] == []

    def test_keyword_search_limit_parameter(self, client, mock_db_cursor):
        """Test that limit parameter is respected."""
        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/keyword?query=test&limit=5")

            assert response.status_code == 200
            # Verify limit was passed to query
            mock_db_cursor.execute.assert_called_once()
            call_args = mock_db_cursor.execute.call_args
            assert call_args[0][1][-1] == 5

    def test_keyword_search_default_limit(self, client, mock_db_cursor):
        """Test that default limit is 10."""
        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/keyword?query=test")

            assert response.status_code == 200
            # Verify default limit of 10 was used
            call_args = mock_db_cursor.execute.call_args
            assert call_args[0][1][-1] == 10

    def test_keyword_search_sql_injection_protection(self, client, mock_db_cursor):
        """Test that SQL injection attempts are safely handled."""
        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            malicious_query = "'; DROP TABLE cards; --"
            response = client.get(f"/api/cards/keyword?query={malicious_query}")

            assert response.status_code == 200
            # Verify parameterized query was used (not string concatenation)
            call_args = mock_db_cursor.execute.call_args
            assert len(call_args[0]) == 2  # SQL string and parameters tuple


class TestSemanticSearch:
    """Test suite for semantic search endpoint."""

    @patch('api.api_server_rules.get_embedding_service')
    def test_semantic_search_empty_query_returns_400(self, mock_embedding_service, client):
        """Test that empty query returns 400 error."""
        with patch('api.api_server_rules.db_conn') as mock_conn:
            response = client.get("/api/cards/semantic?query=")
            assert response.status_code == 400
            assert "cannot be empty" in response.json()["detail"]

    @patch('api.api_server_rules.get_embedding_service')
    def test_semantic_search_valid_query_returns_200(self, mock_embedding_service, client, mock_db_cursor):
        """Test that valid semantic query returns 200 with results."""
        # Mock embedding service
        mock_service = Mock()
        mock_service.generate_embedding.return_value = [0.1] * 384
        mock_embedding_service.return_value = mock_service

        # Mock database results
        mock_cards = [
            {
                'id': '456',
                'name': 'Shock',
                'mana_cost': '{R}',
                'cmc': 1.0,
                'type_line': 'Instant',
                'oracle_text': 'Shock deals 2 damage to any target.',
                'keywords': [],
                'similarity': 0.85
            }
        ]
        mock_db_cursor.fetchall.return_value = mock_cards

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/semantic?query=red damage spell")

            assert response.status_code == 200
            data = response.json()
            assert data['query'] == 'red damage spell'
            assert data['search_type'] == 'semantic'
            assert data['count'] == 1
            assert len(data['cards']) == 1
            assert data['cards'][0]['name'] == 'Shock'

    @patch('api.api_server_rules.get_embedding_service')
    def test_semantic_search_generates_embedding(self, mock_embedding_service, client, mock_db_cursor):
        """Test that semantic search calls embedding service."""
        mock_service = Mock()
        mock_service.generate_embedding.return_value = [0.1] * 384
        mock_embedding_service.return_value = mock_service
        mock_db_cursor.fetchall.return_value = []

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/semantic?query=flying creatures")

            assert response.status_code == 200
            mock_service.generate_embedding.assert_called_once_with('flying creatures')

    @patch('api.api_server_rules.get_embedding_service')
    def test_semantic_search_no_results(self, mock_embedding_service, client, mock_db_cursor):
        """Test semantic search with no matching results."""
        mock_service = Mock()
        mock_service.generate_embedding.return_value = [0.1] * 384
        mock_embedding_service.return_value = mock_service
        mock_db_cursor.fetchall.return_value = []

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/semantic?query=nonexistent mechanic")

            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 0
            assert data['cards'] == []

    @patch('api.api_server_rules.get_embedding_service')
    def test_semantic_search_limit_parameter(self, mock_embedding_service, client, mock_db_cursor):
        """Test that limit parameter is respected."""
        mock_service = Mock()
        mock_service.generate_embedding.return_value = [0.1] * 384
        mock_embedding_service.return_value = mock_service

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/semantic?query=test&limit=5")

            assert response.status_code == 200
            # Verify limit was passed to query
            call_args = mock_db_cursor.execute.call_args
            assert call_args[0][1][-1] == 5

    @patch('api.api_server_rules.get_embedding_service')
    def test_semantic_search_uses_vector_similarity(self, mock_embedding_service, client, mock_db_cursor):
        """Test that semantic search uses pgvector similarity operator."""
        mock_service = Mock()
        test_embedding = [0.5] * 384
        mock_service.generate_embedding.return_value = test_embedding
        mock_embedding_service.return_value = mock_service

        with patch('api.api_server_rules.db_conn') as mock_conn:
            mock_conn.cursor.return_value = mock_db_cursor
            response = client.get("/api/cards/semantic?query=test")

            assert response.status_code == 200
            # Verify SQL contains vector similarity operator
            call_args = mock_db_cursor.execute.call_args
            sql_query = call_args[0][0]
            assert '<=>' in sql_query  # pgvector cosine distance operator
            # Verify embedding was passed as parameter
            assert call_args[0][1][0] == test_embedding
