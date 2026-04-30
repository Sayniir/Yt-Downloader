"""main_window.py — CustomTkinter Void Edition"""
import customtkinter as ctk

from src.core.url_validator import URLType
from src.workers.info_worker import start_info_worker
from src.core.queue_manager import QueueManager
from src.ui import theme

from src.ui.widgets.url_input import UrlInputWidget
from src.ui.widgets.video_info import VideoInfoWidget
from src.ui.widgets.format_selector import FormatSelectorWidget
from src.ui.widgets.playlist_panel import PlaylistPanelWidget
from src.ui.widgets.queue_panel import QueuePanelWidget
from src.ui.widgets.history_panel import HistoryPanelWidget
from src.ui.widgets.settings_panel import SettingsPanelWidget

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Void Downloader Pro")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(fg_color=theme.BG_COLOR)
        
        ctk.set_appearance_mode("dark")
        
        self.queue_manager = QueueManager()
        self._build_ui()
        self._select_tab("Downloader")

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=theme.SURFACE_COLOR, corner_radius=0, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        logo = ctk.CTkLabel(self.sidebar, text="VOID", font=ctk.CTkFont(size=24, weight="bold"), text_color=theme.PRIMARY_COLOR)
        logo.grid(row=0, column=0, padx=20, pady=(24, 32))

        self.btn_tab_dl = ctk.CTkButton(
            self.sidebar, text="Downloader", fg_color="transparent", text_color=theme.TEXT_PRIMARY,
            hover_color=theme.BORDER_COLOR, anchor="w", command=lambda: self._select_tab("Downloader")
        )
        self.btn_tab_dl.grid(row=1, column=0, padx=12, pady=4, sticky="ew")

        self.btn_tab_hist = ctk.CTkButton(
            self.sidebar, text="History", fg_color="transparent", text_color=theme.TEXT_PRIMARY,
            hover_color=theme.BORDER_COLOR, anchor="w", command=lambda: self._select_tab("History")
        )
        self.btn_tab_hist.grid(row=2, column=0, padx=12, pady=4, sticky="ew")

        self.btn_tab_set = ctk.CTkButton(
            self.sidebar, text="Settings", fg_color="transparent", text_color=theme.TEXT_PRIMARY,
            hover_color=theme.BORDER_COLOR, anchor="w", command=lambda: self._select_tab("Settings")
        )
        self.btn_tab_set.grid(row=3, column=0, padx=12, pady=4, sticky="ew")

        # 2. Main Content Container
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Build Tabs
        self.frames = {}
        
        # DOWNLOADING TAB
        f_dl = ctk.CTkFrame(self.content_area, fg_color="transparent")
        f_dl.grid(row=0, column=0, sticky="nsew")
        self._build_downloader_tab(f_dl)
        self.frames["Downloader"] = f_dl

        # HISTORY TAB
        f_hist = HistoryPanelWidget(self.content_area)
        f_hist.grid(row=0, column=0, sticky="nsew")
        self.frames["History"] = f_hist

        # SETTINGS TAB
        f_set = SettingsPanelWidget(self.content_area, self.queue_manager)
        f_set.grid(row=0, column=0, sticky="nsew")
        self.frames["Settings"] = f_set

    def _build_downloader_tab(self, parent):
        # Using pack for vertical stacking
        self.url_input = UrlInputWidget(parent, self._on_fetch_requested)
        self.url_input.pack(fill="x", pady=(0, 16))

        self.video_info = VideoInfoWidget(parent)
        self.playlist_panel = PlaylistPanelWidget(parent)
        
        self.format_selector = FormatSelectorWidget(parent, lambda: None)
        self.format_selector.pack(fill="x", pady=(0, 16))

        self.btn_download = ctk.CTkButton(
            parent, text="Add to Queue", height=44,
            fg_color=theme.PRIMARY_COLOR, hover_color=theme.HOVER_COLOR,
            text_color=theme.TEXT_PRIMARY, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_download_clicked, state="disabled"
        )
        self.btn_download.pack(fill="x", pady=(0, 24))

        self.queue_panel = QueuePanelWidget(parent, self.queue_manager)
        self.queue_panel.pack(fill="both", expand=True)

    def _select_tab(self, name):
        # Update sidebar buttons
        self.btn_tab_dl.configure(fg_color=theme.BORDER_COLOR if name=="Downloader" else "transparent")
        self.btn_tab_hist.configure(fg_color=theme.BORDER_COLOR if name=="History" else "transparent")
        self.btn_tab_set.configure(fg_color=theme.BORDER_COLOR if name=="Settings" else "transparent")

        # Show frame
        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.tkraise()
                if name == "History":
                    frame.load_data()
            else:
                pass # tkraise handles visibility in grid

    def _on_fetch_requested(self, url: str, url_type: URLType):
        self.video_info.clear()
        self.playlist_panel.clear()
        self.btn_download.configure(state="disabled")

        self._info_worker = start_info_worker(
            url=url,
            url_type=url_type,
            on_video_ready=lambda info: self.after(0, lambda: self._on_video_ready(info)),
            on_playlist_ready=lambda info: self.after(0, lambda: self._on_playlist_ready(info)),
            on_error=lambda msg: self.after(0, lambda: self._on_fetch_error(msg)),
            on_finished=lambda: self.after(0, self.url_input.reset_fetch_button)
        )

    def _on_video_ready(self, info):
        self.current_url_type = URLType.SINGLE
        self.current_info = info
        self.video_info.show_info(info)
        self.btn_download.configure(state="normal")

    def _on_playlist_ready(self, info):
        self.current_url_type = URLType.PLAYLIST
        self.current_info = info
        self.playlist_panel.show_playlist(info)
        self.btn_download.configure(state="normal")

    def _on_fetch_error(self, msg):
        self.url_input.lbl_error.configure(text=msg)
        self.url_input.lbl_error.pack(anchor="w", pady=(4, 0))

    def _on_download_clicked(self):
        opts = self.format_selector.get_options()

        if self.current_url_type == URLType.SINGLE:
            self.queue_manager.add_item(
                url=self.current_info.url,
                title=self.current_info.title,
                options=opts
            )
        else:
            urls = self.playlist_panel.get_selected_urls()
            if not urls:
                return
            for u in urls:
                self.queue_manager.add_item(
                    url=u,
                    title=f"Playlist item ({self.current_info.title})",
                    options=opts
                )
