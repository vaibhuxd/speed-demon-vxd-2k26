# Track C — Join

## Objective

Join the records and region data, calculate the required country-level aggregates, and write the exact output to `aggregates.txt`. See the [official Track C specification](https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/c-join.md) for the CSV grammar, edge cases, and output contract.

## Implementation approach

The implementation uses Python's standard-library `csv` reader to handle quoted fields, escaped quotes, embedded commas, and embedded newlines. It loads the region-to-country mapping, processes the records, joins each record to its region, and accumulates the required per-country statistics.

The hot parsing paths use explicit digit checks rather than regular-expression calls. Country aggregates are stored in positional lists to reduce per-record object and attribute overhead. Amounts are handled using integer cents to avoid floating-point rounding differences.

## Dependencies

Python standard library only. No third-party runtime dependencies.

## Validation notes

The performance log records local byte-for-byte comparisons against the reference on tiny and sample datasets. It also states that Docker and full-scale validation had not been completed when those measurements were recorded. The sample measurements are not official board scores.

## Further work

Run the full official dataset through the competition checker, retain the exact output hash and board run ID, and profile the CSV parsing and aggregation stages under the official environment.
