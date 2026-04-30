"""playlist_panel.py — CustomTkinter Void Edition"""
import customtkinter as ctk
from src.core.info_fetcher import PlaylistInfo
from src.ui import theme

class PlaylistPanelWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent, fg_color="transparent")
        self._build()
        self.pack_forget()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=theme.SURFACE_COLOR, corner_radius=8)
        hdr.pack(fill="x", pady=(0, 8))

        self.lbl_title = ctk.CTkLabel(
            hdr, text="", font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.lbl_title.pack(side="left", padx=16, pady=12)

        self.btn_select_all = ctk.CTkButton(
            hdr, text="Select All", width=100, height=32,
            fg_color=theme.BG_COLOR, hover_color=theme.BORDER_COLOR,
            text_color=theme.TEXT_PRIMARY, command=self._select_all
        )
        self.btn_select_all.pack(side="right", padx=16)

        # List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE_COLOR, height=200)
        self.scroll.pack(fill="both", expand=True)

        self._items = []
        self._info = None

    def _select_all(self):
        all_selected = all(chk.get() == 1 for _, chk in self._items)
        for _, chk in self._items:
            if all_selected:
                chk.deselect()
            else:
                chk.select()

    def show_playlist(self, info: PlaylistInfo):
        self._info = info
        self.lbl_title.configure(text=f"{info.title} ({len(info.entries)} videos)")
        
        # Clear existing
        for w, _ in self._items:
            w.destroy()
        self._items.clear()

        for idx, entry in enumerate(info.entries, 1):
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)

            chk = ctk.CTkCheckBox(
                row, text=f"{idx}. {entry.get('title', 'Unknown')}",
                text_color=theme.TEXT_PRIMARY,
                hover_color=theme.PRIMARY_COLOR,
                fg_color=theme.PRIMARY_COLOR,
                border_color=theme.BORDER_COLOR
            )
            chk.pack(side="left", padx=8)
            chk.select()
            self._items.append((row, chk))

        self.pack(fill="both", expand=True, pady=16)

    def clear(self):
        self.pack_forget()
        self._info = None

    def get_selected_urls(self) -> list[str]:
        if not self._info:
            return []
        
        urls = []
        for i, (_, chk) in enumerate(self._items):
            if chk.get() == 1:
                urls.append(self._info.entries[i].get("url", ""))
        return urls
