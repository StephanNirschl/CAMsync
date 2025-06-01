
# Depot-Synchronisation (`run_depot_sync`)

## Zweck
Synchronisiert Werkzeugdaten aus Excel-Dateien mit der lokalen Werkzeugdatenbank (`tools.db`).  
Jede Excel-Datei repräsentiert ein Depot und enthält eine Spalte mit Werkzeugnummern.

## Hauptfunktionen
- **Anlegen neuer Depots**, falls noch nicht vorhanden.
- **Aktualisieren von bestehenden Depots** (Parent-ID sicherstellen).
- **Einfügen von DepotItems** für jedes Werkzeug in der Excel-Datei.
- **Löschen von veralteten DepotItems**, die nicht mehr in der Excel-Datei gelistet sind.

## Ablauflogik

1. **Initialisierung**
   - Lade Konfiguration aus `config.ini` (Datenbankpfad, Excel-Verzeichnis).
   - Initialisiere Logger und SQLite-Verbindung.

2. **Verarbeitung pro Excel-Datei**
   - Bestimme Depotname aus Dateinamen (`Standard_<Depotname>.xlsx`).
   - Lese Werkzeugnummern aus Spalte A.
   - Suche das zugehörige Depot in der Datenbank.
     - Falls nicht vorhanden → Neues Depot anlegen.
     - Falls vorhanden → Parent-ID ggf. korrigieren.
   - Für jede Werkzeugnummer:
     - Prüfe Existenz in `NCTools`.
     - Lösche vorhandene Einträge in `DepotItems` mit gleicher Nummer.
     - Füge neuen Eintrag in `DepotItems` ein mit aktuellem GUID.
   - **Neu (Mai 2025):**  
     Nach dem Einfügen werden **alle DepotItems gelöscht**, die **nicht mehr in der Excel-Datei gelistet** sind.
     - Dies stellt sicher, dass das Depot exakt den Zustand der Excel-Datei widerspiegelt.
     - Das Set der Werkzeugnummern aus Excel wird mit den bestehenden `alt_nc_number_val` verglichen.
     - Die Differenz wird aus der Datenbank gelöscht.

3. **Abschluss**
   - Transaktionen werden gespeichert (`commit`).
   - Verbindung geschlossen.
   - Eine Log-Ausgabe wird sowohl in Datei als auch als Rückgabe generiert.

## Datenbankstruktur (relevant)

### Tabelle: `Depots`
| Spalte       | Typ     | Bedeutung                     |
|--------------|---------|-------------------------------|
| `id`         | INTEGER | Primärschlüssel               |
| `name`       | TEXT    | Depotname                     |
| `parent_id`  | INTEGER | Hierarchie (Standard = 0)     |
| `obj_guid`   | BLOB    | Eindeutiger Bezeichner        |

### Tabelle: `DepotItems`
| Spalte              | Typ     | Bedeutung                         |
|---------------------|---------|-----------------------------------|
| `depot_id`          | INTEGER | Fremdschlüssel auf `Depots.id`    |
| `alt_nc_number_val` | INTEGER | Werkzeugnummer                    |
| `nctool_id`         | INTEGER | Verweis auf `NCTools`             |
| `obj_guid`          | BLOB    | Eindeutiger Eintrag               |
| `alt_nc_name`       | TEXT    | Anzeigename (z. B. inkl. Depotname) |

## Beispiel-Konfiguration (`config.ini`)

```ini
[tools]
db = C:/CAMsync/data/tools.db
defaulttools = C:/CAMsync/assets/depot_excels/
```

## Logging
- Jeder Schritt wird im Logger dokumentiert.
- Rückgabe ist ein `StringIO`-Buffer zur Anzeige in der GUI oder Konsole.
- Typische Einträge:
  - `✅ Eingefügt: ...`
  - `❌ Fehler bei: ...`
  - `🗑️ Lösche veraltete Einträge aus Depot ...`

## Anforderungen
- Python ≥ 3.9
- Pakete: `pandas`, `sqlite3`, `openpyxl` (für Excel-Import)

## Erweiterungsideen
- Kommentare für Depots ergänzen
- in Dauerlauf integrieren??

---

Letzte Aktualisierung: Mai 2025
