# -*- mode: python ; coding: utf-8 -*-

import os

# 🔢 Versionsnummer aus src/core/version.py holen
project_dir = os.getcwd()
version_path = os.path.join(project_dir, "src", "core", "version.py")
version_globals = {}
with open(version_path, "r", encoding="utf-8") as f:
    exec(f.read(), version_globals)

__version__ = version_globals.get("__version__", "0.0.0")
exe_name = f"CAMsync_v{__version__}"

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets/default_config.ini', 'assets'),
        ('src/assets/material_mapping.ini', 'assets'),
        ('src/assets/camsync_icon.ico', 'src/assets'),
        ('docs/README.md', 'docs'),
        ('docs/LICENSE', 'docs'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=exe_name,
    icon='src/assets/camsync_icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI-Modus
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)