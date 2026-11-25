import subprocess, sys, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "work/final_candidate.mp4"
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
    "-i", "work/video_clean.mp4", "-loop", "1", "-i", "work/grad.png",
    "-i", "work/mix_norm.wav", "-filter_complex",
    "[0:v][1:v]overlay=0:0:shortest=1[g];"
    "[g]subtitles=filename=work/overlay.ass:fontsdir=assets/fonts:alpha=1,format=yuv420p[v]",
    "-map", "[v]", "-map", "2:a",
    "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
    "-profile:v", "high", "-level", "4.1", "-r", "30", "-pix_fmt", "yuv420p", "-g", "60",
    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
    "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
    "-movflags", "+faststart", "-shortest", OUT], check=True)
print("composed ->", OUT)
