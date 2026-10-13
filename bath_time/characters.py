"""Lilo, Bobo, Mom and the bath toys. One function per character so every shot
draws exactly the same design."""
import math
from .gfx import Local, ik, soft_shadow

# ---- palette (shared by every shot = consistent design) -------------------
SKIN = (255, 216, 192)
SKIN_D = (238, 170, 140)
HAIR = (128, 78, 44)
HAIR_D = (96, 56, 32)
YELLOW = (255, 212, 58)
STAR_RED = (238, 58, 62)
OVERALL = (78, 128, 228)
WHITE = (250, 250, 252)
IRIS = (96, 56, 32)
BLUSH = (255, 120, 140)
MOUTH = (150, 40, 58)
TONGUE = (255, 125, 140)
PJ = (176, 196, 255)
PJ_STAR = (255, 222, 90)
TOWEL_PINK = (255, 172, 204)
TOWEL_PINK_IN = (255, 214, 230)

ELE = (156, 206, 250)
ELE_D = (130, 182, 236)
EAR = (255, 172, 206)
EAR_IN = (255, 205, 226)
BOBO_TOWEL = (84, 150, 240)


def _eyes(L, ex, ey, rx, ry, look, blink, happy, iris=IRIS, lashes=True):
    lx, ly = look
    for side in (-1, 1):
        cx = ex * side
        if happy:
            L.flat(('arc', (cx, ey + ry * 0.4, rx * 0.9, ry * 0.8, 200, 340, 5.5)), (60, 34, 24))
            continue
        if blink:
            L.flat(('arc', (cx, ey - ry * 0.3, rx * 0.95, ry * 0.7, 25, 155, 5)), (60, 34, 24))
            continue
        L.ball(cx, ey, rx, ry, WHITE, spec=0.25, amb=0.8, rim=0.05)
        ix, iy = cx + lx * rx * 0.25, ey + ly * ry * 0.2 + ry * 0.08
        L.ball(ix, iy, rx * 0.72, ry * 0.74, iris, spec=0.1, amb=0.75, rim=0)
        L.ball(ix, iy + ry * 0.04, rx * 0.44, ry * 0.46, (20, 12, 10), spec=0, amb=1, rim=0)
        L.flat(('ellipse', (ix - rx * 0.28, iy - ry * 0.3, rx * 0.26, ry * 0.24)), WHITE)
        L.flat(('ellipse', (ix + rx * 0.24, iy + ry * 0.3, rx * 0.12, ry * 0.11)), WHITE)
        if lashes:
            o = side
            L.flat(('line', ([(cx + o * rx * 0.75, ey - ry * 0.62), (cx + o * rx * 1.15, ey - ry * 0.95)], 4)), (50, 28, 20))
            L.flat(('line', ([(cx + o * rx * 0.35, ey - ry * 0.92), (cx + o * rx * 0.55, ey - ry * 1.3)], 4)), (50, 28, 20))


def _mouth(L, cx, cy, mouth, smile=1.0, scale=1.0):
    if mouth > 0.06:
        mw = (17 + 9 * mouth) * scale
        mh = (7 + 21 * mouth) * scale
        L.shape([('ellipse', (cx, cy, mw, mh)), ('rect', (cx - mw - 2, cy - mh - 2, cx + mw + 2, cy), 'erase'),
                 ('rrect', (cx - mw, cy - 3 * scale, cx + mw, cy + 3 * scale, 3 * scale))],
                MOUTH, bevel=2, spec=0.15, rim=0)
        if mh > 11 * scale:
            L.shape([('ellipse', (cx, cy + mh * 0.78, mw * 0.55, mh * 0.32))], TONGUE, bevel=2, spec=0.2, rim=0)
        L.flat(('rrect', (cx - mw * 0.6, cy, cx + mw * 0.6, cy + 4 * scale, 2 * scale)), WHITE)
    else:
        w = (16 + 4 * smile) * scale
        L.flat(('arc', (cx, cy - 12 * scale * smile, w, 13 * scale * max(smile, 0.25), 25, 155, 4.5 * scale)), MOUTH)


# --------------------------------------------------------------- Lilo ----
def lilo(fr, x, y, s, outfit='overalls', lh=None, rh=None, run=None, bob=0.0, mouth=0.0,
         smile=1.0, blink=False, happy=False, look=(0, 0), crown=0.0, crown_t=0.0,
         shadow=True, hood=0.0, lean=0.0):
    """Lilo, anchored at the point between her feet. ~410px tall at s=1.
    lh/rh: hand targets (local coords) for her screen-left / screen-right hand.
    outfit: 'overalls' | 'pajamas' | 'towel' | 'bath'."""
    L = Local(fr, x + lean * s, y - bob * s, s)
    lh = lh or (-72, -138)
    rh = rh or (72, -138)
    pants = {'overalls': OVERALL, 'pajamas': PJ}.get(outfit)

    if shadow and outfit != 'bath':
        soft_shadow(fr, x, y + 4 * s, 78 * s, 15 * s, alpha=0.22)

    # ---- legs & feet
    if outfit in ('overalls', 'pajamas'):
        for side in (-1, 1):
            ph = 0 if run is None else run + (0 if side < 0 else math.pi)
            lift = 0 if run is None else 24 * max(0.0, math.sin(ph))
            swing = 0 if run is None else 12 * math.cos(ph)
            hip = (22 * side, -110)
            foot = (27 * side + swing, -26 - lift)
            L.shape(('capsule', (hip[0], hip[1], foot[0], foot[1], 21)), pants, bevel=7, spec=0.2)
            if outfit == 'overalls':
                L.shape(('ellipse', (foot[0] + 3 * side, foot[1] + 13, 31, 18)), WHITE, bevel=6, spec=0.5)
                L.flat(('rrect', (foot[0] - 27 + 3 * side, foot[1] + 20, foot[0] + 33 + 3 * side, foot[1] + 30, 5)), (215, 222, 235))
                L.flat(('ellipse', (foot[0] + 3 * side, foot[1] + 4, 9, 4)), STAR_RED)
            else:
                L.shape(('ellipse', (foot[0] + 3 * side, foot[1] + 12, 27, 17)), (255, 182, 210), bevel=7, spec=0.2)

    # ---- body
    if outfit in ('overalls', 'pajamas', 'bath'):
        top = YELLOW if outfit == 'overalls' else (PJ if outfit == 'pajamas' else SKIN)
        L.ball(0, -172, 60, 72, top, spec=0.25, amb=0.55)
        if outfit == 'overalls':
            L.shape([('ellipse', (0, -172, 61, 73)), ('rect', (-90, -320, 90, -158), 'erase'),
                     ('rrect', (-33, -206, 33, -150, 12)),
                     ('line', ([(-29, -200), (-44, -238)], 12)), ('line', ([(29, -200), (44, -238)], 12))],
                    OVERALL, bevel=7, spec=0.25)
            L.flat(('line', ([(-15, -192), (-15, -168), (15, -168), (15, -192)], 3)), (60, 104, 200))
            for side in (-1, 1):
                L.ball(27 * side, -199, 6.5, 6.5, (252, 205, 80), spec=0.8)
            L.shape(('star', (0, -224, 14, 6.5, 5, 0)), STAR_RED, bevel=2.5, spec=0.5)
        elif outfit == 'pajamas':
            L.flat(('ellipse', (0, -150, 61, 9)), (150, 172, 245), alpha=0.6)
            for (sx, sy, r, rot) in ((-30, -205, 11, 0.2), (22, -180, 9, -0.3), (-12, -140, 10, 0.5),
                                     (35, -128, 8, 0.1), (-40, -165, 7, -0.2), (5, -228, 8, 0.3)):
                L.shape(('star', (sx, sy, r, r * 0.45, 5, rot)), PJ_STAR, bevel=1.5, spec=0.4)
            L.flat(('arc', (0, -250, 26, 16, 20, 160, 7)), (150, 172, 245))
        # ---- arms
        sleeve = {'overalls': YELLOW, 'pajamas': PJ, 'bath': SKIN}[outfit]
        for side, hand in ((-1, lh), (1, rh)):
            S = (54 * side, -218)
            E = ik(S, hand, 58, 54, side)
            if outfit == 'pajamas':
                mid = (E[0] + (hand[0] - E[0]) * 0.75, E[1] + (hand[1] - E[1]) * 0.75)
                L.shape(('path', ([S, E, mid], [19, 17, 16])), PJ, bevel=6, spec=0.2)
                L.ball(hand[0], hand[1], 16, 16, SKIN, spec=0.3)
            else:
                L.shape(('path', ([S, E, hand], [16, 15, 14])), SKIN, bevel=6, spec=0.3)
                L.ball(hand[0], hand[1], 16, 16, SKIN, spec=0.3)
            if outfit != 'bath':
                L.ball(56 * side, -212, 23, 22, sleeve, spec=0.25)

    elif outfit == 'towel':
        L.shape([('rrect', (-92, -250, 92, -10, 70)), ('ellipse', (0, -30, 95, 40))], TOWEL_PINK, bevel=16, spec=0.15, amb=0.6)
        L.flat(('line', ([(-6, -235), (-18, -150), (-4, -60)], 6)), (240, 140, 180), alpha=0.6)
        for side in (-1, 1):
            L.ball(40 * side, -120, 17, 16, SKIN, spec=0.3)   # little hands holding the towel
        L.flat(('line', ([(-90, -40), (90, -40)], 5)), (255, 210, 228), alpha=0.8)

    # ---- head
    hy = -322
    L.ball(0, -248, 22, 18, SKIN_D, spec=0, rim=0)            # neck
    if outfit == 'towel':
        L.ball(0, hy - 10, 112, 104, TOWEL_PINK, spec=0.12, amb=0.6)
        for side, tilt in ((-1, 0.0), (1, 0.18 + 0.1 * math.sin(hood * 6))):
            bx, by = 44 * side, hy - 92
            tx, ty = bx + side * (22 + 40 * tilt), by - 100 + 30 * tilt
            L.shape(('path', ([(bx, by), ((bx + tx) / 2, (by + ty) / 2 - 6), (tx, ty)], [26, 27, 22])), TOWEL_PINK, bevel=9, spec=0.15)
            L.shape(('path', ([(bx, by - 12), ((bx + tx) / 2, (by + ty) / 2 - 6), (tx, ty + 6)], [11, 13, 10])), TOWEL_PINK_IN, bevel=4, spec=0.1)
    for side in (-1, 1):
        L.ball(79 * side, hy + 6, 15, 18, SKIN, spec=0.2)
    if outfit != 'towel':
        L.ball(0, hy - 22, 88, 74, HAIR, spec=0.3)
    L.ball(0, hy, 80, 76, SKIN, spec=0.3, amb=0.58, rim=0.2)

    # face
    L.flat(('ellipse', (-50, hy + 36, 17, 11)), BLUSH, alpha=0.38, blur=5)
    L.flat(('ellipse', (50, hy + 36, 17, 11)), BLUSH, alpha=0.38, blur=5)
    _eyes(L, 31, hy + 8, 21, 25, look, blink, happy)
    for side in (-1, 1):
        L.flat(('arc', (31 * side, hy - 26, 15, 8, 200, 340, 4.5)), HAIR_D)
    L.ball(0, hy + 30, 8, 6, (250, 190, 160), spec=0.5, rim=0)
    _mouth(L, 0, hy + 52, mouth, smile)

    # front hair: soft curls
    curls = [(-62, hy - 50, 27), (-34, hy - 70, 29), (0, hy - 78, 30), (34, hy - 70, 29), (62, hy - 50, 27),
             (-80, hy - 20, 22), (80, hy - 20, 22), (-86, hy + 10, 18), (86, hy + 10, 18),
             (-40, hy - 50, 19), (-12, hy - 56, 20), (16, hy - 55, 20), (43, hy - 48, 18)]
    if outfit == 'towel':
        curls = [(-40, hy - 52, 18), (-12, hy - 58, 19), (16, hy - 57, 19), (42, hy - 50, 17),
                 (-66, hy - 36, 17), (68, hy - 36, 17)]
    L.shape(('circles', curls), HAIR, bevel=7, spec=0.35, gloss=40)
    for (cx, cy, r) in curls[:5]:
        L.flat(('arc', (cx, cy + 2, r * 0.55, r * 0.5, 200, 300, 3)), (170, 112, 70), alpha=0.7)
    if outfit == 'towel':
        # hood rim in front of the hair
        L.shape(('arc', (0, hy - 6, 104, 98, 190, 350, 26)), TOWEL_PINK, bevel=8, spec=0.12)

    if crown > 0:
        _foam_crown(L, hy, crown, crown_t)


def _foam_crown(L, hy, k, t):
    base = [(-78 + i * 13, hy - 62 - 16 * math.sin(i / 12 * math.pi) + 3 * math.sin(t * 3 + i), 20 + 4 * math.sin(i * 1.7))
            for i in range(13)]
    n = int(len(base) * min(1, k * 2) + 0.5)
    circles = base[:max(n, 1)] if k < 0.5 else list(base)
    if k > 0.4:
        g = min(1, (k - 0.4) / 0.6)
        for i, sx in enumerate((-58, -29, 0, 29, 58)):
            h = (0.75 if i in (0, 4) else (1.0 if i == 2 else 0.88)) * g
            cy0 = hy - 92 - 14 * math.cos(sx / 70)
            for j in range(4):
                if j / 4 > h:
                    break
                circles.append((sx + 1.5 * math.sin(t * 2 + j + i), cy0 - j * 21, 18 - j * 3.4))
    L.shape(('circles', circles), (252, 252, 255), bevel=6, spec=0.55, amb=0.75, rim=0.15)
    for i, (cx, cy, r) in enumerate(circles[::3]):
        L.bubble(cx + 4, cy - 2, r * 0.45, phase=t * 0.2 + i * 0.13, alpha=0.8)


# --------------------------------------------------------------- Bobo ----
def bobo(fr, x, y, s, jump=0.0, trunk=0.0, ear=0.0, mouth=0.0, blink=False, happy=False,
         look=(0, 0), towel=False, fx=1, shadow=True, sit=False, trunk_wave=0.0):
    """Bobo the baby elephant. trunk: 0 = hanging, 1 = raised (spraying)."""
    if shadow:
        sh = max(0.35, 1 - jump / 160)
        soft_shadow(fr, x, y + 4 * s, 72 * s * sh, 13 * s * sh, alpha=0.22 * sh)
    L = Local(fr, x, y - jump * s, s, fx)
    # legs
    for side in (-1, 1):
        L.ball(44 * side, -24, 20, 22, ELE_D, spec=0.2)
    L.shape(('path', ([(62, -80), (80, -70), (84, -56)], [6, 5, 4])), ELE_D, bevel=3)
    L.ball(86, -54, 7, 8, EAR, spec=0.2)
    L.ball(0, -78, 70, 60, ELE, spec=0.35, amb=0.55)
    for side in (-1, 1):
        L.ball(24 * side, -28, 22, 27, ELE, spec=0.3)
        for k in (-1, 0, 1):
            L.ball(24 * side + 9 * k, -9, 5, 4, WHITE, spec=0.3, rim=0)
    if towel:
        L.shape([('ellipse', (0, -66, 76, 52)), ('rect', (-90, -150, 90, -92), 'erase')], BOBO_TOWEL, bevel=10, spec=0.15)
        for yy in (-74, -56):
            L.flat(('line', ([(-66, yy), (66, yy)], 5)), (230, 240, 255), alpha=0.8)
        L.shape(('path', ([(-30, -96), (-50, -60), (-58, -30)], [14, 15, 12])), BOBO_TOWEL, bevel=6, spec=0.1)
    # ears (flap)
    hy = -160
    for side in (-1, 1):
        f = 1 + 0.08 * math.sin(ear + (0 if side < 0 else 1.1))
        L.ball(68 * side, hy + 2, 46 * f, 54, EAR, spec=0.15, amb=0.6)
        L.ball(64 * side, hy + 6, 30 * f, 38, EAR_IN, spec=0, amb=0.85, rim=0)
    L.ball(0, hy, 64, 58, ELE, spec=0.4, amb=0.55)
    # cheeks, eyes
    for side in (-1, 1):
        L.flat(('ellipse', (40 * side, hy + 22, 13, 8)), BLUSH, alpha=0.35, blur=4)
    if happy:
        for side in (-1, 1):
            L.flat(('arc', (24 * side, hy - 4, 10, 9, 200, 340, 5)), (40, 30, 40))
    elif blink:
        for side in (-1, 1):
            L.flat(('arc', (24 * side, hy - 10, 10, 7, 25, 155, 4.5)), (40, 30, 40))
    else:
        for side in (-1, 1):
            ex, ey = 24 * side + look[0] * 2, hy - 8 + look[1] * 2
            L.ball(ex, ey, 10, 13, (26, 24, 40), spec=0.2, amb=1, rim=0)
            L.flat(('ellipse', (ex - 3, ey - 5, 4, 4.5)), WHITE)
            L.flat(('ellipse', (ex + 3, ey + 5, 1.8, 1.8)), WHITE)
    # mouth (under trunk)
    if mouth > 0.05:
        L.shape([('ellipse', (0, hy + 34, 20, 8 + 12 * mouth)), ('rect', (-25, hy + 10, 25, hy + 34), 'erase')], MOUTH, bevel=2, rim=0)
    else:
        L.flat(('arc', (0, hy + 20, 24, 14, 25, 155, 4)), (70, 90, 150))
    # trunk: bezier between "hanging" and "raised" poses
    d = [(0, hy + 16), (2, hy + 46), (6, hy + 72), (18, hy + 86)]
    u = [(0, hy + 16), (18, hy + 12), (36, hy - 18), (44, hy - 58)]
    w = trunk_wave
    cps = [(a[0] * (1 - trunk) + b[0] * trunk + (i * 3 * w), a[1] * (1 - trunk) + b[1] * trunk) for i, (a, b) in enumerate(zip(d, u))]
    pts, rs = [], []
    for i in range(12):
        t = i / 11
        mt = 1 - t
        px = mt ** 3 * cps[0][0] + 3 * mt * mt * t * cps[1][0] + 3 * mt * t * t * cps[2][0] + t ** 3 * cps[3][0]
        py = mt ** 3 * cps[0][1] + 3 * mt * mt * t * cps[1][1] + 3 * mt * t * t * cps[2][1] + t ** 3 * cps[3][1]
        pts.append((px, py))
        rs.append(17 - 6 * t)
    L.shape(('path', (pts, rs)), ELE, bevel=6, spec=0.35)
    tip = pts[-1]
    L.ball(tip[0], tip[1], 11, 9, ELE_D, spec=0.2)
    L.flat(('ellipse', (tip[0], tip[1], 5, 4)), (90, 120, 180))
    for k in range(1, 4):
        p = pts[k * 2]
        L.flat(('arc', (p[0], p[1], 12 - k, 4, 200, 340, 2.5)), ELE_D, alpha=0.8)
    return L.P(*tip)


# ---------------------------------------------------------------- Mom ----
def mom(fr, x, y, s, lh, rh, t=0.0, mouth=0.0, part='all'):
    """Mom, upper body, anchored at her waist. lh/rh hand targets (local).
    part: 'body', 'arms' or 'all' (arms can be drawn over Lilo)."""
    L = Local(fr, x, y, s)
    SW = (196, 166, 236)
    MSKIN = (250, 206, 176)
    MHAIR = (92, 56, 36)
    if part == 'hands':
        for hand in (lh, rh):
            L.ball(hand[0], hand[1], 25, 23, MSKIN, spec=0.3)
        return
    L.shape(('rrect', (-125, -270, 125, 80, 95)), SW, bevel=18, spec=0.15, amb=0.6)
    L.flat(('arc', (0, -262, 46, 26, 20, 160, 9)), (176, 146, 220))
    hy = -350
    L.ball(0, -272, 27, 22, (232, 180, 150), spec=0, rim=0)
    L.ball(0, hy - 18, 86, 82, MHAIR, spec=0.3)
    L.ball(0, hy - 100, 40, 36, MHAIR, spec=0.35)
    for side in (-1, 1):
        L.ball(72 * side, hy + 8, 13, 16, MSKIN, spec=0.2)
        L.ball(74 * side, hy + 30, 5, 5, (255, 250, 245), spec=0.9)
    L.ball(0, hy, 72, 80, MSKIN, spec=0.25, amb=0.6)
    for side in (-1, 1):
        L.flat(('ellipse', (42 * side, hy + 30, 15, 9)), BLUSH, alpha=0.32, blur=5)
        L.flat(('arc', (27 * side, hy + 8, 14, 11, 200, 340, 5.5)), (60, 34, 24))
        L.flat(('line', ([(27 * side + 13 * side, hy + 3), (27 * side + 19 * side, hy - 2)], 3.5)), (60, 34, 24))
        L.flat(('arc', (27 * side, hy - 22, 15, 7, 200, 340, 4)), MHAIR)
    L.ball(0, hy + 28, 8, 7, (240, 186, 156), spec=0.5, rim=0)
    _mouth(L, 0, hy + 50, mouth, 1.0, scale=0.9)
    L.shape([('ellipse', (-26, hy - 64, 60, 26)), ('ellipse', (34, hy - 68, 48, 24)), ('ellipse', (-62, hy - 30, 18, 34))],
            MHAIR, bevel=8, spec=0.3)
    if part == 'all':
        _mom_arms(L, lh, rh, SW, MSKIN)


def _mom_arms(L, lh, rh, SW, MSKIN):
    for side, hand in ((-1, lh), (1, rh)):
        S = (102 * side, -220)
        E = ik(S, hand, 145, 135, side)
        L.shape(('path', ([S, E, hand], [30, 26, 22])), SW, bevel=10, spec=0.15)
        L.ball(hand[0], hand[1], 25, 23, MSKIN, spec=0.3)


# --------------------------------------------------------------- toys ----
def duck(fr, x, y, s, t=0.0, squeeze=0.0, fx=1):
    L = Local(fr, x, y, s * (1 + 0.08 * squeeze), fx)
    Y = (255, 214, 50)
    L.ball(0, 0, 42, 28 * (1 - 0.1 * squeeze), Y, spec=0.6)
    L.ball(36, -14, 13, 12, Y, spec=0.5)
    L.ball(-22, -32, 25, 24, Y, spec=0.6)
    L.shape(('ellipse', (-47, -27, 15, 7 + 3 * squeeze)), (255, 140, 40), bevel=3, spec=0.6)
    L.ball(-28, -38, 4.5, 5, (30, 24, 20), spec=0.8, rim=0)
    L.ball(8, -4, 18, 11, (245, 195, 40), spec=0.3)


def boat(fr, x, y, s, t=0.0):
    L = Local(fr, x, y, s)
    L.shape(('poly', [(-56, -8), (56, -8), (40, 22), (-40, 22)]), (236, 66, 66), bevel=5, spec=0.5)
    L.flat(('rect', (-52, -2, 52, 3)), WHITE)
    L.shape(('rrect', (-3, -84, 3, -8, 3)), (170, 110, 70), bevel=2)
    L.shape(('poly', [(6, -80), (6, -14), (46, -16)]), WHITE, bevel=5, spec=0.3)
    L.shape(('poly', [(-6, -74), (-6, -30), (-34, -32)]), (255, 230, 120), bevel=4, spec=0.3)
    L.shape(('poly', [(-3, -84), (-3, -96), (-20, -90)]), (255, 210, 60), bevel=2)


def frog(fr, x, y, s, t=0.0, blink=False):
    L = Local(fr, x, y, s)
    G = (120, 214, 110)
    for side in (-1, 1):
        L.ball(30 * side, 12, 15, 9, (100, 190, 95), spec=0.3)
    L.ball(0, 0, 40, 28, G, spec=0.55)
    for side in (-1, 1):
        L.ball(17 * side, -24, 14, 13, G, spec=0.5)
        if blink:
            L.flat(('arc', (17 * side, -26, 7, 5, 25, 155, 3)), (30, 40, 30))
        else:
            L.ball(17 * side, -25, 9, 9, WHITE, spec=0.3, rim=0)
            L.ball(17 * side + 1, -24, 5, 5.5, (20, 20, 20), spec=0.6, rim=0)
        L.flat(('ellipse', (27 * side, -3, 7, 4)), BLUSH, alpha=0.4, blur=2)
    L.flat(('arc', (0, -12, 20, 12, 25, 155, 3.5)), (50, 110, 50))
