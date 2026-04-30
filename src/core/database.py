"""
database.py
~~~~~~~~~~~
SQLite wrapper for download history.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from src.core import settings

DB_FILE = Path(settings.get("output_folder", str(Path.home() / "Downloads"))) / ".yt_history.db"
# Fallback to local app dir if output_folder is weird, but app dir is safer.
# Let's use the project root for safety and persistence across folder changes.
DB_FILE = Path(__file__).parent.parent.parent / "history.db"

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT,
                quality TEXT,
                format TEXT,
                file_path TEXT,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def add_record(title: str, url: str, quality: str, fmt: str, file_path: str, status: str = "completed") -> int:
    with _get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO history (title, url, quality, format, file_path, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, url, quality, fmt, file_path, status))
        conn.commit()
        return cur.lastrowid

def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        cur = conn.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

def clear_history():
    with _get_conn() as conn:
        conn.execute("DELETE FROM history")
        conn.commit()

# Initialize on import
init_db()
