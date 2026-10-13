"""Music cues and sound effects for « La dernière pomme » (numpy synthesis)."""
import numpy as np

from bath_time.music import SR, T, band, Track, xylo, kick, shaker, chime, pop, reverb
from bath_time.music import pluck as _pluck
from bath_time.song import hz
from . import story

rng = np.random.default_rng(21)


def pluck(f, dur=2.0):
    # the shared Karplus-Strong cache is keyed by pitch only, so always build 2 s and slice
    return _pluck(f, 2.0)[:int(dur * SR)]


def env(t, a=0.005, d=0.3):
    return np.minimum(1, t / a) * np.exp(-t / d)


def saw(f, t):
    ph = np.cumsum(np.broadcast_to(f, t.shape)) / SR
    return 2 * (ph % 1.0) - 1


def tone(f, dur, kind='saw', vib=0.0, vr=5.5, lo=200, hi=5000, a=0.01, d=None):
    t = T(dur)
    ff = f * (1 + vib * np.sin(2 * np.pi * vr * t) * np.clip(t / 0.2, 0, 1))
    if kind == 'saw':
        y = saw(ff, t)
    elif kind == 'square':
        y = np.sign(np.sin(2 * np.pi * np.cumsum(ff) / SR))
    else:
        y = np.sin(2 * np.pi * np.cumsum(ff) / SR)
    y = band(y, lo, hi) if kind != 'sine' else y
    e = np.minimum(1, t / a) * np.minimum(1, (dur - t) / 0.04)
    if d:
        e *= np.exp(-t / d)
    return y * e


def brass(note, dur, vel=1.0):
    f = hz(note) if isinstance(note, str) else note
    return (tone(f, dur, 'saw', vib=0.006, lo=150, hi=3500, a=0.03) * 0.5 + tone(f * 2, dur, 'saw', lo=400, hi=4000, a=0.04) * 0.12) * vel


def whistle(note, dur, vel=1.0):
    f = hz(note) if isinstance(note, str) else note
    return (tone(f, dur, 'sine', vib=0.012, vr=6, a=0.05) + 0.05 * band(rng.standard_normal(int(dur * SR)), 2000, 6000)) * 0.35 * vel


def twang(note, vel=1.0):
    f = hz(note)
    y = pluck(f, 2.0)
    t = T(2.0)
    return y * (1 + 0.3 * np.sin(2 * np.pi * 6 * t)) * 0.9 * vel


def hit(notes, vel=1.0, dur=1.2):
    out = np.zeros(int(dur * SR))
    for n in notes:
        out += tone(hz(n), dur, 'saw', lo=80, hi=2500, a=0.008, d=0.35)
    t = T(dur)
    out += np.sin(2 * np.pi * np.cumsum(60 + 80 * np.exp(-t * 20)) / SR) * np.exp(-t * 4) * 1.5   # timpani
    return out / len(notes) * 0.6 * vel


def snare():
    t = T(0.2)
    return (band(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t * 25) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5) * 0.4


def crash(dur=2.0):
    t = T(dur)
    return band(rng.standard_normal(len(t)), 4000, 14000) * np.exp(-t * 2.2) * 0.35


# ------------------------------------------------------------ effects ----
def thud():
    t = T(0.5)
    return (np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t * 8) + 50) / SR) * np.exp(-t * 9)
            + band(rng.standard_normal(len(t)), 100, 1500) * np.exp(-t * 30) * 0.5) * 0.9


def flaps(dur, rate=9):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur * rate)):
        t = T(0.09)
        b = band(rng.standard_normal(len(t)), 300, 2500) * np.exp(-t * 40) * np.minimum(1, t / 0.006)
        i = int(k / rate * SR)
        out[i:i + len(b)] += b[:len(out) - i]
    return out * 0.5


def oink(pitch=1.0):
    t = T(0.32)
    f = (170 + 60 * np.sin(np.pi * t / 0.32)) * pitch * (1 + 0.04 * rng.standard_normal(len(t)).cumsum() / 300)
    y = saw(f, t)
    y = band(y, 350, 1800) + 0.4 * band(rng.standard_normal(len(t)), 500, 1500) * np.abs(np.sin(2 * np.pi * 30 * t))
    return y * np.sin(np.pi * t / 0.32) ** 0.5 * 0.5


def bray():
    out = []
    for k in range(2):
        t = T(0.32)
        hee = band(saw(820 + 120 * np.sin(np.pi * t / 0.32), t), 600, 4000) + 0.6 * band(rng.standard_normal(len(t)), 1500, 5000)
        hee *= np.sin(np.pi * t / 0.32) * 0.35
        t2 = T(0.42)
        haw = band(saw(200 - 50 * t2 / 0.42, t2), 150, 2500) * np.sin(np.pi * t2 / 0.42) ** 0.6 * 0.7
        out += [hee, haw]
    return np.concatenate(out)


def whoosh(dur=0.7, up=True):
    t = T(dur)
    x = rng.standard_normal(len(t))
    lo, hi = band(x, 200, 1200), band(x, 1500, 6000)
    k = t / dur if up else 1 - t / dur
    return (lo * (1 - k) + hi * k) * np.sin(np.pi * t / dur) ** 1.5 * 0.6


def squeak():
    out = np.zeros(int(0.35 * SR))
    for k in range(3):
        t = T(0.06)
        f = 3000 + 900 * np.sin(np.pi * t / 0.06)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.06) * 0.25
        i = int(k * 0.09 * SR)
        out[i:i + len(b)] += b
    return out


def crunch():
    t = T(0.32)
    y = band(rng.standard_normal(len(t)), 900, 7000) * np.exp(-t * 9)
    clicks = (rng.random(len(t)) > 0.996) * rng.uniform(-1, 1, len(t)) * 3
    return (y + band(clicks, 1000, 8000)) * np.minimum(1, t / 0.003) * 0.7


def chomp():
    t = T(0.12)
    return band(rng.standard_normal(len(t)), 400, 3000) * np.exp(-t * 30) * 0.4


def cricket(dur):
    out = np.zeros(int(dur * SR))
    k = 0.15
    while k < dur - 0.3:
        for p in range(3):
            t = T(0.03)
            b = np.sin(2 * np.pi * 4700 * t) * np.sin(np.pi * t / 0.03) * 0.18
            i = int((k + p * 0.045) * SR)
            out[i:i + len(b)] += b
        k += 0.62
    return out


def punch():
    t = T(0.25)
    return (np.sin(2 * np.pi * np.cumsum(120 * np.exp(-t * 15) + 40) / SR) * np.exp(-t * 14)
            + band(rng.standard_normal(len(t)), 800, 6000) * np.exp(-t * 60) * 0.6) * 0.8


def boing(f0=180, dur=0.5):
    t = T(dur)
    f = f0 + 300 * t / dur + 50 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 3)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) * np.minimum(1, t / 0.005) * 0.4


def slide(f0, f1, dur):
    t = T(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.01 * np.sin(2 * np.pi * 7 * t))) / SR) * np.sin(np.pi * t / dur) ** 0.4 * 0.3


def sigh(dur=1.3):
    t = T(dur)
    y = band(rng.standard_normal(len(t)), 250, 1800)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2 * np.where(t < dur * 0.35, 0.5, 1.0)
    return y * e * 0.35


def ding():
    return chime(hz("E6"), 1.2) * 0.9


def creak(dur):
    t = T(dur)
    f = 90 + 30 * t / dur
    y = band(saw(f * (1 + 0.1 * np.sin(2 * np.pi * 23 * t)), t), 300, 2500)
    return y * np.sin(np.pi * t / dur) * 0.12


# -------------------------------------------------------------- music ----
def music():
    tr = Track(story.DURATION)
    # 0-2.6 : slow-motion tension (tremolo strings rising)
    t = T(2.6)
    f = 110 * 2 ** (t / 2.6 * 0.6)
    tr.put(0, band(saw(f, t), 100, 1800) * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t)) * np.minimum(1, t / 0.8) * 0.25)
    tr.put(0, band(saw(f * 1.5, t), 100, 2400) * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t + 1)) * np.minimum(1, t / 0.8) * 0.15)
    # western sting at the landing + "DUN" hits on the three close-ups
    tr.put(story.APPLE_LAND + 0.05, twang("E2"), 0.9)
    tr.put(story.APPLE_LAND + 0.1, whistle("B5", 0.35), 0.8)
    tr.put(story.APPLE_LAND + 0.45, whistle("E6", 0.25), 0.8)
    tr.put(story.APPLE_LAND + 0.7, whistle("B5", 0.45), 0.7)
    for c, ch in zip(story.FREEZE_CUTS, (["E3", "B3"], ["F3", "C4"], ["F#3", "C#4"])):
        tr.put(c, hit(ch), 1.0)
    tr.put(story.FREEZE_CUTS[-1] + 0.5, crash(1.5), 0.6)
    # 5-28 : bouncy comedy bed (120 bpm pizzicato + bassoon) with entrance stings
    bpm = 120
    B = 60 / bpm
    bass_line = ["C2", "G2", "A2", "E2", "F2", "C2", "G2", "G2"]
    t0, t1 = story.GASTON_JUMP + 0.9, 28.0
    k = 0
    tt = t0
    while tt < t1:
        bar = int((tt - t0) / (4 * B))
        root = bass_line[bar % len(bass_line)]
        tr.put(tt, pluck(hz(root) * (1 if k % 2 == 0 else 1.5), 0.6) * 0.8, 0.9)
        if k % 2 == 1:
            tr.put(tt, xylo(hz(root) * 8, 0.3), 0.12)
        k += 1
        tt += B
    # Gaston fanfare, Mimi sassy trombone, Bernard tuba
    for i, n in enumerate(["G4", "C5", "E5", "G5"]):
        tr.put(story.GASTON_JUMP + 0.05 + i * 0.16, brass(n, 0.15 if i < 3 else 0.6), 0.8)
    t = T(0.9)
    tr.put(story.MIMI_ENTER, band(saw(hz("E3") * 2 ** (np.sin(np.pi * t / 0.9) * 0.2), t), 200, 1500)
           * np.sin(np.pi * t / 0.9) * 0.4)
    tr.put(story.MIMI_ENTER + 0.8, band(saw(hz("C3") * (1 - 0.1 * T(0.6) / 0.6), T(0.6)), 200, 1400)
           * np.sin(np.pi * T(0.6) / 0.6) * 0.35)
    for i, n in enumerate(["C2", "G1", "C2"]):
        tr.put(story.BERNARD_ENTER + i * 0.5, tone(hz(n), 0.45, 'saw', lo=40, hi=700, a=0.03), 0.7)
    # 28-31 standoff: western whistle + twang
    tr.put(28.0, twang("A2"), 0.8)
    tr.put(28.05, whistle("E5", 0.4), 0.7)
    tr.put(28.5, whistle("A5", 0.4), 0.7)
    tr.put(29.0, twang("A2"), 0.6)
    tr.put(29.5, whistle("E5", 0.6), 0.6)
    tr.put(30.0, hit(["A2", "E3"]), 0.8)
    # 31-38 fight: fast chaotic polka at 184 bpm
    B = 60 / 184
    tt, k = story.CLOUD[0], 0
    chords = [("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"])]
    while tt < 38.0:
        root, ch = chords[(k // 8) % 2]
        if k % 2 == 0:
            tr.put(tt, pluck(hz(root), 0.5), 1.0)
            tr.put(tt, kick(), 0.5)
        else:
            for n in ch:
                tr.put(tt, pluck(hz(n), 0.3), 0.35)
            tr.put(tt, snare(), 0.5)
        n = ["C", "D", "E", "F", "G", "A", "B"][(k * 3) % 7] + str(5 + (k % 3 == 0))
        tr.put(tt + B / 2, xylo(hz(n), 0.25), 0.3)
        tr.put(tt + B / 2, shaker(), 0.5)
        k += 1
        tt += B
    tr.put(story.CLOUD[0], crash(), 0.8)
    # 38-45 sneaky tiptoe pizzicato (fight muffled in the background is in sfx)
    B = 60 / 100
    seq = ["E2", None, "E2", "F2", "F#2", None, "G2", None, "G2", "G#2", "A2", None, "B2", "C3", "B2", None]
    tt, k = 38.0, 0
    while tt < 45.0:
        n = seq[k % len(seq)]
        if n:
            tr.put(tt, pluck(hz(n), 0.25) * np.exp(-T(0.25) * 10), 1.3)
        if k % 4 == 3:
            tr.put(tt, xylo(hz("B5"), 0.15), 0.08)
        k += 1
        tt += B / 2
    tr.put(42.4, slide(500, 900, 0.35), 0.6)
    # 46.4-52 silence (cricket in sfx)
    # 52-58.3 playful jingle under Pico, ends on the freeze
    B = 60 / 120
    mel = ["C5", "E5", "G5", "E5", "F5", "A5", "G5", None, "E5", "G5", "C6", "G5", "F5", "D5", "C5", None]
    tt, k = 52.0, 0
    while tt < story.FREEZE - 0.1:
        n = mel[k % len(mel)]
        if n:
            tr.put(tt, xylo(hz(n), 0.4), 0.18)
        tr.put(tt, pluck(hz(["C3", "G2", "A2", "F2"][(k // 4) % 4]), 0.4), 0.5 if k % 2 == 0 else 0.25)
        k += 1
        tt += B / 2
    tr.put(story.SHOCK, hit(["C3", "F#3"]), 0.8)
    # freeze frame: ta-da!
    for i, n in enumerate(["C5", "E5", "G5", "C6"]):
        tr.put(story.FREEZE + 0.15 + i * 0.09, xylo(hz(n), 1.2), 0.5)
    for n in ["C4", "E4", "G4", "C5"]:
        tr.put(story.FREEZE + 0.45, brass(n, 1.0), 0.35)
    tr.put(story.FREEZE + 0.45, crash(), 0.5)
    return tr.x


def sfx():
    tr = Track(story.DURATION)
    tr.put(story.APPLE_LAND, thud(), 1.0)
    tr.put(story.APPLE_LAND + 0.18, thud() * 0.3, 0.6)
    tr.put(story.APPLE_LAND - 0.2, whoosh(0.25), 0.4)
    for c in story.FREEZE_CUTS:
        tr.put(c, whoosh(0.18), 0.4)
    # Gaston
    tr.put(story.GASTON_JUMP, whoosh(0.5), 0.6)
    tr.put(story.GASTON_JUMP + 0.75, thud() * 0.5, 0.7)
    tr.put(story.GASTON_JUMP + 0.8, flaps(0.6, 12), 0.9)
    tr.put(10.0, flaps(1.4, 10), 0.6)
    # Mimi
    tr.put(story.MIMI_ENTER + 0.2, oink(1.1), 0.7)
    tr.put(story.HIP_BUMP, punch(), 0.9)
    tr.put(story.HIP_BUMP + 0.02, boing(160, 0.6), 0.8)
    tr.put(story.HIP_BUMP + 0.05, slide(900, 300, 0.8), 0.5)
    tr.put(story.EAR_FLIP, ding(), 0.6)
    tr.put(18.0, oink(1.2), 0.5)
    tr.put(18.2, ding(), 0.4)
    # Bernard
    t = story.BERNARD_ENTER
    while t < story.BERNARD_ENTER + 1.1:
        tr.put(t, thud() * 0.25, 0.5)
        t += 0.4
    tr.put(story.SIGH, sigh(1.3), 1.0)
    # argument
    tr.put(28.0, flaps(1.0, 14), 0.8)
    tr.put(29.2, oink(1.3), 0.6)
    tr.put(29.5, oink(1.4), 0.6)
    tr.put(story.BRAY, bray(), 1.0)
    # fight
    from .scenes import POW
    for txt, dt in POW:
        tr.put(story.CLOUD[0] + dt, punch(), 0.9)
        tr.put(story.CLOUD[0] + dt + 0.05, boing(200 + 40 * dt, 0.3), 0.4)
    tt = story.CLOUD[0]
    i = 0
    while tt < 45.6:
        muffled = tt >= 38.0
        clip = [flaps(0.3, 14), oink(1.2), whoosh(0.3), punch(), oink(0.9), flaps(0.25, 16)][i % 6]
        if muffled:
            clip = band(clip, 80, 900) * 0.5
        tr.put(tt, clip, 0.6)
        if i % 5 == 2:
            tr.put(tt + 0.1, band(bray(), 80, 900 if muffled else 6000)[:int(0.8 * SR)], 0.4)
        tt += 0.33 + 0.12 * ((i * 7) % 3)
        i += 1
    tr.put(story.CLOUD[0], whoosh(0.6), 0.8)
    # Pico
    tt = story.PICO_ENTER
    while tt < story.PICO_LOOK[0]:
        tr.put(tt, pop() * 0.3, 0.4)
        tt += 0.22
    tr.put(story.PICO_LOOK[0], whoosh(0.15), 0.3)
    tr.put(story.PICO_LOOK[1], whoosh(0.15), 0.3)
    tr.put(story.PICO_GRAB - 0.1, squeak(), 0.8)
    tr.put(story.PICO_GRAB + 0.1, chomp(), 0.6)
    tt = story.PICO_EXIT
    while tt < 45.0:
        tr.put(tt, pop() * 0.3, 0.4)
        tt += 0.18
    # cloud clears, silence, cricket, head turn
    tr.put(story.CLOUD_CLEAR, whoosh(1.1, up=False), 0.9)
    tr.put(story.CRICKET[0], cricket(story.CRICKET[1] - story.CRICKET[0]), 1.0)
    tr.put(story.HEAD_TURN[0], creak(story.HEAD_TURN[1] - story.HEAD_TURN[0]), 1.0)
    # finale
    for b in story.BITES:
        tr.put(b, crunch(), 1.0)
        for k in range(3):
            tr.put(b + 0.3 + k * 0.17, chomp(), 0.5)
    tr.put(story.WINK, ding(), 0.9)
    tr.put(story.WINK + 0.05, squeak(), 0.4)
    tr.put(story.SHOCK, slide(1200, 250, 0.9), 0.6)
    tr.put(story.FREEZE, boing(120, 0.7), 0.9)
    tr.put(story.FREEZE, punch(), 0.6)
    return tr.x


def mix(voice_tracks):
    m = music()
    s = sfx()
    n = min(len(m), len(s))
    v = sum(x[:n].astype(np.float64) for x in voice_tracks.values())
    # duck the music under dialogue
    e = np.abs(v)
    k = int(0.05 * SR)
    e = np.convolve(e, np.ones(k) / k, mode='same')
    duck = 1 - 0.55 * np.clip(e / 0.04, 0, 1)
    out = reverb(m[:n], 0.8, 0.12) * 0.5 * duck + reverb(v, 0.5, 0.08) * 1.35 + s[:n] * 0.55
    t = np.arange(n) / SR
    out *= np.clip((story.DURATION - t) / 0.8, 0, 1)
    out = np.tanh(out * 1.1) / 1.1
    out /= np.abs(out).max() / 0.89
    return out.astype(np.float32)
