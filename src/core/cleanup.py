
import os
from datetime import datetime
from pathlib import Path
from core.logging_utils import get_logger
from config.config_loader import ConfigLoader

def run_cleanup(callback=None, delete_override=None, config_path=None, stop_event=None):
    if not config_path:
        raise ValueError("❌ Kein config_path übergeben – run_cleanup benötigt expliziten Pfad!")

    config = ConfigLoader(config_path, silent=True)
    logger = get_logger("cleanup", config)

    section = "cleanup"
    if section not in config.config.sections():
        raise ValueError(f"Abschnitt [{section}] fehlt in Datei: {config.config_filename}")

    def log(msg):
        logger.info(msg)
        if callback:
            callback(msg)

    path = config.get(section, "path", fallback="").strip()
    extension1 = config.get(section, "extension1", fallback=".stl").strip()
    days1 = config.getint(section, "days1", fallback=1)
    extension2 = config.get(section, "extension2", fallback=".vis").strip()
    days2 = config.getint(section, "days2", fallback=10)
    logfile_dir = config.get(section, "logfile1", fallback="logfile/").strip()
    delete_files = delete_override if delete_override is not None else True

    if not path or not os.path.exists(path):
        raise ValueError(f"Pfad '{path}' ist ungültig oder existiert nicht.")

    os.makedirs(logfile_dir, exist_ok=True)

    now = datetime.now()
    log(now.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"Suche in {path} und lösche alle\n"
        f"{extension1} älter als {days1} Tage und {extension2} älter als {days2} Tage\n"
        f"delete = {delete_files}\n")

    total_deleted, total_kept = 0.0, 0.0

    for ext, limit in [(extension1, days1), (extension2, days2)]:
        pattern = f"*{ext}" if ext.startswith(".") else ext
        log(f"🔍 Suche nach {pattern}...")

        for filepath in Path(path).rglob(pattern):
            if stop_event and stop_event.is_set():
                log("⛔ Vorgang wurde vom Benutzer gestoppt.")
                return

            try:
                file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                age_days = (datetime.now() - file_time).days
                size_mb = filepath.stat().st_size / 1024 / 1024

                if age_days >= limit:
                    msg = f"🗑️ {filepath.name} ({file_time}) - gelöscht={delete_files}"
                    log(msg)
                    total_deleted += size_mb
                    if delete_files:
                        filepath.unlink()
                else:
                    total_kept += size_mb
            except Exception as e:
                log(f"⚠️ Fehler bei {filepath}: {e}")

    log(f"\n✅ {round(total_deleted, 3)} MB gelöscht\n"
        f"📦 {round(total_kept, 3)} MB übrig")


def run_cleanup_dry_run(callback=None, config_path="config.ini", stop_event=None):
    config = ConfigLoader(config_path, silent=True)
    logger = get_logger("cleanup", config)

    section = "cleanup"
    if section not in config.config.sections():
        raise ValueError(f"Abschnitt [{section}] fehlt in Datei: {config.config_filename}")

    def log(msg):
        logger.info(msg)
        if callback:
            callback(msg)

    path = config.get(section, "path", fallback="").strip()
    extension1 = config.get(section, "extension1", fallback=".stl").strip()
    days1 = config.getint(section, "days1", fallback=1)
    extension2 = config.get(section, "extension2", fallback=".vis").strip()
    days2 = config.getint(section, "days2", fallback=10)

    if not path or not os.path.exists(path):
        raise ValueError(f"Pfad '{path}' ist ungültig oder existiert nicht.")

    log("🧪 Dry-Run gestartet – keine Dateien werden gelöscht")
    log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    log(f"Suche in {path} nach:\n"
        f"{extension1} älter als {days1} Tage und {extension2} älter als {days2} Tage")

    total_matches = 0
    total_size = 0.0

    for ext, limit in [(extension1, days1), (extension2, days2)]:
        pattern = f"*{ext}" if ext.startswith(".") else ext
        log(f"🔍 Suche nach {pattern}...")

        for filepath in Path(path).rglob(pattern):
            if stop_event and stop_event.is_set():
                log("⛔ Dry-Run wurde vom Benutzer gestoppt.")
                return

            try:
                file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                age_days = (datetime.now() - file_time).days
                size_mb = filepath.stat().st_size / 1024 / 1024

                if age_days >= limit:
                    msg = f"❕ {filepath.name} ({file_time}) würde gelöscht werden"
                    log(msg)
                    total_matches += 1
                    total_size += size_mb
            except Exception as e:
                log(f"⚠️ Fehler bei {filepath}: {e}")

    log(f"\n📋 Dry-Run Ergebnis: {total_matches} Dateien betroffen, {round(total_size, 2)} MB")
    log("💡 Hinweis: Zum tatsächlichen Löschen bitte Löschmodus aktivieren.")
