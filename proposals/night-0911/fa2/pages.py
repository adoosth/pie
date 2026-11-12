#!/usr/bin/env python3
"""Count fa word pages whose own fa rung is spelled correctly.

This is the page-level number (the dictionary headword count, one page per
distinct word), as opposed to `coverage.py`'s entry-level orthographic column.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from pie import data, service  # noqa: E402

words = sorted({e["word"].strip() for e in data.lexicon("fa")})
match = []
for i, w in enumerate(words, 1):
    try:
        page = service.word("fa", w)
    except Exception as exc:                       # pragma: no cover
        print(f"ERR {w}: {exc}", file=sys.stderr)
        continue
    res = ((page or {}).get("hierarchy") or {}).get("result") or {}
    if res.get("written_match"):
        match.append((w, res.get("written")))
    if i % 500 == 0:
        print(f"  {i}/{len(words)} pages, {len(match)} matched", flush=True)
Path(__file__).with_name("pages.txt").write_text(
    f"{len(match)} of {len(words)} pages\n" + "\n".join(f"{w}\t{f}" for w, f in match),
    encoding="utf-8")
print(f"{len(match)} of {len(words)} pages")
