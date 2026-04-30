"""
settings.py
~~~~~~~~~~~
Persists user preferences to a JSON file in the user's home directory.
Thread-safe reads and writes via a reentrant lock.
"""

import json
import threading
from pathlib import Path

# Store config alongside the application so it stays local
_CONFIG_DIR  = Path.home() / ".youtube_downloader"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS: dict = {
    "output_folder":      str(Path.home() / "Downloads"),
    "default_quality":    "Best",
    "audio_only":         False,
    "download_subtitles": False,
    "subtitle_language":  "en",
    "embed_metadata":     True,
    "embed_thumbnail":    False,
    "max_retries":        3,
    "theme":              "dark",
    "concurrent_frags":   4,          # yt-dlp concurrent fragment downloads
}

_lock = threading.RLock()
_cache: dict | None = None


def _ensure_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_from_disk() -> dict:
    """Read config from disk, merging with defaults for missing keys."""
    _ensure_dir()
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Merge: keep user values but add any new default keys
            merged = {**_DEFAULTS, **data}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def get_all() -> dict:
    """Return a copy of all settings."""
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load_from_disk()
        return dict(_cache)


def get(key: str, default=None):
    """Return a single setting value."""
    return get_all().get(key, default)


def set(key: str, value) -> None:  # noqa: A001
    """Update a single setting and persist to disk immediately."""
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load_from_disk()
        _cache[key] = value
        _save_to_disk(_cache)


def update(data: dict) -> None:
    """Bulk-update settings and persist."""
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load_from_disk()
        _cache.update(data)
        _save_to_disk(_cache)


def reset() -> None:
    """Reset all settings to defaults."""
    global _cache
    with _lock:
        _cache = dict(_DEFAULTS)
        _save_to_disk(_cache)


def _save_to_disk(data: dict) -> None:
    _ensure_dir()
    with open(_CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
