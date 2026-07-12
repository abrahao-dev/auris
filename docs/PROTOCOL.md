# Apple Continuity — Proximity Pairing advertisement

This document describes the Bluetooth Low Energy advertisement that AirPods and
Beats broadcast, and how Auris decodes battery/charging/lid state from it.

## Where the data lives

Every BLE advertisement can carry a **Manufacturer Specific Data** field. The
first two bytes are a little-endian company id assigned by the Bluetooth SIG.
Apple's id is **`0x004C`** (76). BLE stacks (WinRT, BlueZ) expose the field as a
map of `company_id -> bytes`, with the id already stripped — so what Auris
receives is the payload that follows.

Apple multiplexes several *Continuity* message types in that payload. The one we
care about is **Proximity Pairing**, identified by a leading byte `0x07`.

## Payload layout

```
byte  example  field
────  ───────  ─────────────────────────────────────────────
 0    0x07     message type (0x07 = proximity pairing)
 1    0x19     length of the remainder (25 bytes)
 2    0x01     prefix / paired-device count
 3    0x0E  ┐  16-bit model id, big-endian
 4    0x20  ┘  → "0e20" = AirPods Pro
 5    0x21     status byte (bit flags; carries the "flip" bit)
 6    0x9A     battery: high nibble = pod A (9), low nibble = pod B (10)
 7    0x46     high nibble = charging flags (4), low nibble = case battery (6)
 8    0x00     lid open/close state & counter (case)
 9    0x00     device color
10               reserved
11…              AES-encrypted remainder (Auris ignores this)
```

## Battery encoding

Each battery component is a 4-bit nibble:

| nibble | meaning        |
|-------:|----------------|
| 0–10   | value × 10 %   |
| 15 (F) | not available  |

So `0xA` (10) = 100 %, `0x9` = 90 %, `0xF` = pod out of case / disconnected.

## The "flip" bit

AirPods don't have a fixed "left is always first" rule — the advertisement may
report the two pods in either order. Bit 1 of the **high nibble of byte 5**
tells you which:

```
flip = (high_nibble(byte5) & 0x02) == 0
```

- `flip == False`: pod A (byte 6 high nibble) is the **right** pod.
- `flip == True` : pod A is the **left** pod.

Auris applies the same swap to the two low charging bits of byte 7.

## Charging flags (high nibble of byte 7)

| bit  | meaning                         |
|-----:|---------------------------------|
| 0    | one pod charging (per flip bit) |
| 1    | other pod charging              |
| 2    | case charging                   |

## Model ids

The 16-bit model id (bytes 3–4, big-endian) identifies the product. Auris keeps
a lookup table in [`../auris/models.py`](../auris/models.py). Examples:

| id     | device                         |
|--------|--------------------------------|
| 0x0220 | AirPods (1st gen)              |
| 0x0F20 | AirPods (2nd gen)              |
| 0x1320 | AirPods (3rd gen)              |
| 0x0E20 | AirPods Pro                    |
| 0x1420 | AirPods Pro (2nd gen)          |
| 0x2420 | AirPods Pro (2nd gen, USB-C)   |
| 0x0A20 | AirPods Max                    |
| 0x2D20 | AirPods Max (USB-C)            |

The complete recognised set was cross-referenced with the model-id folders
bundled inside MagicPods (`Assets/Headphones/4c00/<id>/`).

## What Auris deliberately does *not* do

- It does not decrypt the encrypted remainder (bytes 11+).
- It does not connect, pair, or send anything to the device.
- In-ear detection is only partially exposed by this broadcast and is left as a
  best-effort/roadmap item rather than a guaranteed feature.

## References

- OpenPods — https://github.com/adolfintel/OpenPods
- AirStatus — https://github.com/delphiki/AirStatus
- LibrePods — community AirPods reverse-engineering
