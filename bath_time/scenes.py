"""The six shots of "Bath Time Song": backgrounds, staging, actions, camera."""
import math
import numpy as np

from . import song
from .gfx import (Frame, shape, ball, glow, bubble, sparkle, vgrad, blur_frame, soft_shadow,
                  set_lighting, W, H)
from .characters import lilo, bobo, mom, duck, boat, frog

# ------------------------------------------------------------- helpers ----


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return a + (b - a) * u


def keys(t, ks):
    """Smooth interpolation through keyframes [(t, v0, v1, ...)]."""
    if t <= ks[0][0]:
        return ks[0][1:]
    for a, b in zip(ks[:-1], ks[1:]):
        if t <= b[0]:
            u = smooth((t - a[0]) / (b[0] - a[0]))
            return tuple(lerp(p, q, u) for p, q in zip(a[1:], b[1:]))
    return ks[-1][1:]


def blink(t, seed=0.0):
    return ((t + seed) % 3.4) < 0.13


def beat_phase(t):
    return (t % song.BEAT) / song.BEAT


def pulse(t, times, width=0.25):
    """1 at each event, decaying to 0 after `width` seconds."""
    v = 0.0
    for e in times:
        if 0 <= t - e < width:
            v = max(v, 1 - (t - e) / width)
    return v


# ------------------------------------------------------------- bubbles ----
def _field(seed, n, tb, box, rr, vy, life, wob=18):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        out.append(dict(tb=rng.uniform(*tb), x=rng.uniform(box[0], box[2]), y=rng.uniform(box[1], box[3]),
                        r=rng.uniform(*rr), vy=rng.uniform(*vy), life=rng.uniform(*life),
                        wob=rng.uniform(0.4, 1.0) * wob, f=rng.uniform(0.8, 1.6), ph=rng.uniform(0, 6.28),
                        hue=rng.uniform(0, 1)))
    return out


S = song.SHOTS
FIELDS = {
    0: _field(1, 16, (-4, 8.0), (260, 450, 1700, 1000), (12, 34), (25, 55), (4, 7.5)),
    1: _field(2, 24, (S[1][0] + 1.0, S[1][1] - 0.4), (300, 690, 1620, 740), (10, 30), (70, 130), (1.4, 3.2)),
    2: _field(3, 16, (S[2][0], S[2][1] - 1), (380, 560, 1420, 600), (10, 24), (40, 80), (2.0, 4.0)),
    3: _field(4, 30, (S[3][0] + 3.0, S[3][1] - 0.5), (790, 260, 1130, 360), (14, 38), (45, 95), (1.6, 3.4), wob=30),
}


def _bub_state(b, t):
    a = t - b['tb']
    if a < 0:
        return None
    x = b['x'] + b['wob'] * math.sin(b['ph'] + a * b['f'] * 2)
    y = b['y'] - b['vy'] * a
    return a, x, y


def draw_bubbles(fr, t, shot, sparkles=False):
    for b in FIELDS.get(shot, []):
        st = _bub_state(b, t)
        if st is None:
            continue
        a, x, y = st
        if a < b['life']:
            k = smooth(a / 0.35)
            bubble(fr, x, y, b['r'] * (0.3 + 0.7 * k), phase=b['hue'] + t * 0.15)
        elif a < b['life'] + 0.22:
            u = (a - b['life']) / 0.22
            shape(fr, [('ellipse', (x, y, b['r'] * (1 + u * 0.6), b['r'] * (1 + u * 0.6))),
                       ('ellipse', (x, y, b['r'] * (1 + u * 0.6) - 3, b['r'] * (1 + u * 0.6) - 3), 'erase')],
                  (255, 255, 255), 'flat', alpha=0.7 * (1 - u))
            if sparkles or b['r'] > 24:
                for k in range(4):
                    ang = k * math.pi / 2 + b['ph']
                    d = b['r'] * (0.8 + u * 0.9)
                    sparkle(fr, x + d * math.cos(ang), y + d * math.sin(ang), 9 * (1 - u) + 3, alpha=1 - u)


def _pop_events():
    ev = []
    for shot, fl in FIELDS.items():
        a, b = S[shot]
        for bb in fl:
            tp = bb['tb'] + bb['life']
            if a + 0.2 < tp < b - 0.05 and bb['y'] - bb['vy'] * bb['life'] > 40:
                ev.append(tp)
    ev.sort()
    out = []
    for t in ev:
        if not out or t - out[-1] > 0.12:
            out.append(t)
    return out


POP_EVENTS = _pop_events()


# --------------------------------------------------------- set pieces ----
def tiles(fr, x0, y0, x1, y1, size, c1, c2, grout, bevel=4):
    shape(fr, ('rect', (x0, y0, x1, y1)), grout, 'flat')
    a, b = [], []
    g = max(size * 0.06, 3)
    j = 0
    y = y0
    while y < y1:
        i = 0
        x = x0
        while x < x1:
            it = ('rrect', (x + g / 2, y + g / 2, min(x + size, x1 + size) - g / 2, y + size - g / 2, size * 0.18))
            (a if (i + j) % 2 == 0 else b).append(it)
            x += size
            i += 1
        y += size
        j += 1
    # clip to the band
    for lst, c in ((a, c1), (b, c2)):
        lst = lst + [('rect', (x0 - 400, y1, x1 + 400, y1 + 400), 'erase')]
        shape(fr, lst, c, bevel=bevel, spec=0.35, amb=0.62, rim=0.05, gloss=40)


def floor_checker(fr, ytop, c1, c2, vp=(960, 150), step=210):
    rows = [ytop]
    h = 26
    while rows[-1] < H + 50:
        rows.append(rows[-1] + h)
        h *= 1.45
    X = lambda xb, y: vp[0] + (xb - vp[0]) * (y - vp[1]) / (H - vp[1])
    cols = list(range(-3000, 5000, step))
    a, b = [], []
    for j in range(len(rows) - 1):
        for i in range(len(cols) - 1):
            ya, yb = rows[j], rows[j + 1]
            poly = [(X(cols[i], ya), ya), (X(cols[i + 1], ya), ya), (X(cols[i + 1], yb), yb), (X(cols[i], yb), yb)]
            (a if (i + j) % 2 == 0 else b).append(('poly', poly))
    shape(fr, a, c1, 'flat')
    shape(fr, b, c2, 'flat')
    shape(fr, ('rect', (0, ytop, W, ytop + 40)), (120, 90, 110), 'flat', alpha=0.10, blur=10)


def window(fr, x0, y0, x1, y1, night=False, t=0.0):
    r = (x1 - x0) / 2
    shape(fr, [('rrect', (x0 - 22, y0 - 22, x1 + 22, y1 + 22, r + 22))], (252, 252, 255), bevel=8, spec=0.3)
    sky = ((40, 50, 110), (80, 80, 150)) if night else ((130, 200, 255), (200, 236, 255))
    shape(fr, [('rrect', (x0, y0, x1, y1, r))], None, 'flat', grad=sky)
    cx = (x0 + x1) / 2
    if night:
        ball(fr, x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.3, 42, 42, (255, 236, 160), spec=0.1, amb=0.9)
        ball(fr, x0 + (x1 - x0) * 0.6, y0 + (y1 - y0) * 0.27, 38, 38, (52, 58, 120), spec=0, amb=1, rim=0)
        glow(fr, x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.3, 140, (90, 90, 60), 0.6)
        for k, (u, v) in enumerate(((0.2, 0.2), (0.35, 0.55), (0.8, 0.65), (0.25, 0.8), (0.55, 0.12))):
            sparkle(fr, x0 + (x1 - x0) * u, y0 + (y1 - y0) * v, 7 + 3 * math.sin(t * 3 + k), alpha=0.9)
    else:
        sx, sy = x0 + (x1 - x0) * 0.72, y0 + (y1 - y0) * 0.3
        glow(fr, sx, sy, 160, (255, 230, 150), 0.8)
        ball(fr, sx, sy, 38, 38, (255, 226, 90), spec=0.2, amb=0.95)
        for (u, v, s) in ((0.28, 0.45, 1.0), (0.6, 0.7, 0.8)):
            px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * v
            shape(fr, ('circles', [(px - 30 * s, py, 22 * s), (px, py - 12 * s, 30 * s), (px + 32 * s, py, 22 * s),
                                   (px, py + 6 * s, 24 * s)]), (255, 255, 255), bevel=7, spec=0.1, amb=0.8)
    shape(fr, [('rect', (cx - 7, y0, cx + 7, y1)), ('rect', (x0, (y0 + y1) / 2 + 20, x1, (y0 + y1) / 2 + 34))],
          (252, 252, 255), bevel=3, spec=0.3)
    shape(fr, ('rrect', (x0 - 40, y1 + 14, x1 + 40, y1 + 44, 14)), (252, 252, 255), bevel=6, spec=0.3)


def sunbeams(fr, x0, x1, ytop, spread=380, alpha=0.10):
    shape(fr, ('poly', [(x0, ytop), (x1, ytop), (x1 + spread, H + 40), (x0 + spread * 0.2, H + 40)]),
          (255, 248, 220), 'flat', alpha=alpha, blur=30)


def bottles(fr, x, y, s=1.0):
    specs = [((255, 150, 190), 40, 110), ((120, 210, 220), 34, 90), ((255, 210, 90), 30, 70), ((190, 160, 240), 36, 100)]
    xx = x
    for col, w, h in specs:
        w, h = w * s, h * s
        shape(fr, ('rrect', (xx, y - h, xx + w * 2, y, w * 0.7)), col, bevel=8 * s, spec=0.7, gloss=80)
        shape(fr, ('rrect', (xx + w * 0.6, y - h - 18 * s, xx + w * 1.4, y - h + 4, 6 * s)), (250, 250, 255), bevel=3 * s, spec=0.6)
        shape(fr, ('rrect', (xx + w * 0.45, y - h * 0.65, xx + w * 1.55, y - h * 0.3, 6 * s)), (255, 255, 255), 'flat', alpha=0.7)
        xx += w * 2 + 14 * s
    return xx


def shelf(fr, x0, x1, y, s=1.0):
    shape(fr, ('rrect', (x0, y, x1, y + 22 * s, 10 * s)), (252, 252, 255), bevel=6 * s, spec=0.3)
    shape(fr, ('rect', (x0 + 10, y + 22 * s, x1 - 10, y + 40 * s)), (90, 80, 110), 'flat', alpha=0.12, blur=8 * s)


def tub(fr, cx, cy, rx, ry, depth, inner_shrink=0.95, feet=True, part='all', level=None, t=0.0, foam=1.0,
        foam_rows=2):
    """part: 'back' (interior + water + foam) or 'front' (rim + front wall + feet)."""
    irx, iry = rx * inner_shrink, ry * 0.8
    icy = cy + ry * 0.07
    if part in ('back', 'all'):
        shape(fr, ('ellipse', (cx, icy, irx, iry)), None, 'flat', grad=((205, 222, 240), (240, 246, 255)))
        if level is not None:
            water_surface(fr, cx, icy, irx, iry, level, t, foam, foam_rows)
    if part in ('front', 'all'):
        shape(fr, [('ellipse', (cx, cy, rx, ry)), ('ellipse', (cx, icy, irx, iry), 'erase')],
              (250, 251, 255), bevel=10, spec=0.6, amb=0.65, gloss=50)
        if feet:
            for side in (-1, 1):
                ball(fr, cx + side * rx * 0.78, cy + depth + 10, 34, 30, (250, 196, 80), spec=0.9, gloss=80)
        shape(fr, [('rrect', (cx - rx * 0.985, icy - 4, cx + rx * 0.985, cy + depth, rx * 0.35)),
                   ('ellipse', (cx, icy, irx, iry), 'erase')], (250, 251, 255), bevel=26, spec=0.4, amb=0.6, gloss=35)
        shape(fr, ('rrect', (cx - rx * 0.8, cy + depth * 0.45, cx + rx * 0.8, cy + depth * 0.45 + 14, 7)),
              (255, 196, 214), bevel=4, spec=0.4)


def water_surface(fr, cx, icy, irx, iry, level, t, foam=1.0, rows=2):
    shape(fr, [('ellipse', (cx, icy, irx - 2, iry - 2)), ('rect', (cx - irx - 5, icy - iry - 5, cx + irx + 5, level), 'erase')],
          (150, 205, 245), 'flat', alpha=0.92)
    if foam <= 0:
        return
    dy = level - icy
    if abs(dy) >= iry:
        return
    hw = irx * math.sqrt(max(0.0, 1 - (dy / iry) ** 2))
    circles = []
    n = int(hw * 2 / 34 * foam) + 1
    for r in range(rows):
        for i in range(n):
            u = (i + 0.5 * (r % 2)) / max(n, 1)
            x = cx - hw * foam + u * 2 * hw * foam
            y = level - 8 + r * 22 + 6 * math.sin(i * 1.9 + r + t * 2.2)
            rad = (22 + 8 * math.sin(i * 2.7 + r * 1.3)) * (0.7 + 0.3 * foam)
            circles.append((x, y, rad))
    if circles:
        shape(fr, ('circles', circles), (252, 252, 255), bevel=6, spec=0.5, amb=0.75, rim=0.1)
        for i, (x, y, rad) in enumerate(circles[::4]):
            bubble(fr, x, y - rad * 0.6, rad * 0.5, phase=i * 0.17 + t * 0.2, alpha=0.9)


def drops(fr, pts, r=9):
    for (x, y, rr) in pts:
        ball(fr, x, y, r * rr, r * rr * 1.2, (190, 230, 255), spec=0.9, amb=0.8, rim=0.4, gloss=40, alpha=0.85)


def speech(fr, x, y, text_scale, alpha):
    """small 'Quack!' cloud; the text itself is drawn in post (screen space)."""
    if alpha <= 0:
        return
    shape(fr, ('circles', [(x - 40 * text_scale, y, 30 * text_scale), (x, y - 10 * text_scale, 38 * text_scale),
                           (x + 42 * text_scale, y, 30 * text_scale), (x, y + 12 * text_scale, 30 * text_scale)]),
          (255, 255, 255), bevel=6, spec=0.2, amb=0.85, alpha=alpha)


# -------------------------------------------------------- backgrounds ----
_BG = {}


def background(shot):
    if shot not in _BG:
        _BG[shot] = np.clip(_make_background(shot).a, 0, 255).astype(np.uint8)
    return Frame(_BG[shot].astype(np.float32))


def _make_background(shot):
    fr = Frame.solid((200, 236, 228))
    if shot == 0:
        vgrad(fr, 0, 450, (208, 242, 234), (186, 230, 222))
        window(fr, 770, 110, 1150, 400)
        tiles(fr, 0, 452, W, 772, 64, (150, 214, 214), (172, 226, 222), (226, 244, 240))
        shape(fr, ('rrect', (-20, 440, W + 20, 462, 10)), (255, 186, 206), bevel=5, spec=0.3)
        floor_checker(fr, 772, (255, 224, 212), (255, 242, 234))
        # door (left) with warm hallway light
        shape(fr, ('rrect', (60, 210, 380, 790, 30)), (252, 252, 255), bevel=8, spec=0.3)
        shape(fr, ('rrect', (88, 238, 352, 790, 18)), None, 'flat', grad=((255, 238, 180), (255, 214, 150)))
        glow(fr, 220, 520, 260, (60, 50, 20), 0.8)
        shape(fr, ('poly', [(88, 238), (20, 200), (20, 860), (88, 790)]), (255, 222, 140), bevel=8, spec=0.2)
        ball(fr, 70, 540, 12, 12, (250, 196, 80), spec=0.9)
        # towel rack
        shape(fr, ('capsule', (440, 480, 660, 480, 7)), (215, 225, 238), bevel=3, spec=0.9, gloss=90)
        shape(fr, ('rrect', (460, 470, 640, 660, 26)), (255, 176, 206), bevel=10, spec=0.15)
        for yy in (600, 620):
            shape(fr, ('rect', (462, yy, 638, yy + 8)), (255, 232, 240), 'flat', alpha=0.8)
        # shelf + bottles above the tub
        shelf(fr, 1360, 1720, 380)
        bottles(fr, 1380, 380, 0.8)
        duck(fr, 1660, 352, 0.6)
        # tub (empty) on the right
        tub(fr, 1530, 600, 300, 54, 170, feet=True)
        shape(fr, ('path', ([(1800, 600), (1800, 520), (1760, 500), (1735, 520)], 12)), (210, 222, 238), bevel=4, spec=0.9, gloss=90)
        # bath mat
        shape(fr, ('ellipse', (960, 915, 270, 58)), (150, 200, 250), bevel=14, spec=0.15, amb=0.65)
        for i in range(18):
            a = i / 18 * 2 * math.pi
            ball(fr, 960 + 262 * math.cos(a), 915 + 54 * math.sin(a), 9, 7, (170, 214, 255), spec=0.2)
        sunbeams(fr, 790, 1130, 300)
        fr = blur_frame(fr, 1.4)
    elif shot == 1:
        vgrad(fr, 0, 230, (208, 242, 234), (190, 232, 224))
        tiles(fr, 0, 250, W, 1080, 112, (150, 214, 214), (172, 226, 222), (226, 244, 240), bevel=6)
        shape(fr, ('rrect', (-20, 230, W + 20, 258, 12)), (255, 186, 206), bevel=6, spec=0.3)
        shelf(fr, 1460, 1880, 200)
        bottles(fr, 1480, 200, 0.9)
        glow(fr, 300, 100, 500, (60, 55, 30), 0.7)
        fr = blur_frame(fr, 3.5)
    elif shot == 2:
        vgrad(fr, 0, 330, (208, 242, 234), (190, 232, 224))
        window(fr, 140, 70, 400, 290)
        tiles(fr, 0, 340, W, 840, 84, (150, 214, 214), (172, 226, 222), (226, 244, 240), bevel=5)
        shape(fr, ('rrect', (-20, 322, W + 20, 346, 12)), (255, 186, 206), bevel=6, spec=0.3)
        floor_checker(fr, 840, (255, 224, 212), (255, 242, 234), vp=(960, 300))
        shelf(fr, 1380, 1800, 240)
        bottles(fr, 1400, 240, 0.85)
        duck(fr, 1745, 212, 0.55)
        sunbeams(fr, 160, 380, 240, spread=500, alpha=0.08)
        fr = blur_frame(fr, 2.2)
    elif shot == 3:
        vgrad(fr, 0, 180, (208, 242, 234), (190, 232, 224))
        tiles(fr, 0, 190, W, 1080, 130, (150, 214, 214), (172, 226, 222), (226, 244, 240), bevel=7)
        shape(fr, ('rrect', (-20, 170, W + 20, 200, 12)), (255, 186, 206), bevel=6, spec=0.3)
        window(fr, 90, -60, 420, 260)
        shelf(fr, 1450, 1950, 330, 1.2)
        bottles(fr, 1480, 330, 1.1)
        glow(fr, 250, 120, 600, (70, 60, 30), 0.8)
        fr = blur_frame(fr, 5.0)
    elif shot == 4:
        vgrad(fr, 0, 1080, (255, 226, 204), (250, 206, 186))
        tiles(fr, 0, 640, W, 1080, 96, (255, 236, 222), (255, 226, 210), (255, 244, 236), bevel=5)
        shape(fr, ('rrect', (-20, 622, W + 20, 648, 12)), (250, 190, 170), bevel=6, spec=0.3)
        # wall lamp + picture frame
        shape(fr, ('rrect', (1560, 120, 1840, 360, 30)), (255, 250, 240), bevel=8, spec=0.3)
        shape(fr, ('rrect', (1586, 146, 1814, 334, 18)), None, 'flat', grad=((170, 220, 255), (210, 240, 255)))
        duck(fr, 1700, 270, 1.1)
        shape(fr, ('rrect', (300, 160, 360, 240, 20)), (250, 200, 120), bevel=6, spec=0.6)
        ball(fr, 330, 140, 70, 60, (255, 240, 190), spec=0.1, amb=0.95)
        glow(fr, 330, 150, 480, (90, 70, 30), 1.0)
        fr = blur_frame(fr, 4.0)
    elif shot == 5:
        vgrad(fr, 0, 1080, (66, 70, 150), (100, 88, 170))
        rng = np.random.default_rng(11)
        dots = [(x, y, 5) for x, y in zip(rng.uniform(0, W, 70), rng.uniform(0, 760, 70))]
        shape(fr, ('circles', dots), (130, 130, 210), 'flat', alpha=0.5)
        window(fr, 1440, 90, 1760, 420, night=True)
        for side in (-1, 1):  # curtains
            x = 1600 + side * 230
            shape(fr, ('rrect', (x - 70, 50, x + 70, 560, 50)), (200, 170, 240), bevel=20, spec=0.1)
        shape(fr, ('capsule', (1340, 50, 1860, 50, 10)), (230, 220, 250), bevel=3, spec=0.6)
        floor_checker(fr, 780, (120, 104, 180), (136, 118, 196), vp=(960, 200))
        shape(fr, ('ellipse', (960, 965, 420, 80)), (255, 170, 200), bevel=16, spec=0.1, amb=0.65)
        # bed (right)
        shape(fr, ('rrect', (1380, 470, 1980, 900, 120)), (160, 200, 255), bevel=20, spec=0.2)
        shape(fr, ('rrect', (1440, 520, 1720, 640, 60)), (250, 250, 255), bevel=18, spec=0.1)
        shape(fr, ('rrect', (1360, 640, 2000, 900, 70)), (255, 190, 214), bevel=24, spec=0.1)
        for (x, y) in ((1500, 720), (1640, 790), (1800, 720), (1880, 830)):
            shape(fr, ('star', (x, y, 24, 11, 5, 0.2)), (255, 228, 120), bevel=3, spec=0.3)
        # night-light table (left)
        shape(fr, ('rrect', (150, 640, 430, 860, 40)), (230, 200, 250), bevel=12, spec=0.3)
        shape(fr, ('rrect', (180, 860, 210, 940, 10)), (210, 180, 240), bevel=6)
        shape(fr, ('rrect', (370, 860, 400, 940, 10)), (210, 180, 240), bevel=6)
        fr = blur_frame(fr, 2.0)
    return fr


# --------------------------------------------------------------- shots ----
def shot1(fr, t):
    """Lilo runs in, waves; bubbles in the air."""
    st = song.mouth_open(t)
    u = smooth((t - 0.3) / 3.3)
    lx, ly, ls = lerp(215, 960, u), lerp(790, 935, u), lerp(0.62, 1.0, u)
    ub = smooth((t - 0.9) / 3.2)
    bx, by, bs = lerp(220, 680, ub), lerp(785, 915, ub), lerp(0.5, 0.86, ub)
    running = 0.3 < t < 3.6
    brun = 0.9 < t < 4.1
    sp = pulse(t, song.SPLASH_WORDS, 0.5)
    hop = 14 * math.sin(math.pi * min(1, sp * 1.0)) if sp > 0 else 0
    bobo(fr, bx, by, bs, jump=(abs(math.sin(t * 9)) * 18 if brun else 6 * abs(math.sin(math.pi * beat_phase(t))) + hop),
         trunk=0.75 * sp + (0.25 if not brun else 0.1), ear=t * 7, mouth=0.5 if sp > 0 else 0.0,
         blink=blink(t, 1.3), happy=sp > 0.2, look=(-0.5, 0))
    if running:
        ph = t * 2 * math.pi * 1.6
        lilo(fr, lx, ly, ls, run=ph, bob=abs(math.sin(ph)) * 12, mouth=0.35, blink=blink(t),
             lh=(-70 - 18 * math.cos(ph), -150 - 12 * math.sin(ph)), rh=(70 + 18 * math.cos(ph), -150 + 12 * math.sin(ph)))
    else:
        if sp > 0:
            lh, rh = (-108, -360), (108, -360)
        elif t < 7.0:
            w = math.sin(t * 2 * math.pi * 1.7)
            lh, rh = (-72, -140), (118 + 16 * w, -352 + 6 * abs(w))
        else:
            lh, rh = (-72, -140), (72, -140)
        lilo(fr, lx, ly, ls, mouth=st, bob=hop, blink=blink(t), happy=sp > 0.3 and st < 0.2, lh=lh, rh=rh,
             look=(0, 0))
    draw_bubbles(fr, t, 0)


def shot2(fr, t):
    a, b = song.SHOTS[1]
    k = (t - a) / (b - a)
    st = song.mouth_open(t)
    # characters behind the tub
    bp = beat_phase(t)
    jump = 120 * math.sin(math.pi * ((t - a) % (2 * song.BEAT)) / (2 * song.BEAT)) ** 2
    bobo(fr, 600, 700, 1.05, jump=jump, trunk=0.6 + 0.4 * math.sin(t * 5), ear=t * 9, mouth=0.6, happy=jump > 80,
         blink=blink(t, 0.7), shadow=False)
    sep = 12 + 40 * abs(math.sin(math.pi * bp))
    lilo(fr, 1370, 705, 1.25, outfit='overalls', mouth=st, lh=(-sep, -228), rh=(sep, -228), shadow=False,
         blink=blink(t, 2.0), happy=(bp < 0.12 and st < 0.3))
    if bp < 0.15:
        for kk in range(3):
            ang = -math.pi / 2 + (kk - 1) * 0.7
            sparkle(fr, 1370 + 70 * math.cos(ang), 705 - 1.25 * 228 + 70 * math.sin(ang), 12 * (1 - bp / 0.15), alpha=1 - bp / 0.15)
    level = lerp(795, 680, smooth(k * 1.05))
    tub(fr, 960, 700, 830, 125, 700, part='back', level=level, t=t, foam=min(1, 0.25 + k * 1.2), foam_rows=2 + int(k * 2))
    tub(fr, 960, 700, 830, 125, 700, part='front', feet=False)
    # faucet + stream
    shape(fr, ('path', ([(330, 620), (330, 530), (370, 502), (418, 512), (436, 540)], [24, 18, 17, 16, 14])),
          (214, 224, 240), bevel=6, spec=1.0, gloss=100, amb=0.5)
    ball(fr, 270, 610, 20, 16, (255, 150, 170), spec=0.8)
    ball(fr, 390, 610, 20, 16, (130, 190, 255), spec=0.8)
    wob = [(436 + 3 * math.sin(t * 30 + y * 0.05), y) for y in np.linspace(550, level, 8)]
    shape(fr, ('path', (wob, 11)), (215, 240, 255), 'flat', alpha=0.75)
    shape(fr, ('path', ([(p[0] - 4, p[1]) for p in wob], 3)), (255, 255, 255), 'flat', alpha=0.8)
    for i in range(6):
        ang = math.pi + i * math.pi / 5
        rr = 30 + 10 * math.sin(t * 20 + i)
        ball(fr, 436 + rr * math.cos(ang), level - 6 + 0.35 * rr * math.sin(ang), 8, 7, (230, 245, 255), spec=0.8, alpha=0.9)
    draw_bubbles(fr, t, 1)


def shot3(fr, t):
    a, b = song.SHOTS[2]
    L3, L4, L5, L6 = (song.line_start(i) for i in (2, 3, 4, 5))
    st = song.mouth_open(t)
    cx, cy = 900, 640
    level = 600
    tub(fr, cx, cy, 640, 110, 260, part='back', level=None)
    # Lilo's pose by section
    quack = pulse(t, song.QUACKS, 0.35)
    spray_on = song.SPRAY[0] <= t <= song.SPRAY[1] + 0.8
    lh, rh = (-95, -120), (95, -120)
    happy = False
    bob = 0.0
    duck_pos = (650, 612)
    if t < L4:
        dpx = 650 + 20 * math.sin(t * 1.5)
        duck_pos = (dpx, 612 - 10 * quack)
        hx = (dpx - 900) / 1.2 + 20
        lh = (hx, -150 + 30 * quack)
        rh = (95, -150)
    elif t < L5:
        lh, rh = (-110, -330), (110, -330)
        happy = st < 0.15
        bob = 4 * math.sin(t * 12)
    elif t < L6:
        wash = pulse(t, song.WASH_S3, 0.6)
        scrub_on = any(0 <= t - s < song.BEAT for s in song.SCRUB_S3)
        if scrub_on:
            w = math.sin(t * 2 * math.pi * 2.5)
            lh, rh = (-30 + 25 * w, -215), (60 - 20 * w, -190)
        else:
            up = 1 - wash
            lh, rh = (-115, -110 - 120 * up * (wash > 0)), (115, -110 - 120 * up * (wash > 0))
    else:
        sway = math.sin((t - L6) * math.pi / song.BEAT)
        lh, rh = (-115 + 10 * sway, -300), (115 + 10 * sway, -300)
        bob = 0
    lean = 10 * math.sin((t - L6) * math.pi / song.BEAT) if t >= L6 else 0
    lilo(fr, cx, 762, 1.2, outfit='bath', mouth=st, lh=lh, rh=rh, happy=happy, blink=blink(t, 0.4),
         bob=bob, lean=lean, look=(-0.5, 0.3) if t < L4 else (0, 0))
    water_surface(fr, cx, cy + 110 * 0.07, 640 * 0.95, 110 * 0.8, level, t, 1.0, 3)
    # toys
    duck(fr, duck_pos[0], duck_pos[1] + 3 * math.sin(t * 2.5), 1.05, squeeze=quack)
    if quack > 0:
        al = min(1, quack * 3)
        speech(fr, duck_pos[0] - 70, duck_pos[1] - 120, 1.25, al)
        shape(fr, ('text', (duck_pos[0] - 70, duck_pos[1] - 122, 'Quack!', 40)), (255, 130, 30), bevel=1.5,
              spec=0.4, amb=0.8, alpha=al)
    bx = 1180 if t < L6 else lerp(1180, 1290, smooth((t - L6) / 4))
    boat(fr, bx, 618 + 4 * math.sin(t * 2 + 1), 1.0)
    if t < song.FROG_HOP:
        fpos = (500, 640)
    else:
        u = min(1, (t - song.FROG_HOP) / 0.5)
        fpos = (lerp(500, 600, u), lerp(640, 630, u) - 150 * math.sin(math.pi * u))
    frog(fr, fpos[0], fpos[1] + 3 * math.sin(t * 2.2 + 2), 0.95, blink=blink(t, 2.2))
    # splashes when she slaps the water
    pts = []
    for s in song.WASH_S3 + [song.FROG_HOP + 0.5]:
        age = t - s
        if 0 <= age < 0.6:
            rng = np.random.default_rng(int(s * 100))
            xs = [900 - 140, 900 + 140] if s != song.FROG_HOP + 0.5 else [600]
            for x0 in xs:
                for _ in range(9):
                    vx, vy = rng.uniform(-200, 200), rng.uniform(-620, -380)
                    pts.append((x0 + vx * age, level - 5 + vy * age + 1500 * age * age, rng.uniform(0.6, 1.2)))
    tub(fr, cx, cy, 640, 110, 260, part='front', feet=True)
    # Bobo beside the tub, trunk shower
    trunk = 0.0
    if spray_on:
        trunk = smooth((t - song.SPRAY[0] + 0.3) / 0.4) * (1 - smooth((t - song.SPRAY[1]) / 0.6))
    elif t >= L6:
        trunk = 0.5 + 0.5 * math.sin(t * 4)
    tip = bobo(fr, 1600, 990, 0.95, trunk=trunk, ear=t * 6, mouth=0.4 if spray_on else 0.0, blink=blink(t, 1.7),
               happy=(t >= L5 and t < L6), look=(-1, -0.5), jump=6 * abs(math.sin(math.pi * beat_phase(t))))
    if spray_on:
        rng = np.random.default_rng(5)
        ts = song.SPRAY[0]
        while ts < min(t, song.SPRAY[1]):
            age = t - ts
            jx, jy = rng.uniform(-70, 70), rng.uniform(-90, 60)
            if age < 1.25:
                x = tip[0] + (-760 + jx) * age
                y = tip[1] + (-1020 + jy) * age + 0.5 * 1100 * age * age
                pts.append((x, y, rng.uniform(0.5, 1.1)))
            ts += 1 / 70
    drops(fr, pts)
    draw_bubbles(fr, t, 2)


def shot4(fr, t):
    a, b = song.SHOTS[3]
    L7, L8, L9 = (song.line_start(i) for i in (6, 7, 8))
    st = song.mouth_open(t)
    crown = smooth((t - (a + 0.3)) / 5.5)
    if t < L8:
        w = math.sin(t * 2 * math.pi * 1.666)
        lh, rh = (-78 + 6 * w, -320 + 14 * w), (78 - 6 * w, -320 - 14 * w)
    elif t < L9:
        sway = math.sin((t - L8) * math.pi / song.BEAT)
        lh, rh = (-90, -150 + 10 * sway), (90, -150 - 10 * sway)
    else:
        lh, rh = (-90, -150), (100, -400)
    lean = 12 * math.sin((t - L8) * math.pi / song.BEAT) if L8 <= t < L9 else 0
    lilo(fr, 960, 1215, 2.3, outfit='bath', mouth=st, lh=lh, rh=rh, crown=crown, crown_t=t, blink=blink(t, 1.1),
         happy=(L8 <= t < L9 and st < 0.1), lean=lean)
    # foam + tub rim across the bottom
    circles = [(x, 800 + 16 * math.sin(x * 0.02 + t * 2), 54 + 12 * math.sin(x * 0.05)) for x in range(-40, 1990, 64)]
    circles += [(x + 30, 870 + 12 * math.sin(x * 0.03 + t * 1.7), 50 + 10 * math.sin(x * 0.07)) for x in range(-40, 1990, 70)]
    shape(fr, ('rect', (0, 800, W, H)), (160, 210, 245), 'flat')
    shape(fr, ('circles', circles), (252, 252, 255), bevel=10, spec=0.5, amb=0.75)
    shape(fr, ('rrect', (-100, 935, W + 100, 1200, 60)), (250, 251, 255), bevel=22, spec=0.5, amb=0.65)
    for i, (x, y, r) in enumerate(circles[::3]):
        bubble(fr, x, y - r * 0.5, r * 0.45, phase=i * 0.21 + t * 0.2)
    draw_bubbles(fr, t, 3, sparkles=True)


def shot5(fr, t):
    a, b = song.SHOTS[4]
    st = song.mouth_open(t)
    rubk = math.sin((t - a) * 2 * math.pi * 1.4)
    lh = (-160 + 8 * rubk, -330 + 16 * rubk)      # one hand rubs the hood
    rh = (95, -60)
    mom(fr, 1180, 960, 1.45, lh, rh, t=t, part='all')
    L11 = song.line_start(10)
    hug = t >= L11
    lilo(fr, 830, 1065, 1.35, outfit='towel', mouth=st, hood=t, blink=blink(t, 0.3), happy=(hug and st < 0.15),
         lean=6 * rubk)
    mom(fr, 1180, 960, 1.45, lh, rh, t=t, part='hands')
    bobo(fr, 560, 935, 0.9, towel=True, ear=t * 4, blink=blink(t, 2.4), happy=hug, look=(1, -0.5),
         jump=4 * abs(math.sin(math.pi * beat_phase(t))))


STAR_POS = [(250, 180), (560, 110), (880, 210), (1160, 120), (420, 360), (720, 330), (1060, 300),
            (1290, 220), (120, 420), (980, 420), (620, 500), (300, 560)]


def shot6(fr, t):
    a, b = song.SHOTS[5]
    st = song.mouth_open(t)
    # projected stars appear one by one
    for i, ((x, y), ts) in enumerate(zip(STAR_POS, song.STAR_TIMES)):
        if t < ts:
            continue
        age = t - ts
        k = min(1.0, age / 0.35)
        sc = 1 + 0.35 * math.sin(math.pi * k) if k < 1 else 1.0
        tw = 0.85 + 0.15 * math.sin(t * 3 + i * 1.7)
        glow(fr, x, y, 90, (120, 110, 50), 0.9 * tw)
        shape(fr, ('star', (x, y, 30 * sc * tw, 13 * sc * tw, 5, 0.3 * math.sin(i))), (255, 232, 120), bevel=3, spec=0.4, amb=0.9)
        if age < 0.5:
            sparkle(fr, x + 34, y - 30, 14 * (1 - age / 0.5), alpha=1 - age / 0.5)
    # night light (moon lamp)
    ball(fr, 290, 560, 74, 74, (255, 236, 160), spec=0.1, amb=1.0, rim=0)
    glow(fr, 290, 560, 300, (120, 100, 40), 1.0 + 0.08 * math.sin(t * 2))
    shape(fr, ('rrect', (250, 630, 330, 645, 6)), (230, 200, 250), bevel=3)
    ending = t > song.line_start(11) + 2 * song.BAR
    w = math.sin(t * 2 * math.pi * 1.4)
    lilo(fr, 860, 960, 1.15, outfit='pajamas', mouth=st, lh=(-72, -140), rh=(118 + 16 * w, -352 + 6 * abs(w)),
         blink=blink(t, 0.9), happy=ending and st < 0.1)
    bobo(fr, 1160, 965, 0.95, trunk=0.5 + 0.5 * math.sin(t * 2 * math.pi * 0.7), trunk_wave=w, ear=t * 4,
         blink=blink(t, 2.1), happy=ending, look=(-1, 0))


SHOT_FUNCS = [shot1, shot2, shot3, shot4, shot5, shot6]

# camera keyframes per shot: (t, cx, cy, zoom)
CAMS = [
    [(0, 960, 540, 1.0), (3.6, 960, 560, 1.0), (9.6, 930, 640, 1.2)],
    [(S[1][0], 960, 540, 1.0), (S[1][1], 1000, 520, 1.08)],
    [(S[2][0], 920, 560, 1.0), (song.line_start(3) - 0.5, 820, 500, 1.13), (song.line_start(3) + 0.8, 1040, 600, 1.0),
     (song.line_start(4), 1040, 600, 1.0), (song.line_start(5) - 0.6, 900, 480, 1.16), (S[2][1], 900, 520, 1.05)],
    [(S[3][0], 960, 540, 1.0), (song.line_start(7), 960, 520, 1.08), (S[3][1], 960, 500, 1.14)],
    [(S[4][0], 860, 560, 1.02), (S[4][1], 840, 580, 1.12)],
    [(S[5][0], 980, 700, 1.32), (S[5][0] + 1.5, 980, 700, 1.32), (S[5][1] - 1.5, 960, 540, 1.0)],
]

GRADES = [
    dict(mul=(1.04, 1.0, 0.95), bloom=0.22, vig=0.18, sat=1.08, light=((1.0, 0.97, 0.90), (0.90, 0.93, 1.0), (1.0, 0.95, 0.85))),
    dict(mul=(1.04, 1.0, 0.95), bloom=0.25, vig=0.18, sat=1.08, light=((1.0, 0.97, 0.90), (0.90, 0.93, 1.0), (1.0, 0.95, 0.85))),
    dict(mul=(1.04, 1.0, 0.95), bloom=0.22, vig=0.18, sat=1.08, light=((1.0, 0.97, 0.90), (0.90, 0.93, 1.0), (1.0, 0.95, 0.85))),
    dict(mul=(1.04, 1.0, 0.95), bloom=0.28, vig=0.2, sat=1.08, light=((1.0, 0.97, 0.90), (0.90, 0.93, 1.0), (1.0, 0.95, 0.85))),
    dict(mul=(1.07, 0.99, 0.90), bloom=0.3, vig=0.22, sat=1.06, light=((1.0, 0.9, 0.78), (0.95, 0.88, 0.9), (1.0, 0.85, 0.7))),
    dict(mul=(0.97, 0.96, 1.03), bloom=0.32, vig=0.26, sat=1.05, light=((1.0, 0.94, 0.84), (0.88, 0.85, 1.0), (1.0, 0.85, 0.6))),
]


def render_world(t):
    shot = song.shot_at(t)
    set_lighting(*GRADES[shot]['light'])
    fr = background(shot)
    SHOT_FUNCS[shot](fr, t)
    cam = keys(t, CAMS[shot])
    return fr, cam, shot
