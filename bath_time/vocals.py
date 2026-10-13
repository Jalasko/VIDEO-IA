"""Singing voice: each lyric chunk is spoken by a neural TTS (Kokoro), then
re-synthesised with the WORLD vocoder on the melody's pitch and rhythm."""
import numpy as np
import pyworld as pw

from . import song

FP = 5.0  # WORLD frame period, ms


def _runs(mask, min_gap=3, min_len=3):
    runs, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < min_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [r for r in merged if r[1] - r[0] >= min_len] or merged


def _fit_runs(runs, k, n):
    runs = [list(r) for r in runs] or [[0, n]]
    while len(runs) > k:                       # merge across the smallest gap
        gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
        i = int(np.argmin(gaps))
        runs[i][1] = runs[i + 1][1]
        del runs[i + 1]
    while len(runs) < k:                       # split the longest run
        i = int(np.argmax([r[1] - r[0] for r in runs]))
        a, b = runs[i]
        m = (a + b) // 2
        runs[i:i + 1] = [[a, m], [m, b]]
    return runs


def sing(x, fs, notes):
    """x: speech (float), notes: [(note_name, seconds)]. Returns (audio, lead_seconds)."""
    x = x.astype(np.float64)
    f0, tpos = pw.harvest(x, fs, f0_floor=90, f0_ceil=600, frame_period=FP)
    sp = pw.cheaptrick(x, f0, tpos, fs)
    ap = pw.d4c(x, f0, tpos, fs)
    n = len(f0)
    voiced = f0 > 0
    runs = _fit_runs(_runs(voiced), len(notes), n)
    # syllable boundaries: middle of the gaps between voiced runs
    bounds = [0] + [(runs[i][1] + runs[i + 1][0]) // 2 for i in range(len(runs) - 1)] + [n]

    src_pos, tgt_f0 = [], []
    lead = 0.0
    for si, ((note, dur), a, b) in enumerate(zip(notes, bounds[:-1], bounds[1:])):
        T = max(int(dur * 0.93 * 1000 / FP), 4)
        seg = np.arange(a, b)
        v = voiced[a:b]
        U, V = int((~v).sum()), int(v.sum())
        us = 1.0 if U <= 0.45 * T else 0.45 * T / max(U, 1)
        vs = (T - U * us) / max(V, 1)
        lengths = np.where(v, vs, us)
        cum = np.concatenate([[0], np.cumsum(lengths)])
        outk = np.arange(T) + 0.5
        pos = np.interp(outk, cum, np.concatenate([seg, [b]]).astype(float))
        pos = np.clip(pos, a, b - 1)
        src_pos.append(pos)
        tgt_f0.append(np.full(T, song.hz(note)))
        if si == 0:
            first_v = np.argmax(v) if V else 0
            lead = min(cum[first_v] * FP / 1000.0, 0.09)
    pos = np.concatenate(src_pos)
    tf0 = np.concatenate(tgt_f0)
    idx = np.round(pos).astype(int)
    sp2 = np.ascontiguousarray(sp[idx])
    ap2 = np.ascontiguousarray(ap[idx])
    vmask = voiced[idx]

    # smooth note transitions (portamento) in log-f0, then gentle vibrato
    lf = np.log(tf0)
    k = 7
    lf = np.convolve(np.pad(lf, k, mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), mode='same')[k:-k]
    t = np.arange(len(lf)) * FP / 1000.0
    onset = np.zeros_like(t)
    acc = 0
    for p in src_pos:
        onset[acc:acc + len(p)] = np.arange(len(p)) * FP / 1000.0
        acc += len(p)
    vib = 0.012 * np.clip((onset - 0.22) / 0.2, 0, 1) * np.sin(2 * np.pi * 5.6 * t)
    f0_out = np.exp(lf + vib)
    f0_out[~vmask] = 0.0
    y = pw.synthesize(f0_out, sp2, ap2, fs, FP)
    return y, lead


def build_vocals(model_dir, out_sr=44100, voice='af_heart'):
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    total = int(song.DURATION * out_sr) + out_sr
    track = np.zeros(total, np.float32)
    cache = {}
    for c in song.CHUNKS:
        if c['tts'] not in cache:
            s, fs = k.create(c['tts'], voice=voice, speed=0.92, lang='en-us')
            s = np.asarray(s, np.float64)
            # trim leading / trailing silence
            env = np.abs(s) > 0.01 * np.abs(s).max()
            i0, i1 = np.argmax(env), len(env) - np.argmax(env[::-1])
            cache[c['tts']] = (s[max(i0 - 200, 0):i1 + 200], fs)
        x, fs = cache[c['tts']]
        y, lead = sing(x, fs, c['notes'])
        y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.12
        # resample to out_sr
        n_out = int(len(y) * out_sr / fs)
        y = np.interp(np.arange(n_out) * fs / out_sr, np.arange(len(y)), y).astype(np.float32)
        fade = min(400, len(y) // 4)
        y[-fade:] *= np.linspace(1, 0, fade)
        y[:80] *= np.linspace(0, 1, 80)
        i = int((c['t0'] - lead) * out_sr)
        track[i:i + len(y)] += y[:max(0, total - i)]
    return track
