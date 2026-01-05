"""add ai_interaction_embedding table

Revision ID: 313c5b58af43
Revises: 86357b00373d
Create Date: 2026-01-04 21:39:13.945646

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "313c5b58af43"
down_revision: Union[str, Sequence[str], None] = "86357b00373d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ai_interaction_embedding",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("prompt", sa.String(length=2048), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ai_interaction_embedding")
