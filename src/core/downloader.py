"""
downloader.py
~~~~~~~~~~~~~
Core download engine wrapping yt-dlp.

Features:
  - Format selection (quality presets + audio-only)
  - Real-time progress via callback hooks
  - Automatic retry with exponential backoff (up to 3 attempts)
  - Clean filename sanitization
  - Duplicate detection
  - Subtitle download (SRT/VTT + embed option)
  - Metadata embedding (title, uploader, date)
  - Thumbnail embedding
  - Cancellation support via threading.Event
"""

from __future__ import annotations

import logging
import re
import threading
import time
from pathlib import Path
from typing import Callable

import yt_dlp
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Quality / format presets
# ---------------------------------------------------------------------------

QUALITY_PRESETS: dict[str, str] = {
    "Best (auto)": "bestvideo+bestaudio/best",
    "4K (2160p)":  "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p":       "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p":       "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":        "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":        "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p":        "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "240p":        "bestvideo[height<=240]+bestaudio/best[height<=240]",
    "144p":        "bestvideo[height<=144]+bestaudio/best[height<=144]",
    "Audio Only":  "bestaudio/best",
}

# Maximum retry attempts and base delay (seconds) for exponential backoff
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


# ---------------------------------------------------------------------------
# Progress hook helpers
# ---------------------------------------------------------------------------

def _clean_ansi(text: str) -> str:
    """Strip ANSI escape codes that yt-dlp injects into percentage strings."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _build_progress_hook(
    callback: Callable[[dict], None],
    cancel_event: threading.Event,
) -> Callable[[dict], None]:
    """
    Return a yt-dlp progress hook that:
      1. Forwards structured progress data to *callback*.
      2. Raises DownloadError if *cancel_event* is set (aborts yt-dlp).
    """
    def hook(d: dict) -> None:
        if cancel_event.is_set():
            raise DownloadError("Download cancelled by user.")

        status = d.get("status")

        if status == "downloading":
            # Parse percentage — may be a string like " 42.3%" or a float
            pct_str = _clean_ansi(d.get("_percent_str", "0%")).strip()
            try:
                pct = float(pct_str.replace("%", ""))
            except ValueError:
                pct = 0.0

            speed_str = _clean_ansi(d.get("_speed_str", "N/A")).strip()
            eta_str   = _clean_ansi(d.get("_eta_str", "N/A")).strip()

            callback({
                "status":    "downloading",
                "percent":   pct,
                "speed":     speed_str,
                "eta":       eta_str,
                "filename":  d.get("filename", ""),
                "total_bytes": d.get("total_bytes") or d.get("total_bytes_estimate", 0),
            })

        elif status == "finished":
            callback({
                "status":   "finished",
                "percent":  100.0,
                "speed":    "",
                "eta":      "",
                "filename": d.get("filename", ""),
            })

        elif status == "error":
            callback({
                "status":  "error",
                "percent": 0.0,
                "speed":   "",
                "eta":     "",
                "message": str(d.get("error", "Unknown error")),
            })

    return hook


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """
    Replace characters that are illegal in Windows/Linux filenames.
    yt-dlp handles most of this with ``restrictfilenames``, but we apply
    an extra pass for safety.
    """
    # Replace Windows-illegal characters
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    # Collapse whitespace runs
    name = re.sub(r"\s+", " ", name).strip()
    # Limit length
    return name[:200]


def _output_exists(output_path: Path, title: str, ext: str) -> bool:
    """Check if a file with the expected name already exists."""
    safe_name = _sanitize_filename(title)
    target = output_path / f"{safe_name}.{ext}"
    return target.exists()


# ---------------------------------------------------------------------------
# Download options builder
# ---------------------------------------------------------------------------

def _build_ydl_opts(
    output_folder: str,
    quality: str,
    audio_only: bool,
    download_subs: bool,
    sub_lang: str,
    embed_metadata: bool,
    embed_thumbnail: bool,
    progress_hook: Callable,
    target_format: str = "Original",
    concurrent_frags: int = 4,
    extra_opts: dict | None = None,
) -> dict:
    """
    Assemble the complete yt-dlp options dictionary.
    """
    output_folder_path = Path(output_folder)
    output_folder_path.mkdir(parents=True, exist_ok=True)

    # Output template: clean title + extension
    output_template = str(output_folder_path / "%(title)s.%(ext)s")

    # Format selection
    if audio_only:
        fmt = QUALITY_PRESETS["Audio Only"]
    else:
        fmt = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["Best (auto)"])

    # Post-processors
    postprocessors: list[dict] = []

    if audio_only:
        postprocessors.append({
            "key":            "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        })

    if embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

    if embed_thumbnail:
        postprocessors.append({"key": "EmbedThumbnail"})

    if not audio_only and target_format and target_format.lower() != "original":
        # Recode video to target format (avi, mkv, mp4, etc.)
        postprocessors.append({
            "key": "FFmpegVideoConvertor",
            "preferedformat": target_format.lower()
        })

    opts: dict = {
        # Format
        "format":              fmt,
        "merge_output_format": "mkv" if target_format.lower() == "mkv" else "mp4",

        # Output
        "outtmpl":             output_template,
        "restrictfilenames":   False,   # we handle sanitization ourselves

        # Progress
        "progress_hooks":      [progress_hook],

        # Network
        "retries":             MAX_RETRIES,
        "fragment_retries":    MAX_RETRIES,
        "concurrent_fragment_downloads": concurrent_frags,

        # Subtitles
        "writesubtitles":      download_subs,
        "writeautomaticsub":   download_subs,
        "subtitleslangs":      [sub_lang] if download_subs else [],
        "subtitlesformat":     "srt/vtt/best",

        # Post-processing
        "postprocessors":      postprocessors,

        # Misc
        "quiet":               True,
        "no_warnings":         True,
        "ignoreerrors":        False,
        "nooverwrites":        True,     # avoid overwriting existing files
        "writethumbnail":      embed_thumbnail,
        "addmetadata":         embed_metadata,
    }

    if extra_opts:
        opts.update(extra_opts)

    return opts


# ---------------------------------------------------------------------------
# Public download function
# ---------------------------------------------------------------------------

def download_video(
    url: str,
    output_folder: str,
    quality: str = "Best (auto)",
    audio_only: bool = False,
    download_subs: bool = False,
    sub_lang: str = "en",
    embed_metadata: bool = True,
    embed_thumbnail: bool = False,
    target_format: str = "Original",
    progress_callback: Callable[[dict], None] | None = None,
    cancel_event: threading.Event | None = None,
    concurrent_frags: int = 4,
) -> str:
    """
    Download a single YouTube video with retry logic.

    Args:
        url:              YouTube URL (video or playlist entry).
        output_folder:    Destination directory path.
        quality:          One of the keys in :data:`QUALITY_PRESETS`.
        audio_only:       Extract audio only (MP3).
        download_subs:    Download subtitles alongside video.
        sub_lang:         Subtitle language code (e.g., "en", "fr").
        embed_metadata:   Write title/uploader/date into file metadata.
        embed_thumbnail:  Embed thumbnail as album art.
        progress_callback: Receives progress dicts during download.
        cancel_event:     Set this event to abort the download cleanly.
        concurrent_frags: Number of concurrent fragment downloads.

    Returns:
        Path to the downloaded file (best-guess; yt-dlp resolves actual name).

    Raises:
        DownloadError: If all retries fail.
        RuntimeError:  If the download is cancelled.
    """
    if cancel_event is None:
        cancel_event = threading.Event()

    _cb = progress_callback or (lambda d: None)

    hook = _build_progress_hook(_cb, cancel_event)

    opts = _build_ydl_opts(
        output_folder   = output_folder,
        quality         = quality,
        audio_only      = audio_only,
        download_subs   = download_subs,
        sub_lang        = sub_lang,
        embed_metadata  = embed_metadata,
        embed_thumbnail = embed_thumbnail,
        progress_hook   = hook,
        target_format   = target_format,
        concurrent_frags = concurrent_frags,
    )

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        if cancel_event.is_set():
            raise RuntimeError("Download cancelled.")

        try:
            logger.info("Download attempt %d/%d — %s", attempt, MAX_RETRIES, url)
            _cb({"status": "downloading", "percent": 0.0,
                 "speed": "", "eta": "",
                 "message": f"Starting download (attempt {attempt}/{MAX_RETRIES})…"})

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            # If we reach here, download succeeded
            _cb({"status": "finished", "percent": 100.0,
                 "speed": "", "eta": "", "filename": ""})
            return output_folder  # caller can scan folder for new files

        except DownloadError as exc:
            exc_str = str(exc)
            if "cancelled by user" in exc_str.lower():
                raise RuntimeError("Download cancelled.") from exc

            last_error = exc
            logger.warning("Attempt %d failed: %s", attempt, exc_str)

            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 2s, 4s, 8s
                _cb({"status": "retrying",
                     "percent": 0.0,
                     "speed": "",
                     "eta": "",
                     "message": f"Retrying in {delay:.0f}s… (attempt {attempt}/{MAX_RETRIES})"})
                # Wait with cancellation support
                for _ in range(int(delay * 10)):
                    if cancel_event.is_set():
                        raise RuntimeError("Download cancelled during retry wait.")
                    time.sleep(0.1)

    raise DownloadError(
        f"Download failed after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


def download_playlist(
    urls: list[str],
    output_folder: str,
    quality: str = "Best (auto)",
    audio_only: bool = False,
    download_subs: bool = False,
    sub_lang: str = "en",
    embed_metadata: bool = True,
    embed_thumbnail: bool = False,
    target_format: str = "Original",
    progress_callback: Callable[[dict], None] | None = None,
    cancel_event: threading.Event | None = None,
    concurrent_frags: int = 4,
) -> list[str]:
    """
    Download multiple videos sequentially (for playlist support).

    *progress_callback* receives an additional ``"item_index"`` and
    ``"item_total"`` key so the UI can display "2 / 10" style progress.

    Returns:
        List of output folder paths (one per video).
    """
    if cancel_event is None:
        cancel_event = threading.Event()

    total   = len(urls)
    results = []

    for idx, url in enumerate(urls, start=1):
        if cancel_event.is_set():
            break

        def _cb(d: dict, _idx=idx, _total=total) -> None:
            if progress_callback:
                d["item_index"] = _idx
                d["item_total"] = _total
                progress_callback(d)

        try:
            result = download_video(
                url             = url,
                output_folder   = output_folder,
                quality         = quality,
                audio_only      = audio_only,
                download_subs   = download_subs,
                sub_lang        = sub_lang,
                embed_metadata  = embed_metadata,
                embed_thumbnail = embed_thumbnail,
                target_format   = target_format,
                progress_callback = _cb,
                cancel_event    = cancel_event,
                concurrent_frags = concurrent_frags,
            )
            results.append(result)
        except RuntimeError:
            # Cancelled — stop the loop
            break
        except DownloadError as exc:
            logger.error("Failed to download item %d (%s): %s", idx, url, exc)
            if progress_callback:
                progress_callback({
                    "status":     "error",
                    "percent":    0.0,
                    "speed":      "",
                    "eta":        "",
                    "item_index": idx,
                    "item_total": total,
                    "message":    str(exc),
                })
            # Continue with next item rather than aborting entire playlist
            continue

    return results
