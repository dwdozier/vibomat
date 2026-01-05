"""add artist and track tables

Revision ID: f069bbd51c99
Revises: 75ad2b67eef0
Create Date: 2026-01-04 20:44:08.651272

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f069bbd51c99"
down_revision: Union[str, Sequence[str], None] = "75ad2b67eef0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "artist",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider_id", sa.String(length=255), nullable=True),
        sa.Column("genres", sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artist_name"), "artist", ["name"], unique=False)
    op.create_index(op.f("ix_artist_provider_id"), "artist", ["provider_id"], unique=False)

    op.create_table(
        "track",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("artist_name", sa.String(length=255), nullable=False),
        sa.Column("album_name", sa.String(length=255), nullable=True),
        sa.Column("provider_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_track_artist_name"), "track", ["artist_name"], unique=False)
    op.create_index(op.f("ix_track_provider_id"), "track", ["provider_id"], unique=False)
    op.create_index(op.f("ix_track_title"), "track", ["title"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("track")
    op.drop_table("artist")
