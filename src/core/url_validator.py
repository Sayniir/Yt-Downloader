"""
url_validator.py
~~~~~~~~~~~~~~~~
Validates and categorises YouTube URLs before any network calls are made.

Supported URL patterns:
  - youtube.com/watch?v=...         → "single"
  - youtu.be/<id>                   → "single"
  - youtube.com/shorts/<id>         → "single"
  - youtube.com/playlist?list=...   → "playlist"
  - youtube.com/watch?v=...&list=   → "playlist"  (video inside a playlist)
"""

import re
from dataclasses import dataclass
from enum import Enum


class URLType(str, Enum):
    SINGLE   = "single"
    PLAYLIST = "playlist"
    INVALID  = "invalid"


@dataclass
class ValidationResult:
    is_valid: bool
    url_type: URLType
    message: str


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

_YT_WATCH   = re.compile(
    r"^https?://(www\.)?youtube\.com/watch\?.*v=[\w-]{11}", re.IGNORECASE
)
_YT_SHORT   = re.compile(
    r"^https?://youtu\.be/[\w-]{11}", re.IGNORECASE
)
_YT_SHORTS  = re.compile(
    r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}", re.IGNORECASE
)
_YT_PLAYLIST = re.compile(
    r"^https?://(www\.)?youtube\.com/playlist\?.*list=[\w-]+", re.IGNORECASE
)
_YT_WATCH_PLAYLIST = re.compile(
    r"^https?://(www\.)?youtube\.com/watch\?.*list=[\w-]+", re.IGNORECASE
)


def validate_url(url: str) -> ValidationResult:
    """
    Validates a URL and determines whether it points to a single video
    or a playlist.

    Args:
        url: The raw URL string pasted by the user.

    Returns:
        A :class:`ValidationResult` with ``is_valid``, ``url_type``,
        and a human-readable ``message``.
    """
    url = url.strip()

    if not url:
        return ValidationResult(False, URLType.INVALID, "Please enter a URL.")

    # Playlist check must come before watch check because watch+list URLs
    # would match both patterns.
    if _YT_PLAYLIST.match(url):
        return ValidationResult(True, URLType.PLAYLIST,
                                "Playlist URL detected.")

    if _YT_WATCH_PLAYLIST.match(url):
        return ValidationResult(True, URLType.PLAYLIST,
                                "Video inside a playlist detected — "
                                "the full playlist will be available.")

    if _YT_WATCH.match(url):
        return ValidationResult(True, URLType.SINGLE, "Video URL detected.")

    if _YT_SHORT.match(url):
        return ValidationResult(True, URLType.SINGLE,
                                "Short link detected.")

    if _YT_SHORTS.match(url):
        return ValidationResult(True, URLType.SINGLE,
                                "YouTube Shorts URL detected.")

    # Generic YouTube domain check — catches edge cases with nicer message
    if "youtube.com" in url.lower() or "youtu.be" in url.lower():
        return ValidationResult(False, URLType.INVALID,
                                "YouTube URL not recognised. "
                                "Please paste a standard watch or playlist link.")

    return ValidationResult(False, URLType.INVALID,
                            "Not a YouTube URL. Please paste a valid link.")
