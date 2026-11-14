"""Sanskrit: why does a spelled form not count? (guard-blocked vs letter-miss)."""
from __future__ import annotations
import sys, difflib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
from pie import data, spelling, citation
from pie.rules import derive
from coverage import (ancestor_starts, exact_kind, orthographic_hit,
                      citation_hit, _identity_hit, distance)

LANG = "sa"
chain = data.derivation_chain(LANG); rs = data.rulesets()

def unaccent(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")

guard_block = Counter(); guard_ex = defaultdict(list)
stem_block = Counter(); stem_ex = defaultdict(list)
spellable = 0
for entry in data.lexicon(LANG):
    target = str(entry.get("word") or "").strip()
    if not target or entry.get("recon"):
        continue
    cands = ancestor_starts(entry, chain)
    if not cands:
        continue
    ipa = entry.get("ipa") or ""
    for stage, form in cands:
        d = derive(form, chain[chain.index(stage):], rs)
        if d.skipped or not d.steps:
            continue
        out = d.output
        # full form
        if spelling.spell(out, LANG) == target and not spelling.plausible(out, ipa, LANG):
            f = spelling._skeleton(spelling._readable(out))
            g = spelling._skeleton(spelling._readable(re.sub(r"[/\[\]() ]", "", ipa)))
            guard_block[(f[0] == g[0], f[1] == g[1])] += 1
            if len(guard_ex[(f[0]==g[0], f[1]==g[1])]) < 12:
                guard_ex[(f[0]==g[0], f[1]==g[1])].append((target, out, spelling.spell(out,LANG), ipa, f[0], g[0]))
        # stem
        for end in citation.endings(LANG):
            if not out.endswith(end) or len(out) <= len(end):
                continue
            stem = out[:-len(end)]
            if spelling.spell(stem, LANG) == target:
                if spelling.plausible(stem, ipa, LANG):
                    stem_block["OK"] += 1
                else:
                    f = spelling._skeleton(spelling._readable(stem))
                    g = spelling._skeleton(spelling._readable(re.sub(r"[/\[\]() ]", "", ipa)))
                    key = (tuple(f[0]), tuple(g[0]), f[1], g[1])
                    stem_block["PLAUSIBLE_FALSE"] += 1
                    if len(stem_ex["PLAUSIBLE_FALSE"]) < 25:
                        stem_ex["PLAUSIBLE_FALSE"].append((target, out, end, stem, ipa, f[0], g[0]))
                break

print("spelled==target but guard says no:", sum(guard_block.values()))
for k, v in guard_block.items():
    print("  cons_eq,vow_eq", k, v)
    for e in guard_ex[k][:6]:
        print("     ", e)
print()
print("stem spelled==target:", stem_block)
for e in stem_ex["PLAUSIBLE_FALSE"][:25]:
    print("   ", e)
