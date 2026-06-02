"""add updated_at to discussion_threads

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02

"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE discussion_threads
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE discussion_threads DROP COLUMN IF EXISTS updated_at;")
