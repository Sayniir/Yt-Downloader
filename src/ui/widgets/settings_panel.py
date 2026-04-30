"""settings_panel.py — CustomTkinter Void Edition"""
import customtkinter as ctk

from src.core import settings
from src.ui import theme

class SettingsPanelWidget(ctk.CTkFrame):
    def __init__(self, parent, queue_manager):
        super().__init__(master=parent, fg_color="transparent")
        self.qm = queue_manager
        self._build()
        self._load()

    def _build(self):
        lbl = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=22, weight="bold"), text_color=theme.TEXT_PRIMARY)
        lbl.pack(anchor="w", pady=(0, 24))

        frame = ctk.CTkFrame(self, fg_color=theme.SURFACE_COLOR, corner_radius=12)
        frame.pack(fill="x")
        
        lbl_conc = ctk.CTkLabel(frame, text="Concurrent Downloads Limit", font=ctk.CTkFont(size=14), text_color=theme.TEXT_PRIMARY)
        lbl_conc.grid(row=0, column=0, padx=16, pady=24, sticky="w")

        self.slider = ctk.CTkSlider(
            frame, from_=1, to=5, number_of_steps=4,
            progress_color=theme.PRIMARY_COLOR, button_color=theme.PRIMARY_COLOR, button_hover_color=theme.HOVER_COLOR,
            command=self._on_slider
        )
        self.slider.grid(row=0, column=1, padx=16, pady=24, sticky="ew")

        self.lbl_val = ctk.CTkLabel(frame, text="2", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme.TEXT_PRIMARY)
        self.lbl_val.grid(row=0, column=2, padx=16, pady=24, sticky="e")

        frame.grid_columnconfigure(1, weight=1)

    def _load(self):
        c = settings.get("max_concurrent_downloads", 2)
        self.slider.set(c)
        self.lbl_val.configure(text=str(int(c)))
        self.qm.set_concurrency(int(c))

    def _on_slider(self, val):
        v = int(val)
        self.lbl_val.configure(text=str(v))
        settings.set("max_concurrent_downloads", v)
        self.qm.set_concurrency(v)
