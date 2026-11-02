#!/usr/bin/env python3
"""Speed Demon 2026, Track D (Traverse): optimized implementation.

    python3.13 d_traverse.py [--data /data] [--out /out]

Output must be byte-identical to the naive reference (reference/d_traverse.py).
specs/d-traverse.md is the contract. Same algorithm (Dijkstra with a binary
heap, fresh per query, early-stopping when the target is settled) -- the
spec itself notes "sophisticated algorithms can lose to simpler
implementations" here, so this keeps Dijkstra and optimizes its constants:

  1. CSR (compressed sparse row) adjacency instead of a Python list of
     per-node lists of (v, w) tuples. Parsing builds three flat lists
     (`heads`, `to`, `wt`, where edges of node u live in `to[off[u]:
     off[u+1]]` / `wt[off[u]:off[u+1]]`) via a counting sort over `u`, so
     building it is still O(n + m). This removes 5,000,000 tuple objects
     (one per edge, at full scale) and the pointer-chasing of a Python
     list-of-lists, replacing inner-loop tuple unpacking with flat integer
     indexing.
  2. **Measured and reverted**: an earlier version of this file used
     `dist.get(v)` in the relax step instead of the reference's
     `v not in dist or nd < dist[v]`, on the theory that one dict lookup
     beats two. Profiling showed this was backwards: `in` and `[]` on a
     dict compile to fast inline bytecode (`CONTAINS_OP`/`BINARY_SUBSCR`,
     no function-call overhead), while `.get()` is a real bound-method
     call -- at 6.15M relax attempts (sample scale), that call overhead
     cost more than the second lookup it was meant to avoid. Kept the
     reference's original pattern. Left as a documented dead end, not
     silently dropped, since it's exactly the kind of "looks faster,
     measures slower" case the optimization loop is supposed to catch.
  3. `heapq.heappush`/`heappop` and the current node's edge-slice bounds are
     bound to local variables inside the query loop (standard CPython
     micro-optimization: local variable access is a fast array slot, module
     attribute access is a dict lookup, and this function is called once
     per query -- 2,000 times at full scale, each running its own
     while-loop with potentially many iterations).
"""

import argparse
import heapq
import os


def read_graph(path):
    """CSR adjacency: to[off[u]:off[u+1]] / wt[off[u]:off[u+1]] are the
    (head, weight) pairs of every edge "u v w" out of u, in file order."""
    with open(path, encoding="ascii") as f:
        n, m = map(int, f.readline().split())
        us = [0] * m
        vs = [0] * m
        ws = [0] * m
        degree = [0] * n
        for i, line in enumerate(f):
            u_s, v_s, w_s = line.split()
            u = int(u_s)
            us[i] = u
            vs[i] = int(v_s)
            ws[i] = int(w_s)
            degree[u] += 1

        off = [0] * (n + 1)
        acc = 0
        for u in range(n):
            off[u] = acc
            acc += degree[u]
        off[n] = acc

        to = [0] * m
        wt = [0] * m
        cursor = off[:n]   # next free slot for each u, starts at off[u]
        for i in range(m):
            u = us[i]
            pos = cursor[u]
            to[pos] = vs[i]
            wt[pos] = ws[i]
            cursor[u] = pos + 1

    return off, to, wt


def read_queries(path):
    with open(path, encoding="ascii") as f:
        return [tuple(map(int, line.split())) for line in f]


def shortest_path(off, to, wt, s, t):
    """Dijkstra from s, stopping when t is settled; -1 if t is never reached."""
    dist = {s: 0}
    heap = [(0, s)]
    heappush = heapq.heappush
    heappop = heapq.heappop
    while heap:
        d, u = heappop(heap)
        if d > dist[u]:
            continue  # stale entry: u was already settled at a shorter distance
        if u == t:
            return d
        start, end = off[u], off[u + 1]
        for i in range(start, end):
            v = to[i]
            nd = d + wt[i]
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                heappush(heap, (nd, v))
    return -1


def main(data_dir, out_dir):
    off, to, wt = read_graph(os.path.join(data_dir, "graph.txt"))
    queries = read_queries(os.path.join(data_dir, "queries.txt"))
    answers = [shortest_path(off, to, wt, s, t) for s, t in queries]
    with open(os.path.join(out_dir, "distances.txt"), "w", encoding="ascii", newline="\n") as f:
        f.write("".join(f"{d}\n" for d in answers))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track D (Traverse) optimized implementation")
    parser.add_argument("--data", default="/data")
    parser.add_argument("--out", default="/out")
    args = parser.parse_args()
    main(args.data, args.out)
