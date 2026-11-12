#!/usr/bin/env python3
"""Collect the readings etymology sentences quote beside a script form.

The word page prints a reading next to every headword written in a non-Latin
script (2026-11-08).  Most of them are the entry's own ``translit``/``ipa``.
For the rest, the glossary itself often *does* record one — one entry's
etymology names an older word and reads it in the same parenthesis:

    Old Persian 𐎱𐎠𐎼𐎿 (p-a-r-s /⁠pārsa⁠/)
    Middle Persian 𐫀𐫡𐫘 (ʾrs /⁠ars⁠/, “tear”)

Those sentences are the dictionary's own reading of that spelling, so they are
harvested here into ``data/readings.json`` (``{form: {reading, translit,
source}}``) and the service prints them plainly, naming the entry they were
read in.  Only scripted forms are kept, only the first writer wins, and a
parenthesis that is a gloss or an author yields nothing.

The same table also holds what Wiktionary's *templates* state about a form: a
templated etymology names the older word together with its transcription, and
that is one record in two fields:

    {{inh|pal|peo|𐎼𐎢𐎨|ts=raučah-|gloss=day}}      (Old Persian 𐎼𐎢𐎨)

``ts=`` is a transcription and ``tr=`` a transliteration, so ``ts`` wins when a
template carries both, and the row is kept even when the headword is written in
Latin letters (``{{m|pal|hnd|tr=hind}}``).  Nothing is guessed: a template
without ``ts``/``tr`` contributes nothing, and a reading that is itself written
in a script is refused (2026-11-11: the ladder of Middle Persian ``lwc`` ran its
sound laws on the cuneiform of its Old Persian ancestor because no table held
that ancestor's reading).

A form this file misses falls back to the script's own values
(``readings.display`` → ``script.read`` / ``translit.transliterate``), which
the page prints in the colour of an automatic reading.

Usage:
    python3 tools/build_readings.py            # rewrite data/readings.json
    python3 tools/build_readings.py --check    # verify it, write nothing
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

from pie import data, readings, translit  # noqa: E402

LEXICON = data.DATA / "lexicon"
OUT = data.DATA / "readings.json"

#: A script token followed by its parenthesis, as Wiktionary prints them.
TOKEN = re.compile(r"([^\s()[\]{},;]{1,40})\s*\(([^()]{1,90})\)")
#: A Wiktionary template, and the pipe that separates its parameters.
TEMPLATE = re.compile(r"\{\{([^{}]{1,600})\}\}")
PIPE = re.compile(r"(?<!\\)\|")
#: Templates whose first parameter is the entry's language and second the
#: form's — ``{{cog|ae|𐬭𐬀𐬊𐬗𐬀𐬵|gloss=light}}``.
_ONE_LANG = {"cog", "m", "l", "desc", "descendant", "arameogram", "alt", "q",
             "doublet", "ncog", "noncog", "lb", "link"}
#: Templates that name the receiving language first and the donor second —
#: ``{{inh|pal|peo|𐎼𐎢𐎨|ts=raučah-}}``.
_TWO_LANG = {"inh", "inherited", "inh+", "der", "der+", "bor", "borrowed",
             "bor+", "con", "con+"}

def languages() -> dict[str, str]:
    path = data.DATA / "language_names.json"
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    # The file is a small document, not a bare table: the codes live under
    # "languages".  Reading the top level instead yielded a source string with
    # no language name at all ("𐌸𐌹𐌿𐌳𐌰𐍂𐌴𐌹𐌺𐍃" rather than "Gothic …"),
    # which is what the tooltip printed (2026-11-11).
    for key, value in (rows.get("languages") or rows).items():
        if isinstance(value, dict):
            out[key] = value.get("name") or key
        elif isinstance(value, str):
            out[key] = value
    return out


def needed() -> set[str]:
    """The script headwords whose own entry records no reading.

    Only these can ever reach the automatic layer, so only these are indexed:
    a form that carries its own IPA or romanisation never consults this file.
    """
    # Only the *first* entry under a word is displayed (`readings_for` reads
    # entries[0]), so only that one decides whether the word is bare.
    first: dict[str, bool] = {}
    for path in sorted(LEXICON.glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                word = entry.get("word") or ""
                if word in first or not translit.is_scripted(word):
                    continue
                first[word] = bool(entry.get("translit") or entry.get("translit_alt")
                                   or entry.get("ipa"))
    return {word for word, read in first.items() if not read}


def corpus_index() -> tuple[dict[str, set[str]], set[tuple[str, str]], set[tuple[str, str]]]:
    """Who spells what, at which stage it is named, and where it is read.

    A reading in this table only earns its place if a page can meet the form:
    it is either a headword of the language the row names, or a spelling some
    entry's ancestry row gives at that stage.  Anything else — a descendant
    mentioned in passing, a word of a *third* language inside a quotation — is
    dropped rather than filed under a language that never writes it
    (2026-11-11: Karakhanid بخسم was recorded as a Persian spelling because one
    Persian headword happens to be spelled the same way).
    """
    spelled: dict[str, set[str]] = {}
    named: set[tuple[str, str]] = set()
    stated: set[tuple[str, str]] = set()
    for path in sorted(LEXICON.glob("*.jsonl.gz")):
        lang = path.name.split(".")[0]
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                word = entry.get("word") or ""
                if word:
                    spelled.setdefault(word, set()).add(lang)
                    if entry.get("translit") or entry.get("translit_alt") or entry.get("ipa"):
                        stated.add((lang, word))
                for stage, form, _rel in entry.get("anc") or ():
                    if form:
                        named.add((stage, form))
    return spelled, named, stated


def spelled_by(lang: str, form: str, spelled: dict[str, set[str]],
               named: set[tuple[str, str]]) -> bool:
    """Whether this language writes the form, or an entry names it at its stage."""
    return (lang, form) in named or lang in spelled.get(form, set())


def scan() -> dict[str, dict]:
    names = languages()
    wanted = needed()
    found: dict[str, dict] = {}
    spelled, named, stated = corpus_index()
    for path in sorted(LEXICON.glob("*.jsonl.gz")):
        lang = path.name.split(".")[0]
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                etym = entry.get("etym") or ""
                if "(" not in etym:
                    continue
                # Only an entry that descends from the form may read it: the
                # parenthesis follows the word the sentence is *about*, and a
                # mention of a prefix or a look-alike is not that word
                # (2026-11-08).
                ancestors = {word for _lang, word, _rel in entry.get("anc") or ()}
                # Which language the quoted spelling belongs to.  The row's
                # ``lang`` is the *form's* language, not the entry's: a Persian
                # entry that quotes Middle Persian 𐭰𐭩𐭭 is a fact about
                # Middle Persian, and a display that looked it up under Persian
                # would print another word's reading (2026-11-11).
                owner = {word: stage for stage, word, _rel in entry.get("anc") or ()}
                for match in TOKEN.finditer(etym):
                    form = match.group(1).strip("*.,;:“”\"'")
                    if form in found or form not in wanted:
                        continue
                    # The sentence must be *about* this form: either the entry
                    # descends from it, or the parenthesis spells its reading
                    # outright after a slash ("p-a-r-s /⁠pārsa⁠/").  A prefix or
                    # a look-alike mentioned in passing is neither
                    # (2026-11-08).
                    inside = match.group(2)
                    if form not in ancestors and not ("/" in inside
                                                      or readings.long_enough(form)):
                        continue
                    quote = readings.parse_quote(inside, form)
                    if not quote.get("reading"):
                        continue
                    form_lang = owner.get(form, lang)
                    found[form] = {
                        "reading": quote["reading"],
                        "translit": quote.get("translit", ""),
                        "source": f"{names.get(lang, lang)} {entry.get('word', '')}".strip(),
                        "lang": form_lang,
                    }
                if len(found) == len(wanted):
                    break
    for form, row in list(found.items()):
        # A spelling whose own entry already reads it needs no second reading
        # (the page prints the entry's), and a row whose language does not
        # write the form is a quotation of somebody else's word (2026-11-11).
        if (row["lang"], form) in stated or not spelled_by(row["lang"], form,
                                                          spelled, named):
            found.pop(form)
    return dict(sorted(found.items()))


def clean_reading(raw: str) -> str:
    """One reading out of a template's ``ts=``/``tr=`` value.

    Wiktionary writes alternates, brackets and a stem hyphen around these
    (``θard-, θarad-``, ``ham(a)``, ``Hiⁿduš⁠``), and none of it belongs to the
    form the laws take: the first alternate is kept, a parenthetical aside is
    dropped, and the result must not be another script.
    """
    value = (raw or "").replace("\u2060", "").strip().strip("[]")
    value = value.split(",")[0].strip()
    value = re.sub(r"\s*\([^()]*\)", "", value).strip().strip("[]*.,;:")
    value = value.strip("-").strip()
    if not value or translit.is_scripted(value):
        return ""
    return value


def templates(names: dict[str, str]) -> dict[str, dict]:
    """The readings Wiktionary's own templates state for a form.

    A template names a language and a form, and usually how it is read; that is
    a record of the spelling in one breath, so it needs no second sentence to
    quote it.  ``ts`` (a transcription) wins over ``tr`` (a transliteration)
    when both are given, because the sound laws take the transcription.
    """
    found: dict[str, dict] = {}
    # A template is free text and may name a prefix or a word of another
    # dictionary; only a form the *glossary* has (a headword) or an entry's
    # ancestry names is something a page will ever read, so the rest is not
    # kept.  𐎼𐎢𐎨 is the case that matters: no Old Persian entry spells it,
    # and every Middle Persian *lwc* names it as its ancestor.
    spelled, named, stated = corpus_index()
    for path in sorted(LEXICON.glob("*.jsonl.gz")):
        outer = path.name.split(".")[0]
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                for text in (entry.get("ref") or "", entry.get("etym") or ""):
                    if "{{" not in text:
                        continue
                    for match in TEMPLATE.finditer(text):
                        parts = [p.strip() for p in PIPE.split(match.group(1))]
                        name = parts[0].lower()
                        if name in _TWO_LANG and len(parts) > 3:
                            lang, form = parts[2], parts[3]
                        elif name in _ONE_LANG and len(parts) > 2:
                            lang, form = parts[1], parts[2]
                        else:
                            continue
                        form = form.strip("[]*.,;:")
                        if not form or "=" in form or form in found:
                            continue
                        params: dict[str, str] = {}
                        for param in parts:
                            key, eq, value = param.partition("=")
                            if eq:
                                params.setdefault(key.strip().lower(), value)
                        reading = clean_reading(params.get("ts") or params.get("tr") or "")
                        if not reading:
                            continue
                        if form not in found:
                            found[form] = {
                                "reading": reading,
                                "translit": "",
                                "source": f"{names.get(outer, outer)} {entry.get('word', '')}".strip(),
                                "lang": lang,
                                "tier": "quoted",
                            }
    # The gates are answered only after every file has been read: a Middle
    # Persian entry may quote Sanskrit श्वेत long before sa.jsonl is reached,
    # and the judgment is about the whole corpus, not about what happened to be
    # read first (2026-11-11).
    return {form: row for form, row in found.items()
            if spelled_by(row["lang"], form, spelled, named)
            and (row["lang"], form) not in stated}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="report, write nothing")
    args = parser.parse_args()
    names = languages()
    rows = scan()
    for form, row in templates(names).items():
        rows.setdefault(form, row)
    rows = dict(sorted(rows.items()))
    text_out = json.dumps(rows, ensure_ascii=False, indent=0, sort_keys=True) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        print(f"{len(rows)} quoted readings; {OUT.name} "
              f"{'is current' if current == text_out else 'is stale'}")
        return 0 if current == text_out else 1
    OUT.write_text(text_out, encoding="utf-8")
    print(f"wrote {len(rows)} quoted readings to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
