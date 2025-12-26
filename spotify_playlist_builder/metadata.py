import logging
import requests
import time
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger("spotify_playlist_builder.metadata")


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
            return True

        recordings = self.search_recording(artist, track)

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

        return False
