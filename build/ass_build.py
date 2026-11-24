"""
Bhangarh Shorts — ASS overlay build (subtitles + HUD + title cards + progress bar).
Everything is drawn by libass so Devanagari shaping/complex scripts stay perfect.
"""
import json, re

W, H = 1080, 1920
TL = json.load(open("work/timeline.json"))
TOTAL = TL["total"]
BEATS = {b["id"]: b for b in TL["beats"]}

CHANNEL = "HORROR HINDI"          # <- change to your channel handle
TAGLINE = "हिंदी स्टोरीज़"

DEV   = "Noto Sans Devanagari Black"
DEV_S = "Noto Sans Devanagari"     # Bold face
TITLE = "Rozha One"
LAT   = "Bebas Neue"

WHITE  = "&H00FFFFFF"
AMBER  = "&H0028C8FF"   # #FFC824
RED    = "&H00202FFF"   # #FF2F20
BLOOD  = "&H00181BDC"   # #DC1B18
GREY   = "&H00B4B4B4"
DARK   = "&H00000000"

# spoken text (exactly what is voiced)
TEXT = {
 "b01": "एक ऐसा किला जहाँ सूरज ढलने के बाद जाना सरकार ने बैन कर दिया है",
 "b02": "भानगढ़ फोर्ट राजस्थान दुनिया के सबसे डरावने इलाकों में गिना जाता है",
 "b03": "कहानी नंबर एक गुरु बालू नाथ शर्त सिर्फ एक थी मेरी समाधि पर महल की परछाईं नहीं पड़ेगी",
 "b04": "राजा ने महल और ऊँचा कर दिया परछाईं पड़ी और पूरा शहर तबाह हो गया",
 "b05": "कहानी नंबर दो तांत्रिक सिंघिया और राजकुमारी रत्नावती इत्र में जादू और फिर मौत का श्राप",
 "b06": "मरते वक़्त सिंघिया ने कहा इस किले में अब कोई सुख से नहीं रहेगा",
 "b07": "असली इतिहास सत्रह सौ तिरासी तक भानगढ़ पूरी तरह वीरान हो चुका था अकाल जंग और पलायन",
 "b08": "तो रात का बैन क्यों बिना छत के खंडहर घुप्प अंधेरा और सरिस्का के तेंदुए",
 "b09": "लेकिन लोग आज भी कहते हैं वहाँ रात में बाज़ार की आवाज़ें आती हैं",
 "b10": "अगर तुम्हें वहाँ रात में अकेला छोड़ दिया जाए तो क्या करोगे कमेंट में बताओ",
}

HEAD = f"""[Script Info]
Title: Bhangarh Short
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: sub,{DEV},96,{WHITE},{WHITE},{DARK},&HA0000000,0,0,0,0,100,100,0,0,1,9,4,5,54,54,0,1
Style: title,{TITLE},132,{WHITE},{WHITE},{DARK},&HA0000000,0,0,0,0,100,100,0,0,1,10,5,5,40,40,0,1
Style: hud,{LAT},52,{WHITE},{WHITE},{DARK},&HA0000000,0,0,0,0,100,100,6,0,1,4,2,7,60,60,0,1
Style: hud2,{DEV_S},40,{GREY},{GREY},{DARK},&HA0000000,0,0,0,0,100,100,0,0,1,3,2,7,60,60,0,1
Style: chip,{DEV},44,{WHITE},{WHITE},{DARK},&HA0000000,0,0,0,0,100,100,0,0,3,10,0,5,40,40,0,1
Style: tag,{LAT},58,{WHITE},{WHITE},&H00000000,&H00000000,0,0,0,0,100,100,10,0,3,15,0,5,40,40,0,1
Style: docT,{DEV},64,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1
Style: docE,{LAT},44,&H008B4A10,&H008B4A10,&H008B4A10,&H008B4A10,0,0,0,0,100,100,8,0,1,0,0,5,40,40,0,1
Style: asmr,{DEV_S},58,{WHITE},{WHITE},{DARK},&HA0000000,0,0,0,0,100,100,4,0,1,4,3,5,80,80,0,1
Style: end,{DEV},76,{WHITE},{WHITE},{DARK},&HA0000000,0,0,0,0,100,100,0,0,1,8,4,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def ts(t):
    t = max(t, 0.0)
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

ev = []
def add(t0, t1, style, text, layer=0):
    if t1 - t0 < 0.03: return
    ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},{style},,0,0,0,,{text}")

# ------------------------------------------------------------------ subtitles
SUBY = 1185
def chunks(words, maxw=2, maxc=17):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(cur + [w])) > maxc):
            out.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur: out.append(cur)
    return out

for bid, b in BEATS.items():
    if bid not in TEXT or bid == "b10": continue
    words = [w for w in re.split(r"\s+", TEXT[bid].strip()) if w]
    t0, t1 = b["start"] + 0.02, b["start"] + b["vo_dur"] + 0.16
    lens = [max(len(w), 3) ** 0.85 for w in words]
    tot = sum(lens)
    times, acc = [], t0
    for L in lens:
        times.append((acc, acc + (t1 - t0) * L / tot))
        acc += (t1 - t0) * L / tot
    cs = chunks(words)
    wi = 0
    for ci, ch in enumerate(cs):
        span = (times[wi][0], times[wi + len(ch) - 1][1])
        pop = "{\\fscx86\\fscy86\\t(0,80,\\fscx104\\fscy104)\\t(80,150,\\fscx100\\fscy100)}"
        for k, w in enumerate(ch):
            a, e = times[wi + k]
            if k == len(ch) - 1: e = max(e, span[1])
            body = " ".join(
                (f"{{\\c{AMBER}}}{x}{{\\c{WHITE}}}" if j == k else x)
                for j, x in enumerate(ch))
            head = "{\\an5\\pos(540,%d)}" % SUBY
            if k == 0: head += pop
            if (ci == 0 and k == 0) or (ci == len(cs) - 1 and k == len(ch) - 1):
                head += "{\\fad(60,60)}"
            add(a, e, "sub", head + body, 2)
        wi += len(ch)

# ------------------------------------------------------------------ HUD
add(0, TOTAL, "hud", f"{{\\an7\\pos(58,92)}}BHANGARH FORT", 3)
add(0, TOTAL, "hud2", f"{{\\an7\\pos(60,152)}}अलवर · राजस्थान", 3)
add(0, TOTAL, "hud", f"{{\\an9\\pos(1022,92)}}{CHANNEL}", 3)
add(0, TOTAL, "hud2", f"{{\\an9\\pos(1020,152)}}{TAGLINE}", 3)

# red accent bar next to the title block
add(0, TOTAL, "tag", "{\\an7\\pos(40,80)\\p1\\bord0\\shad0\\1c" + RED + "\\fscx100\\fscy100}"
    "m 0 0 l 6 0 6 128 0 128{\\p0}", 3)

# progress bar (track + fill)
add(0, TOTAL, "tag", "{\\an7\\pos(60,1812)\\p1\\bord0\\shad0\\1c&H00303030\\1a&H40&}"
    "m 0 0 l 960 0 960 6 0 6{\\p0}", 3)
add(0, TOTAL, "tag", "{\\an7\\pos(60,1812)\\p1\\bord0\\shad0\\1c" + RED + "\\org(60,1815)\\fscx0"
    f"\\t(0,{int(TOTAL*1000)},\\fscx100)}}m 0 0 l 960 0 960 6 0 6{{\\p0}}", 3)

# "सच्ची घटना" badge
b2 = BEATS["b02"]
add(b2["start"] + 0.10, b2["start"] + 3.1, "chip",
    f"{{\\an7\\pos(58,300)\\c{WHITE}\\3c{DARK}\\fad(120,180)\\fscx80\\fscy80"
    "\\t(0,140,\\fscx100\\fscy100)}}  सच्ची घटना  ", 4)

# title cards
for bid, num, sub, dur in (("b03", "कहानी 1", "गुरु बालू नाथ", 2.1),
                           ("b05", "कहानी 2", "सिंघिया × रत्नावती", 2.1)):
    b = BEATS[bid]
    s0 = b["start"] + 0.02
    add(s0, s0 + dur, "title",
        f"{{\\an5\\pos(540,400)\\c{WHITE}\\fad(90,240)\\fscx72\\fscy72"
        f"\\t(0,150,\\fscx106\\fscy106)\\t(150,240,\\fscx100\\fscy100)}}{num}", 5)
    add(s0 + 0.18, s0 + dur, "chip",
        f"{{\\an5\\pos(540,520)\\c{AMBER}\\fad(120,240)}}{sub}", 5)
    add(s0 + 0.02, s0 + dur, "tag",
        "{\\an5\\pos(540,600)\\p1\\bord0\\shad0\\1c" + RED +
        f"\\fad(120,240)}}m -90 0 l 90 0 90 5 -90 5{{\\p0}}", 5)

# hook headline
b1 = BEATS["b01"]
add(b1["start"] + 0.12, b1["start"] + 3.6, "title",
    f"{{\\an5\\pos(540,640)\\c{WHITE}\\fad(80,260)\\fscx88\\fscy88"
    "\\t(0,130,\\fscx100\\fscy100)\\blur0}}सूरज ढलते ही", 5)
add(b1["start"] + 0.34, b1["start"] + 3.6, "title",
    f"{{\\an5\\pos(540,800)\\c{RED}\\fs150\\fad(80,260)\\fscx120\\fscy120"
    "\\t(0,170,\\fscx100\\fscy100)}}जाना बैन", 5)

# fact chips (credibility + retention)
b7 = BEATS["b07"]
add(b7["start"] + 0.8, b7["start"] + 4.2, "chip",
    f"{{\\an5\\pos(540,470)\\c{WHITE}\\3c{DARK}\\fad(120,200)}} 1783 · पूरा शहर वीरान  ", 4)
b8 = BEATS["b08"]
_d0 = b8["start"] + 0.72
_d1 = b8["start"] + 4.6
# paper card
add(_d0, _d1, "chip", "{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H00D2D8CD&\\alpha&H12&"
    "\\fad(90,180)}m 150 430 l 930 430 930 1030 150 1030{\\p0}", 6)
# header strip
add(_d0 + 0.10, _d1, "chip", "{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c" + AMBER +
    "\\fad(120,180)}m 150 430 l 930 430 930 486 150 486{\\p0}", 7)
add(_d0 + 0.12, _d1, "docE", "{\\an5\\pos(540,458)\\1c&H001A1000&}ARCHAEOLOGICAL SURVEY OF INDIA", 7)
add(_d0 + 0.20, _d1, "docT", "{\\an5\\pos(540,560)\\1c&H00202020&}भानगढ़", 7)
add(_d0 + 0.26, _d1, "docT", "{\\an5\\pos(540,650)\\1c&H00202020&\\fs56}प्रवेश से पहले व सूर्यास्त के बाद", 7)
add(_d0 + 0.32, _d1, "docT", "{\\an5\\pos(540,740)\\1c&H001612B8&\\fs72}प्रवेश पूर्णतः प्रतिबंधित है", 7)
add(_d0 + 0.38, _d1, "docE", "{\\an5\\pos(540,838)\\1c&H00606060&\\fs30}ENTRY STRICTLY PROHIBITED", 7)
add(_d0 + 0.44, _d1, "docE", "{\\an5\\pos(540,878)\\1c&H00606060&\\fs30}BEFORE SUNRISE · AFTER SUNSET", 7)
# stamp
add(_d0 + 0.55, _d1, "docT", "{\\an5\\pos(540,972)\\1c" + RED + "\\fs50\\bord0\\shad0"
    "\\fscx130\\fscy130\\t(0,120,\\fscx100\\fscy100)}प्रतिबंधित", 7)

# curse beat — big stamped line
b6 = BEATS["b06"]
add(b6["start"] + 0.55, b6["start"] + 3.0, "title",
    f"{{\\an5\\pos(540,560)\\c{RED}\\fs112\\fad(60,200)\\fscx115\\fscy115"
    "\\t(0,160,\\fscx100\\fscy100)}}मौत का श्राप", 5)

# whisper line (no VO) over b09
b9 = BEATS["b09"]

# found-footage REC stamp
for _b in ("b09", "b10"):
    _s0 = BEATS[_b]["start"] + (0.3 if _b == "b09" else 0.6)
    _s1 = BEATS[_b]["end"] - 0.05
    add(_s0, _s1, "hud2", "{\\an7\\pos(58,1738)\\c&H00D0D0D0&\\alpha&H20&\\fad(120,120)}03:07 AM · REC", 4)
    add(_s0, _s1, "tag", "{\\an7\\pos(58,1730)\\p1\\bord0\\shad0\\1c" + RED +
        "\\alpha&H10&\\t(0,600,\\alpha&HFF&)\\t(600,1200,\\alpha&H10&)}m 0 0 l 12 0 12 12 0 12{\\p0}", 4)

# end CTA
b10 = BEATS["b10"]
add(b10["start"] + 0.5, TOTAL - 0.05, "title",
    f"{{\\an5\\pos(540,560)\\c{WHITE}\\fad(120,200)\\fscx80\\fscy80"
    "\\t(0,160,\\fscx104\\fscy104)\\t(160,240,\\fscx100\\fscy100)}}क्या करोगे?", 5)
add(b10["start"] + 0.75, TOTAL - 0.05, "end",
    f"{{\\an5\\pos(540,700)\\c{AMBER}\\fad(140,200)}}कमेंट में बताओ", 5)
add(b10["start"] + 0.30, b10["start"] + 2.0, "chip",
    f"{{\\an5\\pos(540,420)\\c{AMBER}\\3c{DARK}\\fad(150,200)}}  अगला वीडियो · रात 12 बजे  ", 5)
add(b10["start"] + 0.60, TOTAL - 0.05, "hud2",
    "{\\an5\\pos(540,900)\\c&H00909090&\\fs30\\fad(200,200)}तथ्य: ASI प्रतिबंध · लोककथा: बालू नाथ, सिंघिया", 5)
add(b10["start"] + 0.95, TOTAL - 0.05, "hud2",
    f"{{\\an5\\pos(540,790)\\c{GREY}\\fad(140,200)}}follow · save · share", 5)

open("work/overlay.ass", "w", encoding="utf-8").write(HEAD + "\n".join(ev) + "\n")
print("overlay.ass events:", len(ev), "total:", TOTAL)
