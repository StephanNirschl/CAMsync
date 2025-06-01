import sqlite3
from config.material_config_loader import MaterialConfigLoader

def materials(DB, log):
    """
    Fuehrt Materialersetzungen in der Datenbank `Technologies` durch,
    basierend auf den Zuordnungen in material_mapping.ini.
    Die Log-Ausgabe erfolgt ueber den uebergebenen log(msg)-Callback.
    """
    verbindung = sqlite3.connect(DB)
    zeiger = verbindung.cursor()

    config_loader = MaterialConfigLoader(silent=True)
    mapping = config_loader.get_mapping()

    log("🔁 Starte Materialuebertragungen aus INI-Datei")

    total_updates = 0  # Zaehlvariable fuer geaenderte Eintraege

    for alt, neu in mapping.items():
        sql = """
        UPDATE Technologies
        SET material_id = (SELECT id FROM Materials WHERE name = ?)
        WHERE material_id IN (
            SELECT id FROM Materials WHERE name = ?
        );
        """
        try:
            zeiger.execute(sql, (neu.strip(), alt.strip()))
            verbindung.commit()
            updated = zeiger.rowcount
            total_updates += updated
            log("✅ {} Updates: '{}' → '{}'".format(updated, alt, neu))
        except Exception as e:
            log("❌ Fehler beim Ersetzen '{}': {}".format(alt, str(e)))
            continue

    verbindung.close()
    log("✅ Materialupdate abgeschlossen. Insgesamt geaendert: {} Eintraege.\n".format(total_updates))