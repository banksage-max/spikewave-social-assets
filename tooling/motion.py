"""Icon-motion clips (idea from Apple's App Store promo videos, 7 Nov 2026): the app icon as a frosted-glass
object with a light sweep, slow tilt, drifting particles and a reveal; minimal text and a store line.

Layouts:
  reveal  - near-black, icon fades in from a frosted blank, glow builds ("Now available" / launch day)
  centred - icon centred under the headline, particles drifting ("Coming ..." / "Updated ...")
  hero    - huge tilted icon bleeding off the bottom-right, text top-left (feature line)

Usage: python tooling/motion.py <app slug> <layout> "<headline>" "<sub line>" "<store line>" <out.mp4>
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import styles as st  # noqa: E402

FF = os.environ.get("FFMPEG", r"C:\Users\vundl\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
W, H, FPS = 1080, 1920, 30
INK, SUB = (246, 247, 250), (186, 190, 202)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def glass_icon(slug, size, sheen_x, blur=0.0, glyph=1.0):
    """App icon as a glass tile: rounded mask, inner rim light, diagonal sheen at sheen_x (0..1 across)."""
    ic = st.icon(slug, size).convert("RGBA")
    r = int(size * 0.225)
    if blur > 0.3 or glyph < 1:
        base = ic.filter(ImageFilter.GaussianBlur(size * 0.12))  # frosted blank: the icon's own colours, no glyph
        ic = Image.blend(base, ic.filter(ImageFilter.GaussianBlur(blur)) if blur > 0.3 else ic, glyph)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
    # sheen: a soft diagonal white band
    band = Image.new("L", (size * 2, size * 2), 0)
    cx = int(sheen_x * size * 2)
    ImageDraw.Draw(band).rectangle([cx - size // 9, 0, cx + size // 9, size * 2], fill=120)
    band = band.filter(ImageFilter.GaussianBlur(size // 14)).rotate(28, resample=Image.BICUBIC)
    band = band.crop((size // 2, size // 2, size // 2 + size, size // 2 + size))
    white = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    white.putalpha(band)
    ic.alpha_composite(white)
    # rim: thin bright edge, stronger top-left
    rim = Image.new("L", (size, size), 0)
    ImageDraw.Draw(rim).rounded_rectangle([1, 1, size - 2, size - 2], radius=r, outline=255, width=max(2, size // 160))
    grad = Image.linear_gradient("L").rotate(45, expand=False).resize((size, size)).point(lambda v: 255 - v)
    rim = Image.composite(rim, Image.new("L", (size, size), 0), grad.point(lambda v: max(70, v)))
    rl = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    rl.putalpha(rim.point(lambda v: int(v * 0.8)))
    ic.alpha_composite(rl)
    ic.putalpha(mask)
    return ic


def tilt(im, ax, ay=0.0):
    """Gentle perspective turn: ax > 0 turns the right edge away (shorter), ax < 0 the left edge."""
    w, h = im.size
    pad = int(max(w, h) * 0.12)
    big = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    big.paste(im, (pad, pad))
    kl, kr = max(-ax, 0) * h / 2, max(ax, 0) * h / 2
    sy = ay * h / 2
    quad = (pad, pad - kl + sy, pad, pad + h + kl + sy,  # input points for output TL, BL, BR, TR
            pad + w, pad + h + kr - sy, pad + w, pad - kr - sy)
    return big.transform(big.size, Image.QUAD, quad, resample=Image.BICUBIC), pad


class Particles:
    def __init__(self, n, seed=7):
        rng = np.random.default_rng(seed)
        self.p = rng.random((n, 2)) * [W, H]
        self.v = (rng.random((n, 2)) - 0.5) * [12, 10] + [0, -6]
        self.s = rng.random(n) * 2.4 + 1.2
        self.a = rng.random(n) * 0.5 + 0.25
        self.ph = rng.random(n) * 6.28

    def draw(self, c, t):
        lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for (x, y), (vx, vy), s, a, ph in zip(self.p, self.v, self.s, self.a, self.ph):
            px, py = (x + vx * t) % W, (y + vy * t) % H
            al = int(255 * a * (0.6 + 0.4 * math.sin(t * 1.3 + ph)))
            d.ellipse([px - s, py - s, px + s, py + s], fill=(255, 255, 255, al))
        c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.8)))


def background(app, t, dark=False):
    """Slow-moving soft light over a deep app-tinted gradient (the clips' drifting spotlight)."""
    top = tuple(int(v * (0.25 if dark else 0.55)) for v in app["accent2"]) if not dark else (14, 14, 18)
    bot = app["dark"] if not dark else (8, 8, 11)
    c = st.grad((W, H), top, bot).convert("RGBA")
    gx = W * (0.3 + 0.4 * math.sin(t * 0.35))
    gy = H * (0.25 + 0.1 * math.cos(t * 0.27))
    st.glow(c, (int(gx), int(gy)), 820, (255, 255, 255), 16 if dark else 26)
    return c


def store_pill(c, cx, y, text, app, scale=1.0, left=None):
    d = ImageDraw.Draw(c)
    f = st.font("bold", int(40 * scale))
    tw = d.textlength(text, font=f)
    w, h = tw + 80 * scale, 96 * scale
    if left is not None:
        cx = left + w / 2
    d.rounded_rectangle([cx - w / 2, y, cx + w / 2, y + h], radius=h / 2, fill=app["accent"])
    d.text((cx, y + h / 2), text, font=f, fill=app.get("ink", (20, 20, 20)), anchor="mm")


def frame(app, slug, layout, t, dur, head, sub, store, parts):
    dark = layout == "reveal"
    c = background(app, t, dark)
    if layout != "reveal":
        parts.draw(c, t)
    d = ImageDraw.Draw(c)
    sheen = -0.3 + 1.6 * ((t % 4.0) / 4.0)  # one sweep every 4 s
    wob = (0.035 * math.sin(t * 0.9), 0.01 * math.cos(t * 0.7))
    if layout == "hero":
        size = 940
        ic, pad = tilt(glass_icon(slug, size, sheen), 0.06 + wob[0], wob[1])
        ic = ic.rotate(-12, resample=Image.BICUBIC, expand=True)
        x, y = W - ic.width + 230, 980
        st.glow(c, (x + ic.width // 2, y + ic.height // 2), 760, app["accent"], 38)
        c.alpha_composite(ic, (x, y))
        a = ease(t / 0.8)
        y0 = 360
        f = st.font("bold", 92)
        y0 = st.text_block(d, (72, y0), head, f, INK + (int(255 * a),), W - 144, lh=1.08)
        d.text((72, y0 + 26), app["name"], font=st.font("semi", 42), fill=INK)
        d.text((72, y0 + 84), sub, font=st.font("regular", 36), fill=SUB)
        store_pill(c, None, y0 + 160, store, app, 0.9, left=72)
    elif layout == "centred":
        size = 560
        ic, pad = tilt(glass_icon(slug, size, sheen), 0.04 + wob[0], wob[1])
        ic = ic.rotate(-8 + 2 * math.sin(t * 0.6), resample=Image.BICUBIC, expand=True)
        cx, cy = W // 2, 860
        st.glow(c, (cx, cy), 520, app["accent"], 40)
        c.alpha_composite(ic, (cx - ic.width // 2, cy - ic.height // 2))
        f = st.font("bold", 84)
        st.text_block(d, (90, 300), head, f, INK, W - 180, lh=1.1, align="center")
        d.text((W // 2, 1250), app["name"], font=st.font("semi", 46), fill=INK, anchor="mm")
        d.text((W // 2, 1312), sub, font=st.font("regular", 36), fill=SUB, anchor="mm")
        store_pill(c, W // 2, 1390, store, app)
    else:  # reveal
        size = 520
        r = ease((t - 0.6) / 2.2)
        glyph = r
        ic = glass_icon(slug, size, sheen if t > 2.4 else -1, blur=14 * (1 - r), glyph=glyph)
        cx, cy = W // 2, 880
        st.glow(c, (cx, cy), 330 + int(160 * r), (255, 255, 255), int(10 + 36 * r))
        st.glow(c, (cx, cy), 300, app["accent"], int(30 * r))
        sc = 0.96 + 0.04 * r
        ic = ic.resize((int(size * sc), int(size * sc)), Image.LANCZOS)
        c.alpha_composite(ic, (cx - ic.width // 2, cy - ic.height // 2))
        a = ease(t / 0.7)
        d.text((W // 2, 470), head, font=st.font("bold", 88), fill=INK + (int(255 * a),), anchor="mm")
        d.text((W // 2, 560), app["name"], font=st.font("semi", 46), fill=SUB, anchor="mm")
        d.text((W // 2, 1230), sub, font=st.font("regular", 38), fill=SUB, anchor="mm")
        store_pill(c, W // 2, 1310, store, app)
    # fade in/out
    k = min(ease(t / 0.35), ease((dur - t) / 0.5))
    if k < 1:
        c = Image.blend(Image.new("RGBA", c.size, (0, 0, 0, 255)), c, k)
    return c.convert("RGB")


def render(slug, layout, head, sub, store, out, dur=8.0):
    app = st.APPS[slug]
    parts = Particles(70)
    work = tempfile.mkdtemp()
    try:
        n = int(dur * FPS)
        for i in range(n):
            frame(app, slug, layout, i / FPS, dur, head, sub, store, parts).save(os.path.join(work, f"{i:04d}.png"))
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i",
                        os.path.join(work, "%04d.png"), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "96k",
                        "-movflags", "+faststart", out], check=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


if __name__ == "__main__":
    render(*sys.argv[1:7])
