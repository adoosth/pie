#!/usr/bin/env python3
"""Audit how many Old Persian rows have a usable modelled ancestor, and why not.

Run from the repo root::

    PYTHONPATH=src:tools python3 proposals/2026-09-11/peo/audit.py

It prints the counts the batch report quotes: the glossary, the rows the
derivation chain can start from (``identified``), the rows that state a modelled
stage in their own etymology text (``stated``), and how the unlinked rows
divide between an absent etymology and an honest non-inherited source.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import ingest_op_entries as ingest          # noqa: E402
from coverage import ancestor_starts        # noqa: E402
from pie import data                        # noqa: E402

STAGE = re.compile(r"prot[o-]?(indo.?iranian|iranian|indo.?european)", re.I)
BORROW = re.compile(
    r"(borrow|loanword|^from (avestan|old median|median|elamite|akkadian|"
    r"sumerian|demotic egyptian|egyptian|semitic|greek|sanskrit|old persian))",
    re.I,
)


def classify(entry: dict) -> str:
    text = (entry.get("etym") or "").strip()
    if not text:
        return "no etymology text"
    if STAGE.search(text):
        return "names a modelled stage"
    if BORROW.search(text):
        return "borrowed from a non-modelled language"
    low = text.lower()
    if ("equivalent to" in low or re.search(r"\bfrom\b.*\+", low)
            or "compound" in low or "suffix" in low):
        return "internal formation (suffix or compound)"
    if re.search(r"cognate|compare|akin|related to|see also|parallel", low):
        return "cognate only"
    if re.search(r"disputed|uncertain|unknown|presumably|obscure|unclear", low):
        return "disputed or uncertain origin"
    return "other (from a named but unmodelled source)"


def main() -> None:
    chain = data.derivation_chain("peo")
    rows = list(data.lexicon("peo"))
    linked = [e for e in rows if ancestor_starts(e, chain)]
    unlinked = [e for e in rows if not ancestor_starts(e, chain)]
    stated = [e for e in rows if ingest.stated_ancestry(e)]
    missing = [e for e in stated
               if not (set(r[0] for r in ingest.stated_ancestry(e))
                       & ingest._usable_stages(e))]
    print(f"glossary {len(rows)}  identified {len(linked)}  unlinked {len(unlinked)}")
    print(f"rows whose own etymology names a modelled stage: {len(stated)}")
    print(f"  ... of which any stated stage still lacks a usable row: {len(missing)}")
    for stage in ("ira-pro", "iir-pro", "ine-pro"):
        print(f"  stated {stage}: {sum(1 for e in stated for r in ingest.stated_ancestry(e) if r[0] == stage)}")
    print("unlinked rows by cause:")
    for cause, count in Counter(classify(e) for e in unlinked).most_common():
        print(f"  {count:4d}  {cause}")


if __name__ == "__main__":
    main()
