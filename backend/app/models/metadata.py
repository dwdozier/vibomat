import uuid
from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base
from typing import Optional


class Artist(Base):
    __tablename__ = "artist"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    genres: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)


class Track(Base):
    __tablename__ = "track"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artist_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    album_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
