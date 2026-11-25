"""Timeline, shot list and text cues for the paper cut-out Hindi horror short."""
import numpy as np

FPS = 30
W, H = 1080, 1920

# ------------------------------------------------------------------ VO timing
# measured mp3 durations (seconds)
VO_RAW = {
    "v01": 4.24, "v02": 9.84, "v03": 5.92, "v04": 6.40, "v05": 4.16,
    "v06": 7.16, "v07": 2.48, "v08": 15.96, "v09": 9.40, "v10": 9.44,
}
TEMPO = 1.22
VO = {k: v / TEMPO for k, v in VO_RAW.items()}

# placement of each VO segment (start times)
VO_START = {
    "v01": 0.45,     # hook          0.45 - 3.93
    "v02": 4.15,     # setup         4.15 - 12.22
    "v03": 12.45,    # the order    12.45 - 17.30
    "v04": 17.55,    # alteration   17.55 - 22.80
    "v05": 23.05,    # assassins    23.05 - 26.46
    "v06": 26.70,    # chase        26.70 - 32.57
    "v07": 32.85,    # the cry      32.85 - 34.88
    "v08": 35.10,    # aftermath    35.10 - 48.18
    "v09": 48.45,    # legend       48.45 - 56.15
    "v10": 56.40,    # subscribe    56.40 - 64.14
}
VIDEO_END = 66.20


def vo_end(k):
    return VO_START[k] + VO[k]


# ------------------------------------------------------------------ palette
BONE = (242, 237, 228)
WHITE = (255, 255, 255)
RED = (222, 32, 38)
BLOOD = (176, 14, 20)
GOLD = (216, 170, 78)
GREY = (168, 164, 158)


class Cue:
    """A timed text overlay, set on a torn-paper label."""

    def __init__(self, t0, t1, text, **kw):
        self.t0 = t0
        self.t1 = t1
        self.text = text
        self.font = kw.get("font", "dev_b")
        self.size = kw.get("size", 76)
        self.color = kw.get("color", BONE)
        self.y = kw.get("y", 0.60)
        self.x = kw.get("x", 0.5)
        self.anim = kw.get("anim", "pop")
        self.stroke = kw.get("stroke", 7)
        self.tracking = kw.get("tracking", 0.0)
        self.max_w = kw.get("max_w", 920)
        self.sub = kw.get("sub")
        self.sub_size = kw.get("sub_size", 40)
        self.sub_color = kw.get("sub_color", (196, 192, 184))
        self.hl = kw.get("hl")                 # substring to set on an oxide label
        self.hl_color = kw.get("hl_color", RED)
        self.scrim = kw.get("scrim", 0.0)
        self.shake = kw.get("shake", 0.0)
        self.glitch = kw.get("glitch", False)
        # --- paper label -------------------------------------------------
        # "parchment" (ink text), "charcoal" / "oxide" (bone text), None = no label
        self.paper = kw.get("paper", "parchment")
        self.paper_alpha = kw.get("paper_alpha", 0.97)
        self.paper_rough = kw.get("paper_rough", 0.11)
        self.seed = kw.get("seed", 0)
        self.fade_in = kw.get("fade_in", 0.20)
        self.fade_out = kw.get("fade_out", 0.20)


class Shot:
    def __init__(self, t0, t1, plate, **kw):
        self.t0 = t0
        self.t1 = t1
        self.plate = plate
        self.z0 = kw.get("z0", 1.0)
        self.z1 = kw.get("z1", 1.08)
        self.cx = kw.get("cx", 0.5)
        self.cy = kw.get("cy", 0.5)
        self.cx1 = kw.get("cx1", self.cx)
        self.cy1 = kw.get("cy1", self.cy)
        self.trans = kw.get("trans", "cut")
        self.shake = kw.get("shake", 0.0)
        self.handheld = kw.get("handheld", 0.0)
        self.speed = kw.get("speed", 1.0)
        self.darken = kw.get("darken", 0.0)
        self.sat = kw.get("sat", 1.0)
        self.contrast = kw.get("contrast", 1.0)
        self.warm = kw.get("warm", 0.0)
        self.dust = kw.get("dust", 0.0)
        self.rec = kw.get("rec", False)
        self.chapter = kw.get("chapter")
        self.cues = kw.get("cues", [])
        self.black = kw.get("black", False)
        self.flash = kw.get("flash", 0.0)
        self.vignette = kw.get("vignette", 0.80)
        self.scan = kw.get("scan", 0.05)
        self.aber = kw.get("aber", 1.2)


# ------------------------------------------------------------------ timeline
def build():
    S = []
    HOOK = "paper_test_hook.png"
    GATE = "paper_test_gate.png"

    # ============================================ ACT 1 : HOOK (0 - 3.95)
    # visual + on-screen text + spoken line all land inside the first second
    S.append(Shot(0.00, 3.95, HOOK, z0=1.02, z1=1.20, cy=0.40, shake=1.2,
                  vignette=0.55, cues=[
                      Cue(0.06, 3.95, "250 साल", size=150, y=0.190, paper="oxide",
                          anim="punch", seed=3),
                      Cue(0.38, 3.95, "पुरानी चीख़", size=74, x=0.275, y=0.905,
                          paper="charcoal", anim="slide", seed=4, max_w=600),
                      Cue(0.55, 3.95, "असली घटना", size=40, y=0.125, x=0.29,
                          paper="oxide", anim="slide", seed=11),
                  ]))

    # ============================================ ACT 2 : SETUP (3.95 - 12.45)
    S.append(Shot(3.95, 12.45, GATE, z0=1.00, z1=1.11, cy=0.46, trans="dip",
                  cues=[
                      Cue(4.05, 12.45, "साल 1773", size=128, y=0.250, paper="oxide",
                          anim="punch", seed=5, sub="शनिवारवाड़ा, पुणे", sub_size=54),
                      Cue(8.50, 12.45, "अठारह साल का पेशवा", size=82, y=0.590,
                          paper="parchment", anim="pop", seed=7),
                  ]))

    # ============================================ ACT 3 : THE ORDER (12.45 - 17.55)
    S.append(Shot(12.45, 17.55, "p04_letter.png", z0=1.05, z1=1.24, cy=0.50,
                  trans="whip", cues=[
                      Cue(12.60, 17.55, "एक आदेश भेजा", size=86, y=0.255,
                          paper="parchment", anim="pop", seed=8),
                      Cue(14.15, 17.55, "नारायणराव को पकड़ो", size=94, y=0.640,
                          paper="charcoal", anim="punch", seed=9),
                  ]))

    # ============================================ ACT 4 : THE ALTERATION (17.55 - 23.05)
    S.append(Shot(17.55, 23.05, "p04_letter.png", z0=1.34, z1=1.12, cy=0.56,
                  trans="glitch", cues=[
                      Cue(17.70, 23.05, "पकड़ो की जगह...", size=82, y=0.245,
                          paper="parchment", anim="slide", seed=12),
                      Cue(19.55, 23.05, "मारो", size=186, y=0.485, paper="oxide",
                          anim="punch", shake=4.0, seed=13),
                      Cue(20.85, 23.05, "एक शब्द बदल दिया", size=64, y=0.665,
                          paper="charcoal", anim="slide", seed=14),
                  ]))

    # ============================================ ACT 5 : ASSASSINS (23.05 - 26.70)
    S.append(Shot(23.05, 26.70, "p05_assassins.png", z0=1.00, z1=1.14, cy=0.46,
                  trans="flash", flash=0.5, shake=3.0, cues=[
                      Cue(23.15, 26.70, "गणेश चतुर्थी की रात", size=78, y=0.235,
                          paper="charcoal", anim="pop", seed=15),
                      Cue(24.55, 26.70, "हत्यारे किले में घुस गए", size=80, y=0.680,
                          paper="parchment", anim="punch", seed=16),
                  ]))

    # ============================================ ACT 6 : THE CHASE (26.70 - 32.85)
    S.append(Shot(26.70, 32.85, "p06_running.png", z0=1.02, z1=1.20, cy=0.44,
                  trans="whip", shake=1.6, cues=[
                      Cue(26.85, 32.85, "नारायणराव भागा", size=96, y=0.255,
                          paper="oxide", anim="punch", seed=17),
                      Cue(28.40, 32.85, "अपने ही महल के गलियारों में", size=68,
                          y=0.680, paper="parchment", anim="slide", seed=18),
                  ]))

    # ============================================ ACT 7 : THE CRY (32.85 - 35.10)
    S.append(Shot(32.85, 35.10, HOOK, z0=1.34, z1=1.06, cy=0.44, trans="flash",
                  flash=0.65, shake=7.0, cues=[
                      Cue(32.95, 35.10, "काका... मला वाचवा", size=86, y=0.930,
                          paper="oxide", anim="punch", shake=2.0, seed=19),
                  ]))

    # ============================================ ACT 8 : AFTERMATH (35.10 - 44.90)
    S.append(Shot(35.10, 42.60, "p07_courtyard.png", z0=1.02, z1=1.13, cy=0.55,
                  trans="dip", cues=[
                      Cue(35.30, 42.60, "कोई नहीं आया", size=92, y=0.265,
                          paper="charcoal", anim="pop", seed=20),
                      Cue(37.70, 42.60, "एक मटके में... नदी में", size=78,
                          y=0.655, paper="parchment", anim="slide", seed=21),
                  ]))
    S.append(Shot(42.60, 44.90, "p08_river.png", z0=1.00, z1=1.09, cy=0.50,
                  trans="dip", cues=[
                      Cue(42.75, 44.90, "अंतिम संस्कार कभी नहीं हुआ", size=72,
                          y=0.400, paper="charcoal", anim="pop", seed=22),
                  ]))

    # ============================================ ACT 9 : 1828 (44.90 - 48.40)
    S.append(Shot(44.90, 48.40, "p09_fire.png", z0=1.06, z1=1.22, cy=0.48,
                  trans="flash", flash=0.55, shake=3.5, cues=[
                      Cue(45.00, 48.40, "साल 1828", size=134, y=0.255,
                          paper="oxide", anim="punch", seed=23),
                      Cue(46.40, 48.40, "सात दिन तक जला", size=82, y=0.600,
                          paper="charcoal", anim="slide", seed=24),
                  ]))

    # ============================================ ACT 10 : LEGEND (48.40 - 56.60)
    S.append(Shot(48.40, 56.60, "p10_ruins.png", z0=1.00, z1=1.11, cy=0.48,
                  trans="dip", cues=[
                      Cue(48.60, 56.60, "हर पूर्णिमा की रात", size=84, y=0.255,
                          paper="parchment", anim="pop", seed=25),
                      Cue(50.60, 53.55, "आज भी वो आवाज़ सुनते हैं", size=70,
                          y=0.600, paper="charcoal", anim="slide", seed=26),
                      # the punchline takes over the lower third instead of
                      # stacking a third label over the archway
                      Cue(53.60, 56.60, "जवाब मत देना", size=100, y=0.760,
                          paper="oxide", anim="punch", shake=3.0, seed=27),
                  ]))

    # ============================================ ACT 11 : THE DOORWAY (56.60 - 66.20)
    # no CTA card: the subscribe ask is spoken by the narration
    S.append(Shot(56.60, 66.20, "p11_doorway.png", z0=1.02, z1=1.16, cy=0.50,
                  trans="dip", darken=0.08, vignette=0.85, cues=[
                      # these follow the narration; the subscribe ask itself is
                      # spoken only, never set on screen
                      Cue(56.90, 59.40, "असली जगहों पर", size=68, y=0.235,
                          paper="charcoal", anim="pop", seed=28),
                      Cue(61.95, 64.15, "जहाँ से ये आवाज़ आती है", size=66,
                          y=0.235, paper="charcoal", anim="slide", seed=29),
                      Cue(64.30, 66.20, "काका मला वाचवा", size=84, y=0.868,
                          paper="charcoal", anim="pop", seed=30),
                  ]))
    return S
