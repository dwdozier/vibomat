import spotipy
import logging
import json
import os
from pathlib import Path
from typing import Any
from spotipy.oauth2 import SpotifyOAuth
from .metadata import MetadataVerifier
from .utils.helpers import _similarity, _determine_version, rate_limit_retry, to_snake_case

logger = logging.getLogger("spotify_playlist_builder.client")


class SpotifyPlaylistBuilder:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "https://127.0.0.1:8888/callback",
    ) -> None:
        """Initialize Spotify API client with OAuth authentication."""
        scope = [
            "playlist-modify-public",
            "playlist-modify-private",
            "playlist-read-private",
            "playlist-read-collaborative",
        ]
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                open_browser=True,
            )
        )
        user = self.sp.current_user()
        if user is None:
            raise Exception("Failed to authenticate with Spotify")
        self.user_id = user["id"]
        self.metadata_verifier = MetadataVerifier()

    def _similarity(self, s1: str, s2: str) -> float:
        """Proxy to similarity helper."""
        return _similarity(s1, s2)

    def _determine_version(self, track_name: str, album_name: str) -> str:
        """Proxy to determine_version helper."""
        return _determine_version(track_name, album_name)

    @rate_limit_retry
    def search_track(
        self, artist: str, track: str, album: str | None = None, version: str | None = None
    ) -> str | None:
        """Search for a track on Spotify using fuzzy matching and external verification."""
        if album:
            query = f"track:{track} artist:{artist} album:{album}"
            results = self.sp.search(q=query, type="track", limit=1)
            if results and results["tracks"]["items"]:
                return results["tracks"]["items"][0]["uri"]

        query = f"track:{track} artist:{artist}"
        results = self.sp.search(q=query, type="track", limit=20)
        if results is None or not results["tracks"]["items"]:
            return None

        candidates = results["tracks"]["items"]
        best_match = None
        best_score = -1.0

        for item in candidates:
            score = 0.0
            item_name = item["name"]
            item_artists = [a["name"] for a in item["artists"]]
            item_album = item["album"]["name"]

            # Artist Match (Weight: 30)
            artist_match = max(self._similarity(artist, a) for a in item_artists)
            score += artist_match * 30

            # Track Name Match (Weight: 40)
            track_match = self._similarity(track, item_name)
            score += track_match * 40

            # Album/Version Preference (Weight: 30)
            if album:
                album_match = self._similarity(album, item_album)
                score += album_match * 30
            else:
                detected_version = self._determine_version(item_name, item_album)

                if version == "live":
                    score += 30 if detected_version == "live" else 5
                elif version == "remix":
                    score += 30 if detected_version == "remix" else 5
                elif version == "compilation":
                    score += 30 if detected_version == "compilation" else 5
                elif version == "remaster":
                    score += 30 if detected_version == "remaster" else 5
                elif version == "original":
                    # For original, we specifically want studio and NOT remaster
                    if detected_version == "studio":
                        score += 30
                    elif detected_version == "remaster":
                        score += 10
                    else:
                        score += 5
                else:
                    # Default: Studio/Original preference
                    if detected_version == "studio":
                        score += 30
                    elif detected_version == "remaster":
                        score += 20  # Remaster is better than live/remix if we want studio
                    else:
                        score += 10

            # 4. External Metadata Verification (Weight: 20)
            if version in ["live", "remix", "remaster"]:
                try:
                    primary_artist = item_artists[0] if item_artists else artist
                    if self.metadata_verifier.verify_track_version(
                        primary_artist, item_name, version
                    ):
                        score += 20
                except Exception as e:
                    logger.debug(f"Metadata verification skipped: {e}")

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score > 60:
            return best_match["uri"]
        return None

    @rate_limit_retry
    def find_playlist_by_name(self, playlist_name: str) -> str | None:
        """Find a playlist by name for the authenticated user."""
        offset = 0
        limit = 50
        while True:
            playlists = self.sp.current_user_playlists(limit=limit, offset=offset)
            if playlists is None:
                break
            for playlist in playlists["items"]:
                if playlist["name"] == playlist_name and playlist["owner"]["id"] == self.user_id:
                    return playlist["id"]
            if not playlists["next"]:
                break
            offset += limit
        return None

    @rate_limit_retry
    def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        """Get all track URIs from a playlist."""
        tracks = []
        offset = 0
        limit = 100
        while True:
            results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            if results is None:
                break
            tracks.extend([item["track"]["uri"] for item in results["items"] if item["track"]])
            if not results["next"]:
                break
            offset += limit
        return tracks

    @rate_limit_retry
    def clear_playlist(self, playlist_id: str) -> None:
        """Remove all tracks from a playlist."""
        track_uris = self.get_playlist_tracks(playlist_id)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)

    @rate_limit_retry
    def create_playlist(
        self, playlist_name: str, description: str = "", public: bool = False
    ) -> str:
        """Create a new playlist for the authenticated user."""
        playlist = self.sp.user_playlist_create(
            user=self.user_id, name=playlist_name, public=public, description=description
        )
        if playlist is None:
            raise Exception(f"Failed to create playlist '{playlist_name}'")
        return playlist["id"]

    @rate_limit_retry
    def update_playlist_details(
        self, playlist_id: str, description: str, public: bool = False
    ) -> None:
        """Update playlist details if they differ."""
        playlist = self.sp.playlist(playlist_id)
        if playlist is None:
            return
        current_description = playlist.get("description") or ""
        current_public = playlist.get("public")
        changes = {}
        if current_description != description:
            changes["description"] = description
        if current_public != public:
            changes["public"] = public
        if changes:
            logger.info(f"Updating playlist details: {', '.join(changes.keys())}...")
            self.sp.playlist_change_details(playlist_id, **changes)

    @rate_limit_retry
    def _add_track_uris_to_playlist(self, playlist_id: str, track_uris: list[str]) -> None:
        """Add track URIs to a playlist in batches."""
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            self.sp.playlist_add_items(playlist_id, batch)

    def add_tracks_to_playlist(self, playlist_id: str, tracks: list[dict[str, Any]]) -> list[str]:
        """Add tracks to a playlist, handling batch operations."""
        uris = []
        failed_tracks = []

        for i, track in enumerate(tracks):
            # Ensure we have strings, defaulting to empty string if missing
            artist = str(track.get("artist", ""))
            track_name = str(track.get("track", ""))
            album = track.get("album")
            version = track.get("version")
            if album:
                album = str(album)
            if version:
                version = str(version)

            uri = self.search_track(artist, track_name, album, version)

            if uri:
                uris.append(uri)
            else:
                failed_tracks.append(f"{artist} - {track_name}")

            # Add in batches of 100 (Spotify API limit)
            if len(uris) == 100 or i == len(tracks) - 1:
                if uris:
                    self._add_track_uris_to_playlist(playlist_id, uris)
                    uris = []

        return failed_tracks

    @rate_limit_retry
    def get_playlist_tracks_details(self, playlist_id: str) -> list[dict[str, str]]:
        """Get full track details from a playlist for export."""
        tracks = []
        offset = 0
        limit = 100
        while True:
            results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            if results is None:
                break
            for item in results["items"]:
                track = item.get("track")
                if track:
                    artist_name = track["artists"][0]["name"] if track["artists"] else "Unknown"
                    tracks.append(
                        {
                            "artist": artist_name,
                            "track": track["name"],
                            "album": track["album"]["name"],
                            "version": self._determine_version(
                                track["name"], track["album"]["name"]
                            ),
                        }
                    )
            if not results["next"]:
                break
            offset += limit
        return tracks

    def export_playlist_to_json(self, playlist_name: str, output_file: str) -> None:
        """Export an existing playlist to a JSON file."""
        playlist_id = self.find_playlist_by_name(playlist_name)
        if not playlist_id:
            raise Exception(f"Playlist '{playlist_name}' not found.")
        playlist_info = self.sp.playlist(playlist_id)
        if playlist_info is None:
            raise Exception("Failed to fetch details")
        tracks = self.get_playlist_tracks_details(playlist_id)
        export_data = {
            "name": playlist_name,
            "description": playlist_info.get("description") or "",
            "public": playlist_info.get("public"),
            "tracks": tracks,
        }
        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)
        logger.info(f"✓ Successfully exported {len(tracks)} tracks to {output_file}")

    def backup_all_playlists(self, output_dir: str) -> None:
        """Backup all user playlists to JSON files in a directory."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        offset, limit, playlists = 0, 50, []
        while True:
            results = self.sp.current_user_playlists(limit=limit, offset=offset)
            if results is None:
                break
            playlists.extend(results["items"])
            if not results["next"]:
                break
            offset += limit
        for pl in playlists:
            safe_name = to_snake_case(pl["name"])
            filepath = os.path.join(output_dir, f"{safe_name or pl['id']}.json")
            try:
                self.export_playlist_to_json(pl["name"], filepath)
            except Exception as e:
                logger.error(f"Failed to backup '{pl['name']}': {e}")

    def build_playlist_from_json(self, json_file: str, dry_run: bool = False) -> None:
        """Build or update a playlist from a JSON file."""
        with open(json_file, "r") as f:
            data = json.load(f)
        playlist_name = data.get("name", "New Playlist")
        new_track_uris, failed_tracks = [], []
        for track in data.get("tracks", []):
            uri = self.search_track(
                track.get("artist"), track.get("track"), track.get("album"), track.get("version")
            )
            if uri:
                new_track_uris.append(uri)
            else:
                failed_tracks.append(f"{track.get('artist')} - {track.get('track')}")

        if dry_run:
            logger.info(
                f"Dry run complete. Found {len(new_track_uris)}, missing {len(failed_tracks)}."
            )
            return

        existing_pid = self.find_playlist_by_name(playlist_name)
        if existing_pid:
            self.update_playlist_details(
                existing_pid, data.get("description", ""), data.get("public", False)
            )
            if self.get_playlist_tracks(existing_pid) != new_track_uris:
                self.clear_playlist(existing_pid)
                self._add_track_uris_to_playlist(existing_pid, new_track_uris)
            playlist_id = existing_pid
        else:
            playlist_id = self.create_playlist(
                playlist_name, data.get("description", ""), data.get("public", False)
            )
            self._add_track_uris_to_playlist(playlist_id, new_track_uris)

        logger.info(f"Playlist ready: https://open.spotify.com/playlist/{playlist_id}")
