#!/usr/bin/env python3
"""Repair the ancestry codes the lexicons copied from etymology-tree markup.

Five shapes in ``data/lexicon/*.jsonl.gz`` are not language codes, and a rung
that prints one is a rung that prints nothing:

* ``"['fro"`` / ``'["pal'`` — a Python list repr leaked into the code field.
  The row is the same as the clean row beside it, so it is normalised and the
  duplicate is dropped.
* ``"ML."``, ``"LL."``, ``"NL."``, ``"VL."``, ``"EL."`` — the abbreviated
  Latin stages; they are rewritten to Wiktionary's own codes (``la-med`` …).
* ``"ety"`` (the affix marker), ``"unc"`` (an "uncertain" marker) and ``"w"``
  (a mangled same-language tree node) — markers, not languages; the row is
  removed.
* a root row whose first field is the *root's spelling* rather than a language
  (``["समाविश्", "आविश्", "root"]``) — the language is the entry's own, so the
  row becomes ``["sa", "आविश्", "root"]``.
* ``"xcL"`` — a case typo for ``xcl``.

Exact duplicate rows after that normalisation are dropped.  Every file is
rewritten only when a row changed, in the same compact one-record-per-line
form `tools/build_lexicons.py` writes.

Usage:
    python3 tools/repair_anc_codes.py --dry-run
    python3 tools/repair_anc_codes.py
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data  # noqa: E402

LEXICON = ROOT / "data" / "lexicon"
#: Codes that name a marker rather than a language.
MARKERS = {"ety", "unc", "w"}
CODE = re.compile(r"[a-z][a-z0-9-]*")


def repair_row(row: list, lang: str, stats: Counter) -> list | None:
    code = str(row[0])
    if code.startswith("['") or code.startswith('["'):
        stats["bracket"] += 1
        code = code[2:]
    if code == "xcL":
        stats["case"] += 1
        code = "xcl"
    if code in data.LATIN_STAGE_ABBREVIATIONS:
        stats["abbreviation"] += 1
        code = data.LATIN_STAGE_ABBREVIATIONS[code]
    if code in MARKERS:
        stats["marker"] += 1
        return None
    if len(row) > 2 and str(row[2]) == "root" and not CODE.fullmatch(code) \
            and not code.startswith(":"):
        stats["root"] += 1
        code = lang
    return [code, *row[1:]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = Counter()
    touched_files = 0
    touched_entries = 0
    for path in sorted(LEXICON.rglob("*.jsonl.gz")):
        rows = []
        changed = False
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                before = entry.get("anc") or []
                after, seen = [], set()
                for row in before:
                    if not (isinstance(row, list) and row):
                        after.append(row)
                        continue
                    fixed = repair_row(row, str(entry.get("lang") or ""), stats)
                    if fixed is None:
                        continue
                    key = json.dumps(fixed, ensure_ascii=False)
                    if key in seen:
                        stats["duplicate"] += 1
                        continue
                    seen.add(key)
                    after.append(fixed)
                if after != before:
                    entry["anc"] = after
                    changed = True
                    touched_entries += 1
                rows.append(entry)
        if not changed:
            continue
        touched_files += 1
        if args.dry_run:
            continue
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
                for entry in rows:
                    gz.write((json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
                              + "\n").encode("utf-8"))
        tmp.replace(path)

    print(f"{'would touch' if args.dry_run else 'touched'} {touched_entries} entries "
          f"in {touched_files} files")
    for key in ("bracket", "abbreviation", "marker", "root", "case", "duplicate"):
        print(f"  {key:13s} {stats[key]:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
