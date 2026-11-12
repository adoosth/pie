#!/usr/bin/env python3
"""Is any miss a *letter* problem (right segments, wrong letters)?

For every miss, fold the recorded IPA onto the model's segment inventory and
compare the full segment sequence with the derived phonemic form.  A word that
agrees segment for segment but still spells differently is a genuine
orthographic gap; a word that differs in a segment is the sound laws' business.
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
from pie.phonology import tokenize, is_vowel  # noqa: E402

FOLD = {
    "t͡ʃ": "č", "tʃ": "č", "d͡ʒ": "ǰ", "dʒ": "ǰ", "ʃ": "š", "ʒ": "ž",
    "ɡ": "g", "ɹ": "r", "ɾ": "r", "ʁ": "r", "ʀ": "r", "ʔ": "ʾ", "Ɂ": "ʾ",
    "xʷ": "xw", "kʷ": "kw", "gʷ": "gw", "j": "y", "w": "w",
}
#: every non-model vowel collapses onto the nearest model vowel, length kept
VOWEL = {"æ": "a", "ɑ": "ā", "ɒ": "ā", "aː": "ā", "iː": "ī", "uː": "ū",
         "oː": "ū", "eː": "ī", "ɛ": "e", "ɔ": "o", "ʊ": "u", "ɪ": "i",
         "ə": "e", "y": "i", "ø": "e", "œ": "e"}
LONG = {"aː": "ā", "iː": "ī", "uː": "ū", "oː": "ū", "eː": "ī"}


def segments(text: str) -> list[str]:
    text = re.sub(r"[/\[\]().|ˈˌ\u203f]", "", text or "")
    text = text.replace("\u0329", "")
    out: list[str] = []
    i = 0
    keys = sorted(FOLD, key=len, reverse=True)
    while i < len(text):
        ch = text[i]
        if unicodedata.category(ch) == "Mn":
            i += 1
            continue
        for k in keys:
            if text.startswith(k, i):
                out.append(FOLD[k]); i += len(k); break
        else:
            out.append(ch); i += 1
    # merge a + ː into ā
    merged: list[str] = []
    for tok in out:
        if tok == "ː" and merged:
            merged[-1] = LONG.get(merged[-1] + "ː", merged[-1] + "ː")
            continue
        merged.append(tok)
    final: list[str] = []
    for tok in merged:
        if tok in VOWEL:
            tok = VOWEL[tok]
        final.append(tok)
    return final


rows = list(csv.DictReader(open(Path(__file__).with_name("misses.tsv"), encoding="utf-8"),
                           delimiter="\t"))
letter, segment, no_ipa = [], [], 0
for r in rows:
    if r["matched_spelling"] == "True" or not r["ipa"]:
        no_ipa += not r["ipa"]
        continue
    a, b = segments(r["output"]), segments(r["ipa"])
    (letter if a == b else segment).append(r)

print(f"misses with no IPA            {no_ipa}")
print(f"segment-for-segment equal     {len(letter)}")
print(f"a segment differs             {len(segment)}\n")
for r in letter[:60]:
    print(f"  {r['word']:12s} {r['written']:12s} ipa={r['ipa']:18s} out={r['output']:12s} anc={r['anc']}")
