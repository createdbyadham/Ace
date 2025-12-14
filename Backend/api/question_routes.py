"""
API routes for question sets and questions.

Endpoints:
- GET /question-sets - List all question sets
- GET /question-sets/{set_id} - Get a question set with questions
- DELETE /question-sets/{set_id} - Delete a question set
"""
from __future__ import annotations

from typing import List
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.questions.models import QuestionSetOut, QuestionSetWithQuestions
from domain.questions.service import QuestionService

router = APIRouter(prefix="/question-sets", tags=["questions"])


def get_question_service(pool: asyncpg.Pool = Depends(get_pool)) -> QuestionService:
    return QuestionService(pool)


@router.get("", response_model=List[QuestionSetOut])
async def list_question_sets(
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    List all question sets owned by the current user.
    
    Returns question sets with question counts.
    """
    return await service.list_question_sets(owner_id=user.id)


@router.get("/{set_id}", response_model=QuestionSetWithQuestions)
async def get_question_set(
    set_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Get a specific question set with all its questions.
    
    Returns the full question set including all MCQ questions.
    """
    result = await service.get_question_set(owner_id=user.id, set_id=set_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found",
        )
    return result


@router.delete("/{set_id}")
async def delete_question_set(
    set_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Delete a question set and all its questions.
    
    This is a soft delete - the data can be recovered if needed.
    """
    deleted = await service.delete_question_set(owner_id=user.id, set_id=set_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found",
        )
    return {"message": "Question set deleted", "set_id": str(set_id)}


__all__ = ["router"]

