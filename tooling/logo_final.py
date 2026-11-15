"""Final Spikewave logo set (owner, 15 Nov 2026): P1b with a slightly thicker line, and the serif S icon
with a refined layout.

    python tooling/logo_final.py

Writes brand/logo/:
  spikewave-logo-{navy,white}.png        name + line, transparent, 3000 px wide (navy for light grounds, white for dark)
  spikewave-logo-navy-mono.png            one-colour version for print
  spikewave-icon-{1024,512,192,180,64,32,16}.png   S on the line, navy square (crop to a circle on social)
  youtube-banner-2560x1440.png, facebook-cover-1640x624.png
  mockups.png (profile mock-ups for the owner's check) and final-board.png
"""
import os

from PIL import Image, ImageDraw

import logo_p1 as L1
import logo_premium as P

OUT = os.path.join(os.path.dirname(P.HERE), "brand", "logo")
NAVY, BLUE, PAPER, MUTED, LINE, WHITE = P.NAVY, P.BLUE, P.PAPER, P.MUTED, P.LINE, P.WHITE
BLUE_ON_NAVY = L1.BLUE_ON_NAVY
S = P.S
WEIGHT = 0.058   # line thickness as a share of cap height (round 6 was 0.045)


def lockup(dark=False, mono=False, scale=1.0):
    return L1.lockup(order="spike-wave", weight=WEIGHT, colour="ink" if mono else "blue", dark=dark)


def icon(size=1024, bg=NAVY):
    """The S sits optically centred a little above the middle; the line runs under it with the spike
    under the S's spine. Everything stays inside the circle a round crop keeps (radius 0.5)."""
    n = size * S
    im = Image.new("RGB", (n, n), bg)
    d = ImageDraw.Draw(im)
    f = P.serif(int(n * 0.50), w=600, opsz=60)
    b = f.getbbox("S")
    sw, sh = b[2] - b[0], b[3] - b[1]
    line_y = n * 0.705
    gap = n * 0.115
    sy = line_y - gap - sh                        # S bottom sits a clear gap above the line
    group_top, group_bot = sy, line_y + n * 0.05
    shift = (n - (group_top + group_bot)) / 2      # centre the S + line group vertically
    sy += shift
    line_y += shift
    d.text(((n - sw) / 2 - b[0], sy - b[1]), "S", font=f, fill=WHITE)
    x0, x1 = n * 0.20, n * 0.80
    spike_x = n / 2 + sw / 2 + n * 0.035          # the spike sits just after the S (owner, 15 Nov)
    pts = L1.line_pts(x0, x1, line_y, n * 0.028, n * 0.115, order="wave-spike", spike_at=(spike_x - x0) / (x1 - x0))
    P.stroke(d, pts, n * 0.032, BLUE_ON_NAVY)
    return im.resize((size, size), Image.LANCZOS)


def banner(w, h, box_w, box_h, k):
    im = Image.new("RGB", (w, h), PAPER)
    lg = lockup()
    t = L1.fit(lg, box_w * 0.62 * k, box_h * 0.62 * k)
    im.paste(t, ((w - t.width) // 2, (h - t.height) // 2 - int(box_h * 0.06)), t)
    d = ImageDraw.Draw(im)
    f = P.inter(int(box_h * 0.085 * k), 450)
    line = "Mobile apps for Android and iPhone"
    tw = d.textlength(line, font=f)
    d.text(((w - tw) / 2, (h + t.height) / 2 - int(box_h * 0.02)), line, font=f, fill=MUTED)
    return im


def circle(av, size, bg=PAPER):
    return L1.circle(av, size, bg)


def mockups(ic):
    """Rough mock-ups of the three profile headers (not the platforms' real UI)."""
    W, H = 1800, 620
    im = Image.new("RGB", (W, H), (238, 236, 231))
    d = ImageDraw.Draw(im)
    cols = [("Instagram", "spikewave.tech", "We make phone apps: Leave By, Stopby Reminders and Knock..."),
            ("Facebook", "Spikewave", "We make phone apps: Leave By, Stopby Reminders and Knock."),
            ("YouTube", "Spikewave", "@spikewave3665 · Short videos of the Spikewave apps")]
    cover = banner(1640, 624, 1100, 560, 1.0)
    for i, (plat, name, sub) in enumerate(cols):
        x = 40 + i * 590
        card = Image.new("RGB", (550, 540), WHITE)
        cd = ImageDraw.Draw(card)
        cd.text((20, 14), plat, font=P.inter(18, 600), fill=MUTED)
        if plat != "Instagram":
            c = cover.resize((550, int(550 * 624 / 1640)))
            card.paste(c, (0, 48))
            cy = 48 + c.height + 14
        else:
            cy = 70
        card.paste(circle(ic, 110, WHITE), (24, cy))
        cd.text((150, cy + 30), name, font=P.inter(28, 650), fill=NAVY)
        cd.text((24, cy + 125), sub, font=P.inter(17, 400), fill=MUTED)
        im.paste(card, (x, 40))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, kw in (("navy", {}), ("white", {"dark": True}), ("navy-mono", {"mono": True})):
        lg = lockup(**kw)
        big = lg.resize((3000, int(3000 * lg.height / lg.width)), Image.LANCZOS)
        big.save(os.path.join(OUT, f"spikewave-logo-{name}.png"), optimize=True)
    base = icon(1024)
    for s in (1024, 512, 192, 180, 64, 32, 16):
        (base if s == 1024 else base.resize((s, s), Image.LANCZOS)).save(os.path.join(OUT, f"spikewave-icon-{s}.png"), optimize=True)
    banner(2560, 1440, 1546, 423, 1.12).save(os.path.join(OUT, "youtube-banner-2560x1440.png"), optimize=True)
    banner(1640, 624, 1100, 560, 1.0).save(os.path.join(OUT, "facebook-cover-1640x624.png"), optimize=True)
    mk = mockups(base)
    mk.save(os.path.join(OUT, "mockups.png"), optimize=True)

    # Board: lockup on paper and navy, icon sizes, banners, mock-ups.
    W = 1900
    board = Image.new("RGB", (W, 1880), PAPER)
    d = ImageDraw.Draw(board)
    d.text((60, 40), "Spikewave logo: final set", font=P.inter(40, 600), fill=NAVY)
    d.text((60, 94), "P1b with a slightly thicker line, and the serif S icon with a refined layout.", font=P.inter(21, 400), fill=MUTED)
    lp, ld = lockup(), lockup(dark=True)
    board.paste(L1.fit(lp, 760, 220), (60, 160), L1.fit(lp, 760, 220))
    panel = Image.new("RGB", (900, 300), NAVY)
    t = L1.fit(ld, 700, 200)
    panel.paste(t, ((900 - t.width) // 2, (300 - t.height) // 2), t)
    board.paste(panel, (940, 130))
    y = 470
    d.text((60, y), "Icon", font=P.inter(24, 600), fill=NAVY)
    x = 60
    for s in (220, 120, 64, 40):
        board.paste(circle(base, s), (x, y + 50 + (220 - s) // 2))
        x += s + 40
    sq = base.resize((180, 180), Image.LANCZOS)
    m = Image.new("L", (180, 180), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, 179, 179], radius=40, fill=255)
    board.paste(sq, (x + 20, y + 70), m)
    board.paste(base.resize((32, 32), Image.LANCZOS), (x + 240, y + 144))
    board.paste(base.resize((16, 16), Image.LANCZOS), (x + 290, y + 152))
    d.text((x + 240, y + 190), "browser tab 32 / 16", font=P.inter(14, 400), fill=MUTED)
    y = 780
    d.text((60, y), "Banners", font=P.inter(24, 600), fill=NAVY)
    yt = Image.open(os.path.join(OUT, "youtube-banner-2560x1440.png")).resize((800, 450))
    fb = Image.open(os.path.join(OUT, "facebook-cover-1640x624.png")).resize((820, 312))
    board.paste(yt, (60, y + 44))
    board.paste(fb, (1000, y + 44))
    d.text((60, y + 500), "YouTube 2560x1440 (text inside the all-devices area)", font=P.inter(15, 400), fill=MUTED)
    d.text((1000, y + 362), "Facebook cover 1640x624", font=P.inter(15, 400), fill=MUTED)
    y = 1320
    d.text((60, y), "Profile mock-ups (rough, not the platforms' real layout)", font=P.inter(24, 600), fill=NAVY)
    board.paste(mk.resize((1780, int(1780 * mk.height / mk.width))), (60, y + 44))
    board.save(os.path.join(OUT, "final-board.png"), optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
