import subprocess
from pathlib import Path

# Pfad zur automatisch erzeugten Version
version_file = Path("src/core/version.py")


def get_git_version():
    try:
        # Holt z. B. "v0.1.7-2-gb4c5b21" aus Git
        version = subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return version.lstrip("v")
    except Exception:
        return "0.0.0"  # Fallback wenn kein Git-Repo oder kein Tag vorhanden


def write_version_file(version: str):
    content = f'__version__ = "{version}"\n'
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    version = get_git_version()
    write_version_file(version)
    print(f"[OK] version.py aktualisiert: {version_file} -> {version}")
    