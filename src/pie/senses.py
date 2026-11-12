"""One spelling, several words: the senses a headword carries.

Wiktionary writes a language's section for one spelling as several entries —
one per part of speech, and, when the page has more than one etymology, one per
etymology.  Two of those facts are different:

* the noun and the verb of *bank* that both come from Frankish are **one**
  word seen in two grammatical roles, and
* *bank* the financial institution and *bank* the river's edge are **two**
  words that merely happen to be spelled alike.

The project's first rule is that one lexeme has exactly one etymology pathway
(``docs/PROGRAMME.md``), so the two words must be two pages, each with its own
path, its own band and its own Wiktionary etymology section — while the two
parts of speech of one lexeme stay together, because they share the path.

This module decides that grouping once, for the word page, the glossary and the
coverage counter, so the three can never disagree about how many words a
spelling holds.  The key is the record itself: two entries are one lexeme when
the ancestry chain they state and the etymology prose around it are the same.
An entry that states no ancestry is grouped by its prose, and one that states
neither is its own word in its own part of speech.
"""
from __future__ import annotations

from typing import Iterable


def _prose(entry: dict, length: int = 90) -> str:
    """The start of the entry's etymology, whitespace-flattened.

    Two parts of speech of one word share one etymology section on Wiktionary
    and so one sentence; the sentence is what tells *rice* the noun (“kingdom”)
    from *rice* the adjective (“mighty”), which share a Proto-West Germanic
    etymon but are two words.
    """
    text = " ".join((entry.get("etym") or "").split())
    return text[:length]


def _chain(entry: dict) -> tuple:
    return tuple(tuple(row) for row in entry.get("anc") or ())


def groups(entries: Iterable[dict], gloss_limit: int = 6) -> list[dict]:
    """The senses of one headword, in the order the glossary stores them.

    Each group is ``{"sense", "key", "entries", "rep", "pos", "gloss"}``:
    ``rep`` is the entry the measurement and the page use (the first one that
    is not a reconstructed form), and ``pos`` and ``gloss`` are the union over
    the entries the group holds.

    Two entries are the same word when the etymology sentence they print is
    the same **and** the ancestry chains they state agree — where a shorter
    chain that is the beginning of a longer one is the same chain written more
    briefly (Wiktionary records Persian دیوانه the noun from Proto-Iranian only,
    and دیوانه the adjective from Proto-Iranian, Proto-Indo-Iranian and PIE).
    """
    rows = list(entries)
    chains = [_chain(e) for e in rows]
    prose = [_prose(e) for e in rows]
    out: list[dict] = []
    seen: dict[tuple, dict] = {}
    for entry, chain, text in zip(rows, chains, prose):
        # The canonic form of this entry's chain: the longest chain stored under
        # this spelling that begins with it.
        canon = chain
        for other, other_text in zip(chains, prose):
            if len(other) > len(canon) and other[:len(chain)] == chain and other_text == text:
                canon = other
        if canon:
            k = ("anc", canon, text)
        elif text:
            k = ("etym", text)
        else:
            # Nothing is recorded about where it comes from: two such entries
            # are only told apart by the grammar they belong to.
            k = ("pos", entry.get("pos") or "")
        row = seen.get(k)
        if row is None:
            row = {"sense": len(out) + 1, "key": k, "entries": [],
                   "pos": [], "gloss": []}
            seen[k] = row
            out.append(row)
        row["entries"].append(entry)
        pos = entry.get("pos") or ""
        if pos and pos not in row["pos"]:
            row["pos"].append(pos)
        for gloss in entry.get("gloss") or ():
            if gloss and gloss not in row["gloss"] and len(row["gloss"]) < gloss_limit:
                row["gloss"].append(gloss)
    for row in out:
        row["rep"] = next((e for e in row["entries"] if not e.get("recon")),
                          row["entries"][0])
    return out


def by_word(index: dict[tuple[str, str], list[dict]]) -> dict[tuple[str, str], list[dict]]:
    """``(lang, word) -> senses`` for a whole index, grouped once."""
    return {k: groups(v) for k, v in index.items()}


def for_lexicon(rows: Iterable[dict]) -> list[dict]:
    """Every sense in one language's lexicon, grouped by spelling.

    A whole lexicon is grouped one headword at a time: `groups` compares an
    entry's chain with the chains stored under *its* spelling, so handing it a
    language's 130,000 entries would compare each of them with all the others
    (2026-11-09: that made the full run run for hours).
    """
    by_word: dict[str, list[dict]] = {}
    for entry in rows:
        by_word.setdefault(entry.get("word") or "", []).append(entry)
    out: list[dict] = []
    for entries in by_word.values():
        out.extend(groups(entries))
    return out
