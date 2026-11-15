"""Profile picture and banners for the Spikewave social pages, in the website's paper-and-ink style.

    python tooling/profile_images.py

Writes brand/profiles/: avatar-800.png (Facebook/YouTube/Instagram picture),
youtube-banner-2560x1440.png (text inside YouTube's 1546x423 safe area) and
facebook-cover-1640x624.png (text inside the centre 1100 px that phones keep).
Reuses the logo, fonts and app list from company-website/scripts/make_share_images.py,
so rerun after an app icon changes.
"""
import os
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "company-website")
sys.path.insert(0, os.path.join(SITE, "scripts"))
import make_share_images as s  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "brand", "profiles")


def apps():
    d = os.path.join(SITE, "src", "content", "apps")
    rows = []
    for fn in sorted(os.listdir(d)):
        a = s.frontmatter(os.path.join(d, fn))
        if a["draft"] or not a["icon"]:
            continue
        order = int(re.search(r"^order:\s*(\d+)", open(os.path.join(d, fn), encoding="utf-8").read(), re.M)[1])
        rows.append((order, a))
    return [a for _, a in sorted(rows, key=lambda r: r[0])]


def icon(a, size):
    im = Image.open(os.path.join(SITE, "public", a["icon"].lstrip("/"))).convert("RGBA")
    im = im.resize((size, size), Image.LANCZOS)
    return s.rounded(im, int(size * 0.23))


def banner(w, h, box_w, box_h, scale):
    """Logo, name, line and app icons laid out inside a centred box_w x box_h safe area."""
    im = Image.new("RGB", (w, h), s.PAPER)
    d = ImageDraw.Draw(im)
    x0, y0 = (w - box_w) // 2, (h - box_h) // 2
    lg_size = int(96 * scale)
    lg = s.logo(lg_size)
    name_f, line_f = s.DISPLAY(int(84 * scale)), s.DISPLAY(int(52 * scale))
    line = "Mobile apps for Android and iPhone."
    ic = int(104 * scale)
    gap = int(22 * scale)
    block_h = lg_size + int(34 * scale) + int(64 * scale) + int(40 * scale) + ic
    y = y0 + (box_h - block_h) // 2
    text_w = lg_size + int(26 * scale) + d.textlength("Spikewave", font=name_f)
    widest = max(text_w, d.textlength(line, font=line_f), len(apps()) * (ic + gap) - gap)
    x = x0 + (box_w - int(widest)) // 2
    im.paste(lg, (x, y), lg)
    d.text((x + lg_size + int(26 * scale), y + int(2 * scale)), "Spikewave", font=name_f, fill=s.INK)
    y += lg_size + int(34 * scale)
    d.text((x, y), line, font=line_f, fill=s.INK)
    y += int(64 * scale) + int(40 * scale)
    cx = x
    for a in apps():
        i = icon(a, ic)
        im.paste(i, (cx, y), i)
        cx += ic + gap
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    av = Image.new("RGB", (800, 800), s.INK)
    lg = s.logo(620)  # smaller than the square so a circular crop keeps the line ends
    av.paste(lg, (90, 90), lg)
    av.save(os.path.join(OUT, "avatar-800.png"), optimize=True)
    banner(2560, 1440, 1546, 423, 0.95).save(os.path.join(OUT, "youtube-banner-2560x1440.png"), optimize=True)
    banner(1640, 624, 1100, 560, 1.15).save(os.path.join(OUT, "facebook-cover-1640x624.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    sys.exit(main())
