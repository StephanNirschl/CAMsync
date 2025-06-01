import tkinter as tk
from tkinter import Toplevel, Label, ttk

def show_centered_popup(parent, title, message):
    """
    Zeigt ein zentriertes Popup-Fenster mit einer OK-Schaltfläche.
    """
    popup = Toplevel(parent)
    popup.title(title)
    popup.resizable(False, False)

    width = 700
    height = 200

    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)

    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.transient(parent)
    popup.grab_set()

    # Optional: Mindestgröße festlegen
    popup.minsize(400, 200)

    Label(
        popup,
        text=message,
        wraplength=650,   # Mehr Zeilenbreite
        padx=20,
        pady=20
    ).pack(fill="both", expand=True)

    ttk.Button(popup, text="OK", command=popup.destroy).pack(pady=(0, 15))

def show_centered_yesno_popup(parent, title, message):
    """
    Zeigt ein zentriertes Popup-Fenster mit Ja/Nein-Schaltflächen.
    Gibt True für Ja und False für Nein zurück.
    """
    result = {"value": None}

    popup = Toplevel(parent)
    popup.title(title)
    popup.resizable(False, False)

    width = 600
    height = 250
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.transient(parent)
    popup.grab_set()

    Label(popup, text=message, wraplength=560, justify="left", padx=20, pady=20).pack()

    button_frame = ttk.Frame(popup)
    button_frame.pack(pady=(0, 20))

    def yes():
        result["value"] = True
        popup.destroy()

    def no():
        result["value"] = False
        popup.destroy()

    ttk.Button(button_frame, text="Ja", command=yes).pack(side="left", padx=20)
    ttk.Button(button_frame, text="Nein", command=no).pack(side="right", padx=20)

    popup.wait_window()
    return result["value"]