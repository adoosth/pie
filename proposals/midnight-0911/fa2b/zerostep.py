#!/usr/bin/env python3
"""What the `steps > 0` gate in tools/coverage.py costs the Persian counter.

`orthographic_hit` and the script layer both require `steps`, so a word whose
nearest recorded ancestor is already its New Persian phonemic form — nothing to
change — is never offered to the writing conventions.  This counts those words
with the same spelling layer and the same reading guard the counter uses.
Diagnostic only; it does not change any number the repo publishes.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import importlib.util
spec = importlib.util.spec_from_file_location("ct", ROOT / "tools" / "coverage.py")
ct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct)

from pie import data, script, spelling       # noqa: E402
from pie.rules import derive                 # noqa: E402

lang = sys.argv[1] if len(sys.argv) > 1 else "fa"
chain = data.derivation_chain(lang)
rulesets = data.rulesets()

orth, scr, neither, already = [], [], [], 0
for entry in data.lexicon(lang):
    if entry.get("recon"):
        continue
    target = entry["word"].strip()
    ipa = entry.get("ipa") or ""
    got = False
    for stage, form in ct.ancestor_starts(entry, chain):
        d = derive(form, chain[chain.index(stage):], rulesets)
        if d.skipped:
            continue
        if d.output == target and d.steps:
            already += 1; got = True; break
        if d.steps:
            continue                     # a word the counter can already see
        if spelling.applies(lang) and spelling.spell(d.output, lang) == target \
                and spelling.plausible(d.output, ipa, lang):
            orth.append((target, stage, d.output)); got = True; break
        fit = script.match(lang, d.output, target)
        if fit and fit.get("ok"):
            scr.append((target, stage, d.output)); got = True; break
        if d.output == target:
            neither.append((target, stage, d.output)); got = True; break
    if not got:
        continue

print(f"{lang}: zero-step words the counter cannot see")
print(f"  would be spelled by the orthographic layer : {len(orth)}")
for w in orth: print("     ", w[2], "→", w[0], f"[{w[1]}]")
print(f"  would be read through its own script      : {len(scr)}")
for w in scr[:20]: print("     ", w[2], "→", w[0], f"[{w[1]}]")
print(f"  identical form, no layer claims it        : {len(neither)}")
for w in neither[:20]: print("     ", w[2], f"[{w[1]}]")
