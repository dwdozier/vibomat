import uuid
from sqlalchemy import UUID, Boolean, JSON, Table, ForeignKey, Column
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyBaseOAuthAccountTableUUID,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import List, TYPE_CHECKING, Any
from backend.app.db.session import Base

if TYPE_CHECKING:
    from .service_connection import ServiceConnection
    from .playlist import Playlist

user_favorite_playlists = Table(
    "user_favorite_playlists",
    Base.metadata,
    Column("user_id", UUID, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("playlist_id", UUID, ForeignKey("playlist.id", ondelete="CASCADE"), primary_key=True),
)


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # Public Profile
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    favorite_artists: Mapped[List[str]] = mapped_column(JSON, default=list)
    unskippable_albums: Mapped[List[Any]] = mapped_column(JSON, default=list)

    oauth_accounts: Mapped[List[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined", cascade="all, delete-orphan"
    )

    # Relationships
    service_connections: Mapped[List["ServiceConnection"]] = relationship(
        "ServiceConnection", back_populates="user", cascade="all, delete-orphan"
    )
    playlists: Mapped[List["Playlist"]] = relationship(
        "Playlist",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[Playlist.user_id]",
    )
    favorited_playlists: Mapped[List["Playlist"]] = relationship(
        "Playlist", secondary=user_favorite_playlists, backref="favorited_by"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def __str__(self) -> str:
        return self.email
