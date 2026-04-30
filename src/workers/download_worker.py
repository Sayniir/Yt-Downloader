"""
download_worker.py
~~~~~~~~~~~~~~~~~~
Background thread for downloading videos.
Thread-safe for Tkinter/CustomTkinter.
"""
from __future__ import annotations
import threading

from src.core import downloader as dl

class DownloadWorker(threading.Thread):
    def __init__(self, urls: list[str], output_folder: str, quality: str, audio_only: bool,
                 download_subs: bool, sub_lang: str, embed_metadata: bool,
                 embed_thumbnail: bool, target_format: str, concurrent_frags: int,
                 callbacks: dict):
        super().__init__(daemon=True)
        self._urls = urls
        self._output_folder = output_folder
        self._quality = quality
        self._audio_only = audio_only
        self._download_subs = download_subs
        self._sub_lang = sub_lang
        self._embed_metadata = embed_metadata
        self._embed_thumbnail = embed_thumbnail
        self._target_format = target_format
        self._concurrent_frags = concurrent_frags
        self.callbacks = callbacks
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def run(self) -> None:
        try:
            if len(self._urls) == 1:
                result = dl.download_video(
                    url=self._urls[0],
                    output_folder=self._output_folder,
                    quality=self._quality,
                    audio_only=self._audio_only,
                    download_subs=self._download_subs,
                    sub_lang=self._sub_lang,
                    embed_metadata=self._embed_metadata,
                    embed_thumbnail=self._embed_thumbnail,
                    target_format=self._target_format,
                    progress_callback=self.callbacks.get("on_progress"),
                    cancel_event=self._cancel_event,
                    concurrent_frags=self._concurrent_frags,
                )
                if not self._cancel_event.is_set():
                    if cb := self.callbacks.get("on_finished"):
                        cb(result)
            else:
                dl.download_playlist(
                    urls=self._urls,
                    output_folder=self._output_folder,
                    quality=self._quality,
                    audio_only=self._audio_only,
                    download_subs=self._download_subs,
                    sub_lang=self._sub_lang,
                    embed_metadata=self._embed_metadata,
                    embed_thumbnail=self._embed_thumbnail,
                    target_format=self._target_format,
                    progress_callback=self.callbacks.get("on_progress"),
                    cancel_event=self._cancel_event,
                    concurrent_frags=self._concurrent_frags,
                )
                if not self._cancel_event.is_set():
                    if cb := self.callbacks.get("on_finished"):
                        cb(self._output_folder)
                        
        except RuntimeError as exc:
            if "cancelled" in str(exc).lower():
                if cb := self.callbacks.get("on_cancelled"):
                    cb()
            else:
                if cb := self.callbacks.get("on_error"):
                    cb(str(exc))
        except Exception as exc:
            if cb := self.callbacks.get("on_error"):
                cb(str(exc))

def start_download_worker(
    urls: list[str],
    output_folder: str,
    quality: str = "Best (auto)",
    audio_only: bool = False,
    download_subs: bool = False,
    sub_lang: str = "en",
    embed_metadata: bool = True,
    embed_thumbnail: bool = False,
    target_format: str = "Original",
    concurrent_frags: int = 4,
    on_progress=None,
    on_finished=None,
    on_error=None,
    on_cancelled=None,
) -> DownloadWorker:
    callbacks = {
        "on_progress": on_progress,
        "on_finished": on_finished,
        "on_error": on_error,
        "on_cancelled": on_cancelled,
    }
    worker = DownloadWorker(
        urls, output_folder, quality, audio_only, download_subs, sub_lang,
        embed_metadata, embed_thumbnail, target_format, concurrent_frags, callbacks
    )
    worker.start()
    return worker
