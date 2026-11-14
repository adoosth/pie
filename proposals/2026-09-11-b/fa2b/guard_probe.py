#!/usr/bin/env python3
"""Which misses spell right but are refused by the guard, and why?

For every identified fa entry that is not explained, spell each derivation and
look for one whose spelling equals the headword; then split the reason it is
not counted: no law fired, or `spelling.plausible` refused it.  For the refused
ones print the consonant skeleton and vowel count on both sides, which is
exactly what the guard compares, so a notation fold that would help is visible.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).parent))

from pie import data, spelling                            # noqa: E402
from pie.rules import derive                              # noqa: E402
import coverage as cov                                    # noqa: E402
from pie.spelling import _readable, _skeleton, _apply_folds, reading_folds  # noqa: E402

LANG = "fa"
CHAIN = data.derivation_chain(LANG)
RULES = data.rulesets()
folds = reading_folds(LANG)

def skel(x: str):
    return _skeleton(_apply_folds(_readable(x), folds))

rows = []
for e in data.lexicon(LANG):
    t = e["word"].strip()
    cands = cov.ancestor_starts(e, CHAIN)
    if not cands:
        continue
    ipa = e.get("ipa") or ""
    for stage, form in cands:
        try:
            d = derive(form, CHAIN[CHAIN.index(stage):], RULES)
        except Exception:
            continue
        if d.skipped:
            continue
        if spelling.spell(d.output, LANG) != t:
            continue
        rows.append((t, d.output, len(d.steps), ipa, stage,
                     spelling.plausible(d.output, ipa, LANG), skel(d.output), skel(ipa)))
        break
print("misses whose spelling is already the headword:", len(rows))
print(Counter((r[2] > 0, r[5]) for r in rows))
for r in rows:
    if not r[5]:
        print(f"{r[0]:10s} out={r[1]:12s} ipa={r[3]:16s} stages={r[4]:8s} steps={r[2]}"
              f" form={r[6]} ipa={r[7]}")
