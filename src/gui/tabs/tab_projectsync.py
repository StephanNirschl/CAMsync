import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import getpass
from pathlib import Path
from tkinter import Toplevel, Label
import threading
from gui.loading_popup import LoadingPopup
import threading
from core.project_sync_logic import download_project
from gui.tooltip import ToolTip
from core.project_sync_logging import get_project_log_summary
from core.project_sync_logic import init_db, scan_and_sync_projects, download_project, upload_project, delete_db_project
from core.project_sync_logic import load_projects


class ProjectSyncTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.username = getpass.getuser()

        self.db_path = config.get("projects", "database_path", fallback=os.path.join(os.getenv("APPDATA"), "CAMsync", "project_sync.db"))
        self.local_dir = config.get("projects", "local_working_directory", fallback="C:/CAMsync/Local")
        init_db(self.db_path)


        # === Filterleiste ===
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(filter_frame, text="Kunde:").pack(side="left")
        self.kunden_filter = ttk.Entry(filter_frame, width=20)
        self.kunden_filter.pack(side="left", padx=(5, 20))

        ttk.Label(filter_frame, text="Jahr:").pack(side="left")
        self.jahr_filter = ttk.Entry(filter_frame, width=10)
        self.jahr_filter.pack(side="left", padx=(5, 20))

        ttk.Button(filter_frame, text="Filter anwenden", command=self.load_projects).pack(side="left")

        # === Container für Treeview und Scrollbar ===
        tree_container = ttk.Frame(self)
        tree_container.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tree = ttk.Treeview(tree_container, columns=("status", "user", "modified"), show="tree headings")
        self.tree.heading("#0", text="Projektstruktur")
        self.tree.heading("user", text="Bearbeiter")
        self.tree.heading("status", text="Status")
        self.tree.heading("modified", text="Geändert am")

        # Spaltenbreiten konfigurieren
        self.tree.column("#0", width=330, minwidth=200, stretch=True)        # Baumstruktur
        self.tree.column("user", width=70, anchor="center", stretch=True)
        self.tree.column("status", width=50, anchor="center", stretch=False)
        self.tree.column("modified", width=150, anchor="center", stretch=False)

        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.tree.tag_configure("locked", foreground="red", background="lightgray" ) # Rote Schrift für gesperrte Projekte
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<Motion>", self.on_mouse_hover)  # 🆕 Für Quickinfo Tooltip

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Download", command=lambda: start_download_with_loading(self))
        self.context_menu.add_command(label="Upload", command=lambda: start_upload_with_loading(self))
        self.context_menu.add_command(label="Aus DB löschen", command=lambda: delete_db_project(self))

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)
        ttk.Button(
            button_frame,
            text="Projekte scannen",
            command=lambda: scan_and_sync_projects(self, force=True),
        ).pack(side="left", padx=5)

        self.hover_popup = None  # 🆕 Tooltip-Fenster für Logging-Infos

        self.tooltip = ToolTip(self.tree)
        self.tree.bind("<Motion>", self.on_mouse_hover)
        self.tooltip_timer = None
        self.last_hover = None  # Zwischenspeicher

        self.load_projects()

        # ✅ Nach vollständiger GUI-Erstellung:
        scan_and_sync_projects(self, silent=True)


    def load_projects(self):
        from core.project_sync_logic import load_projects
        load_projects(self)

    def on_right_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        parent = self.tree.parent(item_id)
        if not parent or not self.tree.parent(parent):
            return  # Kein Projekt

        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        self.context_menu.post(event.x_root, event.y_root)

    def on_mouse_hover(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id or row_id == self.last_hover:
            return
        self.last_hover = row_id

        # Nur auf Projektebene (3. Ebene, also Kunde > Jahr > Projekt)
        parent = self.tree.parent(row_id)
        if not parent or not self.tree.parent(parent):
            self.tooltip.hide()
            if self.tooltip_timer:
                self.after_cancel(self.tooltip_timer)
                self.tooltip_timer = None
            return

        name = self.tree.item(row_id, "text")
        info = get_project_log_summary(name, self.db_path)
        self.tooltip.show(info, event.x_root, event.y_root)





def start_download_with_loading(tab):
    popup = LoadingPopup(tab, "Projekt wird heruntergeladen...")

    def threaded_download():
        try:
            download_project(tab, log_action=True)  # hier fest übergeben
        finally:
            popup.close()

    threading.Thread(target=threaded_download, daemon=True).start()


def start_upload_with_loading(tab):
    popup = LoadingPopup(tab, "Projekt wird hochgeladen...")

    def threaded_upload():
        try:
            upload_project(tab, log_action=True)  # hier fest übergeben
        finally:
            popup.close()

    threading.Thread(target=threaded_upload, daemon=True).start()