from config.config_loader import ConfigLoader
from core.modules import status, materials, toolclasses, backup, checkinvalid
import threading
import time
import sys
from core.logging_utils import get_logger

def start_tool_rework_loop(callback, stop_event, config_path):
    try:
        # 📄 Konfiguration laden
        config = ConfigLoader(config_path)

        # 📝 Logger initialisieren (Logfile je nach config_path)
        logger = get_logger("tool_rework", config)

        # ✅ Erfolgsmeldung
        if callback:
            callback("✅ Konfiguration geladen: {}".format(config_path))
            logger.info("Konfiguration geladen: %s", config_path)

    except Exception as e:
        # ❌ Fehler beim Laden der Konfiguration
        try:
            error_message = "❌ Konnte Konfiguration nicht laden: {} ({})".format(config_path, str(e).replace('%', '[%]'))
        except Exception:
            error_message = "❌ Konnte Konfiguration nicht laden: Fehlertext nicht lesbar"
        if callback:
            callback(error_message)
        else:
            print(error_message)
        return

    # Hilfsfunktion: gleichzeitig in Log, Konsole und GUI schreiben
    def log(msg):
        try:
            msg_str = str(msg)
        except Exception as conv_err:
            msg_str = "[FEHLER BEIM FORMATIEREN DER LOG-NACHRICHT] {}".format(repr(conv_err))

        try:
            logger.info(msg_str)
            sys.stdout.write(msg_str + "\n")
            sys.stdout.flush()
        except Exception as log_err:
            print("❌ FEHLER BEIM LOGGEN:", log_err)

        if callback:
            try:
                callback(msg_str)
            except Exception as cb_err:
                print("❌ FEHLER BEIM CALLBACK:", cb_err)

    # 🔧 Werte aus config.ini lesen
    db = config.get("tools", "db")
    sfo = config.get("tools", "syncfolder")
    ifo = config.get("tools", "invalidfolder")

    log("")
    log("📂 Datenbank: {}".format(db))
    log("📁 Sync-Ordner: {}".format(sfo))
    log("📁 Invalid-Ordner: {}".format(ifo))
    log("")

    try:
        while not stop_event.is_set():
            log("🔄 Starte neuen Lauf...\n")

            # 🔁 Backup durchführen
            if config.get("optionstools", "backup", fallback="0") == "1":
                try:
                    backup.backup(db, log, config=config)
                    log("")
                except Exception as e:
                    log("❌ Backup-Fehler:\n")
                    try:
                        error_text = str(e).replace('%', '[%]')
                    except Exception:
                        error_text = "FEHLER-TEXT NICHT LESBAR"
                    log("Fehlermeldung: " + error_text + "\n")
                    break

            # 🔁 Status setzen
            if config.get("optionstools", "status1", fallback="0") == "1":
                try:
                    status.status(db, log)
                except Exception as e:
                    log("❌ Status-Fehler:")
                    try:
                        error_text = str(e).replace('%', '[%]')
                    except Exception:
                        error_text = "FEHLER-TEXT NICHT LESBAR"
                    log("Fehlermeldung: " + error_text)

            # 🔁 Ungültige Dateien prüfen/löschen
            if config.get("optionstools", "checkinvalid", fallback="0") == "1":
                try:
                    checkinvalid.delete_xml_entries(db, ifo, sfo, log)
                except Exception as e:
                    log("❌ Fehler beim Prüfen ungültiger Dateien:")
                    try:
                        error_text = str(e).replace('%', '[%]')
                    except Exception:
                        error_text = "FEHLER-TEXT NICHT LESBAR"
                    log("Fehlermeldung: " + error_text)

            # 🔁 Material & Klassen ändern
            if config.get("optionstools", "changematerialandclass", fallback="0") == "1":
                try:
                    materials.materials(db, log)
                    toolclasses.toolclasses(db, log)
                except Exception as e:
                    log("❌ Fehler bei Material/Klassen:")
                    try:
                        error_text = str(e).replace('%', '[%]')
                    except Exception:
                        error_text = "FEHLER-TEXT NICHT LESBAR"
                    log("Fehlermeldung: " + error_text)

            # 🔁 Durchlauf beendet
            log("✅ Durchlauf abgeschlossen. Warte 60 Sekunden...\n")

            # 🔂 Warten mit Stopp-Möglichkeit
            for _ in range(60):
                if stop_event.is_set():
                    raise KeyboardInterrupt
                time.sleep(1)

    except KeyboardInterrupt:
        # 🛑 Durch Benutzer gestoppt
        log("⛔ Automatischer Lauf wurde gestoppt.")
    except Exception as e:
        # ❌ Unbekannter Fehler im Thread
        log("❌ Unerwarteter Fehler im Rework-Thread:")
        try:
            error_text = str(e).replace('%', '[%]')
        except Exception:
            error_text = "FEHLER-TEXT NICHT LESBAR"
        log("Fehlermeldung: " + error_text)
