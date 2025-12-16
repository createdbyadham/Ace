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

Quiz Endpoints:
- POST /question-sets/{set_id}/quiz/start - Start a quiz
- POST /question-sets/{set_id}/quiz/submit - Submit quiz answers and get results
- POST /question-sets/{set_id}/quiz/revision - Start revision with wrong answers only
"""
from __future__ import annotations

from typing import List
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

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
    QuizStart,
    QuizSubmission,
    QuizResult,
    RevisionStart,
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


# =============================================================================
# Quiz Endpoints
# =============================================================================

class QuizStartRequest(BaseModel):
    """Request body for starting a quiz."""
    time_limit_seconds: int | None = None
    shuffle: bool = True


class RevisionRequest(BaseModel):
    """Request body for starting a revision session."""
    original_quiz_session_id: UUID
    wrong_question_ids: List[UUID]
    shuffle: bool = True


@router.post("/question-sets/{set_id}/quiz/start", response_model=QuizStart)
async def start_quiz(
    set_id: UUID,
    payload: QuizStartRequest = QuizStartRequest(),
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Start a quiz session for a question set.
    
    Returns questions without correct answers.
    The frontend should display these with a timer and collect user answers.
    
    - `time_limit_seconds`: Optional time limit for the quiz (informational for frontend)
    - `shuffle`: Whether to shuffle the question order (default: True)
    """
    result = await service.start_quiz(
        owner_id=user.id,
        set_id=set_id,
        time_limit_seconds=payload.time_limit_seconds,
        shuffle=payload.shuffle,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found or has no questions",
        )
    return result


@router.post("/question-sets/{set_id}/quiz/submit", response_model=QuizResult)
async def submit_quiz(
    set_id: UUID,
    quiz_session_id: UUID,
    submission: QuizSubmission,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Submit quiz answers and get detailed results.
    
    Returns:
    - Each question with the correct answer, user's answer, and explanation
    - Total correct/wrong counts
    - Percentage score
    - List of wrong question IDs for revision mode
    
    The `wrong_question_ids` in the response can be used to start a revision session.
    
    Errors:
    - 400: Duplicate answers or invalid question IDs
    - 404: Question set not found or empty
    """
    try:
        result = await service.submit_quiz(
            owner_id=user.id,
            set_id=set_id,
            quiz_session_id=quiz_session_id,
            submission=submission,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found or has no questions",
        )
    return result


@router.post("/question-sets/{set_id}/quiz/revision", response_model=RevisionStart)
async def start_revision(
    set_id: UUID,
    payload: RevisionRequest,
    user: CurrentUser = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    Start a revision session with only the questions the user got wrong.
    
    Use the `wrong_question_ids` from the quiz result to start a revision.
    This allows users to practice only the questions they missed.
    
    The revision works just like a regular quiz - call `/quiz/submit` with
    the `revision_session_id` as the `quiz_session_id` to grade the revision.
    """
    if not payload.wrong_question_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wrong question IDs provided",
        )
    
    result = await service.start_revision(
        owner_id=user.id,
        set_id=set_id,
        original_quiz_session_id=payload.original_quiz_session_id,
        wrong_question_ids=payload.wrong_question_ids,
        shuffle=payload.shuffle,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found or no valid questions",
        )
    return result


__all__ = ["router"]
