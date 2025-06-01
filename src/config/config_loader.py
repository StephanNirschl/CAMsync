import configparser
import os
import shutil
from paths import get_config_path

class ConfigLoader:
    def __init__(self, config_path=None, silent=False):
        self.config = configparser.ConfigParser()
        self.config_filename = config_path or get_config_path()

        if not os.path.isabs(self.config_filename):
            self.config_filename = get_config_path()

        loaded_files = self.config.read(self.config_filename)
        if not silent:
            if not loaded_files:
                print(f"⚠️  Konfigurationsdatei konnte nicht gelesen werden: {self.config_filename}")
            else:
                print(f"📄 Lade Konfigurationsdatei: {self.config_filename}")

    def get(self, section, option, fallback=None, dtype=str):
        try:
            value = self.config.get(section, option, fallback=fallback)
            return dtype(value)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback

    def getboolean(self, section, option, fallback=False):
        return self.get(section, option, fallback=fallback, dtype=bool)

    def getint(self, section, option, fallback=0):
        return self.get(section, option, fallback=fallback, dtype=int)

    def getfloat(self, section, option, fallback=0.0):
        return self.get(section, option, fallback=fallback, dtype=float)

    def get_section(self, section):
        try:
            return dict(self.config[section])
        except KeyError:
            return {}