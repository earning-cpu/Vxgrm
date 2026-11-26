"""3D paper cut-out renderer with 0-latency exact narration captions."""
import os
import subprocess
import numpy as np
import imageio_ffmpeg

from src import design as D
from src import text_engine as T
from src.timeline import FPS, W, H, SHOTS, VIDEO_END, build_captions
from src.scenes3d import build_scenes

_SCENES = None
_CAPS = None


def _init():
    global _SCENES, _CAPS
    if _SCENES is None:
        _SCENES = build_scenes()
    if _CAPS is None:
        _CAPS = build_captions()


def _active_shot(t: float):
    for t0, t1, key in SHOTS:
        if t0 <= t < t1:
            return t0, t1, key
    return SHOTS[-1]


def _draw_caption(img: np.ndarray, text: str) -> np.ndarray:
    """Clean, high-contrast Devanagari caption at bottom-safe zone (no label box)."""
    size = 54
    max_w = 920
    tw = T.text_width(text, "dev_b", size)
    if tw > max_w:
        size = max(36, int(size * max_w / tw))
        tw = T.text_width(text, "dev_b", size)
    x = int((W - tw) * 0.5)
    y = int(H * 0.80)
    # Crisp dark-ink outline + pure bone-white fill for 100% legibility
    D.draw_text(
        img, text,
        font="dev_b", size=size,
        color=(248, 244, 234),
        x=x, y=y,
        stroke=7, stroke_color=(14, 12, 16),
    )
    return img


def render_frame(fi: int) -> np.ndarray:
    _init()
    t = fi / FPS
    t0, t1, key = _active_shot(t)
    world, cam_fn = _SCENES[key]
    cam = cam_fn(t - t0, t1 - t0)
    img = world.render(cam, t_local=t - t0, t_global=t)

    # Subtle paper vignette
    img = D.apply_vignette(img, strength=0.35, power=2.0)

    # 0-latency exact narration caption
    for cap in _CAPS:
        if cap.t0 <= t < cap.t1:
            img = _draw_caption(img, cap.text)
            break

    return np.clip(img, 0.0, 1.0)


def render(out_path: str, audio_path: str) -> None:
    _init()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    n_frames = int(round(VIDEO_END * FPS))
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        exe, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-maxrate", "11M", "-bufsize", "22M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        "-shortest", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for fi in range(n_frames):
            frame = render_frame(fi)
            proc.stdin.write((frame * 255.0).astype(np.uint8).tobytes())
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg exited with {rc}")
    finally:
        if proc.poll() is None:
            proc.kill()
