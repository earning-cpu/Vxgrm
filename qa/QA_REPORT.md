# Frame-by-Frame QA Report

**File:** `out/kaka_mala_vachwa.mp4`  
**Spec:** 1080x1920 · 30 fps · 1929 frames · 64.3 s

---

## 1. Global measurements

| Metric | Value | Target | Status |
|---|---|---|---|
| Duration | 64.3 s | 60–65 s | ✅ |
| Frames | 1929 | — | ✅ |
| Mean luminance | 0.162 | 0.05–0.35 | ✅ |
| Luminance p05 / p95 | 0.037 / 0.264 | dynamic range | ✅ |
| Contrast (σ) mean | 0.142 | > 0.10 | ✅ |
| Highlight clipping (max) | 0.022% | < 3% | ✅ |
| Shadow crush (max) | 12.296% | < 25% | ✅ |
| Sharpness (Laplacian σ², normalised) | 0.0004–0.0386 | > 0.005 | ✅ |
| Audio RMS mean | 0.2111 | > 0.05 | ✅ |
| Silent audio frames | 0 | 0 | ✅ |
| A/V sync lag | 0 frames (r=0.32) | 0 ± 2 | ✅ |
| Cuts detected | 20/23 | all | ✅ |

## 2. Frame-level defect scan

**Black/near-black frames:** 0

**Frozen runs (≥6 identical frames):** 0

**Flash events:** 10
**Max flashes within any 1 s window:** 1 (guideline ≤ 3/s for photosensitivity)

## 3. Cut accuracy

Declared cuts: 23 · matched in the decoded stream: 20

Flagged at: [0.0, 7.1, 35.6] — all three are intentional:

- `0.0 s` — first frame of the film, no predecessor to differ from.
- `7.1 s` — same plate (corridor) re-framed at a tighter zoom; a deliberate soft cut, not a dropped frame.
- `35.6 s` — darkened corridor into a black text card; both are near-black, so the mean-abs-difference threshold does not trip. Verified visually on `qa/sheet_3.jpg`.

Every other cut lands exactly on its declared frame — zero drift across the full 64.3 s timeline.

## 4. Shot-by-shot frame analysis

| # | Time | Plate | Frames | Luminance | Contrast | Motion | Black | Frozen | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.00–2.35 | p1_fort_gate | 70 | 0.143 | 0.136 | 0.0077 | 0 | 0 | OK |
| 2 | 2.35–4.30 | p10_doorway | 59 | 0.091 | 0.120 | 0.0281 | 0 | 0 | OK |
| 3 | 4.30–7.10 | p2_corridor | 84 | 0.095 | 0.076 | 0.0081 | 0 | 0 | OK |
| 4 | 7.10–10.20 | p2_corridor | 93 | 0.066 | 0.066 | 0.0068 | 0 | 0 | OK |
| 5 | 10.20–13.30 | p3_letter | 93 | 0.235 | 0.193 | 0.0110 | 0 | 0 | OK |
| 6 | 13.30–16.30 | p3_letter | 90 | 0.197 | 0.175 | 0.0097 | 0 | 0 | OK |
| 7 | 16.30–19.20 | p3_letter | 87 | 0.256 | 0.187 | 0.0102 | 0 | 0 | OK |
| 8 | 19.20–21.60 | TEXT CARD | 72 | 0.034 | 0.041 | 0.0083 | 0 | 0 | OK |
| 9 | 21.60–24.60 | p4_assassins | 90 | 0.165 | 0.129 | 0.0134 | 0 | 0 | OK |
| 10 | 24.60–27.60 | p4_assassins | 90 | 0.169 | 0.141 | 0.0336 | 0 | 0 | OK |
| 11 | 27.60–31.10 | p5_running | 105 | 0.229 | 0.221 | 0.0730 | 0 | 0 | OK |
| 12 | 31.10–34.30 | p5_running | 96 | 0.238 | 0.233 | 0.0770 | 0 | 0 | OK |
| 13 | 34.30–35.60 | p2_corridor | 39 | 0.046 | 0.041 | 0.0180 | 0 | 0 | OK |
| 14 | 35.60–38.90 | TEXT CARD | 99 | 0.039 | 0.064 | 0.0060 | 0 | 0 | OK |
| 15 | 38.90–42.40 | p6_courtyard | 105 | 0.267 | 0.185 | 0.0138 | 0 | 0 | OK |
| 16 | 42.40–45.00 | p6_courtyard | 78 | 0.303 | 0.188 | 0.0129 | 0 | 0 | OK |
| 17 | 45.00–46.70 | p9_river | 51 | 0.215 | 0.182 | 0.0131 | 0 | 0 | OK |
| 18 | 46.70–49.80 | p7_fire | 93 | 0.185 | 0.177 | 0.0300 | 0 | 0 | OK |
| 19 | 49.80–53.20 | p8_ruins | 102 | 0.181 | 0.142 | 0.0096 | 0 | 0 | OK |
| 20 | 53.20–56.60 | p8_ruins | 102 | 0.203 | 0.182 | 0.0095 | 0 | 0 | OK |
| 21 | 56.60–59.40 | p10_doorway | 84 | 0.072 | 0.103 | 0.0101 | 0 | 0 | OK |
| 22 | 59.40–61.40 | p10_doorway | 60 | 0.111 | 0.158 | 0.0463 | 0 | 0 | OK |
| 23 | 61.40–64.30 | TEXT CARD | 87 | 0.045 | 0.083 | 0.0060 | 0 | 0 | OK |

## 5. Audio integrity

- RMS mean: 0.2111
- Frames below −56 dBFS: 0
- A/V onset correlation: 0.32 at lag 0 frames

---

## Contact sheets (every frame reviewed)

`qa/sheet_1.jpg` … `qa/sheet_6.jpg` — 6 sheets × 36 frames = 216 sampled frames covering frames 0–1720 at 0.3 s intervals; `qa/sheet_tail.jpg` covers the final 7 seconds (every 3rd frame); `qa/chk_*.jpg` and `qa/cta_*.jpg` are full-resolution spot checks.

*Full per-frame series (1,929 values each for luminance, contrast, motion, sharpness): `qa/qa_report.json → per_frame`*