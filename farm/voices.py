"""Character voices: French TTS (Kokoro ff_siwis) re-voiced with the WORLD
vocoder — pitch, formants (vocal tract size) and intonation per character."""
import json
import numpy as np
import pyworld as pw

from . import story

SR = 44100
FP = 5.0


def revoice(x, fs, f0_mul, formant, expr):
    x = x.astype(np.float64)
    f0, t = pw.harvest(x, fs, f0_floor=70, f0_ceil=700, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, fs)
    ap = pw.d4c(x, f0, t, fs)
    v = f0 > 0
    if v.any():
        lf = np.log(f0[v])
        m = np.median(lf)
        f0 = f0.copy()
        f0[v] = np.exp(m + (lf - m) * expr + np.log(f0_mul))
    # formant warp: scale the spectral envelope along frequency
    nb = sp.shape[1]
    src = np.clip(np.arange(nb) / formant, 0, nb - 1)
    i0 = np.floor(src).astype(int)
    i1 = np.minimum(i0 + 1, nb - 1)
    w = src - i0
    sp2 = np.ascontiguousarray(sp[:, i0] * (1 - w) + sp[:, i1] * w)
    ap2 = np.ascontiguousarray(ap[:, i0] * (1 - w) + ap[:, i1] * w)
    return pw.synthesize(f0, sp2, ap2, fs, FP)


def build(model_dir):
    """Returns (tracks: {who: mono float32 @SR}, meta: list of line timings)."""
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    n = int(story.DURATION * SR) + SR
    tracks = {w: np.zeros(n, np.float32) for w in ('gaston', 'mimi', 'bernard', 'pico')}
    meta = []
    for ln in story.LINES:
        s, fs = k.create(ln['text'], voice='ff_siwis', speed=ln['speed'], lang='fr-fr')
        s = np.asarray(s, np.float64)
        env = np.abs(s) > 0.01 * np.abs(s).max()
        i0, i1 = np.argmax(env), len(env) - np.argmax(env[::-1])
        s = s[max(i0 - 100, 0):i1 + 300]
        y = revoice(s, fs, ln['f0'], ln['formant'], ln['expr'])
        y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.11 * ln['gain']
        m = int(len(y) * SR / fs)
        y = np.interp(np.arange(m) * fs / SR, np.arange(len(y)), y).astype(np.float32)
        y[:60] *= np.linspace(0, 1, 60)
        y[-300:] *= np.linspace(1, 0, 300)
        a = int(ln['t0'] * SR)
        tracks[ln['who']][a:a + len(y)] += y[:n - a]
        # word timings, spread over the voiced part by word length (for captions)
        e = np.abs(y)
        frm = int(SR * 0.02)
        rms = np.sqrt(np.convolve(e ** 2, np.ones(frm) / frm, mode='same'))
        on = rms > 0.15 * rms.max()
        v0, v1 = np.argmax(on) / SR, (len(on) - np.argmax(on[::-1])) / SR
        words = ln['text'].split()
        wl = np.array([len(wd) + 1 for wd in words], float)
        cum = np.concatenate([[0], np.cumsum(wl)]) / wl.sum()
        meta.append(dict(who=ln['who'], text=ln['text'], t0=ln['t0'], t1=ln['t0'] + len(y) / SR,
                         words=[(wd, ln['t0'] + v0 + (v1 - v0) * cum[i], ln['t0'] + v0 + (v1 - v0) * cum[i + 1])
                                for i, wd in enumerate(words)]))
    return tracks, meta


def envelopes(tracks, fps=story.FPS):
    """Per-video-frame mouth openness (0..1) for each character."""
    out = {}
    hop = SR // fps
    for who, x in tracks.items():
        nfr = len(x) // hop
        r = np.sqrt(np.mean(x[:nfr * hop].reshape(nfr, hop) ** 2, axis=1))
        ref = np.percentile(r[r > 1e-4], 90) if (r > 1e-4).any() else 1.0
        out[who] = np.clip(r / (ref + 1e-9), 0, 1.2).tolist()
    return out


def save_meta(path, meta, env):
    with open(path, 'w') as f:
        json.dump(dict(lines=meta, env=env), f)
