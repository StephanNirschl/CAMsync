import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
from core import cleanup


class CleanupTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # === Steuerung für Thread-Stop ===
        self.cleanup_stop_event = threading.Event()

        # === Überschrift ===
        ttk.Label(
            self,
            text="🧹 Alte .vis und .stl Dateien im Projektverzeichnis löschen.",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(15, 0))

        # === Steuerleiste ===
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        control_frame.columnconfigure(1, weight=1)

        self.cleanup_start_button = ttk.Button(control_frame, text="Start", command=self.start_cleanup)
        self.cleanup_start_button.grid(row=0, column=0, sticky="w")

        self.cleanup_stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_cleanup, state="disabled")
        self.cleanup_stop_button.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Combobox mit Löschmodus
        ttk.Label(control_frame, text="🧾 Löschen aktivieren:").grid(row=0, column=2, padx=(20, 5))
        self.delete_var = tk.StringVar(value="False")  # Immer Dry-Run beim Start
        self.delete_option = ttk.Combobox(control_frame, values=["True", "False"],
                                          width=7, state="readonly", textvariable=self.delete_var)
        self.delete_option.grid(row=0, column=3, sticky="w")

        # Hinweistext zum Modus
        self.info_label = ttk.Label(self, text="", foreground="blue")
        self.info_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 5))
        self.delete_option.bind("<<ComboboxSelected>>", self.update_info_label)
        self.update_info_label()

        # === Fortschrittsbalken ===
        self.cleanup_progress = ttk.Progressbar(self, mode="indeterminate")
        self.cleanup_progress.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))

        # === Konsolenausgabe ===
        output_frame = ttk.Frame(self)
        output_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(5, 10))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_cleanup = tk.Text(output_frame, height=20, state="disabled", wrap="word")
        scroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_cleanup.yview)
        self.output_cleanup.configure(yscrollcommand=scroll.set)

        self.output_cleanup.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

    def update_info_label(self, event=None):
        if self.delete_var.get() == "True":
            self.info_label.config(text="⚠️ Dateien werden tatsächlich gelöscht!", foreground="red")
        else:
            self.info_label.config(text="❗ Dry-Run aktiv: Dateien werden NICHT gelöscht.", foreground="green")

    def start_cleanup(self):
        self._write_to_cleanup_output("🧹 Cleanup gestartet...")
        self.cleanup_progress.start()
        self.cleanup_start_button.config(state="disabled")
        self.cleanup_stop_button.config(state="normal")

        delete_setting = self.delete_var.get().lower() == "true"
        config_path = self.config.config_filename
        self.cleanup_stop_event.clear()

        def callback(msg):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.output_cleanup.after(0, lambda: self._write_to_cleanup_output(f"[{timestamp}] {msg}"))

        def thread_func():
            try:
                if delete_setting:
                    cleanup.run_cleanup(
                        callback=callback,
                        delete_override=delete_setting,
                        config_path=config_path,
                        stop_event=self.cleanup_stop_event
                    )
                else:
                    cleanup.run_cleanup_dry_run(
                        callback=callback,
                        config_path=config_path,
                        stop_event=self.cleanup_stop_event
                    )
            except Exception as e:
                callback(f"❌ Fehler: {e}")
            finally:
                self.cleanup_progress.stop()
                self.cleanup_start_button.config(state="normal")
                self.cleanup_stop_button.config(state="disabled")

        self.cleanup_thread = threading.Thread(target=thread_func, daemon=True)
        self.cleanup_thread.start()

    def stop_cleanup(self):
        self.cleanup_stop_event.set()
        self._write_to_cleanup_output("🛑 Cleanup-Stopp angefordert")
        self.cleanup_progress.stop()
        self.cleanup_start_button.config(state="normal")
        self.cleanup_stop_button.config(state="disabled")

    def _write_to_cleanup_output(self, text):
        self.output_cleanup.config(state="normal")
        self.output_cleanup.insert(tk.END, f"{text}\n")
        self.output_cleanup.see(tk.END)
        self.output_cleanup.config(state="disabled")