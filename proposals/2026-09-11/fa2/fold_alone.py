#!/usr/bin/env python3
"""Attribute the guard's notation gap: one fold at a time (fa)."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from pie import spelling  # noqa: E402

ORIG = spelling._readable
FOLDS = {
    "affricate tʃ→č": [("tʃ", "č")],
    "affricate dʒ→ǰ": [("dʒ", "ǰ")],
    "ʃ→š": [("ʃ", "š")],
    "ʒ→ž": [("ʒ", "ž")],
    "aː→ā": [("aː", "ā")],
    "iː/eː→ī": [("iː", "ī"), ("eː", "ī")],
    "uː/oː→ū": [("uː", "ū"), ("oː", "ū")],
    "j→y": [("j", "y")],
}
import covmirror as m  # noqa: E402

base = len(m.measure()["counted"])
print(f"published             {base}")
for name, pairs in FOLDS.items():
    def folded(text, pairs=pairs):
        out = ORIG(text)
        for a, b in pairs:
            out = out.replace(a, b)
        return out
    spelling._readable = folded
    print(f"+ {name:18s} {len(m.measure()['counted'])}")
spelling._readable = ORIG
