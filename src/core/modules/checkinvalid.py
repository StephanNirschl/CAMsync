import sqlite3
import os
import shutil

def delete_xml_entries(DB, ifo, sfo, callback=None):
    def log(msg):
        if callback:
            callback(msg)
        else:
            print(msg)

    try:
        dateien = [f for f in os.listdir(ifo)
                   if f.endswith('.xml') and os.path.isfile(os.path.join(ifo, f))]
    except Exception as e:
        log(f"❌ Fehler beim Lesen des Ordners '{ifo}': {e}")
        return

    log(f"📄 {len(dateien)} XML-Dateien gefunden in '{ifo}'.")

    if not dateien:
        log("ℹ️ Keine XML-Dateien zum Löschen gefunden.\n")
        return

    namen_ohne_endung = [os.path.splitext(f)[0] for f in dateien]

    try:
        verbindung = sqlite3.connect(DB)
        zeiger = verbindung.cursor()

        placeholders = ','.join('?' for _ in namen_ohne_endung)

        zeiger.execute(f"DELETE FROM NCTools WHERE nc_number_val IN ({placeholders})", namen_ohne_endung)
        zeiger.execute(f"DELETE FROM Tools WHERE name IN ({placeholders})", namen_ohne_endung)
        zeiger.execute(f"DELETE FROM Holders WHERE name IN ({placeholders})", namen_ohne_endung)
        zeiger.execute(f"DELETE FROM Extensions WHERE name IN ({placeholders})", namen_ohne_endung)

        verbindung.commit()
        log(f"🧹 {zeiger.rowcount} Einträge anhand von XML-Dateinamen gelöscht.")
        verbindung.close()
    except Exception as e:
        log(f"❌ Fehler beim Löschen aus der Datenbank: {e}")
        return

    for datei in dateien:
        quelle = os.path.join(ifo, datei)
        ziel = os.path.join(sfo, datei)
        try:
            shutil.move(quelle, ziel)
            log(f"📦 Datei verschoben: {datei}")
        except Exception as e:
            log(f"❌ Fehler beim Verschieben von '{datei}': {e}")
