"""add gin index to content_json

Revision ID: 75ad2b67eef0
Revises: 76397b9595a6
Create Date: 2026-01-04 19:33:13.479579

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "75ad2b67eef0"
down_revision: Union[str, Sequence[str], None] = "76397b9595a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_playlist_content_json",
        "playlist",
        ["content_json"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_playlist_content_json", table_name="playlist")
