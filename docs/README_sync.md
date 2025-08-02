# 📂 CAMsync – Projektsynchronisation

Diese Dokumentation beschreibt die Logik und den Ablauf der Projektsynchronisation innerhalb von CAMsync.

---

## 🔧 Datenbank-Tabellen

### Tabelle `projects`
| Spalte        | Typ    | Beschreibung                                      |
|---------------|--------|---------------------------------------------------|
| id            | int    | Eindeutiger Schlüssel                             |
| name          | text   | Projektname (normalisiert, ohne __LOCKED)         |
| path          | text   | Vollständiger Pfad (auch mit `__LOCKED` möglich)  |
| locked_by     | text   | Benutzername, der das Projekt gesperrt hat        |
| locked_since  | text   | Zeitpunkt der Sperrung (ISO-Format)               |

### Tabelle `scan_metadata`
| Spalte | Typ  | Beschreibung                               |
|--------|------|--------------------------------------------|
| key    | text | Schlüssel, z. B. `last_scan`               |
| value  | text | Zugehöriger Wert (Zeitstempel als ISO-String) |

---

## 🔁 Sync-Mechanismus

### `scan_and_sync_projects()`
- Lädt Netzwerkpfad aus der config.
- Entfernt **verwaiste Einträge**, bei denen `path` nicht mehr existiert.
- Iteriert über alle Projektordner (Pfadstruktur: `KUNDE/Jahr/Projekt`)
- Erkennt `__LOCKED` Ordner als gleichwertig zum Originalnamen.
- Fragt Benutzer, ob `__LOCKED` Zustand übernommen werden soll, wenn Inkonsistenz entdeckt wird.
- Neue Projekte werden in die Datenbank eingetragen.
- Speichert den Zeitpunkt des erfolgreichen Scans in `scan_metadata`.
- Vergleicht beim Start den letzten Scan-Zeitstempel mit dem Änderungszeitpunkt des Netzwerkordners und überspringt den Scan, wenn keine Änderungen vorliegen.
- Ein manueller Scan kann über den Button **„Projekte scannen“** erzwungen werden.

### `load_projects()`
- Holt alle Projekt-Einträge aus der Datenbank.
- Extrahiert Kunde und Jahr aus dem Pfad.
- Zeigt Projekte hierarchisch im TreeView (Kunde → Jahr → Projekt).
- `__LOCKED` wird **nicht** im Tree angezeigt.
- Gesperrte Projekte werden optisch markiert.

---

## ⬇️ `download_project()`

- Prüft, ob das Projekt schon lokal existiert
  - Falls ja, wird die Sperrung ggf. korrigiert.
- Netzwerkordner wird in `__LOCKED` umbenannt.
- Projekt wird in lokalen Arbeitsordner kopiert.
- Datenbank wird aktualisiert (Pfad, Sperrung, Zeitpunkt).

---

## ⬆️ `upload_project()`

- Lokaler Ordner wird validiert.
- Falls ein Netzwerkordner mit Originalnamen existiert:
  - Dieser wird umbenannt → ZIP-Backup in `/backup`
  - Dann gelöscht
- Lokaler Ordner wird hochgeladen und ebenfalls als ZIP gesichert.
- Datenbank-Eintrag wird ent-sperrt und Pfad korrigiert.

---

## 🔄 Besonderheiten

- Projekte mit `__LOCKED`-Endung gelten als **gesperrt**.
- Diese Endung wird bei Anzeige entfernt und bei Bedarf beim Download wieder hinzugefügt.
- TreeView speichert den Zustand (expandiert/zugeklappt) in JSON-Datei.
- Backup-Dateien folgen dem Namensschema:
  - `*_older.zip` (Netzwerk)
  - `*_latest.zip` (Lokal)

---

## 📦 Lokale Pfade

- Lokales Arbeitsverzeichnis: `config[projects][local_project_root]`
- Backup-Verzeichnis: `<lokal>/backup/`
- Treeview-State-Datei: im AppData-Ordner oder im Arbeitsverzeichnis

---

## 🧩 To-Do / Erweiterungen

- Anzeige des Sperrstatus in Tooltip
- Konflikt-Handling bei gleichzeitiger Nutzung verbessern
- Versionierung der ZIP-Dateien optional mit git möglich