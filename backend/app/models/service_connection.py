import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.session import Base
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from .user import User


class ServiceConnection(Base):
    __tablename__ = "service_connection"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "spotify"
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    access_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(1024), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # User-supplied configuration (e.g., Client ID, Client Secret for custom app)
    credentials: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="service_connections")
