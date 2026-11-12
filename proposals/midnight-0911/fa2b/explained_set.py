#!/usr/bin/env python3
"""Print every Persian headword the published counter explains (all layers).

Used to attribute a delta to the change that caused it: run the same file in a
clean checkout and diff the two lists.  Mirrors tools/coverage.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, pathways, script, spelling      # noqa: E402
from pie.rules import derive                          # noqa: E402
import coverage as cov                                # noqa: E402

LANG = "fa"
RULES = data.rulesets()
CHAIN = data.derivation_chain(LANG)
DEFAULTS = pathways.defaults()

out = []
for e in data.lexicon(LANG):
    t = e["word"].strip()
    cands = cov.ancestor_starts(e, CHAIN)
    if not cands:
        continue
    ipa = e.get("ipa") or ""
    outputs, here, orth, cit = [], False, None, None
    for st, f in cands:
        d = derive(f, CHAIN[CHAIN.index(st):], RULES)
        if d.skipped:
            continue
        outputs.append((d.output, len(d.steps), st))
        if orth is None:
            orth = cov.orthographic_hit([outputs[-1]], LANG, t, ipa)
        if cit is None and orth is None:
            cit = cov.citation_hit([outputs[-1]], LANG, t, ipa)
        if d.steps and cov.exact_kind(d.output, t):
            here = True
        elif orth or cit:
            here = True
        elif d.steps and (script.match(LANG, d.output, t) or {}).get("ok"):
            here = True
        else:
            if cov._identity_hit([outputs[-1]], t, e) is not None:
                here = True
            if "-" in t and cov._bound_pair(d.output, t):
                here = True
    if here:
        out.append(t)
print("\n".join(sorted(out)))
