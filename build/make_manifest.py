"""
Reconstruct work/shots_manifest.json from the shot plan alone.

The manifest is pure bookkeeping (which plate, which camera, which grade, which
frame range each shot occupies). Deriving it here means the full-frame QA can be
re-run on a delivered file without re-rendering 30 shots.
"""
import json, os, sys
from shotlib import TL, PLAN, FPS, IMG

def build():
    shots, idx = [], 0
    for beat in TL["beats"]:
        bid, start, dur = beat["id"], beat["start"], beat["dur"]
        specs = PLAN[bid]
        raw = [max(0.9, dur * w) for _, w, *_ in specs]
        k = dur / sum(raw)
        durs = [r * k for r in raw]
        durs[-1] = dur - sum(durs[:-1])
        t = start
        for (img, wgt, cam, grade, flags), d in zip(specs, durs):
            n = max(int(round(d * FPS)), 8)
            shots.append({"idx": idx, "file": f"work/shots/shot_{idx:03d}.mp4",
                          "beat": bid, "img": img, "start": round(t, 3),
                          "dur": round(n / FPS, 3), "frames": n,
                          "cam": cam, "grade": grade, "flags": flags})
            t += n / FPS
            idx += 1
    return shots

if __name__ == "__main__":
    shots = build()
    total = sum(s["dur"] for s in shots)
    if abs(total - TL["total"]) > 0.25:
        raise SystemExit(f"manifest total {total:.2f}s != timeline {TL['total']:.2f}s")
    json.dump(shots, open("work/shots_manifest.json", "w"), indent=1)
    print(f"manifest rebuilt: {len(shots)} shots, {total:.3f}s")
