# Visual-first edit: broader review

## Scope
Reviewed 80 evenly spaced frames of `burari_visual_horror.mp4` in four contact sheets, one every 0.5 seconds from 0.0 to 39.5 seconds. The time labels refer to sampling intervals; frames were decoded with the ffmpeg fps filter. This is a broader visual spot check, not independent visual inspection of all 1,200 frames. Also compared all 1,200 old/new frames numerically at 30 fps using 135 × 240 downscaled luma samples; see `visual_review_frame_metrics.csv`.

## Findings and changes
- **0–7.4 s:** Door, lane, stairs and hallway create a clear sequence with minimal captions. No change made to preserve the opening.
- **7.4–14 s:** The same night lane used near the beginning returns for the 2018 date. Replaced 9.1–11.4 s with a separate, lighter morning-street illustration, to distinguish the date/discovery beat from the hook.
- **14–25.7 s:** Several adjacent scenes repeat similar diary and desk imagery. Replaced 19.8–22 s with an investigator comparing documents, and 22–24 s with a quieter notebook-and-window scene. These are illustrative, not records of actual evidence or events.
- **25.7–34.5 s:** File/clock/stairs remain. They support closure and uncertainty; original short captions retained.
- **34.5–40 s:** Hallway and a ceiling fan created an ending that leaned toward horror imagery rather than remembrance. Replaced with a diya at a window, keeping the two short closing captions.
- **Text:** Original minimal text retained elsewhere. The replacement scenes reproduce their corresponding short captions and the illustrative-visuals label. Three of the replacement sections (10, 20.5 and 38 s) were visually checked after rendering.

## Technical comparison
The new 40-second master contains 1,200 frames at 30 fps. All 1,200 pairs of old/new frames were decoded and compared; no new frame had a mean sampled luminance below 20/255. 360 frames had a mean absolute old/new luma difference greater than 5/255, reflecting the replaced segments. Metrics quantify changes and dark pixels; they cannot judge visual meaning, readability, caption/audio synchronization or viewer interest.

## Remaining limitations
The video uses animated AI-generated stills, not filmed action. Visual inspection was limited to the 80 original samples and three revised samples, not every frame. Audio was copied from the previous version and was not re-recorded or independently transcribed for this pass. The short captions are a compressed paraphrase, not a full transcript. No audience retention data is available; performance should be assessed after publication.
