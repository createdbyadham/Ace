"""
File storage service.

Handles user-isolated file storage with metadata tracking.
Files are stored on disk, metadata in JSON files per user.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional
from uuid import UUID, uuid4

import chromadb

from core.config import settings
from domain.chatbot.vectorstore import get_vectorstore
from .models import FileMetadata, FileOut


class FileStorageService:
    """
    User-isolated file storage with RAG integration.
    
    Storage layout:
        {storage_dir}/
            {user_id}/
                metadata.json     # File metadata index
                files/
                    {file_id}.pdf  # Actual files
    """
    
    _lock: Lock = Lock()
    
    def __init__(
        self,
        storage_dir: Optional[str] = None,
        collection: Optional[chromadb.Collection] = None,
    ):
        self.storage_dir = Path(storage_dir or settings.file_storage_dir)
        self.collection = collection or get_vectorstore()
    
    def _user_dir(self, user_id: UUID) -> Path:
        """Get user's storage directory."""
        return self.storage_dir / str(user_id)
    
    def _files_dir(self, user_id: UUID) -> Path:
        """Get user's files directory."""
        return self._user_dir(user_id) / "files"
    
    def _metadata_path(self, user_id: UUID) -> Path:
        """Get path to user's metadata JSON file."""
        return self._user_dir(user_id) / "metadata.json"
    
    def _ensure_user_dirs(self, user_id: UUID) -> None:
        """Create user directories if they don't exist."""
        self._files_dir(user_id).mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self, user_id: UUID) -> dict[str, FileMetadata]:
        """Load user's file metadata from JSON."""
        path = self._metadata_path(user_id)
        if not path.exists():
            return {}
        
        with open(path, "r") as f:
            data = json.load(f)
        
        return {
            k: FileMetadata(**v) for k, v in data.items()
        }
    
    def _save_metadata(self, user_id: UUID, metadata: dict[str, FileMetadata]) -> None:
        """Save user's file metadata to JSON."""
        self._ensure_user_dirs(user_id)
        path = self._metadata_path(user_id)
        
        # Convert to JSON-serializable dict
        data = {}
        for k, v in metadata.items():
            d = v.model_dump()
            d["created_at"] = d["created_at"].isoformat()
            data[k] = d
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def save_file(
        self,
        user_id: UUID,
        file_bytes: bytes,
        filename: str,
        document_id: str,
        folder_path: str = "/",
        content_type: str = "application/pdf",
    ) -> FileMetadata:
        """
        Save a file to storage and record metadata.
        
        Args:
            user_id: Owner's user ID
            file_bytes: File content
            filename: Original filename
            document_id: RAG document ID for cleanup
            folder_path: Logical folder path
            content_type: MIME type
            
        Returns:
            FileMetadata for the saved file
        """
        with self._lock:
            self._ensure_user_dirs(user_id)
            
            file_id = str(uuid4())
            file_path = self._files_dir(user_id) / f"{file_id}.pdf"
            
            # Write file to disk
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            
            # Create metadata
            meta = FileMetadata(
                file_id=file_id,
                user_id=str(user_id),
                filename=filename,
                folder_path=folder_path.strip() or "/",
                document_id=document_id,
                size_bytes=len(file_bytes),
                content_type=content_type,
                created_at=datetime.utcnow(),
            )
            
            # Update metadata index
            all_meta = self._load_metadata(user_id)
            all_meta[file_id] = meta
            self._save_metadata(user_id, all_meta)
            
            return meta
    
    def list_files(
        self,
        user_id: UUID,
        folder_path: Optional[str] = None,
    ) -> list[FileOut]:
        """
        List user's files, optionally filtered by folder.
        
        Args:
            user_id: Owner's user ID
            folder_path: Filter by folder (None = all files)
            
        Returns:
            List of FileOut models
        """
        all_meta = self._load_metadata(user_id)
        
        files = []
        for meta in all_meta.values():
            if folder_path is None or meta.folder_path == folder_path:
                files.append(FileOut(
                    file_id=meta.file_id,
                    filename=meta.filename,
                    folder_path=meta.folder_path,
                    size_bytes=meta.size_bytes,
                    content_type=meta.content_type,
                    created_at=meta.created_at,
                    document_id=meta.document_id,
                ))
        
        # Sort by created_at descending (newest first)
        files.sort(key=lambda x: x.created_at, reverse=True)
        return files
    
    def get_file(self, user_id: UUID, file_id: str) -> Optional[FileOut]:
        """Get file metadata by ID."""
        all_meta = self._load_metadata(user_id)
        meta = all_meta.get(file_id)
        
        if meta is None:
            return None
        
        return FileOut(
            file_id=meta.file_id,
            filename=meta.filename,
            folder_path=meta.folder_path,
            size_bytes=meta.size_bytes,
            content_type=meta.content_type,
            created_at=meta.created_at,
            document_id=meta.document_id,
        )
    
    def get_file_bytes(self, user_id: UUID, file_id: str) -> Optional[bytes]:
        """Read file content from disk."""
        all_meta = self._load_metadata(user_id)
        if file_id not in all_meta:
            return None
        
        file_path = self._files_dir(user_id) / f"{file_id}.pdf"
        if not file_path.exists():
            return None
        
        with open(file_path, "rb") as f:
            return f.read()
    
    def move_file(
        self,
        user_id: UUID,
        file_id: str,
        folder_path: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Optional[FileOut]:
        """
        Move/rename a file (updates logical path only).
        
        Does NOT affect RAG references since document_id stays the same.
        
        Args:
            user_id: Owner's user ID
            file_id: File to move
            folder_path: New folder path (None = keep current)
            filename: New filename (None = keep current)
            
        Returns:
            Updated FileOut or None if not found
        """
        with self._lock:
            all_meta = self._load_metadata(user_id)
            meta = all_meta.get(file_id)
            
            if meta is None:
                return None
            
            # Update fields
            if folder_path is not None:
                meta.folder_path = folder_path.strip() or "/"
            if filename is not None:
                meta.filename = filename.strip()
            
            all_meta[file_id] = meta
            self._save_metadata(user_id, all_meta)
            
            return FileOut(
                file_id=meta.file_id,
                filename=meta.filename,
                folder_path=meta.folder_path,
                size_bytes=meta.size_bytes,
                content_type=meta.content_type,
                created_at=meta.created_at,
                document_id=meta.document_id,
            )
    
    def delete_file(self, user_id: UUID, file_id: str) -> bool:
        """
        Delete a file and remove its RAG entries from ChromaDB.
        
        Args:
            user_id: Owner's user ID
            file_id: File to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            all_meta = self._load_metadata(user_id)
            meta = all_meta.get(file_id)
            
            if meta is None:
                return False
            
            # Delete from ChromaDB using document_id
            # ChromaDB stores chunks with IDs like "doc_xxx_chunk_0"
            # We need to delete all chunks for this document
            try:
                self.collection.delete(
                    where={"document_id": meta.document_id}
                )
            except Exception:
                # ChromaDB might not have the document (already deleted, etc.)
                pass
            
            # Delete file from disk
            file_path = self._files_dir(user_id) / f"{file_id}.pdf"
            if file_path.exists():
                file_path.unlink()
            
            # Remove from metadata
            del all_meta[file_id]
            self._save_metadata(user_id, all_meta)
            
            return True
    
    def get_folders(self, user_id: UUID) -> list[str]:
        """Get list of unique folder paths for a user."""
        all_meta = self._load_metadata(user_id)
        folders = set(meta.folder_path for meta in all_meta.values())
        return sorted(folders)


# Singleton instance
_file_service: Optional[FileStorageService] = None


def get_file_service() -> FileStorageService:
    """Dependency injection helper."""
    global _file_service
    if _file_service is None:
        _file_service = FileStorageService()
    return _file_service


__all__ = ["FileStorageService", "get_file_service"]

