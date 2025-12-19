# Project Roadmap & TODOs

## Features

- [x] **Update Existing Playlists**: Add logic to update a playlist if the name already exists, rather than creating a duplicate.
- [x] **"Dry Run" Mode**: Add a `--dry-run` flag to verify track availability without creating a playlist.
- [ ] **Export Functionality**: Create a command to export an existing Spotify playlist to a local JSON file (backup/migration).
- [ ] **Private Playlists**: Support a `"public": false` field in the JSON schema to create private playlists.
- [ ] **Enhanced Search**: Improve search accuracy (e.g., filter by album, fuzzy matching).
- [ ] **Playlist Cover Art**: Allow specifying a URL or local path for a custom playlist cover image in the JSON.

## Technical Improvements

- [ ] **CLI Framework**: Refactor to use `Typer` or `Click` for a more robust CLI experience.
- [ ] **Unit Tests**: Add a test suite using `pytest`, mocking the Spotify API calls.
- [ ] **CI/CD Pipeline**: Add GitHub Actions for linting (Ruff/Black) and running tests.
- [ ] **Rate Limiting**: Implement backoff strategies for Spotify API rate limits.
- [ ] **Logging**: Replace print statements with the `logging` module for better control over output verbosity (`--verbose`).
- [x] **Type Checking**: Add `pyright` to pre-commit hooks.
- [x] **Type Hinting**: Ensure full type coverage.

## Documentation

- [ ] **JSON Schema**: Add a JSON Schema file to validate playlist JSON files automatically.
- [ ] **Contributing Guide**: Expand on how to run tests and contribute code.
