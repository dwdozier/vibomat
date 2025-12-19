import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import sys
import os
import subprocess
import difflib
from pathlib import Path
from typing import Any

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    # Optional dependency: Set to None if not installed.
    # Type ignore required because we are assigning None to a module name.
    keyring = None  # type: ignore
    KEYRING_AVAILABLE = False


# Credential Management Functions
def get_credentials_from_env() -> tuple[str, str]:
    """Get credentials from .env file."""
    from dotenv import load_dotenv

    load_dotenv()
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise Exception(
            "Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found in .env file.\n"
            "Create a .env file with:\n"
            "  SPOTIFY_CLIENT_ID=your_id\n"
            "  SPOTIFY_CLIENT_SECRET=your_secret"
        )

    return client_id, client_secret


def list_1password_vaults() -> None:
    """List available 1Password vaults."""
    try:
        result = subprocess.run(
            "op vault list", shell=True, capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print("Available 1Password vaults:")
            print(result.stdout)
        else:
            print("Error listing vaults. Make sure you're signed in: eval $(op signin)")
    except FileNotFoundError:
        print("1Password CLI not found. Install it at:")
        print("https://developer.1password.com/docs/cli/get-started")


def get_credentials_from_1password(
    vault: str = "Private",
    item: str = "SpotifyPlaylistBuilder",
    id_field: str = "client_id",
    secret_field: str = "client_secret",
) -> tuple[str, str]:
    """Get credentials from 1Password vault."""
    try:
        cmd_id = f'op read "op://{vault}/{item}/{id_field}"'
        cmd_secret = f'op read "op://{vault}/{item}/{secret_field}"'

        result_id = subprocess.run(cmd_id, shell=True, capture_output=True, text=True, check=False)
        result_secret = subprocess.run(
            cmd_secret, shell=True, capture_output=True, text=True, check=False
        )

        if result_id.returncode != 0 or result_secret.returncode != 0:
            error_msg = result_id.stderr or result_secret.stderr
            raise Exception(
                f"Failed to fetch from 1Password vault '{vault}'.\n"
                f"\nCommon vault names by account type:\n"
                f"  • Individual accounts: 'Personal' or 'Private'\n"
                f"  • Family accounts: 'Private' or 'Shared'\n"
                f"  • Team/Business accounts: 'Employee', 'Private', or custom team vaults\n"
                f"\nTo see your available vaults:\n"
                f"  python spotify_playlist_builder.py --list-vaults\n"
                f"\nThen specify the correct vault:\n"
                f"  python spotify_playlist_builder.py playlist.json "
                f"--source 1password --vault YourVaultName\n"
                f"\nMake sure:\n"
                f"  1. You're authenticated: eval $(op signin)\n"
                f"  2. Item named '{item}' exists in vault '{vault}'\n"
                f"  3. Fields '{id_field}' and '{secret_field}' exist on that item\n"
                f"\nError details: {error_msg}"
            )

        # Ensure stdout is not None before stripping
        client_id = result_id.stdout.strip()
        client_secret = result_secret.stdout.strip()

        return client_id, client_secret

    except FileNotFoundError:
        raise Exception(
            "1Password CLI not found. Install it at:\n"
            "https://developer.1password.com/docs/cli/get-started"
        )


def get_credentials_from_keyring(service: str = "spotify-playlist-builder") -> tuple[str, str]:
    """Get credentials from macOS Keychain (or OS credential store)."""
    if keyring is None:
        raise Exception("keyring library not available. Install it with:\n" "  uv sync")

    client_id = keyring.get_password(service, "client_id")
    client_secret = keyring.get_password(service, "client_secret")

    if not client_id or not client_secret:
        raise Exception(
            f"Credentials not found in keychain.\n"
            f"To store credentials, run the helper command:\n"
            f"  python spotify_playlist_builder.py --store-credentials\n"
            f"\nOr manually:\n"
            f'  python -c "import keyring; '
            f"keyring.set_password('{service}', 'client_secret', 'YOUR_CLIENT_SECRET')\"\n"
            f"\nOr use the helper command (if added):\n"
            f"  python spotify_playlist_builder.py --store-credentials"
        )

    return client_id, client_secret


def store_credentials_in_keyring(
    client_id: str, client_secret: str, service: str = "spotify-playlist-builder"
) -> None:
    """Store credentials in macOS Keychain (or OS credential store)."""
    if keyring is None:
        raise Exception("keyring library not available")

    keyring.set_password(service, "client_id", client_id)
    keyring.set_password(service, "client_secret", client_secret)
    print(f"✓ Credentials stored securely in {keyring.get_keyring().__class__.__name__}")


def get_credentials(
    source: str = "env", vault: str = "Private", item: str = "SpotifyPlaylistBuilder"
) -> tuple[str, str]:
    """
    Get Spotify credentials from specified source.

    Args:
        source: "env" for .env file, "keyring" for OS keychain, or "1password" for 1Password vault
        vault: 1Password vault name (default: Private)
        item: 1Password item name (default: SpotifyPlaylistBuilder)

    Returns:
        Tuple of (client_id, client_secret)
    """
    if source.lower() == "env":
        return get_credentials_from_env()
    elif source.lower() == "keyring":
        return get_credentials_from_keyring()
    elif source.lower() == "1password":
        return get_credentials_from_1password(vault, item)
    else:
        raise ValueError(
            f"Unknown credential source: {source}. Use 'env', 'keyring', or '1password'"
        )


# Spotify Playlist Builder Class
class SpotifyPlaylistBuilder:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "https://127.0.0.1:8888/callback",
    ) -> None:
        """Initialize Spotify API client with OAuth authentication."""
        scope = "playlist-modify-public playlist-modify-private"
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                open_browser=True,
            )
        )
        # Get the current authenticated user's ID
        user = self.sp.current_user()
        if user is None:
            raise Exception("Failed to authenticate with Spotify: current_user() returned None")
        self.user_id = user["id"]

    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity ratio."""
        return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

    def search_track(self, artist: str, track: str, album: str | None = None) -> str | None:
        """
        Search for a track on Spotify using fuzzy matching to find the best version.

        Args:
            artist: Artist name
            track: Track name
            album: Optional album name to prefer/filter by

        Returns:
            Spotify URI if found, None otherwise
        """
        # 1. Try specific search if album is provided (Exact Match Strategy)
        if album:
            query = f"track:{track} artist:{artist} album:{album}"
            results = self.sp.search(q=query, type="track", limit=1)
            if results and results["tracks"]["items"]:
                return results["tracks"]["items"][0]["uri"]

        # 2. Fallback: Broader search with fuzzy matching (Best Match Strategy)
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

            # 1. Artist Match (Weight: 30)
            artist_match = max(self._similarity(artist, a) for a in item_artists)
            score += artist_match * 30

            # 2. Track Name Match (Weight: 40)
            track_match = self._similarity(track, item_name)
            score += track_match * 40

            # 3. Album Preference (Weight: 30)
            if album:
                album_match = self._similarity(album, item_album)
                score += album_match * 30
            else:
                # Prefer studio albums over compilations
                compilation_keywords = ["greatest hits", "best of", "collection", "anthology"]
                is_compilation = any(k in item_album.lower() for k in compilation_keywords)
                score += 10 if is_compilation else 30

            if score > best_score:
                best_score = score
                best_match = item

        # Threshold check (60/100) to ensure we don't return garbage
        if best_match and best_score > 60:
            return best_match["uri"]

        return None

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

    def clear_playlist(self, playlist_id: str) -> None:
        """Remove all tracks from a playlist."""
        track_uris = self.get_playlist_tracks(playlist_id)

        # Remove in batches of 100 (Spotify API limit)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)

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

    def update_playlist_details(
        self, playlist_id: str, description: str, public: bool = False
    ) -> None:
        """Update playlist details if they differ."""
        playlist = self.sp.playlist(playlist_id)
        if playlist is None:
            return

        # Check description (handle None from API)
        current_description = playlist.get("description") or ""
        current_public = playlist.get("public")

        changes = {}
        if current_description != description:
            changes["description"] = description

        if current_public != public:
            changes["public"] = public

        if changes:
            print(f"Updating playlist details: {', '.join(changes.keys())}...")
            self.sp.playlist_change_details(playlist_id, **changes)

    def _add_track_uris_to_playlist(self, playlist_id: str, track_uris: list[str]) -> None:
        """Add track URIs to a playlist in batches."""
        # Add in batches of 100 (Spotify API limit)
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
            if album:
                album = str(album)

            uri = self.search_track(artist, track_name, album)

            if uri:
                uris.append(uri)
            else:
                failed_tracks.append(f"{artist} - {track_name}")

            # Add in batches of 100 (Spotify API limit)
            if len(uris) == 100 or i == len(tracks) - 1:
                if uris:
                    self.sp.playlist_add_items(playlist_id, uris)
                    uris = []

        return failed_tracks

    def get_playlist_tracks_details(self, playlist_id: str) -> list[dict[str, str]]:
        """Get full track details from a playlist for export."""
        tracks: list[dict[str, str]] = []
        offset = 0
        limit = 100

        while True:
            results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            if results is None:
                break

            for item in results["items"]:
                track = item.get("track")
                if track:
                    # Get primary artist
                    artists = track.get("artists", [])
                    artist_name = artists[0]["name"] if artists else "Unknown"

                    track_data = {
                        "artist": artist_name,
                        "track": track["name"],
                        "album": track["album"]["name"],
                    }
                    tracks.append(track_data)

            if not results["next"]:
                break
            offset += limit

        return tracks

    def export_playlist_to_json(self, playlist_name: str, output_file: str) -> None:
        """Export an existing playlist to a JSON file."""
        print(f"Searching for playlist: {playlist_name}")
        playlist_id = self.find_playlist_by_name(playlist_name)

        if not playlist_id:
            raise Exception(f"Playlist '{playlist_name}' not found in your library.")

        # Get playlist details for description
        playlist_info = self.sp.playlist(playlist_id)
        if playlist_info is None:
            raise Exception(f"Failed to fetch details for playlist ID: {playlist_id}")

        description = playlist_info.get("description") or ""
        public = playlist_info.get("public")

        print(f"Fetching tracks for '{playlist_name}'...")
        tracks = self.get_playlist_tracks_details(playlist_id)

        export_data = {
            "name": playlist_name,
            "description": description,
            "public": public,
            "tracks": tracks,
        }

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"✓ Successfully exported {len(tracks)} tracks to {output_file}")

    def backup_all_playlists(self, output_dir: str) -> None:
        """Backup all user playlists to JSON files in a directory."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        print("Fetching all playlists...")
        offset = 0
        limit = 50
        playlists = []

        while True:
            results = self.sp.current_user_playlists(limit=limit, offset=offset)
            if results is None:
                break
            playlists.extend(results["items"])
            if not results["next"]:
                break
            offset += limit

        print(f"Found {len(playlists)} playlists. Starting backup...")

        for i, pl in enumerate(playlists):
            name = pl["name"]
            pid = pl["id"]
            # Sanitize filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
            if not safe_name:
                safe_name = f"playlist_{pid}"
            filename = f"{safe_name}.json"
            filepath = os.path.join(output_dir, filename)

            print(f"[{i+1}/{len(playlists)}] Backing up: {name}")
            try:
                self.export_playlist_to_json(name, filepath)
            except Exception as e:
                print(f"  Failed to backup '{name}': {e}")

    def build_playlist_from_json(self, json_file: str, dry_run: bool = False) -> None:
        """Build or update a playlist from a JSON file."""
        with open(json_file, "r") as f:
            playlist_data = json.load(f)

        playlist_name = playlist_data.get("name", "New Playlist")
        description = playlist_data.get("description", "")
        public = playlist_data.get("public", False)
        tracks = playlist_data.get("tracks", [])

        print(f"Authenticated as: {self.user_id}")
        print(f"Processing playlist: {playlist_name}")

        if dry_run:
            print("DRY RUN MODE: No changes will be made to your Spotify account.")

        # Search for tracks with updated logic (prefer studio albums)
        print(f"Searching for {len(tracks)} tracks (preferring studio albums)...")
        new_track_uris = []
        failed_tracks = []

        for track in tracks:
            artist = track.get("artist")
            track_name = track.get("track")
            album = track.get("album")
            uri = self.search_track(artist, track_name, album)

            if uri:
                new_track_uris.append(uri)
            else:
                failed_tracks.append(f"{artist} - {track_name}")

        if dry_run:
            print("\n[Dry Run Summary]")
            print(f"Playlist: {playlist_name}")
            print(f"Tracks found: {len(new_track_uris)}")
            print(f"Tracks missing: {len(failed_tracks)}")

            if failed_tracks:
                print(f"\n⚠️  {len(failed_tracks)} tracks not found:")
                for track in failed_tracks:
                    print(f"  - {track}")
            else:
                print("\n✓ All tracks found successfully.")
            return

        # Check if playlist already exists
        existing_playlist_id = self.find_playlist_by_name(playlist_name)

        if existing_playlist_id:
            print(f"Found existing playlist (ID: {existing_playlist_id})")

            self.update_playlist_details(existing_playlist_id, description, public=public)

            current_track_uris = self.get_playlist_tracks(existing_playlist_id)

            # Compare current tracks with new tracks
            if current_track_uris == new_track_uris:
                print("Playlist is already up to date, no changes needed.")
            else:
                print(
                    f"Playlist needs updating "
                    f"(current: {len(current_track_uris)} tracks, "
                    f"# new: {len(new_track_uris)} tracks)"
                )
                print("Clearing existing tracks...")
                self.clear_playlist(existing_playlist_id)
                print("Adding updated tracks...")
                self._add_track_uris_to_playlist(existing_playlist_id, new_track_uris)
                print("✓ Playlist updated successfully!")

            playlist_id = existing_playlist_id
        else:
            print("Creating new playlist...")
            playlist_id = self.create_playlist(playlist_name, description, public=public)
            print(f"Playlist created (ID: {playlist_id})")
            print(f"Adding {len(new_track_uris)} tracks...")
            self._add_track_uris_to_playlist(playlist_id, new_track_uris)
            print("✓ Playlist created successfully!")

        if failed_tracks:
            print(f"\n⚠️  {len(failed_tracks)} tracks not found:")
            for track in failed_tracks:
                print(f"  - {track}")

        print(f"\nPlaylist ready: https://open.spotify.com/playlist/{playlist_id}")


# Main Execution
def main() -> None:
    # Handle --list-vaults command
    if "--list-vaults" in sys.argv:
        list_1password_vaults()
        return

    # Handle --store-credentials command
    if "--store-credentials" in sys.argv:
        print("Store Spotify credentials in macOS Keychain")
        client_id = input("Enter Spotify Client ID: ").strip()
        client_secret = input("Enter Spotify Client Secret: ").strip()

        if client_id and client_secret:
            try:
                store_credentials_in_keyring(client_id, client_secret)
                print("\nCredentials stored! You can now use: --source keyring")
            except Exception as e:
                print(f"Error storing credentials: {e}")
                sys.exit(1)
        else:
            print("Error: Both Client ID and Client Secret are required")
            sys.exit(1)
        return

    if len(sys.argv) < 2:
        print(
            "Usage: python spotify_playlist_builder.py <json_file> "
            "[--source env|keyring|1password] [--vault VAULT_NAME] [--dry-run] "
            "[--export PLAYLIST_NAME] "
            "[--backup-all [DIRECTORY]]"
        )
        print("\nExamples:")
        print("  python spotify_playlist_builder.py playlist.json")
        print("  python spotify_playlist_builder.py playlist.json --source keyring")
        print("  python spotify_playlist_builder.py playlist.json --source env")
        print("  python spotify_playlist_builder.py playlist.json --dry-run")
        print("  python spotify_playlist_builder.py backup.json --export 'My Playlist'")
        print("  python spotify_playlist_builder.py --backup-all backups/")
        print("  python spotify_playlist_builder.py playlist.json --source 1password")
        print(
            "  python spotify_playlist_builder.py playlist.json "
            "--source 1password --vault Personal"
        )
        print("\nHelper commands:")
        print(
            "  python spotify_playlist_builder.py --store-credentials  "
            "# Store credentials in macOS Keychain"
        )
        print(
            "  python spotify_playlist_builder.py --list-vaults        "
            "# List available 1Password vaults"
        )
        print("\nNote: The playlist will be created for the authenticated Spotify user.")
        sys.exit(1)

    json_file = sys.argv[1]

    # Parse optional source argument
    source = "env"  # Default to .env
    if "--source" in sys.argv:
        source_idx = sys.argv.index("--source")
        if source_idx + 1 < len(sys.argv):
            source = sys.argv[source_idx + 1]

    # Parse optional vault argument (for 1Password)
    vault = "Private"  # Default vault
    if "--vault" in sys.argv:
        vault_idx = sys.argv.index("--vault")
        if vault_idx + 1 < len(sys.argv):
            vault = sys.argv[vault_idx + 1]

    # Parse dry-run argument
    dry_run = "--dry-run" in sys.argv

    # Parse export argument
    export_playlist_name = None
    if "--export" in sys.argv:
        export_idx = sys.argv.index("--export")
        if export_idx + 1 < len(sys.argv):
            export_playlist_name = sys.argv[export_idx + 1]
        else:
            print("Error: --export requires a playlist name")
            sys.exit(1)

    # Parse backup-all argument
    backup_dir = None
    if "--backup-all" in sys.argv:
        backup_idx = sys.argv.index("--backup-all")
        if backup_idx + 1 < len(sys.argv) and not sys.argv[backup_idx + 1].startswith("-"):
            backup_dir = sys.argv[backup_idx + 1]
        else:
            backup_dir = "backups"

    # Validate inputs
    if not export_playlist_name and not backup_dir and not Path(json_file).exists():
        print(f"Error: {json_file} not found")
        sys.exit(1)

    try:
        # Get credentials from specified source
        if source.lower() == "1password":
            print(f"Fetching credentials from {source} (vault: {vault})...")
        else:
            print(f"Fetching credentials from {source}...")
        client_id, client_secret = get_credentials(source, vault=vault)

        # Build playlist
        builder = SpotifyPlaylistBuilder(client_id, client_secret)
        if backup_dir:
            builder.backup_all_playlists(backup_dir)
        elif export_playlist_name:
            builder.export_playlist_to_json(export_playlist_name, json_file)
        else:
            builder.build_playlist_from_json(json_file, dry_run=dry_run)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
