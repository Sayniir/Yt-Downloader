"""url_input.py — CustomTkinter Void Edition"""
import customtkinter as ctk
from src.core.url_validator import validate_url, URLType
from src.ui import theme

class UrlInputWidget(ctk.CTkFrame):
    def __init__(self, parent, on_fetch_requested):
        super().__init__(master=parent, fg_color="transparent")
        self.on_fetch_requested = on_fetch_requested
        self._build()

    def _build(self):
        lbl = ctk.CTkLabel(
            self, text="Paste YouTube Link",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        )
        lbl.pack(anchor="w", pady=(0, 16))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        self.entry = ctk.CTkEntry(
            row, height=44,
            placeholder_text="https://www.youtube.com/watch?v=...",
            fg_color=theme.SURFACE_COLOR,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.TEXT_PRIMARY,
            placeholder_text_color=theme.TEXT_MUTED,
            font=ctk.CTkFont(size=14)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self._on_fetch())

        self.btn_fetch = ctk.CTkButton(
            row, text="Fetch Info", height=44, width=120,
            fg_color=theme.SURFACE_COLOR,
            hover_color=theme.BORDER_COLOR,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_fetch
        )
        self.btn_fetch.pack(side="right")

        self.lbl_error = ctk.CTkLabel(
            self, text="", text_color=theme.ERROR_COLOR,
            font=ctk.CTkFont(size=12)
        )
        self.lbl_error.pack(anchor="w", pady=(4, 0))
        self.lbl_error.pack_forget()

    def _on_fetch(self):
        url = self.entry.get().strip()
        if not url:
            return

        res = validate_url(url)
        if not res.is_valid:
            self.lbl_error.configure(text=res.message)
            self.lbl_error.pack(anchor="w", pady=(4, 0))
            return

        self.lbl_error.pack_forget()
        self.btn_fetch.configure(state="disabled", text="Fetching...")
        self.on_fetch_requested(url, res.url_type)

    def reset_fetch_button(self):
        self.btn_fetch.configure(state="normal", text="Fetch Info")
