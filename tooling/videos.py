"""YouTube videos from cleared screen recordings (owner, 7 Nov 2026: "cut a bigger batch" + "explainer videos").

  short(spec)      9:16 Short: kicker + two captions over a real phone playing one clip, glass-icon end card.
  explainer(spec)  16:9 explainer: icon title card, numbered chapters (text left, phone right), end card,
                   plus a 1280x720 thumbnail.

Frames are piped straight to ffmpeg (no PNGs). Music is the YouTube Audio Library bed (YouTube-only licence).
Run: python tooling/videos.py <specs.json> <out dir>
"""
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import motion as mo  # noqa: E402
import styles as st  # noqa: E402

FF = mo.FF
FPS = 30
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MUSIC = os.path.join(ROOT, "clips-outbox", "music", "Back To The Start - Patrick Jordan Patrikios.mp3")
INK, SUB = mo.INK, mo.SUB
SRC_W, SRC_H = 1080, 2340


def clip_frames(path, start, dur):
    """Yield the clip's frames (RGB, source size) at FPS."""
    p = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", "-ss", str(start), "-t", str(dur), "-i", path,
                          "-vf", f"fps={FPS},scale={SRC_W}:{SRC_H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    n = SRC_W * SRC_H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield Image.frombuffer("RGB", (SRC_W, SRC_H), b)
    p.wait()


class Phone:
    """Device frame with a transparent screen, so each clip frame drops in behind the bezel."""

    def __init__(self, scr_h):
        L, sx, sy = st.device(Image.new("RGB", (SRC_W, SRC_H)), scr_h)
        self.scr_w, self.scr_h, self.sx, self.sy = int(SRC_W * scr_h / SRC_H), scr_h, sx, sy
        r = 58 - 14
        hole = Image.new("L", L.size, 0)
        ImageDraw.Draw(hole).rounded_rectangle([sx, sy, sx + self.scr_w, sy + scr_h], radius=r, fill=255)
        al = L.split()[3].copy()
        al.paste(0, mask=hole)
        self.bezel = L.copy()
        self.bezel.putalpha(al)
        self.mask = Image.new("L", (self.scr_w, scr_h), 0)
        ImageDraw.Draw(self.mask).rounded_rectangle([0, 0, self.scr_w - 1, scr_h - 1], radius=r, fill=255)
        self.size = L.size
        self.shadow_alpha = L.split()[3]

    def shadow_onto(self, bg, x, y):
        s = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        m = Image.new("L", bg.size, 0)
        m.paste(self.shadow_alpha.point(lambda v: int(v * 0.55)), (x, y + 36))
        s.putalpha(m.filter(ImageFilter.GaussianBlur(46)))
        bg.alpha_composite(s)

    def draw(self, c, frame, x, y):
        s = frame.resize((self.scr_w, self.scr_h), Image.BILINEAR).convert("RGBA")
        s.putalpha(self.mask)
        c.alpha_composite(s, (x + self.sx, y + self.sy))
        c.alpha_composite(self.bezel, (x, y))


class Writer:
    def __init__(self, out, w, h):
        self.out_silent = out[:-4] + "-silent.mp4"
        self.out, self.n, self.w, self.h = out, 0, w, h
        self.p = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                                   "-crf", "18", "-pix_fmt", "yuv420p", self.out_silent], stdin=subprocess.PIPE)

    def add(self, img, times=1):
        b = img.convert("RGB").tobytes()
        for _ in range(times):
            self.p.stdin.write(b)
            self.n += 1

    def close(self, music_start=0.0):
        self.p.stdin.close()
        self.p.wait()
        dur = self.n / FPS
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", self.out_silent, "-ss", str(music_start),
                        "-i", MUSIC, "-filter_complex",
                        f"[1:a]atrim=0:{dur},asetpts=N/SR/TB,volume=0.7,afade=t=in:st=0:d=0.6,afade=t=out:st={max(dur - 2.5, 0)}:d=2.5[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                        "-movflags", "+faststart", self.out], check=True)
        os.remove(self.out_silent)
        return dur


def fade_in_layer(c, layer, a):
    if a <= 0:
        return
    if a < 1:
        layer = layer.copy()
        layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
    c.alpha_composite(layer)


def text_layer(size, draw_fn):
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    return lay


def end_card(app, slug, size, line, store, layout="v"):
    """Static end card: glass icon tile, app name, one line, store pill."""
    W, H = size
    c = st.grad(size, tuple(int(v * 0.5) for v in app["accent2"]), app["dark"]).convert("RGBA")
    st.glow(c, (int(W * 0.5), int(H * 0.3)), int(max(W, H) * 0.45), (255, 255, 255), 14)
    tile = mo.Tile(slug, 380 if layout == "v" else 300)
    cy = H * 0.40
    mo.place_tile(c, mo.turn(tile.render(None), 0.03), W / 2, cy, -6, app["accent"], 38)
    d = ImageDraw.Draw(c)
    y = cy + (300 if layout == "v" else 240)
    d.text((W / 2, y), app["name"], font=st.font("bold", 72 if layout == "v" else 64), fill=INK, anchor="mm")
    d.text((W / 2, y + 80), line, font=st.font("regular", 38 if layout == "v" else 34), fill=SUB, anchor="mm")
    mo.store_pill(c, y + 140, store, app, 1.0, cx=W / 2)
    d.text((W / 2, H - (110 if layout == "v" else 70)), "from Spikewave", font=st.font("regular", 32), fill=SUB, anchor="mm")
    return mo.dither(c.convert("RGB")).convert("RGBA")


def short(spec, out):
    """spec: app, clip, start, dur, kicker, cap1, cap2, cap2_at, end_line, store."""
    slug, app = spec["app"], st.APPS[spec["app"]]
    W, H = 1080, 1920
    bg = mo.background(app, 1.0)
    phone = Phone(1250)
    px, py = (W - phone.size[0]) // 2, 560
    phone.shadow_onto(bg, px, py)
    bg = mo.dither(bg.convert("RGB")).convert("RGBA")
    f_k, f_h = st.font("cond", 36), st.font("bold", 66)

    def cap(text):
        return text_layer((W, H), lambda d: (st.caps(d, (80, 150), spec["kicker"], f_k, app["accent"]),
                                             st.text_block(d, (80, 205), text, f_h, INK, W - 160, lh=1.1)))
    c1, c2 = cap(spec["cap1"]), cap(spec["cap2"])
    wr = Writer(out, W, H)
    t2 = spec.get("cap2_at", spec["dur"] * 0.45)
    for i, fr in enumerate(clip_frames(os.path.join(ROOT, spec["clip"]), spec.get("start", 0), spec["dur"])):
        t = i / FPS
        c = bg.copy()
        phone.draw(c, fr, px, py)
        if t < t2:
            fade_in_layer(c, c1, min(mo.ease(t / 0.5), mo.ease((t2 - t) / 0.3)))
        else:
            fade_in_layer(c, c2, mo.ease((t - t2) / 0.4))
        k = mo.ease(t / 0.3)
        wr.add(Image.blend(Image.new("RGBA", c.size, (0, 0, 0, 255)), c, k) if k < 1 else c)
    ec = end_card(app, slug, (W, H), spec["end_line"], spec["store"])
    for i in range(int(2.6 * FPS)):
        a = mo.ease(i / 10)
        k = min(1.0, mo.ease((2.6 * FPS - i) / 15))
        img = Image.blend(Image.new("RGBA", ec.size, (0, 0, 0, 255)), ec, a * k)
        wr.add(img)
    return wr.close(spec.get("music_start", 0))


def explainer(spec, out):
    """spec: app, title, line, chapters [{clip, start, dur, head, body}], end_line, store, thumb_text."""
    slug, app = spec["app"], st.APPS[spec["app"]]
    W, H = 1920, 1080
    base = st.grad((W, H), tuple(int(v * 0.5) for v in app["accent2"]), app["dark"]).convert("RGBA")
    st.glow(base, (int(W * 0.72), int(H * 0.45)), 700, app["accent"], 30)
    st.glow(base, (int(W * 0.2), int(H * 0.1)), 800, (255, 255, 255), 10)
    phone = Phone(900)
    px, py = int(W * 0.72 - phone.size[0] / 2), (H - phone.size[1]) // 2
    stage = base.copy()
    phone.shadow_onto(stage, px, py)
    stage = mo.dither(stage.convert("RGB")).convert("RGBA")
    wr = Writer(out, W, H)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    # title card (3.5 s): icon tile + name + what it does
    tile = mo.Tile(slug, 300)
    n = int(3.5 * FPS)
    for i in range(n):
        t = i / FPS
        c = mo.dither(base.convert("RGB")).convert("RGBA")
        mo.place_tile(c, mo.turn(tile.render(mo.sheen_at(t, 0.8, 9, 1.3)), 0.04 * math.sin(t * 0.8)), W / 2, 400 + 30 * (1 - mo.ease(t / 0.8)),
                      -6, app["accent"], int(40 * mo.ease(t / 0.8)))
        mo.fade_text(c, (W / 2, 690), spec["title"], st.font("bold", 76), INK, mo.ease((t - 0.3) / 0.7), anchor="mm")
        mo.fade_text(c, (W / 2, 780), spec["line"], st.font("regular", 40), SUB, mo.ease((t - 0.6) / 0.7), anchor="mm")
        k = min(mo.ease(t / 0.4), mo.ease((3.5 - t) / 0.4))
        wr.add(Image.blend(black, c, k))

    # chapters
    total = len(spec["chapters"])
    for ci, ch in enumerate(spec["chapters"]):
        f_num, f_h, f_b = st.font("cond", 40), st.font("bold", 64), st.font("regular", 38)

        def draw_text(d, ch=ch, ci=ci):
            st.caps(d, (130, 330), f"{ci + 1:02d} / {total:02d}", f_num, app["accent"])
            y = st.text_block(d, (130, 392), ch["head"], f_h, INK, 820, lh=1.1)
            st.text_block(d, (130, y + 28), ch["body"], f_b, SUB, 780, lh=1.35)
        txt = text_layer((W, H), draw_text)
        # progress dots
        dots = text_layer((W, H), lambda d, ci=ci: [d.ellipse([130 + j * 28, 880, 142 + j * 28, 892],
                                                              fill=(app["accent"] + (255,)) if j == ci else (255, 255, 255, 70))
                                                     for j in range(total)])
        frames = list(clip_frames(os.path.join(ROOT, ch["clip"]), ch.get("start", 0), ch["dur"]))
        hold = int(ch.get("hold", 0.8) * FPS)  # hold the last frame so the text can be read
        frames += [frames[-1]] * hold
        m = len(frames)
        for i, fr in enumerate(frames):
            t = i / FPS
            c = stage.copy()
            phone.draw(c, fr, px, py)
            fade_in_layer(c, txt, mo.ease((t - 0.15) / 0.6))
            c.alpha_composite(dots)
            k = min(mo.ease(t / 0.35), mo.ease((m - i) / 10))
            wr.add(Image.blend(black, c, k))

    ec = end_card(app, slug, (W, H), spec["end_line"], spec["store"], layout="h")
    n = int(4.0 * FPS)
    for i in range(n):
        k = min(mo.ease(i / 12), mo.ease((n - i) / 20))
        wr.add(Image.blend(black, ec, k))
    dur = wr.close(spec.get("music_start", 0))

    # thumbnail 1280x720: big text left, icon tile right
    th = st.grad((1280, 720), tuple(int(v * 0.55) for v in app["accent2"]), app["dark"]).convert("RGBA")
    st.glow(th, (930, 360), 520, app["accent"], 44)
    tt = mo.Tile(slug, 380)
    mo.place_tile(th, mo.turn(tt.render(0.35), 0.06), 950, 370, -9, None, 0)
    d = ImageDraw.Draw(th)
    st.caps(d, (70, 150), app["name"], st.font("cond", 40), app["accent"])
    st.text_block(d, (70, 210), spec["thumb_text"], st.font("black", 92), INK, 640, lh=1.05)
    mo.dither(th.convert("RGB").resize((1280, 720))).save(out[:-4] + "-thumb.jpg", quality=92)
    return dur


if __name__ == "__main__":
    specs = json.load(open(sys.argv[1], encoding="utf-8"))
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    only = sys.argv[3:] or None
    for s in specs:
        if only and s["name"] not in only:
            continue
        fn = explainer if s["kind"] == "explainer" else short
        d = fn(s, os.path.join(outdir, s["name"] + ".mp4"))
        print(s["name"], f"{d:.1f}s", flush=True)
