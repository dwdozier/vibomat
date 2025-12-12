import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import sys
import os
import subprocess
from pathlib import Path


# Credential Management Functions
def get_credentials_from_env():
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


def get_credentials_from_1password(vault="Personal", item="Spotify", id_field="client_id", secret_field="client_secret"):
    """Get credentials from 1Password vault."""
    try:
        cmd_id = f'op read "op://{vault}/{item}/{id_field}"'
        cmd_secret = f'op read "op://{vault}/{item}/{secret_field}"'

        result_id = subprocess.run(cmd_id, shell=True, capture_output=True, text=True, check=False)
        result_secret = subprocess.run(cmd_secret, shell=True, capture_output=True, text=True, check=False)

        if result_id.returncode != 0 or result_secret.returncode != 0:
            raise Exception(
                f"Failed to fetch from 1Password.\n"
                f"Make sure:\n"
                f"  1. 1Password CLI is installed: https://developer.1password.com/docs/cli/get-started\n"
                f"  2. You've authenticated: op account add\n"
                f"  3. You have an item named '{item}' in vault '{vault}'\n"
                f"  4. Fields '{id_field}' and '{secret_field}' exist on that item"
            )

        client_id = result_id.stdout.strip()
        client_secret = result_secret.stdout.strip()

        return client_id, client_secret

    except FileNotFoundError:
        raise Exception(
            "1Password CLI not found. Install it at:\n"
            "https://developer.1password.com/docs/cli/get-started"
        )


def get_credentials(source="env", vault="Personal", item="Spotify"):
    """
    Get Spotify credentials from specified source.

    Args:
        source: "env" for .env file or "1password" for 1Password vault
        vault: 1Password vault name (default: Personal)
        item: 1Password item name (default: Spotify)

    Returns:
        Tuple of (client_id, client_secret)
    """
    if source.lower() == "env":
        return get_credentials_from_env()
    elif source.lower() == "1password":
        return get_credentials_from_1password(vault, item)
    else:
        raise ValueError(f"Unknown credential source: {source}. Use 'env' or '1password'")


# Spotify Playlist Builder Class
class SpotifyPlaylistBuilder:
    def __init__(self, client_id, client_secret):
        """Initialize Spotify API client."""
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )

    def search_track(self, artist, track):
        """Search for a track on Spotify, return URI if found."""
        query = f"track:{track} artist:{artist}"
        results = self.sp.search(q=query, type="track", limit=1)

        if results["tracks"]["items"]:
            return results["tracks"]["items"][0]["uri"]
        return None

    def create_playlist(self, username, playlist_name, description=""):
        """Create a new playlist."""
        playlist = self.sp.user_playlist_create(
            user=username,
            name=playlist_name,
            public=True,
            description=description
        )
        return playlist["id"]

    def add_tracks_to_playlist(self, playlist_id, tracks):
        """Add tracks to a playlist, handling batch operations."""
        uris = []
        failed_tracks = []

        for i, track in enumerate(tracks):
            artist = track.get("artist")
            track_name = track.get("track")
            uri = self.search_track(artist, track_name)

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

    def build_playlist_from_json(self, json_file, username):
        """Build a playlist from a JSON file."""
        with open(json_file, "r") as f:
            playlist_data = json.load(f)

        playlist_name = playlist_data.get("name", "New Playlist")
        description = playlist_data.get("description", "")
        tracks = playlist_data.get("tracks", [])

        print(f"Creating playlist: {playlist_name}")
        playlist_id = self.create_playlist(username, playlist_name, description)
        print(f"Playlist created (ID: {playlist_id})")

        print(f"Adding {len(tracks)} tracks...")
        failed = self.add_tracks_to_playlist(playlist_id, tracks)

        if failed:
            print(f"\n⚠️  {len(failed)} tracks not found:")
            for track in failed:
                print(f"  - {track}")
        else:
            print(f"✓ All tracks added successfully!")

        print(f"\nPlaylist ready: https://open.spotify.com/playlist/{playlist_id}")


# Main Execution
def main():
    if len(sys.argv) < 2:
        print("Usage: python spotify_playlist.py <json_file> <spotify_username> [--source env|1password]")
        print("\nExamples:")
        print("  python spotify_playlist.py playlist.json dave")
        print("  python spotify_playlist.py playlist.json dave --source env")
        print("  python spotify_playlist.py playlist.json dave --source 1password")
        sys.exit(1)

    json_file = sys.argv[1]
    username = sys.argv[2]

    # Parse optional source argument
    source = "env"  # Default to .env
    if "--source" in sys.argv:
        source_idx = sys.argv.index("--source")
        if source_idx + 1 < len(sys.argv):
            source = sys.argv[source_idx + 1]

    # Validate inputs
    if not Path(json_file).exists():
        print(f"Error: {json_file} not found")
        sys.exit(1)

    try:
        # Get credentials from specified source
        print(f"Fetching credentials from {source}...")
        client_id, client_secret = get_credentials(source)

        # Build playlist
        builder = SpotifyPlaylistBuilder(client_id, client_secret)
        builder.build_playlist_from_json(json_file, username)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
