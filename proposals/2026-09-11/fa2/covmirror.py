#!/usr/bin/env python3
"""Exact mirror of tools/coverage.py's selection for one language.

The published orthographic column (2026-11-09, the Sanskrit commit) tries the
spelling layer on **every** ancestor derivation, in candidate order, and counts
the word if any one spells it right and `spelling.plausible` agrees.  The older
`fa_probe.py` only spelled the *closest* derivation, so its 59 differs from the
published 103.  This module reproduces the published rule so every number in
the `fa2/` report is measured the same way.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling                      # noqa: E402
from pie.rules import derive                        # noqa: E402
import coverage as cov                              # noqa: E402

LANG = "fa"
RULESETS = data.rulesets()
CHAIN = data.derivation_chain(LANG)
ENTRIES = data.lexicon(LANG)
ELIGIBLE = [e for e in ENTRIES if cov.ancestor_starts(e, CHAIN)]


@dataclass
class Result:
    entry: dict
    orth: tuple | None            # (output, stage, Derivation) — counted by coverage
    best: tuple | None            # (stage, ancestor, output, Derivation) nearest
    exact: bool


def entry_result(entry: dict, disabled=()) -> Result | None:
    target = entry["word"].strip()
    candidates = cov.ancestor_starts(entry, CHAIN)
    if not candidates:
        return None
    ipa = entry.get("ipa") or ""
    orth = None
    best = None
    best_distance = 10**6
    exact = False
    for stage, form in candidates:
        try:
            d = derive(form, CHAIN[CHAIN.index(stage):], RULESETS, disabled=disabled)
        except Exception:
            return None
        if d.skipped:
            continue
        if orth is None and d.steps and spelling.spell(d.output, LANG) == target \
                and spelling.plausible(d.output, ipa):
            orth = (d.output, stage, d)
        kind = cov.exact_kind(d.output, target) if d.steps else None
        if kind:
            exact = True
            break
        dist = cov.distance(d.output.lower(), target.lower())
        if dist < best_distance:
            best, best_distance = (stage, form, d.output, d), dist
    return Result(entry, orth, best, exact)


def measure(disabled=()) -> dict:
    counted = []
    missed = []
    for entry in ELIGIBLE:
        r = entry_result(entry, disabled)
        if r is None:
            continue
        if r.exact:
            continue
        (counted if r.orth else missed).append((entry, r))
    return {"counted": counted, "missed": missed}
