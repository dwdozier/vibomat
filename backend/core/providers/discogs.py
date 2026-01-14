from typing import List, Optional, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.core.config import settings
from backend.core.providers.base import BaseMusicProvider
import logging

logger = logging.getLogger("backend.core.providers.discogs")


class DiscogsAPIError(Exception):
    """Custom exception for Discogs API errors."""

    pass


def retry_if_not_auth_error(exception: BaseException) -> bool:
    """Predicate to retry on API errors, but not on authentication errors."""
    if isinstance(exception, httpx.HTTPStatusError):
        # Do not retry on 401 Unauthorized (Auth token expired/invalid)
        return exception.response.status_code != 401
    return True


class DiscogsClient(BaseMusicProvider):
    """
    A client for the Discogs API using a Personal Access Token (PAT).
    This client is designed for metadata enrichment, complementing Spotify's data.
    """

    def __init__(self):
        if not settings.DISCOGS_PAT:
            raise ValueError("DISCOGS_PAT is not configured in settings.")

        self.base_url = "https://api.discogs.com"
        self.headers = {
            "Authorization": f"Discogs token={settings.DISCOGS_PAT}",
            "User-Agent": settings.PROJECT_NAME,  # Required by Discogs API
        }
        self.http_client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=10)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError) | retry_if_exception_type(httpx.RequestError),
        retry_error_callback=lambda retry_state: (
            retry_state.outcome.result() if retry_state.outcome and retry_state.outcome.result() is not None else None
        ),
    )
    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Internal asynchronous GET request with retry logic."""
        response = await self.http_client.get(endpoint, params=params)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Discogs not found: {endpoint} - {e.response.text}")
                return None

            logger.error(f"Discogs API error on {endpoint}: {e}")
            raise DiscogsAPIError(f"Discogs API error: {e.response.status_code}") from e

        return response.json()

    async def search_track(
        self,
        artist: str,
        track: str,
        album: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Searches Discogs for a track and returns a dict with the Discogs URI.
        This implementation is deliberately minimal for now.
        """
        query_parts = [f"{artist} - {track}"]
        if album:
            query_parts.insert(0, album)  # Prefer album match

        params = {
            "query": " ".join(query_parts),
            "type": "master",  # Search for the master release
            "per_page": 1,
        }

        # Discogs uses 'master' for albums and 'release' for singles/specific versions.
        # We start by searching for the master release.
        master_data = await self._get("/database/search", params=params)

        if master_data and master_data.get("results"):
            # For simplicity, we just return the first match's URI
            result = master_data["results"][0]
            if result.get("type") == "master":
                return {"uri": f"discogs:master:{result.get('id')}"}
            elif result.get("type") == "release":
                return {"uri": f"discogs:release:{result.get('id')}"}

        return None

    async def get_metadata(self, discogs_uri: str) -> Optional[Dict[str, Any]]:
        """
        Fetches detailed metadata from a Discogs URI (e.g., discogs:master:12345).
        """
        try:
            uri_type, uri_id = discogs_uri.split(":")[1:]
        except ValueError:
            logger.warning(f"Invalid Discogs URI format: {discogs_uri}")
            return None

        if uri_type == "master":
            endpoint = f"/masters/{uri_id}"
        elif uri_type == "release":
            endpoint = f"/releases/{uri_id}"
        else:
            logger.warning(f"Unsupported Discogs URI type: {uri_type}")
            return None

        data = await self._get(endpoint)

        if not data:
            return None

        # Transform the raw API response into a cleaner format
        artist_name = "Unknown"
        if data.get("artists"):
            artist_name = data["artists"][0].get("name", "Unknown")

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "artist": artist_name,
            "year": data.get("year"),
        }

    # BaseMusicProvider methods (not used for Discogs, but required by abstract class)
    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> str:
        raise NotImplementedError("Discogs is for metadata only.")

    async def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        raise NotImplementedError("Discogs is for metadata only.")

    async def replace_playlist_tracks(self, playlist_id: str, track_uris: List[str]) -> None:
        raise NotImplementedError("Discogs is for metadata only.")

    async def get_playlist(self, playlist_id: str) -> dict:
        raise NotImplementedError("Discogs is for metadata only.")
