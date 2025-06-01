
import os
import datetime
import zipfile
from core.logging_utils import get_logger
from config.config_loader import ConfigLoader

DEFAULT_BACKUP_DIR = "data/backups"

def rotate_backups(backup_dir, max_files=20, max_age_days=14, log=None):
    if not os.path.exists(backup_dir):
        return

    files = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if os.path.isfile(os.path.join(backup_dir, f))
    ]

    if not files:
        return

    files_with_time = [(f, os.path.getmtime(f)) for f in files]
    files_with_time.sort(key=lambda x: x[1], reverse=True)

    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=max_age_days)

    files_to_keep = files_with_time[:max_files]
    files_to_delete = [
        (f, ts) for f, ts in files_with_time[max_files:]
        if datetime.datetime.fromtimestamp(ts) < cutoff
    ]

    for f, _ in files_to_delete:
        try:
            os.remove(f)
            if log:
                log(f"🗑️ Backup gelöscht (älter als {max_age_days} Tage oder zu viele): {os.path.basename(f)}")
        except Exception as e:
            if log:
                log(f"❌ Fehler beim Löschen von {f}: {e}")

def delete_old_backups(callback=None, config=None):
    # Konfiguration ggf. laden
    config = config or ConfigLoader(silent=True)

    # Logger initialisieren mit config
    logger = get_logger("backup", config)

    def log(msg):
        logger.info(msg)
        if callback:
            callback(msg)

    config = config or ConfigLoader()
    backup_dir = config.get("tools", "backupdir", fallback=DEFAULT_BACKUP_DIR)
    max_files = config.getint("tools", "backup_max_files", fallback=20)
    max_age_days = config.getint("tools", "backup_max_age_days", fallback=14)

    rotate_backups(backup_dir, max_files=max_files, max_age_days=max_age_days, log=log)

def backup(db, callback=None, config=None):
    # Konfiguration ggf. laden
    config = config or ConfigLoader(silent=True)

    # Logger initialisieren mit config
    logger = get_logger("backup", config)

    def log(msg):
        logger.info(msg)
        if callback:
            callback(msg)

    config = config or ConfigLoader()
    backup_dir = config.get("tools", "backupdir", fallback=DEFAULT_BACKUP_DIR)

    try:
        if not os.path.isfile(db):
            raise FileNotFoundError(f"Datenbankdatei nicht gefunden: {db}")

        os.makedirs(backup_dir, exist_ok=True)
        delete_old_backups(callback=callback, config=config)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(backup_dir, f"db_backup_{timestamp}.zip")

        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(db, os.path.basename(db))

        log(f"✅ Backup erfolgreich erstellt: {backup_file}")

    except Exception as e:
        log(f"❌ Fehler beim Erstellen des Backups: {str(e)}")
        raise
