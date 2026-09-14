from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys, json, os

# Cross-platform fonts: prefer Segoe UI on Windows, fall back to DejaVu on Linux
# (the cloud runner is Linux and has no Windows fonts). Each logical weight maps
# to the first file that exists.
_FONT_DIRS = ["C:/Windows/Fonts/", "/usr/share/fonts/truetype/dejavu/",
              "/usr/share/fonts/truetype/freefont/"]
_FONT_ALIASES = {
    "seguibl.ttf":  ["seguibl.ttf", "DejaVuSans-Bold.ttf", "FreeSansBold.ttf"],
    "segoeuib.ttf": ["segoeuib.ttf", "DejaVuSans-Bold.ttf", "FreeSansBold.ttf"],
    "segoeui.ttf":  ["segoeui.ttf", "DejaVuSans.ttf", "FreeSans.ttf"],
}
def _resolve(name):
    for cand in _FONT_ALIASES.get(name, [name]):
        for d in _FONT_DIRS:
            p = d + cand
            if os.path.exists(p):
                return p
    return name  # let PIL try / raise
def font(name, size): return ImageFont.truetype(_resolve(name), size)

W, H = 1080, 1350

def rounded(img, rad):
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0,0,img.size[0],img.size[1]], radius=rad, fill=255)
    out = img.convert("RGBA"); out.putalpha(mask); return out

def vgrad(size, top, bot):
    w,h = size; top=tuple(top); bot=tuple(bot)
    col=Image.new("RGB",(1,h))
    px=col.load()
    for y in range(h):
        t=y/(h-1)
        px[0,y]=tuple(int(top[i]+(bot[i]-top[i])*t) for i in range(3))
    return col.resize((w,h))

def wrap(draw, text, fnt, maxw):
    words=text.split(); lines=[]; cur=""
    for wd in words:
        test=(cur+" "+wd).strip()
        if draw.textlength(test, font=fnt)<=maxw: cur=test
        else:
            if cur: lines.append(cur)
            cur=wd
    if cur: lines.append(cur)
    return lines

def compose(spec):
    bg = vgrad((W,H), spec["bg_top"], spec["bg_bot"])
    # accent glow behind phone
    glow = Image.new("RGBA",(W,H),(0,0,0,0))
    gd=ImageDraw.Draw(glow)
    ax,ay=spec["glow_xy"]
    gd.ellipse([ax-380,ay-380,ax+380,ay+380], fill=spec["accent"]+(90,))
    glow=glow.filter(ImageFilter.GaussianBlur(160))
    bg=Image.alpha_composite(bg.convert("RGBA"), glow)

    # phone screenshot
    shot=Image.open(spec["shot"]).convert("RGB")
    ph=Image.new("RGB",(0,0))
    target_h=980
    scale=target_h/shot.height
    pw=int(shot.width*scale); pht=target_h
    shot=shot.resize((pw,pht), Image.LANCZOS)
    shot=rounded(shot, 44)
    # shadow
    sh=Image.new("RGBA",(pw+80,pht+80),(0,0,0,0))
    shd=ImageDraw.Draw(sh)
    shd.rounded_rectangle([40,40,40+pw,40+pht], radius=44, fill=(0,0,0,150))
    sh=sh.filter(ImageFilter.GaussianBlur(30))
    px_ = W-pw-70   # phone right
    py_ = (H-pht)//2 + 40
    bg.alpha_composite(sh,(px_-40,py_-30))
    # subtle border
    bord=Image.new("RGBA",(pw,pht),(0,0,0,0))
    bd=ImageDraw.Draw(bord)
    bd.rounded_rectangle([0,0,pw-1,pht-1], radius=44, outline=spec["accent"]+(120,), width=3)
    bg.alpha_composite(shot,(px_,py_))
    bg.alpha_composite(bord,(px_,py_))

    d=ImageDraw.Draw(bg)
    tx=80; textw=px_-80-60
    # headline
    hf=font("seguibl.ttf", spec.get("hsize",76))
    lines=wrap(d, spec["headline"], hf, textw)
    y=170
    for ln in lines:
        d.text((tx,y), ln, font=hf, fill=(247,242,236)); y+=int(spec.get("hsize",76)*1.06)
    # subline
    y+=24
    sf=font("segoeui.ttf", 33)
    for ln in wrap(d, spec["sub"], sf, textw):
        d.text((tx,y), ln, font=sf, fill=(176,166,152)); y+=46
    # bottom wordmark + cta
    wf=font("segoeuib.ttf", 34)
    cf=font("segoeui.ttf", 28)
    by=H-150
    d.text((tx,by), spec["wordmark"], font=wf, fill=spec["accent"])
    d.text((tx,by+48), spec["cta"], font=cf, fill=(200,206,220))
    d.text((tx,by+86), "www.spikewave.tech", font=cf, fill=(120,126,140))

    bg.convert("RGB").save(spec["out"], quality=95)
    print("wrote", spec["out"])

specs=json.load(open(sys.argv[1]))
for s in specs:
    s["accent"]=tuple(s["accent"])
    compose(s)
