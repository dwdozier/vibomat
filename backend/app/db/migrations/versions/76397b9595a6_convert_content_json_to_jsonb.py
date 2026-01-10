"""convert content_json to jsonb

Revision ID: 76397b9595a6
Revises: 6cc33370c404
Create Date: 2026-01-04 19:31:09.643140

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "76397b9595a6"
down_revision: Union[str, Sequence[str], None] = "6cc33370c404"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE playlist ALTER COLUMN content_json TYPE JSONB USING content_json::JSONB")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE playlist ALTER COLUMN content_json TYPE JSON USING content_json::JSON")
