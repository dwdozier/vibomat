import uuid
import json
import hashlib
import base64
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any, List

from sqlalchemy import ForeignKey, String, DateTime, UUID, TypeDecorator, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptography.fernet import Fernet

from backend.app.db.session import Base
from backend.app.core.config import settings

if TYPE_CHECKING:
    from .user import User

# Get encryption key from environment
SECRET_KEY = settings.SECRET_KEY
# Derive a valid 32-byte base64 key using SHA256
key_bytes = hashlib.sha256(SECRET_KEY.encode()).digest()
FERNET_KEY = base64.urlsafe_b64encode(key_bytes)
fernet = Fernet(FERNET_KEY)


class EncryptedJSON(TypeDecorator):
    """
    SQLAlchemy type for storing encrypted JSON data.
    """

    impl = String
    cache_ok = False

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        json_str = json.dumps(value)
        return fernet.encrypt(json_str.encode()).decode()

    def process_result_value(self, value: Optional[str], dialect: Any) -> Any:
        if value is None:
            return None
        decrypted = fernet.decrypt(value.encode()).decode()
        return json.loads(decrypted)


class ServiceConnection(Base):
    __tablename__ = "service_connection"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "spotify"
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    access_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(1024), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Scopes granted by the user
    scopes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # User-supplied configuration (e.g., Client ID, Client Secret for custom app)
    # Encrypted at rest
    credentials: Mapped[Optional[dict[str, Any]]] = mapped_column(EncryptedJSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="service_connections")

    @property
    def is_connected(self) -> bool:
        """Check if the connection has a valid access token and provider ID."""
        return bool(self.access_token and self.provider_user_id != "PENDING")

    @property
    def client_id(self) -> Optional[str]:
        """Expose the client_id from credentials if set."""
        if self.credentials:
            return self.credentials.get("client_id")
        return None

    @property
    def has_secret(self) -> bool:
        """Check if a client_secret is set without exposing it."""
        if self.credentials:
            return bool(self.credentials.get("client_secret"))
        return False
