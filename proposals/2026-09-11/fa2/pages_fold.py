#!/usr/bin/env python3
"""Page-level count with the guard's notation folded in memory (no src edit)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from pie import data, service, spelling  # noqa: E402

ORIG = spelling._readable


def folded(text: str) -> str:
    out = ORIG(text)
    for a, b in (("tʃ", "č"), ("dʒ", "ǰ"), ("ʃ", "š"), ("ʒ", "ž"),
                 ("aː", "ā"), ("iː", "ī"), ("uː", "ū"), ("eː", "ī"),
                 ("oː", "ū"), ("j", "y")):
        out = out.replace(a, b)
    return out


spelling._readable = folded
words = sorted({e["word"].strip() for e in data.lexicon("fa")})
match = []
for w in words:
    page = service.word("fa", w) or {}
    res = (page.get("hierarchy") or {}).get("result") or {}
    if res.get("written_match"):
        match.append(w)
print(f"{len(match)} of {len(words)} pages with notation folded")
