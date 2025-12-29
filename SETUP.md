# Setup and Installation

This guide provides comprehensive instructions for setting up Vibomat on macOS, Linux,
and Windows.

## Prerequisites

- **Python 3.12+**
- **Node.js 20+ & npm**
- **Docker & Docker Compose** (Recommended for easiest setup)
- **Redis** (Required if not using Docker)
- **uv package manager**: [Installation](https://docs.astral.sh/uv/getting-started/)

---

## 1. Spotify API Registration

To interact with Spotify, you must register an application:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Click **"Create app"**.
3. **Redirect URIs** (Crucial): Add both:
    - `https://127.0.0.1:8888/callback` (for CLI)
    - `http://localhost:8000/api/v1/integrations/spotify/callback` (for Web API)
4. Copy your **Client ID** and **Client Secret**.

---

## 2. Local Installation

1. **Clone & Environment**:

    ```bash
    git clone https://github.com/dwdozier/spotify-playlist-builder.git
    cd spotify-playlist-builder
    uv venv
    source .venv/bin/activate # Linux/Mac
    # .venv\Scripts\activate # Windows
    ```

2. **Install Dependencies**:

    ```bash
    uv pip install -e .[dev]
    cd frontend && npm install && cd ..
    ```

3. **Environment Configuration**:
    Create a `.env` file in the root:

    ```env
    SPOTIFY_CLIENT_ID=your_id
    SPOTIFY_CLIENT_SECRET=your_secret
    SPOTIFY_REDIRECT_URI=http://localhost:8000/api/v1/integrations/spotify/callback
    FASTAPI_SECRET=random_secure_string
    GEMINI_API_KEY=your_google_ai_key # Optional
    ```

---

## 3. Platform Specifics

### macOS

- **Redis**: `brew install redis && brew services start redis`
- **Docker**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### Linux (Ubuntu/Debian)

- **Redis**: `sudo apt install redis-server`
- **Docker**: Follow official [Docker Engine](https://docs.docker.com/engine/install/ubuntu/)
  instructions.

### Windows

- **Recommendation**: Use **WSL2** (Windows Subsystem for Linux).
- **WSL Setup**: Install Ubuntu from the MS Store, then follow the Linux instructions.
- **Native**: If using native Windows, ensure `Redis` is running (via Memurai or WSL) and use
  PowerShell for commands.

---

## 4. Running the Application

### Option A: Docker Compose (Recommended)

This starts the Database, Redis, Backend, Worker, and Frontend in one command.

**Development Mode (Default):**
The default configuration is now optimized for local development. It enables hot-reloading for
both the backend (FastAPI) and frontend (Vite), and mounts your local code into the containers.

```bash
docker-compose up --build
```

- **API:** `http://localhost:8000` (Updates automatically on code changes)
- **Web UI:** `http://localhost:80` (Updates automatically on code changes)

**Tearing Down:**
To stop and remove all containers, networks, and volumes:

```bash
docker-compose down
```

### Option B: Manual (Development)

You will need 4 terminal tabs:

1. **Backend**: `uv run uvicorn backend.app.main:app --reload`
2. **Worker**: `PYTHONPATH=. uv run taskiq worker backend.app.core.tasks:broker`
3. **Frontend**: `cd frontend && npm run dev`
4. **Redis**: `redis-server` (if not running as service)

---

## 5. Verification

Run the test suite to ensure everything is configured correctly:

```bash
# Backend
PYTHONPATH=. pytest backend/tests/

# Frontend
cd frontend && npm test
```

### CLI Tool Usage

```bash
vibomat build playlists/your-file.json
```

---

## Optional Setup

### Pre-commit Hooks

```bash
pre-commit install
```

### Shell Completion (CLI)

```bash
vibomat install-zsh-completion
```
