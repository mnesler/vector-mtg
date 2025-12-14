"""
Shared test fixtures for embeddings module tests.
"""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_card_data():
    """Sample MTG card data for testing"""
    return {
        'id': 'test-uuid-12345',
        'name': 'Sol Ring',
        'type_line': 'Artifact',
        'oracle_text': '{T}: Add {C}{C}.',
        'keywords': [],
        'mana_cost': '{1}',
        'cmc': 1.0
    }


@pytest.fixture
def sample_tags():
    """Sample tag taxonomy data"""
    return [
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
        },
        {
            'name': 'generates_colorless_mana',
            'display_name': 'Generates Colorless Mana',
            'description': 'Produces colorless mana',
            'category': 'Resource Generation',
            'is_combo_relevant': True,
            'depth': 1,
            'parent_tag_id': 'parent-uuid',
            'parent_tag_name': 'generates_mana'
        }
    ]


@pytest.fixture
def mock_db_cursor():
    """Mock database cursor for testing"""
    cursor = MagicMock()
    cursor.fetchall = Mock(return_value=[])
    cursor.fetchone = Mock(return_value=None)
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    return cursor


@pytest.fixture
def mock_db_connection(mock_db_cursor):
    """Mock database connection for testing"""
    conn = MagicMock()
    conn.cursor = Mock(return_value=mock_db_cursor)
    conn.__enter__ = Mock(return_value=conn)
    conn.__exit__ = Mock(return_value=False)
    return conn


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""
    client = MagicMock()
    mock_response = Mock()
    mock_response.content = [Mock(text='[{"tag": "artifact", "confidence": 1.0}]')]
    client.messages.create = Mock(return_value=mock_response)
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API client"""
    client = MagicMock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='[{"tag": "artifact", "confidence": 1.0}]'))]
    client.chat.completions.create = Mock(return_value=mock_response)
    return client


@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence-transformers model"""
    import numpy as np
    
    model = MagicMock()
    # Return a mock embedding (384-dimensional vector)
    model.encode = Mock(return_value=np.random.rand(384))
    return model
