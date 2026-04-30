# YouTube Downloader

A **free, 100% local, production-ready** YouTube video downloader with a premium dark-mode GUI.

Built with **Python + PyQt5 + yt-dlp** — no cloud, no subscriptions, no ads.

---

## Features

| Feature | Details |
|---------|---------|
| 🎬 Video download | 144p → 4K (if available), MP4 output |
| 🎵 Audio-only | Extracts to MP3 at 192kbps via FFmpeg |
| 📋 Playlist support | Download all or select individual items |
| 🌐 Subtitles | Downloads SRT/VTT in your chosen language |
| 📊 Real-time progress | Percentage, speed (MiB/s), ETA |
| 🔄 Auto-retry | Up to 3 retries with exponential backoff |
| 🏷️ Metadata embedding | Title, uploader, date written into file |
| 🖼️ Thumbnail preview | Loaded in background — never blocks UI |
| 🌙 Dark mode UI | Premium deep-navy / coral theme |
| 💾 Persistent settings | Output folder, quality, preferences saved |

---

## Requirements

- **Python 3.9+**
- **FFmpeg** (required for 720p+ and audio-only downloads)

### Install FFmpeg

| Platform | Command |
|----------|---------|
| Windows  | `winget install ffmpeg` or download from https://ffmpeg.org |
| macOS    | `brew install ffmpeg` |
| Linux    | `sudo apt install ffmpeg` |

> ⚠️ FFmpeg must be in your system `PATH`. Restart any terminal after installing.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourname/youtube-downloader.git
cd youtube-downloader

# 2. Create a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the App

```bash
python main.py
```

The GUI will open with a dark-mode window.

---

## Usage

1. **Paste** a YouTube URL into the input field (or click 📋 to paste from clipboard)
2. Click **Fetch Info** — the video thumbnail, title, and duration will appear
3. Choose your **quality** (144p → 4K) or enable **Audio only** for MP3
4. Toggle **Subtitles** if desired and pick a language
5. Select your **output folder** (defaults to `~/Downloads`)
6. Click **⬇ Download** — watch the progress bar fill up
7. When done, click **Open Folder** to view your file

### Playlist Downloads

When you paste a playlist URL, a table appears listing all videos.  
Use the checkboxes to select specific items, then click **Download**.

---

## Project Structure

```
Youtube-Downloader/
├── main.py                          # Entry point
├── requirements.txt
├── README.md
├── assets/
│   └── icon.png                     # App icon
└── src/
    ├── core/
    │   ├── url_validator.py         # URL validation
    │   ├── info_fetcher.py          # Metadata extraction (no download)
    │   ├── downloader.py            # yt-dlp download engine + retry
    │   └── settings.py              # Persistent user preferences
    ├── workers/
    │   ├── info_worker.py           # QThread: fetch metadata
    │   └── download_worker.py       # QThread: run downloads
    └── ui/
        ├── main_window.py           # Main application window
        ├── styles/
        │   └── dark_theme.qss       # Qt Style Sheet (dark mode)
        └── widgets/
            ├── url_input.py         # URL bar + paste + fetch button
            ├── video_info.py        # Thumbnail + metadata card
            ├── format_selector.py   # Quality / options panel
            ├── download_panel.py    # Progress bar + controls
            ├── playlist_panel.py    # Playlist item table
            └── settings_panel.py   # Output folder bar
```

---

## Packaging as .exe (Windows)

```bash
pip install pyinstaller

pyinstaller \
  --onefile \
  --windowed \
  --icon=assets/icon.png \
  --name="YouTubeDownloader" \
  --add-data="src/ui/styles/dark_theme.qss;src/ui/styles" \
  main.py
```

The standalone executable will be at `dist/YouTubeDownloader.exe`.  
Distribute it with FFmpeg (`ffmpeg.exe` in the same folder or in PATH).

---

## Configuration

User settings are saved to `~/.youtube_downloader/config.json`.  
They include: output folder, default quality, subtitle language, and embed toggles.

---

## Future Improvements

- [ ] **Web app**: Convert backend to FastAPI + React frontend
- [ ] **Download queue**: Concurrent downloads with queue management  
- [ ] **Download history**: SQLite database of all past downloads
- [ ] **Browser extension**: One-click download button on YouTube pages
- [ ] **Format conversion**: Built-in MP4 → MKV / AVI converter
- [ ] **Scheduled downloads**: Queue videos to download overnight

---

## Legal

This tool is for personal use only. Downloading copyrighted content may violate  
YouTube's Terms of Service. Always respect content creators' rights.

---

## License

MIT License — free to use, modify, and distribute.
