"""Frame pipeline for « La dernière pomme » (vertical 1080x1920)."""
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import story
from .scenes import render_world, GRADE, META, W, H, smooth
from bath_time.gfx import SS, font

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - (np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) - 0.6) * 0.6, 0, 1) ** 1.5
del _yy, _xx
_LINES = None


def lines():
    global _LINES
    if _LINES is None:
        with open(META) as f:
            _LINES = json.load(f)['lines']
    return _LINES


def camera(fr, cam):
    cx, cy, z, rot = cam
    img = Image.fromarray(np.clip(fr.a, 0, 255).astype(np.uint8))
    a = math.radians(rot)
    ca, sa = abs(math.cos(a)), abs(math.sin(a))
    z = z * (ca + sa * H / W)              # zoom in enough that a tilted view never shows the edge
    w, h = W / z, H / z
    ex, ey = (w * ca + h * sa) / 2, (w * sa + h * ca) / 2
    cx = min(max(cx, ex), W - ex)
    cy = min(max(cy, ey), H - ey)
    if abs(rot) < 0.05:
        box = ((cx - w / 2) * SS, (cy - h / 2) * SS, (cx + w / 2) * SS, (cy + h / 2) * SS)
        return np.asarray(img.resize((W, H), Image.LANCZOS, box=box), np.float32)
    # rotation: pre-shrink to output scale, then affine-rotate around the view centre
    k = z / SS
    big = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
    ccx, ccy = cx * SS * k, cy * SS * k
    c, s_ = math.cos(a), math.sin(a)
    # output (u,v) -> input: centre + R * (u - W/2, v - H/2)
    data = (c, -s_, ccx - c * W / 2 + s_ * H / 2, s_, c, ccy - s_ * W / 2 - c * H / 2)
    out = big.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC)
    return np.asarray(out, np.float32)


def grade(a, t, name):
    g = GRADE
    a = a * np.asarray(g['mul'], np.float32)
    m = a.mean(-1, keepdims=True)
    a = m + (a - m) * g['sat']
    hi = np.clip(a - 180, 0, None)
    small = Image.fromarray(np.clip(hi, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(10))
    a = a + np.asarray(small.resize((W, H), Image.BILINEAR), np.float32) * g['bloom'] * 2.2
    a = a * (1 - (1 - VIG) * (g['vig'] / 0.2))[..., None]
    # quick white flash on the freeze-frame close-ups
    for c in story.FREEZE_CUTS:
        if 0 <= t - c < 0.07:
            a = a + 120 * (1 - (t - c) / 0.07)
    if t >= story.FREEZE:
        k = smooth((t - story.FREEZE) / 0.15)
        a = a + 140 * max(0, 1 - (t - story.FREEZE) / 0.1)
        m = a.mean(-1, keepdims=True)
        a = m + (a - m) * (1 + 0.25 * k)
    if t < 0.25:
        a *= t / 0.25
    return a


def text(d, x, y, s, size, fill, stroke=(20, 16, 24), sw=8, alpha=255, anchor='mm'):
    f = font(size)
    d.text((x, y), s, font=f, anchor=anchor, fill=fill + (alpha,), stroke_width=sw, stroke_fill=stroke + (alpha,))


def captions(d, t):
    for ln in lines():
        if ln['t0'] - 0.1 <= t < ln['t1'] + 0.5:
            size = 64
            f = font(size)
            space = f.getlength(' ')
            rows, cur, cw = [], [], 0
            for w in ln['words']:
                wd = f.getlength(w[0])
                if cur and cw + space + wd > 900:
                    rows.append(cur)
                    cur, cw = [], 0
                cur.append((w, wd))
                cw += wd + (space if cw else 0)
            rows.append(cur)
            y0 = 1580 - (len(rows) - 1) * size * 1.2
            for ri, row in enumerate(rows):
                tot = sum(wd for _, wd in row) + space * (len(row) - 1)
                x = W / 2 - tot / 2
                for (wt, a, b), wd in row:
                    if a <= t < b + 0.05:
                        col, dy, sz = (255, 220, 40), -6, size + 4
                    else:
                        col, dy, sz = (255, 255, 255), 0, size
                    text(d, x + wd / 2, y0 + ri * size * 1.2 + dy, wt, sz, col)
                    x += wd + space


def overlays(img, t):
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    captions(d, t)
    if t >= story.FREEZE:
        k = smooth((t - story.FREEZE - 0.2) / 0.3)
        if k > 0:
            dy = (1 - k) * -80
            text(d, W / 2, 330 + dy, "La dernière", 104, (255, 236, 120), stroke=(150, 30, 30), sw=10, alpha=int(255 * k))
            text(d, W / 2, 460 + dy, "pomme", 150, (235, 50, 50), stroke=(255, 255, 255), sw=12, alpha=int(255 * k))
    return Image.alpha_composite(img.convert('RGBA'), over).convert('RGB')


def render_frame(i):
    t = i / story.FPS
    fr, cam, name = render_world(t)
    a = camera(fr, cam)
    a = grade(a, t, name)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(overlays(img, t)).tobytes()
