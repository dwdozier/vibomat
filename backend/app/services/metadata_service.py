from backend.core.metadata import MetadataVerifier
from typing import Optional, Dict, Any


class MetadataService:
    def __init__(self):
        self.verifier = MetadataVerifier()

    def get_artist_info(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Fetch enriched metadata for an artist."""
        data = self.verifier.search_artist(artist_name)
        if not data:
            return None

        mb_id = data.get("id")
        return {
            "name": data.get("name"),
            "type": data.get("type"),
            "country": data.get("country"),
            "id": mb_id,
            "source_url": f"https://musicbrainz.org/artist/{mb_id}" if mb_id else None,
            "source_name": "MusicBrainz",
        }
        return None

    def get_album_info(self, artist_name: str, album_name: str) -> Optional[Dict[str, Any]]:
        """Fetch enriched metadata for an album."""
        data = self.verifier.search_album(artist_name, album_name)
        if not data:
            return None

        mb_id = data.get("id")
        return {
            "name": data.get("title"),
            "artist": artist_name,
            "first_release_date": data.get("first-release-date"),
            "primary_type": data.get("primary-type"),
            "id": mb_id,
            "source_url": f"https://musicbrainz.org/release-group/{mb_id}" if mb_id else None,
            "source_name": "MusicBrainz",
        }
        return None
