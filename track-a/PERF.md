# Track A: performance log

Every step from the reference to your final version, each with the live-board run ID that measured it. Judges check that the run IDs exist and that each change moved the way you say it did.

| Step | Change | Run ID | T (s) | M (MB) | Points |
|---|---|---|---|---|---|
| 0 | The reference, unchanged | | 32.05 | 228 | 0 |
| 1 | Removed `datetime.strptime`; hour is a fixed 13-byte slice of the timestamp (ts is always exactly 27 bytes per spec, RFC3339 UTC with no other offset) | NOT YET SUBMITTED TO BOARD | — | — | — |

## Local sandbox measurements (NOT official board scores)

Environment: this dev sandbox, Python 3.12, `sample` scale (310,000 lines,
10% of `full`), single run (not the board's 5-run median), no Docker (ran
the module directly, not through the image) -- so these numbers are only
useful for comparing the two implementations to each other, not for
predicting the board's T.

| Implementation | Wall time (sample, this sandbox) | Output |
|---|---|---|
| Reference (unmodified) | 3.4533 s | `sha256:ca6311bb...3893aac3` |
| Optimized (this version) | 0.5018 s | `sha256:ca6311bb...3893aac3` (byte-identical) |

Local speedup: ~6.9x on `sample` scale, this machine. Verified byte-identical
via `diff` and SHA-256 on both `tiny` (all E1-E15 edge cases) and `sample`
scale before this number was recorded.

## Optimization strategy

1. **Removed `datetime.strptime` entirely.** Per `specs/a-ingest.md` the
   timestamp is *always* `YYYY-MM-DDTHH:MM:SS.ffffffZ`, exactly 27 bytes,
   always UTC. The hour-truncated output string is therefore always
   `ts[:13] + ":00:00Z"` -- a fixed slice, not a parse. `strptime` plus
   `datetime.replace()` plus `datetime.strftime()` (three separate calls
   per line in the reference) collapse into one string slice and one
   concatenation.
2. **Error check is `status[0] == "5"` instead of `500 <= int(status) <=
   599`.** Status is always exactly 3 digits (100-599 per spec), so a
   leading `"5"` is both necessary and sufficient -- no `int()` conversion
   needed for this field at all.
3. **One dict instead of two.** The reference keeps `latencies` and
   `errors` as two separate dicts with the same keys (two hash lookups per
   line, one dict-membership check). This version keeps one dict mapping
   `(hour, endpoint) -> [latencies_list, error_count]` (one lookup).
4. **Dropped the explicit `.rstrip("\n")`.** `int()` already strips
   leading/trailing whitespace, including a trailing newline, so letting
   the last split field (`latency_us`) keep its `\n` and relying on `int()`
   to strip it is free -- one fewer full-line string operation per line.

## Correctness validation

- `diff`'d byte-for-byte against the unmodified reference on `tiny` scale
  (covers every edge case E1-E15 per the spec's own table) -- identical.
- `diff`'d byte-for-byte against the unmodified reference on `sample` scale
  (310,000 lines) -- identical, confirmed again via matching SHA-256.
- Not yet run through `check.py` / Docker (no Docker daemon in this
  sandbox -- see HANDOFF.md). Not yet run on `full` scale (3.1M lines) --
  do this before relying on the local timing number for real decisions.

## Trade-offs / further optimization opportunities

- Still pure Python, single-threaded, still builds a full in-memory
  `(hour, endpoint) -> list` structure. The spec notes 1,842 endpoints x 72
  hours is at most ~130k groups, so memory for the grouping structure
  itself isn't the bottleneck -- the 3.1M `int()` calls and list
  appends likely are, at `full` scale. Not yet profiled with `cProfile` to
  confirm where remaining time goes.
- Not yet attempted: avoiding the tuple key `(hour, endpoint)` in favor of
  a single string key, or switching the per-group latency list to
  something that avoids the final `sorted()` call's full-list copy.
- Not yet attempted: a non-Python rewrite. Given S (source size) and D
  (dependencies) are both capped contributors (15% each) and T is
  uncapped at 50%, a compiled rewrite is worth evaluating against the
  `full`-scale number once available, not before.
