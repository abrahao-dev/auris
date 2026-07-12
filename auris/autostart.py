"""
Start Auris automatically when the user logs in.

Windows: a value under HKCU\\...\\CurrentVersion\\Run (no admin needed).
Linux:   a .desktop file in ~/.config/autostart.

Works both for the frozen one-file build (points at the .exe / binary) and for
`python -m auris` during development.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Auris"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_command() -> str:
    """The command that should run at login."""
    if getattr(sys, "frozen", False):
        # PyInstaller one-file build: launch the executable directly.
        return f'"{sys.executable}"'
    # Dev mode: run the module with the windowless interpreter if available.
    exe = sys.executable
    pyw = Path(exe).with_name("pythonw.exe")
    launcher = str(pyw) if pyw.exists() else exe
    return f'"{launcher}" -m auris'


# --------------------------------------------------------------------------- #
# Windows
# --------------------------------------------------------------------------- #
def _win_enable() -> None:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _launch_command())


def _win_disable() -> None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


def _win_is_enabled() -> bool:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False


# --------------------------------------------------------------------------- #
# Linux (freedesktop autostart)
# --------------------------------------------------------------------------- #
def _linux_desktop_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "autostart" / "auris.desktop"


def _linux_enable() -> None:
    path = _linux_desktop_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    exec_cmd = _launch_command().replace('"', "")
    path.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={exec_cmd}\n"
        "X-GNOME-Autostart-enabled=true\n"
        "Terminal=false\n",
        encoding="utf-8",
    )


def _linux_disable() -> None:
    _linux_desktop_path().unlink(missing_ok=True)


def _linux_is_enabled() -> bool:
    return _linux_desktop_path().exists()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def is_enabled() -> bool:
    try:
        return _win_is_enabled() if os.name == "nt" else _linux_is_enabled()
    except OSError:
        return False


def set_enabled(enabled: bool) -> bool:
    """Enable/disable autostart. Returns the resulting state (best-effort)."""
    try:
        if os.name == "nt":
            _win_enable() if enabled else _win_disable()
        else:
            _linux_enable() if enabled else _linux_disable()
    except OSError:
        pass
    return is_enabled()
