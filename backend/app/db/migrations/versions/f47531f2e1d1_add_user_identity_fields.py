"""Add user identity fields

Revision ID: f47531f2e1d1
Revises: 7a4192d49c72
Create Date: 2026-01-05 22:39:47.776406

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f47531f2e1d1"
down_revision: Union[str, Sequence[str], None] = "7a4192d49c72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("user", sa.Column("handle", sa.String(), nullable=True))
    op.add_column("user", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("user", sa.Column("last_name", sa.String(), nullable=True))
    op.create_unique_constraint("uq_user_handle", "user", ["handle"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_user_handle", "user", type_="unique")
    op.drop_column("user", "last_name")
    op.drop_column("user", "first_name")
    op.drop_column("user", "handle")
