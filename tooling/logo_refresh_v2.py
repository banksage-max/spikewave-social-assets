"""Second, more refined round of the Spikewave logo refresh (owner, 15 Nov 2026: "more refined options").

    python tooling/logo_refresh_v2.py

Rules used for every option:
- one spike drawing (ripple, tall peak, deep trough, ripple), stroke weight = the letter stem weight
- one blue (#1F6FB2) and one ink (#17171A); no gradients, glows or shadows
- each option shown on paper and on ink, plus the profile picture at 40, 96 and 220 px

Writes brand/logo-refresh/v2/option-{1..4}.png (lockup on paper, 2x), icon-{blue,ink,paper}-800.png
and options-board-v2.png. Nothing is live until the owner picks.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "brand", "logo-refresh", "v2")
BLUE = (31, 111, 178)          # 5.3:1 against white
BLUE_LIGHT = (110, 176, 230)   # the same blue lifted for use on ink
INK, PAPER, MUTED, LINE = (23, 23, 26), (251, 250, 247), (104, 100, 94), (214, 209, 198)
S = 4

# The spike, in a unit box: x from -1 to 1, y from 0 (top) to 1 (bottom); 0.5 is the resting line.
SPIKE = [(-1.00, 0.50), (-0.58, 0.50), (-0.44, 0.36), (-0.32, 0.56), (-0.16, 0.00),
         (0.10, 1.00), (0.30, 0.38), (0.42, 0.60), (0.56, 0.50), (1.00, 0.50)]


def inter(px, weight):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter-Variable.ttf"), px)
    f.set_variation_by_axes([weight])
    return f


def serif(px):
    f = ImageFont.truetype(os.path.join(FONTS, "SourceSerif4-Variable.ttf"), px)
    f.set_variation_by_axes([600, 40])
    return f


def stem(f):
    """Stem width of the font: width of a capital I, which is one vertical stroke."""
    b = f.getbbox("I")
    return b[2] - b[0]


def spike(draw, cx, cy, half_w, half_h, width, fill, caps=True):
    pts = [(cx + x * half_w, cy + (y - 0.5) * 2 * half_h) for x, y in SPIKE]
    draw.line(pts, fill=fill, width=int(width), joint="curve")
    if caps:
        r = width / 2
        for x, y in (pts[0], pts[-1]):
            draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    return pts


def icon(size, bg, fg, radius=0.23):
    n = size * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * radius), fill=bg)
    spike(d, n / 2, n / 2, n * 0.33, n * 0.27, n * 0.068, fg)
    return im.resize((size, size), Image.LANCZOS)


def avatar(bg, fg):
    """800 px square for a circular crop: spike sized to sit inside the circle."""
    n = 800 * S
    im = Image.new("RGB", (n, n), bg)
    spike(ImageDraw.Draw(im), n / 2, n / 2, n * 0.30, n * 0.25, n * 0.062, fg)
    return im.resize((800, 800), Image.LANCZOS)


def _canvas(w, h):
    return Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))


def seam_lockup(dark=False, lower=False):
    """Options 1 and 2: SPIKE, the spike, then WAVE reversed out of a box that starts at the spike."""
    px = 120 * S
    f = inter(px, 600)
    a, b = ("spike", "wave") if lower else ("SPIKE", "WAVE")
    blue = BLUE_LIGHT if dark else BLUE
    sw = stem(f) * 0.62
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    wa, wb = tmp.textlength(a, font=f), tmp.textlength(b, font=f)
    ref = f.getbbox("x" if lower else "H")
    top, bot = ref[1], ref[3]
    xh = bot - top
    half_w = xh * 1.05
    half_h = xh * 1.0
    gap = half_w * 2 + xh * 0.50
    pad = xh * 0.36
    W = wa + gap + wb + pad * 1.1
    H = half_h * 2 + sw * 2
    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    base = H / 2 - (top + bot) / 2
    d.text((0, base), a, font=f, fill=blue)
    seam = wa + gap / 2
    tx = wa + gap
    by0, by1 = base + top - pad * 0.62, base + bot + pad * 0.62
    d.rectangle([seam, by0, tx + wb + pad, by1], fill=blue)
    d.text((tx, base), b, font=f, fill=INK if dark else (255, 255, 255))
    # The spike: blue outside the box, box colour reversed inside it.
    line = _canvas(W, H)
    spike(ImageDraw.Draw(line), seam, H / 2, half_w, half_h, sw, blue)
    inside = Image.new("L", im.size, 0)
    ImageDraw.Draw(inside).rectangle([seam, by0, W, by1], fill=255)
    a_line = line.split()[3]
    im.alpha_composite(line)
    rev = Image.new("RGBA", im.size, INK + (255,) if dark else (255, 255, 255, 255))
    im.paste(rev, (0, 0), Image.composite(a_line, Image.new("L", im.size, 0), inside))
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def icon_lockup(dark=False, use_serif=False):
    """Options 3 and 4: the icon, then the name (two-tone sans, or the website serif)."""
    px = 120 * S
    f = serif(px) if use_serif else inter(px, 600)
    ink = PAPER if dark else INK
    blue = BLUE_LIGHT if dark else BLUE
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    ref = f.getbbox("H")
    cap = ref[3] - ref[1]
    isz = int(cap * 1.55)
    gap = cap * 0.42
    if use_serif:
        tw = tmp.textlength("Spikewave", font=f)
    else:
        w1, w2 = tmp.textlength("Spike", font=f), tmp.textlength("wave", font=f)
        tw = w1 + w2
    W, H = isz + gap + tw, max(isz, cap * 1.9)
    im = _canvas(W, H)
    ic = icon(isz // S * S, blue, INK if dark else (255, 255, 255))
    ic = ic.resize((isz, isz), Image.LANCZOS)
    im.paste(ic, (0, int((H - isz) / 2)), ic)
    d = ImageDraw.Draw(im)
    base = H / 2 - (ref[1] + ref[3]) / 2
    x = isz + gap
    if use_serif:
        d.text((x, base), "Spikewave", font=f, fill=ink)
    else:
        d.text((x, base), "Spike", font=f, fill=ink)
        d.text((x + w1, base), "wave", font=f, fill=blue)
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def circle(av, size, bg):
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    tile = Image.new("RGB", (size, size), bg)
    tile.paste(av.resize((size, size), Image.LANCZOS), (0, 0), m)
    return tile


def main():
    os.makedirs(OUT, exist_ok=True)
    av_blue = avatar(BLUE, (255, 255, 255))
    av_ink = avatar(INK, BLUE_LIGHT)
    av_paper = avatar((255, 255, 255), BLUE)
    for name, av in (("blue", av_blue), ("ink", av_ink), ("paper", av_paper)):
        av.save(os.path.join(OUT, f"icon-{name}-800.png"), optimize=True)

    options = [
        ("1", "Seam, capitals", "Closest to the 2020 logo. The box now starts exactly at the spike, and the line weight is matched to the letters.",
         seam_lockup, {}, av_blue),
        ("2", "Seam, lowercase", "Same construction, softer and more current. Reads well at small sizes.",
         seam_lockup, {"lower": True}, av_blue),
        ("3", "Icon + two-tone name", "The spike moves into a blue app-style icon; \"wave\" stays blue, echoing the old split.",
         icon_lockup, {}, av_blue),
        ("4", "Icon + serif name", "The same icon with the website's serif. Quietest and most \"company\".",
         icon_lockup, {"use_serif": True}, av_ink),
    ]
    W, RH, TOP = 1800, 330, 150
    board = Image.new("RGB", (W, TOP + RH * len(options) + 260), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 44), "Spikewave logo refresh, round 2", font=inter(40, 600), fill=INK)
    d.text((60, 98), "Based on the 2020 YouTube logo. Each option on paper, on ink, and as a profile picture at 40, 96 and 220 px.",
           font=inter(22, 400), fill=MUTED)
    for i, (key, title, note, fn, kw, av) in enumerate(options):
        y = TOP + i * RH
        d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
        d.text((60, y + 18), f"{key}  {title}", font=inter(28, 600), fill=INK)
        d.text((60, y + 56), note, font=inter(20, 400), fill=MUTED)
        light = fn(dark=False, **kw)
        dark = fn(dark=True, **kw)
        Image.new("RGB", (1, 1))
        out = Image.new("RGB", (light.width * 2 + 160, light.height * 2 + 160), PAPER)
        big = light.resize((light.width * 2, light.height * 2), Image.LANCZOS)
        out.paste(big, (80, 80), big)
        out.save(os.path.join(OUT, f"option-{key}.png"), optimize=True)
        l2 = fit(light, 560, 150)
        board.paste(l2, (60, y + 110 + (180 - l2.height) // 2), l2)
        panel = Image.new("RGB", (620, 200), INK)
        d2 = fit(dark, 520, 140)
        panel.paste(d2, ((620 - d2.width) // 2, (200 - d2.height) // 2), d2)
        board.paste(panel, (680, y + 100))
        x = W - 60 - 220
        board.paste(circle(av, 220, PAPER), (x, y + 90))
        board.paste(circle(av, 96, PAPER), (x - 130, y + 90 + 62))
        board.paste(circle(av, 40, PAPER), (x - 190, y + 90 + 90))
    # Icon colourways strip.
    y = TOP + RH * len(options)
    d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
    d.text((60, y + 18), "Profile picture colourways (any option can use any of these)", font=inter(28, 600), fill=INK)
    for j, (lab, av) in enumerate((("Blue", av_blue), ("Ink", av_ink), ("White", av_paper))):
        x = 60 + j * 300
        board.paste(circle(av, 160, PAPER), (x, y + 70))
        d.text((x + 180, y + 135), lab, font=inter(22, 500), fill=INK)
    board.save(os.path.join(OUT, "options-board-v2.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
