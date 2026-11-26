"""Build layer-by-layer transparent RGBA paper-cutout PNG clips in assets/layers/."""
import os
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw

OUT_DIR = "assets/layers"
os.makedirs(OUT_DIR, exist_ok=True)


def _paper_grain(h, w, seed=1, strength=0.045):
    rng = np.random.default_rng(seed)
    n = rng.normal(0.0, strength, (h, w, 1)).astype(np.float32)
    return n


def _save_rgba(path, rgba_u8):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(rgba_u8, "RGBA").save(path, optimize=True)


def _poly_cutout(w, h, pts, color_rgb, seed=1, edge_jitter=3.5, paper_core=True):
    """Create a torn/scissor-cut paper-cutout RGBA PNG from a polygon."""
    rng = np.random.default_rng(seed)
    # Subdivide & jitter polygon edges for handmade scissor/torn feel
    jpts = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(2, int(dist / 14))
        for s in range(steps):
            t = s / steps
            px = x0 + (x1 - x0) * t
            py = y0 + (y1 - y0) * t
            if s > 0:
                px += rng.uniform(-edge_jitter, edge_jitter)
                py += rng.uniform(-edge_jitter, edge_jitter)
            jpts.append((px, py))

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(jpts, fill=255)
    m = np.asarray(mask, dtype=np.float32) / 255.0

    rgb = np.zeros((h, w, 3), dtype=np.float32)
    rgb[:, :] = np.array(color_rgb, dtype=np.float32) / 255.0
    rgb = np.clip(rgb + _paper_grain(h, w, seed=seed, strength=0.04), 0.0, 1.0)

    if paper_core:
        # Faint white card-stock core along cut edge
        k = np.ones((5, 5), np.uint8)
        eroded = cv2.erode((m * 255).astype(np.uint8), k, iterations=1).astype(np.float32) / 255.0
        edge = np.clip(m - eroded, 0.0, 1.0)[:, :, None]
        rgb = rgb * (1.0 - edge * 0.45) + np.array([0.94, 0.91, 0.85], dtype=np.float32) * (edge * 0.45)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = (rgb * 255).astype(np.uint8)
    rgba[:, :, 3] = (m * 255).astype(np.uint8)
    return rgba


def decompose_plate(plate_path, prefix):
    """Decompose a paper-cutout plate into 3 depth-layered RGBA PNGs:
    - bg.png (sky/far backdrop)
    - mid.png (midground architecture/scene)
    - fg.png (foreground framing/vignette silhouette)
    """
    img = cv2.imread(plate_path)
    if img is None:
        print("SKIP missing:", plate_path)
        return
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]

    # 1. Background: full plate (acts as Z=1800 base)
    bg = np.dstack([rgb, np.full((h, w), 255, dtype=np.uint8)])
    _save_rgba(f"{OUT_DIR}/{prefix}_bg.png", bg)

    # 2. Midground: edge-preserving high-contrast paper shapes (luminance < 0.72 or saturated)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32) / 255.0
    # Keep architecture/characters, drop bright sky
    mid_mask = ((gray < 0.68) | (hsv[:, :, 1] > 0.32)).astype(np.uint8) * 255
    mid_mask = cv2.morphologyEx(mid_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mid_mask = cv2.GaussianBlur(mid_mask, (5, 5), 0)
    mid = np.dstack([rgb, mid_mask])
    _save_rgba(f"{OUT_DIR}/{prefix}_mid.png", mid)

    # 3. Foreground framing: dark silhouette edges (top/sides/bottom framing)
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - w * 0.5) / (w * 0.5)
    ny = (yy - h * 0.5) / (h * 0.5)
    radial = np.sqrt(nx * nx + ny * ny)
    fg_mask = ((gray < 0.24) & (radial > 0.45)).astype(np.uint8) * 255
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    fg_mask = cv2.GaussianBlur(fg_mask, (5, 5), 0)
    fg = np.dstack([rgb, fg_mask])
    _save_rgba(f"{OUT_DIR}/{prefix}_fg.png", fg)


def build_puppets_and_props():
    """Craft pure 2D paper-cutout puppets & animated props as RGBA PNGs."""
    # Narayanrao (young Peshwa) jointed puppet parts
    torso = _poly_cutout(220, 300, [
        (70, 20), (150, 20), (175, 110), (185, 280), (35, 280), (45, 110)
    ], (233, 223, 200), seed=11)
    _save_rgba(f"{OUT_DIR}/puppet_boy_torso.png", torso)

    head = _poly_cutout(160, 180, [
        (45, 40), (115, 35), (135, 90), (115, 155), (45, 155), (25, 90)
    ], (218, 195, 165), seed=12)
    _save_rgba(f"{OUT_DIR}/puppet_boy_head.png", head)

    arm = _poly_cutout(90, 200, [
        (30, 15), (60, 15), (68, 180), (22, 180)
    ], (233, 223, 200), seed=13)
    _save_rgba(f"{OUT_DIR}/puppet_boy_arm.png", arm)

    leg = _poly_cutout(100, 240, [
        (30, 15), (70, 15), (76, 220), (24, 220)
    ], (42, 38, 46), seed=14)
    _save_rgba(f"{OUT_DIR}/puppet_boy_leg.png", leg)

    # Assassin silhouette + dagger arm
    assassin = _poly_cutout(260, 460, [
        (95, 25), (165, 25), (185, 95), (220, 210), (200, 440),
        (60, 440), (40, 210), (75, 95)
    ], (24, 22, 28), seed=21)
    _save_rgba(f"{OUT_DIR}/puppet_assassin.png", assassin)

    dagger_arm = _poly_cutout(180, 180, [
        (20, 130), (110, 50), (165, 15), (130, 75), (45, 155)
    ], (146, 31, 26), seed=22)
    _save_rgba(f"{OUT_DIR}/puppet_dagger_arm.png", dagger_arm)

    # Flames (2 variants for flicker)
    flame1 = _poly_cutout(260, 360, [
        (130, 15), (185, 120), (235, 230), (195, 345), (65, 345), (25, 230), (75, 120)
    ], (218, 84, 34), seed=31)
    _save_rgba(f"{OUT_DIR}/prop_flame_1.png", flame1)

    flame2 = _poly_cutout(260, 360, [
        (115, 25), (170, 100), (225, 210), (190, 345), (70, 345), (35, 210), (85, 110)
    ], (238, 148, 48), seed=32)
    _save_rgba(f"{OUT_DIR}/prop_flame_2.png", flame2)

    # River wave strip
    wave_pts = [(0, 220)]
    for x in range(0, 1201, 60):
        y = 70 + int(35 * math.sin(x * 0.015))
        wave_pts.append((x, y))
    wave_pts.append((1200, 220))
    wave1 = _poly_cutout(1200, 220, wave_pts, (36, 54, 74), seed=41)
    _save_rgba(f"{OUT_DIR}/prop_wave_1.png", wave1)

    # Clay pot
    pot = _poly_cutout(180, 180, [
        (65, 25), (115, 25), (145, 75), (135, 150), (45, 150), (35, 75)
    ], (156, 86, 52), seed=42)
    _save_rgba(f"{OUT_DIR}/prop_pot.png", pot)

    # Full moon
    moon_pts = [(160 + 130 * math.cos(a), 160 + 130 * math.sin(a))
                for a in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
    moon = _poly_cutout(320, 320, moon_pts, (243, 238, 226), seed=51)
    _save_rgba(f"{OUT_DIR}/prop_moon.png", moon)

    # Drifting cloud
    cloud = _poly_cutout(520, 180, [
        (40, 130), (90, 65), (190, 45), (290, 35), (390, 60), (480, 115), (460, 150), (60, 150)
    ], (44, 46, 58), seed=52)
    _save_rgba(f"{OUT_DIR}/prop_cloud.png", cloud)

    # Shadowy doorway figure
    fig = _poly_cutout(220, 520, [
        (80, 20), (140, 20), (155, 85), (175, 200), (160, 500), (60, 500), (45, 200), (65, 85)
    ], (16, 15, 20), seed=61)
    _save_rgba(f"{OUT_DIR}/prop_shadow_figure.png", fig)


if __name__ == "__main__":
    plates = {
        "hook": "assets/img/paper_test_hook.png",
        "gate": "assets/img/paper_test_gate.png",
        "letter": "assets/img/p04_letter.png",
        "assassins": "assets/img/p05_assassins.png",
        "running": "assets/img/p06_running.png",
        "courtyard": "assets/img/p07_courtyard.png",
        "river": "assets/img/p08_river.png",
        "fire": "assets/img/p09_fire.png",
        "ruins": "assets/img/p10_ruins.png",
        "doorway": "assets/img/p11_doorway.png",
    }
    for name, path in plates.items():
        decompose_plate(path, name)
    build_puppets_and_props()
    print("Built all RGBA paper-cutout layers in", OUT_DIR)
