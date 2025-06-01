
import sqlite3
import pandas as pd
import os
import uuid
from io import StringIO
from core.logging_utils import get_logger
from config.config_loader import ConfigLoader

def generate_obj_guid():
    return uuid.uuid4().bytes

def run_depot_sync(config_path="config.ini"):
    output = StringIO()

    config = ConfigLoader(config_path, silent=True)  # config_path extern übergeben
    logger = get_logger("depot_sync", config)       # config-Objekt direkt übergeben

    def log(msg):
        output.write(msg + "\n")
        logger.info(msg)

    db_path = config.get("tools", "db")
    excel_dir = config.get("tools", "defaulttools")
    default_parent_id = 0

    log(f"\n📂 Datenbank: {db_path}")
    log(f"📁 Excel-Verzeichnis: {excel_dir}")

    if not os.path.exists(excel_dir):
        log(f"❌ Verzeichnis nicht gefunden: {excel_dir}\n")
        return output.getvalue()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for file in os.listdir(excel_dir):
        if not file.endswith(".xlsx"):
            continue

        excel_path = os.path.join(excel_dir, file)
        depot_name = os.path.splitext(file)[0].replace("Standard_", "").replace("___", "__")

        log(f"\n🔧 Starte Verarbeitung: {file}")

        try:
            df = pd.read_excel(excel_path, header=None, usecols="A")
            df.dropna(inplace=True)
            werte_liste = df[0].astype(str).tolist()
        except Exception as e:
            log(f"❌ Fehler beim Lesen der Excel-Datei: {e}")
            continue

        cursor.execute("SELECT id, parent_id FROM Depots WHERE name = ?", (depot_name,))
        depot_result = cursor.fetchone()

        if depot_result:
            depot_id, existing_parent_id = depot_result
            if existing_parent_id != default_parent_id:
                cursor.execute("UPDATE Depots SET parent_id = ? WHERE id = ?", (default_parent_id, depot_id))
                log(f"✅ Depot '{depot_name}' gefunden mit id={depot_id} (parent_id aktualisiert)")
            else:
                log(f"✅ Depot '{depot_name}' gefunden mit id={depot_id}")
        else:
            try:
                depot_guid = generate_obj_guid()
                cursor.execute("""
                    INSERT INTO Depots (name, comment, leaf_node, obj_guid, parent_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (depot_name, "Standardwerkzeuge_Coscom", 1, depot_guid, default_parent_id))
                depot_id = cursor.lastrowid
                log(f"➕ Neues Depot '{depot_name}' angelegt mit id={depot_id}")
            except Exception as e:
                log(f"❌ Fehler beim Anlegen des Depots '{depot_name}': {e}")
                continue

        anzahl_erfolgreich = 0
        for wert in werte_liste:
            log(f"\n🔍 Prüfe Werkzeugnummer: {wert}")
            cursor.execute("SELECT id, obj_guid, nc_name FROM NCTools WHERE nc_number_val = ?", (wert,))
            nctool = cursor.fetchone()

            if not nctool:
                log(f"⚠️  Kein Eintrag in 'NCTools' für '{wert}' gefunden.")
                continue

            nctool_id, nctool_guid, nc_name = nctool
            alt_nc_name = f"{depot_name}   {nc_name}"

            try:
                cursor.execute("""
                    DELETE FROM DepotItems WHERE alt_nc_number_val = ? AND depot_id = ?
                """, (wert, depot_id))
                log(f"🔁 Vorheriger Eintrag zu '{wert}' gelöscht (falls vorhanden)")

                new_guid = generate_obj_guid()
                cursor.execute("""
                    INSERT INTO DepotItems (
                        depot_id, alt_nc_number_val, alt_nc_number_str, alt_breakage_check,
                        nctool_id, obj_guid, alt_nc_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    depot_id,
                    int(wert),
                    wert,
                    0,
                    nctool_id,
                    new_guid,
                    alt_nc_name
                ))

                anzahl_erfolgreich += 1
                log(f"✅ Eingefügt: {wert} → nctool_id={nctool_id}")

            except Exception as e:
                log(f"❌ Fehler bei '{wert}': {e}")


        # ➕ NEU: DepotItems bereinigen – alles löschen, was nicht mehr in Excel steht
        try:
            cursor.execute("SELECT alt_nc_number_val FROM DepotItems WHERE depot_id = ?", (depot_id,))
            vorhandene_werte = {str(row[0]) for row in cursor.fetchall()}
            aktuelle_werte_set = set(werte_liste)
            zu_loeschende = vorhandene_werte - aktuelle_werte_set

            if zu_loeschende:
                log(f"\n🗑️ Lösche {len(zu_loeschende)} veraltete Einträge aus Depot '{depot_name}'")
                for alt_wert in zu_loeschende:
                    cursor.execute("DELETE FROM DepotItems WHERE depot_id = ? AND alt_nc_number_val = ?", (depot_id, alt_wert))
                    log(f"❌ Entfernt: {alt_wert}")

        except Exception as e:
            log(f"❌ Fehler beim Löschen veralteter Einträge: {e}")

        conn.commit()
        log(f"\n🟢 Datei abgeschlossen: {anzahl_erfolgreich} Einträge eingefügt, {len(zu_loeschende)} gelöscht.")



    conn.close()
    log("\n✅ Alle Dateien verarbeitet.")
    return output.getvalue()
