"""add deleted_at to playlist

Revision ID: b4abab401265
Revises: 7a4192d49c72
Create Date: 2026-01-06 18:07:41.778653

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b4abab401265"
down_revision: Union[str, Sequence[str], None] = "7a4192d49c72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("playlist", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("playlist", "deleted_at")
