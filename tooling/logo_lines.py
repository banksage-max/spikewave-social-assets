"""Logo round 4: the 2020 idea in a new form, exploring the line (owner, 15 Nov 2026:
direction "Old idea, new form", focus "the spike / wave line").

Fixed in every option: "Spike" in ink, "wave" reversed out of a blue box, the line crossing the seam
between the two (blue outside the box, white inside), and a split icon: paper on the left, blue on
the right, the line crossing the middle. Only the line changes.

    python tooling/logo_lines.py

Writes brand/logo-lines/L<n>-lockup.png, L<n>-icon.png (800 px, for profile pictures) and lines-board.png.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "brand", "logo-lines")
BLUE = (31, 111, 178)
INK, PAPER, MUTED, LINE, WHITE = (23, 23, 26), (251, 250, 247), (104, 100, 94), (214, 209, 198), (255, 255, 255)
S = 4


def inter(px, w):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter-Variable.ttf"), px)
    f.set_variation_by_axes([32 if px >= 60 else 14, w])
    return f


# Each line: points in a unit frame, x from -1 to 1 (seam at 0), y from -1 (bottom) to 1 (top).
def seismo():
    return [(-1, 0), (-0.72, 0), (-0.62, 0.22), (-0.52, -0.12), (-0.42, 0.42), (-0.32, 0.10), (-0.18, 1.0),
            (0.06, -1.0), (0.20, -0.30), (0.30, -0.52), (0.42, -0.08), (0.52, -0.22), (0.62, 0), (1, 0)]


def single():
    return [(-1, 0), (-0.30, 0), (-0.12, 1.0), (0.12, -1.0), (0.30, 0), (1, 0)]


def sine_to_spike():
    pts = [(-1 + i * 0.02, 0.28 * math.sin((-1 + i * 0.02) * math.pi * 3)) for i in range(0, 36)]  # -1 .. -0.30
    x0, y0 = pts[-1]
    return pts + [(-0.14, 1.0), (0.10, -1.0), (0.26, 0.0), (1, 0)]


def digital():
    return [(-1, 0), (-0.55, 0), (-0.55, 0.45), (-0.30, 0.45), (-0.30, -0.45), (-0.08, -0.45), (-0.08, 1.0),
            (0.12, 1.0), (0.12, -1.0), (0.32, -1.0), (0.32, 0), (1, 0)]


def ecg():
    return [(-1, 0), (-0.66, 0), (-0.56, 0.18), (-0.46, 0), (-0.22, 0), (-0.16, -0.22), (-0.06, 1.0),
            (0.06, -0.62), (0.14, 0), (0.38, 0), (0.50, 0.30), (0.62, 0), (1, 0)]


def crescendo():
    return [(-1, 0), (-0.74, 0), (-0.66, 0.25), (-0.58, -0.15), (-0.48, 0.45), (-0.38, -0.30), (-0.26, 0.70),
            (-0.14, -0.55), (0.00, 1.0), (0.14, -0.20), (0.22, 0), (1, 0)]


LINES = [
    ("L1", "Seismograph", "The 2020 line, tidied: small tremors, one big spike, settling down.", seismo),
    ("L2", "Single spike", "One clean peak and one trough. The simplest version, strongest when small.", single),
    ("L3", "Wave to spike", "A calm wave that breaks into one spike: the name, literally.", sine_to_spike),
    ("L4", "Digital pulse", "Square steps like a signal on a screen. Technical and crisp.", digital),
    ("L5", "Heartbeat", "A heartbeat trace. Warm and alive, but familiar from health apps.", ecg),
    ("L6", "Crescendo", "Peaks that grow left to right, ending in the tallest spike. Growth.", crescendo),
]


def draw_line(d, pts, cx, cy, half_w, half_h, width, fill):
    P = [(cx + x * half_w, cy - y * half_h) for x, y in pts]
    d.line(P, fill=fill, width=int(width), joint="curve")
    r = width / 2
    for x, y in (P[0], P[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def two_tone(size, rect, draw_fn, out_col, in_col):
    """Draw a line once; colour it out_col outside rect and in_col inside rect."""
    layer = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(layer), 255)
    inside = Image.new("L", size, 0)
    ImageDraw.Draw(inside).rectangle(rect, fill=255)
    a_in = Image.composite(layer, Image.new("L", size, 0), inside)
    a_out = Image.composite(Image.new("L", size, 0), layer, inside)
    return a_out, a_in


def lockup(fn):
    px = 120 * S
    f = inter(px, 620)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    wa, wb = tmp.textlength("Spike", font=f), tmp.textlength("wave", font=f)
    xb = f.getbbox("x")
    xh = xb[3] - xb[1]
    asc = f.getbbox("S")[1]
    half_w, half_h = xh * 1.45, xh * 1.10
    gap = half_w * 2 + xh * 0.30
    pad = xh * 0.42
    W = wa + gap + wb + pad
    H = half_h * 2 + xh * 0.6
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    mid = H / 2
    base = mid - (xb[1] + xb[3]) / 2           # x-height centred on the line's rest position
    d.text((0, base), "Spike", font=f, fill=INK)
    seam = wa + gap / 2
    tx = wa + gap
    top = base + asc - pad * 0.55
    bot = base + xb[3] + pad * 0.55
    rect = [seam, top, tx + wb + pad, bot]
    d.rectangle(rect, fill=BLUE)
    d.text((tx, base), "wave", font=f, fill=WHITE)
    lw = xh * 0.13
    a_out, a_in = two_tone(im.size, rect, lambda dd, c: draw_line(dd, fn(), seam, mid, half_w, half_h, lw, c), BLUE, WHITE)
    im.paste(Image.new("RGBA", im.size, BLUE + (255,)), (0, 0), a_out)
    im.paste(Image.new("RGBA", im.size, WHITE + (255,)), (0, 0), a_in)
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def icon(fn, size=800, rounded=False):
    n = size * S
    im = Image.new("RGBA", (n, n), WHITE + (255,))
    rect = [n / 2, 0, n, n]
    ImageDraw.Draw(im).rectangle(rect, fill=BLUE)
    lw = n * 0.055
    a_out, a_in = two_tone(im.size, rect, lambda dd, c: draw_line(dd, fn(), n / 2, n / 2, n * 0.34, n * 0.27, lw, c), BLUE, WHITE)
    im.paste(Image.new("RGBA", im.size, BLUE + (255,)), (0, 0), a_out)
    im.paste(Image.new("RGBA", im.size, WHITE + (255,)), (0, 0), a_in)
    if rounded:
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.23), fill=255)
        im.putalpha(m)
    return im.resize((size, size), Image.LANCZOS)


def circle(av, size):
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    t = Image.new("RGB", (size, size), (236, 233, 226))
    t.paste(av.convert("RGB").resize((size, size), Image.LANCZOS), (0, 0), m)
    return t


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    W, RH, TOP = 1900, 270, 150
    board = Image.new("RGB", (W, TOP + RH * len(LINES) + 30), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 44), "Spikewave logo, round 4: the 2020 idea in a new form", font=inter(40, 600), fill=INK)
    d.text((60, 98), "Same build every time (Spike, the line across the seam, wave in a blue box). Only the line changes. "
           "Right: app icon and profile picture at 160, 96 and 40 px.", font=inter(21, 400), fill=MUTED)
    for i, (key, title, note, fn) in enumerate(LINES):
        y = TOP + i * RH
        d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
        d.text((60, y + 18), f"{key}  {title}", font=inter(27, 600), fill=INK)
        d.text((60, y + 54), note, font=inter(19, 400), fill=MUTED)
        lp = lockup(fn)
        out = Image.new("RGB", (lp.width + 160, lp.height + 160), PAPER)
        out.paste(lp, (80, 80), lp)
        out.save(os.path.join(OUT, f"{key}-lockup.png"), optimize=True)
        ic = icon(fn)
        ic.convert("RGB").save(os.path.join(OUT, f"{key}-icon.png"), optimize=True)
        l2 = fit(lp, 760, 150)
        board.paste(l2, (60, y + 92 + (160 - l2.height) // 2), l2)
        tile = icon(fn, 160, rounded=True)
        x = W - 60 - 160
        ImageDraw.Draw(board).rounded_rectangle([x - 420, y + 76, W - 40, y + 260], radius=18, fill=(232, 229, 222))
        board.paste(circle(ic, 160), (x, y + 88))
        board.paste(circle(ic, 96), (x - 120, y + 120))
        board.paste(circle(ic, 40), (x - 180, y + 148))
        board.paste(tile, (x - 390, y + 88), tile)
    board.save(os.path.join(OUT, "lines-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
