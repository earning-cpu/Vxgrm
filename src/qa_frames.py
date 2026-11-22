#!/usr/bin/env python3
"""Exhaustive per-frame QA over every extracted frame + caption presence verification."""
import csv, json, os, re, sys
import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
FRAMES = os.path.join(ROOT, 'qa', 'frames')
ASS = os.path.join(ROOT, 'production', 'captions.ass')

files = sorted(f for f in os.listdir(FRAMES) if f.endswith('.jpg'))
N = len(files)
print(f'frames to check: {N}')

def load(i):
    return np.asarray(Image.open(os.path.join(FRAMES, files[i])).convert('RGB'), dtype=np.float32)

# ---------- pass 1: per-frame metrics ----------
metrics = []
prev_small = None
for i in range(N):
    try:
        im = load(i)
    except Exception as e:
        metrics.append((i, files[i], None, None, None, None, None, f'DECODE_ERROR: {e}'))
        continue
    gray = im.mean(axis=2)
    mean, std = float(gray.mean()), float(gray.std())
    mn, mx = float(gray.min()), float(gray.max())
    # dead-ish channels (informational)
    chans = [float(im[:, :, c].std()) for c in range(3)]
    dead = ','.join(str(c) for c, s in enumerate(chans) if s < 0.5) or '-'
    small = np.asarray(Image.fromarray(im.astype(np.uint8)).convert('L').resize((64, 114)), dtype=np.float32)
    diff = float(np.mean(np.abs(small - prev_small))) if prev_small is not None else 0.0
    prev_small = small
    flag = '-'
    metrics.append((i, files[i], mean, std, mn, mx, diff, dead))

# ---------- pass 2: anomaly detection ----------
bugs = []
def bug(cat, detail, frames):
    bugs.append(dict(category=cat, detail=detail, frames=frames))

BLACK_T, WHITE_T, FROZEN_T, SPIKE_T = 9.0, 245.0, 0.05, 20.0
frame_times = [i / 30.0 for i in range(N)]

# global dark/bright runs
runs = []
cur = None
for i, m in enumerate(metrics):
    _, _, mean, std, mn, mx, _, _ = m
    kind = None
    if mean is not None and mean < BLACK_T and std < 14:
        kind = 'BLACK'
    elif mean is not None and mean > WHITE_T and std < 14:
        kind = 'WHITE'
    if kind:
        if cur and cur[0] == kind and cur[2] == i - 1:
            cur[2] = i
        else:
            if cur:
                runs.append(cur)
            cur = [kind, i, i]
    else:
        if cur:
            runs.append(cur)
            cur = None
if cur:
    runs.append(cur)
for kind, a, b in runs:
    # allow the intended fade-in/out to black at the very edges
    edge_ok = (a < 20 and kind == 'BLACK') or (b > N - 40 and kind == 'BLACK')
    bug('black-or-white-frame-run', f'{kind} run frames {a}-{b} ({(b-a+1)/30:.2f}s) edge_fade={edge_ok}', f'{a}-{b}')

_tl = json.load(open(os.path.join(ROOT, 'production', 'timeline.json')))
cut_frames = set()
# hard cuts from the shot table (absolute video time)
_sh = json.load(open(os.path.join(ROOT, 'production', 'shots.json')))
for s in _sh['shots']:
    f0 = int(round(s['abs_start'] * 30))
    for f in range(f0 - 2, f0 + 3):
        cut_frames.add(f)
# intentional lightning gamma bursts in S10 (see build_video2.py: local t 1.05-1.12 and 2.66-2.73)
_s10 = next(sc for sc in _tl['scenes'] if sc['id'] == 'S10')
for lt in (1.05, 1.12, 2.66, 2.73):
    f0 = int(round((_s10['actual_start'] + lt) * 30))
    for f in range(f0 - 1, f0 + 2):
        cut_frames.add(f)
print(f'whitelisted cut/flash frames (±2/±1): {len(cut_frames)}')

for i, m in enumerate(metrics):
    _, _, mean, std, mn, mx, diff, dead = m
    if mean is None:
        bug('decode-error', m[7], str(i))
        continue
    if dead != '-' and mean >= 20.0:  # near-black frames are intentional fade edges
        bug('dead-channel', f'channel(s) {dead} flat (std<0.5)', str(i))
    if i > 0 and diff > SPIKE_T and i not in cut_frames:
        bug('luma-spike', f'|frame diff| {diff:.2f} > {SPIKE_T}', str(i))

frozen_start = None
for i in range(1, N):
    diff = metrics[i][6]
    if diff is not None and diff < FROZEN_T:
        if frozen_start is None:
            frozen_start = i - 1
    else:
        if frozen_start is not None:
            if i - frozen_start >= 45:
                bug('frozen-run', f'{i - frozen_start} frames nearly identical ({(i - frozen_start) / 30:.1f}s)', f'{frozen_start}-{i - 1}')
            frozen_start = None
if frozen_start is not None and N - frozen_start >= 45:
    bug('frozen-run', f'{N - frozen_start} frames nearly identical at tail', f'{frozen_start}-{N - 1}')

# ---------- pass 3: caption presence + horizontal-clip detection ----------
def parse_ass(path):
    evts = []
    for line in open(path):
        if not line.startswith('Dialogue:'):
            continue
        p = line.split(',', 9)
        style = p[3]
        def t2s(ts):
            h, mnt, s = ts.split(':')
            return int(h) * 3600 + int(mnt) * 60 + float(s)
        evts.append((t2s(p[1]), t2s(p[2]), style, p[9]))
    return evts

events = parse_ass(ASS)
BAND_VIRAL = slice(1150, 1420)   # viral captions sit ~1240-1350
BAND_FLASH = slice(760, 1160)    # date flash is vertically centered
CLIP_EDGE = 36                   # px from each side counted as "over the margin"
missing, clipped = [], []
for si, (t0, t1, style, text) in enumerate(events):
    band = BAND_FLASH if style == 'DateFlash' else BAND_VIRAL
    f0, f1 = int(t0 * 30), min(N - 1, int(t1 * 30))
    found = 0
    clip_hits = 0
    lo = f0 + int(0.30 * max(1, f1 - f0))  # skip pop-in ramp
    for f in range(lo, f1 + 1, max(1, (f1 - lo) // 3)):
        im = load(f)
        b = im[band, :, :]
        bright = ((b.max(axis=2) > 190)).sum()
        reddish = ((b[:, :, 0] > 150) & (b[:, :, 1] < 135) & (b[:, :, 2] < 135)).sum()
        if bright + reddish > 60:
            found += 1
        # horizontal clip: meaningful bright pixels within CLIP_EDGE px of either border
        left = b[:, :CLIP_EDGE, :].max(axis=2) > 190
        right = b[:, -CLIP_EDGE:, :].max(axis=2) > 190
        if int(left.sum()) + int(right.sum()) > 25:
            clip_hits += 1
    if found == 0:
        missing.append((t0, t1, text.strip().replace('\\fad(90,70)', '')))
    if clip_hits >= 2:  # consistent overflow across the whole window
        clipped.append((t0, t1, text.strip().replace('\\fad(90,70)', '')))
for t0, t1, text in missing:
    bug('caption-missing', f'caption window [{t0:.2f}s-{t1:.2f}s] shows no legible text pixels: {text[:60]}', f'frames {int(t0*30)}-{int(t1*30)}')
for t0, t1, text in clipped:
    bug('caption-h-clip', f'text clipped at left/right edge in [{t0:.2f}s-{t1:.2f}s]: {text[:60]}', f'frames {int(t0*30)}-{int(t1*30)}')

# ---------- pass 4: expected scene boundaries vs huge global changes ----------
# informational: record scene-cut frames
tl = json.load(open(os.path.join(ROOT, 'production', 'timeline.json')))
for sc in tl['scenes'][1:]:
    f = int(sc['scene_start'] * 30)
    if 0 <= f < N:
        pass  # xfade = expected gradual transition; no assertion needed

# ---------- write metrics CSV + bug report ----------
with open(os.path.join(ROOT, 'qa', 'frame-metrics.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['frame', 'file', 'time_s', 'mean_luma', 'std_luma', 'min', 'max', 'diff_to_prev', 'dead_channels'])
    for i, m in enumerate(metrics):
        w.writerow([i, m[1], f'{i / 30:.4f}', *(f'{v:.4f}' if isinstance(v, float) else v for v in m[2:7]), m[7]])

print(f'black/white runs: {len(runs)}')
print(f'caption events: {len(events)}, missing: {len(missing)}')
print(f'TOTAL BUGS: {len(bugs)}')
for b in bugs:
    print(f"  [{b['category']}] {b['detail']} (frames {b['frames']})")
json.dump(bugs, open(os.path.join(ROOT, 'qa', 'frame-bugs.json'), 'w'), indent=1)
sys.exit(0 if len(bugs) == 0 else 2)
