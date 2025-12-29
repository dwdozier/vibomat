import difflib
import logging
import re
from spotipy.exceptions import SpotifyException
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)

logger = logging.getLogger("backend.core")


def is_rate_limit_error(exception: BaseException) -> bool:
    """Return True if exception is a 429 Too Many Requests."""
    return isinstance(exception, SpotifyException) and exception.http_status == 429


rate_limit_retry = retry(
    retry=retry_if_exception(is_rate_limit_error),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


def _similarity(s1: str, s2: str) -> float:
    """Calculate string similarity ratio."""
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def _determine_version(track_name: str, album_name: str) -> str:
    """Determine the version of a track based on its name and album."""
    name_lower = track_name.lower()
    album_lower = album_name.lower()

    if "live" in name_lower or "live" in album_lower:
        return "live"
    if "remix" in name_lower or "mix" in name_lower:
        return "remix"

    compilation_keywords = ["greatest hits", "best of", "collection", "anthology"]
    if any(k in album_lower for k in compilation_keywords):
        return "compilation"

    if "remaster" in name_lower or "remaster" in album_lower:
        return "remaster"

    return "studio"


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    text = re.sub(r"[^a-zA-Z0-9]", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.lower().strip("_")
