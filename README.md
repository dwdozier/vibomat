# Playlist Builder

A tool to programmatically create and manage playlists from local JSON data files, now
evolving into a full-stack web application.

## What It Does

Feed it a JSON file with artist/track pairs, or use the web interface to:

- **Generate** playlists using AI (Gemini) based on mood or style.
- **Verify** tracks against external metadata (MusicBrainz/Discogs).
- **Search** Spotify for each track (with intelligent fuzzy matching).
- **Create/Update** playlists on your account automatically.

## Getting Started

1. **Register a Spotify App**: Get your API credentials by following the
   [App Registration Guide](APP_REGISTRATION.md).
2. **Setup AI (Optional)**: To use AI features, follow the [AI Setup Guide](AI_SETUP.md).
3. **Install & Configure**: Follow the [Setup Guide](SETUP.md) to install dependencies and
   configure your database and credentials.

## Usage

### 1. Web API (FastAPI)

Start the backend server:

```bash
uv run uvicorn backend.app.main:app --reload
```

Access the interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. CLI Tool

The CLI remains functional for direct core access.

```bash
spotify-playlist-builder build playlists/my-playlist.json
```

## File Structure

```sh
spotify-playlist-builder/
├── backend/
│   ├── app/                 # FastAPI application
│   │   ├── api/             # API Endpoints
│   │   ├── core/auth/       # Identity & Authentication
│   │   ├── db/              # Database & Migrations
│   │   ├── models/          # SQLAlchemy Models
│   │   └── services/        # Business Logic Services
│   ├── core/                # Shared Core Logic (former spotify_playlist_builder)
│   └── tests/               # Backend Test Suite
├── frontend/                # (Under Development) Web UI
├── planning/                # Project Roadmap & Phased Plans
├── pyproject.toml           # Project config & dependencies
└── playlists/               # Local JSON playlist files
```

## License

MIT
