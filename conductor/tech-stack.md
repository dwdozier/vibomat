# Technology Stack

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

## Quality & Tooling

- **Python Linting/Formatting:** Ruff, Black
- **Frontend Linting:** ESLint
- **Backend Testing:** Pytest, Pytest-Asyncio, Pytest-Cov
- **Frontend Testing:** Vitest, Testing Library
- **E2E Testing:** Playwright
- **Pre-commit Hooks:** Automated linting and type checking (Ty)
