import logging
import os
from config.config_loader import ConfigLoader


def get_logger(name: str, config: ConfigLoader) -> logging.Logger:
    """
    Gibt einen Logger zurück, der sowohl in eine Datei als auch in die Konsole schreibt.
    
    :param name: Name des Moduls (z.B. "tool_rework", "cleanup")
    :param config: Instanz von ConfigLoader mit gültiger Konfiguration
    :return: logging.Logger-Instanz
    """

    # 📁 Log-Verzeichnis ermitteln
    log_dir = os.path.dirname(
        config.get("logging", "logfile", fallback="logs/default.log")
    ) or "logs"

    if name == "cleanup":
        log_dir = config.get("cleanup", "logfile1", fallback=log_dir)

    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 📝 Datei-Logging
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 🖥 Konsolen-Logging
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger