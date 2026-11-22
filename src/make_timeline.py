#!/usr/bin/env python3
"""Master timeline v2 — computed in ACTUAL video time (post-xfade).
Segments keep pre-fade lengths for zoompan; captions/SFX use actual video time."""
import json, os, re, subprocess, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
FF = os.path.join(ROOT, '.venv', 'lib', 'python3.11', 'site-packages', 'imageio_ffmpeg', 'binaries', 'ffmpeg-linux-x86_64-v9.0.2')
FADE = 0.45

def vo_dur(name):
    out = subprocess.run([FF, '-hide_banner', '-i', os.path.join(ROOT, 'assets', 'audio', name)],
                         capture_output=True, text=True).stderr
    m = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', out)
    h, mnt, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mnt * 60 + s

BEATS = [
    ('S01', 's01_hook.jpg', 'vo_01_hook.mp3', 0.30, 'zoomin',
     ['ON JULY 14TH, 1518 —', 'A WOMAN BEGAN TO DANCE'], ['JULY 14TH, 1518']),
    ('S02', 's02_troffea.jpg', 'vo_02_context.mp3', 0.30, 'panup',
     ['HISTORY CALLS HER', 'FRAU TROFFEA.', 'NO MUSIC. NO REASON.', 'SHE COULD NOT STOP.'], ['FRAU TROFFEA', 'COULD NOT STOP']),
    ('S03', 's03_fourhundred.jpg', 'vo_03_build1.mp3', 0.30, 'zoomout',
     ['SHE DANCED FOR DAYS.', 'THEN — THIRTY OTHERS JOINED.', 'THEN 400.'], ['THIRTY OTHERS', '400']),
    ('S04', 's04_feet.jpg', 'vo_04_build2.mp3', 0.34, 'zoomin',
     ['VACANT EYES.', 'FEET BLED INTO THEIR SHOES.', 'THEY SCREAMED FOR HELP —', 'AND KEPT DANCING.'], ['VACANT EYES', 'BLED']),
    ('S05', 's05_council.jpg', 'vo_05_build3.mp3', 0.30, 'panright',
     ['THE CITY COUNCIL\'S CURE?', 'MORE DANCING.', 'HIRED MUSICIANS.'], ['MORE DANCING', 'HIRED MUSICIANS']),
    ('S06', 's06_musicians.jpg', 'vo_06_breadcrumb.mp3', 0.30, 'zoomout',
     ['THE CURE WAS', 'THE CATASTROPHE.', 'THE STREETS FILLED.'], ['CATASTROPHE']),
    ('S07', 's07_collapse.jpg', 'vo_07_toll.mp3', 0.34, 'zoomin',
     ['CHRONICLES CLAIM', '15 DIED IN ONE DAY.', 'THE TRUE TOLL IS LOST.'], ['15 DIED', 'LOST']),
    ('S08', 's08_shrine.jpg', 'vo_08_shrine.mp3', 0.30, 'panleft',
     ['MARCHED TO A SHRINE —', 'RED SHOES, HOLY WATER,', 'SAINT VITUS.'], ['SAINT VITUS', 'RED SHOES']),
    ('S09', 's09_chapel.jpg', 'vo_09_september.mp3', 0.42, 'zoomin',
     ['THEY BEGGED IN LATIN —', 'AND BY SEPTEMBER…', 'IT SIMPLY — STOPPED.'], ['STOPPED']),
    ('S10', 's10_rye.jpg', 'vo_10_loop.mp3', 0.12, 'zoomout',
     ['STILL UNSOLVED.', 'POISONED RYE? MASS HYSTERIA?', 'OR SOMETHING THAT', 'WANTED THEM DANCING.'], ['STILL UNSOLVED', 'POISONED RYE']),
    ('S11', 's11_still.jpg', None, 1.50, 'zoomin',
     ['IF THE PLAGUE NEVER ENDED…', 'SOMEONE IS STILL DANCING.', 'FOLLOW FOR MORE\\NTRUE NIGHTMARES'], ['STILL DANCING', 'FOLLOW']),
]
VO_SPLIT_S10 = 0.485  # vo_10 fraction played under S10 (word boundary after "dancing", word 17/35)

def words(s):
    return len(s.replace('—', ' ').replace('…', ' ').replace('?', ' ').split())

# ---- pass 1: pre-fade scene lengths and raw VO scheduling ----
raw = []
cursor = 0.0
for sid, img, vo, gap, kb, chunks, reds in BEATS:
    dur = vo_dur(vo) if vo else None
    start = cursor
    if sid == 'S10':
        scene_len = dur * VO_SPLIT_S10 + 0.10 + gap
        cursor = start + scene_len
        raw.append(dict(id=sid, image=img, vo=vo, vo_start_raw=start, vo_offset=0.0,
                        vo_dur=dur, scene_len=scene_len, kb=kb, chunks=chunks, reds=reds))
        continue
    if sid == 'S11':
        prev = raw[-1]
        vo_total = prev['vo_dur']
        vo_offset = VO_SPLIT_S10 * vo_total
        scene_len = (vo_total - vo_offset) + gap
        cursor = start + scene_len
        raw.append(dict(id=sid, image=img, vo=prev['vo'], vo_start_raw=prev['vo_start_raw'],
                        vo_offset=vo_offset, vo_dur=vo_total, scene_len=scene_len, kb=kb, chunks=chunks, reds=reds))
        continue
    scene_len = dur + gap
    cursor = start + scene_len
    raw.append(dict(id=sid, image=img, vo=vo, vo_start_raw=start, vo_offset=0.0,
                    vo_dur=dur, scene_len=scene_len, kb=kb, chunks=chunks, reds=reds))

PRE_FADE_TOTAL = cursor
ACTUAL_TOTAL = PRE_FADE_TOTAL - (len(raw) - 1) * FADE
# ---- pass 2: map raw (pre-fade) time -> actual video time: t_actual = t_raw - k*FADE ----
cum = 0.0
scenes = []
for i, r in enumerate(raw):
    a_start = cum
    cum += r['scene_len'] - FADE
    a_end = a_start + r['scene_len'] - (0 if i == len(raw) - 1 else 0)  # scene ends at its own pre-fade len; xfade only affects boundary visuals
    # actual video time of a raw timestamp inside scene i: t_raw - i*FADE
    shift = i * FADE
    vo_start = r['vo_start_raw'] - shift
    if r['id'] == 'S01':
        vo_start = 0.12
    if r['id'] == 'S11':
        vo_start = scenes[-1]['vo_start']  # shared clip with S10 — starts when S10's VO starts
    scenes.append(dict(id=r['id'], image=r['image'], vo=r['vo'], vo_start=round(vo_start, 4),
                       vo_dur=round(r['vo_dur'], 4) if r['vo_dur'] else None,
                       vo_offset=round(r['vo_offset'], 4),
                       scene_start=round(a_start, 4),
                       scene_len=round(r['scene_len'], 4),
                       actual_start=round(a_start, 4),
                       kb=r['kb'], chunks=r['chunks'], reds=r['reds']))

# actual end of video
ACTUAL_TOTAL = round(sum(r['scene_len'] for r in raw) - (len(raw) - 1) * FADE, 4)

def ass_time(t):
    t = max(0.0, min(t, ACTUAL_TOTAL))
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def esc(s):
    # escape ASS override-brace chars only; keep intentional \N line breaks intact
    return s.replace('{', '\\{').replace('}', '\\}')

def colorize(chunk, reds):
    txt = chunk
    for kw in reds:
        txt = txt.replace(kw, f'\x00{kw}\x01')
    txt = esc(txt)
    txt = txt.replace('\x00', '{\\c&H4D48E5&}').replace('\x01', '{\\c&HFFFFFF&}')
    return txt

events = []
shift_lookup = {sc['id']: idx * FADE for idx, sc in enumerate(scenes)}
for sc in scenes:
    shift = shift_lookup[sc['id']]
    slice_start = sc['vo_offset']
    slice_end = sc['vo_dur'] if sc['id'] != 'S10' else VO_SPLIT_S10 * sc['vo_dur']
    cw = [words(c) for c in sc['chunks']]
    total_cw = sum(cw)
    acc = slice_start
    for i, chunk in enumerate(sc['chunks']):
        w = cw[i]
        frac = w / total_cw
        c_start = sc['vo_start'] + acc
        c_end = sc['vo_start'] + acc + frac * (slice_end - slice_start)
        acc += frac * (slice_end - slice_start)
        c_end = min(c_end, ACTUAL_TOTAL)  # chunks tile exactly; no crossfade overlap
        c_start = min(c_start, ACTUAL_TOTAL - 0.15)
        events.append((c_start, c_end, colorize(chunk, sc['reds']), 'Viral'))

events.append((0.06, 2.30, 'STRASBOURG · 14 JULY 1518', 'DateFlash'))
events.sort(key=lambda e: e[0])

ASS_HEAD = """[Script Info]
Title: Dancing Plague 1518 — Viral Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Viral,DejaVu Sans Bold,60,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,1,3.6,1.8,2,55,55,560,1
Style: DateFlash,DejaVu Sans Bold,46,&H004D48E5,&H000000FF,&H00000000,&H64000000,-1,0,1,2.6,1.3,5,30,30,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(os.path.join(ROOT, 'production', 'captions.ass'), 'w') as f:
    f.write(ASS_HEAD)
    for start, end, text, style in events:
        pos = '\\an2\\pos(540,1352)' if style == 'Viral' else '\\an5\\pos(540,830)'
        f.write(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{{{pos}\\fad(70,50)}}{text}\n')

s = {sc['id']: sc for sc in scenes}
sfx = [
    ('bell', 1.85),
    ('murmur', s['S03']['actual_start'] + 0.2),
    ('heartbeat', s['S04']['actual_start'] + 0.35),
    ('stinger', s['S06']['actual_start'] + 0.05),
    ('rumble', s['S07']['actual_start'] + 0.1),
    ('tap', s['S09']['actual_start'] + 5.15),
    ('bell2', s['S09']['actual_start'] + 5.3),
    ('subdrop', s['S11']['actual_start'] + 1.1),
]
timeline = dict(total=ACTUAL_TOTAL, pre_fade_total=PRE_FADE_TOTAL, fade=FADE,
                scenes=[{k: v for k, v in sc.items() if k not in ('chunks', 'reds')} for sc in scenes],
                sfx=sfx)

print(f'ACTUAL video duration = {ACTUAL_TOTAL:.2f}s  ({ACTUAL_TOTAL*30:.0f} frames @30fps)')
for sc in scenes:
    print(f"{sc['id']:>4}  actual_start={sc['actual_start']:.2f} vo_start={sc['vo_start']:.2f} scene_len={sc['scene_len']:.2f} kb={sc['kb']}")
print('\nSFX:')
for name, t in sfx:
    print(f'  {name:<9} @ {t:.2f}s')
with open(os.path.join(ROOT, 'production', 'timeline.json'), 'w') as f:
    json.dump(timeline, f, indent=1)
print(f'\ncaptions: {len(events)} events')
