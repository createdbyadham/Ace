"""Convert questions options columns to JSONB array

Revision ID: d2e3f4g5h6i7
Revises: c1d2e3f4g5h6
Create Date: 2024-12-15

Migrates from separate option_a, option_b, option_c, option_d columns
to a single options JSONB array column. Also changes correct_answer
from CHAR(1) to SMALLINT (0-3 index).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d2e3f4g5h6i7"
down_revision: Union[str, None] = "c1d2e3f4g5h6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new options JSONB column
    op.execute("""
        ALTER TABLE public.questions
        ADD COLUMN options JSONB
    """)
    
    # Migrate existing data: combine option_a/b/c/d into options array
    op.execute("""
        UPDATE public.questions
        SET options = jsonb_build_array(option_a, option_b, option_c, option_d)
    """)
    
    # Make options NOT NULL after migration
    op.execute("""
        ALTER TABLE public.questions
        ALTER COLUMN options SET NOT NULL
    """)
    
    # Add new correct_answer_idx column as SMALLINT
    op.execute("""
        ALTER TABLE public.questions
        ADD COLUMN correct_answer_idx SMALLINT
    """)
    
    # Migrate correct_answer: A->0, B->1, C->2, D->3
    op.execute("""
        UPDATE public.questions
        SET correct_answer_idx = CASE correct_answer
            WHEN 'A' THEN 0
            WHEN 'B' THEN 1
            WHEN 'C' THEN 2
            WHEN 'D' THEN 3
            ELSE 0
        END
    """)
    
    # Make correct_answer_idx NOT NULL and add constraint
    op.execute("""
        ALTER TABLE public.questions
        ALTER COLUMN correct_answer_idx SET NOT NULL
    """)
    op.execute("""
        ALTER TABLE public.questions
        ADD CONSTRAINT questions_correct_answer_idx_check 
        CHECK (correct_answer_idx >= 0 AND correct_answer_idx <= 3)
    """)
    
    # Drop old columns
    op.execute("ALTER TABLE public.questions DROP COLUMN option_a")
    op.execute("ALTER TABLE public.questions DROP COLUMN option_b")
    op.execute("ALTER TABLE public.questions DROP COLUMN option_c")
    op.execute("ALTER TABLE public.questions DROP COLUMN option_d")
    op.execute("ALTER TABLE public.questions DROP COLUMN correct_answer")
    
    # Rename correct_answer_idx to correct_answer
    op.execute("""
        ALTER TABLE public.questions
        RENAME COLUMN correct_answer_idx TO correct_answer
    """)


def downgrade() -> None:
    # Add back individual option columns
    op.execute("ALTER TABLE public.questions ADD COLUMN option_a TEXT")
    op.execute("ALTER TABLE public.questions ADD COLUMN option_b TEXT")
    op.execute("ALTER TABLE public.questions ADD COLUMN option_c TEXT")
    op.execute("ALTER TABLE public.questions ADD COLUMN option_d TEXT")
    
    # Migrate options array back to individual columns
    op.execute("""
        UPDATE public.questions
        SET 
            option_a = options->>0,
            option_b = options->>1,
            option_c = options->>2,
            option_d = options->>3
    """)
    
    # Make NOT NULL
    op.execute("ALTER TABLE public.questions ALTER COLUMN option_a SET NOT NULL")
    op.execute("ALTER TABLE public.questions ALTER COLUMN option_b SET NOT NULL")
    op.execute("ALTER TABLE public.questions ALTER COLUMN option_c SET NOT NULL")
    op.execute("ALTER TABLE public.questions ALTER COLUMN option_d SET NOT NULL")
    
    # Rename correct_answer to correct_answer_idx temporarily
    op.execute("ALTER TABLE public.questions RENAME COLUMN correct_answer TO correct_answer_idx")
    
    # Add back correct_answer as CHAR(1)
    op.execute("ALTER TABLE public.questions ADD COLUMN correct_answer CHAR(1)")
    
    # Migrate index back to letter
    op.execute("""
        UPDATE public.questions
        SET correct_answer = CASE correct_answer_idx
            WHEN 0 THEN 'A'
            WHEN 1 THEN 'B'
            WHEN 2 THEN 'C'
            WHEN 3 THEN 'D'
            ELSE 'A'
        END
    """)
    
    # Make NOT NULL and add constraint
    op.execute("ALTER TABLE public.questions ALTER COLUMN correct_answer SET NOT NULL")
    op.execute("""
        ALTER TABLE public.questions
        ADD CONSTRAINT questions_correct_answer_check 
        CHECK (correct_answer IN ('A', 'B', 'C', 'D'))
    """)
    
    # Drop new columns
    op.execute("ALTER TABLE public.questions DROP CONSTRAINT questions_correct_answer_idx_check")
    op.execute("ALTER TABLE public.questions DROP COLUMN correct_answer_idx")
    op.execute("ALTER TABLE public.questions DROP COLUMN options")

