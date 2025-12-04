"""test

Revision ID: e96959187896
Revises: b61d4f92d5db
Create Date: 2025-12-04 16:20:44.582567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e96959187896'
down_revision: Union[str, None] = 'b61d4f92d5db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE sr.states SET SCHEMA public")
    op.execute("ALTER TABLE sr.reviews SET SCHEMA public")


def downgrade() -> None:
    pass

