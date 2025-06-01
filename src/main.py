import tkinter as tk
from gui.main_window import MainWindow
from config.config_loader import ConfigLoader
from paths import ensure_config_exists, get_config_path
from core.project_sync_logic import save_tree_state  # Wichtig für Treeview-Status

# CAMsync - Hauptprogramm

try:
    from version import __version__
except ImportError:
    __version__ = "dev"

print(f"CAMsync Version: {__version__}")

def main():
    root = tk.Tk()

    # Konfigurationsdatei erzeugen, falls nötig
    ensure_config_exists()
    config_path = get_config_path()

    # Config laden
    config = ConfigLoader(config_path=config_path)

    # GUI starten
    app = MainWindow(root, config=config)

    # >>> HIER: Window-Closing-Handler setzen
    def on_closing():
        print("🔚 GUI wird geschlossen")
        if getattr(app, "tab_projectsync", None) and hasattr(app.tab_projectsync, "tree"):
            save_tree_state(app.tab_projectsync.tree)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)  # <- Wichtig!

    root.mainloop()

if __name__ == "__main__":
    main()