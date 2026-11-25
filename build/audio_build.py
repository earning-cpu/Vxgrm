"""
Bhangarh Shorts — audio build.
Produces:
  work/timeline.json   beat timings used by the video build
  work/mix_norm.wav    final -14 LUFS stereo mix
Music/SFX are synthesized from scratch (no stock audio, fully original).
"""
import json, os, re, subprocess, wave
import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
TEMPO = 1.12          # viral pace-up of the narration (pitch preserved)
GAP = 0.22            # breathing room between beats
TAIL = 1.60           # end card hold

os.makedirs("work", exist_ok=True)

# ---------------------------------------------------------------- VO decode
def ff_dur(path):
    o = subprocess.run([FF, "-hide_banner", "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", o)
    return float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3))

def load_wav(path):
    with wave.open(path, "rb") as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == SR
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return data

BEATS = ["b01","b02","b03","b04","b05","b06","b07","b08","b09","b10"]

# ---------------------------------------------------------------- VO prep (idempotent)
# Trim leading/trailing silence, de-noise and gently compress the raw TTS takes.
if not os.path.exists("work/vo/vo_b01.wav"):
    os.makedirs("work/vo", exist_ok=True)
    af = ("silenceremove=start_periods=1:start_duration=0:start_threshold=-45dB:detection=peak,"
          "areverse,silenceremove=start_periods=1:start_duration=0:start_threshold=-45dB:detection=peak,areverse,"
          "highpass=f=85,lowpass=f=15000,acompressor=threshold=-18dB:ratio=3:attack=8:release=180:makeup=2,"
          "loudnorm=I=-16:TP=-1.5:LRA=9")
    for b in BEATS:
        src = f"assets/audio/vo_{b}.mp3"
        if not os.path.exists(src):
            raise SystemExit(f"missing narration take: {src}")
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
                        "-af", af, "-ar", "48000", "-ac", "1", f"work/vo/vo_{b}.wav"], check=True)
    print("VO prepped from assets/audio")


vo = {}
for b in BEATS:
    src = f"work/vo/vo_{b}.wav"
    dst = f"work/vo/vo_{b}_fast.wav"
    # atempo keeps pitch, slight brightening for phone-speaker clarity
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
                    "-af", f"atempo={TEMPO},equalizer=f=3200:t=q:w=1.0:g=2.2,"
                           "acompressor=threshold=-16dB:ratio=2.5:attack=6:release=120",
                    "-ar", str(SR), "-ac", "1", dst], check=True)
    vo[b] = load_wav(dst)

# ---------------------------------------------------------------- timeline
t = 0.0
timeline = []
for i, b in enumerate(BEATS):
    d = len(vo[b]) / SR
    seg = d + GAP + (TAIL if i == len(BEATS) - 1 else 0.0)
    timeline.append({"id": b, "start": round(t, 3), "vo_dur": round(d, 3),
                     "dur": round(seg, 3), "end": round(t + seg, 3)})
    t += seg
TOTAL = round(t, 3)
json.dump({"total": TOTAL, "beats": timeline}, open("work/timeline.json", "w"), indent=1)
print("TIMELINE total", TOTAL)
for s in timeline:
    print(f'  {s["id"]}  {s["start"]:6.2f} -> {s["end"]:6.2f}  ({s["dur"]:.2f}s)')

N = int(TOTAL * SR) + SR // 2
def tt(n): return np.arange(n) / SR

# ---------------------------------------------------------------- helpers
def env_adsr(n, a, d, s, r):
    a, d, r = int(a*SR), int(d*SR), int(r*SR)
    s_n = max(n - a - d - r, 0)
    return np.concatenate([np.linspace(0, 1, max(a, 1)),
                           np.linspace(1, s, max(d, 1)),
                           np.full(s_n, s),
                           np.linspace(s, 0, max(r, 1))])[:n]

def smooth(x, ms=12):
    k = max(int(SR * ms / 1000), 1)
    return np.convolve(x, np.ones(k) / k, mode="same")

def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    n = min(len(sig), len(buf) - i)
    buf[i:i+n] += sig[:n] * gain

def reverb(x, decay=2.4, mix=0.35, seed=7):
    rng = np.random.default_rng(seed)
    L = int(decay * SR)
    ir = rng.standard_normal(L) * np.exp(-np.linspace(0, 6, L))
    ir = smooth(ir, 3)
    ir /= np.sqrt((ir**2).sum())
    n = len(x) + L
    nfft = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return (1 - mix) * x + mix * y * 3.0

def lowpass(x, hz):
    a = np.exp(-2 * np.pi * hz / SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y

def bandpass(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)

def saw(f, n, detune=0.0, phase=0.0):
    t = tt(n)
    out = np.zeros(n)
    for h in range(1, 14):
        out += np.sin(2*np.pi*(f*(1+detune))*h*t*1.0 + phase*h) / (h**1.25)
    return out

# ---------------------------------------------------------------- music bed
music = np.zeros(N)
rng = np.random.default_rng(11)

# sub drone (D1/D2/A2) + slow beating
drone = (0.55 * saw(36.71, N) + 0.30 * saw(55.0, N, detune=0.0015)
         + 0.22 * saw(73.42, N, detune=-0.0012) + 0.10 * saw(110.0, N, detune=0.002))
lfo = 0.65 + 0.35 * np.sin(2*np.pi*0.045*tt(N))
music += lowpass(drone, 320) * lfo * 0.55

# dissonant tension pad, swells over the whole piece
pad = (saw(146.83, N, 0.001) * 0.30 + saw(174.61, N, -0.001) * 0.26
       + saw(220.0, N, 0.0016) * 0.22 + saw(155.56, N, 0.0008) * 0.14)  # Eb rub
swell = np.clip(tt(N) / TOTAL, 0, 1) ** 0.8
music += lowpass(pad, 900) * (0.06 + 0.20 * swell) * 0.35

# heartbeat pulse — enters low, gets urgent
beats_per_min = np.linspace(58, 92, N)
phase = np.cumsum(beats_per_min / 60.0 / SR)
pulse = np.zeros(N)
hub_positions = np.where(np.diff(np.floor(phase)) > 0)[0]
for p in hub_positions:
    for off, g in ((0.0, 1.0), (0.235, 0.55)):
        i = p + int(off * SR)
        if i >= N: continue
        n = min(int(0.22 * SR), N - i)
        e = np.exp(-np.linspace(0, 9, n))
        f = 62 * np.exp(-np.linspace(0, 1.6, n)) + 34
        pulse[i:i+n] += np.sin(2*np.pi*np.cumsum(f)/SR) * e * g
hb_gain = np.interp(tt(N), [0, 8, 26, 45, TOTAL], [0.0, 0.35, 0.55, 0.85, 1.0])
music += pulse * 0.20 * hb_gain

# ---------------------------------------------------------------- SFX
sfx = np.zeros(N)

def whoosh(dur=0.55, f0=300, f1=2600, seed=1):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    nz = r.standard_normal(n)
    out = np.zeros(n); acc = 0.0
    for i in range(n):
        fc = f0 + (f1 - f0) * (i / n) ** 2
        a = np.exp(-2*np.pi*fc/SR)
        acc = (1-a)*nz[i] + a*acc
        out[i] = acc
    e = np.sin(np.linspace(0, np.pi, n)) ** 1.4
    return out * e * 3.0

def boom(dur=1.1, f0=70, f1=28):
    n = int(dur * SR)
    f = f0 * np.exp(-np.linspace(0, 2.2, n)) + f1
    e = np.exp(-np.linspace(0, 5.0, n))
    r = np.random.default_rng(3)
    nz = bandpass(r.standard_normal(n), 60, 900) * np.exp(-np.linspace(0, 22, n))
    return (np.sin(2*np.pi*np.cumsum(f)/SR) * e + nz * 0.7)

def riser(dur=1.6):
    r = np.random.default_rng(5)
    n = int(dur * SR)
    nz = r.standard_normal(n)
    out = np.zeros(n); acc = 0.0
    for i in range(n):
        fc = 300 * (10 ** (3.0 * i / n))
        a = np.exp(-2*np.pi*min(fc, 15000)/SR)
        acc = (1-a)*nz[i] + a*acc
        out[i] = acc
    out *= np.linspace(0.05, 1.0, n) ** 2.2
    tone = np.sin(2*np.pi*np.cumsum(np.linspace(110, 700, n))/SR) * 0.25
    return out * 2.5 + tone * out.max()

def bell(f=880, dur=2.4):
    n = int(dur * SR)
    t = tt(n)
    s = (np.sin(2*np.pi*f*t) + 0.45*np.sin(2*np.pi*f*2.01*t)
         + 0.25*np.sin(2*np.pi*f*3.02*t)) * np.exp(-np.linspace(0, 5.5, n))
    return s

S = {s["id"]: s for s in timeline}
# stable per-beat seeds (hash() is salted per process -> non-reproducible renders)
SUM1 = {b: 100 + i for i, b in enumerate(BEATS)}
# beats that get an impact + whoosh;  keep it rhythmic
for b in ["b02", "b04", "b05", "b06", "b07", "b09", "b10"]:
    st = S[b]["start"]
    place(sfx, whoosh(0.5, 320, 2900, seed=SUM1[str(b)]), st - 0.30, 0.34)
    if b in ("b04", "b06", "b09", "b10"):
        place(sfx, boom(), st, 0.55)
        place(sfx, riser(1.25), st - 1.25, 0.30)

# opening sting
place(sfx, boom(1.4, 80, 30), 0.0, 0.75)
place(sfx, riser(1.4), 0.0, 0.22)

# bells / eerie pings
for at, f, g in [(S["b02"]["start"] + 1.2, 1046, .12), (S["b05"]["start"] + 2.0, 880, .10),
                 (S["b07"]["start"] + 0.6, 740, .12), (S["b09"]["start"] + 0.8, 1320, .10)]:
    place(sfx, bell(f), at, g)

# bazaar murmur under b09 — distant voices, reverb soaked
n = int(S["b09"]["dur"] * SR)
r = np.random.default_rng(21)
murmur = bandpass(r.standard_normal(n), 180, 1600)
am = 0.55 + 0.45*np.sin(2*np.pi*3.3*tt(n)) * np.sin(2*np.pi*0.7*tt(n))
murmur = reverb(murmur * am, 2.8, 0.6, seed=4) * 0.055
place(sfx, murmur, S["b09"]["start"], 1.0)

# hard silence-drop right on the curse beat (retention trick)
silen = np.ones(N)
c0 = S["b06"]["start"]
silen[int(c0*SR):int((c0+0.55)*SR)] = 0.0
silen = smooth(silen, 25)

# ---------------------------------------------------------------- whisper
# (voiced by the second voice, processed dark + wide)
wpath = "work/vo/whisper.wav"
if os.path.exists(wpath):
    w = load_wav(wpath)
    wn = int(len(w) / 0.86)
    w = np.interp(np.linspace(0, len(w)-1, wn), np.arange(len(w)), w)
    w = reverb(w, 3.2, 0.65, seed=9) * 0.55
    place(sfx, w, S["b05"]["start"] + 1.4, 0.9)
    place(sfx, w[: int(len(w)*0.45)], S["b09"]["start"] + 1.1, 0.55)

# ---------------------------------------------------------------- mix
vo_track = np.zeros(N)
for b in BEATS:
    place(vo_track, vo[b], S[b]["start"], 1.0)

vo_env = smooth(np.abs(vo_track), 90)
vo_env = np.clip(vo_env / (vo_env.max() + 1e-9), 0, 1)
duck = 1.0 - 0.62 * vo_env            # music ducks under narration

music = reverb(music, 3.0, 0.32, seed=2) * 0.42
sfx = sfx * 0.85

# VO stays dead centre; music and SFX are decorrelated L/R for width.
# (the earlier draft summed the bed twice, then overwrote it - one clean pass now)
mL = reverb(music, 0.7, 0.3, seed=31) * duck * silen
mR = reverb(music, 0.7, 0.3, seed=32) * duck * silen
L = vo_track + mL * 0.42 + sfx * silen * 0.85
R = vo_track + mR * 0.42 + sfx * silen * 0.85

mix = np.stack([L, R], axis=1)[:int(TOTAL*SR)]
mix = np.tanh(mix * 1.05)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.89

with wave.open("work/mix_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", "work/mix_raw.wav",
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), "-ac", "2",
                "work/mix_norm.wav"], check=True)
print("MIX OK", round(ff_dur("work/mix_norm.wav"), 3), "s")
