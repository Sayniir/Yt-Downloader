"""
main.py
~~~~~~~
Entry point for Void Downloader Pro (CustomTkinter)
"""
import sys
from src.core import database, settings

def main():
    database.init_db()

    from src.ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
