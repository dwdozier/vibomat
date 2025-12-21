# GEMINI.md - AI Assistant Guide

This guide provides context and instructions for AI assistants to effectively contribute to this project.

## 1. Project Summary

A Python CLI tool to programmatically create and manage Spotify playlists from local JSON data files. It supports multiple methods for securely handling Spotify API credentials.

## 2. Development Environment

Use the following commands to set up the development environment.

1.  **Create and activate the virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

2.  **Install dependencies in editable mode:**
    ```bash
    uv pip install -e .[dev]
    ```

## 3. Core Architecture

-   **Main Entry Point:** The application logic is contained entirely within `spotify_playlist_builder.py`.
-   **Core Class:** The `SpotifyPlaylistBuilder` class orchestrates all interaction with the Spotify API, including authentication, track searching, and playlist manipulation.
-   **Credential Management:** The script can retrieve credentials from a `.env` file or the system's native keychain (via `keyring`). The default source is `.env`.
-   **Configuration:** Project dependencies and tool settings are defined in `pyproject.toml`.

## 4. Key Commands

Use these commands to maintain code quality and run the application.

-   **Run the application:**
    ```bash
    spotify-playlist-builder build playlists/your-playlist.json --source [env|keyring]
    ```

-   **Format code:**
    ```bash
    black .
    ```

-   **Lint code:**
    ```bash
    ruff check .
    ```

 -   **Run tests with coverage:**
    ```bash
    pytest --cov=spotify_playlist_builder tests/
    ```

 -   **Run pre-commit manually:**
    ```bash
    pre-commit run --all-files
    ```

## 5. Coding Standards

-   **Line Length:** 100 characters (Strictly enforced).
-   **Type Hinting:** Required for all function signatures (Python 3.11+ syntax).
-   **Docstrings:** Required for all functions and classes.
-   **Formatter:** Black.
-   **Linter:** Ruff.
-   **Testing:** Unit tests required for new features. Maintain high coverage.
-   **Type Checker:** Ty (via pre-commit).
-   **Pre-Commit:** **MANDATORY**: Run `black .` and `ruff check . --fix` before every code submission to prevent CI/pre-commit failures.
