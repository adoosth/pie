#!/usr/bin/env python3
"""Dehkhoda's headwords as Persian glossary entries (2026-11-10).

The dictionary's inventory is read from vajehyab's sitemaps (``tools/
dehkhoda_index.py``) and written as a supplement, one row per single-token
headword the built Wiktionary lexicon does not already hold.  A row states only
what is known from the index: the spelling, the dictionary it is a headword of,
and the page that prints its entry.  It carries **no** etymology, part of speech
or gloss of its own — those are read from that page when a reader opens it (the
meanings tab), and a word with no recorded origin stays in the `unexplained`
band, which is the honest place for it.

Multi-word headwords are not stored: a phrase is an entry in a dictionary, not
a word of the language, and this glossary counts words.  Their number is
reported so the omission is visible rather than silent.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from pie import data

OUT = data.DATA / "lexicon" / "_supplement" / "fa.dehkhoda.jsonl.gz"
HEADS = data.DATA / "dehkhoda" / "heads.txt"
FA = data.DATA / "lexicon" / "fa.jsonl.gz"
#: A Persian word: Arabic-script letters and the ZWNJ, nothing else.
WORD = re.compile(r"^[\u0620-\u064A\u0671-\u06D3\u06FA-\u06FF\u200c]+$")


def read_heads(path: Path = HEADS) -> list[str]:
    if not path.exists():
        raise SystemExit(f"{path} is missing — run tools/dehkhoda_index.py --fetch")
    return [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip()]


def held(path: Path = FA) -> set[str]:
    out: set[str] = set()
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            out.add(json.loads(line)["word"])
    return out


def classify(word: str) -> str:
    if " " in word:
        return "phrase"
    if "-" in word:
        return "phrase"          # the sitemap writes a space as a hyphen
    if not WORD.match(word):
        return "other"
    if len(word) < 2:
        return "short"
    if len(word) > 24:
        return "long"
    return "word"


def rows(words, glosses: dict[str, list[str]] | None = None,
         marks: dict[str, tuple[str, str]] | None = None):
    """One entry per headword, with only what the dictionary itself prints.

    ``glosses`` is Dehkhoda's own first line; ``marks`` is the language tag it
    prints beside the word and the code that tag means.  A tag is a *record*:
    (ع اِ) is the dictionary saying Arabic, so it becomes `borrowed_from` and
    the word is counted as borrowed rather than unexplained — with the mark
    kept verbatim in `source_note`, because the reader is entitled to see what
    was read (2026-11-10).
    """
    glosses = glosses or {}
    marks = marks or {}
    for word in words:
        row = {
            "word": word,
            "lang": "fa",
            "source": "dehkhoda",
            "sources": ["dehkhoda"],
            "pos": "",
            "gloss": list(glosses.get(word) or []),
            "url": f"https://vajehyab.com/dehkhoda/{quote(word, safe='')}",
        }
        mark = marks.get(word)
        if mark:
            code, tag = mark
            if code:
                row["borrowed_from"] = code
                row["source_note"] = f"Dehkhoda marks this word ({tag})"
        yield row


def read_glosses(path: Path | None) -> dict[str, list[str]]:
    """Every gloss read so far, from the first worker's file and its shards."""
    return {word: gloss for word, (gloss, _mark) in _read_rows(path).items()}


def read_marks(path: Path | None) -> dict[str, tuple[str, str]]:
    """The language tag Dehkhoda prints for a word: ``word -> (code, tag)``."""
    return {word: mark for word, (_gloss, mark) in _read_rows(path).items() if mark}


def _read_rows(path: Path | None) -> dict[str, tuple[list[str], tuple[str, str] | None]]:
    out: dict[str, tuple[list[str], tuple[str, str] | None]] = {}
    if not path:
        return out
    # `glosses.jsonl.gz` and its four shards are one set: the stem is the part
    # before the first hyphen, or the whole name when there is none — the old
    # expression globbed "glosses.jsonl.gz*.jsonl.gz" and silently read nothing
    # (2026-11-10).
    stem = path.name.split("-")[0] if "-" in path.name else path.name.split(".")[0]
    for part in sorted(path.parent.glob(stem + "*.jsonl.gz")):
        try:
            with gzip.open(part, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    word = row.get("word")
                    if not word:
                        continue
                    mark = (row.get("origin") or "", row.get("tag") or "")
                    out[word] = (list(row.get("gloss") or []),
                                 mark if mark[0] else None)
        # A worker may be writing this shard right now: a truncated gzip
        # stream raises zlib.error, and one unreadable file must not lose
        # the rows every other file already has (2026-11-10).
        except Exception:  # noqa: BLE001
            continue
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--heads", type=Path, default=HEADS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--glosses", type=Path, default=None,
                    help="jsonl.gz of {word, gloss} read from Dehkhoda's pages")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true",
                    help="rewrite every stored row, not only the new words "
                         "(used to add the meanings read after the first import)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    heads = read_heads(args.heads)
    have = held()
    kinds: dict[str, int] = {}
    keep: list[str] = []
    seen: set[str] = set()
    for word in heads:
        kind = classify(word)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind != "word" or word in seen or (word in have and not args.refresh):
            continue
        seen.add(word)
        keep.append(word)
    if args.limit:
        keep = keep[: args.limit]
    glosses = read_glosses(args.glosses)
    marks = read_marks(args.glosses)
    print(f"{len(heads)} headwords · " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    with_gloss = sum(1 for w in keep if w in glosses)
    with_mark = sum(1 for w in keep if w in marks)
    more = f" ({with_gloss} with a gloss, {with_mark} with a language mark)" if glosses else ""
    print(f"{len(keep)} new single-token words to store{more}")
    if args.dry_run:
        for word in keep[:15]:
            print("  ", word)
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".tmp")
    with tmp.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for row in rows(keep, glosses, marks):
                gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                         .encode("utf-8"))
    tmp.replace(args.out)
    print(f"wrote {args.out} ({args.out.stat().st_size/1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
