#!/usr/bin/env python3
"""Which words would `final_h_loss` alone decide?

Hold the ancestor fixed (chosen with the law on), derive with the law on and
off, spell both, and report every word where only the h changes the spelling.
Also print the ladder of every entry whose *recorded IPA* ends in /h/ and whose
best derivation fired the law: those are the only words whose h it could be
wrong to delete.
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


def best(entry):
    best = None; best_distance = 10**6
    for stage, form in cov.ancestor_starts(entry, chain):
        try:
            d = derive(form, chain[chain.index(stage):], rs)
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


print("== every word where switching the law off changes the SPELLED form to the record")
seen = set()
for entry in eligible:
    word = entry["word"].strip()
    got = best(entry)
    if got is None or word in seen:
        continue
    stage, form, d = got
    if not any(s.rule_id == "final_h_loss" for s in d.steps):
        continue
    d2 = derive(form, chain[chain.index(stage):], rs, disabled=(KEY,))
    on_w, off_w = spelling.spell(d.output, LANG), spelling.spell(d2.output, LANG)
    if off_w == word and on_w != word:
        seen.add(word)
        ok = spelling.plausible(d2.output, entry.get("ipa") or "")
        print(f"  {word:8s} ipa={entry.get('ipa',''):14s} on={d.output!r}->{on_w}  "
              f"off={d2.output!r}->{off_w}  plausible(off)={ok}  anc={stage}:{form}")

print("\n== entries whose recorded IPA ends in /h/ and whose best derivation fired the law")
for entry in eligible:
    word = entry["word"].strip()
    ipa = entry.get("ipa") or ""
    if not ipa.replace(" ", "").rstrip("/]").endswith("h"):
        continue
    got = best(entry)
    if got is None:
        continue
    stage, form, d = got
    if not any(s.rule_id == "final_h_loss" for s in d.steps):
        continue
    d2 = derive(form, chain[chain.index(stage):], rs, disabled=(KEY,))
    print(f"  {word:8s} {ipa:14s} on={d.output!r}->{spelling.spell(d.output, LANG)}   "
          f"off={d2.output!r}->{spelling.spell(d2.output, LANG)}  anc={stage}:{form}")
