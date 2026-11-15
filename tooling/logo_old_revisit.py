"""Revisit of the original 2020 Spikewave logo, kept close to how it was drawn
(owner, 15 Nov 2026: "revisit old design").

Read from the old YouTube picture: light, rounded capitals; SPIKE in sky blue; WAVE white in a sky-blue
box; a thin, jagged seismograph line that climbs over "KE" to a tall peak, drops through the box's
left edge and finishes in a small zigzag under the box.

    python tooling/logo_old_revisit.py

Writes brand/logo-old-revisit/: R1-R3 lockups (paper + ink), matching profile pictures, and revisit-board.png.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "brand", "logo-old-revisit")
SKY = (84, 166, 222)          # the 2020 blue, cleaned
SKY_DEEP = (31, 111, 178)     # a deeper blue that passes contrast for white text
INK, PAPER, MUTED, LINE, WHITE = (23, 23, 26), (251, 250, 247), (104, 100, 94), (214, 209, 198), (255, 255, 255)
S = 4


def inter(px, w):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter-Variable.ttf"), px)
    f.set_variation_by_axes([32 if px >= 60 else 14, w])  # Inter axes: optical size, weight
    return f


# Seismograph line in cap-height units, origin at the box's top-left corner; bh = box height in cap units.
def wave(bh):
    return [(-1.30, -0.30), (-1.10, -0.52), (-0.96, -0.36), (-0.80, -0.78), (-0.66, -0.50),
            (-0.40, -1.10), (0.22, bh + 0.95), (0.38, bh + 0.40), (0.50, bh + 0.70), (0.64, bh + 0.30)]


def lockup(blue, weight, dark=False, line_w=0.075, a="SPIKE", b="WAVE"):
    px = 120 * S
    f = inter(px, weight)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    cap = f.getbbox("H")
    ch = cap[3] - cap[1]
    wa, wb = tmp.textlength(a, font=f), tmp.textlength(b, font=f)
    pad_x, pad_y = ch * 0.16, ch * 0.24
    gap = ch * 0.10
    bx0 = wa + gap
    bx1 = bx0 + pad_x * 2 + wb
    top_room, bot_room = ch * 1.25, ch * 1.10
    H = top_room + ch + pad_y * 2 + bot_room
    W = bx1 + ch * 0.1
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    by0 = top_room
    by1 = by0 + ch + pad_y * 2
    base = by0 + pad_y - cap[1]
    d.text((0, base), a, font=f, fill=blue)
    d.rectangle([bx0, by0, bx1, by1], fill=blue)
    d.text((bx0 + pad_x, base), b, font=f, fill=INK if dark else WHITE)
    bh = (by1 - by0) / ch
    pts = [(bx0 + x * ch, by0 + y * ch) for x, y in wave(bh)]
    lw = ch * line_w
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts, fill=blue, width=int(lw), joint="curve")
    inside = Image.new("L", im.size, 0)
    ImageDraw.Draw(inside).rectangle([bx0, by0, bx1, by1], fill=255)
    a = layer.split()[3]
    im.alpha_composite(layer)
    im.paste(Image.new("RGBA", im.size, (INK if dark else WHITE) + (255,)), (0, 0),
             Image.composite(a, Image.new("L", im.size, 0), inside))
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def avatar(kw, bg):
    """Profile picture: the logo in miniature, S + line + W in the box, centred on a white circle."""
    mini = lockup(**dict(kw, a="S", b="W", line_w=max(kw.get("line_w", 0.075), 0.10)))
    av = Image.new("RGB", (800, 800), bg)
    k = min(560 / mini.width, 560 / mini.height)
    m = mini.resize((int(mini.width * k), int(mini.height * k)), Image.LANCZOS)
    av.paste(m, ((800 - m.width) // 2, (800 - m.height) // 2), m)
    return av


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
    rows = [
        ("R1", "As it was, cleaned up", "Same light letters, sky blue and jagged line as 2020, redrawn sharp. Nothing else changed.",
         dict(blue=SKY, weight=300), (WHITE, SKY, WHITE, SKY)),
        ("R2", "Same design, a little stronger", "Medium-weight letters and a deeper blue so white text passes contrast. The line and layout are untouched.",
         dict(blue=SKY_DEEP, weight=500), (WHITE, SKY_DEEP, WHITE, SKY_DEEP)),
        ("R3", "Same design, bold", "Heavier letters and a heavier line for small screens and app stores. Still the 2020 composition.",
         dict(blue=SKY_DEEP, weight=650, line_w=0.10), (SKY_DEEP, WHITE, SKY_DEEP, WHITE)),
    ]
    W, RH, TOP = 1900, 340, 150
    board = Image.new("RGB", (W, TOP + RH * len(rows) + 30), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 44), "Spikewave: the 2020 logo, revisited", font=inter(40, 600), fill=INK)
    d.text((60, 98), "Kept close to the original. Left: on paper. Middle: on ink. Right: profile picture at 220, 96 and 40 px.",
           font=inter(22, 400), fill=MUTED)
    for i, (key, title, note, kw, avc) in enumerate(rows):
        y = TOP + i * RH
        d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
        d.text((60, y + 18), f"{key}  {title}", font=inter(28, 600), fill=INK)
        d.text((60, y + 56), note, font=inter(19, 400), fill=MUTED)
        lp = lockup(**kw)
        kd = dict(kw)
        if kd["blue"] == SKY_DEEP:
            kd["blue"] = SKY
        ld = lockup(dark=True, **kd)
        out = Image.new("RGB", (lp.width + 160, lp.height + 160), PAPER)
        out.paste(lp, (80, 80), lp)
        out.save(os.path.join(OUT, f"{key}-lockup.png"), optimize=True)
        av = avatar(kw, WHITE)
        av.save(os.path.join(OUT, f"{key}-avatar.png"), optimize=True)
        l2 = fit(lp, 560, 210)
        board.paste(l2, (60, y + 95 + (220 - l2.height) // 2), l2)
        panel = Image.new("RGB", (600, 230), INK)
        d2 = fit(ld, 520, 190)
        panel.paste(d2, ((600 - d2.width) // 2, (230 - d2.height) // 2), d2)
        board.paste(panel, (680, y + 90))
        x = W - 60 - 220
        board.paste(circle(av, 220), (x, y + 95))
        board.paste(circle(av, 96), (x - 130, y + 157))
        board.paste(circle(av, 40), (x - 190, y + 185))
    board.save(os.path.join(OUT, "revisit-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
