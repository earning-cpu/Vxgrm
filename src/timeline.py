"""Timeline, 3D shot list, and 0-latency exact narration captions."""

FPS = 30
W, H = 1080, 1920

VO_RAW = {
    "v01": 4.24, "v02": 9.84, "v03": 5.92, "v04": 6.40, "v05": 4.16,
    "v06": 7.16, "v07": 2.48, "v08": 15.96, "v09": 9.40, "v10": 9.44,
}
TEMPO = 1.22
VO = {k: v / TEMPO for k, v in VO_RAW.items()}
VO_START = {
    "v01": 0.45,
    "v02": 4.15,
    "v03": 12.45,
    "v04": 17.55,
    "v05": 23.05,
    "v06": 26.70,
    "v07": 32.85,
    "v08": 35.10,
    "v09": 48.45,
    "v10": 56.40,
}
VIDEO_END = 66.20

# Exact spoken Hindi narration lines (no alterations)
VO_TEXT = {
    "v01": [
        "ये चीख़...",
        "दो सौ पचास साल से रुकी नहीं है।",
    ],
    "v02": [
        "साल 1773। पुणे का शनिवारवाड़ा।",
        "अठारह साल के पेशवा नारायणराव...",
        "जिन्हें अपने ही चाचा रघुनाथराव पर भरोसा था।",
    ],
    "v03": [
        "रघुनाथराव ने एक हुक्म लिखा...",
        "'नारायणराव को पकड़ो'।",
    ],
    "v04": [
        "लेकिन हुक्म बदलने में सिर्फ़ एक शब्द लगा।",
        "'पकड़ो'... 'मारो' बन गया।",
    ],
    "v05": [
        "गणेश चतुर्थी की रात।",
        "कातिल महल में घुस आए।",
    ],
    "v06": [
        "नारायणराव अपने ही महल के गलियारों में भागते रहे...",
        "जान बचाने के लिए...",
        "चाचा के कमरे की तरफ़।",
    ],
    "v07": [
        "काका... मला वाचवा।",
    ],
    "v08": [
        "कोई नहीं आया।",
        "उसका शरीर टुकड़ों में... एक मटके में...",
        "नदी में बहा दिया गया।",
        "अंतिम संस्कार कभी नहीं हुआ।",
        "साल 1828।",
        "पूरा महल सात दिन तक जला।",
        "सिर्फ़ दीवारें बचीं।",
    ],
    "v09": [
        "और आज... हर पूर्णिमा की रात...",
        "लोग आज भी वो आवाज़ सुनते हैं।",
        "अगर तुम सुनो... तो जवाब मत देना।",
    ],
    "v10": [
        "और अगर तुम्हें ये कहानियाँ असली जगहों पर सुननी हैं...",
        "तो सब्सक्राइब कर लो।",
        "मैं तुम्हें वहीं ले चलूँगा...",
        "जहाँ से ये आवाज़ आती है।",
    ],
}

# 12 3D-world shots: (t0, t1, scene_key)
SHOTS = [
    (0.00, 3.95, "hook"),
    (3.95, 12.45, "gate"),
    (12.45, 17.55, "letter"),
    (17.55, 23.05, "alteration"),
    (23.05, 26.70, "assassins"),
    (26.70, 32.85, "chase"),
    (32.85, 35.10, "cry"),
    (35.10, 42.60, "aftermath"),
    (42.60, 44.90, "river"),
    (44.90, 48.40, "fire"),
    (48.40, 56.60, "legend"),
    (56.60, VIDEO_END, "doorway"),
]


class Caption:
    """Exact 0-latency spoken caption."""
    def __init__(self, t0: float, t1: float, text: str):
        self.t0 = t0
        self.t1 = t1
        self.text = text


def build_captions():
    """Distribute each VO segment's exact phrases across [VO_START[k], VO_START[k]+VO[k]]."""
    caps = []
    for k, phrases in VO_TEXT.items():
        t_start = VO_START[k]
        dur = VO[k]
        weights = [max(1, len(p.replace(" ", ""))) for p in phrases]
        total_w = sum(weights)
        cur = t_start
        for p, w in zip(phrases, weights):
            seg_dur = dur * (w / total_w)
            caps.append(Caption(cur, cur + seg_dur, p))
            cur += seg_dur
    return caps
