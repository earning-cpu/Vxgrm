"""Dense contact sheets covering every frame of the film, for visual review."""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

import imageio_ffmpeg

FPS = 30
W, H = 1080, 1920


def sheets(video, outdir="qa", n_sheets=6, cols=6, rows=6, tw=216, th=384):
    os.makedirs(outdir, exist_ok=True)
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    sw, sh_ = 216, 384
    r = subprocess.run([exe, "-v", "error", "-i", video, "-vf", f"scale={sw}:{sh_}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(buf) // (sw * sh_ * 3)
    frames = buf[:n * sw * sh_ * 3].reshape(n, sh_, sw, 3)
    print(f"{n} frames decoded")

    per = cols * rows
    step = max(1, n // (n_sheets * per))
    idx = list(range(0, n, step))[:n_sheets * per]
    out = []
    for s in range(n_sheets):
        chunk = idx[s * per:(s + 1) * per]
        if not chunk:
            break
        sh = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)
        for k, fi in enumerate(chunk):
            im = Image.fromarray(frames[fi]).resize((tw, th), Image.LANCZOS)
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, tw - 1, th - 1], outline=(70, 70, 74))
            d.text((5, 5), f"{fi}", fill=(230, 220, 200))
            rr, cc = k // cols, k % cols
            sh[rr * th:(rr + 1) * th, cc * tw:(cc + 1) * tw] = np.asarray(im)
        p = f"{outdir}/sheet_{s+1}.png"
        Image.fromarray(sh).save(p)
        out.append((p, chunk[0], chunk[-1]))
        print("wrote", p, "frames", chunk[0], "-", chunk[-1])
    return out


def heroes(video, times, outdir="qa", tag="hero"):
    """Full-resolution frames at given timestamps."""
    os.makedirs(outdir, exist_ok=True)
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    paths = []
    for i, t in enumerate(times):
        p = f"{outdir}/{tag}_{i:02d}_{t:05.2f}s.png"
        subprocess.run([exe, "-v", "error", "-y", "-ss", str(t), "-i", video,
                        "-frames:v", "1", p], capture_output=True)
        paths.append(p)
    return paths


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "out/kaka_mala_vachwa.mp4"
    sheets(video)
