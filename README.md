# कुलधरा — Hindi Horror YouTube Short

A vertical, cinematic Hindi horror short built around the real abandoned settlement of Kuldhara near Jaisalmer, Rajasthan.

## Deliverable

- **`Kuldhara_Hindi_Horror_Short.mp4`** — 9:16 portrait, 1080 × 1920, 30 fps, approximately 46.5 seconds, Hindi narration, burned-in Devanagari captions, and original synthetic ambience.
- `assets/captions.srt` — editable subtitle track for YouTube.
- `assets/script-hi.md` — narration transcript plus upload title, description, hashtags, and pinned-comment suggestion.

## Historical framing

Kuldhara is a real abandoned village. The story about Diwan Salim Singh, the village head's daughter, an overnight departure, and a curse is presented as **local legend**, not verified fact. The video's narration explicitly says that supernatural claims are folklore and that the precise reason for the settlement's decline is uncertain. The visuals are AI-generated atmospheric recreations, not archival photographs or documentary footage.

The legend is recounted by Rajasthan Tourism: [Kuldhara — Rajasthan Tourism](https://www.tourism.rajasthan.gov.in/kuldhara.html).

## Re-render

Run `python3 render_kuldhara_short.py` from this folder. The renderer needs FFmpeg with `libx264` and `libass` support; it uses a system `ffmpeg` if available, or the `imageio-ffmpeg` Python package as a fallback. The Devanagari font in `assets/fonts/` is Noto Sans Devanagari Bold and is distributed under the SIL Open Font License (`assets/NotoSansDevanagari-OFL.txt`).
