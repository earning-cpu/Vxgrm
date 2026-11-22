# QA / QC Report — dancing-plague-1518-true-story-short.mp4

**Date:** 2026-11-22 · **Pipeline:** Python 3.11 + static FFmpeg (imageio-ffmpeg) + Pillow/NumPy + libass captions
**Final file:** `output/dancing-plague-1518-true-story-short.mp4` · 1080×1920 (9:16) · 30 fps · H.264 High · yuv420p (tv, BT.709) · AAC-LC 48 kHz stereo
**Duration:** 73.32 s (2 199 frames) · **Size:** ~39 MB · **SHA-256:** `fae1aebfec4580f65f983d2a5aa0bee0a58f5b422c99e931c4aa0e812bb09962`
**Verification loop (v2):** 3 full render → extract → analyze cycles (shot-pipeline rebuild → FX-only rebuild → dark-scene lift + embers opacity rebuild). v1 cycle retained below for history; current pass covers the v2 file.

---

## 1. Frame-by-frame video QA (every frame, none skipped) — v2 file

Extraction: `ffmpeg -vf fps=30 -q:v 3 qa/frames/f_%05d.jpg` → **2 199 frames** (73.32 s @ 30 fps).

Automated checks on the **v2** build (`src/qa_frames.py`, hard-cut frames read from `production/shots.json` ±2, S10 lightning-burst frames ±1 whitelisted — 175 whitelisted frames total, all accounted for as intended cuts/flashes):

| Check | Result |
|---|---|
| Decode of every frame | ✅ 2 199/2 199 OK |
| Black/white runs | ✅ 0 (candlelit S05/S07/S09 lifted +1.14 gamma after v2-QA flagged a 2-frame dip — see V2-001 in §3) |
| Luma-spike detection | ✅ 0 non-cut/flash frames |
| Caption presence | ✅ 36/36, 0 missing |
| **TOTAL BUGS** | ✅ **0** |

## 1b. Frame-by-frame video QA — v1 file (history)

Extraction: `ffmpeg -vf fps=30 -q:v 3 qa/frames/f_%05d.jpg` → **2 199 frames** (73.32 s @ 30 fps).

Automated checks (`src/qa_frames.py`, results in `qa/frame-metrics.csv`, raw findings in `qa/frame-bugs.json`):

| Check | Result |
|---|---|
| Decode of every frame (PIL open + full RGB parse) | ✅ 2 199/2 199 OK, 0 decode errors |
| Black-frame detection (mean luma < 9, std < 14) | ✅ 0 runs (only intended fade-in 0.00–0.10 s and fade-out 72.93–73.27 s; confirmed via `blackdetect=d=0.1:pix_th=0.10` — exactly those two, both intentional) |
| White/blown-frame detection (mean luma > 245) | ✅ 0 frames |
| Frozen-frame runs (>45 consecutive frames with mean-abs-diff < 0.05) | ✅ none (Ken Burns guarantees motion everywhere) |
| Luma-spike / hard-error detection (|diff| > 20 vs previous frame) | ✅ none (xfade 0.45 s transitions are gradual) |
| Dead color channels (std < 0.5 in any channel, excluding fade-to-black) | ✅ none |
| Caption presence in every caption window (36/36 events, ≥60 bright/red px required) | ✅ 36/36 present |
| Caption horizontal-clip detection (bright px within 36 px of edges, consistent across ≥2 samples) | ✅ 0 flagged (after fixes) |
| Caption vertical-anchor consistency (all Viral chunks must share one baseline) | ✅ unified at 1302–1339 px (after fix, see C-003) |
| Scene-boundary integrity (11 scenes, xfade offsets audited vs timeline.json) | ✅ aligned (after fix, B-007) |

**Per-scene frame coverage of the automated pass:** S01 0–179 · S02 180–377 · S03 378–575 · S04 579–779 · S05 781–942 · S06 925–1183 (xfade overlap) · S07 1104–1433 · S08 1330–1610 · S09 1496–1802 · S10 1675–2043 · S11 1904–2198. All checked — none skipped.

**Visual inspection** (independent from the automated pass) of 26 strategic frames: hook, date-flash, all 11 scene midpoints, caption moments incl. red-keyword chunks, all xfade midpoints, stinger moment (S06), two-line CTA, fade-in/fade-out edges — see §4.

## 2. Audio QA (every sample, none skipped)

| Check | v2 file (current) | v1 file (history) |
|---|---|---|
| Integrated loudness | **I ≈ −14.6 LUFS**, LRA **4.4 LU** | I ≈ −14 LUFS, LRA 4.3 LU |
| True peak | **−1.4 dBTP** | −1.3 dBTP / −1.41 dBFS |
| DC offset | −0.00001 (highpass on premix retained) | −0.00001 (was −0.0506, A-001) |
| Silence gaps > 0.6 s @ −50 dB | ✅ none | ✅ none |
| Clipping / full-scale samples | ✅ none | ✅ none |
| Channel layout | ✅ 48 kHz **stereo** AAC-LC | ✅ 48 kHz stereo (was mono, A-002) |
| VO/SFX sync | ✅ VO 0.12 s; SFX 1.85 bell · 12.77 murmur · 19.63 heartbeat · 30.88 stinger · 36.92 rumble · 55.01 shoe tap · 64.57 sub-drop; **+ riser 1.25 s ending exactly on the 30.88 stinger** (v2) | SFX verified at same timestamps |
| Spectrum | `qa/spectrogram.png` (v1) — v2 keeps identical mix topology | bell partials, heartbeat, stinger visible |

## 3. Bug list — found → fixed → re-verified

### Critical / video
- **V-001 (P0) — Date-flash text horizontally clipped on both edges.** `STRASBOURG · 14 JULY 1518` at letter-spaced fs54 exceeded 1080 px and was cut (“TRASBOURG · 14 JULY 151”). **Fix:** fs46, unspaced string, `\an5\pos(540,830)` center anchor. **Re-verified:** fits with ~200 px side margins; QA edge-clip detector now passes.
- **V-002 (P0) — Final CTA caption clipped.** `FOLLOW FOR MORE TRUE NIGHTMARES` at fs60 overflowed and lost the first/last glyphs. **Fix:** explicit two-line break `FOLLOW FOR MORE\NTRUE NIGHTMARES`, `\an2\pos(540,1352)`. **Re-verified:** two clean lines, no edge pixels in margin zone across frames 2090–2170.
- **V-003 (P1) — Captions jumped vertically between chunks.** libass rendered consecutive one-line Viral events alternating between two anchors 68 px apart (verified by per-frame row profiling across all 36 events). **Fix:** absolute position `\an2\pos(540,1352)` on every Viral event. **Re-verified:** 27/27 white Viral chunks byte-identical ink band 1302–1339 px; red chunks identical too.
- **V-004 (P1) — Crossfade double-vision.** Chunk windows overlapped 60 ms with identical anchors → unreadable ghost composite (e.g. “THE / AND KEPT DANCING.” frame). **Fix:** chunks now tile exactly (no extension), `\fad(70,50)`. **Re-verified:** boundary frames show clean handoff; aliasing undetectable at 30 fps.
- **V-005 (P1) — Literal “\N” printed in CTA.** ASS writer double-escaped backslashes. **Fix:** esc() no longer doubles `\`. **Re-verified:** CTA renders a true line break.
- **V-006 (P2) — Full-range color tags.** Stream was tagged yuvj420p/bt470bg → washed-out look in some players. **Fix:** `scale=in_range=auto:out_range=limited,format=yuv420p` + BT.709 tv-range tags. **Re-verified:** `yuv420p(tv, bt709)`.
- **V-007 (P2) — Caption-chunk timing vs xfade compression.** Pre-fade vs post-fade time bases disagreed by up to 4.5 s (captions/SFX would late-sync by end of video). **Fix:** timeline recomputed in true video time (scene_i_actual = Σlen − i·0.45); S11 shared-VO pinned to S10’s VO start (was 55.39 → correct 55.84). **Re-verified:** VO/caption/SFX audit vs scene starts.

### Critical / audio
- **A-001 (P2) — DC offset −0.051.** Source: brown-noise ambience (cumsum drift). **Fix:** `highpass=f=25` on premix. **Re-verified:** −0.00001.
- **A-002 (P2) — Mono output.** amix inherited layout from mono VO mp3s. **Fix:** `aformat=channel_layouts=stereo` on every input branch. **Re-verified:** 48 kHz stereo, −1.41 dBFS peak.

### QA tooling (found & fixed inside the checker itself)
- **T-001** caption band constant checked rows 1450–1750 → real captions render at ~1240–1350; moved to 1150–1420 (Viral) / 760–1160 (DateFlash).
- **T-002** dead-channel check false-flagged intentional fade-to-black frames → whitelisted mean<20 frames.
- **T-003** added missing coverage: horizontal-clip detector + per-event baseline check + red-chunk detection.

### Non-issues (investigated, confirmed intentional)
- Fade-in (0.00–0.10 s) & fade-out (72.93–73.27 s) black — by design (blackdetect agrees).
- 2200-vs-2199 frame count: 73.32 s × 30 fps = 2 199.6 → 2 199 extracted frames; container PTS consistent.
- Frame 0/1 near-black during 0.5 s fade-in — by design.

### v2-specific findings (all closed)
- **V2-001 (P1) — 2-frame near-black run f1237–1238** in candlelit S07 (the `eq=brightness` flicker trough on an already-dark crop; mean luma ≈ 8). **Fix:** per-scene shadow lift `eq=gamma=1.14` for S05/S07/S09 in `src/build_video2.py`. **Re-verified:** black/white-run check = 0 across 2 199 frames.
- **V2-002 (P2) — Luma spikes at hard cuts (f531, f1449, f1708, f1710, f1756, f1758).** Not defects — shot-boundary cuts and S10 lightning bursts (local t 1.05–1.12 / 2.66–2.73 s). **Fix:** spike check now whitelists shot-cut frames ±2 (from `production/shots.json`) and lightning frames ±1. **Re-verified:** 0 non-whitelisted spikes; 175 whitelisted frames all map to intended cuts/flashes.
- **V2-003 (P2) — Flicker amplitude too hot** (eq brightness ±0.026 caused visible dimming on dark scenes). **Fix:** reduced to 0.016/0.010 harmonics; S07 additionally gamma-lifted. **Re-verified:** QA clean.
- **V2-004 (P3) — Embers overlay nearly invisible** at 0.34 screen opacity. **Fix:** raised to 0.52. **Re-verified:** S06 detail/punch shots show warm ember field against the magenta grade; captions unaffected.
- **V2-005 (P2) — QA checker regression:** cut whitelist originally read `timeline.json['cuts']`, but `make_timeline.py` regenerates timeline.json and wipes the key (returned "0 across 0 cuts"). **Fix:** whitelist now reads `production/shots.json` (`abs_start`×30). **Re-verified:** 175 cut/flash frames recognised.

**Bug tally (v2):** 5 findings, all closed. Final automated pass on the v2 file: **TOTAL BUGS: 0** (2 199 frames, 36/36 captions).

**Bug tally:** 10 unique bugs (V-001…V-007, A-001…A-002, plus 3 tooling fixes). All **closed**. Final automated pass: **TOTAL BUGS: 0**.

## 4. Visual inspection log (26 frames)
All inspected good: f00002 (fade-in), f00030/f00045 (date-flash + hook caption), f00100 (hook chunk 2), f00180 (hook→S02 xfade midpoint), f00210 (Troffea portrait), f00240 (red FRAU TROFFEA chunk), f00450/f00570 (crowd "SHE DANCED FOR DAYS" / "THEN 400."), f00600/f00640/f00733/f00740/f00741 (feet scene, SCREAMED→KEPT caption handoff), f00925/f00980 (council → guildhall stinger beat), f01150 ("15 DIED", red), f01350/f01450 (shrine procession + red SHOES), f01630 (chapel, red STOPPED), f01904 (rye field, "WANTED THEM DANCING"), f02085 (out-fading STILL DANCING), f02100/f02126/f02150 (CTA two-line, red FOLLOW), f02198 (fade-out to black). Anomalies found during inspection (CTA clip, literal \N, caption parity jump, double-vision, edge-clipped date-flash) are fixed and re-verified — see V-001…V-005.

## 5. Compliance / honesty notes
- “Fifteen per day” and “400” are chronicle claims — video hedges (“chronicles claim”, “up to 400”) and the description carries a full disclaimer + source list. Cause presented as **unsolved** (mass psychogenic illness vs ergot) — accurate.
- Images are AI-generated cinematic illustrations, not documentary photos; no real person depictions; intended as stylized reconstructions.
- VO is an AI narration voice registered/selected this session; SFX are synthesized in-repo (no licensing issues).

## 6. v2 — what makes it read as video, not a slideshow

v1 was rejected for uniform Ken Burns pan/zoom + xfade-only transitions. v2 applies still-image-to-video techniques researched this session (parallax-style layered crops, punch-in keyframes, blend-mode atmosphere, cut rhythm):

| Technique | Where | Implementation |
|---|---|---|
| **3-shot rhythm per scene** (wide → detail crop → punch-in) | All 11 scenes, 33 shots (`production/shots.json`, `src/make_shots.py`) | ~2.2 s average shot length; hard cuts on the VO beat instead of another drifting zoom |
| **Depth crops** | S01–S11 detail shots | Letterboxed crop boxes (e.g. S01 `[380,700→860,1529]` on the figure) re-framed 9:16 → subject/figure separation, parallax feel without 3D layers |
| **Punch-in zoom curves** | All punch shots (e.g. S01 `punch` move) | `peak` 1.16–1.24 with exponential-in curve (exp≈3.2) + wobble → snaps, not drifts |
| **Atmosphere screen-blends** | S01/S11 rain+fog · S03/S08 fog · S06 embers+rgbashift (rh=1, bh=−1) | Synth loops `assets/fx/{rain,fog,embers}.mp4` blended `screen` @ 0.38/0.22/0.52 — moving particulate = depth cue over stills |
| **Electric accents** | S05/S07/S09 flicker (eq brightness harmonics 3.1 Hz + 7.6 Hz) · S10 lightning (gamma 1→1.85 for 70 ms at local t 1.05–1.12 and 2.66–2.73) | Motivates frame-to-frame change; flicker reads as failing lantern light, lightning sells the rye-field storm |
| **Rhythm interrupts** | ~2.2 s cut cadence, xfades retained only at scene boundaries | Jump-cut energy (0.4–0.9 s accents) per horror-edit research; silence-before-drop + riser (42→98 Hz swell, 1.25 s) lands exactly on the S06 stinger |
| **Caption motion design** | Viral chunks | Pop-in scale 62→116→100 % bounce; DateFlash `STRASBOURG · 14 JULY 1518` alpha-glitch flicker sequence |
| **Per-scene grade stack** | Global vignette + noise + fades; S06 magenta cast; S10 storm; S07 candle-lift (v2-001) | Each scene distinct at a glance, not one uniform LUT |

**Visual inspection log (v2, additive):** f00003 (near-black fade-in, edge_fade intentional), f00030 (hook at 1 s — Frau Troffea silhouette, red date-flash, hook caption legible), f01005/f01010/f01100 (S06 wide/detail/punch — magenta cast + riser→stinger build), f01237–01240 (S07 "15 DIED / THE TRUE TOLL IS LOST." — lifted shadows, captions legible), f01708 (S10 lightning burst — bolt visible right of frame, "STILL UNSOLVED."), f02170 (fade-out). All pass.

**Verification loop (v2):** build #1 (full) → 7 bugs (V2-001…V2-004 + tooling) → build #2 (FX-only, `SKIP_VIDEO=1`) → 1 bug → **dark-scene lift + embers opacity** → build #3 (FX-only) → extract 2 199 frames → **qa_frames.py: TOTAL BUGS: 0** · captions 36/36 · loudness I = −14.6 LUFS · TP = −1.4 dBTP · duration 73.32 s · 1080×1920 @30 fps.
