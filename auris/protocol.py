"""
Decoder for Apple's proprietary BLE "proximity pairing" advertisement.

This is the heart of Auris. AirPods / Beats continuously broadcast an
unencrypted-enough BLE advertisement under Apple's manufacturer-data company id
``0x004C``. Part of that payload (the "proximity pairing" message, type ``0x07``)
carries live status: per-earbud and case battery, charging flags, lid state and
the device model. Apple's own software and closed-source tools like MagicPods
read exactly this. Auris decodes it in the open.

Nothing here talks to the device: we only *listen* to broadcast advertisements,
so no pairing, no keys and no writes are involved.

Payload layout (bytes, after the 0x004C company id is stripped by the BLE stack)
------------------------------------------------------------------------------
    off  hex   meaning
    0    07    message type: 0x07 == proximity pairing
    1    19    remaining length (usually 25)
    2    01    prefix / device count
    3-4  ....   model id, big-endian (e.g. 0E 20 -> "0e20" == AirPods Pro)
    5    ..    status byte (contains the "flip" bit: which physical pod is
               reported first, plus in-ear-ish flags)
    6    ..    battery nibbles: high nibble = pod A, low nibble = pod B
    7    ..    high nibble = charging flags, low nibble = case battery
    8    ..    lid open counter / state (case)
    9    ..    device color
    10   ..    reserved
    11+  ....   encrypted remainder (not used here)

Battery nibble encoding: value 0..10 -> that many *10 percent (10 == 100%).
Value 15 (0xF) means "not available" (pod out / disconnected).

The nibble/bit offsets follow the well-established community reverse engineering
(OpenPods, AirStatus, LibrePods), which we re-document rather than copy blindly.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

from . import models

PROXIMITY_PAIRING_TYPE = 0x07
_UNAVAILABLE_NIBBLE = 0x0F


@dataclass
class Battery:
    """A single battery component. ``percent`` is None when unavailable."""

    percent: Optional[int]
    charging: bool

    @property
    def present(self) -> bool:
        return self.percent is not None


@dataclass
class PodsStatus:
    """Fully decoded status of one AirPods/Beats device."""

    model_id: str
    model_name: str
    family: str
    left: Battery
    right: Battery
    case: Battery
    # "single" devices (Max, over-ear Beats) report one battery -> `.single`.
    single: Battery
    lid_open: Optional[bool]
    # Best-effort in-ear signal from the broadcast status byte. Robust per-pod
    # ear detection needs a connected AAP session, so this is experimental and
    # only consumed by the (off-by-default) auto-pause feature.
    in_ear: Optional[bool]
    status_flags: int
    raw_hex: str

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def summary(self) -> str:
        """One-line human summary, e.g. 'AirPods Pro  L 90%  R 85%  Case 60%'."""
        parts = [self.model_name]
        if self.family == models.FAMILY_SINGLE:
            parts.append(_fmt("", self.single))
        else:
            parts.append(_fmt("L", self.left))
            parts.append(_fmt("R", self.right))
            parts.append(_fmt("Case", self.case))
        return "  ".join(p for p in parts if p)


def _fmt(label: str, b: Battery) -> str:
    if not b.present:
        return ""
    bolt = "⚡" if b.charging else ""
    return f"{label} {b.percent}%{bolt}".strip()


def _nibble_to_percent(n: int) -> Optional[int]:
    """Apple battery nibble -> percentage (0..100) or None if unavailable."""
    if n == _UNAVAILABLE_NIBBLE or n > 10:
        return None
    return n * 10


def decode(manufacturer_data: dict[int, bytes]) -> Optional[PodsStatus]:
    """Decode a bleak ``manufacturer_data`` dict.

    Returns a :class:`PodsStatus`, or ``None`` if the advertisement is not an
    Apple proximity-pairing message we understand.
    """
    payload = manufacturer_data.get(models.APPLE_COMPANY_ID)
    if payload is None:
        return None
    return decode_payload(payload)


def decode_payload(payload: bytes) -> Optional[PodsStatus]:
    """Decode the raw Apple manufacturer-data payload (company id stripped)."""
    if len(payload) < 16:
        return None
    if payload[0] != PROXIMITY_PAIRING_TYPE:
        return None

    h = payload.hex()

    # Model id lives in bytes 3-4 == hex chars [6:10], big-endian.
    model_id = h[6:10]
    model_name, family = models.lookup(model_id)

    # The "flip" bit tells us which physical pod the first battery nibble is.
    # bit 1 of the high nibble of the status byte (payload[5]).
    flip = (int(h[10], 16) & 0x02) == 0

    # Battery nibbles: payload[6] holds both pods, payload[7] low nibble = case.
    pod_a = int(h[12], 16)
    pod_b = int(h[13], 16)
    case_n = int(h[15], 16)

    left_n = pod_a if flip else pod_b
    right_n = pod_b if flip else pod_a

    # Charging flags: high nibble of payload[7].
    charge = int(h[14], 16)
    if flip:
        charging_left = bool(charge & 0x01)
        charging_right = bool(charge & 0x02)
    else:
        charging_left = bool(charge & 0x02)
        charging_right = bool(charge & 0x01)
    charging_case = bool(charge & 0x04)

    left = Battery(_nibble_to_percent(left_n), charging_left)
    right = Battery(_nibble_to_percent(right_n), charging_right)
    case = Battery(_nibble_to_percent(case_n), charging_case)

    # Single-battery devices (AirPods Max, over-ear Beats) put their level in
    # the first pod nibble; the other nibbles are unused/0xF.
    single = left if left.present else right

    # Lid state (case): payload[8] high nibble is the lid-open counter; the low
    # bit distinguishes open/closed on cases that report it. Best-effort only.
    lid_open: Optional[bool] = None
    if len(payload) > 8:
        lid_byte = payload[8]
        lid_open = bool(lid_byte & 0x08) if family == models.FAMILY_BUDS else None

    # Status byte (payload[5]) carries in-ear-related flags. The exact semantics
    # vary and are only fully reliable over a connected session, so we expose a
    # best-effort "at least one pod in ear" signal for the experimental
    # auto-pause feature. Bit 0x02 of the low nibble tracks in-ear on the models
    # tested by the community; unknown => None.
    status_flags = payload[5]
    in_ear: Optional[bool] = None
    if family == models.FAMILY_BUDS:
        in_ear = bool(status_flags & 0x02)

    return PodsStatus(
        model_id=model_id,
        model_name=model_name,
        family=family,
        left=left,
        right=right,
        case=case,
        single=single,
        lid_open=lid_open,
        in_ear=in_ear,
        status_flags=status_flags,
        raw_hex=h,
    )
