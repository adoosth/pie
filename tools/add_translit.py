#!/usr/bin/env python3
"""Add romanisations to glossary entries whose script is not Latin.

The rule engine works on transliterations (``pedar``, ``patēr``, ``hayr``), so a
word page for a Greek, Armenian, Persian, Sanskrit or cuneiform entry can only
compare the derivation with the attested form if the entry carries its
romanisation. Wiktionary records it in ``forms`` with the tag ``romanization``;
we copy it into the entry as ``translit`` (plus ``translit_alt`` when a word has
several accepted readings).

    python3 tools/add_translit.py --src /home/cloud/kaikki --langs fa grc el hy xcl sa peo chu hit got
    python3 tools/add_translit.py --check        # only report what is missing
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
DATA = ROOT / "data"

from build_lexicons import DUMP_TO_ID, clean  # noqa: E402


def romanisations(entry: dict) -> list[str]:
    out: list[str] = []
    for f in entry.get("forms") or []:
        if "romanization" not in (f.get("tags") or []):
            continue
        value = clean(f.get("form"), 80)
        if not value or any(ch in value for ch in " ,;") or value in out:
            continue
        out.append(value)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/home/cloud/kaikki")
    ap.add_argument("--langs", nargs="*", default=["fa", "grc", "el", "hy", "xcl", "sa", "peo", "chu", "hit", "got"])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    wanted = {lang: dump for dump, lang in DUMP_TO_ID.items() if lang in set(args.langs)}
    missing_total = 0
    for lang, dump in sorted(wanted.items()):
        lex_path = DATA / "lexicon" / f"{lang}.jsonl.gz"
        if not lex_path.exists():
            continue
        if args.check:
            with gzip.open(lex_path, "rt", encoding="utf-8") as fh:
                rows = [json.loads(line) for line in fh]
            missing = sum(1 for r in rows if not r.get("translit"))
            missing_total += missing
            print(f"{lang:<8} {len(rows) - missing:>6} / {len(rows):<6} have a romanisation")
            continue
        src = Path(args.src) / f"{dump}.jsonl"
        if not src.exists():
            print(f"{lang:<8} no dump at {src}", file=sys.stderr)
            continue
        forms: dict[str, list[str]] = {}
        with src.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                word = entry.get("word")
                if not word:
                    continue
                roman = romanisations(entry)
                if not roman:
                    continue
                bucket = forms.setdefault(word, [])
                for r in roman:
                    if r not in bucket:
                        bucket.append(r)
        rows = []
        patched = 0
        with gzip.open(lex_path, "rt", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                candidates = forms.get(row.get("word", ""), [])
                if candidates and row.get("translit") not in candidates:
                    row["translit"] = candidates[0]
                    if len(candidates) > 1:
                        row["translit_alt"] = candidates[1:]
                    patched += 1
                rows.append(row)
        with gzip.open(lex_path, "wt", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(f"{lang:<8} {patched:>6} / {len(rows):<6} entries got a romanisation")
    if args.check:
        print(f"missing: {missing_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
