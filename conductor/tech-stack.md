# Technology Stack

## Core Architecture

- **Modular Structure:** The application is organized as a Python package `spotify_playlist_builder`.
  - `client.py`: Contains `SpotifyPlaylistBuilder` for API interaction.
  - `cli.py`: Defines the Typer application and commands.
  - `auth.py`: Handles credential auto-discovery and storage.
  - `metadata.py`: Handles external metadata verification (MusicBrainz).
- **Credential Management:** Supports `.env` and system keychain, with auto-discovery logic
  in `auth.py`.
- **Configuration:** Project dependencies and tool settings are defined in `pyproject.toml`.

## Backend

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (Async) with Pydantic for validation
- **Migrations:** Alembic
- **Task Queue:** TaskIQ with Redis
- **Auth:** FastAPI-Users with SQLAlchemy backend

## Frontend

- **Language:** TypeScript
- **Library:** React 19+
- **Routing:** TanStack Router
- **Data Fetching:** TanStack Query
- **Tables:** TanStack Table
- **Styling:** Tailwind CSS (v4)
- **Build Tool:** Vite

## Infrastructure

- **Databases:** PostgreSQL (Production), SQLite (Development)
- **Cache/Broker:** Redis
- **Containerization:** Docker & Docker Compose

## Quality & Tooling

- **Python Linting/Formatting:** Ruff, Black
- **Frontend Linting:** ESLint
- **Backend Testing:** Pytest, Pytest-Asyncio, Pytest-Cov
- **Frontend Testing:** Vitest, Testing Library
- **E2E Testing:** Playwright
- **Pre-commit Hooks:** Automated linting and type checking (Ty)

## Coding Standards

- **Line Length:** 100 characters (Strictly enforced).
- **Type Hinting:** Required for all function signatures (Python 3.11+ syntax).
- **Docstrings:** Required for all functions and classes.
- **Formatter:** Black.
- **Linter:** Ruff.
- **Testing:** Unit tests required for new features. Maintain high coverage.
- **Clean Code & Idiomatic Solutions:** ALWAYS prioritize "Pythonic," clean, and maintainable
  solutions over fragile workarounds, "hacks," or monkeypatching. If a library has a bug, seek a
  declarative or structural fix within the project's code first. Do not sacrifice code quality for
  speed; aim for standard solutions that are easy to reason about.
- **Type Checker:** Ty (via pre-commit).
- **Pre-Commit Hooks:** Use `uv run <tool>` (e.g., `uv run ty`) in `.pre-commit-config.yaml` to
  ensure the correct project environment is used regardless of the user's shell state.
- **Documentation Linting:** Proactively verify `markdownlint` conformance (especially the
  100-character line length limit) before every commit to ensure CI efficiency.

## Implementation Patterns

- **Admin Dashboard:** Favor native React/TanStack components over external libraries like
  `sqladmin` to maintain a consistent tech stack and avoid legacy dependencies.
- **E2E Sanity:** All PRs must pass the `e2e-sanity` playwright check, verifying core navigation
  and site availability.
- **Async DB Sessions:** Always use `async with request.state.session` or similar context
  managers within admin/app routes to ensure proper connection pooling.
