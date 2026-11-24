"""
Exposure calibration: renders ONE representative frame per shot with the real
filter chain (minus motion/grain), measures delivered luma inside the safe area,
and writes per-shot gamma multipliers so every shot lands on its target.
Iterate:  calibrate -> render -> QA  (2 passes usually converge).
"""
import json, subprocess, sys, os
import numpy as np
from PIL import Image
from shotlib import (FF, W, H, FPS, TL, IMG, PLAN, build_chain, TARGET)

SAFE = (0.10, 0.06, 0.90, 0.56)   # x0,y0,x1,y1 : excludes HUD, subs, gradient-heavy bottom

def delivered_luma(png):
    im = Image.open(png).convert("L")
    w, h = im.size
    a = np.array(im.crop((int(w*SAFE[0]), int(h*SAFE[1]), int(w*SAFE[2]), int(h*SAFE[3])))).astype(np.float32)
    return float(a.mean())

def main(write=True):
    os.makedirs("work/cal", exist_ok=True)
    cal = json.load(open("work/expo_calib.json")) if os.path.exists("work/expo_calib.json") else {}
    idx = 0
    rows = []
    for beat in TL["beats"]:
        bid = beat["id"]
        for img, wgt, cam, grade, flags in PLAN[bid]:
            png = f"work/cal/{idx:03d}.png"
            chain = build_chain(IMG[img], cam, grade, flags, bid, 30, idx, for_sim=True)
            subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                            "-i", IMG[img], "-vf", ",".join(chain),
                            "-frames:v", "1", png], check=True)
            got = delivered_luma(png)
            tgt = TARGET[bid]
            if "s05" in IMG[img]: tgt += 7
            if "ghost" in IMG[img]: tgt += 6
            if "bg_end" in IMG[img]: tgt += 4
            ratio = tgt / max(got, 1.0)
            # gamma is nonlinear: a factor f in luma ~ gamma^(1/2.2) shift, damp the step
            step = min(max(ratio ** 0.42, 0.80), 1.25)
            cur = cal.get(str(idx), 1.0)
            new = round(min(max(cur * step, 0.30), 1.75), 3)
            rows.append((idx, bid, img, cam, round(got, 1), round(tgt, 1), cur, new))
            if write:
                cal[str(idx)] = new
            idx += 1
    print(f"{'idx':>3} {'beat':4s} {'img':14s} {'cam':6s} {'got':>6s} {'target':>6s} {'old':>5s} {'new':>5s}")
    for r in rows:
        print(f"{r[0]:3d} {r[1]:4s} {r[2]:14s} {r[3]:6s} {r[4]:6.1f} {r[5]:6.1f} {r[6]:5.2f} {r[7]:5.2f}")
    if write:
        json.dump(cal, open("work/expo_calib.json", "w"), indent=1)
        ok = sum(1 for r in rows if abs(r[4]-r[5]) <= max(5, r[5]*0.22))
        print(f"\nwithin 22% of target: {ok}/{len(rows)}   (calib -> work/expo_calib.json)")

if __name__ == "__main__":
    main(write="--dry" not in sys.argv)
