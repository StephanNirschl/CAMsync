import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from gui.tabs.tab_tools import ToolsTab
from gui.popup_centered import show_centered_popup

# core/version.py einbinden
from core.version import __version__

class MainWindow:
    def __init__(self, root, config):

        self.root = root

        try:
            base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
            icon_path = os.path.join(base_dir, "src/assets/camsync_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                #print(f"[INFO] Fenster-Icon gesetzt: {icon_path}")
            else:
                print(f"[WARN] Icon-Datei nicht gefunden: {icon_path}")
        except Exception as e:
            print(f"[WARN] Fenster-Icon konnte nicht gesetzt werden: {e}")


        # Setzen des Fenstertitels:
        self.root.title(f"CAMsync {__version__}")

        self.root.geometry("1000x1000")
        self.root.minsize(width=1000, height=600)  # Mindestgröße


        self.config = config  # übergebene ConfigLoader-Instanz
        self.config_path = config.config_filename
        self.project_sync_enabled = self.config.get("optionsproject", "enable_project_sync", fallback="0") in ("1", "true", "yes", "on")
        self.cleanup_enabled = self.config.get("cleanup", "enable_cleanup", fallback="1") in ("1", "true", "yes", "on")



        self.apply_theme(self.config.get("gui", "theme", fallback="light"))
        self.input_fields = {}

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.available_themes = ["light", "dark"]

        print("DEBUG config:", self.config.get("optionsproject", "enable_project_sync", fallback="NOT FOUND"))
        
        self.create_tabs()


    

    def create_tabs(self):
        
        
        if self.config.get("optionsproject", "enable_project_sync", fallback="0") in ("1", "true", "yes", "on"):
            from gui.tabs.tab_projectsync import ProjectSyncTab
            self.tab_projectsync = ProjectSyncTab(self.notebook, config=self.config)
            self.notebook.add(self.tab_projectsync, text="Projects")
        else:
            self.tab_projectsync = None


        tools_tab = ToolsTab(self.notebook, config=self.config)
        self.notebook.add(tools_tab, text="ToolDB")


        if self.cleanup_enabled:
            from gui.tabs.tab_cleanup import CleanupTab
            self.tab_cleanup = CleanupTab(self.notebook, config=self.config)
            self.notebook.add(self.tab_cleanup, text="Projects Clean Up")
        else:
            self.tab_cleanup = None


        self.create_settings_tab()


    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Settings")

        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

        self.settings_canvas = tk.Canvas(tab, bg=self.get_theme_bg())
        canvas = self.settings_canvas
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("frame", width=e.width))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="frame")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.input_fields = {}
        self.active_group = None
        self.groups = []
        current_row = 0

        def create_group(title, sections):
            nonlocal current_row

            header_frame = ttk.Frame(scrollable_frame)
            content_frame = ttk.Frame(scrollable_frame)
            arrow = tk.StringVar(value="▶")

            def place_save_button():
                last_row = scrollable_frame.grid_size()[1]
                if hasattr(self, "save_button"):
                    self.save_button.grid_forget()
                self.save_button = ttk.Button(
                    scrollable_frame,
                    text="Einstellungen speichern",
                    command=self.save_settings
                )
                self.save_button.grid(row=last_row, column=0, columnspan=2, pady=20, padx=20, sticky="ew")
                scrollable_frame.grid_rowconfigure(last_row + 1, weight=1)

            def toggle():
                for group in self.groups:
                    group["content"].grid_remove()
                    group["arrow"].set("▶")

                if self.active_group == content_frame:
                    self.active_group = None
                    return

                content_frame.grid()
                arrow.set("▼")
                self.active_group = content_frame

            ttk.Button(header_frame, textvariable=arrow, width=2, command=toggle).grid(row=0, column=0, sticky="w")
            ttk.Label(header_frame, text=title, font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w", padx=5)
            header_frame.grid(row=current_row, column=0, columnspan=2, sticky="w", pady=(15, 5))
            current_row += 1

            content_row = 0
            for section in sections:
                if section not in self.config.config.sections():
                    continue
                for key, value in self.config.get_section(section).items():
                    ttk.Label(content_frame, text=key).grid(row=content_row, column=0, sticky="w", padx=10)

                    if value in ("0", "1", "true", "false", "yes", "no"):
                        dtype = bool
                        var = tk.BooleanVar(value=value.lower() in ("1", "true", "yes", "on"))
                        widget = ttk.Checkbutton(content_frame, variable=var)
                    elif value.isdigit():
                        dtype = int
                        var = tk.StringVar(value=value)
                        widget = ttk.Entry(content_frame, textvariable=var, width=120)
                    elif section == "gui" and key == "theme":
                        dtype = str
                        var = tk.StringVar(value=value)
                        themes = self.available_themes if hasattr(self, "available_themes") else list(ttk.Style().theme_names())
                        if value not in themes:
                            themes.append(value)
                        widget = ttk.Combobox(content_frame, textvariable=var, values=themes, state="readonly", width=20)
                    else:
                        dtype = str
                        var = tk.StringVar(value=value)
                        widget = ttk.Entry(content_frame, textvariable=var, width=120)

                    widget.grid(row=content_row, column=1, padx=10, pady=2, sticky="w")
                    self.input_fields[(section, key)] = (var, dtype)
                    content_row += 1

                    place_save_button()

            content_frame.grid_columnconfigure(0, weight=0)
            content_frame.grid_columnconfigure(1, weight=1)
            content_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
            content_frame.grid_remove()

            self.groups.append({
                "header": header_frame,
                "content": content_frame,
                "arrow": arrow
            })

            current_row += 1

        create_group("Tools", ["tools", "optionstools"])
        create_group("Projects", ["projects", "optionsproject"])
        create_group("Projects CLEAN UP", ["cleanup"])
        create_group("GUI", ["gui"])
        create_group("Logs", ["logging"])
        create_group("Allgemein", ["scheduler", "users"])

        scrollable_frame.grid_columnconfigure(0, weight=0)
        scrollable_frame.grid_columnconfigure(1, weight=1)


        # === Status: Konfiguration und Logging ===
        status_text = f"🟢 Konfiguration geladen: {self.config.config_filename}"
        log_dir = self.config.get("logging", "logfile", fallback="logs/default.log")
        status_log = f"📄 Log-Dateien: {os.path.dirname(log_dir)}"

        ttk.Label(scrollable_frame, text=status_text, foreground="green").grid(
            row=current_row, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 0)
        )
        current_row += 1

        ttk.Label(scrollable_frame, text=status_log, foreground="green").grid(
            row=current_row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10)
        )
        current_row += 1

        # === Lizenzanzeige mit Button ===
        ttk.Separator(scrollable_frame).grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=10)
        current_row += 1

        ttk.Label(
            scrollable_frame,
            text="🔗 Lizenz: MIT License – siehe LICENSE-Datei im Projektverzeichnis.",
            foreground="gray",
            font=("Arial", 9)
        ).grid(row=current_row, column=0, sticky="w", padx=10, pady=(0, 5))

        ttk.Button(
            scrollable_frame,
            text="LICENSE anzeigen",
            command=self.open_license
        ).grid(row=current_row, column=1, sticky="e", padx=10, pady=(0, 5))

        current_row += 1

    def save_settings(self):
        all_input_fields = dict(self.input_fields)
        changes = []  # Liste für Änderungen
        settings_saved = False

        for (section, key), (var, dtype) in all_input_fields.items():
            try:
                if dtype == int:
                    value = str(int(var.get()))
                elif dtype == bool:
                    value = "1" if var.get() else "0"
                else:
                    value = var.get()
            except ValueError:
                messagebox.showerror("Fehler", f"Ungültiger Wert für {section}.{key}: erwartet {dtype.__name__}")
                return

            old_value = self.config.get(section, key, fallback=None)
            if value != old_value:
                self.config.config.set(section, key, value)
                settings_saved = True

                if (section, key) == ("gui", "theme"):
                    self.apply_theme(value)

        # Datei schreiben
        with open(self.config_path, "w") as configfile:
            self.config.config.write(configfile)

        # === Tabs prüfen und ggf. aktualisieren ===
        new_project_status = self.config.get("optionsproject", "enable_project_sync", fallback="0") in ("1", "true", "yes", "on")
        if new_project_status != self.project_sync_enabled:
            self.project_sync_enabled = new_project_status
            if new_project_status:
                from gui.tabs.tab_projectsync import ProjectSyncTab
                self.tab_projectsync = ProjectSyncTab(self.notebook, config=self.config)
                self.notebook.insert(0, self.tab_projectsync, text="Projects")
                changes.append("✅ 'Projects'-Tab wurde aktiviert.")
            else:
                if self.tab_projectsync:
                    index = self.notebook.index(self.tab_projectsync)
                    self.notebook.forget(index)
                    self.tab_projectsync = None
                changes.append("🗑 'Projects'-Tab wurde deaktiviert.")

        new_cleanup_status = self.config.get("cleanup", "enable_cleanup", fallback="1") in ("1", "true", "yes", "on")
        if new_cleanup_status != self.cleanup_enabled:
            self.cleanup_enabled = new_cleanup_status
            if new_cleanup_status:
                from gui.tabs.tab_cleanup import CleanupTab
                self.tab_cleanup = CleanupTab(self.notebook, config=self.config)
                settings_index = self.notebook.index("end") - 1
                self.notebook.insert(settings_index, self.tab_cleanup, text="Projects Clean Up")
                changes.append("✅ 'Projects Clean Up'-Tab wurde aktiviert.")
            else:
                if self.tab_cleanup:
                    index = self.notebook.index(self.tab_cleanup)
                    self.notebook.forget(index)
                    self.tab_cleanup = None
                changes.append("🗑 'Projects Clean Up'-Tab wurde deaktiviert.")

        # === Popup-Ausgabe anpassen ===
        if changes and settings_saved:
            msg = "💾 Einstellungen gespeichert\n" + "\n".join(changes)
            show_centered_popup(self.root, "Einstellungen übernommen", msg)
        elif changes:
            msg = "\n".join(changes)
            show_centered_popup(self.root, "Tabs aktualisiert", msg)
        elif settings_saved:
            show_centered_popup(self.root, "Gespeichert", "Alle Einstellungen wurden gespeichert.")
        else:
            show_centered_popup(self.root, "Keine Änderung", "Es wurden keine Änderungen vorgenommen.")

    def apply_theme(self, theme_name):
        style = ttk.Style()
        style.theme_use("default")

        if theme_name == "dark":
            self.root.configure(bg="#2e2e2e")
            style.configure("TFrame", background="#2e2e2e")
            style.configure("TLabel", background="#2e2e2e", foreground="white")
            style.configure("TNotebook", background="#2e2e2e")
            style.configure("TNotebook.Tab", background="#444", foreground="white")
            style.configure("TEntry", fieldbackground="#555", foreground="white")
            style.configure("TButton", background="#444", foreground="white")
            style.configure("TCheckbutton", background="#2e2e2e", foreground="white")
        else:
            self.root.configure(bg="SystemButtonFace")
            style.configure("TFrame", background="SystemButtonFace")
            style.configure("TLabel", background="SystemButtonFace", foreground="black")
            style.configure("TNotebook", background="SystemButtonFace")
            style.configure("TNotebook.Tab", background="SystemButtonFace", foreground="black")
            style.configure("TEntry", fieldbackground="white", foreground="black")
            style.configure("TButton", background="SystemButtonFace", foreground="black")
            style.configure("TCheckbutton", background="SystemButtonFace", foreground="black")

        if hasattr(self, "settings_canvas"):
            self.settings_canvas.configure(bg=self.get_theme_bg())

    def get_theme_bg(self):
        theme = self.config.get("gui", "theme", fallback="light").lower()
        return "#2e2e2e" if theme == "dark" else "SystemButtonFace"
    
    def open_license(self):

        from tkinter import messagebox

        if getattr(sys, 'frozen', False):  # Wenn als EXE gepackt
            base_path = sys._MEIPASS
        else:  # IDE-Modus
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        license_path = os.path.join(base_path, "docs", "LICENSE")

        if os.path.exists(license_path):
            os.startfile(license_path)
        else:
            messagebox.showwarning("Nicht gefunden", f"LICENSE-Datei nicht gefunden:\n{license_path}")

