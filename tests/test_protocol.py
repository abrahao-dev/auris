"""
Unit tests for the Apple Continuity decoder.

Advertisements are hand-built so the expected battery values are known exactly.
Run with:  python -m pytest    (or plain `python tests/test_protocol.py`)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auris import models, protocol  # noqa: E402


def _mfg(hexstr: str) -> dict[int, bytes]:
    return {models.APPLE_COMPANY_ID: bytes.fromhex(hexstr)}


def test_airpods_pro_not_flipped():
    # type=07 len=19 pfx=01 model=0e20 status=21 batt=9a charge/case=46 ...
    adv = _mfg("0719010e20219a4600" + "00" * 18)
    s = protocol.decode(adv)
    assert s is not None
    assert s.model_id == "0e20"
    assert s.model_name == "AirPods Pro"
    assert s.family == models.FAMILY_BUDS
    assert s.left.percent == 100 and not s.left.charging
    assert s.right.percent == 90 and not s.right.charging
    assert s.case.percent == 60 and s.case.charging


def test_flip_bit_swaps_pods():
    # status=01 -> high nibble 0 -> flip True; batt=80 -> pod_a=8, pod_b=0
    adv = _mfg("0719010e20018000" + "00" * 19)
    s = protocol.decode(adv)
    assert s is not None
    # flip True => left = pod_a = 8 -> 80%, right = pod_b = 0 -> 0%
    assert s.left.percent == 80
    assert s.right.percent == 0


def test_airpods_max_single_battery():
    adv = _mfg("0719010a2001800f" + "00" * 19)
    s = protocol.decode(adv)
    assert s is not None
    assert s.model_name == "AirPods Max"
    assert s.family == models.FAMILY_SINGLE
    assert s.single.percent == 80
    # case nibble 0xF -> unavailable
    assert s.case.percent is None


def test_unavailable_nibble_is_none():
    # both pod nibbles 0xF -> not present
    adv = _mfg("0719010e2021ff0f" + "00" * 19)
    s = protocol.decode(adv)
    assert s is not None
    assert s.left.percent is None
    assert s.right.percent is None


def test_unknown_model_degrades_gracefully():
    adv = _mfg("07190199990000" + "00" * 20)
    s = protocol.decode(adv)
    assert s is not None
    assert "Unknown" in s.model_name


def test_non_apple_payload_rejected():
    assert protocol.decode({0x0075: b"\x01\x02\x03"}) is None


def test_wrong_message_type_rejected():
    # first byte 0x10 is not proximity-pairing (0x07)
    assert protocol.decode(_mfg("1019010e20219a4600" + "00" * 18)) is None


def test_summary_formats():
    adv = _mfg("0719010e20219a4600" + "00" * 18)
    s = protocol.decode(adv)
    line = s.summary()
    assert "AirPods Pro" in line and "L 100%" in line and "R 90%" in line


def test_in_ear_flag_parsed():
    # status byte 0x23 has the in-ear bit (0x02) set; 0x21 does not.
    assert protocol.decode(_mfg("0719010e20239a4600" + "00" * 18)).in_ear is True
    assert protocol.decode(_mfg("0719010e20219a4600" + "00" * 18)).in_ear is False


def test_in_ear_none_for_single_devices():
    # AirPods Max (single battery) doesn't expose per-pod in-ear here.
    s = protocol.decode(_mfg("0719010a2023800f" + "00" * 19))
    assert s.in_ear is None


def test_auto_pause_transition_logic():
    # Exercise the app's edge detection without a real tray or media session.
    # Skips when GUI deps (pystray) aren't installed, e.g. the lean CI job.
    import types

    try:
        from auris import app as app_mod
    except ImportError:
        print("  skip test_auto_pause_transition_logic (pystray not installed)")
        return

    events = []
    dev = app_mod.Device("AA", protocol.decode(_mfg("0719010e20239a4600" + "00" * 18)))
    fake = types.SimpleNamespace(config={"auto_pause": True})
    handler = app_mod.AurisApp._maybe_auto_pause

    orig_play, orig_pause = app_mod.media.play, app_mod.media.pause
    app_mod.media.play = lambda: events.append("play")
    app_mod.media.pause = lambda: events.append("pause")
    try:
        out = protocol.decode(_mfg("0719010e20219a4600" + "00" * 18))   # in_ear False
        handler(fake, dev, out)                                          # -> pause
        back = protocol.decode(_mfg("0719010e20239a4600" + "00" * 18))  # in_ear True
        handler(fake, dev, back)                                         # -> play
    finally:
        app_mod.media.play, app_mod.media.pause = orig_play, orig_pause
    assert events == ["pause", "play"], events


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
