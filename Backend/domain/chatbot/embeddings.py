"""
Embedding generation for RAG.

Uses sentence-transformers for local embedding generation.
"""
from __future__ import annotations

import os
from threading import Lock
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from core.config import settings


class EmbeddingService:
    """
    Singleton embedding service using sentence-transformers.
    
    Default model: all-MiniLM-L6-v2 (fast, good quality)
    """
    
    _instance: Optional["EmbeddingService"] = None
    _lock: Lock = Lock()
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    # Disable any cached HF token to avoid auth issues with public models
                    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
                    self._model = SentenceTransformer(
                        settings.embedding_model,
                        token=False,  # Explicitly disable token auth
                    )
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed([text])[0]


def get_embedding_service() -> EmbeddingService:
    """Dependency injection helper."""
    return EmbeddingService()


__all__ = ["EmbeddingService", "get_embedding_service"]

