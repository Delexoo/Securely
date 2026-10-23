"""Render crisp Inno Setup wizard logos from the high-res Securely mark.

Opaque RGB on charcoal — avoids muddy transparent fringes against the wizard chrome.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "installer" / "wizard"
SRC_CANDIDATES = [
    ROOT / "securely-app" / "assets" / "SecurelyLogo-source.png",
    Path(r"C:\Users\Massi\OneDrive\Desktop\SecurelyLogo.png"),
    ROOT / "securely-app" / "ui" / "public" / "logo.png",
    ROOT / "securely-app" / "host" / "securely-logo.png",
]
CHARCOAL = (26, 26, 26, 255)
PANEL = (15, 17, 22)


def load_master() -> Image.Image:
    path = next((p for p in SRC_CANDIDATES if p.is_file()), None)
    if path is None:
        raise FileNotFoundError("No Securely logo PNG found")
    img = Image.open(path).convert("RGBA")
    print("source", path, img.size)
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), CHARCOAL)
    canvas.paste(img, ((side - img.size[0]) // 2, (side - img.size[1]) // 2), img)
    return canvas.resize((2048, 2048), Image.Resampling.LANCZOS)


def rounded_opaque(master: Image.Image, size: int, radius_ratio: float = 0.22) -> Image.Image:
    hi = 8  # heavy supersample for smooth squircle + shield curves
    big = size * hi
    base = master.resize((big, big), Image.Resampling.LANCZOS)
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, big - 1, big - 1), radius=int(big * radius_ratio), fill=255
    )
    solid = Image.new("RGBA", (big, big), CHARCOAL)
    solid.paste(base, (0, 0))
    shaped = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    shaped.paste(solid, (0, 0), mask)
    # Flatten onto charcoal so installer edges never fringe against white chrome
    flat = Image.new("RGBA", (big, big), CHARCOAL)
    flat.alpha_composite(shaped)
    return flat.resize((size, size), Image.Resampling.LANCZOS).convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    master = load_master()

    for size, name in (
        (58, "wizard-small-58.png"),
        (147, "wizard-small-147.png"),
        (256, "wizard-small-256.png"),
    ):
        path = OUT / name
        rounded_opaque(master, size).save(path, "PNG")
        print(name, path.stat().st_size)

    for w, h, name in (
        (202, 386, "wizard-202x386.png"),
        (240, 459, "wizard-240x459.png"),
    ):
        panel = Image.new("RGB", (w, h), PANEL)
        logo_size = min(w - 28, int(h * 0.38))
        mark = rounded_opaque(master, logo_size)
        x = (w - logo_size) // 2
        y = max(24, (h - logo_size) // 2 - h // 14)
        panel.paste(mark, (x, y))
        path = OUT / name
        panel.save(path, "PNG")
        print(name, path.stat().st_size)


if __name__ == "__main__":
    main()
