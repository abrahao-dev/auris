"""
Render the tray icon: a battery ring with a percentage, drawn with Pillow.

Mirrors what MagicPods' ``TrayTileController`` does ("Battery drawn on tray icon
l=95") — turn the lowest live battery reading into a small glanceable icon.
"""

from __future__ import annotations

from typing import Optional

from PIL import Image, ImageDraw, ImageFont

SIZE = 64  # icon is rendered at 64px and downscaled by the tray


def _ring_color(percent: Optional[int], charging: bool) -> tuple[int, int, int, int]:
    if charging:
        return (52, 199, 89, 255)  # green
    if percent is None:
        return (142, 142, 147, 255)  # grey
    if percent <= 20:
        return (255, 59, 48, 255)  # red
    if percent <= 40:
        return (255, 149, 0, 255)  # orange
    return (255, 255, 255, 255)  # white


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render(percent: Optional[int], charging: bool = False) -> Image.Image:
    """Return an RGBA icon showing ``percent`` inside a coloured ring."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = _ring_color(percent, charging)

    pad = 4
    box = (pad, pad, SIZE - pad, SIZE - pad)

    # faint background ring
    d.arc(box, 0, 360, fill=(120, 120, 120, 120), width=6)

    # filled arc proportional to charge (start at top, clockwise)
    if percent is not None:
        sweep = int(360 * max(0, min(percent, 100)) / 100)
        d.arc(box, -90, -90 + sweep, fill=color, width=6)

    # centred label
    label = "?" if percent is None else str(percent)
    font = _load_font(26 if len(label) < 3 else 20)
    tb = d.textbbox((0, 0), label, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    d.text(
        ((SIZE - tw) / 2 - tb[0], (SIZE - th) / 2 - tb[1]),
        label,
        font=font,
        fill=color,
    )

    if charging:
        # little bolt hint in the corner
        d.polygon(
            [(SIZE - 16, 6), (SIZE - 22, 20), (SIZE - 17, 20), (SIZE - 21, 30),
             (SIZE - 9, 16), (SIZE - 15, 16)],
            fill=(52, 199, 89, 255),
        )
    return img


def default_icon() -> Image.Image:
    """Icon shown when nothing is connected."""
    return render(None, False)
