"""queue_panel.py — CustomTkinter Void Edition"""
import customtkinter as ctk
from src.core.queue_manager import QueueItem
from src.ui import theme

class QueuePanelWidget(ctk.CTkFrame):
    def __init__(self, parent, queue_manager):
        super().__init__(master=parent, fg_color="transparent")
        self.qm = queue_manager
        self.rows: dict[str, ctk.CTkFrame] = {}
        self._build()

        self.qm.on_item_added = self.add_item
        self.qm.on_item_updated = self.update_item

    def _build(self):
        lbl = ctk.CTkLabel(self, text="Download Queue", font=ctk.CTkFont(size=18, weight="bold"), text_color=theme.TEXT_PRIMARY)
        lbl.pack(anchor="w", pady=(0, 8))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE_COLOR, corner_radius=12)
        self.scroll.pack(fill="both", expand=True)

    def add_item(self, item: QueueItem):
        def _add():
            row = ctk.CTkFrame(self.scroll, fg_color=theme.BG_COLOR, corner_radius=8)
            row.pack(fill="x", pady=4, padx=4)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(12, 4))
            
            lbl_title = ctk.CTkLabel(top, text=item.title, font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w", wraplength=400)
            lbl_title.pack(side="left", expand=True, fill="x")

            btn_cancel = ctk.CTkButton(top, text="Cancel", width=60, height=24, fg_color="transparent", border_color=theme.BORDER_COLOR, border_width=1, text_color=theme.TEXT_SECONDARY, hover_color=theme.BORDER_COLOR, command=lambda: self.qm.cancel_item(item.id))
            btn_cancel.pack(side="right")

            mid = ctk.CTkFrame(row, fg_color="transparent")
            mid.pack(fill="x", padx=12, pady=(0, 8))

            prog = ctk.CTkProgressBar(mid, height=6, progress_color=theme.PRIMARY_COLOR, fg_color=theme.BORDER_COLOR)
            prog.pack(fill="x", pady=4)
            prog.set(0)

            bot = ctk.CTkFrame(row, fg_color="transparent")
            bot.pack(fill="x", padx=12, pady=(0, 12))

            lbl_status = ctk.CTkLabel(bot, text="Queued", text_color=theme.TEXT_SECONDARY, font=ctk.CTkFont(size=11))
            lbl_status.pack(side="left")

            self.rows[item.id] = {
                "frame": row,
                "title": lbl_title,
                "prog": prog,
                "status": lbl_status,
                "cancel": btn_cancel
            }
        self.after(0, _add)

    def update_item(self, item: QueueItem):
        def _update():
            if item.id not in self.rows:
                return
            r = self.rows[item.id]
            r["prog"].set(item.percent / 100.0)

            if item.status == "downloading":
                text = f"Downloading: {item.percent:.1f}%"
                if item.speed: text += f" @ {item.speed}"
                if item.eta: text += f" (ETA {item.eta})"
                r["status"].configure(text=text, text_color=theme.TEXT_SECONDARY)
            elif item.status == "finished":
                r["status"].configure(text="Finished", text_color=theme.SUCCESS_COLOR)
                r["prog"].configure(progress_color=theme.SUCCESS_COLOR)
                r["cancel"].configure(state="disabled")
            elif item.status == "error":
                r["status"].configure(text=f"Error: {item.error_msg}", text_color=theme.ERROR_COLOR)
                r["prog"].configure(progress_color=theme.ERROR_COLOR)
                r["cancel"].configure(state="disabled")
            elif item.status == "cancelled":
                r["status"].configure(text="Cancelled", text_color=theme.WARNING_COLOR)
                r["prog"].configure(progress_color=theme.WARNING_COLOR)
                r["cancel"].configure(state="disabled")

        self.after(0, _update)
