"""Refresh of the original Spikewave logo (YouTube, 2020): SPIKE in blue, WAVE reversed out of a
blue box, a jagged waveform crossing the seam between the two words.

    python tooling/logo_refresh.py

Writes brand/logo-refresh/option-{a,b,c}-wordmark.png, option-{a,b,c}-avatar.png and options-board.png.
Nothing here is live; the owner picks an option first.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "brand", "logo-refresh")
BLUE = (31, 122, 194)        # deeper than the 2020 sky blue (91,170,220) so white text on it reads (4.6:1)
BLUE_DARK = (18, 74, 122)
PAPER, INK = (251, 250, 247), (23, 23, 26)
S = 4                        # supersample


def inter(size, weight):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter-Variable.ttf"), size)
    f.set_variation_by_axes([weight])
    return f


def serif(size):
    f = ImageFont.truetype(os.path.join(FONTS, "SourceSerif4-Variable.ttf"), size)
    f.set_variation_by_axes([600, 40])
    return f


def wave_pts(x, top, bottom, w):
    """A tidy version of the 2020 spike: small ripple, tall spike up, deep spike down, small ripple.
    x is the seam, top/bottom the vertical extent, w the half-width of the wave."""
    h = bottom - top
    mid = top + h * 0.5
    rel = [(-1.00, 0.50), (-0.70, 0.50), (-0.55, 0.30), (-0.40, 0.58), (-0.22, 0.00),
           (0.05, 1.00), (0.25, 0.42), (0.40, 0.66), (0.55, 0.50), (1.00, 0.50)]
    return [(x + rx * w, top + ry * h) for rx, ry in rel], mid


def wordmark(text_a, text_b, size, case_upper=True, weight=600):
    """SPIKE | [WAVE] with the waveform across the seam. Returns RGBA at 1x."""
    f = inter(size * S, weight)
    a, b = (text_a.upper(), text_b.upper()) if case_upper else (text_a, text_b)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    wa, wb = tmp.textlength(a, font=f), tmp.textlength(b, font=f)
    asc, desc = f.getmetrics()
    cap = f.getbbox("H")
    cap_top, cap_bot = cap[1], cap[3]
    pad_x, pad_y = int(size * 0.28 * S), int(size * 0.22 * S)
    wave_w = size * 0.34 * S          # half-width of the wave
    gap = int(2 * wave_w + size * 0.16 * S)  # the wave sits in the gap, clear of both words
    wave_h = int((cap_bot - cap_top) * 2.3)
    W = int(wa + gap + pad_x * 2 + wb + size * 0.2 * S)
    H = wave_h + pad_y * 2
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base_y = (H - (cap_bot - cap_top)) // 2 - cap_top
    d.text((0, base_y), a, font=f, fill=BLUE)
    seam = int(wa + gap / 2)          # the box starts at the seam, so the wave's right half is white inside it
    tx = int(wa + gap)                # WAVE starts clear of the wave
    bx0, bx1 = seam, int(tx + wb + pad_x)
    by0, by1 = base_y + cap_top - pad_y, base_y + cap_bot + pad_y
    d.rectangle([bx0, by0, bx1, by1], fill=BLUE)
    d.text((tx, base_y), b, font=f, fill=(255, 255, 255))
    pts, _ = wave_pts(seam, (H - wave_h) // 2, (H + wave_h) // 2, wave_w)
    lw = max(2, int(size * 0.075 * S))
    # The line is blue outside the box and white where it crosses the box.
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts, fill=BLUE, width=lw, joint="curve")
    inside = Image.new("L", im.size, 0)
    ImageDraw.Draw(inside).rectangle([bx0, by0, bx1, by1], fill=255)
    white = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im.alpha_composite(layer)
    im.paste(white, (0, 0), Image.composite(layer.split()[3], Image.new("L", im.size, 0), inside))
    # Erase a little paper gap where the line crosses the text so letters stay readable.
    return im.resize((W // S, H // S), Image.LANCZOS)


def mark(size, bg=BLUE, line=(255, 255, 255)):
    """Square icon: the refreshed spike in a blue rounded square (option B icon)."""
    n = size * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.22), fill=bg)
    pts, _ = wave_pts(n / 2, n * 0.22, n * 0.78, n * 0.36)
    d.line(pts, fill=line, width=int(n * 0.075), joint="curve")
    for p in (pts[0], pts[-1]):
        r = n * 0.0375
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=line)
    return im.resize((size, size), Image.LANCZOS)


def avatar_from(img, bg=(255, 255, 255), fill=0.72):
    av = Image.new("RGB", (800, 800), bg)
    k = min(800 * fill / img.width, 800 * fill / img.height)
    im = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
    av.paste(im, ((800 - im.width) // 2, (800 - im.height) // 2), im)
    return av


def circle_preview(av, size=260):
    m = Image.new("L", av.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, av.width - 1, av.height - 1], fill=255)
    out = Image.new("RGB", av.size, (232, 229, 222))
    out.paste(av, (0, 0), m)
    return out.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    opts = {}
    # A: faithful refresh of the 2020 lockup, caps.
    a = wordmark("Spike", "Wave", 120, True, 600)
    opts["a"] = (a, None, "A  Faithful refresh: same idea, cleaner type and wave, deeper blue")
    # B: blue spike icon + Source Serif name (matches the website type).
    m = mark(200)
    f = serif(120 * S)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = int(tmp.textlength("Spikewave", font=f))
    b = Image.new("RGBA", (200 * S + 40 * S + tw, 200 * S), (0, 0, 0, 0))
    b.paste(mark(200 * S), (0, 0))
    ImageDraw.Draw(b).text((240 * S, 200 * S // 2), "Spikewave", font=f, fill=INK, anchor="lm")
    b = b.resize((b.width // S, b.height // S), Image.LANCZOS)
    mav = Image.new("RGB", (800, 800), BLUE)
    big = mark(800)
    mav.paste(big, (0, 0), big)
    opts["b"] = (b, mav, "B  Icon + name: the spike becomes a blue app-style icon; name in the website's serif")
    # C: lowercase lockup.
    c = wordmark("spike", "wave", 120, False, 700)
    opts["c"] = (c, None, "C  Lowercase: friendlier, same split box and spike")

    opts = {k: (wm, av if av is not None else mav, lab) for k, (wm, av, lab) in opts.items()}
    for k, (wm, av, _) in opts.items():
        bg = Image.new("RGB", (wm.width + 120, wm.height + 120), PAPER)
        bg.paste(wm, (60, 60), wm)
        bg.save(os.path.join(OUT, f"option-{k}-wordmark.png"), optimize=True)
        av.save(os.path.join(OUT, f"option-{k}-avatar.png"), optimize=True)

    # Board: each row = wordmark on paper, wordmark on ink-free white, circle avatar.
    rows = len(opts)
    W, RH = 1600, 380
    board = Image.new("RGB", (W, 120 + rows * RH), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 40), "Spikewave logo refresh: options (based on the 2020 YouTube logo)", font=inter(34, 600), fill=INK)
    for i, (k, (wm, av, label)) in enumerate(opts.items()):
        y = 120 + i * RH
        d.line([(60, y), (W - 60, y)], fill=(207, 201, 188), width=2)
        d.text((60, y + 20), label, font=inter(26, 500), fill=INK)
        k2 = min(900 / wm.width, 200 / wm.height)
        w2 = wm.resize((int(wm.width * k2), int(wm.height * k2)), Image.LANCZOS)
        board.paste(w2, (60, y + 80 + (200 - w2.height) // 2), w2)
        cp = circle_preview(av, 240)
        board.paste(cp, (W - 60 - 240, y + 70))
        small = circle_preview(av, 64)
        board.paste(small, (W - 60 - 240 - 100, y + 70 + 88))
    board.save(os.path.join(OUT, "options-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
