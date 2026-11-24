#!/usr/bin/env python3
"""Generate Marvin's UI textures into media/.

All textures are white (or white with alpha) so the skin tints them with
colordiffuse. Re-run after changing any shape constant:  python3 scripts/gen_textures.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "media")
SS = 4  # supersampling factor for smooth edges


def out(path):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def rounded(w, h, r, path):
    """White rounded rectangle on transparent, anti-aliased."""
    big = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=255)
    a = big.resize((w, h), Image.LANCZOS)
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(a)
    img.save(out(path))


def ring(w, h, r, stroke, path):
    big = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        (0, 0, w * SS - 1, h * SS - 1), r * SS, outline=255, width=stroke * SS)
    a = big.resize((w, h), Image.LANCZOS)
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(a)
    img.save(out(path))


def glow(size, r, pad, blur, path, strength=1.0):
    """Soft outer glow/shadow around a rounded rect; used 9-sliced with border=pad+r."""
    w = h = size + pad * 2
    base = Image.new("L", (w, h), 0)
    ImageDraw.Draw(base).rounded_rectangle((pad, pad, w - pad - 1, h - pad - 1), r, fill=int(255 * strength))
    base = base.filter(ImageFilter.GaussianBlur(blur))
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(base)
    img.save(out(path))


def linear(w, h, path, axis, stops):
    """stops: list of (pos 0..1, alpha 0..255). axis 'x' or 'y'."""
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    px = img.load()
    n = w if axis == "x" else h
    for i in range(n):
        t = i / (n - 1)
        for (p0, a0), (p1, a1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                k = (t - p0) / (p1 - p0) if p1 > p0 else 0
                k = k * k * (3 - 2 * k)  # smoothstep for a filmic falloff
                a = int(a0 + (a1 - a0) * k)
                break
        if axis == "x":
            for y in range(h):
                px[i, y] = (255, 255, 255, a)
        else:
            for x in range(w):
                px[x, i] = (255, 255, 255, a)
    img.save(out(path))


def vignette(w, h, path):
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx = (x / (w - 1) - 0.5) * 2
            dy = (y / (h - 1) - 0.5) * 2
            d = min(1.0, math.sqrt(dx * dx * 0.7 + dy * dy))
            a = int(255 * max(0.0, (d - 0.45) / 0.55) ** 1.6)
            px[x, y] = (255, 255, 255, a)
    img.save(out(path))


def circle(d, path):
    rounded(d, d, d // 2, path)


def main():
    # Solid
    Image.new("RGBA", (8, 8), (255, 255, 255, 255)).save(out("common/white.png"))

    # Panels / buttons (9-slice: border = radius)
    rounded(64, 64, 14, "common/r14.png")          # border="14"
    rounded(32, 32, 8, "common/r8.png")            # border="8"
    rounded(48, 48, 24, "common/pill48.png")       # border="24"
    rounded(16, 16, 8, "common/pill16.png")        # border="8" (thin bars)
    ring(64, 64, 14, 3, "common/r14-ring.png")     # focus ring, border="14"
    circle(128, "common/circle.png")
    circle(24, "common/nib.png")  # seek/slider nib (drawn at native size)
    Image.new("RGBA", (4, 32), (255, 255, 255, 255)).save(out("common/tick.png"))  # chapter marks

    # Focus glow + drop shadow (9-slice: border = 40)
    glow(64, 14, 40, 14, "common/glow.png", 0.9)
    glow(64, 14, 40, 18, "common/shadow.png", 1.0)

    # Diffuse masks for artwork (stretched to exact control size; keep aspect)
    rounded(400, 600, 16, "masks/poster.png")
    rounded(640, 360, 14, "masks/landscape.png")
    rounded(640, 360, 10, "masks/landscape-small.png")
    circle(256, "masks/circle.png")

    # Gradients
    linear(512, 8, "gradients/left.png", "x", [(0, 250), (0.55, 140), (1, 0)])
    linear(8, 512, "gradients/bottom.png", "y", [(0, 0), (0.45, 130), (1, 250)])
    linear(8, 256, "gradients/top.png", "y", [(0, 200), (1, 0)])
    linear(8, 256, "gradients/bottom-soft.png", "y", [(0, 0), (1, 200)])
    vignette(480, 270, "gradients/vignette.png")


if __name__ == "__main__":
    main()
    print("textures written to", os.path.normpath(ROOT))
