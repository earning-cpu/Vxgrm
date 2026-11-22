# Vxgrm — The Dancing Plague of 1518 (True Horror Story) — YouTube Short

A real, documented, still-unsolved horror mystery turned into a fact-checked, viral-format YouTube Short.

**🎥 Final video:** `output/dancing-plague-1518-true-story-short.mp4` — 73.3 s, 1080×1920 (9:16), 30 fps, H.264 + AAC stereo, ~34 MB

## What this is

| Step | Deliverable |
|---|---|
| Topic research & multi-source fact-check | `research/fact-check-dancing-plague-1518.md` |
| Viral Short craft research (script/edit/captions/SFX/VFX) | `research/viral-horror-shorts-playbook.md` |
| Script (4-beat spine, VO-verbatim, caption chunks) | `production/script.md` |
| Upload pack (titles, description, tags, pinned comment) | `production/upload-pack.md` |
| Master timeline + ASS captions | `production/timeline.json`, `production/captions.ass` |
| QA/QC — **every frame at 30 fps checked**, audio QA, bug list + fixes | `qa/QA-QC-REPORT.md` (+ `qa/frame-metrics.csv`, `qa/spectrogram.png`) |
| Full source pipeline | `src/` (synth_sfx → make_timeline → prep_images → build_video → qa_frames) |

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install pillow numpy imageio imageio-ffmpeg
.venv/bin/python src/synth_sfx.py        # synthesize SFX/ambience (numpy)
.venv/bin/python src/prep_images.py      # crop 9:16 + horror grade
.venv/bin/python src/make_timeline.py    # timeline.json + captions.ass
.venv/bin/python src/build_video.py      # render segments → xfade → grade → mix → burn captions
.venv/bin/python src/qa_frames.py        # exhaustive per-frame QA (after ffmpeg -vf fps=30 extraction)
```

## Fact-check summary

Event is real (Strasbourg Ratsprotokolle, physician notes, sermons, chronicles). Claims hedged where disputed: participant count 50–400 (Britannica: up to 400), death toll unknown ("15/day" is a chronicle claim), cause unsolved (mass psychogenic illness — Waller; vs ergot poisoning). See the dossier for claim-by-claim sources.

## Credits & disclaimers

AI-generated cinematic illustrations (no documentary photos; not depicting real identifiable persons). AI narration voice selected this session. SFX synthesized in-repo. Fonts: DejaVu (system). Historical content fact-checked from ≥7 independent sources; disputed claims are hedged, never stated as fact. Educational/entertainment use; horror dramatization of real events.
