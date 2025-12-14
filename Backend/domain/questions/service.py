"""
Service for MCQ question sets.
"""
from __future__ import annotations

import json
from typing import List, Optional
from uuid import UUID

import asyncpg

from .models import (
    QuestionCreate,
    QuestionOut,
    QuestionSetCreate,
    QuestionSetOut,
    QuestionSetWithQuestions,
)


class QuestionService:
    """Service for managing question sets and questions."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_question_set(
        self,
        *,
        owner_id: UUID,
        payload: QuestionSetCreate,
    ) -> QuestionSetOut:
        """Create a new question set."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.question_sets (owner_id, title, description, tags)
                VALUES ($1, $2, $3, $4)
                RETURNING set_id, owner_id, title, description, tags, created_at
                """,
                owner_id,
                payload.title,
                payload.description,
                json.dumps(payload.tags),
            )
        return QuestionSetOut(
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            description=row["description"],
            tags=row["tags"] if row["tags"] else [],
            created_at=row["created_at"],
            questions_count=0,
        )

    async def list_question_sets(self, *, owner_id: UUID) -> List[QuestionSetOut]:
        """List all question sets for a user."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    qs.set_id, qs.owner_id, qs.title, qs.description, qs.tags, qs.created_at,
                    COUNT(q.question_id) as questions_count
                FROM public.question_sets qs
                LEFT JOIN public.questions q ON q.set_id = qs.set_id
                WHERE qs.owner_id = $1 AND qs.deleted_at IS NULL
                GROUP BY qs.set_id
                ORDER BY qs.created_at DESC
                """,
                owner_id,
            )
        return [
            QuestionSetOut(
                set_id=row["set_id"],
                owner_id=row["owner_id"],
                title=row["title"],
                description=row["description"],
                tags=row["tags"] if row["tags"] else [],
                created_at=row["created_at"],
                questions_count=row["questions_count"],
            )
            for row in rows
        ]

    async def get_question_set(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
    ) -> Optional[QuestionSetWithQuestions]:
        """Get a question set with all its questions."""
        async with self._pool.acquire() as conn:
            set_row = await conn.fetchrow(
                """
                SELECT set_id, owner_id, title, description, tags, created_at
                FROM public.question_sets
                WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
                """,
                set_id,
                owner_id,
            )
            if set_row is None:
                return None

            question_rows = await conn.fetch(
                """
                SELECT question_id, set_id, owner_id, question_text,
                       option_a, option_b, option_c, option_d,
                       correct_answer, explanation, source_file, created_at
                FROM public.questions
                WHERE set_id = $1
                ORDER BY created_at
                """,
                set_id,
            )

        questions = [
            QuestionOut(
                question_id=row["question_id"],
                set_id=row["set_id"],
                owner_id=row["owner_id"],
                question_text=row["question_text"],
                option_a=row["option_a"],
                option_b=row["option_b"],
                option_c=row["option_c"],
                option_d=row["option_d"],
                correct_answer=row["correct_answer"],
                explanation=row["explanation"],
                source_file=row["source_file"],
                created_at=row["created_at"],
            )
            for row in question_rows
        ]

        return QuestionSetWithQuestions(
            set_id=set_row["set_id"],
            owner_id=set_row["owner_id"],
            title=set_row["title"],
            description=set_row["description"],
            tags=set_row["tags"] if set_row["tags"] else [],
            created_at=set_row["created_at"],
            questions=questions,
        )

    async def create_question(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
        payload: QuestionCreate,
    ) -> QuestionOut:
        """Create a single question in a set."""
        async with self._pool.acquire() as conn:
            # Verify set exists and belongs to user
            set_owner = await conn.fetchval(
                "SELECT owner_id FROM public.question_sets WHERE set_id = $1",
                set_id,
            )
            if set_owner is None:
                raise ValueError("Question set does not exist")
            if set_owner != owner_id:
                raise PermissionError("Question set does not belong to the current user")

            row = await conn.fetchrow(
                """
                INSERT INTO public.questions 
                    (set_id, owner_id, question_text, option_a, option_b, option_c, option_d,
                     correct_answer, explanation, source_file)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING question_id, set_id, owner_id, question_text,
                          option_a, option_b, option_c, option_d,
                          correct_answer, explanation, source_file, created_at
                """,
                set_id,
                owner_id,
                payload.question_text,
                payload.option_a,
                payload.option_b,
                payload.option_c,
                payload.option_d,
                payload.correct_answer.value,
                payload.explanation,
                payload.source_file,
            )

        return QuestionOut(
            question_id=row["question_id"],
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            question_text=row["question_text"],
            option_a=row["option_a"],
            option_b=row["option_b"],
            option_c=row["option_c"],
            option_d=row["option_d"],
            correct_answer=row["correct_answer"],
            explanation=row["explanation"],
            source_file=row["source_file"],
            created_at=row["created_at"],
        )

    async def delete_question_set(self, *, owner_id: UUID, set_id: UUID) -> bool:
        """Soft delete a question set."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.question_sets
                SET deleted_at = now()
                WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
                """,
                set_id,
                owner_id,
            )
        return result == "UPDATE 1"


__all__ = ["QuestionService"]

