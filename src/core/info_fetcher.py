"""
info_fetcher.py
~~~~~~~~~~~~~~~
Fetches video/playlist metadata from YouTube using yt-dlp WITHOUT
downloading any media. Returns clean Python dicts ready for the UI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

import yt_dlp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FormatInfo:
    """Represents a single available download format."""
    format_id:  str
    extension:  str
    resolution: str          # e.g. "1080p", "audio only"
    filesize:   int | None   # bytes, may be None if unknown
    vcodec:     str
    acodec:     str
    fps:        float | None
    note:       str          # human-readable label for the UI

    @property
    def is_audio_only(self) -> bool:
        return self.vcodec in ("none", "") or not self.vcodec


@dataclass
class VideoInfo:
    """Metadata for a single video."""
    url:          str
    video_id:     str
    title:        str
    uploader:     str
    duration:     int              # seconds
    thumbnail_url: str
    view_count:   int | None
    upload_date:  str              # YYYYMMDD
    description:  str
    formats:      list[FormatInfo] = field(default_factory=list)

    @property
    def duration_str(self) -> str:
        h, rem = divmod(self.duration, 3600)
        m, s   = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


@dataclass
class PlaylistEntry:
    """Lightweight entry for a playlist item (no full format list)."""
    index:    int
    url:      str
    video_id: str
    title:    str
    duration: int | None
    uploader: str


@dataclass
class PlaylistInfo:
    """Metadata for a playlist."""
    url:          str
    playlist_id:  str
    title:        str
    uploader:     str
    entry_count:  int
    entries:      list[PlaylistEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_ydl_opts(quiet: bool = True) -> dict:
    return {
        "quiet":          quiet,
        "no_warnings":    True,
        "extract_flat":   False,   # we want full info
        "skip_download":  True,
        "noplaylist":     True,    # controlled per-call
        "ignoreerrors":   False,
    }


def _best_thumbnail(thumbnails: list[dict]) -> str:
    """Return the URL of the highest-resolution thumbnail available."""
    if not thumbnails:
        return ""
    # yt-dlp sorts thumbnails by quality (last is usually best)
    for t in reversed(thumbnails):
        if url := t.get("url"):
            return url
    return ""


def _parse_format(fmt: dict) -> FormatInfo:
    """Convert a raw yt-dlp format dict into a :class:`FormatInfo`."""
    height  = fmt.get("height")
    res_str = f"{height}p" if height else "audio only"
    fps     = fmt.get("fps")
    note    = fmt.get("format_note", "")

    return FormatInfo(
        format_id  = fmt.get("format_id", "?"),
        extension  = fmt.get("ext", "?"),
        resolution = res_str,
        filesize   = fmt.get("filesize") or fmt.get("filesize_approx"),
        vcodec     = fmt.get("vcodec", ""),
        acodec     = fmt.get("acodec", ""),
        fps        = fps,
        note       = note,
    )


def _unique_resolutions(formats: list[dict]) -> list[FormatInfo]:
    """
    Deduplicate formats keeping the best quality per resolution bucket.
    Audio-only tracks are preserved as a group.
    """
    seen_heights: set[str] = set()
    result: list[FormatInfo] = []

    # Sort descending by height so we keep the best quality per bucket
    def sort_key(f: dict) -> int:
        return f.get("height") or 0

    for fmt in sorted(formats, key=sort_key, reverse=True):
        vcodec = fmt.get("vcodec", "")
        acodec = fmt.get("acodec", "")
        height = fmt.get("height")

        # Skip format-less entries
        if fmt.get("format_id") is None:
            continue

        # Audio-only: always include the best audio format
        if (not height) and vcodec in ("none", "", None):
            if "audio_only" not in seen_heights:
                seen_heights.add("audio_only")
                result.append(_parse_format(fmt))
            continue

        # Video formats: deduplicate by height
        key = str(height) if height else "?"
        if key not in seen_heights:
            seen_heights.add(key)
            result.append(_parse_format(fmt))

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_video_info(
    url: str,
    progress_callback: Callable[[str], None] | None = None,
) -> VideoInfo:
    """
    Extract metadata for a single YouTube video.

    Args:
        url:               YouTube watch URL.
        progress_callback: Optional callable called with status strings
                           (e.g., "Fetching video info…").

    Returns:
        A populated :class:`VideoInfo` instance.

    Raises:
        yt_dlp.utils.DownloadError: If yt-dlp cannot access the URL.
        ValueError:                 If the URL resolves to a playlist,
                                    not a single video.
    """
    if progress_callback:
        progress_callback("Fetching video info…")

    opts = _make_ydl_opts()

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise ValueError("Could not retrieve video information.")

    # If yt-dlp returns a playlist dict, reject it here
    if info.get("_type") == "playlist":
        raise ValueError(
            "This URL points to a playlist. Use 'fetch_playlist_info' instead."
        )

    formats = _unique_resolutions(info.get("formats", []))

    return VideoInfo(
        url           = url,
        video_id      = info.get("id", ""),
        title         = info.get("title", "Unknown Title"),
        uploader      = info.get("uploader") or info.get("channel", "Unknown"),
        duration      = info.get("duration") or 0,
        thumbnail_url = _best_thumbnail(info.get("thumbnails", [])),
        view_count    = info.get("view_count"),
        upload_date   = info.get("upload_date", ""),
        description   = (info.get("description") or "")[:500],
        formats       = formats,
    )


def fetch_playlist_info(
    url: str,
    progress_callback: Callable[[str], None] | None = None,
) -> PlaylistInfo:
    """
    Extract metadata for a YouTube playlist (without downloading).

    This uses ``extract_flat=True`` to get entry titles quickly without
    fetching full info for each video (much faster for long playlists).

    Args:
        url:               YouTube playlist URL.
        progress_callback: Optional status callback.

    Returns:
        A populated :class:`PlaylistInfo` instance.

    Raises:
        yt_dlp.utils.DownloadError: On network/access errors.
        ValueError:                 If the URL is not a playlist.
    """
    if progress_callback:
        progress_callback("Fetching playlist info…")

    opts = {
        "quiet":        True,
        "no_warnings":  True,
        "extract_flat": True,   # fast — no per-video network calls
        "skip_download": True,
        "noplaylist":   False,  # allow playlist extraction
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise ValueError("Could not retrieve playlist information.")

    if info.get("_type") not in ("playlist", "multi_video"):
        # Single video URL passed by mistake
        raise ValueError(
            "This URL points to a single video. "
            "Use 'fetch_video_info' instead."
        )

    raw_entries = info.get("entries") or []
    entries: list[PlaylistEntry] = []

    for idx, entry in enumerate(raw_entries, start=1):
        if entry is None:
            continue
        vid_id = entry.get("id", "")
        entries.append(PlaylistEntry(
            index    = idx,
            url      = entry.get("url") or f"https://www.youtube.com/watch?v={vid_id}",
            video_id = vid_id,
            title    = entry.get("title", f"Video {idx}"),
            duration = entry.get("duration"),
            uploader = entry.get("uploader") or entry.get("channel", ""),
        ))

    return PlaylistInfo(
        url         = url,
        playlist_id = info.get("id", ""),
        title       = info.get("title", "Unknown Playlist"),
        uploader    = info.get("uploader") or info.get("channel", ""),
        entry_count = len(entries),
        entries     = entries,
    )
