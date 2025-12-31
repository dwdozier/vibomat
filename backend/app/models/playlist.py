import uuid
from sqlalchemy import ForeignKey, String, JSON, Boolean, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .user import User


class Playlist(Base):
    __tablename__ = "playlist"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Store the tracks as JSON for flexibility
    content_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="playlists")
