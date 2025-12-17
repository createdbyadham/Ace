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
    QuizQuestion,
    QuizStart,
    QuizSubmission,
    QuestionResult,
    QuizResult,
    RevisionStart,
)


class QuestionService:
    """Service for managing question sets and questions."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @staticmethod
    def _parse_tags(tags_value) -> list[str]:
        """Parse tags from database - handles both JSON string and list."""
        if tags_value is None:
            return []
        if isinstance(tags_value, list):
            return tags_value
        if isinstance(tags_value, str):
            return json.loads(tags_value)
        return []

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
            tags=self._parse_tags(row["tags"]),
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
                tags=self._parse_tags(row["tags"]),
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
            tags=self._parse_tags(set_row["tags"]),
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
            params.append(json.dumps(payload.tags))
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
            tags=self._parse_tags(row["tags"]),
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
            tags=self._parse_tags(row["tags"]),
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

    # =========================================================================
    # Quiz Methods
    # =========================================================================

    async def start_quiz(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
        time_limit_seconds: int | None = None,
        shuffle: bool = True,
    ) -> QuizStart | None:
        """
        Start a quiz session for a question set.
        Returns questions without correct answers.
        """
        import random
        import uuid
        
        async with self._pool.acquire() as conn:
            # Get question set info
            set_row = await conn.fetchrow(
                """
                SELECT set_id, title
                FROM public.question_sets
                WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
                """,
                set_id,
                owner_id,
            )
            if set_row is None:
                return None

            # Get all questions
            question_rows = await conn.fetch(
                """
                SELECT question_id, question_text, options
                FROM public.questions
                WHERE set_id = $1
                ORDER BY created_at
                """,
                set_id,
            )

        if not question_rows:
            return None

        questions = [
            QuizQuestion(
                question_id=row["question_id"],
                question_text=row["question_text"],
                options=row["options"] if isinstance(row["options"], list) else json.loads(row["options"]),
            )
            for row in question_rows
        ]

        if shuffle:
            random.shuffle(questions)

        return QuizStart(
            quiz_session_id=uuid.uuid4(),  # Generate a unique session ID
            set_id=set_row["set_id"],
            title=set_row["title"],
            questions=questions,
            time_limit_seconds=time_limit_seconds,
        )

    async def submit_quiz(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
        quiz_session_id: UUID,
        submission: QuizSubmission,
    ) -> QuizResult | None:
        """
        Grade a quiz submission and return detailed results.
        Only grades questions that were submitted (supports both full quiz and revision).
        
        Raises:
            ValueError: If duplicate answers or invalid question IDs are submitted.
        """
        # Validate: no duplicate answers
        submitted_question_ids: list[UUID] = []
        seen_question_ids: set[UUID] = set()
        for answer in submission.answers:
            if answer.question_id in seen_question_ids:
                raise ValueError(f"Duplicate answer for question {answer.question_id}")
            seen_question_ids.add(answer.question_id)
            submitted_question_ids.append(answer.question_id)

        if not submitted_question_ids:
            return None

        async with self._pool.acquire() as conn:
            # Get question set info
            set_row = await conn.fetchrow(
                """
                SELECT set_id, title
                FROM public.question_sets
                WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
                """,
                set_id,
                owner_id,
            )
            if set_row is None:
                return None

            # Get only the SUBMITTED questions (not all questions from the set)
            # This correctly handles both full quizzes and revisions
            question_rows = await conn.fetch(
                """
                SELECT question_id, question_text, options, correct_answer, explanation
                FROM public.questions
                WHERE set_id = $1 AND question_id = ANY($2)
                """,
                set_id,
                submitted_question_ids,
            )

        if not question_rows:
            return None

        # Build lookup: question_id -> row data
        question_data_map = {row["question_id"]: row for row in question_rows}

        # Validate: all submitted answers are for questions in this set
        valid_question_ids = set(question_data_map.keys())
        invalid_ids = seen_question_ids - valid_question_ids
        if invalid_ids:
            raise ValueError(f"Invalid question IDs not in this set: {[str(id) for id in invalid_ids]}")

        # Build lookup for user answers: question_id -> selected_answer
        user_answers_map = {
            answer.question_id: answer.selected_answer
            for answer in submission.answers
        }

        # Grade only SUBMITTED questions (preserves submission order)
        results: list[QuestionResult] = []
        correct_count = 0
        wrong_question_ids: list[UUID] = []

        for question_id in submitted_question_ids:
            row = question_data_map[question_id]
            options = row["options"] if isinstance(row["options"], list) else json.loads(row["options"])
            correct_answer = row["correct_answer"]
            user_answer = user_answers_map[question_id]
            is_correct = user_answer == correct_answer

            if is_correct:
                correct_count += 1
            else:
                wrong_question_ids.append(question_id)

            results.append(
                QuestionResult(
                    question_id=question_id,
                    question_text=row["question_text"],
                    options=options,
                    correct_answer=correct_answer,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    explanation=row["explanation"],
                )
            )

        total = len(results)
        wrong_count = total - correct_count
        percentage = (correct_count / total * 100) if total > 0 else 0.0

        return QuizResult(
            quiz_session_id=quiz_session_id,
            set_id=set_row["set_id"],
            title=set_row["title"],
            total_questions=total,
            correct_count=correct_count,
            wrong_count=wrong_count,
            percentage=round(percentage, 2),
            time_taken_seconds=submission.time_taken_seconds,
            results=results,
            wrong_question_ids=wrong_question_ids,
        )

    async def start_revision(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
        original_quiz_session_id: UUID,
        wrong_question_ids: list[UUID],
        shuffle: bool = True,
    ) -> RevisionStart | None:
        """
        Start a revision session with only the questions the user got wrong.
        """
        import random
        import uuid

        if not wrong_question_ids:
            return None

        async with self._pool.acquire() as conn:
            # Get question set info
            set_row = await conn.fetchrow(
                """
                SELECT set_id, title
                FROM public.question_sets
                WHERE set_id = $1 AND owner_id = $2 AND deleted_at IS NULL
                """,
                set_id,
                owner_id,
            )
            if set_row is None:
                return None

            # Get only the wrong questions
            question_rows = await conn.fetch(
                """
                SELECT question_id, question_text, options
                FROM public.questions
                WHERE set_id = $1 AND question_id = ANY($2)
                """,
                set_id,
                wrong_question_ids,
            )

        if not question_rows:
            return None

        questions = [
            QuizQuestion(
                question_id=row["question_id"],
                question_text=row["question_text"],
                options=row["options"] if isinstance(row["options"], list) else json.loads(row["options"]),
            )
            for row in question_rows
        ]

        if shuffle:
            random.shuffle(questions)

        return RevisionStart(
            revision_session_id=uuid.uuid4(),
            set_id=set_row["set_id"],
            title=set_row["title"],
            original_quiz_session_id=original_quiz_session_id,
            questions=questions,
        )

    async def get_questions_by_ids(
        self,
        *,
        owner_id: UUID,
        set_id: UUID,
        question_ids: list[UUID],
    ) -> list[QuestionOut]:
        """Get specific questions by their IDs."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT question_id, set_id, owner_id, question_text,
                       options, correct_answer, explanation, source_file, created_at
                FROM public.questions
                WHERE set_id = $1 AND owner_id = $2 AND question_id = ANY($3)
                """,
                set_id,
                owner_id,
                question_ids,
            )
        return [
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
            for row in rows
        ]


__all__ = ["QuestionService"]
