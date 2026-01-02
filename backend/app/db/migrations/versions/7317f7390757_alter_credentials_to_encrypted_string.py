"""alter credentials to encrypted string

Revision ID: 7317f7390757
Revises: b4fe00f3c024
Create Date: 2026-01-02 04:41:19.567465

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7317f7390757"
down_revision: Union[str, Sequence[str], None] = "b4fe00f3c024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Clear existing unencrypted data to avoid decryption errors
    op.execute("UPDATE service_connection SET credentials = NULL")

    # 2. Alter column type
    op.alter_column(
        "service_connection",
        "credentials",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=sa.String(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Note: Downgrading will make the encrypted string look like a JSON string in the DB,
    # but since we cleared data on upgrade, it's fine.
    op.alter_column(
        "service_connection",
        "credentials",
        existing_type=sa.String(),
        type_=postgresql.JSON(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using="credentials::json",
    )
