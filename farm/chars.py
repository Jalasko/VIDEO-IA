"""Gaston the rooster, Mimi the pig, Bernard the donkey, Pico the mouse, and the apple.

Every function draws the character in its own local coordinates (anchored at the
feet), so each design is identical in every shot.  Common expression knobs:
  mouth  0..1   lip-sync openness
  brow   -1..1  sad/worried .. angry/proud
  lid    0..1   eyelid closure
  wide   >1     shocked bulging eyes
  look   (x,y)  pupil direction
  shock  0..1   jaw-drop "O" mouth
"""
import math
from bath_time.gfx import Local, soft_shadow

WHITE = (252, 251, 246)
BLACK = (28, 24, 30)


def eyes(L, cx, cy, sep, rx, ry, look=(0, 0), lid=0.0, wide=1.0, brow=0.0, brow_col=BLACK, lid_col=WHITE,
         pupil=0.55, wink=None, brow_w=7, brow_dy=1.25, lashes=0, iris=None):
    for side in (-1, 1):
        x = cx + sep * side
        erx, ery = rx * wide, ry * wide
        if wink == side:
            L.flat(('arc', (x, cy + ery * 0.2, erx * 0.9, ery * 0.6, 200, 340, 6)), BLACK)
        else:
            L.ball(x, cy, erx, ery, WHITE, spec=0.25, amb=0.8, rim=0.05)
            px, py = x + look[0] * erx * 0.35, cy + look[1] * ery * 0.3
            if iris:
                L.ball(px, py, erx * pupil * 1.3, ery * pupil * 1.3, iris, spec=0.1, amb=0.8, rim=0)
            L.ball(px, py, erx * pupil, ery * pupil, BLACK, spec=0.3, amb=1, rim=0)
            L.flat(('ellipse', (px - erx * 0.18, py - ery * 0.22, erx * 0.18, ery * 0.16)), WHITE)
            L.flat(('ellipse', (px + erx * 0.16, py + ery * 0.2, erx * 0.08, ery * 0.07)), WHITE)
            if lid > 0.02:
                # upper eyelid covers the top of the eye
                L.shape([('ellipse', (x, cy, erx * 1.06, ery * 1.06)),
                         ('rect', (x - erx * 1.2, cy - ery * 1.2 + 2 * ery * 1.06 * lid, x + erx * 1.2, cy + ery * 1.3), 'erase')],
                        lid_col, bevel=3, spec=0.2, rim=0)
                yl = cy - ery * 1.06 + 2 * ery * 1.06 * lid
                L.flat(('line', ([(x - erx * 0.95, yl), (x + erx * 0.95, yl)], 4)), BLACK)
            for k in range(lashes):
                if lid > 0.02:      # lashes sit on the eyelid edge
                    yl = cy - ery * 1.06 + 2 * ery * 1.06 * lid
                    bx = x + side * erx * (0.25 + 0.3 * k)
                    a0, a1 = (bx, yl), (bx + side * (10 + 4 * k), yl - 14 - 3 * k)
                else:
                    a = math.radians(-150 + k * 30) if side < 0 else math.radians(-30 - k * 30)
                    a0 = (x + erx * 0.95 * math.cos(a), cy + ery * 0.95 * math.sin(a))
                    a1 = (x + erx * 1.45 * math.cos(a) + 6 * side, cy + ery * 1.4 * math.sin(a) - 4)
                L.flat(('line', ([a0, a1], 4.5)), BLACK)
        # eyebrow: angle by mood (inner end down = angry)
        by = cy - ery * brow_dy
        inner, outer = (x - side * erx * 0.2, by + 10 * brow), (x + side * erx * 1.0, by - 10 * brow - 2)
        L.shape(('line', ([outer, inner], brow_w)), brow_col, bevel=2, spec=0.2)


def o_mouth(L, cx, cy, w, h, col=(110, 30, 40)):
    L.shape(('ellipse', (cx, cy, w, h)), col, bevel=3, spec=0.2, rim=0)
    L.flat(('ellipse', (cx, cy + h * 0.5, w * 0.6, h * 0.35)), (240, 110, 120))


# ------------------------------------------------------------- Gaston ----
G_RED = (232, 38, 44)
G_BEAK = (255, 188, 40)
G_LEG = (250, 160, 40)
G_TAIL = (40, 110, 110)


def gaston(fr, x, y, s, mouth=0.0, brow=0.6, lid=0.0, wide=1.0, look=(0, 0), wings=0.0, flap=0.0, puff=1.0,
           shock=0.0, jump=0.0, rot=0.0, fx=1, shadow=True, feathers_lost=0.0):
    """wings: 0 folded .. 1 spread wide; flap: phase for flapping."""
    if shadow:
        sh = max(0.3, 1 - jump / 300)
        soft_shadow(fr, x, y + 4 * s, 120 * s * sh, 20 * s * sh, 0.25 * sh)
    L = Local(fr, x, y - jump * s, s, fx)
    # tail fan behind the body
    for i, (ang, ln, col) in enumerate(((-60, 210, WHITE), (-40, 240, G_TAIL), (-20, 250, WHITE), (0, 230, G_TAIL),
                                         (20, 210, WHITE))):
        a = math.radians(ang + 5 * math.sin(flap * 0.5 + i))
        b = (60, -230)
        tip = (b[0] + ln * math.sin(a + 0.9), b[1] - ln * math.cos(a + 0.9) * 0.9)
        mid = ((b[0] + tip[0]) / 2 + 20, (b[1] + tip[1]) / 2 - 30)
        L.shape(('path', ([b, mid, tip], [26, 24, 12])), col, bevel=8, spec=0.6 if col == G_TAIL else 0.3, gloss=50)
    # legs
    for side in (-1, 1):
        L.shape(('path', ([(30 * side, -120), (32 * side, -60), (30 * side, -14)], [11, 9, 9])), G_LEG, bevel=4, spec=0.4)
        for k in (-1, 0, 1):
            L.shape(('capsule', (30 * side, -12, 30 * side + 30 * k, 0, 6)), G_LEG, bevel=3, spec=0.4)
    # body + puffed chest
    L.ball(0, -215, 125, 118, WHITE, spec=0.3, amb=0.6)
    L.ball(0, -200, 95 * puff, 92 * puff, (255, 252, 240), spec=0.35, amb=0.65)
    # wings
    for side in (-1, 1):
        base = (98 * side, -250)
        ang0 = math.radians(160 - 120 * wings + 18 * math.sin(flap)) if wings > 0.05 else math.radians(170)
        feathers = []
        for k in range(5):
            a = ang0 - math.radians(12 * (k - 2))
            ln = 150 - 12 * abs(k - 2)
            tip = (base[0] + side * ln * math.sin(a), base[1] - ln * math.cos(a))
            feathers.append(('path', ([base, ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2), tip], [34, 30, 18])))
        L.shape(feathers, (248, 246, 238), bevel=9, spec=0.3)
    # head
    hy = -390
    L.ball(0, hy + 40, 62, 60, WHITE, spec=0.2)                       # neck
    crest = [(-48, hy - 70, 30), (-15, hy - 98, 38), (24, hy - 104, 40), (58, hy - 82, 33), (80, hy - 50, 25), (-70, hy - 42, 22)]
    L.shape(('circles', crest), G_RED, bevel=10, spec=0.6, gloss=50)
    L.ball(0, hy, 78, 76, WHITE, spec=0.3, amb=0.6)
    # beak (upper + lower, opens with the mouth)
    op = max(mouth, shock) * 26
    L.shape(('ellipse', (0, hy + 34 + op * 0.5, 24, 10 + op * 0.6)), (120, 30, 40), bevel=2, rim=0)
    L.shape(('poly', [(-24, hy + 30 + op), (24, hy + 30 + op), (0, hy + 52 + op * 1.4)]), (240, 160, 30), bevel=4, spec=0.5)
    L.shape(('poly', [(-30, hy + 14), (30, hy + 14), (0, hy + 50)]), G_BEAK, bevel=5, spec=0.7)
    L.shape(('circles', [(-8, hy + 66 + op * 1.2, 15), (8, hy + 74 + op * 1.2, 17)]), G_RED, bevel=6, spec=0.5)
    eyes(L, 0, hy - 14, 34, 19, 22, look=look, lid=lid, wide=wide, brow=brow, lid_col=WHITE, brow_w=9)
    if feathers_lost > 0:
        for k in range(3):
            L.flat(('line', ([(-60 + 50 * k, -330), (-50 + 50 * k, -350)], 4)), (200, 200, 200), alpha=feathers_lost)


# --------------------------------------------------------------- Mimi ----
M_PINK = (255, 172, 196)
M_DARK = (238, 128, 160)
M_HOOF = (110, 70, 80)


def mimi(fr, x, y, s, mouth=0.0, brow=0.0, lid=0.35, wide=1.0, look=(0, 0), hip=0.0, ear=0.0, stomp=0.0,
         shock=0.0, jump=0.0, fx=1, shadow=True, smirk=0.5):
    """hip: sideways hip bump amount (-1..1); ear: ear-flip progress 0..1."""
    if shadow:
        soft_shadow(fr, x, y + 4 * s, 110 * s, 18 * s, 0.25)
    L = Local(fr, x, y - jump * s, s, fx)
    # curly tail
    L.shape(('path', ([(100 + 40 * hip, -150), (130 + 40 * hip, -170), (140 + 40 * hip, -140), (120 + 40 * hip, -130),
                       (128 + 40 * hip, -155)], 7)), M_DARK, bevel=3)
    # legs (stomp lifts alternate front legs)
    for side, ph in ((-1, 0), (1, math.pi)):
        lift = 30 * max(0, math.sin(stomp + ph)) if stomp else 0
        L.shape(('capsule', (40 * side, -90, 42 * side, -22 - lift, 22)), M_PINK, bevel=8, spec=0.3)
        L.shape(('rrect', (42 * side - 22, -26 - lift, 42 * side + 22, -4 - lift, 9)), M_HOOF, bevel=4, spec=0.5)
    L.ball(70 * hip, -150, 112, 100, M_PINK, spec=0.35, amb=0.6)
    hy = -285
    # ears (back layer)
    for side in (-1, 1):
        flip = ear if side == 1 else 0.0
        tip = (side * (125 + 20 * flip), hy - 110 - 45 * flip)
        L.shape(('poly', [(side * 35, hy - 62), tip, (side * 100, hy - 15)]), M_DARK, bevel=8, spec=0.3)
        L.shape(('poly', [(side * 52, hy - 58), (tip[0] * 0.85, tip[1] + 14), (side * 92, hy - 26)]), (255, 196, 212),
                bevel=4, spec=0.1)
    # flower behind left ear
    fxp, fyp = -86, hy - 52
    for k in range(5):
        a = k * 2 * math.pi / 5
        L.ball(fxp + 20 * math.cos(a), fyp + 20 * math.sin(a), 15, 15, (255, 252, 255), spec=0.3, amb=0.75)
    L.ball(fxp, fyp, 11, 11, (255, 206, 50), spec=0.5)
    L.ball(0, hy, 96, 88, M_PINK, spec=0.4, amb=0.6)
    # cheeks
    for side in (-1, 1):
        L.flat(('ellipse', (side * 58, hy + 28, 20, 13)), (255, 110, 150), alpha=0.4, blur=5)
    eyes(L, 0, hy - 18, 38, 20, 23, look=look, lid=lid, wide=wide, brow=brow, lid_col=M_DARK, brow_col=(150, 70, 90),
         brow_w=6, lashes=3, iris=(90, 160, 230), pupil=0.45)
    # snout
    L.ball(0, hy + 30, 42, 30, M_DARK, spec=0.5, amb=0.6)
    for side in (-1, 1):
        L.flat(('ellipse', (side * 13, hy + 30, 7, 11)), (150, 60, 90))
    # mouth
    if shock > 0.05:
        o_mouth(L, 0, hy + 78, 22 * shock + 6, 26 * shock + 6)
    elif mouth > 0.06:
        w = 26 + 8 * mouth
        h = 8 + 22 * mouth
        L.shape([('ellipse', (8, hy + 70, w, h)), ('rect', (8 - w - 2, hy + 70 - h - 2, 8 + w + 2, hy + 70), 'erase')],
                (130, 40, 70), bevel=2, rim=0)
        L.flat(('arc', (8, hy + 70 - 2, w, 6, 180, 360, 5)), (230, 80, 120))
    else:
        L.flat(('arc', (10, hy + 56, 24, 16 * smirk + 4, 20, 150, 5)), (190, 70, 110))


# ------------------------------------------------------------ Bernard ----
B_BROWN = (150, 110, 80)
B_DARK = (96, 66, 46)
B_MUZZLE = (226, 206, 180)


def bernard(fr, x, y, s, mouth=0.0, brow=0.4, lid=0.55, wide=1.0, look=(0, 0), ears=0.0, bray=0.0, walk=None,
            shock=0.0, jump=0.0, fx=1, shadow=True, head_turn=0.0):
    """ears: 0 droopy .. 1 straight up; bray: 0..1 huge open mouth with teeth."""
    if shadow:
        soft_shadow(fr, x, y + 4 * s, 150 * s, 22 * s, 0.25)
    L = Local(fr, x, y - jump * s, s, fx)
    # tail
    L.shape(('path', ([(120, -260), (150, -200), (150, -150)], [8, 7, 6])), B_BROWN, bevel=3)
    L.shape(('ellipse', (150, -135, 16, 26)), B_DARK, bevel=5)
    # legs
    for i, lx in enumerate((-80, -35, 35, 80)):
        ph = 0 if walk is None else walk + (0 if i % 2 else math.pi)
        lift = 0 if walk is None else 18 * max(0, math.sin(ph))
        c = B_BROWN if i in (1, 2) else (130, 94, 68)
        L.shape(('capsule', (lx, -200, lx, -28 - lift, 20)), c, bevel=7, spec=0.25)
        L.shape(('rrect', (lx - 21, -34 - lift, lx + 21, -6 - lift, 8)), (60, 44, 36), bevel=4, spec=0.5)
    L.ball(0, -250, 140, 105, B_BROWN, spec=0.3, amb=0.6)
    L.ball(0, -225, 80, 60, (176, 136, 104), spec=0.1, amb=0.7, rim=0)
    hx = 40 * head_turn
    hy = -470
    L.shape(('capsule', (0, -300, hx * 0.5, hy + 40, 58)), B_BROWN, bevel=14, spec=0.2)
    # ears
    for side in (-1, 1):
        base = (hx + 40 * side, hy - 70)
        droop = 1 - ears
        tip = (base[0] + side * (40 + 90 * droop), base[1] - 140 + 100 * droop)
        mid = ((base[0] + tip[0]) / 2 + side * 10, (base[1] + tip[1]) / 2 - 20 * (1 - droop))
        L.shape(('path', ([base, mid, tip], [26, 28, 16])), B_BROWN, bevel=9, spec=0.25)
        L.shape(('path', ([base, mid, tip], [12, 14, 6])), (210, 170, 140), bevel=4, spec=0.1)
        L.ball(tip[0], tip[1], 14, 14, B_DARK, spec=0.2)
    L.ball(hx, hy, 72, 104, B_BROWN, spec=0.3, amb=0.6)
    # mane tuft
    L.shape(('circles', [(hx - 22, hy - 98, 20), (hx, hy - 110, 24), (hx + 22, hy - 98, 20), (hx + 6, hy - 80, 18)]),
            B_DARK, bevel=6, spec=0.3)
    eyes(L, hx, hy - 28, 36, 18, 20, look=look, lid=lid, wide=wide, brow=brow, lid_col=(140, 100, 72),
         brow_col=B_DARK, brow_w=11, pupil=0.5)
    for side in (-1, 1):   # eye bags
        L.flat(('arc', (hx + 36 * side, hy - 8, 16, 7, 20, 160, 3)), B_DARK, alpha=0.5)
    # muzzle + mouth
    my = hy + 66
    open_ = max(mouth * 0.7, bray, shock * 0.8)
    if open_ > 0.05:
        h = 18 + 60 * open_
        L.shape(('ellipse', (hx, my + 30 + h * 0.4, 46, h * 0.6)), (110, 40, 40), bevel=3, rim=0)
        L.shape(('rrect', (hx - 30, my + 26, hx + 30, my + 44, 5)), (252, 250, 240), bevel=2, spec=0.4)
        L.ball(hx, my + 36 + h * 0.75, 50, 26, B_MUZZLE, spec=0.2)            # lower jaw
    L.ball(hx, my, 64, 50, B_MUZZLE, spec=0.3, amb=0.65)
    for side in (-1, 1):
        L.flat(('ellipse', (hx + 22 * side, my - 6, 9, 13)), (90, 60, 50))
    if open_ <= 0.05:
        L.flat(('arc', (hx, my + 18, 30, 14, 200, 340, 5)), (120, 80, 60))


# --------------------------------------------------------------- Pico ----
P_GREY = (176, 176, 190)
P_PINK = (255, 170, 190)


def pico(fr, x, y, s, mouth=0.0, look=(0, 0), wink=None, tiptoe=None, hands='down', chew=0.0, crouch=0.0,
         fx=1, shadow=True, brow=0.4, wide=1.0, head=0.0):
    """hands: 'down' | 'sneak' | 'up' (holding something overhead) | 'hold' (at mouth)."""
    if shadow:
        soft_shadow(fr, x, y + 3 * s, 46 * s, 9 * s, 0.25)
    bob = 0 if tiptoe is None else 6 * abs(math.sin(tiptoe))
    L = Local(fr, x, y - bob * s, s, fx)
    L.shape(('path', ([(30, -30), (75, -20), (95, -55), (80, -90), (100, -110)], [6, 5, 4, 3, 2.5])), P_PINK, bevel=2)
    for side, ph in ((-1, 0), (1, math.pi)):
        lift = 0 if tiptoe is None else 12 * max(0, math.sin(tiptoe + ph))
        L.ball(16 * side, -8 - lift, 15, 7, P_PINK, spec=0.3)
    cy = -55 + 10 * crouch
    L.ball(0, cy, 40, 44, P_GREY, spec=0.35, amb=0.6)
    L.ball(0, cy + 8, 26, 28, (225, 225, 232), spec=0.1, amb=0.75, rim=0)
    hy = -120 + 14 * crouch
    hx = 14 * head
    hand_pos = {'down': [(-34, cy + 10), (34, cy + 10)], 'sneak': [(-26, cy - 26), (30, cy - 8)],
                'up': [(-30, hy - 70), (30, hy - 70)], 'hold': [(-24, hy + 28), (24, hy + 28)]}[hands]
    for side, hp in zip((-1, 1), hand_pos):
        L.shape(('path', ([(30 * side, cy - 18), hp], [8, 7])), P_GREY, bevel=3)
        L.ball(hp[0], hp[1], 9, 9, P_PINK, spec=0.3)
    for side in (-1, 1):
        L.ball(hx + 40 * side, hy - 38, 34, 32, P_GREY, spec=0.3, amb=0.6)
        L.ball(hx + 40 * side, hy - 36, 23, 21, P_PINK, spec=0.1, amb=0.8, rim=0)
    L.ball(hx, hy, 44, 38, P_GREY, spec=0.35, amb=0.6)
    eyes(L, hx, hy - 8, 16, 9, 11, look=look, wink=wink, wide=wide, brow=brow, brow_col=(110, 110, 125), brow_w=4,
         pupil=0.7, brow_dy=1.5)
    L.ball(hx, hy + 14, 8, 7, (255, 120, 150), spec=0.8)
    for side in (-1, 1):
        for k in (-1, 0, 1):
            L.flat(('line', ([(hx + 12 * side, hy + 16 + 3 * k), (hx + 50 * side, hy + 10 + 10 * k)], 2)), (80, 80, 90))
    if mouth > 0.06 or chew > 0.05:
        o = max(mouth, chew)
        L.shape(('ellipse', (hx + 4, hy + 28, 9 + 4 * o, 3 + 9 * o)), (110, 40, 50), bevel=1.5, rim=0)
        L.flat(('rrect', (hx - 1, hy + 24, hx + 9, hy + 30, 2)), WHITE)
    else:
        L.flat(('arc', (hx + 8, hy + 18, 16, 10, 10, 120, 3.5)), (80, 60, 70))   # mischievous smirk


# -------------------------------------------------------------- apple ----
def apple(fr, x, y, r, rot=0.0, bites=0, alpha=1.0):
    """Shiny red apple centred at (x, y). bites: 0..3 chunks taken out (right side)."""
    L = Local(fr, x, y, r / 100.0)
    bite_c = [(92, -18, 30), (84, 34, 28), (40, -78, 30)][:bites]
    items = [('circles', [(-28, 0, 96), (28, 0, 96), (0, 20, 88)])] + [('circles', [b]) + ('erase',) for b in bite_c]
    L.shape(items, (220, 30, 40), bevel=28, spec=0.9, gloss=70, amb=0.55, alpha=alpha)
    for bx, by, br in bite_c:
        L.shape([('circles', [(bx - 10, by, br + 6)]), ('circles', [(bx + 4, by, br)], 'erase')], (255, 244, 210),
                bevel=4, spec=0.2, alpha=alpha)
    L.flat(('ellipse', (-46, -52, 22, 14)), (255, 255, 255), alpha=0.55 * alpha, blur=4)
    sx = 6 * math.sin(rot)
    L.shape(('capsule', (sx, -92, sx + 10, -140, 7)), (110, 70, 40), bevel=3, alpha=alpha)
    L.shape(('poly', [(sx + 10, -122), (sx + 70, -150), (sx + 40, -112)]), (90, 180, 70), bevel=5, spec=0.4, alpha=alpha)
