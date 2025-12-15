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
    QuestionUpdate,
    QuestionOut,
    QuestionSetCreate,
    QuestionSetUpdate,
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
                       options, correct_answer, explanation, source_file, created_at
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
                options=row["options"] if isinstance(row["options"], list) else json.loads(row["options"]),
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
                    (set_id, owner_id, question_text, options, correct_answer, explanation, source_file)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING question_id, set_id, owner_id, question_text,
                          options, correct_answer, explanation, source_file, created_at
                """,
                set_id,
                owner_id,
                payload.question_text,
                payload.options,  # Pass list directly, asyncpg handles JSON encoding
                payload.correct_answer,
                payload.explanation,
                payload.source_file,
            )

        return QuestionOut(
            question_id=row["question_id"],
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            question_text=row["question_text"],
            options=row["options"] if isinstance(row["options"], list) else json.loads(row["options"]),
            correct_answer=row["correct_answer"],
            explanation=row["explanation"],
            source_file=row["source_file"],
            created_at=row["created_at"],
        )

    async def update_question_set(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
        payload: QuestionSetUpdate,
    ) -> Optional[QuestionSetOut]:
        """Update a question set."""
        # Build dynamic update query
        updates = []
        params = []
        param_idx = 3  # $1 = set_id, $2 = owner_id
        
        if payload.title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(payload.title)
            param_idx += 1
        
        if payload.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(payload.description)
            param_idx += 1
        
        if payload.tags is not None:
            updates.append(f"tags = ${param_idx}")
            params.append(payload.tags)
            param_idx += 1
        
        if not updates:
            # Nothing to update, just return current
            return await self._get_question_set_basic(owner_id=owner_id, set_id=set_id)
        
        query = f"""
            UPDATE public.question_sets
            SET {", ".join(updates)}
            WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
            RETURNING set_id, owner_id, title, description, tags, created_at
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, set_id, owner_id, *params)
        
        if row is None:
            return None
        
        return QuestionSetOut(
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            description=row["description"],
            tags=row["tags"] if row["tags"] else [],
            created_at=row["created_at"],
            questions_count=0,  # Not fetching count for update response
        )

    async def _get_question_set_basic(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
    ) -> Optional[QuestionSetOut]:
        """Get basic question set info without questions."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT set_id, owner_id, title, description, tags, created_at
                FROM public.question_sets
                WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
                """,
                set_id,
                owner_id,
            )
        if row is None:
            return None
        return QuestionSetOut(
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            description=row["description"],
            tags=row["tags"] if row["tags"] else [],
            created_at=row["created_at"],
            questions_count=0,
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

    async def get_question(
        self,
        *,
        owner_id: UUID,
        question_id: UUID,
    ) -> Optional[QuestionOut]:
        """Get a single question by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT question_id, set_id, owner_id, question_text,
                       options, correct_answer, explanation, source_file, created_at
                FROM public.questions
                WHERE question_id = $1 AND owner_id = $2
                """,
                question_id,
                owner_id,
            )
        if row is None:
            return None
        return QuestionOut(
            question_id=row["question_id"],
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            question_text=row["question_text"],
            options=row["options"] if isinstance(row["options"], list) else json.loads(row["options"]),
            correct_answer=row["correct_answer"],
            explanation=row["explanation"],
            source_file=row["source_file"],
            created_at=row["created_at"],
        )

    async def update_question(
        self,
        *,
        owner_id: UUID,
        question_id: UUID,
        payload: QuestionUpdate,
    ) -> Optional[QuestionOut]:
        """Update a question."""
        # Build dynamic update query
        updates = []
        params = []
        param_idx = 3  # $1 = question_id, $2 = owner_id
        
        if payload.question_text is not None:
            updates.append(f"question_text = ${param_idx}")
            params.append(payload.question_text)
            param_idx += 1
        
        if payload.options is not None:
            updates.append(f"options = ${param_idx}")
            params.append(payload.options)
            param_idx += 1
        
        if payload.correct_answer is not None:
            updates.append(f"correct_answer = ${param_idx}")
            params.append(payload.correct_answer)
            param_idx += 1
        
        if payload.explanation is not None:
            updates.append(f"explanation = ${param_idx}")
            params.append(payload.explanation)
            param_idx += 1
        
        if not updates:
            # Nothing to update, just return current
            return await self.get_question(owner_id=owner_id, question_id=question_id)
        
        query = f"""
            UPDATE public.questions
            SET {", ".join(updates)}
            WHERE question_id = $1 AND owner_id = $2
            RETURNING question_id, set_id, owner_id, question_text,
                      options, correct_answer, explanation, source_file, created_at
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, question_id, owner_id, *params)
        
        if row is None:
            return None
        
        return QuestionOut(
            question_id=row["question_id"],
            set_id=row["set_id"],
            owner_id=row["owner_id"],
            question_text=row["question_text"],
            options=row["options"] if isinstance(row["options"], list) else json.loads(row["options"]),
            correct_answer=row["correct_answer"],
            explanation=row["explanation"],
            source_file=row["source_file"],
            created_at=row["created_at"],
        )

    async def delete_question(self, *, owner_id: UUID, question_id: UUID) -> bool:
        """Delete a question permanently."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM public.questions
                WHERE question_id = $1 AND owner_id = $2
                """,
                question_id,
                owner_id,
            )
        return result == "DELETE 1"


__all__ = ["QuestionService"]
