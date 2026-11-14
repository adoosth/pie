#!/usr/bin/env python3
"""Dump every Persian miss with the closest derivation, its ladder and the record.

Mirrors tools/coverage.py's selection (closest ancestor attempt by character
distance; counted only when a law fired and spelling.plausible passes), then
writes one TSV row per word so the misses can be classified by hand.  Diagnostic
only — writes nothing but its own output in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).parent))

from pie import data, spelling
from pie.rules import derive
import coverage as cov

from covmirror import ELIGIBLE, measure  # noqa: E402
from pie import spelling                  # noqa: E402

LANG = "fa"
res = measure()
rows = []
for entry, r in res["missed"]:
    if r.best is None:
        continue
    stage, ancestor, output, d = r.best
    written = spelling.spell(output, LANG)
    rows.append({
        "word": entry["word"].strip(), "ipa": entry.get("ipa") or "",
        "anc": ancestor, "stage": stage, "output": output, "written": written,
        "distance": cov.distance(written, entry["word"].strip()),
        "matched_spelling": False, "plausible": spelling.plausible(output, entry.get("ipa") or ""),
        "steps": len(d.steps), "step_ids": ",".join(s.rule_id for s in d.steps),
        "ladder": " > ".join(d.forms),
    })

out = Path(__file__).with_name("misses.tsv")
keys = ("word", "ipa", "distance", "matched_spelling", "plausible", "stage",
        "anc", "output", "written", "steps", "step_ids", "ladder")
with out.open("w", encoding="utf-8") as fh:
    fh.write("\t".join(keys) + "\n")
    for r in sorted(rows, key=lambda r: (r["distance"], r["word"])):
        fh.write("\t".join(str(r[k]).replace("\t", " ") for k in keys) + "\n")
print(f"{len(rows)} miss rows -> {out}")
