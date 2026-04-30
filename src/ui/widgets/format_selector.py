"""format_selector.py — CustomTkinter Void Edition"""
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog

from src.core import downloader as dl
from src.core import settings
from src.ui import theme

class FormatSelectorWidget(ctk.CTkFrame):
    def __init__(self, parent, on_options_changed):
        super().__init__(master=parent, fg_color="transparent")
        self.on_options_changed = on_options_changed
        self._build()
        self._load()

    def _build(self):
        # 2x3 Grid
        self.grid_columnconfigure((0, 1, 2), weight=1, pad=16)
        self.grid_rowconfigure((0, 1), pad=16)

        # Quality
        lq = ctk.CTkLabel(self, text="Quality", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        lq.grid(row=0, column=0, sticky="sw")
        self.combo_quality = ctk.CTkComboBox(
            self, values=list(dl.QUALITY_PRESETS.keys()),
            fg_color=theme.SURFACE_COLOR, border_color=theme.BORDER_COLOR,
            button_color=theme.SURFACE_COLOR, button_hover_color=theme.BORDER_COLOR,
            dropdown_fg_color=theme.SURFACE_COLOR, dropdown_hover_color=theme.BORDER_COLOR,
            dropdown_text_color=theme.TEXT_PRIMARY, text_color=theme.TEXT_PRIMARY,
            state="readonly", command=self._changed
        )
        self.combo_quality.grid(row=0, column=0, sticky="sew", pady=(24, 0))

        # Format
        lf = ctk.CTkLabel(self, text="Format", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        lf.grid(row=0, column=1, sticky="sw")
        self.combo_format = ctk.CTkComboBox(
            self, values=["Original", "MP4", "MKV", "AVI", "WEBM", "FLV"],
            fg_color=theme.SURFACE_COLOR, border_color=theme.BORDER_COLOR,
            button_color=theme.SURFACE_COLOR, button_hover_color=theme.BORDER_COLOR,
            dropdown_fg_color=theme.SURFACE_COLOR, dropdown_hover_color=theme.BORDER_COLOR,
            dropdown_text_color=theme.TEXT_PRIMARY, text_color=theme.TEXT_PRIMARY,
            state="readonly", command=self._changed
        )
        self.combo_format.grid(row=0, column=1, sticky="sew", pady=(24, 0))

        # Output Folder
        lo = ctk.CTkLabel(self, text="Save to", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        lo.grid(row=0, column=2, sticky="sw")
        out_frame = ctk.CTkFrame(self, fg_color="transparent")
        out_frame.grid(row=0, column=2, sticky="sew", pady=(24, 0))
        self.field_output = ctk.CTkEntry(
            out_frame, fg_color=theme.SURFACE_COLOR, border_color=theme.BORDER_COLOR,
            text_color=theme.TEXT_PRIMARY, state="readonly"
        )
        self.field_output.pack(side="left", fill="x", expand=True, padx=(0, 8))
        btn_browse = ctk.CTkButton(
            out_frame, text="...", width=40,
            fg_color=theme.SURFACE_COLOR, hover_color=theme.BORDER_COLOR,
            border_color=theme.BORDER_COLOR, border_width=1,
            text_color=theme.TEXT_PRIMARY, command=self._browse
        )
        btn_browse.pack(side="right")

        # Switches (Audio, Subs, Meta, Thumb)
        s_frame = ctk.CTkFrame(self, fg_color="transparent")
        s_frame.grid(row=1, column=0, columnspan=3, sticky="w")
        s_frame.grid_columnconfigure((0,1,2,3), pad=24)

        self.chk_audio = ctk.CTkSwitch(
            s_frame, text="Audio Only", progress_color=theme.PRIMARY_COLOR,
            command=self._audio_toggled
        )
        self.chk_audio.grid(row=0, column=0, sticky="w")

        self.chk_subs = ctk.CTkSwitch(
            s_frame, text="Subtitles", progress_color=theme.PRIMARY_COLOR,
            command=self._subs_toggled
        )
        self.chk_subs.grid(row=0, column=1, sticky="w")

        self.combo_lang = ctk.CTkComboBox(
            s_frame, values=["en", "fr", "es", "de", "it", "ja", "ko", "pt", "ru"],
            width=60, fg_color=theme.SURFACE_COLOR, border_color=theme.BORDER_COLOR,
            button_color=theme.SURFACE_COLOR, button_hover_color=theme.BORDER_COLOR,
            dropdown_fg_color=theme.SURFACE_COLOR, dropdown_hover_color=theme.BORDER_COLOR,
            dropdown_text_color=theme.TEXT_PRIMARY, text_color=theme.TEXT_PRIMARY,
            state="disabled", command=self._changed
        )
        self.combo_lang.grid(row=0, column=2, sticky="w")
        self.combo_lang.set("en")

        self.chk_meta = ctk.CTkSwitch(
            s_frame, text="Metadata", progress_color=theme.PRIMARY_COLOR,
            command=self._changed
        )
        self.chk_meta.grid(row=0, column=3, sticky="w")

        self.chk_thumb = ctk.CTkSwitch(
            s_frame, text="Thumbnail", progress_color=theme.PRIMARY_COLOR,
            command=self._changed
        )
        self.chk_thumb.grid(row=0, column=4, sticky="w")

    def _load(self):
        c = settings.get_all()
        self.combo_quality.set(c.get("default_quality", "Best (auto)"))
        self.combo_format.set(c.get("target_format", "Original"))
        if c.get("audio_only", False):
            self.chk_audio.select()
            self._audio_toggled()
        if c.get("download_subtitles", False): self.chk_subs.select()
        if c.get("embed_metadata", True): self.chk_meta.select()
        if c.get("embed_thumbnail", False): self.chk_thumb.select()
        
        f = c.get("output_folder", str(Path.home() / "Downloads"))
        self.set_output_folder(f)

    def _changed(self, *_):
        settings.update({
            "default_quality": self.combo_quality.get(),
            "target_format": self.combo_format.get(),
            "embed_metadata": self.chk_meta.get() == 1,
            "embed_thumbnail": self.chk_thumb.get() == 1,
            "audio_only": self.chk_audio.get() == 1,
            "download_subtitles": self.chk_subs.get() == 1,
            "subtitle_language": self.combo_lang.get(),
        })
        self.on_options_changed()

    def _subs_toggled(self):
        state = "readonly" if self.chk_subs.get() == 1 else "disabled"
        self.combo_lang.configure(state=state)
        self._changed()

    def _audio_toggled(self):
        on = self.chk_audio.get() == 1
        state = "disabled" if on else "readonly"
        self.combo_quality.configure(state=state)
        self.combo_format.configure(state=state)
        self._changed()

    def _browse(self):
        cur = self.field_output.get()
        f = filedialog.askdirectory(initialdir=cur, title="Select Output Folder")
        if f:
            self.set_output_folder(f)
            settings.set("output_folder", f)
            self.on_options_changed()

    def set_output_folder(self, folder: str):
        self.field_output.configure(state="normal")
        self.field_output.delete(0, "end")
        self.field_output.insert(0, folder)
        self.field_output.configure(state="readonly")

    def get_options(self) -> dict:
        return {
            "quality": self.combo_quality.get(),
            "audio_only": self.chk_audio.get() == 1,
            "download_subs": self.chk_subs.get() == 1,
            "sub_lang": self.combo_lang.get(),
            "output_folder": self.field_output.get(),
            "embed_metadata": self.chk_meta.get() == 1,
            "embed_thumbnail": self.chk_thumb.get() == 1,
            "target_format": self.combo_format.get(),
        }
