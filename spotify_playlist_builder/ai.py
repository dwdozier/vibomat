import os
import json
import logging
from typing import Any
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .metadata import MetadataVerifier

logger = logging.getLogger("spotify_playlist_builder.ai")

SYSTEM_PROMPT = """
You are a professional music curator. Your goal is to generate a list of songs based on the user's
description. Return ONLY a raw JSON array of objects. Do not include markdown formatting, code
blocks, or explanatory text.
Each object must follow this schema:
{
  "artist": "Artist Name",
  "track": "Track Title",
  "version": "studio" | "live" | "remix" | "original" | "remaster" | null
}
If the user specifies a number of songs, try to meet that count. Default to 20 if unspecified.
"""


def get_ai_api_key() -> str:
    """Retrieve the AI API Key from keyring or env."""
    try:
        # Check env first
        key = os.getenv("GEMINI_API_KEY")
        if key:
            return key

        # Check keyring (if available)
        try:
            import keyring

            key = keyring.get_password("spotify-playlist-builder", "gemini_api_key")
            if key:
                return key
        except ImportError:
            pass

        raise ValueError(
            "Gemini API Key not found. Run 'spotify-playlist-builder setup-ai' or set "
            "GEMINI_API_KEY."
        )

    except Exception as e:
        raise ValueError(f"Failed to retrieve API Key: {e}")


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True,
)
def generate_content_with_retry(client, model, contents, config):
    """Wrapper for generate_content with retry logic."""
    return client.models.generate_content(model=model, contents=contents, config=config)


def list_available_models(client: genai.Client | None = None) -> list[str]:
    """List available Gemini models for the configured key."""
    if not client:
        try:
            api_key = get_ai_api_key()
            client = genai.Client(api_key=api_key)
        except Exception:
            return []
    models = []
    try:
        for m in client.models.list():
            methods = getattr(m, "supported_generation_methods", [])
            if "generateContent" in methods:
                models.append(m.name)
        return models
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return []


def get_best_flash_model(client: genai.Client) -> str:
    """Determine the best available Flash model."""
    env_model = os.getenv("GEMINI_MODEL")
    if env_model:
        return env_model

    # Known models in order of preference (latest first)
    known_models = [
        "gemini-flash-latest",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-001",
    ]

    try:
        available = list_available_models(client)
        # Check for known models in available list
        for candidate in known_models:
            # Check for exact match or 'models/' prefix match
            if candidate in available or f"models/{candidate}" in available:
                return candidate

        # If no known flash model found, try to find *any* model with 'flash' in name
        flash_models = [m for m in available if "flash" in m.lower()]
        if flash_models:
            # Sort to pick the one that looks "newest" (highest number/version)
            flash_models.sort(reverse=True)
            return flash_models[0].replace("models/", "")

    except Exception as e:
        logger.warning(f"Could not auto-detect models: {e}")

    # Fallback default if detection fails
    return "gemini-2.0-flash"


def generate_playlist(description: str, count: int = 20) -> list[dict[str, Any]]:
    """Generate a playlist structure using Google Gemini (via google-genai SDK)."""
    api_key = get_ai_api_key()
    client = genai.Client(api_key=api_key)
    model_name = get_best_flash_model(client)

    # Construct the user prompt
    user_message = f"""
    Create a playlist with {count} songs based on this description:
    "{description}"
    """

    try:
        logger.info(f"Sending request to Gemini (Model: {model_name})...")

        response = generate_content_with_retry(
            client=client,
            model=model_name,
            contents=[SYSTEM_PROMPT, user_message],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        logger.info("Received response from Gemini.")

        text = response.text.strip()

        # Clean up response text if it accidentally contains markdown
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text)

        if not isinstance(data, list):
            if isinstance(data, dict) and "tracks" in data:
                return data["tracks"]
            raise ValueError("AI response was not a list of tracks.")

        return data

    except Exception as e:
        if "404" in str(e):
            logger.error(f"Model '{model_name}' not found.")
            available = list_available_models(client)
            if available:
                logger.info(f"Available models: {', '.join(available)}")
                logger.info("Set GEMINI_MODEL environment variable to one of the above.")
        logger.error(f"AI Generation failed: {e}")
        raise


def verify_ai_tracks(tracks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Verify AI-generated tracks against MusicBrainz."""
    verifier = MetadataVerifier()
    verified_tracks = []
    rejected_tracks = []

    logger.info(f"Verifying {len(tracks)} tracks against MusicBrainz...")

    for item in tracks:
        artist = item.get("artist")
        track = item.get("track")
        version = item.get("version")

        if not artist or not track:
            continue

        try:
            # We use verify_track_version which checks for existence + version
            # If version is None or 'studio', it just checks existence
            if verifier.verify_track_version(artist, track, version or "studio"):
                verified_tracks.append(item)
            else:
                rejected_tracks.append(f"{artist} - {track}")
        except Exception as e:
            logger.debug(f"Verification failed for {artist} - {track}: {e}")
            # If API fails, we lean towards keeping it but maybe warning?
            # For now, let's keep it if MB is down, but reject if MB says no.
            verified_tracks.append(item)

    return verified_tracks, rejected_tracks
