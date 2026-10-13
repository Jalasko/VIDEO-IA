"""Frame pipeline: world render -> camera -> grade/bloom/vignette -> text."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import song
from .gfx import W, H, SS, font
from .scenes import render_world, vertical_cam, GRADES

FPS = 30

# output format: 'wide' = 1920x1080 (YouTube), 'vertical' = 1080x1920 (TikTok / Reels / Shorts)
FMT = 'wide'
OW, OH = W, H
_VIG = {}


def set_format(fmt):
    global FMT, OW, OH
    FMT = fmt
    OW, OH = (1080, 1920) if fmt == 'vertical' else (W, H)


def vignette():
    if (OW, OH) not in _VIG:
        yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
        r = np.sqrt(((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2)
        _VIG[(OW, OH)] = np.clip(1 - (r - 0.55) * 0.55, 0, 1) ** 1.6
    return _VIG[(OW, OH)]


def camera(fr, cam):
    """Crop the world (virtual 1920x1080) around cam=(cx, cy, zoom) to the output aspect."""
    cx, cy, z = cam
    img = Image.fromarray(np.clip(fr.a, 0, 255).astype(np.uint8))
    if FMT == 'vertical':
        h = H / z
        w = h * OW / OH
    else:
        w, h = W / z, H / z
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h / 2, 0), H - h)
    box = (x0 * SS, y0 * SS, (x0 + w) * SS, (y0 + h) * SS)
    return np.asarray(img.resize((OW, OH), Image.LANCZOS, box=box), np.float32)


def grade(a, g, shot, t):
    a = a * np.asarray(g['mul'], np.float32)
    m = a.mean(-1, keepdims=True)
    a = m + (a - m) * g['sat']
    # bloom
    hi = np.clip(a - 175, 0, None)
    small = Image.fromarray(np.clip(hi, 0, 255).astype(np.uint8)).resize((OW // 4, OH // 4), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(10))
    a = a + np.asarray(small.resize((OW, OH), Image.BILINEAR), np.float32) * g['bloom'] * 2.2
    vig = 1 - (1 - vignette()) * (g['vig'] / 0.2)
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
    over = Image.new('RGBA', (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    vert = FMT == 'vertical'
    # vertical: keep text inside TikTok's safe zone (clear of the top bar, captions and side buttons)
    y_title, y_sub, y_end = (330, 445, 400) if vert else (175, 285, 150)
    tsize = 112 if vert else 128
    # ---- title
    if t < 4.8:
        al = min(1, max(0, (t - 0.3) / 0.4)) * min(1, max(0, (4.6 - t) / 0.4))
        if al > 0:
            title = "Bath Time Song"
            f = font(tsize)
            widths = [f.getlength(c) for c in title]
            x = OW / 2 - sum(widths) / 2
            for i, (c, wd) in enumerate(zip(title, widths)):
                k = min(1, max(0, (t - 0.3 - i * 0.06) / 0.25))
                if c != ' ' and k > 0:
                    dy = -abs(math.sin(t * 3.2 + i * 0.5)) * 14 + (1 - k) * 40
                    draw_text_center(d, x + wd / 2, y_title + dy, c, tsize, PALETTE[i % len(PALETTE)],
                                     stroke=(255, 255, 255), sw=9, alpha=int(255 * al * k))
                x += wd
            draw_text_center(d, OW / 2, y_sub, "with Lilo & Bobo", 54, (255, 255, 255), stroke=(120, 90, 170), sw=5,
                             alpha=int(255 * al))
    # ---- ending
    end0 = song.line_start(11) + 2 * song.BAR + 0.3
    if t > end0:
        al = min(1, (t - end0) / 0.6)
        draw_text_center(d, OW / 2, y_end - 8 * math.sin(t * 2.5), "Goodnight!", 120, (255, 226, 110),
                         stroke=(255, 255, 255), sw=8, alpha=int(255 * al))
    # ---- karaoke lyrics
    li = song.current_line(t)
    if li is not None:
        a = song.line_start(li) - 0.35
        b = a + 2 * song.BAR
        al = min(1, (t - a) / 0.25, (b - t) / 0.25)
        chunks = [c for c in song.CHUNKS if c['line'] == li]
        size = 66 if vert else 60
        f = font(size)
        space = f.getlength(' ')
        widths = [f.getlength(c['text']) for c in chunks]
        # wrap into rows that fit the frame (vertical lines usually become two rows)
        rows, cur = [], []
        for c, wd in zip(chunks, widths):
            if cur and sum(w for _, w in cur) + space * len(cur) + wd > OW - 160:
                rows.append(cur)
                cur = []
            cur.append((c, wd))
        rows.append(cur)
        row_h = size * 1.25
        yc = 1540 if vert else OH - 95
        y0 = yc - row_h * (len(rows) - 1) / 2
        maxw = max(sum(w for _, w in r) + space * (len(r) - 1) for r in rows)
        d.rounded_rectangle([OW / 2 - maxw / 2 - 40, y0 - 50, OW / 2 + maxw / 2 + 40, y0 + row_h * (len(rows) - 1) + 50],
                            radius=50, fill=(255, 255, 255, int(130 * al)), outline=(255, 255, 255, int(200 * al)), width=3)
        for ri, row in enumerate(rows):
            total = sum(w for _, w in row) + space * (len(row) - 1)
            x = OW / 2 - total / 2
            y = y0 + ri * row_h
            for c, wd in row:
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
    if FMT == 'vertical':
        cam = vertical_cam(t, shot)
    a = camera(fr, cam)
    a = grade(a, GRADES[shot], shot, t)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img = overlays(img, t)
    return np.asarray(img).tobytes()
