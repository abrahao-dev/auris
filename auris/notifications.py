"""
Cross-platform desktop notifications with graceful fallbacks.

Windows : winotify (native toast) if available.
Linux   : `notify-send` (libnotify) if available.
Fallback: print to stdout so nothing is lost.
"""

from __future__ import annotations

import os
import shutil
import subprocess

APP_NAME = "Auris"

_backend = None


def _detect_backend() -> str:
    global _backend
    if _backend is not None:
        return _backend
    if os.name == "nt":
        try:
            import winotify  # noqa: F401

            _backend = "winotify"
            return _backend
        except ImportError:
            _backend = "print"
            return _backend
    if shutil.which("notify-send"):
        _backend = "notify-send"
    else:
        _backend = "print"
    return _backend


def notify(title: str, message: str) -> None:
    backend = _detect_backend()
    try:
        if backend == "winotify":
            from winotify import Notification

            Notification(app_id=APP_NAME, title=title, msg=message).show()
            return
        if backend == "notify-send":
            subprocess.run(
                ["notify-send", "-a", APP_NAME, title, message],
                check=False,
            )
            return
    except Exception:
        pass  # never let a notification failure crash the app
    print(f"[{APP_NAME}] {title}: {message}")
