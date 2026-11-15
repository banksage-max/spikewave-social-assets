"""Logo round 6: refining P1 "Calm line" (owner, 15 Nov 2026: "lets work with p1").

Variants of the lockup (where the spike sits, line weight, colour), icon variants, and a small-size test.

    python tooling/logo_p1.py

Writes brand/logo-p1/ (lockups, icons, favicon test) and p1-board.png.
"""
import os

from PIL import Image, ImageDraw

import logo_premium as P

OUT = os.path.join(os.path.dirname(P.HERE), "brand", "logo-p1")
NAVY, BLUE, PAPER, MUTED, LINE, WHITE = P.NAVY, P.BLUE, P.PAPER, P.MUTED, P.LINE, P.WHITE
BLUE_ON_NAVY = (140, 170, 230)
S = P.S


def line_pts(x0, x1, y, amp, spike_h, order="wave-spike", spike_at=0.56):
    """The calm line. order 'wave-spike' = slow wave then spike (P1);
    'spike-wave' = spike first (under "Spike") then the slow wave (under "wave")."""
    w = x1 - x0
    bez = P.bez
    if order == "wave-spike":
        p = bez((x0, y), (x0 + w * .08, y - amp), (x0 + w * .16, y - amp), (x0 + w * .24, y))
        p += bez((x0 + w * .24, y), (x0 + w * .30, y + amp * .7), (x0 + w * .37, y + amp * .7), (x0 + w * .43, y))[1:]
        s = spike_at
        p += [(x0 + w * (s - .04), y), (x0 + w * s, y - spike_h), (x0 + w * (s + .04), y + spike_h * .38),
              (x0 + w * (s + .07), y), (x1, y)]
        return p
    s = spike_at
    p = [(x0, y), (x0 + w * (s - .04), y), (x0 + w * s, y - spike_h), (x0 + w * (s + .04), y + spike_h * .38),
         (x0 + w * (s + .07), y)]
    a = x0 + w * (s + .07)
    r = x1 - a
    p += bez((a, y), (a + r * .16, y - amp), (a + r * .32, y - amp), (a + r * .48, y))[1:]
    p += bez((a + r * .48, y), (a + r * .62, y + amp * .7), (a + r * .78, y + amp * .7), (x1, y))[1:]
    return p


def lockup(order="wave-spike", weight=0.045, colour="blue", length=1.0, dark=False, spike_at=None):
    ink = PAPER if dark else NAVY
    acc = {"blue": BLUE_ON_NAVY if dark else BLUE, "ink": ink}[colour]
    f = P.serif(120 * S)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = tmp.textlength("Spikewave", font=f)
    wspike = tmp.textlength("Spike", font=f)
    cap = f.getbbox("S")
    ch = cap[3] - cap[1]
    W, H = tw + 20 * S, ch * 2.15
    im = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, ch * .05 - cap[1]), "Spikewave", font=f, fill=ink)
    y = ch * 1.62
    x0 = ch * .04
    x1 = x0 + (tw - x0) * length
    if spike_at is None:
        # Spike-first puts the spike under the k of "Spike"; wave-first keeps the P1 position.
        kx = tmp.textlength("Spi", font=f) + tmp.textlength("k", font=f) * 0.5
        spike_at = (kx - x0) / (x1 - x0) if order == "spike-wave" else 0.56
    P.stroke(d, line_pts(x0, x1, y, ch * .07, ch * .40, order, spike_at), ch * weight, acc)
    return im.resize((int(W) // S, int(H) // S), Image.LANCZOS)


def icon(kind="line", size=800, bg=NAVY, fg=WHITE):
    n = size * S
    im = Image.new("RGB", (n, n), bg)
    d = ImageDraw.Draw(im)
    if kind == "line":           # the line alone, as in round 5
        P.stroke(d, line_pts(n * .20, n * .80, n * .56, n * .035, n * .24), n * .030, fg)
    elif kind == "bold":         # heavier and bigger so it survives 40 px
        P.stroke(d, line_pts(n * .14, n * .86, n * .58, n * .055, n * .30, spike_at=0.58), n * .055, fg)
    elif kind == "S":            # the serif S sitting on the line
        f = P.serif(int(n * .46))
        b = f.getbbox("S")
        d.text(((n - (b[2] - b[0])) / 2 - b[0], n * .40 - (b[3] - b[1]) / 2 - b[1]), "S", font=f, fill=fg)
        P.stroke(d, line_pts(n * .20, n * .80, n * .74, n * .028, n * .13, spike_at=0.60), n * .028, BLUE_ON_NAVY)
    return im.resize((size, size), Image.LANCZOS)


def circle(av, size, bg=PAPER):
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    t = Image.new("RGB", (size, size), bg)
    t.paste(av.resize((size, size), Image.LANCZOS), (0, 0), m)
    return t


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    variants = [
        ("a", "P1 as it was", "Slow wave first, spike towards the end.", dict()),
        ("b", "Spike under Spike", "Same line, reversed to follow the name: the spike sits under the k, the slow wave runs under \"wave\".",
         dict(order="spike-wave")),
        ("c", "Finer line", "Variant b with a hairline closer to the serif's thin strokes. Quieter, more premium; weaker when small.",
         dict(order="spike-wave", weight=0.030)),
        ("d", "One colour", "Variant b in navy only. Most restrained; works on letterheads, invoices and embossing.",
         dict(order="spike-wave", colour="ink")),
    ]
    icons = [("line", "Line only (round 5)"), ("bold", "Line, bolder for small sizes"), ("S", "Serif S on the line")]
    W = 1900
    RH = 230
    TOP = 150
    H = TOP + RH * len(variants) + 520
    board = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 44), "Spikewave logo, round 6: refining P1", font=P.inter(40, 600), fill=NAVY)
    d.text((60, 98), "Lockup variants on paper and navy, then three profile-picture options tested from 200 px down to a 16 px browser tab.",
           font=P.inter(21, 400), fill=MUTED)
    for i, (k, title, note, kw) in enumerate(variants):
        y = TOP + i * RH
        d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
        d.text((60, y + 16), f"P1{k}  {title}", font=P.inter(26, 600), fill=NAVY)
        d.text((60, y + 50), note, font=P.inter(18, 400), fill=MUTED)
        lp, ld = lockup(**kw), lockup(dark=True, **kw)
        out = Image.new("RGB", (lp.width + 200, lp.height + 200), PAPER)
        out.paste(lp, (100, 100), lp)
        out.save(os.path.join(OUT, f"P1{k}-lockup.png"), optimize=True)
        l2 = fit(lp, 520, 140)
        board.paste(l2, (60, y + 82 + (140 - l2.height) // 2), l2)
        panel = Image.new("RGB", (520, 150), NAVY)
        d2 = fit(ld, 440, 110)
        panel.paste(d2, ((520 - d2.width) // 2, (150 - d2.height) // 2), d2)
        board.paste(panel, (640, y + 76))
        # small size test of the lockup
        sm = fit(lp, 180, 40)
        board.paste(sm, (1220, y + 120), sm)
        d.text((1220, y + 90), "at 180 px wide", font=P.inter(16, 400), fill=MUTED)
    y = TOP + RH * len(variants)
    d.line([(60, y), (W - 60, y)], fill=LINE, width=2)
    d.text((60, y + 16), "Profile picture / app icon", font=P.inter(26, 600), fill=NAVY)
    for j, (kind, label) in enumerate(icons):
        x = 60 + j * 600
        ic = icon(kind)
        ic.save(os.path.join(OUT, f"icon-{kind}-800.png"), optimize=True)
        board.paste(circle(ic, 200), (x, y + 70))
        board.paste(circle(ic, 96), (x + 220, y + 122))
        board.paste(circle(ic, 40), (x + 330, y + 150))
        fav = ic.resize((32, 32), Image.LANCZOS)
        board.paste(fav, (x + 390, y + 154))
        board.paste(ic.resize((16, 16), Image.LANCZOS), (x + 436, y + 162))
        d.text((x, y + 290), label, font=P.inter(20, 500), fill=NAVY)
        d.text((x + 390, y + 200), "32 / 16 px tab", font=P.inter(14, 400), fill=MUTED)
    board.save(os.path.join(OUT, "p1-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
