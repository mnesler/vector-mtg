"""
Embeddings module for MTG card analysis.

This module provides functionality for:
- Generating vector embeddings for cards and rules
- Extracting functional tags from cards using LLMs
- Rate limiting and API management
"""

# Public API exports
from .models import TagResult, CardTagExtraction
from .rate_limit_handler import handle_rate_limit
from .prompt_builder import build_tag_extraction_prompt
from .database import (
    get_default_db_connection_string,
    load_tag_taxonomy,
    store_card_tags
)

__all__ = [
    'TagResult',
    'CardTagExtraction',
    'handle_rate_limit',
    'build_tag_extraction_prompt',
    'get_default_db_connection_string',
    'load_tag_taxonomy',
    'store_card_tags',
]
