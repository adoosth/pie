#!/usr/bin/env python3
"""File the Middle Persian Corpus and Dictionary (MPCD) into the pal glossary.

The MPCD (mpcorpus.org) is a corpus *and* a dictionary: every lemma it lists is
tied to the tokens a text writes, so it can say how often a word occurs and
which Pahlavi spellings it has.  That is what this repository's Middle Persian
stage was missing — 697 hand-filed words against a corpus of 827,000 tokens
(2026-11-13).

What is taken, and what is left behind:

* the **word** as MPCD transcribes it (``garm``), the same convention the
  glossary already follows for Middle Persian;
* its **part of speech**, the tag most of its tokens carry (MPCD tags tokens,
  not lemmas);
* its **English senses**, one gloss each;
* the number of **occurrences**, which is the attestation (`occurrences`, the
  page says "the corpus writes it 102 times");
* the **spellings** the corpus writes for it: the commonest goes in ``translit``
  and up to eight more in ``translit_variants`` (garm is written glm 48×,
  g03lm 43×, …).  They are the same word written differently, never rows of
  their own (2026-11-13);
* the address of its **MPCD entry**, so the word page carries a book icon that
  opens the entry the word was read in (nothing more: the occurrence list and
  the texts it quotes are out of scope, 2026-11-13).

A lemma no token of the corpus writes is not filed: the dictionary lists it,
but no text spells it, and this model would then call it attested.  Multiword
expressions, punctuation and the clitic rows MPCD writes with a leading ``=``
are left to a later pass — a phrase is not a word of the stage, and a clitic is
grammar.

    python3 tools/import_mpcd.py --lemmas lemmas.jsonl \
        --tokens tokens.jsonl.gz --pos pos.jsonl.gz

The three inputs come from the ``mpcd`` skill (``scripts/pull_lemmas.py`` and
``scripts/pull_corpus.py``); the tool is a pure function of them, so the
supplement can be rebuilt from the site at any time.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "lexicon" / "_supplement" / "pal.mpcd.jsonl.gz"
ENTRY = "https://www.mpcorpus.org/dict/{id}/"

#: Universal Dependencies tags → the glossary's own words.  A tag with no row
#: is left empty rather than guessed.
POS = {
    "ADJ": "adjective", "NOUN": "noun", "PROPN": "proper noun", "VERB": "verb",
    "AUX": "verb", "ADV": "adverb", "PRON": "pronoun", "DET": "determiner",
    "ADP": "preposition", "CCONJ": "conjunction", "SCONJ": "conjunction",
    "PART": "particle", "NUM": "numeral", "INTJ": "interjection",
}

#: The MPCD writes a homonym's number after its word (abar1, abar2): it is the
#: dictionary's index, not a letter of the word.
_HOMONYM = re.compile(r"\d+$")
#: A row that is not a word of the stage: punctuation, a clitic, a phrase, a
#: fragment of one (MPCD marks the cut with §).
_NOT_A_WORD = re.compile(r"[\s§,=$]|^$")


def read_jsonl(path: Path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def counts(tokens: Path, pos: Path) -> tuple[dict, dict, dict]:
    """How often each lemma occurs, the tags its tokens carry, its spellings."""
    tag_of: dict[str, str] = {}
    if pos and pos.exists():
        for row in read_jsonl(pos):
            tag_of[row["t"]] = row["p"]
    n: collections.Counter = collections.Counter()
    tags: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    spellings: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for row in read_jsonl(tokens):
        p = tag_of.get(row["i"], "")
        for lemma in row.get("l") or []:
            n[lemma] += 1
            if p:
                tags[lemma][p] += 1
            if row.get("tl"):
                spellings[lemma][row["tl"]] += 1
    return n, tags, spellings


#: A sense that is an annotation label rather than a meaning: MPCD's tokens
#: carry Universal Dependencies case and part-of-speech tags, and a few lemmas
#: list them among their senses (pad: DAT, EQU, INS, LOC).  A reader wants the
#: meaning, so the labels go.
_LABEL = re.compile(r"^(?:[A-Z][A-Z/]{1,6}|n/?a\.?|\?)$")


def senses(lemma: dict) -> list[str]:
    out: list[str] = []
    for row in lemma.get("related_senses") or []:
        if row.get("language") != "eng":
            continue
        text = " ".join(str(row.get("sense") or "").split())
        if text and not _LABEL.match(text) and text not in out:
            out.append(text)
    return out


def rows(lemmas: Path, tokens: Path | None, pos: Path | None, *, minimum: int = 1
         ) -> tuple[list[dict], dict]:
    n, tags, spellings = ({}, collections.defaultdict(collections.Counter), {}) \
        if not tokens else counts(tokens, pos)
    out: list[dict] = []
    skipped = collections.Counter()
    seen: dict[tuple[str, str], dict] = {}
    spelled: dict[tuple[str, str], collections.Counter] = {}
    for lemma in read_jsonl(lemmas):
        if lemma.get("language") != "pal":
            skipped["not Middle Persian"] += 1
            continue
        word = _HOMONYM.sub("", str(lemma.get("word") or "")).strip()
        if not word or _NOT_A_WORD.search(word):
            skipped["not a word of the stage"] += 1
            continue
        if lemma.get("multiword_expression"):
            skipped["multiword expression"] += 1
            continue
        gloss = senses(lemma)
        if not gloss:
            skipped["no English sense"] += 1
            continue
        count = n.get(lemma["id"], 0) if tokens else 0
        if tokens and count < minimum:
            skipped["no text writes it"] += 1
            continue
        tag = (tags.get(lemma["id"]) or collections.Counter()).most_common(1)
        row = {
            "word": word, "lang": "pal", "pos": POS.get(tag[0][0], "") if tag else "",
            "gloss": gloss, "source": "mpcd", "sources": ["mpcd"],
            "url": ENTRY.format(id=lemma["id"]),
        }
        if count:
            row["occurrences"] = count
        # Two MPCD lemmas that differ only by their homonym number are one
        # spelling here: their senses are one word's senses until the model can
        # tell them apart (it has no homonym index, 2026-11-13).
        key = (word, row["pos"])
        if key in seen:
            for g in gloss:
                if g not in seen[key]["gloss"]:
                    seen[key]["gloss"].append(g)
            if count:
                seen[key]["occurrences"] = seen[key].get("occurrences", 0) + count
            spelled[key].update(spellings.get(lemma["id"]) or {})
            continue
        seen[key] = row
        spelled[key] = collections.Counter(spellings.get(lemma["id"]) or {})
        out.append(row)
    # A lemma's corpus spellings are orthographic variants of one word, not
    # separate words: keep the commonest in `translit` and at most eight more,
    # most frequent first, in `translit_variants` (2026-11-13).
    for key, row in seen.items():
        forms = [form for form, _ in sorted(spelled[key].items(),
                                            key=lambda item: (-item[1], item[0]))]
        if forms:
            row["translit"] = forms[0]
            row["spellings_n"] = len(forms)
            if len(forms) > 1:
                row["translit_variants"] = forms[1:9]
    return out, dict(skipped)


def write(rows_: list[dict], dest: Path = OUT) -> None:
    rows_.sort(key=lambda r: (r["word"], r["pos"]))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for row in rows_:
            gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                     .encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lemmas", type=Path, required=True)
    ap.add_argument("--tokens", type=Path)
    ap.add_argument("--pos", type=Path)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--min-occurrences", type=int, default=1)
    a = ap.parse_args(argv)
    rows_, skipped = rows(a.lemmas, a.tokens, a.pos, minimum=a.min_occurrences)
    write(rows_, a.out)
    print(f"filed {len(rows_)} Middle Persian words in {a.out}")
    for why, how in sorted(skipped.items(), key=lambda kv: -kv[1]):
        print(f"  left out {how:6d}  {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
