#!/usr/bin/env python3
"""Build the Dancing Plague 1518 Short end-to-end (video + audio + captions)."""
import json, os, subprocess, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
FF = os.path.join(ROOT, '.venv', 'lib', 'python3.11', 'site-packages', 'imageio_ffmpeg', 'binaries', 'ffmpeg-linux-x86_64-v9.0.2')
WORK = os.path.join(ROOT, 'assets', 'segments')
os.makedirs(WORK, exist_ok=True)
OUT_DIR = os.path.join(ROOT, 'output')
os.makedirs(OUT_DIR, exist_ok=True)
CAPTIONS = os.path.join(ROOT, 'production', 'captions.ass')
TIMELINE = json.load(open(os.path.join(ROOT, 'production', 'timeline.json')))
TOTAL = TIMELINE['total']
FADE = 0.45

def run(args, desc):
    print(f'» {desc}', flush=True)
    p = subprocess.run([FF, '-hide_banner', '-y', *args], capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-3500:])
        sys.exit(f'FAILED: {desc}')
    return p

SKIP_VIDEO = os.environ.get('SKIP_VIDEO') == '1' and os.path.exists(os.path.join(WORK, 'graded.mp4'))
if SKIP_VIDEO:
    print('SKIP_VIDEO=1 — reusing existing graded.mp4')
    seg_paths = [os.path.join(WORK, f"seg_{sc['id']}.mp4") for sc in TIMELINE['scenes']]
    base_dur = TOTAL
    graded = os.path.join(WORK, 'graded.mp4')
else:
  # ---------- Step 1: scene segments with Ken Burns zoompan ----------
  seg_paths = []
  for sc in TIMELINE['scenes']:
    n = int(round(sc['scene_len'] * 30))
    img = os.path.join(ROOT, 'assets', 'work', sc['image'])
    seg = os.path.join(WORK, f"seg_{sc['id']}.mp4")
    N = n  # frames
    if sc['kb'] == 'zoomin':
        z, x, y = f"'1+0.17*on/{N}'", "'iw/2-(iw/zoom/2)'", "'ih/2-(ih/zoom/2)'"
    elif sc['kb'] == 'zoomout':
        z, x, y = f"'1.17-0.17*on/{N}'", "'iw/2-(iw/zoom/2)'", "'ih/2-(ih/zoom/2)'"
    elif sc['kb'] == 'panup':
        z, x, y = "'1.24'", "'iw/2-(iw/zoom/2)'", f"'(ih-ih/zoom)*(1-on/{N})'"
    elif sc['kb'] == 'panleft':
        z, x, y = "'1.24'", f"'(iw-iw/zoom)*on/{N}'", "'ih/2-(ih/zoom/2)'"
    elif sc['kb'] == 'panright':
        z, x, y = "'1.24'", f"'(iw-iw/zoom)*(1-on/{N})'", "'ih/2-(ih/zoom/2)'"
    else:
        z, x, y = "'1.1'", "'iw/2-(iw/zoom/2)'", "'ih/2-(ih/zoom/2)'"
    vf = (f"scale=1620:2880:flags=lanczos,"
          f"zoompan=z={z}:x={x}:y={y}:d={N}:s=1080x1920:fps=30,"
          f"setsar=1,format=yuv420p")
    run(['-loop', '1', '-i', img, '-vf', vf, '-frames:v', str(N),
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', seg], f"segment {sc['id']} ({N} frames)")
    seg_paths.append(seg)

if not SKIP_VIDEO:
  # ---------- Step 2: xfade chain ----------
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
       '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', base],
      'xfade chain -> base.mp4')
  # accurate duration: sum(scene_len) - (n-1)*FADE
  base_dur = sum(s['scene_len'] for s in TIMELINE['scenes']) - (n - 1) * FADE
  print(f'base duration ≈ {base_dur:.2f}s  (timeline total {TOTAL:.2f}s)')

  # ---------- Step 3: grade (vignette + grain + fades) ----------
  graded = os.path.join(WORK, 'graded.mp4')
  run(['-i', base,
       '-vf', f'vignette=angle=PI/4.3,noise=alls=6:allf=t+u,fade=t=in:st=0:d=0.5,fade=t=out:st={max(base_dur-1.25,0.5):.2f}:d=1.25,format=yuv420p',
       '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', graded], 'grade: vignette+grain+fades')

# ---------- Step 4: audio mix ----------
mix = os.path.join(WORK, 'mix.wav')
audio_inputs = []
filter_parts = []
idx = 0
# VO clips: map each unique VO file to the scene where it starts (S10 before S11 for vo_10)
vo_starts = {}
for sc in TIMELINE['scenes']:
    vo_starts.setdefault(sc['vo'], sc['vo_start'])
for name, path_start in vo_starts.items():
    audio_inputs += ['-i', os.path.join(ROOT, 'assets', 'audio', name)]
    delay_ms = int(round(path_start * 1000))
    filter_parts.append(f'[{idx}:a]aformat=channel_layouts=stereo,adelay={delay_ms}|{delay_ms},volume=1.0[vo{idx}]')
    idx += 1
vo_labels = ''.join(f'[vo{i}]' for i in range(len(vo_starts)))

# ambience (trim to actual duration)
amb = [
    ('amb_drone.wav', 0.50),
    ('amb_wind.wav', 0.30),
]
amb_labels = ''
for name, vol in amb:
    audio_inputs += ['-i', os.path.join(ROOT, 'assets', 'audio', name)]
    filter_parts.append(f'[{idx}:a]aformat=channel_layouts=stereo,atrim=0:{TOTAL:.2f},asetpts=PTS-STARTPTS,volume={vol}[amb{idx}]')
    amb_labels += f'[amb{idx}]'
    idx += 1

# sfx events (all timed from TIMELINE['sfx'] actual video time)
SFX_MAP = {'bell': ('sfx_bell.wav', 0.75), 'heartbeat': ('sfx_heartbeat.wav', 0.80),
           'stinger': ('sfx_stinger.wav', 0.90), 'rumble': ('sfx_rumble.wav', 0.62),
           'tap': ('sfx_tap.wav', 0.60), 'bell2': ('sfx_bell.wav', 0.55),
           'subdrop': ('sfx_subdrop.wav', 0.85), 'murmur': ('sfx_murmur.wav', 0.42),
           'murmur2': ('sfx_murmur.wav', 0.30)}
sfx_labels = ''
for name, t in TIMELINE['sfx']:
    if name not in SFX_MAP:
        continue
    fname, vol = SFX_MAP[name]
    audio_inputs += ['-i', os.path.join(ROOT, 'assets', 'audio', fname)]
    delay_ms = int(round(t * 1000))
    filter_parts.append(f'[{idx}:a]aformat=channel_layouts=stereo,adelay={delay_ms}|{delay_ms},volume={vol}[sfx{idx}]')
    sfx_labels += f'[sfx{idx}]'
    idx += 1

total_inputs = len(vo_starts) + len(amb) + len([s for s in TIMELINE['sfx'] if s[0] in SFX_MAP])
filter_parts.append(f'{vo_labels}{amb_labels}{sfx_labels}amix=inputs={total_inputs}:normalize=0:dropout_transition=0[premix]')
filter_parts.append(f'[premix]highpass=f=25,afade=t=out:st={max(TOTAL-1.5,0.5):.2f}:d=1.5,loudnorm=I=-14:TP=-1.5:LRA=11:dual_mono=false[mixout]')
run([*audio_inputs, '-filter_complex', ';'.join(filter_parts),
     '-map', '[mixout]', '-ar', '48000', '-c:a', 'pcm_s16le', mix], 'audio mix (VO + ambience + SFX, loudnorm -14 LUFS)')

# ---------- Step 5: final mux + caption burn ----------
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
