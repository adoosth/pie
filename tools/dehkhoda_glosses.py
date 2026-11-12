#!/usr/bin/env python3
"""Read Dehkhoda's own words for its headwords, politely and resumably.

Each headword's page on vajehyab.com holds the dictionary's entry.  This tool
walks the stored headword list once, reads the first line of the first entry —
never the whole text: the page is kept in `pie.meanings`' cache for the reader,
and the short gloss is written beside it so the glossary can print something
the dictionary actually says instead of an empty cell.

Rate-limited and resumable: an interrupted run loses nothing, and a page that
does not answer is skipped rather than retried in a loop.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import sys
import time
from pathlib import Path

from pie import data, meanings

SUPP = data.DATA / "lexicon" / "_supplement" / "fa.dehkhoda.jsonl.gz"
OUT = data.DATA / "dehkhoda" / "glosses.jsonl.gz"
def out_path(shard: int, of: int):
    """One file per worker: appending to one file from several processes is a
    race, and a worker that dies must not take the others' rows with it."""
    if of <= 1:
        return OUT
    return OUT.with_name(f"glosses-{shard}.jsonl.gz")
MAXLEN = 160


def words(path: Path) -> list[str]:
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return [json.loads(line)["word"] for line in fh if line.strip()]
    raise SystemExit(f"{path} is missing — run tools/import_dehkhoda.py first")


def done(path: Path) -> set[str]:
    """Every word already read, across all workers' files.

    A worker's file is read while it is still being written, so the last line
    may be incomplete: that row is simply read again by somebody later.
    """
    seen: set[str] = set()
    for part in sorted(path.parent.glob("glosses*.jsonl.gz")):
        try:
            with gzip.open(part, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        seen.add(json.loads(line)["word"])
                    except (ValueError, KeyError):
                        continue
        except Exception:  # noqa: BLE001 - a shard being written is not a crash
            continue
    return seen


def first_line(text: str, head: str) -> str:
    """The dictionary's first sentence, with the headword taken off the front."""
    for line in (text or "").splitlines():
        line = re.sub(r"\s+", " ", line).strip(" .:‌\u00a0")
        if not line:
            continue
        if head and line.startswith(head):
            line = line[len(head):].lstrip(" :.،-").strip()
        # The dictionary's apparatus comes off the front, in whatever order it
        # is written: a pronunciation in brackets and the language/part of
        # speech mark in parentheses are both stored beside the gloss already,
        # so «[ ءَ ] (ع اِ) ج ِ اِبط» is the meaning «ج ِ اِبط» (2026-11-10).
        for _ in range(4):
            stripped = re.sub(
                r"^(?:\[[^\]]{0,80}\]|[\(（][^\)）]{1,24}[\)）])\s*", "", line).strip()
            if stripped == line:
                break
            line = stripped
        if len(line) < 2:
            continue
        if len(line) > MAXLEN:
            cut = max(line.rfind(x, 0, MAXLEN) for x in "،؛.:")
            line = line[: cut + 1] if cut > 40 else line[:MAXLEN].rstrip() + "…"
        return line
    return ""


#: Dehkhoda writes a headword, then a pronunciation in brackets, then the part
#: of speech — and the language, when it is not Persian: «آءة. [ ءَ ] (ع اِ) …».
#: The tag is the first parenthetical of the entry's first line; a pronunciation
#: is bracketed, not parenthesised, so it is skipped rather than parsed
#: (2026-11-10).
TAG = re.compile(r"^[^()（）]{0,60}[\(（]\s*([^\)）]{1,24})\s*[\)）]")
#: Dehkhoda's own abbreviation for the language a word comes from.  Only what
#: the dictionary itself prints is read here; the tag is kept beside the gloss so
#: a later run can say "Dehkhoda marks this word Arabic" and quote the mark.
LANG_TAGS = {
    "ع": "ar", "عربی": "ar", "معرب": "ar", "فر": "fr", "فرا": "fr",
    "فرانسه": "fr", "انگ": "en", "انگلیسی": "en", "ترک": "tr", "ترکی": "tr",
    "یون": "el", "یونانی": "el", "لات": "la", "لاتین": "la", "سریانی": "syc",
    "عبری": "he", "هندی": "hi", "روس": "ru", "روسی": "ru", "آلمانی": "de",
    "ایتالیایی": "it", "اسپانیایی": "es", "پرتغالی": "pt", "ارمنی": "hy",
    "مغولی": "mn", "چینی": "zh", "ژاپنی": "ja", "اردو": "ur", "کردی": "ku",
    # The adjectival spellings: Dehkhoda writes «(فرانسوی ، اِ)» as often as
    # «(فر)», and 1,053 Persian words carry the French one (2026-11-10).
    "فرانسوی": "fr", "انگلیسی": "en", "لاتینی": "la", "پرتغالی": "pt",
    "هلندی": "nl", "دانمارکی": "da", "سوئدی": "sv", "مجاری": "hu",
    "رومانیایی": "ro", "بلغاری": "bg", "صربی": "sr", "لهستانی": "pl",
    "چک": "cs", "یونانی": "el", "عبرانی": "he", "آلمانی": "de",
}


def tag_of(text: str) -> str:
    m = TAG.match(text or "")
    return m.group(1).strip() if m else ""


def lang_of(tag: str) -> str:
    for word in re.split(r"[\s،,]+", tag):
        if word in LANG_TAGS:
            return LANG_TAGS[word]
    return ""


def _from_cache(words: list[str]) -> int:
    """Rewrite the glossary rows from the pages already stored on disk.

    A reader that mis-reads a tag is worth fixing twice: once in the code and
    once in the 27,000 pages it has already paid for.  Nothing here touches the
    network — a word with no stored page is simply left out, and the next live
    pass will reach it.
    """
    out = OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    n = marks = 0
    with open(tmp, "wb") as raw:
        stream = gzip.GzipFile(fileobj=raw, mode="wb", mtime=0)
        for word in words:
            path = meanings._cache_path(word)
            if not path.exists():
                continue
            try:
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    row = json.load(fh)
            except Exception:  # noqa: BLE001 - an unreadable page is skipped
                continue
            if not row.get("entries"):
                continue
            first = row["entries"][0]
            gloss = first_line(first.get("text", ""), first.get("head") or word)
            if not gloss:
                continue
            tag = tag_of(first.get("text", ""))
            origin = lang_of(tag)
            marks += 1 if origin else 0
            n += 1
            stream.write((json.dumps({"word": word, "gloss": [gloss], "tag": tag,
                                      "origin": origin, "url": row.get("url", "")},
                                     ensure_ascii=False) + "\n").encode("utf-8"))
        stream.close()
    tmp.replace(out)
    print(f"rebuilt {n} rows from the cache ({marks} with a language mark)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rate", type=float, default=4.0, help="pages per second")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0, help="this worker's slice (0-based)")
    ap.add_argument("--of", type=int, default=1, help="how many workers share the list")
    ap.add_argument("--pause-file", type=Path, default=Path("/tmp/dehkhoda-pause"))
    ap.add_argument("--from-cache", action="store_true",
                    help="rebuild the rows from the stored pages, without a "
                         "single request (used after a reader is corrected)")
    args = ap.parse_args(argv)
    todo = words(SUPP)
    have = done(OUT)
    todo = sorted((w for w in todo if w not in have), key=lambda w: (len(w), w))
    if args.of > 1:
        # Several polite readers share the list by a stable hash of the word:
        # no two of them ever read the same page, and an interrupted worker
        # leaves the others' slices untouched.
        import zlib
        todo = [w for w in todo if zlib.crc32(w.encode("utf-8")) % args.of == args.shard]
    if args.limit:
        todo = todo[: args.limit]
    if args.from_cache:
        # Every word with a stored page, not only the ones a live run has not
        # reached: this pass exists to re-derive what the reader got wrong.
        every = words(SUPP)
        return _from_cache(every if not args.limit else every[: args.limit])

    delay = 1.0 / max(0.2, args.rate)
    print(f"{len(todo)} headwords to read", flush=True)
    target = out_path(args.shard, args.of)
    target.parent.mkdir(parents=True, exist_ok=True)
    fails = 0
    with open(target, "ab") as raw:
        stream = gzip.GzipFile(fileobj=raw, mode="wb", mtime=0)
        for n, word in enumerate(todo, 1):
            while args.pause_file.exists():
                time.sleep(5)
            try:
                row = meanings.dehkhoda(word)
            except Exception as exc:  # noqa: BLE001 - a page is not the run
                row, fails = None, fails + 1
                print(f"  ! {word}: {exc}", flush=True)
            gloss = ""
            if row and row.get("entries"):
                first = row["entries"][0]
                gloss = first_line(first.get("text", ""), first.get("head") or word)
            if gloss:
                tag = tag_of(row["entries"][0].get("text", ""))
                stream.write((json.dumps({"word": word, "gloss": [gloss],
                                          "tag": tag, "origin": lang_of(tag),
                                          "url": row.get("url", "")},
                                         ensure_ascii=False) + "\n").encode("utf-8"))
                fails = 0
            elif row is not None:
                # A page that answered but heads nothing is a fact too: record it,
                # so a second run does not re-read the same 150,000 pages to learn
                # the same thing (2026-11-10).
                stream.write((json.dumps({"word": word, "gloss": [], "tag": "",
                                          "origin": "", "url": row.get("url", ""),
                                          "missing": True},
                                         ensure_ascii=False) + "\n").encode("utf-8"))
                fails += 1
            else:
                fails += 1
            if n % 100 == 0:
                stream.flush()
                print(f"  {n}/{len(todo)}  last {word}", flush=True)
            # A long tail of empty entries is normal in a dictionary that lemmatises
            # everything; pages that do not answer at all are not, and 150 in a row
            # means the site has stopped talking to us (2026-11-10).
            if fails >= 150:
                print("  150 pages in a row gave nothing — stopping", flush=True)
                break
            time.sleep(delay * random.uniform(0.7, 1.3))
        stream.close()
    print("stopped", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
