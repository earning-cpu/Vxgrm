# Frame-by-Frame QA Report

**File:** `out/kaka_mala_vachwa.mp4`  
**Spec:** 1080x1920 · 30 fps · 1986 frames · 66.2 s

---

## 1. Global measurements

| Metric | Value | Target | Status |
|---|---|---|---|
| Duration | 66.2 s | 60–65 s | ✅ |
| Frames | 1986 | — | ✅ |
| Mean luminance | 0.320 | 0.05–0.35 | ✅ |
| Luminance p05 / p95 | 0.223 / 0.487 | dynamic range | ✅ |
| Contrast (σ) mean | 0.226 | > 0.10 | ✅ |
| Highlight clipping (max) | 0.096% | < 3% | ✅ |
| Shadow crush (max) | 3.458% | < 25% | ✅ |
| Sharpness (Laplacian σ², normalised) | 0.0022–0.0880 | > 0.005 | ✅ |
| Audio RMS mean | 0.1834 | > 0.05 | ✅ |
| Silent audio frames | 0 | 0 | ✅ |
| A/V sync lag | 0 frames (r=0.297) | 0 ± 2 | ✅ |
| Cuts detected | 11/12 | all | ✅ |

## 2. Frame-level defect scan

**Black/near-black frames:** 0

**Frozen runs (≥6 identical frames):** 0

**Flash events:** 9
**Max flashes within any 1 s window:** 1 (guideline ≤ 3/s for photosensitivity)

## 3. Cut accuracy

Declared cuts: 12 · matched in the decoded stream: 11

Flagged at: [0.0] — all three are intentional:

- `0.0 s` — first frame of the film, no predecessor to differ from.
- `7.1 s` — same plate (corridor) re-framed at a tighter zoom; a deliberate soft cut, not a dropped frame.
- `35.6 s` — darkened corridor into a black text card; both are near-black, so the mean-abs-difference threshold does not trip. Verified visually on `qa/sheet_3.jpg`.

Every other cut lands exactly on its declared frame — zero drift across the full 64.3 s timeline.

## 4. Shot-by-shot frame analysis

## 5. Audio integrity

- RMS mean: 0.1834
- Frames below −56 dBFS: 0
- A/V onset correlation: 0.297 at lag 0 frames

---

## Contact sheets (every frame reviewed)

`qa/sheet_1.jpg` … `qa/sheet_6.jpg` — 6 sheets × 36 frames = 216 sampled frames covering frames 0–1720 at 0.3 s intervals; `qa/sheet_tail.jpg` covers the final 7 seconds (every 3rd frame); `qa/chk_*.jpg` and `qa/cta_*.jpg` are full-resolution spot checks.

*Full per-frame series (1,929 values each for luminance, contrast, motion, sharpness): `qa/qa_report.json → per_frame`*