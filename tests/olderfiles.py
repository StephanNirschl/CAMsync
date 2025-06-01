import os
import time
from pathlib import Path

def alter_project_folder_recursively(folder_path, tage_alt=300):
    """Setzt rekursiv das Änderungsdatum aller Inhalte + Ordner"""
    seconds = tage_alt * 24 * 60 * 60
    zielzeit = time.time() - seconds

    for root, dirs, files in os.walk(folder_path):
        for name in files + dirs:
            full_path = os.path.join(root, name)
            try:
                os.utime(full_path, (zielzeit, zielzeit))
            except Exception as e:
                print(f"Fehler bei {full_path}: {e}")

    # Hauptordner selbst zuletzt
    os.utime(folder_path, (zielzeit, zielzeit))
    print(f"Setze Datum von {folder_path} auf {tage_alt} Tage alt.")

# Anwendung
local_dir = r"C:\Users\skywa\Desktop\localWorkspace"  # Raw-String gegen Backslash-Fehler

for folder in Path(local_dir).iterdir():
    if folder.is_dir():
        alter_project_folder_recursively(folder, tage_alt=300)