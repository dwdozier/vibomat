import os
import logging
from enum import Enum
from typing import Tuple

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

logger = logging.getLogger("backend.core.auth")


class CredentialSource(str, Enum):
    env = "env"
    keyring = "keyring"


def get_credentials_from_env(silent: bool = False) -> Tuple[str, str] | None:
    """Get credentials from .env file."""
    from dotenv import load_dotenv

    load_dotenv()
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        if silent:
            return None
        raise Exception(
            "Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found in .env file.\n"
            "Create a .env file with:\n"
            "  SPOTIFY_CLIENT_ID=your_id\n"
            "  SPOTIFY_CLIENT_SECRET=your_secret"
        )
    return client_id, client_secret


def get_credentials_from_keyring(
    service: str = "spotify-playlist-builder", silent: bool = False
) -> Tuple[str, str] | None:
    """Get credentials from macOS Keychain (or OS credential store)."""
    if keyring is None:
        if silent:
            return None
        raise Exception("keyring library not available. Install it with:\n  uv sync")

    client_id = keyring.get_password(service, "client_id")
    client_secret = keyring.get_password(service, "client_secret")

    if not client_id or not client_secret:
        if silent:
            return None
        raise Exception("Credentials not found in keychain. Run store-credentials first.")

    return client_id, client_secret


def store_credentials_in_keyring(
    client_id: str, client_secret: str, service: str = "spotify-playlist-builder"
) -> None:
    """Store credentials in macOS Keychain (or OS credential store)."""
    if keyring is None:
        raise Exception("keyring library not available")
    keyring.set_password(service, "client_id", client_id)
    keyring.set_password(service, "client_secret", client_secret)
    logger.info(f"✓ Credentials stored securely in {keyring.get_keyring().__class__.__name__}")


def get_credentials(source: str | None = None) -> Tuple[str, str]:
    """Get Spotify credentials from specified source or auto-discover."""
    if source == "env":
        result = get_credentials_from_env()
        if result is None:
            raise Exception("Failed to load credentials from env.")
        return result
    elif source == "keyring":
        result = get_credentials_from_keyring()
        if result is None:
            raise Exception("Failed to load credentials from keyring.")
        return result
    elif source is None:
        logger.debug("Attempting to retrieve credentials from Keychain...")
        creds = get_credentials_from_keyring(silent=True)
        if creds:
            return creds
        logger.debug("Keychain failed/empty. Falling back to .env...")
        creds = get_credentials_from_env(silent=True)
        if creds:
            return creds
        raise Exception("Credentials not found. Configure system keychain or a .env file.")
    else:
        raise ValueError(f"Unknown credential source: {source}. Use 'env' or 'keyring'")


def get_builder(source: CredentialSource | None = None):
    """Helper to initialize SpotifyPlaylistBuilder with credentials."""
    from .client import SpotifyPlaylistBuilder

    source_val = source.value if source else None
    logger.info(f"Fetching credentials (source: {source_val or 'auto'})...")

    client_id, secret = get_credentials(source_val)
    return SpotifyPlaylistBuilder(client_id, secret)
