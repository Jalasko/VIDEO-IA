"""Tiny soft-3D renderer: shaded "plastic" shapes composited into a float frame.

Everything is drawn in a virtual 1920x1080 space and rasterised at SS times
that resolution; the camera crop + downscale at the end gives anti-aliasing.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2
W, H = 1920, 1080
WI, HI = W * SS, H * SS


FONT_PATH = __file__.rsplit('/', 2)[0] + '/assets/fonts/Fredoka.ttf'
_fonts = {}


def font(size):
    from PIL import ImageFont
    size = int(size)
    if size not in _fonts:
        f = ImageFont.truetype(FONT_PATH, size)
        try:
            f.set_variation_by_axes([700, 100])   # Bold
        except Exception:
            pass
        _fonts[size] = f
    return _fonts[size]


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / np.linalg.norm(v)


# ---------------------------------------------------------------- lighting --
class Light:
    dir = _unit([-0.45, -0.7, 0.6])
    half = _unit(dir + np.array([0, 0, 1.0], np.float32))
    key = np.array([1.0, 0.97, 0.90], np.float32)   # warm sun
    amb = np.array([0.90, 0.93, 1.0], np.float32)   # cool sky fill
    rim = np.array([1.0, 0.95, 0.85], np.float32)


def set_lighting(key=(1.0, 0.97, 0.90), amb=(0.90, 0.93, 1.0), rim=(1.0, 0.95, 0.85)):
    Light.key = np.array(key, np.float32)
    Light.amb = np.array(amb, np.float32)
    Light.rim = np.array(rim, np.float32)


def shade(nx, ny, nz, color, amb=0.55, spec=0.4, rim=0.25, gloss=60):
    L, Hh = Light.dir, Light.half
    c = np.asarray(color, np.float32)
    ndl = nx * L[0] + ny * L[1] + nz * L[2]
    diff = np.clip((ndl + 0.3) / 1.3, 0, 1)            # wrapped = soft
    k = amb * Light.amb + (1 - amb) * diff[..., None] * Light.key
    rgb = c * k
    # saturate the shadow side a little (cheap subsurface feel)
    sat = (1 - diff)[..., None] * 0.18
    rgb = rgb + (rgb - rgb.mean(axis=-1, keepdims=True)) * sat
    if spec:
        ndh = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1)
        s = (ndh ** gloss) * spec * 255 + (ndh ** 6) * spec * 22
        rgb = rgb + s[..., None] * Light.key
    if rim:
        f = (1 - np.clip(nz, 0, 1)) ** 3 * rim * 110
        rgb = rgb + f[..., None] * Light.rim
    return rgb


# ------------------------------------------------------------------ frame --
class Frame:
    def __init__(self, arr):
        self.a = arr

    @classmethod
    def solid(cls, color):
        a = np.empty((HI, WI, 3), np.float32)
        a[:] = color
        return cls(a)

    def copy(self):
        return Frame(self.a.copy())

    @staticmethod
    def _clip(x0, y0, w, h):
        X0, Y0 = max(x0, 0), max(y0, 0)
        X1, Y1 = min(x0 + w, WI), min(y0 + h, HI)
        if X1 <= X0 or Y1 <= Y0:
            return None
        return X0, Y0, X1, Y1

    def comp(self, x0, y0, rgb, alpha):
        h, w = alpha.shape
        c = self._clip(x0, y0, w, h)
        if c is None:
            return
        X0, Y0, X1, Y1 = c
        al = alpha[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
        if np.ndim(rgb) == 3:
            src = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        else:
            src = np.asarray(rgb, np.float32)
        reg = self.a[Y0:Y1, X0:X1]
        reg += (src - reg) * al

    def add(self, x0, y0, rgb):
        h, w = rgb.shape[:2]
        c = self._clip(x0, y0, w, h)
        if c is None:
            return
        X0, Y0, X1, Y1 = c
        self.a[Y0:Y1, X0:X1] += rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]


# --------------------------------------------------------------- geometry --
def _bbox(kind, g):
    if kind == 'ellipse':
        cx, cy, rx, ry = g
        return cx - rx, cy - ry, cx + rx, cy + ry
    if kind == 'circles':
        return (min(c[0] - c[2] for c in g), min(c[1] - c[2] for c in g),
                max(c[0] + c[2] for c in g), max(c[1] + c[2] for c in g))
    if kind == 'poly':
        xs, ys = zip(*g)
        return min(xs), min(ys), max(xs), max(ys)
    if kind in ('rrect', 'rect'):
        return g[0], g[1], g[2], g[3]
    if kind == 'capsule':
        x1, y1, x2, y2, r = g
        return min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r
    if kind in ('path', 'line'):
        pts, r = g
        rr = max(r) if np.ndim(r) else (r if kind == 'path' else r / 2)
        xs, ys = zip(*pts)
        return min(xs) - rr, min(ys) - rr, max(xs) + rr, max(ys) + rr
    if kind == 'arc':
        cx, cy, rx, ry, a0, a1, wd = g
        return cx - rx - wd, cy - ry - wd, cx + rx + wd, cy + ry + wd
    if kind == 'star':
        cx, cy, ro = g[0], g[1], g[2]
        return cx - ro, cy - ro, cx + ro, cy + ro
    if kind == 'text':
        cx, cy, s, size = g
        hw = size * 0.36 * len(s) + size * 0.3
        return cx - hw, cy - size * 0.8, cx + hw, cy + size * 0.8
    raise ValueError(kind)


def star_pts(cx, cy, ro, ri, n=5, rot=0.0):
    pts = []
    for i in range(2 * n):
        r = ro if i % 2 == 0 else ri
        a = rot - math.pi / 2 + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _draw(d, T, k, kind, g, fill):
    if kind == 'ellipse':
        cx, cy, rx, ry = g
        x, y = T(cx, cy)
        d.ellipse([x - rx * k, y - ry * k, x + rx * k, y + ry * k], fill=fill)
    elif kind == 'circles':
        for cx, cy, r in g:
            x, y = T(cx, cy)
            d.ellipse([x - r * k, y - r * k, x + r * k, y + r * k], fill=fill)
    elif kind == 'poly':
        d.polygon([T(*p) for p in g], fill=fill)
    elif kind == 'rect':
        a, b = T(g[0], g[1]), T(g[2], g[3])
        d.rectangle([a, b], fill=fill)
    elif kind == 'rrect':
        a, b = T(g[0], g[1]), T(g[2], g[3])
        r = min(g[4] * k, (b[0] - a[0]) / 2 - 0.5, (b[1] - a[1]) / 2 - 0.5)
        d.rounded_rectangle([a, b], radius=max(r, 0), fill=fill)
    elif kind == 'capsule':
        x1, y1, x2, y2, r = g
        _draw(d, T, k, 'path', ([(x1, y1), (x2, y2)], r), fill)
    elif kind == 'path':
        pts, r = g
        rs = list(r) if np.ndim(r) else [r] * len(pts)
        tp = [T(*p) for p in pts]
        for i in range(len(tp)):
            x, y = tp[i]
            rr = rs[i] * k
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill)
            if i:
                # quad between consecutive circles (tapered capsule)
                (xa, ya), (xb, yb) = tp[i - 1], tp[i]
                ra, rb = rs[i - 1] * k, rr
                dx, dy = xb - xa, yb - ya
                L = math.hypot(dx, dy) or 1e-6
                nx, ny = -dy / L, dx / L
                d.polygon([(xa + nx * ra, ya + ny * ra), (xb + nx * rb, yb + ny * rb),
                           (xb - nx * rb, yb - ny * rb), (xa - nx * ra, ya - ny * ra)], fill=fill)
    elif kind == 'line':
        pts, wd = g
        tp = [T(*p) for p in pts]
        d.line(tp, fill=fill, width=max(1, int(round(wd * k))), joint='curve')
        r = wd * k / 2
        for x, y in (tp[0], tp[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    elif kind == 'arc':
        cx, cy, rx, ry, a0, a1, wd = g
        x, y = T(cx, cy)
        wpx = max(1, int(round(wd * k)))
        d.arc([x - rx * k, y - ry * k, x + rx * k, y + ry * k], a0, a1, fill=fill, width=wpx)
        # round caps
        for a in (a0, a1):
            px = x + (rx * k - wpx / 2) * math.cos(math.radians(a))
            py = y + (ry * k - wpx / 2) * math.sin(math.radians(a))
            d.ellipse([px - wpx / 2, py - wpx / 2, px + wpx / 2, py + wpx / 2], fill=fill)
    elif kind == 'star':
        d.polygon([T(*p) for p in star_pts(*g)], fill=fill)
    elif kind == 'text':
        cx, cy, s, size = g
        d.text(T(cx, cy), s, font=font(size * k), anchor='mm', fill=fill)


def make_mask(items, pad=4):
    boxes = [_bbox(it[0], it[1]) for it in items if 'erase' not in it[2:]]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    X0 = int(math.floor(x0 * SS)) - pad
    Y0 = int(math.floor(y0 * SS)) - pad
    X1 = int(math.ceil(x1 * SS)) + pad
    Y1 = int(math.ceil(y1 * SS)) + pad
    # never build masks much larger than the frame
    X0, Y0 = max(X0, -WI // 2), max(Y0, -HI // 2)
    X1, Y1 = min(X1, WI + WI // 2), min(Y1, HI + HI // 2)
    w, h = max(X1 - X0, 1), max(Y1 - Y0, 1)
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    T = lambda x, y: (x * SS - X0, y * SS - Y0)
    for it in items:
        _draw(d, T, SS, it[0], it[1], 0 if 'erase' in it[2:] else 255)
    return X0, Y0, m


def _norm_items(items):
    if isinstance(items, tuple):
        return [items]
    return list(items)


def shape(fr, items, color, mode='pillow', bevel=10, spec=0.35, amb=0.55, rim=0.25,
          alpha=1.0, blur=0, gloss=60, grad=None):
    """Draw a union of primitives. mode: 'pillow' (soft 3D) or 'flat'.
    grad=(top_color, bottom_color) gives a vertical colour gradient instead of `color`."""
    items = _norm_items(items)
    pad = int(blur * SS * 3) + 4
    X0, Y0, m = make_mask(items, pad)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur * SS))
    A = np.asarray(m, np.float32) / 255.0
    if A.max() <= 0:
        return
    col = color
    if grad is not None:
        h = A.shape[0]
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        col = np.asarray(grad[0], np.float32) * (1 - t) + np.asarray(grad[1], np.float32) * t
        col = np.broadcast_to(col, A.shape + (3,))
    if mode == 'flat':
        rgb = col
    else:
        sig = max(bevel * SS, 0.6)
        hb = np.asarray(m.filter(ImageFilter.GaussianBlur(sig)), np.float32) / 255.0
        gy, gx = np.gradient(hb)
        k = sig * 2.5066 * 2.2
        idx = A > 0.002
        nx, ny = -gx[idx] * k, -gy[idx] * k
        inv = 1.0 / np.sqrt(nx * nx + ny * ny + 1.0)
        rgb = np.zeros(A.shape + (3,), np.float32)
        rgb[idx] = shade(nx * inv, ny * inv, inv, col[idx] if np.ndim(col) == 3 else col, amb, spec, rim, gloss)
    fr.comp(X0, Y0, rgb, A * alpha)


def ball(fr, cx, cy, rx, ry, color, spec=0.45, amb=0.5, rim=0.3, alpha=1.0, gloss=60):
    """Analytic shaded ellipsoid (rounder than pillow shapes)."""
    X0 = int(math.floor((cx - rx) * SS)) - 1
    X1 = int(math.ceil((cx + rx) * SS)) + 1
    Y0 = int(math.floor((cy - ry) * SS)) - 1
    Y1 = int(math.ceil((cy + ry) * SS)) + 1
    if X1 <= 0 or Y1 <= 0 or X0 >= WI or Y0 >= HI or rx <= 0 or ry <= 0:
        return
    xs = ((np.arange(X0, X1, dtype=np.float32) + 0.5) / SS - cx) / rx
    ys = ((np.arange(Y0, Y1, dtype=np.float32) + 0.5) / SS - cy) / ry
    x, y = xs[None, :], ys[:, None]
    r2 = x * x + y * y
    rr = np.sqrt(r2)
    A = np.clip((1 - rr) * min(rx, ry) * SS, 0, 1) * alpha
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    rz = (rx + ry) / 2
    idx = A > 0
    x, y = np.broadcast_to(x, A.shape)[idx], np.broadcast_to(y, A.shape)[idx]
    nx, ny, nz = x / rx, y / ry, z[idx] / rz
    inv = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz + 1e-9)
    rgb = np.zeros(A.shape + (3,), np.float32)
    rgb[idx] = shade(nx * inv, ny * inv, nz * inv, color, amb, spec, rim, gloss)
    fr.comp(X0, Y0, rgb, A)


def soft_shadow(fr, cx, cy, rx, ry, alpha=0.25, color=(70, 50, 80)):
    shape(fr, ('ellipse', (cx, cy, rx, ry)), color, 'flat', alpha=alpha, blur=max(ry * 0.5, 2))


def glow(fr, cx, cy, r, color, strength=1.0):
    X0 = int((cx - r) * SS); Y0 = int((cy - r) * SS)
    n = int(2 * r * SS) + 1
    xs = ((np.arange(n, dtype=np.float32) + X0) / SS - cx) / r
    ys = ((np.arange(n, dtype=np.float32) + Y0) / SS - cy) / r
    d2 = xs[None, :] ** 2 + ys[:, None] ** 2
    g = np.exp(-d2 * 4.0) * strength
    g[d2 > 1] = 0
    fr.add(X0, Y0, g[..., None] * np.asarray(color, np.float32))


def hsv2rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


def bubble(fr, cx, cy, r, phase=0.0, alpha=1.0):
    """Iridescent soap bubble."""
    X0 = int(math.floor((cx - r) * SS)) - 1
    Y0 = int(math.floor((cy - r) * SS)) - 1
    n = int(math.ceil(2 * r * SS)) + 3
    if r <= 0.5 or X0 + n < 0 or Y0 + n < 0 or X0 >= WI or Y0 >= HI:
        return
    xs = ((np.arange(n, dtype=np.float32) + X0 + 0.5) / SS - cx) / r
    ys = ((np.arange(n, dtype=np.float32) + Y0 + 0.5) / SS - cy) / r
    x, y = xs[None, :], ys[:, None]
    rr = np.sqrt(x * x + y * y)
    edge = np.clip((1 - rr) * r * SS, 0, 1)
    hue = (np.arctan2(y, x) / (2 * np.pi) + phase + rr * 0.4) % 1.0
    col = hsv2rgb(hue, 0.45, 1.0) * 255
    rimv = np.clip((rr - 0.55) / 0.45, 0, 1) ** 2
    A = (0.06 + 0.6 * rimv) * edge
    # highlights
    hl = np.exp(-(((x + 0.38) / 0.22) ** 2 + ((y + 0.42) / 0.15) ** 2))
    hl2 = np.exp(-(((x - 0.35) / 0.12) ** 2 + ((y - 0.45) / 0.08) ** 2)) * 0.6
    h = np.clip(hl + hl2, 0, 1) * edge
    col = col * (1 - h[..., None]) + 255 * h[..., None]
    A = np.clip(A + h * 0.9, 0, 1) * alpha
    fr.comp(X0, Y0, col, A)


def sparkle(fr, cx, cy, r, alpha=1.0, color=(255, 250, 210)):
    if r <= 0.5 or alpha <= 0:
        return
    pts = []
    for i in range(8):
        rad = r if i % 2 == 0 else r * 0.22
        a = i * math.pi / 4
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    shape(fr, ('poly', pts), color, 'flat', alpha=alpha)
    glow(fr, cx, cy, r * 1.6, (255, 240, 200), 0.6 * alpha)


def vgrad(fr, y0, y1, c0, c1, x0=0, x1=W):
    Y0, Y1 = int(y0 * SS), int(y1 * SS)
    X0, X1 = int(x0 * SS), int(x1 * SS)
    t = np.linspace(0, 1, max(Y1 - Y0, 1), dtype=np.float32)[:, None, None]
    col = np.asarray(c0, np.float32) * (1 - t) + np.asarray(c1, np.float32) * t
    fr.comp(X0, Y0, np.broadcast_to(col, (Y1 - Y0, X1 - X0, 3)),
            np.ones((Y1 - Y0, X1 - X0), np.float32))


def blur_frame(fr, radius):
    img = Image.fromarray(np.clip(fr.a, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(radius * SS))
    return Frame(np.asarray(img, np.float32).copy())


# ------------------------------------------------------ local transforms --
def tf(items, ox, oy, s, fx=1):
    """Map items from character-local coords (scale s, x-flip fx) to world."""
    out = []
    X = lambda px: ox + px * s * fx
    Y = lambda py: oy + py * s
    for it in _norm_items(items):
        kind, g, rest = it[0], it[1], it[2:]
        if kind == 'ellipse':
            cx, cy, rx, ry = g
            g = (X(cx), Y(cy), rx * s, ry * s)
        elif kind == 'circles':
            g = [(X(c[0]), Y(c[1]), c[2] * s) for c in g]
        elif kind == 'poly':
            g = [(X(p[0]), Y(p[1])) for p in g]
        elif kind in ('rrect', 'rect'):
            xa, xb = sorted((X(g[0]), X(g[2])))
            g = (xa, Y(g[1]), xb, Y(g[3])) + ((g[4] * s,) if kind == 'rrect' else ())
        elif kind == 'capsule':
            g = (X(g[0]), Y(g[1]), X(g[2]), Y(g[3]), g[4] * s)
        elif kind == 'path':
            pts, r = g
            g = ([(X(p[0]), Y(p[1])) for p in pts], [ri * s for ri in r] if np.ndim(r) else r * s)
        elif kind == 'line':
            pts, wd = g
            g = ([(X(p[0]), Y(p[1])) for p in pts], wd * s)
        elif kind == 'arc':
            cx, cy, rx, ry, a0, a1, wd = g
            if fx < 0:
                a0, a1 = 180 - a1, 180 - a0
            g = (X(cx), Y(cy), rx * s, ry * s, a0, a1, wd * s)
        elif kind == 'star':
            cx, cy, ro, ri, n, rot = g
            g = (X(cx), Y(cy), ro * s, ri * s, n, rot)
        out.append((kind, g) + tuple(rest))
    return out


class Local:
    """Helper to draw a character in its own coordinate system."""

    def __init__(self, fr, x, y, s, fx=1):
        self.fr, self.x, self.y, self.s, self.fx = fr, x, y, s, fx

    def P(self, dx, dy):
        return self.x + dx * self.s * self.fx, self.y + dy * self.s

    def ball(self, dx, dy, rx, ry, color, **kw):
        cx, cy = self.P(dx, dy)
        ball(self.fr, cx, cy, rx * self.s, ry * self.s, color, **kw)

    def shape(self, items, color, mode='pillow', bevel=8, blur=0, **kw):
        shape(self.fr, tf(items, self.x, self.y, self.s, self.fx), color, mode,
              bevel=bevel * self.s, blur=blur * self.s, **kw)

    def flat(self, items, color, alpha=1.0, blur=0):
        self.shape(items, color, 'flat', alpha=alpha, blur=blur)

    def glow(self, dx, dy, r, color, strength=1.0):
        cx, cy = self.P(dx, dy)
        glow(self.fr, cx, cy, r * self.s, color, strength)

    def bubble(self, dx, dy, r, phase=0, alpha=1.0):
        cx, cy = self.P(dx, dy)
        bubble(self.fr, cx, cy, r * self.s, phase, alpha)

    def sparkle(self, dx, dy, r, alpha=1.0):
        cx, cy = self.P(dx, dy)
        sparkle(self.fr, cx, cy, r * self.s, alpha)


def ik(S, T, l1, l2, out_sign):
    """2-bone IK. Returns elbow; out_sign picks the elbow bending side."""
    sx, sy = S; tx, ty = T
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = min(max(d, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    if d < 1e-6:
        return sx, sy + l1
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(l1 * l1 - a * a, 0))
    ux, uy = dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1)
    bx, by = sx + a * ux, sy + a * uy
    e1 = (bx - uy * hh, by + ux * hh)
    e2 = (bx + uy * hh, by - ux * hh)
    # choose the elbow further outward (out_sign = -1 left side, +1 right side)
    return e1 if (e1[0] - e2[0]) * out_sign > 0 else e2
