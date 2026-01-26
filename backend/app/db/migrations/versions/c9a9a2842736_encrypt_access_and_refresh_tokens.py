"""encrypt_access_and_refresh_tokens

Revision ID: c9a9a2842736
Revises: cfe0aee7e7f0
Create Date: 2026-01-26 17:17:35.430423

"""

from typing import Sequence, Union
import json
import hashlib
import base64

from alembic import op
from sqlalchemy import text
from cryptography.fernet import Fernet


# revision identifiers, used by Alembic.
revision: str = "c9a9a2842736"
down_revision: Union[str, Sequence[str], None] = "cfe0aee7e7f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_fernet():
    """Get Fernet cipher for encryption."""
    from backend.app.core.config import settings

    SECRET_KEY = settings.SECRET_KEY
    key_bytes = hashlib.sha256(SECRET_KEY.encode()).digest()
    FERNET_KEY = base64.urlsafe_b64encode(key_bytes)
    return Fernet(FERNET_KEY)


def encrypt_value(value: str, fernet: Fernet) -> str:
    """Encrypt a string value using the same logic as EncryptedJSON."""
    if value is None:
        raise ValueError("Cannot encrypt None value")
    json_str = json.dumps(value)
    return fernet.encrypt(json_str.encode()).decode()


def is_encrypted(value: str, fernet: Fernet) -> bool:
    """Check if a value is already encrypted."""
    if value is None:
        return True
    try:
        decrypted = fernet.decrypt(value.encode()).decode()
        json.loads(decrypted)
        return True
    except Exception:
        return False


def upgrade() -> None:
    """Encrypt existing plaintext access and refresh tokens."""
    conn = op.get_bind()
    fernet = get_fernet()

    # Get all service connections
    result = conn.execute(text("SELECT id, access_token, refresh_token FROM service_connection"))

    for row in result:
        connection_id = row[0]
        access_token = row[1]
        refresh_token = row[2]

        # Check if tokens are already encrypted (idempotent migration)
        if access_token and not is_encrypted(access_token, fernet):
            encrypted_access = encrypt_value(access_token, fernet)
            conn.execute(
                text("UPDATE service_connection SET access_token = :token WHERE id = :id"),
                {"token": encrypted_access, "id": connection_id},
            )

        if refresh_token and not is_encrypted(refresh_token, fernet):
            encrypted_refresh = encrypt_value(refresh_token, fernet)
            conn.execute(
                text("UPDATE service_connection " "SET refresh_token = :token WHERE id = :id"),
                {"token": encrypted_refresh, "id": connection_id},
            )

    conn.commit()


def downgrade() -> None:
    """Decrypt tokens back to plaintext (not recommended for production)."""
    conn = op.get_bind()
    fernet = get_fernet()

    # Get all service connections
    result = conn.execute(text("SELECT id, access_token, refresh_token FROM service_connection"))

    for row in result:
        connection_id = row[0]
        access_token = row[1]
        refresh_token = row[2]

        # Decrypt if encrypted
        if access_token and is_encrypted(access_token, fernet):
            try:
                decrypted = fernet.decrypt(access_token.encode()).decode()
                plaintext_access = json.loads(decrypted)
                conn.execute(
                    text("UPDATE service_connection " "SET access_token = :token WHERE id = :id"),
                    {"token": plaintext_access, "id": connection_id},
                )
            except Exception:
                pass  # Skip if decryption fails

        if refresh_token and is_encrypted(refresh_token, fernet):
            try:
                decrypted = fernet.decrypt(refresh_token.encode()).decode()
                plaintext_refresh = json.loads(decrypted)
                conn.execute(
                    text("UPDATE service_connection " "SET refresh_token = :token WHERE id = :id"),
                    {"token": plaintext_refresh, "id": connection_id},
                )
            except Exception:
                pass  # Skip if decryption fails

    conn.commit()
