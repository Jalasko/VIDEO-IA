"""Synthesised backing track (xylophone, ukulele, bass, claps, shaker) and
sound effects (splashes, bubble pops, duck squeaks...), all in numpy."""
import numpy as np

from . import song

SR = 44100
rng = np.random.default_rng(7)


def T(sec):
    return np.arange(int(sec * SR)) / SR


def band(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1.0 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


class Track:
    def __init__(self, dur):
        self.x = np.zeros(int(dur * SR) + SR, np.float64)

    def put(self, t, clip, gain=1.0):
        i = int(t * SR)
        if i < 0:
            clip, i = clip[-i:], 0
        n = min(len(clip), len(self.x) - i)
        if n > 0:
            self.x[i:i + n] += clip[:n] * gain


# ------------------------------------------------------------ instruments --
def xylo(f, dur=0.9, vel=1.0):
    t = T(dur)
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t * 5)
         + 0.28 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 16)
         + 0.07 * np.sin(2 * np.pi * f * 9.5 * t) * np.exp(-t * 30))
    click = rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.15
    y = (y + click) * np.minimum(1, t / 0.002)
    return y * vel


_ks_cache = {}


def pluck(f, dur=1.4):
    key = round(f, 2)
    if key in _ks_cache:
        return _ks_cache[key]
    n = int(dur * SR)
    p = int(SR / f)
    y = np.zeros(n + p + 1)
    burst = rng.uniform(-1, 1, p)
    burst = np.convolve(burst, np.ones(3) / 3, mode='same')     # softer nylon tone
    y[:p] = burst
    decay = 0.996
    for k in range(p, n + p, p):
        e = min(k + p, n + p)
        seg = y[k - p:e - p]
        prev = y[k - p - 1:e - p - 1] if k - p - 1 >= 0 else np.concatenate([[0], y[k - p:e - p - 1]])
        y[k:e] = decay * 0.5 * (seg + prev)
    y = y[:n] * np.exp(-np.arange(n) / SR * 1.8)
    _ks_cache[key] = y
    return y


UKE = {'C': ['G4', 'C4', 'E4', 'C5'], 'F': ['A4', 'C4', 'F4', 'A4'],
       'G': ['G4', 'D4', 'G4', 'B4'], 'Am': ['A4', 'C4', 'E4', 'A4']}
ROOT = {'C': 'C3', 'F': 'F2', 'G': 'G2', 'Am': 'A2'}


def strum(chord, down=True, vel=1.0):
    notes = UKE[chord] if down else UKE[chord][::-1]
    out = np.zeros(int(1.5 * SR))
    for i, n in enumerate(notes):
        c = pluck(song.hz(n))
        o = int(i * 0.011 * SR)
        out[o:o + len(c)] += c[:len(out) - o] * (0.9 if i else 1.0)
    return out * vel * 0.32


def bass(f, dur):
    t = T(dur)
    env = np.minimum(1, t / 0.01) * np.exp(-t * 2.5)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * env * 0.45


def clap():
    t = T(0.25)
    n = rng.standard_normal(len(t))
    env = np.zeros_like(t)
    for d in (0, 0.009, 0.018):
        env += np.exp(-np.maximum(t - d, 0) * 60) * (t >= d)
    env += np.exp(-t * 18) * 0.3
    return band(n * env, 800, 3500) * 0.5


def shaker():
    t = T(0.06)
    return band(rng.standard_normal(len(t)) * np.exp(-t * 70) * np.minimum(1, t / 0.008), 5000, 12000) * 0.18


def kick():
    t = T(0.25)
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.5


def chime(f, dur=1.6):
    t = T(dur)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 3) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 7)) \
        * np.minimum(1, t / 0.003) * 0.35


# -------------------------------------------------------------- effects --
def splash(big=1.0):
    t = T(0.6)
    n = rng.standard_normal(len(t))
    y = band(n, 300, 4000) * np.exp(-t * 7) * np.minimum(1, t / 0.006)
    y += band(rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t * 12) * 0.4
    for _ in range(5):
        d = rng.uniform(0.03, 0.35)
        f0 = rng.uniform(700, 1400)
        tt = np.maximum(t - d, 0)
        y += np.sin(2 * np.pi * (f0 * tt + 2500 * tt * tt)) * np.exp(-tt * 60) * (t >= d) * 0.25
    return y * 0.5 * big


def pop():
    t = T(0.09)
    f = 350 + 1400 * t / 0.09
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * np.minimum(1, t / 0.002)
    return y * 0.3


def squeak():
    t = T(0.32)
    f = 1050 + 380 * np.sin(np.pi * t / 0.32) - 200 * t + 35 * np.sin(2 * np.pi * 28 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)
    env = np.sin(np.pi * np.clip(t / 0.32, 0, 1)) ** 0.6
    return y * env * 0.16


def water_run(dur):
    t = T(dur)
    n = rng.standard_normal(len(t))
    y = band(n, 200, 2200) * 0.6 + band(rng.standard_normal(len(t)), 2000, 7000) * 0.2
    y *= (0.8 + 0.2 * np.sin(2 * np.pi * 3.3 * t) * np.sin(2 * np.pi * 0.7 * t))
    y *= np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.4)
    for _ in range(int(dur * 9)):
        d = rng.uniform(0, dur - 0.1)
        f0 = rng.uniform(500, 1200)
        tt = np.maximum(t - d, 0)
        y += np.sin(2 * np.pi * (f0 * tt + 4000 * tt * tt)) * np.exp(-tt * 70) * (t >= d) * 0.12
    return y * 0.45


def spray(dur):
    t = T(dur)
    y = band(rng.standard_normal(len(t)), 1500, 8000)
    y *= np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.3) * (0.85 + 0.15 * np.sin(2 * np.pi * 7 * t))
    return y * 0.35


def scrub():
    t = T(0.35)
    y = band(rng.standard_normal(len(t)), 600, 2500) * (np.sin(np.pi * t / 0.35) ** 2)
    y *= 0.7 + 0.3 * np.sin(2 * np.pi * 18 * t)
    return y * 0.3


def boing():
    t = T(0.45)
    f = 220 + 380 * t / 0.45 + 60 * np.sin(2 * np.pi * 18 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * np.minimum(1, t / 0.005) * 0.3


def step():
    t = T(0.07)
    return (np.sin(2 * np.pi * 140 * t) * np.exp(-t * 60) + band(rng.standard_normal(len(t)), 300, 1500) * np.exp(-t * 90) * 0.4) * 0.35


def rub(dur):
    t = T(dur)
    y = band(rng.standard_normal(len(t)), 400, 3000) * (0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 1.6 * t)))
    return y * np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.4) * 0.12


# ------------------------------------------------------------------ mix --
def build_music():
    tr = Track(song.DURATION)
    B = song.BEAT
    nbars = len(song.CHORDS)
    for bar, ch in enumerate(song.CHORDS):
        t0 = bar * song.BAR
        outro = bar >= nbars - 2
        intro = bar < song.INTRO_BARS
        # ukulele: D . D U . U D U
        pattern = [(0, True, 1.0), (1, True, 0.8), (1.5, False, 0.6), (2.5, False, 0.6), (3, True, 0.8), (3.5, False, 0.6)]
        if outro:
            pattern = [(0, True, 0.8)] if bar == nbars - 1 else [(0, True, 0.8), (2, True, 0.6)]
        for b, dn, v in pattern:
            tr.put(t0 + b * B, strum(ch, dn, v))
        # bass
        if not intro and not outro:
            tr.put(t0, bass(song.hz(ROOT[ch]), 1.1))
            tr.put(t0 + 2 * B, bass(song.hz(ROOT[ch]), 1.1), 0.8)
            for b in (0, 2):
                tr.put(t0 + b * B, kick(), 0.6)
            for b in (1, 3):
                tr.put(t0 + b * B, clap())
            for b in range(8):
                tr.put(t0 + b * B / 2, shaker(), 1.0 if b % 2 else 0.6)
        elif intro:
            tr.put(t0 + 2 * B, clap(), 0.6)
            tr.put(t0 + 3 * B, clap(), 0.8)
            tr.put(t0 + 3.5 * B, clap(), 0.6)
    # intro xylophone hook + outro music-box arpeggio
    hook = ["C5", "E5", "G5", "E5", "D5", "G4", "B4", "D5"]
    for i, n in enumerate(hook):
        tr.put(i * B * 0.5 + (0 if i < 4 else B * 2), xylo(song.hz(n)), 0.5)
    tr.put(4 * B * 0.75, xylo(song.hz("C6")), 0.3)
    end = (nbars - 2) * song.BAR
    for i, n in enumerate(["C5", "E5", "G5", "C6", "G5", "E5", "C5", "G4", "C5"]):
        tr.put(end + i * B * 0.5, chime(song.hz(n)), 0.5)
    # xylophone doubling the vocal melody (an octave up, soft), fills in the rests
    for s in song.SYLLABLES:
        f = song.hz(s['note']) * 2
        tr.put(s['t0'], xylo(f, 0.6), 0.16)
    for li in range(len(song.LINES)):
        t = song.line_start(li) + 6 * B
        for k, n in enumerate(["G5", "E5", "C5"] if li % 2 else ["C5", "E5", "G5"]):
            tr.put(t + k * B * 0.5, xylo(song.hz(n), 0.7), 0.22)
    return tr.x


def build_sfx():
    tr = Track(song.DURATION)
    for t in song.SPLASH_WORDS:
        tr.put(t + 0.03, pop(), 0.9)
        tr.put(t + 0.12, pop(), 0.6)
    # shot 1: footsteps while running in
    t = 0.35
    while t < 3.5:
        tr.put(t, step(), 0.8)
        t += 1 / 3.0
    tr.put(song.FILL[0], water_run(song.FILL[1] - song.FILL[0] + 0.4), 0.9)
    for t in song.CLAPS_S2:
        tr.put(t, clap(), 0.35)
    for t in song.QUACKS:
        tr.put(t + 0.06, squeak(), 1.0)
    tr.put(song.SPRAY[0], spray(song.SPRAY[1] - song.SPRAY[0]), 1.0)
    for t in song.WASH_S3:
        tr.put(t + 0.02, splash(), 1.0)
    for t in song.SCRUB_S3 + song.WASH_S4 + song.SCRUB_S4:
        tr.put(t, scrub(), 1.0)
    tr.put(song.FROG_HOP, boing(), 1.0)
    tr.put(song.FROG_HOP + 0.42, splash(0.6), 0.7)
    # bubble pops sprinkled through the bathroom shots (matching visual pops)
    from .scenes import POP_EVENTS
    for t in POP_EVENTS:
        tr.put(t, pop(), 0.45)
    tr.put(song.SHOTS[4][0] + 0.2, rub(song.SHOTS[4][1] - song.SHOTS[4][0] - 0.4), 1.0)
    for i, t in enumerate(song.STAR_TIMES):
        tr.put(t, chime(song.hz(["C6", "E6", "G6", "D6", "A6", "C7"][i % 6]), 1.2), 0.25)
    return tr.x


def reverb(x, secs=1.1, wet=0.18):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 6.5)
    ir = band(ir, 200, 7000)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return x + wet * y


def mix(vocals):
    music = build_music()
    sfx = build_sfx()
    n = min(len(music), len(sfx), len(vocals))
    v = reverb(vocals[:n].astype(np.float64), 1.2, 0.22)
    m = reverb(music[:n], 0.9, 0.12)
    out = m * 0.55 + v * 1.25 + sfx[:n] * 0.6
    # end fade and gentle limiter
    t = np.arange(n) / SR
    out *= np.clip((song.DURATION - t) / 1.2, 0, 1)
    out = np.tanh(out * 1.1) / 1.1
    out /= np.abs(out).max() / 0.89
    return out.astype(np.float32)
