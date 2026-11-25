"""Torn-paper primitives — the visual language of the paper cut-out film.

Every piece of type in this film sits on a label that reads as *cut paper*:
an irregular torn edge, a soft contact shadow, visible fibre grain and a
thin lit edge where the card catches the light. That guarantees legibility
on any plate without looking like a broadcast lower-third.
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

# ---------------------------------------------------------------- palette
PARCHMENT = (233, 223, 200)
PARCHMENT_DK = (206, 193, 166)
OXIDE = (146, 31, 26)
CHARCOAL = (26, 24, 30)
INK = (26, 19, 18)
BONE = (243, 238, 226)
BLOOD = (168, 22, 22)

_MASK = {}


def _rng(seed):
    return np.random.default_rng(int(seed) * 7919 + 101)


def torn_mask(w, h, seed=0, rough=0.10, ss=2):
    """Irregular torn-paper rectangle as a float mask (h, w) in 0..1."""
    w = max(4, int(round(w)))
    h = max(4, int(round(h)))
    key = (w, h, int(seed), round(rough, 4))
    if key in _MASK:
        return _MASK[key]

    rng = _rng(seed)
    W2, H2 = int(w * ss), int(h * ss)
    n = max(12, int(w / 7))
    xs = np.linspace(0, W2, n + 1)
    rp = rough * H2

    def walk():
        # random walk -> the jagged profile of a hand-torn edge
        v = np.cumsum(rng.normal(0, 1, n + 1))
        v -= v.min()
        v /= max(v.max(), 1e-6)
        return v

    top = walk() * rp
    bot = H2 - walk() * rp
    pts = [(xs[i], top[i]) for i in range(n + 1)]
    pts += [(xs[i], bot[i]) for i in range(n, -1, -1)]
    im = Image.new("L", (W2, H2), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    arr = np.asarray(im.resize((w, h), Image.LANCZOS), dtype=np.float32) / 255.0

    if len(_MASK) > 500:
        _MASK.clear()
    _MASK[key] = arr
    return arr


def _clip(img, mask, x0, y0):
    """Yield (img_slice, mask_slice) for a clipped placement."""
    H, W = img.shape[:2]
    h, w = mask.shape
    x0, y0 = int(round(x0)), int(round(y0))
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return None
    sub = mask[dy0 - y0:dy1 - y0, dx0 - x0:dx1 - x0]
    return img[dy0:dy1, dx0:dx1], sub


def blit(img, mask, x0, y0, color, alpha=1.0):
    if alpha <= 0.002:
        return
    r = _clip(img, mask, x0, y0)
    if r is None:
        return
    reg, sub = r
    a = (sub * alpha)[..., None]
    col = np.array(color, dtype=np.float32) / 255.0
    reg[...] = reg * (1.0 - a) + col * a


def _grain(h, w, seed):
    rng = _rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    return gaussian_filter(n, 0.55)


def panel(img, x0, y0, x1, y1, color, seed=0, alpha=1.0, rough=0.10,
          shadow_px=13.0, grain=0.055):
    """A torn paper label with contact shadow, fibre grain and lit edges."""
    w = x1 - x0
    h = y1 - y0
    if w < 5 or h < 5 or alpha <= 0.004:
        return
    m = torn_mask(w, h, seed, rough)

    if shadow_px > 0:
        sh = gaussian_filter(m, shadow_px * 0.40)
        blit(img, sh, x0 + 2.0, y0 + shadow_px, (0, 0, 0), 0.40 * alpha)

    blit(img, m, x0, y0, color, alpha)

    # fibre grain inside the sheet
    if grain > 0:
        g = _grain(m.shape[0], m.shape[1], int(seed) + 3)
        r = _clip(img, m, x0, y0)
        if r is not None:
            reg, sub = r
            a = (sub * grain * alpha)[..., None]
            reg[...] = np.clip(reg + g[..., None] * a * 0.9, 0.0, 1.0)

    # lit top edge (card catching the light)
    up = np.zeros_like(m)
    up[3:, :] = m[:-3, :]
    band = np.clip(m - up, 0, 1)
    blit(img, band, x0, y0, (255, 252, 244), 0.30 * alpha)

    # shaded bottom edge (paper thickness)
    dn = np.zeros_like(m)
    dn[:-3, :] = m[3:, :]
    band2 = np.clip(m - dn, 0, 1)
    blit(img, band2, x0, y0, (0, 0, 0), 0.22 * alpha)


def strip_behind_text(img, x0, x1, cy, height, color, seed=0, alpha=1.0,
                      rough=0.12, pad=0.0):
    """Convenience: centred vertical paper strip spanning x0..x1."""
    panel(img, x0 - pad, cy - height / 2, x1 + pad, cy + height / 2,
          color, seed=seed, alpha=alpha, rough=rough)


def silhouette(img, cx, cy, scale, color=(12, 10, 14), alpha=1.0):
    """A small child silhouette, cut from near-black card, standing in a doorway.

    Built from simple cut-paper shapes so it always matches the plate style.
    """
    s = float(scale)
    col = np.array(color, dtype=np.float32) / 255.0

    def disc(px, py, r):
        yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]].astype(np.float32)
        d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
        return np.clip(r - d + 0.5, 0, 1)

    def taper(px, y0, y1, r0, r1):
        yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]].astype(np.float32)
        t = np.clip((yy - y0) / max(y1 - y0, 1e-3), 0, 1)
        r = r0 + (r1 - r0) * t
        inside = np.clip((r - np.abs(xx - px)) + 0.5, 0, 1)
        band = ((yy >= y0) & (yy <= y1)).astype(np.float32)
        return inside * band

    m = np.zeros(img.shape[:2], dtype=np.float32)
    m = np.maximum(m, disc(cx, cy, 0.052 * s))                      # head
    m = np.maximum(m, taper(cx, cy + 0.050 * s, cy + 0.300 * s, 0.055 * s, 0.075 * s))
    m = np.maximum(m, taper(cx - 0.048 * s, cy + 0.055 * s, cy + 0.300 * s, 0.026 * s, 0.020 * s))
    m = np.maximum(m, taper(cx + 0.048 * s, cy + 0.055 * s, cy + 0.300 * s, 0.026 * s, 0.020 * s))
    m = np.maximum(m, taper(cx - 0.034 * s, cy + 0.300 * s, cy + 0.470 * s, 0.026 * s, 0.016 * s))
    m = np.maximum(m, taper(cx + 0.034 * s, cy + 0.300 * s, cy + 0.470 * s, 0.026 * s, 0.016 * s))

    a = (m * alpha)[..., None]
    img[...] = img * (1.0 - a) + col * a
