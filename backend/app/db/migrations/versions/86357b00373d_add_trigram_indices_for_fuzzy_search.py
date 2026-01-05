"""add trigram indices for fuzzy search

Revision ID: 86357b00373d
Revises: 84b62cc85542
Create Date: 2026-01-04 20:51:27.150012

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "86357b00373d"
down_revision: Union[str, Sequence[str], None] = "84b62cc85542"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_artist_name_trgm",
        "artist",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_track_title_trgm",
        "track",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_track_artist_name_trgm",
        "track",
        ["artist_name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"artist_name": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_track_artist_name_trgm", table_name="track")
    op.drop_index("ix_track_title_trgm", table_name="track")
    op.drop_index("ix_artist_name_trgm", table_name="artist")
