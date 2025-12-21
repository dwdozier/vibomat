#!/usr/bin/env python3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
import difflib
import sys
import subprocess
from pathlib import Path
from typing import Any, Annotated
import typer
from enum import Enum

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    # Optional dependency: Set to None if not installed.
    # Type ignore required because we are assigning None to a module name.
    keyring = None  # type: ignore
    KEYRING_AVAILABLE = False

app = typer.Typer(help="Spotify Playlist Builder CLI")


class CredentialSource(str, Enum):
    env = "env"
    keyring = "keyring"


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


def get_credentials(source: str = "env") -> tuple[str, str]:
    """
    Get Spotify credentials from specified source.

    Args:
        source: "env" for .env file or "keyring" for OS keychain

    Returns:
        Tuple of (client_id, client_secret)
    """
    if source.lower() == "env":
        return get_credentials_from_env()
    elif source.lower() == "keyring":
        return get_credentials_from_keyring()
    else:
        raise ValueError(f"Unknown credential source: {source}. Use 'env' or 'keyring'")


# Spotify Playlist Builder Class
class SpotifyPlaylistBuilder:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "https://127.0.0.1:8888/callback",
    ) -> None:
        """Initialize Spotify API client with OAuth authentication."""
        scope = (
            "playlist-modify-public"
            "playlist-modify-private "
            "playlist-read-private "
            "playlist-read-collaborative"
        )
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


def get_builder(source: CredentialSource) -> SpotifyPlaylistBuilder:
    """Helper to initialize SpotifyPlaylistBuilder with credentials."""
    print(f"Fetching credentials from {source.value}...")

    client_id, client_secret = get_credentials(source.value)
    return SpotifyPlaylistBuilder(client_id, client_secret)


@app.command()
def build(
    json_file: Annotated[Path, typer.Argument(exists=True, help="Path to playlist JSON file")],
    source: Annotated[
        CredentialSource, typer.Option(help="Credential source")
    ] = CredentialSource.env,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Verify tracks without creating playlist")
    ] = False,
) -> None:
    """Build or update a Spotify playlist from a JSON file."""
    try:
        builder = get_builder(source)
        builder.build_playlist_from_json(str(json_file), dry_run=dry_run)
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def export(
    playlist_name: Annotated[str, typer.Argument(help="Name of the Spotify playlist to export")],
    output_file: Annotated[Path, typer.Argument(help="Path to save the JSON file")],
    source: Annotated[
        CredentialSource, typer.Option(help="Credential source")
    ] = CredentialSource.env,
) -> None:
    """Export an existing Spotify playlist to a JSON file."""
    try:
        builder = get_builder(source)
        builder.export_playlist_to_json(playlist_name, str(output_file))
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def backup(
    output_dir: Annotated[Path, typer.Argument(help="Directory to save backup files")] = Path(
        "backups"
    ),
    source: Annotated[
        CredentialSource, typer.Option(help="Credential source")
    ] = CredentialSource.env,
) -> None:
    """Backup all user playlists to JSON files."""
    try:
        builder = get_builder(source)
        builder.backup_all_playlists(str(output_dir))
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command("store-credentials")
def store_credentials_cmd() -> None:
    """Store Spotify credentials in macOS Keychain."""
    print("Store Spotify credentials in macOS Keychain")
    client_id = typer.prompt("Enter Spotify Client ID")
    client_secret = typer.prompt("Enter Spotify Client Secret", hide_input=True)

    if client_id and client_secret:
        try:
            store_credentials_in_keyring(client_id, client_secret)
            print("\nCredentials stored! You can now use: --source keyring")
        except Exception as e:
            print(f"Error storing credentials: {e}")
            raise typer.Exit(code=1)
    else:
        print("Error: Both Client ID and Client Secret are required")
        raise typer.Exit(code=1)


@app.command("install-zsh-completion")
def install_zsh_completion() -> None:
    """Install Zsh completion for Oh My Zsh users."""
    omz_dir = Path.home() / ".oh-my-zsh"

    if not omz_dir.exists():
        print(f"Error: Oh My Zsh directory not found at {omz_dir}")
        print("This command is intended for Oh My Zsh users.")
        raise typer.Exit(code=1)

    completions_dir = omz_dir / "completions"
    completions_dir.mkdir(parents=True, exist_ok=True)

    target_file = completions_dir / "_spotify-playlist-builder"

    print("Generating Zsh completion script...")

    # Get absolute path to this script
    script_path = os.path.abspath(__file__)

    # Run the command with --show-completion zsh to get the script
    # We use sys.executable to run the current script with the flag
    result = subprocess.run(
        [sys.executable, script_path, "--show-completion", "zsh"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Error generating completion script:")
        print(result.stderr)
        raise typer.Exit(code=1)

    completion_script = result.stdout

    if not completion_script.strip():
        print("Error: Generated completion script is empty.")
        raise typer.Exit(code=1)

    with open(target_file, "w") as f:
        f.write(completion_script)

    print(f"✓ Completion script installed to: {target_file}")
    print("\nTo activate changes:")
    print("1. Run: rm -f ~/.zcompdump; compinit")
    print("2. Restart your shell")


@app.command("uninstall-completion")
def uninstall_completion_cmd() -> None:
    """Show instructions to uninstall shell completion."""
    print("To uninstall shell completion, identify which method you used:")
    print("\nMethod 1: Automatic Installation (e.g. --install-completion)")
    print("  1. Open your shell config (e.g., ~/.zshrc, ~/.bashrc).")
    print("  2. Find the block starting with '# shell completion for spotify-playlist-builder'.")
    print("  3. Delete that entire block.")
    print("\nMethod 2: Manual Oh-My-Zsh Installation")
    print("  1. Remove the completion file:")
    print("     rm ~/.oh-my-zsh/completions/_spotify-playlist-builder")
    print("  2. Clear the completion cache:")
    print("     rm ~/.zcompdump*")
    print("\nAfter either method, restart your terminal.")


if __name__ == "__main__":
    app()
