#!/usr/bin/env python3.13
"""Speed Demon 2026, Track C (Join): optimized implementation.

    python3.13 c_join.py [--data /data] [--out /out]

Output must be byte-identical to the naive reference (reference/c_join.py).
specs/c-join.md is the contract. Still uses Python's `csv` module for the
actual hostile-CSV tokenizing (quoted fields, embedded commas/newlines,
"" escapes) -- that module is a correct, battle-tested C implementation of
exactly this grammar, and section 2.1 is explicit that a fast-but-wrong
parser scores zero, so it is not worth the correctness risk of
hand-rolling a replacement. Everything *around* the tokenizer is optimized:

  1. `parse_int` and `parse_cents` no longer use `re.fullmatch`. Manual
     string checks (`.isascii()`, `.isdigit()`, slicing) do the same
     validation without per-call regex engine overhead, which matters at
     3.32M calls each (full scale).
  2. `name_bytes`/`note_bytes` no longer call `.encode("utf-8")` per
     record. specs/c-join.md 2.2 ("Bytes") guarantees every byte in
     records.csv is printable ASCII, LF or CR (plus the BOM, which is
     stripped before this point) -- so after CSV unescaping, name and
     note are pure ASCII strings, and `len(s) == len(s.encode("utf-8"))`
     always. This removes an allocation-heavy encode call per field per
     record (up to ~6.6M calls at full scale).
  3. Each country's running aggregate is a list (positional fields)
     instead of a `Country` object -- list-item access avoids per-field
     attribute lookup through `__dict__`.
"""

import argparse
import os

RECORDS_FILE = "records.csv"
REGIONS_FILE = "regions.csv"
OUTPUT_FILE = "aggregates.txt"

RECORDS_HEADER = ["id", "name", "note", "region_id", "amount"]
REGIONS_HEADER = ["region_id", "country"]
BOM = "\ufeff"
UNMATCHED = "_UNMATCHED"

# Country aggregate list indices.
I_COUNT, I_IDSUM, I_AMTSUM, I_AMTMIN, I_AMTMAX, I_NAMES, I_NAMEBYTES, I_NOTEBYTES = range(8)


def parse_int(text):
    """'42' -> 42, for id and region_id.

    No `.isascii()` check: specs/c-join.md section 2.2 ("Bytes") guarantees
    every byte in records.csv is already printable ASCII (0x20-0x7E), LF or
    CR -- so any substring of a parsed field is already ASCII before this
    function ever sees it, and re-checking that per call is pure overhead.
    `.isdigit()` is still checked (cheap, and real validation against a
    non-digit character reaching here via a logic error elsewhere).
    """
    if not text or not text.isdigit():
        raise ValueError(f"bad integer {text!r}")
    return int(text)


def parse_cents(text):
    """'-5.25' -> -525. Exact integer cents, never a float.

    Grammar: amount = ["-"] 1*DIGIT "." 2DIGIT, no leading zeros on the
    integer part except a bare "0". See parse_int for why `.isascii()`
    is not re-checked here.
    """
    body = text[1:] if text[:1] == "-" else text
    dot = body.rfind(".")
    if dot == -1:
        raise ValueError(f"bad amount {text!r}")
    whole, frac = body[:dot], body[dot + 1:]
    if not whole or not whole.isdigit():
        raise ValueError(f"bad amount {text!r}")
    if len(whole) > 1 and whole[0] == "0":
        raise ValueError(f"bad amount {text!r}")
    if len(frac) != 2 or not frac.isdigit():
        raise ValueError(f"bad amount {text!r}")
    cents = int(whole) * 100 + int(frac)
    return -cents if text[:1] == "-" else cents


def format_cents(cents):
    """-525 -> '-5.25', -5 -> '-0.05', 0 -> '0.00'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def load_regions(path):
    """regions.csv -> {region_id: country}."""
    import csv
    regions = {}
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        if next(reader) != REGIONS_HEADER:
            raise ValueError("unexpected regions.csv header")
        for region_id, country in reader:
            regions[parse_int(region_id)] = country
    return regions


def read_records(path):
    """Yield (id, name, note, region_id, amount) string tuples from records.csv."""
    import csv
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for number, row in enumerate(reader):
            if len(row) != 5:
                raise ValueError(f"record {number}: expected 5 fields, got {len(row)}")
            row[0] = row[0].removeprefix(BOM)
            if number == 0:
                if row != RECORDS_HEADER:
                    raise ValueError("unexpected records.csv header")
                continue
            yield row


def main(data_dir, out_dir):
    regions = load_regions(os.path.join(data_dir, REGIONS_FILE))
    countries = {}
    for record_id, name, note, region_id, amount in read_records(os.path.join(data_dir, RECORDS_FILE)):
        key = regions.get(parse_int(region_id), UNMATCHED)    # the hash join
        c = countries.get(key)
        cents = parse_cents(amount)
        rid = parse_int(record_id)
        if c is None:
            countries[key] = [1, rid, cents, cents, cents, {name}, len(name), len(note)]
        else:
            c[I_COUNT] += 1
            c[I_IDSUM] += rid
            c[I_AMTSUM] += cents
            if cents < c[I_AMTMIN]:
                c[I_AMTMIN] = cents
            if cents > c[I_AMTMAX]:
                c[I_AMTMAX] = cents
            c[I_NAMES].add(name)
            c[I_NAMEBYTES] += len(name)
            c[I_NOTEBYTES] += len(note)

    # str order is code point order, which is UTF-8 byte order.
    lines = []
    for key in sorted(countries):
        c = countries[key]
        lines.append(" ".join([
            key,
            str(c[I_COUNT]),
            str(c[I_IDSUM]),
            format_cents(c[I_AMTSUM]),
            format_cents(c[I_AMTMIN]),
            format_cents(c[I_AMTMAX]),
            str(len(c[I_NAMES])),
            str(c[I_NAMEBYTES]),
            str(c[I_NOTEBYTES]),
        ]))

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, OUTPUT_FILE), "wb") as f:
        f.write("".join(line + "\n" for line in lines).encode("utf-8"))


def cli(argv=None):
    ap = argparse.ArgumentParser(description="Track C (Join) optimized implementation.")
    ap.add_argument("--data", default="/data")
    ap.add_argument("--out", default="/out")
    args = ap.parse_args(argv)
    main(args.data, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
