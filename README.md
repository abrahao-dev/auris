# Auris

**An open-source AirPods & Bluetooth-earbuds companion for Windows and Linux.**

Auris shows your **AirPods / Beats battery** (left, right, case), charging state and
low-battery alerts from a system-tray icon — the features Windows normally hides.
It's a free, transparent alternative to closed-source apps like MagicPods, and it
runs on **Linux** too from the same codebase.

> Auris only *listens* to the Bluetooth Low Energy advertisements your earbuds
> already broadcast. It never pairs, connects, writes, or phones home.

---

## Features

- 🔋 Live **left / right / case** battery percentages
- ⚡ **Charging** indicator per component
- 🎧 Works with **AirPods** (1–4, Pro, Pro 2, Max) and many **Beats** models
- 🔔 **Low-battery** and **connect** notifications (native toast on Windows, `notify-send` on Linux)
- 🖼️ Battery ring drawn onto the **tray icon** for an at-a-glance read
- 🪟 **Windows** + 🐧 **Linux** (BlueZ) from one Python codebase
- 🧾 MIT-licensed, no telemetry, ~600 lines of readable code

## Quick start

```bash
git clone <your-fork-url> auris
cd auris
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux: source .venv/bin/activate
pip install -r requirements.txt

# Tray app:
python -m auris

# Headless debug (prints decoded advertisements, no tray):
python -m auris --cli
```

Requires Python 3.10+ and a Bluetooth LE adapter. On Linux you need BlueZ
(`bluez`) and permission to scan (run in a `bluetooth` group or via `sudo`).

## How it works

Apple earbuds continuously broadcast a BLE advertisement under Apple's
manufacturer-data **company id `0x004C`**. Inside it is a *proximity-pairing*
message (type `0x07`) that encodes battery, charging and lid state in the clear.
Apple's own OS and closed apps read this same broadcast; Auris just decodes it
openly.

```
manufacturer_data[0x004C] payload (company id already stripped):

  off  value  meaning
  0    07     message type = proximity pairing
  1    19     length (25)
  2    01     prefix / device count
  3-4  ....   model id, big-endian  (0E20 = AirPods Pro, 0A20 = AirPods Max, …)
  5    ..     status byte — includes the "flip" bit (which pod is reported first)
  6    ..     battery: high nibble = pod A, low nibble = pod B
  7    ..     high nibble = charging flags, low nibble = case battery
  8    ..     lid / case state
  9+   ....   color, then encrypted remainder (unused)

battery nibble: 0..10 -> ×10 percent (10 = 100%);  0xF = unavailable
charging flags: bit for each pod (assigned via the flip bit) + bit 2 = case
```

The model-id table in [`auris/models.py`](auris/models.py) was cross-checked
against the asset folders bundled with MagicPods (`Assets/Headphones/4c00/<id>`),
which enumerate every id it recognises. The AirPods entries are high-confidence;
Beats ids are community-sourced (OpenPods / AirStatus / LibrePods) and marked as
such.

See [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for the full write-up.

## Architecture

```
auris/
  protocol.py      Apple Continuity decoder  ← the core (fully unit-tested)
  models.py        model-id → name/family table
  scanner.py       bleak BLE advertisement scanner (WinRT on Windows, BlueZ on Linux)
  icon.py          Pillow battery-ring tray-icon renderer
  notifications.py cross-platform toasts (winotify / notify-send / stdout)
  config.py        JSON config under the user profile
  app.py           tray + state tracking + notifications (orchestrator)
  __main__.py      `python -m auris` entry point (+ --cli)
tests/
  test_protocol.py decoder tests with hand-built advertisements
```

The design mirrors MagicPods' own split (a UI process talking to a background
Bluetooth service): here, a daemon thread runs the asyncio BLE scanner and pushes
decoded status to the pystray icon loop on the main thread.

## Roadmap

- [ ] Ear-detection auto-pause (parse in-ear flags → media keys)
- [ ] Windows startup entry / Linux `.desktop` autostart
- [ ] Optional Windows 11 widget
- [ ] PyInstaller one-file builds for releases
- [ ] Per-device naming and multiple-device UI

Contributions welcome — the decoder is the fun part and it's small.

## Credits & prior art

Auris stands on open reverse-engineering of Apple's Continuity protocol by the
community: **OpenPods**, **AirStatus**, and **LibrePods**. MagicPods is an
unaffiliated closed-source app referenced only for interoperability research.
"AirPods", "Beats" and "MagicPods" are trademarks of their respective owners;
Auris is independent and not endorsed by any of them.

## License

MIT — see [LICENSE](LICENSE).
