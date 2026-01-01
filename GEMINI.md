# GEMINI.md - AI Assistant Guide

This guide provides context and instructions for AI assistants to effectively contribute to this
project.

## 1. Project Summary

Vibomat is a universal music platform to generate and manage playlists using Generative AI and
external metadata verification. It supports multiple streaming services and uses a FastAPI backend
with a TanStack/React frontend.

## 2. Development Environment

Use the following commands to set up the development environment.

1. **Create and activate the virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate
    ```

2. **Install dependencies in editable mode:**

    ```bash
    uv pip install -e .[dev]
    ```

## 3. Core Architecture

- **Modular Structure:** The application is organized as a Python package `spotify_playlist_builder`.
  - **`client.py`:** Contains `SpotifyPlaylistBuilder` for API interaction.
  - **`cli.py`:** Defines the Typer application and commands.
  - **`auth.py`:** Handles credential auto-discovery and storage.
  - **`metadata.py`:** Handles external metadata verification (MusicBrainz).
- **Credential Management:** Supports `.env` and system keychain, with auto-discovery logic
  in `auth.py`.
- **Configuration:** Project dependencies and tool settings are defined in `pyproject.toml`.

## 4. Key Commands

Use these commands to maintain code quality and run the application.

- **Run the application:**

    ```bash
    vibomat build playlists/your-playlist.json --source [env|keyring]
    ```

- **Format code:**

    ```bash
    black .
    ```

- **Lint code:**

    ```bash
    ruff check .
    ```

- **Run tests with coverage:**

    ```bash
    pytest --cov=spotify_playlist_builder tests/
    ```

- **Run pre-commit manually:**

    ```bash
    pre-commit run --all-files
    ```

## 5. Coding Standards

- **Line Length:** 100 characters (Strictly enforced).
- **Type Hinting:** Required for all function signatures (Python 3.11+ syntax).
- **Docstrings:** Required for all functions and classes.
- **Formatter:** Black.
- **Linter:** Ruff.
- **Testing:** Unit tests required for new features. Maintain high coverage.
- **Clean Code & Idiomatic Solutions:** ALWAYS prioritize "Pythonic," clean, and maintainable
  solutions over fragile workarounds, "hacks," or monkeypatching. If a library has a bug, seek a
  declarative or structural fix within the project's code first. Do not sacrifice code quality for
  speed; aim for standard solutions that are easy to reason about, even if they require multiple
  iterations to perfect.
- **Type Checker:** Ty (via pre-commit).
- **Pre-Commit Hooks:** Use `uv run <tool>` (e.g., `uv run ty`) in `.pre-commit-config.yaml` to
  ensure the correct project environment is used regardless of the user's shell state.
- **Documentation Linting:** Proactively verify `markdownlint` conformance (especially the
  100-character line length limit) before every commit to ensure CI efficiency.

## 6. Architecture & Implementation Patterns

- **Admin Dashboard:** Favor native React/TanStack components over external libraries like
  `sqladmin` to maintain a consistent tech stack and avoid legacy dependencies (jQuery, etc.).
- **Vib-O-Mat Terminology:**
  - **Citizens:** Users
  - **Archives:** Playlists
  - **Relays:** Service Connections
  - **Nodes:** OAuth Identity Links
- **E2E Sanity:** All PRs must pass the `e2e-sanity` playwright check, verifying core navigation
  and site availability.
- **Async DB Sessions:** Always use `async with request.state.session` or similar context
  managers within admin/app routes to ensure proper connection pooling.

## 7. Critical Rules

- **CRITICAL RULE:** Never use write_file on an existing file unless specifically told to
  "overwrite" or "replace" it. Always read_file first to perform a merge, or use
  run_shell_command with cat >> for appending. If a file is over 50 lines, always prefer
  incremental edits.
- **CRITICAL RULE:** Force pushing is strictly forbidden as it rewrites history and can disrupt
  collaboration. It should only be used as a last resort and REQUIRES explicit user approval.
  Prefer accumulating multiple commits within an open PR, as they will be squash-merged upon
  completion.
- **CRITICAL RULE: No Rule Bypassing:** Never bypass security rules, branch protections, or
  verification failures (linting, testing, etc.) without explicit user approval. Always employ the
  Pull Request workflow unless specifically directed to push to `main`.
- **CRITICAL RULE: Branching Strategy:** Feature branches must always branch off the latest `main`
  branch.
  - **No Chaining:** Never create a feature branch from another unmerged feature branch. This
      prevents complex "chained" dependencies that clutter history and complicate reviews.
  - **Related Changes:** If a request involves bug fixes or refinements to an existing open PR,
      apply those changes directly to that PR's branch.
  - **Unrelated Changes:** For new, unrelated features or tasks, always return to `main`, pull the
      latest changes, and create a new branch. If the new work depends on an unmerged PR, inform the
      user and wait for the merge or seek explicit approval to branch off the feature.

## 7. Documentation Automation

A **Documentation Agent** (CI/CD service) automatically monitors code changes and updates
project documentation.

- **Workflow:**
  - Detects changes in code, configuration, or specifications.
  - Runs `agent_docs.py` using Gemini.
  - Updates **`README.md`**, **`CONTRIBUTING.md`**, and **`SETUP.md`** to keep them synchronized.
  - Generates/Updates usage guides in `docs/guides/`.
  - Generates a PR for human review.
- **Style Guide:**
  - Adheres to **Google Developer Documentation Style**.
  - **Voice:** Active, present tense.
  - **Tone:** Professional, objective, helpful (no "please" or "simply").
  - **Format:** Sentence case headings, clear procedures.
- **Developer Responsibility:**
  - Review auto-generated documentation PRs for technical accuracy and style compliance.
  - Merge documentation PRs promptly to keep guides in sync with code.
