"""Derived plates: ghost composite, doc-card bg, end-card bg (all from the 8 generated stills)."""
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np, os
os.makedirs("work", exist_ok=True)

# 1) ghost of the princess — cold, blood-drained, dim but readable
im = Image.open("assets/img/s05_princess.png").convert("RGB")
a = np.array(im).astype(np.float32) / 255.0
a[..., 0] *= 0.58; a[..., 2] *= 1.20
Image.fromarray((np.clip(a * 0.95, 0, 1) * 255).astype(np.uint8)).save("work/s05_ghost.png")

# 2) doc-card background — soft dark ruin, must not fight the paper card
d = Image.open("assets/img/s02_fort_wide.png").convert("RGB").resize((1620, 2880), Image.LANCZOS)
d = d.filter(ImageFilter.GaussianBlur(22))
d = ImageEnhance.Brightness(d).enhance(0.50); d = ImageEnhance.Color(d).enhance(0.55)
b = np.array(d).astype(np.float32); b[..., 2] *= 1.10; b[..., 0] *= 0.92
Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).save("work/bg_doccard.png")

# 3) end-card background — moody but visible, with a real vignette + grain
e = Image.open("assets/img/s01_hook.png").convert("RGB").resize((1620, 2880), Image.LANCZOS)
e = e.filter(ImageFilter.GaussianBlur(9))
e = ImageEnhance.Brightness(e).enhance(0.78); e = ImageEnhance.Color(e).enhance(0.72)
e = ImageEnhance.Contrast(e).enhance(1.18)
a = np.array(e).astype(np.float32)
h, w, _ = a.shape
yy, xx = np.mgrid[0:h, 0:w]
r = np.sqrt(((xx - w/2)/(w/1.55))**2 + ((yy - h/2)/(h/1.6))**2)
a *= np.clip(1 - 0.75*np.clip(r, 0, 1)**1.5, 0, 1)[..., None]
a += np.random.default_rng(5).normal(0, 3.2, a.shape[:2])[..., None]
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save("work/bg_end.png")
print("derived plates rebuilt")

# ---------------------------------------------------------------- extra compositions
# New looks from the same art (keeps the film visually varied without new assets).
def crop_plate(src, box, out, mirror=False, bright=1.0, sat=1.0):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    c = im.crop((int(w*box[0]), int(h*box[1]), int(w*box[2]), int(h*box[3])))
    if mirror: c = c.transpose(Image.FLIP_LEFT_RIGHT)
    c = ImageEnhance.Brightness(c).enhance(bright)
    c = ImageEnhance.Color(c).enhance(sat)
    c = c.resize((941, 1672), Image.LANCZOS)
    c.save(out)

crop_plate("assets/img/s01_hook.png",     (0.00, 0.42, 1.00, 1.00), "work/s01_gate.png",  bright=1.15, sat=0.9)   # gateway + road, no moon
crop_plate("assets/img/s03_sadhu.png",    (0.12, 0.05, 0.88, 0.62), "work/s03_sadhu_up.png")                          # face / beads
crop_plate("assets/img/s05_princess.png", (0.00, 0.05, 0.72, 0.95), "work/s05_corridor.png", bright=1.35, sat=0.8)     # corridor + shadow figure
crop_plate("assets/img/s04_shadow.png",   (0.45, 0.10, 1.00, 0.95), "work/s04_shrine.png",   mirror=True, bright=1.05)  # shrine side
crop_plate("assets/img/s07_archive.png",  (0.30, 0.20, 1.00, 1.00), "work/s07_ruins.png",    mirror=True, bright=1.05)  # ruins close-up
print("extra compositions built")
