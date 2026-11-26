"""3D-world 2D paper cut-out animation engine.

Provides exact (X, Y, Z) world placement, perspective camera projection,
depth-sorted rendering (painter's algorithm), cast paper drop-shadows,
pivot-based 2D rotation/scaling, and optional stepped stop-motion timing.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, List
import cv2
import numpy as np


@dataclass
class Camera3D:
    """Perspective camera in world space (pixels, +Z is into the screen)."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    focal: float = 900.0
    roll: float = 0.0          # degrees
    shake_x: float = 0.0
    shake_y: float = 0.0


@dataclass
class Layer3D:
    """A 2D RGBA paper-cutout clip placed in 3D world space."""
    name: str
    rgba: np.ndarray           # uint8 (H, W, 4) premultiplied or straight RGBA
    x: float = 0.0             # world X (0 = center)
    y: float = 0.0             # world Y (0 = center)
    z: float = 900.0           # world Z (> cam.z + 20)
    scale: float = 1.0         # base world scale
    sx: float = 1.0            # dynamic X scale
    sy: float = 1.0            # dynamic Y scale
    rot: float = 0.0           # degrees, clockwise
    pivot: Tuple[float, float] = (0.5, 0.5)  # normalized (0..1, 0..1)
    opacity: float = 1.0
    shadow: bool = True        # cast paper drop-shadow onto layers behind
    shadow_offset: Tuple[float, float] = (14.0, 18.0)
    shadow_alpha: float = 0.42
    shadow_blur: int = 15
    step_fps: Optional[float] = None  # e.g. 12.0 for stop-motion feel
    visible: bool = True
    # Optional per-frame updater: fn(layer, t_local, t_global)
    animate: Optional[Callable[["Layer3D", float, float], None]] = None


def load_rgba(path: str, max_dim: Optional[int] = None) -> np.ndarray:
    """Load an RGBA PNG as uint8 (H, W, 4) in RGB+A order."""
    bgr = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if bgr is None:
        raise FileNotFoundError(f"Layer PNG not found: {path}")
    if bgr.ndim == 2:
        rgba = cv2.cvtColor(bgr, cv2.COLOR_GRAY2RGBA)
    elif bgr.shape[2] == 3:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        a = np.full((rgb.shape[0], rgb.shape[1], 1), 255, dtype=np.uint8)
        rgba = np.concatenate([rgb, a], axis=2)
    else:
        rgba = cv2.cvtColor(bgr, cv2.COLOR_BGRA2RGBA)
    if max_dim is not None and max(rgba.shape[:2]) > max_dim:
        h, w = rgba.shape[:2]
        s = max_dim / float(max(h, w))
        rgba = cv2.resize(rgba, (max(1, int(w * s)), max(1, int(h * s))),
                          interpolation=cv2.INTER_AREA)
    return rgba


def _quantize_t(t: float, step_fps: Optional[float]) -> float:
    if step_fps is None or step_fps <= 0:
        return t
    return math.floor(t * step_fps) / step_fps


def _alpha_composite(dst_rgb: np.ndarray, src_rgba: np.ndarray,
                     x0: int, y0: int, opacity: float = 1.0) -> None:
    """In-place alpha composite of uint8 src_rgba onto float32 dst_rgb (0..1)."""
    dh, dw = dst_rgb.shape[:2]
    sh, sw = src_rgba.shape[:2]
    x1, y1 = x0 + sw, y0 + sh
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(dw, x1), min(dh, y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    sx0, sy0 = cx0 - x0, cy0 - y0
    sx1, sy1 = sx0 + (cx1 - cx0), sy0 + (cy1 - cy0)

    patch = src_rgba[sy0:sy1, sx0:sx1]
    a = (patch[:, :, 3:4].astype(np.float32) * (1.0 / 255.0)) * opacity
    if a.max() <= 0.002:
        return
    rgb = patch[:, :, :3].astype(np.float32) * (1.0 / 255.0)
    dst_slice = dst_rgb[cy0:cy1, cx0:cx1]
    dst_rgb[cy0:cy1, cx0:cx1] = rgb * a + dst_slice * (1.0 - a)


def _shadow_composite(dst_rgb: np.ndarray, alpha_u8: np.ndarray,
                      x0: int, y0: int, shadow_alpha: float,
                      blur_k: int) -> None:
    """In-place soft dark-ink drop shadow onto float32 dst_rgb (0..1)."""
    if shadow_alpha <= 0.005:
        return
    dh, dw = dst_rgb.shape[:2]
    sh, sw = alpha_u8.shape[:2]
    x1, y1 = x0 + sw, y0 + sh
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(dw, x1), min(dh, y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    sx0, sy0 = cx0 - x0, cy0 - y0
    sx1, sy1 = sx0 + (cx1 - cx0), sy0 + (cy1 - cy0)

    a_patch = alpha_u8[sy0:sy1, sx0:sx1].astype(np.float32) * (1.0 / 255.0)
    if blur_k >= 3:
        k = blur_k if blur_k % 2 == 1 else blur_k + 1
        a_patch = cv2.GaussianBlur(a_patch, (k, k), 0)
    a = (a_patch * shadow_alpha)[:, :, None]
    # Warm charcoal-ink shadow (0.04, 0.03, 0.05)
    dst_slice = dst_rgb[cy0:cy1, cx0:cx1]
    dst_rgb[cy0:cy1, cx0:cx1] = dst_slice * (1.0 - a) + np.array([0.04, 0.03, 0.05], dtype=np.float32) * a


class World3D:
    """A 3D scene holding paper-cutout layers and a perspective camera."""

    def __init__(self, width: int = 1080, height: int = 1920,
                 bg_color: Tuple[float, float, float] = (0.06, 0.06, 0.08)):
        self.w = width
        self.h = height
        self.bg_color = np.array(bg_color, dtype=np.float32)
        self.layers: List[Layer3D] = []

    def add(self, layer: Layer3D) -> Layer3D:
        self.layers.append(layer)
        return layer

    def render(self, cam: Camera3D, t_local: float = 0.0,
               t_global: float = 0.0) -> np.ndarray:
        """Render all visible layers sorted back-to-front into float32 RGB (0..1)."""
        canvas = np.empty((self.h, self.w, 3), dtype=np.float32)
        canvas[:, :] = self.bg_color

        # Update animations
        for lyr in self.layers:
            if lyr.animate is not None:
                tl = _quantize_t(t_local, lyr.step_fps)
                tg = _quantize_t(t_global, lyr.step_fps)
                lyr.animate(lyr, tl, tg)

        # Sort back-to-front (largest Z first)
        ordered = sorted(
            (l for l in self.layers if l.visible and l.opacity > 0.004),
            key=lambda l: l.z,
            reverse=True,
        )

        cx_cam = cam.x + cam.shake_x
        cy_cam = cam.y + cam.shake_y

        for lyr in ordered:
            dz = lyr.z - cam.z
            if dz <= 15.0:
                continue
            persp = cam.focal / dz
            sx_total = lyr.scale * lyr.sx * persp
            sy_total = lyr.scale * lyr.sy * persp
            if sx_total <= 0.01 or sy_total <= 0.01:
                continue

            sh, sw = lyr.rgba.shape[:2]
            tw = max(1, int(round(sw * sx_total)))
            th = max(1, int(round(sh * sy_total)))

            # Resize
            interp = cv2.INTER_AREA if (tw < sw or th < sh) else cv2.INTER_LINEAR
            scaled = cv2.resize(lyr.rgba, (tw, th), interpolation=interp)

            # Rotate around pivot if needed
            rot_deg = lyr.rot - cam.roll
            px = lyr.pivot[0] * tw
            py = lyr.pivot[1] * th

            if abs(rot_deg) > 0.05:
                M = cv2.getRotationMatrix2D((px, py), -rot_deg, 1.0)
                cos_a = abs(M[0, 0])
                sin_a = abs(M[0, 1])
                nw = int(math.ceil(th * sin_a + tw * cos_a))
                nh = int(math.ceil(th * cos_a + tw * sin_a))
                M[0, 2] += (nw * 0.5) - px
                M[1, 2] += (nh * 0.5) - py
                # New pivot offset in rotated image
                px_rot = nw * 0.5
                py_rot = nh * 0.5
                scaled = cv2.warpAffine(
                    scaled, M, (nw, nh),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(0, 0, 0, 0),
                )
            else:
                px_rot, py_rot = px, py

            # Project world (x, y) to screen
            scr_x = self.w * 0.5 + (lyr.x - cx_cam) * persp
            scr_y = self.h * 0.5 + (lyr.y - cy_cam) * persp
            x0 = int(round(scr_x - px_rot))
            y0 = int(round(scr_y - py_rot))

            # Cast paper drop-shadow
            if lyr.shadow and lyr.z < 2000.0:
                sox = int(round(lyr.shadow_offset[0] * persp))
                soy = int(round(lyr.shadow_offset[1] * persp))
                _shadow_composite(
                    canvas, scaled[:, :, 3],
                    x0 + sox, y0 + soy,
                    lyr.shadow_alpha * lyr.opacity,
                    max(3, int(round(lyr.shadow_blur * persp))),
                )

            _alpha_composite(canvas, scaled, x0, y0, lyr.opacity)

        return np.clip(canvas, 0.0, 1.0)
