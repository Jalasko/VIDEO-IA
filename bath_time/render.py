"""Frame pipeline: world render -> camera -> grade/bloom/vignette -> text."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import song
from .gfx import W, H, SS, font
from .scenes import render_world, GRADES

FPS = 30

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_R = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIG = np.clip(1 - (_R - 0.55) * 0.55, 0, 1) ** 1.6
del _yy, _xx, _R


def camera(fr, cam):
    cx, cy, z = cam
    img = Image.fromarray(np.clip(fr.a, 0, 255).astype(np.uint8))
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    box = (x0 * SS, y0 * SS, (x0 + w) * SS, (y0 + h) * SS)
    return np.asarray(img.resize((W, H), Image.LANCZOS, box=box), np.float32)


def grade(a, g, shot, t):
    a = a * np.asarray(g['mul'], np.float32)
    m = a.mean(-1, keepdims=True)
    a = m + (a - m) * g['sat']
    # bloom
    hi = np.clip(a - 175, 0, None)
    small = Image.fromarray(np.clip(hi, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(10))
    a = a + np.asarray(small.resize((W, H), Image.BILINEAR), np.float32) * g['bloom'] * 2.2
    vig = 1 - (1 - VIG) * (g['vig'] / 0.2)
    a = a * vig[..., None]
    # fades: in at start, out at the end
    if t < 0.5:
        a *= t / 0.5
    a *= min(1.0, max(0.0, (song.DURATION - t) / 1.3))
    return a


PALETTE = [(255, 120, 150), (255, 176, 60), (255, 214, 60), (110, 200, 110), (90, 180, 250), (176, 130, 250)]


def draw_text_center(d, x, y, s, size, fill, stroke=(120, 70, 140), sw=5, alpha=255):
    f = font(size)
    d.text((x, y + size * 0.06), s, font=f, anchor='mm', fill=(60, 30, 80, int(alpha * 0.35)))
    d.text((x, y), s, font=f, anchor='mm', fill=fill + (alpha,), stroke_width=sw, stroke_fill=stroke + (alpha,))


def overlays(img, t):
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    # ---- title
    if t < 4.8:
        al = min(1, max(0, (t - 0.3) / 0.4)) * min(1, max(0, (4.6 - t) / 0.4))
        if al > 0:
            title = "Bath Time Song"
            f = font(128)
            widths = [f.getlength(c) for c in title]
            x = W / 2 - sum(widths) / 2
            for i, (c, wd) in enumerate(zip(title, widths)):
                k = min(1, max(0, (t - 0.3 - i * 0.06) / 0.25))
                if c != ' ' and k > 0:
                    dy = -abs(math.sin(t * 3.2 + i * 0.5)) * 14 + (1 - k) * 40
                    draw_text_center(d, x + wd / 2, 175 + dy, c, 128, PALETTE[i % len(PALETTE)],
                                     stroke=(255, 255, 255), sw=9, alpha=int(255 * al * k))
                x += wd
            draw_text_center(d, W / 2, 285, "with Lilo & Bobo", 54, (255, 255, 255), stroke=(120, 90, 170), sw=5,
                             alpha=int(255 * al))
    # ---- ending
    end0 = song.line_start(11) + 2 * song.BAR + 0.3
    if t > end0:
        al = min(1, (t - end0) / 0.6)
        draw_text_center(d, W / 2, 150 - 8 * math.sin(t * 2.5), "Goodnight!", 120, (255, 226, 110),
                         stroke=(255, 255, 255), sw=8, alpha=int(255 * al))
    # ---- karaoke lyrics
    li = song.current_line(t)
    if li is not None:
        a = song.line_start(li) - 0.35
        b = a + 2 * song.BAR
        al = min(1, (t - a) / 0.25, (b - t) / 0.25)
        chunks = [c for c in song.CHUNKS if c['line'] == li]
        size = 60
        f = font(size)
        space = f.getlength(' ')
        widths = [f.getlength(c['text']) for c in chunks]
        total = sum(widths) + space * (len(chunks) - 1)
        x = W / 2 - total / 2
        y = H - 95
        d.rounded_rectangle([x - 40, y - 50, x + total + 40, y + 50], radius=50,
                            fill=(255, 255, 255, int(130 * al)), outline=(255, 255, 255, int(200 * al)), width=3)
        for c, wd in zip(chunks, widths):
            if t >= c['t1']:
                col, dy = (255, 200, 60), 0
            elif t >= c['t0'] - 0.03:
                u = (t - c['t0']) / max(c['t1'] - c['t0'], 1e-3)
                col, dy = (255, 120, 160), -10 * math.sin(math.pi * min(1, u * 2))
            else:
                col, dy = (255, 255, 255), 0
            draw_text_center(d, x + wd / 2, y + dy, c['text'], size, col, stroke=(110, 70, 160), sw=5,
                             alpha=int(255 * al))
            x += wd + space
    img = Image.alpha_composite(img.convert('RGBA'), over)
    return img.convert('RGB')


def render_frame(i):
    t = i / FPS
    fr, cam, shot = render_world(t)
    a = camera(fr, cam)
    a = grade(a, GRADES[shot], shot, t)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img = overlays(img, t)
    return np.asarray(img).tobytes()
