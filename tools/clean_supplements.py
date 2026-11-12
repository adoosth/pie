#!/usr/bin/env python3
"""Drop obviously mis-parsed rows from the hand-built supplement lexicons.

The Pahlavi entries come from OCR'd dictionary pages and the Avestan ones from
raw Wiktionary wikitext; both produce a few artefacts (a headword and its
transliteration run together, "see X" cross-references, script-table rows).
This keeps the supplement honest without pretending to be a full parser.

    python tools/clean_supplements.py
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPP = ROOT / "data" / "lexicon" / "_supplement"

BAD_GLOSS = re.compile(
    r"^(=+|used to represent|see |cf\.|compare |var\. of|alternative form of a letter|the (first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last) letter|a letter of)",
    re.I,
)


def keep(row: dict) -> bool:
    word = (row.get("word") or "").strip()
    gloss = (row.get("gloss") or [""])[0]
    if not word or re.search(r"\s", word):
        return False
    if not any(ch.isalpha() for ch in word):
        return False
    if BAD_GLOSS.match(gloss.strip()):
        return False
    return True


def main() -> int:
    for path in sorted(SUPP.glob("*.jsonl.gz")):
        rows = [json.loads(line) for line in gzip.open(path, "rt", encoding="utf-8")]
        keepers = [r for r in rows if keep(r)]
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            for row in keepers:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(f"{path.name}: {len(rows)} → {len(keepers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
