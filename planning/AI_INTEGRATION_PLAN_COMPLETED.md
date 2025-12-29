# AI Playlist Builder Integration Plan

This document outlines the strategy for integrating Generative AI into the `spotify-playlist-builder`.
The goal is to allow users to generate verified, high-quality playlists by describing their mood,
style, and preferences to an AI agent.

## 1. Objective

Enable users to generate high-quality playlist structures via AI, verified against external metadata
(MusicBrainz) to reduce hallucinations, and finally built on Spotify.

## 2. User Experience (UX) Scenarios

We will implement a new command `spotify-playlist-builder generate`. The user can choose between an
interactive wizard or a one-shot command.

### Scenario A: Interactive Wizard

1. **Command**: User runs `spotify-playlist-builder generate` without arguments.
2. **Prompt 1 (Mood)**: "Describe the mood or theme." (e.g., "Late night coding session").
3. **Prompt 2 (Artists)**: "Specific artists/inspirations?" (e.g., "The Midnight").
4. **Prompt 3 (Preference)**: "Preferred version?" (Studio/Live/Remix/Any).
5. **Prompt 4 (Count)**: "How many songs?" (Default: 20, Max: 100).
6. **Processing**: AI generates the list.
7. **Verification**: App verifies tracks against MusicBrainz.
8. **Review**: User sees the list of verified tracks (and any that were hallucinated/dropped).
9. **Approval**: User confirms generation of the JSON file.

### Scenario B: One-Shot Command

1. **Command**:

    ```bash
    spotify-playlist-builder generate \
        --prompt "20-song workout playlist, 80s rock, prefer remixes" \
        --output playlists/workout.json
    ```

2. **Processing**: AI generates list.
3. **Verification**: App verifies tracks against MusicBrainz.
4. **Output**: Generates JSON file with verified tracks.
5. **Feedback**: Logs success/failures to console (e.g., "Generated 18 verified tracks, 2 dropped").

## 3. AI Service Provider Options

We will focus on **Google Gemini** for the Proof of Concept (PoC) due to its generous free tier and
capabilities.

**Credential Setup**:
We will provide a setup wizard (`spotify-playlist-builder setup-ai`) to help users configure their API
key. Users can choose to store it in:

* System Keyring (Secure, Recommended)
* `.env` file (Portable)

## 4. Technical Architecture

### Module Structure

* `spotify_playlist_builder/ai.py`: Handles AI prompts and response parsing.
* `spotify_playlist_builder/metadata.py`: (Existing) Handles verification.

### Data Flow

1. **Input**: Collect user requirements.
2. **Prompting**: Send a structured prompt to the AI provider requesting a JSON array of
    `{artist, track, version_preference}`.
3. **Parsing**: Extract JSON from AI response.
4. **Verification (Anti-Hallucination)**:
    * Iterate through the AI-generated list.
    * Query **MusicBrainz** (via `MetadataVerifier`) to confirm the track exists.
    * *Note*: This avoids hitting Spotify API limits during the "brainstorming" phase.
5. **Review/Approval**:
    * Interactive: Display list to user.
    * One-shot: Log summary.
6. **File Generation**: Write valid entries to a local JSON file (matching `playlist_schema.json`).
7. **Build (Separate Step)**: The user runs `spotify-playlist-builder build` (or we chain it
    optionally) to search Spotify and create the playlist.

### Limits

* **Playlist Size**: Capped at 50-100 tracks per generation to prevent timeouts and API rate
    limits.
* **Spotify**: Actual Spotify lookup happens only during the `build` phase, allowing the tool to
    report "Track not found on Spotify" without failing the whole process.

## 5. Implementation Stages

### Phase 1: AI Setup & Connectivity (PoC)

* Implement `setup-ai` command (API Key management).
* Implement basic `generate` command using Google Gemini.
* Output raw AI JSON to console.

### Phase 2: Verification & Structure

* Integrate `MetadataVerifier` to check AI results against MusicBrainz.
* Implement the "Review" step (displaying verified vs. rejected tracks).
* Save output to `playlists/filename.json`.

### Phase 3: Polish & Integration

* Add interactive wizard prompts (Typer).
* Support chaining: `generate` -> auto-trigger `build`.
* Refine prompts for better version handling (Live vs Studio).

## 6. Implementation Checklist

### Phase 1: PoC

* [x] Create branch `feature/ai-integration-poc`.
* [x] Add `google-genai` to `pyproject.toml`.
* [x] Implement `ai.py` with basic Gemini connection.

* [x] Add `setup-ai` command to CLI for API key management (Keyring/.env).
* [x] Add basic `generate` command to CLI (takes prompt, prints raw JSON).

### Phase 2: Verification

* [x] Create branch `feature/ai-verification`.
* [x] Connect `ai.py` output to `MetadataVerifier` in `metadata.py`.
* [x] Filter out hallucinations (songs not found in MusicBrainz).
* [x] Parse AI JSON into strict schema format.
* [x] Implement file saving to `playlists/`.

### Phase 3: UX & Polish

* [x] Create branch `feature/ai-ux-polish`.
* [x] Implement interactive Typer prompts (Mood, Artist, Count).
* [x] Add `generate --build` flag to chain the build process.
* [x] Add unit tests for AI logic (mocking the API).
* [x] Update documentation (README, SETUP).
