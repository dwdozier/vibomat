# Vibomat

An intelligent, full-stack application to generate and manage music playlists using Generative AI
and external metadata verification.

## Core Features

- **AI Generation**: Describe a mood or theme (e.g., "Deep space ambient") and get a curated list.
- **Multi-Provider Verification**: Cross-references AI results with MusicBrainz and Discogs to
    eliminate hallucinations.
- **Service Sync**: Automatically creates and updates playlists on Spotify (with extensibility for
    other providers).
- **Modern Architecture**: FastAPI Backend + TanStack/React Frontend.
- **Robust Background Processing**: Uses TaskIQ and Redis for reliable playlist building.

## Tech Stack

- **Frontend**: React, TanStack Router, TanStack Query, Tailwind CSS, Lucide.
- **Backend**: FastAPI, SQLAlchemy (Async), Pydantic, Google Gemini SDK.
- **Infrastructure**: Docker, Redis, PostgreSQL (Production) / SQLite (Dev).
- **Quality**: 95% test coverage enforced via CI/CD.

## Quick Start

### 1. Register Spotify App

Get your credentials at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

### 2. Configure & Install

Follow the [SETUP.md](SETUP.md) for detailed platform-specific installation.

### 3. Run with Docker

The Docker setup is pre-configured for development with hot-reloading enabled.

```bash
docker-compose up --build
```

- Open [http://localhost:80](http://localhost:80) to start building.
- Changes to your local code will automatically reflect in the running containers.
- To stop the stack: `docker-compose down`.

## Development & Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for standards and testing guidelines.

## License

MIT
