"""
Models for file storage.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Internal file metadata stored in JSON."""
    file_id: str
    user_id: str
    filename: str
    folder_path: str = "/"  # Logical path, e.g. "/lectures/week1"
    document_id: str  # RAG reference for ChromaDB cleanup
    size_bytes: int
    content_type: str = "application/pdf"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FileOut(BaseModel):
    """Public file response model."""
    file_id: str
    filename: str
    folder_path: str
    size_bytes: int
    content_type: str
    created_at: datetime
    document_id: str


class FileMoveRequest(BaseModel):
    """Request to move/rename a file."""
    folder_path: Optional[str] = Field(None, description="New folder path (e.g. '/lectures/week2')")
    filename: Optional[str] = Field(None, description="New filename")


class FileListOut(BaseModel):
    """Response for listing files."""
    files: list[FileOut]
    total: int


__all__ = ["FileMetadata", "FileOut", "FileMoveRequest", "FileListOut"]

