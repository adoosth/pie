#!/usr/bin/env python3
"""Classify every Persian miss: which layer would have to change, and why.

Mirrors tools/coverage.py's counting exactly (exact, pathway, script,
orthographic, citation, identity, bound form, join) for language `fa`, then
dumps one TSV row per still-unexplained word with the closest derivation and
the flags the report's table is built from.  Diagnostic only.
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, pathways, script, spelling          # noqa: E402
from pie.rules import derive                              # noqa: E402
import coverage as cov                                    # noqa: E402

LANG = "fa"
RULESETS = data.rulesets()
CHAIN = data.derivation_chain(LANG)
DEFAULTS = pathways.defaults()
ENTRIES = data.lexicon(LANG)

FOLD = {"t͡ʃ": "č", "tʃ": "č", "d͡ʒ": "ǰ", "dʒ": "ǰ", "ʃ": "š", "ʒ": "ž",
        "ɡ": "g", "ɹ": "r", "ɾ": "r", "ʁ": "r", "ʀ": "r", "ʔ": "ʾ", "Ɂ": "ʾ",
        "xʷ": "xw", "kʷ": "kw", "gʷ": "gw", "j": "y"}
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


LATIN = re.compile(r"^[A-Za-zāēīōūǎěǐǒǔǖǘǚǜǰčšžɣʾθðβḱǵʰʷˀ()\-]+$")


def is_latin_phonemic(form: str) -> bool:
    """A form the law engine can in principle read: Latin letters only."""
    return bool(LATIN.match(form))


def classify(entry: dict, candidates, outputs, joined: bool) -> dict:
    target = entry["word"].strip()
    ipa = entry.get("ipa") or ""
    translit = entry.get("translit") or ""
    rec = {"word": target, "ipa": ipa, "translit": translit,
           "joined": joined, "n_paths": len(outputs),
           "near_stage": candidates[-1][0] if candidates else ""}
    best = None
    best_d = 10**6
    near = candidates[-1][0] if candidates else None
    ordered = sorted(outputs, key=lambda o: (o[2] != near, cov.distance(o[0], target)))
    for output, steps, stage, anc, _d in ordered:
        d = cov.distance(output.lower(), target.lower())
        if d < 10**6:
            best_d, best = d, (output, steps, stage, anc, _d)
            break
    if best is None:
        rec.update(stage="", anc=candidates[0][1] if candidates else "",
                   output="", written="", steps=0, ladder="", d=0)
        return rec
    output, steps, stage, anc, deriv = best
    rec.update(stage=stage, anc=anc, output=output, steps=len(steps),
               written=spelling.spell(output, LANG) if spelling.applies(LANG) else "",
               ladder=" > ".join(deriv.forms), d=best_d)
    # causes, in order of certainty
    if not steps:
        rec["cause"] = "e-blocked"
    elif ipa and segments(output) == segments(ipa):
        rec["cause"] = "c-notation"
    elif translit and (output == translit or cov.stress_only(output, translit)):
        rec["cause"] = "c-notation"
    elif translit and segments(output) == segments(translit):
        rec["cause"] = "c-letters"
    else:
        rec["cause"] = "?"
    return rec


rows = []
explained = 0
for entry in ENTRIES:
    target = entry["word"].strip()
    candidates = cov.ancestor_starts(entry, CHAIN)
    if not candidates:
        continue
    ipa = entry.get("ipa") or ""
    pieces = cov._compound_pieces(entry, LANG)
    outputs = []
    here = False
    orth = None
    citation = None
    for stage, form in candidates:
        start = CHAIN.index(stage)
        try:
            d = derive(form, CHAIN[start:], RULESETS)
        except Exception:
            continue
        if d.skipped:
            continue
        outputs.append((d.output, d.steps, stage, form, d))
        if orth is None:
            orth = cov.orthographic_hit([(d.output, len(d.steps), stage)], LANG, target, ipa)
        if citation is None and orth is None:
            citation = cov.citation_hit([(d.output, len(d.steps), stage)], LANG, target, ipa)
        if d.steps and cov.exact_kind(d.output, target):
            here = True
        elif orth is not None:
            here = True
        elif citation is not None:
            here = True
        elif d.steps and (script.match(LANG, d.output, target) or {}).get("ok"):
            here = True
        else:
            ident = cov._identity_hit([(d.output, len(d.steps), stage)], target, entry)
            if ident is not None:
                here = True
            if "-" in target and cov._bound_pair(d.output, target):
                here = True
    if not here and (LANG, target) in DEFAULTS:
        off = list(DEFAULTS[(LANG, target)].get("disabled") or [])
        on = list(DEFAULTS[(LANG, target)].get("enabled") or [])
        for stage, form in candidates:
            try:
                d = derive(form, CHAIN[CHAIN.index(stage):], RULESETS, disabled=off, enabled=on)
            except Exception:
                break
            if d.skipped:
                continue
            if (d.output == target and d.steps) or \
                    (d.steps and (script.match(LANG, d.output, target) or {}).get("ok")):
                here = True
                break
    if not outputs:
        rows.append(classify(entry, candidates, [], bool(pieces)))
        continue
    if here:
        explained += 1
        continue
    rows.append(classify(entry, candidates, outputs, bool(pieces)))

print(f"eligible {len(ENTRIES) and sum(1 for e in ENTRIES if cov.ancestor_starts(e, CHAIN))}"
      f" explained {explained} misses {len(rows)}")
from collections import Counter
print(Counter(r["cause"] for r in rows))
print(Counter((r["cause"], r["joined"]) for r in rows))

keys = ("word", "translit", "ipa", "stage", "near_stage", "anc", "output",
        "written", "steps", "d", "joined", "n_paths", "cause", "ladder")
out = Path(__file__).with_name("misses.tsv")
with out.open("w", encoding="utf-8") as fh:
    fh.write("\t".join(keys) + "\n")
    for r in sorted(rows, key=lambda r: (r["cause"], r["d"], r["word"])):
        fh.write("\t".join(str(r.get(k, "")).replace("\t", " ") for k in keys) + "\n")
print(f"-> {out}")
