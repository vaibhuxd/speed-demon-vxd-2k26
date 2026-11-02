# Track D: performance log

Every step from the reference to your final version, each with the live-board run ID that measured it. Judges check that the run IDs exist and that each change moved the way you say it did.

| Step | Change | Run ID | T (s) | M (MB) | Points |
|---|---|---|---|---|---|
| 0 | The reference, unchanged | | 72.69 | 893 | 0 |
| 1 | CSR adjacency instead of list-of-lists-of-tuples; local-var-bound heappush/heappop | NOT YET SUBMITTED TO BOARD | — | — | — |
| 1a | TRIED AND REVERTED: `dist.get(v)` instead of `v not in dist or nd < dist[v]` in the relax step -- measured SLOWER, see "A real regression" below | n/a (never kept) | n/a | n/a | n/a |

## Local sandbox measurements (NOT official board scores)

Environment: this dev sandbox, Python 3.12, `sample` scale (174,051 nodes,
500,000 edges, 200 queries -- 10% of full's node/edge counts), 3 reps each,
no Docker. This sandbox is noticeably noisy for this track (shared CPU,
long-running processes) -- reference time varied from 8.1s to 9.5s across
different benchmark invocations in this session, so treat the speedup
below as directional, not precise.

| Implementation | Wall time, 3 reps (s) | Mean (s) | Output |
|---|---|---|---|
| Reference (unmodified) | 9.384, 9.485, 9.438 | 9.436 | `sha256:a4c76ed0...2e57046a0` |
| Optimized (CSR, .get() reverted) | 8.531, 8.446, 9.571 | 8.849 | `sha256:a4c76ed0...2e57046a0` (byte-identical) |

Local speedup: **~1.07x**, modest, and the gap is on the same order as the
run-to-run noise -- an earlier version of this file (CSR + `dist.get()`)
measured **slower than the reference** (0.90x) before the `.get()` change
was identified and reverted; see below.

## A real regression, caught and reverted (not hidden)

The first version of this file replaced the reference's relax-step check
`if v not in dist or nd < dist[v]:` with `cur = dist.get(v); if cur is None
or nd < cur:`, on the theory that one dict lookup beats a membership test
plus a second lookup. Measured result: **slower**, not faster (0.90x vs
reference on sample scale, see git-free history in this session's tool
calls). `cProfile` on both versions showed why: `v not in dist` and
`dist[v]` compile to fast inline bytecode (`CONTAINS_OP` / `BINARY_SUBSCR`,
no function-call overhead), while `dict.get` is a genuine bound-method
call -- at ~6.15M relax attempts on sample scale (10x that at full), that
per-call overhead outweighed the lookup it was meant to save. Reverted to
the reference's original pattern; kept CSR adjacency (see below), which
profiling showed was roughly neutral-to-slightly-positive on its own.

## Optimization strategy

1. **CSR (compressed sparse row) adjacency** instead of
   `adj[u] = [(v, w), ...]` (a Python list of per-node lists of tuples).
   Three flat lists (`off`, `to`, `wt`) built via a counting-sort-style
   two-pass construction (count degrees, prefix-sum into offsets, scatter
   into place) -- still O(n + m). Removes one tuple object per edge
   (5,000,000 at full scale) and replaces `for v, w in adj[u]:` (tuple
   unpacking per iteration) with flat integer indexing
   `to[i]`/`wt[i]` over `range(off[u], off[u+1])`.
2. **Local-variable-bound `heapq.heappush`/`heappop`** inside
   `shortest_path`, since the function runs its own while-loop per query
   (2,000 queries at full scale) and local-slot access beats a module
   attribute lookup repeated across every heap operation.
3. **Did not change** the algorithm itself (fresh Dijkstra per query,
   binary heap, early-stop on target settle) -- the spec's own Track D
   section explicitly warns "sophisticated algorithms can lose to simpler
   implementations" here, and profiling (see above) showed the relax loop
   itself, not algorithm choice, is where the real cost and the real
   regression both live.

## Correctness validation

- `diff`'d byte-for-byte against the unmodified reference on `tiny` scale
  -- identical, both before and after the `.get()` revert.
- `diff`'d byte-for-byte against the unmodified reference on `sample`
  scale (174,051 nodes / 500,000 edges / 200 queries) -- identical,
  confirmed via matching SHA-256, after the revert.
- Not yet run through `check.py` / Docker (no Docker daemon in this
  sandbox). Not yet run on `full` scale (1,740,512 nodes / 5,000,000
  edges / 2,000 queries).

## Trade-offs / further optimization opportunities

- `cProfile` showed `shortest_path` itself (not graph construction) is
  ~85-90% of total time at every version tried, and within that,
  `heapq.heappop`/`heappush` call overhead is a large, not-yet-attacked
  chunk (2.28M `heappop` calls at sample scale). A manual binary heap
  using a flat list and hand-written sift-up/down (avoiding the
  `heapq` module's own function-call overhead per operation) is the next
  thing worth measuring, not yet attempted.
- Not yet profiled at `full` scale.
- Given T is 50% of the score and uncapped, and this track's spec
  explicitly flags that preprocessing time counts inside the timed run,
  a from-scratch non-Python rewrite is plausibly higher-value here than
  further Python micro-optimization -- not evaluated yet given time spent
  this session on A and C.
