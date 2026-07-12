# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for Auris (cross-platform).

  Windows -> dist/Auris.exe        (windowed, single file)
  Linux   -> dist/auris-linux      (single file)

Build:  pyinstaller Auris.spec
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

IS_WIN = sys.platform.startswith("win")
# Distribution build is windowed on Windows. Set AURIS_BUILD_CONSOLE=1 to force a
# console subsystem so `--selftest` output is visible when smoke-testing.
CONSOLE = (not IS_WIN) or os.environ.get("AURIS_BUILD_CONSOLE") == "1"

datas, binaries, hiddenimports = [], [], []


def _add(pkg):
    d, b, h = collect_all(pkg)
    datas.extend(d)
    binaries.extend(b)
    hiddenimports.extend(h)


# Core deps that PyInstaller can't fully trace on its own.
_add("bleak")
hiddenimports += collect_submodules("pystray")

if IS_WIN:
    # bleak's WinRT backend rides on the split winrt-Windows.* projection
    # packages; they are namespace packages PyInstaller misses without help.
    _add("winrt")
    _add("winotify")
    hiddenimports += [
        "winrt.windows.devices.bluetooth",
        "winrt.windows.devices.bluetooth.advertisement",
        "winrt.windows.devices.enumeration",
        "winrt.windows.devices.radios",
        "winrt.windows.foundation",
        "winrt.windows.foundation.collections",
        "winrt.windows.storage.streams",
    ]
else:
    # Linux BlueZ backend (dbus-fast) + the pure-python Xorg tray backend, which
    # is always bundleable. Users wanting the richer AppIndicator tray can run
    # from source with PyGObject installed.
    hiddenimports += collect_submodules("dbus_fast")
    hiddenimports += collect_submodules("Xlib")

TARGET_NAME = "Auris" if IS_WIN else "auris-linux"


a = Analysis(
    ["packaging/entry.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=TARGET_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Windowed on Windows (tray app, no console flash); console on Linux is fine.
    console=CONSOLE,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
