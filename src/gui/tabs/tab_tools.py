import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
import os
import tkinter.messagebox as messagebox
from core.tool_report import export_all_status_tools_to_excel
from config.config_loader import ConfigLoader

from core import depot_sync
from core import tool_rework


class ToolsTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # Status für Tooldatabase Rework
        self.rework_thread = None
        self.rework_stop_event = threading.Event()

        # Layout aufteilen
        self.columnconfigure(0, weight=1)
        self.rowconfigure(7, weight=0)

        # --- OBERER BEREICH: Tooldatabase Rework ---
        # Zeile 1 Label
        ttk.Label(self, text=" ").grid(row=0, column=0, sticky="w", padx=10, pady=(0, 0))

        #Zeile 2 Buttons
        rework_button_frame = ttk.Frame(self)
        rework_button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 0))
        rework_button_frame.columnconfigure(0, weight=1)
        rework_button_frame.columnconfigure(1, weight=1)
        rework_button_frame.columnconfigure(2, weight=1)

        self.start_button = ttk.Button(rework_button_frame, text="ToolDatabase Rework starten", command=self.start_tool_rework)
        self.start_button.grid(row=0, column=0, sticky="w")

        self.clear_rework_button = ttk.Button(rework_button_frame, text="🧹 Log leeren", command=self.clear_rework_output)
        self.clear_rework_button.grid(row=0, column=2, sticky="e", padx=(0, 80))

        self.stop_button = ttk.Button(rework_button_frame, text="Stop", command=self.stop_tool_rework, state="disabled")
        self.stop_button.grid(row=0, column=2, sticky="e", padx=(0, 5))

        # Zeile 3 labels

        self.status_label = ttk.Label(self, text="↓ Logbereich Database-Rework ↓" , font=("Segoe UI", 9, "bold"))
        self.status_label.grid(row=2, column=0, padx=(0, 0), pady=(5, 0))

        self.status_label = ttk.Label(self, text="🕒 Nicht gestartet" , font=("Segoe UI", 9))
        self.status_label.grid(row=2, column=0, sticky="w", padx=(35, 0), pady=(5, 0))
        
  
        # --- PANED WINDOW für dynamische Größenanpassung ---
        paned = ttk.PanedWindow(self, orient="vertical")
        paned.grid(row=3, column=0, rowspan=2, sticky="nsew", padx=10, pady=5)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)

        # Gemeinsamer Frame für Rework-Ausgabe + Beschriftung
        top_frame = ttk.Frame(paned)
        top_frame.columnconfigure(0, weight=1)
        top_frame.rowconfigure(0, weight=3)
        top_frame.rowconfigure(1, weight=0)

        # Frame für Rework-Ausgabe
        rework_frame = ttk.Frame(top_frame)
        rework_frame.grid(row=0, column=0, sticky="nsew")
        rework_frame.columnconfigure(0, weight=1)
        rework_frame.rowconfigure(0, weight=1)

        self.output_rework = tk.Text(rework_frame, state="disabled", wrap="word")
        rework_scroll = ttk.Scrollbar(rework_frame, orient="vertical", command=self.output_rework.yview)
        self.output_rework.configure(yscrollcommand=rework_scroll.set)

        self.output_rework.grid(row=0, column=0, sticky="nsew")
        rework_scroll.grid(row=0, column=1, sticky="ns")

        # Frame für Bereichsbeschriftung (mittig)
        label_frame = ttk.Frame(top_frame)
        label_frame.grid(row=1, column=0, sticky="ew")
        label_frame.columnconfigure(0, weight=1)

        ttk.Label(label_frame, text="↓ Logereich für Wartung ↓", anchor="center", font=("Segoe UI", 9, "bold")).pack(fill="x", pady=(0, 5))

        # Frame für Depot-Ausgabe (unten)
        depot_frame = ttk.Frame(paned)
        depot_frame.columnconfigure(0, weight=1)
        depot_frame.rowconfigure(0, weight=1)

        self.output_depot = tk.Text(depot_frame, state="disabled", wrap="word")
        depot_scroll = ttk.Scrollbar(depot_frame, orient="vertical", command=self.output_depot.yview)
        self.output_depot.configure(yscrollcommand=depot_scroll.set)

        self.output_depot.grid(row=0, column=0, sticky="nsew")
        depot_scroll.grid(row=0, column=1, sticky="ns")

        # Frames zum PanedWindow hinzufügen
        paned.add(top_frame, weight=3)
        paned.add(depot_frame, weight=2)

        # --- UNTERER BUTTON-BEREICH ---
        ttk.Separator(self).grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 0))


        button_frame = ttk.Frame(self)
        button_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=5)

        # Gleichmäßige Breite für Buttonspalten
        for i in [0, 2, 4, 6, 8]:
            button_frame.columnconfigure(i, weight=1)
        # Keine Breite für Separatoren (sie bleiben schmal)
        for i in [1, 3, 5, 7]:
            button_frame.columnconfigure(i, minsize=5)  # Optional für etwas Sichtbarkeit

        button_frame.rowconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)

        # Reihe 0 Buttons
        ttk.Button(button_frame, text="").grid(row=0, column=0, sticky="ew", padx=20, pady=2)
        ttk.Separator(button_frame, orient="vertical").grid(row=0, column=1, rowspan=2, sticky="ns")
        self.sync_button = ttk.Button(button_frame, text="Depot Sync starten", command=self.run_depot_sync)
        self.sync_button.grid(row=0, column=2, padx=20, pady=2, sticky="ew")
        ttk.Separator(button_frame, orient="vertical").grid(row=0, column=3, rowspan=2, sticky="ns")
        ttk.Button(button_frame, text="").grid(row=0, column=4, sticky="ew", padx=20, pady=2)
        ttk.Separator(button_frame, orient="vertical").grid(row=0, column=5, rowspan=2, sticky="ns")
        self.report_button = ttk.Button(button_frame, text="Report")
        self.report_button.grid(row=0, column=6, sticky="ew", padx=20, pady=2)
        self.report_button.config(command=self.run_tool_report_all)
        ttk.Separator(button_frame, orient="vertical").grid(row=0, column=7, rowspan=2, sticky="ns")
        self.clear_depot_button = ttk.Button(button_frame, text="🧹 Log leeren", command=self.clear_depot_output)
        self.clear_depot_button.grid(row=0, column=8, sticky="ew", padx=20, pady=2)

        # Reihe 1 Buttons (optional)
        ttk.Button(button_frame, text="").grid(row=1, column=0, sticky="ew", padx=20, pady=2)
        self.open_folder_button = ttk.Button(button_frame, text="🗂 Depot -> Excel config ", command=self.open_defaulttools_folder)
        self.open_folder_button.grid(row=1, column=2, sticky="ew", padx=20, pady=2)
        ttk.Button(button_frame, text="").grid(row=1, column=4, sticky="ew", padx=20, pady=2)
        ttk.Button(button_frame, text="").grid(row=1, column=6, sticky="ew", padx=20, pady=2)
        ttk.Button(button_frame, text="").grid(row=1, column=8, sticky="ew", padx=20, pady=2)




        button_frame = ttk.Frame(self)
        button_frame.grid(row=7, column=0, sticky="ew", padx=10, pady=(5, 5))

    # === TOOL-REWORK (oben) ===

    def start_tool_rework(self):
        if self.rework_thread and self.rework_thread.is_alive():
            return  # schon aktiv

        self._write_to_rework_output("▶️ Tool-Rework gestartet.")
        self.rework_stop_event.clear()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        def run_with_wrapped_callback():
            def callback(text):
                timestamp = datetime.now().strftime("%H:%M:%S")
                safe_text = text.replace('%', '%%')
                self.output_rework.after(0, lambda: self._write_to_rework_output(f"[{timestamp}] {safe_text}"))

            try:
                tool_rework.start_tool_rework_loop(callback, self.rework_stop_event, self.config.config_filename)
            except Exception as e:
                self.output_rework.after(0, lambda: self._write_to_rework_output(f"❌ Fehler im Rework-Thread: {str(e)}"))
                self.output_rework.after(0, lambda: self._update_status("🛑 Fehlgeschlagen"))
                self.output_rework.after(0, lambda: self.start_button.config(state="normal"))
                self.output_rework.after(0, lambda: self.stop_button.config(state="disabled"))

        self.rework_thread = threading.Thread(
            target=run_with_wrapped_callback,
            daemon=True
        )
        self.rework_thread.start()
        self._update_status("✅ Läuft...")

    def stop_tool_rework(self):
        if self.rework_thread and self.rework_thread.is_alive():
            self.rework_stop_event.set()
            self._update_status("🛑 Stopp angefordert.")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def _write_to_rework_output(self, text):
        self.output_rework.config(state="normal")
        self.output_rework.insert(tk.END, f"{text}\n")
        self.output_rework.see(tk.END)
        self.output_rework.config(state="disabled")

    def _update_status(self, text):
        self.status_label.config(text=text)

    # === DEPOT-SYNC (unten) ===

    def run_depot_sync(self):
        self.sync_button.config(state="disabled")
        self._write_to_depot_output("⏳ Depot-Sync wird gestartet...")

        thread = threading.Thread(target=self._run_depot_sync_thread, daemon=True)
        thread.start()

    def _run_depot_sync_thread(self):
        try:
            result = depot_sync.run_depot_sync(self.config.config_filename)
        except Exception as e:
            result = f"❌ Fehler beim Ausführen: {e}"
        self.output_depot.after(0, lambda: self._update_depot_output(result))

    def _update_depot_output(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_depot.config(state="normal")
        self.output_depot.delete(1.0, tk.END)
        self.output_depot.insert(tk.END, f"[{timestamp}] {text}\n")
        self.output_depot.config(state="disabled")
        self.sync_button.config(state="normal")

    def _write_to_depot_output(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_depot.config(state="normal")
        self.output_depot.insert(tk.END, f"[{timestamp}] {text}\n")
        self.output_depot.see(tk.END)
        self.output_depot.config(state="disabled")

    def open_defaulttools_folder(self):
        folder_path = self.config.get("tools", "defaulttools", fallback=None)
        if folder_path and os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            messagebox.showwarning("Pfad nicht gefunden", f"Ordner nicht gefunden:\n{folder_path}")

    def clear_depot_output(self):
        self.output_depot.config(state="normal")
        self.output_depot.delete("1.0", tk.END)
        self.output_depot.config(state="disabled")

    def clear_rework_output(self):
        self.output_rework.config(state="normal")
        self.output_rework.delete("1.0", tk.END)
        self.output_rework.config(state="disabled")

    def run_tool_report_all(self):
        config_loader = ConfigLoader()
        export_all_status_tools_to_excel(config_loader, self.log)

    def log(self, msg):
        print(msg)  # oder in ein Textfeld schreiben