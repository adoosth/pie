#!/usr/bin/env python3
"""Measure candidate conventions by their effect on the *written* form.

Each candidate is a whole-word rewrite applied on top of the installed layer.
A candidate is scored with the same rule as coverage: written == recorded word
AND spelling.plausible(derived, ipa).  `fix` counts misses it would win,
`break` counts words it currently wins and would lose.  A convention that only
moves letters between words (fix - break <= 0) is not a convention: it is a
lexical choice.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from pie import spelling  # noqa: E402

rows = list(csv.DictReader(open(Path(__file__).with_name("misses.tsv"), encoding="utf-8"),
                           delimiter="\t"))

def counted(written: str, r: dict) -> bool:
    return written == r["word"] and r["plausible"] == "True"

CANDS = {
    "final ā as ه":          lambda s: re.sub(r"ا$", "ه", s),
    "final -e/-a as ا":      lambda s: re.sub(r"ه$", "ا", s),
    "initial short a as آ":  lambda s: "آ" + s[1:] if s.startswith("ا") else s,
    "خا- as خوا-":           lambda s: "خوا" + s[2:] if s.startswith("خا") else s,
    "خوا- as خا-":           lambda s: "خا" + s[3:] if s.startswith("خوا") else s,
    "final ه written ی":     lambda s: s[:-1] + "ی" if s.endswith("ه") else s,
    "drop final ه":          lambda s: s[:-1] if s.endswith("ه") else s,
    "drop final ا":          lambda s: s[:-1] if s.endswith("ا") else s,
    "drop final و":          lambda s: s[:-1] if s.endswith("و") else s,
    "drop final ی":          lambda s: s[:-1] if s.endswith("ی") else s,
    "final -āy as ی":        lambda s: re.sub(r"ای$", "ی", s),
    "drop final ن":          lambda s: s[:-1] if s.endswith("ن") else s,
}
base_wins = sum(1 for r in rows if counted(r["written"], r))
print(f"installed layer: {base_wins} spelled+plausible words among the misses\n")
for name, fn in CANDS.items():
    fix = break_ = 0
    for r in rows:
        now, new = counted(r["written"], r), counted(fn(r["written"]), r)
        fix += new and not now
        break_ += now and not new
    print(f"{name:22s} fix {fix:3d}  break {break_:3d}  net {fix - break_:+d}")
