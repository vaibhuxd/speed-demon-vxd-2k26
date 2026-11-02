#!/usr/bin/env python3
"""Speed Demon 2026 — Track B: Query-aware inverted index."""

import argparse
import heapq
import os
import re

TOKEN_RE = re.compile(rb"[a-z0-9]+")
EMPTY = frozenset()


def parse_queries(path):
    queries = []
    required = set()

    with open(path, "rb") as f:
        for line in f:
            if line.endswith(b"\n"):
                line = line[:-1]
            kind, sep, rest = line.partition(b" ")

            if not sep:
                raise ValueError(f"Invalid query: {line!r}")

            if kind == b"BOOL":
                parts = rest.split(b" ")
                terms = tuple(parts[::2])
                operators = tuple(parts[1::2])

                if not terms or len(operators) != len(terms) - 1:
                    raise ValueError(f"Invalid BOOL query: {line!r}")
                if any(op not in (b"AND", b"OR", b"NOT") for op in operators):
                    raise ValueError(f"Invalid BOOL operator: {line!r}")

                queries.append((0, terms, operators))
                required.update(terms)

            elif kind == b"PHRASE":
                if not (rest.startswith(b'"') and rest.endswith(b'"')):
                    raise ValueError(f"Invalid PHRASE query: {line!r}")

                # LIST, not tuple: token slices are lists, and list != tuple.
                terms = rest[1:-1].split(b" ")

                if not 2 <= len(terms) <= 8 or any(not t for t in terms):
                    raise ValueError(f"Invalid PHRASE query: {line!r}")

                queries.append((1, terms, ()))
                required.update(terms)

            else:
                     terms = rest[1:-1].split(b" ")

    return queries, required


def build_index(path, required):
    texts = []
    index = {term: set() for term in required}

    with open(path, "rb", buffering=1024 * 1024) as f:
        for expected_id, line in enumerate(f):
            if line.endswith(b"\n"):
                line = line[:-1]

            tab = line.find(b"\t")
            if tab < 0:
                raise ValueError("Malformed document: missing TAB")

            doc_id = int(line[:tab])
            if doc_id != expected_id:
                raise ValueError("Document IDs are not dense and ordered")

            text = line[tab + 1:]
            texts.append(text)

            for term in set(TOKEN_RE.findall(text.lower())):
                posting = index.get(term)
                if posting is not None:
                    posting.add(doc_id)

    return texts, index


def eval_bool(terms, operators, index):
    result = index.get(terms[0], EMPTY)

    # Strict left-to-right evaluation.
    for op, term in zip(operators, terms[1:]):
        other = index.get(term, EMPTY)
        if op == b"AND":
            result = result & other
        elif op == b"OR":
            result = result | other
        else:  # NOT (operators validated at parse time)
            result = result - other

    return result


def phrase_matches(text, phrase, first, width):
    tokens = TOKEN_RE.findall(text.lower())
    for i, tok in enumerate(tokens):
        if tok == first and tokens[i:i + width] == phrase:
            return True
    return False


def eval_phrase(terms, index, texts):
    postings = [index.get(term, EMPTY) for term in terms]

    rarest = min(postings, key=len)
    if not rarest:
        return EMPTY

    candidates = set(rarest)
    for posting in postings:
        if posting is rarest:
            continue
        candidates.intersection_update(posting)
        if not candidates:
            return EMPTY

    first = terms[0]
    width = len(terms)
    return {d for d in candidates if phrase_matches(texts[d], terms, first, width)}


def format_result(matches):
    count = len(matches)
    if count == 0:
        return b"0 0"
    smallest = heapq.nsmallest(10, matches)
    return (f"{count} {sum(matches)} " + " ".join(map(str, smallest))).encode("ascii")


def main(data_dir, out_dir):
    queries, required = parse_queries(os.path.join(data_dir, "queries.txt"))
    texts, index = build_index(os.path.join(data_dir, "docs.txt"), required)

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.txt"), "wb", buffering=1024 * 1024) as out:
        for kind, terms, operators in queries:
            if kind == 0:
                matches = eval_bool(terms, operators, index)
            else:
                matches = eval_phrase(terms, index, texts)
            out.write(format_result(matches))
            out.write(b"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/data")
    parser.add_argument("--out", default="/out")
    args = parser.parse_args()
    main(args.data, args.out)