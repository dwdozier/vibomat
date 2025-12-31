import uuid
from sqlalchemy import UUID
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyBaseOAuthAccountTableUUID,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import List, TYPE_CHECKING
from backend.app.db.session import Base

if TYPE_CHECKING:
    from .service_connection import ServiceConnection
    from .playlist import Playlist


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    oauth_accounts: Mapped[List[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined", cascade="all, delete-orphan"
    )

    # Relationships
    service_connections: Mapped[List["ServiceConnection"]] = relationship(
        "ServiceConnection", back_populates="user", cascade="all, delete-orphan"
    )
    playlists: Mapped[List["Playlist"]] = relationship(
        "Playlist", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def __str__(self) -> str:
        return self.email
