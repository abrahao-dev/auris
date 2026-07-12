"""
Auris application: wires the BLE scanner to a system-tray icon.

Threading model (same shape as MagicPods' UI <-> service split):
  * main thread  -> pystray icon event loop (must own the main thread)
  * daemon thread-> asyncio BLE scanner, pushing decoded status back
"""

from __future__ import annotations

import time
from typing import Optional

import pystray
from PIL import Image

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
        if not self.devices:
            return "No AirPods detected"
        return "  |  ".join(d.status.summary() for d in self.devices.values())

    # ---- scanner callback (runs on the BLE thread) --------------------------
    def _on_status(self, address: str, rssi: int, status: PodsStatus) -> None:
        is_new = address not in self.devices
        dev = self.devices.get(address)
        if dev is None:
            dev = Device(address, status)
            self.devices[address] = dev
            if self.config["notify_on_connect"]:
                notifications.notify("Auris", f"Connected: {status.summary()}")
        else:
            dev.status = status
            dev.last_seen = time.monotonic()

        self._check_low_battery(dev)
        self._prune()
        self._refresh_icon()
        if is_new:
            self.icon.menu = self._build_menu()

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
        gone = [a for a, d in self.devices.items() if now - d.last_seen > timeout]
        for a in gone:
            del self.devices[a]
        if gone:
            self.icon.menu = self._build_menu()

    def _lowest_component(self) -> tuple[Optional[int], bool]:
        """Lowest live battery across all devices, for the tray glyph."""
        best: Optional[int] = None
        charging = False
        for dev in self.devices.values():
            for _name, p in self._component_levels(dev.status):
                if p is None:
                    continue
                if best is None or p < best:
                    best = p
                    # charging if any component of that device is charging
                    s = dev.status
                    charging = any(
                        b.charging for b in (s.left, s.right, s.case, s.single)
                    )
        return best, charging

    def _refresh_icon(self) -> None:
        percent, charging = self._lowest_component()
        img: Image.Image = icon_render.render(percent, charging)
        self.icon.icon = img
        self.icon.title = self._status_line()


def main() -> None:
    AurisApp().run()


if __name__ == "__main__":
    main()
