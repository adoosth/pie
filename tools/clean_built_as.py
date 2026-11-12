#!/usr/bin/env python3
"""Drop construction rows whose pieces are not words.

An early reader wrote a piece down as ``str(['کَم ', '>'])`` — a printed list
where a form belongs — and 69 pieces across 34 Persian entries reached the
built lexicon that way.  A page cannot show such a row honestly (it would name
a word that does not exist), so the row is dropped: the entry keeps every row
whose pieces are forms, and a word that has only the malformed row is left with
none, exactly as a word whose record states no construction.

This runs over the *built* glossary and needs no kaikki dump, and it is safe to
run twice.  The reader in ``pie.service`` refuses a malformed piece as well, so
a rebuild that reintroduces one cannot print it either (2026-11-12).

    python3 tools/clean_built_as.py [--write]
"""
import argparse
import gzip
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEXICON = ROOT / "data" / "lexicon"
MALFORMED = re.compile(r"^\s*[\[({]")


def piece_form(piece) -> str:
    value = piece
    while isinstance(value, (list, tuple)) and value:
        value = value[0]
    return str(value or "").strip()


def clean(entry: dict) -> tuple[dict, int]:
    rows = entry.get("built_as") or []
    kept = [row for row in rows
            if all(piece_form(p) and not MALFORMED.match(piece_form(p))
                   for p in (row.get("pieces") or []))]
    dropped = len(rows) - len(kept)
    if not dropped:
        return entry, 0
    entry = dict(entry)
    if kept:
        entry["built_as"] = kept
    else:
        entry.pop("built_as", None)
    return entry, dropped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="rewrite the glossaries")
    ap.add_argument("--only", nargs="*", help="language ids to clean")
    args = ap.parse_args()
    total = 0
    for path in sorted(LEXICON.glob("*.jsonl.gz")):
        lang = path.name.split(".")[0]
        if args.only and lang not in args.only:
            continue
        rows, changed = [], 0
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                entry, dropped = clean(json.loads(line))
                changed += dropped
                rows.append(entry)
        if changed:
            print(f"{path.name}: {changed} malformed construction rows")
            total += changed
            if args.write:
                tmp = path.with_suffix(".tmp")
                with gzip.open(tmp, "wt", encoding="utf-8") as fh:
                    for entry in rows:
                        fh.write(json.dumps(entry, ensure_ascii=False,
                                            separators=(",", ":")) + "\n")
                tmp.replace(path)
    print(f"{total} rows {'dropped' if args.write else 'would be dropped'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
