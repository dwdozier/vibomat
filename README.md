# Spotify Playlist Builder

A simple Python CLI tool to programmatically create Spotify playlists from JSON data files.

## What It Does

Feed it a JSON file with artist/track pairs, and it:

- Searches Spotify for each track
- Creates a new public playlist on your account
- Adds all found tracks in order
- Reports any tracks that couldn't be found

Perfect for curating playlists programmatically and versioning them in git.

## Prerequisites

- Python 3.11+
- A Spotify account
- Spotify Developer credentials (free to create)
- `uv` package manager: https://docs.astral.sh/uv/getting-started/
- Optional: 1Password account for credential management

## Setup

### 1. Register a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in (create a free account if needed)
3. Click "Create an App" and agree to the terms
4. You'll get a **Client ID** and **Client Secret**

### 2. Set Up Virtual Environment and Dependencies

```bash
# Create project and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

This reads from `pyproject.toml` and creates an isolated environment.

### 3. Choose Credential Storage Method

You can store credentials in `.env`, your system's secure keychain, or 1Password. Pick one:

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
python spotify_playlist_builder.py --store-credentials
```
You will be prompted to enter your Client ID and Secret.

This is more secure than a `.env` file as credentials are encrypted and managed by your OS.

#### Option C: Use 1Password (Recommended)

**Install and authenticate 1Password CLI:**

1. Install from: https://developer.1password.com/docs/cli/get-started
2. Authenticate in your terminal:

   ```bash
   op account add
   ```

**Create a Spotify item in your Personal vault:**

1. Open 1Password app
2. Go to your **Personal** vault
3. Click **+** to create a new item
4. Select **Password** as the type
5. Set **Title** to `Spotify`
6. Click **Edit** and add two custom fields:
   - Field name: `client_id` → Value: (your Spotify Client ID)
   - Field name: `client_secret` → Value: (your Spotify Client Secret)
7. Click **Save**

**Verify it works:**

```bash
op read "op://Personal/Spotify/client_id"
```

Should output your Client ID.

## Usage

### Create a Playlist JSON File

Create a file in `playlists/` like `my-playlist.json`:

```json
{
  "name": "My Awesome Playlist",
  "description": "A curated collection of tracks",
  "tracks": [
    {"artist": "Artist Name", "track": "Song Title"},
    {"artist": "Another Artist", "track": "Another Song"},
    {"artist": "Kraftwerk", "track": "The Robots"}
  ]
}
```

### Run the Script

**Using .env (default):**
```bash
python spotify_playlist_builder.py playlists/my-playlist.json
```

**Using System Keychain:**
```bash
python spotify_playlist_builder.py playlists/my-playlist.json --source keyring
```

**Using 1Password:**
```bash
python spotify_playlist_builder.py playlists/my-playlist.json --source 1password
```

**With custom 1Password vault/item (if different from defaults):**
```bash
python spotify_playlist_builder.py playlists/my-playlist.json --source 1password --vault "MyVault" --item "MySpotifyItem"
```

### What Happens

The script will:
1. Fetch credentials from your chosen source
2. Create a new public playlist on your Spotify account
3. Search for each track and add it if found
4. Report any missing tracks
5. Output a link to your new playlist

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
- **Reuse the JSON**: You can run the same JSON multiple times to create duplicate playlists, or modify it and create variations
- **Version Control**: Keep your playlist JSON files in git to track curation changes over time
- **Credential Security**: 1Password and the system keychain are more secure than .env—credentials stay encrypted and never committed to git
- **Team Sharing**: If sharing with your team, have each person use their own credential store locally

## Example

See `playlists/depeche-mode.json` for a complete example with ~36 tracks.

```bash
python spotify_playlist_builder.py playlists/depeche-mode.json
```

## License

MIT
