"""Per-shot frame analysis + subtitles + thumbnail."""
import json
import os
import subprocess

import numpy as np
from PIL import Image

import imageio_ffmpeg

from src import timeline as TL

FPS = 30
SM_W, SM_H = 270, 480


def decode_gray(path):
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([exe, "-v", "error", "-i", path, "-vf", f"scale={SM_W}:{SM_H}",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.uint8)
    return a.reshape(-1, SM_H, SM_W).astype(np.float32) / 255.0


def per_shot(video, shots):
    g = decode_gray(video)
    n = len(g)
    diff = np.zeros(n, dtype=np.float32)
    diff[1:] = np.abs(g[1:] - g[:-1]).mean(axis=(1, 2))
    rows = []
    for i, s in enumerate(shots):
        a = int(round(s.t0 * FPS))
        b = min(n, int(round(s.t1 * FPS)))
        if b <= a:
            continue
        seg = g[a:b]
        d = diff[a:b]
        if a == 0:
            d = d[1:] if len(d) > 1 else d
        lum = seg.mean()
        con = seg.std()
        black = int((seg.mean(axis=(1, 2)) < 0.012).sum())
        frozen = int((d < 0.0006).sum())
        rows.append({
            "n": i + 1, "t0": round(s.t0, 2), "t1": round(s.t1, 2),
            "frames": int(b - a),
            "plate": (s.plate or "TEXT CARD").replace("sb1_", "").replace(".jpg", ""),
            "lum": round(float(lum), 4), "contrast": round(float(con), 4),
            "motion": round(float(d.mean()), 5),
            "black": black, "frozen": frozen,
            "cues": len(s.cues), "trans": s.trans,
            "status": "OK" if (black == 0 and frozen == 0 and con > 0.03) else "REVIEW",
        })
    return rows


def srt(shots, path="out/kaka_mala_vachwa.srt"):
    lines = [
        "पुणे का ये किला... आज भी एक आवाज़ सुनता है।",
        "साल 1773। शनिवारवाड़ा — मराठा साम्राज्य का दिल।\nऔर इसका मालिक... अठारह साल का नारायणराव पेशवा।",
        "उसके चाचा रघुनाथराव ने एक आदेश भेजा —\nनारायणराव को पकड़ो।",
        "लेकिन रास्ते में... किसी ने एक शब्द बदल दिया।\nपकड़ो की जगह... मारो।",
        "गणेश चतुर्थी की रात, हत्यारे किले में घुस गए।",
        "नारायणराव भागा... अपने ही महल के गलियारों में।\nऔर फिर वो चीख़... जो आज तक नहीं रुकी।",
        "काका... मला वाचवा।",
        "कोई नहीं आया। उसका शरीर टुकड़ों में... एक मटके में...\nनदी में बहा दिया गया। अंतिम संस्कार कभी नहीं हुआ।",
        "साल 1828। पूरा महल सात दिन तक जला। सिर्फ़ दीवारें बचीं।",
        "और आज... हर पूर्णिमा की रात...\nलोग आज भी वो आवाज़ सुनते हैं।\nअगर तुम सुनो... तो जवाब मत देना।",
    ]
    keys = ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08", "v09", "v10"]

    def ts(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out = []
    for i, k in enumerate(keys):
        t0 = TL.VO_START[k]
        t1 = t0 + TL.VO[k]
        out.append(f"{i+1}\n{ts(t0)} --> {ts(t1)}\n{lines[i]}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return path


def thumbnail(path="out/thumbnail.jpg"):
    """1280x720 YouTube thumbnail built from the doorway plate + title type."""
    from src import design as D
    from src import renderer as R
    W, H = 1280, 720
    img = D.cover(D.load("assets/img/sb1_p10_doorway.jpg"), W, H, 1.02, 0.5, 0.45)
    img = D.color_grade(img, gain=(1.03, 1.0, 1.0), saturation=1.08, contrast=1.10)
    img = np.clip(img, 0, 1) ** 0.90
    img *= D.vignette_mask(W, H, 0.55, 2.0)[..., None]
    # left dark scrim for type
    xs = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    img *= (1 - 0.80 * np.clip(1 - xs / 0.72, 0, 1) ** 1.3)

    # badge
    D.fill_rr(img, (54, 60, 300, 116), 8, (176, 20, 26), 0.95)
    D.stroke_rr(img, (54, 60, 300, 116), 8, (240, 110, 110), 2, 0.9)
    D.draw_text(img, "असली घटना", "dev_b", 38, (255, 255, 255), 66, 88, "lm", stroke=3)

    # title
    D.draw_text(img, "काका...", "serif_b", 104, (240, 234, 224), 56, 250, "lt", stroke=6)
    D.draw_text(img, "मला वाचवा", "serif_b", 118, (236, 34, 40), 56, 372, "lt", stroke=9)
    D.draw_text(img, "250 साल पुरानी चीख़", "dev_b", 40, (214, 208, 198), 58, 520, "lt",
                stroke=4)
    D.draw_text(img, "शनिवारवाड़ा · 1773", "dev", 32, (170, 166, 158), 58, 578, "lt", stroke=3)
    img = D.grain(img, 0.02, 7)
    Image.fromarray(D.to_uint8(img)).save(path, quality=94)
    return path


if __name__ == "__main__":
    video = "out/kaka_mala_vachwa.mp4"
    shots = TL.build()
    rows = per_shot(video, shots)
    json.dump(rows, open("qa/per_shot.json", "w"), indent=1)
    print(f"{'#':>3} {'t0':>6} {'plate':<22} {'frames':>6} {'lum':>6} {'con':>6} {'mot':>7} {'stat':>7}")
    for r in rows:
        print(f"{r['n']:>3} {r['t0']:>6.2f} {r['plate'][:22]:<22} {r['frames']:>6} "
              f"{r['lum']:>6.3f} {r['contrast']:>6.3f} {r['motion']:>7.4f} {r['status']:>7}")
    print("\nsrt:", srt(shots))
    print("thumb:", thumbnail())
