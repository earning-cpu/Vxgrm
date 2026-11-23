# Burari horror short: edit and frame review

## Deliverables
- `burari_horror_30fps.mp4`: 40 seconds, 540 × 960, 30 fps, Hindi/Hinglish narration.
- `horror_30fps_frames.zip`: 1,200 sequential JPEG frames, `frame_0000.jpg` through `frame_1199.jpg`, one for every 1/30 second. JPEG quality is reduced for a manageable download; the MP4 is the master.
- `frame_comparison.csv`: one row per frame, comparing the new master to `burari_hinglish_multishot.mp4` sampled at 30 fps.

## What was changed
The hook, investigation and ending now use an immediate solid title on a darker backing, rather than starting with a translucent title over a potentially bright image. The date has a dedicated callout; the diary/investigation section has a moving evidence marker. Cuts between 21 illustrative shots remain linked to narrative beats. The 30 fps render uses eased camera and graphic movement, a subdued cut wipe, and a low atmospheric sound bed. The tone is darker but avoids invented paranormal claims or graphic depictions.

## Frame-by-frame methodology
Both versions were decoded at 30 fps to 540 × 960 RGB. The older 24 fps master was sampled at 30 fps for temporal alignment; this does not add real motion detail. For every frame, the CSV records time, intended shot/subject, average luma, fraction of pixels near black, mean luma difference from the preceding frame, and mean luma difference against the old frame. Luma measurements were computed on a 4× spatial subsample; differences are pixel-wise absolute differences in luma. A flag identifies frames with mean luma below 20/255.

Results: 1,200 pairs analyzed; no new frame has a full-frame mean luma below 20. Mean luma changed from 51.45/255 to 45.04/255; average adjacent-frame luma change is 3.22 in the old version and 3.30 in the new version. These numbers describe image intensity/change, not readability, motion quality, or viewer retention. Whole-frame brightness alone cannot establish text contrast. Frame descriptions are planned shot labels, not an independent semantic interpretation of each image.

## Visual spot check and fixes
A contact sheet of 12 time points in each version was visually examined (0.5, 3.5, 7.5, 11.5, 14.5, 17.5, 20.5, 24.5, 26.5, 30.5, 34.5 and 38 seconds). In the old edit, titles briefly faded against the image at several scene entrances, notably the date and ending. The revised edit starts titles at full opacity over a dark panel. The date was present in small text; it now also has a larger date card. The lower caption band was strengthened to improve separation. These are targeted changes, not proof that every visual problem is fixed.

## Shot map
| Time | Intended visual beat |
|---|---|
| 0–2.9 | Door and Delhi lane: family and death count |
| 2.9–7.4 | Hall and window: survival question |
| 7.4–11.4 | Clock, lane and closed shop: location and date |
| 11.4–14 | Hall and investigator: discovery |
| 14–19.8 | Diary, writing and investigator: documentary evidence |
| 19.8–25.7 | Analysis desk and case papers: psychological-autopsy possibility |
| 25.7–30.4 | Security camera and folder: closure-report beat |
| 30.4–34.5 | Clock and window: uncertainty about final moments |
| 34.5–40 | Candles and lamp: remembrance |

All visuals are fictional illustrations, not evidence photographs or reconstructions of verified events. A camera or shop shown on screen must not be read as a depiction of an actual camera or shop involved in the case.

## Limits and further validation
The 1,200 frames received automated numerical analysis; only the 12 listed time points were visually spot-checked. No human or vision model independently interpreted every frame, and the CSV cannot detect all clipping, misleading imagery, audio issues, or caption synchronization problems. The edit is animated still imagery and motion graphics, not generated live-action footage. Actual audience retention and whether the video is 'trendy' cannot be established without publication and audience data. A further pass should check spoken words against captions at normal speed and review readability on a phone.

## Research references
- Reporting on the discovery and diaries: https://www.bbc.com/news/world-asia-india-44844617 and https://indianexpress.com/article/cities/delhi/11-people-found-dead-in-burari-at-family-home-notes-on-surrendering-life-5241624/
- Police closure report and psychological-autopsy nuance: https://timesofindia.indiatimes.com/city/delhi/burari-deaths-police-closure-report-mentions-no-foul-play/articleshow/87169901.cms
- Audience retention is measured after publication, including dips and spikes: https://support.google.com/youtube/answer/9314415?hl=en
- Keyframe interpolation and easing: https://helpx.adobe.com/premiere/desktop/add-video-effects/control-effects-and-transitions-using-keyframes/change-keyframe-interpolation-method.html
