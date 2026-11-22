# Viral Horror Shorts — Research Playbook (applied to this video)

Compiled from current 2025–2026 short-form guidance and the documented workflow of viral AI horror channels. Each rule lists how it is actually implemented in this production.

## A. Structure & retention (the 4-beat spine)
Sources: growthos.in (2026), postcrest.com (2025), klap.app (2025), narrationbox.com (2025), virvid.ai (2026).

| Rule | Finding | Implementation |
|---|---|---|
| Hook in 0–2s | Swipe decision is made before conscious processing; stated payoff or contradiction up front. | Opens mid-story: "On July 14th, 1518, a woman in Strasbourg stepped into the street — and began to dance." Plus on-screen date flash `STRASBOURG — 14 JULY 1518` at 0.0s. |
| Context in 2–7s | One sentence of who/what/stakes. No fluff. | "History calls her Frau Troffea. No music. No reason. She danced for days." |
| Payoff = escalation | Use But/Therefore logic; every beat escalates, never "and then… and then". | Troffea → 30 dancers → 400 → city hiring musicians (backfire) → red shoes & shrine → "it never fully stopped". |
| Loop ending | Last line/frame restarts the opening; replays are a top algorithm signal. | Ends on "…and if the plague ever truly ended — rewatch the first frame. It started with one woman." Visual echo of the opening frame + same drone note. |
| Pattern break every 2–4s | Zoom, angle change, text overlay, sound change. | 11 scene changes in ~58s (avg 5.3s, with 3 cuts < 4s); Ken Burns drift on every frame; caption chunks every 1.2–2s; SFX stings at 0s, 17s, 33s, 47s. |
| Length | 20–45s sweet spot; never pad. | ~58s incl. outro title card (within Shorts limit; information-dense, zero dead air). |
| Build for silence | ~85% watched on mute; 6–8 words max on screen; high contrast. | ALL captions ≤ 6 words/chunk, 2-line max, heavy outline. No dependence on audio for comprehension. |
| Breadcrumb lines | Planted re-hooks past drop-off points. | "What happened next made it worse." / "The cure was the catastrophe." at the 2 natural drop-off beats. |
| CTA placement | In caption/description, not a spoken 3s outro. | Spoken CTA = 1.2s ("Follow if you believe…"), placed *inside* the narrative loop, then hard cut to black + title card 1.5s. |

## B. Horror-specific packaging (what viral AI-horror channels do)
Sources: Medium / NoahBourland ("viral horror shorts with free AI tools"), readray.ai (Vexub/CapCut horror course), sendshort.ai, revid.ai.

- **9:16 vertical, 1080×1920** — full-screen immersion, no black bars. ✅ (exported 1080×1920, 30 fps)
- **Image style prompt recipe:** dark lighting, subtle film grain, desaturated grade, cold blue-grey cast with amber highlights, faces half-shadowed, period detail, cinematic 35mm look. ✅ applied to every generated still; graded uniformly in post (vignette + grain + contrast).
- **Fade transitions, not wipes** — horror pacing is slow fades + hard cuts for stingers. ✅
- **Vignette + grain + subtle shake** on the loudest beats. ✅ (ffmpeg vignette/noise; micro-shake on 2 stinger beats)
- **Captions:** "high-retention" clean style, ~35–40pt equivalent relative size, positioned **below center (~65% down)**, bold + shadow/outline to pop on dark footage; no emoji. ✅ (ASS subtitle: DejaVu Sans Bold, white w/ black outline + soft shadow, MarginV ≈ lower third)
- **Voice:** calm, low, unhurried narrator; micro-pauses as tension. ✅ (registered deep narration voice; per-line clips, gaps tuned 0.12–0.35s)
- **Micro-pauses kept** — "cut dead air, but leave micro-pauses for tension". ✅
- **Export 1080p.** ✅ (30 fps as requested; H.264 CRF 20 high quality for review)
- **Titles that pull clicks:** curiosity-gap + specificity ("…the night a town could not stop dancing (real story)"). Draft titles in `production/script.md`.
- **Thumbnail/cover frame:** one focal object — we ship frame-0-compatible cover (Troffea silhouette). ✅

## C. Audio design (SFX/ambience)
Synthesized in-repo (no licensing issues), layered under VO at −18…−22 LUFS relative to voice:

| Layer | Sound | Role |
|---|---|---|
| Ambience | 55 Hz + 55.5 Hz beating drone, slow attack, evolving lowpass | Sub-dread bed from 0s to end |
| Ambience | Brown-noise wind with 8s LFO | 1518 street air |
| Event SFX | Single distant **church-bell toll** at "…1518" | Time anchor, omen |
| Event SFX | **Low rumble + crowd murmur** under "four hundred" montage | Scale |
| Event SFX | **Heartbeat** from "vacant eyes…" to "…bled into their shoes" | Human dread sync |
| Event SFX | **Dissonant string stinger** at "the cure was the catastrophe" | Jump-scare accent (2nd drop-off) |
| Event SFX | Final **bell + sub drop** at last line, resolved into drone | Loop closure |
| Mix | VO-forward, ambience sidechained by silence (gains ramped under VO gaps), true peak ≤ −1.5 dBTP | Broadcast-safe, no clipping |

## D. Caption style spec
- Font: DejaVu Sans Bold (installed system font; stands in for the "Espresso/Infected-style" bold display faces popularized by CapCut/Vexub).
- Case: ALL CAPS. Keywords highlighted in blood-red (`#E5484D`) — date, "could not stop", "400", "fifteen", "never explained".
- Layout: max 2 lines, ≤ 6 words per chunk, centered, baseline ~68% of frame height (clear of the platform UI zone and of faces).
- Timing: chunks timed to the synthesized VO per sentence; fade/slide-in 80 ms.

## E. QA/QC gate (what was actually executed — see qa/QA-QC-REPORT.md)
1. Extract **every frame** at 30 fps; per-frame automated checks: black/blown frames, frozen runs, dead color channels, decode errors, luma spikes.
2. Visual inspection of scene starts/midpoints/caption moments + random sweep.
3. Audio: ebur128 loudness, true peak, silence scan, clipping scan, spectral spot-check.
4. Bug list → fix → re-render → re-verify loop.
