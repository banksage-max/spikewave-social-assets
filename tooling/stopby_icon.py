"""Stopby Reminders icon v2 (owner, 11 Nov 2026: variant 1 "Arriving dot"): violet tile, solid bell inside an
open ring, with a dot arriving at the gap. Exports the masters the app and stores need.

  python tooling/stopby_icon.py [teal|violet] [v2|A|B|C] [outdir]   ->  brand/icons/stopby-v3-teal/ (or stopby-v2/ for violet)
    icon-1024.png                 full square, opaque (App Store, Play 512 source, legacy launcher)
    play-512.png                  Play store listing icon
    adaptive-foreground-1024.png  Android adaptive foreground, glyph inside the 66/108 safe zone, transparent
    adaptive-background-1024.png  Android adaptive background (violet gradient)
    adaptive-monochrome-1024.png  Android 13 themed icon (white glyph, transparent)
    preview-rounded-1024.png      rounded preview for decks and the website
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S, K = 1024, 4
N = S * K
C = N / 2
import sys

PALETTES = {
    # v2: violet (owner picked 11 Nov, then dropped the same day)
    "violet": dict(v1=(124, 92, 255), v2=(70, 38, 200), shadow=(20, 0, 60), out="stopby-v2"),
    # v3: teal (owner's final choice, 11 Nov): #13968A -> #0D6B63, matches the app accent #0F766E
    "teal": dict(v1=(19, 150, 138), v2=(13, 107, 99), shadow=(0, 36, 32), out="stopby-v3-teal"),
}
PAL = PALETTES[sys.argv[1] if len(sys.argv) > 1 else "teal"]
LAYOUT = sys.argv[2] if len(sys.argv) > 2 else "v2"
V1, V2 = PAL["v1"], PAL["v2"]
OUT = os.path.join(os.path.dirname(__file__), "..", "brand", "icons", sys.argv[3] if len(sys.argv) > 3 else PAL["out"])


def background():
    y, x = np.mgrid[0:N, 0:N].astype(np.float32) / (N - 1)
    t = np.clip(x * 0.45 + y * 0.55, 0, 1)
    a, b = np.array(V1, np.float32), np.array(V2, np.float32)
    img = Image.fromarray((a + (b - a) * t[..., None]).astype(np.uint8), "RGB").convert("RGBA")
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    d = np.sqrt((xx - N * 0.25) ** 2 + (yy - N * 0.12) ** 2) / (N * 0.75)
    glow = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    glow.putalpha(Image.fromarray((np.clip(1 - d, 0, 1) ** 2 * 46).astype(np.uint8), "L"))
    img.alpha_composite(glow)
    return img


def bell(d, cx, cy, h):
    w = h * 0.84
    top = cy - h * 0.46
    lip_y = top + h * 0.74
    r_dome = w * 0.31
    dome_cy = top + r_dome
    pts = [(cx + r_dome * math.cos(math.pi + math.pi * i / 60), dome_cy + r_dome * math.sin(math.pi + math.pi * i / 60))
           for i in range(61)]
    side = []
    for i in range(61):
        t = i / 60
        side.append((cx + r_dome + (w / 2 - r_dome) * t ** 2.6, dome_cy + (lip_y - dome_cy) * t))
    pts += side + [(2 * cx - x, y) for (x, y) in reversed(side)]
    d.polygon(pts, fill=255)
    lip_h = h * 0.10
    d.rounded_rectangle([cx - w * 0.57, lip_y - 1, cx + w * 0.57, lip_y + lip_h], radius=lip_h / 2, fill=255)
    kr = h * 0.05
    d.ellipse([cx - kr, top - kr * 1.3, cx + kr, top + kr * 0.7], fill=255)
    cr = h * 0.085
    c2 = lip_y + lip_h + cr * 1.15
    d.ellipse([cx - cr, c2 - cr, cx + cr, c2 + cr], fill=255)


# Glyph layouts. "v2" = original single arriving dot at the ring gap.
# v4 (owner, 11 Nov): three radar blips on the outer ring ("a radar picking up alerts").
#   each dot = (angle in degrees, clockwise from 3 o'clock; radius as fraction of N)
LAYOUTS = {
    "v2": dict(gap=(-30, 250), dots=[(-50, 0.042)], halo=False),
    # A: closed ring, three blips of falling size, like a sweep that just passed them
    "A": dict(gap=None, dots=[(-40, 0.050), (75, 0.040), (200, 0.032)], halo=True),
    # B: open ring (gap top-right), three blips spread round the ring, the biggest at the gap
    "B": dict(gap=(-25, 255), dots=[(-50, 0.048), (110, 0.042), (185, 0.042)], halo=False),  # owner pick 11 Nov -> v4
    # C: closed ring, three equal blips clustered on the upper-right quadrant (fresh hits)
    "C": dict(gap=None, dots=[(-75, 0.036), (-35, 0.046), (5, 0.036)], halo=True),
}


def glyph(layout="v2"):
    """White glyph mask on N x N: outer ring (open or closed), blips on the ring, bell."""
    L = LAYOUTS[layout]
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    r, w = N * 0.335, N * 0.042
    rc = r - w / 2                     # centreline radius, so stroke, caps and dots share one centre
    a0, a1 = L["gap"] if L["gap"] else (0, 360)
    ts = np.radians(np.linspace(a0, a1, 1440))
    outer = [(C + r * math.cos(t), C + r * math.sin(t)) for t in ts]
    inner = [(C + (r - w) * math.cos(t), C + (r - w) * math.sin(t)) for t in ts[::-1]]
    d.polygon(outer + inner, fill=255)                     # ring as one filled band: smooth edges
    if L["gap"]:
        for t in (ts[0], ts[-1]):
            x, y = C + rc * math.cos(t), C + rc * math.sin(t)
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)
    for ang, rad in L["dots"]:
        a = math.radians(ang)
        x, y = C + rc * math.cos(a), C + rc * math.sin(a)
        if L["halo"]:                  # knock a clear gap round the blip so it reads at small sizes
            hr = N * rad + w * 0.75
            d.ellipse([x - hr, y - hr, x + hr, y + hr], fill=0)
        d.ellipse([x - N * rad, y - N * rad, x + N * rad, y + N * rad], fill=255)
    bell(d, C, C + N * 0.005, N * 0.38)
    return m


def with_shadow(base, mask):
    img = base.copy()
    sh = Image.new("RGBA", (N, N), PAL["shadow"] + (0,))
    sh.putalpha(mask.filter(ImageFilter.GaussianBlur(N / 70)).point(lambda v: int(v * 0.35)))
    img.alpha_composite(sh, (0, int(N / 90)))
    ink = Image.new("RGBA", (N, N), (255, 255, 255, 255))
    ink.putalpha(mask)
    img.alpha_composite(ink)
    return img


def scaled(mask, k):
    """Shrink a mask about the centre by factor k (for the adaptive safe zone)."""
    small = mask.resize((int(N * k), int(N * k)), Image.LANCZOS)
    out = Image.new("L", (N, N), 0)
    out.paste(small, ((N - small.width) // 2, (N - small.height) // 2))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    g = glyph(LAYOUT)
    full = with_shadow(background(), g)
    down = lambda im: im.resize((S, S), Image.LANCZOS)
    icon = down(full).convert("RGB")
    icon.save(os.path.join(OUT, "icon-1024.png"))
    icon.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "play-512.png"))
    down(background()).convert("RGB").save(os.path.join(OUT, "adaptive-background-1024.png"))
    # fit the glyph's measured extent into the adaptive safe zone (66/108 of the tile)
    bb = g.getbbox()
    extent = max(bb[2] - bb[0], bb[3] - bb[1], 2 * max(C - bb[0], bb[2] - C, C - bb[1], bb[3] - C)) / N
    k = min(0.80, (66 / 108) / extent)
    gs = scaled(g, k)
    print(f"glyph extent {extent:.3f} -> adaptive scale {k:.3f}")
    fg = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    fg = with_shadow(fg, gs)
    down(fg).save(os.path.join(OUT, "adaptive-foreground-1024.png"))
    mono = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    mono.putalpha(gs)
    down(mono).save(os.path.join(OUT, "adaptive-monochrome-1024.png"))
    rr = Image.new("L", (S, S), 0)
    ImageDraw.Draw(rr).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.225), fill=255)
    prev = icon.convert("RGBA")
    prev.putalpha(rr)
    prev.save(os.path.join(OUT, "preview-rounded-1024.png"))
    print("exported to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
