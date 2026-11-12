#!/usr/bin/env python3
"""Audit the "one accent, two spellings" rule in the exact counter.

Replicates the matching loop of ``tools/coverage.py::measure`` exactly (first
ancestor that matches wins, at least one law must fire) and records every pair
the counter calls ``notation``: the record, the laws' output, the stage and the
ancestor.  It then answers the only question that matters for the rule's
honesty: is the difference really the stress spelling, and do the two sides put
the accent on the same syllable?

    PYTHONPATH=src python3 proposals/night-0911/notation_probe.py            # all languages
    PYTHONPATH=src python3 proposals/night-0911/notation_probe.py --langs ira-pro iir-pro
    PYTHONPATH=src python3 proposals/night-0911/notation_probe.py --json out.json

Classification of a pair
------------------------
``positions``   the two sides put primary stress on the same syllable and every
                differing character is a stress mark (ˈ ˌ or a combining acute/
                grave/circumflex).  The difference is spelling, nothing else.
``other``       the accent is on the same syllable, but some other character
                differs too (breve dropped, standalone ʰ read as h).  Notation,
                but not *stress* notation: the label is imprecise.
``silent``      only one side marks stress and the other is a dictionary form
                written without any accent, so the position cannot disagree.
``mismatch``    both sides mark the accent, on different syllables.  This is a
                bug: the counter accepted a word whose stress the laws get wrong.
``unknown``     the accent mark could not be placed (a mark on a glide, an
                unrecognised diacritic, unequal nuclei).

Nothing here writes to the repo.  Exit status is 1 when a ``mismatch`` or an
unexplained difference is found, so the audit can be a gate.
"""
from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, pathways                     # noqa: E402
from pie.phonology import STRESS_TOKENS, is_vowel, letters, tokenize  # noqa: E402
from pie.rules import derive                       # noqa: E402
from pie.service import _comparison_key, printable_form  # noqa: E402

_spec = importlib.util.spec_from_file_location("coverage_tool", ROOT / "tools" / "coverage.py")
coverage = importlib.util.module_from_spec(_spec)
sys.modules["coverage_tool"] = coverage
_spec.loader.exec_module(coverage)

STRESS_CHARS = {"ˈ", "ˌ", "\u0301", "\u0300", "\u0302", "\u0342"}
SYLLABIC_MARKS = {"\u0325", "\u0329"}


def diff_chars(a: str, b: str) -> tuple[list[str], list[str]]:
    """Characters in *a* that *b* lacks, and vice versa (NFD, char level)."""
    left = list(unicodedata.normalize("NFD", a))
    right = list(unicodedata.normalize("NFD", b))
    sm = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    only_a: list[str] = []
    only_b: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            only_a.extend(left[i1:i2])
        if tag in ("insert", "replace"):
            only_b.extend(right[j1:j2])
    return only_a, only_b


def stress_profile(form: str) -> dict:
    """Where the accent sits, in nuclei of the word.

    ``tokenize`` already turns an acute on a vowel or a syllabic sonorant into
    the engine's own ``ˈ``, so both spellings are read in one representation.
    Every remaining mark is kept as a raw diacritic for the report.
    """
    toks = tokenize(form)
    nuclei: list[int] = []
    for i, tok in enumerate(toks):
        if tok in STRESS_TOKENS:
            continue
        let = letters(tok)
        if is_vowel(tok) or (let in {"r", "l", "m", "n"} and SYLLABIC_MARKS & set(unicodedata.normalize("NFD", tok))):
            nuclei.append(i)
    marks: list[dict] = []
    for i, tok in enumerate(toks):
        if tok in STRESS_TOKENS:
            after = [k for k in nuclei if k > i]
            marks.append({"mark": tok, "nucleus": nuclei.index(after[0]) if after else None,
                          "on_letter": after[0] if after else None})
    raw = [ch for ch in unicodedata.normalize("NFD", form)
           if ch in {"\u0300", "\u0302", "\u0342"}]
    return {"nuclei": len(nuclei), "marks": marks, "raw_accents": raw,
            "primary": next((m["nucleus"] for m in marks if m["mark"] == "ˈ"), None),
            "secondary": [m["nucleus"] for m in marks if m["mark"] == "ˌ"]}


def classify(target: str, output: str) -> dict:
    ka, kb = _comparison_key(target), _comparison_key(output)
    only_t, only_o = diff_chars(target, output)
    stray = sorted({c for c in only_t + only_o if c not in STRESS_CHARS})
    prof_t, prof_o = stress_profile(target), stress_profile(output)
    rec_marks = [m for m in prof_t["marks"]]
    eng_marks = [m for m in prof_o["marks"]]
    rec_primary = prof_t["primary"]
    eng_primary = prof_o["primary"]

    if ka != kb:                       # the one-sided path of _same_form
        path = "one-sided"
    else:
        path = "key-equal"

    if rec_primary is not None and eng_primary is not None:
        if rec_primary != eng_primary:
            verdict = "mismatch"
        elif stray:
            verdict = "other"
        else:
            verdict = "positions"
    elif eng_primary is not None and rec_primary is None:
        # the record says nothing about stress (no acute, or a mark tokenize
        # cannot read) — nothing can contradict the engine
        verdict = "silent"
    elif rec_primary is not None and eng_primary is None:
        verdict = "silent" if not eng_marks else "unknown"
    elif not rec_marks and not eng_marks:
        verdict = "other" if stray else "positions"
    else:
        verdict = "unknown"

    if prof_t["nuclei"] != prof_o["nuclei"]:
        verdict = "unknown"
    return {
        "path": path, "verdict": verdict,
        "record": target, "output": output,
        "only_record": "".join(only_t), "only_output": "".join(only_o),
        "stray": stray,
        "record_nuclei": prof_t["nuclei"], "output_nuclei": prof_o["nuclei"],
        "record_primary": rec_primary, "output_primary": eng_primary,
        "record_secondary": prof_t["secondary"], "output_secondary": prof_o["secondary"],
        "record_raw_accents": prof_t["raw_accents"],
    }


def scan(lang: str, chain: list[str], rulesets, tiers, limit: int, default_paths) -> dict:
    entries = data.lexicon(lang)
    eligible = [e for e in entries if coverage.ancestor_starts(e, chain)]
    used = coverage.sample([e for e in eligible if not e.get("recon")], limit)
    pairs: list[dict] = []
    strict = 0
    pathway = 0
    for entry in used:
        target = str(entry.get("word") or "").strip()
        if not target:
            continue
        candidates = coverage.ancestor_starts(entry, chain)
        if not candidates:
            continue
        matched = False
        for stage, form in candidates:
            try:
                d = derive(form, chain[chain.index(stage):], rulesets, tiers=tiers)
            except Exception:
                break
            if d.skipped or not d.steps:
                continue
            if d.output == target:
                strict += 1
                matched = True
                break
            if coverage._same_form(d.output, target):
                row = classify(target, d.output)
                row.update({"lang": lang, "stage": stage, "ancestor": form})
                pairs.append(row)
                matched = True
                break
        if not matched and default_paths and (lang, target) in default_paths:
            off = list(default_paths[(lang, target)].get("disabled") or [])
            on = list(default_paths[(lang, target)].get("enabled") or [])
            for stage, form in candidates:
                try:
                    d = derive(form, chain[chain.index(stage):], rulesets, tiers=tiers,
                               disabled=off, enabled=on)
                except Exception:
                    break
                if d.skipped or not d.steps:
                    continue
                if d.output == target:
                    pathway += 1
                    break
    return {"lang": lang, "tested": len(used), "strict": strict,
            "notation": len(pairs), "pairs": pairs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--show", default="", help="comma list of verdicts to print")
    ap.add_argument("--guard", action="store_true",
                    help="also report what the stress_only guard keeps and drops")
    args = ap.parse_args()

    rulesets = data.rulesets()
    default_paths = pathways.defaults()
    want = set(args.show.split(",")) if args.show else None
    results = {}
    for lang, meta in data.languages().items():
        if lang == "ine-pro":
            continue
        if args.langs and lang not in args.langs:
            continue
        chain = data.derivation_chain(lang)
        if not chain or not any(l == lang for l, _ in data.available_lexicons()):
            continue
        r = scan(lang, chain, rulesets, None, args.limit, default_paths)
        results[lang] = r
        counts: dict[str, int] = {}
        for p in r["pairs"]:
            counts[p["verdict"]] = counts.get(p["verdict"], 0) + 1
        detail = " ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        print(f"{lang:<12} tested={r['tested']:>6} strict={r['strict']:>5} "
              f"notation={r['notation']:>4}  {detail}")
        for p in r["pairs"]:
            if want and p["verdict"] not in want:
                continue
            print(f"    [{p['verdict']}] {p['record']}  ≠  {p['output']}   "
                  f"(record+{' '.join(p['only_record']) or '—'} "
                  f"output+{' '.join(p['only_output']) or '—'} "
                  f"stress {p['record_primary']}→{p['output_primary']})")

    total = {k: sum(1 for r in results.values() for p in r["pairs"] if p["verdict"] == k)
             for k in ("positions", "other", "silent", "mismatch", "unknown")}
    print("----")
    print("totals: strict=%d notation=%d %s" % (
        sum(r["strict"] for r in results.values()),
        sum(r["notation"] for r in results.values()),
        " ".join(f"{k}={v}" for k, v in total.items())))
    if args.guard:
        pairs = [p for r in results.values() for p in r["pairs"]]
        kept = [p for p in pairs if stress_only(p["output"], p["record"])]
        print(f"guard stress_only: keeps {len(kept)}/{len(pairs)}, drops {len(pairs)-len(kept)}; "
              f"position-verified kept {sum(1 for p in kept if p['verdict'] == 'positions')}"
              f"/{sum(1 for p in pairs if p['verdict'] == 'positions')}")
    if args.json:
        args.json.write_text(json.dumps({"languages": results, "totals": total}, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"wrote {args.json}")
    return 0 if not (total["mismatch"] or total["unknown"]) else 1




# --- the guard this audit recommends, as executable evidence -----------------
# A stress-only comparison that does *not* go through tokenize(), so a hyphen,
# bracket, space, breve, thorn or ʰ can never be mistaken for an accent.
_VOWELS = set("aeiouyəɛɔæœøɨɤɯɪʊɐɑɒɵʌʉɘ")
_SONORANTS = set("rlmn")
_STRESS = {"ˈ", "ˌ"}
_SYLLABIC = {"\u0325", "\u0329"}


def stress_only(output: str, target: str) -> bool:
    """True when the two forms differ only in how (or whether) stress is written."""
    def profile(form: str) -> tuple[str, tuple[int, ...]]:
        text = unicodedata.normalize("NFD", form)
        segs: list[list[str]] = []          # [base, *kept marks]
        stress: list[tuple[int, int | None]] = []   # (segment index, acute here?)
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in _STRESS:
                stress.append((len(segs), None))   # marks the next nucleus
                i += 1
                continue
            if unicodedata.combining(ch) and segs:
                if ch == "\u0301":
                    stress.append((len(segs) - 1, 0))
                else:
                    segs[-1].append(ch)
                i += 1
                continue
            segs.append([ch])
            i += 1
        skeleton = "".join("".join(s) for s in segs)
        ordinals: list[int | None] = []
        n = 0
        for seg in segs:
            base, marks = seg[0], "".join(seg[1:])
            if base in _VOWELS or (base in _SONORANTS and any(m in _SYLLABIC for m in marks)):
                ordinals.append(n)
                n += 1
            else:
                ordinals.append(None)
        positions: list[int] = []
        for at, acute in stress:
            if acute is not None:
                if ordinals[at] is None:
                    return skeleton, (-1,)   # accent on a non-nucleus
                positions.append(ordinals[at])
                continue
            nxt = next((ordinals[j] for j in range(at, len(segs)) if ordinals[j] is not None), None)
            positions.append(-1 if nxt is None else nxt)
        return skeleton, tuple(positions)

    a, pa = profile(printable_form(output))
    b, pb = profile(target)
    if a != b:
        return False
    if pa and pb:
        return pa == pb
    return bool(pa or pb)

if __name__ == "__main__":
    raise SystemExit(main())
