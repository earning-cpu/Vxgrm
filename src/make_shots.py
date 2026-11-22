#!/usr/bin/env python3
"""Shot list v2 — every scene re-cut as 2-3 dynamic shots (wide / detail / punch).
Shot durations tile each scene exactly (sum == scene_len). Writes production/shots.json
and patches production/timeline.json with absolute cut times for the QA spike whitelist."""
import json, os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
TL_PATH = os.path.join(ROOT, 'production', 'timeline.json')

# (image, crop=(x,y,w,h)|None, move, peak_zoom, weight, wobble)
SHOTS = {
    'S01': [('s01_hook.jpg', None, 'ease_in', 1.16, 2.30, 15),
            ('s01_hook.jpg', (380, 700, 860, 1529), 'punch', 1.22, 2.20, 20),
            ('s01_hook.jpg', (460, 240, 700, 1244), 'ease_in', 1.24, 1.94, 15)],
    'S02': [('s02_troffea.jpg', (210, 80, 1200, 2133), 'ease_in', 1.18, 2.40, 15),
            ('s02_troffea.jpg', (430, 60, 760, 1351), 'punch', 1.20, 2.42, 19),
            ('s02_troffea.jpg', (120, 1500, 640, 1138), 'ease_in', 1.22, 2.21, 15)],
    'S03': [('s03_fourhundred.jpg', None, 'ease_out', 1.17, 2.66, 15),
            ('s03_fourhundred.jpg', (300, 900, 1000, 1778), 'ease_in', 1.20, 2.42, 16),
            ('s03_fourhundred.jpg', (760, 60, 620, 1102), 'ease_in', 1.22, 2.08, 15)],
    'S04': [('s04_feet.jpg', None, 'ease_in', 1.17, 2.52, 15),
            ('s04_feet.jpg', (250, 1400, 700, 1244), 'punch', 1.22, 2.30, 20),
            ('s04_feet.jpg', (620, 1200, 900, 1600), 'ease_in', 1.18, 2.30, 15)],
    'S05': [('s05_council.jpg', None, 'ease_in', 1.16, 1.90, 15),
            ('s05_council.jpg', (330, 900, 900, 1600), 'ease_in', 1.20, 1.80, 15),
            ('s05_council.jpg', (250, 1100, 1000, 1778), 'punch', 1.20, 1.63, 18)],
    'S06': [('s06_musicians.jpg', (280, 900, 1050, 1867), 'ease_in', 1.18, 2.30, 16),
            ('s06_musicians.jpg', (550, 1280, 900, 1600), 'punch', 1.22, 2.30, 20),
            ('s06_musicians.jpg', (850, 1000, 700, 1244), 'ease_in', 1.20, 1.84, 15)],
    'S07': [('s07_collapse.jpg', None, 'ease_out', 1.16, 3.06, 15),
            ('s07_collapse.jpg', (600, 800, 950, 1689), 'ease_in', 1.20, 2.35, 15),
            ('s07_collapse.jpg', (80, 1100, 900, 1600), 'ease_in', 1.18, 2.52, 15)],
    'S08': [('s08_shrine.jpg', None, 'ease_in', 1.15, 2.10, 15),
            ('s08_shrine.jpg', (150, 1450, 800, 1422), 'ease_in', 1.20, 1.90, 15),
            ('s08_shrine.jpg', (660, 20, 660, 1173), 'ease_in', 1.22, 2.01, 15)],
    'S09': [('s09_chapel.jpg', None, 'ease_out', 1.16, 2.36, 15),
            ('s09_chapel.jpg', (60, 1458, 800, 1422), 'punch', 1.20, 2.06, 19),
            ('s09_chapel.jpg', (330, 380, 500, 889), 'punch', 1.18, 2.01, 18)],
    'S10': [('s10_rye.jpg', None, 'ease_out', 1.16, 3.30, 15),
            ('s10_rye.jpg', (100, 420, 760, 1351), 'punch', 1.22, 2.36, 20),
            ('s10_rye.jpg', (210, 747, 1200, 2133), 'ease_in', 1.18, 2.42, 15)],
    'S11': [('s11_still.jpg', None, 'ease_in', 1.18, 3.60, 15),
            ('s11_still.jpg', (350, 600, 700, 1244), 'ease_in', 1.22, 3.10, 16),
            ('s11_still.jpg', (400, 1600, 480, 853), 'punch', 1.24, 3.15, 20)],
}

# scene-level FX applied after concat: list of fx names
SCENE_FX = {
    'S01': ['rain', 'fog'],
    'S02': [],
    'S03': ['fog'],
    'S04': [],
    'S05': ['flicker'],
    'S06': ['embers', 'rgbashift'],
    'S07': ['flicker'],
    'S08': ['fog'],
    'S09': ['flicker'],
    'S10': ['lightning'],
    'S11': ['rain', 'fog'],
}

tl = json.load(open(TL_PATH))
shots = []
cuts = []
idx = 0
for sc in tl['scenes']:
    sid = sc['id']
    plan = SHOTS[sid]
    weights = [p[4] for p in plan]
    total_w = sum(weights)
    local = 0.0
    for j, (img, crop, move, peak, w, wobble) in enumerate(plan):
        if j < len(plan) - 1:
            dur = sc['scene_len'] * w / total_w
        else:
            dur = sc['scene_len'] - local  # absorb rounding into last shot
        abs_start = sc['actual_start'] + local
        cuts.append(abs_start)
        shots.append(dict(idx=idx, scene=sid, image=img, crop=crop, move=move, peak=peak,
                          dur=round(dur, 4), frames=int(round(dur * 30)), wobble=wobble,
                          abs_start=round(abs_start, 4)))
        idx += 1
        local += dur
# remove duplicates (scene starts double as cut of previous scene start? no—only shot boundaries)
cuts = sorted(set(round(c, 4) for c in cuts))
# cut points are shot starts; the first shot of each scene IS a cut (scene boundary) — keep for QA whitelist
tl['cuts'] = cuts
json.dump(tl, open(TL_PATH, 'w'), indent=1)
with open(os.path.join(ROOT, 'production', 'shots.json'), 'w') as f:
    json.dump(dict(shots=shots, scene_fx=SCENE_FX), f, indent=1)
print(f'{len(shots)} shots written to production/shots.json')
for s in shots:
    c = f'crop={s["crop"]}' if s['crop'] else 'full'
    print(f"  shot{s['idx']:>2} {s['scene']} {s['move']:<8} peak={s['peak']} dur={s['dur']:.2f}s frames={s['frames']} {c}")
