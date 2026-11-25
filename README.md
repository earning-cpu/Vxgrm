# काका मला वाचवा — Hindi Horror Short

A 64-second vertical (1080×1920) Hindi horror short for YouTube Shorts, built end-to-end
in this repo: **three competing storyboards → scored analysis → one approved board →
production → frame-by-frame QA**.

**Story:** the assassination of 18-year-old Peshwa Narayanrao inside Shaniwar Wada, Pune,
on 30 August 1773 — a documented historical event, not folklore.

---

## Deliverables

| File | What it is |
|---|---|
| `out/kaka_mala_vachwa.mp4` | **The film.** 1080×1920 · 30 fps · 64.3 s · H.264 High · AAC 192k |
| `out/kaka_mala_vachwa.srt` | Hindi subtitles, timed to the narration |
| `out/thumbnail.jpg` | 1280×720 YouTube thumbnail |
| `storyboards/SB01_Kaka_Mala_Vachwa.jpg` | **Approved** storyboard (10 panels, 9.30/10) |
| `storyboards/SB02_Kuldhara.jpg` | Backup board (7.43/10) |
| `storyboards/SB03_Nale_Ba.jpg` | Backup board (7.29/10) |
| `storyboards/ANALYSIS.md` | Full scoring rubric + why Board 01 won |
| `qa/QA_REPORT.md` | Frame-by-frame audit: every one of the 1,929 frames measured |
| `qa/sheet_1..6.jpg` | Contact sheets — 216 sampled frames across the whole film |
| `qa/sheet_tail.jpg` | Every 3rd frame of the last 7 s (57.3–64.3 s) |
| `qa/per_shot.json` | Per-shot luminance / contrast / motion / black / frozen counts |
| `qa/chk_*.jpg`, `qa/cta_*.jpg` | Full-resolution spot checks (marker boxes, CTA) |

---

## The film

**Structure** — 7 acts, 23 shots, ~4–7 s per shot:

| Act | Time | Beat |
|---|---|---|
| Hook | 0:00–0:04 | A fort that still hears a voice |
| Setup | 0:04–0:13 | 1773 · Shaniwar Wada · an 18-year-old Peshwa |
| The order | 0:13–0:21 | “धर” (seize) becomes “मार” (slay) |
| The chase | 0:21–0:35 | Ganesh Chaturthi night · assassins inside · he runs |
| The cry | 0:36–0:39 | **काका... मला वाचवा** |
| Aftermath | 0:39–0:47 | No one came · a pot · the river · no last rites |
| Legend | 0:47–1:01 | 1828 fire · the ruins today · full-moon nights |
| CTA | 1:01–1:04 | “अगला हिस्सा चाहिए?” |

**Visual language** — kinetic Devanagari type with marker-box word highlights, punch-in /
whip-pan / glitch / flash transitions, teal-and-amber grade, film grain, chromatic
aberration, vignette, scanlines, dust motes, REC timecode, progress bar and chapter badges.

**Sound** — fully procedural score built in `src/audio.py` (numpy + scipy): detuned saw
drone bed, sub hits, heartbeat that accelerates through the chase, swept-noise whooshes,
risers, reverse swells, fire crackle, wind, and whispered syllables. Voiceover is
time-stretched 1.18× for pace and sidechain-ducked under the music.

---

## Rebuild it

```bash
python3 -m pip install -r requirements.txt

python3 build_storyboards.py     # renders the 3 storyboard sheets
python3 render.py out/film.mp4   # audio + 1929 frames + mux  (~9 min)
python3 qa.py out/film.mp4       # frame-by-frame audit -> qa/
python3 qa_sheets.py out/film.mp4
python3 qa_extras.py             # per-shot table, SRT, thumbnail
```

### Pipeline

```
src/text_engine.py   HarfBuzz shaping + FreeType rasterisation (correct Devanagari
                     conjuncts/matras, per-glyph control for kinetic type)
src/design.py        compositing toolkit: gradients, rounded rects, grade, bloom,
                     grain, vignette, chromatic aberration, cached Layer surface
src/timeline.py      the edit: shots, camera moves, transitions, text cues
src/renderer.py      frame renderer + ffmpeg encode
src/audio.py         procedural score, SFX, VO assembly, limiter, loudness
src/storyboard.py    storyboard sheet renderer + procedural styleframes
```

### Fonts

`assets/fonts/` holds Noto Sans/Serif Devanagari (merged Devanagari + Latin subsets from
Fontsource woff2, converted to TTF with fontTools) plus Anton and Bebas Neue. Latin-only
faces are auto-substituted when a cue contains Devanagari (`resolve_font`).

### Assets

`assets/img/` — 10 generated plates (768×1376, upscaled and graded per shot).
`assets/vo/` — 10 Hindi narration chunks.

---

## QA summary

Measured across all 1,929 decoded frames:

| Check | Result |
|---|---|
| Duration / frames | 64.30 s · 1929 frames |
| Black or dropped frames | **0** |
| Frozen runs | **0** |
| Max flashes per second | **1** (photosensitivity-safe) |
| Highlight clipping | 0.023 % |
| Shadow crush | 12.3 % |
| Silent audio frames | **0** |
| A/V sync lag | **0 frames** |
| Declared cuts landing on frame | 20 / 23 * |
| Loudness | −14.0 LUFS · true peak −0.3 dBFS |

\* The three unmatched are frame 0 (no predecessor), 7.10 s (same-plate soft cut) and
35.60 s (dark corridor → black text card). All three are intentional; the rest land exactly.

---

## Fact basis

- Narayanrao Peshwa, b. 10 Aug 1755, assassinated 30 Aug 1773, aged 18 — Wikipedia,
  *Narayan Rao*.
- Order altered from “नारायणराव ला धरा” to “मारा”; cry “काका, मला वाचवा” — contemporary
  Maratha accounts, summarised by Indian Paranormal Society and Pune district histories.
- Body dismembered, carried out in a pot, thrown into the river; last rites never performed.
- Interior destroyed by a seven-day fire beginning 27 Feb 1828.
- The full-moon cry is the *legend*; the film labels it as legend, not fact.

---

## Honest notes

- Narration is TTS. It is clean and correctly paced, but it is not a human voice actor —
  for a channel upload you may want to re-record the VO and drop it in at the same
  timecodes (`src/timeline.py → VO_START`).
- The 10 plates are AI-generated. They were visually checked for artifacts (hands, faces,
  text); the parchment shot deliberately has unreadable ink, with the real line typeset
  over it.
- Boards 02 and 03 are presented as *styleframe* boards (procedural compositions), while
  Board 01 has full generated key art — so their visual scores reflect concept strength,
  not finished frames.
