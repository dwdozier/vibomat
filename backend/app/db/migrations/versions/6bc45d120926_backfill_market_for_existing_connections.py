"""backfill_market_for_existing_connections

Revision ID: 6bc45d120926
Revises: 62c91989979d
Create Date: 2026-01-27 22:47:09.447066

"""

from typing import Sequence, Union, Optional
import json
import hashlib
import base64

from alembic import op
from sqlalchemy import text
from cryptography.fernet import Fernet
import spotipy
import logging

logger = logging.getLogger("alembic.backfill_market")


# revision identifiers, used by Alembic.
revision: str = "6bc45d120926"
down_revision: Union[str, Sequence[str], None] = "62c91989979d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_fernet():
    """Get Fernet cipher for decryption."""
    from backend.app.core.config import settings

    SECRET_KEY = settings.SECRET_KEY
    key_bytes = hashlib.sha256(SECRET_KEY.encode()).digest()
    FERNET_KEY = base64.urlsafe_b64encode(key_bytes)
    return Fernet(FERNET_KEY)


def decrypt_token(encrypted_value: str, fernet: Fernet) -> str:
    """Decrypt an access token."""
    try:
        decrypted = fernet.decrypt(encrypted_value.encode()).decode()
        return json.loads(decrypted)
    except Exception as e:
        logger.warning(f"Failed to decrypt token: {e}")
        raise


def fetch_market_for_connection(connection_id: str, access_token: str) -> Optional[str]:
    """Fetch market for a single connection using Spotify API."""
    try:
        sp = spotipy.Spotify(auth=access_token)
        user = sp.current_user()

        if user is None:
            logger.warning(f"Failed to authenticate for connection {connection_id}")
            return None

        market = user.get("country")
        if market:
            logger.info(f"Fetched market '{market}' for connection {connection_id}")
        else:
            logger.warning(f"No market available for connection {connection_id}")
        return market
    except Exception as e:
        logger.warning(f"Failed to fetch market for connection {connection_id}: {e}")
        return None


def upgrade() -> None:
    """Backfill market for existing Spotify connections."""
    conn = op.get_bind()
    fernet = get_fernet()

    # Get all Spotify connections without a market
    result = conn.execute(
        text("SELECT id, access_token FROM service_connection " "WHERE provider_name = 'spotify' AND market IS NULL")
    )

    connections = list(result)
    if not connections:
        logger.info("No Spotify connections to backfill")
        return

    logger.info(f"Backfilling market for {len(connections)} Spotify connections")

    # Process each connection
    for row in connections:
        connection_id = row[0]
        encrypted_token = row[1]

        try:
            # Decrypt the access token
            access_token = decrypt_token(encrypted_token, fernet)

            # Fetch market from Spotify API
            market = fetch_market_for_connection(str(connection_id), access_token)

            # Update the connection if market was fetched
            if market:
                conn.execute(
                    text("UPDATE service_connection SET market = :market WHERE id = :id"),
                    {"market": market, "id": connection_id},
                )

        except Exception as e:
            # Log error but continue with other connections
            logger.warning(f"Skipping connection {connection_id}: {e}")
            continue

    logger.info("Market backfill completed")


def downgrade() -> None:
    """Clear market for connections (optional rollback)."""
    # Optional: Clear all markets set during backfill
    # In practice, you probably don't want to do this
    logger.info("Downgrade: No action taken (keeping market data)")
