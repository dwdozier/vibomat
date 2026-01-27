"""add_market_to_service_connection

Revision ID: 62c91989979d
Revises: c9a9a2842736
Create Date: 2026-01-27 16:49:23.717146

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "62c91989979d"
down_revision: Union[str, Sequence[str], None] = "c9a9a2842736"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add market column to service_connection table."""
    op.add_column("service_connection", sa.Column("market", sa.String(length=2), nullable=True))


def downgrade() -> None:
    """Remove market column from service_connection table."""
    op.drop_column("service_connection", "market")
