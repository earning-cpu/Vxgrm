# Vxgrm — द डांसिंग प्लेग 1518 (सच डरावनी कहानी) — YouTube Short (Hindi v3)

A real, documented, still-unsolved horror mystery turned into a fact-checked, **Hindi-first, India-targeted** viral YouTube Short.

**🎥 Final video (Hindi):** `output/dancing-plague-1518-true-story-short.mp4` — 65.8 s, 1080×1920 (9:16), 30 fps, H.264 + AAC stereo, ~35 MB (36,063,368 bytes)

> **v3 (2026-11-22, Hindi India cut)** — full re-voice and re-edit for Indian audiences after v2 (English) delivered. Hindi Devanagari narration (voice-01, hi-IN) with **per-chunk measured caption sync** (zero latency by construction — caption windows = measured clip windows), **karaoke `\k` word-sweep** synced to every spoken word, Hinglish keywords in accent red, 2026-style silent-first design (progress line, ≥fs54, thumb-zone placement). SFX are **sidechain-ducked under narration** — never mask the voice. Includes all v2 craft (33 shots, wide→detail→punch, rain/fog/embers, flicker, lightning, stinger impact flash + screen shake, caption pop-in bounce, DateFlash glitch). See `production/script_hi.md`, `src/make_timeline_hi.py`, `research/hindi-shorts-trends-2026.md`. atempo 1.22 (pitch-preserved) used for tight ~66 s runtime.

**v2 (English)** — shot-based rebuild that killed the "slide show" look. Retained in git history (`5c4a342`); v3 used a fresh Hindi VO so the two cuts are independent.

## What this is

| Step | Deliverable |
|---|---|
| Topic research & multi-source fact-check | `research/fact-check-dancing-plague-1518.md` |
| Viral craft research (English) | `research/viral-horror-shorts-playbook.md` |
| India/Hindi 2026 Shorts trend research | `research/hindi-shorts-trends-2026.md` |
| Script v3 (Hindi, verbatim chunks, karaoke map) | `production/script_hi.md` |
| Upload pack (Hindi titles/description/tags) | `production/upload-pack.md` |
| Master timeline + ASS captions (26 events) | `production/timeline.json`, `production/captions.ass` |
| Shot plan (33 shots, 3/scene) | `production/shots.json` |
| Hindi VO chunks (25 clips, voice-01) | `assets/audio/hi/c01.mp3` … `c25.mp3` |
| QA/QC — every frame at 30 fps checked + captions, audio QA | `qa/QA-QC-REPORT.md` (+ `qa/frame-metrics.csv`, `qa/spectrogram.png`) |
| Pipeline | `src/` (synth_sfx → synth_overlays → prep_images → make_shots → make_timeline_hi → build_video2 → qa_frames) |

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install pillow numpy imageio imageio-ffmpeg
.venv/bin/python src/synth_sfx.py        # synthesize SFX/ambience (numpy)
.venv/bin/python src/synth_overlays.py   # synthesize rain/fog/embers FX loops
.venv/bin/python src/prep_images.py      # crop 9:16 + horror grade
.venv/bin/python src/make_timeline_hi.py # measured chunk timings + captions.ass + timeline.json
.venv/bin/python src/make_shots.py       # shot plan -> production/shots.json
.venv/bin/python src/build_video2.py     # shots -> FX -> xfade -> grade(shake/flash/progress) -> sidechain-ducked mix -> captions
.venv/bin/python src/qa_frames.py        # exhaustive per-frame QA (after ffmpeg -vf fps=30 extraction)
```

`build_video2.py` honors `SKIP_VIDEO=1` to reuse shots/scenes (FX→grade→mix→captions only). `DEBUG_MIX=1` prints loudnorm diagnostics. `qa_frames.py` whitelists hard shot-cut frames (±2, from `production/shots.json`), S10 lightning bursts (±1) and the stinger impact flash (±1).

## Fact-check summary

Event is real (Strasbourg Ratsprotokolle, physician notes, sermons, chronicles). Claims hedged where disputed: participant count 50–400 (Britannica: up to 400), death toll unknown ("15/day" is a chronicle claim — the narration scopes it under "कुछ क्रोनिकल्स का दावा है"), cause unsolved (mass psychogenic illness — Waller; vs ergot poisoning). See the dossier for claim-by-claim sources.

## Credits & disclaimers

AI-generated cinematic illustrations (no documentary photos; not depicting real identifiable persons). AI Hindi narration voice (voice-01, hi-IN) selected this session. SFX synthesized in-repo; Noto Sans Devanagari font (SIL OFL) bundled in `assets/fonts/`. Historical content fact-checked from ≥7 independent sources; disputed claims are hedged, never stated as fact. Educational/entertainment use; horror dramatization of real events.
