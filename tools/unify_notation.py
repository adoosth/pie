#!/usr/bin/env python3
"""Fold a stage's glossary into its standard romanisation and merge duplicates.

Three steps, all reported:

1. **Romanise.**  A source whose headword is a transliteration rather than a
   reading (Wiktionary heads Middle Persian ``hwʾb``, MacKenzie's dictionary
   was typed without diacritics) takes the reading its own record states —
   ``translit``/``phon`` on the row, or the stage's reading table — and keeps
   the spelling it was quoted under in ``translit_quoted``.
2. **Fold.**  Every remaining headword is written in the stage's standard
   alphabet (``data/notation/<lang>.yaml``: Middle Persian ``j`` → ``ǰ``,
   ``c`` → ``č``), so one word has one spelling.
3. **Merge.**  Rows that now name the same word *and the same sense* are one
   entry: a union of the senses, the sources, the attestation and the
   etymology.  Two senses that differ stay two senses — this merges notation,
   never meanings.

    python tools/unify_notation.py --lang pal [--dry-run]

The loader applies the same fold, so a row added by any importer is read in
the standard notation even before this script runs again.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import notation  # noqa: E402

LEXICON = ROOT / "data" / "lexicon"


def readings(lang: str) -> dict[str, str]:
    """Every reading table the stage has: the spelling it was quoted under → reading."""
    out: dict[str, str] = {}
    for path in sorted((ROOT / "data").glob(f"readings_{lang}*.json")):
        try:
            with path.open(encoding="utf-8") as fh:
                table = json.load(fh)
        except (OSError, ValueError):
            continue
        for key, value in table.items():
            if isinstance(value, dict):
                text = str(value.get("reading") or "").strip()
                if text:
                    out.setdefault(str(key), text)
    return out


def stated_reading(lang: str, row: dict, table: dict[str, str]) -> str:
    """The reading a row states for itself, when it states one as a reading.

    ``phon`` is the word's pronunciation, ``translit`` the romanisation the
    compiler wrote beside the spelling — but MacKenzie's rows carry his
    bracketed Pahlavi spelling there ("ypytl | M y ydt N ~"), which is not a
    reading of anything.  A candidate is used only when it spells the stage's
    romanisation (first alternative of a "this, or that" pair), so a damaged
    spelling is never promoted to a headword.
    """
    fields = (notation.table(lang).get("reading_fields") or {}).get(str(row.get("source")), [])
    candidates = [row.get(field) for field in fields] + list(row.get("translit_alt") or [])
    for raw in candidates + [table.get(str(row.get("word") or ""), "")]:
        text = str(raw or "").strip()
        if not text:
            continue
        text = re.split(r"[,/;]", text)[0].strip().strip("*")
        text = notation.canonical(lang, text)
        if not text:
            continue
        if all(ch in notation.letters(lang) or ch in notation.PUNCTUATION for ch in text):
            return text
    return ""


def romanise(lang: str, rows: list[dict], table: dict[str, str]) -> list[dict]:
    sources = notation.romanise_sources(lang)
    changed = 0
    for row in rows:
        if row.get("source") not in sources:
            continue
        # A headword written in a script is a writing, not a transliteration:
        # 𐫀𐫡𐫘 stays the word and keeps its reading beside it.  Only a Latin
        # transliteration (hwʾb, lwc) is replaced by the reading it states.
        if any(ch and notation.is_quoted_script(lang, ch) for ch in str(row.get("word"))):
            continue
        reading = stated_reading(lang, row, table)
        if not reading or reading == row.get("word"):
            continue
        row.setdefault("translit_quoted", row.get("word"))
        row["word"] = reading
        changed += 1
    return rows if not changed else rows


def _split_senses(gloss) -> list[str]:
    """One gloss line as the senses it lists ("treasure, treasury" → two)."""
    if isinstance(gloss, str):
        gloss = [gloss]
    out: list[str] = []
    for text in gloss or []:
        depth = 0
        piece = ""
        for ch in str(text):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            if ch in ";·" or (ch == "," and depth == 0):
                if piece.strip():
                    out.append(piece.strip())
                piece = ""
                continue
            piece += ch
        if piece.strip():
            out.append(piece.strip())
    return out


def senses_of(row: dict) -> set[str]:
    """The senses a row states, compared without the wording's apparatus.

    A trailing parenthesis is the dictionary's note ("faith (especially
    non-Mazdean)"), not part of the sense, so it is cut before comparing.
    """
    out = set()
    for text in _split_senses(row.get("gloss")):
        text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
        text = text.strip(" .,;:").casefold()
        if text:
            out.add(text)
    return out


def same_entry(lang: str, a: set[str], b: set[str], row_a: dict, row_b: dict) -> bool:
    """Whether two rows record the same sense of one word.

    The two rows must record the *same* senses.  Containment is not enough:
    MacKenzie's dictionary files several homographs under one headword (his
    az entry carries "except", "fertile", "dragon" and the preposition in one
    gloss), so a subset rule let that one row swallow every az the corpus
    has.  Equal sense sets merge; anything else stays a sense of its own
    (2026-11-13).
    """
    if not a or not b:
        return False
    if a == b:
        return True
    bundled = notation.bundled_sources(lang)
    if row_a.get("source") in bundled or row_b.get("source") in bundled:
        return False
    return a <= b or b <= a


def richer(a: dict, b: dict) -> dict:
    """The row that says more: an etymology, then attestation, then the standard source."""
    def weight(row: dict) -> tuple:
        return (bool(row.get("anc")), bool(row.get("etym")), int(row.get("occurrences") or 0),
                row.get("source") == "mpcd", len(row.get("ref") or ""))
    return a if weight(a) >= weight(b) else b


def combined(cluster: list[dict]) -> dict:
    """One entry from the rows that record the same word and the same sense."""
    base = cluster[0]
    for row in cluster[1:]:
        base = richer(base, row)
    entry = dict(base)
    gloss = [str(text) for text in (base.get("gloss") or [])]
    covered = senses_of({"gloss": gloss})
    for row in cluster:
        if row is base:
            continue
        for text in row.get("gloss") or []:
            senses = senses_of({"gloss": [text]})
            if senses and senses <= covered:
                continue
            if str(text) not in gloss:
                gloss.append(str(text))
                covered |= senses
        for src in row.get("sources") or [row.get("source")]:
            if src and src not in entry.setdefault("sources", []):
                entry["sources"].append(src)
        entry["occurrences"] = (max(int(entry.get("occurrences") or 0),
                                    int(row.get("occurrences") or 0))
                                or entry.get("occurrences"))
        for field, value in row.items():
            if field in ("word", "gloss", "sources", "source", "occurrences"):
                continue
            entry.setdefault(field, value)
    entry["gloss"] = gloss
    entry["sources"] = entry.get("sources") or [entry.get("source")]
    return entry


def merge(lang: str, rows: list[dict]) -> tuple[list[dict], list[tuple[str, int]]]:
    by_word: dict[str, list[dict]] = {}
    order: list[str] = []
    for row in rows:
        word = str(row.get("word") or "")
        if word not in by_word:
            order.append(word)
        by_word.setdefault(word, []).append(row)
    out: list[dict] = []
    report: list[tuple[str, int]] = []
    for word in order:
        clusters: list[list[dict]] = []
        for row in by_word[word]:
            senses = senses_of(row)
            for cluster in clusters:
                if any(same_entry(lang, senses, senses_of(member), row, member)
                       for member in cluster):
                    cluster.append(row)
                    break
            else:
                clusters.append([row])
        for cluster in clusters:
            out.append(combined(cluster))
            if len(cluster) > 1:
                report.append((word, len(cluster)))
    return out, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    lang = args.lang
    path = LEXICON / f"{lang}.jsonl.gz"
    if not path.exists():
        print(f"no glossary at {path}", file=sys.stderr)
        return 1
    if not notation.table(lang):
        print(f"{lang} states no notation table in data/notation/; nothing to fold", file=sys.stderr)
        return 1

    with gzip.open(path, "rt", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    before = len(rows)

    table = readings(lang)
    translit = sum(1 for row in rows if row.get("source") in notation.romanise_sources(lang)
                   and stated_reading(lang, row, table) not in ("", row.get("word")))
    romanise(lang, rows, table)
    folded = 0
    for row in rows:
        word = notation.canonical(lang, row.get("word") or "")
        if word != row.get("word"):
            row["word"] = word
            folded += 1

    out, merged = merge(lang, rows)
    out.sort(key=lambda row: (row.get("word") or "", tuple(row.get("gloss") or [])))

    variants = notation.variants(lang, [row["word"] for row in out])
    quoted = [row["word"] for row in out if notation.is_quoted(lang, row["word"])]
    bad = notation.offenders(lang, [row["word"] for row in out])
    stuck = {}
    for row in out:
        if row.get("source") in notation.romanise_sources(lang) and not row.get("translit_quoted"):
            stuck[row.get("source")] = stuck.get(row.get("source"), 0) + 1

    print(f"{lang}: {before} rows → {len(out)}")
    print(f"  romanised from a transliteration: {translit}")
    print(f"  headwords folded: {folded}")
    print(f"  duplicate rows merged: {before - len(out)} in {len(merged)} groups")
    print(f"  variant spellings left: {len(variants)}")
    print(f"  headwords still quoted (Avestan/transliteration): {len(quoted)}")
    for source, count in sorted(stuck.items()):
        print(f"    {source}: {count} headwords state no reading and keep their spelling")
    if bad:
        print("  outside the standard alphabet:")
        for word, maths in bad[:40]:
            print(f"    {word}  {maths}")
    for word, count in merged[:20]:
        print(f"    merged {count} × {word}")
    if args.dry_run:
        return 0
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as fh:
        for row in out:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
    tmp.replace(path)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
