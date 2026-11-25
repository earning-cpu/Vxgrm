"""Timeline, shot list and text cues for the Hindi horror short."""
import numpy as np

FPS = 30
W, H = 1080, 1920

# ------------------------------------------------------------------ VO timing
# actual mp3 durations (seconds) measured at 48k
VO_RAW = {
    "v01": 4.04, "v02": 10.32, "v03": 5.76, "v04": 6.84, "v05": 3.92,
    "v06": 8.56, "v07": 2.76, "v08": 8.84, "v09": 7.28, "v10": 8.84,
}
TEMPO = 1.18
VO = {k: v / TEMPO for k, v in VO_RAW.items()}

# placement of each VO segment (start times)
VO_START = {
    "v01": 0.70,
    "v02": 4.30,
    "v03": 13.30,
    "v04": 18.60,
    "v05": 24.60,
    "v06": 28.20,
    "v07": 35.60,
    "v08": 38.90,
    "v09": 46.70,
    "v10": 53.20,
}
VIDEO_END = 64.30


def vo_end(k):
    return VO_START[k] + VO[k]


# ------------------------------------------------------------------ palette
BONE = (242, 237, 228)
WHITE = (255, 255, 255)
RED = (222, 32, 38)
BLOOD = (176, 14, 20)
GOLD = (216, 170, 78)
GREY = (168, 164, 158)
DIMGREY = (120, 118, 114)
GREEN = (150, 210, 140)


class Cue:
    """A timed text overlay."""

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
        self.max_w = kw.get("max_w", 940)
        self.sub = kw.get("sub")
        self.sub_size = kw.get("sub_size", 40)
        self.sub_color = kw.get("sub_color", (196, 192, 184))
        self.hl = kw.get("hl")                 # substring to colour red
        self.hl_color = kw.get("hl_color", RED)
        self.scrim = kw.get("scrim", 0.50)
        self.shake = kw.get("shake", 0.0)
        self.glitch = kw.get("glitch", False)
        self.rotate = kw.get("rotate", 0.0)
        self.fade_in = kw.get("fade_in", 0.22)
        self.fade_out = kw.get("fade_out", 0.22)


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
        self.flash = kw.get("flash", 0.0)     # red flash strength at start
        self.vignette = kw.get("vignette", 0.80)
        self.scan = kw.get("scan", 0.05)
        self.aber = kw.get("aber", 1.2)


# ------------------------------------------------------------------ timeline
def build():
    S = []

    # ================= ACT 1 : HOOK =================
    S.append(Shot(0.00, 2.35, "sb1_p1_fort_gate.jpg", z0=1.02, z1=1.14, cy=0.45,
                  darken=0.18, chapter="असली घटना", cues=[
                      Cue(0.12, 2.35, "पुणे का ये किला...", size=92, y=0.575,
                          anim="pop", hl="किला", scrim=0.62, stroke=9),
                  ]))
    S.append(Shot(2.35, 4.30, "sb1_p10_doorway.jpg", z0=1.24, z1=1.02, cy=0.42,
                  trans="flash", flash=0.55, shake=3.0, darken=0.14, cues=[
                      Cue(2.52, 4.30, "...आज भी एक आवाज़ सुनता है।", size=82, y=0.60,
                          anim="glitch", hl="आवाज़", scrim=0.60, stroke=9),
                  ]))

    # ================= ACT 2 : SETUP =================
    S.append(Shot(4.30, 7.10, "sb1_p2_corridor.jpg", z0=1.04, z1=1.16, cy=0.5,
                  trans="glitch", darken=0.22, dust=1.0, cues=[
                      Cue(4.42, 7.10, "साल", size=54, y=0.245, color=(206, 198, 182),
                          anim="pop", scrim=0.30),
                      Cue(4.62, 7.10, "1773", font="anton", size=190, y=0.345,
                          color=GOLD, anim="punch", tracking=0.06, scrim=0.30),
                      Cue(5.55, 7.10, "शनिवारवाड़ा, पुणे", size=62, y=0.70,
                          anim="slide", color=(212, 208, 200), scrim=0.62),
                  ]))
    S.append(Shot(7.10, 10.20, "sb1_p2_corridor.jpg", z0=1.20, z1=1.34, cx=0.5, cy=0.35,
                  trans="cut", darken=0.20, dust=1.0, cues=[
                      Cue(7.24, 10.20, "मराठा साम्राज्य का दिल", size=88, y=0.62,
                          anim="pop", hl="दिल", hl_color=GOLD, scrim=0.62, stroke=10),
                  ]))
    S.append(Shot(10.20, 13.30, "sb1_p3_letter.jpg", z0=1.05, z1=1.22, cy=0.55,
                  trans="cut", darken=0.14, cues=[
                      Cue(10.34, 13.30, "अठारह साल का पेशवा", size=86, y=0.63,
                          anim="pop", hl="अठारह साल", scrim=0.66, stroke=10),
                      Cue(11.15, 13.30, "नारायणराव", font="serif_b", size=112, y=0.745,
                          color=(232, 194, 124), anim="slide", scrim=0.30, stroke=8),
                  ]))

    # ================= ACT 3 : THE ORDER =================
    S.append(Shot(13.30, 16.30, "sb1_p3_letter.jpg", z0=1.26, z1=1.40, cy=0.45,
                  trans="cut", darken=0.20, cues=[
                      Cue(13.44, 16.30, "उसके चाचा ने आदेश भेजा", size=80, y=0.56,
                          anim="pop", scrim=0.66, stroke=9),
                      Cue(14.35, 16.30, "नारायणराव को पकड़ो", size=96, y=0.68,
                          anim="punch", color=WHITE, stroke=11, scrim=0.66),
                  ]))
    S.append(Shot(16.30, 19.20, "sb1_p3_letter.jpg", z0=1.42, z1=1.56, cx=0.55, cy=0.62,
                  trans="cut", darken=0.16, cues=[
                      Cue(16.44, 19.20, "लेकिन रास्ते में...", size=74, y=0.34,
                          anim="glitch", color=(198, 194, 186), scrim=0.60),
                      Cue(17.10, 19.20, "एक शब्द बदल गया", size=100, y=0.58,
                          anim="punch", hl="एक शब्द", stroke=12, scrim=0.70),
                  ]))
    S.append(Shot(19.20, 21.60, None, black=True, trans="dip", dust=0.8,
                  chapter="वो आदेश", cues=[
                      Cue(19.28, 21.60, "धर", font="serif_b", size=200, y=0.36,
                          color=(150, 146, 140), anim="glitch", scrim=0.0, stroke=6),
                      Cue(19.92, 21.60, "मार", font="serif_b", size=240, y=0.545,
                          color=RED, anim="punch", stroke=16, scrim=0.0),
                      Cue(20.60, 21.60, "सिर्फ़ एक शब्द।", size=52, y=0.70,
                          anim="slide", color=(214, 210, 202), scrim=0.0),
                  ]))
    S.append(Shot(21.60, 24.60, "sb1_p4_assassins.jpg", z0=1.10, z1=1.22, cy=0.55,
                  trans="glitch", shake=1.5, darken=0.12, cues=[
                      Cue(21.74, 24.60, "गणेश चतुर्थी की रात", size=70, y=0.38,
                          anim="pop", color=(226, 196, 148), scrim=0.62),
                      Cue(22.60, 24.60, "हत्यारे अंदर आए", size=98, y=0.57,
                          anim="punch", hl="हत्यारे", stroke=12, scrim=0.70),
                  ]))

    # ================= ACT 4 : THE CHASE =================
    S.append(Shot(24.60, 27.60, "sb1_p4_assassins.jpg", z0=1.24, z1=1.40, cx=0.42, cy=0.5,
                  trans="cut", handheld=2.5, darken=0.10, cues=[
                      Cue(24.74, 27.60, "वो भागा...", size=108, y=0.55, anim="punch",
                          stroke=13, scrim=0.72),
                      Cue(25.55, 27.60, "अपने ही महल में", size=72, y=0.665,
                          anim="slide", color=(204, 200, 192), scrim=0.60),
                  ]))
    S.append(Shot(27.60, 31.10, "sb1_p5_running.jpg", z0=1.06, z1=1.20, cy=0.42,
                  trans="whip", handheld=5.0, shake=2.0, darken=0.08, cues=[
                      Cue(27.68, 31.10, "अपने ही घर में", size=84, y=0.74,
                          anim="glitch", color=WHITE, stroke=11, scrim=0.68),
                  ]))
    S.append(Shot(31.10, 34.30, "sb1_p5_running.jpg", z0=1.24, z1=1.38, cx=0.55, cy=0.30,
                  trans="cut", handheld=6.0, shake=3.0, darken=0.04, cues=[
                      Cue(31.20, 34.30, "और फिर...", size=72, y=0.245, anim="glitch",
                          color=(206, 202, 194), scrim=0.62),
                  ]))
    S.append(Shot(34.30, 35.60, "sb1_p2_corridor.jpg", z0=1.30, z1=1.44, cy=0.25,
                  trans="cut", darken=0.34, handheld=2.0, cues=[]))

    # ================= ACT 5 : THE CRY =================
    S.append(Shot(35.60, 38.90, None, black=True, trans="glitch", dust=0.8,
                  chapter="वो चीख़", cues=[
                      Cue(35.68, 38.90, "काका...", font="serif_b", size=150, y=0.34,
                          color=BONE, anim="glitch", stroke=12, scrim=0.0),
                      Cue(36.30, 38.90, "मला वाचवा", font="serif_b", size=168, y=0.505,
                          color=RED, anim="punch", stroke=18, scrim=0.0, shake=1.2),
                      Cue(37.35, 38.90, "“काका, मुझे बचा लो”", size=50, y=0.655,
                          anim="slide", color=(212, 206, 196), scrim=0.0),
                  ]))

    # ================= ACT 6 : AFTERMATH =================
    S.append(Shot(38.90, 42.40, "sb1_p6_courtyard.jpg", z0=1.02, z1=1.12, cy=0.62,
                  trans="flash", flash=0.30, darken=0.20, cues=[
                      Cue(39.02, 42.40, "कोई नहीं आया।", size=104, y=0.30,
                          anim="punch", stroke=13, scrim=0.70),
                      Cue(40.20, 42.40, "सिर्फ़ ख़ामोशी", size=54, y=0.405,
                          anim="slide", color=(196, 192, 184), scrim=0.55),
                  ]))
    S.append(Shot(42.40, 45.00, "sb1_p6_courtyard.jpg", z0=1.30, z1=1.46, cx=0.5, cy=0.68,
                  trans="cut", darken=0.16, cues=[
                      Cue(42.52, 45.00, "टुकड़ों में...", size=78, y=0.25,
                          anim="glitch", color=(226, 178, 178), scrim=0.62),
                      Cue(43.15, 45.00, "एक मटके में", size=88, y=0.355,
                          anim="punch", stroke=11, scrim=0.66),
                  ]))
    S.append(Shot(45.00, 46.70, "sb1_p9_river.jpg", z0=1.05, z1=1.16, cy=0.5,
                  trans="cut", darken=0.14, cues=[
                      Cue(45.08, 46.70, "नदी में बहा दिया गया", size=78, y=0.31,
                          anim="slide", stroke=10, scrim=0.66),
                  ]))
    S.append(Shot(46.70, 49.80, "sb1_p7_fire.jpg", z0=1.24, z1=1.08, cy=0.5,
                  trans="whip", shake=4.0, darken=0.06, cues=[
                      Cue(46.82, 49.80, "साल", size=50, y=0.215, color=(224, 206, 170),
                          anim="pop", scrim=0.30),
                      Cue(47.00, 49.80, "1828", font="anton", size=170, y=0.315,
                          color=GOLD, anim="punch", tracking=0.06, scrim=0.30),
                      Cue(47.85, 49.80, "सात दिन तक जला", size=82, y=0.42,
                          anim="punch", stroke=11, scrim=0.62),
                  ]))

    # ================= ACT 7 : THE LEGEND =================
    S.append(Shot(49.80, 53.20, "sb1_p8_ruins.jpg", z0=1.02, z1=1.14, cy=0.5,
                  trans="cut", darken=0.18, cues=[
                      Cue(49.94, 53.20, "सिर्फ़ दीवारें बचीं", size=86, y=0.32,
                          anim="slide", color=(206, 204, 198), scrim=0.66, stroke=10),
                  ]))
    S.append(Shot(53.20, 56.60, "sb1_p8_ruins.jpg", z0=1.16, z1=1.30, cx=0.5, cy=0.34,
                  trans="cut", darken=0.16, cues=[
                      Cue(53.32, 56.60, "हर पूर्णिमा की रात", size=84, y=0.30,
                          anim="glitch", color=(216, 212, 204), scrim=0.66, stroke=10),
                  ]))
    S.append(Shot(56.60, 59.40, "sb1_p10_doorway.jpg", z0=1.30, z1=1.10, cy=0.45,
                  trans="cut", darken=0.14, cues=[
                      Cue(56.72, 59.40, "लोग आज भी सुनते हैं", size=80, y=0.28,
                          anim="slide", color=(210, 206, 198), scrim=0.66, stroke=10),
                  ]))
    S.append(Shot(59.40, 61.40, "sb1_p10_doorway.jpg", z0=1.05, z1=1.45, cy=0.42,
                  trans="flash", flash=0.75, shake=7.0, darken=0.02, cues=[
                      Cue(59.50, 61.40, "जवाब मत देना।", size=108, y=0.615,
                          anim="punch", color=RED, stroke=15, scrim=0.55, shake=2.0),
                  ]))

    # ================= CTA =================
    S.append(Shot(61.40, 64.30, None, black=True, trans="dip", dust=0.6, cues=[
        Cue(61.48, 64.30, "अगला हिस्सा चाहिए?", size=84, y=0.40, anim="pop",
            scrim=0.0, stroke=10),
        Cue(61.86, 64.30, "फॉलो करो — Part 2 जल्द", size=48, y=0.495, anim="slide",
            color=(178, 174, 168), scrim=0.0),
        Cue(62.10, 64.30, "सब्सक्राइब", size=64, y=0.615, color=WHITE, anim="button",
            tracking=0.04, scrim=0.0, stroke=0),
    ]))
    return S
