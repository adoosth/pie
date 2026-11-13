"""One romanisation alphabet per stage, and the folds that reach it.

A stage's glossary is written by several dictionaries, and they do not agree
on how to spell the same sound: MPCD romanises Middle Persian with ``ǰ`` and
``č``, MacKenzie's dictionary was typed in an ASCII fold (``j``, ``S``), and
Wiktionary heads a word by its Pahlavi *transliteration* (``hwʾb``) rather
than by its reading (``xwāb``).  Two spellings of one word are two pages, so
the corpus is folded into the standard the stage's own dictionary uses
(``data/notation/<lang>.yaml``).  A fold is notation: it renames nothing.

Only ``folds`` is applied at read time (the loader and every lookup), so a
headword edited by hand or a new import cannot bring a variant back; the
stored corpus is folded too (``tools/unify_notation.py``).
"""
from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
NOTATION_DIR = ROOT / "data" / "notation"

#: Punctuation a headword may carry for reasons that are not spelling: a
#: bound morpheme's hyphen, a compound's seam, a quoted alternative.
PUNCTUATION = set("-‑–—()[]{}.,/;:*?!+& \u200c\u200d")


def _load(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except OSError:
        return {}


@lru_cache(maxsize=None)
def _table_cached(lang: str, stamp: tuple) -> dict:
    return _load(NOTATION_DIR / f"{lang}.yaml")


def table(lang: str) -> dict:
    """The notation table of one stage, re-read when the file changes."""
    path = NOTATION_DIR / f"{lang}.yaml"
    try:
        stat = path.stat()
    except OSError:
        return {}
    return _table_cached(lang, (stat.st_size, stat.st_mtime_ns))


def languages() -> list[str]:
    """Every stage that states a standard alphabet."""
    try:
        return sorted(path.stem for path in NOTATION_DIR.glob("*.yaml"))
    except OSError:
        return []


def folds(lang: str) -> dict[str, str]:
    return {str(k): str(v) for k, v in (table(lang).get("folds") or {}).items()}


def letters(lang: str) -> set[str]:
    text = str(table(lang).get("letters") or "")
    return set(text.replace(" ", ""))


def reading_fields(lang: str, source: str) -> list[str]:
    table_ = table(lang).get("reading_fields") or {}
    return [str(field) for field in (table_.get(source) or [])]


def romanise_sources(lang: str) -> set[str]:
    return {str(s) for s in (table(lang).get("romanise_sources") or [])}


def bundled_sources(lang: str) -> set[str]:
    """Sources whose one row may hold several homographs."""
    return {str(source) for source in (table(lang).get("bundled_sources") or [])}


def quoted_letters(lang: str) -> set[str]:
    text = str(table(lang).get("quoted_letters") or "")
    return set(text.replace(" ", ""))


def quoted_scripts(lang: str) -> list[str]:
    return [str(s) for s in (table(lang).get("quoted_scripts") or [])]


def canonical(lang: str, word: str) -> str:
    """The word spelled in the stage's standard notation.

    Composition is normalised first (a combining caron and a precomposed ǰ
    are one letter), then every fold is applied.  A stage without a table is
    left exactly as it is.
    """
    text = unicodedata.normalize("NFC", str(word or ""))
    marks = folds(lang)
    if not marks or not text:
        return text
    return "".join(marks.get(ch, ch) for ch in text)


def is_quoted(lang: str, word: str) -> bool:
    """Whether a headword carries a sign of a quotation, not of the romanisation.

    True for the Avestan and Semitic letters the table names as quotation
    (``ą ə β δ θ ϑ ŋ``, ``ʾ ʿ ḥ ẕ``) and for the characters of a script it
    lists: such a headword is quoted from another language or written in
    Pahlavi, and the Middle Persian alphabet is not the thing to judge it by.
    """
    text = str(word or "")
    allowed = quoted_letters(lang)
    blocks = quoted_scripts(lang)
    for ch in text:
        if ch in allowed:
            return True
        if any(_in_block(ch, block) for block in blocks):
            return True
    return False


def _in_block(ch: str, block: str) -> bool:
    try:
        return block.casefold() in unicodedata.name(ch, "").casefold()
    except ValueError:  # pragma: no cover - unicodedata always answers
        return False


def is_quoted_script(lang: str, ch: str) -> bool:
    """Whether one character belongs to a script the stage lists."""
    return any(_in_block(ch, block) for block in quoted_scripts(lang))


def outside(lang: str, word: str) -> str:
    """The characters of a headword that the stage's notation does not account for.

    Empty when the word is spelled in the standard alphabet (a foldable
    variant does not count: it *is* a standard letter written another way, and
    :func:`variants` reports it separately), or when the word is a quotation.
    """
    text = str(word or "")
    if is_quoted(lang, text):
        return ""
    marks = folds(lang)
    capitals = bool(table(lang).get("quoted_capitals"))
    bad = [ch for ch in text
           if ch not in letters(lang) and ch not in marks and ch not in PUNCTUATION
           and not ch.isdigit() and not (capitals and ch.isupper())]
    return "".join(sorted(set(bad)))


def offenders(lang: str, words) -> list[tuple[str, str]]:
    """Headwords that neither the standard alphabet nor a quotation explains."""
    return [(str(word), maths) for word in words
            if (maths := outside(lang, str(word or "")))]


def variants(lang: str, words) -> list[tuple[str, str]]:
    """Headwords that still spell a standard letter another way."""
    marks = folds(lang)
    bad = []
    for word in words:
        text = str(word or "")
        folded = canonical(lang, text)
        if folded != text:
            bad.append((text, folded))
    return bad
