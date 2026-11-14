#!/usr/bin/env python3
"""Group the cause-(a) misses by the shape of the difference between the law's
output and the word's own reading, so a systematic law can be told from a
one-off.  Diagnostic only."""
from __future__ import annotations
import csv, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from classify import segments  # reuse the same folding

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "classified.tsv", encoding="utf-8"), delimiter="\t"))

def diff(a, b):
    """Longest-common-subsequence edit script, compact."""
    import difflib
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append(f"{'-' + ''.join(a[i1:i2]) if i1 != i2 else ''}{'+' + ''.join(b[j1:j2]) if j1 != j2 else ''}")
    return " ".join(out)

groups = defaultdict(list)
stage = sys.argv[1] if len(sys.argv) > 1 else "pal"
cause = sys.argv[2] if len(sys.argv) > 2 else "a"
for r in rows:
    if r["near_stage"] != stage or r["cause5"] != cause:
        continue
    out, w = segments(r["output"]), segments(r["ipa"] or r["translit"])
    if not out or not w:
        groups["<no reading/output>"].append(r); continue
    groups[diff(out, w)].append(r)

for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"{len(v):>3}  {k:<28}  {', '.join(sorted({x['word'] for x in v})[:10])}")
