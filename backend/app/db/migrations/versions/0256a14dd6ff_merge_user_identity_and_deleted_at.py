"""merge user identity and deleted at

Revision ID: 0256a14dd6ff
Revises: 3e94dca99d0d, f47531f2e1d1
Create Date: 2026-01-10 04:24:00.834982

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "0256a14dd6ff"
down_revision: Union[str, Sequence[str], None] = ("3e94dca99d0d", "f47531f2e1d1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
