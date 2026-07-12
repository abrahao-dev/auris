<div align="center">

# 🎧 Auris

**An open-source AirPods & Bluetooth-earbuds companion for Windows and Linux.**

See your **AirPods / Beats battery** — left, right and case — right from the system tray.
A free, transparent alternative to closed-source apps like MagicPods.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue.svg)](#-download)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/abrahao-dev/auris?include_prereleases&sort=semver)](https://github.com/abrahao-dev/auris/releases/latest)
[![CI](https://github.com/abrahao-dev/auris/actions/workflows/ci.yml/badge.svg)](https://github.com/abrahao-dev/auris/actions/workflows/ci.yml)

**English** · [Português (Brasil)](README.pt-BR.md)

</div>

> [!NOTE]
> Auris only **listens** to the Bluetooth Low Energy advertisements your earbuds
> already broadcast. It never pairs, connects, writes, or phones home.

---

## ✨ Features

- 🔋 Live **left / right / case** battery percentages
- ⚡ **Charging** indicator per component
- 🎧 Works with **AirPods** (1–4, Pro, Pro 2, Max) and many **Beats** models
- 🔔 **Low-battery** and **connect** notifications (native toast on Windows, `notify-send` on Linux)
- 🖼️ Battery ring drawn onto the **tray icon** for an at-a-glance read
- 🪟 **Windows** + 🐧 **Linux** (BlueZ) from one Python codebase
- 🧾 MIT-licensed, no telemetry, ~600 lines of readable code

## 📥 Download

Grab a ready-to-run build from the [**latest release**](https://github.com/abrahao-dev/auris/releases/latest) — no Python required.

| Platform | File | How to run |
|----------|------|------------|
| 🪟 **Windows 10/11** | `Auris.exe` | Double-click it. Auris appears in the system tray. |
| 🐧 **Linux (x86-64)** | `auris-linux` | `chmod +x auris-linux && ./auris-linux` |

> Windows may show a SmartScreen warning because the binary isn't code-signed
> (it's an open-source community build) — click **More info → Run anyway**, or
> [build it yourself](#-run-from-source).
>
> Linux needs BlueZ (`bluez`) and permission to scan BLE (a `bluetooth` group
> membership or running via `sudo`). A tray requires a StatusNotifier host
> (GNOME needs the *AppIndicator* extension).

## 🚀 Run from source

```bash
git clone https://github.com/abrahao-dev/auris.git
cd auris
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux: source .venv/bin/activate
pip install -r requirements.txt

python -m auris          # tray app
python -m auris --cli    # headless: print decoded advertisements to the console
```

Requires Python 3.10+ and a Bluetooth LE adapter.

## 🔬 How it works

Apple earbuds continuously broadcast a BLE advertisement under Apple's
manufacturer-data **company id `0x004C`**. Inside it is a *proximity-pairing*
message (type `0x07`) that encodes battery, charging and lid state in the clear.
Apple's own OS reads this same broadcast; Auris decodes it openly.

```
manufacturer_data[0x004C] payload (company id already stripped):

  off  value  meaning
  0    07     message type = proximity pairing
  3-4  ....   model id, big-endian  (0E20 = AirPods Pro, 0A20 = AirPods Max, …)
  5    ..     status byte — includes the "flip" bit (which pod is reported first)
  6    ..     battery: high nibble = pod A, low nibble = pod B
  7    ..     high nibble = charging flags, low nibble = case battery

  battery nibble: 0..10 -> ×10 percent (10 = 100%);  0xF = unavailable
```

The model-id table in [`auris/models.py`](auris/models.py) was cross-checked
against the asset folders bundled with MagicPods. Full write-up in
[`docs/PROTOCOL.md`](docs/PROTOCOL.md).

## 🧱 Architecture

```
auris/
  protocol.py      Apple Continuity decoder  ← the core (fully unit-tested)
  models.py        model-id → name/family table
  scanner.py       bleak BLE scanner (WinRT on Windows, BlueZ on Linux)
  icon.py          Pillow battery-ring tray-icon renderer
  notifications.py cross-platform toasts (winotify / notify-send / stdout)
  config.py        JSON config under the user profile
  app.py           tray + state tracking + notifications (orchestrator)
tests/
  test_protocol.py decoder tests with hand-built advertisements
```

The design mirrors MagicPods' own split (a UI process talking to a background
Bluetooth service): a daemon thread runs the asyncio BLE scanner and pushes
decoded status to the pystray icon loop on the main thread.

## 🧪 Development

```bash
pip install -r requirements.txt
python tests/test_protocol.py     # or: pip install pytest && pytest
```

Build a standalone binary locally:

```bash
pip install pyinstaller
pyinstaller Auris.spec             # output in dist/
```

## 🗺️ Roadmap

- [ ] Ear-detection auto-pause (parse in-ear flags → media keys)
- [ ] Windows startup entry / Linux `.desktop` autostart
- [ ] Optional Windows 11 widget
- [ ] Per-device naming and multiple-device UI
- [ ] Code-signed Windows builds

Contributions welcome — the decoder is the fun part and it's small.

## 🙌 Credits & prior art

Auris stands on open reverse-engineering of Apple's Continuity protocol by the
community: [OpenPods](https://github.com/adolfintel/OpenPods),
[AirStatus](https://github.com/delphiki/AirStatus), and **LibrePods**. MagicPods
is an unaffiliated closed-source app referenced only for interoperability
research. "AirPods", "Beats" and "MagicPods" are trademarks of their respective
owners; Auris is independent and not endorsed by any of them.

## 📄 License

MIT — see [LICENSE](LICENSE).
