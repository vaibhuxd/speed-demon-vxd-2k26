#!/usr/bin/env python3
"""Speed Demon 2026, Track A (Ingest): optimized implementation.

    python3.13 a_ingest.py [--data /data] [--out /out]

Output must be byte-identical to the naive reference (reference/a_ingest.py).
specs/a-ingest.md is the contract; this file implements the same algorithm,
optimized:

  1. No datetime.strptime. Per specs/a-ingest.md the timestamp is ALWAYS
     27 bytes, "YYYY-MM-DDTHH:MM:SS.ffffffZ" -- RFC3339 in UTC, never any
     other offset. The hour string the output needs is a fixed slice:
     ts[:13] + ":00:00Z". strptime was the single biggest cost in the
     reference per the spec's own profiling note; this removes it entirely.
  2. Error detection is a single character compare (status[0] == "5")
     instead of int(status) + a range check -- equivalent because status is
     always exactly 3 digits (100-599), so a leading "5" is necessary and
     sufficient for 500 <= status <= 599.
  3. One dict lookup per line instead of two: each group's value is a
     [latencies_list, error_count] pair instead of two parallel dicts.
  4. No `.rstrip("\n")` call: int() already strips leading/trailing
     whitespace (including the newline the last field carries), so the
     trailing newline is left on latency_us and stripped for free by int().
  5. Output built with a list + single "".join() (as the reference already
     does) -- kept, it was never the bottleneck.
"""
import argparse
import os
import sys

INPUT_NAME = "requests.log"
OUTPUT_NAME = "summary.txt"


def percentile(sorted_values, p):
    """Nearest rank: the value at 1-indexed rank ceil(p * n / 100)."""
    n = len(sorted_values)
    rank = (p * n + 99) // 100   # ceil(p * n / 100) in integer arithmetic
    return sorted_values[rank - 1]


def main(data_dir, out_dir):
    groups = {}   # (hour_str, endpoint) -> [latencies_list, error_count]

    with open(os.path.join(data_dir, INPUT_NAME), encoding="utf-8") as f:
        for line in f:
            ts, method, endpoint, status, latency_us = line.split(" ")
            hour = ts[:13] + ":00:00Z"   # ts is always "YYYY-MM-DDTHH:MM:SS.ffffffZ"
            key = (hour, endpoint)
            g = groups.get(key)
            if g is None:
                g = [[], 0]
                groups[key] = g
            g[0].append(int(latency_us))   # int() strips the trailing "\n" for free
            if status[0] == "5":           # status is always 3 digits; leading '5' <=> 500-599
                g[1] += 1

    lines = []
    # Endpoints are ASCII (see the spec), so Python's string order is bytewise order.
    for key in sorted(groups):
        hour, endpoint = key
        latencies, errs = groups[key]
        values = sorted(latencies)
        count = len(values)
        ppm = errs * 1_000_000 // count
        lines.append(
            f"{hour} {endpoint} {count} "
            f"{percentile(values, 50)} {percentile(values, 95)} {percentile(values, 99)} "
            f"{errs} {ppm}\n"
        )

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, OUTPUT_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track A (Ingest) optimized implementation.")
    parser.add_argument("--data", default="/data", help="directory holding requests.log")
    parser.add_argument("--out", default="/out", help="directory to write summary.txt into")
    args = parser.parse_args()
    main(args.data, args.out)
    sys.exit(0)
