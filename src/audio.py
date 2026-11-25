"""Procedural score + sound design + voiceover assembly for the short."""
import os
import subprocess
import numpy as np
from scipy import signal as sg

import imageio_ffmpeg

SR = 48000
DUR = 64.6
N = int(SR * DUR)

RNG = np.random.default_rng(20261124)


# ============================================================ primitives
def t_axis(n):
    return np.arange(n, dtype=np.float64) / SR


def noise(n, seed=0):
    return np.random.default_rng(seed).standard_normal(n)


def env_ad(n, attack, decay, curve=2.0):
    a = np.clip(t_axis(n) / max(attack, 1e-4), 0, 1)
    d = np.exp(-np.clip(t_axis(n) - attack, 0, None) / max(decay, 1e-4)) ** curve
    return a * d


def env_adsr(n, a, d, s, r):
    t = t_axis(n)
    total = n / SR
    e = np.ones(n)
    e = np.where(t < a, t / max(a, 1e-5), e)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-5), e)
    e = np.where((t >= a + d) & (t < total - r), s, e)
    rel = np.clip((total - t) / max(r, 1e-5), 0, 1)
    e = np.where(t >= total - r, s * rel, e)
    return e


def lowpass(x, fc, order=2):
    fc = min(fc, SR * 0.45)
    b, a = sg.butter(order, fc / (SR / 2), btype="low")
    return sg.lfilter(b, a, x)


def highpass(x, fc, order=2):
    b, a = sg.butter(order, fc / (SR / 2), btype="high")
    return sg.lfilter(b, a, x)


def bandpass(x, f1, f2, order=2):
    b, a = sg.butter(order, [f1 / (SR / 2), min(f2, SR * 0.45) / (SR / 2)], btype="band")
    return sg.lfilter(b, a, x)


def saw_add(f, n, harmonics=12, detune=0.0):
    t = t_axis(n)
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        out += np.sin(2 * np.pi * f * k * (1 + detune) * t) / k
    return out


def stereo(mono, pan=0.0):
    """pan -1..1"""
    l = mono * np.sqrt(0.5 * (1 - pan))
    r = mono * np.sqrt(0.5 * (1 + pan))
    return np.stack([l, r], axis=1)


# ============================================================ instruments
def drone(dur, root=73.42, level=1.0, bright=0.0):
    n = int(dur * SR)
    t = t_axis(n)
    parts = []
    for mult, det, amp in [(1.0, -0.003, 0.55), (1.0, 0.003, 0.55), (1.5, 0.0, 0.30),
                           (2.0, -0.002, 0.18), (0.5, 0.0, 0.35)]:
        parts.append(saw_add(root * mult, n, 10, det) * amp)
    x = np.sum(parts, axis=0)
    x = lowpass(x, 320 + bright * 1400)
    # slow movement
    lfo = 0.72 + 0.28 * np.sin(2 * np.pi * 0.055 * t + 0.7) * np.sin(2 * np.pi * 0.021 * t)
    x = x * lfo
    # slow fade in/out
    x *= env_adsr(n, min(2.0, dur * 0.2), 1.0, 1.0, min(2.5, dur * 0.3))
    return x * level


def sub_hit(dur=1.4, f0=58, f1=32, level=1.0):
    n = int(dur * SR)
    t = t_axis(n)
    f = f0 * (f1 / f0) ** np.clip(t / (dur * 0.55), 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / (dur * 0.30))
    click = noise(n, 11) * np.exp(-t / 0.012) * 0.35
    click = lowpass(click, 2400)
    return (x + click) * level


def impact(level=1.0, dur=1.6):
    n = int(dur * SR)
    t = t_axis(n)
    body = sub_hit(dur, 110, 30, 1.0)
    burst = noise(n, 5) * np.exp(-t / 0.09)
    burst = bandpass(burst, 180, 3800)
    metal = np.zeros(n)
    for f, a, d in [(317, 0.30, 0.20), (587, 0.22, 0.14), (1013, 0.16, 0.10),
                    (1830, 0.10, 0.07)]:
        metal += np.sin(2 * np.pi * f * t) * a * np.exp(-t / d)
    x = body * 1.0 + burst * 0.55 + metal * 0.30
    return x * level


def whoosh(dur=0.55, up=True, level=1.0, seed=3):
    n = int(dur * SR)
    x = noise(n, seed)
    # time varying bandpass via short blocks
    out = np.zeros(n)
    blk = 256
    zi = None
    for i in range(0, n, blk):
        p = i / n
        c = (200 + 5200 * (p ** 1.8)) if up else (5200 - 5000 * (p ** 1.5))
        c = float(np.clip(c, 60, SR * 0.4))
        b, a = sg.butter(2, [max(40, c * 0.45) / (SR / 2), min(c * 2.1, SR * 0.44) / (SR / 2)],
                         btype="band")
        seg = x[i:i + blk]
        if len(seg) == 0:
            break
        y = sg.lfilter(b, a, seg)
        out[i:i + len(seg)] = y
    e = np.sin(np.pi * np.clip(t_axis(n) / dur, 0, 1)) ** 1.6
    return out * e * level


def riser(dur=2.2, level=1.0, seed=9):
    n = int(dur * SR)
    t = t_axis(n)
    x = noise(n, seed)
    out = np.zeros(n)
    blk = 256
    for i in range(0, n, blk):
        p = i / n
        c = 180 + 7000 * (p ** 2.0)
        b, a = sg.butter(2, [max(40, c * 0.5) / (SR / 2), min(c * 2.0, SR * 0.44) / (SR / 2)],
                         btype="band")
        seg = x[i:i + blk]
        out[i:i + len(seg)] = sg.lfilter(b, a, seg)
    f = 70 * (11 ** np.clip(t / dur, 0, 1))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.30
    e = (t / dur) ** 2.2
    return (out * 0.9 + tone) * e * level


def heartbeat(dur=1.0, level=1.0):
    n = int(dur * SR)
    t = t_axis(n)
    x = np.zeros(n)
    for off, amp in [(0.0, 1.0), (0.175, 0.62)]:
        m = int(0.30 * SR)
        tt = t_axis(m)
        th = np.sin(2 * np.pi * 52 * tt) * np.exp(-tt / 0.055)
        th += np.sin(2 * np.pi * 96 * tt) * np.exp(-tt / 0.030) * 0.4
        s = int(off * SR)
        e = min(n, s + m)
        x[s:e] += th[:e - s] * amp
    return x * level


def fire(dur, level=1.0, seed=17):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    # crackles
    for _ in range(int(dur * 55)):
        s = rng.integers(0, max(1, n - 2000))
        ln = rng.integers(80, 900)
        amp = rng.uniform(0.15, 1.0) ** 2
        e = np.exp(-np.arange(ln) / (ln * 0.28))
        x[s:s + ln] += rng.standard_normal(ln) * e * amp
    x = bandpass(x, 500, 7000)
    rumble = lowpass(noise(n, seed + 1), 140) * 2.4
    rumble *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t_axis(n))
    return (x * 0.42 + rumble * 0.5) * level


def wind(dur, level=1.0, seed=23):
    n = int(dur * SR)
    t = t_axis(n)
    x = bandpass(noise(n, seed), 180, 1100, 2)
    am = 0.45 + 0.55 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + 1.2)) * \
        (0.6 + 0.4 * np.sin(2 * np.pi * 0.037 * t))
    return x * am * level


def whispers(dur, level=1.0, seed=31):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = bandpass(noise(n, seed), 1100, 3600, 2)
    # syllable envelope
    env = np.zeros(n)
    i = 0
    while i < n:
        ln = int(rng.uniform(0.06, 0.22) * SR)
        gap = int(rng.uniform(0.02, 0.14) * SR)
        seg = env[i:i + ln]
        e = np.hanning(len(seg))
        env[i:i + ln] = np.maximum(seg, e * rng.uniform(0.3, 1.0))
        i += ln + gap
    return x * env * level


def glitch_sting(level=1.0, seed=41):
    n = int(0.22 * SR)
    t = t_axis(n)
    x = noise(n, seed)
    # bit crush
    x = np.round(x * 6) / 6
    x = bandpass(x, 400, 6000)
    gate = (np.sin(2 * np.pi * 47 * t) > 0).astype(float)
    return x * gate * np.exp(-t / 0.10) * level


def reverse_swell(dur=1.6, level=1.0, seed=47):
    x = impact(1.0, dur)
    return x[::-1] * level


def clock_tick(level=1.0):
    n = int(0.06 * SR)
    t = t_axis(n)
    x = noise(n, 51) * np.exp(-t / 0.004)
    x = bandpass(x, 1200, 6000)
    return x * level


def paper(level=1.0):
    n = int(0.5 * SR)
    t = t_axis(n)
    x = bandpass(noise(n, 53), 900, 5200)
    e = np.exp(-t / 0.16) * (0.5 + 0.5 * np.sin(2 * np.pi * 33 * t))
    return x * e * level


def metal_clash(level=1.0, seed=59):
    n = int(0.9 * SR)
    t = t_axis(n)
    x = np.zeros(n)
    for f, a, d in [(820, 0.5, 0.22), (1310, 0.4, 0.18), (1980, 0.3, 0.13),
                    (2740, 0.22, 0.09), (4100, 0.15, 0.06)]:
        x += np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) * a * np.exp(-t / d)
    x += bandpass(noise(n, seed), 1500, 8000) * np.exp(-t / 0.05) * 0.6
    return x * level


# ============================================================ assembly
def place(buf, sig, t, gain=1.0, pan=0.0):
    """Add mono (or stereo) sig into stereo buf at time t (seconds)."""
    s = int(t * SR)
    if s >= len(buf) or s < 0:
        return
    if sig.ndim == 1:
        sig = stereo(sig, pan)
    e = min(len(buf), s + sig.shape[0])
    buf[s:e] += sig[:e - s] * gain


def load_vo(name, tempo=1.18):
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    p = os.path.join("assets/vo", name + ".mp3")
    r = subprocess.run([exe, "-v", "error", "-i", p, "-filter:a",
                        f"atempo={tempo},highpass=f=70,acompressor=threshold=-18dB:ratio=3",
                        "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
    # trim leading/trailing silence
    th = 0.006
    idx = np.where(np.abs(a) > th)[0]
    if len(idx):
        a = a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.08 * SR)]
    return a


def build_audio(shots, out_wav, vo_start=None, tempo=1.18, stems=False):
    from . import timeline as TL
    vo_start = vo_start or TL.VO_START
    buf = np.zeros((N, 2), dtype=np.float64)

    # ---------------- voiceover
    vo_bus = np.zeros((N, 2), dtype=np.float64)
    vo_env = np.zeros(N)
    for name, t in sorted(vo_start.items(), key=lambda kv: kv[1]):
        a = load_vo(name, tempo)
        # normalise each line
        rms = np.sqrt(np.mean(a ** 2)) + 1e-9
        a = a * (0.115 / rms)
        a = np.clip(a, -0.98, 0.98)
        place(buf, a, t, 1.0, 0.0)
        place(vo_bus, a, t, 1.0, 0.0)
        s = int(t * SR)
        e = min(N, s + len(a))
        vo_env[s:e] = np.maximum(vo_env[s:e], np.abs(a))

    # smooth ducking envelope
    k = int(0.12 * SR)
    kernel = np.hanning(k * 2 + 1)
    kernel /= kernel.sum()
    duck = np.convolve(vo_env, kernel, mode="same")
    duck = np.clip(duck * 6.0, 0, 1)
    duck = 1.0 - 0.55 * duck

    # ---------------- music bed
    music = np.zeros((N, 2), dtype=np.float64)

    # A: hook drone
    place(music, drone(4.6, 73.42, 0.85, 0.0), 0.0)
    # B: setup
    place(music, drone(16.0, 73.42, 0.62, 0.25), 4.3)
    place(music, drone(7.0, 55.0, 0.55, 0.10), 13.0)
    # C: the order - thin, tense
    place(music, drone(2.6, 82.41, 0.40, 0.05), 19.2)
    # D: chase
    place(music, drone(14.4, 73.42, 0.72, 0.55), 21.6)
    # E: the cry
    place(music, drone(3.6, 61.74, 0.95, 0.15), 35.5)
    # F: aftermath
    place(music, drone(8.2, 73.42, 0.50, 0.0), 38.8)
    # G: fire
    place(music, drone(3.4, 49.0, 0.70, 0.7), 46.6)
    # H: legend
    place(music, drone(10.0, 73.42, 0.55, 0.10), 49.7)
    # I: scare
    place(music, drone(2.2, 46.25, 0.80, 0.2), 59.3)
    # J: CTA
    place(music, drone(3.2, 73.42, 0.55, 0.2), 61.3)

    music *= duck[:, None]
    music_gain = 0.30
    buf += music * music_gain

    # ---------------- sub hits & pulses
    for t in [0.0, 2.35, 4.30, 7.10, 10.20, 13.30, 16.30, 19.20, 21.60, 24.60,
              27.60, 31.10, 34.30, 35.60, 38.90, 42.40, 45.00, 46.70, 49.80,
              53.20, 56.60, 59.40, 61.40]:
        place(buf, sub_hit(1.2, 62, 30, 0.42), t, 1.0, 0.0)
    place(buf, sub_hit(2.4, 48, 24, 1.0), 35.60, 1.0)
    place(buf, sub_hit(2.0, 44, 22, 0.95), 59.40, 1.0)
    place(buf, sub_hit(2.4, 40, 20, 0.9), 61.40, 1.0)

    # ---------------- transition SFX driven by the shot list
    for s in shots:
        if s.trans == "whip":
            place(buf, whoosh(0.55, True, 0.55, seed=hash(s.plate or "") % 997), s.t0, 1.0, -0.2)
        elif s.trans == "glitch":
            place(buf, glitch_sting(0.40), s.t0, 1.0, 0.15)
        elif s.trans == "flash":
            place(buf, impact(0.62, 1.4), s.t0, 1.0, 0.0)
        elif s.trans == "dip":
            place(buf, sub_hit(1.6, 50, 26, 0.5), s.t0, 1.0, 0.0)

    # ---------------- chase heartbeat
    hb = heartbeat(1.0, 1.0)
    t = 24.6
    while t < 35.4:
        bpm = 62 + (t - 24.6) * 4.2
        place(buf, hb, t, 0.55, 0.0)
        t += 60.0 / bpm
    # heartbeat in the order section (slower, quieter)
    t = 19.4
    while t < 21.4:
        place(buf, hb, t, 0.34, 0.0)
        t += 1.25

    # ---------------- foley
    place(buf, paper(0.55), 13.45, 1.0, -0.15)
    place(buf, paper(0.45), 17.15, 1.0, -0.15)
    place(buf, metal_clash(0.45), 21.65, 1.0, 0.2)
    place(buf, metal_clash(0.30), 24.65, 1.0, -0.1)
    place(buf, clock_tick(0.22), 22.20, 1.0, 0.3)

    # ---------------- fire
    place(buf, fire(3.6, 0.85), 46.6, 1.0, 0.0)

    # ---------------- wind / atmosphere
    place(buf, wind(6.0, 0.30), 0.0, 1.0, -0.3)
    place(buf, wind(9.0, 0.26), 38.8, 1.0, 0.25)
    place(buf, wind(10.0, 0.30), 49.7, 1.0, -0.2)

    # ---------------- whispers in the legend section
    place(buf, whispers(9.5, 0.16, 71), 49.9, 1.0, -0.35)
    place(buf, whispers(8.0, 0.12, 73), 51.2, 1.0, 0.35)

    # ---------------- risers
    place(buf, riser(2.4, 0.55), 33.2, 1.0, 0.0)
    place(buf, riser(2.0, 0.62), 57.4, 1.0, 0.0)
    place(buf, reverse_swell(1.8, 0.55), 57.6, 1.0, 0.0)

    # ---------------- the scare
    place(buf, impact(1.0, 2.2), 59.40, 1.0, 0.0)
    place(buf, glitch_sting(0.5), 59.42, 1.0, 0.0)

    # ---------------- final hit
    place(buf, impact(0.55, 2.0), 61.40, 1.0, 0.0)

    # ---------------- master
    # gentle high-pass to remove DC / rumble
    for c in range(2):
        buf[:, c] = highpass(buf[:, c], 28, 2)

    # ---- look-ahead style limiter (raises average loudness, tames peaks)
    env = np.abs(buf).max(axis=1)
    k = int(0.004 * SR)
    env_s = np.convolve(env, np.ones(k) / k, mode="same")
    thr = 0.42
    gain = np.minimum(1.0, thr / np.maximum(env_s, 1e-6))
    k2 = int(0.045 * SR)
    gk = np.hanning(k2 * 2 + 1)
    gk /= gk.sum()
    gain = np.convolve(gain, gk, mode="same")
    buf = buf * gain[:, None]

    # ---- gentle saturation for glue
    buf = np.tanh(buf * 1.35) * 0.86

    # ---- stereo width (mid/side)
    mid = (buf[:, 0] + buf[:, 1]) * 0.5
    side = (buf[:, 0] - buf[:, 1]) * 0.5 * 1.55
    buf[:, 0] = mid + side
    buf[:, 1] = mid - side

    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.95

    if stems:
        import wave as _w
        def _wr(path, data):
            pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
            with _w.open(path, "wb") as fh:
                fh.setnchannels(2); fh.setsampwidth(2); fh.setframerate(SR)
                fh.writeframes(pcm.tobytes())
        _wr(out_wav.replace(".wav", "_music.wav"), music * music_gain)
        _wr(out_wav.replace(".wav", "_vo.wav"), vo_bus)

    # write wav (float32)
    import wave
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_wav, DUR
