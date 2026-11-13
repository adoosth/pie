#!/usr/bin/env python3
"""What Dehkhoda says a word *is*: the label he prints beside every headword.

Every entry in the dictionary opens with the headword, its pronunciation and a
parenthetical grammar tag — ``(اِ مرکب)`` "noun, compound", ``(ص نسبی)``
"relative adjective", ``(اِخ)`` "proper noun", ``(هزوارش)`` "huzvarish".  That
tag is a record, exactly as a language tag is: it is the dictionary saying
something about the word, and reading it is not a guess of ours.

This tool reads the tag from the entry pages already cached under
``data/meanings/fa/`` and writes one row per headword to
``data/dehkhoda/structure.jsonl.gz``.  The row keeps the tag **verbatim** and
only the flags the tag itself states:

    word         the headword as the dictionary prints it
    label        the parenthetical, verbatim (spaces normalised)
    pos          a part of speech, only for the abbreviations that are certain
    compound     the tag says مرکب (or ترکیب اضافی): a compound, not a root
    relational   the tag says نسبی: a relative adjective, i.e. -ی on a noun
    diminutive   the tag says مصغر
    huzvarish    the tag says هزوارش: a Middle Persian heterogram
    affix        the tag says پسوند/پیشوند: the entry heads a bound morpheme
    name         the tag says اِخ: a proper noun

Nothing here is an etymology.  A word labelled ``مرکب`` is a word the
dictionary calls a compound; the tool does not claim which words it is made of,
and a word labelled ``اِخ`` is a name, not a loan.

The labels are read with the dictionary's own abbreviations, which are also
printed on its first pages:

    اِ اسم noun              اِخ اسم خاص proper noun
    ص صفت adj                ص نسبی relative adj · ص لیاقت "fit to" adj
    ق قید adv                مص مصدر infinitive (the verb itself)
    حامص حاصل مصدر verbal noun · اِمص اسم مصدر verbal noun
    نف نعت فاعلی present participle · ن مف نعت مفعولی past participle
    صوت اسم صوت interjection  پسوند/پیشوند an affix

``--merge`` is not used: the rows are joined to the lexicon at load time by
``pie.data.lexicon`` so the 9 MB Persian lexicon stays byte-identical.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import data  # noqa: E402

OUT = data.DATA / "dehkhoda" / "structure.jsonl.gz"
MEANINGS = data.DATA / "meanings" / "fa"

#: The headword (one token), an optional period and pronunciation in brackets,
#: then the grammar tag in the first parenthetical.  Anchored to a single-token
#: headword, because a parenthesis late in an entry is prose and not a label:
#: "آب . مایع حیات (به گفتهٔ فردوسی) روان است" must read as no label at all.
#: The pronunciation block can be long ("[ زِءْ ب ِ / زُءْ ب ُ / زَبَر … ]"), and
#: capping it at 40 characters silently dropped 53 entries with a clear tag
#: (review, 2026-11-10).
LABEL = re.compile(r"^(\S{1,40}?)\s*\.?\s*(?:\[[^\]]{0,120}\]\s*\.?\s*)?\(([^()]{1,80})\)")

#: A tag is a short run of the dictionary's own abbreviations.  Anything with a
#: digit, a quotation, or a phrase in it is prose that happens to be bracketed.
LABEL_CHARS = re.compile(r"^[\u0620-\u064A\u0671-\u06D3\u06FA-\u06FF\u200c"
                         r"\u0654\u064B-\u0652 /،,.‌-]{1,40}$")

#: The dictionary's abbreviations → the part of speech they stand for.  Only
#: the ones whose meaning is not in doubt: a tag outside this map keeps its
#: verbatim label and no `pos`.
POS = {
    "اِ": "noun",
    "اِخ": "name",
    "ص": "adj",
    "ص نسبی": "adj",
    "ص لیاقت": "adj",
    "ق": "adv",
    "مص": "verb",
    "حامص": "noun",
    "اِمص": "noun",
    "نف": "adj",
    "ن مف": "adj",
    "صوت": "intj",
    "اِ صوت": "intj",
    "پسوند": "suffix",
    "پیشوند": "prefix",
    # The dictionary prints a few of its tags without the space that separates
    # the abbreviation from its modifier ("اِمرکب" for "اِ مرکب") and names the
    # word class of a function word in words, not abbreviations.
    "حرف اضافه": "prep",
    "حرف ربط": "conj",
    "حرف ندا": "interj",
}

#: The languages and marks the dictionary prints in the same parenthesis as the
#: grammar tag — ``(ع اِ)`` Arabic noun, ``(فرانسوی ، اِ)`` French noun.  They
#: are stripped before the tag is read, because they are the entry's origin and
#: not its part of speech.
LANG_TOKENS = frozenset({
    "ع", "عربی", "معرب", "از", "ترکی", "ترک", "مغولی", "تاتاری", "افغان",
    "فرانسوی", "فرانسه", "ایتالیایی", "اسپانیایی", "پرتغالی", "هلندی",
    "انگلیسی", "آلمانی", "روسی", "یونانی", "لاتین", "لاتینی", "هندی",
    "سانسکریت", "سنسکریت", "کردی", "ارمنی", "عبری", "سریانی", "چینی",
    "ژاپنی", "فنلاندی", "پهلوی", "اوستایی", "هزوارش", "اروپایی",
})

#: Flags the tag states outright.  Each needle is matched against a token of
#: the label, so "(ص مرکب ، ق مرکب)" carries compound once and a word whose
#: label says nothing about names is never called a name.
FLAGS = {
    # ترکیب اضافی and ترکیب وصفی name a compound in words rather than with
    # «مرکب»; the docstring has always counted them and the reader did not
    # (review, 2026-11-10).
    "compound": ("مرکب", "ترکیب"),
    "relational": ("نسبی",),
    "diminutive": ("مصغر",),
    "huzvarish": ("هزوارش",),
    "affix": ("پسوند", "پیشوند"),
    "name": ("اِخ",),
}


def normalise(label: str) -> str:
    label = unicodedata.normalize("NFC", label)
    # The ezafe mark the dictionary sometimes prints inside a tag
    # ("حرف اضافهٔ مرکب") is orthography, not a word: drop it so the tag reads
    # as the abbreviation plus its modifier.
    label = label.replace("\u0654", "").replace("\u200c", " ").replace("،", " ، ").replace("  ", " ")
    return re.sub(r"\s+", " ", label).strip()


def read_label(text: str) -> str | None:
    """The grammar tag this entry opens with, verbatim, or None."""
    text = (text or "").lstrip()
    if not text:
        return None
    m = LABEL.match(text)
    if not m:
        return None
    label = normalise(m.group(2))
    if not label or not LABEL_CHARS.match(label):
        return None
    return label


def row(word: str, label: str) -> dict:
    out = {"word": word, "label": label}
    pos = pos_of(label)
    if pos:
        out["pos"] = pos
    tokens = [_ for part in label.replace("،", " ").replace("/", " ").split()
              for _ in [part]]
    for flag, needles in FLAGS.items():
        if any(n == t or (flag != "name" and n in t) for t in tokens for n in needles):
            out[flag] = True
    return out


def pos_of(label: str) -> str | None:
    """The part of speech the tag states, or None when it is not certain.

    ``(ع اِ)`` is an Arabic noun: the ``ع`` is the entry's origin and the ``اِ``
    is the grammar.  A tag like ``(اِ مرکب ، ق مرکب)`` states two parts of
    speech; the first certain one is taken.  Anything outside the map — ``ن تف``,
    a typo, a phrase — gets no part of speech, because a guessed one would read
    as the dictionary's word for it.
    """
    if label in POS:
        return POS[label]
    for part in label.split("،"):
        tokens = [t for t in part.replace("/", " ").split() if t]
        foreign = bool(tokens) and tokens[0] in LANG_TOKENS
        while tokens and tokens[0] in LANG_TOKENS:
            tokens.pop(0)
        # An Arabic maṣdar is a *noun* in Persian: فظاظة is «درشتخوی گردیدن»
        # in Dehkhoda's words, but the word a Persian sentence uses is the
        # noun «درشتخویی», and the page called it a verb (critic batch 08,
        # 2026-11-13).  A Persian مص (an infinitive) is still a verb.
        if foreign and tokens == ["مص"]:
            return "noun"
        # "اِمرکب" and "اِمصغر" are one word: the modifier ran into the
        # abbreviation.  Split it off before the lookup and keep reading.
        if tokens:
            for suffix in ("مرکب", "مصغر"):
                if tokens[0].endswith(suffix) and tokens[0] != suffix:
                    head = tokens[0][: -len(suffix)]
                    if head:
                        tokens = [head, suffix] + tokens[1:]
                        break
        for i in range(len(tokens), 0, -1):
            candidate = " ".join(tokens[:i])
            if candidate in POS:
                return POS[candidate]
    return None


def cached_entries(meanings: Path) -> dict[str, str]:
    """Every cached Dehkhoda page, loose file or packed shard.

    The cache went from one file per word to 256 shards (`tools/pack_meanings.py`)
    so the tree stopped costing 4 KB a word; a reader that only globbed
    `*.json.gz` would have found the few loose files and nothing else
    (2026-11-12).
    """
    out: dict[str, str] = {}
    rows: list[tuple[str, dict]] = []
    for path in sorted(meanings.glob("*.json.gz")):
        word = unicodedata.normalize("NFC", __import__("urllib.parse", fromlist=["unquote"])
                                      .unquote(path.name[: -len(".json.gz")]))
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                rows.append((word, json.load(fh)))
        except Exception:  # noqa: BLE001 - a half-written cache file is skipped
            continue
    for path in sorted((meanings.parent / "packs").glob("*.jsonl.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if row.get("w"):
                        rows.append((unicodedata.normalize("NFC", row["w"]), row.get("row") or {}))
        except OSError:
            continue
    for word, payload in rows:
        entries = payload.get("entries") or []
        # One page can print several words; the tag to read is the one under
        # this headword, not whichever entry happens to come first (review,
        # 2026-11-10).
        chosen = None
        for entry in entries:
            if str(entry.get("head") or "").strip() == word:
                chosen = entry
                break
        if chosen is not None or entries:
            out[word] = (chosen or entries[0]).get("text") or ""
    return out


def build(lexicon: Path, meanings: Path) -> tuple[list[dict], Counter]:
    entries = cached_entries(meanings)
    stats: Counter = Counter()
    rows: list[dict] = []
    seen: set[str] = set()
    for word in sorted(entries):
        if word in seen or not word or " " in word:
            continue
        seen.add(word)
        label = read_label(entries[word])
        if not label:
            stats["no label"] += 1
            continue
        stats["labelled"] += 1
        rows.append(row(word, label))
        for key in ("compound", "relational", "diminutive", "huzvarish", "affix", "name", "pos"):
            if rows[-1].get(key):
                stats[key] += 1
    return rows, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lexicon", type=Path, default=data.DATA / "lexicon" / "fa.jsonl.gz")
    ap.add_argument("--meanings", type=Path, default=MEANINGS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args(argv)
    rows, stats = build(args.lexicon, args.meanings)
    held = {e["word"] for e in data.lexicon("fa")}
    stray = [r["word"] for r in rows if r["word"] not in held]
    print(f"{len(rows):,} headwords labelled · {dict(stats)}")
    print(f"{len(stray):,} labels for words the glossary does not hold"
          + (f" (e.g. {', '.join(stray[:6])})" if stray else ""))
    counts = Counter(r["label"] for r in rows)
    for label, n in counts.most_common(18):
        print(f"  {n:6d}  {label}")
    if args.check:
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".tmp")
    with tmp.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
                         .encode("utf-8"))
    tmp.replace(args.out)
    print(f"wrote {args.out} ({args.out.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
