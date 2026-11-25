"""Low-level design / compositing toolkit (numpy float RGB)."""
import numpy as np
from PIL import Image

from .text_engine import rasterize, over, blend_onto, blur_alpha


# ---------------------------------------------------------------- canvas
def canvas(w, h, color=(0, 0, 0)):
    img = np.empty((h, w, 3), dtype=np.float32)
    img[...] = np.array(color, dtype=np.float32) / 255.0
    return img


def vgrad(w, h, stops):
    """Vertical gradient. stops = [(pos0..1, (r,g,b)), ...]"""
    ys = np.linspace(0, 1, h, dtype=np.float32)
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.array([s[1] for s in stops], dtype=np.float32) / 255.0
    out = np.empty((h, 3), dtype=np.float32)
    for c in range(3):
        out[:, c] = np.interp(ys, pos, cols[:, c])
    return np.repeat(out[:, None, :], w, axis=1)


def hgrad(w, h, stops):
    xs = np.linspace(0, 1, w, dtype=np.float32)
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.array([s[1] for s in stops], dtype=np.float32) / 255.0
    out = np.empty((w, 3), dtype=np.float32)
    for c in range(3):
        out[:, c] = np.interp(xs, pos, cols[:, c])
    return np.repeat(out[None, :, :], h, axis=0)


def radial_glow(w, h, cx, cy, radius, color, power=2.0, intensity=1.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(radius, 1e-3)
    falloff = np.clip(1.0 - d, 0, 1) ** power
    m = falloff * intensity
    out = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        out[..., c] = m * (color[c] / 255.0)
    return out


# ---------------------------------------------------------------- shapes
def rr_mask(w, h, box, radius):
    """Anti-aliased rounded-rect mask (float 0..1) covering full w,h."""
    x0, y0, x1, y1 = box
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = np.clip(xx, x0 + radius, x1 - radius)
    cy = np.clip(yy, y0 + radius, y1 - radius)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    inside = np.minimum(np.minimum(xx - x0, x1 - xx), np.minimum(yy - y0, y1 - yy))
    m = np.where(inside >= 0, np.clip((radius - d) + 0.5, 0, 1), 0.0)
    m = np.where(inside < 0, 0.0, m)
    m = np.where(inside >= radius, 1.0, m)
    return m.astype(np.float32)


def fill_rr(img, box, radius, color, alpha=1.0):
    m = rr_mask(img.shape[1], img.shape[0], box, radius) * alpha
    col = np.array(color, dtype=np.float32) / 255.0
    img[...] = img * (1 - m[..., None]) + col * m[..., None]
    return img


def stroke_rr(img, box, radius, color, width=2, alpha=1.0):
    inner = (box[0] + width, box[1] + width, box[2] - width, box[3] - width)
    m = rr_mask(img.shape[1], img.shape[0], box, radius) - rr_mask(
        img.shape[1], img.shape[0], inner, max(0, radius - width))
    m = np.clip(m, 0, 1) * alpha
    col = np.array(color, dtype=np.float32) / 255.0
    img[...] = img * (1 - m[..., None]) + col * m[..., None]
    return img


# ---------------------------------------------------------------- text
def draw_text(img, text, font="dev", size=60, color=(255, 255, 255), x=0, y=0,
              anchor="lt", stroke=0, stroke_color=(0, 0, 0), alpha=1.0,
              tracking=0.0, shadow=None, max_width=None, ss=1):
    """Draw shaped text onto float RGB image. Returns ink bbox."""
    if max_width is not None:
        while size > 8:
            from .text_engine import text_width
            if text_width(text, font, size, tracking) <= max_width:
                break
            size -= 2
    rgba, bb = rasterize(text, font, size, color, tracking, stroke, stroke_color,
                         shadow, alpha, supersample=ss)
    ox, oy, ex, ey = bb
    iw, ih = ex - ox, ey - oy
    hx = {"l": 0, "c": 0.5, "r": 1.0}[anchor[0]]
    vy = {"t": 0, "m": 0.5, "b": 1.0}[anchor[1]]
    px = int(round(x - ox - iw * hx))
    py = int(round(y - oy - ih * vy))
    blend_onto(img, rgba, px, py)
    return (int(x - iw * hx), int(y - ih * vy), int(x - iw * hx) + iw, int(y - ih * vy) + ih)


def text_size(text, font="dev", size=60, tracking=0.0):
    from .text_engine import layout
    _, w = layout(text, font, size, tracking)
    return w, size * 0.75


def fit_size(text, font, max_width, start=120, tracking=0.0):
    from .text_engine import text_width
    s = start
    while s > 10 and text_width(text, font, s, tracking) > max_width:
        s -= 2
    return s


# ---------------------------------------------------------------- effects
def grain(img, amount=0.035, seed=0, chroma=0.0):
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    n = rng.standard_normal((h, w), dtype=np.float32)
    if chroma > 0:
        out = img + (n * amount)[..., None]
        for c in range(3):
            out[..., c] += rng.standard_normal((h, w), dtype=np.float32) * amount * chroma
        return out
    return img + (n * amount)[..., None]


def vignette_mask(w, h, strength=0.75, power=2.2, cx=None, cy=None):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    d = np.sqrt(((xx - cx) / (w * 0.5)) ** 2 + ((yy - cy) / (h * 0.5)) ** 2)
    return (1.0 - strength * np.clip(d, 0, 1.4) ** power).clip(0, 1).astype(np.float32)


def apply_vignette(img, strength=0.75, power=2.2):
    m = vignette_mask(img.shape[1], img.shape[0], strength, power)
    return img * m[..., None]


def chroma_aberration(img, amount=2.0, axis=1):
    """Shift R and B channels in opposite directions."""
    out = img.copy()
    a = int(round(amount))
    if a <= 0:
        return out
    if axis == 1:
        out[:, :, 0] = np.roll(img[:, :, 0], a, axis=1)
        out[:, :, 2] = np.roll(img[:, :, 2], -a, axis=1)
    else:
        out[:, :, 0] = np.roll(img[:, :, 0], a, axis=0)
        out[:, :, 2] = np.roll(img[:, :, 2], -a, axis=0)
    return out


def scanlines(img, strength=0.08, period=4, offset=0):
    h = img.shape[0]
    yy = (np.arange(h) + offset) % period
    m = 1.0 - strength * (yy < period / 2)
    return img * m[:, None, None]


def bloom(img, threshold=0.72, radius=18, amount=0.35):
    from .text_engine import blur_alpha
    lum = img.max(axis=2)
    mask = np.clip((lum - threshold) / (1 - threshold + 1e-6), 0, 1)
    bl = np.zeros_like(img)
    for c in range(3):
        bl[..., c] = blur_alpha(img[..., c] * mask, radius)
    return img + bl * amount


def color_grade(img, lift=(0, 0, 0), gamma=(1, 1, 1), gain=(1, 1, 1), saturation=1.0,
                contrast=1.0, pivot=0.5):
    out = img.copy()
    out = out * np.array(gain, dtype=np.float32) + np.array(lift, dtype=np.float32)
    out = np.clip(out, 0, 4) ** np.array(gamma, dtype=np.float32)
    lum = out @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    out = lum[..., None] + (out - lum[..., None]) * saturation
    out = (out - pivot) * contrast + pivot
    return out


def add(img, layer):
    return img + layer


def screen(img, layer):
    return 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(layer, 0, 1))


def overlay(img, layer, alpha=1.0):
    return img * (1 - alpha) + layer * alpha


def to_uint8(img):
    return (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def save(img, path, quality=95):
    Image.fromarray(to_uint8(img)).save(path, quality=quality)


def load(path, w=None, h=None):
    im = Image.open(path).convert("RGB")
    if w and h:
        im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def cover(img, w, h, zoom=1.0, cx=0.5, cy=0.5):
    """Scale/crop img to fill w x h (like CSS object-fit: cover)."""
    ih, iw = img.shape[:2]
    scale = max(w / iw, h / ih) * zoom
    nw, nh = int(round(iw * scale)), int(round(ih * scale))
    im = Image.fromarray(to_uint8(img)).resize((nw, nh), Image.LANCZOS)
    x = int(round((nw - w) * cx))
    y = int(round((nh - h) * cy))
    x = max(0, min(nw - w, x))
    y = max(0, min(nh - h, y))
    return np.asarray(im, dtype=np.float32)[y:y + h, x:x + w] / 255.0


def paste_rgb(img, src, x, y):
    """Paste an opaque float RGB image onto img at integer (x, y), clipped."""
    H, W = img.shape[:2]
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return img
    img[y0:y1, x0:x1] = src[y0 - y:y1 - y, x0 - x:x1 - x]
    return img


# ---------------------------------------------------------------- cached grids
_GRIDS = {}


def grids(w, h):
    key = (w, h)
    if key not in _GRIDS:
        _GRIDS[key] = np.mgrid[0:h, 0:w].astype(np.float32)
    return _GRIDS[key]


class Layer:
    """Small RGBA drawing surface with proper alpha accumulation."""

    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.zeros((self.h, self.w), np.float32)

    def _comp(self, m, color):
        m = m.astype(np.float32)
        c = np.array(color, dtype=np.float32) / 255.0
        self.rgb = self.rgb * (1 - m[..., None]) + c * m[..., None]
        self.a = self.a * (1 - m) + m

    def fill(self, box, radius, color, alpha=1.0):
        self._comp(rr_mask(self.w, self.h, box, radius) * alpha, color)

    def stroke(self, box, radius, color, width=2, alpha=1.0):
        inner = (box[0] + width, box[1] + width, box[2] - width, box[3] - width)
        m = np.clip(rr_mask(self.w, self.h, box, radius) -
                    rr_mask(self.w, self.h, inner, max(0, radius - width)), 0, 1) * alpha
        self._comp(m, color)

    def text(self, s, font, size, color, x, y, anchor="lm", tracking=0.0,
             stroke=0, stroke_color=(0, 0, 0)):
        rgba, bb = rasterize(s, font, size, color, tracking, stroke, stroke_color, None, 1.0)
        ox, oy, ex, ey = bb
        iw, ih = ex - ox, ey - oy
        hx = {"l": 0, "c": 0.5, "r": 1}[anchor[0]]
        vy = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
        px, py = int(round(x - ox - iw * hx)), int(round(y - oy - ih * vy))
        self.sprite(rgba, px, py)

    def sprite(self, rgba, x, y):
        H, W = self.h, self.w
        h, w = rgba.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        sx, sy = x0 - x, y0 - y
        sp = rgba[sy:sy + (y1 - y0), sx:sx + (x1 - x0)]
        sa = sp[..., 3]
        da = self.a[y0:y1, x0:x1]
        oa = sa + da * (1 - sa)
        rgb = sp[..., :3] * sa[..., None] + self.rgb[y0:y1, x0:x1] * da[..., None] * (1 - sa[..., None])
        self.rgb[y0:y1, x0:x1] = np.divide(rgb, oa[..., None], out=np.zeros_like(rgb),
                                           where=oa[..., None] > 1e-6)
        self.a[y0:y1, x0:x1] = oa

    def rgba(self):
        out = np.zeros((self.h, self.w, 4), np.float32)
        out[..., :3] = self.rgb
        out[..., 3] = self.a
        return out
