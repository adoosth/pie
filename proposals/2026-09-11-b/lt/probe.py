#!/usr/bin/env python3
"""Diagnose the ine-bsl-pro -> lt derivation: exact count, misses, edit ops."""
import json
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data                                   # noqa: E402
from pie.rules import derive                           # noqa: E402
from coverage import (ancestor_starts, exact_kind,     # noqa: E402
                      _identity_hit, distance)


def run():
    chain = data.derivation_chain("lt")
    rulesets = data.rulesets()
    exact = identity = 0
    misses, examples = [], []
    for entry in data.lexicon("lt"):
        target = entry["word"].strip()
        if entry.get("recon"):
            continue
        candidates = ancestor_starts(entry, chain)
        if not candidates:
            continue
        outputs, hit = [], None
        for stage, form in candidates:
            try:
                d = derive(form, chain[chain.index(stage):], rulesets)
            except Exception:
                continue
            if d.skipped:
                continue
            outputs.append((d.output, len(d.steps), stage))
            if d.steps and exact_kind(d.output, target):
                hit = (target, stage, form, d.output, [s.rule_id for s in d.steps])
                break
        if hit:
            exact += 1
            if len(examples) < 10:
                examples.append(hit)
            continue
        if outputs and _identity_hit(outputs, target, entry):
            identity += 1
            continue
        if outputs:
            best = min(outputs, key=lambda o: distance(o[0], target))
            misses.append({"word": target, "stage": best[2], "output": best[0],
                           "ipa": entry.get("ipa", ""),
                           "gloss": (entry.get("gloss") or [""])[0][:30],
                           "anc": [list(c) for c in candidates]})
    return exact, identity, misses, examples


if __name__ == "__main__":
    exact, identity, misses, examples = run()
    print(f"exact {exact}  identity {identity}  misses {len(misses)}  "
          f"tested {exact + identity + len(misses)}")
    print("--- exact examples")
    for ex in examples:
        print("  ", ex)
    print("--- closest misses")
    for m in sorted(misses, key=lambda m: distance(m["output"], m["word"]))[:35]:
        print(f"  {m['word']:18} <- {m['stage']:14} {m['output']:20} {m['ipa']}")
    ops = Counter()
    opex = {}
    for m in misses:
        sm = SequenceMatcher(None, m["output"], m["word"], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            key = (tag, m["output"][i1:i2], m["word"][j1:j2])
            ops[key] += 1
            opex.setdefault(key, []).append(m)
    print("--- edit operations on the misses")
    for key, n in ops.most_common(40):
        print(f"  {key[0]:>7} {key[1]!r:>10} -> {key[2]!r:<10} {n:4} " +
              ", ".join(f"{x['output']}->{x['word']}" for x in opex[key][:4]))
    json.dump(misses, open("/tmp/lt_misses.json", "w"), ensure_ascii=False, indent=1)
