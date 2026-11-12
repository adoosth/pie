#!/usr/bin/env python3
"""final_h_loss: fixed-ancestor measurement (the right population).

The previous script let disabling the law change which ancestor is 'closest',
which inflates the count.  Here the ancestor chosen with the law ON is held
fixed and only the law is toggled.
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
    best = None; best_distance = 10**6
    for stage, form in cov.ancestor_starts(entry, chain):
        try:
            d = derive(form, chain[chain.index(stage):], rs, disabled=disabled)
        except Exception:
            return None
        if d.skipped:
            continue
        if d.output == entry["word"].strip() and d.steps:
            return (stage, form, d, True)
        dist = cov.distance(d.output.lower(), entry["word"].strip().lower())
        if dist < best_distance:
            best, best_distance = (stage, form, d, False), dist
    return best

fired = kept_h = 0
rows = []
for entry in eligible:
    word = entry["word"].strip()
    got = best(entry)
    if got is None:
        continue
    stage, form, d, exact = got
    if not any(s.rule_id == "final_h_loss" for s in d.steps):
        continue
    fired += 1
    d2 = derive(form, chain[chain.index(stage):], rs, disabled=(KEY,))
    out_on, out_off = d.output, d2.output
    if out_off == out_on:
        continue
    # the h the law deletes is the last segment of the pre-law form
    ends_h = out_off.rstrip("ˈ").endswith(("h", "hah"))
    record_h = word.endswith(("ه", "اه"))
    if record_h:
        kept_h += 1
    rows.append((word, entry.get("ipa") or "", stage, form, out_on, out_off, record_h, exact))

print(f"identified entries                     {len(eligible)}")
print(f"entries whose best derivation fires    {fired}")
print(f"  output differs when law is off       {len(rows)}")
print(f"  and the record ends in ه/اه          {kept_h}")
print()
seen = {}
for word, ipa, stage, form, on, off, rec, exact in rows:
    if rec:
        seen.setdefault(word, []).append((ipa, stage, form, on, off))
for word, lst in sorted(seen.items()):
    for ipa, stage, form, on, off in lst:
        print(f"{word}  {ipa}  anc={stage}:{form}")
        print(f"   with law   {on!r} -> {spelling.spell(on, LANG)!r}")
        print(f"   without    {off!r} -> {spelling.spell(off, LANG)!r}")
