import sqlite3

def toolclasses(DB, callback=None):
    def log(msg):
        if callback:
            callback(msg)
        else:
            print(msg)

    verbindung = sqlite3.connect(DB)
    zeiger = verbindung.cursor()

    log("🔄 Werkzeuge in Schnittklassen schieben:")

    try:
        drill_kenna_uni = """
        UPDATE Tools
        SET tool_class_id = (
            SELECT tool_class_id FROM ToolClasses WHERE name = 'Kennametal_Universal' LIMIT 1
        )
        WHERE name IN (
            SELECT nc_number_val FROM NCTools WHERE nc_name LIKE '%SpiBo Kenna%HM IKZ (UNI)%'
        )
        AND tool_type_id IN (
            SELECT id FROM GeometryClasses WHERE name LIKE 'Drilltool'
        )
        AND cutting_material_id IN (
            SELECT id FROM CuttingMaterials WHERE name LIKE 'VHM - PVD-TiAlN'
        );
        """
        zeiger.execute(drill_kenna_uni)
        verbindung.commit()
        log(f"✅ {zeiger.rowcount} Werkzeug(e) in Klasse 'Kennametal_Universal' verschoben.")
    except Exception as e:
        log(f"❌ Fehler beim Verschieben in 'Kennametal_Universal': {e}")

    # Weitere Regeln kannst du genauso einfügen und aktivieren:
    # - logische Namen (z. B. 'TORUS_Gelbring_unbeschichtet')
    # - strukturierte Bedingungen
    # - auf Wunsch aktivieren wir die restlichen Blöcke

    verbindung.close()
    log("✅ Toolklassen-Update abgeschlossen.\n")