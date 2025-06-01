import os
import sys
import shutil

def get_appdata_dir():
    return os.path.join(os.getenv("APPDATA"), "CAMsync")

def get_appdata_config_path():
    return os.path.join(get_appdata_dir(), "config.ini")

def get_local_config_path():
    """
    Gibt den Pfad zur config.ini zurück:
    - bei IDE-Start: aus /src/config/
    - bei portabler .exe: aus EXE-Verzeichnis
    """
    if getattr(sys, 'frozen', False):  # .exe Build
        base_dir = os.path.dirname(sys.executable)
        return os.path.join(base_dir, "config.ini")
    else:
        # IDE-Pfad: src/config/config.ini
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_dir, "config", "config.ini")

def get_config_path():
    """
    Bestimmt den aktiven Pfad für config.ini.
    """
    local_path = get_local_config_path()
    if os.path.exists(local_path):
        return local_path
    return get_appdata_config_path()

def ensure_config_exists():
    """
    Stellt sicher, dass eine Konfigurationsdatei vorhanden ist.
    Kopiert aus /assets, falls sie in %APPDATA% fehlt.
    """
    config_path = get_config_path()
    if not os.path.exists(config_path):
        base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
        default_config = os.path.join(base_path, "assets", "default_config.ini")
        if os.path.exists(default_config):
            shutil.copyfile(default_config, config_path)
            print(f"[INFO] Standard-Konfiguration erzeugt unter: {config_path}")
        else:
            print("❌ default_config.ini nicht gefunden!")

def get_material_config_path(filename="material_mapping.ini"):
    """
    Gibt Pfad zu material_mapping.ini zurück.
    - IDE: src/config/
    - EXE: %APPDATA%/
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(get_appdata_dir(), filename)
    else:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_dir, "config", filename)
