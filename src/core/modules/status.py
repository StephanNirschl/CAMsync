import sqlite3

def status(DB, callback=None):
    def log(msg):
        if callback:
            callback(msg)
        else:
            print(msg)

    verbindung = sqlite3.connect(DB)
    zeiger = verbindung.cursor()

    # === Löschungen nach Status ===
    log("🧹 Lösche NC-Werkzeuge aufgrund Status...")

    deletes = [
        ("Gelöscht", "Gelöscht"),
        ("Auslauf", "Auslaufwerkzeug"),
        ("Gesperrt", "Gesperrt"),
        ("Nicht für Werk ROD", "Nicht für Werk 'ROD' freigegeben"),
    ]

    for name, value in deletes:
        query = f"""
        DELETE FROM NCTools
        WHERE id IN (
            SELECT nctool_id FROM NCToolCustomData
            WHERE custom_data_value_id IN (
                SELECT custom_data_value_id FROM CustomDataValues
                WHERE custom_data_class_id = (
                    SELECT custom_data_class_id FROM CustomDataClasses WHERE name = 'Werkzeugstatus'
                )
                AND custom_data_value = ?
            )
        )
        """
        zeiger.execute(query, (value,))
        verbindung.commit()
        log(f"🗑️ {zeiger.rowcount} gelöscht für Status: {name}")

    # === Status als Präfix zum nc_name hinzufügen ===
    log("\n✏️ Statuspräfixe zum nc_name hinzufügen:")

    updates = [
        ("(+)_", "FAVORIT"),
        ("(F)_", "Freigegeben"),
        ("(F)_", "ROD Frei | WÜM Sonder"),
        ("(K)_", "Auftrags-Komplettwerkzeug"),
        ("(S)_", "ROD Sonder | WÜM Frei"),
        ("(S)_", "Sonderbeschaffung"),
        ("(S)_", "Form-/ Sonderwerkzeug"),
        ("(S)_", "Beigestelltes Werkzeug"),
        ("(S)_", "Inaktiv / keine Verwendung in beiden DB"),
        ("(S)_", "Versuchswerkzeug"),
    ]

    for prefix, status_value in updates:
        query = f"""
        UPDATE NCTools
        SET nc_name = CONCAT('{prefix}', nc_name)
        WHERE id IN (
            SELECT nctool_id FROM NCToolCustomData
            WHERE custom_data_value_id IN (
                SELECT custom_data_value_id FROM CustomDataValues
                WHERE custom_data_class_id = (
                    SELECT custom_data_class_id FROM CustomDataClasses WHERE name = 'Werkzeugstatus'
                )
                AND custom_data_value = ?
            )
        )
        AND nc_name NOT LIKE '%{prefix}%'
        """
        zeiger.execute(query, (status_value,))
        verbindung.commit()
        log(f"✅ {zeiger.rowcount} aktualisiert für Status: {status_value}")

    verbindung.close()
    log("✅ Status-Update abgeschlossen.\n")
