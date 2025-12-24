# Spotify Playlist Builder

A simple Python CLI tool to programmatically create and manage Spotify playlists from local
JSON data files.

## What It Does

Feed it a JSON file with artist/track pairs, and it:

- **Searches** Spotify for each track (with intelligent fuzzy matching).
- **Creates** a new playlist on your account (or updates an existing one).
- **Adds** all found tracks in the correct order.
- **Reports** any tracks that couldn't be found.

Perfect for curating playlists programmatically and versioning them in git.

## Getting Started

1. **Register a Spotify App**: Get your API credentials by following the
   [App Registration Guide](APP_REGISTRATION.md).
2. **Install & Configure**: Follow the [Setup Guide](SETUP.md) to install dependencies and
   configure your credentials.

## Usage

### 1. Create a Playlist JSON File

Create a file in `playlists/` like `my-playlist.json`:

```json
{
  "name": "My Awesome Playlist",
  "description": "A curated collection of tracks",
  "public": false,
  "tracks": [
    {"artist": "Artist Name", "track": "Song Title"},
    {"artist": "Another Artist", "track": "Another Song", "album": "Specific Album"},
    {"artist": "Kraftwerk", "track": "The Robots", "version": "studio"},
    {"artist": "The Cure", "track": "Lullaby", "version": "live"}
  ]
}
```

### Supported Track Fields

- `artist` (required): Name of the artist.
- `track` (required): Name of the song.
- `album` (optional): Preferred album title.
- `version` (optional): Version preference. Supported values: `studio` (default), `live`, `remix`,
  `compilation`, `original`, `remaster`.

### 2. Build a Playlist

Create or update a playlist on Spotify from a JSON file.

**Basic usage:**

```bash
spotify-playlist-builder build playlists/my-playlist.json
```

**Options:**

- `--source [env|keyring]`: Credential source (default: `env`)
- `--dry-run`: Simulate the process without making changes to Spotify.
- `--verbose`: Enable detailed logging.

**Example with options:**

```bash
spotify-playlist-builder build playlists/my-playlist.json --source keyring --dry-run
```

### 3. Export a Playlist

Export an existing Spotify playlist to a JSON file for backup or editing.

```bash
spotify-playlist-builder export <spotify_playlist_id_or_url> --output playlists/my-exported-playlist.json
```

### 4. Backup All Playlists

Backup all your user's playlists to JSON files in a directory.

```bash
spotify-playlist-builder backup --output-dir backups/
```

## Tips

- **Spotify Username**: Find it in your profile settings (or the URL when you visit your profile)
- **Track Not Found**: If a track isn't found, check the spelling. Spotify's search is forgiving
  but works best with exact artist/track names
- **Update Playlists**: Running the `build` command again with the same playlist name in the JSON
  will **update** the existing playlist (syncing tracks and description) instead of creating
  a duplicate.
- **Version Control**: Keep your playlist JSON files in git to track curation changes over time
- **Credential Security**: The system keychain is more secure than .env—credentials stay
  encrypted and never committed to git

## File Structure

```sh
spotify-playlist-builder/
├── spotify_playlist_builder/ # App package
│   ├── __init__.py
│   ├── auth.py              # Credential management
│   ├── cli.py               # Typer CLI commands
│   ├── client.py            # Core Spotify logic
│   ├── main.py              # Entry point
│   ├── metadata.py          # Metadata verification
│   └── utils/               # Shared utilities
├── pyproject.toml           # Project config & dependencies
├── uv.lock                  # Locked dependencies
├── APP_REGISTRATION.md      # Spotify App setup guide
├── SETUP.md                 # Installation & config guide
├── README.md                # This file
├── .venv/                   # Virtual environment (in .gitignore)
├── .env                     # Your Spotify credentials (in .gitignore, env only)
├── .gitignore
└── playlists/
    ├── depeche-mode.json   # Example playlist
    └── your-playlist.json   # Your playlists
```

## License

MIT
