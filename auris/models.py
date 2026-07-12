"""
Apple device model-ID table.

Apple encodes a 16-bit model identifier inside its BLE "proximity pairing"
advertisement (see ``protocol.py``). The same IDs are used by iOS/macOS and by
the closed-source MagicPods app, whose bundled asset folders
(``Assets/Headphones/4c00/<id>``) confirmed the exact set of IDs recognised
below.

Values are the model id as it appears big-endian in the advertisement, e.g.
AirPods Pro advertise ``0x0E20`` -> looked up here as the string ``"0e20"``.

The AirPods entries are high-confidence (Apple + cross-checked community data).
The Beats entries are community-sourced (OpenPods / LibrePods / AirStatus) and
may be imprecise; unknown-but-recognised IDs still resolve to a friendly label
so the app degrades gracefully.
"""

from __future__ import annotations

# Apple's Bluetooth SIG company identifier.
APPLE_COMPANY_ID = 0x004C

# family -> which battery components the device reports.
# "buds"  = left + right + case
# "single"= one battery (e.g. AirPods Max, single-can headphones)
FAMILY_BUDS = "buds"
FAMILY_SINGLE = "single"

# id -> (display name, family)
MODELS: dict[str, tuple[str, str]] = {
    # ---- AirPods (high confidence) ----
    "0220": ("AirPods (1st generation)", FAMILY_BUDS),
    "0f20": ("AirPods (2nd generation)", FAMILY_BUDS),
    "1320": ("AirPods (3rd generation)", FAMILY_BUDS),
    "1920": ("AirPods (4th generation)", FAMILY_BUDS),
    "1b20": ("AirPods (4th generation, ANC)", FAMILY_BUDS),
    "0e20": ("AirPods Pro", FAMILY_BUDS),
    "1420": ("AirPods Pro (2nd generation)", FAMILY_BUDS),
    "2420": ("AirPods Pro (2nd generation, USB-C)", FAMILY_BUDS),
    "0a20": ("AirPods Max", FAMILY_SINGLE),
    "2d20": ("AirPods Max (USB-C)", FAMILY_SINGLE),
    # ---- Beats (community sourced) ----
    "0520": ("Powerbeats3", FAMILY_BUDS),
    "0620": ("Beats Solo3 / Studio3", FAMILY_SINGLE),
    "0920": ("BeatsX", FAMILY_BUDS),
    "0b20": ("Beats Studio3", FAMILY_SINGLE),
    "0c20": ("Beats Flex", FAMILY_BUDS),
    "1020": ("Beats Solo Pro", FAMILY_SINGLE),
    "1120": ("Powerbeats Pro", FAMILY_BUDS),
    "1220": ("Powerbeats (2020)", FAMILY_BUDS),
    "1620": ("Beats Fit Pro", FAMILY_BUDS),
    "1720": ("Beats Studio Buds", FAMILY_BUDS),
    "1a20": ("Beats Flex", FAMILY_BUDS),
    "1d20": ("Beats Studio Buds+", FAMILY_BUDS),
    "2f20": ("Beats Studio Pro", FAMILY_SINGLE),
    # ---- Recognised but not confidently named (from MagicPods asset set) ----
    "0320": ("Apple/Beats device", FAMILY_BUDS),
    "0d20": ("Apple/Beats device", FAMILY_BUDS),
    "2520": ("Apple/Beats device", FAMILY_BUDS),
    "2620": ("Apple/Beats device", FAMILY_BUDS),
    "2720": ("Apple/Beats device", FAMILY_BUDS),
    "1f20": ("Apple/Beats device", FAMILY_BUDS),
}


def lookup(model_id: str) -> tuple[str, str]:
    """Return ``(display_name, family)`` for a lowercase 4-hex model id."""
    key = model_id.lower()
    if key in MODELS:
        return MODELS[key]
    return (f"Unknown AirPods/Beats (0x{key})", FAMILY_BUDS)
