"""Entry point: ``python -m auris``.

Supports a headless ``--cli`` mode for debugging the decoder without a tray.
"""

from __future__ import annotations

import argparse
import asyncio

from . import __version__


def _cli() -> None:
    """Print decoded advertisements to the console (no tray)."""
    from .scanner import Scanner

    def on_status(address, rssi, status):
        print(f"{address}  rssi={rssi:>4}  {status.summary()}")

    scanner = Scanner(on_status, verbose=False)
    print("Auris CLI — listening for AirPods/Beats advertisements. Ctrl+C to stop.")
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        pass


def _selftest() -> int:
    """Import every module and exercise the core paths. Used to smoke-test a
    frozen (PyInstaller) build: it proves all dependencies were bundled."""
    import os

    from . import icon, models, protocol, scanner, app, notifications, config  # noqa
    import bleak  # noqa

    # Confirm the platform BLE backend was bundled.
    if os.name == "nt":
        from bleak.backends.winrt.scanner import BleakScannerWinRT  # noqa
    else:
        from bleak.backends.bluezdbus.scanner import BleakScannerBlueZDBus  # noqa

    img = icon.render(42, charging=True)
    assert img.size == (icon.SIZE, icon.SIZE)
    adv = {models.APPLE_COMPANY_ID: bytes.fromhex("0719010e20219a4600" + "00" * 18)}
    s = protocol.decode(adv)
    assert s and s.left.percent == 100 and s.model_name == "AirPods Pro"
    print(f"Auris {__version__} selftest OK — {s.summary()}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="auris", description=__doc__)
    parser.add_argument("--version", action="version", version=f"Auris {__version__}")
    parser.add_argument("--cli", action="store_true",
                        help="headless mode: print decoded status to stdout")
    parser.add_argument("--selftest", action="store_true",
                        help="verify the (possibly frozen) build loads and exit")
    args = parser.parse_args()

    if args.selftest:
        raise SystemExit(_selftest())
    if args.cli:
        _cli()
    else:
        from .app import main as run_app
        run_app()


if __name__ == "__main__":
    main()
