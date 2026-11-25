"""
Bhangarh Shorts — full frame-by-frame QA.
Decodes EVERY frame and measures luma/contrast/clipping/text-band energy, detects
cuts, freezes, black frames, and validates them against the shot manifest + timeline.
Also audits the audio timeline (silence, VO presence per beat, loudness/peak).
"""
import json, subprocess, numpy as np, imageio_ffmpeg, os, hashlib, sys

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "out/bhangarh_shorts.mp4"
GW, GH = 216, 384
os.makedirs("work/qa", exist_ok=True)
TL = json.load(open("work/timeline.json"))
SHOTS = json.load(open("work/shots_manifest.json"))

# ---------------------------------------------------------------- decode all frames
def probe(path, stream=None):
    o = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    import re
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", o)
    return float(d.group(1))*3600 + float(d.group(2))*60 + float(d.group(3)), o

DUR, meta = probe(SRC)
FPS = 30
proc = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", "-i", SRC,
                         "-vf", f"scale={GW}:{GH},format=gray", "-f", "rawvideo", "-"],
                        stdout=subprocess.PIPE)
frame_sz = GW*GH
grays = []
while True:
    buf = proc.stdout.read(frame_sz)
    if len(buf) < frame_sz: break
    grays.append(np.frombuffer(buf, dtype=np.uint8).reshape(GH, GW))
proc.wait()
NF = len(grays)
print("frames decoded:", NF, "duration:", round(DUR, 3))

# band definitions in grid coordinates
def band(y0, y1): return slice(int(y0/GH*GH) if False else 0, 0)  # placeholder
BANDS = {
    "hud_top":    (0.00, 0.09),
    "sub_band":   (0.56, 0.70),
    "card_band":  (0.22, 0.54),
    "bottom":     (0.88, 1.00),
}
bmask = {k: (slice(int(a*GH), int(b*GH)), slice(0, GW)) for k, (a, b) in BANDS.items()}

rows = []
prev = None
for i, g in enumerate(grays):
    f = g.astype(np.float32)
    mean = f.mean(); p5, p95 = np.percentile(f, [5, 95])
    clip_hi = float((f > 248).mean()); black = float((f < 12).mean())
    contrast = p95 - p5
    d = 0.0 if prev is None else float(np.abs(f - prev).mean())
    stats = {}
    for k, (ys, xs) in bmask.items():
        b = f[ys, xs]
        stats[k] = (float(b.mean()), float((b > 225).mean()), float((b > 200).mean()))
    # red-ness in sub band (karaoke highlight)
    rows.append({"i": i, "t": round(i/FPS, 3), "mean": round(mean, 2),
                 "p5": round(float(p5), 1), "p95": round(float(p95), 1),
                 "contrast": round(float(contrast), 1),
                 "clip_hi": round(clip_hi, 5), "black": round(black, 4),
                 "delta": round(d, 3),
                 "sub_mean": round(stats["sub_band"][0], 1),
                 "sub_white": round(stats["sub_band"][2], 4),
                 "hud_white": round(stats["hud_top"][2], 4),
                 "card_white": round(stats["card_band"][2], 4)})
    prev = f

arr = lambda k: np.array([r[k] for r in rows])

# ---------------------------------------------------------------- cut detection
delta = arr("delta")
# a cut = spike >> local median
med = np.array([np.median(delta[max(0,i-8):i+9]) for i in range(NF)])
# structural cut detector: edge-structure difference per 8x6 block.
# flashes / overlay pops change brightness, not edge layout -> ignored.
def edge_blocks(g):
    f = g.astype(np.float32)
    gx = np.abs(np.diff(f, axis=1))
    gy = np.abs(np.diff(f, axis=0))
    gy = np.pad(gy, ((0, 1), (0, 0)), mode="edge")
    gx = np.pad(gx, ((0, 0), (0, 1)), mode="edge")
    e = gx + gy
    out = np.array([[e[y*e.shape[0]//6:(y+1)*e.shape[0]//6,
                       x*e.shape[1]//8:(x+1)*e.shape[1]//8].mean()
                     for x in range(8)] for y in range(6)])
    return out.reshape(-1)
sig = np.stack([edge_blocks(g) for g in grays])
ediff = np.zeros(NF)
for i in range(1, NF):
    ediff[i] = float(np.abs(sig[i] - sig[i-1]).mean())
ref = np.median(ediff[ediff > 0])
THRESH = max(2.2, 3.0*ref)
cand = [i for i in range(5, NF-5) if ediff[i] > THRESH and ediff[i] >= ediff[i-4:i+5].max()-1e-9]
cuts = []
for c in cand:
    if cuts and c - cuts[-1] <= 4: continue
    cuts.append(c)

det_cut_t = [round(c/FPS, 3) for c in cuts]
man_cut_t = sorted({round(x["start"], 3) for x in SHOTS})
matched, unmatched_man = [], []
for m in man_cut_t:
    # ignore t=0 (stream start is not a cut) and detect within +-0.25s
    if m == 0.0: continue
    hit = min(det_cut_t, key=lambda x: abs(x-m)) if det_cut_t else None
    if hit is not None and abs(hit-m) <= 0.25:
        matched.append((m, hit, round(abs(hit-m)*1000)))
    else:
        unmatched_man.append(m)
extra = [c for c in det_cut_t if all(abs(c-m) > 0.25 for m in man_cut_t)]

# ---------------------------------------------------------------- anomaly scans
black_frames = [r for r in rows if r["mean"] < 10]
frozen = [i for i in range(1, NF) if delta[i] < 0.012 and delta[i-1] < 0.012]
dull = [r for r in rows if r["contrast"] < 45]
hot = [r for r in rows if r["clip_hi"] > 0.06]
dark_scene = [r for r in rows if r["mean"] < 22]

# per-beat visual summary
beatsum = []
for b in TL["beats"]:
    i0, i1 = int(b["start"]*FPS), min(int(b["end"]*FPS), NF)
    seg = rows[i0:i1]
    if not seg: continue
    m = np.array([s["mean"] for s in seg])
    c = np.array([s["contrast"] for s in seg])
    beatsum.append({"id": b["id"], "t": (b["start"], b["end"]),
                    "frames": len(seg), "luma_mean": round(m.mean(), 1),
                    "luma_min": round(m.min(), 1), "luma_max": round(m.max(), 1),
                    "contrast_mean": round(c.mean(), 1),
                    "shots": sum(1 for s in SHOTS if abs(s["start"]-b["start"]) < 0.05 or (b["start"] <= s["start"] < b["end"]))})

# shot-level brightness (catch one dark shot among bright ones)
shotsum = []
for s in SHOTS:
    i0, i1 = int(s["start"]*FPS), min(int(s["start"]*FPS)+s["frames"], NF)
    seg = rows[i0:i1]
    if not seg: continue
    m = float(np.mean([x["mean"] for x in seg])); c = float(np.mean([x["contrast"] for x in seg]))
    shotsum.append({"beat": s["beat"], "t": s["start"], "img": s["img"], "cam": s["cam"],
                    "grade": s["grade"], "dur": s["dur"], "luma": round(m, 1),
                    "contrast": round(c, 1)})

# ---------------------------------------------------------------- audio audit
def load_audio(path):
    raw = subprocess.run([FF, "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1",
                          "-ar", "48000", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

a = load_audio(SRC)
SR = 48000
win = int(0.05*SR)
rms = np.array([np.sqrt(np.mean(a[i:i+win]**2)) for i in range(0, len(a)-win, win)])
db = 20*np.log10(rms+1e-9)
silence_runs = []
run = 0
for i, v in enumerate(db):
    if v < -45: run += 1
    else:
        if run >= 6: silence_runs.append((round((i-run)*0.05, 2), round(run*0.05, 2)))
        run = 0
if run >= 6: silence_runs.append((round((len(db)-run)*0.05, 2), round(run*0.05, 2)))

vo_energy = []
for b in TL["beats"]:
    s0, s1 = b["start"], b["start"] + b["vo_dur"]
    seg = a[int(s0*SR):int(s1*SR)]
    silent = float((20*np.log10(np.sqrt(np.mean(seg**2))+1e-9)))
    vo_energy.append({"id": b["id"], "rms_db": round(silent, 1), "vo_dur": b["vo_dur"]})

loud = subprocess.run([FF, "-hide_banner", "-i", SRC, "-af", "ebur128=peak=true",
                       "-f", "null", "-"], capture_output=True, text=True).stderr
import re
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
LRA = re.findall(r"LRA:\s+(-?[\d.]+) LU", loud)
TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)

# ---------------------------------------------------------------- report
def pct(v, lo, hi):
    return round(100.0*float(((v >= lo) & (v <= hi)).mean()), 1)

rep = {
  "file": SRC, "bytes": os.path.getsize(SRC), "duration": DUR, "frames": NF,
  "fps": FPS, "resolution": "1080x1920", "sar": "1:1",
  "video": {
    "luma_mean": round(float(arr('mean').mean()), 1),
    "luma_p10": round(float(np.percentile(arr('mean'), 10)), 1),
    "luma_p90": round(float(np.percentile(arr('mean'), 90)), 1),
    "contrast_mean": round(float(arr('contrast').mean()), 1),
    "pct_frames_in_healthy_range": pct(arr('mean'), 26, 135),
    "pct_frames_too_dark": pct(arr('mean'), 0, 21.99),
    "pct_frames_near_clip": round(100*float((arr('clip_hi') > 0.06).mean()), 1),
    "black_frames": len(black_frames),
    "frozen_frame_pairs": len(frozen),
    "dull_lowcontrast_frames": len(dull),
    "edge_diff_median": round(float(ref), 2), "edge_cut_threshold": round(float(THRESH), 2),
    "edge_diff_top": [round(float(x),2) for x in sorted(ediff)[-14:]],
    "cuts_detected": len(det_cut_t),
    "cuts_expected": len(man_cut_t),
    "cuts_matched": len(matched),
    "cut_sync_max_ms": max([m[2] for m in matched]) if matched else None,
    "missing_cuts": unmatched_man, "extra_cuts": extra,
    "avg_shot_len": round(float(np.mean([s["dur"] for s in SHOTS])), 2),
    "min_shot_len": round(float(np.min([s["dur"] for s in SHOTS])), 2),
    "max_shot_len": round(float(np.max([s["dur"] for s in SHOTS])), 2),
  },
  "audio": {"integrated_lufs": I[-1] if I else None, "lra": LRA[-1] if LRA else None,
            "true_peak_dbfs": TP[-1] if TP else None,
            "silence_runs": silence_runs,
            "vo_rms_per_beat": vo_energy},
  "beats": beatsum, "shots": shotsum,
  "subtitle_band": {"frames_with_white_text_pct": round(100*float((arr('sub_white') > 0.004).mean()), 1),
                    "min_band_luma": round(float(arr('sub_mean').min()), 1),
                    "max_band_luma": round(float(arr('sub_mean').max()), 1)},
  "hud_band": {"frames_with_text_pct": round(100*float((arr('hud_white') > 0.002).mean()), 1)},
}
os.makedirs("work/qa", exist_ok=True)
rep["source"] = SRC
json.dump(rep, open("work/qa/report.json","w"), indent=1, default=lambda o: float(o) if hasattr(o,"__float__") else str(o))
json.dump(rows, open("work/qa/frames.json","w"), default=float)
json.dump(det_cut_t, open("work/qa/cuts.json", "w"))

print(json.dumps({k: rep[k] for k in ("video", "audio", "subtitle_band", "hud_band")}, indent=1)[:2600])
print("\nBEATS")
for b in beatsum: print(f'  {b["id"]} t={b["t"][0]:5.2f}-{b["t"][1]:5.2f} luma={b["luma_mean"]:5.1f} '
                         f'[{b["luma_min"]:.0f}..{b["luma_max"]:.0f}] contrast={b["contrast_mean"]:5.1f} shots={b["shots"]}')
