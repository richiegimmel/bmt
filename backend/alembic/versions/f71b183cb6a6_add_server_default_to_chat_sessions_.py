"""Add server_default to chat_sessions.updated_at

Revision ID: f71b183cb6a6
Revises: 5a1068dbd9e6
Create Date: 2025-11-06 18:13:44.150453

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f71b183cb6a6'
down_revision = '5a1068dbd9e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add server_default to updated_at column
    op.execute("ALTER TABLE chat_sessions ALTER COLUMN updated_at SET DEFAULT now();")

    # Update existing NULL values
    op.execute("UPDATE chat_sessions SET updated_at = created_at WHERE updated_at IS NULL;")


def downgrade() -> None:
    # Remove server_default from updated_at column
    op.execute("ALTER TABLE chat_sessions ALTER COLUMN updated_at DROP DEFAULT;")
