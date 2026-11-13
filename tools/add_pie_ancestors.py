#!/usr/bin/env python3
"""Give a daughter word's named PIE ancestor an entry when its record states it.

A daughter's etymology often names a Proto-Indo-European word the PIE glossary
does not hold: Proto-Indo-Iranian *dʰárati is "From Proto-Indo-European
*dʰér-e-ti, from *dʰer- (“to support, hold”) + *-eti (thematic present
suffix)", and no page of Wiktionary's carries *dʰéreti — the word exists only
inside that sentence.  The timeline then prints the rung and says "no entry for
this word", and the word it belongs to cannot be fully explained while its
recorded rung is a hole (admin, 2026-11-13).

This tool writes such a word into ``data/lexicon/_supplement/ine-pro.jsonl.gz``
as a reconstruction whose citation is the sentence that names it, and whose
construction is that sentence's own addition.  It invents nothing:

* the form is the one the record writes, and only its morpheme boundaries are
  taken off (a record writes *h₂éǵ-o-s; the glossary heads words solid);
* the pieces are the record's own ``*A + *B`` clause — every piece must carry
  the record's asterisk, must be a word the PIE glossary already holds or a
  morpheme ``data/morphology/ine-pro.yaml`` registers, and the pieces' letters
  (vowels, laryngeals and stress set aside) must be the word's own, so a clause
  about a different form is refused;
* the gloss is left empty unless the record glosses the form itself: the word
  is cited, not translated, and the page prints the construction instead of a
  guessed sense (the same rule the Proto-Germanic strong verbs follow).

    PYTHONPATH=src python3 tools/add_pie_ancestors.py --check
    PYTHONPATH=src python3 tools/add_pie_ancestors.py --lang iir-pro
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, service  # noqa: E402

SUPPLEMENT = ROOT / "data" / "lexicon" / "_supplement" / "ine-pro.jsonl.gz"

#: Vowels are the grade, not the letters: *negʷ- + *-nós spells *nogʷ-nó-s,
#: and a check on the consonants alone is what can tell the record's pieces
#: from a clause about another word.
#: The glides belong with them: a diphthong's zero grade is its second element
#: (*leykʷ- + *-tós → *likʷtós*, *wekʷ- + *-tós → *ukʷtós*), so *w* and *y*
#: are grade, not letters, exactly like *u* and *i*.
VOWELS = frozenset("aeiouāēīōūăĕĭŏŭáéíóúàèìòùâêîôûǻắếốӯȳαεηιουωwy")

#: A sentence that hedges its origin names a possibility: it is not evidence
#: for a word of its own (`pie.dubious.HEDGES` is the same test).
HEDGE = re.compile(r"\b(uncertain|unknown|possibly|perhaps|probably|disputed|doubtful)\b",
                   re.IGNORECASE)

#: ``*h₂eǵ- (“goat”)`` — a starred form and the gloss the sentence puts after it.
PIECE = re.compile(r"\*([^\s,;+()\[\]“”]+)(?:\s*[（(]“?([^”()]*?)”?[)）])?")


def letters(form: str) -> str:
    """A form's consonant skeleton: vowels, laryngeals and stress set aside."""
    text = unicodedata.normalize("NFD", str(form or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("*", "").replace("-", "").replace("(", "").replace(")", "")
    text = re.sub(r"[hH][₁₂₃]?", "", text)
    return "".join(ch for ch in text.lower() if ch not in VOWELS and not ch.isspace())


def solid(form: str) -> str:
    """The headword: the record's spelling without its morpheme boundaries."""
    return str(form or "").strip().lstrip("*").replace("(", "").replace(")", "").replace("-", "")


def names(etym: str, form: str):
    """Where the etymology names ``form`` as a Proto-Indo-European word, or None.

    A record names the same form two ways: the inheritance template writes it
    solid (*h₁wéh₂yeti*) and the sentence beside it writes the morpheme
    boundaries (*h₁wéh₂-ye-ti*).  Both are the same word, so both spellings are
    searched (2026-11-13).
    """
    for spelling in (form.lstrip("*"), form.lstrip("*").replace("-", "")):
        at = re.search(r"Proto-Indo-European\s+\*?" + re.escape(spelling), etym)
        if at:
            return at
    return None


def clause(etym: str, form: str) -> str:
    """The record's own ``from *A + *B`` clause for ``form``, or ``''``."""
    at = names(etym, form)
    if not at:
        return ""
    after = etym[at.end():]
    found = re.search(r"\bfrom\b(.{0,320})", after)
    if not found:
        return ""
    return re.split(r"\.\s|\.$|\bCognate\b|\bCompare\b|\bAlternatively\b|\bSee\b",
                    found.group(1))[0].strip()


def sentence_around(etym: str, form: str) -> str:
    """The sentence of the etymology that names ``form``."""
    at = names(etym, form)
    if not at:
        return ""
    left = max(etym.rfind(". ", 0, at.start()), etym.rfind("; ", 0, at.start())) + 1
    right = etym.find(". ", at.end())
    return etym[left:right + 1 if right >= 0 else len(etym)]


def pieces_of(text: str) -> list[list[str]]:
    """The pieces of a ``from *A (“x”) + *B (y)`` clause, ``+`` outside brackets."""
    parts, depth, buffer = [], 0, ""
    for ch in text:
        if ch in "([“":
            depth += 1
        elif ch in ")]”":
            depth = max(0, depth - 1)
        if ch == "+" and depth == 0:
            parts.append(buffer)
            buffer = ""
        else:
            buffer += ch
    parts.append(buffer)
    if len(parts) < 2:
        return []
    out = []
    for part in parts:
        found = PIECE.search(part)
        if not found:
            return []
        out.append([found.group(1).strip(), (found.group(2) or "").strip()])
    return out


def explained_piece(piece: str, bound) -> bool:
    """Whether a piece stands somewhere: a PIE word, or a registered morpheme."""
    raw = str(piece or "").strip()
    if not raw:
        return False
    if raw[:1] == "-" or raw[-1:] == "-":
        return service.normalise_etymon(raw) in bound or bool(
            service._lemma_entry("ine-pro", raw))
    return bool(service._lemma_entry("ine-pro", raw))


def candidates(lang: str) -> tuple[list[dict], list[tuple[str, str]]]:
    """Supplement rows this language's records justify, and the ones refused."""
    chain = data.derivation_chain(lang)
    bound = service._bound_forms("ine-pro")
    rows: dict[str, dict] = {}
    refused: list[tuple[str, str]] = []
    for entry in data.lexicon(lang):
        for hole in service.unrecorded_ancestry(entry, chain):
            if hole["stage"] != "ine-pro":
                continue
            form = hole["form"]
            etym = entry.get("etym") or ""
            text = clause(etym, form)
            if not text:
                refused.append((entry["word"], f"{form}: the record does not say how it was formed"))
                continue
            if HEDGE.search(sentence_around(etym, form)):
                # "Unknown; perhaps from *X" names a possibility, not a word:
                # a hedged row is parked in the review backlog, never filed as
                # an entry of its own (the rule `pie.dubious` states).
                refused.append((entry["word"], f"{form}: the record hedges it"))
                continue
            pieces = pieces_of(text)
            if not pieces:
                refused.append((entry["word"], f"{form}: the clause is not an addition"))
                continue
            if letters("".join(p[0] for p in pieces)) != letters(form):
                refused.append((entry["word"], f"{form}: the pieces spell another form"))
                continue
            short = [p[0] for p in pieces if not explained_piece(p[0], bound)]
            if short:
                refused.append((entry["word"], f"{form}: {' + '.join(short)} has no entry"))
                continue
            word = solid(form)
            row = rows.get(word)
            if row is None:
                row = rows[word] = {
                    "word": word,
                    "lang": "ine-pro",
                    "pos": "",
                    "recon": True,
                    "source": "wiktionary",
                    "sources": ["wiktionary"],
                    "etym": "From " + " + ".join(
                        f"*{p[0]}" + (f" (“{p[1]}”)" if p[1] else "") for p in pieces) + ".",
                    "ref": "",
                    "url": "",
                    "built_as": [{
                        "lang": "ine-pro",
                        "kind": "suffix" if pieces[-1][0][:1] == "-" else "compound",
                        "of": word,
                        "pieces": [["*" + p[0].lstrip("*"), p[1]] for p in pieces],
                    }],
                    "cited_by": [],
                }
                # The entry is only worth filing when its own timeline stands:
                # the record's pieces must compose the word by the grade the
                # suffix asks for, and every piece must have somewhere to
                # stand.  A word whose clause this model cannot yet reproduce
                # (a suffix whose grade the morphology table does not state)
                # stays a hole in the daughter's record and is named in the
                # worklist instead of being filed as a construction that "does
                # not spell the word" (2026-11-13).
                built = service.construction_path(row, "ine-pro", ["ine-pro"])
                if not (built or {}).get("exact"):
                    rows.pop(word, None)
                    refused.append((entry["word"],
                                    f"{form}: the model cannot compose "
                                    f"{' + '.join(p[0] for p in pieces)} yet"))
                    continue
                if not built.get("explained"):
                    rows.pop(word, None)
                    refused.append((entry["word"],
                                    f"{form}: {' + '.join(built.get('unexplained') or [])} "
                                    "has no entry"))
                    continue
            row["cited_by"].append(entry["word"])
            page = entry.get("url") or (
                "https://en.wiktionary.org/wiki/" + quote(
                    service._wiktionary_title(entry), safe="/:"))
            sentence = f"“{etym.strip()}”"
            row["ref"] = (row["ref"] + " Also named in " if row["ref"] else
                          "Named in the etymology of ") + f"{entry['word']}: {sentence}"
            row["url"] = row["url"] or page
    return list(rows.values()), refused


def write(rows: list[dict]) -> int:
    """Append the rows to the PIE supplement, keeping its order and its bytes."""
    existing: dict[str, str] = {}
    if SUPPLEMENT.exists():
        for line in gzip.open(SUPPLEMENT, "rt", encoding="utf-8"):
            if line.strip():
                existing[json.loads(line)["word"]] = line
    added = 0
    for row in rows:
        if row["word"] in existing:
            continue
        existing[row["word"]] = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        added += 1
    if not added:
        return 0
    with open(SUPPLEMENT, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for word in sorted(existing):
                gz.write(existing[word].encode("utf-8"))
    return added


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", action="append",
                        help="daughter stage to read (repeatable; default iir-pro)")
    parser.add_argument("--check", action="store_true", help="report only, write nothing")
    args = parser.parse_args()
    langs = args.lang or ["iir-pro"]
    total = 0
    for lang in langs:
        rows, refused = candidates(lang)
        print(f"{lang}: {len(rows)} ancestor entries the records justify")
        for row in rows:
            print("  +", row["word"], "=", " + ".join(p[0] for p in row["built_as"][0]["pieces"]),
                  f"({len(row['cited_by'])} citation{'s' if len(row['cited_by']) > 1 else ''})")
        if args.check:
            for word, why in refused:
                print("  -", word, why)
        if not args.check:
            total += write(rows)
    if not args.check:
        print(f"wrote {total} new entries; rebuild with "
              f"`python3 tools/build_lexicons.py --supplements-only`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
