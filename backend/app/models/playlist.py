import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, JSON, Boolean, UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .user import User


class Playlist(Base):
    __tablename__ = "playlist"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_duration_ms: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Sync Engine
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Store the tracks as JSON for flexibility
    content_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="playlists")
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playlist.id", ondelete="SET NULL"), nullable=True)
    source_playlist: Mapped["Playlist"] = relationship(remote_side=[id], backref="derived_playlists")
