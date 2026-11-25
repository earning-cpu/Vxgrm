"""Bhangarh Shorts — shot render driver (uses shotlib for all shot logic)."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
import imageio_ffmpeg
from shotlib import (FF, W, H, FPS, TL, IMG, PLAN, SHOT_DIR, cam_expr, build_chain)

ONLY = None
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))

shots, idx = [], 0
for beat in TL["beats"]:
    bid, start, dur = beat["id"], beat["start"], beat["dur"]
    if ONLY and bid not in ONLY:
        idx += len(PLAN[bid]); continue
    specs = PLAN[bid]
    raw = [max(0.9, dur * w) for _, w, *_ in specs]
    k = dur / sum(raw)
    durs = [r * k for r in raw]
    durs[-1] = dur - sum(durs[:-1])
    t = start
    for (img, wgt, cam, grade, flags), d in zip(specs, durs):
        n = max(int(round(d * FPS)), 8)
        out = f"{SHOT_DIR}/shot_{idx:03d}.mp4"
        chain = build_chain(IMG[img], cam, grade, flags, bid, n, idx)
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", IMG[img], "-vf", ",".join(chain),
                        "-frames:v", str(n), "-r", str(FPS),
                        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                        "-g", "60", "-pix_fmt", "yuv420p", out], check=True)
        shots.append({"idx": idx, "file": out, "beat": bid, "img": img,
                      "start": round(t, 3), "dur": round(n / FPS, 3), "frames": n,
                      "cam": cam, "grade": grade, "flags": flags})
        t += n / FPS
        idx += 1
    print(f"{bid}: {len(specs)} shots, {dur:.2f}s")

if ONLY:
    old = {x["idx"]: x for x in json.load(open("work/shots_manifest.json"))}
    for x in shots: old[x["idx"]] = x
    shots = [old[k2] for k2 in sorted(old)]

json.dump(shots, open("work/shots_manifest.json", "w"), indent=1)
print("shots rendered:", len(shots))

# integrity guard: every shot must exist and its duration must match the timeline
missing = [x for x in shots if not os.path.exists(x["file"])]
if missing:
    raise SystemExit(f"ABORT: {len(missing)} shot files missing (e.g. {missing[0]['file']}). "
                     f"Run a full render, not --only.")
total = sum(x["dur"] for x in shots)
if abs(total - TL["total"]) > 0.25:
    raise SystemExit(f"ABORT: shot total {total:.2f}s != timeline {TL['total']:.2f}s")

with open("work/concat.txt", "w") as f:
    for s in shots:
        f.write(f"file '{os.path.abspath(s['file'])}'\n")
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
                "-safe", "0", "-i", "work/concat.txt", "-c", "copy",
                "work/video_clean.mp4"], check=True)
print("clean video:", round(sum(s["dur"] for s in shots), 3), "s")

# gradient overlay
h, w = H, W
yy = np.linspace(0, 1, h)[:, None]
top = np.clip((0.30 - yy) / 0.30, 0, 1) ** 1.5 * 0.55
bot = np.clip((yy - 0.64) / 0.36, 0, 1) ** 1.30 * 0.62
alpha = np.clip(top + bot, 0, 1)
rgb = np.zeros((h, w, 4), dtype=np.uint8)
rgb[:, :, 3] = (alpha * 255).astype(np.uint8)
Image.fromarray(rgb, "RGBA").save("work/grad.png")

subprocess.run([".venv/bin/python", "build/ass_build.py"], check=True)
subprocess.run([".venv/bin/python", "build/compose.py", "--out", "work/final_candidate.mp4"], check=True)
print("CANDIDATE -> work/final_candidate.mp4  (run build/apply.py to gate + promote)")
