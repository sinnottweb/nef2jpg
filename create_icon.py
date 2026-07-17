"""
create_icon.py — Generates assets/icon.ico from scratch using Pillow.
Run once before building with PyInstaller:  python create_icon.py
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def make_icon(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r_outer = int(size * 0.46)
    r_inner = int(size * 0.22)

    # Background circle
    draw.ellipse(
        [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
        fill=(28, 28, 28, 255),
    )

    # Aperture blades (6 blades = hexagonal aperture)
    blade_color = (232, 168, 56, 255)   # #e8a838
    n_blades = 6
    for i in range(n_blades):
        angle = math.radians(i * 60)
        # Each blade is a rotated rounded rectangle
        bx = cx + int(r_inner * 0.7 * math.cos(angle))
        by = cy + int(r_inner * 0.7 * math.sin(angle))
        blade_w = int(size * 0.38)
        blade_h = int(size * 0.10)

        blade = Image.new("RGBA", (blade_w, blade_h), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blade)
        bd.rounded_rectangle([0, 0, blade_w - 1, blade_h - 1], radius=blade_h // 2, fill=blade_color)
        blade = blade.rotate(-math.degrees(angle), expand=True)

        ox = bx - blade.width // 2
        oy = by - blade.height // 2
        img.paste(blade, (ox, oy), blade)

    # Inner circle (lens)
    draw.ellipse(
        [cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
        fill=(20, 20, 20, 255),
    )

    # Inner glow circle
    r_dot = int(size * 0.08)
    draw.ellipse(
        [cx - r_dot, cy - r_dot, cx + r_dot, cy + r_dot],
        fill=(255, 200, 80, 200),
    )

    # NEF text below
    font_size = max(18, size // 12)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    text = "NEF→JPG"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = cx - tw // 2
    ty = cy + r_outer - font_size - int(size * 0.04)
    draw.text((tx, ty), text, fill=(232, 168, 56, 220), font=font)

    return img


def save_ico(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 32, 48, 64, 128, 256]
    images = [make_icon(s) for s in sizes]
    images[0].save(
        str(output_path),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"[OK] Icono generado: {output_path}")


if __name__ == "__main__":
    save_ico(Path("assets/icon.ico"))
