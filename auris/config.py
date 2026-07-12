"""Tiny JSON-file config, stored under the user profile (cross-platform)."""

from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "Auris"


def config_dir() -> Path:
    """Per-user config directory, respecting platform conventions."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    # Linux / macOS
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME.lower()


DEFAULTS: dict = {
    # Notify once when any component drops to/below this percentage. 0 disables.
    "low_battery_threshold": 20,
    # Show a notification when a device connects.
    "notify_on_connect": True,
    # Seconds without an advertisement before we consider a device gone.
    "disconnect_timeout": 30,
    # Log decoded advertisements to the console.
    "verbose": False,
}


class Config:
    def __init__(self) -> None:
        self.path = config_dir() / "config.json"
        self.data = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def __getitem__(self, key: str):
        return self.data.get(key, DEFAULTS.get(key))

    def __setitem__(self, key: str, value) -> None:
        self.data[key] = value
        self.save()
