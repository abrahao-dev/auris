"""
Auris application: wires the BLE scanner to a system-tray icon.

Threading model (same shape as MagicPods' UI <-> service split):
  * main thread  -> pystray icon event loop (must own the main thread)
  * daemon thread-> asyncio BLE scanner, pushing decoded status back
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import pystray

from . import icon as icon_render
from . import notifications, scanner
from .config import Config
from .models import FAMILY_SINGLE
from .protocol import PodsStatus


class Device:
    """Tracks the last-seen status of one physical device."""

    def __init__(self, address: str, status: PodsStatus) -> None:
        self.address = address
        self.status = status
        self.last_seen = time.monotonic()
        self.low_notified = False


class AurisApp:
    def __init__(self) -> None:
        self.config = Config()
        self.devices: dict[str, Device] = {}
        # Advertisements arrive on the BLE thread; the tray reads on the main
        # thread. This lock guards the shared device map.
        self._lock = threading.Lock()
        # Cache the last rendered glyph/title so we only touch the tray (and
        # re-draw a PIL image) when the visible state actually changes.
        self._last_icon_key: object = None
        self._last_title: Optional[str] = None
        self.icon = pystray.Icon(
            "auris",
            icon=icon_render.default_icon(),
            title="Auris — scanning…",
            menu=self._build_menu(),
        )
        self._scanner: Optional[scanner.ScannerThread] = None

    # ---- lifecycle ----------------------------------------------------------
    def run(self) -> None:
        self._scanner = scanner.run_in_thread(
            self._on_status, verbose=self.config["verbose"]
        )
        self.icon.run(setup=self._setup)

    def _setup(self, icon: pystray.Icon) -> None:
        icon.visible = True

    def _quit(self, icon: pystray.Icon, _item) -> None:
        if self._scanner:
            self._scanner.stop()
        icon.visible = False
        icon.stop()

    # ---- menu ---------------------------------------------------------------
    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(lambda _i: self._status_line(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _status_line(self) -> str:
        with self._lock:
            if not self.devices:
                return "No AirPods detected"
            return "  |  ".join(d.status.summary() for d in self.devices.values())

    # ---- scanner callback (runs on the BLE thread) --------------------------
    def _on_status(self, address: str, rssi: int, status: PodsStatus) -> None:
        connected = None
        with self._lock:
            dev = self.devices.get(address)
            if dev is None:
                dev = Device(address, status)
                self.devices[address] = dev
                connected = status.summary()
            else:
                dev.status = status
                dev.last_seen = time.monotonic()

        # Notify outside the lock (toasts can block briefly).
        if connected is not None and self.config["notify_on_connect"]:
            notifications.notify("Auris", f"Connected: {connected}")

        self._check_low_battery(dev)
        self._prune()
        self._refresh_icon()
        # The menu structure is constant; its text is a live callable, so it
        # never needs rebuilding when devices change.

    # ---- helpers ------------------------------------------------------------
    def _check_low_battery(self, dev: Device) -> None:
        threshold = self.config["low_battery_threshold"]
        if not threshold:
            return
        levels = self._component_levels(dev.status)
        low = [(n, p) for n, p in levels if p is not None and p <= threshold]
        if low and not dev.low_notified:
            names = ", ".join(f"{n} {p}%" for n, p in low)
            notifications.notify("Auris — low battery", f"{dev.status.model_name}: {names}")
            dev.low_notified = True
        elif not low:
            dev.low_notified = False

    @staticmethod
    def _component_levels(status: PodsStatus):
        if status.family == FAMILY_SINGLE:
            return [("Battery", status.single.percent)]
        return [
            ("Left", status.left.percent),
            ("Right", status.right.percent),
            ("Case", status.case.percent),
        ]

    def _prune(self) -> None:
        timeout = self.config["disconnect_timeout"]
        now = time.monotonic()
        with self._lock:
            gone = [a for a, d in self.devices.items() if now - d.last_seen > timeout]
            for a in gone:
                del self.devices[a]

    def _lowest_component(self) -> tuple[Optional[int], bool]:
        """Lowest live battery across all devices, for the tray glyph."""
        best: Optional[int] = None
        charging = False
        with self._lock:
            statuses = [d.status for d in self.devices.values()]
        for s in statuses:
            for _name, p in self._component_levels(s):
                if p is None:
                    continue
                if best is None or p < best:
                    best = p
                    # charging if any component of that device is charging
                    charging = any(
                        b.charging for b in (s.left, s.right, s.case, s.single)
                    )
        return best, charging

    def _refresh_icon(self) -> None:
        percent, charging = self._lowest_component()
        key = (percent, charging)
        # Only redraw / touch the tray when the visible state changed. Skips a
        # PIL render on every advertisement (there can be several per second).
        if key != self._last_icon_key:
            self.icon.icon = icon_render.render(percent, charging)
            self._last_icon_key = key
        title = self._status_line()
        if title != self._last_title:
            self.icon.title = title
            self._last_title = title


def main() -> None:
    AurisApp().run()


if __name__ == "__main__":
    main()
