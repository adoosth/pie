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
import unicodedata
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


#: A clause that is Dehkhoda's **comparative etymology** rather than a meaning:
#: نشیب opens «اوستا: نیخشوئپه ، پهلوی : …، کردی : …» and the meaning is the
#: clause after it, which the page printed as a list cut at «کردی :» (critic
#: batch 07, 2026-11-13).
COMPARATIVE = re.compile(
    r"^\s*(?:اوستا|پهلوی|پازند|کردی|بلوچی|افغانی|پشتو|تاجیکی|عربی|ترکی|ارمنی|"
    r"سریانی|عبری|سانسکریت|سنسکریت|هندی|یونانی|لاتینی|فارسی|معرب|آرامی|"
    r"اوستایی|پهلوی اشکانی|پارسی)\s*:")
#: Notes about the word's *shape*, not its meaning: «یا الغاز،» names another
#: spelling and «بر وزن پی سوز،» the pattern it scans (القاز، قیسوس, critic
#: batch 07, 2026-11-13).
SHAPE_NOTE = re.compile(r"^\s*(?:یا\s+.{1,30}?[،,]|بر\s+وزن\s+.{1,40}?[،,])\s*")
#: A clause that is only Dehkhoda's source note — «(از حاشیهٔ برهان چ معین )»,
#: «(از ناظم الاطباء)» — or only a plural/reading note «ج ِ مَزبله [ ب َ ]».
NOTE_ONLY = re.compile(r"^(?:\([^()]{0,60}\)\s*)+$|^\(?از\s[^()]{0,60}\)?$")
#: A Persian verb, near enough to tell a definition («از شاعران بود») from a
#: label that only names a person («احمد اطعمهٔ شیرازی»).
VERBISH = re.compile(
    r"(?:^|\s)(?:است|بود|بودند|بوده|هست|نیست|شد|شود|شدند|باشد|باشند|کرد|کند|"
    r"دارد|داشت|یافت|گشت|متوفی|از\s+شاعران|می‌\S+|نمی‌\S+)(?:\s|$)")


def _letters(text: str) -> str:
    """The consonants of a Persian spelling: harakat and ZWNJ taken away."""
    return "".join(ch for ch in unicodedata.normalize("NFD", str(text or ""))
                   if not unicodedata.combining(ch)
                   and ch not in "\u200c\u0640 .،؛:")


def _is_respelling(token: str, head: str) -> bool:
    """Whether a clause is the headword written again, with its vowels."""
    if not token or not head:
        return False
    a, b = _letters(token), _letters(head)
    if len(a) < 3 or len(b) < 3 or abs(len(a) - len(b)) > 2:
        return False
    if a == b:
        return True
    if a[:2] != b[:2]:
        return False
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.85


def _meaning_clause(line: str, head: str, tag: str = "") -> str:
    """The first clause of Dehkhoda's run that is a meaning.

    The dictionary's first clause is often **notation**: the headword respelled
    with its vowels (اسقوربوط «اِسْقُربوط. مرضی ساری …»), a comparative
    etymology list (نشیب), the name of the person a name entry is about
    (اطعمه «احمد اطعمهٔ شیرازی . از شاعران بود …»).  Each is skipped when a
    clause that does define the word follows — never when it is all there is,
    because an empty meaning is a worse page than a terse one (critic batch 07,
    2026-11-13).
    """
    # «||» is Dehkhoda's own boundary between senses; " . " separates sentences.
    clauses = [c.strip(" .،؛:") for c in
               re.split(r"\s*\|\|\s*|\s\.\s|\.\s", line) if c.strip(" .،؛:")]
    if len(clauses) < 2:
        return line
    name_entry = "اِخ" in (tag or "") or "اَخ" in (tag or "")
    for index, clause in enumerate(clauses):
        if index == len(clauses) - 1:
            break
        if COMPARATIVE.match(clause) or NOTE_ONLY.match(clause):
            continue
        if _is_respelling(clause, head):
            continue
        # A name entry opens with the name and defines the person in the next
        # clause: skip a bare name, keep a clause that says something.
        if (name_entry and len(clause.split()) <= 5 and not VERBISH.search(clause)
                and VERBISH.search(clauses[index + 1])):
            continue
        return _with_synonyms(clause, clauses[index + 1:])
    return clauses[-1]


def _with_synonyms(clause: str, following: list[str]) -> str:
    """The meaning and the short equivalents Dehkhoda lists beside it.

    «بیمار. علیل. مریض. رنجور. ناسالم . دردمند.» is one sense written six ways,
    and taking only the first word left the page saying «بیمار» for a word whose
    whole point is the list.  A further clause is kept while it is short and is
    not the dictionary's apparatus; a sentence that runs on is not a synonym and
    ends the meaning, which is also where the 160-character cut lands.
    """
    out = [clause]
    for extra in following:
        extra = extra.strip(" .،؛:")
        if not extra or len(extra.split()) > 4 or len(extra) > 40:
            break
        if COMPARATIVE.match(extra) or NOTE_ONLY.match(extra) or VERBISH.search(extra):
            break
        if len(" . ".join(out + [extra])) > 120:
            break
        out.append(extra)
        if len(out) >= 4:
            break
    return " . ".join(out)


def first_line(text: str, head: str, tag: str = "") -> str:
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
        # The word's shape is not its meaning (القاز «یا الغاز، …», قیسوس
        # «بر وزن پی سوز، …»): the note comes off and the definition stays.
        line = SHAPE_NOTE.sub("", line).strip() or line
        line = _meaning_clause(line, head, tag)
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
    # The cache is a loose file per word *or* a row in one of the packed shards
    # (`tools/pack_meanings.py` folded 153k loose files into 256).  Asking for
    # one word at a time reopened a whole shard per word; walking the cache once
    # reads each shard once (2026-11-13).
    wanted = set(words)
    n = marks = 0
    written: set[str] = set()
    with open(tmp, "wb") as raw:
        stream = gzip.GzipFile(fileobj=raw, mode="wb", mtime=0)
        for word, row in meanings.iter_cache():
            if word in written or word not in wanted:
                continue
            if not row or not row.get("entries"):
                continue
            first = row["entries"][0]
            tag = tag_of(first.get("text", ""))
            gloss = first_line(first.get("text", ""), first.get("head") or word, tag)
            if not gloss:
                continue
            origin = lang_of(tag)
            marks += 1 if origin else 0
            n += 1
            written.add(word)
            stream.write((json.dumps({"word": word, "gloss": [gloss], "tag": tag,
                                      "origin": origin, "url": row.get("url", "")},
                                     ensure_ascii=False) + "\n").encode("utf-8"))
        stream.close()
    # The old shards stay beside this file: `import_dehkhoda._read_rows` reads
    # them first and this one last, so a row rebuilt here always wins, and a
    # word whose page was never cached keeps the reading it had (2026-11-13).
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
                gloss = first_line(first.get("text", ""), first.get("head") or word,
                                   tag_of(first.get("text", "")))
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
