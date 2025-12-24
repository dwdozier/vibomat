# Project Roadmap & TODOs

## Features

- [x] **Update Existing Playlists**: Add logic to update a playlist if the name already exists,
  rather than creating a duplicate.
- [x] **"Dry Run" Mode**: Add a `--dry-run` flag to verify track availability without creating a
  playlist.
- [x] **Export Functionality**: Create a command to export an existing Spotify playlist to a local
  JSON file (backup/migration).
- [x] **Private Playlists**: Support a `"public": false` field in the JSON schema to create private
  playlists.
- [x] **Enhanced Search**: Improve search accuracy (e.g., filter by album, fuzzy matching).
- [ ] **Playlist Cover Art**: Allow specifying a URL or local path for a custom playlist cover
  image in the JSON.
- [ ] **AI Playlist Builder**: Generate playlists based on mood, favorite artists, and other
  criteria using AI.
- [x] **External Metadata Sources**: Use non-Spotify sources to verify song/album versions for
  better accuracy.
- [x] **Version Preference**: Allow specifying song/album type (live, studio, compilation, remix)
  in the JSON configuration.
  - [x] **Apply Version to backup JSON files**: Try to determine the song/album type when backing up
    for future import.
  - [x] **Try to determine if original or remaster**: Let's see if the version is a remaster and
    let user choose preference if there is a choice.

## Technical Improvements

- [x] **CLI Framework**: Refactor to use `Typer` or `Click` for a more robust CLI experience.
- [x] **Unit Tests**: Add a test suite using `pytest`, mocking the Spotify API calls.
- [x] **Code Coverage**: Add `pytest-cov` to track test coverage.
- [ ] **CI/CD Pipeline**: Add GitHub Actions for linting (Ruff/Black) and running tests.
- [x] **Rate Limiting**: Implement backoff strategies for Spotify API rate limits.
- [x] **Logging**: Replace print statements with the `logging` module for better control over
  output verbosity (`--verbose`).
- [x] **Type Checking**: Add `ty` to pre-commit hooks (via local shim).
- [x] **Type Hinting**: Ensure full type coverage.

## Documentation

- [x] **JSON Schema**: Add a JSON Schema file to validate playlist JSON files automatically.
- [x] **Contributing Guide**: Expand on how to run tests and contribute code.
- [x] **App Registration Guide**: Detailed steps for creating a Spotify App, including setting the
  Redirect URI (`https://127.0.0.1:8888/callback`).
