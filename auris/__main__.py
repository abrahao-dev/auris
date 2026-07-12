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


def main() -> None:
    parser = argparse.ArgumentParser(prog="auris", description=__doc__)
    parser.add_argument("--version", action="version", version=f"Auris {__version__}")
    parser.add_argument("--cli", action="store_true",
                        help="headless mode: print decoded status to stdout")
    args = parser.parse_args()

    if args.cli:
        _cli()
    else:
        from .app import main as run_app
        run_app()


if __name__ == "__main__":
    main()
