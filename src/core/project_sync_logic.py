import os
import sqlite3
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from gui.popup_centered import show_centered_popup, show_centered_yesno_popup
from core.project_sync_logging import log_project_action
import json
import sys
from gui.loading_popup import LoadingPopup



STATE_FILE = "treeview_state.json"

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        c.execute("SELECT path FROM projects LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("DROP TABLE IF EXISTS projects")

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            locked_by TEXT,
            locked_since TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            displayname TEXT
        )
    """)

    # Speichert Metadaten wie den Zeitpunkt des letzten erfolgreichen Netzwerkscans
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    conn.commit()
    conn.close()

def load_projects(tab):
    expanded = load_tree_state()
    tab.tree.delete(*tab.tree.get_children())

    conn = sqlite3.connect(tab.db_path)
    c = conn.cursor()
    c.execute("SELECT name, path, locked_by, locked_since FROM projects")
    rows = c.fetchall()
    conn.close()

    kunden_map = {}

    for name, path, locked_by, locked_since in rows:
        normalized_name = normalize_project_name(name)  # 🔧 Immer normalisieren
        path_parts = Path(path).parts
        kunde = path_parts[-3] if len(path_parts) >= 3 else "UNBEKANNT"
        jahr = path_parts[-2] if len(path_parts) >= 2 else "----"

        if tab.kunden_filter.get() and tab.kunden_filter.get() not in kunde:
            continue
        if tab.jahr_filter.get() and tab.jahr_filter.get() not in jahr:
            continue

        if kunde not in kunden_map:
            kunden_map[kunde] = tab.tree.insert("", "end", text=kunde, open=False)

        kunde_id = kunden_map[kunde]
        jahr_key = f"{kunde}_{jahr}"
        if jahr_key not in kunden_map:
            kunden_map[jahr_key] = tab.tree.insert(kunde_id, "end", text=jahr, open=False)

        jahr_id = kunden_map[jahr_key]

        status = "frei" if not locked_by else "gesperrt"
        user = "-" if not locked_by else locked_by
        modified = "-"
        try:
            mtime = os.path.getmtime(path)
            modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass


        item = tab.tree.insert(jahr_id, "end", text=normalized_name, values=(status, user, modified))
        if locked_by:
            tab.tree.item(item, tags=("locked",))

    # Wichtig: Expand-Zustand leicht verzögert wiederherstellen
    tab.after(50, lambda: restore_expanded_nodes(tab.tree, expanded))

def scan_and_sync_projects(tab, silent=False, force=False):
    """
    Scannt das Netzwerkverzeichnis nach Projekten und synchronisiert sie mit der lokalen Datenbank.
    Entfernt verwaiste Einträge und erkennt __LOCKED-Projekte als dieselben Einträge.
    Wenn ``force`` False ist, wird der Scan nur ausgeführt, wenn sich das
    Netzwerkverzeichnis seit dem letzten erfolgreichen Scan geändert hat.
    """
    from gui.popup_centered import show_centered_popup, show_centered_yesno_popup

    removed = 0
    conn = sqlite3.connect(tab.db_path)
    c = conn.cursor()

    # Tabelle für Scan-Metadaten sicherstellen
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    base_path = tab.config.get("projects", "network_project_root", fallback="")

    # Prüfen, ob ein Scan notwendig ist
    if not force and base_path and os.path.isdir(base_path):
        c.execute("SELECT value FROM scan_metadata WHERE key = 'last_scan'")
        row = c.fetchone()
        if row:
            try:
                last_scan = datetime.fromisoformat(row[0])
                root_mtime = datetime.fromtimestamp(os.path.getmtime(base_path))
                if root_mtime <= last_scan:
                    conn.close()
                    if not silent:
                        show_centered_popup(tab, "Info", "Keine Änderungen seit letztem Scan.")
                    load_projects(tab)
                    return
            except Exception:
                pass

    # 1. Verwaiste Projekte entfernen
    c.execute("SELECT id, path FROM projects")
    for proj_id, path in c.fetchall():
        if not os.path.exists(path):
            c.execute("DELETE FROM projects WHERE id = ?", (proj_id,))
            removed += 1
    conn.commit()

    # 2. Netzwerkpfad prüfen
    if not base_path or not os.path.isdir(base_path):
        conn.close()
        messagebox.showerror("Fehler", f"Pfad aus [projects] network_project_root nicht gefunden:\n{base_path}")
        return

    # 3. Projekte erfassen
    existing_paths = {}
    c.execute("SELECT id, name, path FROM projects")
    for row in c.fetchall():
        existing_paths[row[2]] = {"id": row[0], "name": row[1]}

    new_projects = []
    for kundenordner in Path(base_path).iterdir():
        if not kundenordner.is_dir():
            continue
        for jahrordner in kundenordner.iterdir():
            if not jahrordner.is_dir():
                continue
            for projektordner in jahrordner.iterdir():
                if not projektordner.is_dir():
                    continue

                detected_path = str(projektordner)
                detected_name = projektordner.name
                normalized_name = normalize_project_name(detected_name)
                is_locked = detected_name != normalized_name

                # Prüfen ob normalisierter Eintrag existiert
                match = None
                for path in existing_paths.keys():
                    if Path(path).name == normalized_name:
                        match = path
                        break

                if match:
                    if is_locked:
                        # Frage an Benutzer: Inkonsistenter LOCK-Zustand erkannt
                        antwort = show_centered_yesno_popup(tab,
                            "Inkompatibler LOCK-Zustand",
                            f"⚠️ Für das Projekt '{normalized_name}' wurde im Netzwerk ein '__LOCKED' Ordner gefunden.\n"
                            f"Dies widerspricht dem erwarteten Zustand der Datenbank.\n\n"
                            f"Soll der gefundene Zustand trotzdem übernommen werden?")
                        if antwort:
                            # ✅ Benutzer akzeptiert → Pfad in DB aktualisieren
                            c.execute("UPDATE projects SET path = ? WHERE name = ?", (detected_path, normalized_name))
                            conn.commit()

                            # 🆕 Automatisch Sperre setzen, wenn LOCK-Zustand erkannt, aber DB keinen Lock hat
                            c.execute("SELECT locked_by FROM projects WHERE name = ?", (normalized_name,))
                            locked_by = c.fetchone()
                            if locked_by and locked_by[0] is None:
                                # SYSTEM-Lock setzen zur Sicherheit
                                c.execute("UPDATE projects SET locked_by = 'SYSTEM', locked_since = ? WHERE name = ?",
                                        (datetime.now().isoformat(), normalized_name))
                                conn.commit()
                        # Wenn der Nutzer "Nein" klickt → Keine Änderungen
                else:
                    # Neues Projekt: Name normalisieren und aufnehmen
                    # Nur ein Eintrag pro Projektname zulassen:
                    existing_entry = c.execute("SELECT id FROM projects WHERE name = ?", (normalized_name,)).fetchone()
                    if not existing_entry:
                        c.execute("INSERT INTO projects (name, path) VALUES (?, ?)", (normalized_name, detected_path))
                        new_projects.append(normalized_name)
                    else:
                        # Optional: Du kannst hier den Pfad aktualisieren, falls der neue Pfad korrekt ist
                        c.execute("UPDATE projects SET path = ? WHERE name = ?", (detected_path, normalized_name))

    # Zeitpunkt des erfolgreichen Scans speichern
    c.execute(
        "REPLACE INTO scan_metadata (key, value) VALUES ('last_scan', ?)",
        (datetime.now().isoformat(),),
    )

    conn.commit()
    conn.close()

    # 4. Meldung erzeugen
    msg = ""
    if removed > 0:
        msg += f"{removed} verwaiste Projekte wurden entfernt.\n"
    if new_projects:
        msg += f"{len(new_projects)} neue Projekte hinzugefügt:\n" + "\n".join(new_projects)
    else:
        msg += "Keine neuen Projekte gefunden."

    if not silent:
        show_centered_popup(tab, "Projekt-Scan abgeschlossen", msg)

    # 5. Tree aktualisieren
    load_projects(tab)


def download_project(tab, log_action=True):
    selected = tab.tree.selection()
    if not selected:
        return show_centered_popup(tab, "Hinweis", "Bitte ein Projekt auswählen.")

    name = tab.tree.item(selected[0], "text")
    if log_action:
        log_project_action(name, tab.username, "download", tab.db_path)

    loading = LoadingPopup(tab, "Projekt wird heruntergeladen...")
    conn = sqlite3.connect(tab.db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT path, locked_by FROM projects WHERE name = ?", (name,))
        result = c.fetchone()
        if not result:
            return

        path, locked_by = result
        if locked_by and locked_by != tab.username:
            return show_centered_popup(tab, "Gesperrt", f"Projekt wird aktuell von {locked_by} bearbeitet.")

        locked_name = name + "__LOCKED"
        locked_path = os.path.join(os.path.dirname(path), locked_name)
        local_path = os.path.join(tab.local_dir, name)

        os.rename(path, locked_path)
        c.execute("UPDATE projects SET path = ?, locked_by = ?, locked_since = ? WHERE name = ?",
                  (locked_path, tab.username, datetime.now().isoformat(), name))
        conn.commit()

        if os.path.exists(local_path):
            raise FileExistsError(f"⚠️ Das Projekt existiert bereits lokal:\n{local_path}")

        shutil.copytree(locked_path, local_path)
        show_centered_popup(tab, "Download abgeschlossen", f"Projekt wurde lokal gespeichert unter:\n{tab.local_dir}")

    except FileExistsError as e:
        c.execute("SELECT path, locked_by FROM projects WHERE name = ?", (name,))
        current = c.fetchone()
        if current:
            c.execute("UPDATE projects SET path = ?, locked_by = ?, locked_since = ? WHERE name = ?",
                      (locked_path, tab.username, datetime.now().isoformat(), name))
            conn.commit()
        show_centered_popup(tab, "Projekt bereits vorhanden", str(e))

    except Exception as e:
            show_centered_popup(tab, "Fehler beim Download", f"Beim Herunterladen ist ein Fehler aufgetreten:\n\n{e}")
    finally:
            loading.close()
            expanded = get_expanded_nodes(tab.tree)
            load_projects(tab)
            restore_expanded_nodes(tab.tree, expanded)

def upload_project(tab, log_action=True):
    selected = tab.tree.selection()
    if not selected:
        return show_centered_popup(tab, "Hinweis", "Bitte ein Projekt auswählen.")

    name = tab.tree.item(selected[0], "text")
    local_path = os.path.join(tab.local_dir, name)
    if not os.path.exists(local_path):
        return show_centered_popup(tab, "Fehler", f"Lokales Projektverzeichnis nicht gefunden:\n{local_path}")

    if log_action:
        log_project_action(name, tab.username, "upload", tab.db_path)

    loading = LoadingPopup(tab, "Projekt wird hochgeladen...")

    conn = sqlite3.connect(tab.db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT path, locked_by FROM projects WHERE name = ?", (name,))
        result = c.fetchone()
        if not result:
            return

        locked_path, locked_by = result
        if locked_by != tab.username:
            return show_centered_popup(tab, "Fehler", "Du hast dieses Projekt nicht gesperrt.")

        original_name = normalize_project_name(name)
        original_path = os.path.join(os.path.dirname(locked_path), original_name)
        network_root = tab.config.get("projects", "network_project_root", fallback="Z:/CAM_Projekte/")
        backup_net_dir = os.path.join(network_root, "backup")
        os.makedirs(backup_net_dir, exist_ok=True)

        if os.path.exists(original_path):
            konfliktname = original_name + "__KONFLIKT"
            konfliktpfad = os.path.join(os.path.dirname(locked_path), konfliktname)
            os.rename(locked_path, konfliktpfad)
            locked_path = konfliktpfad
        else:
            os.rename(locked_path, original_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name_net = f"{original_name}_{timestamp}_older.zip"
        zip_path_net = os.path.join(backup_net_dir, zip_name_net)
        with zipfile.ZipFile(zip_path_net, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(original_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, original_path)
                    zipf.write(full_path, rel_path)

        shutil.rmtree(original_path)
        shutil.copytree(local_path, original_path)

        local_backup_dir = os.path.join(tab.local_dir, "backup")
        os.makedirs(local_backup_dir, exist_ok=True)

        zip_name_local = f"{original_name}_{timestamp}_latest.zip"
        zip_path_local = os.path.join(local_backup_dir, zip_name_local)
        with zipfile.ZipFile(zip_path_local, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(local_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, local_path)
                    zipf.write(full_path, rel_path)

        shutil.rmtree(local_path)

        c.execute("UPDATE projects SET path = ?, locked_by = NULL, locked_since = NULL WHERE name = ?",
                  (original_path, name))
        conn.commit()

        info = f"""✅ Upload abgeschlossen.

                📂 Netzwerkprojekt gespeichert unter:
                {original_path}

                🗜️ Netzwerk-Backup:
                {zip_path_net}

                🗜️ Lokales Backup:
                {zip_path_local}
                """
        show_centered_popup(tab, "Upload erfolgreich", info)

    except Exception as e:
        show_centered_popup(tab, "Fehler beim Upload", str(e))
    finally:
        loading.close()
        expanded = get_expanded_nodes(tab.tree)
        load_projects(tab)
        restore_expanded_nodes(tab.tree, expanded)

def delete_db_project(tab):
    selected = tab.tree.focus()
    if not selected:
        return

    name = tab.tree.item(selected, "text")
    if not messagebox.askyesno("Löschen", f"Projekt {name} wirklich aus Datenbank entfernen?"):
        return

    conn = sqlite3.connect(tab.db_path)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    expanded = get_expanded_nodes(tab.tree)
    load_projects(tab)
    restore_expanded_nodes(tab.tree, expanded)

def get_state_file_path():
    """Ermittelt den Speicherort für treeview_state.json je nach Laufzeitumgebung."""
    if getattr(sys, 'frozen', False):  # Wir laufen als gepackte EXE
        appdata_path = os.path.join(os.getenv("APPDATA"), "CAMsync")
        os.makedirs(appdata_path, exist_ok=True)
        return os.path.join(appdata_path, "treeview_state.json")
    else:
        return os.path.join(os.getcwd(), "treeview_state.json")




STATE_FILE = get_state_file_path()

def get_expanded_nodes(tree):
    expanded = set()

    def recurse(item, path=""):
        text = tree.item(item, "text")
        current_path = f"{path}/{text}" if path else text
        is_open = tree.item(item, "open")
        #print(f"{current_path}: {'OPEN' if is_open else 'closed'}")  # Debug-Ausgabe
        if is_open:
            expanded.add(current_path)
        for child in tree.get_children(item):
            recurse(child, current_path)

    for top_level in tree.get_children(""):
        recurse(top_level)
    return expanded

def restore_expanded_nodes(tree, expanded_set):
    """Stellt geöffnete Treeview-Knoten anhand gespeicherter Pfade wieder her."""
    def recurse(item, path=""):
        text = tree.item(item, "text")
        current_path = f"{path}/{text}" if path else text
        if current_path in expanded_set:
            tree.item(item, open=True)
        for child in tree.get_children(item):
            recurse(child, current_path)

    for top_level in tree.get_children(""):
        recurse(top_level)

def save_tree_state(tree):
    """Speichert den aktuellen Expand-Zustand des Treeviews."""
    expanded = list(get_expanded_nodes(tree))
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(expanded, f)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern des Treeview-Zustands: {e}")

def load_tree_state():
    """Lädt gespeicherte Expand-Zustände oder gibt leere Menge zurück."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"⚠️ Fehler beim Laden des Treeview-Zustands: {e}")
            return set()
    return set()

def normalize_project_name(name: str) -> str:
    """
    Entfernt "__LOCKED", "__locked", "__LOCKED__LOCKED" etc. am Ende eines Projektnamens.
    """
    while name.upper().endswith("__LOCKED"):
        name = name[: -len("__LOCKED")]
    return name
