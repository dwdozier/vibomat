import logging
import requests
import time
import os
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger("spotify_playlist_builder.metadata")


def get_discogs_token() -> str | None:
    """Retrieve Discogs PAT from env or keyring."""
    try:
        # Check env first
        key = os.getenv("DISCOGS_PAT")
        if key:
            return key

        # Check keyring (if available)
        try:
            import keyring

            key = keyring.get_password("spotify-playlist-builder", "discogs_pat")
            if key:
                return key
        except ImportError:
            pass

    except Exception as e:
        logger.debug(f"Failed to retrieve Discogs Token: {e}")
    return None


class DiscogsVerifier:
    def __init__(self) -> None:
        self.token = get_discogs_token()
        self.base_url = "https://api.discogs.com/database/search"
        self.headers = {
            "User-Agent": "SpotifyPlaylistBuilder/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Discogs token={self.token}"
        self.last_request_time = 0.0
        # Discogs allows 60 req/min -> 1 req/sec
        self.rate_limit_delay = 1.1

    def _enforce_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        wait=wait_fixed(2),
        stop=stop_after_attempt(3),
    )
    def search_recording(self, artist: str, track: str) -> list[dict]:
        """Search Discogs for releases matching the artist and track."""
        if not self.token:
            return []

        self._enforce_rate_limit()

        params = {
            "artist": artist,
            "track": track,
            "type": "release",
            "per_page": 5,
        }

        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.RequestException as e:
            logger.debug(f"Discogs API error: {e}")
            return []
        except Exception as e:
            logger.debug(f"Unexpected error querying Discogs: {e}")
            return []

    def verify_track_version(self, artist: str, track: str, version: str) -> bool:
        """Verify if a track matches the requested version using Discogs metadata."""
        if not self.token:
            return False

        results = self.search_recording(artist, track)

        for res in results:
            title = res.get("title", "").lower()
            formats = res.get("format", [])
            format_str = " ".join(formats).lower()

            # Discogs titles are often "Artist - Track"
            # We can check if the version keywords appear in title or formats
            if version == "live":
                if "live" in title or "live" in format_str:
                    return True
            elif version == "remix":
                if "remix" in title or "mix" in title or "remix" in format_str:
                    return True
            elif version == "remaster":
                if "remaster" in title or "remastered" in format_str:
                    return True
            elif version == "studio":
                # If we found a result that matches artist/track, and it's not explicitly
                # live/remix, we assume it exists as a studio version.
                return True

        return False


class MetadataVerifier:
    def __init__(self) -> None:
        self.base_url = "https://musicbrainz.org/ws/2/recording"
        self.headers = {
            "User-Agent": "SpotifyPlaylistBuilder/0.1.0 "
            "( https://github.com/dwdozier/spotify-playlist-builder )",
            "Accept": "application/json",
        }
        self.last_request_time = 0.0
        # MusicBrainz allows ~1 req/sec
        self.rate_limit_delay = 1.1
        self.discogs = DiscogsVerifier()

    def _enforce_rate_limit(self):
        """Sleep to respect MusicBrainz rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        wait=wait_fixed(2),
        stop=stop_after_attempt(3),
    )
    def search_recording(self, artist: str, track: str) -> list[dict]:
        """Search MusicBrainz for recordings matching the artist and track."""
        self._enforce_rate_limit()

        # Lucene search syntax
        query = f'artist:"{artist}" AND recording:"{track}"'
        params = {"query": query, "fmt": "json", "limit": 10}

        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("recordings", [])
        except requests.RequestException as e:
            logger.warning(f"MusicBrainz API error: {e}")
            raise e
        except Exception as e:
            logger.warning(f"Unexpected error querying MusicBrainz: {e}")
            return []

    def verify_track_version(self, artist: str, track: str, version: str) -> bool:
        """Verify if a track matches the requested version using MusicBrainz metadata."""
        if not version or version == "studio":
            # Just check if it exists
            pass

        # 1. Try MusicBrainz
        try:
            recordings = self.search_recording(artist, track)
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
        except Exception:
            pass

        # 2. Fallback to Discogs if MusicBrainz didn't confirm the specific version
        # OR if MusicBrainz didn't find the track at all.
        if self.discogs.verify_track_version(artist, track, version or "studio"):
            logger.info(f"Verified {artist} - {track} ({version}) via Discogs.")
            return True

        # If MB found it but we were looking for a specific version (e.g. remix)
        # and didn't find it in MB, we still fell through to Discogs.
        # If Discogs also failed, we return False.
        # However, if we just wanted 'studio' (default) and MB found it, we returned True above.

        return False
