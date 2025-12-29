# Setup and Installation

This guide covers the prerequisites, installation, and configuration required to run the
Playlist Builder (CLI and Web API).

## Prerequisites

- **Python 3.11+**
- **uv package manager**: [Installation Instructions](https://docs.astral.sh/uv/getting-started/)
- **Spotify Developer Credentials**: Follow the [App Registration Guide](APP_REGISTRATION.md) to
  get your Client ID and Client Secret.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/dwdozier/spotify-playlist-builder.git
    cd spotify-playlist-builder
    ```

2. **Create and activate the virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate  # macOS/Linux
    ```

3. **Install dependencies:**

    ```bash
    uv pip install -e .[dev]
    ```

## Configuration

### 1. Environment Variables (.env)

Create a `.env` file in the project root:

```env
# Spotify Credentials
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here

# Web API Configuration
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/v1/integrations/spotify/callback
FASTAPI_SECRET=your_random_secret_here

# AI Features (Optional)
GEMINI_API_KEY=your_gemini_key_here

# Database (Optional, defaults to local sqlite)
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
```

### 2. Database Migrations

Initialize the database using Alembic:

```bash
PYTHONPATH=. alembic upgrade head
```

## Running the App

### Web API

```bash
uv run uvicorn backend.app.main:app --reload
```

### CLI Tool

```bash
spotify-playlist-builder build playlists/your-file.json
```

## Optional Setup

### Pre-commit Hooks

```bash
pre-commit install
```

### Shell Completion (CLI)

```bash
spotify-playlist-builder install-zsh-completion
```
