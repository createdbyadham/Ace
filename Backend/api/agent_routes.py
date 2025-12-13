"""
API routes for AI agents.

Endpoints:
- POST /agents/flashcards - Generate flashcards from PDFs
"""
from __future__ import annotations

from typing import List

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.agents.flashcard_agent import FlashcardAgent
from domain.agents.models import FlashcardGenerationResponse

router = APIRouter(prefix="/agents", tags=["agents"])


def get_flashcard_agent(pool: asyncpg.Pool = Depends(get_pool)) -> FlashcardAgent:
    return FlashcardAgent(pool)


@router.post("/flashcards", response_model=FlashcardGenerationResponse)
async def generate_flashcards(
    files: List[UploadFile] = File(..., description="PDF files to generate flashcards from"),
    num_cards: int = Form(..., ge=1, le=100, description="Number of flashcards to generate"),
    deck_title: str = Form(..., min_length=1, max_length=200, description="Title for the new deck"),
    deck_description: str = Form(default=None, max_length=1000, description="Optional deck description"),
    user: CurrentUser = Depends(get_current_user),
    agent: FlashcardAgent = Depends(get_flashcard_agent),
):
    """
    Generate flashcards from uploaded PDF files using AI.
    
    The agent will:
    1. Extract text from each PDF
    2. Use AI to generate high-quality flashcards
    3. Distribute cards evenly across PDFs (e.g., 10 cards from 2 PDFs = 5 each)
    4. Create a new deck with all the flashcards
    
    Args:
        files: One or more PDF files (lectures, notes, textbooks)
        num_cards: Total number of flashcards to generate (distributed evenly)
        deck_title: Name for the new deck
        deck_description: Optional description for the deck
        
    Returns:
        The created deck with all generated flashcards
    """
    # Validate files
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one PDF file is required",
        )
    
    pdf_files = []
    
    for file in files:
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All files must have filenames",
            )
        
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF files are supported. Got: {file.filename}",
            )
        
        # Read file content
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File is empty: {file.filename}",
            )
        
        pdf_files.append((pdf_bytes, file.filename))
    
    # Check if we have more files than cards requested
    if len(pdf_files) > num_cards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate {num_cards} cards from {len(pdf_files)} files. "
                   f"Please request at least {len(pdf_files)} cards.",
        )
    
    try:
        result = await agent.generate_flashcards(
            owner_id=user.id,
            deck_title=deck_title,
            deck_description=deck_description if deck_description else None,
            num_cards=num_cards,
            pdf_files=pdf_files,
        )
        return result
    
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(exc)}",
        ) from exc


__all__ = ["router"]

