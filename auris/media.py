"""
Cross-platform media play/pause, used by the auto-pause feature.

Windows: synthesize the VK_MEDIA_PLAY_PAUSE virtual key via the Win32 API.
Linux:   `playerctl` if installed (MPRIS), else a no-op.

We only ever send play/pause — never anything destructive.
"""

from __future__ import annotations

import os
import shutil
import subprocess

_VK_MEDIA_PLAY_PAUSE = 0xB3
_KEYEVENTF_KEYUP = 0x0002


def _win_play_pause() -> None:
    import ctypes

    user32 = ctypes.windll.user32
    user32.keybd_event(_VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    user32.keybd_event(_VK_MEDIA_PLAY_PAUSE, 0, _KEYEVENTF_KEYUP, 0)


def _linux_cmd(action: str) -> None:
    if shutil.which("playerctl"):
        subprocess.run(["playerctl", action], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def toggle() -> None:
    """Toggle play/pause of the current media session."""
    try:
        if os.name == "nt":
            _win_play_pause()
        else:
            _linux_cmd("play-pause")
    except Exception:
        pass  # media control is a convenience, never fatal


def pause() -> None:
    if os.name == "nt":
        toggle()  # Windows only exposes a single toggle key
    else:
        try:
            _linux_cmd("pause")
        except Exception:
            pass


def play() -> None:
    if os.name == "nt":
        toggle()
    else:
        try:
            _linux_cmd("play")
        except Exception:
            pass
