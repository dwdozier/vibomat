# Contributing to Spotify Playlist Builder

Thank you for your interest in contributing! Here is a guide to help you get started.

## Development Setup

1. **Prerequisites:**
    - Python 3.11+
    - `uv` package manager

2. **Installation:**

    ```bash
    # Create virtual environment
    uv venv
    source .venv/bin/activate

    # Install dependencies
    uv pip install -e .[dev]

    # Install pre-commit hooks
    pre-commit install
    ```

## Development Workflow

### Running Tests

We use `pytest` for testing.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=spotify_playlist_builder tests/
```

### Static Analysis & Formatting

We use `ruff` for linting, `black` for formatting, and `ty` for type checking.

## Coding Standards

- **Line Length:** 100 characters.
- **Type Hinting:** Required for all function signatures.
- **Docstrings:** Required for all public functions and classes.
- **New Features:** Must include unit tests.
