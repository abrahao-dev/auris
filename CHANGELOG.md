# Changelog

All notable changes to Auris are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

## [0.3.0]

### Added
- **Windows installer** (`AurisSetup.exe`, Inno Setup) — per-user, no admin,
  with Start Menu / optional desktop / optional startup shortcuts. Built in CI
  and attached to every release.
- **winget manifest** templates (`packaging/winget/`) toward
  `winget install Abrahao.Auris`.
- Animated demo GIF and updated screenshots in the READMEs.
- `CHANGELOG.md`.

### Changed
- **Auto-pause is now debounced**: an in-ear change must repeat for 2 consecutive
  advertisements before media is paused/resumed, so a single noisy reading can't
  toggle playback.

## [0.2.0]

### Added
- **Auto-pause** (experimental): pause media when the pods leave your ears and
  resume when they return, from a best-effort in-ear broadcast signal. Off by default.
- **Start with system** toggle (Windows `Run` key / Linux `.desktop` autostart).
- Cross-platform **media control** (`media.py`): Win32 media key / `playerctl`.
- Tray **Settings** submenu to toggle autostart, connect notifications, auto-pause.
- README preview image; Portuguese README.

## [0.1.0]

### Added
- Apple Continuity **proximity-pairing decoder** (company `0x004C`, type `0x07`)
  for left/right/case battery, charging, lid and model — fully unit-tested.
- Model-id table cross-checked against MagicPods assets.
- **bleak** BLE scanner (WinRT on Windows, BlueZ on Linux).
- System-tray battery-ring icon (Pillow), low-battery and connect notifications.
- One-file **PyInstaller** builds for Windows and Linux, published via GitHub
  Actions on tag; CI runs the decoder tests.
