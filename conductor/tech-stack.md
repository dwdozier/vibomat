# Technology Stack

## Core Architecture

- **Modular Structure:** The application is organized as a Python package `spotify_playlist_builder`.
  - `client.py`: Contains `SpotifyPlaylistBuilder` for API interaction.
  - `cli.py`: Defines the Typer application and commands.
  - `auth.py`: Handles credential auto-discovery and storage.
  - `metadata.py`: Handles external metadata verification (MusicBrainz).
- **Credential Management:** Supports `.env` files with auto-discovery logic in `auth.py`.
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
  - **Extensions:** `pgvector` (Vector similarity search), `pg_trgm` (Fuzzy string matching)
- **Cache/Broker:** Redis
- **Containerization:** Docker & Docker Compose

## Testing Stack

- **Backend (Unit/Integration):** **Pytest** with `pytest-asyncio` for asynchronous testing and
  `pytest-cov` for coverage reporting.
- **Frontend (Unit/Component):** **Vitest** with `React Testing Library` for logic and component
  verification.
- **End-to-End (E2E):** **Playwright** (Python-based via `pytest-playwright`) for Critical User
  Journeys (CUJs).
- **Sanity Checks:** A specialized `e2e-sanity` check (Playwright) must pass for every PR to
  ensure core site availability.

## Quality & Tooling

- **Philosophy:** Treat linters and formatters as **verification tools**, not just fixers. Aim to
  write compliant code (correct line lengths, types, formatting) from the start.
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

## Troubleshooting

- **Vite 504 (Outdated Optimize Dep):** A '504 (Outdated Optimize Dep)' error in the browser
  usually indicates a stale cache in the `node_modules/.vite` directory. Resolve by restarting the
  dev server or clearing the `.vite` directory.
- **SQLAlchemy Duplicate Rows:** When using joined eager loads on collections, always call
  `.unique()` on the execution result to avoid `InvalidRequestError` caused by duplicate parent
  rows.

- **Admin Dashboard:** Favor native React/TanStack components over external libraries like
  `sqladmin` to maintain a consistent tech stack and avoid legacy dependencies.
- **E2E Sanity:** All PRs must pass the `e2e-sanity` playwright check, verifying core navigation
  and site availability.
- **Async DB Sessions:** Always use `async with request.state.session` or similar context
  managers within admin/app routes to ensure proper connection pooling.
