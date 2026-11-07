"""YouTube videos from cleared screen recordings (owner, 7 Nov 2026: "cut a bigger batch", "explainer videos",
then "vary the intros and polish for a professional clean look").

  short(spec)      9:16 Short. Opening (spec "intro"):
                     type  - full-screen hook on the app colour, wipes up to reveal the phone
                     zoom  - starts close on a focus point of the screen ("focus": [fx, fy]), pulls back
                     icon  - glass app icon resolves, then the phone rises in
                     stat  - one real number from the screen, huge ("stat"), crossfades to the phone
                     rise  - phone rises in while the caption builds word by word
                   End card (spec "end"): "icon" (glass tile) or "type" (app-colour block).
  explainer(spec)  16:9 explainer: title card (spec "title_style": icon | type | phone), numbered chapters
                   (text left, phone right, slow push-in), end card, plus a 1280x720 thumbnail.

Polish: screen frames are scaled by ffmpeg with Lanczos straight to the phone's screen size; the phone carries a
pre-blurred shadow and a slow push-in; captions fade and slide; every frame is dithered against banding.
Frames are piped to ffmpeg. Music: YouTube Audio Library bed (YouTube-only licence).
Run: python tooling/videos.py <specs.json> <out dir> [names...]
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
ease, ease_io = mo.ease, mo.ease_io


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- phone

class Phone:
    """Phone with a transparent screen and a pre-blurred shadow, composited as one padded layer that can be
    scaled and placed per frame. Screen frames arrive already sized (ffmpeg Lanczos)."""

    def __init__(self, scr_h):
        L, sx, sy = st.device(Image.new("RGB", (SRC_W, SRC_H)), scr_h)
        self.scr_w, self.scr_h = int(SRC_W * scr_h / SRC_H), scr_h
        r = 58 - 14
        hole = Image.new("L", L.size, 0)
        ImageDraw.Draw(hole).rounded_rectangle([sx, sy, sx + self.scr_w, sy + scr_h], radius=r, fill=255)
        al = L.split()[3].copy()
        al.paste(0, mask=hole)
        bezel = L.copy()
        bezel.putalpha(al)
        self.pad = 140
        P = self.pad
        self.size = (L.width + 2 * P, L.height + 2 * P)
        sh = Image.new("L", self.size, 0)
        sh.paste(L.split()[3].point(lambda v: int(v * 0.6)), (P, P + 40))
        self.shadow = Image.new("RGBA", self.size, (0, 0, 0, 0))
        self.shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(48)))
        self.bezel = Image.new("RGBA", self.size, (0, 0, 0, 0))
        self.bezel.alpha_composite(bezel, (P, P))
        self.mask = Image.new("L", (self.scr_w, scr_h), 0)
        ImageDraw.Draw(self.mask).rounded_rectangle([0, 0, self.scr_w - 1, scr_h - 1], radius=r, fill=255)
        self.screen_xy = (P + sx, P + sy)
        self.body = L.size

    def layer(self, frame):
        lay = self.shadow.copy()
        s = frame.convert("RGBA")
        s.putalpha(self.mask)
        lay.alpha_composite(s, self.screen_xy)
        lay.alpha_composite(self.bezel)
        return lay

    def place(self, c, lay, cx, cy, scale=1.0, alpha=1.0):
        """Composite the padded layer so the phone body is centred at (cx, cy)."""
        if abs(scale - 1) > 1e-3:
            lay = lay.resize((int(lay.width * scale), int(lay.height * scale)), Image.BICUBIC)
        if alpha < 1:
            lay = lay.copy()
            lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
        c.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


def clip_frames(path, start, dur, w, h):
    """The clip's frames at FPS, scaled with Lanczos to (w, h)."""
    p = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", "-ss", str(start), "-t", str(dur), "-i", path,
                          "-vf", f"fps={FPS},scale={w}:{h}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    n = w * h * 3
    out = []
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        out.append(Image.frombuffer("RGB", (w, h), b))
    p.wait()
    return out


# ---------------------------------------------------------------- output

class Writer:
    def __init__(self, out, w, h):
        self.out_silent = out[:-4] + "-silent.mp4"
        self.out, self.n = out, 0
        self.p = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                                   "-crf", "17", "-pix_fmt", "yuv420p", self.out_silent], stdin=subprocess.PIPE)

    def add(self, img):
        self.p.stdin.write(mo.dither(img.convert("RGB")).tobytes())
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


def with_alpha(layer, a):
    if a >= 1:
        return layer
    layer = layer.copy()
    layer.putalpha(layer.split()[3].point(lambda v: int(v * max(a, 0))))
    return layer


def text_layer(size, fn):
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay))
    return lay


def ground(app, size, spot=(0.5, 0.42)):
    """Deep app-tinted gradient with one soft spotlight and a faint accent glow."""
    W, H = size
    c = st.grad(size, tuple(int(v * 0.5) for v in app["accent2"]), tuple(int(v * 0.9) for v in app["dark"])).convert("RGBA")
    st.glow(c, (int(W * spot[0]), int(H * spot[1])), int(max(W, H) * 0.42), app["accent"], 26)
    st.glow(c, (int(W * 0.15), int(H * 0.05)), int(max(W, H) * 0.5), (255, 255, 255), 10)
    return c


# ---------------------------------------------------------------- end cards

def end_card(app, slug, size, line, store, style="icon"):
    W, H = size
    v = H > W
    if style == "type":
        c = Image.new("RGBA", size, app["accent"] + (255,))
        st.glow(c, (int(W * 0.8), int(H * 0.2)), int(max(W, H) * 0.5), (255, 255, 255), 30)
        d = ImageDraw.Draw(c)
        ink = app.get("ink", (20, 20, 20))
        x = 90 if v else 160
        y0 = int(H * (0.30 if v else 0.26))
        isz = 150 if v else 120
        ic = st.icon(slug, isz)
        sh = Image.new("RGBA", (isz + 120, isz + 120), (0, 0, 0, 0))
        m = Image.new("L", sh.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([60, 72, 60 + isz, 72 + isz], radius=int(isz * 0.22), fill=110)
        sh.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
        c.alpha_composite(sh, (x - 60, y0 - 60))
        c.alpha_composite(ic, (x, y0))
        ImageDraw.Draw(c).rounded_rectangle([x, y0, x + isz - 1, y0 + isz - 1], radius=int(isz * 0.22),
                                            outline=(255, 255, 255, 150), width=2)
        y = y0 + (200 if v else 160)
        y = st.text_block(d, (x, y), app["name"], st.font("black", 110 if v else 96), ink, W - 2 * x, lh=1.02)
        y = st.text_block(d, (x, y + 20), line, st.font("semi", 46 if v else 40), ink, W - 2 * x, lh=1.2)
        f = st.font("bold", 40)
        tw = d.textlength(store, font=f)
        d.rounded_rectangle([x, y + 50, x + tw + 84, y + 50 + 92], radius=46, fill=ink)
        d.text((x + (tw + 84) / 2, y + 96), store, font=f, fill=app["accent"], anchor="mm")
        d.text((x, H - (120 if v else 80)), "from Spikewave", font=st.font("semi", 34), fill=ink)
        return c
    c = ground(app, size, (0.5, 0.38))
    tile = mo.Tile(slug, 380 if v else 300)
    cy = H * 0.38
    mo.place_tile(c, mo.turn(tile.render(None), 0.03), W / 2, cy, -6, app["accent"], 38)
    d = ImageDraw.Draw(c)
    y = cy + (300 if v else 235)
    d.text((W / 2, y), app["name"], font=st.font("bold", 72 if v else 64), fill=INK, anchor="mm")
    d.text((W / 2, y + 78), line, font=st.font("regular", 38 if v else 34), fill=SUB, anchor="mm")
    mo.store_pill(c, y + 138, store, app, 1.0, cx=W / 2)
    d.text((W / 2, H - (110 if v else 70)), "from Spikewave", font=st.font("regular", 32), fill=SUB, anchor="mm")
    return c


def play_end(wr, card, secs):
    n = int(secs * FPS)
    black = Image.new("RGBA", card.size, (0, 0, 0, 255))
    for i in range(n):
        k = min(ease(i / 9), ease((n - i) / 15))
        wr.add(Image.blend(black, card, k) if k < 1 else card)


# ---------------------------------------------------------------- Shorts

def short(spec, out):
    slug, app = spec["app"], st.APPS[spec["app"]]
    W, H = 1080, 1920
    intro = spec.get("intro", "rise")
    bg = ground(app, (W, H), (0.5, 0.62))
    phone = Phone(1300)
    PCX, PCY = W / 2, 560 + phone.body[1] / 2          # phone body centre at rest
    frames = clip_frames(os.path.join(ROOT, spec["clip"]), spec.get("start", 0), spec["dur"], phone.scr_w, phone.scr_h)
    f_k, f_h = st.font("cond", 36), st.font("bold", 66)

    def cap_layer(text, words=None):
        def fn(d):
            st.caps(d, (80, 150), spec["kicker"], f_k, app["accent"])
            d.rectangle([80, 196, 80 + 56, 200], fill=app["accent"])
            st.text_block(d, (80, 222), text if words is None else " ".join(text.split()[:words]), f_h, INK, W - 160, lh=1.1)
        return text_layer((W, H), fn)
    c1, c2 = cap_layer(spec["cap1"]), cap_layer(spec["cap2"])

    lead = {"type": 1.5, "icon": 1.5, "stat": 1.4}.get(intro, 0.0)   # seconds before the clip starts playing
    T = lead + len(frames) / FPS
    t2 = lead + spec.get("cap2_at", spec["dur"] * 0.45)
    wr = Writer(out, W, H)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    tile = mo.Tile(slug, 420) if intro == "icon" else None
    intro_bg = ground(app, (W, H), (0.5, 0.45)) if intro in ("icon", "stat") else None
    n_total = int(T * FPS)
    word_cache = {}
    for i in range(n_total):
        t = i / FPS
        ci = min(max(int((t - lead) * FPS), 0), len(frames) - 1)
        lay = phone.layer(frames[ci])
        u = max(t - lead, 0) / max(T - lead, 1e-3)
        push = 1.0 + 0.035 * ease_io(u)                    # slow push-in across the clip
        c = bg.copy()
        cap_a = 1.0
        if intro == "zoom":
            z = ease_io(min(t / 1.6, 1))
            fx, fy = spec.get("focus", [0.5, 0.3])
            fpx = phone.screen_xy[0] + fx * phone.scr_w - phone.size[0] / 2   # focus offset from layer centre
            fpy = phone.screen_xy[1] + fy * phone.scr_h - phone.size[1] / 2
            s = lerp(2.3, push, z)
            cx = lerp(W / 2 - fpx * 2.3, PCX, z)
            cy = lerp(H * 0.55 - fpy * 2.3, PCY, z)
            phone.place(c, lay, cx, cy, s)
            cap_a = ease((t - 1.0) / 0.6)
        elif intro == "rise":
            r = ease(min(t / 0.9, 1))
            phone.place(c, lay, PCX, PCY + 900 * (1 - r), lerp(0.94, push, r))
            cap_a = 1.0
        elif intro in ("type", "icon", "stat"):
            r = ease(min(max(t - lead + 0.45, 0) / 0.7, 1))
            phone.place(c, lay, PCX, PCY + 500 * (1 - r), lerp(0.96, push, r), alpha=r)
            cap_a = ease((t - lead + 0.1) / 0.5)
        # captions
        if t < t2:
            if intro == "rise" and t < 2.0:
                nw = max(1, min(len(spec["cap1"].split()), int(t / 0.16) + 1))
                if nw not in word_cache:
                    word_cache[nw] = cap_layer(spec["cap1"], nw)
                c.alpha_composite(with_alpha(word_cache[nw], ease(t / 0.3)))
            else:
                c.alpha_composite(with_alpha(c1, min(cap_a, ease((t2 - t) / 0.3))))
        else:
            a = ease((t - t2) / 0.45)
            lay2 = c2 if a >= 1 else with_alpha(c2, a)
            c.alpha_composite(lay2, (0, int(18 * (1 - a))))
        # opening overlays
        if intro == "type" and t < lead + 0.45:
            off = int(H * ease_io(max(t - (lead - 0.25), 0) / 0.7))
            panel = Image.new("RGBA", (W, H), app["accent"] + (255,))
            d = ImageDraw.Draw(panel)
            ink = app.get("ink", (20, 20, 20))
            st.caps(d, (90, 640), spec["kicker"], st.font("cond", 40), ink)
            st.text_block(d, (90, 700), spec.get("hook", spec["cap1"]), st.font("black", 112), ink, W - 180, lh=1.04)
            a = ease(t / 0.35)
            c.alpha_composite(with_alpha(panel, a), (0, -off))
        elif intro == "icon" and t < lead + 0.3:
            k = 1 - ease(max(t - (lead - 0.3), 0) / 0.6)
            o = intro_bg.copy()
            rv = ease_io(min(t / 1.0, 1))
            mo.place_tile(o, mo.turn(tile.render(mo.sheen_at(t, 0.9, 9, 0.9), reveal=rv), 0.04 * math.sin(t)),
                          W / 2, 860, -6, app["accent"], int(40 * rv))
            mo.fade_text(o, (W / 2, 1180), app["name"], st.font("bold", 72), INK, ease((t - 0.4) / 0.5), anchor="mm")
            c.alpha_composite(with_alpha(o, k))
        elif intro == "stat" and t < lead + 0.3:
            k = 1 - ease(max(t - (lead - 0.35), 0) / 0.6)
            o = intro_bg.copy()
            d = ImageDraw.Draw(o)
            a = ease(t / 0.5)
            st.caps(d, (90, 640), spec["kicker"], st.font("cond", 40), app["accent"])
            st.text_block(d, (90, 700), spec["stat"], st.font("black", 150), INK + (int(255 * a),), W - 180, lh=1.0)
            d.text((90, 1120), spec.get("stat_sub", ""), font=st.font("regular", 44), fill=SUB + (int(255 * a),))
            c.alpha_composite(with_alpha(o, k))
        k = ease(t / 0.25)
        wr.add(Image.blend(black, c, k) if k < 1 else c)
    play_end(wr, end_card(app, slug, (W, H), spec["end_line"], spec["store"], spec.get("end", "icon")), 2.6)
    return wr.close(spec.get("music_start", 0))


# ---------------------------------------------------------------- explainers

def explainer(spec, out):
    slug, app = spec["app"], st.APPS[spec["app"]]
    W, H = 1920, 1080
    base = ground(app, (W, H), (0.72, 0.5))
    phone = Phone(940)
    PCX, PCY = W * 0.72, H / 2 + 6
    wr = Writer(out, W, H)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    chapters = spec["chapters"]
    tc = spec.get("title_clip", {"clip": chapters[0]["clip"], "start": chapters[0].get("start", 0)})
    first = clip_frames(os.path.join(ROOT, tc["clip"]), tc.get("start", 0), 0.1, phone.scr_w, phone.scr_h)[0]

    style = spec.get("title_style", "icon")
    n = int(3.8 * FPS)
    tile = mo.Tile(slug, 300)
    for i in range(n):
        t = i / FPS
        if style == "type":
            c = Image.new("RGBA", (W, H), app["accent"] + (255,))
            st.glow(c, (int(W * 0.85), int(H * 0.15)), 900, (255, 255, 255), 28)
            d = ImageDraw.Draw(c)
            ink = app.get("ink", (20, 20, 20))
            a = ease((t - 0.15) / 0.6)
            c.alpha_composite(with_alpha(st.icon(slug, 120), a), (160, 300))
            st.text_block(d, (160, 460 + 20 * (1 - a)), spec["title"], st.font("black", 104), ink + (int(255 * a),), 1500, lh=1.02)
            mo.fade_text(c, (160, 600), spec["line"], st.font("semi", 44), ink, ease((t - 0.5) / 0.6))
        elif style == "phone":
            c = base.copy()
            r = ease(min(t / 1.0, 1))
            phone.place(c, phone.layer(first), PCX, PCY + 600 * (1 - r), lerp(0.95, 1.0, r))
            mo.fade_text(c, (160, 430), app["name"].upper(), st.font("cond", 44), app["accent"], ease((t - 0.3) / 0.5))
            lay = text_layer((W, H), lambda d: st.text_block(d, (160, 490), spec["title"], st.font("black", 92), INK, 900, lh=1.04))
            c.alpha_composite(with_alpha(lay, ease((t - 0.5) / 0.6)))
            ln = text_layer((W, H), lambda d: st.text_block(d, (160, 700), spec["line"], st.font("regular", 40), SUB, 820, lh=1.3))
            c.alpha_composite(with_alpha(ln, ease((t - 0.8) / 0.6)))
        else:
            c = base.copy()
            mo.place_tile(c, mo.turn(tile.render(mo.sheen_at(t, 0.8, 9, 1.3)), 0.04 * math.sin(t * 0.8)),
                          W / 2, 400 + 30 * (1 - ease(t / 0.8)), -6, app["accent"], int(40 * ease(t / 0.8)))
            mo.fade_text(c, (W / 2, 690), spec["title"], st.font("bold", 76), INK, ease((t - 0.3) / 0.7), anchor="mm")
            mo.fade_text(c, (W / 2, 780), spec["line"], st.font("regular", 40), SUB, ease((t - 0.6) / 0.7), anchor="mm")
        k = min(ease(t / 0.4), ease((3.8 - t) / 0.4))
        wr.add(Image.blend(black, c, k))

    total = len(chapters)
    for ci, ch in enumerate(chapters):
        frames = clip_frames(os.path.join(ROOT, ch["clip"]), ch.get("start", 0), ch["dur"], phone.scr_w, phone.scr_h)
        frames += [frames[-1]] * int(ch.get("hold", 0.8) * FPS)

        def draw_text(d, ch=ch, ci=ci):
            st.caps(d, (160, 330), f"{ci + 1:02d}  /  {total:02d}", st.font("cond", 40), app["accent"])
            d.rectangle([160, 384, 216, 388], fill=app["accent"])
            y = st.text_block(d, (160, 410), ch["head"], st.font("bold", 66), INK, 800, lh=1.08)
            st.text_block(d, (160, y + 26), ch["body"], st.font("regular", 38), SUB, 760, lh=1.38)
            for j in range(total):
                d.rounded_rectangle([160 + j * 46, 880, 160 + j * 46 + (34 if j == ci else 14), 892], radius=6,
                                    fill=(app["accent"] + (255,)) if j == ci else (255, 255, 255, 70))
        txt = text_layer((W, H), draw_text)
        m = len(frames)
        for i, fr in enumerate(frames):
            t = i / FPS
            c = base.copy()
            push = 1.0 + 0.03 * ease_io(i / m)
            enter = ease(min(t / 0.6, 1)) if ci == 0 else 1.0
            phone.place(c, phone.layer(fr), PCX, PCY + 80 * (1 - enter), push)
            a = ease((t - 0.15) / 0.6)
            c.alpha_composite(with_alpha(txt, a), (int(-30 * (1 - a)), 0))
            k = min(ease(t / 0.35), ease((m - i) / 10))
            wr.add(Image.blend(black, c, k) if k < 1 else c)

    play_end(wr, end_card(app, slug, (W, H), spec["end_line"], spec["store"], spec.get("end", "icon")), 4.0)
    dur = wr.close(spec.get("music_start", 0))

    # thumbnail 1280x720: big text left, icon tile right
    th = st.grad((1280, 720), tuple(int(v * 0.55) for v in app["accent2"]), app["dark"]).convert("RGBA")
    st.glow(th, (930, 360), 520, app["accent"], 44)
    tt = mo.Tile(slug, 380)
    mo.place_tile(th, mo.turn(tt.render(0.35), 0.06), 950, 370, -9, None, 0)
    d = ImageDraw.Draw(th)
    st.caps(d, (70, 150), app["name"], st.font("cond", 40), app["accent"])
    st.text_block(d, (70, 210), spec["thumb_text"], st.font("black", 92), INK, 640, lh=1.05)
    mo.dither(th.convert("RGB")).save(out[:-4] + "-thumb.jpg", quality=92)
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
