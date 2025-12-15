"""Add question sets and questions tables for MCQ quizzes

Revision ID: c1d2e3f4g5h6
Revises: 93b6023b0f4b
Create Date: 2024-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c1d2e3f4g5h6"
down_revision: Union[str, None] = "93b6023b0f4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # question_sets - a collection of MCQ questions
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.question_sets (
            set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            tags JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_question_sets_owner ON public.question_sets(owner_id)")

    # questions - individual MCQ questions within a set
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.questions (
            question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            set_id UUID NOT NULL REFERENCES public.question_sets(set_id) ON DELETE CASCADE,
            owner_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
            explanation TEXT,
            source_file TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_questions_set ON public.questions(set_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_questions_owner ON public.questions(owner_id)")

    # Trigger for updated_at on question_sets
    op.execute("""
        CREATE OR REPLACE TRIGGER update_question_sets_updated_at
            BEFORE UPDATE ON public.question_sets
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)

    # Trigger for updated_at on questions
    op.execute("""
        CREATE OR REPLACE TRIGGER update_questions_updated_at
            BEFORE UPDATE ON public.questions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_questions_updated_at ON public.questions")
    op.execute("DROP TRIGGER IF EXISTS update_question_sets_updated_at ON public.question_sets")
    op.execute("DROP TABLE IF EXISTS public.questions")
    op.execute("DROP TABLE IF EXISTS public.question_sets")
