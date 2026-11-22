#!/usr/bin/env python3
"""Build v2 — shot-based edit: 33 shots -> per-scene concat -> scene FX -> xfade -> grade -> mix -> captions."""
import json, os, subprocess, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
FF = os.path.join(ROOT, '.venv', 'lib', 'python3.11', 'site-packages', 'imageio_ffmpeg', 'binaries', 'ffmpeg-linux-x86_64-v9.0.2')
WORK = os.path.join(ROOT, 'assets', 'segments2')
os.makedirs(WORK, exist_ok=True)
OUT_DIR = os.path.join(ROOT, 'output')
CAPTIONS = os.path.join(ROOT, 'production', 'captions.ass')
TIMELINE = json.load(open(os.path.join(ROOT, 'production', 'timeline.json')))
SHOTS = json.load(open(os.path.join(ROOT, 'production', 'shots.json')))
TOTAL = TIMELINE['total']
FADE = 0.45

def run(args, desc):
    print(f'» {desc}', flush=True)
    p = subprocess.run([FF, '-hide_banner', '-y', *args], capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-4000:])
        sys.exit(f'FAILED: {desc}')
    return p

SKIP_VIDEO = os.environ.get('SKIP_VIDEO') == '1' and os.path.exists(os.path.join(WORK, 'scenefx_S11.mp4'))
shot_paths = [os.path.join(WORK, f"shot_{s['idx']:02d}.mp4") for s in SHOTS['shots']]
scene_paths = {sc['id']: os.path.join(WORK, f'scene_{sc["id"]}.mp4') for sc in TIMELINE['scenes']}

if not SKIP_VIDEO:
  # ---------- Step 1: shots ----------
  shot_paths = []
  for s in SHOTS['shots']:
    img = os.path.join(ROOT, 'assets', 'work', s['image'])
    N = s['frames']
    P, W = s['peak'], s['wobble']
    exp = 1.7 if s['move'] != 'punch' else 3.2
    if s['move'] == 'ease_out':
        z = f"'{P:.3f}-{P - 1:.3f}*pow(on/{N},{exp})'"
    else:
        z = f"'1+{P - 1:.3f}*pow(on/{N},{exp})'"
    x = f"'iw/2-(iw/zoom/2)+{W}*sin(on*0.055)'"
    y = f"'ih/2-(ih/zoom/2)+{W}*cos(on*0.043+1.1)'"
    chain = []
    if s['crop']:
        cx, cy, cw, ch = s['crop']
        chain.append(f'crop={cw}:{ch}:{cx}:{cy}')
    chain.append('scale=1620:2880:flags=lanczos')
    chain.append(f'zoompan=z={z}:x={x}:y={y}:d={N}:s=1080x1920:fps=30')
    chain.append('setsar=1,format=yuv420p')
    out = os.path.join(WORK, f"shot_{s['idx']:02d}.mp4")
    run(['-loop', '1', '-i', img, '-vf', ','.join(chain), '-frames:v', str(N),
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', out],
        f"shot {s['idx']:02d} {s['scene']} {s['move']} ({N}f)")
    shot_paths.append(out)

  # ---------- Step 2: per-scene concat ----------
  scene_paths = {}
  for sc in TIMELINE['scenes']:
      sid = sc['id']
      ss = [shot_paths[s['idx']] for s in SHOTS['shots'] if s['scene'] == sid]
      inputs = []
      for p in ss:
          inputs += ['-i', p]
      labels = ''.join(f'[{i}:v]' for i in range(len(ss)))
      out = os.path.join(WORK, f'scene_{sid}.mp4')
      run([*inputs, '-filter_complex', f'{labels}concat=n={len(ss)}:v=1:a=0[v]',
           '-map', '[v]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p', out],
          f'concat {sid} ({len(ss)} shots)')
      scene_paths[sid] = out

# ---------- Step 2b: scene FX ----------
def fx_chain(sid):
    fx = SHOTS['scene_fx'].get(sid, [])
    if not fx:
        return None
    parts = []
    label = '[0:v]'
    idx = 1
    pre = []
    # per-scene shadow lift: candlelit/collapse scenes are too dark for phone screens
    if sid in ('S07', 'S05', 'S09'):
        pre.append("eq=gamma=1.14")
    if 'flicker' in fx:
        pre.append("eq=brightness='0.016*sin(2*PI*3.1*t)+0.010*sin(2*PI*7.6*t+1.3)':eval=frame")
    if 'lightning' in fx:
        pre.append("eq=gamma='1+0.85*(between(t,1.05,1.12)+between(t,2.66,2.73))':eval=frame")
    if pre:
        parts.append(f'{label}{",".join(pre)}[pre]')
        label = '[pre]'
    fx_inputs = []
    blends = []
    for name, op in (('rain', 0.38), ('embers', 0.52), ('fog', 0.22)):
        if name in fx:
            fx_inputs += ['-i', os.path.join(ROOT, 'assets', 'fx', f'{name}.mp4')]
            parts.append(f'[{idx}:v]trim=duration={TIMELINE["scenes"][[s["id"] for s in TIMELINE["scenes"]].index(sid)]["scene_len"]:.3f},setpts=PTS-STARTPTS[fx{idx}]')
            blends.append((label, f'[fx{idx}]', op, f'[b{idx}]'))
            label = f'[b{idx}]'
            idx += 1
    for a, b, op, o in blends:
        parts.append(f'{a}{b}blend=all_mode=screen:all_opacity={op}{o}')
    if 'rgbashift' in fx:
        parts.append(f'{label}rgbashift=rh=1:bh=-1[out]')
        label = '[out]'
    return parts, fx_inputs, label

scene_fx_paths = {}
for sc in TIMELINE['scenes']:
    sid = sc['id']
    built = fx_chain(sid)
    src = scene_paths[sid]
    dst = os.path.join(WORK, f'scenefx_{sid}.mp4')
    if built is None:
        run(['-i', src, '-c:v', 'copy', dst], f'fx {sid}: none (stream copy)')
    else:
        parts, fx_inputs, out_label = built
        run(['-i', src, *fx_inputs, '-filter_complex', ';'.join(parts),
             '-map', out_label, '-c:v', 'libx264', '-preset', 'fast', '-crf', '16',
             '-pix_fmt', 'yuv420p', dst], f'fx {sid}: {SHOTS["scene_fx"].get(sid)}')
    scene_fx_paths[sid] = dst

# ---------- Step 3: xfade chain ----------
seg_paths = [scene_fx_paths[sc['id']] for sc in TIMELINE['scenes']]
n = len(seg_paths)
inputs = []
for p in seg_paths:
    inputs += ['-i', p]
parts, prev, cum = [], '[0:v]', TIMELINE['scenes'][0]['scene_len']
for k in range(1, n):
    offset = cum - FADE
    cum += TIMELINE['scenes'][k]['scene_len'] - FADE
    out = f'[x{k}]'
    parts.append(f'{prev}[{k}:v]xfade=transition=fade:duration={FADE}:offset={offset:.4f}{out}')
    prev = out
base = os.path.join(WORK, 'base.mp4')
run([*inputs, '-filter_complex', ';'.join(parts), '-map', prev,
     '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p', base],
    'xfade chain -> base.mp4')
base_dur = sum(s['scene_len'] for s in TIMELINE['scenes']) - (n - 1) * FADE

# ---------- Step 4: grade ----------
graded = os.path.join(WORK, 'graded.mp4')
run(['-i', base,
     '-vf', f'vignette=angle=PI/4.3,noise=alls=6:allf=t+u,fade=t=in:st=0:d=0.5,fade=t=out:st={max(base_dur-1.25,0.5):.2f}:d=1.25,format=yuv420p',
     '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', graded], 'grade')

# ---------- Step 5: audio mix ----------
mix = os.path.join(WORK, 'mix.wav')
audio_inputs, filter_parts = [], []
idx = 0
vo_starts = {}
for sc in TIMELINE['scenes']:
    vo_starts.setdefault(sc['vo'], sc['vo_start'])
for name, path_start in vo_starts.items():
    audio_inputs += ['-i', os.path.join(ROOT, 'assets', 'audio', name)]
    delay_ms = int(round(path_start * 1000))
    filter_parts.append(f'[{idx}:a]aformat=channel_layouts=stereo,adelay={delay_ms}|{delay_ms},volume=1.0[vo{idx}]')
    idx += 1
vo_labels = ''.join(f'[vo{i}]' for i in range(len(vo_starts)))
amb = [('amb_drone.wav', 0.50), ('amb_wind.wav', 0.30)]
amb_labels = ''
for name, vol in amb:
    audio_inputs += ['-i', os.path.join(ROOT, 'assets', 'audio', name)]
    filter_parts.append(f'[{idx}:a]aformat=channel_layouts=stereo,atrim=0:{TOTAL:.2f},asetpts=PTS-STARTPTS,volume={vol}[amb{idx}]')
    amb_labels += f'[amb{idx}]'
    idx += 1
STINGER_T = next(t for n_, t in TIMELINE['sfx'] if n_ == 'stinger')
sfx_events = [e for e in TIMELINE['sfx'] if e[0] not in ('murmur2',)] + [('riser', max(STINGER_T - 1.22, 0.05))]
SFX_MAP = {'bell': ('sfx_bell.wav', 0.75), 'bell2': ('sfx_bell.wav', 0.55),
           'heartbeat': ('sfx_heartbeat.wav', 0.80), 'stinger': ('sfx_stinger.wav', 0.90),
           'rumble': ('sfx_rumble.wav', 0.62), 'tap': ('sfx_tap.wav', 0.60),
           'subdrop': ('sfx_subdrop.wav', 0.85), 'murmur': ('sfx_murmur.wav', 0.42),
           'riser': ('sfx_riser.wav', 0.80)}
sfx_labels = ''
for name, t in sfx_events:
    if name not in SFX_MAP:
        continue
    fname, vol = SFX_MAP[name]
    audio_inputs += ['-i', os.path.join(ROOT, 'assets', 'audio', fname)]
    delay_ms = int(round(t * 1000))
    filter_parts.append(f'[{idx}:a]aformat=channel_layouts=stereo,adelay={delay_ms}|{delay_ms},volume={vol}[sfx{idx}]')
    sfx_labels += f'[sfx{idx}]'
    idx += 1
total_inputs = len(vo_starts) + len(amb) + len([e for e in sfx_events if e[0] in SFX_MAP])
filter_parts.append(f'{vo_labels}{amb_labels}{sfx_labels}amix=inputs={total_inputs}:normalize=0:dropout_transition=0[premix]')
filter_parts.append(f'[premix]highpass=f=25,afade=t=out:st={max(TOTAL-1.5,0.5):.2f}:d=1.5,loudnorm=I=-14:TP=-1.5:LRA=11:dual_mono=false[mixout]')
run([*audio_inputs, '-filter_complex', ';'.join(filter_parts),
     '-map', '[mixout]', '-ar', '48000', '-c:a', 'pcm_s16le', mix], 'audio mix + riser')

# ---------- Step 6: final mux + captions ----------
final = os.path.join(OUT_DIR, 'dancing-plague-1518-true-story-short.mp4')
run(['-i', graded, '-i', mix,
     '-filter_complex', f"[0:v]scale=in_range=auto:out_range=limited,subtitles='{CAPTIONS}':fontsdir=/usr/share/fonts/truetype/dejavu,format=yuv420p[v]",
     '-map', '[v]', '-map', '1:a',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
     '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
     '-shortest', final], 'final mux + caption burn')
print(f'\nFINAL → {final}')
print(f'expected duration ≈ {base_dur:.2f}s @30fps, 1080x1920')
