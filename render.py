"""Render the 3D paper-cutout film."""
import sys
from types import SimpleNamespace
from src import timeline as TL, renderer as R, audio as A


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "out/kaka_mala_vachwa.mp4"
    shots = [SimpleNamespace(t0=t0, t1=t1, trans="cut") for t0, t1, _ in TL.SHOTS]
    A.build_audio(shots, "build/master.wav", vo_start=TL.VO_START, tempo=TL.TEMPO)
    R.render(out, "build/master.wav")
    print("DONE:", out)


if __name__ == "__main__":
    main()
