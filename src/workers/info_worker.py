"""
info_worker.py
~~~~~~~~~~~~~~
Background thread for fetching video/playlist metadata.
Thread-safe for Tkinter/CustomTkinter.
"""
from __future__ import annotations
import threading

from src.core.info_fetcher import (
    VideoInfo,
    PlaylistInfo,
    fetch_video_info,
    fetch_playlist_info,
)
from src.core.url_validator import URLType

class InfoWorker(threading.Thread):
    def __init__(self, url: str, url_type: URLType, callbacks: dict):
        super().__init__(daemon=True)
        self._url = url
        self._url_type = url_type
        self.callbacks = callbacks

    def run(self) -> None:
        try:
            if self._url_type == URLType.PLAYLIST:
                info = fetch_playlist_info(
                    self._url,
                    progress_callback=self.callbacks.get("on_status")
                )
                if cb := self.callbacks.get("on_playlist_ready"):
                    cb(info)
            else:
                info = fetch_video_info(
                    self._url,
                    progress_callback=self.callbacks.get("on_status")
                )
                if cb := self.callbacks.get("on_video_ready"):
                    cb(info)
        except Exception as exc:
            if cb := self.callbacks.get("on_error"):
                cb(str(exc))
        finally:
            if cb := self.callbacks.get("on_finished"):
                cb()

def start_info_worker(
    url: str,
    url_type: URLType,
    on_video_ready=None,
    on_playlist_ready=None,
    on_status=None,
    on_error=None,
    on_finished=None,
) -> InfoWorker:
    callbacks = {
        "on_video_ready": on_video_ready,
        "on_playlist_ready": on_playlist_ready,
        "on_status": on_status,
        "on_error": on_error,
        "on_finished": on_finished,
    }
    worker = InfoWorker(url, url_type, callbacks)
    worker.start()
    return worker
