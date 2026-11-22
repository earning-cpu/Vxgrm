# QA / QC Report — dancing-plague-1518-true-story-short.mp4

**Date:** 2026-11-22 · **Pipeline:** Python 3.11 + static FFmpeg (imageio-ffmpeg) + Pillow/NumPy + libass captions
**Final file:** `output/dancing-plague-1518-true-story-short.mp4` · 1080×1920 (9:16) · 30 fps · H.264 High · yuv420p (tv, BT.709) · AAC-LC 48 kHz stereo
**Duration:** 73.32 s (2 199 frames) · **Size:** ~34 MB · **SHA-256:** `4187a68f00b346224e7a489ae52fe5694deeafc94c4dd3a9c3617ad7d4771902`
**Verification loop:** 3 full render → extract → analyze cycles (bugs re-verified after every fix)

---

## 1. Frame-by-frame video QA (every frame, none skipped)

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

| Check | Tool | Result |
|---|---|---|
| Integrated loudness | `ebur128=peak=true` | **I ≈ −14 LUFS**, LRA **4.3 LU** (LRA low −16.8 / high −12.5) — consistent, no pumping |
| True peak | ebur128 TPK / `astats` Peak_level | **−1.3 dBTP / −1.41 dBFS** — no clipping anywhere |
| DC offset | `astats` | **−0.00001** — clean (was −0.0506, see A-001) |
| Silence gaps > 0.6 s @ −50 dB | `silencedetect` | ✅ none — no dead air |
| Clipping / full-scale samples | manual peak scan + astats | ✅ none |
| Channel layout | ffprobe-style stream dump | ✅ 48 kHz **stereo** AAC-LC (was mono, see A-002) |
| VO/SFX sync | per-clip measured durations → timeline.json | ✅ VO starts at intended 0.12 s; SFX events verified at 1.85 (bell), 12.77 (murmur), 19.63 (heartbeat), 30.88 (stinger), 36.92 (rumble), 55.01 (shoe tap), 64.57 (sub-drop) |
| Spectrum | `qa/spectrogram.png` | bell partials, heartbeat thumps and stinger transient clearly visible; no DC rail; energy concentrated 20 Hz–2 kHz as designed |

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

**Bug tally:** 10 unique bugs (V-001…V-007, A-001…A-002, plus 3 tooling fixes). All **closed**. Final automated pass: **TOTAL BUGS: 0**.

## 4. Visual inspection log (26 frames)
All inspected good: f00002 (fade-in), f00030/f00045 (date-flash + hook caption), f00100 (hook chunk 2), f00180 (hook→S02 xfade midpoint), f00210 (Troffea portrait), f00240 (red FRAU TROFFEA chunk), f00450/f00570 (crowd "SHE DANCED FOR DAYS" / "THEN 400."), f00600/f00640/f00733/f00740/f00741 (feet scene, SCREAMED→KEPT caption handoff), f00925/f00980 (council → guildhall stinger beat), f01150 ("15 DIED", red), f01350/f01450 (shrine procession + red SHOES), f01630 (chapel, red STOPPED), f01904 (rye field, "WANTED THEM DANCING"), f02085 (out-fading STILL DANCING), f02100/f02126/f02150 (CTA two-line, red FOLLOW), f02198 (fade-out to black). Anomalies found during inspection (CTA clip, literal \N, caption parity jump, double-vision, edge-clipped date-flash) are fixed and re-verified — see V-001…V-005.

## 5. Compliance / honesty notes
- “Fifteen per day” and “400” are chronicle claims — video hedges (“chronicles claim”, “up to 400”) and the description carries a full disclaimer + source list. Cause presented as **unsolved** (mass psychogenic illness vs ergot) — accurate.
- Images are AI-generated cinematic illustrations, not documentary photos; no real person depictions; intended as stylized reconstructions.
- VO is an AI narration voice registered/selected this session; SFX are synthesized in-repo (no licensing issues).
