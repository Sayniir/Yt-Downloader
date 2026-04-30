"""
queue_manager.py
~~~~~~~~~~~~~~~~
Manages concurrent downloads via a thread-pool-like mechanism, logging results
to the SQLite history database automatically.
Removed PyQt5 dependencies for CustomTkinter compatibility.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass

from src.core import database
from src.workers.download_worker import start_download_worker

@dataclass
class QueueItem:
    id: str
    url: str
    title: str
    options: dict
    status: str = "queued"
    percent: float = 0.0
    speed: str = ""
    eta: str = ""
    filename: str = ""
    error_msg: str = ""


class QueueManager:
    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.items: dict[str, QueueItem] = {}
        self.queue: list[str] = []
        self.active: list[str] = []
        self._workers: dict[str, object] = {}

        # Callbacks to be set by UI
        self.on_item_added = None
        self.on_item_updated = None
        self.on_queue_completed = None

    def add_item(self, url: str, title: str, options: dict) -> str:
        item_id = str(uuid.uuid4())
        item = QueueItem(id=item_id, url=url, title=title, options=options)
        self.items[item_id] = item
        self.queue.append(item_id)
        if self.on_item_added:
            self.on_item_added(item)
        self._process_queue()
        return item_id

    def cancel_item(self, item_id: str):
        if item_id in self.queue:
            self.queue.remove(item_id)
            self.items[item_id].status = "cancelled"
            if self.on_item_updated:
                self.on_item_updated(self.items[item_id])
        elif item_id in self.active:
            worker = self._workers.get(item_id)
            if worker:
                worker.cancel()

    def set_concurrency(self, limit: int):
        self.max_concurrent = limit
        self._process_queue()

    def _process_queue(self):
        while len(self.active) < self.max_concurrent and self.queue:
            item_id = self.queue.pop(0)
            self._start_download(item_id)

    def _start_download(self, item_id: str):
        item = self.items[item_id]
        item.status = "downloading"
        self.active.append(item_id)
        if self.on_item_updated:
            self.on_item_updated(item)

        def on_prog(d):
            if d.get("status") == "downloading":
                item.percent = d.get("percent", 0.0)
                item.speed = d.get("speed", "")
                item.eta = d.get("eta", "")
                fn = d.get("filename", "")
                if fn:
                    item.filename = fn
                if self.on_item_updated:
                    self.on_item_updated(item)
            elif d.get("status") == "retrying":
                item.error_msg = d.get("message", "Retrying...")
                if self.on_item_updated:
                    self.on_item_updated(item)

        def on_fin(folder):
            item.status = "finished"
            item.percent = 100.0
            if self.on_item_updated:
                self.on_item_updated(item)
            self._cleanup_worker(item_id)
            database.add_record(
                title=item.title, url=item.url, quality=item.options.get("quality", ""),
                fmt=item.options.get("target_format", "Original"), file_path=item.filename or folder, status="completed"
            )

        def on_err(msg):
            item.status = "error"
            item.error_msg = msg
            if self.on_item_updated:
                self.on_item_updated(item)
            self._cleanup_worker(item_id)
            database.add_record(
                title=item.title, url=item.url, quality=item.options.get("quality", ""),
                fmt=item.options.get("target_format", "Original"), file_path="", status="error"
            )

        def on_can():
            item.status = "cancelled"
            if self.on_item_updated:
                self.on_item_updated(item)
            self._cleanup_worker(item_id)

        opts = item.options
        w = start_download_worker(
            urls=[item.url],
            output_folder=opts.get("output_folder", ""),
            quality=opts.get("quality", "Best (auto)"),
            audio_only=opts.get("audio_only", False),
            download_subs=opts.get("download_subs", False),
            sub_lang=opts.get("sub_lang", "en"),
            embed_metadata=opts.get("embed_metadata", True),
            embed_thumbnail=opts.get("embed_thumbnail", False),
            target_format=opts.get("target_format", "Original"),
            on_progress=on_prog,
            on_finished=on_fin,
            on_error=on_err,
            on_cancelled=on_can
        )
        self._workers[item_id] = w

    def _cleanup_worker(self, item_id: str):
        if item_id in self.active:
            self.active.remove(item_id)
        if item_id in self._workers:
            del self._workers[item_id]
        self._process_queue()
        if not self.active and not self.queue:
            if self.on_queue_completed:
                self.on_queue_completed()
