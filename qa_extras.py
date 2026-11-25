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
        "ये चीख़... दो सौ पचास साल से रुकी नहीं है।",
        "साल 1773। पुणे का शनिवारवाड़ा।\nऔर उसका मालिक... सिर्फ़ अठारह साल का नारायणराव पेशवा।",
        "उसके चाचा रघुनाथराव ने एक आदेश भेजा — नारायणराव को पकड़ो।",
        "लेकिन रास्ते में किसी ने एक शब्द बदल दिया।\nपकड़ो की जगह... मारो।",
        "गणेश चतुर्थी की रात, हत्यारे किले में घुस गए।",
        "नारायणराव भागा... अपने ही महल के गलियारों में।\nऔर फिर वो चीख़...",
        "काका... मला वाचवा।",
        "कोई नहीं आया। उसका शरीर टुकड़ों में... एक मटके में...\nनदी में बहा दिया गया। अंतिम संस्कार कभी नहीं हुआ।\nसाल 1828। पूरा महल सात दिन तक जला। सिर्फ़ दीवारें बचीं।",
        "और आज... हर पूर्णिमा की रात...\nलोग आज भी वो आवाज़ सुनते हैं।\nअगर तुम सुनो... तो जवाब मत देना।",
        "और अगर तुम्हें ये कहानियाँ असली जगहों पर सुननी हैं...\nतो सब्सक्राइब कर लो। मैं तुम्हें वहीं ले चलूँगा...\nजहाँ से ये आवाज़ आती है।",
    ]
    keys = ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08", "v09", "v10"]

    def ts(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out = []
    for i, k in enumerate(keys):
        t0 = TL.VO_START[k]
        t1 = min(t0 + TL.VO[k], TL.VIDEO_END)
        out.append(f"{i+1}\n{ts(t0)} --> {ts(t1)}\n{lines[i]}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return path


def thumbnail(path="out/thumbnail.jpg"):
    """1280x720 YouTube thumbnail, set in the film's paper cut-out type."""
    from src import design as D
    from src import paper as P
    W, H = 1280, 720
    img = D.cover(D.load("assets/img/paper_test_hook.png"), W, H, 1.06, 0.52, 0.42)
    img = np.clip(img, 0, 1)
    # darken the left half so torn-paper labels read cleanly
    xs = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    img *= (1 - 0.72 * np.clip(1 - xs / 0.78, 0, 1) ** 1.25)
    img *= D.vignette_mask(W, H, 0.50, 2.0)[..., None]

    def label(box, color, seed=0):
        x0, y0, x1, y1 = box
        P.panel(img, x0, y0, x1, y1, color, seed=seed, alpha=0.97, rough=0.10)

    label((44, 40, 300, 100), P.OXIDE, 3)
    D.draw_text(img, "असली घटना", "dev_b", 36, P.BONE, 62, 70, "lm")

    # two-line title on one torn parchment sheet
    label((44, 118, 570, 350), P.PARCHMENT, 4)
    D.draw_text(img, "काका...", "serif_b", 96, P.INK, 74, 168, "lm")
    D.draw_text(img, "मला वाचवा", "serif_b", 96, P.INK, 74, 286, "lm")

    label((44, 372, 700, 452), P.CHARCOAL, 5)
    D.draw_text(img, "250 साल पुरानी चीख़", "dev_b", 46, P.BONE, 74, 412, "lm")

    D.draw_text(img, "शनिवारवाड़ा · 1773", "dev", 30, (196, 190, 180), 74, 490, "lt",
                stroke=3)
    img = D.grain(img, 0.02, 7)
    Image.fromarray(D.to_uint8(np.clip(img, 0, 1))).save(path, quality=94)
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
