"""
API routes for summaries CRUD operations.

Endpoints:
- GET /summaries - List all summaries for current user
- GET /summaries/{summary_id} - Get a specific summary
- PATCH /summaries/{summary_id} - Update a summary
- DELETE /summaries/{summary_id} - Delete a summary
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.agents.models import SummaryOut, SummaryListResponse

router = APIRouter(prefix="/summaries", tags=["summaries"])


async def _get_summary_by_id(conn: asyncpg.Connection, summary_id: UUID, owner_id: UUID):
    """Helper to get a summary and verify ownership."""
    row = await conn.fetchrow(
        """
        SELECT summary_id, owner_id, title, content, key_points, source_files, 
               word_count, created_at, updated_at
        FROM public.summaries
        WHERE summary_id = $1 AND deleted_at IS NULL
        """,
        summary_id,
    )
    
    if not row:
        return None
    
    if row["owner_id"] != owner_id:
        raise PermissionError("You don't have access to this summary")
    
    return row


@router.get("", response_model=SummaryListResponse)
async def list_summaries(
    search: Optional[str] = Query(None, description="Search in title and content"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    """List all summaries for the current user."""
    async with pool.acquire() as conn:
        if search:
            # Full-text search
            rows = await conn.fetch(
                """
                SELECT summary_id, owner_id, title, content, key_points, source_files, 
                       word_count, created_at, updated_at
                FROM public.summaries
                WHERE owner_id = $1 
                  AND deleted_at IS NULL
                  AND to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $2)
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
                """,
                user.id,
                search,
                limit,
                offset,
            )
            
            count_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as total
                FROM public.summaries
                WHERE owner_id = $1 
                  AND deleted_at IS NULL
                  AND to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', $2)
                """,
                user.id,
                search,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT summary_id, owner_id, title, content, key_points, source_files, 
                       word_count, created_at, updated_at
                FROM public.summaries
                WHERE owner_id = $1 AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user.id,
                limit,
                offset,
            )
            
            count_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as total
                FROM public.summaries
                WHERE owner_id = $1 AND deleted_at IS NULL
                """,
                user.id,
            )
        
        summaries = [
            SummaryOut(
                summary_id=str(row["summary_id"]),
                owner_id=str(row["owner_id"]),
                title=row["title"],
                content=row["content"],
                key_points=row["key_points"] or [],
                source_files=row["source_files"] or [],
                word_count=row["word_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
        
        return SummaryListResponse(summaries=summaries, total=count_row["total"])


@router.get("/{summary_id}", response_model=SummaryOut)
async def get_summary(
    summary_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Get a specific summary by ID."""
    async with pool.acquire() as conn:
        try:
            row = await _get_summary_by_id(conn, summary_id, user.id)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )
        
        return SummaryOut(
            summary_id=str(row["summary_id"]),
            owner_id=str(row["owner_id"]),
            title=row["title"],
            content=row["content"],
            key_points=row["key_points"] or [],
            source_files=row["source_files"] or [],
            word_count=row["word_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@router.patch("/{summary_id}", response_model=SummaryOut)
async def update_summary(
    summary_id: UUID,
    title: Optional[str] = None,
    content: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Update a summary's title or content."""
    async with pool.acquire() as conn:
        # Verify ownership
        try:
            existing = await _get_summary_by_id(conn, summary_id, user.id)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )
        
        # Build update
        updates = []
        params = []
        param_idx = 1
        
        if title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(title)
            param_idx += 1
        
        if content is not None:
            updates.append(f"content = ${param_idx}")
            params.append(content)
            param_idx += 1
            # Recalculate word count
            updates.append(f"word_count = ${param_idx}")
            params.append(len(content.split()))
            param_idx += 1
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )
        
        params.append(summary_id)
        
        row = await conn.fetchrow(
            f"""
            UPDATE public.summaries
            SET {', '.join(updates)}
            WHERE summary_id = ${param_idx}
            RETURNING summary_id, owner_id, title, content, key_points, source_files, 
                      word_count, created_at, updated_at
            """,
            *params,
        )
        
        return SummaryOut(
            summary_id=str(row["summary_id"]),
            owner_id=str(row["owner_id"]),
            title=row["title"],
            content=row["content"],
            key_points=row["key_points"] or [],
            source_files=row["source_files"] or [],
            word_count=row["word_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@router.delete("/{summary_id}")
async def delete_summary(
    summary_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Soft-delete a summary."""
    async with pool.acquire() as conn:
        # Verify ownership
        try:
            existing = await _get_summary_by_id(conn, summary_id, user.id)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )
        
        await conn.execute(
            """
            UPDATE public.summaries
            SET deleted_at = now()
            WHERE summary_id = $1
            """,
            summary_id,
        )
        
        return {"message": "Summary deleted", "summary_id": str(summary_id)}


__all__ = ["router"]

