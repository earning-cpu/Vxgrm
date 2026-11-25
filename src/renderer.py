"""Frame renderer: camera moves, kinetic typography, transitions, grade."""
import os
import subprocess
import numpy as np
from PIL import Image, ImageFilter
from functools import lru_cache

from . import design as D
from . import paper as P
from .text_engine import rasterize, blend_onto, blur_alpha, over
from . import timeline as TL

W, H = TL.W, TL.H
FPS = TL.FPS


# =============================================================== plates
class _PlateCache:
    def __init__(self, maxsize=4):
        self.maxsize = maxsize
        self.order = []
        self.data = {}

    def get(self, name, grade=None):
        key = (name, grade)
        if key in self.data:
            self.order.remove(key)
            self.order.append(key)
            return self.data[key]
        path = os.path.join("assets/img", name)
        im = Image.open(path).convert("RGB")
        iw, ih = im.size
        # pre-scale so that zoom=1 maps to W x H, with headroom for zoom
        base = max(W / iw, H / ih)
        s = base * 1.55
        nw, nh = int(iw * s), int(ih * s)
        im = im.resize((nw, nh), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.5, percent=38, threshold=3))
        arr = np.asarray(im, dtype=np.float32) / 255.0
        if grade:
            warm, sat, contrast, darken = grade
            arr = D.color_grade(arr, gain=(1.04, 1.01, 1.0), saturation=sat,
                                contrast=contrast)
            arr = np.clip(arr, 0, 1) ** 0.93
            arr = arr * 1.06 + 0.006
            if warm:
                arr = arr + np.array([0.03, 0.012, -0.02], dtype=np.float32) * warm
            if darken:
                arr = arr * (1 - darken)
        if len(self.order) >= self.maxsize:
            old = self.order.pop(0)
            self.data.pop(old, None)
        self.data[key] = arr
        self.order.append(key)
        return arr


PLATES = _PlateCache(4)


def camera(plate, zoom, cx, cy):
    """Crop a W x H window at (cx, cy) with the given zoom, from a pre-scaled plate."""
    ph, pw = plate.shape[:2]
    cw, ch = W / zoom, H / zoom
    # plate was scaled so that zoom=1 -> W x H; so crop size is (W/zoom, H/zoom)
    x = (pw - cw) * cx
    y = (ph - ch) * cy
    x = max(0, min(pw - cw, x))
    y = max(0, min(ph - ch, y))
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = x0 + int(round(cw)), y0 + int(round(ch))
    crop = plate[y0:y1, x0:x1]
    if crop.shape[1] == W and crop.shape[0] == H:
        return crop
    im = Image.fromarray(D.to_uint8(crop)).resize((W, H), Image.BILINEAR)
    return np.asarray(im, dtype=np.float32) / 255.0


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_out_back(x, s=1.9):
    x = np.clip(x, 0, 1)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def smoothstep(a, b, x):
    t = np.clip((x - a) / max(b - a, 1e-6), 0, 1)
    return t * t * (3 - 2 * t)


# =============================================================== text
_layer_cache = {}


def text_layer(text, font, size, color, stroke, tracking, ss=1):
    from .text_engine import resolve_font
    font = resolve_font(text, font)
    key = (text, font, size, color, stroke, tracking, ss)
    if key in _layer_cache:
        return _layer_cache[key]
    rgba, bb = rasterize(text, font, size, color, tracking, stroke, (0, 0, 0),
                         shadow=(0, 7, 9, 0.75), alpha=1.0, supersample=ss)
    if len(_layer_cache) > 220:
        _layer_cache.clear()
    _layer_cache[key] = (rgba, bb)
    return rgba, bb


def _rich_segments(cue):
    """Split a cue into (text, color) segments at word boundaries for highlighting."""
    if not cue.hl:
        return [(cue.text, cue.color)]
    idx = cue.text.find(cue.hl)
    if idx < 0:
        return [(cue.text, cue.color)]
    pre, mid, post = cue.text[:idx], cue.text[idx:idx + len(cue.hl)], cue.text[idx + len(cue.hl):]
    segs = []
    if pre:
        segs.append((pre, cue.color))
    segs.append((mid, cue.hl_color))
    if post:
        segs.append((post, cue.color))
    return segs


def _draw_pill(img, cue, t, alpha, scale, dy):
    """Red subscribe pill behind the CTA text. Returns horizontal text offset."""
    from .text_engine import text_width
    # text_layer renders at 1.3x then _place scales back, so ink is text_width*1.3*scale
    tw = text_width(cue.text, "dev_b", cue.size, cue.tracking) * 1.30 * scale
    pulse = 1.0 + 0.030 * np.sin((t - cue.t0) * 8.0)
    w = tw + cue.size * 2.45 * scale * pulse
    h = cue.size * 1.78 * scale * pulse
    cx, cy = cue.x * W, cue.y * H + dy
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    D.fill_rr(img, (x0 + 5, y0 + 12, x1 + 5, y1 + 12), h * 0.34, (0, 0, 0), 0.5 * alpha)
    D.fill_rr(img, (x0, y0, x1, y1), h * 0.34, (190, 20, 26), 0.97 * alpha)
    D.stroke_rr(img, (x0, y0, x1, y1), h * 0.34, (255, 132, 132), 2.2, 0.7 * alpha)
    # bell glyph
    bx, by = x0 + h * 0.52, cy - h * 0.02
    r = h * 0.125
    D.fill_rr(img, (bx - r, by - r * 1.1, bx + r, by + r * 0.5), r, (255, 255, 255), alpha)
    D.fill_rr(img, (bx - r * 0.40, by + r * 0.5, bx + r * 0.40, by + r * 0.88), r * 0.2,
              (255, 255, 255), alpha)
    D.fill_rr(img, (bx - r * 0.50, by - r * 1.50, bx + r * 0.50, by - r * 1.02), r * 0.3,
              (255, 255, 255), alpha)
    text_cx = x0 + h * 1.18 + tw / 2
    return text_cx - cx


def _place(img, rgba, x, y, scale=1.0, alpha=1.0):
    if scale <= 0.001 or alpha <= 0.002:
        return
    if abs(scale - 1.0) > 0.004:
        h, w = rgba.shape[:2]
        nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        im = Image.fromarray(D.to_uint8(rgba)).resize((nw, nh), Image.BILINEAR)
        rgba = np.asarray(im, dtype=np.float32) / 255.0
    if alpha < 0.998:
        rgba = rgba.copy()
        rgba[..., 3] *= alpha
    blend_onto(img, rgba, int(round(x)), int(round(y)))


def draw_cue(img, cue, t):
    """Draw a text cue on a torn-paper label (the film's type system)."""
    if t < cue.t0 - 0.001 or t > cue.t1 + 0.001:
        return
    p_in = np.clip((t - cue.t0) / max(cue.fade_in, 1e-3), 0, 1)
    p_out = np.clip((cue.t1 - t) / max(cue.fade_out, 1e-3), 0, 1)
    alpha = min(float(p_in), float(p_out)) ** 0.75

    scale, dy, dx = 1.0, 0.0, 0.0
    if cue.anim == "pop":
        e = ease_out_back(p_in, 1.6)
        scale = 0.72 + 0.28 * e
        dy = (1 - ease_out_cubic(p_in)) * 26
    elif cue.anim == "slide":
        dy = (1 - ease_out_cubic(p_in)) * 64
    elif cue.anim == "punch":
        k = np.clip((t - cue.t0) / 0.20, 0, 1)
        scale = 1.0 + 0.20 * (1 - k) ** 2
    elif cue.anim == "glitch":
        e = ease_out_cubic(p_in)
        scale = 0.92 + 0.08 * e
        dy = (1 - e) * 14
    elif cue.anim == "type":
        pass

    if cue.shake:
        rng = np.random.default_rng(int(t * 1000) % 99991)
        dx += rng.normal(0, cue.shake)
        dy += rng.normal(0, cue.shake)

    # ---------------------------------------------------------- ink layout
    base_col = _ink_color(cue.paper, cue.color)
    hl_col = _hl_ink(cue.paper)
    # ink printed on light card needs no outline; bone on dark card does
    base_stroke = 0 if cue.paper == "parchment" else cue.stroke
    segs = _rich_segments(cue)
    layers, total_w = [], 0.0
    for txt, col in segs:
        is_hl = col is cue.hl_color
        use = hl_col if is_hl else base_col
        st = (cue.stroke if is_hl else base_stroke)
        rgba, bb = text_layer(txt, cue.font, int(cue.size * 1.30), use, st, cue.tracking)
        ox, oy, ex, ey = bb
        layers.append([rgba, bb, (ex - ox) * scale, is_hl])
        total_w += (ex - ox) * scale

    if total_w > cue.max_w:
        f = cue.max_w / total_w
        scale *= f
        for L in layers:
            L[2] *= f
        total_w = cue.max_w

    # union of the ink's vertical extent, in layer space
    ink_top = min(L[1][1] for L in layers) * scale
    ink_bot = max(L[1][3] for L in layers) * scale
    ink_h = max(1.0, ink_bot - ink_top)

    cx = cue.x * W
    cy = cue.y * H + dy

    # ------------------------------------------------------- paper label
    if cue.paper:
        pad_x = cue.size * 0.40 * scale
        pad_y = cue.size * 0.30 * scale
        P.panel(img, cx - total_w / 2 - pad_x, cy - ink_h / 2 - pad_y,
                cx + total_w / 2 + pad_x, cy + ink_h / 2 + pad_y,
                _paper_color(cue.paper),
                seed=cue.seed if cue.seed else int(abs(hash(cue.text)) % 9973),
                alpha=alpha * cue.paper_alpha, rough=cue.paper_rough)

    # -------------------------------------------- oxide label behind a word
    x = cx - total_w / 2
    if cue.hl and cue.paper == "parchment":
        for rgba, bb, iw, is_hl in layers:
            if not is_hl:
                x += iw
                continue
            ox, oy, ex, ey = bb
            hx0 = x - ox * scale - cue.size * 0.20 * scale
            hx1 = x - ox * scale + iw + cue.size * 0.20 * scale
            hy0 = cy - ink_h / 2 + (oy * scale - ink_top) - cue.size * 0.10 * scale
            hy1 = cy - ink_h / 2 + (ey * scale - ink_top) + cue.size * 0.10 * scale
            P.panel(img, hx0, hy0, hx1, hy1, P.OXIDE,
                    seed=int(abs(hash(cue.text + cue.hl)) % 9973),
                    alpha=alpha * 0.98, rough=cue.paper_rough * 1.2,
                    shadow_px=8.0)
            x += iw

    # ------------------------------------------------------------- ink
    x = cx - total_w / 2
    for rgba, bb, iw, is_hl in layers:
        ox, oy, ex, ey = bb
        px = x - ox * scale
        py = cy - ink_h / 2 - ink_top          # shared origin: union of ink is centred
        _place(img, rgba, px + dx, py, scale, alpha)
        x += iw

    # ------------------------------------------------------------ sub line
    if cue.sub:
        rgba, bb = text_layer(cue.sub, "dev", int(cue.sub_size * 1.30), P.INK, 0, 0.0)
        ox, oy, ex, ey = bb
        iw = (ex - ox) * scale
        ih = (ey - oy) * scale
        sh = ih + cue.sub_size * 0.70 * scale
        px = cx - iw / 2
        py = cy + ink_h / 2 + cue.size * 0.52 * scale
        P.panel(img, px - cue.sub_size * 0.55 * scale, py,
                px + iw + cue.sub_size * 0.55 * scale, py + sh,
                P.PARCHMENT_DK, seed=int(abs(hash(cue.sub)) % 9973),
                alpha=alpha * 0.97, rough=cue.paper_rough, shadow_px=7.0)
        _place(img, rgba, px + dx, py + (sh - ih) / 2 - oy * scale, scale, alpha)


def _paper_color(kind):
    return {"parchment": P.PARCHMENT, "charcoal": P.CHARCOAL,
            "oxide": P.OXIDE}.get(kind, P.PARCHMENT)


def _ink_color(kind, fallback):
    if kind in ("charcoal", "oxide"):
        return P.BONE
    if kind == "parchment":
        return P.INK
    return fallback


def _hl_ink(kind):
    """Ink for the highlighted word. On dark card it must be a bright accent,
    never dark-on-dark."""
    return P.BONE if kind == "parchment" else (232, 92, 74)



# =============================================================== overlays
def draw_progress(img, t, t_start=0.0, t_end=66.20):
    """Thin paper ribbon along the very top: a retention cue, not a broadcast bar."""
    if t < t_start:
        return
    p = np.clip((t - t_start) / max(t_end - t_start, 1e-3), 0, 1)
    y, hh = 44, 5
    x0, x1 = 64, W - 64
    track = np.array([0.78, 0.74, 0.66], dtype=np.float32)
    fill = np.array([0.60, 0.13, 0.11], dtype=np.float32)
    reg = img[y:y + hh, x0:x1]
    reg[...] = reg * 0.30 + track * 0.70
    k = x0 + int((x1 - x0) * p)
    if k > x0:
        img[y:y + hh, x0:k] = fill


_TILE = {}


def _chapter_tile(label):
    key = ("chapter", label)
    if key in _TILE:
        return _TILE[key]
    rgba, bb = text_layer(label, "dev_b", 36, (224, 218, 208), 4, 0.0)
    ox, oy, ex, ey = bb
    tw = (ex - ox) + 44
    th = 52
    L = D.Layer(tw, th)
    L.fill((0, 0, tw, th), 6, (10, 10, 12), 0.62)
    L.stroke((0, 0, tw, th), 6, (198, 40, 44), 1.5, 0.9)
    L.fill((14, 16, 20, 36), 2, (198, 40, 44), 1.0)
    L.text(label, "dev_b", 36, (224, 218, 208), 32, th / 2, "lm", 0.0, 4, (0, 0, 0))
    out = L.rgba()
    _TILE[key] = out
    return out


def draw_badge(img, text="असली घटना", t=0.0):
    """Top-left authority badge (cached tile)."""
    key = ("badge", text)
    if key not in _TILE:
        rgba, bb = text_layer(text, "dev_b", 34, (240, 234, 224), 4, 0.0)
        ox, oy, ex, ey = bb
        tw = (ex - ox) + 46
        th = 58
        L = D.Layer(tw, th)
        L.fill((0, 0, tw, th), 8, (150, 22, 26), 0.92)
        L.stroke((0, 0, tw, th), 8, (226, 96, 96), 1.5, 1.0)
        L.fill((16, 22, 30, 36), 7, (255, 214, 214), 1.0)
        L.text(text, "dev_b", 34, (240, 234, 224), 40, th / 2, "lm", 0.0, 4, (0, 0, 0))
        _TILE[key] = L.rgba()
    blend_onto(img, _TILE[key], 46, 128)


def draw_rec(img, t):
    key = ("rec",)
    if key not in _TILE:
        L = D.Layer(190, 40)
        L.fill((0, 9, 22, 31), 11, (210, 30, 30), 1.0)
        L.text("REC", "bebas", 34, (232, 226, 216), 34, 20, "lm", 0.10, 3, (0, 0, 0))
        L.text("00:00:00", "bebas", 30, (200, 194, 186), 186, 20, "rm", 0.06, 3, (0, 0, 0))
        _TILE[key] = L.rgba()
    tile = _TILE[key]
    blink = 0.45 + 0.55 * abs(np.cos(t * 3.0))
    t2 = tile.copy()
    t2[..., 3] *= blink
    blend_onto(img, t2, W - 236, 200)


def draw_chapter(img, label, alpha=1.0):
    tile = _chapter_tile(label)
    if alpha < 0.999:
        tile = tile.copy()
        tile[..., 3] *= alpha
    blend_onto(img, tile, 46, 205)


def draw_dust(img, t, amount=1.0, seed=0):
    rng = np.random.default_rng(seed + 7)
    n = int(46 * amount)
    xs = rng.uniform(0, W, n)
    ys = rng.uniform(0, H, n)
    sz = rng.uniform(0.6, 2.6, n)
    sp = rng.uniform(8, 34, n)
    ph = rng.uniform(0, 6.28, n)
    br = rng.uniform(0.10, 0.55, n)
    for i in range(n):
        y = (ys[i] - t * sp[i]) % H
        x = (xs[i] + np.sin(t * 0.7 + ph[i]) * 16) % W
        r = int(max(1, sz[i]))
        v = br[i]
        yy, xx = int(y), int(x)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy > r * r:
                    continue
                py, px = yy + dy, xx + dx
                if 0 <= py < H and 0 <= px < W:
                    a = v * (1 - (dx * dx + dy * dy) / (r * r + 1e-6))
                    img[py, px] = img[py, px] * (1 - a) + np.array([0.95, 0.88, 0.72]) * a


# =============================================================== transitions
def apply_glitch(img, strength, t):
    if strength <= 0.01:
        return img
    rng = np.random.default_rng(int(t * 1000) % 7919)
    out = img.copy()
    # RGB split
    a = int(2 + 10 * strength)
    out[..., 0] = np.roll(img[..., 0], a, axis=1)
    out[..., 2] = np.roll(img[..., 2], -a, axis=1)
    # slice displacement
    n = 10
    for i in range(n):
        y0 = int(H * i / n)
        y1 = int(H * (i + 1) / n)
        if rng.random() < 0.55 * strength:
            dx = int(rng.normal(0, 40 * strength))
            out[y0:y1] = np.roll(out[y0:y1], dx, axis=1)
    return out


def apply_whip(img, p):
    """Horizontal motion smear for a whip pan."""
    if p <= 0.01:
        return img
    k = max(1, int(10 * p))
    acc = np.zeros_like(img)
    for i in range(k):
        dx = int((i - k / 2) * 26 * p)
        acc += np.roll(img, dx, axis=1)
    return acc / k


def apply_flash(img, strength, color=(255, 244, 236)):
    if strength <= 0.003:
        return img
    c = np.array(color, dtype=np.float32) / 255
    return img * (1 - strength) + c * strength


# =============================================================== frame
_VIG = None
_SCAN = None
_VIGPOW = {}


def _prep():
    global _VIG, _SCAN
    if _VIG is None:
        _VIG = D.vignette_mask(W, H, 0.42, 2.0)
        yy = np.arange(H)
        _SCAN = (1.0 - 0.055 * ((yy % 4) < 2)).astype(np.float32)[:, None, None]
    return _VIG, _SCAN


def _vig_pow(v):
    v = round(float(v), 2)
    if v not in _VIGPOW:
        _VIGPOW[v] = (_VIG ** v)[..., None]
    return _VIGPOW[v]


def render_frame(shots, t):
    # find shot
    cur = None
    for s in shots:
        if s.t0 - 1e-6 <= t < s.t1 - 1e-6:
            cur = s
            break
    if cur is None:
        cur = shots[-1]

    VIG, SCAN = _prep()
    lt = t - cur.t0
    dur = max(cur.t1 - cur.t0, 1e-3)
    p = np.clip(lt / dur, 0, 1)
    e = ease_out_cubic(p)

    if cur.black:
        img = D.canvas(W, H, (3, 3, 4))
        img += D.radial_glow(W, H, W * 0.5, H * 0.42, W * 1.1, (16, 14, 18), 2.0, 1.0)
    else:
        gk = (round(cur.warm, 2), round(cur.sat, 2), round(cur.contrast, 2),
              round(cur.darken, 2))
        plate = PLATES.get(cur.plate, gk)
        zoom = cur.z0 + (cur.z1 - cur.z0) * e
        cx = cur.cx + (cur.cx1 - cur.cx) * e
        cy = cur.cy + (cur.cy1 - cur.cy) * e
        if cur.handheld > 0:
            rng = np.random.default_rng(int(t * FPS) % 100003)
            cx += rng.normal(0, 0.0016 * cur.handheld)
            cy += rng.normal(0, 0.0022 * cur.handheld)
            zoom += rng.normal(0, 0.0016 * cur.handheld)
        zoom = max(0.9, zoom)
        img = camera(plate, zoom, float(np.clip(cx, 0, 1)), float(np.clip(cy, 0, 1)))

        # ---- grade is baked into the plate; only screen-space vignette here
        if cur.vignette:
            img *= _vig_pow(cur.vignette * 0.85)
        if cur.scan:
            img *= (1 - (1 - SCAN) * (cur.scan / 0.055))
        if cur.aber:
            img = D.chroma_aberration(img, cur.aber)

        # ---- per-shot effects
        if cur.shake:
            rng = np.random.default_rng(int(t * FPS) % 7717)
            img = np.roll(img, int(rng.normal(0, cur.shake)), axis=1)
            img = np.roll(img, int(rng.normal(0, cur.shake * 0.7)), axis=0)
        if cur.dust:
            draw_dust(img, t, cur.dust, seed=hash(cur.plate) % 97)

        # ---- transitions
        if cur.trans == "whip":
            pp = 1 - np.clip(lt / 0.42, 0, 1)
            img = apply_whip(img, pp ** 2)
        if cur.trans == "glitch":
            g = (1 - np.clip(lt / 0.34, 0, 1)) ** 2
            img = apply_glitch(img, g * 0.9, t)
        if cur.flash:
            f = cur.flash * (1 - np.clip(lt / 0.22, 0, 1)) ** 2
            img = apply_flash(img, f, (255, 236, 228))

    # ---- global grain
    rng = np.random.default_rng(int(t * 1000) % 26699)
    g = rng.standard_normal((H // 2, W // 2), dtype=np.float32)
    g = np.repeat(np.repeat(g, 2, axis=0), 2, axis=1)[:H, :W]
    img = img + (g * 0.017)[..., None]

    # ---- overlays
    draw_progress(img, t)
    if cur.chapter:
        draw_chapter(img, cur.chapter, alpha=float(np.clip((cur.t1 - t) / 0.3, 0, 1)))
    if cur.rec:
        draw_rec(img, t)

    for c in cur.cues:
        draw_cue(img, c, t)

    return img


# =============================================================== encode
def render(shots, out_path, audio_path=None, t0=0.0, t1=None, progress=True):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    t1 = TL.VIDEO_END if t1 is None else t1
    n = int(round((t1 - t0) * FPS))
    cmd = [exe, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio_path:
        cmd += ["-ss", str(t0), "-t", str(t1 - t0), "-i", audio_path]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "21",
            "-maxrate", "11M", "-bufsize", "22M",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
            "-x264-params", "keyint=60:min-keyint=30:scenecut=0",
            "-movflags", "+faststart"]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out_path]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    for i in range(n):
        t = t0 + i / FPS
        fr = render_frame(shots, t)
        proc.stdin.write(D.to_uint8(fr).tobytes())
        if progress and i % 150 == 0:
            print(f"  frame {i}/{n}  t={t:.2f}s", flush=True)
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "ignore")
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(err[-3000:])
    return out_path
