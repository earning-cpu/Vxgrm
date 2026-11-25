"""Full pipeline: audio -> frames -> mux."""
import sys
import time

from src import timeline as TL, renderer as R, audio as A

OUT = sys.argv[1] if len(sys.argv) > 1 else "out/kaka_mala_vachwa.mp4"


def main():
    shots = TL.build()
    t0 = time.time()
    print("building score ...", flush=True)
    A.build_audio(shots, "build/score.wav")
    print(f"  audio done in {time.time()-t0:.1f}s", flush=True)

    t1 = time.time()
    print("rendering video ...", flush=True)
    R.render(shots, OUT, audio_path="build/score.wav")
    print(f"  video done in {time.time()-t1:.1f}s", flush=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
