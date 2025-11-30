#!/usr/bin/env python3
"""
Embedding service for generating query embeddings.
Used by semantic search to convert text queries into vectors.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single text string.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty input
            return [0.0] * self.embedding_dim

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()


# Global singleton instance
_embedding_service = None


def get_embedding_service(model_name: str = 'all-MiniLM-L6-v2') -> EmbeddingService:
    """
    Get or create the global embedding service instance.
    Uses singleton pattern to avoid loading the model multiple times.

    Args:
        model_name: Name of the sentence-transformers model

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name)
    return _embedding_service
