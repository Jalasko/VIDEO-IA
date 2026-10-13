"""Farm set, staging and camera for every shot of « La dernière pomme ».
Screen space is a vertical 1080x1920 virtual canvas."""
import json
import math
import os
import numpy as np

from bath_time import gfx
gfx.configure(1080, 1920)
from bath_time.gfx import (Frame, shape, ball, glow, sparkle, vgrad, blur_frame, soft_shadow, set_lighting, Local)
from . import story
from .chars import gaston, mimi, bernard, pico, apple

W, H = 1080, 1920
META = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'farm_voice.json')


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return a + (b - a) * u


def keys(t, ks):
    if t <= ks[0][0]:
        return ks[0][1:]
    for a, b in zip(ks[:-1], ks[1:]):
        if t <= b[0]:
            u = smooth((t - a[0]) / (b[0] - a[0]))
            return tuple(lerp(p, q, u) for p, q in zip(a[1:], b[1:]))
    return ks[-1][1:]


def blink(t, seed=0.0, period=3.1):
    return ((t + seed) % period) < 0.12


def pulse(t, t0, width):
    return max(0.0, 1 - abs(t - t0) / width) if abs(t - t0) < width else 0.0


# ------------------------------------------------------------ lip sync ----
_ENV = None


def mouth(who, t):
    global _ENV
    if _ENV is None:
        with open(META) as f:
            _ENV = json.load(f)['env']
    e = _ENV[who]
    i = int(t * story.FPS)
    return float(e[i]) if 0 <= i < len(e) else 0.0


# ----------------------------------------------------------------- set ----
_BG = {}


def farm_bg(cx, cy, s, blur=1.5):
    key = (round(cx), round(cy), round(s, 3), blur)
    if key not in _BG:
        _BG[key] = np.clip(_farm(cx, cy, s, blur).a, 0, 255).astype(np.uint8)
    return Frame(_BG[key].astype(np.float32))


def _farm(cx, cy, s, blur):
    X = lambda fx: 540 + (fx - cx) * s
    Y = lambda fy: 960 + (fy - cy) * s
    fr = Frame.solid((255, 226, 170))
    hz = Y(820)
    vgrad(fr, 0, max(min(hz + 40, H), 1), (255, 184, 104), (255, 236, 186))
    sx, sy = X(260), Y(400)
    glow(fr, sx, sy, 700 * s, (255, 200, 110), 0.9)
    ball(fr, sx, sy, 90 * s, 90 * s, (255, 246, 200), spec=0, amb=1.0, rim=0)
    for (ux, uy, k) in ((600, 260, 1.0), (950, 420, 0.8), (-150, 300, 0.9)):
        px, py = X(ux), Y(uy)
        shape(fr, ('circles', [(px - 70 * k * s, py, 50 * k * s), (px, py - 30 * k * s, 70 * k * s), (px + 75 * k * s, py, 52 * k * s),
                               (px, py + 14 * k * s, 56 * k * s)]), (255, 248, 236), bevel=14 * s, spec=0.05, amb=0.85)
    shape(fr, ('ellipse', (X(150), Y(880), 820 * s, 180 * s)), (170, 206, 110), bevel=30 * s, spec=0.05, amb=0.75)
    shape(fr, ('ellipse', (X(1000), Y(890), 900 * s, 200 * s)), (150, 196, 96), bevel=30 * s, spec=0.05, amb=0.72)
    vgrad(fr, max(Y(860), 0), H, (162, 206, 86), (118, 172, 58))
    # barn
    shape(fr, ('rect', (X(40), Y(540), X(520), Y(920))), (214, 62, 52), bevel=10 * s, spec=0.2)
    for k in range(1, 9):
        shape(fr, ('rect', (X(40 + k * 53), Y(545), X(42 + k * 53), Y(915))), (170, 40, 36), 'flat', alpha=0.5)
    shape(fr, ('poly', [(X(10), Y(552)), (X(280), Y(370)), (X(550), Y(552))]), (160, 40, 40), bevel=12 * s, spec=0.3)
    shape(fr, ('line', ([(X(10), Y(552)), (X(280), Y(370)), (X(550), Y(552))], 16 * s)), (250, 246, 236), bevel=4 * s)
    shape(fr, ('rrect', (X(190), Y(690), X(370), Y(920), 8 * s)), (186, 50, 44), bevel=8 * s, spec=0.2)
    shape(fr, [('rect', (X(190), Y(690), X(370), Y(704))), ('rect', (X(190), Y(906), X(370), Y(920))),
               ('rect', (X(190), Y(690), X(204), Y(920))), ('rect', (X(356), Y(690), X(370), Y(920))),
               ('line', ([(X(198), Y(698)), (X(362), Y(912))], 12 * s)), ('line', ([(X(362), Y(698)), (X(198), Y(912))], 12 * s))],
          (250, 246, 236), bevel=3 * s, spec=0.3)
    shape(fr, ('rrect', (X(240), Y(470), X(320), Y(540), 6 * s)), (250, 246, 236), bevel=4 * s)
    shape(fr, ('rrect', (X(252), Y(482), X(308), Y(530), 4 * s)), (240, 196, 90), bevel=3 * s)
    # haystack
    shape(fr, ('circles', [(X(-60), Y(960), 110 * s), (X(40), Y(930), 130 * s), (X(150), Y(965), 100 * s)]),
          (244, 204, 90), bevel=16 * s, spec=0.15)
    # apple tree
    shape(fr, ('path', ([(X(890), Y(1000)), (X(870), Y(820)), (X(890), Y(640))], [52 * s, 42 * s, 34 * s])), (140, 96, 60),
          bevel=12 * s, spec=0.2)
    shape(fr, ('path', ([(X(880), Y(760)), (X(980), Y(680))], [20 * s, 12 * s])), (140, 96, 60), bevel=6 * s)
    leaves = [(880, 520, 200), (720, 580, 150), (1040, 580, 160), (800, 400, 160), (980, 400, 150), (890, 300, 130),
              (700, 460, 110), (1080, 470, 110)]
    shape(fr, ('circles', [(X(a), Y(b), r * s) for a, b, r in leaves]), (86, 168, 66), bevel=24 * s, spec=0.2, amb=0.55)
    shape(fr, ('circles', [(X(a - 30), Y(b - 40), r * 0.55 * s) for a, b, r in leaves]), (120, 196, 84), bevel=16 * s,
          spec=0.2, alpha=0.8)
    for (a, b) in ((760, 620), (980, 640), (850, 470), (1050, 520), (700, 520)):
        ball(fr, X(a), Y(b), 22 * s, 22 * s, (225, 36, 44), spec=0.8)
    # fence
    posts = [('rrect', (X(fx - 18), Y(960), X(fx + 18), Y(1100), 6 * s)) for fx in range(-600, 1800, 150)]
    shape(fr, posts, (200, 150, 96), bevel=6 * s, spec=0.2)
    shape(fr, [('rrect', (X(-650), Y(990), X(1850), Y(1014), 6 * s)), ('rrect', (X(-650), Y(1044), X(1850), Y(1068), 6 * s))],
          (214, 164, 106), bevel=5 * s, spec=0.25)
    # yard dirt + tufts
    shape(fr, ('ellipse', (X(540), Y(1430), 560 * s, 230 * s)), (226, 196, 136), 'flat', alpha=0.9, blur=30 * s)
    rng = np.random.default_rng(3)
    tufts = []
    for _ in range(60):
        fx, fy = rng.uniform(-500, 1600), rng.uniform(1120, 2300)
        if ((fx - 540) / 560) ** 2 + ((fy - 1430) / 230) ** 2 < 1:
            continue
        h = rng.uniform(16, 30)
        tufts.append(('poly', [(X(fx - 10), Y(fy)), (X(fx - 4), Y(fy - h)), (X(fx), Y(fy - 4)), (X(fx + 5), Y(fy - h * 0.9)),
                               (X(fx + 10), Y(fy))]))
    shape(fr, tufts, (104, 160, 50), bevel=2 * s, spec=0.1)
    for _ in range(25):
        fx, fy = rng.uniform(-400, 1500), rng.uniform(1150, 2200)
        ball(fr, X(fx), Y(fy), 7 * s, 7 * s, [(255, 255, 255), (255, 220, 80), (255, 150, 190)][_ % 3], spec=0.3)
    return blur_frame(fr, blur) if blur else fr


def speed_lines(fr, cx, cy, t, col=(255, 240, 200), n=26, alpha=0.5):
    rng = np.random.default_rng(int(t * 12))
    items = []
    for k in range(n):
        a = k / n * 2 * math.pi + rng.uniform(-0.05, 0.05)
        r0, r1 = rng.uniform(380, 520), 1500
        w = rng.uniform(0.012, 0.03)
        items.append(('poly', [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                               (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w)),
                               (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))]))
    shape(fr, items, col, 'flat', alpha=alpha)


def dust(fr, x, y, k, t, seed=0, col=(236, 214, 170)):
    """Dust puff of size k (0..1) expanding with t (0..1)."""
    if k <= 0:
        return
    rng = np.random.default_rng(seed)
    circles = []
    for i in range(10):
        a = rng.uniform(math.pi, 2 * math.pi) if i < 7 else rng.uniform(0, math.pi)
        d = (40 + 120 * t) * k * rng.uniform(0.6, 1.2)
        circles.append((x + d * math.cos(a) * 1.6, y + d * math.sin(a) * 0.6, (30 + 30 * t) * k * rng.uniform(0.7, 1.2)))
    shape(fr, ('circles', circles), col, bevel=10 * k, spec=0.05, amb=0.75, alpha=max(0, 1 - t))


def feathers(fr, t, t0, x, y, n=8, spread=500, seed=1):
    age = t - t0
    if age < 0 or age > 2.2:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        vx, vy = rng.uniform(-1, 1) * spread, rng.uniform(-1.2, -0.3) * spread
        px = x + vx * age + 30 * math.sin(age * 5 + i)
        py = y + vy * age + 260 * age * age
        a = age * 4 + i
        L = Local(fr, px, py, 1.0)
        L.shape(('poly', [(-26 * math.cos(a), -26 * math.sin(a)), (8 * math.sin(a), -8 * math.cos(a)),
                          (26 * math.cos(a), 26 * math.sin(a)), (-8 * math.sin(a), 8 * math.cos(a))]),
                (252, 252, 248), bevel=3, spec=0.2, alpha=max(0, 1 - age / 2.2))


def comic(fr, x, y, text, size, t, col=(255, 220, 60)):
    k = 1 + 0.15 * math.sin(t * 20)
    shape(fr, ('star', (x, y, size * 1.9 * k, size * 1.25 * k, 10, t)), (255, 255, 255), bevel=4, spec=0.1, amb=0.9)
    shape(fr, ('star', (x, y, size * 1.7 * k, size * 1.1 * k, 10, t)), (255, 90, 60), bevel=4, spec=0.2, amb=0.8)
    shape(fr, ('text', (x, y, text, size * k)), col, bevel=2, spec=0.4, amb=0.85)


# ---------------------------------------------------------------- shots ----
def s_apple_fall(t):
    fr = farm_bg(880, 470, 2.6, blur=7)
    u = t / (story.APPLE_LAND - 0.15)
    y = lerp(-260, 1650, u ** 1.6)
    for k in (3, 2, 1):                    # slow-motion trail
        apple(fr, 540, y - 70 * k, 240, rot=t * 2, alpha=0.12 * (4 - k) / 3)
    apple(fr, 540, y, 240, rot=t * 2)
    rng = np.random.default_rng(9)
    for i in range(6):
        lx = rng.uniform(80, 1000) + 60 * math.sin(t * 1.5 + i)
        ly = (rng.uniform(-200, 1900) + 260 * t) % 2100 - 100
        a = t * 1.3 + i
        Local(fr, lx, ly, 1.0).shape(('poly', [(-40 * math.cos(a), -40 * math.sin(a)), (12 * math.sin(a), -12 * math.cos(a)),
                                              (40 * math.cos(a), 40 * math.sin(a))]), (100, 186, 72), bevel=5, spec=0.3)
    return fr, (540, 960, 1.0 + 0.05 * u, 0)


GROUP = dict(g=(210, 1395, 0.6), m=(470, 1690, 0.58), b=(860, 1400, 0.55))
APPLE_SPOT = (600, 1500)


def _trio(fr, t, eyes_wide=1.0, look=(0, 0.5), shock=0.0, lids=True):
    gx, gy, gs = GROUP['g']
    mx, my, ms = GROUP['m']
    bx, by, bs = GROUP['b']
    bernard(fr, bx, by, bs, wide=eyes_wide, lid=0.0 if eyes_wide > 1.05 else 0.5, look=look, brow=0.2, ears=0.3,
            shock=shock, fx=-1)
    gaston(fr, gx, gy, gs, wide=eyes_wide, look=look, brow=0.1, shock=shock)
    mimi(fr, mx, my, ms, wide=eyes_wide, lid=0.0 if eyes_wide > 1.05 else 0.35, look=(look[0], -0.6), shock=shock)


def s_apple_land(t):
    fr = farm_bg(540, 1150, 1.0)
    ax, ay = APPLE_SPOT
    a0 = story.APPLE_LAND
    if t < a0:
        y = lerp(-150, ay, (t - (a0 - 0.15)) / 0.15)
        _trio(fr, t, 1.0, look=(0.5, -1))
        apple(fr, ax, y, 60)
    else:
        b = t - a0
        y = ay - 60 * abs(math.sin(b * 9)) * math.exp(-b * 6)
        _trio(fr, t, 1.45, look=(0.3, 0.6))
        soft_shadow(fr, ax, ay + 50, 50, 10, 0.3)
        apple(fr, ax, y, 60)
        dust(fr, ax, ay + 50, 1.0, min(1, b / 0.6), seed=1)
    return fr, (560, 1450, 1.45, 0)


def s_freeze(t, who):
    fr = farm_bg(540, 1150, 1.0, blur=10)
    a = [s for s in story.SHOTS if s[2] == 'freeze_' + who][0][0]
    k = t - a
    speed_lines(fr, 540, 900, a, alpha=0.45)
    if who == 'gaston':
        gaston(fr, 540, 1900, 2.6, wide=1.5, look=(0.2, 0.6), brow=-0.2, shadow=False)
        cy = 1900 - 2.6 * 400
    elif who == 'mimi':
        mimi(fr, 540, 1760, 2.7, wide=1.5, lid=0.0, look=(0.2, 0.6), brow=-0.3, shadow=False)
        cy = 1760 - 2.7 * 290
    else:
        bernard(fr, 540, 2050, 2.1, wide=1.45, lid=0.0, look=(-0.2, 0.6), brow=-0.3, ears=0.8, shadow=False)
        cy = 2050 - 2.1 * 470
    return fr, (540, cy + 60, 1.0 + 0.12 * smooth(k / 0.12), 0)


def s_gaston(t):
    fr = farm_bg(540, 1250, 1.3, blur=4)
    a = story.GASTON_JUMP
    u = smooth((t - a) / 0.75)
    x = lerp(-250, 540, u)
    jump = 260 * math.sin(math.pi * min(1, (t - a) / 0.75)) if t < a + 0.75 else 0
    wings = smooth((t - a - 0.8) / 0.25)
    m = mouth('gaston', t)
    crow = pulse(t, 10.6, 0.9)
    flap = t * (18 if (crow > 0 or m > 0.2) else 6)
    gaston(fr, x, 1700, 1.45, mouth=m, wings=wings, flap=flap, brow=0.9 - 0.6 * crow, puff=1.0 + 0.12 * wings,
           jump=jump, lid=0.15 if crow < 0.3 else 0.6, look=(0, -0.3 - 0.6 * crow))
    if 5.85 < t < 6.6:
        for i in range(5):
            sparkle(fr, 540 + 300 * math.cos(i * 1.3 + t), 1100 + 200 * math.sin(i * 1.7 + t), 22, alpha=1 - (t - 5.85) / 0.75)
    apple(fr, 540, 1830, 120)
    feathers(fr, t, a + 0.75, 540, 1400, n=5, spread=300, seed=2)
    rot = -4 + 3 * math.sin(t * 0.8)
    return fr, keys(t, [(a, 540, 1100, 1.0, rot), (a + 0.8, 540, 1050, 1.0, rot), (story.MIMI_ENTER, 540, 1000, 1.12, rot)])


def s_mimi(t):
    fr = farm_bg(560, 1250, 1.3, blur=4)
    a, hb = story.MIMI_ENTER, story.HIP_BUMP
    # Gaston knocked out of frame at the hip bump
    if t < hb + 0.9:
        if t < hb:
            gaston(fr, 400, 1700, 1.45, mouth=0.0, wings=1.0 - smooth((t - a) / 0.4) * 0.6, flap=t * 6, brow=0.8,
                   look=(1, 0))
        else:
            u = (t - hb) / 0.9
            gaston(fr, lerp(400, -500, u), 1700 - 500 * math.sin(math.pi * u * 0.8), 1.45, shock=1.0, wide=1.4,
                   wings=1.0, flap=t * 30, brow=-0.6, shadow=False)
            feathers(fr, t, hb, 300, 1300, n=10, spread=600, seed=3)
    xin = lerp(1400, 640, smooth((t - a) / 0.9))
    hip = -1.0 * pulse(t, hb, 0.35)
    m = mouth('mimi', t)
    ear = smooth((t - story.EAR_FLIP) / 0.18) * (1 - smooth((t - story.EAR_FLIP - 0.6) / 0.3)) \
        + 0.3 * pulse(t, 18.2, 0.4)
    mimi(fr, xin, 1720, 1.55, mouth=m, hip=hip, ear=ear, lid=0.45 if m > 0.05 or t > 17.9 else 0.3,
         brow=0.3 if m > 0.05 else -0.1, look=(-0.4, 0) if t < 17.9 else (0.2, 0.2),
         stomp=(t * 9) if a < t < a + 0.9 else 0.0)
    if hb <= t < hb + 0.4:
        comic(fr, 260, 1150, "BOUM !", 70, t)
    if 17.95 < t < 18.6:
        sparkle(fr, 470, 1180, 30, alpha=1 - (t - 17.95) / 0.65)
    apple(fr, 360, 1840, 110)
    return fr, keys(t, [(a, 520, 1060, 1.0, 4), (hb, 520, 1060, 1.0, 4), (hb + 0.15, 540, 1070, 1.06, -3),
                        (story.BERNARD_ENTER, 600, 1020, 1.12, -2)])


def s_bernard(t):
    fr = farm_bg(520, 1230, 1.25, blur=4)
    a = story.BERNARD_ENTER
    u = min(1, (t - a) / 1.1)
    x = lerp(-300, 540, smooth(u))
    walk = (t - a) * 5 if u < 1 else None
    sigh = pulse(t, story.SIGH + 0.4, 0.6)
    m = mouth('bernard', t)
    bernard(fr, x, 1880, 1.15, mouth=m, lid=0.6 + 0.2 * sigh, brow=0.5, ears=0.15 - 0.15 * sigh, walk=walk,
            look=(0, 0.2))
    if story.SIGH < t < story.SIGH + 1.2:
        k = (t - story.SIGH) / 1.2
        dust(fr, x + 60, 1880 - 1.15 * 360, 0.6, k, seed=4, col=(250, 250, 250))
    apple(fr, 800, 1840, 105)
    return fr, keys(t, [(a, 540, 1100, 1.0, 0), (story.SIGH, 540, 1080, 1.03, 0), (28.0, 540, 1000, 1.14, 2)])


def s_argue_wide(t):
    fr = farm_bg(540, 1300, 1.15, blur=3)
    apple(fr, 540, 1820, 90)
    bernard(fr, 560, 1640, 0.85, mouth=mouth('bernard', t), lid=0.3, brow=1.0, ears=0.6, look=(0, 0.3))
    gaston(fr, 230, 1780, 1.05, mouth=mouth('gaston', t), wings=1.0, flap=t * 25, brow=1.0, look=(1, 0),
           jump=20 * abs(math.sin(t * 12)))
    mimi(fr, 860, 1820, 1.05, mouth=0.4, lid=0.3, brow=1.0, look=(-1, 0), fx=-1, stomp=t * 14)
    return fr, (540, 1250, 1.0, 9 + 2 * math.sin(t * 20))


def s_argue_mimi(t):
    fr = farm_bg(560, 1250, 1.6, blur=6)
    speed_lines(fr, 540, 900, t, col=(255, 160, 150), alpha=0.35)
    mimi(fr, 540, 1900, 2.3, mouth=mouth('mimi', t), lid=0.1, brow=1.0, ear=0.6, stomp=t * 16, look=(-0.6, 0), wide=1.1)
    sh = 8 * math.sin(t * 60)
    return fr, (540 + sh, 1150, 1.0, -7)


def s_argue_bernard(t):
    fr = farm_bg(560, 1250, 1.6, blur=6)
    br = smooth((t - story.BRAY) / 0.12) * (1 - smooth((t - story.BRAY - 0.8) / 0.15))
    speed_lines(fr, 540, 800, t, col=(255, 230, 160), alpha=0.4 * br)
    bernard(fr, 540, 2100, 1.9, bray=br, lid=0.0, wide=1.0 + 0.3 * br, brow=1.0, ears=br, look=(0, 0))
    if br > 0.3:
        comic(fr, 820, 520, "HI-HAN !", 64, t, col=(255, 250, 200))
    sh = 14 * br * math.sin(t * 70)
    return fr, (540 + sh, 1000 + sh, 1.0, 5)


POW = [("PAF !", 0.3), ("BIM !", 1.4), ("BOUM !", 2.6), ("PAF !", 3.9), ("BAM !", 5.1), ("BIM !", 6.2)]


def fight_cloud(fr, t, cx, cy, scale=1.0, alpha=1.0, limbs=True, seed=0):
    rng = np.random.default_rng(seed)
    circles = []
    for i in range(16):
        a = i / 16 * 2 * math.pi + t * 2.2 + rng.uniform(0, 0.3)
        d = (260 + 50 * math.sin(t * 7 + i * 1.3)) * scale
        r = (150 + 40 * math.sin(t * 9 + i * 2.1)) * scale
        circles.append((cx + d * math.cos(a), cy + d * 0.75 * math.sin(a), r))
    circles.append((cx, cy, 300 * scale))
    if limbs and alpha > 0.5:
        # bits of the fighters poking out of the cloud
        ph = int(t * 5) % 6
        L = Local(fr, cx, cy, scale)
        if ph in (0, 3):     # Gaston's wing
            L.shape(('path', ([(-300, -150), (-500, -300), (-640, -330)], [50, 44, 26])), (250, 248, 240), bevel=12, spec=0.3)
        if ph in (1, 4):     # Mimi's leg
            L.shape(('capsule', (350, 60, 600, 170, 34)), (255, 172, 196), bevel=10, spec=0.3)
            L.shape(('rrect', (585, 130, 650, 205, 12)), (110, 70, 80), bevel=5)
        if ph in (2, 5):     # Bernard's ear
            L.shape(('path', ([(-60, -320), (-120, -560), (-140, -640)], [30, 26, 16])), (150, 110, 80), bevel=8, spec=0.2)
        if ph in (0, 2, 4):  # a hoof
            L.shape(('capsule', (150, 300, 220, 580, 26)), (150, 110, 80), bevel=8)
            L.shape(('rrect', (190, 560, 256, 600, 10)), (60, 44, 36), bevel=4)
        if ph in (1, 3, 5):  # Gaston's crest
            L.shape(('circles', [(-200, -420, 34), (-160, -450, 40), (-115, -440, 34)]), (232, 38, 44), bevel=10, spec=0.5)
    shape(fr, ('circles', circles), (238, 216, 172), bevel=26 * scale, spec=0.08, amb=0.75, alpha=alpha)
    if alpha > 0.5:
        for i in range(5):
            a = t * 4 + i * 1.26
            sx, sy = cx + 330 * scale * math.cos(a), cy - 200 * scale + 120 * scale * math.sin(a)
            shape(fr, ('star', (sx, sy, 40 * scale, 18 * scale, 5, t * 6 + i)), (255, 224, 60), bevel=4, spec=0.5)
        for i in range(3):
            a0 = (t * 300 + i * 120) % 360
            shape(fr, ('arc', (cx + (i - 1) * 160 * scale, cy - 60 * scale, 70 * scale, 50 * scale, a0, a0 + 220, 10 * scale)),
                  (150, 110, 80), 'flat', alpha=0.6)


def s_fight(t):
    fr = farm_bg(540, 1250, 1.15, blur=3)
    a = story.CLOUD[0]
    k = smooth((t - a) / 0.5)
    fight_cloud(fr, t, 540, 1350, 0.4 + 0.6 * k)
    feathers(fr, t, a + 0.2, 540, 1200, n=8, spread=700, seed=5)
    feathers(fr, t, a + 3.2, 540, 1200, n=8, spread=700, seed=6)
    for txt, dt in POW:
        if 0 <= t - a - dt < 0.55:
            rng = np.random.default_rng(int(dt * 10))
            comic(fr, rng.uniform(250, 830), rng.uniform(800, 1100), txt, 70, t)
    apple(fr, 540, 1830, 95)
    sh = 10 * math.sin(t * 50)
    return fr, (540 + sh, 1250 + 0.7 * sh, 1.0 + 0.05 * math.sin(t * 2), 3 * math.sin(t * 3))


def s_pico(t):
    fr = farm_bg(560, 1300, 2.0, blur=8)
    fight_cloud(fr, t, 540, 820, 1.1, limbs=True, seed=2)
    blurred = blur_frame(fr, 5)
    fr = blurred
    a = story.PICO_ENTER
    ax, ay = 690, 1620
    l0, l1 = story.PICO_LOOK
    g, e = story.PICO_GRAB, story.PICO_EXIT
    head, look = 0.0, (0, 0)
    hands = 'sneak'
    crouch = 0.3
    tiptoe = None
    if t < l0:
        x = lerp(-150, 430, smooth((t - a) / (l0 - a)))
        tiptoe = (t - a) * 9
    elif t < g - 0.5:
        x = 430
        if t < l1:
            head, look = -1.0, (-1, 0)
        elif t < l1 + 0.6:
            head, look = 1.0, (1, 0)
        else:
            head, look = 0.0, (0.3, -0.3)
            x = lerp(430, 520, smooth((t - l1 - 0.6) / 0.5))
            tiptoe = t * 9
    elif t < e:
        x = 520
        hands = 'up' if t > g + 0.15 else 'hold'
        crouch = 0.6 * pulse(t, g, 0.3)
    else:
        x = lerp(520, 1350, smooth((t - e) / 1.6))
        hands = 'up'
        tiptoe = t * 11
    if t >= g:
        lift = smooth((t - g) / 0.4)
        apx, apy = x + 10, lerp(ay, 1620 - 1.9 * 210, lift)
    else:
        apx, apy = ax, ay
    if t < g:
        apple(fr, apx, apy, 120)
    pico(fr, x, 1740, 1.9, look=look, head=head, hands=hands, tiptoe=tiptoe, crouch=crouch, brow=0.6,
         wide=1.15 if l0 <= t < l1 + 0.6 else 1.0)
    if t >= g:
        apple(fr, apx, apy, 120)
    return fr, keys(t, [(a, 540, 1250, 1.0, 0), (l0, 480, 1300, 1.12, 0), (g, 600, 1300, 1.15, 0), (45, 760, 1250, 1.05, 0)])


def s_clear(t):
    fr = farm_bg(540, 1250, 1.15, blur=3)
    a = story.CLOUD_CLEAR
    k = smooth((t - a) / 1.0)
    look = (0, 1) if t > story.LOOK_DOWN else (0.6, -0.4)
    soft_shadow(fr, 540, 1780, 80, 16, 0.25)
    bernard(fr, 800, 1640, 0.8, bray=0.6 * (1 - k), lid=0.2, brow=0.3, ears=0.6, look=look, fx=-1,
            wide=1.0 + 0.2 * (t > story.LOOK_DOWN))
    gaston(fr, 260, 1720, 0.95, wings=1.0 - k * 0.7, flap=t * 6 * (1 - k), brow=0.3, look=look, feathers_lost=1.0,
           shock=0.3 * (t > story.LOOK_DOWN))
    mimi(fr, 560, 1880, 0.95, lid=0.1, brow=0.2, look=look, stomp=(t * 10) * (1 - k) if k < 0.9 else 0)
    if k < 1:
        fight_cloud(fr, t, 540, 1350, 1.0 + 0.4 * k, alpha=1 - k, limbs=False)
    return fr, (540, 1300, 1.0, 0)


def s_empty(t):
    fr = farm_bg(560, 1400, 2.4, blur=6)
    shape(fr, ('ellipse', (540, 1500, 170, 40)), (180, 150, 100), 'flat', alpha=0.5, blur=10)
    Local(fr, 600, 1470, 1.4).shape(('poly', [(-50, 0), (40, -30), (60, 10)]), (90, 180, 70), bevel=5, spec=0.3)
    return fr, (540, 1300, 1.0 + 0.04 * (t - 47.4), 0)


def s_turn(t):
    fr = farm_bg(540, 1250, 1.3, blur=4)
    a, b = story.HEAD_TURN
    k = smooth((t - a) / (b - a))
    look = (lerp(0, 1, k), lerp(0.8, -0.2, k))
    bl = blink(t, 0.4, 2.2)
    bernard(fr, 830, 1820, 0.9, lid=0.0 if not bl else 1.0, wide=1.1, brow=-0.2, ears=0.5, look=look, head_turn=k, fx=-1)
    gaston(fr, 250, 1860, 1.05, lid=1.0 if bl else 0.0, wide=1.1, brow=-0.2, look=look, feathers_lost=1.0)
    mimi(fr, 560, 2000, 1.05, lid=1.0 if bl else 0.0, wide=1.1, brow=-0.2, look=look)
    return fr, (540, 1250, 1.0 + 0.04 * (t - 48.6), 0)


def s_finale(t):
    fr = farm_bg(560, 1050, 1.0, blur=2)
    tf = min(t, story.FREEZE)
    bites = sum(1 for b in story.BITES if tf >= b)
    chew = abs(math.sin(tf * 14)) * 0.8 if any(0 < tf - b < 0.9 for b in story.BITES) else 0.0
    m = mouth('pico', tf)
    wink = 1 if story.WINK <= tf < story.WINK + 0.55 else None
    shock = smooth((tf - story.SHOCK) / 0.2)
    # Pico on top of a fence post
    px, py = 560, 980
    shape(fr, ('rrect', (px - 50, py - 10, px + 50, py + 170, 12)), (200, 150, 96), bevel=6, spec=0.2)
    pico(fr, px, py, 1.6, mouth=m, chew=chew, wink=wink, hands='down', look=(0.2, 0.1) if wink is None else (0, 0),
         brow=0.5, shadow=False)
    apple(fr, px + 92, py - 70, 58, bites=bites)      # held at his side, face stays visible
    if wink and tf - story.WINK < 0.5:
        sparkle(fr, px + 80, py - 300, 30, alpha=1 - (tf - story.WINK) / 0.5)
    look = (lerp(0.6, 0.3, shock), -0.8)
    gaston(fr, 190, 1700, 0.9, shock=shock, wide=1.0 + 0.5 * shock, brow=-0.5 * shock, look=look, feathers_lost=1.0)
    bernard(fr, 900, 1690, 0.75, shock=shock, wide=1.0 + 0.5 * shock, lid=0.5 * (1 - shock), brow=-0.4 * shock,
            ears=shock, look=(-0.6, -0.8), fx=-1)
    mimi(fr, 560, 1860, 0.95, shock=shock, wide=1.0 + 0.45 * shock, lid=0.3 * (1 - shock), brow=-0.4 * shock,
         look=(0, -1))
    z = 1.06 + 0.035 * (tf - 52)
    if t >= story.FREEZE:
        z += 0.1 * smooth((t - story.FREEZE) / 0.12)
    return fr, (560, 1150, z, 0)


FUNCS = dict(apple_fall=s_apple_fall, apple_land=s_apple_land,
             freeze_gaston=lambda t: s_freeze(t, 'gaston'), freeze_mimi=lambda t: s_freeze(t, 'mimi'),
             freeze_bernard=lambda t: s_freeze(t, 'bernard'), gaston=s_gaston, mimi=s_mimi, bernard=s_bernard,
             argue_wide=s_argue_wide, argue_mimi=s_argue_mimi, argue_bernard=s_argue_bernard, fight=s_fight,
             pico=s_pico, clear=s_clear, empty=s_empty, turn=s_turn, finale=s_finale)

GRADE = dict(mul=(1.06, 1.0, 0.9), sat=1.12, bloom=0.3, vig=0.22)


def render_world(t):
    set_lighting(key=(1.0, 0.92, 0.76), amb=(0.88, 0.86, 0.96), rim=(1.0, 0.88, 0.65))
    i = story.shot_at(t)
    name = story.SHOTS[i][2]
    fr, cam = FUNCS[name](t)
    return fr, cam, name
