"""
Regenerate the README art (docs/preview.png and docs/demo.gif).

Replicates the geometry of auris/icon.py at high resolution (the real renderer
is fixed at 64 px for the tray) so the docs stay faithful to what the app draws.

Usage:  python docs/make_assets.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

DOCS = Path(__file__).parent

# palette (matches auris/icon.py + a GitHub-dark friendly card)
CARD_BG = (17, 19, 24, 255)
TILE_BG = (32, 35, 42, 255)
TEXT = (235, 237, 240, 255)
SUBTEXT = (150, 155, 165, 255)
GREEN = (52, 199, 89, 255)
GREY = (142, 142, 147, 255)
RED = (255, 59, 48, 255)
ORANGE = (255, 149, 0, 255)
WHITE = (255, 255, 255, 255)

SS = 2  # supersampling factor


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    names = (
        ["Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["Arial.ttf", "arial.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise OSError("no usable TrueType font found")


def _ring_color(percent: Optional[int], charging: bool):
    if charging:
        return GREEN
    if percent is None:
        return GREY
    if percent <= 20:
        return RED
    if percent <= 40:
        return ORANGE
    return WHITE


def render_icon(percent: Optional[int], charging: bool, size: int) -> Image.Image:
    """auris.icon.render(), scaled from its native 64 px geometry."""
    s = size * SS / 64
    px = size * SS
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = _ring_color(percent, charging)

    pad = 4 * s
    box = (pad, pad, px - pad, px - pad)
    d.arc(box, 0, 360, fill=(120, 120, 120, 120), width=round(6 * s))
    if percent is not None:
        sweep = 360 * max(0, min(percent, 100)) / 100
        d.arc(box, -90, -90 + sweep, fill=color, width=round(6 * s))

    label = "?" if percent is None else str(percent)
    font = _font(round((26 if len(label) < 3 else 20) * s))
    tb = d.textbbox((0, 0), label, font=font)
    d.text(
        ((px - (tb[2] - tb[0])) / 2 - tb[0], (px - (tb[3] - tb[1])) / 2 - tb[1]),
        label,
        font=font,
        fill=color,
    )
    if charging:
        d.polygon(
            [(px - 16 * s, 6 * s), (px - 22 * s, 20 * s), (px - 17 * s, 20 * s),
             (px - 21 * s, 30 * s), (px - 9 * s, 16 * s), (px - 15 * s, 16 * s)],
            fill=GREEN,
        )
    return img.resize((size, size), Image.LANCZOS)


def rounded_card(size: tuple[int, int], radius: int, fill) -> Image.Image:
    img = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(
        (0, 0, size[0] * SS - 1, size[1] * SS - 1), radius * SS, fill=fill
    )
    return img.resize(size, Image.LANCZOS)


def make_preview() -> None:
    states = [
        (100, True, "Full · charging"),
        (85, False, "Good"),
        (60, True, "Charging"),
        (20, False, "Low"),
        (None, False, "No device"),
    ]
    icon, tile_w, tile_h, gap, m = 96, 150, 176, 18, 28
    title_h = 64
    W = m * 2 + tile_w * len(states) + gap * (len(states) - 1)
    H = m + title_h + tile_h + m

    card = rounded_card((W, H), 18, CARD_BG)
    d = ImageDraw.Draw(card)
    d.text((m + 4, m + 2), "Auris", font=_font(30), fill=TEXT)
    tw = d.textbbox((0, 0), "Auris", font=_font(30))[2]
    d.text((m + 4 + tw + 10, m + 8), "— live tray battery icon",
           font=_font(22, bold=False), fill=SUBTEXT)

    for i, (pct, chg, label) in enumerate(states):
        x = m + i * (tile_w + gap)
        y = m + title_h
        tile = rounded_card((tile_w, tile_w), 22, TILE_BG)
        card.alpha_composite(tile, (x, y))
        ic = render_icon(pct, chg, icon)
        card.alpha_composite(ic, (x + (tile_w - icon) // 2, y + (tile_w - icon) // 2))
        lf = _font(19, bold=False)
        lw = d.textbbox((0, 0), label, font=lf)[2]
        d.text((x + (tile_w - lw) / 2, y + tile_w + 8), label, font=lf, fill=SUBTEXT)

    card.save(DOCS / "preview.png")
    print("preview.png", card.size)


def make_demo() -> None:
    """Battery drains white->orange->red, then charges back green. Loops."""
    size, pad = 132, 10
    W = H = size + pad * 2
    steps: list[tuple[int, bool]] = []
    steps += [(p, False) for p in range(100, 9, -5)]   # drain
    steps += [(10, False)] * 4                          # linger on red
    steps += [(p, True) for p in range(10, 101, 6)]     # charge
    steps += [(100, True)] * 6                          # linger on full

    rgba = []
    for pct, chg in steps:
        frame = rounded_card((W, H), 24, CARD_BG)
        frame.alpha_composite(render_icon(pct, chg, size), (pad, pad))
        rgba.append(frame)

    # one global 255-colour palette for every frame, index 255 kept transparent
    sheet = Image.new("RGB", (W * len(rgba), H), CARD_BG[:3])
    for i, f in enumerate(rgba):
        sheet.paste(f.convert("RGB"), (i * W, 0))
    master = sheet.quantize(colors=255, method=Image.MEDIANCUT)

    frames = []
    for f in rgba:
        p = f.convert("RGB").quantize(palette=master, dither=Image.Dither.NONE)
        clear = f.getchannel("A").point(lambda a: 255 if a < 128 else 0)
        p.paste(255, mask=clear)  # GIF alpha is 1-bit: snap soft pixels
        frames.append(p)

    frames[0].save(
        DOCS / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
        disposal=2,
        transparency=255,
    )
    print("demo.gif", (W, H), len(frames), "frames")


if __name__ == "__main__":
    make_preview()
    make_demo()
