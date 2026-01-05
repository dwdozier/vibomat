"""add hnsw index to ai_interaction_embedding

Revision ID: 69789f1cfee8
Revises: 313c5b58af43
Create Date: 2026-01-04 21:48:16.961892

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "69789f1cfee8"
down_revision: Union[str, Sequence[str], None] = "313c5b58af43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_ai_interaction_embedding_hnsw",
        "ai_interaction_embedding",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_l2_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ai_interaction_embedding_hnsw", table_name="ai_interaction_embedding")
