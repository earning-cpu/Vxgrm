"""Devanagari text renderer using HarfBuzz shaping + FreeType rasterization.

Gives per-glyph control (needed for kinetic typography, per-word highlight,
glitch slices and word-by-word pop animation).
"""
import numpy as np
import uharfbuzz as hb
import freetype
from functools import lru_cache

FONT_DIR = "assets/fonts"
FONTS = {
    "dev":     f"{FONT_DIR}/NotoSansDevanagari.ttf",
    "dev_b":   f"{FONT_DIR}/NotoSansDevanagari-Bold.ttf",
    "serif":   f"{FONT_DIR}/NotoSerifDevanagari.ttf",
    "serif_b": f"{FONT_DIR}/NotoSerifDevanagari-Bold.ttf",
    "anton":   f"{FONT_DIR}/Anton.ttf",
    "bebas":   f"{FONT_DIR}/BebasNeue.ttf",
}


@lru_cache(maxsize=32)
def _hb_font(path):
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    f = hb.Font(face)
    f.scale = (face.upem, face.upem)
    return f, face.upem


@lru_cache(maxsize=16)
def _ft_face(path):
    return freetype.Face(path)


DEVANAGARI = "\u0900-\u097F"


def has_devanagari(text):
    return any("\u0900" <= ch <= "\u097F" for ch in text)


def resolve_font(text, font_key):
    """Anton / Bebas Neue carry no Devanagari glyphs - fall back to the sans."""
    if has_devanagari(text) and font_key in ("anton", "bebas"):
        return "dev_b"
    return font_key


def shape(text, font_key="dev", features=None):
    font_key = resolve_font(text, font_key)
    """Return (glyph list, upem) for a string.

    glyph = dict(gid, adv, xo, yo, cluster)
    """
    path = FONTS[font_key]
    font, upem = _hb_font(path)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {"kern": True, "liga": True})
    out = [
        dict(gid=i.codepoint, adv=p.x_advance, xo=p.x_offset, yo=p.y_offset, cluster=i.cluster)
        for i, p in zip(buf.glyph_infos, buf.glyph_positions)
    ]
    return out, upem


def layout(text, font_key="dev", size=100, tracking=0.0):
    """Layout text at pixel size. Returns (glyph list with px coords, width)."""
    glyphs, upem = shape(text, font_key)
    s = size / upem
    x = 0.0
    out = []
    for g in glyphs:
        out.append(dict(gid=g["gid"], x=x + g["xo"] * s, y=-g["yo"] * s,
                        adv=g["adv"] * s, cluster=g["cluster"]))
        x += g["adv"] * s + tracking * size
    return out, x


def text_width(text, font_key="dev", size=100, tracking=0.0):
    return layout(text, font_key, size, tracking)[1]


def text_height(text, font_key="dev", size=100):
    """Ink height of the rendered text."""
    return 0.0


@lru_cache(maxsize=200000)
def _glyph_bitmap(gid, path, size):
    face = freetype.Face(path)
    face.set_char_size(int(size * 64))
    face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_LIGHT)
    bmp = face.glyph.bitmap
    w, h = bmp.width, bmp.rows
    if w == 0 or h == 0:
        return None, 0, 0
    try:
        buf = np.frombuffer(bytes(bmp.buffer), dtype=np.uint8).reshape(h, w).copy()
    except Exception:
        buf = np.asarray(bmp.buffer, dtype=np.uint8).reshape(h, w).copy()
    return (buf, bmp.width, bmp.rows), face.glyph.bitmap_left, face.glyph.bitmap_top


def rasterize(text, font_key="dev", size=100, color=(255, 255, 255), tracking=0.0,
              stroke=0, stroke_color=None, shadow=None, alpha=1.0, supersample=1):
    """Render text to a float RGBA numpy array (H,W,4) with values 0..1.

    stroke:   outline width in px (drawn under the fill)
    shadow:   (dx, dy, blur, opacity) or None
    supersample: render at Nx then downsample (antialiasing for small text)
    """
    path = FONTS[font_key]
    if supersample != 1:
        return _rasterize_ss(text, font_key, size, color, tracking, stroke, stroke_color,
                             shadow, alpha, supersample)
    glyphs, width = layout(text, font_key, size, tracking)
    face = freetype.Face(path)
    face.set_char_size(int(size * 64))
    asc = face.size.height / 64.0

    pad = int(size * 0.5) + stroke * 2 + 2
    W = int(np.ceil(width)) + pad * 2
    H = int(np.ceil(asc)) + pad * 2
    alpha_map = np.zeros((H, W), dtype=np.float32)

    for g in glyphs:
        got, left, top = _glyph_bitmap(g["gid"], path, size)
        if got is None:
            continue
        buf = got[0]
        h, w = buf.shape
        ox = int(round(g["x"] + left + pad))
        oy = int(round(pad + asc * 0.80 - top - g["y"]))
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(W, ox + w), min(H, oy + h)
        if x1 <= x0 or y1 <= y0:
            continue
        sub = buf[y0 - oy:y1 - oy, x0 - ox:x1 - ox].astype(np.float32) / 255.0
        alpha_map[y0:y1, x0:x1] = np.maximum(alpha_map[y0:y1, x0:x1], sub)

    out = np.zeros((H, W, 4), dtype=np.float32)
    out[..., 0] = color[0] / 255.0
    out[..., 1] = color[1] / 255.0
    out[..., 2] = color[2] / 255.0
    out[..., 3] = alpha_map * alpha

    if stroke > 0:
        grown = grow_alpha(alpha_map, stroke)
        sc = stroke_color if stroke_color else (0, 0, 0)
        lay = np.zeros((H, W, 4), dtype=np.float32)
        lay[..., 0], lay[..., 1], lay[..., 2] = sc[0] / 255.0, sc[1] / 255.0, sc[2] / 255.0
        lay[..., 3] = grown * alpha
        out = over(lay, out)  # stroke UNDER fill

    if shadow is not None:
        dx, dy, blur, op = shadow
        sh = np.zeros((H, W, 4), dtype=np.float32)
        sh[..., 3] = blur_alpha(alpha_map, blur) * op * alpha
        canvas = np.zeros((H + abs(dy) + blur * 2, W + abs(dx) + blur * 2, 4), dtype=np.float32)
        ox = max(0, dx) + blur
        oy = max(0, dy) + blur
        canvas[oy:oy + H, ox:ox + W] = sh
        canvas2 = np.zeros_like(canvas)
        ox2 = max(0, -dx) + blur
        oy2 = max(0, -dy) + blur
        canvas2[oy2:oy2 + H, ox2:ox2 + W] = out
        out = over(canvas2, canvas)

    ys, xs = np.where(out[..., 3] > 0.004)
    if len(ys) == 0:
        return out, (0, 0, out.shape[1], out.shape[0])
    return out, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def _rasterize_ss(text, font_key, size, color, tracking, stroke, stroke_color, shadow, alpha, ss):
    big, bbox = rasterize(text, font_key, size * ss, color, tracking, stroke * ss,
                          stroke_color, shadow, alpha, supersample=1)
    H = (big.shape[0] // ss) * ss
    W = (big.shape[1] // ss) * ss
    big = big[:H, :W]
    small = big.reshape(H // ss, ss, W // ss, ss, 4).mean(axis=(1, 3))
    bbox2 = (bbox[0] // ss, bbox[1] // ss, int(np.ceil(bbox[2] / ss)), int(np.ceil(bbox[3] / ss)))
    return small.astype(np.float32), bbox2


def grow_alpha(a, r):
    """Square dilation by r px (cheap, no scipy)."""
    if r <= 0:
        return a
    out = a.copy()
    for _ in range(int(r)):
        p = np.pad(out, 1, mode="constant")
        out = np.maximum.reduce([
            p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1],
            p[1:-1, :-2], p[1:-1, 2:],
        ])
    return out


def blur_alpha(a, r):
    """Separable box blur, 3 passes (approximates gaussian). Preserves shape."""
    if r <= 0:
        return a
    out = np.asarray(a, dtype=np.float32).copy()
    r = int(r)
    k = 2 * r
    for _ in range(3):
        # vertical
        p = np.pad(out, ((r, r), (0, 0)), mode="constant")
        c = np.cumsum(p, axis=0, dtype=np.float32)
        out = (c[k:] - c[:-k]) / k
        # horizontal
        p = np.pad(out, ((0, 0), (r, r)), mode="constant")
        c = np.cumsum(p, axis=1, dtype=np.float32)
        out = (c[:, k:] - c[:, :-k]) / k
    return out


def over(dst, src):
    """Porter-Duff 'over' compositing for float RGBA (premultiplied-safe)."""
    sa = src[..., 3:4]
    da = dst[..., 3:4]
    oa = sa + da * (1 - sa)
    rgb = src[..., :3] * sa + dst[..., :3] * da * (1 - sa)
    out = np.empty_like(dst)
    out[..., :3] = np.divide(rgb, oa, out=np.zeros_like(rgb), where=oa > 1e-6)
    out[..., 3:4] = oa
    return out


def blend_onto(dst_rgb, src_rgba, x, y):
    """Alpha-composite src RGBA (float) onto dst RGB float array at integer (x,y)."""
    H, W = dst_rgb.shape[:2]
    h, w = src_rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return dst_rgb
    sx0, sy0 = x0 - x, y0 - y
    s = src_rgba[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = s[..., 3:4]
    dst_rgb[y0:y1, x0:x1] = dst_rgb[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a
    return dst_rgb
