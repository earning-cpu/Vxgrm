#!/usr/bin/env python3
"""Synthesize black-background FX overlay videos (composited with screen blend).
Produces: rain, embers, dust, fog — 1080x1920, 30fps, ~9s loops."""
import os, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
TMP = os.path.join(ROOT, 'assets', 'fx_tmp')
OUT = os.path.join(ROOT, 'assets', 'fx')
os.makedirs(TMP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
W, H, FPS = 1080, 1920, 30
FF = os.path.join(ROOT, '.venv', 'lib', 'python3.11', 'site-packages', 'imageio_ffmpeg', 'binaries', 'ffmpeg-linux-x86_64-v9.0.2')
rng = np.random.default_rng(1518)

def encode(name, frame_iter, n):
    d = os.path.join(TMP, name)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    for i, frame in enumerate(frame_iter):
        frame.save(os.path.join(d, f'{i:04d}.png'))
    out = os.path.join(OUT, f'{name}.mp4')
    subprocess.run([FF, '-hide_banner', '-y', '-framerate', '30', '-i', os.path.join(d, '%04d.png'),
                    '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-an', out],
                   check=True, capture_output=True)
    print('encoded', out)

def rain():
    n = 270
    N = 9 * FPS
    streaks = [dict(x=rng.uniform(-50, W + 50), y=rng.uniform(-H, H),
                    ln=rng.uniform(28, 95), sp=rng.uniform(17, 30), dx=rng.uniform(2.2, 4.2),
                    a=int(rng.uniform(80, 210)), w=rng.choice([1, 1, 1, 2])) for _ in range(n)]
    def frames():
        for i in range(N):
            im = Image.new('RGB', (W, H), (0, 0, 0))
            d = ImageDraw.Draw(im)
            for s in streaks:
                yy = (s['y'] + i * s['sp']) % (H + 220) - 110
                xx = s['x'] + i * s['dx']
                d.line([(xx, yy), (xx + s['dx'] * s['ln'] / s['sp'], yy + s['ln'])],
                       fill=(s['a'], s['a'], s['a']), width=s['w'])
            im = im.filter(ImageFilter.GaussianBlur(0.6))
            yield im
    return frames(), N

def embers():
    N = 9 * FPS
    P = 55
    def spawn():
        return dict(x=rng.uniform(0.15 * W, 0.85 * W), y=rng.uniform(H * 0.55, H * 1.05),
                    vy=rng.uniform(1.1, 2.9), ph=rng.uniform(0, 6.28), fr=rng.uniform(0.6, 1.4),
                    amp=rng.uniform(8, 34), r=rng.uniform(0.8, 2.6), a=rng.uniform(0.55, 1.0))
    parts = [spawn() for _ in range(P)]
    def frames():
        for i in range(N):
            im = Image.new('RGB', (W, H), (0, 0, 0))
            d = ImageDraw.Draw(im)
            for p in parts:
                p['y'] -= p['vy']
                xx = p['x'] + p['amp'] * math.sin(p['ph'] + i * 0.05 * p['fr'] * 30)
                if p['y'] < -20 or p['a'] <= 0:
                    parts[parts.index(p)] = spawn(); continue
                tw = 0.6 + 0.4 * math.sin(i * 0.35 + p['ph'] * 7)
                a = int(255 * p['a'] * tw)
                r = p['r'] * (0.8 + 0.4 * tw)
                col = (a, int(a * 0.62), int(a * 0.28))
                d.ellipse([xx - r, p['y'] - r, xx + r, p['y'] + r], fill=col)
            im = im.filter(ImageFilter.GaussianBlur(1.1))
            yield im
    return frames(), N

def dust():
    N = 9 * FPS
    P = 70
    parts = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), vx=rng.uniform(-0.65, 0.15),
                  vy=rng.uniform(0.12, 0.55), r=rng.uniform(0.7, 1.9), a=rng.uniform(0.25, 0.75),
                  ph=rng.uniform(0, 6.28)) for _ in range(P)]
    def frames():
        for i in range(N):
            im = Image.new('RGB', (W, H), (0, 0, 0))
            d = ImageDraw.Draw(im)
            for p in parts:
                p['x'] += p['vx']; p['y'] += p['vy']
                if p['y'] > H + 4: p['y'] = -4; p['x'] = rng.uniform(0, W)
                if p['x'] < -4: p['x'] = W + 4
                a = int(255 * p['a'] * (0.65 + 0.35 * math.sin(i * 0.16 + p['ph'])))
                d.ellipse([p['x'] - p['r'], p['y'] - p['r'], p['x'] + p['r'], p['y'] + p['r']],
                          fill=(a, a, a))
            im = im.filter(ImageFilter.GaussianBlur(0.8))
            yield im
    return frames(), N

def fog():
    N = 10 * FPS
    # small canvas upscaled -> naturally soft fog blobs
    sw, sh = 180, 320
    blobs = [dict(x=rng.uniform(0, sw), y=rng.uniform(0.15 * sh, 0.95 * sh),
                  r=rng.uniform(28, 68), vx=rng.uniform(0.16, 0.42) * rng.choice([1, 1, 1, -1]),
                  a=rng.uniform(26, 62)) for _ in range(16)]
    def frames():
        for i in range(N):
            small = Image.new('L', (sw, sh), 0)
            d = ImageDraw.Draw(small)
            for b in blobs:
                x = (b['x'] + i * b['vx']) % (sw + 2 * b['r']) - b['r']
                d.ellipse([x - b['r'], b['y'] - b['r'] * 0.62, x + b['r'], b['y'] + b['r'] * 0.62],
                          fill=int(b['a']))
            im = small.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(24))
            yield Image.merge('RGB', (im, im, im))
    return frames(), N

if __name__ == '__main__':
    for name, fn in [('rain', rain), ('embers', embers), ('dust', dust), ('fog', fog)]:
        frames_iter, n = fn()
        encode(name, frames_iter, n)
    print('overlay synthesis complete.')
