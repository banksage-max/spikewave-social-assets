"""Completely new Spikewave logo concepts (owner, 15 Nov 2026: "develop completely new designs").

    python tooling/logo_new.py

Five concepts, none based on the 2020 logo or the current ink square. One accent (cobalt) plus ink,
flat shapes only. Each concept: the mark as an app-style tile, the profile picture (circle crop) at
40/96 px, and a name lockup on paper and on ink.
Writes brand/logo-new/concept-<key>-{tile,avatar,lockup}.png and concepts-board.png.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "brand", "logo-new")
COBALT = (36, 76, 212)       # 6.6:1 on white
COBALT_LIGHT = (122, 150, 255)
INK, PAPER, MUTED, LINE, WHITE = (23, 23, 26), (251, 250, 247), (104, 100, 94), (214, 209, 198), (255, 255, 255)
S = 4


def inter(px, w):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter-Variable.ttf"), px)
    f.set_variation_by_axes([w])
    return f


def serif(px):
    f = ImageFont.truetype(os.path.join(FONTS, "SourceSerif4-Variable.ttf"), px)
    f.set_variation_by_axes([600, 40])
    return f


def down(im):
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


# ---------- marks: each draws into an n x n RGBA canvas (n already supersampled) ----------

def mark_peak(n, fg, bg=None):
    """A: an S drawn as one continuous wave (two arcs), round ends."""
    im = Image.new("RGBA", (n * 2, n * 2), (0, 0, 0, 0))   # extra supersample for clean arcs
    d = ImageDraw.Draw(im)
    N = n * 2
    r, w = N * 0.17, N * 0.10
    cx, cy = N / 2, N / 2
    d.arc([cx - r, cy - 2 * r, cx + r, cy], start=90, end=335, fill=fg, width=int(w))
    d.arc([cx - r, cy, cx + r, cy + 2 * r], start=-90, end=155, fill=fg, width=int(w))
    for ang, c in ((335, (cx, cy - r)), (155, (cx, cy + r))):
        a = math.radians(ang)
        x, y = c[0] + (r - w / 2) * math.cos(a), c[1] + (r - w / 2) * math.sin(a)
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fg)
    return im.resize((n, n), Image.LANCZOS)


def mark_disc(n, fg, bg2):
    """B: a disc split by one wave; top half accent, bottom half ink."""
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    r = n * 0.38
    cx = cy = n / 2
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    top = Image.new("RGBA", (n, n), fg + (255,))
    bot = Image.new("RGBA", (n, n), bg2 + (255,))
    split = Image.new("L", (n, n), 0)
    pts = [(x, cy + n * 0.07 * math.sin((x - cx) / (2 * r) * 2 * math.pi)) for x in range(0, n + 1, 4)]
    ImageDraw.Draw(split).polygon(pts + [(n, n), (0, n)], fill=255)
    im.paste(top, (0, 0), mask)
    m2 = Image.composite(mask, Image.new("L", (n, n), 0), split)
    im.paste(bot, (0, 0), m2)
    return im


def mark_ring(n, fg, bg=None):
    """C: a pulse passing through a ring: the line peaks inside the circle."""
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r, w = n * 0.27, n * 0.065
    cx, cy = n / 2, n / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=int(w))
    pts = [(n * 0.10, cy), (cx - r * 0.42, cy), (cx - r * 0.12, cy - r * 0.62), (cx + r * 0.22, cy + r * 0.50),
           (cx + r * 0.46, cy), (n * 0.90, cy)]
    d.line(pts, fill=fg, width=int(w), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fg)
    return im


def mark_i(n, fg, bg=None):
    """D: the letter i, with its dot sharpened into a spike."""
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = n * 0.15
    cx = n / 2
    d.rounded_rectangle([cx - w / 2, n * 0.44, cx + w / 2, n * 0.84], radius=int(w / 2), fill=fg)
    d.polygon([(cx - w * 0.78, n * 0.36), (cx, n * 0.12), (cx + w * 0.78, n * 0.36)], fill=fg)
    return im


def mark_levels(n, fg, bg=None):
    """E: three level lines; the middle one carries a single sharp spike."""
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = n * 0.07
    x0, x1 = n * 0.18, n * 0.82
    for y in (n * 0.30, n * 0.74):
        d.line([(x0, y), (x1, y)], fill=fg, width=int(w))
        for x in (x0, x1):
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fg)
    y = n * 0.52
    pts = [(x0, y), (n * 0.44, y), (n * 0.53, n * 0.14), (n * 0.62, y + n * 0.0), (x1, y)]
    d.line(pts, fill=fg, width=int(w), joint="curve")
    for x, yy in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, yy - w / 2, x + w / 2, yy + w / 2], fill=fg)
    return im


CONCEPTS = [
    ("A", "Wave S", "The S of Spikewave drawn as one continuous wave. A monogram that also says wave.", mark_peak, "inter"),
    ("B", "Wave disc", "A circle cut by one wave: two colours, no lines. Calm, works tiny, made for round profile pictures.", mark_disc, "serif"),
    ("C", "Pulse", "A signal passing through a ring, peaking inside it. Like a lens on one moment.", mark_ring, "inter"),
    ("D", "The i", "The dot of the i sharpened into a spike. The mark comes straight from the name.", mark_i, "dotless"),
    ("E", "Levels", "Three level lines; the middle one spikes. Precise, calm, a little technical.", mark_levels, "inter"),
]


def tile(fn, size, bg, fg, fg2=INK):
    n = size * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.23), fill=bg)
    m = fn(n, fg, fg2)
    im.alpha_composite(m)
    return down(im)


def avatar(fn, bg, fg, fg2):
    n = 800 * S
    im = Image.new("RGBA", (n, n), bg + (255,))
    m = fn(int(n * 0.92), fg, fg2)
    im.alpha_composite(m, (int(n * 0.04), int(n * 0.04)))
    return down(im).convert("RGB")


def lockup(key, fn, face, dark):
    ink = PAPER if dark else INK
    acc = COBALT_LIGHT if dark else COBALT
    px = 120 * S
    f = serif(px) if face == "serif" else inter(px, 640)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    cap = f.getbbox("H")
    ch = cap[3] - cap[1]
    if face == "dotless":
        # Wordmark: "spıkewave" with a spike in place of the i's dot.
        word = "spıkewave"
        tw = tmp.textlength(word, font=f)
        W, H = tw + 8 * S, ch * 1.9
        im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        base = H * 0.62 - cap[3]
        d.text((0, base), word, font=f, fill=ink)
        x_i = tmp.textlength("sp", font=f)
        wi = tmp.textlength("ı", font=f)
        ib = f.getbbox("ı")
        stem = (ib[2] - ib[0])
        cx = x_i + ib[0] + stem / 2
        xh_top = base + f.getbbox("x")[1]
        d.polygon([(cx - stem * 0.78, xh_top - stem * 0.45), (cx, xh_top - stem * 2.1), (cx + stem * 0.78, xh_top - stem * 0.45)], fill=acc)
        return down(im)
    isz = int(ch * 1.6)
    gap = ch * 0.45
    tw = tmp.textlength("Spikewave", font=f)
    W, H = isz + gap + tw, isz
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    m = fn(isz, acc, ink)
    im.alpha_composite(m, (0, 0))
    d = ImageDraw.Draw(im)
    d.text((isz + gap, H / 2 - (cap[1] + cap[3]) / 2), "Spikewave", font=f, fill=ink)
    return down(im)


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def circle(av, size):
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    t = Image.new("RGB", (size, size), PAPER)
    t.paste(av.resize((size, size), Image.LANCZOS), (0, 0), m)
    return t


def main():
    os.makedirs(OUT, exist_ok=True)
    W, RH, TOP = 1900, 300, 150
    board = Image.new("RGB", (W, TOP + RH * len(CONCEPTS) + 40), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 44), "Spikewave: new logo concepts", font=inter(40, 600), fill=INK)
    d.text((60, 98), "Five new directions, one blue and ink. Left to right: icon, profile picture (220, 96, 40 px), name on paper, name on ink.",
           font=inter(22, 400), fill=MUTED)
    for i, (key, title, note, fn, face) in enumerate(CONCEPTS):
        y = TOP + i * RH
        d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
        t = tile(fn, 200, COBALT, WHITE, INK if key != "B" else INK)
        if key == "B":
            t = tile(fn, 200, PAPER, COBALT, INK)
        av = avatar(fn, COBALT, WHITE, INK) if key != "B" else avatar(fn, (255, 255, 255), COBALT, INK)
        lp, ld = lockup(key, fn, face, False), lockup(key, fn, face, True)
        t.save(os.path.join(OUT, f"concept-{key}-tile.png"))
        av.save(os.path.join(OUT, f"concept-{key}-avatar.png"), optimize=True)
        big = Image.new("RGB", (lp.width + 160, lp.height + 160), PAPER)
        big.paste(lp, (80, 80), lp)
        big.save(os.path.join(OUT, f"concept-{key}-lockup.png"), optimize=True)
        d.text((60, y + 18), f"{key}  {title}", font=inter(28, 600), fill=INK)
        d.text((60, y + 56), note, font=inter(19, 400), fill=MUTED)
        board.paste(t, (60, y + 90), t)
        board.paste(circle(av, 180), (300, y + 100))
        board.paste(circle(av, 96), (500, y + 142))
        board.paste(circle(av, 40), (614, y + 170))
        l2 = fit(lp, 520, 120)
        board.paste(l2, (700, y + 100 + (180 - l2.height) // 2), l2)
        panel = Image.new("RGB", (560, 190), INK)
        d2 = fit(ld, 470, 110)
        panel.paste(d2, ((560 - d2.width) // 2, (190 - d2.height) // 2), d2)
        board.paste(panel, (W - 60 - 560, y + 95))
    board.save(os.path.join(OUT, "concepts-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
