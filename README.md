# Vxgrm — The Dancing Plague of 1518 (True Horror Story) — YouTube Short

A real, documented, still-unsolved horror mystery turned into a fact-checked, viral-format YouTube Short.

**🎥 Final video:** `output/dancing-plague-1518-true-story-short.mp4` — 73.3 s, 1080×1920 (9:16), 30 fps, H.264 + AAC stereo, ~39 MB (v2 — shot-based, not a slideshow)

> **v2 (2026-11-22):** rebuilt after v1 was rejected as a "slide show". v2 uses a **shot-based edit, not uniform Ken Burns**: 33 shots (3 per scene — wide → detail crop → punch-in), hard beat-synced cuts (~2.2 s avg shot length), cropped depth shots with peak-zoom curves, screen-blend atmospheric FX (rain, fog, embers), per-scene flicker/lightning accents, caption pop-in bounce + DateFlash glitch, and a synthesized riser that lands on the stinger. See `production/shots.json` and `src/make_shots.py` / `src/build_video2.py` / `src/synth_overlays.py`.

## What this is

| Step | Deliverable |
|---|---|
| Topic research & multi-source fact-check | `research/fact-check-dancing-plague-1518.md` |
| Viral Short craft research (script/edit/captions/SFX/VFX) | `research/viral-horror-shorts-playbook.md` |
| Script (4-beat spine, VO-verbatim, caption chunks) | `production/script.md` |
| Upload pack (titles, description, tags, pinned comment) | `production/upload-pack.md` |
| Master timeline + ASS captions | `production/timeline.json`, `production/captions.ass` |
| Shot plan v2 (33 shots, 3/scene) | `production/shots.json` |
| QA/QC — **every frame at 30 fps checked**, audio QA, bug list + fixes | `qa/QA-QC-REPORT.md` (+ `qa/frame-metrics.csv`, `qa/spectrogram.png`) |
| Full source pipeline | `src/` (synth_sfx → synth_overlays → prep_images → make_shots → make_timeline → build_video2 → qa_frames) |

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install pillow numpy imageio imageio-ffmpeg
.venv/bin/python src/synth_sfx.py        # synthesize SFX/ambience (numpy)
.venv/bin/python src/synth_overlays.py   # synthesize rain/fog/embers FX loops (screen-blend)
.venv/bin/python src/prep_images.py      # crop 9:16 + horror grade
.venv/bin/python src/make_timeline.py    # timeline.json + captions.ass
.venv/bin/python src/make_shots.py       # shot plan (33 shots) -> production/shots.json
.venv/bin/python src/build_video2.py     # shots -> scene concat -> FX -> xfade -> grade -> mix -> burn captions
.venv/bin/python src/qa_frames.py        # exhaustive per-frame QA (after ffmpeg -vf fps=30 extraction)
```

`build_video2.py` honors `SKIP_VIDEO=1` to reuse already-rendered shots/scenes in `assets/segments2/` (FX→mix→caption pass only). `qa_frames.py` whitelists hard-cut frames (±2) read from `production/shots.json` and S10 lightning-burst frames (±1).

## Fact-check summary

Event is real (Strasbourg Ratsprotokolle, physician notes, sermons, chronicles). Claims hedged where disputed: participant count 50–400 (Britannica: up to 400), death toll unknown ("15/day" is a chronicle claim), cause unsolved (mass psychogenic illness — Waller; vs ergot poisoning). See the dossier for claim-by-claim sources.

## Credits & disclaimers

AI-generated cinematic illustrations (no documentary photos; not depicting real identifiable persons). AI narration voice selected this session. SFX synthesized in-repo. Fonts: DejaVu (system). Historical content fact-checked from ≥7 independent sources; disputed claims are hedged, never stated as fact. Educational/entertainment use; horror dramatization of real events.
