"""Meanings from outside the glossary, one tab per source (2026-11-10).

The glossary's own ``gloss`` is Wiktionary's: a short definition, often in
English.  A Persian reader wants the Persian dictionary's own entry beside it,
so the word page carries a tab per source.  Nothing here changes a band, a
derivation or a count: a meaning is a gloss, never evidence about a form.

Dehkhoda's entry is read from vajehyab.com (``/dehkhoda/<word>``), which also
lists the word's other numbered entries (آن، آن (2) …), and the answer is
cached on disk so a page opens instantly after the first visit and still works
offline.  The cache stores only what the page said, with its URL and the time it
was read, so a stale entry can always be traced back.
"""
from __future__ import annotations

import gzip
import json
import re
import time
import zlib
import urllib.error
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote

from . import data

CACHE = data.DATA / "meanings"
UA = ("pie-lexicon/0.16 (+https://github.com/adoosth/pie; meanings tab; "
      "contact adoosth@gwdg.de)")
BASE = "https://vajehyab.com"
#: How many numbered homograph pages to read for one word.  Seven is the most
#: the site lists for آن; the page always links the rest.
MAX_PAGES = 6


class _Entry(HTMLParser):
    """Read one vajehyab page: its headword, definition blocks, other entries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.head = ""
        self.title = ""
        self.blocks: list[str] = []
        self.other: list[str] = []
        self._in_head = False
        self._in_title = False
        self._in_def = 0
        self._in_others = False
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "h1":
            self._in_head = True
        elif tag == "h2":
            self._in_title = True
            self._in_others = "معانی دیگر" in ""  # reset below by text
            self._last_h2: list[str] = []
        elif tag == "div" and (a.get("role") == "definition" or "V-IIZ" in cls):
            self._in_def = 1
            self._buf = []
        elif tag == "div" and self._in_def:
            self._in_def += 1
        elif tag == "br" and self._in_def:
            self._buf.append("\n")
        elif tag == "a" and self._in_others:
            href = a.get("href") or ""
            if href.startswith("/dehkhoda/"):
                self.other.append(href)

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_head = False
        elif tag == "h2":
            self._in_title = False
            text = "".join(getattr(self, "_last_h2", [])).strip()
            self._in_others = "معانی دیگر" in text
        elif tag == "div" and self._in_def:
            self._in_def -= 1
            if not self._in_def:
                text = _tidy("".join(self._buf))
                if text:
                    self.blocks.append(text)
                self._buf = []

    def handle_data(self, text):
        if self._in_head:
            self.head += text
        elif self._in_title:
            self._last_h2.append(text)
        elif self._in_def:
            self._buf.append(text)


#: The dictionary's parenthetical, right after the headword: «(اِخ)» is a
#: proper name, «(اِ)» a noun.
_TAG = re.compile(r"^[^()（）]{0,60}[（(]\s*([^)）]{1,24})\s*[)）]")
#: Dehkhoda's marks for a proper name: a person, a place, a tribe.
NAME_TAGS = ("اِخ", "اَخ")


def tag_of(entry: dict) -> str:
    m = _TAG.match(str((entry or {}).get("text") or ""))
    return m.group(1).strip() if m else ""


def is_name_entry(entry: dict) -> bool:
    tag = tag_of(entry)
    return any(name in tag for name in NAME_TAGS)


def entry_for(entries: list[dict], word: str = "") -> dict | None:
    """The entry to read for a headword that has several.

    A page can print more than one word under one headword.  The one to read is
    the entry filed under this headword, and — when the dictionary gives a
    person's biography first and the word itself after it (ابوشبل «صحابی است»
    before «اسد … شیر», محاسن a scholar before «ج ِ حسن») — the first entry that
    is not a proper name, because the page is the word's, not the man's (critic
    batch 09, 2026-11-13).
    """
    entries = [e for e in entries or [] if str(e.get("text") or "").strip()]
    if not entries:
        return None
    same = [e for e in entries if word and str(e.get("head") or "").strip() == word]
    pool = same or entries
    for entry in pool:
        if not is_name_entry(entry):
            return entry
    return pool[0]


def _tidy(text: str) -> str:
    """One paragraph of the page's own text, line breaks inside it kept."""
    text = unescape(text).replace("\u200c", "\u200c")
    lines = [re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _get(url: str, timeout: float = 12.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def _cache_path(word: str) -> Path:
    safe = quote(word, safe="")
    return CACHE / "fa" / f"{safe}.json.gz"


#: The cache holds one small file per word, and 153,206 of them cost 612 MB on
#: a 4 KB-block file system to store 83 MB of text: the blocks, not the
#: dictionary, were the weight.  `tools/pack_meanings.py` folds the loose files
#: into 256 shards of about 600 words each (2026-11-12).  A lookup is a scan of
#: one shard, a word read since the last pack is a file of its own, and the
#: loose file wins because it is the newer one.
PACKS = CACHE / "packs"
PACK_SHARDS = 256


def _shard_path(word: str) -> Path:
    return PACKS / f"fa-{zlib.crc32(word.encode('utf-8')) % PACK_SHARDS:03d}.jsonl.gz"


def _read_shard(word: str) -> dict | None:
    path = _shard_path(word)
    if not path.exists():
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("w") == word:
                    return row.get("row")
    except OSError:
        return None
    return None


def _read_cache(word: str, max_age: float) -> dict | None:
    path = _cache_path(word)
    row = None
    if path.exists():
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                row = json.load(fh)
        except (OSError, ValueError):
            row = None
    if row is None:
        row = _read_shard(word)
    if row is None:
        return None
    if max_age and time.time() - float(row.get("read_at") or 0) > max_age:
        return None
    return row


def iter_cache():
    """Every cached answer, loose file or packed, as ``(word, row)``.

    The tools that read the whole cache used to glob ``*.json.gz``, which found
    the loose files and nothing in the shards; one iterator means a packed
    cache is the same cache (2026-11-12).
    """
    for path in sorted((CACHE / "fa").glob("*.json.gz")):
        word = unquote(path.name[: -len(".json.gz")])
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                row = json.load(fh)
        except (OSError, ValueError):
            continue
        yield word, row
    for path in sorted(PACKS.glob("*.jsonl.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if row.get("w"):
                        yield row["w"], row.get("row") or {}
        except OSError:
            continue


def _write_cache(word: str, row: dict) -> None:
    path = _cache_path(word)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8") as fh:
            json.dump(row, fh, ensure_ascii=False)
        tmp.replace(path)
    except OSError:
        pass


def dehkhoda(word: str, *, refresh: bool = False,
             max_age: float = 30 * 24 * 3600) -> dict | None:
    """Dehkhoda's entry for *word*, as vajehyab prints it.

    Returns ``{source, url, entries: [{head, url, text}], read_at}``; ``None``
    when the site has no entry or cannot be reached.  A cached answer is used
    for thirty days unless ``refresh`` is set.
    """
    word = (word or "").strip()
    if not word:
        return None
    if not refresh:
        cached = _read_cache(word, max_age)
        if cached:
            return cached
    entries: list[dict] = []
    seen: set[str] = set()
    urls = [f"{BASE}/dehkhoda/{quote(word, safe='')}"]
    read_at = time.time()
    while urls and len(entries) < MAX_PAGES:
        url = urls.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            html = _get(url)
        except (urllib.error.URLError, OSError, ValueError):
            if not entries:
                return None
            break
        page = _Entry()
        page.feed(html)
        head = _tidy(page.head) or word
        text = "\n\n".join(page.blocks)
        if text:
            entries.append({"head": head, "url": url, "text": text})
        for href in page.other:
            if re.match(r"^/dehkhoda/[^/?#]+$", href):
                candidate = BASE + href
                if candidate not in seen and candidate not in urls:
                    urls.append(candidate)
        if len(urls) + len(entries) > MAX_PAGES:
            urls = urls[: max(0, MAX_PAGES - len(entries))]
    if not entries:
        return None
    row = {"source": "dehkhoda", "name": "لغت‌نامهٔ دهخدا", "site": "vajehyab.com",
           "url": f"{BASE}/dehkhoda/{quote(word, safe='')}", "entries": entries,
           "read_at": read_at}
    _write_cache(word, row)
    return row


def sources(lang: str, word: str, glosses, *, refresh: bool = False) -> dict:
    """The meaning tabs for one word, in the order the page shows them."""
    out: list[dict] = []
    glosses = [str(g).strip() for g in (glosses or []) if str(g).strip()]
    out.append({
        "id": "wiktionary", "name": "Wiktionary",
        "url": (f"https://en.wiktionary.org/wiki/{quote(word, safe='')}"),
        "entries": [{"head": word, "text": "\n\n".join(glosses)}] if glosses else [],
        "note": "" if glosses else "No gloss is recorded for this word.",
    })
    if lang == "fa":
        deh = dehkhoda(word, refresh=refresh)
        if deh:
            out.append({"id": "dehkhoda", "name": deh["name"], "url": deh["url"],
                        "entries": deh["entries"], "note": ""})
        else:
            out.append({"id": "dehkhoda", "name": "لغت‌نامهٔ دهخدا",
                        "url": f"{BASE}/dehkhoda/{quote(word, safe='')}",
                        "entries": [],
                        "note": "vajehyab.com did not answer for this word."})
    return {"lang": lang, "word": word, "sources": out}
