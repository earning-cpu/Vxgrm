"""Builds the three competing storyboard sheets + the analysis document."""
import os
import numpy as np

from src import storyboard as SB
from src import design as D

OUT = "storyboards"
os.makedirs(OUT, exist_ok=True)

P = SB.PW
H = SB.PH


def plate(name, zoom=1.0, cx=0.5, cy=0.5):
    return D.cover(D.load(f"assets/img/{name}"), P, H, zoom, cx, cy)


# ============================================================ BOARD 01
sb1_panels = [
    dict(tc="00:00–00:03", shot="Extreme wide / establish",
         desc="पूर्णिमा के नीचे शनिवारवाड़ा का मुख्य दरवाज़ा। कोहरा। एक भी आदमी नहीं।",
         cam="4% slow push-in", audio="Sub drone + दूर का कौवा",
         frame=plate("sb1_p1_fort_gate.jpg", 1.02, 0.5, 0.45)),
    dict(tc="00:03–00:07", shot="Interior / corridor",
         desc="महल का अंदरूनी गलियारा। दीयों की रोशनी। लंबे साये। डरावनी ख़ामोशी।",
         cam="Slow dolly forward", audio="पत्थर पर कदमों की गूंज",
         frame=plate("sb1_p2_corridor.jpg", 1.05, 0.5, 0.5)),
    dict(tc="00:07–00:13", shot="Insert / macro",
         desc="क़लम से शाही आदेश। एक शब्द बदला जा रहा है — 'धर' की जगह 'मार'।",
         cam="Macro push + rack focus", audio="क़लम की खरखराहट + दिल की धड़कन",
         frame=plate("sb1_p3_letter.jpg", 1.0, 0.5, 0.55)),
    dict(tc="00:13–00:19", shot="Wide / low angle",
         desc="मशालों के साथ गर्री हत्यारे दरवाज़े से अंदर आते हैं। चेहरे अंधेरे में।",
         cam="Low angle, handheld", audio="भाले की खनक + आग की चटक",
         frame=plate("sb1_p4_assassins.jpg", 1.05, 0.5, 0.5)),
    dict(tc="00:19–00:27", shot="Tracking / panic",
         desc="अठारह साल का नारायणराव अपने ही महल में भाग रहा है। पीछे मुड़कर देखता है।",
         cam="Handheld chase, 24fps", audio="सांसें + कदम + धड़कन तेज़",
         frame=plate("sb1_p5_running.jpg", 1.08, 0.5, 0.42)),
    dict(tc="00:27–00:33", shot="Static wide / aftermath",
         desc="ख़ाली आँगन। चाँदनी। फ़र्श पर ख़ून का लंबा निशान — दरवाज़े तक।",
         cam="Locked-off, slow creep", audio="एक भी आवाज़ नहीं — सिर्फ़ हवा",
         frame=plate("sb1_p6_courtyard.jpg", 1.03, 0.5, 0.5)),
    dict(tc="00:33–00:39", shot="Night exterior",
         desc="नदी का किनारा। पानी में चाँद का परछाई। किनारे पर एक टूटा मटका।",
         cam="Slow push, water reflection", audio="पानी की छल-छल + बाज़ की चीख़",
         frame=plate("sb1_p9_river.jpg", 1.04, 0.5, 0.5)),
    dict(tc="00:39–00:46", shot="Wide / inferno",
         desc="साल 1828। पूरा महल सात दिन जलता है। अंदर की हर चीज़ राख़।",
         cam="Slow pull-back", audio="आग की दहाड़ + गिरती दीवारें",
         frame=plate("sb1_p7_fire.jpg", 1.06, 0.5, 0.55)),
    dict(tc="00:46–00:53", shot="Establish / ruins",
         desc="आज का शनिवारवाड़ा — सिर्फ़ दीवारें बची हैं। धुंध में डूबा खंडहर।",
         cam="Slow orbit feel", audio="हवा + दूर की चीख़ (पहली बार)",
         frame=plate("sb1_p8_ruins.jpg", 1.05, 0.5, 0.5)),
    dict(tc="00:53–01:00", shot="The reveal / scare",
         desc="काला दरवाज़ा। अंधेरे में एक बच्चे की परछाई — बिल्कुल स्थिर। फिर फ्रेम कट।",
         cam="Snap zoom + shake", audio="साइलेंस → स्केयर स्टिंग → कट",
         frame=plate("sb1_p10_doorway.jpg", 1.0, 0.5, 0.45)),
]

sb1_scores = [
    ("हुक — पहले 3 सेकंड (Hook)", 9.4, "चीख़ + पूर्णिमा = तुरंत रुकना"),
    ("विज़ुअल संभावना (Visual potential)", 9.2, "महल, आग, ख़ून — एपिक स्केल"),
    ("असली होना (Documentation)", 10.0, "Wikipedia / इतिहास — तारीख़ तक दर्ज"),
    ("इमोशनल आर्क (Emotional arc)", 9.0, "अपने ही चाचा से धोखा — 18 साल का बच्चा"),
    ("शेयरएबिलिटी (Shareability)", 9.0, "“काका मला वाचवा” — जाना-पहचाना वाक्य"),
    ("कल्चरल रेज़ोनेंस (Cultural resonance)", 9.2, "मराठा इतिहास + हिंदी बेल्ट"),
    ("प्रोडक्शन फ़ीज़िबिलिटी (Feasibility)", 9.3, "10 प्लेट रेडी, एक जैसा ग्रेड"),
]
sb1_verdict = ("इतिहास दर्ज है, इमोशन पर्सनल है, और हर शॉट के लिए स्ट्रॉन्ग विज़ुअल मौजूद है। "
               "हुक 2 सेकंड में चीख़ देता है और क्लाइमेक्स एक असली डरावनी इमेज पर ख़त्म होता है। "
               "यही बोर्ड अप्रूव किया जाता है।")

# ============================================================ BOARD 02
sb2_panels = [
    dict(tc="00:00–00:04", shot="Extreme wide / desert",
         desc="राजस्थान का रेगिस्तान। ढलता सूरज। दूर जलसरे हवेलियों के खंडहर।",
         cam="Slow push", audio="हवा + रेत की सरसराहट",
         frame=SB.styleframe_desert(0)),
    dict(tc="00:04–00:10", shot="Wide / street",
         desc="गाँव की ख़ाली गली। सारे दरवाज़े खुले। अंदर कोई नहीं।",
         cam="Dolly down the street", audio="डोर की चरचराहट",
         frame=SB.styleframe_village(1)),
    dict(tc="00:10–00:16", shot="Insert / macro",
         desc="मेज़ पर रखा खाना। आधा खाया हुआ। उस पर धूल की एक परत।",
         cam="Macro, shallow DOF", audio="ड्रोन + घड़ी की टिक-टिक",
         frame=SB.styleframe_ear(2)),
    dict(tc="00:16–00:23", shot="Close / wall",
         desc="दीवार पर खोदा हुआ श्राप — “यहाँ कोई नहीं बसेगा।”",
         cam="Slow tilt up", audio="लो-फ़्रीक़वेंसी ड्रोन",
         frame=SB.styleframe_wall(3)),
    dict(tc="00:23–00:31", shot="Wide / storm",
         desc="रेत का तूफ़ान पूरे गाँव को निगल जाता है। आख़ि्री दरवाज़ा भी बंद।",
         cam="Whip pan + speed ramp", audio="तूफ़ान + रिवर्स रिसर",
         frame=SB.styleframe_sandstorm(4)),
    dict(tc="00:31–00:38", shot="Night / signboard",
         desc="आज: “सूरज ढलने के बाद प्रवेश वर्जित।” पर आज भी कुछ सुनाई देता है।",
         cam="Slow push on dark", audio="साइलेंस → स्टिंग",
         frame=SB.styleframe_street(5)),
]
sb2_scores = [
    ("हुक — पहले 3 सेकंड (Hook)", 8.0, "“पूरा गाँव एक रात में ग़ायब”"),
    ("विज़ुअल संभावना (Visual potential)", 8.2, "रेगिस्तान गॉथिक — पर दोहराव"),
    ("असली होना (Documentation)", 6.8, "त्यागा हुआ गाँव असली, तारीख़ विवादित"),
    ("इमोशनल आर्क (Emotional arc)", 7.2, "कोई पर्सनल प्रोटैगोनिस्ट नहीं"),
    ("शेयरएबिलिटी (Shareability)", 8.2, "“आज भी वर्जित है” — अच्छा हुक"),
    ("कल्चरल रेज़ोनेंस (Cultural resonance)", 7.4, "राजस्थान — नेशनल रिकॉग्निशन कम"),
    ("प्रोडक्शन फ़ीज़िबिलिटी (Feasibility)", 6.2, "कोई प्लेट रेडी नहीं; रेत में वैरायटी मुश्किल"),
]
sb2_verdict = ("कॉन्सेप्ट मज़बूत है, पर कहानी में एक साफ़ प्रोटैगोनिस्ट नहीं — इसलिए दर्शक किसी से "
               "जुड़ नहीं पाता। विज़ुअली रेगिस्तान के 6 शॉट एक जैसे लगते हैं। बैकअप के तौर पर रखा गया।")

# ============================================================ BOARD 03
sb3_panels = [
    dict(tc="00:00–00:03", shot="Night / street",
         desc="कर्नाटक का गाँव। रात। बस एक बत्ती जल रही है। सन्नाटा।",
         cam="Slow push", audio="झींगुर + दूर का कुत्ता",
         frame=SB.styleframe_street(0)),
    dict(tc="00:03–00:09", shot="Insert / door",
         desc="एक दरवाज़े पर चॉक से लिखा: “नाले बा” — कल आना।",
         cam="Macro on chalk", audio="चॉक की खरखराहट",
         frame=SB.styleframe_door(1)),
    dict(tc="00:09–00:15", shot="Wide / silhouette",
         desc="गली के छोर पर एक औरत की परछाई — बुला रही है। नाम से।",
         cam="Slow creep forward", audio="फुसफुसाहट में नाम",
         frame=SB.styleframe_village(2)),
    dict(tc="00:15–00:21", shot="Macro / ear",
         desc="कान। सांस। आवाज़ और करीब आ रही है।",
         cam="Extreme macro", audio="बायोरिदम + फुसफुसाहट",
         frame=SB.styleframe_ear(3)),
    dict(tc="00:21–00:29", shot="Insert / hand",
         desc="काँपता हाथ दरवाज़े पर लिखता है — और आवाज़ रुक जाती है।",
         cam="Handheld insert", audio="सांस रुकना",
         frame=SB.styleframe_door(4)),
    dict(tc="00:29–00:36", shot="Present day",
         desc="आज भी कर्नाटक के कई दरवाज़ों पर यही लिखा है। क्यों?",
         cam="Slow pull-back", audio="लो ड्रोन + स्टिंग",
         frame=SB.styleframe_street(5)),
]
sb3_scores = [
    ("हुक — पहले 3 सेकंड (Hook)", 9.0, "“जवाब मत देना” — परफेक्ट टेंशन"),
    ("विज़ुअल संभावना (Visual potential)", 6.0, "एक ही लोकेशन — वैरायटी कम"),
    ("असली होना (Documentation)", 5.2, "लोक-कथा, कोई दर्ज घटना नहीं"),
    ("इमोशनल आर्क (Emotional arc)", 8.4, "सेकंड-पर्सन डर — बहुत पर्सनल"),
    ("शेयरएबिलिटी (Shareability)", 9.0, "“टैग सोमवन” के लिए बेस्ट"),
    ("कल्चरल रेज़ोनेंस (Cultural resonance)", 6.8, "कर्नाटक-स्पेसिफ़िक"),
    ("प्रोडक्शन फ़ीज़िबिलिटी (Feasibility)", 6.6, "सिर्फ़ दरवाज़ा/गली/कान — सीमित"),
]
sb3_verdict = ("हुक सबसे तेज़ है, पर यह एक लोक-कथा है — दर्ज इतिहास नहीं। विज़ुअल वैरायटी कम है, "
               "इसलिए 60 सेकंड में रुक-रुक कर दोहराव आएगा। स्क्रिप्ट बैकअप के लिए सुरक्षित।")


def main():
    print("Rendering storyboard 01 …")
    SB.render(f"{OUT}/SB01_Kaka_Mala_Vachwa.png", 1,
              "काका मला वाचवा", 
              "शनिवारवाड़ा, पुणे — 30 अगस्त 1773. अठारह साल का पेशवा अपने ही महल में भागता है। "
              "उसका चाचा एक शब्द बदल देता है — और इतिहास हमेशा के लिए बदल जाता है।",
              ["TRUE STORY", "60 SEC", "9:16 VERTICAL", "HINDI"],
              sb1_panels, sb1_scores, sb1_verdict, True)

    print("Rendering storyboard 02 …")
    SB.render(f"{OUT}/SB02_Kuldhara.png", 2,
              "कुलधरा — एक रात में ग़ायब गाँव",
              "राजस्थान, 1825. एक ही रात में पूरा गाँव खाली हो जाता है — दरवाज़े खुले, "
              "खाना मेज़ पर, और दीवार पर एक श्राप।",
              ["FOLK HISTORY", "60 SEC", "9:16 VERTICAL", "HINDI"],
              sb2_panels, sb2_scores, sb2_verdict, False)

    print("Rendering storyboard 03 …")
    SB.render(f"{OUT}/SB03_Nale_Ba.png", 3,
              "नाले बा — जवाब मत देना",
              "कर्नाटक, 1990s. रात को एक आवाज़ तुम्हारा नाम पुकारती है। जवाब देने वाले "
              "अगली सुबह नहीं मिले। इसलिए दरवाज़ों पर लिखा: “नाले बा।”",
              ["FOLK HORROR", "60 SEC", "9:16 VERTICAL", "HINDI"],
              sb3_panels, sb3_scores, sb3_verdict, False)
    print("done")


if __name__ == "__main__":
    main()
