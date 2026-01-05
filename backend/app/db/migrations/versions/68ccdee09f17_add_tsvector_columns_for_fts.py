"""add tsvector columns for fts

Revision ID: 68ccdee09f17
Revises: f069bbd51c99
Create Date: 2026-01-04 20:46:56.225074

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision: str = "68ccdee09f17"
down_revision: Union[str, Sequence[str], None] = "f069bbd51c99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("artist", sa.Column("search_vector", TSVECTOR(), nullable=True))
    op.add_column("track", sa.Column("search_vector", TSVECTOR(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("track", "search_vector")
    op.drop_column("artist", "search_vector")
