import musicbrainzngs
import logging
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger("spotify_playlist_builder.metadata")

# Configure MusicBrainz
# We must set a user agent. Using a generic one for this tool.
musicbrainzngs.set_useragent(
    "SpotifyPlaylistBuilder", "0.1.0", "https://github.com/dwdozier/spotify-playlist-builder"
)


class MetadataVerifier:
    def __init__(self):
        self.rate_limit = 1.1  # Seconds (slightly more than 1.0 to be safe)

    @retry(
        retry=retry_if_exception_type(musicbrainzngs.MusicBrainzError),
        wait=wait_fixed(2),  # Wait 2 seconds between retries
        stop=stop_after_attempt(3),
    )
    def search_recording(self, artist: str, track: str) -> list[dict]:
        """
        Search MusicBrainz for recordings matching the artist and track.
        Retries on MusicBrainz errors (which includes 503 Service Unavailable).
        """
        try:
            result = musicbrainzngs.search_recordings(
                query=f'artist:"{artist}" AND recording:"{track}"', limit=10
            )
            return result.get("recording-list", [])
        except musicbrainzngs.ResponseError as e:
            logger.warning(f"MusicBrainz API error: {e}")
            raise e
        except Exception as e:
            logger.warning(f"Unexpected error querying MusicBrainz: {e}")
            return []

    def verify_track_version(self, artist: str, track: str, version: str) -> bool:
        """
        Verify if a track matches the requested version using MusicBrainz metadata.

        Args:
            artist: Artist name
            track: Track name
            version: Preferred version ('live', 'remix', 'studio', etc.)

        Returns:
            True if metadata confirms the version, False otherwise (or if uncertain).
        """
        if not version or version == "studio":
            # Default/Studio is hard to "verify" positively without false negatives,
            # so we assume it's valid unless we find strong evidence otherwise.
            # For now, we'll return True to let the fuzzy search handle it.
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
