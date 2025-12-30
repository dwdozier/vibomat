from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyBaseOAuthAccountTableUUID,
)
from sqlalchemy.orm import Mapped, relationship
from typing import List, TYPE_CHECKING
from backend.app.db.session import Base

if TYPE_CHECKING:
    from .service_connection import ServiceConnection
    from .playlist import Playlist


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

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
