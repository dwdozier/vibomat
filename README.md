# Spotify Playlist Builder

A simple Python CLI tool to programmatically create Spotify playlists from JSON data files.

## What It Does

Feed it a JSON file with artist/track pairs, and it:

- Searches Spotify for each track
- Creates a new playlist on your account
- Adds all found tracks in order
- Reports any tracks that couldn't be found

Perfect for curating playlists programmatically and versioning them in git.

## Prerequisites

- Python 3.11+
- A Spotify account
- Spotify Developer credentials (free to create)
- `uv` package manager: https://docs.astral.sh/uv/getting-started/

## Setup

### 1. Register a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in (create a free account if needed)
3. Click "Create an App" and agree to the terms
4. You'll get a **Client ID** and **Client Secret**

### 2. Set Up Virtual Environment and Dependencies

```bash
# Create the virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies in editable mode
uv pip install -e .[dev]
```

This installs the project in "editable" mode along with all development dependencies from `pyproject.toml`.

### 3. Choose Credential Storage Method

You can store credentials in `.env` or your system's secure keychain. Pick one:

#### Option A: Use .env File

Create a `.env` file in the repo root:

```sh
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

**Important:** Add `.env` to `.gitignore` so you don't commit secrets.

#### Option B: Use System Keychain (macOS, Linux, Windows)

Use a helper command to securely store your credentials in your operating system's default keychain (e.g., macOS Keychain, Windows Credential Manager).

**Store credentials:**
```bash
spotify-playlist-builder store-credentials
```
You will be prompted to enter your Client ID and Secret.

This is more secure than a `.env` file as credentials are encrypted and managed by your OS.

### 4. Set Up Pre-commit Hooks

To ensure code quality checks run automatically before every commit:

```bash
# Install git hooks
pre-commit install
```

### 5. Set Up Shell Completion (Zsh/Oh-My-Zsh)

To enable tab completion for commands and options (highly recommended):

```bash
# Run the installation command
python spotify_playlist_builder.py install-zsh-completion
```

Follow the on-screen instructions to reload your shell.

## Usage

### Create a Playlist JSON File

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
- `version` (optional): Version preference. Supported values: `studio` (default), `live`, `remix`, `compilation`.

### Build a Playlist

Create or update a playlist on Spotify from a JSON file.

**Basic usage:**
```bash
python spotify_playlist_builder.py build playlists/my-playlist.json
```

**Options:**
- `--source [env|keyring]`: Credential source (default: `env`)
- `--dry-run`: Simulate the process without making changes to Spotify.
- `--verbose`: Enable detailed logging.

**Example with options:**
```bash
python spotify_playlist_builder.py build playlists/my-playlist.json --source keyring --dry-run
```

### Export a Playlist

Export an existing Spotify playlist to a JSON file.

```bash
python spotify_playlist_builder.py export <spotify_playlist_id_or_url> --output playlists/my-exported-playlist.json
```

**Options:**
- `--source [env|keyring]`: Credential source (default: `env`)
- `--output`: Path to save the JSON file (default: `playlist_export.json`).

### Backup All Playlists

Backup all your user's playlists to JSON files in a directory.

```bash
python spotify_playlist_builder.py backup --output-dir backups/
```

**Options:**
- `--source [env|keyring]`: Credential source (default: `env`)
- `--output-dir`: Directory to save the backup files (default: `backups`).

### What Happens (Build Command)

The script will:
1. Fetch credentials from your chosen source
2. Create a new playlist (or update an existing one if the name matches)
3. Search for each track and add it if found
4. Report any missing tracks
5. Output a link to your playlist

```sh
Fetching credentials from env...
Creating playlist: My Awesome Playlist
Playlist created (ID: 7abc123...)
Adding 3 tracks...
✓ All tracks added successfully!

Playlist ready: https://open.spotify.com/playlist/7abc123...
```

## File Structure

```sh
spotify-playlist-builder/
├── spotify_playlist_builder.py # Main script
├── pyproject.toml           # Project config & dependencies
├── uv.lock                  # Locked dependencies
├── .venv/                   # Virtual environment (in .gitignore)
├── .env                     # Your Spotify credentials (in .gitignore, env only)
├── .gitignore
├── README.md               # This file
└── playlists/
    ├── depeche-mode.json   # Example playlist
    └── your-playlist.json   # Your playlists
```

## Tips

- **Spotify Username**: Find it in your profile settings (or the URL when you visit your profile)
- **Track Not Found**: If a track isn't found, check the spelling. Spotify's search is forgiving but works best with exact artist/track names
- **Update Playlists**: Running the `build` command again with the same playlist name in the JSON will **update** the existing playlist (syncing tracks and description) instead of creating a duplicate.
- **Version Control**: Keep your playlist JSON files in git to track curation changes over time
- **Credential Security**: The system keychain is more secure than .env—credentials stay encrypted and never committed to git
- **Team Sharing**: If sharing with your team, have each person use their own credential store locally

## Example

See `playlists/depeche-mode.json` for a complete example with ~36 tracks.

```bash
python spotify_playlist_builder.py build playlists/depeche-mode.json
```

## License

MIT
