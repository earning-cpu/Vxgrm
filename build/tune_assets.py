"""
Deterministic per-asset exposure tuning.

For every source plate: search gamma so the DELIVERED frame (after grade, filmic
curve and vignette) has median luma ~= MEDIAN_TARGET while keeping highlights
below the clip ceiling. Writes ASSET_TUNE = {path: {"gamma": g, "shoulder": bool}}
to work/asset_tune.json; shotlib reads it.

No feedback loop, no mean-of-sky bias: we optimise the median, which is what the
eye reads as "exposure", and we never allow a gamma that crushes shadows.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from shotlib import FF, W, H, IMG, GRADE

MEDIAN_TARGET = 38.0
P95_CEIL = 208.0
GAMMAS = [round(0.80 + 0.05*i, 2) for i in range(21)]   # 0.80 .. 1.80

# gentle filmic curve: lifts blacks a touch, rolls off highlights (no crush)
SHOULDER = "curves=all='0/0.025 0.28/0.35 0.58/0.62 0.82/0.83 1/0.93'"

def measure(png):
    a = np.array(Image.open(png).convert("L")).astype(np.float32)
    h, w = a.shape
    safe = a[int(h*0.08):int(h*0.94), int(w*0.06):int(w*0.94)]
    return float(np.median(safe)), float(np.percentile(safe, 95)), float(safe.mean())

def chain_for(path, gamma, grade, shoulder):
    c = ["scale=1620:2880:flags=lanczos,setsar=1",
         "zoompan=z='1.12':d=1:s=%dx%d:fps=30" % (W // 2, H // 2),
         GRADE[grade], f"eq=gamma={gamma}"]
    if shoulder:
        c.append(SHOULDER)
    c.append("vignette=PI/5.2")
    c.append("setsar=1,format=yuv420p")
    return ",".join(c)

PLATES = {
    "s01_hook": "night", "s02_fort_wide": "cold", "s03_sadhu": "night",
    "s04_shadow": "dusk", "s05_princess": "night", "s05_ghost": "night",
    "s07_archive": "cold", "s08_sign": "cold", "s09_leopard": "night",
    "bg_doccard": "cold", "bg_end": "night",
    "s01_gate": "night", "s03_sadhu_up": "night", "s05_corridor": "night",
    "s04_shrine": "dusk", "s07_ruins": "cold",
    "s06_curse": "night", "s10_bazaar": "night", "s11_victim": "night",
}

os.makedirs("work/tune", exist_ok=True)
tune = json.load(open("work/asset_tune.json")) if os.path.exists("work/asset_tune.json") else {}
NEW = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else set(PLATES)
for name, grade in PLATES.items():
    if name not in NEW:
        continue
    path = IMG[name]
    best = None
    rows = []
    for g in GAMMAS:
        for sh in (False, True):
            png = f"work/tune/{name}_{g}_{int(sh)}.png"
            subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", path,
                            "-vf", chain_for(path, g, grade, sh), "-frames:v", "1", png],
                           check=True)
            med, p95, mean = measure(png)
            rows.append((g, sh, med, p95, mean))
            if p95 > P95_CEIL:
                continue
            score = abs(med - MEDIAN_TARGET)
            if best is None or score < best[0]:
                best = (score, g, sh, med, p95, mean)
            os.remove(png)
    if best is None:                      # nothing under the clip ceiling -> closest
        best = min((abs(r[2]-MEDIAN_TARGET), r[0], r[1], r[2], r[3], r[4]) for r in rows)
    _, g, sh, med, p95, mean = best
    tune[name] = {"gamma": g, "shoulder": bool(sh), "median": med, "p95": p95, "mean": mean}
    print(f"{name:14s} grade={grade:5s} gamma={g:.2f} shoulder={str(sh):5s} "
          f"median={med:5.1f} p95={p95:5.1f} mean={mean:5.1f}")

json.dump(tune, open("work/asset_tune.json", "w"), indent=1)
print("\nwithin 6 luma of median target:",
      sum(1 for v in tune.values() if abs(v["median"]-MEDIAN_TARGET) <= 6), "/", len(tune))
