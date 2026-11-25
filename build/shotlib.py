"""
Bhangarh Shorts — video build.
1) renders every shot with Ken Burns motion + cinematic grade + grain
2) hard-cut concat (viral pacing)
3) builds gradient legibility overlay + ASS overlay/subtitles
4) composes final 1080x1920 30fps deliverable with the -14 LUFS mix
"""
"""Shot library: plan, grading, camera paths, exposure model, filter-chain builder."""
import json, os, subprocess, math, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "build"))
import numpy as np
from PIL import Image
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
TL = json.load(open("work/timeline.json"))
SHOT_DIR = "work/shots"
os.makedirs(SHOT_DIR, exist_ok=True)
os.makedirs("out", exist_ok=True)

IMG = {
    "s01_hook":     "assets/img/s01_hook.png",
    "s02_fort_wide":"assets/img/s02_fort_wide.png",
    "s03_sadhu":    "assets/img/s03_sadhu.png",
    "s04_shadow":   "assets/img/s04_shadow.png",
    "s05_princess": "assets/img/s05_princess.png",
    "s07_archive":  "assets/img/s07_archive.png",
    "s08_sign":     "assets/img/s08_sign.png",
    "s09_leopard":  "assets/img/s09_leopard.png",
    "bg_doccard":   "work/bg_doccard.png",
    "bg_end":       "work/bg_end.png",
    "s05_ghost":    "work/s05_ghost.png",
    "s01_gate":     "work/s01_gate.png",
    "s03_sadhu_up": "work/s03_sadhu_up.png",
    "s05_corridor": "work/s05_corridor.png",
    "s04_shrine":   "work/s04_shrine.png",
    "s07_ruins":    "work/s07_ruins.png",
    "s06_curse":    "assets/img/s06_curse.png",
    "s10_bazaar":   "assets/img/s10_bazaar.png",
    "s11_victim":   "assets/img/s11_victim.png",
}


# --------------------------------------------------------------- shot plan
# (image, weight, camera, grade, flags)
PLAN = {
 "b01": [("s01_hook",      0.30, "punch",  "night", ["flash", "shake"]),
         ("s01_gate",      0.24, "zin",    "night", ["glitch", "mirror"]),
         ("s07_ruins",     0.46, "zin",    "cold",  ["shake"])],
 "b02": [("s02_fort_wide", 0.34, "panL",   "cold",  ["flash"]),
         ("s07_ruins",     0.31, "zout",   "cold",  ["grain2"]),
         ("s01_hook",      0.35, "tiltUp", "night", ["shake"])],
 "b03": [("s03_sadhu",     0.36, "zin",    "night", ["flash", "shake"]),
         ("s03_sadhu_up",  0.30, "panL",   "warm",  ["grain2"]),
         ("s04_shrine",    0.34, "drift",  "dusk",  ["pulse"])],
 "b04": [("s04_shadow",    0.34, "zin",    "dusk",  ["flash", "shake"]),
         ("s04_shrine",    0.30, "tiltUp", "warm",  ["glitch", "mirror"]),
         ("s07_archive",   0.36, "zout",   "cold",  ["invert"])],
 "b05": [("s05_princess",  0.34, "zin",    "night", ["flash"]),
         ("s05_corridor",  0.33, "panL",   "warm",  ["shake", "grain2"]),
         ("s05_ghost",     0.33, "drift",  "night", ["glitch"])],
 "b06": [("s05_ghost",     0.34, "punch",  "night", ["flash", "shake"]),
         ("s05_corridor",  0.30, "zin",    "night", ["ghost", "glitch"]),
         ("s02_fort_wide", 0.36, "zout",   "cold",  ["pulse"])],
 "b07": [("s07_archive",   0.33, "zout",   "cold",  ["flash"]),
         ("s02_fort_wide", 0.31, "panL",   "cold",  ["grain2", "mirror"]),
         ("s07_ruins",     0.36, "tiltUp", "warm",  ["shake"])],
 "b08": [("s08_sign",      0.32, "zin",    "cold",  ["flash", "shake"]),
         ("bg_doccard",    0.36, "drift",  "cold",  ["pulse"]),
         ("s09_leopard",   0.32, "punch",  "night", ["invert"])],
 "b09": [("s10_bazaar",    0.42, "zin",    "night", ["shake", "grain2"]),
         ("s05_princess",  0.26, "nin",    "night", ["ghost"]),
         ("s10_bazaar",    0.32, "panR",   "night", ["ghost", "glitch"])],
 "b10": [("bg_end",        0.30, "drift",  "night", ["flash"]),
         ("s11_victim",    0.32, "zout",   "night", ["grain2"]),
         ("s09_leopard",   0.38, "zin",    "night", ["shake", "pulse"])],
}

GRADE = {
 "night": "eq=contrast=1.13:saturation=0.74:brightness=0.012:gamma=1.08,"
          "colorbalance=bs=0.16:bm=0.05:bh=0.10:rh=-0.02",
 "dusk":  "eq=contrast=1.12:saturation=0.88:brightness=0.006:gamma=1.05,"
          "colorbalance=rh=0.14:gh=0.02:bh=0.10:bs=0.06",
 "cold":  "eq=contrast=1.10:saturation=0.38:brightness=0.014:gamma=1.07,"
          "colorbalance=bs=0.18:bm=0.04:bh=0.06",
 "warm":  "eq=contrast=1.10:saturation=1.00:brightness=0.006:gamma=1.06,"
          "colorbalance=rh=0.11:gh=0.03:bs=0.05",
}

TARGET = {"b01":44,"b02":52,"b03":50,"b04":54,"b05":40,"b06":40,
          "b07":52,"b08":50,"b09":38,"b10":36}
_src_luma = {}
def src_luma(path):
    """robust central-region luma (global mean lies about big black borders)"""
    if path not in _src_luma:
        from PIL import Image
        import numpy as np
        im = Image.open(path).convert("L")
        w, h = im.size
        c = im.crop((int(w*0.12), int(h*0.10), int(w*0.88), int(h*0.90)))
        a = np.array(c).astype(np.float32)
        _src_luma[path] = float(a.mean())
    return _src_luma[path]

def crop_luma(img_path, cam, n):
    """luma of the region the virtual camera will actually show (start of shot)"""
    from PIL import Image
    import numpy as np
    key = (img_path, cam)
    if key in _src_luma: return _src_luma[key]
    im = Image.open(img_path).convert("L")
    W0, H0 = im.size
    z = {"zin":1.03,"zout":1.30,"punch":1.40,"panL":1.24,"panR":1.24,
         "tiltUp":1.24,"drift":1.14,"nin":1.50}.get(cam, 1.2)
    cw, ch = W0/z, H0/z
    if cam in ("panL","panR"):   cx, cy = (0.0 if cam=="panL" else 1.0), 0.5
    elif cam == "tiltUp":        cx, cy = 0.5, 0.0
    elif cam == "drift":         cx, cy = 0.30, 0.5
    elif cam == "nin":           cx, cy = 0.52, 0.30
    else:                        cx, cy = 0.5, 0.5
    x0 = int((W0-cw)*cx); y0 = int((H0-ch)*cy)
    a = np.array(im.crop((x0, y0, x0+int(cw), y0+int(ch)))).astype(np.float32)
    _src_luma[key] = float(a.mean())
    return _src_luma[key]

def expo_gamma(img_path, beat, grade, cam, idx=None):
    md = crop_luma(img_path, cam, 0)
    mt = TARGET[beat]
    # delivered luma is lowered by vignette + gradient overlay; compensate targets
    mt *= 1.28
    if "s05" in img_path: mt += 4
    if "ghost" in img_path: mt += 6
    if "bg_end" in img_path: mt += 2
    if md <= 2: return 1.0
    g = math.log(min(mt,235)/255.0) / math.log(max(md,1.0)/255.0)
    g = min(max(g, 0.62), 1.25)
    # data-driven correction learned from the previous QA pass
    calib = EXPOSURE_CAL.get(str(idx), 1.0)
    return round(min(max(g * calib, 0.30), 1.75), 3)

def cam_expr(cam, n):
    cx = "iw/2-(iw/zoom/2)"
    cy = "ih/2-(ih/zoom/2)"
    if cam == "zin":     z, x, y = f"min(1.03+{0.0030:.6f}*on,1.34)", cx, cy
    elif cam == "zout":  z, x, y = f"max(1.30-{0.0030:.6f}*on,1.03)", cx, cy
    elif cam == "punch": z, x, y = f"max(1.40-{0.0075:.6f}*on,1.06)", cx, cy
    elif cam == "panL":  z, x, y = "1.24", f"(iw-iw/zoom)*(1-on/{n})", cy
    elif cam == "panR":  z, x, y = "1.24", f"(iw-iw/zoom)*(on/{n})", cy
    elif cam == "tiltUp":z, x, y = "1.24", cx, f"(ih-ih/zoom)*(1-on/{n})"
    elif cam == "nin":   z, x, y = f"min(1.50+{0.0018:.6f}*on,1.72)", \
                                   "(iw-iw/zoom)*0.52", "(ih-ih/zoom)*0.30"
    else:                z, x, y = f"min(1.14+{0.0010:.6f}*on,1.30)", \
                                   f"(iw-iw/zoom)*(0.30+0.22*on/{n})", cy
    return z, x, y


EXPOSURE_CAL = json.load(open("work/expo_calib.json")) if os.path.exists("work/expo_calib.json") else {}


FLAG_LIFT = ("s05", "bg_end", "s01_hook", "s09", "s08")
SHOULDER = "curves=all='0/0.025 0.28/0.35 0.58/0.62 0.82/0.83 1/0.93'"
ASSET_TUNE = json.load(open("work/asset_tune.json")) if os.path.exists("work/asset_tune.json") else {}

def tune_for(img_path):
    stem = os.path.splitext(os.path.basename(img_path))[0]
    if stem not in ASSET_TUNE:
        # never silently fall back to a neutral gamma: that ships a dark/over-bright shot
        raise SystemExit(f"no exposure solution for plate '{stem}'. "
                         f"Run: cd build && ../.venv/bin/python tune_assets.py {stem}")
    return ASSET_TUNE[stem]

def build_chain(img_path, cam, grade, flags, beat, n, idx, for_sim=False):
    W_, H_ = W, H
    z, x, y = cam_expr(cam, n)
    chain = ["scale=1620:2880:flags=lanczos,setsar=1"]
    if not for_sim:
        chain.append(f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W_}x{H_}:fps={FPS}")
    else:
        zval = eval(z.replace("on", "0"), {"min": min, "max": max}) if not z.replace(".", "").isdigit() else float(z)
        chain.append(f"zoompan=z='{zval}':d=1:s={W_}x{H_}:fps={FPS}")
    if "ghost" in flags and not for_sim:
        chain.append("gblur=sigma=2.2:enable='between(t,0.05,0.42)'")
    if "mirror" in flags:
        chain.append("hflip")
    if "dissolve" in flags and not for_sim:
        chain.append("fade=in:st=0:d=0.20:color=black")
    if "shake" in flags:
        chain.append(f"crop=1040:1880:'20+6*sin(t*63)':'20+5*cos(t*47)',scale={W_}:{H_}:flags=lanczos,setsar=1")
    chain.append(GRADE[grade])
    _t = tune_for(img_path)
    chain.append(f"eq=gamma={_t['gamma']}")
    if _t.get("shoulder"):
        chain.append(SHOULDER)
    chain.append("vignette=PI/5.2")
    if not for_sim:
        chain.append("noise=alls=%d:allf=t+u" % (11 if "grain2" in flags else 8))
    chain.append("unsharp=5:5:0.55:5:5:0.0")
    if not for_sim:
        if "glitch" in flags:
            chain.append("rgbashift=rh=9:bh=-9:gv=2:enable='lt(t,0.10)'")
            chain.append("noise=alls=34:allf=t+u:enable='lt(t,0.10)'")
        else:
            chain.append("rgbashift=rh=2:bh=-2")
        if "invert" in flags:
            chain.append("negate=enable='lt(t,0.055)'")
        if "flash" in flags:
            chain.append("drawbox=x=0:y=0:w=iw:h=ih:color=white@0.92:t=fill:enable='lt(t,0.06)'")
        if "pulse" in flags:
            chain.append("eq=brightness='0.012*sin(2*PI*t*1.35)':eval=frame")
    chain.append("setsar=1,format=yuv420p")
    return chain
