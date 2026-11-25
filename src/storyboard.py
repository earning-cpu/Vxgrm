"""Renders storyboard sheets (analysis deliverables) for the competing concepts."""
import numpy as np
from PIL import Image

from . import design as D
from .text_engine import rasterize, blend_onto

W = 1960
MARGIN = 26
COLS = 5
GUT = 18
PW = (W - 2 * MARGIN - (COLS - 1) * GUT) // COLS      # panel width
PH = int(PW * 16 / 9)                                  # panel height (9:16)
CAP_H = 196

RED = (198, 24, 32)
BONE = (232, 226, 214)
DIM = (138, 134, 130)
GOLD = (214, 168, 74)


def _panel_caption(img, x, y, w, h, num, tc, shot, desc, cam, audio):
    D.fill_rr(img, (x, y, x + w, y + h), 10, (16, 16, 19), 1.0)
    D.stroke_rr(img, (x, y, x + w, y + h), 10, (46, 44, 46), 1)
    # number + timecode
    D.draw_text(img, f"{num:02d}", "bebas", 34, RED, x + 12, y + 8, "lt")
    D.draw_text(img, tc, "bebas", 22, BONE, x + w - 12, y + 14, "rt", tracking=0.06)
    D.draw_text(img, shot.upper(), "bebas", 17, GOLD, x + 12, y + 46, "lt", tracking=0.12)
    # description, wrapped
    _wrap(img, desc, "dev", 17, (206, 202, 196), x + 12, y + 74, w - 24, 3, lh=25)
    # camera / audio
    D.draw_text(img, "CAM", "bebas", 13, (90, 88, 86), x + 12, y + h - 34, "lt", tracking=0.1)
    _wrap(img, cam, "dev", 14, (150, 146, 142), x + 48, y + h - 36, w - 60, 1, lh=18)
    D.draw_text(img, "SFX", "bebas", 13, (90, 88, 86), x + 12, y + h - 15, "lt", tracking=0.1)
    _wrap(img, audio, "dev", 14, (150, 146, 142), x + 48, y + h - 17, w - 60, 1, lh=18)


def _wrap(img, text, font, size, color, x, y, max_w, max_lines=3, lh=None):
    """Naive word wrap for Devanagari/Latin mixed text."""
    from .text_engine import text_width
    lh = lh or int(size * 1.35)
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(trial, font, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines[:max_lines]):
        D.draw_text(img, ln, font, size, color, x, y + i * lh, "lt")


def _check(img, cx, cy, size, color):
    """Draw a bold check mark with PIL (glyph not present in Bebas)."""
    from PIL import ImageDraw, ImageFont
    lay = Image.new("L", (size * 3, size * 3), 0)
    d = ImageDraw.Draw(lay)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size * 2)
    d.text((size * 0.4, size * 0.2), "✓", font=f, fill=255)
    m = np.asarray(lay, dtype=np.float32) / 255.0
    m = m[:size * 2, :size * 2]
    h, w = m.shape
    ox, oy = int(cx - w / 2), int(cy - h / 2)
    for yy in range(h):
        for xx in range(w):
            a = m[yy, xx]
            if a > 0.02:
                py, px = oy + yy, ox + xx
                if 0 <= py < img.shape[0] and 0 <= px < img.shape[1]:
                    img[py, px] = img[py, px] * (1 - a) + np.array(color, dtype=np.float32) / 255 * a


def _header(img, index, kicker, title_hn, logline, tags):
    h0 = 40
    D.draw_text(img, f"STORYBOARD {index:02d} / 03", "bebas", 26, RED, MARGIN, h0, "lt",
                tracking=0.18)
    D.draw_text(img, "VXGRM  •  HINDI HORROR SHORTS  •  TRUE STORY", "bebas", 22, DIM,
                W - MARGIN, h0 + 4, "rt", tracking=0.14)
    D.draw_text(img, title_hn, "serif_b", 104, BONE, MARGIN, h0 + 52, "lt", tracking=-0.01)
    D.draw_text(img, logline, "dev", 27, (176, 172, 166), MARGIN, h0 + 190, "lt")
    # tags
    tx = MARGIN
    ty = h0 + 246
    for t in tags:
        tw = int(D.text_size(t, "bebas", 20, 0.1)[0]) + 26
        D.fill_rr(img, (tx, ty, tx + tw, ty + 34), 6, (30, 12, 14), 1.0)
        D.stroke_rr(img, (tx, ty, tx + tw, ty + 34), 6, (86, 30, 34), 1)
        D.draw_text(img, t, "bebas", 20, (214, 150, 150), tx + 13, ty + 17, "lm", tracking=0.1)
        tx += tw + 10
    return ty + 34


def _footer(img, y, score_rows, verdict, approved):
    hh = 350
    D.fill_rr(img, (MARGIN, y, W - MARGIN, y + hh), 12, (13, 13, 16), 1.0)
    D.stroke_rr(img, (MARGIN, y, W - MARGIN, y + hh), 12, (48, 46, 48), 1)

    # ---- left: scoring bars
    lx = MARGIN + 26
    D.draw_text(img, "SCORING", "bebas", 24, GOLD, lx, y + 20, "lt", tracking=0.16)
    bar_x = lx + 330
    bar_w = 700
    by = y + 66
    for i, (label, val, note) in enumerate(score_rows):
        yy = by + i * 38
        D.draw_text(img, label, "dev", 18, (186, 182, 176), lx, yy + 9, "lm")
        D.fill_rr(img, (bar_x, yy + 2, bar_x + bar_w, yy + 20), 5, (28, 28, 32), 1.0)
        D.fill_rr(img, (bar_x, yy + 2, bar_x + int(bar_w * val / 10), yy + 20), 5,
                  (150, 26, 32) if val < 7 else (186, 140, 52), 1.0)
        D.draw_text(img, f"{val:.1f}", "bebas", 21, BONE, bar_x + bar_w + 14, yy + 11, "lm")
        if note:
            D.draw_text(img, note, "dev", 14, (118, 116, 112), bar_x + bar_w + 74, yy + 11, "lm")

    # ---- divider
    dx = W - MARGIN - 590
    D.fill_rr(img, (dx, y + 20, dx + 1, y + hh - 20), 0, (58, 56, 58), 1.0)

    # ---- right: verdict
    vx = dx + 30
    vw = W - MARGIN - 30 - vx
    D.draw_text(img, "VERDICT", "bebas", 24, GOLD, vx, y + 20, "lt", tracking=0.16)
    _wrap(img, verdict, "dev", 19, (206, 202, 196), vx, y + 58, vw, 5, lh=28)
    bw = 240
    bx = vx + (vw - bw) // 2
    if approved:
        D.fill_rr(img, (bx, y + hh - 78, bx + bw, y + hh - 26), 8, (150, 26, 32), 1.0)
        _check(img, bx + 34, y + hh - 52, 24, (255, 255, 255))
        D.draw_text(img, "APPROVED", "bebas", 30, (255, 255, 255), bx + 56, y + hh - 52,
                    "lm", tracking=0.12)
    else:
        D.stroke_rr(img, (bx, y + hh - 78, bx + bw, y + hh - 26), 8, (72, 70, 72), 2)
        D.draw_text(img, "NOT SELECTED", "bebas", 25, (152, 148, 144), bx + bw // 2,
                    y + hh - 52, "cm", tracking=0.12)


def render(path, index, title_hn, logline, tags, panels, score_rows, verdict, approved):
    rows = (len(panels) + COLS - 1) // COLS
    header_h = 340
    total_h = header_h + rows * (PH + CAP_H + GUT) + 400
    img = D.canvas(W, total_h, (8, 8, 10))
    img = D.apply_vignette(img, 0.55, 2.0)

    _header(img, index, "", title_hn, logline, tags)

    top = header_h
    for i, p in enumerate(panels):
        c, r = i % COLS, i // COLS
        x = MARGIN + c * (PW + GUT)
        y = top + r * (PH + CAP_H + GUT)
        frame = p["frame"]
        # image
        D.paste_rgb(img, frame, x, y)
        D.stroke_rr(img, (x, y, x + PW, y + PH), 3, (40, 40, 44), 1)
        _panel_caption(img, x, y + PH + 8, PW, CAP_H, i + 1, p["tc"], p["shot"],
                       p["desc"], p["cam"], p["audio"])

    _footer(img, total_h - 386, score_rows, verdict, approved)
    img = D.grain(img, 0.012, seed=hash(path) % 1000)
    D.save(img, path, quality=92)
    return path


# --------------------------------------------------------------- styleframes
def _erosion(seed, w, h, amount=0.55):
    rng = np.random.default_rng(seed)
    n = rng.random((h, w), dtype=np.float32)
    return np.clip((n - amount) * 3.0 + 1.0, 0, 1)


def _chalk_text(img, text, font, size, x, y, anchor="cm", color=(226, 222, 210), seed=0):
    """Draw text then distress it so it reads as chalk on a rough surface."""
    from . import design as D
    from .text_engine import rasterize, blend_onto
    rgba, bb = rasterize(text, font, size, color, tracking=0.0, alpha=1.0, supersample=2)
    h, w = rgba.shape[:2]
    ero = _erosion(seed, w, h, 0.42)
    # vertical drip streaks
    rng = np.random.default_rng(seed + 5)
    streak = np.ones((h, w), dtype=np.float32)
    for _ in range(28):
        cx = rng.integers(0, w)
        cy = rng.integers(0, h)
        ln = rng.integers(4, 26)
        for t in range(ln):
            yy = cy + t
            if 0 <= yy < h and 0 <= cx < w:
                streak[yy, cx] *= rng.uniform(0.55, 0.95)
    rgba[..., 3] *= ero * streak
    ox, oy, ex, ey = bb
    iw, ih = ex - ox, ey - oy
    hx = {"l": 0, "c": 0.5, "r": 1.0}[anchor[0]]
    vy = {"t": 0, "m": 0.5, "b": 1.0}[anchor[1]]
    blend_onto(img, rgba, int(x - ox - iw * hx), int(y - oy - ih * vy))


def _carved_text(img, text, font, size, x, y, anchor="cm", seed=0):
    """Text that looks chiselled into stone: dark cut with a lit lower edge."""
    from .text_engine import rasterize, blend_onto
    rgba, bb = rasterize(text, font, size, (8, 7, 6), alpha=1.0, supersample=2)
    h, w = rgba.shape[:2]
    rgba[..., 3] *= _erosion(seed, w, h, 0.30)
    ox, oy, ex, ey = bb
    iw, ih = ex - ox, ey - oy
    hx = {"l": 0, "c": 0.5, "r": 1.0}[anchor[0]]
    vy = {"t": 0, "m": 0.5, "b": 1.0}[anchor[1]]
    px, py = int(x - ox - iw * hx), int(y - oy - ih * vy)
    # lit edge
    edge = np.zeros_like(rgba)
    edge[..., 0] = 0.42; edge[..., 1] = 0.38; edge[..., 2] = 0.33
    edge[..., 3] = np.roll(rgba[..., 3], 3, axis=0) * 0.55
    blend_onto(img, edge, px, py)
    blend_onto(img, rgba, px, py)


def styleframe_desert(i):
    """Rajasthan desert at dusk with ruined havelis."""
    img = D.vgrad(PW, PH, [(0.0, (26, 30, 52)), (0.28, (86, 62, 74)), (0.46, (176, 112, 66)),
                           (0.60, (120, 74, 46)), (1.0, (26, 18, 16))])
    sx, sy = PW * 0.50, PH * 0.40
    img += D.radial_glow(PW, PH, sx, sy, PW * 0.95, (255, 168, 96), 2.2, 0.55)
    img = D.screen(img, D.radial_glow(PW, PH, sx, sy, PW * 0.30, (255, 226, 176), 2.2, 0.95))
    img = D.screen(img, D.radial_glow(PW, PH, sx, sy, PW * 0.11, (255, 248, 226), 2.0, 1.0))
    # birds
    for bx, by, sc in [(0.24, 0.22, 1.0), (0.30, 0.18, 0.7), (0.72, 0.26, 0.8)]:
        _bird(img, PW * bx, PH * by, 9 * sc, (20, 14, 16))
    # dunes
    yy = np.arange(PH, dtype=np.float32)[:, None]
    xx = np.arange(PW, dtype=np.float32)[None, :]
    for k, (base, amp, col, fr) in enumerate([
            (PH * 0.60, PW * 0.05, (188, 122, 70), 1.0),
            (PH * 0.70, PW * 0.045, (132, 84, 54), 1.5),
            (PH * 0.80, PW * 0.035, (78, 52, 38), 2.1),
            (PH * 0.90, PW * 0.025, (40, 28, 24), 2.8)]):
        wave = base + amp * np.sin(xx / PW * 6.28 * fr + k * 1.9) + amp * 0.4 * np.sin(
            xx / PW * 6.28 * fr * 2.7 + k)
        m = (yy > wave).astype(np.float32)
        m = D.blur_alpha(m, 3)[..., None]
        img = img * (1 - m) + np.array(col, dtype=np.float32)[None, None, :] / 255 * m
    # ruined havelis on the horizon
    ru = np.zeros((PH, PW, 3), dtype=np.float32)
    for hx, hw, hh, st in [(0.10, 0.11, 0.30, 0.0), (0.24, 0.08, 0.22, 0.02),
                           (0.62, 0.09, 0.26, 0.03), (0.74, 0.12, 0.34, 0.0)]:
        x0 = PW * (hx + st); x1 = x0 + PW * hw
        y1 = PH * 0.62; y0 = y1 - PH * hh
        D.fill_rr(ru, (x0, y0, x1, y1), 1, (22, 15, 16), 1.0)
        # broken top
        for kk in range(5):
            bx0 = x0 + (x1 - x0) * kk / 5
            D.fill_rr(ru, (bx0, y0 + PH * 0.02 * (kk % 2), bx0 + (x1 - x0) / 5 - 2, y0 + PH * 0.05),
                      0, (22, 15, 16), 1.0)
        # arched windows (lit)
        for kk in range(2):
            wx = x0 + (x1 - x0) * (0.28 + kk * 0.42)
            wy = y0 + PH * 0.06
            D.fill_rr(ru, (wx - 7, wy, wx + 7, wy + 26), 7, (255, 176, 96), 1.0)
    m = ru.max(axis=2, keepdims=True) * 0.95
    img = img * (1 - m) + ru * m
    img = D.apply_vignette(img, 0.62, 2.0)
    return D.grain(img, 0.030, 100 + i)


def _bird(img, cx, cy, s, col):
    s = int(round(s))
    for t in range(-s, s + 1):
        yy = int(cy + abs(t) * 0.55)
        xx = int(cx + t)
        if 0 <= yy < img.shape[0] and 0 <= xx < img.shape[1]:
            img[yy, xx] = np.array(col, dtype=np.float32) / 255
            if xx + 1 < img.shape[1]:
                img[yy, xx + 1] = np.array(col, dtype=np.float32) / 255


def styleframe_door(i):
    """A village door with 'नाले बा' scrawled in chalk."""
    img = D.vgrad(PW, PH, [(0.0, (16, 16, 18)), (0.45, (34, 31, 28)), (1.0, (7, 7, 8))])
    img += D.radial_glow(PW, PH, PW * 0.5, PH * 0.10, PW * 1.1, (140, 126, 96), 2.2, 0.42)
    dx0, dy0, dx1, dy1 = PW * 0.15, PH * 0.10, PW * 0.85, PH * 0.94
    D.fill_rr(img, (dx0, dy0, dx1, dy1), 4, (52, 40, 30), 1.0)
    # planks
    for k in range(5):
        px = dx0 + (dx1 - dx0) * k / 5
        D.fill_rr(img, (px, dy0, px + 2, dy1), 0, (26, 20, 16), 1.0)
    D.stroke_rr(img, (dx0, dy0, dx1, dy1), 4, (18, 14, 12), 8, 1.0)
    # iron studs
    for ry in (0.16, 0.84):
        for rx in (0.25, 0.5, 0.75):
            cx, cy = PW * rx, PH * ry
            D.fill_rr(img, (cx - 5, cy - 5, cx + 5, cy + 5), 5, (38, 34, 30), 1.0)
            D.fill_rr(img, (cx - 2, cy - 2, cx + 2, cy + 2), 2, (92, 84, 74), 1.0)
    # grain / peeling paint
    rng = np.random.default_rng(40 + i)
    for _ in range(900):
        x, y = int(rng.uniform(dx0, dx1)), int(rng.uniform(dy0, dy1))
        img[y, x] *= rng.uniform(0.86, 1.14)
    _chalk_text(img, "नाले बा", "dev_b", int(PW * 0.30), PW * 0.50, PH * 0.50, "cm",
                (226, 222, 208), 40 + i)
    _chalk_text(img, "कल आना", "dev", int(PW * 0.11), PW * 0.50, PH * 0.64, "cm",
                (200, 194, 180), 44 + i)
    return D.apply_vignette(D.grain(img, 0.028, 200 + i), 0.6, 2.0)


def styleframe_street(i):
    """Empty village street at night, one lamp, volumetric cone."""
    img = D.vgrad(PW, PH, [(0.0, (8, 11, 18)), (0.5, (20, 23, 28)), (1.0, (6, 7, 9))])
    lx, ly = PW * 0.5, PH * 0.26
    # volumetric cone
    yy = np.arange(PH, dtype=np.float32)[:, None]
    xx = np.arange(PW, dtype=np.float32)[None, :]
    spread = (yy - ly) * 0.55
    cone = np.clip(1.0 - np.abs(xx - lx) / np.maximum(spread, 1e-3), 0, 1)
    cone *= np.clip((yy - ly) / 60.0, 0, 1) * np.clip(1.0 - (yy - ly) / (PH * 0.72), 0, 1)
    img += cone[..., None] * np.array([0.55, 0.42, 0.22], dtype=np.float32) * 0.55
    img += D.radial_glow(PW, PH, lx, ly, PW * 0.55, (255, 198, 116), 2.6, 0.85)
    img = D.screen(img, D.radial_glow(PW, PH, lx, ly, PW * 0.055, (255, 246, 224), 2.0, 1.0))
    # houses
    for x0, x1 in [(0, PW * 0.28), (PW * 0.72, PW)]:
        D.fill_rr(img, (x0, PH * 0.34, x1, PH), 1, (9, 11, 13), 1.0)
        for k in range(3):
            wx = x0 + (x1 - x0) * (0.3 + 0.4 * (k % 2))
            wy = PH * (0.40 + k * 0.13)
            D.fill_rr(img, (wx - 13, wy, wx + 13, wy + 22), 2, (26, 24, 20), 1.0)
    # road + shadows
    D.fill_rr(img, (PW * 0.28, PH * 0.46, PW * 0.72, PH), 0, (15, 16, 17), 0.5)
    img = D.apply_vignette(img, 0.75, 2.1)
    return D.grain(img, 0.032, 300 + i)


def styleframe_ear(i):
    """Abstract listening / waveform frame."""
    img = D.vgrad(PW, PH, [(0.0, (10, 10, 12)), (1.0, (4, 4, 5))])
    for k, r in enumerate([0.50, 0.40, 0.30, 0.20]):
        img += D.radial_glow(PW, PH, PW * 0.5, PH * 0.44, PW * r, (86, 104, 122), 2.2,
                             0.16 + k * 0.10)
    rng = np.random.default_rng(3 + i)
    n = 260
    env = np.abs(np.sin(np.linspace(0, 9, n))) ** 1.6
    ys = np.abs(rng.standard_normal(n)) ** 0.55 * env
    xs = np.linspace(PW * 0.08, PW * 0.92, n)
    mid = PH * 0.62
    prev = None
    for a, b, ya, yb in zip(xs[:-1], xs[1:], ys[:-1], ys[1:]):
        p0 = (int(a), int(mid - ya * PH * 0.20))
        p1 = (int(b), int(mid - yb * PH * 0.20))
        _line(img, p0, p1, (0.30, 0.88, 0.76))
        p0b = (int(a), int(mid + ya * PH * 0.20))
        p1b = (int(b), int(mid + yb * PH * 0.20))
        _line(img, p0b, p1b, (0.24, 0.74, 0.64))
    return D.grain(img, 0.030, 400 + i)


def _line(img, p0, p1, col, thick=1):
    x0, y0 = p0; x1, y1 = p1
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    c = np.array(col, dtype=np.float32)
    for t in range(n + 1):
        xx = int(x0 + (x1 - x0) * t / n)
        yy = int(y0 + (y1 - y0) * t / n)
        for dx in range(-thick, thick + 1):
            for dy in range(-thick, thick + 1):
                px, py = xx + dx, yy + dy
                if 0 <= py < img.shape[0] and 0 <= px < img.shape[1]:
                    img[py, px] = np.maximum(img[py, px], c)


def styleframe_sandstorm(i):
    """Sandstorm swallowing the village."""
    img = D.vgrad(PW, PH, [(0.0, (58, 40, 26)), (0.4, (128, 88, 50)), (1.0, (30, 20, 15))])
    img += D.radial_glow(PW, PH, PW * 0.72, PH * 0.22, PW * 0.7, (255, 196, 120), 2.0, 0.5)
    rng = np.random.default_rng(11 + i)
    # diagonal sand streaks
    for _ in range(2600):
        x = rng.integers(-80, PW)
        y = rng.integers(-40, PH)
        L = rng.integers(30, 150)
        a = rng.uniform(0.10, 0.42)
        col = np.array([rng.uniform(190, 255), rng.uniform(140, 200), rng.uniform(80, 130)],
                       dtype=np.float32) / 255
        for t in range(L):
            xx, yy = int(x + t), int(y + t * 0.30)
            if 0 <= xx < PW and 0 <= yy < PH:
                img[yy, xx] = img[yy, xx] * (1 - a) + col * a
    # dark structure barely visible
    ru = np.zeros_like(img)
    D.fill_rr(ru, (PW * 0.12, PH * 0.52, PW * 0.36, PH * 0.86), 1, (16, 11, 9), 1.0)
    D.fill_rr(ru, (PW * 0.55, PH * 0.46, PW * 0.70, PH * 0.86), 1, (16, 11, 9), 1.0)
    m = ru.max(axis=2, keepdims=True) * 0.55
    img = img * (1 - m) + ru * m
    # foreground haze
    img = img * 0.55 + D.radial_glow(PW, PH, PW * 0.5, PH * 0.55, PW * 0.9,
                                     (150, 104, 62), 1.6, 0.85) * 0.9
    return D.apply_vignette(D.grain(img, 0.035, 500 + i), 0.72, 2.0)


def styleframe_village(i):
    """Village at night with one lit window and a distant silhouette."""
    img = D.vgrad(PW, PH, [(0.0, (10, 14, 26)), (0.42, (36, 34, 34)), (1.0, (8, 7, 8))])
    # stars
    rng = np.random.default_rng(60 + i)
    for _ in range(180):
        x, y = int(rng.uniform(0, PW)), int(rng.uniform(0, PH * 0.35))
        img[y, x] = np.array([0.55, 0.58, 0.66], dtype=np.float32) * rng.uniform(0.3, 1.0)
    img += D.radial_glow(PW, PH, PW * 0.80, PH * 0.24, PW * 0.55, (236, 214, 170), 2.4, 0.55)
    # houses
    for k in range(6):
        x = PW * (0.02 + k * 0.165)
        hh = PH * (0.10 + (k % 3) * 0.045)
        D.fill_rr(img, (x, PH * 0.60 - hh, x + PW * 0.15, PH * 0.66), 1, (13, 13, 15), 1.0)
        if k == 3:
            D.fill_rr(img, (x + PW * 0.055, PH * 0.60 - hh * 0.6, x + PW * 0.10,
                            PH * 0.60 - hh * 0.1), 2, (255, 178, 92), 0.95)
    # silhouette at the end of the street
    sx, sy = PW * 0.50, PH * 0.655
    for t in range(int(PH * 0.10)):
        wdt = 6 - t * 0.05
        D.fill_rr(img, (sx - wdt, sy - t, sx + wdt, sy - t + 1), 0, (6, 5, 6), 1.0)
    D.fill_rr(img, (sx - 13, sy - PH * 0.14, sx + 13, sy - PH * 0.075), 13, (6, 5, 6), 1.0)
    D.fill_rr(img, (0, PH * 0.66, PW, PH), 0, (7, 7, 8), 0.9)
    return D.apply_vignette(D.grain(img, 0.030, 600 + i), 0.7, 2.0)


def styleframe_wall(i):
    """A stone wall with a curse carved into it."""
    img = D.vgrad(PW, PH, [(0.0, (30, 26, 22)), (0.5, (22, 20, 18)), (1.0, (8, 7, 7))])
    rng = np.random.default_rng(21 + i)
    for _ in range(3000):
        x, y = int(rng.uniform(0, PW)), int(rng.uniform(0, PH))
        img[y, x] *= rng.uniform(0.84, 1.16)
    # stone blocks
    for r in range(9):
        yy = PH * (0.12 + r * 0.098)
        D.fill_rr(img, (0, yy, PW, yy + 2), 0, (12, 11, 10), 0.55)
        for c in range(3):
            xx = PW * ((c * 0.36 + (r % 2) * 0.18) % 1.0)
            D.fill_rr(img, (xx, yy, xx + 2, yy + PH * 0.098), 0, (12, 11, 10), 0.45)
    _carved_text(img, "यहाँ कोई", "serif_b", int(PW * 0.135), PW * 0.50, PH * 0.34, "cm", 21)
    _carved_text(img, "नहीं बसेगा", "serif_b", int(PW * 0.135), PW * 0.50, PH * 0.48, "cm", 22)
    # handprint smear
    hp = np.zeros((PH, PW, 3), dtype=np.float32)
    D.fill_rr(hp, (PW * 0.18, PH * 0.66, PW * 0.40, PH * 0.80), 30, (58, 12, 12), 1.0)
    m = hp.max(axis=2, keepdims=True)
    img = img * (1 - m * 0.55) + hp * m * 0.55
    return D.apply_vignette(D.grain(img, 0.030, 700 + i), 0.72, 2.0)
