#!/usr/bin/env python3
"""Render the Kuldhara Hindi short from the included stills and narration."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "Kuldhara_Hindi_Horror_Short.mp4"
VOICE = ASSETS / "kuldhara-voiceover-final.mp3"
CAPTIONS = ASSETS / "captions.ass"
FONTS = ASSETS / "fonts"
IMAGES = [
    ASSETS / "scene-01-dusk.jpg",
    ASSETS / "scene-02-lane.jpg",
    ASSETS / "scene-03-door.jpg",
    ASSETS / "scene-04-moon.jpg",
]

FPS = 30
WIDTH = 1080
HEIGHT = 1920
CROSSFADE_FRAMES = 18  # 0.6 seconds
FIRST_SEGMENT_FRAMES = [339, 369, 351]


def find_ffmpeg() -> str:
    """Return an FFmpeg executable, preferring the user's system install."""
    configured = os.environ.get("FFMPEG")
    if configured and Path(configured).is_file():
        return configured
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise SystemExit(
            "FFmpeg is required (with libx264 and libass). Install FFmpeg or run "
            "`python3 -m pip install imageio-ffmpeg`."
        ) from exc


def media_duration(ffmpeg: str, media: Path) -> float:
    """Read a media duration from FFmpeg's input header."""
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(media), "-f", "null", "-"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read duration for {media}:\n{result.stderr[-1500:]}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def filter_path(path: Path) -> str:
    """Escape a path for FFmpeg filter options."""
    return path.resolve().as_posix().replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def main() -> None:
    for required in [VOICE, CAPTIONS, *IMAGES, FONTS / "NotoSansDevanagari-Bold.ttf"]:
        if not required.is_file():
            raise SystemExit(f"Missing required asset: {required.relative_to(ROOT)}")

    ffmpeg = find_ffmpeg()
    duration = media_duration(ffmpeg, VOICE)
    total_frames = round(duration * FPS)
    xfade_seconds = CROSSFADE_FRAMES / FPS
    segment_frames = FIRST_SEGMENT_FRAMES + [
        total_frames + 3 * CROSSFADE_FRAMES - sum(FIRST_SEGMENT_FRAMES)
    ]
    if segment_frames[-1] <= CROSSFADE_FRAMES:
        raise SystemExit("Audio is too short for the configured edit.")

    command = [ffmpeg, "-hide_banner", "-y"]
    for image in IMAGES:
        command += ["-i", str(image)]
    command += ["-i", str(VOICE)]
    command += [
        "-f", "lavfi", "-i",
        f"anoisesrc=color=pink:sample_rate=48000:amplitude=0.16:duration={duration:.3f}",
        "-f", "lavfi", "-i",
        f"sine=frequency=55:sample_rate=48000:duration={duration:.3f}",
    ]

    filters: list[str] = []
    for index, frames in enumerate(segment_frames):
        pan_x = "max(0,min(iw-iw/zoom,iw/2-iw/zoom/2+12*sin(on/120)))"
        pan_y = "max(0,min(ih-ih/zoom,ih/2-ih/zoom/2+18*sin(on/145)))"
        filters.append(
            f"[{index}:v]"
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            "eq=contrast=1.06:saturation=0.91:brightness=-0.015,"
            f"zoompan=z='min(zoom+0.00014,1.07)':x='{pan_x}':y='{pan_y}':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
            "setsar=1,format=yuv420p,setpts=PTS-STARTPTS"
            f"[v{index}]"
        )

    current_label = "v0"
    current_frames = segment_frames[0]
    for index in range(1, len(segment_frames)):
        offset = (current_frames - CROSSFADE_FRAMES) / FPS
        next_label = f"vx{index}"
        filters.append(
            f"[{current_label}][v{index}]"
            f"xfade=transition=fade:duration={xfade_seconds:.3f}:offset={offset:.6f}"
            f"[{next_label}]"
        )
        current_frames += segment_frames[index] - CROSSFADE_FRAMES
        current_label = next_label

    captions_path = filter_path(CAPTIONS)
    fonts_path = filter_path(FONTS)
    filters.append(
        f"[{current_label}]"
        f"subtitles=filename='{captions_path}':fontsdir='{fonts_path}':"
        f"original_size={WIDTH}x{HEIGHT},fps={FPS},format=yuv420p[vout]"
    )

    voice_index = len(IMAGES)
    wind_index = voice_index + 1
    drone_index = voice_index + 2
    filters += [
        f"[{voice_index}:a]asetpts=PTS-STARTPTS,highpass=f=70,lowpass=f=11000,"
        "loudnorm=I=-16:TP=-1.5:LRA=11:linear=true[voice]",
        f"[{wind_index}:a]highpass=f=150,lowpass=f=1700,tremolo=f=0.14:d=0.7,"
        f"volume=0.34,afade=t=out:st={max(0.0, duration - 1.9):.3f}:d=1.8[wind]",
        f"[{drone_index}:a]lowpass=f=95,tremolo=f=0.11:d=0.5,volume=0.18,"
        f"afade=t=out:st={max(0.0, duration - 1.9):.3f}:d=1.8[drone]",
        "[voice][wind][drone]amix=inputs=3:duration=first:"
        "weights='1 0.38 0.28':normalize=0,alimiter=limit=0.96,"
        "aresample=48000,asetpts=PTS-STARTPTS[aout]",
    ]

    command += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-frames:v", str(total_frames),
        "-t", f"{duration:.3f}",
        "-r", str(FPS),
        "-aspect", "9:16",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        "-metadata", "title=Kuldhara: A Hindi Folklore Horror Short",
        "-metadata", "comment=Kuldhara is real; paranormal claims are folklore, not verified fact.",
        str(OUTPUT),
    ]

    print(f"Rendering {OUTPUT.name}: {WIDTH}x{HEIGHT} at {FPS} fps, {duration:.2f}s")
    subprocess.run(command, cwd=ROOT, check=True)
    print(f"Done: {OUTPUT} ({OUTPUT.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"FFmpeg exited with status {exc.returncode}.", file=sys.stderr)
        raise
