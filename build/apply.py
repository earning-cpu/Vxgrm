"""
Release gate.

QA the freshly rendered candidate and only copy it over out/bhangarh_shorts.mp4
if it passes every hard check. A failed build therefore never destroys a
previously verified deliverable (this actually bit us once: an untuned plate
rendered a 339-black-frame cut straight over a good file).

Usage:  .venv/bin/python build/apply.py [candidate.mp4]
"""
import json, os, shutil, subprocess, sys

CAND = sys.argv[1] if len(sys.argv) > 1 else "work/final_candidate.mp4"
DEST = "out/bhangarh_shorts.mp4"
REPORT = "work/qa/report.json"

# hard gates: (report path, description, predicate)
GATES = [
    ("video.black_frames",            "no black frames",              lambda v: v == 0),
    ("video.frozen_frame_pairs",      "no frozen frame pairs",        lambda v: v == 0),
    ("video.pct_frames_too_dark",     "dark frames <= 2%",            lambda v: v <= 2.0),
    ("video.pct_frames_in_healthy_range", "healthy-luma frames >= 90%", lambda v: v >= 90.0),
    ("video.pct_frames_near_clip",    "clipping frames <= 1%",        lambda v: v <= 1.0),
    ("video.extra_cuts",              "no phantom cuts",              lambda v: len(v) == 0),
    ("video.cuts_matched",            "at least 25 cuts verified",    lambda v: v >= 25),
    ("audio.silence_runs",            "no unintended silence",        lambda v: len(v) == 0),
    ("duration",                      "duration 59-61 s",             lambda v: 59.0 <= v <= 61.0),
]

def dig(d, path):
    for k in path.split("."):
        d = d[k]
    return d

def main():
    if not os.path.exists(CAND):
        raise SystemExit(f"no candidate at {CAND}")
    print(f"QA-gating {CAND} ...")
    subprocess.run([sys.executable, "build/qa_analyze.py", CAND], check=True,
                   stdout=subprocess.DEVNULL)
    r = json.load(open(REPORT))
    if os.path.abspath(r.get("source", "")) not in (os.path.abspath(CAND),):
        raise SystemExit(f"ABORT: QA report is for '{r.get('source')}', not '{CAND}'")
    fails = []
    for key, label, ok in GATES:
        val = dig(r, key) if not key.startswith("duration") else r["duration"]
        good = ok(val)
        print(f"  [{'PASS' if good else 'FAIL'}] {label:32s} ({val if not isinstance(val, list) else len(val)})")
        if not good:
            fails.append(label)
    # audio loudness sanity
    lufs = float(r["audio"]["integrated_lufs"])
    tp = float(r["audio"]["true_peak_dbfs"])
    for label, good, val in (("loudness -15..-13 LUFS", -15.0 <= lufs <= -13.0, lufs),
                             ("true peak <= -1 dBTP", tp <= -1.0, tp)):
        print(f"  [{'PASS' if good else 'FAIL'}] {label:32s} ({val})")
        if not good:
            fails.append(label)

    if fails:
        print(f"\nREJECTED - kept the previous deliverable. Failed: {', '.join(fails)}")
        raise SystemExit(1)

    shutil.copyfile(CAND, DEST)
    shutil.copyfile(REPORT, "out/qa_report.json")
    print(f"\nPASSED - promoted to {DEST} ({os.path.getsize(DEST)/1048576:.1f} MB)")

if __name__ == "__main__":
    main()
