# Track C: performance log

Every step from the reference to your final version, each with the live-board run ID that measured it. Judges check that the run IDs exist and that each change moved the way you say it did.

| Step | Change | Run ID | T (s) | M (MB) | Points |
|---|---|---|---|---|---|
| 0 | The reference, unchanged | | 14.44 | 367 | 0 |
| 1 | Replaced regex-based `parse_int`/`parse_cents` with manual string checks; dropped `name.encode("utf-8")`/`note.encode("utf-8")` in favor of `len(name)`/`len(note)` (ASCII-only, per spec 2.2); `Country` object -> list | NOT YET SUBMITTED TO BOARD | — | — | — |

## Local sandbox measurements (NOT official board scores)

Environment: this dev sandbox, Python 3.12, `sample` scale (332,000
records, 10% of `full`), 5 reps each, no Docker. Noisy sandbox -- all reps
shown, not cherry-picked.

| Implementation | Wall time, 5 reps (s) | Mean (s) | Output |
|---|---|---|---|
| Reference (unmodified) | 2.313, 2.042, 2.267, 2.277, 1.822 | 2.144 | `sha256:9035fed3...5ebe9a66` |
| Optimized (this version) | 1.689, 1.550, 2.160, 2.100, 1.350 | 1.770 | `sha256:9035fed3...5ebe9a66` (byte-identical) |

Local speedup: **~1.21x**, modest and the variance between reps is nearly
as large as the gap between implementations -- treat this as "probably a
real but small improvement," not a confident number.

## Why this track moved so little (profiled, not guessed)

`cProfile` on the sample dataset (see raw output in session notes) showed
`parse_int`/`parse_cents` together were the single largest cost even after
optimization -- `csv.reader` itself (the C-implemented hostile-CSV
tokenizer) is the actual floor here, and this version deliberately does not
replace it. Section 2.1 of the spec is explicit: "a parser that is three
times faster and wrong scores zero" -- hand-rolling quote/escape/BOM/mixed-
line-ending handling to beat the stdlib `csv` module's C implementation is
a correctness risk this version chose not to take within the time available.

## Optimization strategy

1. **Dropped `re.fullmatch` in `parse_int`/`parse_cents`.** Manual
   `.isdigit()` + slicing checks instead of a compiled regex per call
   (864,000 `parse_int` calls + 332,000 `parse_cents` calls at sample
   scale, 10x that at `full`).
2. **Dropped the redundant `.isascii()` check** inside both parsers.
   specs/c-join.md 2.2 ("Bytes") guarantees every byte in `records.csv` is
   already printable ASCII (0x20-0x7E), LF, or CR -- so any field substring
   reaching `parse_int`/`parse_cents` is already ASCII by construction, and
   re-checking it per call was pure overhead. `.isdigit()` stays, as real
   validation.
3. **Dropped `name.encode("utf-8")` / `note.encode("utf-8")`** before
   taking byte length. Same 2.2 guarantee: name/note content is restricted
   to ASCII letters, spaces, and lowercase words, so after CSV unescaping,
   `len(s) == len(s.encode("utf-8"))` always holds. Removed up to ~6.6M
   `.encode()` calls at `full` scale.
4. **`Country` class -> plain list** per group, to avoid per-field
   `__dict__` attribute lookups during the hot per-record update.
5. **Did not touch** `csv.reader` itself, `load_regions`, or the hash-join
   logic -- profiling showed these were not where the remaining time goes
   relative to the two parse functions, and `csv.reader` is deliberately
   left as the stdlib's own hostile-CSV implementation (see above).

## Correctness validation

- `diff`'d byte-for-byte against the unmodified reference on `tiny` scale
  (covers all 20 edge cases listed in spec section 2.5) -- identical, twice
  (once before, once after dropping `.isascii()`).
- `diff`'d byte-for-byte against the unmodified reference on `sample` scale
  (332,000 records) -- identical, confirmed via matching SHA-256.
- Not yet run through `check.py` / Docker (no Docker daemon in this
  sandbox). Not yet run on `full` scale (3.32M records).

## Trade-offs / further optimization opportunities

- The CSV tokenizer itself is now the dominant cost and untouched. A
  hand-rolled byte-level state machine (possibly reading the whole file
  into memory and scanning with `bytes.find`/a manual loop instead of
  `csv.reader`'s row-by-row Python-level iteration) is the highest-value
  remaining optimization, but given "wrong scores zero" on this track
  specifically, this was deliberately not attempted without more time to
  validate it against every edge case in 2.5.
- Not yet profiled at `full` scale -- `sample`-scale profiling may not
  reflect `full`-scale bottlenecks exactly if constant overheads matter
  less at 10x the data.
