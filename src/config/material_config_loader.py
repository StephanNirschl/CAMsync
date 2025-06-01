import configparser
import os
import shutil
import sys
from paths import get_material_config_path

class MaterialConfigLoader:
    def __init__(self, filename="material_mapping.ini", silent=False):
        self.config = configparser.RawConfigParser()
        self.config_path = get_material_config_path(filename)

        # Falls Datei fehlt → aus assets kopieren (nur bei EXE)
        if not os.path.exists(self.config_path) and getattr(sys, 'frozen', False):
            base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
            default_path = os.path.join(base_path, "assets", filename)
            if os.path.exists(default_path):
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                shutil.copy(default_path, self.config_path)
                if not silent:
                    print(f"📄 Material-Mapping kopiert nach: {self.config_path}")
            else:
                if not silent:
                    print(f"❌ Material-Mapping-Default fehlt: {default_path}")

        loaded = self.config.read(self.config_path)
        if not silent:
            if not loaded:
                print(f"⚠️ Material-Konfig konnte nicht geladen werden: {self.config_path}")
            else:
                print(f"📄 Lade Material-Mapping: {self.config_path}")

    def get_mapping(self, section="Materialersetzung"):
        try:
            return dict(self.config[section])
        except KeyError:
            return {}