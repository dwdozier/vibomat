# Contributing to Vibomat

We welcome contributions! As a full-stack project, we maintain high standards for type safety,
testing, and clean architecture.

## 1. Development Principles

- **Type Safety**: We use Pydantic for Backend schemas and TanStack Router/Query for Frontend types.
- **Decoupling**: Identity is decoupled from service providers (Spotify).
- **Quality**: We maintain **95% minimum test coverage** for all new logic.
- **TanStack Patterns**: Prefer `loader` functions for data fetching on route entry. Avoid
  `useEffect` for state synchronization where TanStack Query or Router hooks can be used.
- **E2E Stability**: Use `data-play` attributes for all critical UI elements to ensure
  Playwright tests are decoupled from CSS or text changes.
- **Clean Code & Idiomatic Solutions:** ALWAYS prioritize "Pythonic," clean, and maintainable
  solutions over fragile workarounds, "hacks," or monkeypatching. If a library has a bug, seek a
  declarative or structural fix within the project's code first. Do not sacrifice code quality for
  speed; aim for standard solutions that are easy to reason about, even if they require multiple
  iterations to perfect.

## 2. Setting Up for Development

Follow the [SETUP.md](SETUP.md) guide to get your environment running.

## 3. Workflow

1. **Branching**: Always branch off `main`.
2. **Naming**: Use `feat/`, `fix/`, `docs/`, or `test/` prefixes.
3. **No Chaining**: Do not branch off unmerged feature branches.

## 4. Testing Requirements

### Backend (Python)

We use `pytest`. All logic in `backend/core` and `backend/app` must be tested.

```bash
PYTHONPATH=. uv run pytest --cov=backend/core --cov=backend/app --cov-fail-under=95 backend/tests/
```

### Frontend (TypeScript)

We use `Vitest` and `React Testing Library`.

```bash
cd frontend && npm test
```

### Pre-Commit Hooks

MANDATORY. Install before committing. All hooks are configured to run via `uv run` to ensure
environment stability:

```bash
pre-commit install
pre-commit run --all-files
```

**Note:** Proactively wrap your documentation text to 100 characters to prevent `markdownlint`
failures during the commit process.

## 5. Pull Requests

- Provide a clear description of the change.
- Ensure all CI checks pass (Linting, Coverage, Tests).
- Requests will be squashed and merged once approved.
