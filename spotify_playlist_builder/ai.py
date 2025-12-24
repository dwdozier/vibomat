import os
import json
import logging
import google.generativeai as genai
from typing import Any

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
    # We reuse the auth logic but look for a specific key
    # For now, let's look for GEMINI_API_KEY in env or keyring
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


def generate_playlist(description: str, count: int = 20) -> list[dict[str, Any]]:
    """Generate a playlist structure using Google Gemini."""
    api_key = get_ai_api_key()
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

    # Construct the user prompt
    user_message = f"""
    Create a playlist with {count} songs based on this description:
    "{description}"
    """

    try:
        logger.info("Sending request to Gemini...")
        response = model.generate_content(
            contents=[SYSTEM_PROMPT, user_message],
            generation_config={"response_mime_type": "application/json"},
        )

        logger.info("Received response from Gemini.")

        # Clean up response text if it accidentally contains markdown
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text)

        if not isinstance(data, list):
            # Sometimes it might return {"tracks": [...]}
            if isinstance(data, dict) and "tracks" in data:
                return data["tracks"]
            raise ValueError("AI response was not a list of tracks.")

        return data

    except Exception as e:
        logger.error(f"AI Generation failed: {e}")
        raise
