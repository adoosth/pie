#!/usr/bin/env python3
"""How much of the remaining gap is the guard's *notation*, not the letters?

For every identified fa entry, walk the ancestor candidates exactly as
coverage.py does and record the first derivation whose spelling equals the
record.  Then ask why it was not counted: plausible() (and if so, whether the
only disagreement is notation: same segments after folding č/š/ž/ǰ and ā/ī/ū)
or "no law fired".
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import covmirror as m  # noqa: E402
from pie import spelling  # noqa: E402

FOLD = {"t͡ʃ": "č", "tʃ": "č", "d͡ʒ": "ǰ", "dʒ": "ǰ", "ʃ": "š", "ʒ": "ž",
        "ɡ": "g", "ɹ": "r", "ɾ": "r", "ʁ": "r", "ʀ": "r", "ʔ": "ʾ",
        "j": "y"}
VOWEL = {"æ": "a", "ɑ": "ā", "ɒ": "ā", "aː": "ā", "iː": "ī", "uː": "ū",
         "oː": "ū", "eː": "ī", "ɛ": "e", "ɔ": "o", "ʊ": "u", "ɪ": "i",
         "ə": "e", "y": "i", "ø": "e", "œ": "e"}
LONG = {"aː": "ā", "iː": "ī", "uː": "ū", "oː": "ū", "eː": "ī"}


def segments(text: str) -> list[str]:
    text = re.sub(r"[/\[\]().|ˈˌ\u203f]", "", text or "").replace("\u0329", "")
    out, i, keys = [], 0, sorted(FOLD, key=len, reverse=True)
    while i < len(text):
        if unicodedata.category(text[i]) == "Mn":
            i += 1
            continue
        for k in keys:
            if text.startswith(k, i):
                out.append(FOLD[k]); i += len(k); break
        else:
            out.append(text[i]); i += 1
    merged = []
    for tok in out:
        if tok == "ː" and merged:
            merged[-1] = LONG.get(merged[-1] + "ː", merged[-1] + "ː")
            continue
        merged.append(tok)
    return [VOWEL.get(t, t) for t in merged]


def report():
    right = counted = guard = notated = zero = 0
    rows = []
    for entry in m.ELIGIBLE:
        target = entry["word"].strip()
        ipa = entry.get("ipa") or ""
        hit = None          # first spelling hit that fired a law (for the guard)
        passed = None       # ... and passes plausible() (coverage counts this one)
        fallback = None     # spelling hit in which no law fired
        for stage, form in m.cov.ancestor_starts(entry, m.CHAIN):
            d = m.derive(form, m.CHAIN[m.CHAIN.index(stage):], m.RULESETS)
            if d.skipped:
                continue
            if spelling.spell(d.output, m.LANG) == target:
                if not d.steps:
                    if fallback is None:
                        fallback = (d.output, stage, d)
                    continue
                if hit is None:
                    hit = (d.output, stage, d)
                if spelling.plausible(d.output, ipa):
                    passed = (d.output, stage, d)
                    break
        if passed is not None:
            hit = passed
        elif hit is None and fallback is not None:
            hit = fallback
        if hit is None:
            continue
        right += 1
        output, stage, d = hit
        ok = bool(d.steps) and spelling.plausible(output, ipa)
        if ok:
            counted += 1
        elif not d.steps:
            zero += 1
        else:
            guard += 1
            if segments(output) == segments(ipa):
                notated += 1
                rows.append((target, output, ipa, stage))

    print(f"identified                         {len(m.ELIGIBLE)}")
    print(f"spelling equals the record         {right}")
    print(f"  counted (law fired + plausible)  {counted}")
    print(f"  no law fired (identity)          {zero}")
    print(f"  rejected by plausible()          {guard}")
    print(f"    of those, segments identical   {notated}   <- notation only")
    print("\nthe notation-only rejections:")
    for w, o, ipa, stage in rows:
        print(f"  {w:8s} {o:10s} {ipa:16s} ({stage})")


if __name__ == "__main__":
    report()
