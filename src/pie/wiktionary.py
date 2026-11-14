"""What the Persian Wiktionary says about a word, and where its page is.

The glossaries are machine-readable Wiktionary (kaikki's dumps), but the fa
dump is thin: most Persian words reach this model through Dehkhoda, which gives
a gloss, a grammar label and sometimes an ancestry, and never a page of its own
on the English Wiktionary.  The Persian Wiktionary (fa.wiktionary.org) does have
those pages, and this module is the record of the ones that have been read.

A word is either *found* — the page exists, and the entry keeps its address, its
revision and the etymology the page prints — or *missing*, and the ledger says
so, so a later pass never asks the site the same question twice.  Nothing here
is a claim about the word: the etymology is stored as a quotation with the page
it came from, and it is shown beside this model's own reading rather than mixed
into it (2026-11-11: "if the wiktionary provides etymology, store that
appropriately").
"""
from __future__ import annotations

import gzip
import json
import re
import zlib
from functools import lru_cache

from . import data

LEDGER = data.DATA / "sources" / "fa_wiktionary.jsonl.gz"
#: The English Wiktionary's pages for glossary headwords, one file per language,
#: written by ``tools/en_wiktionary_index.py``.  Only pages that answered are
#: stored: a word absent from the file has no *recorded* page, and the word page
#: shows no icon for it (2026-11-12).
EN_DIR = data.DATA / "sources" / "en_wiktionary"

#: The headings a Persian Wiktionary page uses for the history of the word.
ETYM_HEADINGS = ("ریشه لغت", "ریشهشناسی", "ریشه شناسی", "ریشه‌شناسی",
                 "ریشه لغت‌شناسی", "واژه‌شناسی", "واژه شناسی", "اشتقاق",
                 "بن‌واژه", "بن واژه", "تاریخچه")

HEADING = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$", re.M)

#: Headings that end an etymology even when they are nested under it: a page
#: often keeps its references and categories inside the same subtree.
STOP = ("منابع", "منبع", "منبع معتبر", "پانویس", "رده", "رده‌ها",
        "جستارهای وابسته", "جستار وابسته", "یادداشت", "یادداشت‌ها",
        "پیوند به بیرون", "واژه‌های وابسته")


@lru_cache(maxsize=1)
def ledger() -> dict[tuple[str, str], dict]:
    """Every word asked about so far: ``(lang, word)`` → the row that answered."""
    if not LEDGER.exists():
        return {}
    out: dict[tuple[str, str], dict] = {}
    with gzip.open(LEDGER, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[(row["lang"], row["word"])] = row
    return out


def note(lang: str, word: str) -> dict | None:
    """The page for this word, or ``None`` when it was never asked about.

    A *missing* row returns a dict too — ``found`` is false and there is no
    address — because "checked, no page" is itself an answer the page should be
    able to stay quiet about without asking again.
    """
    row = ledger().get((lang, word))
    if not row:
        return None
    return {
        "found": row.get("status") == "found",
        "url": row.get("url") or "",
        "title": row.get("title") or word,
        "etym": row.get("etym") or "",
        "revised": row.get("revised") or "",
        "checked": row.get("checked") or "",
        "site": row.get("site") or "fa.wiktionary.org",
    }


@lru_cache(maxsize=16)
def en_pages(lang: str) -> dict[str, str]:
    """The recorded English-Wiktionary page of each headword of one language."""
    path = EN_DIR / f"{lang}.jsonl.gz"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        try:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                # A title is shared by every language on the site: en.wiktionary's
                # نقوع is an Arabic entry with no Persian section, and the W it
                # drew claimed a record of the Persian word (critic batch 01,
                # 2026-11-13).  Rows this repo has checked say which they are
                # (`tools/en_wiktionary_sections.py`); an unchecked row keeps
                # the old behaviour until the pass reaches it.
                if row.get("section") is False:
                    continue
                if row.get("status") == "found" and row.get("url"):
                    out[row["word"]] = row["url"]
        except (EOFError, OSError, zlib.error):
            # A pass still writing the file leaves its last member open; what
            # it has finished is already an answer (2026-11-12).
            pass
    return out


def en_page(lang: str, word: str) -> dict | None:
    """This word's English Wiktionary page, when one was recorded."""
    url = en_pages(lang).get(word)
    if not url:
        return None
    return {"url": url, "site": "en.wiktionary.org", "title": "Wiktionary"}


def tally() -> dict[str, int]:
    """How far the pass has gone, per language: found, missing and total."""
    out: dict[str, int] = {}
    for (_lang, _word), row in ledger().items():
        kind = "found" if row.get("status") == "found" else "missing"
        out[kind] = out.get(kind, 0) + 1
    out["checked"] = sum(1 for _ in ledger())
    out["with_etymology"] = sum(1 for row in ledger().values() if row.get("etym"))
    return out


# --- reading the page ------------------------------------------------------

def section(text: str, name: str, level: int | None = None) -> str:
    """The body under a heading, up to the next heading of the same rank.

    A nested heading that only carries the page's furniture (``منابع``,
    ``رده``) ends the body too: the references of a page are not its
    etymology, even though the page's own markup nests them inside it.
    """
    for m in HEADING.finditer(text):
        if m.group(2).strip() != name:
            continue
        rank = len(m.group(1))
        if level is not None and rank != level:
            continue
        rest = text[m.end():]
        for nxt in HEADING.finditer(rest):
            if len(nxt.group(1)) <= rank or nxt.group(2).strip() in STOP:
                return rest[:nxt.start()]
        return rest
    return ""


def language_section(text: str, language: str) -> tuple[str, bool]:
    """The page's section for one language, and whether it had one at all."""
    body = section(text, language)
    if body:
        return body, True
    # A page written in Persian about a Persian word often skips the language
    # heading and opens with the word's history. That is the Persian section by
    # convention, but say so, because the tool only takes etymology from a
    # page that names the language or carries an etymology heading.
    return text, False


def etymology(text: str) -> tuple[str, str]:
    """``(heading, plain text)`` of the page's etymology, or ``("", "")``."""
    body, named = language_section(text, "فارسی")
    for heading in ETYM_HEADINGS:
        found = section(body, heading)
        if found.strip():
            return heading, plain(found)
    return "", ""


_COMMENT = re.compile(r"<!--.*?-->", re.S)
_REF = re.compile(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", re.S)
_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_FILE = re.compile(r"\[\[(?:پرونده|تصویر|File|Image|رده|Category):[^\]]*\]\]", re.S | re.I)
_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_EXT = re.compile(r"\[(?:https?:)?//[^\s\]]+\s*([^\]]*)\]")
_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
_QUOTES = re.compile(r"'{2,5}")


def plain(wikitext: str) -> str:
    """Wikitext as a sentence a reader can read, losing no claim.

    Links keep their visible half, templates go (they are formatting, and the
    ones that carry a fact are not in the etymology lines this reads), and the
    markup that survives — bold, italics, bullets — is dropped.  What is left
    is joined into one paragraph so it can be quoted as a sentence.
    """
    text = _COMMENT.sub("", wikitext)
    text = _REF.sub("", text)
    text = _FILE.sub("", text)
    for _ in range(4):
        new = _TEMPLATE.sub("", text)
        if new == text:
            break
        text = new
    text = _LINK.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)
    text = _EXT.sub(lambda m: (m.group(1) or "").strip(), text)
    text = _TAG.sub("", text)
    text = _QUOTES.sub("", text)
    text = text.replace("&nbsp;", " ")
    lines = []
    for line in text.splitlines():
        line = line.strip().lstrip("*#:;").strip()
        if line:
            lines.append(line)
    out = " ".join(lines)
    return re.sub(r"\s+", " ", out).strip()
