"""Icon-motion clips (idea from Apple's App Store promo videos, 7 Nov 2026): the app icon as a glass tile with
depth, a light sweep, a slow turn, drifting particles and a reveal; minimal text and a store line.

Layouts:
  reveal  - near-black, the icon resolves out of a frosted blank, glow builds ("Now available" / launch day)
  centred - headline above a centred icon, particles drifting ("Coming ..." / "Updated ...")
  hero    - large turned icon low on the right, benefit line top-left

Quality: every tile is drawn at 2x and downsampled (smooth edges), the background is dithered (no banding),
text fades up in sequence, and motion is eased.

Usage: python tooling/motion.py <app slug> <layout> "<headline>" "<sub line>" "<store line>" <out.mp4>
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import styles as st  # noqa: E402

FF = os.environ.get("FFMPEG", r"C:\Users\vundl\anaconda3\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
W, H, FPS = 1080, 1920, 30
INK, SUB = (246, 247, 250), (178, 183, 196)
SS = 2  # supersampling factor for the tile


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def rr_mask(size, r, inset=0):
    """Anti-aliased rounded-square mask (drawn at 4x, reduced)."""
    k = 4
    m = Image.new("L", (size * k, size * k), 0)
    ImageDraw.Draw(m).rounded_rectangle([inset * k, inset * k, (size - inset) * k - 1, (size - inset) * k - 1],
                                        radius=max(r - inset, 1) * k, fill=255)
    return m.resize((size, size), Image.LANCZOS)


class Tile:
    """The app icon as a glass tile at SS x the display size. Static layers are built once."""

    def __init__(self, slug, size):
        self.n = size * SS
        n = self.n
        self.r = int(n * 0.225)
        src = Image.open(os.path.join(os.path.dirname(__file__), "..", "brand", "icons", f"{slug}.png")).convert("RGBA")
        self.icon = src.resize((n, n), Image.LANCZOS)
        self.frost = self.icon.filter(ImageFilter.GaussianBlur(n * 0.14))
        self.mask = rr_mask(n, self.r)
        # glass highlight: soft white from the top, gone by 55%
        g = np.clip(1 - np.linspace(0, 1, n) / 0.55, 0, 1) ** 1.6 * 46
        hl = Image.fromarray(np.repeat(g[:, None], n, 1).astype(np.uint8), "L")
        self.highlight = Image.new("RGBA", (n, n), (255, 255, 255, 0))
        self.highlight.putalpha(hl)
        # inner rim: bright at top-left, faint at bottom-right
        w = max(int(n * 0.006), 2)
        ring = ImageChops.subtract(self.mask, rr_mask(n, self.r, w)).filter(ImageFilter.GaussianBlur(w * 0.35))
        ring = ring.point(lambda v: int(v * 0.62))  # even, quiet edge light; the top highlight carries the shine
        self.rim = Image.new("RGBA", (n, n), (255, 255, 255, 0))
        self.rim.putalpha(ring)
        # bottom inner shade for depth
        sh = np.clip((np.linspace(0, 1, n) - 0.6) / 0.4, 0, 1) ** 1.5 * 40
        self.shade = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        self.shade.putalpha(Image.fromarray(np.repeat(sh[:, None], n, 1).astype(np.uint8), "L"))

    def render(self, sheen=None, reveal=1.0):
        n = self.n
        im = self.icon if reveal >= 1 else Image.blend(self.frost, self.icon, ease_io(reveal))
        im = im.copy()
        im.alpha_composite(self.highlight)
        im.alpha_composite(self.shade)
        if sheen is not None and -0.4 < sheen < 1.4:
            band = Image.new("L", (n * 2, n * 2), 0)
            cx = int((sheen * 1.0 + 0.5) * n)
            ImageDraw.Draw(band).rectangle([cx - n // 14, 0, cx + n // 14, n * 2], fill=78)
            band = band.filter(ImageFilter.GaussianBlur(n // 18)).rotate(-24, resample=Image.BICUBIC)
            band = band.crop((n // 2, n // 2, n // 2 + n, n // 2 + n))
            lay = Image.new("RGBA", (n, n), (255, 255, 255, 0))
            lay.putalpha(band)
            im.alpha_composite(lay)
        im.alpha_composite(self.rim)
        im.putalpha(ImageChops.multiply(im.split()[3], self.mask))
        return im


def turn(im, ax, ay=0.0):
    """Gentle perspective turn on an SS-scale tile: ax > 0 shortens the right edge, ay > 0 the bottom edge."""
    w, h = im.size
    pad = int(max(w, h) * 0.1)
    big = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    big.paste(im, (pad, pad))
    kl, kr = max(-ax, 0) * h / 2, max(ax, 0) * h / 2
    kt, kb = max(-ay, 0) * w / 2, max(ay, 0) * w / 2
    quad = (pad - kt, pad - kl, pad - kb, pad + h + kl,  # input points for output TL, BL, BR, TR
            pad + w + kb, pad + h + kr, pad + w + kt, pad - kr)
    return big.transform(big.size, Image.QUAD, quad, resample=Image.BICUBIC)


def place_tile(c, tile_ss, cx, cy, angle=0.0, glow_col=None, glow_a=0):
    """Rotate at SS scale, downsample (smooth edges), drop a soft shadow, composite centred at (cx, cy)."""
    t = tile_ss.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else tile_ss
    t = t.resize((t.width // SS, t.height // SS), Image.LANCZOS)
    x, y = int(cx - t.width / 2), int(cy - t.height / 2)
    if glow_col is not None and glow_a:
        st.glow(c, (int(cx), int(cy)), int(t.width * 0.75), glow_col, glow_a)
    a = t.split()[3]
    for blur, alpha, dy in ((60, 0.55, int(t.height * 0.07)), (14, 0.35, int(t.height * 0.02))):
        s = Image.new("RGBA", t.size, (0, 0, 0, 0))
        s.putalpha(a.point(lambda v, k=alpha: int(v * k)))
        pad = blur * 3
        sb = Image.new("RGBA", (t.width + 2 * pad, t.height + 2 * pad), (0, 0, 0, 0))
        sb.alpha_composite(s, (pad, pad))
        c.alpha_composite(sb.filter(ImageFilter.GaussianBlur(blur)), (x - pad, y - pad + dy))
    c.alpha_composite(t, (x, y))


class Particles:
    """Two depths: small sharp specks and a few large soft bokeh discs."""

    def __init__(self, n, seed=7):
        rng = np.random.default_rng(seed)
        self.p = rng.random((n, 2)) * [W, H]
        self.v = (rng.random((n, 2)) - 0.5) * [10, 8] + [0, -7]
        self.s = rng.random(n) * 1.6 + 1.0
        self.a = rng.random(n) * 0.45 + 0.2
        self.ph = rng.random(n) * 6.28
        self.bp = rng.random((7, 2)) * [W, H]
        self.bs = rng.random(7) * 40 + 30

    def draw(self, c, t, strength=1.0):
        lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for (x, y), s in zip(self.bp, self.bs):
            px, py = (x + 4 * t) % W, (y - 10 * t) % H
            d.ellipse([px - s, py - s, px + s, py + s], fill=(255, 255, 255, int(14 * strength)))
        lay = lay.filter(ImageFilter.GaussianBlur(14))
        d = ImageDraw.Draw(lay)
        for (x, y), (vx, vy), s, a, ph in zip(self.p, self.v, self.s, self.a, self.ph):
            px, py = (x + vx * t) % W, (y + vy * t) % H
            al = int(255 * a * strength * (0.55 + 0.45 * math.sin(t * 1.1 + ph)))
            d.ellipse([px - s, py - s, px + s, py + s], fill=(255, 255, 255, al))
        c.alpha_composite(lay)


_NOISE = None


def dither(img):
    """Fixed fine noise (+/-3 levels) so gradients and glows don't band after H.264."""
    global _NOISE
    if _NOISE is None:
        _NOISE = (np.random.default_rng(3).random((H, W)) * 7 - 3.5).astype(np.int16)
    a = np.asarray(img, dtype=np.int16) + _NOISE[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def background(app, t, dark=False):
    """Deep app-tinted gradient with a slow drifting light."""
    if dark:
        top, bot = (16, 16, 20), (6, 6, 8)
    else:
        top = tuple(int(v * 0.5) for v in app["accent2"])
        bot = tuple(int(v * 0.9) for v in app["dark"])
    c = st.grad((W, H), top, bot).convert("RGBA")
    gx = W * (0.35 + 0.3 * math.sin(t * 0.3))
    gy = H * (0.22 + 0.08 * math.cos(t * 0.23))
    st.glow(c, (int(gx), int(gy)), 900, (255, 255, 255), 12 if dark else 20)
    return c


def fade_text(c, xy, text, f, fill, a, anchor="la", rise=24):
    """Text that fades up into place (a: 0..1)."""
    if a <= 0:
        return
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((xy[0], xy[1] + rise * (1 - a)), text, font=f, fill=fill + (int(255 * a),), anchor=anchor)
    c.alpha_composite(lay)


def fade_block(c, xy, text, f, fill, maxw, a, lh=1.06, align="left", rise=28):
    if a <= 0:
        return xy[1]
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
    y = st.text_block(ImageDraw.Draw(lay), (xy[0], xy[1] + rise * (1 - a)), text, f, fill + (int(255 * a),), maxw,
                      lh=lh, align=align)
    c.alpha_composite(lay)
    return y - rise * (1 - a)


def store_pill(c, y, text, app, a, cx=None, left=None, scale=1.0):
    if a <= 0:
        return
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = st.font("bold", int(38 * scale))
    w, h = d.textlength(text, font=f) + 84 * scale, 92 * scale
    x0 = left if left is not None else cx - w / 2
    y = y + 20 * (1 - a)
    d.rounded_rectangle([x0, y, x0 + w, y + h], radius=h / 2, fill=app["accent"] + (int(255 * a),))
    d.text((x0 + w / 2, y + h / 2 + 1), text, font=f, fill=app.get("ink", (20, 20, 20)) + (int(255 * a),), anchor="mm")
    c.alpha_composite(lay)


def sheen_at(t, start=1.6, period=4.0, dur=1.3):
    """One eased sweep per period, starting at `start`, None between sweeps."""
    if t < start:
        return None
    u = ((t - start) % period) / dur
    return None if u > 1 else -0.35 + 1.7 * ease_io(u)


def frame(app, layout, t, dur, head, sub, store, parts, tile):
    dark = layout == "reveal"
    c = background(app, t, dark)
    parts.draw(c, t, 0.6 if dark else 1.0)
    sw = sheen_at(t)
    ax = 0.045 * math.sin(t * 0.55)
    ay = 0.02 * math.sin(t * 0.4 + 1)
    if layout == "hero":
        intro = ease(t / 1.1)
        place_tile(c, turn(tile.render(sw), 0.07 + ax, ay), W * 0.66, 1420 + 70 * (1 - intro), -11 + 1.5 * math.sin(t * 0.5),
                   app["accent"], int(34 * intro))
        y = fade_block(c, (80, 330), head, st.font("bold", 96), INK, W - 160, ease((t - 0.25) / 0.7))
        fade_text(c, (80, y + 34), app["name"], st.font("semi", 44), INK, ease((t - 0.55) / 0.6))
        fade_text(c, (80, y + 94), sub, st.font("regular", 40), SUB, ease((t - 0.7) / 0.6))
        store_pill(c, y + 176, store, app, ease((t - 0.9) / 0.6), left=80)
    elif layout == "centred":
        intro = ease(t / 1.0)
        place_tile(c, turn(tile.render(sw), 0.05 + ax, ay), W / 2, 900 + 50 * (1 - intro), -7 + 1.5 * math.sin(t * 0.5),
                   app["accent"], int(40 * intro))
        fade_block(c, (60, 320), head, st.font("bold", 78), INK, W - 120, ease((t - 0.2) / 0.7), lh=1.08, align="center")
        fade_text(c, (W / 2, 1290), app["name"], st.font("semi", 48), INK, ease((t - 0.5) / 0.6), anchor="mm")
        fade_text(c, (W / 2, 1356), sub, st.font("regular", 40), SUB, ease((t - 0.65) / 0.6), anchor="mm")
        store_pill(c, 1430, store, app, ease((t - 0.85) / 0.6), cx=W / 2)
    else:  # reveal
        r = ease_io((t - 0.5) / 2.0)
        img = turn(tile.render(sw if t > 2.6 else None, reveal=r), 0.6 * ax, 0.6 * ay)
        st.glow(c, (W // 2, 930), 300 + int(180 * r), (255, 255, 255), int(8 + 30 * r))
        place_tile(c, img, W / 2, 930, 0, app["accent"], int(34 * r))
        fade_text(c, (W / 2, 400), head, st.font("bold", 92), INK, ease((t - 0.2) / 0.8), anchor="mm")
        fade_text(c, (W / 2, 494), app["name"], st.font("semi", 48), SUB, ease((t - 0.5) / 0.8), anchor="mm")
        fade_text(c, (W / 2, 1300), sub, st.font("regular", 40), SUB, ease((t - 2.2) / 0.7), anchor="mm")
        store_pill(c, 1380, store, app, ease((t - 2.5) / 0.7), cx=W / 2)
    k = min(ease(t / 0.4), ease((dur - t) / 0.6))
    if k < 1:
        c = Image.blend(Image.new("RGBA", c.size, (0, 0, 0, 255)), c, k)
    return dither(c.convert("RGB"))


SIZES = {"hero": 820, "centred": 540, "reveal": 500}


def render(slug, layout, head, sub, store, out, dur=8.0):
    app = st.APPS[slug]
    parts = Particles(60)
    tile = Tile(slug, SIZES[layout])
    work = tempfile.mkdtemp()
    try:
        for i in range(int(dur * FPS)):
            frame(app, layout, i / FPS, dur, head, sub, store, parts, tile).save(os.path.join(work, f"{i:04d}.png"))
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i",
                        os.path.join(work, "%04d.png"), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                        "-c:v", "libx264", "-preset", "slow", "-tune", "film", "-pix_fmt", "yuv420p", "-crf", "16",
                        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], check=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


if __name__ == "__main__":
    render(*sys.argv[1:7])
