"""Icon study: the line runs AFTER the S (to its right) instead of under it (owner, 15 Nov 2026).

    python tooling/logo_s_after.py

Writes brand/logo/s-after/icon-<v>.png and s-after-board.png.
"""
import os

from PIL import Image, ImageDraw

import logo_p1 as L1
import logo_premium as P

OUT = os.path.join(os.path.dirname(P.HERE), "brand", "logo", "s-after")
NAVY, PAPER, MUTED, LINE, WHITE = P.NAVY, P.PAPER, P.MUTED, P.LINE, P.WHITE
BLUE_ON_NAVY = L1.BLUE_ON_NAVY
S = P.S


def s_glyph(n, h_share):
    f = P.serif(int(n * h_share), w=600, opsz=60)
    return f, f.getbbox("S")


def after_line(x0, y, n, start_wave=True):
    """Fixed-size pieces so the spike keeps its shape: a calm wave (two soft humps), then a spike
    (up sharply, small dip), then a short rest."""
    bz = P.bez
    hw = n * 0.075          # width of one soft hump
    amp = n * 0.026
    p = []
    x = x0
    if start_wave:
        p += bz((x, y), (x + hw * .35, y - amp), (x + hw * .65, y - amp), (x + hw, y))
        p += bz((x + hw, y), (x + hw * 1.35, y + amp * .8), (x + hw * 1.65, y + amp * .8), (x + hw * 2, y))[1:]
        x += hw * 2
    p += [(x + n * 0.03, y), (x + n * 0.055, y - n * 0.15), (x + n * 0.085, y + n * 0.05), (x + n * 0.105, y), (x + n * 0.17, y)]
    return p


def icon(variant, size=1024):
    n = size * S
    im = Image.new("RGB", (n, n), NAVY)
    d = ImageDraw.Draw(im)
    f, b = s_glyph(n, 0.40)
    sw, sh = b[2] - b[0], b[3] - b[1]
    lw = n * 0.024
    line_w = n * (0.075 * 2 + 0.17)
    total = sw + n * 0.035 + line_w
    x = (n - total) / 2
    ys = (n - sh) / 2
    if variant == "under":   # the current final, for comparison
        return Image.open(os.path.join(os.path.dirname(OUT), "spikewave-icon-1024.png")).resize((size, size), Image.LANCZOS)
    d.text((x - b[0], ys - b[1]), "S", font=f, fill=WHITE)
    x0 = x + sw + n * 0.035
    if variant == "mid":
        P.stroke(d, after_line(x0, n / 2 + n * 0.01, n), lw, BLUE_ON_NAVY)
    elif variant == "base":
        P.stroke(d, after_line(x0 - n * 0.02, ys + sh - lw * 0.5, n), lw, BLUE_ON_NAVY)
    elif variant == "tail":
        P.stroke(d, after_line(x + sw * 0.86, ys + sh * 0.84, n), lw, WHITE)
    return im.resize((size, size), Image.LANCZOS)


def wrap(d, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t2 = f"{cur} {w}".strip()
        if d.textlength(t2, font=f) <= width:
            cur = t2
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


VARIANTS = [
    ("under", "Current: line under the S", "For comparison."),
    ("mid", "Line after the S, mid-height", "S, then a calm wave and one spike. Reads left to right like the name: S... wave."),
    ("base", "Line after the S, on the baseline", "The line starts from the foot of the S and lifts once, like an underline that carries on."),
    ("tail", "The S flows into the line", "One gesture: the letter's tail becomes the wave and the spike. All white, calmest."),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    W, H = 1900, 760
    board = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 40), "Icon study: the wave after the S", font=P.inter(40, 600), fill=NAVY)
    d.text((60, 94), "Each icon as a circle at 260, 96 and 40 px, plus a 32 px browser tab.", font=P.inter(21, 400), fill=MUTED)
    for i, (v, title, note) in enumerate(VARIANTS):
        x = 60 + i * 455
        ic = icon(v)
        ic.save(os.path.join(OUT, f"icon-{v}.png"), optimize=True)
        board.paste(L1.circle(ic, 260), (x, 160))
        board.paste(L1.circle(ic, 96), (x, 450))
        board.paste(L1.circle(ic, 40), (x + 120, 478))
        board.paste(ic.resize((32, 32), Image.LANCZOS), (x + 184, 482))
        d.text((x, 580), title, font=P.inter(20, 600), fill=NAVY)
        for j, line in enumerate(wrap(d, note, P.inter(16, 400), 400)):
            d.text((x, 612 + j * 22), line, font=P.inter(16, 400), fill=MUTED)
    board.save(os.path.join(OUT, "s-after-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
