#!/usr/bin/env python3
"""Audit every unexplained entry of a language by cause, not by word.

Counts exactly as tools/coverage.py: a recorded ancestor in the word's own
chain, at least one law fired, and the output identical to the attested form
(an acute read as the stress token counts as exact, `exact_kind`; a hyphen-only
difference is the counter's own `bound_form` column).

Every miss gets one cause, in this order:
  no_ancestor    the record names no ancestor at a modelled stage
  no_law         an ancestor exists but no rule fires on it
  morphology     the target contains material the ancestor lacks (a suffix,
                 an ending, a preverb) — a sound law may not add a morpheme
  bound          the record writes a hyphen the laws never write
  accent         the only difference is where the stress stands
  letters        the letters differ — the sound-law worklist

    PYTHONPATH=src python3 proposals/night-0911/piir2/audit_misses.py ira-pro
    PYTHONPATH=src python3 proposals/night-0911/piir2/audit_misses.py ira-pro --json
    PYTHONPATH=src python3 proposals/night-0911/piir2/audit_misses.py ira-pro --cause letters
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data                                    # noqa: E402
from pie.phonology import tokenize, detokenize          # noqa: E402
from pie.rules import derive                            # noqa: E402
from coverage import (ancestor_starts, exact_kind, _bound_pair,   # noqa: E402
                      _identity_hit, _stress_free, distance)


def signature(output: str, target: str) -> str:
    """The token-level change, as ``-a +b`` style ops."""
    a, b = tokenize(output), tokenize(target)
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        if tag == "equal":
            continue
        got, want = detokenize(a[i1:i2]), detokenize(b[j1:j2])
        if tag in ("replace", "insert"):
            ops.append(f"-{got}+{want}" if got else f"+{want}")
        elif tag == "delete":
            ops.append(f"-{got}")
    return " ".join(ops)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cause")
    ap.add_argument("--word")
    args = ap.parse_args()

    lang = args.lang
    chain = data.derivation_chain(lang)
    rulesets = data.rulesets()
    rows = []
    for entry in data.lexicon(lang):
        target = str(entry.get("word") or "").strip()
        if not target or entry.get("recon"):
            continue
        if args.word and args.word != target:
            continue
        starts = ancestor_starts(entry, chain)
        outputs = []
        hit = None
        for stage, form in starts:
            try:
                d = derive(form, chain[chain.index(stage):], rulesets, tiers=None)
            except Exception:                       # noqa: BLE001
                continue
            if d.skipped:
                continue
            outputs.append((d.output, len(d.steps), stage, form))
            if d.steps and exact_kind(d.output, target):
                hit = ("exact", d.output, stage, form)
                break
        if hit is None and _identity_hit([(o, s, st) for o, s, st, _f in outputs],
                                         target, entry):
            hit = ("identity", None, None, None)
        bound = "-" in target and any(_bound_pair(o, target) for o, _s, _st, _f in outputs)
        if hit or bound:
            continue
        best = None
        for out, steps, stage, form in outputs:
            if not steps:
                continue
            dist = distance(out, target)
            if best is None or dist < best[0]:
                best = (dist, out, stage, form, steps)
        if not starts:
            cause = "no_ancestor"
        elif best is None:
            cause = "no_law"
        elif _stress_free(best[1]) == _stress_free(target):
            cause = "accent"
        elif ("-" in target) and _stress_free(best[1].replace("-", "")) == _stress_free(target.replace("-", "")):
            cause = "bound"
        elif tokens_extra(best[1], target):
            cause = "morphology"
        else:
            cause = "letters"
        rows.append({
            "word": target,
            "cause": cause,
            "ancestors": [[a[0], a[1], a[2]] for a in (entry.get("anc") or [])],
            "etym": entry.get("etym") or "",
            "outputs": [[o, s, st, f] for o, s, st, f in outputs],
            "best": best,
            "signature": signature(best[1], target) if best else "no derivation",
        })

    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return 0
    fam = Counter(r["signature"] for r in rows if r["cause"] == "letters")
    causes = Counter(r["cause"] for r in rows)
    print(f"{lang}: {len(rows)} unexplained")
    for cause, n in causes.most_common():
        print(f"{n:4d}  {cause}")
    print("\nletters, by signature:")
    for sig, n in fam.most_common():
        print(f"{n:4d}  {sig}")
    print()
    for r in rows:
        if args.cause and r["cause"] != args.cause:
            continue
        b = r["best"]
        if b:
            print(f"[{r['cause']:12s}] {r['word']:20s} <- {b[3]:20s} ({b[2]}) = {b[1]:22s}  [{r['signature']}]")
        else:
            print(f"[{r['cause']:12s}] {r['word']:20s} <- {'/'.join(a[1] for a in r['ancestors']) or '(none)'}")
    return 0


def tokens_extra(output: str, target: str) -> bool:
    """True when the target contains a run the output lacks (added material)."""
    a, b = tokenize(output), tokenize(target)
    ops = difflib.SequenceMatcher(a=a, b=b).get_opcodes()
    return any(tag in ("insert",) for tag, *_ in ops)


if __name__ == "__main__":
    raise SystemExit(main())
