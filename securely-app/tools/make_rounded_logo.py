"""Build rounded Securely logo assets (PNG + multi-size ICO)."""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

SRC = Path(r"C:\Users\Massi\OneDrive\Desktop\SecurelyLogo.png")
OUT_UI = Path(r"E:\MasterVault\Securely\securely-app\ui\public")
OUT_HOST = Path(r"E:\MasterVault\Securely\securely-app\host")
OUT_ASSETS = Path(r"E:\MasterVault\Securely\securely-app\assets")


def round_corners(im: Image.Image, radius_ratio: float = 0.22) -> Image.Image:
    size = im.size[0]
    radius = max(1, int(size * radius_ratio))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    out = im.copy()
    out.putalpha(mask)
    return out


def save_ico(images: list[Image.Image], path: Path) -> None:
    # Write each size into a proper multi-resolution ICO via Pillow.
    buf = BytesIO()
    largest = images[-1]
    largest.save(
        buf,
        format="ICO",
        sizes=[(im.size[0], im.size[1]) for im in images],
        append_images=images[:-1],
    )
    path.write_bytes(buf.getvalue())


def main() -> None:
    OUT_UI.mkdir(parents=True, exist_ok=True)
    OUT_HOST.mkdir(parents=True, exist_ok=True)
    OUT_ASSETS.mkdir(parents=True, exist_ok=True)

    img = Image.open(SRC).convert("RGBA")
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (26, 26, 26, 255))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    rounded = round_corners(canvas.resize((1024, 1024), Image.Resampling.LANCZOS), 0.22)

    rounded.save(OUT_UI / "logo.png", "PNG")
    rounded.save(OUT_ASSETS / "SecurelyLogo-rounded.png", "PNG")
    rounded.resize((256, 256), Image.Resampling.LANCZOS).save(OUT_UI / "logo-256.png", "PNG")
    rounded.resize((64, 64), Image.Resampling.LANCZOS).save(OUT_UI / "favicon.png", "PNG")
    rounded.resize((32, 32), Image.Resampling.LANCZOS).save(OUT_UI / "favicon-32.png", "PNG")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    ico_images = [rounded.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
    save_ico(ico_images, OUT_HOST / "securely.ico")
    save_ico(ico_images, OUT_UI / "favicon.ico")
    print("logo.png", (OUT_UI / "logo.png").stat().st_size)
    print("securely.ico", (OUT_HOST / "securely.ico").stat().st_size)


if __name__ == "__main__":
    main()
