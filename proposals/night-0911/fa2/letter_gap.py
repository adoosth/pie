#!/usr/bin/env python3
"""Under the published rule (spelling tried on every ancestor), is there any
word whose derived PHONEMES match the record's own IPA but whose LETTERS do
not?  Those, and only those, are gaps a writing convention could close.

Segments are compared after folding notation only (č=t͡ʃ, š=ʃ, ž=ʒ, ǰ=d͡ʒ,
y=j, ā=aː, ī=iː, ū=uː, and the vowel qualities the model does not name).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import covmirror as m                     # noqa: E402
from guard_gap import segments            # noqa: E402
from pie import spelling                  # noqa: E402

res = m.measure()
rows = []
for entry, r in res["missed"]:
    target = entry["word"].strip()
    ipa = entry.get("ipa") or ""
    if not ipa:
        continue
    want = segments(ipa)
    for stage, form in m.cov.ancestor_starts(entry, m.CHAIN):
        d = m.derive(form, m.CHAIN[m.CHAIN.index(stage):], m.RULESETS)
        if d.skipped or not d.steps:
            continue
        if segments(d.output) != want:
            continue
        written = spelling.spell(d.output, m.LANG)
        if written == target:
            break                        # already counted (or guard-rejected)
        rows.append((target, d.output, written, ipa, stage, form))
        break

print(f"misses with a segment-identical derivation whose spelling is wrong: {len(rows)}")
for w, o, wr, ipa, stage, anc in rows[:60]:
    print(f"  {w:10s} out={o:12s} written={wr:12s} ipa={ipa:16s} {stage}:{anc}")
