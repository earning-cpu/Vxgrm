#!/usr/bin/env python3
"""Crop generated stills to 9:16, apply uniform horror grade, save working copies."""
import os
from PIL import Image, ImageEnhance, ImageDraw, ImageFilter

SRC = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
DST = os.path.join(os.path.dirname(__file__), '..', 'assets', 'work')
os.makedirs(DST, exist_ok=True)

TW, TH = 1620, 2880  # 9:16 working resolution (1.5x of 1080x1920)

def grade(path_in, path_out):
    im = Image.open(path_in).convert('RGB')
    w, h = im.size
    target_ratio = TW / TH
    ratio = w / h
    if abs(ratio - target_ratio) > 0.001:
        if ratio > target_ratio:  # too wide -> crop width
            nw = int(h * target_ratio)
            x = (w - nw) // 2
            im = im.crop((x, 0, x + nw, h))
        else:  # too tall -> crop height
            nh = int(w / target_ratio)
            y = (h - nh) // 2
            im = im.crop((0, y, w, y + nh))
    im = im.resize((TW, TH), Image.LANCZOS)
    # horror grade: suppress color, deepen contrast, darken, slight cool cast
    im = ImageEnhance.Color(im).enhance(0.80)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Brightness(im).enhance(0.88)
    # cool blue wash (shadows) + faint warm center glow via radial overlay
    overlay = Image.new('RGB', im.size, (16, 22, 38))
    im = Image.blend(im, overlay, 0.16)
    glow = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(glow)
    cx, cy, r = TW // 2, int(TH * 0.42), int(TW * 0.75)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=46)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=400))
    warm = Image.new('RGB', im.size, (70, 48, 30))
    im = Image.composite(Image.blend(im, warm, 0.35), im, glow)
    im.save(path_out, quality=92)
    print('graded', os.path.basename(path_out))

for name in sorted(os.listdir(SRC)):
    if name.lower().endswith(('.jpg', '.jpeg', '.png')):
        grade(os.path.join(SRC, name), os.path.join(DST, name.rsplit('.', 1)[0] + '.jpg'))
