#!/usr/bin/env python3
"""Synthesize all SFX/ambience for the Dancing Plague Short (numpy, no licensing issues)."""
import numpy as np
import wave
import os

SR = 48000
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'audio')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(1518)

def stereo(sig):
    return np.stack([sig, sig], axis=1)

def lowpass(sig, alpha):
    """Simple one-pole lowpass."""
    y = np.empty_like(sig)
    acc = 0.0
    for i, x in enumerate(sig):
        acc += alpha * (x - acc)
        y[i] = acc
    return y

def butter_lp_fast(sig, cutoff, order=2):
    """Cahnerita via repeated one-pole (cheap, stable)."""
    alpha = cutoff / (cutoff + SR / (2 * np.pi))
    y = sig.copy()
    for _ in range(order):
        y = lowpass(y, alpha)
    return y

def norm(sig, peak=0.89):
    m = np.max(np.abs(sig))
    return sig * (peak / m) if m > 0 else sig

def save(name, stereo_sig):
    path = os.path.join(OUT, name)
    data = np.clip(stereo_sig, -1, 1)
    pcm = (data * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    dur = len(data) / SR
    print(f'wrote {path}  ({dur:.2f}s)')

def t_env(n, attack_s=0.01, release_s=0.3):
    env = np.ones(n)
    a = int(attack_s * SR); r = int(release_s * SR)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if r > 0:
        env[-r:] *= np.linspace(1, 0, r)
    return env

def exp_decay(n, tau_s):
    return np.exp(-np.arange(n) / (tau_s * SR))

# ---------- 1. DRONE (full-duration sub bed, 55Hz beating pair) ----------
T_TOTAL = 80.0
n = int(T_TOTAL * SR)
t = np.arange(n) / SR
drone = (0.55 * np.sin(2 * np.pi * 55.0 * t)
         + 0.30 * np.sin(2 * np.pi * 55.7 * t)
         + 0.18 * np.sin(2 * np.pi * 110.0 * t)
         + 0.10 * np.sin(2 * np.pi * 164.8 * t))
# slow beating LFO (0.07 Hz) + faint instability wobble
drone *= (0.72 + 0.28 * np.sin(2 * np.pi * 0.07 * t + 0.6))
drone += 0.02 * rng.standard_normal(n)  # air
drone = butter_lp_fast(drone, 400, 2)
save('amb_drone.wav', norm(stereo(drone), 0.62))

# ---------- 2. WIND (brown noise, slow swell LFO) ----------
white = rng.standard_normal(n)
brown = np.cumsum(white)
brown = brown / np.max(np.abs(brown))
wind = butter_lp_fast(brown, 260, 3)
wind *= (0.55 + 0.45 * np.sin(2 * np.pi * t / 8.0 + 1.2))
save('amb_wind.wav', norm(stereo(wind), 0.42))

# ---------- 3. BELL (distant church bell, partials 0.5/1/2.02/2.74/5.4) ----------
dur = 9.0; nb = int(dur * SR); tb = np.arange(nb) / SR
partials = [(0.5, 0.5, 6.0), (1.0, 1.0, 5.0), (2.02, 0.42, 3.2), (2.74, 0.28, 2.1), (5.4, 0.09, 1.2)]
bell = np.zeros(nb)
for ratio, amp, tau in partials:
    bell += amp * np.sin(2 * np.pi * 98.0 * ratio * tb) * exp_decay(nb, tau)
bell *= t_env(nb, 0.008, 0.6)
bell = butter_lp_fast(bell, 1200, 2)
save('sfx_bell.wav', norm(stereo(bell), 0.72))

# ---------- 4. HEARTBEAT (lub-dub @ 72bpm, ~14s) ----------
dur = 15.0; hb = np.zeros(int(dur * SR))
period = 60.0 / 72.0
def thump(sig, at, amp=1.0):
    start = int(at * SR)
    length = int(0.34 * SR)
    if start + length > len(sig):
        length = len(sig) - start
    th_t = np.arange(length) / SR
    th = np.sin(2 * np.pi * 52 * th_t) * exp_decay(length, 0.055)
    th += 0.5 * np.sin(2 * np.pi * 39 * th_t) * exp_decay(length, 0.08)
    sig[start:start + length] += amp * th
at = 0.0
while at < dur - 0.8:
    thump(hb, at, 1.0)
    thump(hb, at + 0.32, 0.72)
    at += period
hb = butter_lp_fast(hb, 160, 2)
save('sfx_heartbeat.wav', norm(stereo(hb), 0.78))

# ---------- 5. RUMBLE (low crowd/storm rumble, 10s) ----------
dur = 10.0; nr = int(dur * SR)
rum = butter_lp_fast(rng.standard_normal(nr), 90, 3)
rum *= t_env(nr, 1.2, 2.0)
rum += 0.35 * np.sin(2 * np.pi * 34 * np.arange(nr) / SR) * t_env(nr, 1.0, 2.2)
save('sfx_rumble.wav', norm(stereo(rum), 0.66))

# ---------- 6. MURMUR (uneasy crowd wash, 26s) ----------
dur = 26.0; nm = int(dur * SR); tm = np.arange(nm) / SR
mur = butter_lp_fast(rng.standard_normal(nm), 520, 2)
mur *= (0.5 + 0.5 * np.sin(2 * np.pi * tm / 3.1 + 0.4)) * (0.6 + 0.4 * np.sin(2 * np.pi * tm / 7.7))
mur = butter_lp_fast(mur, 700, 1)
mur *= t_env(nm, 1.5, 2.5)
save('sfx_murmur.wav', norm(stereo(mur), 0.40))

# ---------- 7. STINGER (dissonant dread hit, 2.6s) ----------
dur = 2.6; ns = int(dur * SR); ts = np.arange(ns) / SR
sting = np.zeros(ns)
for f0, det in [(659.3, 0), (698.5, 4), (830.6, -3), (110.9, 0)]:
    sting += np.sin(2 * np.pi * (f0 + det) * ts) * exp_decay(ns, 0.85 if f0 > 200 else 1.6)
sting += 0.6 * np.sin(2 * np.pi * 55 * ts) * exp_decay(ns, 1.9)
sting *= t_env(ns, 0.006, 0.4)
sting = butter_lp_fast(sting, 2400, 1)
save('sfx_stinger.wav', norm(stereo(sting), 0.80))

# ---------- 8. SUB DROP (final 40→26Hz sweep, 5s) ----------
dur = 5.0; nd = int(dur * SR); td = np.arange(nd) / SR
freq = 40.0 - 14.0 * (td / dur)
phase = 2 * np.pi * np.cumsum(freq) / SR
sub = np.sin(phase) * exp_decay(nd, 2.4)
sub *= t_env(nd, 0.01, 0.5)
save('sfx_subdrop.wav', norm(stereo(sub), 0.85))

# ---------- 9. RED SHOE TAP (single hard heel tap under "stopped", 0.8s) ----------
dur = 0.8; nt = int(dur * SR); tt = np.arange(nt) / SR
tap = np.sin(2 * np.pi * 180 * tt) * exp_decay(nt, 0.045) + 0.4 * rng.standard_normal(nt) * exp_decay(nt, 0.02)
tap = butter_lp_fast(tap, 1500, 1)
save('sfx_tap.wav', norm(stereo(tap), 0.70))

print('SFX synthesis complete.')
