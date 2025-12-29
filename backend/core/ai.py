import os
import json
import logging
from typing import Any
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from .metadata import MetadataVerifier

logger = logging.getLogger("backend.core.ai")

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


def is_retryable_error(e: BaseException) -> bool:
    """Check if the exception is retryable (not a 404/Not Found error)."""
    msg = str(e).lower()
    return "404" not in msg and "not found" not in msg


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
    retry=retry_if_exception(is_retryable_error),
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


def discover_fallback_model(client: genai.Client) -> str:
    """Dynamically discover the best available Flash model as a fallback."""
    try:
        available = list_available_models(client)
        # Filter for 'flash' models and strip 'models/' prefix
        flash_models = [m.replace("models/", "") for m in available if "flash" in m.lower()]

        if flash_models:
            # Sort reverse alphabetically (e.g. gemini-2.0 > gemini-1.5)
            flash_models.sort(reverse=True)
            return flash_models[0]

    except Exception as e:
        logger.warning(f"Could not discovery fallback models: {e}")

    # Ultimate fallback
    return "gemini-2.0-flash"


def generate_playlist(description: str, count: int = 20) -> list[dict[str, Any]]:
    """Generate a playlist structure using Google Gemini (via google-genai SDK)."""
    api_key = get_ai_api_key()
    client = genai.Client(api_key=api_key)

    # Default to user preference or the latest alias
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    # Construct the user prompt
    user_message = f"""
    Create a playlist with {count} songs based on this description:
    "{description}"
    """

    contents = [SYSTEM_PROMPT, user_message]
    config = types.GenerateContentConfig(response_mime_type="application/json")

    response = None
    try:
        logger.info(f"Sending request to Gemini (Model: {model_name})...")
        response = generate_content_with_retry(
            client=client, model=model_name, contents=contents, config=config
        )
    except Exception as e:
        if not is_retryable_error(e):
            logger.warning(f"Model '{model_name}' not found or unavailable. Attempting fallback...")
            fallback = discover_fallback_model(client)
            if fallback and fallback != model_name:
                logger.info(f"Retrying with fallback model: {fallback}")
                response = generate_content_with_retry(
                    client=client, model=fallback, contents=contents, config=config
                )
            else:
                raise
        else:
            raise

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
