#!/usr/bin/env python3
"""Sort the audit's misses into the report's six causes, on the near ancestor.

`audit.py` writes one row per Persian word that has a recorded ancestor at a
modelled stage and is still unexplained.  This pass adds the two facts the
report's table needs: the *nearest* recorded ancestor (the transition that
decides the last mile) and the cause, defined so that each row can be checked
by hand:

  a  the nearest ancestor is Middle Persian in Latin transcription and a
     pal -> fa law ran, leaving a form that differs from the word
  b  morphology or the citation form (bound headword, infinitive, plural)
  c  orthography/notation only (the derived segments are the word's own IPA)
  d  the recorded ancestor is a different lexeme (its first segment is not the
     headword's, and it is phonemic)
  e  the nearest ancestor carries no reading (Pahlavi/Manichaean script or a
     consonantal transliteration), so no law can start  [another agent's wall]
  u  the nearest recorded ancestor is upstream of Middle Persian, so the miss
     is not this transition's to fix

Diagnostic only; reads misses.tsv, writes classified.tsv and prints the tables.
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROWS = list(csv.DictReader(open(HERE / "misses.tsv", encoding="utf-8"), delimiter="\t"))

FOLD = {"t͡ʃ": "č", "tʃ": "č", "d͡ʒ": "ǰ", "dʒ": "ǰ", "ʃ": "š", "ʒ": "ž",
        "ɡ": "g", "ɹ": "r", "ɾ": "r", "ʁ": "r", "ʀ": "r", "ʔ": "ʾ", "Ɂ": "ʾ",
        "xʷ": "xw", "kʷ": "kw", "gʷ": "gw", "j": "y"}
VOWEL = {"æ": "a", "ɑ": "ā", "ɒ": "ā", "aː": "ā", "iː": "ī", "uː": "ū",
         "oː": "ū", "eː": "ī", "ɛ": "e", "ɔ": "o", "ʊ": "u", "ɪ": "i",
         "ə": "e", "y": "i", "ø": "e", "œ": "e"}
LONG = {"aː": "ā", "iː": "ī", "uː": "ū", "oː": "ū", "eː": "ī"}
VOWELS = set("aeiouāēīōū")
ARABIC = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")


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


def phonemic(form: str) -> bool:
    if not form or ARABIC.search(form):
        return False
    if "ʾ" in form or "'" in form or "*" in form:
        return False
    return any(c in VOWELS for c in form)


def cause(r: dict) -> tuple[str, str]:
    w, ipa, tr = r["word"], r["ipa"], r["translit"]
    anc, out, steps = r["anc"], r["output"], int(r["steps"] or 0)
    if int(r["d"]) == 0:
        return "already", ""
    if not phonemic(anc):
        return "e", "nearest ancestor has no reading"
    if int(r["n_paths"] or 0) == 0 or (r.get("stage") == r.get("near_stage") and steps == 0
                                       and not r["joined"]):
        return "e", "no law fires from the reading"
    if " " in w or "\u200c" in w or w.startswith("-") or w.endswith("-") or "ـ" in w:
        return "b", "bound/phrase headword"
    if w.endswith(("دن", "تن")) and not anc.endswith(("dan", "tan", "tan'", "tn")):
        return "b", "infinitive cited, stem in ancestor"
    for suffix, why in (("ان", "plural oblique -ān"), ("ها", "plural -hā"),
                        ("ترین", "superlative"), ("تر", "comparative -tar"),
                        ("را", "object marker rā")):
        if tr and out and tr != out and w.endswith(suffix) and len(w) > len(suffix) + 1:
            return "b", why
    if ipa and segments(out) == segments(ipa):
        return "c", "segments equal the IPA"
    if tr and segments(out) == segments(tr):
        return "c", "segments equal the transliteration"
    so, st = segments(out), segments(tr)
    if so and st and so[0] != st[0]:
        return "d", "ancestor starts differently"
    return "a", "law ran, form differs"


rows = []
for r in ROWS:
    k, why = cause(r)
    rows.append(dict(r, cause5=k, why=why))
by = Counter(r["cause5"] for r in rows)
print("misses", len(rows), dict(by))
print("\nby nearest recorded ancestor:")
print("stage      a   b   c   d   e   u  total")
for st in ("pal", "peo", "ira-pro", "iir-pro", "ine-pro"):
    sub = [r for r in rows if r["near_stage"] == st]
    c = Counter(r["cause5"] for r in sub)
    print(f"{st:10s} {c['a']:3d} {c['b']:3d} {c['c']:3d} {c['d']:3d} {c['e']:3d} {c['u']:3d}  {len(sub):5d}")
keys = ("word", "translit", "ipa", "near_stage", "anc", "output", "written", "steps",
        "d", "joined", "cause5", "why", "ladder")
with (HERE / "classified.tsv").open("w", encoding="utf-8") as fh:
    fh.write("\t".join(keys) + "\n")
    for r in sorted(rows, key=lambda r: (r["cause5"], r["near_stage"], int(r["d"]))):
        fh.write("\t".join(str(r.get(k, "")).replace("\t", " ") for k in keys) + "\n")
print("-> classified.tsv")
