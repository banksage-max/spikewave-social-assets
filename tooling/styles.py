"""Spikewave post styles: eight distinct layouts so the feed doesn't repeat one template.

Usage:  python tooling/styles.py specs.json
Each spec: {"style": "<name>", "app": "<slug>", "out": "path.png", ...style fields}
Styles: bold_block, editorial_light, detail_callouts, big_number, problem_type,
        split_compare, minimal_phone, three_steps. All 1080x1350 (4:5).
Real screens only: every screen comes from source-screenshots/ or a clip frame.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, os, sys
import numpy as np

W, H = 1080, 1350
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fonts: the bundled open-licence fonts in tooling/fonts/ (OFL, see the OFL-*.txt files) come first, so
# renders look the same locally and on the Linux cloud runner. Entries are "file" or "file@VariationName".
_DIRS = [os.path.join(ROOT, "tooling", "fonts") + "/", "C:/Windows/Fonts/",
         "/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/truetype/freefont/"]
_ALIAS = {
    "black": ["ArchivoBlack-Regular.ttf", "seguibl.ttf", "DejaVuSans-Bold.ttf"],
    "bold": ["Inter-Variable.ttf@Bold", "segoeuib.ttf", "DejaVuSans-Bold.ttf"],
    "semi": ["Inter-Variable.ttf@SemiBold", "seguisb.ttf", "DejaVuSans-Bold.ttf"],
    "regular": ["Inter-Variable.ttf@Regular", "segoeui.ttf", "DejaVuSans.ttf"],
    "light": ["Inter-Variable.ttf@Light", "segoeuil.ttf", "DejaVuSans.ttf"],
    "serif": ["DMSerifDisplay-Regular.ttf", "GeorgiaPro-Bold.ttf", "DejaVuSerif-Bold.ttf"],
    "serif_reg": ["SourceSerif4-Variable.ttf@Regular", "georgia.ttf", "DejaVuSerif.ttf"],
    "cond": ["BarlowCondensed-SemiBold.ttf", "bahnschrift.ttf", "DejaVuSansCondensed-Bold.ttf"],
    "mono": ["consolab.ttf", "DejaVuSansMono-Bold.ttf"],
}


def font(kind, size):
    for cand in _ALIAS[kind]:
        name, _, var = cand.partition("@")
        for d in _DIRS:
            if os.path.exists(d + name):
                f = ImageFont.truetype(d + name, size)
                if var:
                    f.set_variation_by_name(var)
                return f
    return ImageFont.load_default()


# App palettes (content/app-visuals.md). accent2 = deeper shade, ink = text on accent.
APPS = {  # slug added below
    "leave_by": dict(name="Leave By", accent=(255, 122, 61), accent2=(240, 74, 18), dark=(17, 17, 19),
                     ink=(20, 12, 8), cta="Free on Google Play"),
    "which_box": dict(name="Which Box", accent=(134, 231, 212), accent2=(49, 108, 100), dark=(17, 20, 19),
                      ink=(8, 28, 25), cta="Coming 12 Jan 2027"),
    "knock": dict(name="Knock", accent=(96, 165, 250), accent2=(37, 99, 235), dark=(11, 15, 25),
                  ink=(5, 12, 30), cta="Live on Google Play"),
}
for _k, _v in APPS.items():
    _v["slug"] = _k
CREAM, INK, MUTED = (245, 239, 230), (22, 22, 24), (120, 116, 110)


def shot(path, crop=None):
    im = Image.open(os.path.join(ROOT, path)).convert("RGB")
    return im.crop(crop) if crop else im


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=r, fill=255)
    out = im.convert("RGBA"); out.putalpha(m); return out


def shadow(canvas, box, r, blur=36, alpha=150, off=(0, 24)):
    x0, y0, x1, y1 = box
    s = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]], radius=r,
                                        fill=(0, 0, 0, alpha))
    canvas.alpha_composite(s.filter(ImageFilter.GaussianBlur(blur)))


def device(im, h, bezel=14, r=58):
    """Phone body: metal rim, black bezel, side buttons, punch-hole camera, faint screen glare."""
    w = int(im.width * h / im.height)
    bw, bh, ox = w + 2 * bezel, h + 2 * bezel, 8
    L = Image.new("RGBA", (bw + 2 * ox, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    k = h / 1400
    for (y0, ln, side) in ((0.20, 0.10, 1), (0.17, 0.06, 0), (0.25, 0.10, 0)):
        x0 = ox + bw - 3 if side else ox - 5
        d.rounded_rectangle([x0, int(bh * y0), x0 + 8, int(bh * (y0 + ln))], radius=3, fill=(58, 62, 70, 255))
    d.rounded_rectangle([ox, 0, ox + bw - 1, bh - 1], radius=r, fill=(112, 118, 130, 255))
    d.rounded_rectangle([ox + 2, 2, ox + bw - 3, bh - 3], radius=r - 2, fill=(44, 47, 54, 255))
    d.rounded_rectangle([ox + 4, 4, ox + bw - 5, bh - 5], radius=r - 4, fill=(8, 8, 10, 255))
    scr = rounded(im.resize((w, h), Image.LANCZOS), max(r - bezel, 8))
    L.alpha_composite(scr, (ox + bezel, bezel))
    cx, cy, cr = ox + bezel + w // 2, bezel + int(26 * k), max(int(10 * k), 4)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(4, 4, 6, 255), outline=(30, 32, 38, 255))
    glare = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(glare)
    for i in range(0, w + h, 4):
        a = max(0, 16 - i * 16 // int((w + h) * 0.55))
        if a: gd.line([(i, 0), (0, i)], fill=a, width=4)
    gl = Image.new("RGBA", (w, h), (255, 255, 255, 0)); gl.putalpha(Image.composite(glare, Image.new("L", (w, h), 0), scr.split()[3]))
    L.alpha_composite(gl, (ox + bezel, bezel))
    return L, ox + bezel, bezel


def place(canvas, layer, x, y, tilt=0):
    """Composite a device layer with a soft ambient shadow and a tighter contact shadow."""
    if tilt:
        layer = layer.rotate(tilt, resample=Image.BICUBIC, expand=True)
    a = layer.split()[3]
    for blur, alpha, dy in ((60, 0.45, 50), (14, 0.35, 10)):
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        m = Image.new("L", canvas.size, 0); m.paste(a.point(lambda v: int(v * alpha)), (x, y + dy))
        sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)))
        canvas.alpha_composite(sh)
    canvas.alpha_composite(layer, (x, y))


def phone(canvas, im, x, y, h, bezel=14, r=58, bezel_col=None, shade=True, tilt=0):
    """Screen top-left at (x, y), screen height h, in a realistic device; returns the device box."""
    L, sx, sy = device(im, h, bezel, r)
    place(canvas, L, x - sx, y - sy, tilt)
    return (x - sx, y - sy, x - sx + L.width, y - sy + L.height)


def glow(c, xy, radius, colour, alpha=90):
    g = Image.new("RGBA", c.size, (0, 0, 0, 0))
    x, y = xy
    ImageDraw.Draw(g).ellipse([x - radius, y - radius, x + radius, y + radius], fill=tuple(colour) + (alpha,))
    c.alpha_composite(g.filter(ImageFilter.GaussianBlur(radius * 0.6)))


def caps(d, xy, text, f, fill, track=0.14):
    """Upper-case label with letter-spacing."""
    x, y = xy
    for ch in text.upper():
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + f.size * track


def wrap(d, text, f, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for wd in para.split():
            t = (cur + " " + wd).strip()
            if d.textlength(t, font=f) <= maxw:
                cur = t
            else:
                if cur: out.append(cur)
                cur = wd
        out.append(cur)
    return out


def text_block(d, xy, text, f, fill, maxw, lh=1.08, align="left"):
    x, y = xy
    for ln in wrap(d, text, f, maxw):
        tx = x if align == "left" else x + (maxw - d.textlength(ln, font=f)) / 2
        d.text((tx, y), ln, font=f, fill=fill)
        y += int(f.size * lh)
    return y


def grad(size, a, b, vertical=True):
    w, h = size
    g = Image.new("RGB", (1, h) if vertical else (w, 1))
    px = g.load(); n = (h if vertical else w) - 1
    for i in range(n + 1):
        t = i / n
        px[(0, i) if vertical else (i, 0)] = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
    return g.resize((w, h)).convert("RGBA")


def icon(slug, size):
    p = os.path.join(ROOT, "brand", "icons", slug + ".png")
    if not os.path.exists(p):
        return None
    return rounded(Image.open(p).convert("RGB").resize((size, size), Image.LANCZOS), int(size * 0.22))


def footer(c, app, colour, sub_colour, x=72, y=H - 112, cta=True):
    """App icon + name + CTA line, the sign-off on every post."""
    d = ImageDraw.Draw(c)
    ic = icon(app["slug"], 64)
    tx = x
    if ic:
        c.alpha_composite(ic, (x, y + 4)); tx = x + 84
    d.text((tx, y), app["name"], font=font("bold", 32), fill=colour)
    if cta:
        d.text((tx, y + 42), f"{app['cta']}  ·  spikewave.tech", font=font("regular", 25), fill=sub_colour)


# ---------------------------------------------------------------- styles

def bold_block(s, app):
    """Full app-colour field, huge dark headline, phone bleeding off the bottom."""
    c = grad((W, H), app["accent"], app["accent2"])
    d = ImageDraw.Draw(c)
    caps(d, (72, 70), app["name"], font("cond", 34), app["ink"])
    y = text_block(d, (72, 120), s["headline"], font("black", 104), app["ink"], W - 144, lh=1.08)
    y = text_block(d, (72, y + 34), s.get("sub", ""), font("semi", 36), app["ink"], 560, lh=1.3)
    glow(c, (W - 200, 300), 380, (255, 255, 255), 40)
    phone(c, shot(s["shot"]), s.get("phone_x", 600), max(y + 40, 500), s.get("phone_h", 1560), tilt=s.get("tilt", 7))
    footer(c, app, app["ink"], app["ink"], y=H - 110)
    return c


def editorial_light(s, app):
    """Cream paper, serif headline, small framed phone, magazine label."""
    c = Image.new("RGBA", (W, H), CREAM + (255,))
    d = ImageDraw.Draw(c)
    caps(d, (72, 72), s.get("kicker", "Feature"), font("cond", 30), app["accent2"])
    d.line([(72, 118), (W - 72, 118)], fill=(200, 192, 180), width=2)
    y = text_block(d, (72, 150), s["headline"], font("serif", 84), INK, W - 144, lh=1.1)
    text_block(d, (72, y + 14), s.get("sub", ""), font("serif_reg", 34), MUTED, W - 260, lh=1.35)
    phone(c, shot(s["shot"]), 330, max(y + 150, 640), 980, bezel_col=(30, 30, 34))
    c.alpha_composite(Image.new("RGBA", (W, 110), CREAM + (255,)), (0, H - 110))
    footer(c, app, INK, MUTED, y=H - 96)
    return c


def detail_callouts(s, app):
    """One UI card blown up full width, with labelled callouts for each row."""
    c = grad((W, H), (14, 15, 18), app["dark"])
    glow(c, (W - 120, 260), 420, app["accent"], 40)
    d = ImageDraw.Draw(c)
    y = text_block(d, (72, 80), s["headline"], font("bold", 66), (240, 240, 244), W - 144)
    crop = shot(s["shot"], tuple(s["crop"]))
    cw = W - 2 * 72 - 40
    ch = int(crop.height * cw / crop.width)
    top = max(y + 50, 300)
    shadow(c, (72, top, 72 + cw, top + ch), 34)
    c.alpha_composite(rounded(crop.resize((cw, ch), Image.LANCZOS), 34), (72, top))
    sc = cw / crop.width
    for i, (ry, label) in enumerate(s["callouts"]):
        cy = top + int(ry * sc)
        d.ellipse([W - 92, cy - 22, W - 48, cy + 22], fill=app["accent"])
        d.text((W - 70, cy), str(i + 1), font=font("bold", 26), fill=app["ink"], anchor="mm")
    ly = top + ch + 44
    for i, (_, label) in enumerate(s["callouts"]):
        col, row = i % 2, i // 2
        x = 72 + col * 520
        d.text((x, ly + row * 46), f"{i + 1}", font=font("bold", 30), fill=app["accent"])
        d.text((x + 40, ly + row * 46), label, font=font("regular", 30), fill=(200, 202, 210))
    footer(c, app, app["accent"], (130, 134, 146))
    return c


def big_number(s, app):
    """Giant number pulled from a real screen; the parts that add up to it as chips."""
    c = Image.new("RGBA", (W, H), app["dark"] + (255,))
    glow(c, (260, 330), 460, app["accent"], 46)
    d = ImageDraw.Draw(c)
    caps(d, (72, 80), s.get("kicker", ""), font("cond", 32), app["accent"])
    nf = font("black", s.get("number_size", 400))
    d.text((60, 120), s["number"], font=nf, fill=app["accent"])
    nw = d.textlength(s["number"], font=nf)
    d.text((80 + nw, 380), s["unit"], font=font("bold", 80), fill=(240, 240, 244))
    y = text_block(d, (72, 610), s["headline"], font("bold", 58), (240, 240, 244), W - 144)
    x, y = 72, y + 40
    for chip in s["chips"]:
        f = font("semi", 32)
        tw = d.textlength(chip, font=f)
        if x + tw + 56 > W - 72:
            x, y = 72, y + 84
        d.rounded_rectangle([x, y, x + tw + 48, y + 66], radius=33, outline=app["accent"], width=3)
        d.text((x + 24, y + 13), chip, font=f, fill=(230, 230, 236))
        x += tw + 70
    text_block(d, (72, y + 120), s.get("sub", ""), font("regular", 32), (150, 154, 166), W - 144, lh=1.35)
    footer(c, app, app["accent"], (130, 134, 146))
    return c


def problem_type(s, app):
    """Text only: a relatable problem in big type, no screen. Pure hook."""
    c = grad((W, H), (12, 14, 22), (26, 30, 44))
    glow(c, (W - 160, H - 380), 480, app["accent"], 34)
    d = ImageDraw.Draw(c)
    d.text((64, 40), "\u201c", font=font("serif", 300), fill=app["accent"])
    y = text_block(d, (72, 330), s["headline"], font("serif", 92), (244, 241, 236), W - 144, lh=1.12)
    d.line([(72, y + 40), (232, y + 40)], fill=app["accent"], width=6)
    text_block(d, (72, y + 80), s.get("sub", ""), font("regular", 38), (170, 174, 188), W - 200, lh=1.35)
    footer(c, app, app["accent"], (130, 134, 146))
    return c


def split_compare(s, app):
    """Top: what the calendar says. Bottom: what the app says. Real numbers from the screen."""
    c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    top_h = 560
    c.alpha_composite(Image.new("RGBA", (W, top_h), (232, 230, 226, 255)))
    c.alpha_composite(grad((W, H - top_h), app["accent"], app["accent2"]), (0, top_h))
    d = ImageDraw.Draw(c)
    caps(d, (72, 70), s["a_label"], font("cond", 32), (110, 106, 100))
    d.text((72, 120), s["a_value"], font=font("black", 190), fill=(150, 146, 140))
    text_block(d, (72, 350), s["a_note"], font("regular", 36), (110, 106, 100), W - 144)
    caps(d, (72, top_h + 60), s["b_label"], font("cond", 32), app["ink"])
    d.text((72, top_h + 110), s["b_value"], font=font("black", 190), fill=app["ink"])
    text_block(d, (72, top_h + 340), s["b_note"], font("semi", 40), app["ink"], W - 144)
    footer(c, app, app["ink"], app["ink"], y=H - 110)
    return c


def minimal_phone(s, app):
    """White, lots of space, centred phone, one line."""
    c = Image.new("RGBA", (W, H), (250, 250, 250, 255))
    d = ImageDraw.Draw(c)
    h = 930
    w = int(1080 * h / 2340)
    phone(c, shot(s["shot"]), (W - w) // 2, 90, h, bezel_col=(28, 28, 32))
    text_block(d, (72, 1100), s["headline"], font("semi", 52), INK, W - 144, align="center")
    d.text((W // 2, H - 72), f"{app['name']}  ·  {app['cta']}", font=font("regular", 28), fill=MUTED, anchor="mm")
    return c


def three_steps(s, app):
    """Three phones in a row, numbered: a how-it-works cover."""
    c = grad((W, H), app["dark"], (28, 30, 36))
    glow(c, (W // 2, 720), 520, app["accent"], 34)
    d = ImageDraw.Draw(c)
    y = text_block(d, (72, 80), s["headline"], font("bold", 70), (240, 240, 244), W - 144)
    h = 640; w = int(1080 * h / 2340); gap = (W - 3 * w) // 4
    top = max(y + 70, 330)
    for i, (path, label) in enumerate(s["steps"]):
        x = gap + i * (w + gap)
        phone(c, shot(path), x, top, h, bezel=8, r=32)
        d.ellipse([x + w // 2 - 30, top + h + 40, x + w // 2 + 30, top + h + 100], fill=app["accent"])
        d.text((x + w // 2, top + h + 70), str(i + 1), font=font("bold", 34), fill=app["ink"], anchor="mm")
        text_block(d, (x - 20, top + h + 120), label, font("semi", 30), (220, 222, 230), w + 40, align="center")
    footer(c, app, app["accent"], (130, 134, 146))
    return c


def _paid_frame(size, s, app, with_text=True):
    """Paid-ad frame (research, 25 Oct 2026): brand colour, one real screen, a 4-6 word headline (<20% of the
    area), small icon sign-off. with_text=False gives the text- and logo-free version Google asks for."""
    Wd, Hd = size
    k = min(Wd, Hd) / 1080
    c = grad((Wd, Hd), app["accent"], app["accent2"])
    glow(c, (int(Wd * 0.85), int(Hd * 0.15)), int(420 * k), (255, 255, 255), 38)
    d = ImageDraw.Draw(c)
    landscape = Wd > Hd * 1.3
    sc = shot(s["shot"])
    if landscape:
        if with_text:
            hf = font("black", int(64 * Hd / 628))
            lines = wrap(d, s["headline"], hf, int(Wd * 0.48))
            y = (Hd - len(lines) * int(hf.size * 1.08)) // 2 - int(30 * Hd / 628)
            text_block(d, (int(48 * Hd / 628), y), s["headline"], hf, app["ink"], int(Wd * 0.48))
            footer_small(c, app, app["ink"], int(48 * Hd / 628), Hd - int(70 * Hd / 628), int(Hd / 628 * 34))
        ph = int(Hd * 1.15)
        pw = int(1080 * ph / 2340)
        x = int(Wd * 0.62) if with_text else (Wd - pw) // 2
        phone(c, sc, x, int(Hd * 0.12), ph, bezel=int(10 * Hd / 628), r=int(40 * Hd / 628), tilt=6 if with_text else 0)
        return c
    top = int(80 * k)
    if with_text:
        hf = font("black", int(92 * k))
        top = text_block(d, (int(72 * k), int(72 * k)), s["headline"], hf, app["ink"], Wd - int(144 * k), lh=1.06)
        top += int(48 * k)
    ph = int(Hd * (1.05 if Hd > Wd else 1.0))
    pw = int(1080 * ph / 2340)
    phone(c, sc, (Wd - pw) // 2, max(top, int(Hd * 0.08)), ph, bezel=int(14 * k), r=int(58 * k))
    if with_text:
        footer_small(c, app, app["ink"], int(72 * k), Hd - int(96 * k), int(40 * k), plate=True)
    return c


def footer_small(c, app, colour, x, y, size, plate=False):
    """Icon + app name only (no URL), for paid frames."""
    d = ImageDraw.Draw(c)
    f = font("bold", int(size * 0.8))
    tw = d.textlength(app["name"], font=f)
    if plate:
        d.rounded_rectangle([x - size // 4, y - size // 4, x + size + 16 + tw + size // 3, y + size + size // 4],
                            radius=size // 2, fill=(255, 255, 255, 235))
        colour = INK
    ic = icon(app["slug"], size)
    if ic:
        c.alpha_composite(ic, (x, y))
    d.text((x + size + 14, y + size // 2), app["name"], font=f, fill=colour, anchor="lm")


PAID_SIZES = {"1x1": (1080, 1080), "4x5": (1080, 1350), "9x16": (1080, 1920), "191x1": (1200, 628)}


def paid_set(s, app):
    """All paid sizes, with and without text: returns [(suffix, image)]."""
    out = [(k, _paid_frame(v, s, app)) for k, v in PAID_SIZES.items()]
    out += [(k + "-notext", _paid_frame(v, s, app, with_text=False)) for k, v in PAID_SIZES.items() if k != "9x16"]
    return out


def ui_float(s, app):
    """One or two real UI cards floating without a phone, on a soft app-tinted ground."""
    base = tuple(int(CREAM[i] * 0.9 + app["accent"][i] * 0.1) for i in range(3))
    c = Image.new("RGBA", (W, H), base + (255,))
    glow(c, (W - 160, 260), 360, app["accent"], 50)
    d = ImageDraw.Draw(c)
    caps(d, (72, 72), s.get("kicker", app["name"]), font("cond", 30), app["accent2"])
    y = text_block(d, (72, 120), s["headline"], font("serif", 78), INK, W - 144, lh=1.1)
    cards = [(s["crop"], -3, 0)] + ([(s["crop2"], 4, 1)] if s.get("crop2") else [])
    top = y + 60
    for crop, tilt, i in cards:
        im = shot(s["shot2"] if i and s.get("shot2") else s["shot"], tuple(crop))
        cw = 860 if i == 0 else 700
        ch = int(im.height * cw / im.width)
        L = rounded(im.resize((cw, ch), Image.LANCZOS), 34)
        x = (W - cw) // 2 - 40 + i * 120
        place(c, L, x, top + i * (ch // 2 + 60), tilt)
    footer(c, app, INK, MUTED)
    return c


def carousel(s, app):
    """Swipeable panorama: slide 1 is the hook, then one real screen per step; a line runs across slides."""
    steps = s["steps"]
    n = 1 + len(steps)
    P = grad((W * n, H), app["dark"], (30, 32, 38))
    for i in range(n):
        glow(P, (W * i + W // 2, 700), 460, app["accent"], 30)
    d = ImageDraw.Draw(P)
    caps(d, (72, 96), app["name"], font("cond", 34), app["accent"])
    text_block(d, (72, 150), s["headline"], font("black", 96), (244, 244, 248), W - 160, lh=1.06)
    text_block(d, (72, H - 260), s.get("sub", "Swipe to see how →"), font("semi", 36), (190, 194, 206), W - 144)
    ly = H - 190
    d.line([(W - 200, ly), (W * n - 520, ly)], fill=app["accent"], width=4)
    h = 760; w = int(1080 * h / 2340)
    for i, (path, label) in enumerate(steps):
        cx = W * (i + 1) + W // 2
        x = cx - w // 2 - (180 if i == 0 else 0)
        phone(P, shot(path), x, 270, h, tilt=-6 if i == 0 else 0)
        d.ellipse([cx - 28, ly - 28, cx + 28, ly + 28], fill=app["accent"])
        d.text((cx, ly), str(i + 1), font=font("bold", 30), fill=app["ink"], anchor="mm")
        text_block(d, (W * (i + 1) + 72, 110), label, font("bold", 60), (244, 244, 248), W - 144, align="center")
    slides = [P.crop((W * i, 0, W * (i + 1), H)) for i in range(n)]
    footer(slides[-1], app, app["accent"], (150, 154, 166), x=W - 560, y=H - 100)
    return [(f"{i + 1}", sl) for i, sl in enumerate(slides)]


STYLES = {f.__name__: f for f in (bold_block, editorial_light, detail_callouts, big_number, problem_type,
                                   split_compare, minimal_phone, three_steps, paid_set, ui_float, carousel)}


def grain(img, amount=5):
    """Fine film grain (about +/-5 levels): lifts flat digital fills."""
    n = np.asarray(Image.effect_noise(img.size, 40), dtype=np.int16) - 128
    out = np.asarray(img, dtype=np.int16) + (n * amount // 40)[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def render(spec):
    """Render one spec. Multi-image styles (paid_set, carousel) write <out stem>-<suffix>.png for each image."""
    app = APPS[spec["app"]]
    res = STYLES[spec["style"]](spec, app)
    os.makedirs(os.path.dirname(os.path.abspath(spec["out"])), exist_ok=True)
    if not isinstance(res, list):
        grain(res.convert("RGB")).save(spec["out"], quality=95)
        return spec["out"]
    stem, ext = os.path.splitext(spec["out"])
    outs = []
    for suffix, img in res:
        p = f"{stem}-{suffix}{ext}"
        grain(img.convert("RGB")).save(p, quality=95)
        outs.append(p)
    return ", ".join(outs)


if __name__ == "__main__":
    for sp in json.load(open(sys.argv[1], encoding="utf-8")):
        print("wrote", render(sp))
