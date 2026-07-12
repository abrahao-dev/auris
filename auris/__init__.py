"""Auris — an open-source AirPods & Bluetooth-earbuds companion for Windows & Linux."""

import sys as _sys

__version__ = "0.2.0"

# Windows consoles default to a legacy codepage (cp1252) that can't encode the
# emoji we use in status lines (⚡). Make our stdout/stderr UTF-8 so --cli and
# verbose modes never crash on a plain console. No-op where already UTF-8.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
