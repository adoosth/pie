#!/usr/bin/env python3
"""Measure what peo~pal:final_h_loss does to the Persian corpus.

For every identified fa entry, derive from every ancestor with the law on and
off, and report the words whose closest derivation changes.  Diagnostic only.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling
from pie.rules import derive
import coverage as cov

LANG = "fa"
KEY = "peo~pal:final_h_loss"
rs = data.rulesets()
chain = data.derivation_chain(LANG)
entries = data.lexicon(LANG)
eligible = [e for e in entries if cov.ancestor_starts(e, chain)]

def best(entry, disabled=()):
    best = None; best_distance = 10**6; fired = False
    for stage, form in cov.ancestor_starts(entry, chain):
        try:
            d = derive(form, chain[chain.index(stage):], rs, disabled=disabled)
        except Exception:
            return None
        if d.skipped:
            continue
        if d.output == entry["word"].strip() and d.steps:
            return (stage, form, d)
        dist = cov.distance(d.output.lower(), entry["word"].strip().lower())
        if dist < best_distance:
            best, best_distance = (stage, form, d), dist
    return best

changed = []
for entry in eligible:
    word = entry["word"].strip()
    on = best(entry)
    off = best(entry, disabled=(KEY,))
    if on is None or off is None:
        continue
    if on[2].output != off[2].output and any(s.rule_id == "final_h_loss" for s in on[2].steps):
        changed.append((word, entry.get("ipa") or "", on, off))

print(f"identified fa entries          {len(eligible)}")
print(f"closest derivation changes     {len(changed)}")
print(f"of those, record ends in ه     {sum(1 for w, *_ in changed if w.endswith('ه'))}")
print(f"of those, record ends in h     {sum(1 for w, *_ in changed if w.endswith('h'))}")
uniq = {}
for word, ipa, on, off in changed:
    uniq.setdefault(word, (ipa, on, off))
print(f"distinct words                 {len(uniq)}\n")
for word, (ipa, on, off) in sorted(uniq.items()):
    print(f"{word}  {ipa}   stage={on[0]} anc={on[1]}")
    print(f"   on : {' > '.join(on[2].forms)}   => {on[2].output} -> {spelling.spell(on[2].output, LANG)}")
    print(f"   off: {' > '.join(off[2].forms)}   => {off[2].output} -> {spelling.spell(off[2].output, LANG)}")
    print(f"   steps on: {[s.rule_id for s in on[2].steps]}")
    print()
