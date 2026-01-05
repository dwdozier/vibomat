"""add gin indices for fts

Revision ID: 84b62cc85542
Revises: 68ccdee09f17
Create Date: 2026-01-04 20:49:10.053588

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "84b62cc85542"
down_revision: Union[str, Sequence[str], None] = "68ccdee09f17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_artist_search_vector",
        "artist",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_track_search_vector",
        "track",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_track_search_vector", table_name="track")
    op.drop_index("ix_artist_search_vector", table_name="artist")
