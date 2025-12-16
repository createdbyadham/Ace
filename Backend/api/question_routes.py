"""
API routes for question sets and questions.

Endpoints:
- POST /question-sets - Create a question set
- GET /question-sets - List all question sets
- GET /question-sets/{set_id} - Get a question set with questions
- PATCH /question-sets/{set_id} - Update a question set
- DELETE /question-sets/{set_id} - Delete a question set
- POST /question-sets/{set_id}/questions - Create a question
- GET /questions/{question_id} - Get a question
- PATCH /questions/{question_id} - Update a question
- DELETE /questions/{question_id} - Delete a question
"""
from __future__ import annotations

from typing import List
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.questions.models import (
    QuestionCreate,
    QuestionUpdate,
    QuestionOut,
    QuestionSetCreate,
    QuestionSetUpdate,
    QuestionSetOut,
    QuestionSetWithQuestions,
)
from domain.questions.service import QuestionService

router = APIRouter (prefix="/questions", tags=["questions"])


def get_question_service(pool: asyncpg.Pool = Depends(get_pool)) -> QuestionService:
    return QuestionService(pool)


# =============================================================================
# Question Set Endpoints
# =============================================================================

@router.post("/question-sets", response_model=QuestionSetOut, status_code=status.HTTP_201_CREATED)
async def create_question_set(
    payload: QuestionSetCreate,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Create a new question set.
    
    Question sets are containers for MCQ questions.
    """
    return await service.create_question_set(owner_id=user.id, payload=payload)


@router.get("/question-sets", response_model=List[QuestionSetOut])
async def list_question_sets(
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    List all question sets owned by the current user.
    
    Returns question sets with question counts.
    """
    return await service.list_question_sets(owner_id=user.id)


@router.get("/question-sets/{set_id}", response_model=QuestionSetWithQuestions)
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


@router.patch("/question-sets/{set_id}", response_model=QuestionSetOut)
async def update_question_set(
    set_id: UUID,
    payload: QuestionSetUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Update a question set.
    
    Only provided fields will be updated.
    """
    result = await service.update_question_set(owner_id=user.id, set_id=set_id, payload=payload)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found",
        )
    return result


@router.delete("/question-sets/{set_id}")
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


# =============================================================================
# Question Endpoints
# =============================================================================

@router.post("/question-sets/{set_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(
    set_id: UUID,
    payload: QuestionCreate,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Create a new question in a question set.
    
    Requires exactly 4 options and a correct_answer index (0-3).
    """
    try:
        return await service.create_question(owner_id=user.id, set_id=set_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get("/questions/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Get a specific question by ID.
    """
    result = await service.get_question(owner_id=user.id, question_id=question_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return result


@router.patch("/questions/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Update a question.
    
    Only provided fields will be updated.
    If updating options, must provide all 4 options.
    """
    result = await service.update_question(owner_id=user.id, question_id=question_id, payload=payload)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return result


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Delete a question permanently.
    """
    deleted = await service.delete_question(owner_id=user.id, question_id=question_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return {"message": "Question deleted", "question_id": str(question_id)}


__all__ = ["router"]
