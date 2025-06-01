import tkinter as tk
from tkinter import ttk

class LoadingPopup:
    def __init__(self, parent, message="Bitte warten..."):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg="#333333")  # Dunkler Hintergrund
        self.top.geometry("300x100")
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        # Fenster zentrieren
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 50
        self.top.geometry(f"+{x}+{y}")

        # Lade-Label
        label = tk.Label(
            self.top,
            text=message,
            fg="white",
            bg="#333333",
            font=("Segoe UI", 12),
            anchor="center"
        )
        label.pack(pady=(20, 10))

        # Ladebalken
        self.progress = ttk.Progressbar(self.top, mode='indeterminate')
        self.progress.pack(pady=(0, 20), padx=20, fill="x")
        self.progress.start(10)

        self.top.update()
        self.top.lift()  # Sicherstellen, dass das Fenster im Vordergrund ist

    def close(self):
        self.progress.stop()
        self.top.destroy()