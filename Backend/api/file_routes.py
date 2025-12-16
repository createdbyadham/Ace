"""
API routes for file storage.

Endpoints:
- POST /files/upload - Upload a file (saves + indexes to RAG)
- GET /files - List user's files
- GET /files/{file_id} - Get file metadata
- GET /files/{file_id}/download - Download file content
- PATCH /files/{file_id} - Move/rename file
- DELETE /files/{file_id} - Delete file (also removes from RAG)
- GET /files/folders - List user's folders
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from api.auth import CurrentUser, get_current_user
from domain.chatbot.service import ChatbotService, get_chatbot_service
from domain.files.models import FileListOut, FileMoveRequest, FileOut
from domain.files.service import FileStorageService, get_file_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    folder_path: str = Form(default="/", description="Logical folder path"),
    user: CurrentUser = Depends(get_current_user),
    file_service: FileStorageService = Depends(get_file_service),
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    """
    Upload a PDF file.
    
    The file will be:
    1. Stored in your personal storage
    2. Indexed into RAG for AI chat queries
    
    Args:
        file: PDF file to upload
        folder_path: Logical folder path (e.g. "/lectures/week1")
        
    Returns:
        File metadata including document_id for RAG reference
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )
    
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type. Expected application/pdf",
        )
    
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file",
            )
        
        # Index into RAG (existing chatbot service)
        chunks_created, document_id = chatbot_service.upload_pdf(pdf_bytes, file.filename)
        
        # Save to file storage with RAG reference
        meta = file_service.save_file(
            user_id=user.id,
            file_bytes=pdf_bytes,
            filename=file.filename,
            document_id=document_id,
            folder_path=folder_path,
        )
        
        return FileOut(
            file_id=meta.file_id,
            filename=meta.filename,
            folder_path=meta.folder_path,
            size_bytes=meta.size_bytes,
            content_type=meta.content_type,
            created_at=meta.created_at,
            document_id=meta.document_id,
        )
    
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload error: {str(exc)}",
        ) from exc


@router.get("", response_model=FileListOut)
async def list_files(
    folder_path: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
    service: FileStorageService = Depends(get_file_service),
):
    """
    List your uploaded files.
    
    Args:
        folder_path: Filter by folder (optional)
        
    Returns:
        List of files with metadata
    """
    files = service.list_files(user_id=user.id, folder_path=folder_path)
    return FileListOut(files=files, total=len(files))


@router.get("/folders")
async def list_folders(
    user: CurrentUser = Depends(get_current_user),
    service: FileStorageService = Depends(get_file_service),
):
    """
    List your folder paths.
    
    Returns unique folder paths from all uploaded files.
    """
    folders = service.get_folders(user.id)
    return {"folders": folders}


@router.get("/{file_id}", response_model=FileOut)
async def get_file(
    file_id: str,
    user: CurrentUser = Depends(get_current_user),
    service: FileStorageService = Depends(get_file_service),
):
    """Get file metadata by ID."""
    file = service.get_file(user.id, file_id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    user: CurrentUser = Depends(get_current_user),
    service: FileStorageService = Depends(get_file_service),
):
    """
    Download file content.
    
    Returns the raw PDF file.
    """
    # Get metadata for filename
    file_meta = service.get_file(user.id, file_id)
    if file_meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Get file bytes
    file_bytes = service.get_file_bytes(user.id, file_id)
    if file_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content not found",
        )
    
    return Response(
        content=file_bytes,
        media_type=file_meta.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_meta.filename}"'
        },
    )


@router.patch("/{file_id}", response_model=FileOut)
async def move_file(
    file_id: str,
    payload: FileMoveRequest,
    user: CurrentUser = Depends(get_current_user),
    service: FileStorageService = Depends(get_file_service),
):
    """
    Move or rename a file.
    
    Only updates the logical path - does NOT affect RAG indexing.
    
    Args:
        folder_path: New folder path (optional)
        filename: New filename (optional)
    """
    if payload.folder_path is None and payload.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of folder_path or filename must be provided",
        )
    
    result = service.move_file(
        user_id=user.id,
        file_id=file_id,
        folder_path=payload.folder_path,
        filename=payload.filename,
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    return result


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user: CurrentUser = Depends(get_current_user),
    service: FileStorageService = Depends(get_file_service),
):
    """
    Delete a file.
    
    This removes:
    1. The file from storage
    2. All RAG/ChromaDB entries for this document
    """
    deleted = service.delete_file(user.id, file_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return {"message": "File deleted", "file_id": file_id}


__all__ = ["router"]

