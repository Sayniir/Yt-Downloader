"""video_info.py — CustomTkinter Void Edition"""
import threading
import requests
from io import BytesIO
from PIL import Image
import customtkinter as ctk

from src.core.info_fetcher import VideoInfo
from src.ui import theme

class VideoInfoWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent, fg_color=theme.SURFACE_COLOR, corner_radius=12)
        self._build()
        self.pack_forget()  # Hidden initially

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        # Thumbnail
        self.lbl_thumb = ctk.CTkLabel(self, text="")
        self.lbl_thumb.grid(row=0, column=0, padx=16, pady=16, sticky="nw")

        # Info container
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=(0, 16), pady=16, sticky="nsew")

        self.lbl_title = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=theme.TEXT_PRIMARY,
            justify="left", wraplength=400
        )
        self.lbl_title.pack(anchor="w", pady=(0, 4))

        self.lbl_channel = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=13),
            text_color=theme.TEXT_SECONDARY
        )
        self.lbl_channel.pack(anchor="w", pady=(0, 12))

        # Stats chips
        stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(anchor="w")

        self.lbl_views = self._make_chip(stats_frame)
        self.lbl_views.pack(side="left", padx=(0, 8))

        self.lbl_duration = self._make_chip(stats_frame)
        self.lbl_duration.pack(side="left")

    def _make_chip(self, parent):
        lbl = ctk.CTkLabel(
            parent, text="",
            fg_color=theme.BG_COLOR,
            text_color=theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            padx=10, pady=4
        )
        return lbl

    def clear(self):
        self.pack_forget()
        self.lbl_thumb.configure(image=None)
        self.lbl_title.configure(text="")

    def show_info(self, info: VideoInfo):
        self.lbl_title.configure(text=info.title)
        self.lbl_channel.configure(text=info.uploader)
        self.lbl_views.configure(text=f"{info.view_count:,} views")
        self.lbl_duration.configure(text=info.duration_str)
        self.pack(fill="x", pady=16)

        if info.thumbnail_url:
            self._load_thumbnail(info.thumbnail_url)

    def _load_thumbnail(self, url: str):
        def fetch():
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    # Crop to 16:9
                    w, h = img.size
                    target_ratio = 16 / 9
                    if w / h > target_ratio:
                        new_w = int(h * target_ratio)
                        left = (w - new_w) / 2
                        img = img.crop((left, 0, left + new_w, h))
                    elif w / h < target_ratio:
                        new_h = int(w / target_ratio)
                        top = (h - new_h) / 2
                        img = img.crop((0, top, w, top + new_h))
                    
                    img.thumbnail((240, 135), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 112))
                    self.after(0, lambda: self.lbl_thumb.configure(image=ctk_img))
            except Exception:
                pass
        threading.Thread(target=fetch, daemon=True).start()
