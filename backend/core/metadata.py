import logging
import asyncio
from typing import List, Optional, Dict, Any

import httpx
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

from backend.app.core.config import settings
from backend.core.providers.discogs import DiscogsClient

logger = logging.getLogger("backend.core.metadata")


# Exception for retry logic
class MusicBrainzAPIError(Exception):
    """Custom exception for MusicBrainz API errors."""

    pass


class MetadataVerifier:
    """
    Asynchronous metadata verifier using MusicBrainz (primary) and Discogs (fallback).
    """

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.base_url = "https://musicbrainz.org/ws/2/recording"
        self.headers = {
            "User-Agent": f"{settings.PROJECT_NAME}/0.1.0 " "( https://github.com/dwdozier/vibomat )",
            "Accept": "application/json",
        }
        self.last_request_time = 0.0
        # MusicBrainz allows ~1 req/sec
        self.rate_limit_delay = 1.1
        self.discogs_client = DiscogsClient()

    async def _enforce_rate_limit(self):
        """Sleep to respect MusicBrainz rate limits."""
        elapsed = asyncio.get_event_loop().time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_fixed(2),
        stop=stop_after_attempt(3),
        retry_error_callback=lambda retry_state: (
            retry_state.outcome.result() if retry_state.outcome and retry_state.outcome.result() is not None else None
        ),
    )
    async def search_recording(self, artist: str, track: str) -> List[Dict[str, Any]]:
        """Search MusicBrainz for recordings matching the artist and track."""
        await self._enforce_rate_limit()

        # Lucene search syntax
        query = f'artist:"{artist}" AND recording:"{track}"'
        params = {"query": query, "fmt": "json", "limit": 10}
        url = "https://musicbrainz.org/ws/2/recording"

        try:
            response = await self.http_client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("recordings", [])
        except httpx.HTTPStatusError as e:
            logger.warning(f"MusicBrainz HTTP error for {artist} - {track}: {e}")
            raise MusicBrainzAPIError(f"MB HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.warning(f"MusicBrainz Request error for {artist} - {track}: {e}")
            raise e
        except Exception as e:
            logger.warning(f"Unexpected error querying MusicBrainz: {e}")
            return []

    async def verify_track_version(self, artist: str, track: str, version: str) -> bool:
        """Verify if a track matches the requested version using MusicBrainz (primary)
        and Discogs (fallback) metadata.
        """
        version = version.lower() if version else "studio"

        # 1. Try MusicBrainz
        try:
            recordings = await self.search_recording(artist, track)
            if recordings:
                for rec in recordings:
                    disambiguation = rec.get("disambiguation", "").lower()
                    title = rec.get("title", "").lower()

                    if version == "live":
                        if "live" in disambiguation or "live" in title:
                            return True
                    elif version == "remix":
                        if "remix" in disambiguation or "remix" in title or "mix" in title:
                            return True
                    elif version == "remaster":
                        if "remaster" in disambiguation or "remaster" in title:
                            return True
                    else:
                        # For 'studio' or unspecified, simple existence in MB is enough
                        # provided we aren't looking for a specific alternate version
                        return True
        except MusicBrainzAPIError as e:
            logger.warning(f"MusicBrainz verification failed, falling back to Discogs: {e}")
            # Continue to Discogs fallback
        except Exception as e:
            logger.warning(f"MusicBrainz search failed unexpectedly: {e}")
            # Continue to Discogs fallback

        # 2. Fallback to Discogs
        discogs_uri = await self.discogs_client.search_track(
            artist=artist,
            track=track,
            # We don't have album/version yet, so we only pass the core data.
        )

        if discogs_uri:
            logger.info(f"Found Discogs URI for {artist} - {track}: {discogs_uri}")
            # Since Discogs search is more general, we currently assume existence is enough.
            # We will improve version matching logic later if needed.
            return True

        return False

    async def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Search MusicBrainz for artist metadata."""
        await self._enforce_rate_limit()
        url = "https://musicbrainz.org/ws/2/artist"
        params = {"query": f'artist:"{artist_name}"', "fmt": "json", "limit": 1}
        try:
            response = await self.http_client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            artists = data.get("artists", [])
            if artists:
                return artists[0]
        except Exception as e:
            logger.debug(f"Failed to fetch artist metadata for {artist_name}: {e}")
        return None

    async def search_album(self, artist_name: str, album_name: str) -> Optional[Dict[str, Any]]:
        """Search MusicBrainz for album (release-group) metadata."""
        await self._enforce_rate_limit()
        url = "https://musicbrainz.org/ws/2/release-group"
        query = f'artist:"{artist_name}" AND releasegroup:"{album_name}"'
        params = {"query": query, "fmt": "json", "limit": 1}
        try:
            response = await self.http_client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            groups = data.get("release-groups", [])
            if groups:
                return groups[0]
        except Exception as e:
            logger.debug(f"Failed to fetch album metadata for {artist_name} - {album_name}: {e}")
        return None
