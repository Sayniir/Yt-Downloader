"""history_panel.py — CustomTkinter Void Edition"""
import os
import subprocess
import customtkinter as ctk

from src.core import database
from src.ui import theme

class HistoryPanelWidget(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master=parent, fg_color="transparent")
        self._build()

    def _build(self):
        # Header Area
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 16))

        lbl = ctk.CTkLabel(hdr, text="Download History", font=ctk.CTkFont(size=22, weight="bold"), text_color=theme.TEXT_PRIMARY)
        lbl.pack(side="left")

        btn_refresh = ctk.CTkButton(
            hdr, text="Refresh", width=80, height=32,
            fg_color=theme.SURFACE_COLOR, hover_color=theme.BORDER_COLOR,
            border_color=theme.BORDER_COLOR, border_width=1,
            text_color=theme.TEXT_PRIMARY, command=self.load_data
        )
        btn_refresh.pack(side="right")

        btn_clear = ctk.CTkButton(
            hdr, text="Clear History", width=120, height=32,
            fg_color="transparent", hover_color=theme.HOVER_COLOR,
            border_color=theme.PRIMARY_COLOR, border_width=1,
            text_color=theme.PRIMARY_COLOR, command=self._clear_history
        )
        btn_clear.pack(side="right", padx=12)

        # Table Header
        th = ctk.CTkFrame(self, fg_color=theme.SURFACE_COLOR, corner_radius=0, height=40)
        th.pack(fill="x")
        th.pack_propagate(False)

        ctk.CTkLabel(th, text="Title", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(weight="bold")).place(x=16, y=8)
        ctk.CTkLabel(th, text="Format", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(weight="bold")).place(x=300, y=8)
        ctk.CTkLabel(th, text="Status", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(weight="bold")).place(x=400, y=8)
        ctk.CTkLabel(th, text="Date", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(weight="bold")).place(x=500, y=8)
        ctk.CTkLabel(th, text="Actions", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(weight="bold")).place(x=650, y=8)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=theme.BG_COLOR, corner_radius=0)
        self.scroll.pack(fill="both", expand=True)

        self.rows = []

    def load_data(self):
        for r in self.rows:
            r.destroy()
        self.rows.clear()

        records = database.get_history()
        for rec in records:
            # rec: id, title, url, quality, format, file_path, status, timestamp
            row = ctk.CTkFrame(self.scroll, fg_color=theme.SURFACE_COLOR, corner_radius=0, height=48)
            row.pack(fill="x", pady=(0, 2))
            row.pack_propagate(False)

            t_lbl = ctk.CTkLabel(row, text=rec[1], text_color=theme.TEXT_PRIMARY, anchor="w", width=270)
            t_lbl.place(x=16, y=10)

            f_lbl = ctk.CTkLabel(row, text=rec[4], text_color=theme.TEXT_SECONDARY, anchor="w", width=80)
            f_lbl.place(x=300, y=10)

            status_color = theme.SUCCESS_COLOR if rec[6] == "completed" else theme.ERROR_COLOR
            s_lbl = ctk.CTkLabel(row, text=rec[6].capitalize(), text_color=status_color, anchor="w", width=80)
            s_lbl.place(x=400, y=10)

            d_lbl = ctk.CTkLabel(row, text=rec[7][:16], text_color=theme.TEXT_MUTED, anchor="w", width=120)
            d_lbl.place(x=500, y=10)

            if rec[5] and rec[6] == "completed":
                btn = ctk.CTkButton(
                    row, text="Open", width=60, height=24,
                    fg_color="transparent", border_color=theme.BORDER_COLOR, border_width=1,
                    hover_color=theme.BORDER_COLOR, text_color=theme.TEXT_PRIMARY,
                    command=lambda p=rec[5]: self._open_file(p)
                )
                btn.place(x=650, y=12)

            self.rows.append(row)

    def _clear_history(self):
        database.clear_history()
        self.load_data()

    def _open_file(self, path: str):
        if not os.path.exists(path):
            return
        if os.path.isfile(path):
            # Select file in explorer
            subprocess.run(["explorer", "/select,", os.path.normpath(path)], shell=True)
        else:
            # Open dir
            subprocess.run(["explorer", os.path.normpath(path)], shell=True)
