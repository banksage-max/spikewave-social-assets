"""Logo round 5: premium and calm, less template, a better-drawn line
(owner, 15 Nov 2026: still generic, line not right; feeling "premium and calm").

Approach: the website's serif (Source Serif 4) for the name, deep navy ink, one quiet blue, lots of space.
The spike is drawn by hand (Bezier curves, stroke contrast), not stuck on as a separate shape.

    python tooling/logo_premium.py

Writes brand/logo-premium/P<n>-lockup.png, P<n>-icon.png and premium-board.png.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "brand", "logo-premium")
NAVY = (19, 27, 46)
BLUE = (58, 98, 168)
PAPER, MUTED, LINE, WHITE = (250, 248, 243), (110, 106, 98), (218, 213, 203), (255, 255, 255)
S = 4


def serif(px, w=560, opsz=48):
    f = ImageFont.truetype(os.path.join(FONTS, "SourceSerif4-Variable.ttf"), px)
    f.set_variation_by_axes([w, opsz])
    return f


def inter(px, w):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter-Variable.ttf"), px)
    f.set_variation_by_axes([32 if px >= 60 else 14, w])
    return f


def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def stroke(d, pts, w, fill):
    d.line(pts, fill=fill, width=int(w), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def calm_line(x0, x1, y, amp, spike_h):
    """A slow wave that settles, then one fine, tall spike, then rest. Smooth everywhere except the spike."""
    w = x1 - x0
    p = []
    p += bez((x0, y), (x0 + w * 0.08, y - amp), (x0 + w * 0.16, y - amp), (x0 + w * 0.24, y))
    p += bez((x0 + w * 0.24, y), (x0 + w * 0.30, y + amp * 0.7), (x0 + w * 0.37, y + amp * 0.7), (x0 + w * 0.43, y))[1:]
    p += [(x0 + w * 0.52, y), (x0 + w * 0.56, y - spike_h), (x0 + w * 0.60, y + spike_h * 0.38), (x0 + w * 0.63, y)]
    p += [(x1, y)]
    return p


def tapered(d, a, b, w0, w1, fill):
    """A straight stroke whose width goes from w0 at a to w1 at b (for serif-like contrast)."""
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0]) + math.pi / 2
    dx, dy = math.cos(ang), math.sin(ang)
    d.polygon([(a[0] + dx * w0 / 2, a[1] + dy * w0 / 2), (b[0] + dx * w1 / 2, b[1] + dy * w1 / 2),
               (b[0] - dx * w1 / 2, b[1] - dy * w1 / 2), (a[0] - dx * w0 / 2, a[1] - dy * w0 / 2)], fill=fill)


# ---------------- options ----------------

def p1_calm_line(dark=False):
    """P1: the name in serif, a hand-drawn calm line beneath: a slow wave that ends in one fine spike."""
    ink = PAPER if dark else NAVY
    acc = (140, 170, 230) if dark else BLUE
    f = serif(120 * S)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = tmp.textlength("Spikewave", font=f)
    cap = f.getbbox("S")
    ch = cap[3] - cap[1]
    W, H = tw + 20 * S, ch * 2.15
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, ch * 0.05 - cap[1]), "Spikewave", font=f, fill=ink)
    y = ch * 1.62
    stroke(d, calm_line(ch * 0.04, tw, y, ch * 0.07, ch * 0.40), ch * 0.045, acc)
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def p2_spike_w(dark=False):
    """P2: the w of wave is redrawn so its middle stroke rises into a spike as tall as the k."""
    ink = PAPER if dark else NAVY
    acc = (140, 170, 230) if dark else BLUE
    f = serif(120 * S)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    a, c = "Spike", "ave"
    wa = tmp.textlength(a, font=f)
    ww = tmp.textlength("w", font=f) * 1.10
    wc = tmp.textlength(c, font=f)
    xb, kb = f.getbbox("x"), f.getbbox("k")
    xh = xb[3] - xb[1]
    thick = xh * 0.215         # the serif's main stem, measured by eye against the n
    thin = thick * 0.34
    W, H = wa + ww + wc + 10 * S, (kb[3] - kb[1]) * 1.45
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    oy = H * 0.12 - kb[1]
    d.text((0, oy), a, font=f, fill=ink)
    d.text((wa + ww, oy), c, font=f, fill=ink)
    top, base, peak = oy + xb[1], oy + xb[3], oy + kb[1]
    x0 = wa + thick * 1.25
    x1 = wa + ww - thick * 0.6
    q = (x1 - x0) / 4
    A, B, C, D_, E = (x0, top), (x0 + q, base), (x0 + 2 * q, peak), (x0 + 3 * q, base), (x1, top)
    tapered(d, A, B, thick, thick * 0.9, ink)
    tapered(d, B, C, thin, thin * 0.55, acc)       # the rising stroke becomes the spike, in blue
    tapered(d, C, D_, thin * 0.55, thick * 0.9, ink)
    tapered(d, D_, E, thin, thin, ink)
    # small flat serifs on the two top terminals, like the font's
    for x, s in ((A[0], thick), (E[0], thin)):
        d.rectangle([x - s * 1.1, top - thin * 0.05, x + s * 0.9, top + thin * 0.7], fill=ink)
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def p3_horizon(dark=False):
    """P3: name in serif with a hairline horizon running out of the e, with one quiet spike."""
    ink = PAPER if dark else NAVY
    acc = (140, 170, 230) if dark else BLUE
    f = serif(120 * S, w=500)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = tmp.textlength("Spikewave", font=f)
    cap = f.getbbox("S")
    ch = cap[3] - cap[1]
    tail = ch * 2.6
    W, H = tw + tail + ch * 0.3, ch * 1.9
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    oy = H * 0.5 - (cap[1] + cap[3]) / 2
    d.text((0, oy), "Spikewave", font=f, fill=ink)
    xb = f.getbbox("x")
    y = oy + (xb[1] + xb[3]) / 2
    x0 = tw + ch * 0.18
    pts = [(x0, y), (x0 + tail * 0.42, y), (x0 + tail * 0.52, y - ch * 0.72), (x0 + tail * 0.60, y + ch * 0.30),
           (x0 + tail * 0.66, y), (x0 + tail, y)]
    stroke(d, pts, ch * 0.034, acc)
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def icon_calm(size=800, bg=NAVY, fg=WHITE, acc=(140, 170, 230)):
    n = size * S
    im = Image.new("RGB", (n, n), bg)
    d = ImageDraw.Draw(im)
    stroke(d, calm_line(n * 0.20, n * 0.80, n * 0.56, n * 0.035, n * 0.24), n * 0.030, fg)
    return im.resize((size, size), Image.LANCZOS)


def icon_w(size=800, bg=NAVY, fg=WHITE, acc=(140, 170, 230)):
    n = size * S
    im = Image.new("RGB", (n, n), bg)
    d = ImageDraw.Draw(im)
    thick, thin = n * 0.075, n * 0.028
    top, base, peak = n * 0.42, n * 0.70, n * 0.24
    x0, x1 = n * 0.27, n * 0.73
    q = (x1 - x0) / 4
    A, B, C, D_, E = (x0, top), (x0 + q, base), (x0 + 2 * q, peak), (x0 + 3 * q, base), (x1, top)
    tapered(d, A, B, thick, thick * 0.9, fg)
    tapered(d, B, C, thin, thin * 0.6, acc)
    tapered(d, C, D_, thin * 0.6, thick * 0.9, fg)
    tapered(d, D_, E, thin, thin, fg)
    for x in (A[0], E[0]):
        d.rectangle([x - thick * 0.75, top - thin * 0.1, x + thick * 0.55, top + thin * 0.9], fill=fg)
    return im.resize((size, size), Image.LANCZOS)


def icon_horizon(size=800, bg=NAVY, fg=WHITE, acc=(140, 170, 230)):
    n = size * S
    im = Image.new("RGB", (n, n), bg)
    d = ImageDraw.Draw(im)
    y = n * 0.56
    pts = [(n * 0.16, y), (n * 0.44, y), (n * 0.51, n * 0.26), (n * 0.57, n * 0.66), (n * 0.62, y), (n * 0.84, y)]
    stroke(d, pts, n * 0.030, fg)
    return im.resize((size, size), Image.LANCZOS)


OPTIONS = [
    ("P1", "Calm line", "The name in the website's serif. Beneath it, a hand-drawn line: a slow wave that settles, then one fine spike.", p1_calm_line, icon_calm),
    ("P2", "The spike in the w", "No added shape: the w of \"wave\" is redrawn so its rising stroke becomes a spike as tall as the k, in blue.", p2_spike_w, icon_w),
    ("P3", "Horizon", "A hairline runs out of the name like a horizon and lifts once. Quiet, lots of space.", p3_horizon, icon_horizon),
]


def circle(av, size):
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    t = Image.new("RGB", (size, size), PAPER)
    t.paste(av.resize((size, size), Image.LANCZOS), (0, 0), m)
    return t


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    W, RH, TOP = 1900, 330, 150
    board = Image.new("RGB", (W, TOP + RH * len(OPTIONS) + 30), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 44), "Spikewave logo, round 5: premium and calm", font=inter(40, 600), fill=NAVY)
    d.text((60, 98), "The website's serif, deep navy and one quiet blue. The spike is drawn into the logo, not added on. "
           "Right: name on navy, profile picture at 200, 96 and 40 px.", font=inter(21, 400), fill=MUTED)
    for i, (key, title, note, fn, icf) in enumerate(OPTIONS):
        y = TOP + i * RH
        d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
        d.text((60, y + 18), f"{key}  {title}", font=inter(27, 600), fill=NAVY)
        d.text((60, y + 54), note, font=inter(19, 400), fill=MUTED)
        lp, ld = fn(False), fn(True)
        out = Image.new("RGB", (lp.width + 200, lp.height + 200), PAPER)
        out.paste(lp, (100, 100), lp)
        out.save(os.path.join(OUT, f"{key}-lockup.png"), optimize=True)
        ic = icf()
        ic.save(os.path.join(OUT, f"{key}-icon.png"), optimize=True)
        l2 = fit(lp, 620, 190)
        board.paste(l2, (60, y + 95 + (210 - l2.height) // 2), l2)
        panel = Image.new("RGB", (560, 220), NAVY)
        d2 = fit(ld, 470, 160)
        panel.paste(d2, ((560 - d2.width) // 2, (220 - d2.height) // 2), d2)
        board.paste(panel, (730, y + 88))
        x = W - 60 - 200
        board.paste(circle(ic, 200), (x, y + 95))
        board.paste(circle(ic, 96), (x - 125, y + 147))
        board.paste(circle(ic, 40), (x - 185, y + 175))
    board.save(os.path.join(OUT, "premium-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
