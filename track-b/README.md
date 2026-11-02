# Track B — Index

## Objective

Build an inverted index over `docs.txt` and answer the Boolean and phrase queries in `queries.txt`, writing one result line per query to `results.txt`. The authoritative tokenization, query semantics, and output contract are defined in the [official Track B specification](https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/b-index.md).

## Implementation approach

The implementation parses the query set first and collects the terms required by those queries. During the document pass, it tokenizes document text using ASCII byte lowercasing and the `[a-z0-9]+` token pattern, retaining postings only for required terms. Document text is retained for exact phrase verification.

Boolean queries use posting-set operations in strict left-to-right order. Phrase queries first intersect the postings for their terms to produce candidate documents, then verify the exact adjacent token sequence against each candidate's original text.

Each result reports the match count, the sum of matching document IDs, and up to the ten smallest matching IDs in ascending order. Empty results use the required `0 0` representation.

## Dependencies

Python standard library only. No third-party runtime dependencies.

## Validation and performance status

The implementation has been locally exercised in the repository's Docker checker. The repository archive supplied for this cleanup does not contain an independently recorded final reference-hash result or official board run ID, so no final correctness or speedup claim is made here.

## Further work

Record the final reference-hash comparison and official board run ID for the submitted version. Benchmark the full official dataset and document the measured runtime and memory rather than extrapolating from sample runs.
