"""
BLE advertisement scanner built on bleak.

bleak uses the native Windows ``Windows.Devices.Bluetooth.Advertisement`` WinRT
API (the same one MagicPods uses) and BlueZ on Linux — so this one module works
on both platforms. We passively listen; we never connect or pair.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from . import protocol
from .protocol import PodsStatus

# callback(address, rssi, status)
StatusCallback = Callable[[str, int, PodsStatus], None]


class Scanner:
    def __init__(self, on_status: StatusCallback, verbose: bool = False) -> None:
        self._on_status = on_status
        self._verbose = verbose
        self._stop = asyncio.Event()

    def _detection(self, device: BLEDevice, adv: AdvertisementData) -> None:
        status = protocol.decode(adv.manufacturer_data)
        if status is None:
            return
        if self._verbose:
            print(f"[scan] {device.address} rssi={adv.rssi}  {status.summary()}"
                  f"  raw={status.raw_hex}")
        self._on_status(device.address, adv.rssi, status)

    async def run(self) -> None:
        """Scan until :meth:`stop` is called."""
        scanner = BleakScanner(detection_callback=self._detection, scanning_mode="active")
        await scanner.start()
        try:
            await self._stop.wait()
        finally:
            await scanner.stop()

    def stop(self) -> None:
        self._stop.set()


def run_in_thread(on_status: StatusCallback, verbose: bool = False) -> "ScannerThread":
    """Start scanning on a private asyncio loop in a daemon thread."""
    return ScannerThread(on_status, verbose)


import threading  # noqa: E402  (kept near its only user)


class ScannerThread:
    def __init__(self, on_status: StatusCallback, verbose: bool) -> None:
        self._scanner: Optional[Scanner] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread = threading.Thread(target=self._entry, args=(on_status, verbose),
                                        daemon=True, name="auris-ble")
        self._thread.start()

    def _entry(self, on_status: StatusCallback, verbose: bool) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._scanner = Scanner(on_status, verbose)
        try:
            self._loop.run_until_complete(self._scanner.run())
        except Exception as exc:  # surface BLE stack errors without dying silently
            print(f"[auris] scanner stopped: {exc!r}")

    def stop(self) -> None:
        if self._scanner and self._loop:
            self._loop.call_soon_threadsafe(self._scanner.stop)
