# Track A — Ingest

## Objective

Process the request-log input and write the required hourly endpoint summary to `summary.txt`. The exact input contract and output format are defined in the [official Track A specification](https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/a-ingest.md).

## Implementation approach

The implementation reads the log sequentially and aggregates latency values and server-error counts by `(UTC hour, endpoint)`.

It uses the fixed timestamp layout guaranteed by the specification to derive the hour with a string slice rather than parsing each timestamp with `datetime`. It also uses the three-digit status-code format to identify 5xx responses from the leading digit. Each group stores its latency list and error count together, reducing duplicate dictionary lookups.

Latency percentiles are calculated using the nearest-rank rule with integer arithmetic. Output is assembled in the format required by the specification.

## Dependencies

Python standard library only. No third-party runtime dependencies.

## Validation notes

The repository's performance log records byte-for-byte comparisons against the reference on tiny and sample datasets. Those are local measurements, not official board results. The log also records that Docker and full-scale validation had not been completed when it was written.

## Further work

Run the official full-scale dataset through the competition checker, retain the resulting reference hash and board run ID, and profile memory and runtime under the official environment.
