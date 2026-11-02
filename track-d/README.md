# Track D — Traverse

## Objective

Answer the directed weighted-graph shortest-path queries and write the results to `distances.txt`. The [official Track D specification](https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/d-traverse.md) defines graph input, query behavior, and output requirements.

## Implementation approach

The implementation uses Dijkstra's algorithm with a binary heap and stops a query once its target is settled. The graph is represented using compressed sparse row (CSR) adjacency arrays rather than a Python list of per-vertex lists containing edge tuples.

CSR construction uses degree counting, prefix offsets, and flat destination and weight arrays. The shortest-path search iterates over the contiguous edge range for each vertex. Heap operations are bound to local variables inside the query routine to reduce repeated attribute lookup overhead.

## Dependencies

Python standard library only. No third-party runtime dependencies.

## Validation notes

The performance log records local byte-for-byte comparisons against the reference on tiny and sample datasets. It also states that Docker and full-scale validation had not been completed when those measurements were recorded. The sample timings are not official board scores.

## Further work

Run the full official graph dataset through the competition checker, retain the exact output hash and board run ID, and profile preprocessing, heap operations, runtime, and peak memory under the official environment.
