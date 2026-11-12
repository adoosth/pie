#!/usr/bin/env python3
"""Put the relation labels of every stored etymology tree back in brackets.

Wiktextract welds a tree's label onto the term before it (``*peh₂-der.``), so a
published glossary cannot tell a Proto-Indo-European suffix ``-der`` from
Wiktionary's "derived terms" arrow.  ``pie.etymtext`` locates the tree block and
brackets each label; this tool applies it to the glossaries already in ``data/``
without touching any other field, so the corpus, the ancestry links and the
coverage numbers stay exactly as they are.

    python3 tools/repair_etym_labels.py            # report only
    python3 tools/repair_etym_labels.py --write    # rewrite data/lexicon/*.jsonl.gz
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

from pie import etymtext  # noqa: E402

LEXICON = ROOT / "data" / "lexicon"
REGISTRY = ROOT / "data" / "language_names.json"

STILL = re.compile(r"(\S)(" + "|".join(re.escape(a) for a in etymtext._ALL) + r")(\?)?(?=\s|$)")


def names() -> set[str]:
    if not REGISTRY.exists():
        return set()
    return {row["name"] for row in json.loads(REGISTRY.read_text(encoding="utf-8"))["languages"].values()}


def rewrite(path: Path, known: set[str], write: bool) -> tuple[int, int, int]:
    """(records read, records changed, labels still welded)."""
    rows = []
    read = changed = 0
    left: list[str] = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            read += 1
            etym = row.get("etym") or ""
            if "Etymology tree" in etym:
                fixed = etymtext.split_labels(etym, known)
                if fixed != etym:
                    row["etym"] = fixed
                    changed += 1
                left.extend(m.group(0) for m in STILL.finditer(row["etym"]))
            rows.append(row)
    if write and changed:
        tmp = path.with_suffix(".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        tmp.replace(path)
    return read, changed, len(left)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="rewrite the glossaries in place")
    ap.add_argument("--only", nargs="*", help="language ids to touch")
    args = ap.parse_args()

    known = names()
    total_read = total_changed = total_left = 0
    for path in sorted(LEXICON.glob("*.jsonl.gz")):
        if args.only and path.name[: -len(".jsonl.gz")] not in args.only:
            continue
        read, changed, left = rewrite(path, known, args.write)
        total_read += read
        total_changed += changed
        total_left += left
        if changed or left:
            print(f"{path.name:>18}  {read:>7} records  {changed:>6} changed  {left:>4} still welded")
    verb = "rewritten" if args.write else "would change"
    print(f"\n{total_changed} of {total_read} records {verb}; {total_left} labels still welded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
