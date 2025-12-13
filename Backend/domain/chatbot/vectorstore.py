"""
ChromaDB Singleton for RAG vector storage.

Uses a singleton pattern to ensure only one ChromaDB client instance exists.
"""
from __future__ import annotations

import os
from threading import Lock
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings


class ChromaDBSingleton:
    """Thread-safe singleton for ChromaDB client."""
    
    _instance: Optional[chromadb.ClientAPI] = None
    _lock: Lock = Lock()
    _collection_name: str = "pdf_documents"
    
    @classmethod
    def get_client(cls) -> chromadb.ClientAPI:
        """Get or create the ChromaDB client instance."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    persist_dir = settings.chroma_persist_dir
                    os.makedirs(persist_dir, exist_ok=True)
                    
                    cls._instance = chromadb.PersistentClient(
                        path=persist_dir,
                        settings=ChromaSettings(
                            anonymized_telemetry=False,
                            allow_reset=True,
                        )
                    )
        return cls._instance
    
    @classmethod
    def get_collection(cls) -> chromadb.Collection:
        """Get or create the main document collection."""
        client = cls.get_client()
        return client.get_or_create_collection(
            name=cls._collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.reset()
            cls._instance = None


def get_vectorstore() -> chromadb.Collection:
    """Dependency injection helper to get the ChromaDB collection."""
    return ChromaDBSingleton.get_collection()


__all__ = ["ChromaDBSingleton", "get_vectorstore"]

