# Track B: performance log

This log distinguishes implementation details from measurements. No official board run ID or final full-scale timing is included in the supplied repository archive, so those fields are intentionally not fabricated.

| Step | Change | Run ID | T (s) | M (MB) | Points |
|---|---|---|---|---|---|
| 0 | Reference implementation baseline | Not recorded in this repository | 56.35 (reference baseline recorded in starter log) | 2,200 (reference baseline recorded in starter log) | — |
| 1 | Query-aware inverted index: collect terms from the query set and build postings only for those terms | Not recorded | — | — | — |
| 2 | Evaluate Boolean posting operations in strict left-to-right order | Not recorded | — | — | — |
| 3 | Filter phrase candidates by intersecting term postings, then verify the exact adjacent token sequence against retained document text | Not recorded | — | — | — |
| 4 | Format result count, ID sum, and ten smallest IDs without sorting the complete match set | Not recorded | — | — | — |

## Implementation notes

- Tokenization uses ASCII byte lowercasing and the `[a-z0-9]+` pattern.
- Document IDs are checked for dense, ordered input.
- The index stores document-ID postings for terms referenced by the query set.
- Boolean operations preserve the specification's strict left-to-right semantics.
- Phrase queries use posting intersections as a candidate filter and then perform exact sequence verification.
- Results are emitted as ASCII with one newline per query.

## Validation status

The supplied repository archive does not include a verified final reference-hash comparison or an official board run ID for the current implementation. The historical local output hashes from earlier iterations are not presented as final correctness evidence.

Record the final `check.py --expected` result and official board run ID here when available. Add only measured full-scale timing and memory values; do not substitute sample timings or estimates.
