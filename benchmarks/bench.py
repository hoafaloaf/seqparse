"""Benchmarks for seqparse: CPU time (best of N) and peak memory per workload.

Usage:
    python benchmarks/bench.py                      # print results
    python benchmarks/bench.py --save base.json     # save a baseline
    python benchmarks/bench.py --compare base.json  # fail on regressions

A workload "regresses" when its time exceeds the baseline by more than
--tolerance (default 10%, to absorb timer noise). Memory is reported for
information and compared with the same tolerance.
"""

import argparse
import gc
import json
import os
import random
import sys
import tempfile
import time
import tracemalloc

# Benchmark the checkout this script lives in, not an installed copy.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seqparse
from seqparse import sequences

RNG = random.Random(1234)
GAPPY = sorted(RNG.sample(range(200_000), 100_000))
GAPPY_STR = str(sequences.FrameSequence(GAPPY, pad=6))
DENSE = list(range(1, 100_001))
FSEQ_FRAMES = sorted(RNG.sample(range(20_000), 5_000))
FILE_NAMES = [
    f"/renders/shot{s:02d}/plate.{f:04d}.exr"
    for s in range(10)
    for f in sorted(RNG.sample(range(1, 9_000), 5_000))
]
RNG.shuffle(FILE_NAMES)


def w_parse_string():
    """Parse a ~45k-chunk frame sequence string and render it."""
    return str(sequences.FrameSequence(GAPPY_STR))


def w_build_gappy():
    """Build from 100k gappy integer frames and render."""
    return str(sequences.FrameSequence(GAPPY, pad=6))


def w_build_dense():
    """Build from 100k contiguous integer frames and render."""
    return str(sequences.FrameSequence(DENSE, pad=6))


def w_iterate():
    """Iterate the padded frames of a 100k-frame sequence."""
    seq = sequences.FrameSequence(GAPPY, pad=6)
    str(seq)
    return sum(1 for _ in seq)


def w_invert():
    """Invert a 100k-frame gappy sequence."""
    return str(sequences.FrameSequence(GAPPY, pad=6).invert())


def w_membership():
    """2k membership checks (ints, padded strings, file names)."""
    seq = sequences.FileSequence(
        name="/r/plate", ext="exr", frames=FSEQ_FRAMES, pad=4
    )
    probes = FSEQ_FRAMES[::10]
    hits = sum(f in seq for f in probes)
    hits += sum(f"{f:04d}" in seq for f in probes)
    hits += sum(f"/r/plate.{f:04d}.exr" in seq for f in probes[:100])
    return hits


def w_seqparse_add():
    """Add 50k file names (10 sequences) to a parser and render output."""
    parser = seqparse.get_parser()
    for name in FILE_NAMES:
        parser.add_file(name)
    return [str(x) for x in parser.output()]


def w_seqparse_missing():
    """Render the missing frames of 10 x 5k-frame sequences."""
    parser = seqparse.get_parser()
    for name in FILE_NAMES:
        parser.add_file(name)
    return [str(x) for x in parser.output(missing=True)]


SCAN_DIR = ""


def w_scan_stat():
    """Scan a directory of 3k files with disk stats (I/O bound)."""
    parser = seqparse.get_parser()
    parser.scan_options["stat"] = True
    parser.scan_path(SCAN_DIR)
    return [(str(x), x.size) for x in parser.output()]


WORKLOADS = {
    "parse_string": (w_parse_string, 5),
    "build_gappy": (w_build_gappy, 5),
    "build_dense": (w_build_dense, 5),
    "iterate": (w_iterate, 5),
    "invert": (w_invert, 5),
    "membership": (w_membership, 3),
    "seqparse_add": (w_seqparse_add, 3),
    "seqparse_missing": (w_seqparse_missing, 3),
    "scan_stat": (w_scan_stat, 5),
}


def make_scan_dir(root):
    """Create 3 directories x 1000 small files."""
    for d in range(3):
        sub = os.path.join(root, f"d{d}")
        os.makedirs(sub)
        for f in range(1, 1001):
            if f % 97 == 0:
                continue  # leave gaps
            with open(os.path.join(sub, f"img.{f:04d}.exr"), "w") as handle:
                handle.write("x" * (f % 13))


def measure(func, repeats):
    """Best-of-N CPU time (seconds) and peak traced memory (bytes)."""
    times = []
    for _ in range(repeats):
        gc.collect()
        start = time.process_time()
        func()
        times.append(time.process_time() - start)
    gc.collect()
    tracemalloc.start()
    func()
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return {"time": min(times), "peak_mem": peak}


def main():
    """Run the benchmarks and optionally save or compare results."""
    global SCAN_DIR  # noqa: PLW0603
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save")
    parser.add_argument("--compare")
    parser.add_argument("--tolerance", type=float, default=0.10)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()

    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        make_scan_dir(tmp)
        SCAN_DIR = tmp
        for name, (func, repeats) in WORKLOADS.items():
            if args.only and name not in args.only:
                continue
            results[name] = measure(func, repeats)

    baseline = None
    if args.compare:
        with open(args.compare, encoding="utf-8") as handle:
            baseline = json.load(handle)

    regressions = []
    print(f"{'workload':<18} {'time (ms)':>10} {'peak mem (KiB)':>15}", end="")
    print("   vs baseline (time / mem)" if baseline else "")
    for name, res in results.items():
        ms, kib = res["time"] * 1e3, res["peak_mem"] / 1024
        line = f"{name:<18} {ms:>10.1f} {kib:>15.0f}"
        if baseline and name in baseline:
            base = baseline[name]
            t_ratio = res["time"] / base["time"] if base["time"] else 1.0
            m_ratio = (
                res["peak_mem"] / base["peak_mem"] if base["peak_mem"] else 1.0
            )
            line += f"   {t_ratio:>5.2f}x / {m_ratio:>5.2f}x"
            if t_ratio > 1 + args.tolerance:
                regressions.append(f"{name}: time {t_ratio:.2f}x")
            if m_ratio > 1 + args.tolerance:
                regressions.append(f"{name}: memory {m_ratio:.2f}x")
        print(line)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2)
    if regressions:
        print("REGRESSIONS: " + "; ".join(regressions))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
