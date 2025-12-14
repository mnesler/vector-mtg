"""
Data models for MTG card tag extraction.

This module contains the data structures used throughout the embeddings system.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TagResult:
    """Result of tag extraction for a single tag"""
    tag: str
    confidence: float
    reasoning: Optional[str] = None


@dataclass
class CardTagExtraction:
    """Complete tag extraction result for a card"""
    card_id: str
    card_name: str
    tags: List[TagResult]
    extraction_successful: bool
    error_message: Optional[str] = None
