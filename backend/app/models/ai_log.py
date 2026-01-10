import uuid
from sqlalchemy import String, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base
from pgvector.sqlalchemy import Vector
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class AIInteractionEmbedding(Base):
    __tablename__ = "ai_interaction_embedding"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    prompt: Mapped[str] = mapped_column(String(2048), nullable=False)
    # dimension 768 corresponds to Gemini text-embedding-004
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(768), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship()
