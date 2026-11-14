#!/usr/bin/env python3
"""What would a notation-folding guard count?  Diagnostic only, no src edit.

`spelling.plausible` folds the *dictionary's* IPA notation (ɡ, ɾ, the tie bar)
but not the model's philological letters, so č is compared with t͡ʃ and ā with
aː as if they were different segments.  This patches `_readable` in memory (the
module's own normalisation point, used for both sides) and re-measures.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from pie import spelling  # noqa: E402

ORIG = spelling._readable


def folded(text: str) -> str:
    out = ORIG(text)
    for a, b in (("tʃ", "č"), ("dʒ", "ǰ"), ("ʃ", "š"), ("ʒ", "ž"),
                 ("aː", "ā"), ("iː", "ī"), ("uː", "ū"), ("eː", "ī"),
                 ("oː", "ū"), ("j", "y"), ("ɡ", "g")):
        out = out.replace(a, b)
    return out


before = spelling.plausible
spelling._readable = folded
spelling.plausible.__globals__["_readable"] = folded
import covmirror as m  # noqa: E402  (import after the patch: module-level use is a call)

res = m.measure()
print(f"fa counted with the guard as it stands : 103 (published)")
print(f"fa counted with notation folded         : {len(res['counted'])}")
print(f"fa misses                               : {len(res['missed'])}")
