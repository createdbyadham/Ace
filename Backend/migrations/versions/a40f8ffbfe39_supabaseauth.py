"""Supabaseauth

Revision ID: a40f8ffbfe39
Revises: e96959187896
Create Date: 2025-12-04 17:05:11.557009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a40f8ffbfe39'
down_revision: Union[str, None] = 'e96959187896'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Create FK: public.users.user_id -> auth.users.id
    op.create_foreign_key(
        constraint_name="users_user_id_fkey_to_auth_users",
        source_table="users",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        source_schema="public",
        referent_schema="auth",
        ondelete="CASCADE",
    )

    # 2) Enable RLS and create policies on public.users
    op.execute("""
    ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
    -- allow selecting only own row
    CREATE POLICY users_select_own ON public.users
      FOR SELECT USING (user_id = auth.uid());
    -- allow inserting a profile only for own user_id
    CREATE POLICY users_insert_own ON public.users
      FOR INSERT WITH CHECK (user_id = auth.uid());
    -- allow updating only own row
    CREATE POLICY users_update_own ON public.users
      FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
    -- allow deleting only own row
    CREATE POLICY users_delete_own ON public.users
      FOR DELETE USING (user_id = auth.uid());
    """)

    # 3) Enable RLS and add owner-based policies for public.cards (owner_id)
    op.execute("""
    ALTER TABLE public.cards ENABLE ROW LEVEL SECURITY;
    CREATE POLICY cards_select_owner ON public.cards
      FOR SELECT USING (owner_id = auth.uid());
    CREATE POLICY cards_insert_owner ON public.cards
      FOR INSERT WITH CHECK (owner_id = auth.uid());
    CREATE POLICY cards_update_owner ON public.cards
      FOR UPDATE USING (owner_id = auth.uid()) WITH CHECK (owner_id = auth.uid());
    CREATE POLICY cards_delete_owner ON public.cards
      FOR DELETE USING (owner_id = auth.uid());
    """)

    # 4) Enable RLS and add owner-based policies for public.decks (owner_id)
    op.execute("""
    ALTER TABLE public.decks ENABLE ROW LEVEL SECURITY;
    CREATE POLICY decks_select_owner ON public.decks
      FOR SELECT USING (owner_id = auth.uid());
    CREATE POLICY decks_insert_owner ON public.decks
      FOR INSERT WITH CHECK (owner_id = auth.uid());
    CREATE POLICY decks_update_owner ON public.decks
      FOR UPDATE USING (owner_id = auth.uid()) WITH CHECK (owner_id = auth.uid());
    CREATE POLICY decks_delete_owner ON public.decks
      FOR DELETE USING (owner_id = auth.uid());
    """)

    # 5) Enable RLS and add owner-based policies for public.reviews (user_id)
    op.execute("""
    ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
    CREATE POLICY reviews_select_owner ON public.reviews
      FOR SELECT USING (user_id = auth.uid());
    CREATE POLICY reviews_insert_owner ON public.reviews
      FOR INSERT WITH CHECK (user_id = auth.uid());
    CREATE POLICY reviews_update_owner ON public.reviews
      FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
    CREATE POLICY reviews_delete_owner ON public.reviews
      FOR DELETE USING (user_id = auth.uid());
    """)

    # 6) Enable RLS and add owner-based policies for public.states (user_id)
    op.execute("""
    ALTER TABLE public.states ENABLE ROW LEVEL SECURITY;
    CREATE POLICY states_select_owner ON public.states
      FOR SELECT USING (user_id = auth.uid());
    CREATE POLICY states_insert_owner ON public.states
      FOR INSERT WITH CHECK (user_id = auth.uid());
    CREATE POLICY states_update_owner ON public.states
      FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
    CREATE POLICY states_delete_owner ON public.states
      FOR DELETE USING (user_id = auth.uid());
    """)

    # Optional: you may create additional admin/service policies as needed,
    # but avoid adding overly-broad policies here by default.


def downgrade():
    # reverse order: drop policies, disable RLS, drop FK

    # 1) public.states
    op.execute("""
    DROP POLICY IF EXISTS states_delete_owner ON public.states;
    DROP POLICY IF EXISTS states_update_owner ON public.states;
    DROP POLICY IF EXISTS states_insert_owner ON public.states;
    DROP POLICY IF EXISTS states_select_owner ON public.states;
    ALTER TABLE public.states DISABLE ROW LEVEL SECURITY;
    """)

    # 2) public.reviews
    op.execute("""
    DROP POLICY IF EXISTS reviews_delete_owner ON public.reviews;
    DROP POLICY IF EXISTS reviews_update_owner ON public.reviews;
    DROP POLICY IF EXISTS reviews_insert_owner ON public.reviews;
    DROP POLICY IF EXISTS reviews_select_owner ON public.reviews;
    ALTER TABLE public.reviews DISABLE ROW LEVEL SECURITY;
    """)

    # 3) public.decks
    op.execute("""
    DROP POLICY IF EXISTS decks_delete_owner ON public.decks;
    DROP POLICY IF EXISTS decks_update_owner ON public.decks;
    DROP POLICY IF EXISTS decks_insert_owner ON public.decks;
    DROP POLICY IF EXISTS decks_select_owner ON public.decks;
    ALTER TABLE public.decks DISABLE ROW LEVEL SECURITY;
    """)

    # 4) public.cards
    op.execute("""
    DROP POLICY IF EXISTS cards_delete_owner ON public.cards;
    DROP POLICY IF EXISTS cards_update_owner ON public.cards;
    DROP POLICY IF EXISTS cards_insert_owner ON public.cards;
    DROP POLICY IF EXISTS cards_select_owner ON public.cards;
    ALTER TABLE public.cards DISABLE ROW LEVEL SECURITY;
    """)

    # 5) public.users
    op.execute("""
    DROP POLICY IF EXISTS users_delete_own ON public.users;
    DROP POLICY IF EXISTS users_update_own ON public.users;
    DROP POLICY IF EXISTS users_insert_own ON public.users;
    DROP POLICY IF EXISTS users_select_own ON public.users;
    ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
    """)

    # 6) Drop FK: public.users.user_id -> auth.users.id
    op.drop_constraint(
        constraint_name="users_user_id_fkey_to_auth_users",
        table_name="users",
        schema="public",
        type_="foreignkey"
    )

