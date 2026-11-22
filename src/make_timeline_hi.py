#!/usr/bin/env python3
"""Master timeline v3 (Hindi cut) — every caption window measured from the actual
synthesized VO clip => zero latency by construction. Word-level karaoke (\k) timing
proportional to word length. SFX ducked under VO at mix time (see build_video2.py)."""
import json, os, re, subprocess

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
FF = os.path.join(ROOT, '.venv', 'lib', 'python3.11', 'site-packages', 'imageio_ffmpeg', 'binaries', 'ffmpeg-linux-x86_64-v9.0.2')
FADE = 0.45
LEAD = 0.32          # silence before first word (fade-in breathes)
GAP = 0.09           # breath between chunks
SCENE_TAIL = 0.42    # beat after last word of a scene
S06_PRE = 0.78       # silence-before-drop pocket: riser lands, stinger hits, THEN VO

# (scene, file, verbatim text, keyword|None)
CHUNKS = [
    ('S01', 'c01.mp3', '14 जुलाई 1518 — स्ट्रासबर्ग।', '1518'),
    ('S01', 'c02.mp3', 'एक औरत सड़क पर नाचने लगी।', 'नाचने लगी'),
    ('S02', 'c03.mp3', 'इतिहास उसे Frau Troffea कहता है।', 'Frau Troffea'),
    ('S02', 'c04.mp3', 'न संगीत, न वजह — वो रुक नहीं सकती थी।', 'रुक नहीं सकती'),
    ('S03', 'c05.mp3', 'वो दिनों-दिन नाचती रही।', 'दिनों-दिन'),
    ('S03', 'c06.mp3', 'फिर तीस लोग जुड़ गए — फिर चार सौ।', 'चार सौ'),
    ('S04', 'c07.mp3', 'आँखें सूनी हो गईं।', 'आँखें सूनी'),
    ('S04', 'c08.mp3', 'पैर खून से लाल — फिर भी नाचते रहे।', 'नाचते रहे'),
    ('S05', 'c09.mp3', 'शहर के लीडर्स डर गए —', 'डर गए'),
    ('S05', 'c10.mp3', 'इलाज बताया: और ज़्यादा नाच!', 'और ज़्यादा नाच'),
    ('S06', 'c11.mp3', 'इलाज ही तबाही बन गया।', 'तबाही'),
    ('S06', 'c12.mp3', 'सड़कें और लोगों से भर गईं।', 'भर गईं'),
    ('S07', 'c13.mp3', 'कुछ क्रोनिकल्स का दावा है —', 'दावा'),
    ('S07', 'c14.mp3', 'एक ही दिन में 15 लोग मर गए।', '15 लोग'),
    ('S07', 'c15.mp3', 'असली गिनती आज भी गुम है।', 'गुम है'),
    ('S08', 'c16.mp3', 'उन्हें Saint Vitus के मंदिर ले जाया गया —', 'Saint Vitus'),
    ('S08', 'c17.mp3', 'लाल जूते, पवित्र जल से ब्लेस।', 'लाल जूते'),
    ('S09', 'c18.mp3', 'उन्होंने लैटिन में माफ़ी माँगी…', 'माफ़ी'),
    ('S09', 'c19.mp3', 'और सितंबर तक — नाच रुक गया।', 'रुक गया'),
    ('S10', 'c20.mp3', 'वजह आज भी अनसुलझी है।', 'अनसुलझी'),
    ('S10', 'c21.mp3', 'जहरीला राई? या Mass Hysteria?', 'Mass Hysteria'),
    ('S10', 'c22.mp3', 'या कुछ ऐसा जो चाहता था — नाचते रहें।', 'नाचते रहें'),
    ('S11', 'c23.mp3', 'अगर प्लेग कभी खत्म ही नहीं हुई —', 'खत्म ही नहीं'),
    ('S11', 'c24.mp3', 'तो कहीं कोई… आज भी नाच रहा है।', 'आज भी नाच रहा है'),
    ('S11', 'c25.mp3', 'ऐसी सच्ची कहानियों के लिए — फ़ॉलो करें।', 'फ़ॉलो करें'),
]
SCENE_IMG = {'S01': 's01_hook.jpg', 'S02': 's02_troffea.jpg', 'S03': 's03_fourhundred.jpg',
             'S04': 's04_feet.jpg', 'S05': 's05_council.jpg', 'S06': 's06_musicians.jpg',
             'S07': 's07_collapse.jpg', 'S08': 's08_shrine.jpg', 'S09': 's09_chapel.jpg',
             'S10': 's10_rye.jpg', 'S11': 's11_still.jpg'}
SCENE_ORDER = ['S01','S02','S03','S04','S05','S06','S07','S08','S09','S10','S11']

import sys
MISSING = [fname for _, fname, _, _ in CHUNKS
           if not os.path.exists(os.path.join(ROOT, 'assets', 'audio', 'hi', fname))]
if MISSING:
    sys.exit('missing VO clips (generate first): ' + ', '.join(MISSING))

def vo_dur(path):
    out = subprocess.run([FF, '-hide_banner', '-i', path], capture_output=True, text=True).stderr
    m = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', out)
    h, mnt, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mnt * 60 + s

# measure all clips
durs = []
for sid, fname, text, kw in CHUNKS:
    p = os.path.join(ROOT, 'assets', 'audio', 'hi', fname)
    durs.append(vo_dur(p))

# ---- layout in raw (pre-fade) time ----
cursor = LEAD
scenes = []
chunks_meta = []   # (scene_idx, chunk_idx, raw_start, dur, ...)
for sid in SCENE_ORDER:
    sc_start = cursor
    local = 0.0
    for (c_sid, fname, text, kw), dur in zip([c for c in CHUNKS if c[0] == sid],
                                             [d for (c, d) in zip(CHUNKS, durs) if c[0] == sid]):
        if c_sid == 'S06' and local == 0.0:
            local += S06_PRE
        chunks_meta.append(dict(scene=sid, file=fname, text=text, kw=kw,
                                raw_start=sc_start + local, dur=dur))
        local += dur + GAP
    scene_len = local - GAP + SCENE_TAIL
    cursor = sc_start + scene_len
    scenes.append(dict(id=sid, image=SCENE_IMG[sid], scene_start=sc_start, scene_len=scene_len))

PRE_FADE_TOTAL = cursor
ACTUAL_TOTAL = PRE_FADE_TOTAL - (len(scenes) - 1) * FADE

# map raw -> actual (xfade compression)
for i, sc in enumerate(scenes):
    sc['actual_start'] = round(sc['scene_start'] - i * FADE, 4)
    sc['shift'] = i * FADE
    sc['scene_len'] = round(sc['scene_len'], 4)
    sc['scene_start'] = round(sc['scene_start'], 4)
ACTUAL_TOTAL = round(ACTUAL_TOTAL, 4)

for ch in chunks_meta:
    si = SCENE_ORDER.index(ch['scene'])
    ch['start'] = round(ch['raw_start'] - si * FADE, 4)
    ch['end'] = round(ch['raw_start'] + ch['dur'] - si * FADE, 4)

def ass_time(t):
    t = max(0.0, min(t, ACTUAL_TOTAL))
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def esc(s):
    return s.replace('{', '\\{').replace('}', '\\}')

RED = '{\\c&H4D48E5&\\2c&H4D48E5&}'   # red in both sweep states (keyword)
WHT = '{\\c&HFFFFFF&\\2c&HFFFFFF&}'

def karaoke_weighted(text, kw, total_cs):
    """Proper approach: per-token \\k, keyword tokens painted red via inline colour."""
    tokens = text.split(' ')
    weights = [max(len(t), 2) for t in tokens]
    tw = sum(weights)
    cs_list = [max(4, round(w / tw * total_cs)) for w in weights]
    cs_list[-1] = max(4, cs_list[-1] + (total_cs - sum(cs_list)))
    kw_tokens = set(kw.split(' ')) if kw else set()
    PUNCT = '।,!?….—–-'
    out = []
    for tok, cs in zip(tokens, cs_list):
        body = esc(tok)
        if tok.strip(PUNCT) in kw_tokens:
            out.append(f'{RED}{{\\k{cs}}}{body}{WHT}')
        else:
            out.append(f'{{\\k{cs}}}{body}')
    return ' '.join(out)

events = []
for ch in chunks_meta:
    total_cs = max(10, int(round((ch['end'] - ch['start']) * 100)))
    txt = karaoke_weighted(ch['text'], ch['kw'], total_cs)
    events.append((ch['start'], ch['end'], txt, 'Viral'))

# DateFlash date stamp (S01 hook)
c1 = chunks_meta[0]
events.append((0.06, round(c1['end'] + 1.35, 2), '14 JULY 1518 · स्ट्रासबर्ग', 'DateFlash'))
events.sort(key=lambda e: e[0])

ASS_HEAD = """[Script Info]
Title: Dancing Plague 1518 — Hindi Captions (Devanagari)
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Viral,Noto Sans Devanagari,54,&H00FFFFFF,&H9AFFFFFF,&H00000000,&H64000000,-1,0,1,3.4,1.6,2,48,48,560,1
Style: DateFlash,Noto Sans Devanagari,52,&H004D48E5,&H000000FF,&H00000000,&H64000000,-1,0,1,2.6,1.3,5,24,24,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(os.path.join(ROOT, 'production', 'captions.ass'), 'w', encoding='utf-8') as f:
    f.write(ASS_HEAD)
    for start, end, text, style in events:
        if style == 'Viral':
            pos = '\\an2\\pos(540,1352)\\fad(55,40)\\fscx62\\fscy62\\t(0,110,\\fscx116\\fscy116)\\t(110,205,\\fscx100\\fscy100)'
        else:
            pos = '\\an5\\pos(540,830)\\fad(60,110)\\t(0,240,\\alpha&H00&)\\t(290,330,\\alpha&H66&)\\t(365,425,\\alpha&H00&)\\t(510,565,\\alpha&H80&)\\t(625,685,\\alpha&H00&)'
        f.write(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{{{pos}}}{text}\n')

s = {sc['id']: sc for sc in scenes}
S06 = s['S06']; S01 = s['S01']; S03 = s['S03']; S04 = s['S04']; S07 = s['S07']; S08 = s['S08']; S09 = s['S09']; S11 = s['S11']
stinger_t = S06['actual_start'] + S06_PRE - 0.04   # lands in the VO pocket
print(f'stinger @ {stinger_t:.2f}s (VO pocket)')
sfx = [
    ('bell', S01['actual_start'] + 1.55),
    ('murmur', S03['actual_start'] + 1.00),
    ('heartbeat', S04['actual_start'] + 1.10),
    ('stinger', stinger_t),
    ('rumble', S07['actual_start'] + 0.10),
    ('tap', S08['actual_start'] + 1.35),
    ('bell2', S09['actual_start'] + 1.10),
    ('subdrop', S11['actual_start'] + 3.30),
]
timeline = dict(total=ACTUAL_TOTAL, pre_fade_total=round(PRE_FADE_TOTAL, 4), fade=FADE,
                scenes=[dict(id=sc['id'], image=sc['image'], vo=None, vo_start=None,
                             vo_dur=None, vo_offset=0.0, scene_start=sc['scene_start'],
                             scene_len=sc['scene_len'], actual_start=sc['actual_start'],
                             kb='zoomin',
                             chunks=[{'file': ch['file'], 'start': ch['start'], 'end': ch['end']}
                                     for ch in chunks_meta if ch['scene'] == sc['id']])
                        for sc in scenes],
                vo_chunks=[{'file': ch['file'], 'start': ch['start'], 'end': ch['end']} for ch in chunks_meta],
                sfx=sfx)
with open(os.path.join(ROOT, 'production', 'timeline.json'), 'w') as f:
    json.dump(timeline, f, indent=1, ensure_ascii=False)
print(f'ACTUAL duration = {ACTUAL_TOTAL:.2f}s  ({ACTUAL_TOTAL*30:.0f} frames)')
for sc in scenes:
    print(f"{sc['id']:>4}  start={sc['actual_start']:.2f} len={sc['scene_len']:.2f}")
for name, t in sfx:
    print(f'  sfx {name:<9} @ {t:.2f}s')
print(f'captions: {len(events)} events')
