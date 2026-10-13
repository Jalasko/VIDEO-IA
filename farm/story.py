"""« La dernière pomme » — timeline shared by picture and sound (seconds)."""

DURATION = 60.0
FPS = 30

# ---- dialogue: (who, start, text, tts speed, f0 multiplier, formant warp, intonation gain)
LINES = [
    dict(who='gaston', t0=6.0, text="Cette pomme est à moi ! C'est moi qui réveille toute la ferme chaque matin !",
         speed=1.02, f0=0.70, formant=0.88, expr=1.6, gain=1.0),
    dict(who='mimi', t0=14.3, text="Excuse-moi ? C'est moi la plus belle de la ferme, la pomme me revient !",
         speed=1.0, f0=1.06, formant=1.05, expr=1.7, gain=1.0),
    dict(who='bernard', t0=22.3, text="Moi, je travaille toute la journée. Vous, vous faites rien. La pomme est pour moi.",
         speed=0.78, f0=0.52, formant=0.80, expr=0.55, gain=1.1),
    dict(who='gaston', t0=10.05, text="Cocoricooo !", speed=0.85, f0=0.78, formant=0.88, expr=2.2, gain=1.1),
    # the argument: overlapping shouts
    dict(who='gaston', t0=28.15, text="C'est à moi !", speed=1.15, f0=0.74, formant=0.88, expr=1.8, gain=1.0),
    dict(who='mimi', t0=29.1, text="Non, à moi !", speed=1.15, f0=1.1, formant=1.05, expr=1.8, gain=1.0),
    dict(who='pico', t0=53.6, text="Pendant que vous vous disputiez… moi, j'ai mangé.",
         speed=1.0, f0=1.55, formant=1.22, expr=1.35, gain=1.0),
]

# ---- key moments
APPLE_LAND = 2.6
FREEZE_CUTS = [3.35, 3.9, 4.45]          # close-ups on the three faces
GASTON_JUMP = 5.0
MIMI_ENTER = 12.0
HIP_BUMP = 13.0
EAR_FLIP = 13.75
BERNARD_ENTER = 20.0
SIGH = 21.1
BRAY = 30.05
CLOUD = (31.0, 45.8)                     # fight cloud exists
PICO_ENTER = 38.0
PICO_LOOK = (39.8, 40.7)                 # look left, then right
PICO_GRAB = 42.4
PICO_EXIT = 43.4
CLOUD_CLEAR = 45.0
LOOK_DOWN = 46.4
CRICKET = (47.3, 50.2)
HEAD_TURN = (50.0, 51.8)
BITES = [52.35, 52.95, 57.45]
WINK = 56.35
SHOCK = 56.9
FREEZE = 58.3

# ---- shots / quick cuts: (start, end, name)
SHOTS = [
    (0.0, APPLE_LAND - 0.15, 'apple_fall'),
    (APPLE_LAND - 0.15, FREEZE_CUTS[0], 'apple_land'),
    (FREEZE_CUTS[0], FREEZE_CUTS[1], 'freeze_gaston'),
    (FREEZE_CUTS[1], FREEZE_CUTS[2], 'freeze_mimi'),
    (FREEZE_CUTS[2], GASTON_JUMP, 'freeze_bernard'),
    (GASTON_JUMP, MIMI_ENTER, 'gaston'),
    (MIMI_ENTER, BERNARD_ENTER, 'mimi'),
    (BERNARD_ENTER, 28.0, 'bernard'),
    (28.0, 29.0, 'argue_wide'),
    (29.0, 30.0, 'argue_mimi'),
    (30.0, 31.0, 'argue_bernard'),
    (31.0, 38.0, 'fight'),
    (38.0, 45.0, 'pico'),
    (45.0, 47.4, 'clear'),
    (47.4, 48.6, 'empty'),
    (48.6, 52.0, 'turn'),
    (52.0, DURATION, 'finale'),
]


def shot_at(t):
    for i, (a, b, n) in enumerate(SHOTS):
        if a <= t < b:
            return i
    return len(SHOTS) - 1
