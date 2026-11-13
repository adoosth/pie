"""Read models used by the web API: word pages, search, derivations."""

from __future__ import annotations

import json
import gzip
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from functools import lru_cache
from typing import Iterable
from urllib.parse import quote

from . import attestation, data, pathways, senses
from . import review as review_queue
from . import wiktionary as wiktionary_pages
from .phonology import detokenize, letters, tokenize
from . import readings as readings_index
from . import citation, script, spelling, translit
from .rules import TIERS, Derivation, Level, derive, derive_detailed, rule_key


@lru_cache(maxsize=1)
def language_names() -> dict[str, dict]:
    """Wiktionary's names for language codes that have no registry row.

    Most cognate sets are recorded in codes we have no glossary for (``xcl``,
    ``yms``, ``hyx-pro`` …). The registry stays the source of truth; this file
    fills the names in so the interface never shows a bare code.
    """
    return data.language_names()


def _lang(lang: str) -> dict:
    """A language's registry row, or the best name the data can give it.

    The registry wins; then the names harvested from Wiktionary's descendant
    trees (which carry a branch); then the display names for borrowers outside
    that tree; then a register of a modelled stage read at its stage; then the
    register of non-Indo-European donors; then Wiktionary's full language
    table.  Each of those is a different fact — a branch, a stage's kind and
    era, a donor family — so they stay separate here even though
    `data.language_name` answers the one question a page usually asks
    (2026-11-12).
    """
    row = data.languages().get(lang)
    if row:
        return row
    named = data.language_names().get(lang, {})
    if named.get("name"):
        return {
            "id": lang,
            "name": named["name"],
            "short": named["name"],
            "branch": named.get("branch") or named.get("family", ""),
        }
    extra = data.language_name_extras().get(lang, {})
    if extra.get("name"):
        return {
            "id": lang,
            "name": extra["name"],
            "short": extra["name"],
            "branch": extra.get("branch") or extra.get("family", ""),
        }
    variety = data.varieties().get(lang) or {}
    if variety.get("name") and variety.get("of") and variety["of"] != lang:
        base = _lang(variety["of"])
        return {"id": lang, "name": variety["name"], "short": variety["name"],
                "branch": base.get("branch", ""), "kind": base.get("kind", ""),
                "era": base.get("era")}
    donor = data.non_ie_sources().get(lang) or {}
    if donor.get("name"):
        return {"id": lang, "name": donor["name"], "short": donor["name"],
                "branch": donor.get("family", "Contact / non-IE")}
    full = data.wiktionary_language_names().get(lang)
    if full:
        return {"id": lang, "name": full, "short": full, "branch": ""}
    name = data.language_name(lang)
    return {"id": lang, "name": name or lang, "short": name or lang, "branch": ""}


@lru_cache(maxsize=1)
def cognate_index() -> dict[str, dict]:
    return {rec["id"]: rec for rec in data.cognate_sets()}


@lru_cache(maxsize=None)
def lang_index(lang: str) -> dict[str, list[dict]]:
    """One stage's glossary by headword, loaded and grouped on its own.

    Every view that asks about one language — a word page, a glossary page, a
    branch — wants that language's rows and nothing else.  Loading the family
    to answer a question about one stage was the cold-start cost of the whole
    site; this is the unit of loading now (2026-11-12).
    """
    idx: dict[str, list[dict]] = {}
    for entry in data.lexicon(lang):
        idx.setdefault(entry["word"], []).append(entry)
    return idx


class _WordIndex(Mapping):
    """``(lang, word) -> entries``, loading one glossary at a time.

    A word page reads four or five languages.  Building all 37 glossaries
    (591k entries, about 4.5 s of gzip and JSON) before the first byte was the
    cold-start cost that made a page take ten seconds after every restart; the
    index now loads a language the first time it is asked for one of its words
    and keeps it.  ``.items()`` still walks the whole family, which is what the
    glossary, the search, the cognate sets and the coverage counter ask for —
    those pages need every language anyway (2026-11-12).
    """

    def __init__(self) -> None:
        self._order: list[str] = [lang for lang, _ in data.available_lexicons()]

    def _lang(self, lang: str) -> dict[str, list[dict]]:
        return lang_index(lang)

    def __getitem__(self, key: tuple[str, str]) -> list[dict]:
        try:
            lang, word = key
        except (TypeError, ValueError):
            raise KeyError(key) from None
        return self._lang(lang)[word]

    def __iter__(self):
        for lang in self._order:
            for word in self._lang(lang):
                yield (lang, word)

    def __len__(self) -> int:
        return sum(len(self._lang(lang)) for lang in self._order)


@lru_cache(maxsize=1)
def word_index() -> Mapping:
    return _WordIndex()


@lru_cache(maxsize=8192)
def word_entries(lang: str, word: str) -> list[dict]:
    """The rows one spelling has in one stage's glossary, case aside.

    A link may write a headword in another case (Old Persian's own
    transliterations, Latin ``Nox`` for ``nox``), so a miss is retried without
    case — inside that language, never across the family: the old fallback
    walked all 591k rows of every glossary to find a word in one of them
    (2026-11-12).
    """
    rows = lang_index(lang).get(word)
    if rows:
        return rows
    folded = word.casefold()
    for spelling, candidates in lang_index(lang).items():
        if spelling.casefold() == folded:
            return candidates
    return []


def prewarm() -> None:
    """Load what a word page is going to need, before it is needed.

    Called from a thread as the server starts: the registry and its laws, the
    published bands, every glossary, and the cognate map.  Each of these is a
    cache entry the first request would build anyway, and none of them is
    stale-able — a data file that changes invalidates its own disk cache — so
    warming them can only ever save the reader time (2026-11-12).
    """
    data.languages()
    data.rulesets()
    band_index()
    for lang in [lang for lang, _ in data.available_lexicons()]:
        lang_index(lang)
    cog_words()
    # Only a reconstructed stage's etymologies are parsed for constructions,
    # and the scan of one is a whole glossary: do the two that have any.
    for lang in ("ine-pro", "iir-pro"):
        _construction_scan(lang)
    # The lemma index is one pass over a glossary, and the six largest are the
    # ones a page actually reaches for (English, Persian, German, Italian,
    # Greek, Latin).  The rest build on demand, as before.
    for lang, size in sorted(data.available_lexicons(), key=lambda row: -row[1])[:6]:
        _lemma_index(lang)


@lru_cache(maxsize=4096)
def _senses_for(key: tuple[str, str]) -> list[dict]:
    return senses.groups(word_index().get(key) or [])


def _group_of(groups: list[dict], entry: dict) -> dict | None:
    """The group one glossary row belongs to, matched by what the row says.

    ``senses.groups`` is cached per headword, and a glossary read again — a
    file edited, or the parse cache evicted — hands out the same rows as new
    objects.  The search and the rung looked their row up with ``is``, so after
    a re-read the row matched no group: *aiganaz lost "own" and read "past
    participle of *aiganą", and two homographs collapsed into one row
    (admin, 2026-11-12).  A row is identified the way the grouper identifies
    it: part of speech, meanings and etymology.  Two rows that agree on all
    three are the same word to `senses.groups` too, so this is as
    discriminating as the grouping itself.
    """
    for group in groups or []:
        for row in group.get("entries") or []:
            if row is entry:
                return group
            if (str(row.get("pos") or "") == str(entry.get("pos") or "")
                    and list(row.get("gloss") or []) == list(entry.get("gloss") or [])
                    and str(row.get("etym") or "") == str(entry.get("etym") or "")):
                return group
    return None


class _SenseIndex(Mapping):
    """``(lang, word) -> senses``, grouped when a view asks for that word.

    `word_index` keeps the raw entries Wiktionary stores under one spelling —
    one per part of speech, which is not the same thing as one per word.  This
    groups them into lexemes (see `pie.senses`), so the glossary prints a row
    per meaning, the word page shows a selector, and the coverage counter
    measures a word rather than each of its parts of speech (2026-11-09).

    Grouping all 591k entries up front cost about 2.5 s on the first request;
    `groups` looks only at the entries stored under one spelling, so the
    grouping is per headword now and a page pays for one spelling, not for the
    family.  Walking the whole index (the glossary, the coverage counter)
    groups every word exactly as before, one at a time.
    """

    def __getitem__(self, key: tuple[str, str]) -> list[dict]:
        rows = _senses_for(key)
        if not rows:
            raise KeyError(key)
        return rows

    def __iter__(self):
        return iter(word_index())

    def __len__(self) -> int:
        return len(word_index())


@lru_cache(maxsize=1)
def sense_index() -> Mapping:
    return _SenseIndex()


def senses_of(lang: str, word: str) -> list[dict]:
    """The senses one headword carries, or an empty list when it is not stored."""
    return _senses_for((lang, word))


@lru_cache(maxsize=1)
def cog_words() -> dict[str, list[tuple[str, str]]]:
    """Which glossary entries belong to each cognate set.

    The cognate sets come from Wiktionary's descendant trees, which are rich in
    small and reconstructed languages but frequently miss the modern ones we
    have glossaries for. Persian پدر, English *father* and German *Vater* are in
    the dataset through their own ancestry chains, so they are merged into the
    set at read time instead of being rebuilt into the generated file.
    """
    def build() -> dict[str, list[tuple[str, str]]]:
        out: dict[str, list[tuple[str, str]]] = {}
        for (lang, word), entries in word_index().items():
            cog = entries[0].get("cog")
            if cog:
                out.setdefault(cog, []).append((lang, word))
        return out

    # Walking every glossary of the family is the price of the map, and the
    # map only changes when a glossary does: it is written beside them once
    # and read back on the next start (2026-11-12).
    return data.cached("cog-words", 1,
                       [*data.lexicon_paths(), data.COGNATE_DIR], build)


@lru_cache(maxsize=512)
def _set_stage_source(set_id: str, stage: str, form: str) -> str | None:
    """The Proto-Indo-European-stage form a cognate set puts above ``form``.

    English *book* starts its ladder at the root *bʰeh₂g-, but Wiktionary's
    descendant tree records a derived noun at the PIE stage on the way to
    Proto-Germanic *bōks (``*bʰóh₂g-s ~ *bʰéh₂g-s``, "allotment", tagged
    uncertain). Reporting it explains why the top rung is a root instead of a
    word, without starting the laws from an alternation we would have to pick
    between — that choice would be this repo's reconstruction, not a record.
    """
    rec = cognate_index().get(set_id)
    if not rec:
        return None
    key = _comparison_key(form)
    for candidate in rec["forms"]:
        if candidate["l"] != stage or _comparison_key(candidate["w"]) != key:
            continue
        for step in candidate.get("p") or ():
            lang, _, word = step.partition(":")
            if lang == "ine-pro" and normalise_etymon(word) != normalise_etymon(form):
                return word
    return None


def _lang_order(lang: str) -> tuple[int, str]:
    """Attested languages first, then reconstructions, alphabetically."""
    row = _lang(lang)
    return (1 if row.get("kind") == "proto" or lang.endswith("-pro") else 0, row.get("name", lang))


def kind_of(lang: str) -> str:
    """``proto`` for reconstructed stages, ``attested`` for everything else.

    The registry is authoritative; codes that only exist in the cognate sets
    (``sqj-pro``, ``grk-pro``) still count as reconstructions by their suffix,
    so a Proto-Albanian form is never presented as if it were written in a text.
    """
    kind = (_lang(lang).get("kind") or "").strip()
    if kind in {"proto", "attested"}:
        return kind
    return "proto" if lang.endswith("-pro") else "attested"


SCRIPT_LATIN = "latin"


def needs_reading(lang: str) -> bool:
    """True when words in this language are not written in the Latin alphabet.

    Those forms are unreadable without a pronunciation, so every place that
    shows one also shows its IPA (or the dictionary's romanisation when no IPA
    is recorded) — Old Persian cuneiform, Greek, Persian, Gothic, Avestan …
    Proto-forms are already written in a phonological transcription.
    """
    script = (_lang(lang).get("script") or "").strip().lower()
    if not script or SCRIPT_LATIN in script:
        return False
    return script != "reconstructed"


def show_reading(lang: str, word: str) -> bool:
    """True when *this* form needs a pronunciation next to it.

    Old Persian cuneiform, Greek, Persian, Gothic … all do. A language whose
    script is non-Latin but whose glossary writes the lemma in a *phonological*
    transliteration (Tocharian B ``pācer``, Proto-Slavic ``-akъ``) does not:
    the form is already read, so a second spelling would only add noise.

    A lemma spelled in the language's own *script transliteration* is a third
    case, and it does need its reading: Book Pahlavi ``lwc`` is the signs
    l-w-c, not a romanisation, and the word is read ``rōz``.  ``script.writes``
    answers whether these letters are that script's letters (data/script/
    <lang>.yaml), so the page prints ``lwc · rōz`` without mistaking a true
    romanisation for a spelling (2026-11-11).
    """
    if not needs_reading(lang):
        return False
    return translit.is_scripted(word) or script.writes(lang, word)


def _year(year: int) -> str:
    return f"{abs(int(year))} BCE" if year < 0 else f"{int(year)} CE"


PRESENT_YEAR = 2026
"""Stand-in for the open end of a living language's era (``[1500, null]``)."""


def era_label(era) -> str:
    """A registry era pair as prose: ``c. 4500–2500 BCE``.

    A living language is recorded as ``[1500, null]``: its era runs to the
    present, so the label says so instead of inventing an end date.
    """
    if not era or len(era) != 2 or era[0] is None:
        return ""
    lo, hi = int(era[0]), era[1]
    if hi is None:
        return f"c. {_year(lo)} – present" if lo < 0 else f"since c. {lo}"
    hi = int(hi)
    if lo < 0 and hi <= 0:
        return f"c. {abs(lo)}–{abs(hi)} BCE"
    if lo >= 0:
        return f"c. {lo}–{hi}"
    return f"c. {_year(lo)} – {_year(hi)}"


def era_midpoint(era) -> float | None:
    if not era or len(era) != 2 or era[0] is None:
        return None
    hi = PRESENT_YEAR if era[1] is None else era[1]
    return (float(era[0]) + float(hi)) / 2


def _is_syllabic(text: str) -> bool:
    """``ku-u-ru-u-š`` / ``at-ta-aš``: sign-by-sign, not a pronunciation."""
    parts = text.split("-")
    return len(parts) > 1 and all(0 < len(p) <= 3 for p in parts)


def readings_for(entry: dict) -> dict:
    """The pronunciation the dictionaries record for one glossary entry.

    Wiktionary's IPA wins. Failing that, the best romanisation is used, with
    syllabic transcriptions (Old Persian ``ku-u-ru-u-š``, Hittite ``at-ta-aš``)
    passed over in favour of the reading recorded next to them (``Kuruš``).
    Nothing is invented: a language with no recorded reading gets none.
    """
    ipa = (entry.get("ipa") or "").strip().strip("/[]").strip()
    # ``phon`` is the reading a dictionary states for the word itself (Middle
    # Persian pus, where ``translit`` holds the spelling or nothing at all);
    # it is the same field the laws start from, so the page and the ladder
    # cannot print two different readings of one entry (2026-11-12).
    candidates = ([entry.get("phon")] if (entry.get("phon") or "").strip()
                  else []) + [entry.get("translit")] + list(entry.get("translit_alt") or [])
    reading = next((c for c in candidates if c and not _is_syllabic(c)), "")
    if not reading:
        reading = next((c for c in candidates if c), "")
    return {"ipa": ipa, "reading": reading}


def _notation_entries(lang: str, word: str) -> list[dict]:
    """The glossary rows for a spelling, reading a reconstructed hyphen as notation.

    A record may write a reconstructed word with its morpheme boundaries
    (``*tr̥s-nó-s``) while the glossary heads the word solid (``*tr̥snós``).  A
    hyphen there is the record's notation, not a sound, and a lookup that
    compares spellings literally reported "no entry for this word" beside a link
    that opened the entry it had (admin, 2026-11-12, Persian تشنه).  Every
    reader of a form — its meaning, its evidence, its ✓ — goes through here.
    """
    entries = word_index().get((lang, word)) or []
    if entries:
        return entries
    record = _lemma_entry(lang, word)
    return [record] if record else []


def pronunciation(lang: str, word: str, fallback: str = "") -> dict:
    """IPA + romanisation for a form, and whether a glossary records it."""
    entries = _notation_entries(lang, word)
    if not entries:
        return {"ipa": "", "reading": fallback, "documented": False}
    out = readings_for(entries[0])
    out["reading"] = out["reading"] or fallback
    out["documented"] = True
    return out


OP_CUNEIFORM = re.compile(r"[\U000103A0-\U000103DF]")


def _latin_letters(word: str) -> bool:
    """Whether every letter of *word* is a Latin one (marks and punctuation aside)."""
    seen = False
    for char in word or "":
        if not char.isalpha():
            continue
        seen = True
        try:
            if not unicodedata.name(char).startswith("LATIN"):
                return False
        except ValueError:  # an unassigned or private character
            return False
    return seen


def _in_native_script(lang: str, word: str) -> bool:
    """Whether a record is written in the language's own script.

    A word is *attested* only when the headword is a writing, not a reading of
    one: Old Persian 𐎭𐎠𐎼𐎹𐎺𐎢𐏁 is attested, while `madu` is a
    transliteration quoted from a grammar and is recorded (2026-11-08).  The
    same is true of every other stage with a script of its own, and this used to
    be checked for Old Persian alone: 617 Middle Persian and 231 Tocharian B
    transliterations were printed as *attested* beside a definition that says
    "in the language's own script" (2026-11-12, critic P0-1).

    The stage's spelling table knows which of its characters are signs and
    which are the Latin transliteration of a sign (``kind: translit``).  A word
    with at least one sign is a writing.  A stage whose script has no table
    falls back to the letters themselves: an all-Latin headword of a stage
    written in another script is a transliteration.
    """
    meta = _lang(lang)
    if str(meta.get("kind") or "") == "proto":
        return False
    name = (meta.get("script") or "").strip().lower()
    if not name or "latin" in name or "reconstructed" in name:
        return True
    table = script.table(lang)
    if table:
        if any((table.get(c) or {}).get("kind") not in (None, "translit", "roman")
               for c in word or ""):
            return True
        if any((row or {}).get("kind") not in (None, "translit", "roman")
               for row in table.values()):
            return False
    return not _latin_letters(word)


def is_reconstructed(lang: str, word: str) -> bool:
    """Whether the glossary records this word only as a reconstruction.

    Wiktionary keeps reconstructed words in a separate ``Reconstruction:``
    namespace and marks them with an asterisk; the lexicon build now carries
    that flag. Without it 237 Old Persian entries titled in Latin letters — and
    Latin's own 684 reconstructed words — read as if a text spelled them
    (2026-11-08: an attested word must be one a text writes).
    """
    rows = _notation_entries(lang, word)
    # Homographs are separate entries: Old English *ne* is an attested adverb
    # and conjunction beside a reconstructed noun **nē*. The word is gold only
    # when every entry under it is a reconstruction.
    return bool(rows) and all(row.get("recon") for row in rows)


def _entry_evidence(lang: str, entry: dict) -> str:
    """Evidence for one glossary entry, using its own reconstruction flag."""
    if entry.get("recon"):
        return "literary"
    return evidence_for(entry.get("word") or "", lang)


def evidence_for(word: str, lang: str) -> str:
    """``attested`` (green) or ``literary`` (gold) for a recorded form.

    Green is a claim that a text or a dictionary writes this exact word, so it
    needs a written headword. A reconstructed stage, a form written with * and
    an Old Persian record preserved only as a transliteration are all gold:
    recorded in the literature, but not a word a text spells.
    """
    if kind_of(lang) == "proto" or word.startswith("*"):
        return "literary"
    if is_reconstructed(lang, word):
        return "literary"
    if not _in_native_script(lang, word):
        return "literary"
    return "attested"


def _with_reading(payload: dict, lang: str, word: str) -> dict:
    """Attach the reading line a form is printed with.

    Three sources, in order and never mixed: the dictionary's own IPA or
    romanisation, a reading the glossary quotes for the same script form, and
    the script's own values.  Only the last is automatic, and the page says so
    in its colour (2026-11-08).
    """
    line = readings_index.display(lang, word, payload.get("ipa", ""),
                                  payload.get("reading", ""))
    if line["reading"] and (line["reading"] == word
                            or (line["auto"] and not translit.is_scripted(word))):
        # A reading that repeats the word says nothing, and an automatic one
        # beside a transliteration is the same letters again (lwc → l-w-c).
        line = {**line, "reading": "", "auto": False, "how": "", "note": ""}
    payload.update({
        "ipa": line["ipa"],
        "reading": line["reading"],
        "reading_auto": line["auto"],
        "reading_how": line["how"],
        "reading_note": line["note"],
    })
    # ``show_reading`` asks for a reading; this is the one place that knows
    # whether there is one to print, so a form with nothing recorded is not
    # promised a reading it cannot show (2026-11-11: Book Pahlavi yʿm is a
    # transliteration with no reading in the record).
    payload["show_reading"] = bool(payload.get("show_reading")
                                   and (line["ipa"] or line["reading"]))
    if line["translit"] and not payload.get("translit"):
        payload["translit"] = line["translit"]
    return payload


def _form_meta(lang: str, word: str, reading: str = "") -> dict:
    """Everything the interface needs to display one recorded form."""
    row = _lang(lang)
    pron = pronunciation(lang, word, reading)
    return _with_reading({
        "kind": kind_of(lang),
        "script": row.get("script", ""),
        "in_script": _in_native_script(lang, word),
        "recon": is_reconstructed(lang, word),
        "show_reading": show_reading(lang, word),
        "evidence": evidence_for(word, lang),
        "ipa": pron["ipa"],
        "reading": pron["reading"],
        "known": pron["documented"],
    }, lang, word)


def _attestation_reason(entry: dict, lang: str, status: str) -> str:
    """One sentence on why the page prints this status (2026-11-11)."""
    if status == "proposed":
        return ("This model proposes the form itself: nothing in the literature "
                "records it, so it is printed with an asterisk.")
    if status == "transliterated":
        return (f"A text writes this word; the glossary keeps the reading of its "
                f"signs and no headword in {_lang(lang).get('name', lang)}'s own "
                f"script is known, so it is not called attested.")
    if status == "recorded":
        return ("No text spells this word: it is a reconstruction the literature "
                "records as the probable form, and it is printed with an asterisk.")
    return ("A text or a dictionary writes this exact word in the language's own "
            "script — the headword is that writing.")


def attestation_of(entry: dict, lang: str) -> dict:
    """The attested / recorded / proposed block for one entry's word page."""
    status = attestation.classify(
        entry,
        proto=kind_of(lang) == "proto",
        in_script=_in_native_script(lang, entry.get("word") or ""),
    )
    return attestation.payload(entry.get("word") or "", status,
                               reason=_attestation_reason(entry, lang, status))


def _is_wiktionary_url(url: str) -> bool:
    """Whether an address is a Wiktionary page and not some other dictionary."""
    if not url:
        return False
    host = re.sub(r"^https?://", "", url.strip().lower()).split("/")[0]
    return host == "wiktionary.org" or host.endswith(".wiktionary.org")


def _wiktionary_title(entry: dict) -> str:
    """The page title Wiktionary keeps this word under.

    A reconstructed word lives in the ``Reconstruction:`` namespace with its
    language; an attested headword is the title itself. The address and the
    record of which pages exist are both built from this one title.
    """
    word = (entry.get("word") or "").strip()
    if not word:
        return ""
    lang = entry.get("lang") or ""
    recon = bool(entry.get("recon")) or (bool(lang) and kind_of(lang) == "proto")
    if recon and word.startswith("*"):
        # The namespace already says "reconstruction": Wiktionary titles the
        # page without the asterisk (Reconstruction:Proto-Germanic/nahts), and a
        # link that keeps it opens nothing (2026-11-12).
        word = word[1:]
    name = _lang(lang).get("name") or lang
    return f"Reconstruction:{name}/{word}" if recon else word


def _wiktionary_page(entry: dict) -> dict | None:
    """The Persian Wiktionary's page for this word, when one was read.

    The glossary's Persian words come from Dehkhoda, which has no page on the
    English Wiktionary to open.  A pass over fa.wiktionary.org records which
    words do have one (`data/sources/fa_wiktionary.jsonl.gz`), so the word page
    can point at the place the word was actually read — and, where the page
    prints an etymology, quote it beside this model's own reading instead of
    mixing the two (admin, 2026-11-11).
    """
    if (entry.get("lang") or "") != "fa":
        return None
    note = wiktionary_pages.note("fa", entry.get("word") or "")
    if not note or not note.get("found"):
        return None
    return note


def _entry_sources(entry: dict) -> list[dict]:
    """Where the glossary entry itself came from, resolved to titles and links.

    Most entries are machine-readable Wiktionary; the hand-built supplements in
    ``data/lexicon/_supplement/`` name their own source, and an entry that
    quotes a passage carries it in ``ref``. A reconstructed form added by hand
    must show its citation — the entry is only as good as the sentence behind
    it (2026-11-08).
    """
    known = data.sources()
    ids: list[str] = []
    for src in [entry.get("source"), *(entry.get("sources") or [])]:
        if src and src not in ids:
            ids.append(src)
    # The generated lexicons do not repeat their provenance on every one of
    # 266k rows: they are machine-readable Wiktionary by construction, and the
    # hand-built supplements all name their own source. So an entry without a
    # declared source is a Wiktionary entry, and saying so is a fact, not a
    # guess (2026-11-08: an attested word must have a source).
    if not ids and entry.get("word"):
        ids.append("wiktionary")
    out: list[dict] = []
    for sid in ids:
        row = known.get(sid) or {}
        source = {
            "id": sid,
            "title": row.get("title") or sid,
            "url": row.get("url") or "",
            "kind": row.get("kind") or "",
            "ref": entry.get("ref") or "",
        }
        # A Wiktionary row points at the site; carry the entry's own page so a
        # citation is something a reader can open (2026-11-08).
        stored = entry.get("url") or ""
        if sid == "wiktionary":
            # A root the dictionary never gave a page of its own was recorded
            # *inside* another entry's etymology, so the entry names that page
            # instead of a page that does not exist (2026-11-08).  The stored
            # address is only a Wiktionary page when it really is one: a
            # Persian entry's `url` is its Dehkhoda page, and labelling that as
            # the Wiktionary link put a vajehyab address behind the quotation
            # mark (admin, 2026-11-11).
            if _is_wiktionary_url(stored):
                source["entry"] = stored
            else:
                # No address was recorded when the entry was read, so the page
                # is only claimed when this repo's own pass found one
                # (`tools/en_wiktionary_index.py`); otherwise the icon stays
                # away instead of opening a title that may not exist (admin,
                # 2026-11-12).
                found = wiktionary_pages.en_page(entry.get("lang") or "",
                                                 entry.get("word") or "")
                if found:
                    source["entry"] = found["url"]
        elif stored and _same_site(stored, row.get("url") or ""):
            # An entry imported from a dictionary records the page it was read
            # on — Dehkhoda's own entry for کبود, not the dictionary's front
            # page.  Only an address on the source's own site counts as that
            # source's page (admin, 2026-11-12: the book must open the word).
            source["entry"] = stored
        out.append(source)
    page = _wiktionary_page(entry)
    if page:
        row = known.get("fa-wiktionary") or {}
        out.append({
            "id": "fa-wiktionary",
            "title": row.get("title") or "ویکی‌واژه فارسی",
            "url": row.get("url") or "https://fa.wiktionary.org",
            "kind": row.get("kind") or "lexicon",
            "ref": "",
            "entry": page["url"],
        })
    return out


def _same_site(one: str, other: str) -> bool:
    """Whether two addresses are pages of one site (``www.`` aside)."""
    def host(url: str) -> str:
        return re.sub(r"^www\.", "",
                      re.sub(r"^https?://", "", (url or "").strip().lower()).split("/")[0])
    return bool(one and other) and host(one) == host(other)


def _entry_pages(entry: dict) -> list[dict]:
    """The pages a reader can open for this word — one row per page.

    A page is carried only when it is *recorded*: the address the entry was read
    on (a Wiktionary article, Dehkhoda's entry on vajehyab), or a Wiktionary page
    this pass found for the headword (`tools/en_wiktionary_index.py`).  A word
    with no recorded page yields nothing, and the page then shows no icon at all
    (admin, 2026-11-12) — an icon that opens nothing is worse than no icon.
    """
    pages: list[dict] = []
    seen: set[str] = set()
    for src in _entry_sources(entry):
        url = src.get("entry") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        pages.append({
            "id": src.get("id") or "",
            "title": src.get("title") or "",
            "url": url,
            "kind": "wiktionary" if _is_wiktionary_url(url) else (src.get("kind") or ""),
        })
    if not any(p["kind"] == "wiktionary" for p in pages):
        found = wiktionary_pages.en_page(entry.get("lang") or "",
                                         entry.get("word") or "")
        if found and found["url"] not in seen:
            pages.append({"id": "wiktionary", "title": "Wiktionary",
                          "url": found["url"], "kind": "wiktionary"})
    return pages


def _cognate_payload(set_id: str) -> dict | None:
    """A cognate set with names, native forms and the glossary's own entries."""
    rec = cognate_index().get(set_id)
    if not rec:
        return None
    forms: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for f in rec["forms"]:
        key = (f["l"], f["w"])
        if key in seen:
            continue
        seen.add(key)
        row = _lang(f["l"])
        forms.append({
            "l": f["l"],
            "w": f["w"],
            "r": f.get("r") or "",
            "s": f.get("s") or "",
            "lang_name": row.get("name", f["l"]),
            "branch": row.get("branch", ""),
            **_form_meta(f["l"], f["w"], f.get("r") or ""),
        })
    for lang, word in cog_words().get(set_id, []):
        entry = (word_index().get((lang, word)) or [{}])[0]
        readings = attested_spellings(entry)
        if (lang, word) in seen:
            # Wiktionary's descendant tree often records the form without the
            # romanisation; borrow it from our own glossary entry instead of
            # leaving the row unreadable in the cognate table (and unusable for
            # matching a rebuilt form).
            for f in forms:
                if f["l"] == lang and f["w"] == word:
                    if readings:
                        f["r"] = readings[0]
                        f["readings"] = readings
                    f["glossary"] = True
                    f.update(_form_meta(lang, word, f["r"]))
                    break
            continue
        seen.add((lang, word))
        row = _lang(lang)
        forms.append({
            "l": lang,
            "w": word,
            "r": readings[0] if readings else "",
            "readings": readings,
            "s": "; ".join(entry.get("gloss", [])[:1]),
            "lang_name": row.get("name", lang),
            "branch": row.get("branch", ""),
            "glossary": True,
            **_form_meta(lang, word, readings[0] if readings else ""),
        })
    forms.sort(key=lambda f: (_lang_order(f["l"])[0], f["branch"] or "zz", _lang_order(f["l"])[1]))
    return {
        **rec,
        "forms": forms,
        "n": len(forms),
        "branches": len({f["branch"] for f in forms if f["branch"]}),
    }


def overview() -> dict:
    langs = []
    total_words = 0
    for lang, row in data.languages().items():
        n = len(data.lexicon(lang)) if any(l == lang for l, _ in data.available_lexicons()) else 0
        total_words += n
        chain = data.derivation_chain(lang) if lang != "ine-pro" else []
        langs.append({
            "id": lang,
            "name": row.get("name", lang),
            "short": row.get("short", lang),
            "kind": row.get("kind", "attested"),
            "branch": row.get("branch", ""),
            "ancestor": row.get("ancestor"),
            "era": row.get("era"),
            "script": row.get("script", ""),
            "notes": row.get("notes", ""),
            "provisional": bool(row.get("provisional")),
            "chain": chain,
            "missing": data.missing_stages(chain) if chain else [],
            "words": n,
        })
    rules = [
        {
            "src": src, "dst": dst, "name": rs.name, "count": len(rs.rules),
            "established": sum(1 for r in rs.rules if r.tier == "established"),
            "proposed": sum(1 for r in rs.rules if r.tier != "established"),
            "date_start": rs.date_start, "date_end": rs.date_end,
            "description": rs.description,
        }
        for (src, dst), rs in sorted(data.rulesets().items())
    ]
    return {
        "languages": langs,
        "rules": rules,
        "stats": {
            "languages": len(langs),
            "words": total_words,
            "rulesets": len(rules),
            "rules": sum(r["count"] for r in rules),
            "cognate_sets": len(cognate_index()),
        },
        "coverage": coverage(),
        "morphology": morphology(),
    }


@lru_cache(maxsize=64)
def _search_rows(lang: str) -> tuple[tuple[str, str, dict], ...]:
    """One language's lookup table, built once: (lowercased word, glosses, entry).

    Searching the raw glossaries took a second per query, because the same
    266,000 entries were lowercased and joined again on every keystroke. The
    table is the same data with the work already done, so a search is a scan of
    prepared strings and the interface can answer while the reader types
    (2026-11-08: the home page is a single search box).
    """
    rows = []
    for entry in data.lexicon(lang):
        word = entry.get("word") or ""
        rows.append((word.lower(), " ".join(entry.get("gloss") or []).lower(), entry))
    return tuple(rows)


def search(q: str, lang: str | None = None, limit: int = 40, gloss: bool = True) -> list[dict]:
    q = q.strip().lower()
    if not q:
        return []
    exact, prefix, contains, semantic = [], [], [], []
    # One row per *word*, not per part of speech: Wiktionary files the same
    # lexeme under several headings (the participle and the adjective of
    # *aiganaz), and a list that printed one row for each made one word look
    # like two entries (admin, 2026-11-12).  The grouping is the one the
    # glossary already uses, so the two lists cannot disagree.
    seen: set[tuple[str, str, int]] = set()
    langs = [lang] if lang else [l for l, _ in data.available_lexicons()]
    for lg in langs:
        for word, glosses, entry in _search_rows(lg):
            if word == q:
                bucket = exact
            elif word.startswith(q):
                bucket = prefix
            elif q in word:
                bucket = contains
            elif gloss and q in glosses:
                bucket = semantic
            else:
                continue
            pron = readings_for(entry)
            groups = sense_index().get((lg, entry["word"])) or []
            here = _group_of(groups, entry)
            key = (lg, entry["word"], here["sense"] if here else 0)
            if key in seen:
                # This part of speech is another heading of a word already on
                # the list; its glosses came with the row.
                continue
            seen.add(key)
            search_status = attestation.classify(
                entry, proto=kind_of(lg) == "proto",
                in_script=_in_native_script(lg, entry["word"]))
            bucket.append(_with_reading({
                "word": entry["word"], "lang": lg,
                # The word's own parts of speech and meanings, as the glossary
                # prints them (`aiganaz` is one word, "verb / adj", "own").
                "pos": " / ".join(here["pos"]) if here else entry.get("pos", ""),
                "gloss": (here["gloss"] if here else entry.get("gloss", []))[:2],
                "cog": entry.get("cog"),
                "attestation": search_status,
                "written": attestation.written(entry["word"], search_status),
                # Which word of a shared spelling this hit is, so the row opens
                # the right meaning instead of the landing page (2026-11-09).
                "sense": here["sense"] if here else 0,
                "senses": len(groups) if groups else 1,
                "evidence": evidence_for(entry["word"], lg),
                "show_reading": show_reading(lg, entry["word"]),
                "reading": pron["reading"], "ipa": pron["ipa"],
            }, lg, entry["word"]))
            if len(exact) >= limit:
                break
    return (exact + prefix + contains + semantic)[:limit]


def glossary(lang: str, limit: int = 400, roots_first: bool = True,
             band: str | None = None, q: str | None = None) -> dict:
    """Every headword of one stage, alphabetically, each a door to its page.

    This is the replacement for a separate "cognates" page (2026-11-08): a word or root *glossary* that opens the word view again, instead of
    a list of reconstructed sets. Roots come first for Proto-Indo-European,
    because the root is what everything else is built on.

    Each row carries the word's coverage band, so the glossary is coloured with
    the same six colours as the coverage page (2026-11-09).  The band is
    read from `data/category_index.json.gz`, written by the same full run of
    `tools/coverage.py` that publishes `data/coverage.json`: the list cannot
    disagree with the numbers, and the page never re-measures 400 words per
    request.  A proto stage has no band — the six are for attested languages.
    """
    # `all` is the address the glossary writes for "no filter", so the API
    # accepts it too (2026-11-09).
    band = None if band == "all" else band
    rows: list[dict] = []
    # One read of the published index for the whole page: `band_for` stats the
    # file to notice a new measurement, and doing that once per headword made a
    # 165,000-word glossary stat the same file 165,000 times and take five
    # seconds a request (2026-11-10).
    index = band_index().get(lang) or {}
    # One stage-wide fact, read once: a proto stage is reconstructed as a whole,
    # and a stage with its own script has to show that script to be attested
    # (2026-11-11).
    proto = kind_of(lang) == "proto"
    needle = (q or "").strip().lower()
    for word, entries in lang_index(lang).items():
        # A list of 165,000 headwords is read by looking for one: `q` keeps the
        # rows whose spelling contains it (2026-11-10, the Persian inventory).
        # The hit is recorded on the row rather than dropping it here, because
        # the stage-wide counts below must not shrink to the 204 words that
        # happen to contain "ab" (2026-11-12, critic P1-2).
        matched = not needle or needle in word.lower()
        # One row per *word*, not per part of speech (2026-11-09): a spelling
        # Wiktionary writes as a noun and a verb with one etymology is one
        # headword with one row, and two spellings that mean different things
        # are two rows, numbered (1, 2 …) so a reader can pick the right one.
        groups = _senses_for((lang, word)) or senses.groups(entries)
        for group in groups:
            entry = group["rep"]
            # What the headword *is*, as a column of its own (admin,
            # 2026-11-13).  The old "root" pill asked whether the word's
            # etymology mentioned a root, which is true of almost every word
            # in a reconstructed stage and told the reader nothing: 796 of the
            # 799 Proto-Indo-Iranian rows wore it.  A row is a **root** when the
            # dictionary heads it as one, and an **affix** when it is written
            # bound (-a-, -nós) or headed as one; every other row is a word and
            # the cell stays empty.
            pos_label = (entry.get("pos") or "").strip().lower()
            headword = word.strip()
            bound = headword.startswith("-") or headword.endswith("-")
            kind = ("root" if pos_label == "root"
                    else "affix" if bound or pos_label in _BOUND_POS else "")
            # The reading line is only ever printed, so it is built for the
            # rows that are shown, not for the 165,000 the counts need
            # (2026-11-10).
            # How this headword is known, for the chip beside it: attested
            # words print in their own script, a reconstruction carries its
            # asterisk (2026-11-11).
            status = attestation.for_word(
                group["entries"], proto=proto,
                in_script=_in_native_script(lang, entry["word"]))
            rows.append({
                "_q": matched,
                "word": entry["word"], "pos": " / ".join(group["pos"]),
                "attestation": status,
                "written": attestation.written(entry["word"], status),
                "gloss": [g for g in _page_gloss(lang, entry, group["gloss"])[:2] if g],
                "kind": kind,
                "root": kind == "root",
                # The colour of this sense, from the same published measurement
                # the coverage page prints.
                "band": _band_in(index, entry["word"], group["sense"]),
                "sense": group["sense"], "senses": len(groups),
                # This row's own reading, not the spelling's first homograph:
                # دوش is duš (shower) and dōš (shoulder, 'last night'), and a
                # list that printed one reading for all three said the wrong
                # word (2026-11-12).
                "reading": readings_for(entry)["reading"],
                "ipa": entry.get("ipa") or "",
            })
    rows.sort(key=lambda r: (0 if (roots_first and r["root"]) else 1,
                             r["word"].lstrip("*").lower(), r.get("sense", 1)))
    # Counts over the whole stage, not over the page: a reader filtering for
    # *fully explained* wants to know how many there are, not how many fit in
    # the first 400 (2026-11-09).
    counts = Counter(r["band"] for r in rows if r["band"])
    stage_total = len(rows)
    sense_total = sum(1 for r in rows if r.get("sense", 1) == 1)
    rows = [r for r in rows if r.pop("_q", True)]
    if band == PIE_WORDS_BAND:
        # The reader's default view (2026-11-09): everything the record
        # keeps inside the family.  A word borrowed from Arabic or Turkic is
        # not a failure of the sound laws, so it does not belong in the list a
        # reader opens by default; `band=all` (an empty band) shows them.
        rows = [r for r in rows if r["band"] != "non_pie"]
    elif band:
        rows = [r for r in rows if r["band"] == band]
    shown = [_with_reading({**row,
                            "show_reading": show_reading(lang, row["word"]),
                            "evidence": evidence_for(row["word"], lang)}, lang, row["word"])
             for row in rows[:limit]]
    legend = Counter(r["band"] for r in shown if r["band"])
    # *banded* describes the list the reader filtered, not the 400 rows on the
    # page: subtracting a page's count from a language's total said "4 not
    # banded" about a stage of 7,613 (2026-11-12, critic P1-3).
    banded = sum(1 for r in rows if r["band"])
    return {"lang": lang, "lang_name": _lang(lang).get("name", lang),
            "total": len(rows), "roots": sum(1 for r in rows if r["root"]),
            "rows": shown, "limit": limit,
            "band": band or "",
            # What "attested", "recorded" and "proposed" mean, once per page:
            # the status column says the word, the tooltip says the sentence
            # (`attestation.DEFINITIONS`, the same text the word pages use).
            "statuses": dict(attestation.DEFINITIONS),
            # The whole stage, before the band is applied: the selector counts
            # "PIE words" as this minus the non-PIE band.
            "stage_total": stage_total,
            "counts": dict(counts.most_common()),
            # How many spellings the stage holds, beside how many words: the
            # gap between the two is the homographs (2026-11-09).
            "headwords": sense_total,
            "banded": banded,
            "legend": dict(legend.most_common())}


class BandIndex(dict):
    """The published bands, plus the inputs the measurement was taken over."""

    def __init__(self, mapping=(), inputs=None):
        super().__init__(mapping)
        self.inputs = inputs if isinstance(inputs, dict) else {}

    @property
    def stale(self) -> bool:
        """True when the files behind the measurement have changed since."""
        return data.inputs_stale(self.inputs)


@lru_cache(maxsize=1)
def _band_index_at(_stamp: int) -> BandIndex:
    """The published band of every attested word, or an error if it is broken.

    A missing index is a fresh clone before the first measurement, and no
    colours is the honest answer there.  A file that is present but cannot be
    read is different: it used to be swallowed and every row silently lost its
    colour, so a truncated publish looked like a project with nothing in it.
    That now raises, and the reader sees the error instead of a colourless
    glossary (2026-11-12).
    """
    path = data.DATA / "category_index.json.gz"
    if not path.exists():
        return BandIndex()
    # A megabyte of JSON per process is pure overhead on a restart, and the
    # file only changes when the measurement is republished — which moves its
    # mtime and so its cache key (2026-11-12).
    def build() -> dict:
        with gzip.open(path, mode="rt", encoding="utf-8") as fh:
            try:
                payload = json.load(fh)
            except ValueError as exc:  # a truncated or half-replaced file
                raise RuntimeError(
                    f"{path.name} is unreadable ({exc}); rerun tools/coverage.py"
                ) from exc
        return {"bands": payload.get("bands", {}), "inputs": payload.get("inputs")}

    payload = data.cached("bands", 1, [path], build)
    return BandIndex(payload.get("bands", {}), inputs=payload.get("inputs"))


def _band_in(index: dict, word: str, sense: int = 1) -> str:
    """One word's band inside an index a caller has already read."""
    row = (index or {}).get((word or "").strip())
    if isinstance(row, list):
        return row[sense - 1] if 0 < sense <= len(row) else ""
    return row or ""


def band_for(lang: str, word: str, sense: int = 1) -> str:
    """The published band of one *sense* of a word.

    Since 2026-11-09 the index stores one band per sense — ``bank`` the
    institution and ``bank`` the river's edge can fall in different bands — and
    a file written by the previous run stores one band for the whole spelling.
    Both are read here, so an old index never colours the wrong row.
    """
    row = (band_index().get(lang) or {}).get((word or "").strip())
    if isinstance(row, list):
        return row[sense - 1] if 0 < sense <= len(row) else ""
    return row or ""


def band_index() -> dict[str, dict[str, str]]:
    """``lang -> word -> band`` from the published measurement.

    Cached on the file's mtime, so a long-lived server picks up a new
    measurement without a restart, and absent before the first published full
    run (the glossary then simply shows no colours).
    """
    path = data.DATA / "category_index.json.gz"
    try:
        stamp = path.stat().st_mtime_ns
    except OSError:
        return BandIndex()
    return _band_index_at(stamp)


def suggest(q: str, limit: int = 8, lang: str | None = None) -> list[dict]:
    """A short list of the closest words for the search box, words first.

    Form matches only — a meaning match needs the gloss scan and belongs to the
    results page, not to a dropdown that opens on every keystroke.
    """
    rows = search(q, lang, limit=limit, gloss=False)
    return [{"word": r["word"], "lang": r["lang"], "reading": r.get("reading", ""),
             "gloss": (r.get("gloss") or [""])[0]} for r in rows]


def _ancestry_triples(entry: dict) -> list[tuple[str, str, str]]:
    """Ancestry records with the ``:inh`` shorthand expanded and de-duplicated.

    Wiktextract writes some inheritance links as a single ``:inh`` row holding
    ``lang:form`` (``ine-pro:*ḱwṓ``); the display and the derivation both want
    the plain triple.
    """
    out: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for lang, word, rel in entry.get("anc") or []:
        if lang == ":inh":
            if ":" not in (word or ""):
                continue
            lang, word = word.split(":", 1)
            rel = "inherit"
            word = word.strip().rstrip(">").strip()
        elif lang.startswith(":"):
            continue
        if not word or (lang, word) in seen:
            continue
        seen.add((lang, word))
        out.append((lang, word, rel))
    if not out:
        # No template states an origin; the entry's own sentence may (see
        # `_prose_ancestry`).  Nothing is read when one does, so a word with
        # both is answered by the template alone.
        out.extend(_prose_ancestry(entry))
    return _not_a_flattened_prefix(out, entry)


#: "From Proto-Iranian *ā- + *gam-" — a verb stated as two bound morphemes.
_PREFIXED_VERB = re.compile(r"\bfrom\s+(?:[A-Za-z][\w-]*\s+)?\S*-\s*\+\s*\S*-", re.I)


def _not_a_flattened_prefix(rows: list[tuple[str, str, str]], entry: dict) -> list[tuple[str, str, str]]:
    """Drop an ancestry that is really a prefixed verb's pieces read in a line.

    fa آمدن's record says "From Proto-Iranian *ā- + *gam-", and the extractor
    filed both morphemes as ancestors, so the ladder climbed *ā- and printed
    Proto-Indo-European *h₂éd → Persian ad above a verb meaning "to come, to
    arrive" (critic batch 06, 2026-11-13).  When every row is a bound form and
    the sentence states the word as one bound form plus another, the rows are
    pieces of a construction, not a chain: only the root the sentence names
    survives, and a chain with no root is no ancestry at all.
    """
    if len(rows) < 2 or not any(str(row[1] or "").endswith("-") for row in rows):
        return rows
    first = re.split(r"\.\s|;", str(entry.get("etym") or ""), 1)[0]
    if not _PREFIXED_VERB.search(first):
        return rows
    # The root the sentence names is the verb's own; the prefixes it is made
    # with are pieces, and their history is not the verb's history.
    return [row for row in rows if str(row[2] or "") == "root"]


#: A sentence that states where a word comes from, in words rather than in an
#: ancestry template.  Only the **first** sentence of an entry is read, and only
#: when it opens with one of these; anything later in the paragraph is
#: commentary, an author's argument, or a note about another word.
_PROSE_ANCESTRY_CUE = re.compile(
    r"^\s*(?:Inherited|Derived|Borrowed|Learned borrowing|Semi-learned borrowing|"
    r"From|Continues|Descends)\b", re.I)
#: The stage and the form it names: ``from Proto-Indo-European *h₂énts``,
#: ``from the Proto-Indo-European root noun *h₂énts``.  A form has to carry the
#: asterisk a reconstruction is written with — that is what makes the sentence
#: unambiguous — so an attested stage's bare word is not read this way.
_PROSE_ANCESTRY_RE = re.compile(
    r"\b(?:from|Inherited from|Derived from|Borrowed from|Descends from)\s+(?:the\s+)?"
    # The name is case-sensitive even though the cue is not — "Proto-Indo-European
    # root" would otherwise swallow the word "root" into the name.
    r"(?P<name>(?-i:(?:Proto|Old|Middle|New|Ancient|Classical|Late|Vulgar)[ -][A-Z][A-Za-z-]*"
    r"(?:\s+[A-Z][A-Za-z-]*)?))\b(?:\s+[a-z][a-z-]*){0,4}?\s*\*"
    r"(?P<form>[^\s,;.:()\[\]“”\"'’]+)", re.I)
#: A form written with a ``pre-`` label, ``pre-Germanic *h₂entó-``.  The label
#: names the stage a form belongs to in words, not a stage this model has: the
#: form it marks is read at the nearest registered stage the sentence names for
#: it.  It is a label on *that* form — never a licence to read on to the next
#: starred form, which is the form this one is made from (admin, 2026-11-12).
_PROSE_PRE_STAGE_RE = re.compile(
    r"\b(?P<label>(?:[Pp]re)[- ][A-Z][A-Za-z-]*)\s+\*"
    r"(?P<form>[^\s,;.:()\[\]“”\"'’]+)")
#: A sentence that hedges, compares, or names a substrate is not a statement of
#: ancestry: "likely from a substrate", "cognate with", "possibly related to".
#: A sentence with a ``+`` states a construction, which is the construction
#: reader's business, not a single ancestor's.
_PROSE_ANCESTRY_STOP = re.compile(
    r"\+|\b(?:cognate|compare|related|synonym|homonym|doublet|variant|uncertain|"
    r"unknown|obscure|unclear|possibly|perhaps|probably|likely|maybe|may|might|"
    r"could|suggest\w*|traced|assum\w*|hypothes\w*|substrate|doubtful)\b", re.I)


@lru_cache(maxsize=1)
def _stage_by_name() -> dict[str, str]:
    """The registry's stage names and abbreviations, folded to their codes.

    One reader for a name a sentence writes — "Proto-Indo-European", "PIE" —
    so a prose ancestor can only ever be a stage this model actually has.
    """
    out: dict[str, str] = {"pie": "ine-pro"}
    for code, row in data.languages().items():
        for key in (row.get("name"), row.get("short")):
            if isinstance(key, str) and key.strip():
                out.setdefault(key.strip().lower(), code)
    return out


#: Where the prose of an etymology begins, after a scraped *tree* of nodes.
_ETYM_CUE = re.compile(r"\b(Borrowed|Inherited|From|Probably|Possibly|Uncertain|"
                       r"Doublet|Blend|Clipping|Back-formation|Calque|Contracted|"
                       r"Alteration|Unknown|Named)\b")


def _prose_etym(lang: str, word: str, text: str) -> str:
    """The record's sentence, with Wiktionary's flattened etymology *tree* cut.

    A scraped article can hand a tree over as one string — «Etymology tree
    Latin Gallus Proto-Indo-European *-(i)yós … ▲ Latin -ius [nom.] French
    gallium [bor.] Persian گالیم Borrowed from French gallium.» — and the page
    printed every node as if it were prose (critic batch 02, 2026-11-13: 1,662
    Persian entries; گالیم).  The tree is a picture the site draws; only the
    sentence after it is the record, and it is found by the headword node the
    tree ends on (`Persian گالیم`), with the opening cue as a fallback.  A tree
    with no sentence under it says nothing rather than reciting nodes.
    """
    text = str(text or "").strip()
    if "Etymology tree" not in text:
        return text
    tail = ""
    name = (data.language_name(lang) or "").split(" (")[0].strip()
    if name and word:
        marker = f"{name} {word}"
        at = text.rfind(marker)
        if at >= 0:
            tail = text[at + len(marker):]
    if not tail.strip(" ,;·—–-"):
        found = _ETYM_CUE.search(text, max(0, text.rfind("▲")))
        tail = text[found.start():] if found else ""
    return tail.strip(" ,;·—–-")


def _prose_ancestry(entry: dict) -> list[tuple[str, str, str]]:
    """The ancestor an entry's own sentence names, when no template states one.

    *anda- is the case (admin, 2026-11-12): Wiktionary writes "From
    pre-Germanic *h₂entó- … from the Proto-Indo-European root noun *h₂énts" as
    prose, with no ``{{inh}}`` row, so the ladder stopped at a ``???`` over a
    piece whose page did record where it came from.  The sentence is the
    record — the construction reader has always read prose the same way — so a
    named, registered stage and a form its glossary really holds are accepted
    as one ``derived`` ancestor.

    A ``pre-`` label is read as a label, not a stage.  "pre-Germanic
    *h₂entó- … from the Proto-Indo-European root noun *h₂énts" names two
    forms: the one that came first (*h₂entó-, the ancestor) and the one it was
    made from (*h₂énts, which belongs to *h₂entó-'s own construction).  Skipping
    the label because it is unregistered and taking the next registered stage
    climbed one level too far; the marked form stands at the stage the sentence
    names for it — here Proto-Indo-European (admin, 2026-11-12).

    Nothing else is read: only the first sentence, only when it opens with an
    ancestry cue, never a hedged or comparative one, never a sentence with a
    ``+`` (that is a construction), and never a form the ancestor stage does not
    head.  A ``pre-`` form whose sentence never names a registered stage has no
    stage this model can place it at, and is left as silence rather than a
    guess.
    """
    text = str(entry.get("etym") or "")
    if not text or entry.get("built_as") or text.startswith("Etymology tree"):
        return []
    first = re.split(r"(?<=[.;])\s+", text.strip())[0]
    if not _PROSE_ANCESTRY_CUE.match(first) or _PROSE_ANCESTRY_STOP.search(first):
        return []
    own = str(entry.get("lang") or "")
    named: list[tuple[int, str, str]] = []
    stages: list[tuple[int, str]] = []
    for match in _PROSE_ANCESTRY_RE.finditer(first):
        code = _stage_by_name().get(match.group("name").strip().lower())
        if not code:
            continue
        stages.append((match.start(), code))
        named.append((match.start(), code, match.group("form").strip()))
    for match in _PROSE_PRE_STAGE_RE.finditer(first):
        # The label stands for the stage the sentence goes on to name for the
        # form it marks.  A later stage of the same sentence is the only place
        # this model can read it from, so no registered name, no row.
        code = next((c for pos, c in stages if pos > match.start()), "")
        if not code:
            continue
        named.append((match.start(), code, match.group("form").strip()))
    # The sentence's own order decides: the first form it names is the nearest
    # ancestor, and a form the stage does not head cannot become a rung.
    for _pos, code, form in sorted(named):
        if code == own:
            continue
        if not form or form in ("*", "*-"):
            continue
        if _lemma_entry(code, form) is None:
            continue
        return [(code, form, "derived")]
    return []


def _piece_ancestor_gloss(entry: dict, form: str) -> str:
    """The meaning a construction's piece quotes for one of the word's ancestors.

    *andaswarō states no gloss for its PIE root — its sentence is "From *anda-
    + *swarō" — but the piece *swarō says the root it comes from means "to
    say, speak, talk, swear, curse".  That is the sense the row must carry;
    without it the page quoted the other PIE root spelled *swer- (2026-11-12).
    """
    stage = data.stage_of(str(entry.get("lang") or "")) or str(entry.get("lang") or "")
    if not stage:
        return ""
    for row in entry.get("built_as") or []:
        for piece in row.get("pieces") or []:
            written = _formed_piece(piece)
            other = _lemma_entry(stage, written) if written else None
            hint = _ancestor_gloss(other or {}, form)
            if hint:
                return hint
    return ""


def _ancestry_forms(entry: dict) -> list[dict]:
    """The word's recorded ancestors, oldest meaning in the right sense.

    A construction's ancestor is named by the piece, not by the compound:
    *andaswarō's PIE row is the root its second piece *swarō comes from, and
    *swarō's own sentence is the one that quotes that root's meaning.
    """
    out = []
    for lang, word, rel in _ancestry_triples(entry):
        row = _lang(lang)
        # What the word meant at that stage, so a rung of the loan ladder is a
        # word with a sense like every rung of a word's own ladder (admin,
        # 2026-11-12).
        # The sense the entry's own sentence gives this ancestor, when it names
        # one: two roots spelled *swer- must not trade glosses (2026-11-12).  A
        # compound reaches the ancestor through a piece, and the piece's own
        # sentence may be the one that says which sense.
        held = _sense_entry(lang, normalise_etymon(word) or word,
                            _ancestor_gloss(entry, word)
                            or _piece_ancestor_gloss(entry, word))
        out.append({
            "lang": lang,
            "lang_name": row.get("name", lang),
            "form": word,
            "rel": rel,
            # A rung's line is a caption beside the step it names, not a
            # dictionary article: the sense is cut at 72 characters.
            "gloss": _rung_gloss(held.get("gloss") or [], limit=72) if held else "",
            "pos": str(held.get("pos") or "") if held else "",
            # A rung of a timeline names its stage and the years it was in use;
            # the loan ladder reads the same two fields (2026-11-09).
            "era_label": era_label(row.get("era")),
            "branch": row.get("branch", ""),
            **_form_meta(lang, normalise_etymon(word) or word),
        })
    return out


RTL_RANGES = (
    (0x0590, 0x05FF),   # Hebrew
    (0x0600, 0x06FF),   # Arabic
    (0x0700, 0x074F),   # Syriac
    (0x0750, 0x077F),   # Arabic supplement
    (0x0780, 0x07BF),   # Thaana
    (0x08A0, 0x08FF),   # Arabic extended-A
    (0xFB1D, 0xFDFF),   # Hebrew/Arabic presentation forms
    (0xFE70, 0xFEFF),   # Arabic presentation forms-B
    (0x10840, 0x1087F), # Imperial Aramaic
    (0x1E900, 0x1E95F), # Adlam
)


def is_rtl(text: str) -> bool:
    """True when a word's own script runs right to left (Persian, Arabic, Hebrew)."""
    return any(start <= ord(ch) <= end for ch in text for start, end in RTL_RANGES)


def attested_spellings(entry: dict) -> list[str]:
    """Romanisations recorded for the word, which the sound laws can produce.

    Persian پدر has three accepted readings (``pedar``, ``pidar``, ``padar``);
    the rules output one of them. Without these the page for every non-Latin
    word would report "differs" even when the derivation is exact.

    A sign-by-sign transliteration is not a reading: Old Persian ``k-a-r`` is
    how the syllabary is written, not how the word sounds (``kāraʰ``), and
    stripping its hyphens would let the page claim a match against a spelling
    (2026-11-08, the same lesson as the superscript ʰ). ``_is_syllabic`` keeps
    those out, exactly as ``readings_for`` does for display.
    """
    out: list[str] = []
    for value in [entry.get("translit")] + list(entry.get("translit_alt") or []):
        if not value or not isinstance(value, str) or _is_syllabic(value):
            continue
        cleaned = detokenize(tokenize(value))
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


_LONG_VOWEL_NOTATION = str.maketrans({"â": "ā", "ê": "ē", "î": "ī", "ô": "ō",
                                      "û": "ū", "Â": "Ā", "Ê": "Ē", "Î": "Ī",
                                      "Ô": "Ō", "Û": "Ū"})


def _comparison_key(form: str) -> str:
    """How two spellings of the same phonological form are compared.

    Two dictionary conventions are writing, not phonology, and are dropped
    before comparing. Wiktionary marks short vowels with a breve (Greek
    ``pătḗr``) while the engine writes length only. It also writes the Old
    Persian final /h/ — a consonant the syllabary leaves unwritten — as a
    superscript: 𐎭𐎼𐎹 *drayaʰ* "sea", and the entry that records IPA as well
    spells the same sign with a plain *h* (``vazr̥kaʰ`` = /waˈzr̩kah/). A
    standalone ʰ therefore reads as *h*; a ʰ inside a stop token (``kʰ``,
    ``dʰ``) is aspiration and is left alone. Nothing else is dropped.
    """
    # Two romanisation schemes write one long vowel: the dictionaries use the
    # circumflex (bâz, târ) where the sound laws write the macron (bāz, tār).
    # It is the same letter and the same length, so it is notation here too
    # (2026-11-09: 25 Persian words were "not the same form" for that only).
    form = form.translate(_LONG_VOWEL_NOTATION)
    # The zero-width non-joiner is how Persian orthography writes the seam of a
    # compound (آب‌خانه); the dictionary may write the same word without it
    # (Dehkhoda's آب‌خانه headword), and that is spelling, not a different word
    # (2026-11-10).
    form = form.replace("\u200c", "")
    tokens = ["h" if token == "ʰ" else token for token in tokenize(form)]
    return unicodedata.normalize("NFC", "".join(
        ch for ch in unicodedata.normalize("NFD", detokenize(tokens)) if ch != "\u0306"))


STRESSED_VOWELS = "aeiouyæœøəɛɔɨɤɯɪʊɐɑɒɵʌʉɘ"
"""The vowels an acute may be printed on (see the page's own ``pf``)."""

SYLLABIC_MARKS = "\u0325\u0329"
"""The diacritics that make a consonant the syllable's nucleus (r̥, l̩).

A syllabic sonorant carries the stress just as a vowel does: the dictionary
writes Proto-Iranian *wŕ̥kah* and the engine writes ``wˈr̥kah`` (2026-11-08: the recorded word was not found). It is a letter plus its own mark,
so the acute goes after that mark, exactly as it does after a vowel's macron.
"""


def printable_form(form: str) -> str:
    """A form the way a dictionary writes it: the engine's stress token as an acute.

    The rule engine marks stress with ``ˈ`` before the syllable (``jrˈayah``);
    a dictionary puts an acute on the vowel (``jráyah``). The page prints the
    second and stores the first, so a link that carries the printed form must
    still find its headword: this is that translation, applied to every vowel
    and after the vowel's own marks so a long vowel keeps its macron.
    """
    text = unicodedata.normalize("NFD", form)
    out: list[str] = []
    i = 0
    while i < len(text):
        char = text[i]
        if char in "ˈˌ" and i + 1 < len(text):
            letter = text[i + 1]
            j = i + 2
            own = []
            while j < len(text) and unicodedata.combining(text[j]):
                own.append(text[j])
                j += 1
            # A vowel always takes the acute; a consonant only when it is the
            # syllable's nucleus (r̥, l̩), never an ordinary onset consonant.
            if letter in STRESSED_VOWELS or any(own_mark in SYLLABIC_MARKS for own_mark in own):
                mark = "\u0301" if char == "ˈ" else "\u0300"
                out.append(letter + "".join(own) + mark)
                i = j
                continue
        out.append(char)
        i += 1
    return unicodedata.normalize("NFC", "".join(out))


def _same_form(a: str, b: str) -> bool:
    """Whether two forms are one phonological string, notation aside.

    Stress is compared only when both sides mark it: a dictionary headword or
    romanisation with no stress mark is silent about stress, not a claim that
    none fell, and the chain inherits the acute of its ancestor (``*ȷ́ráyas``)
    as a stress mark (``drˈayah``). Everything else must agree.
    """
    key_a, key_b = _comparison_key(a), _comparison_key(b)
    if key_a == key_b:
        return True
    marked = lambda key: "ˈ" in key or "ˌ" in key
    if marked(key_a) == marked(key_b):
        return False
    return key_a.replace("ˈ", "").replace("ˌ", "") == key_b.replace("ˈ", "").replace("ˌ", "")


def _notation_only(a: str, b: str) -> str | None:
    """The letter two spellings disagree on when it is the same consonant.

    Old Persian writes one sign, 𐎺, and transcribers letter it v, while the
    sound laws write the Proto-Iranian labiovelar as *w (OP 𐎭𐎡𐎺 *daivaʰ*,
    laws *daiwˈah*). That is a fact about transcription, not about the word, so
    the rung may say so — but it is never counted as a match: the letter that
    differs is returned and the page explains it, and the verdict stays as the
    laws give it (2026-11-08; measured: a *w > v law costs more words than it
    gains, see proposals/009).
    """
    ka, kb = _comparison_key(a), _comparison_key(b)
    strip = lambda k: k.replace("ˈ", "").replace("ˌ", "")
    if ka == kb or strip(ka) == strip(kb):
        return None
    if strip(ka).replace("v", "w") == strip(kb).replace("v", "w"):
        return "v/w"
    return None


_STRESS_MARKS = {"ˈ", "ˌ"}


def stress_only(a: str, b: str) -> bool:
    """Whether two forms differ only in how, or whether, stress is written.

    The engine marks stress with its own token before the syllable (``jrˈayah``)
    and a dictionary prints an acute on the vowel (``jráyah``); one side may
    also be silent about stress, because an old reconstruction often is.  The
    two are one word, and the word page has always said so.

    Nothing else is forgiven here: the letters (þ against θ), a hyphen, a
    bracket, a space, the breve and every length must agree character for
    character once the accent is set aside.  Mill's audit of the coverage
    counter (proposals/night-0911/notation-audit.md, 2026-11-09) found 397 of
    the 922 "notation" pairs differing by something other than stress, and the
    counter that calls them notation inflates a figure that claims to be
    character for character.  The comparison is made on the raw letters, not
    through ``tokenize``, precisely because tokenize folds þ to θ.
    """
    def profile(form: str) -> tuple[str, tuple[int, ...]]:
        text = unicodedata.normalize("NFD", form)
        segs: list[list[str]] = []
        stress: list[tuple[int, int | None]] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in _STRESS_MARKS:
                stress.append((len(segs), None))
                i += 1
                continue
            if unicodedata.combining(ch) and segs:
                if ch == "\u0301":
                    stress.append((len(segs) - 1, 0))
                else:
                    segs[-1].append(ch)
                i += 1
                continue
            segs.append([ch])
            i += 1
        skeleton = "".join("".join(seg) for seg in segs)
        ordinals: list[int | None] = []
        n = 0
        for seg in segs:
            base, marks_ = seg[0], "".join(seg[1:])
            if base in STRESSED_VOWELS or (base in "rlmn" and any(m in SYLLABIC_MARKS for m in marks_)):
                ordinals.append(n)
                n += 1
            else:
                ordinals.append(None)
        positions: list[int] = []
        for at, acute in stress:
            if acute is not None:
                if at >= len(ordinals) or ordinals[at] is None:
                    return skeleton, (-1,)
                positions.append(ordinals[at])
                continue
            nxt = next((ordinals[j] for j in range(at, len(segs)) if ordinals[j] is not None), None)
            positions.append(-1 if nxt is None else nxt)
        return skeleton, tuple(positions)

    sa, pa = profile(printable_form(a))
    sb, pb = profile(b)
    if sa != sb:
        return False
    if pa and pb:
        return pa == pb
    return bool(pa or pb)


def _match_spelling(form: str, spellings: list[str]) -> str | None:
    """The recorded spelling a derived form reproduces, notation aside."""
    for spelling in spellings:
        if _comparison_key(spelling) == _comparison_key(form):
            return spelling
    return next((spelling for spelling in spellings if _same_form(spelling, form)), None)


#: A gloss in parentheses at the very end of a form: ``*per- (fare)``.
#: Only a trailing one is dictionary apparatus; a parenthesis inside the form
#: is the movable s (``*(s)pend-``) and is handled below.
_TRAILING_GLOSS = re.compile(r"\s*\([^()]*\)\s*$")


def normalise_etymon(form: str) -> str:
    """Strip the notation that belongs to a dictionary, not to a derivation.

    ``*bʰeh₂g-`` → ``*bʰeh₂g``; ``*(s)pend-`` → ``*spend`` (the movable s is
    treated as present); ``(*kʷ)`` style brackets are dropped.

    Three pieces of dictionary apparatus are removed whole rather than merged
    into the form, because each would otherwise become part of a word that no
    dictionary holds: a sense label after a hash (``*kʷís#Determiner`` →
    ``*kʷís``), a gloss in trailing parentheses (``*per- (fare)`` → ``*per``),
    and the second member of an alternation (``*ḱḗr ~ *kr̥d-`` → ``*ḱḗr``, the
    first member being the one the entry names first).  A genuine two-word
    lemma such as ``newe founde`` carries none of these and is left whole: a
    space is a word boundary, never a label.
    """
    form = form.strip()
    # The overwhelmingly common case is a plain glossary headword, and this
    # runs once per entry when a language's lemma index is built (164k Persian
    # headwords): nothing to strip, nothing to compose (2026-11-12).
    if not any(ch in form for ch in "#()~*") and form[:1] != "-" and form[-1:] != "-":
        return form
    if "#" in form:
        form = form.split("#", 1)[0]
    form = _TRAILING_GLOSS.sub("", form)
    if "~" in form:
        form = form.split("~", 1)[0]
    form = form.strip().strip("*").strip()
    form = form.replace("(", "").replace(")", "")
    return form.strip("-").strip()


def _pie_form(entry: dict) -> str | None:
    # Prefer a full word over a bare root when Wiktionary records both
    # (``*ph₂tḗr`` rather than ``*peh₂-``); a root is not a word to derive.
    rows = [word for lang, word, _rel in _ancestry_triples(entry)
            if lang == "ine-pro" and word and word != "ine-pro"]
    full = [word for word in rows if not word.strip().endswith("-")]
    for word in full or rows:
        return normalise_etymon(word)
    if entry.get("cog", "").startswith("ine-pro:"):
        return normalise_etymon(entry["cog"].split(":", 1)[1])
    return None


def inherited_from_pie(entry: dict) -> bool:
    """True when Wiktionary records the word as inherited from PIE."""
    return any(l == "ine-pro" and rel != "borrow" for l, _w, rel in _ancestry_triples(entry))


@lru_cache(maxsize=64)
@lru_cache(maxsize=48)
@lru_cache(maxsize=8)
def _seam_index(lang: str) -> dict[str, str]:
    """Headwords keyed without their zero-width non-joiner.

    Persian writes the seam of a compound with a ZWNJ (آب‌خانه) and a
    dictionary may head the same word without it (Dehkhoda's آبخانه); a link
    or a composed form must open either.  Only the first headword of a seam is
    kept, so the map can never choose between two words — it only makes the
    same word reachable.
    """
    out: dict[str, str] = {}
    for word in data.lexicon_index(lang):
        out.setdefault(word.replace("\u200c", ""), word)
    return out


@lru_cache(maxsize=None)
def _lemma_index(lang: str) -> dict[str, dict]:
    """Glossary entries keyed by their notation-free lemma.

    A cognate set names an etymon the way its root page writes it (``bʰeh₂g-``
    with the root hyphen), while the ladder consumes the stripped form
    (``bʰeh₂g``); ``*bōks`` and ``bōks`` are the same lemma too. Indexing by
    ``normalise_etymon`` lets a rung find the dictionary's own record of the
    form it starts from instead of reporting that nothing is recorded.
    """
    out: dict[str, dict] = {}
    for word, rows in data.lexicon_index(lang).items():
        out.setdefault(normalise_etymon(word), rows[0])
        # A stage may head a word in lower case while a record quotes it with a
        # capital (Proto-Iranian heads *hā́fš, the ancestry row writes *Hā́fš).
        # Case is spelling, not a sound, and one more key per word costs a
        # dictionary slot only where the two differ (2026-11-12).
        out.setdefault(normalise_etymon(word).casefold(), rows[0])
        if "\u200c" in word:
            # The same headword without the seam: a composed Persian compound
            # is written with the ZWNJ and the dictionary may head it without
            # (2026-11-10).
            out.setdefault(normalise_etymon(word.replace("\u200c", "")), rows[0])
    return out


#: The meaning a record writes in brackets beside an ancestor it names:
#: ``*swer- (“to say, speak, talk, swear, curse”)``.
_QUOTED_MEANING_RE = re.compile(
    r"\*\s*(?P<form>[^\s(“”\"',;:()\[\]]+)\s*\(\s*[“\"](?P<gloss>[^”\"]+)[”\"]")


def _ancestor_gloss(entry: dict, form: str) -> str:
    """The meaning an entry's own sentence gives an ancestor it names.

    Wiktionary quotes it beside the form — "From Proto-Indo-European *swer-
    (“to say, speak, talk, swear, curse”)" — and it is what tells two
    homonyms apart (admin, 2026-11-12).
    """
    key = normalise_etymon(form)
    if not key:
        return ""
    for seen in _QUOTED_MEANING_RE.finditer(str((entry or {}).get("etym") or "")):
        if normalise_etymon(seen.group("form")) == key:
            return seen.group("gloss").strip()
    return ""


def _sense_entry(lang: str, form: str, hint: str = "") -> dict | None:
    """The glossary entry a form names, choosing the sense a hint points at.

    One spelling can head two words: Proto-Indo-European heads *swer- "to
    ache, fester" and *swer- "to resound; to speak loudly", and a lemma index
    keeps the first.  A child whose sentence quotes a meaning — Proto-Germanic
    *swarō "oath" is "from Proto-Indo-European *swer- (“to say, speak, talk,
    swear, curse”)" — must be given that one; otherwise the timeline reads
    "oath" over the root of aching (admin, 2026-11-12).

    Nothing is guessed: with no hint, or no shared word in either sense, the
    first entry stands exactly as before.
    """
    # The spelling as the glossary heads it: the record writes *swer-, the
    # stage heads swer-, and only the headword reaches every sense of it.
    rows = _notation_entries(lang, form)
    head = str((_lemma_entry(lang, form) or {}).get("word") or "")
    if head:
        rows = word_index().get((lang, head)) or rows
    if not rows:
        return None
    if len(rows) == 1 or not hint:
        return rows[0]
    wanted = senses.content_words(hint)
    if not wanted:
        return rows[0]
    scored = [(len(wanted & senses.content_words(row.get("gloss") or ())), row)
              for row in rows]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[0][1] if scored[0][0] else rows[0]


@lru_cache(maxsize=None)
def _stressless_index(lang: str) -> dict[str, list[str]]:
    """A stage's headwords keyed by their letters with stress left out.

    A record often quotes a reconstruction without the accent the dictionary
    heads (*h₂m̥bʰi for h₂m̥bʰí, *h₂eḱru for h₂éḱru), and that is one word in
    two notations — ``stress_only`` already decides so for the rungs.  The map
    exists only for the miss path, so a glossary is walked this way once per
    process and never for a word the ordinary lookup already answered.
    """
    out: dict[str, list[str]] = {}
    for word in data.lexicon_index(lang):
        bare = _skeleton(word)
        if bare:
            out.setdefault(bare, []).append(word)
    return out


def _skeleton(form: str) -> str:
    """A form's letters with every combining stress mark taken off."""
    text = unicodedata.normalize("NFD", str(form or ""))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()


def _same_boundness(a: str, b: str) -> bool:
    """Whether two spellings are both bound (*-nós*) or both free (*nós*)."""
    return ((a[:1] == "-") == (b[:1] == "-")) and ((a[-1:] == "-") == (b[-1:] == "-"))


@lru_cache(maxsize=None)
def _has_glossary(stage: str) -> bool:
    """Whether this model holds any entry for ``stage`` at all.

    The model describes the stages it has a glossary for.  Proto-Italic and
    Proto-Hellenic sit in Latin's and Greek's chains without one, and a rung
    there is a form the literature quotes, not a word this model can look up —
    so the page must not read the silence as "no entry" (2026-11-13).
    """
    try:
        return bool(data.lexicon_index(stage))
    except Exception:
        return False


def _lemma_entry(lang: str, form: str) -> dict | None:
    """The glossary entry a form names, comparing lemmas without notation."""
    key = normalise_etymon(form)
    if not key:
        return None
    # A record that names the two stems of one ablauting noun writes them
    # together: "*h₂ṓp-s ~ *h₂ép-s" is *one* word, and looking up the joined
    # string found nothing — so the page said "no entry" for a word the record
    # names, and the band inherited the hole (admin, 2026-11-13, Persian آبجو).
    if "~" in form:
        for variant in form.split("~"):
            found = _lemma_entry(lang, variant.strip())
            if found is not None:
                return found
    record = _lemma_index(lang).get(key) or _lemma_index(lang).get(key.casefold())
    if record:
        return record
    # The engine writes stress as a token before the syllable (Hnˈawa) and a
    # dictionary writes it as an acute on the vowel (Hnáwa, headed hnáwa) or
    # not at all (naht).  The token is notation, so an ancestor spelled with it
    # is the same headword — and a rung that missed this said "no entry for
    # this word" under a form whose page showed a meaning (admin, 2026-11-12).
    for spelled in (printable_form(form), form.replace("ˈ", "").replace("ˌ", "")):
        if not spelled or spelled == form:
            continue
        rows = word_index().get((lang, spelled))
        if rows:
            return rows[0]
    # A record may write a reconstructed form with its morpheme boundaries
    # (*tr̥s-nó-s), while the glossary heads the word solid (*tr̥snós).  A
    # hyphen there is the record's notation, not a sound, and a page that says
    # "no entry for this word" beside a link that opens the entry is simply
    # wrong (admin, 2026-11-12, Persian تشنه).  Only a reconstructed spelling
    # is joined this way: in an attested language a hyphen can belong to the
    # headword itself (English well-being is not wellbeing).
    bare = form.strip("*").strip()
    if (len(bare) >= 3 and "-" in bare[1:-1]
            and ("*" in form or kind_of(lang) == "proto")):
        joined = detokenize(tokenize(form))
        for candidate in (joined, printable_form(joined)):
            other = normalise_etymon(candidate)
            if other and other != key:
                record = (_lemma_index(lang).get(other)
                          or _lemma_index(lang).get(other.casefold()))
                if record:
                    return record
            # The lemma index is keyed in lower case, so a headword the record
            # writes with a capital (*HréwdH-ti → HréwdHti) was found nowhere
            # and the rung said "no entry for this word" beside the entry.
            rows = word_index().get((lang, candidate))
            if rows:
                return rows[0]
    # One word, two notations of stress: a record that writes no accent
    # names the headword that carries one (*h₂m̥bʰi → h₂m̥bʰí).  Only that
    # difference is forgiven (``stress_only``), and a bound spelling answers
    # only a bound headword, so *-nós* never becomes the free *nós*.
    bare = _skeleton(key)
    if bare and kind_of(lang) == "proto":
        for head in _stressless_index(lang).get(bare, ())[:16]:
            if not _same_boundness(form, head):
                continue
            if not stress_only(printable_form(form), head):
                continue
            record = _lemma_index(lang).get(normalise_etymon(head))
            if record:
                return record
    return None


def _headword_at(lang: str, form: str) -> dict | None:
    """The glossary entry a derived form names, reading the notation as notation.

    The engine writes stress as ``ˈ`` before the syllable; a dictionary writes
    it as an acute on the vowel (``jráyah``) or leaves it unmarked (``naht``).
    Four spellings are therefore tried — the form, its printed form, and both
    without the stress token — and nothing else is dropped, so length and every
    other mark still have to agree. Without this a gold proto-form looked like
    a form no glossary held (2026-11-08).
    """
    keys: list[str] = []
    for candidate in (form, printable_form(form)):
        for key in (candidate, candidate.replace("ˈ", "").replace("ˌ", "")):
            if key and key not in keys:
                keys.append(key)
    for key in keys:
        record = _lemma_entry(lang, key)
        if record:
            return record
        rows = word_index().get((lang, key))
        if rows:
            return rows[0]
    return None


#: A word the entry says is built from other words: "From astro- + -naut",
#: "Compound of south + Australia", "Blend of motor + hotel".  Only the
#: pieces that are headwords of the same language are kept, so a sentence
#: that mentions a foreign word or a gloss is never turned into a construction
#: (2026-11-09).
_COMPOUND_CUE_RE = re.compile(
    r"\b(?:[Ff]rom|[Cc]ompound of|[Cc]ompounded of|[Cc]ompound from|[Bb]lend of|"
    r"[Ss]hort for|[Cc]ontraction of|[Dd]erived from|[Ee]quivalent to|[Ff]ormed from|"
    r"[Ff]ormed as|[Bb]uilt from|[Bb]y surface analysis,?|[Ss]urface analysis of|"
    r"[Ss]urface etymology of|[Cc]oined based on|[Mm]ade of)\s+([^.;]{3,90})")


def _piece_name(piece: str) -> str:
    """The bare form of a compound piece, without the gloss the dictionary adds.

    Wiktextract keeps a piece's gloss inside the construction sentence
    (``sesqui- (“one and a half”) + pedalian (“of the foot”)``,
    ``ab- (prefix from Latin ab (“from”)) + irritant, from French irritant``).
    The piece is the word before that gloss, so the lookup takes the text up to
    the first parenthesis or comma.  Nothing is guessed: what remains still has
    to be a headword of this language (2026-11-09).
    """
    piece = re.split(r"\s+\(|,", piece.strip())[0]
    return _STAGE_KEY.sub("", piece.strip(" .,;:()"))


@lru_cache(maxsize=1)
def _language_names_lower() -> tuple[str, ...]:
    """Every language name the data knows, longest first (for prefix matching)."""
    names = {str(meta.get("name", "")).lower() for meta in data.languages().values()}
    try:
        raw = json.loads((data.ROOT / "data" / "language_names.json").read_text(encoding="utf-8"))
        names.update(str(v.get("name", "")).lower() for v in raw.get("languages", {}).values())
    except Exception:
        pass
    names.update(("latin", "greek", "arabic", "french", "old french", "middle english",
                  "old english", "german", "old high german", "sanskrit", "avestan"))
    names.discard("")
    return tuple(sorted(names, key=len, reverse=True))


def _names_another_language(text: str, lang: str) -> bool:
    """Whether a construction sentence starts by naming a language other than this one."""
    lowered = text.lower()
    own = str(_lang(lang).get("name", "")).lower()
    return any(lowered.startswith(name + " ") or lowered.startswith(name + ",")
               for name in _language_names_lower() if name != own)


def _compound_pieces(entry: dict, lang: str) -> list[dict]:
    """The pieces a word states it is built from, each with its own origin.

    A compound is not one etymology but several: ``astronaut`` joins a Greek
    first element to a Greek second element, and ``blackbird`` joins two
    English words that reached the language by different paths.  The timeline
    can only draw that join if the pieces are real words, so a piece is kept
    only when the same language's glossary records it (``astronaut``'s
    ``astro-`` is the entry ``astro-``).  Nothing is guessed: no headword, no
    piece, and the sentence stays beside the row as the record says it.
    """
    text = str(entry.get("etym") or "")
    word = str(entry.get("word") or "")
    if " + " not in text or not word:
        return []
    index = _lemma_index(lang)
    for match in _COMPOUND_CUE_RE.finditer(text):
        chunk = match.group(1).strip()
        # "From Latin focus + -alis" describes a Latin formation, not an
        # English one.  When the sentence names another language first, the
        # pieces are that language's words and must not be read against this
        # one's headwords (2026-11-09).
        if _names_another_language(chunk, lang):
            continue
        raw = re.split(r"\s+\+\s+", chunk)
        if len(raw) < 2 or len(raw) > 4:
            continue
        found: list[tuple[str, dict]] = []
        for piece in raw:
            piece = piece.strip(" .,;:")
            bare = _piece_name(piece)
            if not bare:
                found = []
                break
            # The record's own parenthesis decides between homonyms — «مال
            # (mâl-)» is a verb stem, «باش (… stem form of بودن)» the present
            # stem of بودن — so the piece is resolved by `_piece_entry`, and
            # the plain index is the fallback (critic batches 02-03, 2026-11-13).
            record = (_piece_entry(lang, bare, "", text,
                                   " ".join(str(g) for g in entry.get("gloss") or ()))
                      or index.get(normalise_etymon(bare)))
            if record is None:
                # The glossary may head the same morpheme without the hyphen
                # the sentence writes (*-craft* / craft).  Only an affix entry
                # may be found that way: stripping a hyphen from ``-en`` would
                # otherwise land on the letter *en*, which is a different word
                # and a false join (2026-11-09).
                for key in (bare.strip("-"), piece.strip("-"), piece.rstrip("-")):
                    other = index.get(normalise_etymon(key)) if key else None
                    if other and str(other.get("pos") or "") in (
                            "prefix", "suffix", "infix", "interfix"):
                        record = other
                        break
            if record is None:
                found = []
                break
            # The piece without its gloss is what the sentence names and what
            # the page shows ("-en", not "-en (compare …)").
            found.append((bare, record))
        if len(found) < 2:
            continue
        rows = []
        for piece, record in found:
            chain = _ancestry_forms(record)
            chain.reverse()          # oldest first, as a timeline reads
            rows.append({
                "form": piece,
                "word": record["word"],
                "lang": lang,
                "gloss": (record.get("gloss") or [""])[0],
                "pos": record.get("pos", ""),
                "etymon": _pie_form(record),
                "ancestry": [{"lang": a["lang"], "lang_name": a["lang_name"],
                              "branch": _lang(a["lang"]).get("branch", ""),
                              "form": a["form"]} for a in chain[:12]],
            })
        return [{"pieces": rows, "etym": match.group(0).strip()}]
    return []


# ------------------------------------------------------------- ablaut (grade)
#: The vowels that carry ablaut, and the sonorants that can lose it and become
#: the syllable instead (*-er- > *-r̥-).  Gradation is morphology: a law changes
#: sounds between two stages, a grade is the shape a morpheme takes inside one
#: formation (2026-11-12).
_ABLAUT_VOWELS = frozenset("aeiouāēīōáéíóúā́ḗṓǖ")
_SONORANTS = frozenset(("r", "l", "m", "n", "w", "y"))
_SYLLABIC = {c + "\u0325" for c in ("r", "l", "m", "n")}
_RING = "\u0325"


def _bare_vowel(token: str) -> str:
    """A vowel without its accent: *é and *e are one grade, *ḗ is another."""
    return "".join(ch for ch in unicodedata.normalize("NFD", token)
                   if ch not in "\u0300\u0301\u0304\u0306\u0308")


def _grade_tokens(form: str) -> list[str]:
    """The segments of a morpheme, without the accent marks that sit between."""
    text = normalise_etymon(str(form or ""))
    return [t for t in tokenize(text) if t not in ("ˈ", "ˌ")]


def _nucleus(tokens: list[str]) -> int:
    """Index of the first syllable of a morpheme — a vowel, or a syllabic
    sonorant, because *n̥bʰrós has no vowel in its root at all."""
    for index, token in enumerate(tokens):
        if token in _ABLAUT_VOWELS or token in _SYLLABIC:
            return index
    return -1


@lru_cache(maxsize=None)
def _grades(lang: str) -> tuple:
    """The formation types whose root grade the handbooks fix."""
    path = data.DATA / "morphology" / f"{lang}.yaml"
    if not path.exists():
        return ()
    raw = data._load_yaml(path) or {}
    return tuple(raw.get("grades") or ())


def _suffix_pattern(suffix: str) -> list[str]:
    return [_bare_vowel(t) if t in _ABLAUT_VOWELS else t
            for t in _grade_tokens(suffix)]


def _grade_of_suffix(suffix: str, lang: str = "ine-pro") -> dict | None:
    """What the handbooks say about the root of a formation in this suffix.

    The pattern is the suffix's own opening segments with its vowel stripped of
    the accent (*-tó- and *-to- are one entry), so *-tós and *-tó- match the
    same row while *-tis does not: the vowel of the type is part of the type.
    """
    pattern = _suffix_pattern(suffix)
    if not pattern:
        return None
    for row in _grades(lang):
        want = _suffix_pattern(row.get("suffix") or "")
        if want and len(pattern) >= len(want) and pattern[:len(want)] == want:
            return row
    return None


def root_grade(base: str, word: str, suffixes: Iterable[str] = "",
               lang: str = "ine-pro") -> dict | None:
    """How the root's vowel stands in the formation that builds *word*.

    Observed from the two forms, and explained only when the suffix is one whose
    grade the handbooks state: *ters- + *-tó- gives *tr̥s-tó-s in zero grade
    (*mer- + *-tó- > *mr̥-tó-s, *kʷer- + *-tó- > *kʷr̥-tó-), while *-éye- is the
    o-grade causative (*tors-éye-ti).  A root of the shape *CeR loses the vowel
    and its sonorant becomes the syllable, which is why the *e* of *ters- is an
    *r̥* in *tr̥s-nó-s and still an *e* in the root-accented *térs-e-tor: the
    grade belongs to the formation, not to the suffix (2026-11-12).
    """
    base_tokens = _grade_tokens(base)
    word_tokens = _grade_tokens(word)
    if not base_tokens or not word_tokens:
        return None
    index = _nucleus(base_tokens)
    if index < 0:
        return None
    before, after = base_tokens[:index], base_tokens[index + 1:]
    seen = ""
    # Zero grade: the root's vowel is gone and the sonorant beside it is the
    # syllable.  The sonorant may stand before the vowel (*nebʰ- > *n̥bʰrós) or
    # after it (*ters- > *tr̥s-), and either way it wears the ring below.
    if before and before[-1] in _SONORANTS:
        head = before[:-1]
        if (word_tokens[:len(head)] == head
                and word_tokens[len(head):len(head) + 1] == [before[-1] + _RING]):
            seen = "zero"
    if not seen and after and after[0] in _SONORANTS:
        if (word_tokens[:len(before)] == before
                and word_tokens[len(before):len(before) + 1] == [after[0] + _RING]):
            seen = "zero"
    if not seen:
        word_index = _nucleus(word_tokens)
        if word_index < 0:
            return None
        have, want = _bare_vowel(word_tokens[word_index]), _bare_vowel(base_tokens[index])
        if have == want:
            return None                      # full grade: nothing to explain
        if have in ("ē", "ō", "ā") and want in "eoa":
            seen = "lengthened"
        elif have == "o":
            seen = "o"
        elif have == "e":
            seen = "e"
        else:
            return None
    if isinstance(suffixes, str):
        suffixes = [suffixes] if suffixes else []
    for suffix in suffixes or []:
        row = _grade_of_suffix(str(suffix), lang)
        if row is None:
            continue
        if str(row.get("grade") or "") != seen:
            continue                         # the type does not claim this grade
        return {"grade": seen, "suffix": str(suffix),
                "label": _GRADE_LABELS[seen],
                "note": str(row.get("note") or "").strip(),
                "sources": list(row.get("sources") or [])}
    return None


def _grade_stem(stem: str, grade: str) -> str:
    """The stem in the grade a formation takes it in.

    The observer above reads a grade off two forms; this writes it, so a word
    the page builds can stand in the grade its suffix asks for.  Zero grade of
    a root in *-CeR- loses the vowel and the sonorant becomes the syllable
    (*ters- → *tr̥s-, *gʷʰer- → *gʷʰr̥-), and of a root that opens with one the
    sonorant is the syllable before the consonant (*nebʰ- → *n̥bʰ-); the
    o-grade puts *o where the vowel stood (*ters- → *tors-).  A stem already in
    that grade, or one with no vowel of its own (*h₂wl̥p-), is returned as it
    stands (2026-11-12).
    """
    tokens = _grade_tokens(stem)
    index = _nucleus(tokens)
    if index < 0 or tokens[index] in _SYLLABIC:
        return stem
    if grade == "o":
        return detokenize(tokens[:index] + ["o"] + tokens[index + 1:])
    if grade != "zero":
        return stem
    after = tokens[index + 1] if index + 1 < len(tokens) else ""
    before = tokens[index - 1] if index else ""
    # A diphthong's zero grade is its vocalic second element: *-ey- and *-oy-
    # become *-i-, *-ew- and *-ow- become *-u- (*leykʷ- → *likʷ-, *dewk- →
    # *duk-, *ḱweyt- → *ḱwit-).  Read as "the vowel is not beside a sonorant",
    # these roots lost the vowel and kept a glide that is not a syllable at all
    # (*l̥ykʷ-, *wkʷ-), which no record writes (2026-11-13).
    if after in ("y", "w"):
        return detokenize(tokens[:index] + ["i" if after == "y" else "u"]
                          + tokens[index + 2:])
    if after in ("r", "l", "m", "n"):
        return detokenize(tokens[:index] + [after + _RING] + tokens[index + 2:])
    if before in ("r", "l", "m", "n"):
        return detokenize(tokens[:index - 1] + [before + _RING] + tokens[index + 1:])
    # A glide that opened the syllable becomes the vowel when the root loses
    # its own: *wekʷ- → *ukʷ-, *yeḱ- → *iḱ- (*ukʷ-tó-s is the word the record
    # writes).
    if before in ("w", "y"):
        return detokenize(tokens[:index - 1] + ["u" if before == "w" else "i"]
                          + tokens[index + 1:])
    # A root whose vowel is not beside a sonorant simply loses it.
    return detokenize(tokens[:index] + tokens[index + 1:])


def _formation_grade(stem: str, suffix: str, lang: str = "ine-pro") -> tuple[str, dict | None]:
    """The stem as the suffix's formation takes it, with the reason.

    Only a grade the handbooks state is applied: a suffix the table does not
    name (*-ó-, *-ti-, *-ró-) leaves the stem exactly as the reader typed it,
    because a guess dressed as morphology is worse than no note (2026-11-12).
    """
    row = _grade_of_suffix(suffix, lang)
    if not row:
        return stem, None
    want = str(row.get("grade") or "")
    if want not in ("zero", "o"):
        return stem, None
    changed = _grade_stem(stem, want)
    if changed == stem:
        return stem, None
    return changed, {
        "grade": want,
        "label": {"zero": "zero grade", "o": "o-grade"}[want],
        "note": str(row.get("note") or "").strip(),
        "sources": list(row.get("sources") or []),
    }


def _rung_gloss(glosses: Iterable[str], limit: int = 110) -> str:
    """The first dictionary sense, short enough to sit on a rung."""
    text = next((g.strip() for g in glosses if g and g.strip()), "")
    # Some rows were extracted with the dictionary's own colon still on the
    # sense (": type, form, lineage").  It is punctuation of the source, not of
    # the meaning, and it is dropped rather than printed under a word.
    text = text.lstrip(": ").strip()
    note = _GLOSS_NOTE.search(text)
    if note and note.start() > 0:
        text = text[:note.start()].strip()
    elif note:
        return ""
    # Dehkhoda separates one sense from the next with a spaced full stop, and a
    # bound piece inherits the whole run ("to touch and rub … . (Nāzem
    # al-Atebbā)…").  The first sense is the meaning; the rest is a dictionary's
    # own apparatus (2026-11-13, دستمال's مال).
    if " . " in text:
        text = text.split(" . ", 1)[0].strip()
    if len(text) > limit:
        # Cut at a clause, never mid-word: نشیب's rung ended at «کردی :»
        # (critic batch 07, 2026-11-13).
        cut = max(text.rfind("،", 0, limit), text.rfind(" ", 0, limit))
        text = (text[:cut] if cut > limit // 2 else text[:limit]).rstrip(" ,;:-،") + "…"
    return text


def _morph_gloss(form: str, lang: str = "ine-pro") -> str:
    """What a bound morpheme does, from the row written for it by hand.

    The piece in a recorded construction is written as the word spells it —
    *-nó-s, the suffix plus the ending the row brings — while the table stores
    the morpheme alone (-nó-, ending -s).  Both are the same claim, so the
    ending is added before the comparison instead of the suffix being guessed.
    """
    wanted = _piece_spelling(str(form or "")).lstrip("*-\u2011\u0640")
    if not wanted:
        return ""
    for row in _curated_suffixes(lang):
        bare = _piece_spelling(str(row.get("form") or "")).lstrip("*-\u2011\u0640")
        if not bare:
            continue
        ending = str(row.get("ending") or "").lstrip("*")
        if wanted in (bare, bare.rstrip("-") + ending):
            return str(row.get("gloss") or "").strip()
    return ""


def _formed_from(entry: dict) -> set[tuple[str, str]]:
    """The ancestor a word is *derived* from rather than inherited from.

    A dictionary may record that a word is its ancestor **plus a suffix**
    (Persian گربه is Proto-Iranian *wr̥pa-ka-, i.e. PIE *h₂wl̥pís + the animal
    suffix *-ka-). No sound law may add a suffix, so such a link is not a
    candidate starting point for the rules: they would have to invent the
    syllable. The record is kept, the rung still quotes it, and the ladder says
    why it begins lower down (2026-11-08, de Vaan 2000 on the animal suffix).
    """
    formed = entry.get("formed") or {}
    out: set[tuple[str, str]] = set()
    for stage, word in (formed.get("from") or []):
        out.add((stage, normalise_etymon(word)))
    return out




def _is_root_etymon(stage: str, form: str) -> bool:
    """Whether a cognate-set etymon is a bare root rather than a word.

    The dictionary stores a root as its own headword with the part of speech
    ``root``, and writes it with a trailing hyphen (``*sewh₁-``). Both are
    records of the same fact, and neither is a form a word was inherited from:
    a root carries no derivational morphology, so a ladder that starts there
    cannot produce a suffixed word (2026-11-09, proposals/010).
    """
    if not form:
        return False
    if str(form).strip().endswith("-"):
        return True
    row = _lemma_entry(stage, form)
    return bool(row) and str(row.get("pos") or "").lower() == "root"


def _etymon_record(stage: str, form: str) -> dict | None:
    """The glossary's own entry for a cognate-set etymon, without invention."""
    row = _lemma_entry(stage, normalise_etymon(form))
    if not row:
        return None
    return {"w": normalise_etymon(row.get("word") or form),
            "pos": str(row.get("pos") or ""),
            "gloss": _rung_gloss(row.get("gloss") or [])}


_BRANCH_DEPTH = 8


# How many constructions deep a timeline may nest: a word may be built from
# words that were themselves built, and the page keeps going up until the
# record stops — but a row that states a word in terms of itself must not.
_BUILD_DEPTH = 3


def _origin_node(lang: str, form: str, rel: str = "", depth: int = 0,
                 seen: frozenset = frozenset(), build_depth: int = 0,
                 hint: str = "", quoted: tuple = (),
                 given: dict | None = None) -> dict:
    """One word on a construction piece's own timeline (admin, 2026-11-12).

    A construction is not a line under the word: its pieces are words with
    histories of their own, and the page draws each one climbing upward until
    the trail ends.  It ends in one of four honest ways, and the page says
    which:

    * ``pie`` — the word is Proto-Indo-European, the top of the family;
    * ``outside`` — the word belongs to a language outside the family, so the
      trail begins there and nothing above it is missing;
    * ``borrowed`` — the record says the piece was borrowed from this word, so
      the donor's own history belongs to the donor, not to this word;
    * ``end`` — the word is recorded but no origin is, so a ``???`` stands
      above it;
    * ``missing`` — the record names a form the glossary has no entry for, and
      the node itself is the ``???``: the origin is unexplained.

    Nothing is invented on the way: every row is an ancestor the piece's own
    entry states, and a walk that would revisit a form stops there.

    A node also carries the construction the record states for *it* (``builds``,
    ``built_as``) when it has one: *kit-ró-s is *keyt- + *-rós, and a page that
    showed only the word would be hiding the step that made it (admin,
    2026-11-12: keep going up).  A built form has no single ancestor walk, so
    its construction replaces the parents it would otherwise climb to.

    ``quoted`` is the origin the *quoting* record states for this piece, when
    the piece's own entry states none: Persian رضاقلی says it is a compound of
    رضا + Old Anatolian Turkish قلی, so that piece is a borrowing even though
    the fa entry for قلی records no origin at all — and a borrowing ends its
    trail at the donor rather than at a ``???`` (admin, 2026-11-13: قلی is
    obviously a borrowing, so the question marks should never have been there).
    """
    row = _lang(lang)
    # ``hint`` is the meaning the child's own sentence quotes for this form:
    # the two PIE roots spelled *swer- are told apart by it (2026-11-12).
    entry = given if given is not None else _sense_entry(lang, form, hint)
    # A language outside the family — Arabic, Turkish, Old Anatolian Turkish —
    # has no Indo-European trail to trace and no glossary of its own in this
    # model.  The page says "non-PIE word" for it instead of "no entry", which
    # would claim the word is missing when it is only outside what is modelled
    # (admin, 2026-11-13).
    outside = lang in data.non_ie_sources()
    node = {
        "lang": lang,
        "lang_name": row.get("name", lang),
        "short": row.get("short", row.get("name", lang)),
        "form": form,
        "rel": rel,
        "known": bool(entry),
        "outside": outside,
        "era_label": era_label(row.get("era")),
        "branch": row.get("branch", ""),
        # Whether the language is attested or reconstructed: the tree prints the
        # piece in the same colour the timeline prints a form, so the page needs
        # the same fact here (2026-11-12).
        "kind": row.get("kind", "") or kind_of(lang),
        "gloss": _rung_gloss(entry.get("gloss") or []) if entry else "",
        # The category travels with the meaning: a rung says `adj “visible”`
        # the way the word's own page says `name · “a male given name”`
        # (admin, 2026-11-12).
        "pos": str(entry.get("pos") or "") if entry else "",
        "reading": "",
        "terminal": "",
        "parents": [],
    }
    if entry and _in_native_script(lang, form):
        node["reading"] = (readings_for(entry).get("reading") or "").strip()
    # The word's own construction, if the record states one at its stage.  Only
    # the record's rows are read here: the seam reader's guess belongs to the
    # page the word has, not to a row of someone else's branch.
    if entry and build_depth < _BUILD_DEPTH:
        stated = _rung_builds(entry, data.stage_of(lang), form,
                              record_only=True, build_depth=build_depth + 1)
        if stated:
            node["builds"] = stated
            node["built_as"] = stated[0]
    if rel == "borrow":
        node["terminal"] = "borrowed"
        return node
    if outside:
        # A word of a language outside the family — Arabic, Turkish, a Semitic
        # proto-form — starts its own trail: the family tree above it is not
        # unknown, it does not exist.  A ??? there would claim a missing
        # ancestry the model never had a place for (admin, 2026-11-12: the ???
        # is for a descendant of Proto-Indo-European whose origin is not
        # recorded).
        node["terminal"] = "outside"
        return node
    if lang == "ine-pro":
        # Proto-Indo-European is the top of the family, so a PIE form ends the
        # trail whether or not a glossary entry happens to hold it: there is
        # nothing above it to explain (2026-11-12).
        node["terminal"] = "pie"
        return node
    if not entry:
        node["terminal"] = "missing"
        return node
    if node.get("builds"):
        # The construction is the step that made this form: it is what stands
        # above the word, so the walk does not invent a single parent instead.
        return node
    if depth >= _BRANCH_DEPTH:
        return node
    # One word above, not nine.  An entry may list several rows that are
    # alternatives ("non- … non … nān … *nainaz …"), not a fan of real
    # ancestors; a timeline climbs by the record's own inheritance first, then
    # the borrowing, then the derivation (2026-11-12).  A root is a relation,
    # not an ancestor (see `_is_root_form`), so it is never the step above.
    rows = [t for t in _ancestry_triples(entry) if (t[0], t[1]) not in seen]
    if not rows and quoted:
        # A piece's own entry may say nothing while the record that quotes it
        # says where it came from.  The entry's own rows win when it has them:
        # a compound's sentence must not overrule the piece's own article.
        rows = [tuple(t) for t in quoted if tuple(t)[:2] not in seen]
    chosen = None
    if rows:
        # **The nearest recorded stage is the parent** (admin, 2026-11-13:
        # "The timeline for a word should appear more-or-less exactly the same
        # if another page refers to it" — fa جو showed Middle Persian jaw on its
        # own page and lost it as a piece of آبجو).  The relation preference
        # below exists to choose between *alternatives at one level* ("non …
        # nān … *nainaz"), and it used to reach past a nearer derivation to a
        # farther inheritance: Wiktionary writes the Persian ← Middle Persian
        # link with `{{der}}` and the rest with `{{inh}}`, so jaw was skipped and
        # the piece climbed from Old Persian.  Distance along the word's own
        # chain decides first, relation only breaks the tie.
        chain = data.derivation_chain(lang)
        def _distance(row: tuple) -> int:
            stage = data.stage_of(row[0]) or row[0]
            return chain.index(stage) if stage in chain else -1
        # **A loan is the word's origin, not a rung of the family ladder.**  The
        # record lists its nearest ancestor first, so when that row is a
        # borrowing from a language outside this word's chain the word came from
        # there and the climb ends at the donor: peo *farnah is Old Median
        # *farnah (a loan), and distance-first picked Proto-Iranian *huHarnáh
        # instead, which is the *donor's* ancestry, not this word's (critic
        # batch 02, 2026-11-13).  Inside the family the distance rule stands.
        lead = rows[0]
        borrow_rels = ("borrow", "borrowed", "lbor", "slbor", "obor", "ubor",
                       "calque")
        lead_outside = _distance(lead) < 0 and lead[2] in borrow_rels
        if lead_outside:
            chosen = lead
        best = max(_distance(t) for t in rows)
        nearest = [t for t in rows if _distance(t) == best]
        if chosen is None:
            for rel_kind in ("inherit", "borrow", "derived"):
                chosen = next((t for t in nearest if t[2] == rel_kind), None)
                if chosen:
                    break
        chosen = chosen or nearest[0]
    if chosen is None:
        node["terminal"] = "end"
        return node
    p_lang, p_form, p_rel = chosen
    parent = _origin_node(p_lang, p_form, p_rel, depth + 1,
                          seen | {(p_lang, p_form)}, build_depth=build_depth + 1,
                          hint=_ancestor_gloss(entry, p_form))
    # A construction of the ancestor may be stated in *this* entry, not in the
    # ancestor's own: Wiktionary writes *kit-ró-s = *keyt- + *-rós in its
    # article on *čitrás, and that page has no article of its own.  The row is
    # about the ancestor's stage and form, which is what `_rung_builds` reads,
    # so the parent node keeps the step that made it — otherwise the page
    # hides a construction its own branch climbs through (admin, 2026-11-12:
    # keep going up, all of it, on the word's page).
    if build_depth < _BUILD_DEPTH and not parent.get("builds"):
        carried = _rung_builds(entry, data.stage_of(p_lang), p_form,
                               record_only=True, build_depth=build_depth + 2)
        if carried:
            parent["builds"] = carried
            parent["built_as"] = carried[0]
            # The construction is what explains the form: no single parent may
            # stand in its place, and the form is not a ??? any more.
            parent["parents"] = []
            if parent.get("terminal") == "missing":
                parent["terminal"] = ""
    # **A form brings its whole timeline with it** (admin, 2026-11-13, fa
    # ناراضی: "Every form that is brought into a timeline brings its entire
    # timeline with it above it, right?").  The record may name only a
    # Proto-Indo-Iranian ancestor while the word's own page draws every stage
    # between it and the word, because the cited laws carry the form down.  A
    # piece drawn from that same record must show the same rungs, so the chain
    # between the parent and this word is filled with the forms the laws
    # produce — marked `derived`, never presented as recorded.
    node["parents"] = _chain_between(lang, parent, data.derivation_chain(lang))
    return node


def _chain_between(lang: str, parent: dict, chain: list[str]) -> list[dict]:
    """The recorded parent, wrapped in the rungs the laws reach it through.

    A word's ladder runs one rung per stage of its chain, deriving each form
    from the one above (`hierarchy`), so fa ناـ's own page prints Proto-Indo-
    European *né → Proto-Indo-Iranian *ná → Proto-Iranian → Old Persian →
    Middle Persian.  A construction piece climbed only the *recorded* rows and
    therefore started at Proto-Indo-Iranian, which made the same word look
    shorter wherever another page quoted it (admin, 2026-11-13).

    The rungs added here carry `derived: True` and no entry: they are the
    model's own derivation, drawn in the ladder's "derived" colour, and they
    are never counted as a hole (`_unexplained_branch` walks past them).
    """
    p_stage = data.stage_of(str(parent.get("lang") or "")) or str(parent.get("lang") or "")
    own = data.stage_of(lang) or lang
    if p_stage not in chain or own not in chain:
        return [parent]
    first, last = chain.index(p_stage), chain.index(own)
    if last - first < 2:
        return [parent]
    stages = [p_stage] + [s for s in chain[first + 1:last + 1]]
    try:
        forms = list(derive_detailed(str(parent.get("form") or ""), stages,
                                     data.rulesets())[0].forms)
    except Exception:
        return [parent]
    if len(forms) != len(stages):
        return [parent]
    rungs: list[dict] = []
    # The last rung of `stages` is the word itself: the piece already stands
    # there in the form the record writes, so only the stages between it and
    # the parent are added.
    for index in range(len(stages) - 2, 0, -1):
        stage = stages[index]
        row = _lang(stage)
        rung = {
            "lang": stage,
            "lang_name": row.get("name", stage),
            "short": row.get("short", row.get("name", stage)),
            "form": str(forms[index] or ""),
            "rel": "",
            "known": False,
            "era_label": era_label(row.get("era")),
            "branch": row.get("branch", ""),
            "kind": row.get("kind", "") or kind_of(stage),
            "gloss": "",
            "pos": "",
            "reading": "",
            "terminal": "",
            "parents": [],
            # The ladder's own word for a rung no glossary records: the laws
            # produce this form between two stages the record names.
            "derived": True,
        }
        if rungs:
            rungs[-1]["parents"] = [rung]
        rungs.append(rung)
    rungs[-1]["parents"] = [parent]
    return [rungs[0]]


# A piece of a construction is a word or a morpheme, never a printed
# structure.  A handful of stored rows carry a piece that was written down as
# ``str(['کَم ', '>'])`` by an early reader; a page must not print that as a
# word, and the row it came from says nothing usable (2026-11-12).
_MALFORMED_PIECE = re.compile(r"^\s*[\[({]")

#: The construction kinds that may state a single piece: a word the record says
#: was made from one other word and nothing else.  *h₂entó- is the case — "a
#: combining form or allative formation from … *h₂énts" — and the step that
#: made it *is* its history.  Every other kind is a join, and a one-piece row of
#: another kind is an analysis cut short, not a construction (admin, 2026-11-12).
_SINGLE_PIECE_KINDS = frozenset({"combining", "derivation", "reduplication"})

#: The words the timeline uses for each ablaut grade, in one place: a
#: formation states its grade and the step prints it beside the root.
_GRADE_LABELS = {"zero": "zero grade", "o": "o-grade",
                 "e": "full grade", "lengthened": "lengthened grade"}

#: A record that states a reduplicated formation in words: the sentence names
#: the type ("reduplicated stative of the root", "i-reduplicated present of …")
#: and the root it repeats.  The type's syllable and grade come from the stage's
#: morphology table (`reduplications:`), never from this regex.
_REDUPLICATION_RE = re.compile(
    r"\b(?P<what>"
    r"root\s+or\s+reduplicated\s+root\s+perfect"
    r"|(?:athematic|thematic)\s+(?:[ei]-)?reduplicated\s+"
    r"(?:root\s+aorist|root\s+present|root|present|aorist)"
    r"|reduplicated\s+(?:stative/perfect|stative|perfect|derivative|thematic\s+adjective)"
    r")\s+(?:of|formed\s+to)\s+(?:the\s+root\s+)?"
    r"(?P<root>\*[^\s(“”\",.;:)]+)"
    r"(?:\s*\((?P<gloss>[^)]*)\))?", re.I)

#: Which morphology row each sentence names, matched in this order: the
#: aorist before the i-reduplicated root, because the aorist phrase contains
#: the other's words.
_REDUPLICATION_TYPES = (
    ("stative", "perfect-stative"),
    ("perfect", "perfect-stative"),
    ("aorist", "aorist"),
    ("i-reduplicated", "present-i"),
    ("e-reduplicated", "present-e"),
)


#: Harakat a quoted reading carries and a headword does not (نَامَه / نامه).
_HARAKAT = re.compile(r"[\u064b-\u0652\u0670\u0653-\u0655]")
#: A stage key in front of a form: `fa-cls:روز` is the word روز.
_STAGE_KEY = re.compile(r"^[a-z][a-z0-9-]{1,12}:(?=\S)")


def _piece_spelling(text: str) -> str:
    """A piece as the word is spelled, without the record's notation.

    Three kinds of notation reached the page as if they were spelling (critic
    batch 04, 2026-11-13): a stage key in front of the word (`fa-cls:روز` over
    a glossary that heads روز), the harakat of a quoted reading (`نَامَه`,
    `خِدْمَت`, `غَم`, `ـنَاک`), and the non-breaking hyphen of a suffix (`‑ی`
    for the table's `-ی`, which is why every Persian suffix but ـمند reached
    its row bare).  The word is the same word, so the lookup and the line both
    use its spelling.
    """
    text = str(text or "").strip()
    text = _STAGE_KEY.sub("", text)
    text = _HARAKAT.sub("", text)
    return text.replace("\u2011", "-").replace("\u2010", "-")


def _lookup_form(text: str) -> str:
    """The form a word is looked up by: the spelling without the harakat.

    A record quotes a reading (نَامَه، خِدْمَت، کَم) and the glossary heads the
    word as it is written, so the lookup drops the vowel marks.  The *line*
    keeps what the record prints (critic batch 04, 2026-11-13).
    """
    return _HARAKAT.sub("", _piece_spelling(text))


def _formed_piece(form) -> str:
    """A piece's own form, or ``""`` when the stored value is not one.

    A stage key in front of the piece (`fa-cls:روز`) is notation, not spelling,
    and is dropped; the rest is printed as the record writes it.
    """
    value = form
    while isinstance(value, (list, tuple)) and value:
        value = value[0]
    text = _STAGE_KEY.sub("", str(value or "").strip()).replace("\u2011", "-").replace("\u2010", "-")
    # A scraps of the record's own sentence can land in the slot — رفتار's row
    # stores «رفت رفتن (raftan, “to go”)>».  The piece is the first token, and
    # only when the junk tells us so; a piece is never two Persian words.
    if "(" in text or text.endswith(">"):
        text = re.split(r"\s+\(|>", text)[0].strip()
        text = text.split(" ")[0]
    if not text or _MALFORMED_PIECE.match(text):
        return ""
    return text


def _stated_piece_ancestry(value) -> tuple[tuple[str, str, str], ...]:
    """The origin a construction's own row states for one of its pieces.

    A compound is not always built from the language's own words.  Persian
    رضاقلی is "a compound of رضا + Old Anatolian Turkish قلی": the second piece
    is a word of the donor, and its own fa entry says nothing about where it
    came from — it heads a different homonym.  The row that states the join
    states the piece's origin too, in the third slot of the piece:
    ``["قلی", "the possessed form of قل", [["trk-oat", "قلی", "borrow"]]]``.
    Nothing is read from prose here, and a malformed slot states nothing.
    """
    out: list[tuple[str, str, str]] = []
    for row in value or ():
        if isinstance(row, dict):
            lang = str(row.get("lang") or "")
            form = str(row.get("form") or "")
            rel = str(row.get("rel") or "borrow")
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            lang, form = str(row[0] or ""), str(row[1] or "")
            rel = str(row[2] if len(row) > 2 else "borrow")
        else:
            continue
        if not lang or not form.strip():
            continue
        out.append((lang, form.strip(), rel or "borrow"))
    return tuple(out)


@lru_cache(maxsize=None)
def _verb_stem_index(lang: str) -> dict[str, dict]:
    """Present stems of the ``-idan`` verbs this stage's glossary heads.

    Persian states a compound's verb piece by its present stem and marks it with
    a hyphen — دستمال is "From دست (dast) + مال (mâl-)" — while the glossary
    heads the infinitive مالیدن "to rub".  The piece therefore matched Arabic
    مال "property", and the timeline said the handkerchief was made of wealth
    (admin, 2026-11-13: "the مال is from مالیدن not the Arabic word").

    Only the ``-idan`` class is read: it is the productive one, its stem is the
    infinitive minus ‑یدن, and the other classes (ساختن/ساز, رفتن/رو) are
    irregular enough that a guess would be worse than the homonym.
    """
    out: dict[str, dict] = {}
    try:
        entries = data.lexicon(lang)
    except Exception:
        return out
    for entry in entries:
        if str(entry.get("pos") or "") != "verb":
            continue
        word = str(entry.get("word") or "")
        if word.endswith("یدن") and len(word) > len("یدن") + 1:
            out.setdefault(word[:-len("یدن")], entry)
    return out


_PIECE_HINT_RE = r"\s*\(([^()]{0,60})\)"


#: "present stem form of بودن (budan, “to be”)" — the record naming a verb.
_STEM_OF = re.compile(r"stem\s+(?:form\s+)?of\s+([\u0600-\u06ff\u200c]+)")


def _stem_verb(etym: str, form: str) -> str:
    """The verb whose stem a piece is said to be, or "".

    باشنده's sentence is "From باش (bâš, present stem form of بودن (budan, “to
    be”)) + ـنده", and the parenthesis nests, so the piece's own hint is not a
    single bracket group.  The phrase is read instead: everything the record
    says about this piece up to the next plus sign (critic batch 03, 2026-11-13:
    باش was drawn from the jade homonym, under a red ??? of its own).
    """
    if not etym or not form:
        return ""
    at = etym.find(form + " (")
    if at < 0:
        return ""
    found = _STEM_OF.search(etym[at:at + 200])
    return found.group(1) if found else ""


def _piece_hint(etym: str, form: str) -> str:
    """The parenthetical the record puts after one piece of a construction.

    دستمال's sentence is "From دست (dast) + مال (mâl-)."; the second piece's
    hint is a stem, marked by the trailing hyphen, and that mark is the record's
    own statement that the piece is a verb stem and not a noun homonym.
    """
    if not etym or not form:
        return ""
    match = re.search(re.escape(form) + _PIECE_HINT_RE, etym)
    return match.group(1).strip() if match else ""


def _ancestor_gloss_words(entry: dict) -> set[str]:
    """Content words of the meaning an entry's nearest recorded ancestor has."""
    try:
        for lang, word, rel in _ancestry_triples(entry):
            if rel == "root":
                continue
            other = _lemma_entry(lang, word)
            if other is None:
                continue
            return senses.content_words(" ".join(str(g) for g in other.get("gloss") or ()))
    except Exception:
        pass
    return set()


def _homonym_by_meaning(lang: str, rows: list[dict], child) -> dict | None:
    """The homonym whose meaning the child's own meaning asks for, if any.

    A compound's piece is often the spelling of several words, and no index
    order is evidence: آبرو "face, honour, reputation" is آب + روی "face", not
    روی "bronze", and کمزور "weak" is زور "force, strength", not the slang
    "cool" (critic batch 04, 2026-11-13).  The child's meaning is the only
    thing in the record that can choose, and it chooses only when one candidate
    is strictly closer than the rest.
    """
    wanted = senses.content_words(child or "")
    if len(rows) < 2 or not wanted:
        return None

    def closeness(row):
        own = senses.content_words(" ".join(str(g) for g in row.get("gloss") or ()))
        hits = 0
        for mine in own:
            for their in wanted:
                if mine == their or (len(mine) > 3 and len(their) > 3
                                     and (mine.startswith(their) or their.startswith(mine))):
                    hits += 1
                    break
        return hits

    scored = sorted(((closeness(row), row) for row in rows), key=lambda pair: pair[0],
                    reverse=True)
    if scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
        return scored[0][1]
    return None


def _piece_entry(lang: str, form: str, gloss: str, etym: str = "",
                 child: str = "") -> dict | None:
    """The entry a construction's piece means, not merely the first it heads.

    One spelling heads several words, and a compound's piece is one of them:
    fa دست heads Dehkhoda's classifier "a set or suite of objects" before the
    noun "hand", so دستمال was drawn from a classifier (admin, 2026-11-13).
    Two record facts decide, in this order:

    * the parenthetical the sentence puts after the piece — a trailing hyphen
      means a verb stem, and the stage's own ‑یدن verb supplies the word
      (مال (mâl-) is مالیدن, not Arabic مال);
    * the meaning the piece's own recorded ancestry carries — دست's ancestor
      is Middle Persian dast "hand", which is the noun, not the classifier.

    With neither fact the first entry stands, exactly as before.
    """
    form = _lookup_form(form) or form
    hint = _piece_hint(etym, form)
    if hint.endswith("-"):
        stem = _verb_stem_index(lang).get(form)
        if stem is not None:
            return stem
    named = _stem_verb(etym, form)
    if named:
        verb = _lemma_entry(lang, named)
        if verb is not None:
            return verb
    # A sentence that names the infinitive beside a bare stem — "کش (keš) from
    # کشیدن (kešidan, to pull)" — has said which verb the piece is, without a
    # hyphen or a "stem form of" phrase (critic batch 04: دستکش).
    infinitive = _verb_stem_index(lang).get(form)
    if infinitive is not None and str(infinitive.get("word") or "") in etym:
        return infinitive
    rows = _notation_entries(lang, form)
    if gloss and len(rows) > 1:
        return _sense_entry(lang, form, gloss)
    by_meaning = _homonym_by_meaning(lang, rows, child)
    if by_meaning is not None:
        return by_meaning
    if len(rows) < 2:
        return rows[0] if rows else _lemma_entry(lang, form)
    wanted = _ancestor_gloss_words(rows[0])
    if wanted:
        scored = sorted(
            ((len(wanted & senses.content_words(" ".join(str(g) for g in row.get("gloss") or ()))), row)
             for row in rows), key=lambda pair: pair[0], reverse=True)
        if scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            return scored[0][1]
    return rows[0]


def _suffix_slot(kind: str, index: int, count: int) -> bool:
    """Whether a piece holds the suffix slot of a row the record writes as one.

    گفتار's row is [گفتن, ار] with kind `suffix`, and the parse dropped the
    tatweel that marks the ending, so the piece resolved to the place-name ار
    ("a village of 952 souls") and the pieces spelled گفتنار (critic batch 06,
    2026-11-13).  The row's own kind says the last piece is a morpheme.
    """
    return kind == "suffix" and count > 1 and index == count - 1


def _bound_piece(kind: str, form: str, index: int) -> bool:
    """Whether a piece is a bound morpheme of the stage, not a word.

    A suffix is written with a leading hyphen (``-tós``) or, in Persian, with
    a leading tatweel (``ـدار``); a prefix's hyphen trails it and does not make
    it bound on its own (``astro-`` is the Greek word ἄστρον).  A bound
    morpheme has no history of its own, so the timeline draws it as itself and
    does not hang a ``???`` above it (admin, 2026-11-12).
    """
    if kind not in ("suffix", "affix", "infix") or index == 0:
        return False
    return form.startswith(("-", "ـ", "*-"))


@lru_cache(maxsize=8)
def _reduplication_types(lang: str = "ine-pro") -> tuple[dict, ...]:
    """The reduplicated formations a stage's morphology table records."""
    path = data.DATA / "morphology" / f"{lang}.yaml"
    if not path.exists():
        return ()
    raw = data._load_yaml(path) or {}
    return tuple(raw.get("reduplications") or [])


def _reduplication_type(type_id: str, lang: str = "ine-pro") -> dict | None:
    for row in _reduplication_types(lang):
        if str(row.get("id") or "") == type_id:
            return row
    return None


def _reduplication_read(entry: dict) -> dict | None:
    """A reduplicated formation the entry states in words, if it states one.

    Wiktionary writes these as one sentence — "Reduplicated stative of the root
    *h₂eyḱ- (“to obtain, possess, own”)."  The first sentence only, no hedged
    reading, no arithmetic (a ``+`` means the sentence is a join read
    elsewhere), and the root must stand at the word's beginning.  A sentence
    that offers two analyses ("Root or reduplicated root perfect of *megʰ-") is
    the record's `argued` row, not a guess: it is one of the two the entry
    prints.
    """
    if kind_of(entry.get("lang") or "") != "proto":
        return None
    sentences = _sentences(str(entry.get("etym") or ""))
    if not sentences:
        return None
    sentence = sentences[0]
    if "+" in sentence or _HEDGE_RE.search(sentence):
        return None
    seen = _REDUPLICATION_RE.search(sentence)
    if not seen:
        return None
    # A sentence that opens by naming an ancestor — "From Proto-Indo-European
    # *pe-póyh₂-e ~ *pe-pih₂-ḗr, reduplicated stative of *peyh₂-" — is
    # describing *that ancestor's* formation, not this word's: the chain has
    # crossed a stage boundary before the clause, the same test
    # `_CHAIN_BOUNDARY_RE` makes for an arithmetic.  Proto-Indo-Iranian
    # *pipáyHa descends from PIE *pepóyh₂e; it is not itself a reduplication
    # of *peyh₂- (admin, 2026-11-12).  It climbs to the reduplicated word,
    # whose own page states the construction.
    if _PROSE_ANCESTRY_CUE.match(sentence) and "*" in sentence[:seen.start()]:
        return None
    root = seen.group("root").lstrip("*").strip()
    if not root or not _construction_covers([root],
                                            word=str(entry.get("word") or ""),
                                            sentence=sentence):
        return None
    what = " ".join(seen.group("what").lower().split())
    type_id = ""
    for needle, candidate in _REDUPLICATION_TYPES:
        if needle in what:
            type_id = candidate
            break
    row = _reduplication_type(type_id, entry.get("lang") or ROOT_LANG)
    label = str((row or {}).get("label") or "").strip()
    if not label:
        # No handbook row for this one (a reduplicated derivative or a
        # reduplicated adjective): the entry's own words are the label, minus
        # the "reduplicated" the kind already says.
        label = re.sub(r"^reduplicated\s+", "", what).strip() or what
    return {
        "root": root,
        "gloss": (seen.group("gloss") or "").strip().strip("“”\"'").strip(),
        "type": type_id,
        "formation": label,
        "confidence": ("argued" if _ALTERNATIVE_CUE_RE.search(sentence)
                       else "stated"),
        "sentence": sentence.strip(),
    }


def _reduplication_rows(entry: dict, stage: str) -> list[dict]:
    """The reduplication as a `built_as` row of the entry's own stage."""
    read = _reduplication_read(entry)
    if not read:
        return []
    return [{"lang": stage, "kind": "reduplication",
             "of": str(entry.get("word") or ""),
             "pieces": [[read["root"], read["gloss"]]],
             "reduplication": read["type"],
             "formation": read["formation"],
             "confidence": read["confidence"],
             "note": read["sentence"], "source": "record"}]


def _built_row_names(row: dict, form: str, stage: str) -> bool:
    """Whether a structured row already states this form at this stage."""
    if (data.stage_of(str(row.get("lang") or "")) or "") != stage:
        return False
    of = str(row.get("of") or "")
    return bool(of) and (_same_form(form, of)
                         or _same_form(normalise_etymon(form),
                                       normalise_etymon(of)))


def _rung_builds(entry: dict, stage: str, form: str, record_only: bool = False,
                 build_depth: int = 0) -> list[dict]:
    """The constructions the record states for a form, at its own stage.

    Every row is one analysis the dictionary itself prints: English ``about``
    is stated as ``on + be + out`` *and* as ``on + but``, and a page that kept
    only the first would be silent about the competitor the record also gives
    (2026-11-12, the reader asked for a tab per construction).  ``_rung_built``
    keeps its old name for the first row, so a caller that wants one still
    gets one.

    ``dáwxšati`` is a Proto-Iranian word, but its entry states that its
    Proto-Indo-European ancestor *déwk-s-eti is ``*dewk- + *-seti``. That
    statement belongs on the PIE rung — the rung it is about — not under the
    Proto-Iranian headword, and not in the place of the ladder: the ladder
    starts at the whole form, and the formation explains how the whole form
    came to be (2026-11-09).

    Only a record that names the pieces makes a row; nothing is read out of
    prose here, and a formation whose product cannot be identified is not
    attached to a rung it may not belong to.

    A piece row is ``[form, gloss]``, or ``[form, gloss, origin]`` when the
    sentence that states the join also states where that piece came from: fa
    رضاقلی is a compound of رضا + **Old Anatolian Turkish** قلی, and the third
    slot says so (see `_stated_piece_ancestry`).
    """
    found: list[dict] = []
    seen_rows: set[tuple] = set()
    # A record may state a formation in words instead of as an arithmetic
    # ("Reduplicated stative of the root *h₂eyḱ-"): the reducer below turns
    # such a sentence into the same row shape, and it is read here because the
    # step belongs to the timeline (admin, 2026-11-12: is the reduplicated
    # stative part of the morphology?).  Only when no structured row of the
    # entry already states this form, so one analysis is never drawn twice.
    rows = list(entry.get("built_as") or [])
    if not any(_built_row_names(row, form, stage) for row in rows):
        rows.extend(_reduplication_rows(entry, stage))
    # A template can stop where the sentence goes on: the stored row for
    # *h₂ḱh₂owsyéti names *h₂eḱ- + *h₂ṓws, while its own etymology continues
    # "and + *-yéti (denominative verbal suffix)".  The dictionary's arithmetic
    # is the fuller statement of the same analysis, so a row the sentence
    # states that *starts with* the stored row and adds a piece is read here;
    # the prefix-merge below then keeps the longer one and drops the shorter
    # (admin, 2026-11-13: the suffix was missing from the timeline).
    if rows and str(entry.get("etym") or ""):
        stored = [tuple(normalise_etymon(str(p[0] if isinstance(p, (list, tuple)) else p))
                        for p in (row.get("pieces") or []))
                  for row in rows]
        for stated in _stated_constructions(str(entry.get("etym") or ""), stage,
                                            str(entry.get("word") or ""),
                                            str(entry.get("pos") or "")):
            seq = ([stated["base"]["form"]]
                   + [m["form"] for m in stated.get("members") or []]
                   + [x["form"] for x in stated.get("suffixes") or []])
            forms = tuple(normalise_etymon(str(x)) for x in seq)
            if len(forms) < 2 or not any(
                    len(old) and forms[:len(old)] == old and len(forms) > len(old)
                    for old in stored):
                continue
            rows.append({
                "lang": stage,
                # A row that ends in a bound morpheme is an affix formation
                # (the suffix is drawn as a morpheme, not as a word with no
                # history); a row of words only is a compound.
                "kind": "affix" if stated.get("suffixes") else "compound",
                "of": str(entry.get("word") or ""),
                "pieces": [[stated["base"]["form"], stated["base"].get("gloss") or ""]]
                          + [[m["form"], m.get("gloss") or ""]
                             for m in stated.get("members") or []]
                          + [[x["form"], x.get("gloss") or ""]
                             for x in stated.get("suffixes") or []],
                "confidence": str(stated.get("confidence") or "stated"),
            })
    for row in rows:
        lang = str(row.get("lang") or "")
        if data.stage_of(lang) != stage:
            continue
        of = str(row.get("of") or "")
        if of and not (_same_form(form, of)
                       or _same_form(normalise_etymon(form), normalise_etymon(of))):
            continue
        pieces = []
        kind = str(row.get("kind") or "formation")
        raw = row.get("pieces") or []
        for index, piece_row in enumerate(raw):
            form_piece, gloss = ((piece_row + ["", ""])[:2]
                                 if isinstance(piece_row, (list, tuple))
                                 else (piece_row, ""))
            form_piece = _formed_piece(form_piece)
            if not form_piece:
                continue
            # A piece may carry the origin the row's own sentence states for
            # it, when its entry states none (see `_stated_piece_ancestry`).
            piece_anc = (_stated_piece_ancestry(piece_row[2])
                         if isinstance(piece_row, (list, tuple))
                         and len(piece_row) > 2 else ())
            piece = _piece_entry(lang, form_piece.lstrip("‑ـ"), str(gloss or ""),
                                 str(entry.get("etym") or ""),
                                 " ".join(str(g) for g in entry.get("gloss") or ()))
            # A piece is a word of its own, so the line prints it the way the
            # word page does: the writing, then its reading, when the writing
            # is in a script (2026-11-12: 𐎨𐎡𐏂 čiçaʰ + *farnah).
            reading = ""
            if piece and _in_native_script(lang, form_piece):
                reading = (readings_for(piece).get("reading") or "").strip()
            # A piece the record writes with a trailing hyphen is a **stem**,
            # not a free word (مال (mâl-) in دستمال): it wears no dot and starts
            # no climb of its own, exactly like a bound morpheme, while the
            # entry it resolves to still gives it its meaning (2026-11-13).
            # «present stem form of بودن» names a stem exactly as a trailing
            # hyphen does (باشنده, critic batch 03, 2026-11-13).
            piece_stem = (_piece_hint(str(entry.get("etym") or ""), form_piece).endswith("-")
                          or bool(_stem_verb(str(entry.get("etym") or ""), form_piece)))
            # A piece written as a morpheme (‑دار، *-lom) is not a free word:
            # the entry the lookup finds for «دار» is the noun "tree", which
            # would hang a whole tree above a suffix (critic batch 07; the
            # suite's own bound-morpheme test, 2026-11-13).
            if (str(form_piece).startswith(("-", "ـ", "*-")) and piece
                    and str(piece.get("pos") or "") not in
                    ("suffix", "prefix", "affix", "infix", "interfix")):
                piece = None
            # A suffix slot holds a morpheme even when the parse dropped its
            # tatweel — but only if what the lookup found is not itself an
            # affix entry (PIE *-lom is a suffix with a page of its own).
            slot = (_suffix_slot(kind, index, len(raw))
                    and str((piece or {}).get("pos") or "") not in
                    ("suffix", "prefix", "affix", "infix", "interfix"))
            if slot:
                # گفتار's «ار» found the place-name ار; the row says the slot is
                # an ending, so the morpheme — not that word — is drawn.
                piece = None
            bound = _bound_piece(kind, form_piece, index) or piece_stem or slot
            # The meaning under the word in the timeline (admin, 2026-11-12):
            # the row's own parenthesis when it has one, otherwise the sense
            # the piece's glossary entry gives it.  That fallback is what lets
            # a bound suffix say what it does (*-rós: "forms adjectives from
            # Caland-system roots"), since a suffix row usually carries no
            # parenthesis at all.
            sense = str(gloss or "").strip() or (
                _rung_gloss(piece.get("gloss") or []) if piece else "")
            # A parenthesis that states the relation rather than a meaning —
            # «present stem form of بودن (budan, “to be”)» — is not the word's
            # sense; the entry the piece resolves to has that (critic batch 03,
            # 2026-11-13).
            if piece and sense and _STEM_OF.search(sense):
                sense = _rung_gloss(piece.get("gloss") or []) or sense
            # A bound morpheme is not a word and has no glossary entry: what it
            # does is written in the morphology table, so the timeline takes it
            # from there (*-nó-s: "verbal adjective or passive participle") —
            # otherwise the piece stands under the word with nothing to say
            # (admin, 2026-11-12: every term, suffixes included, says its
            # meaning).
            if bound:
                # A bound morpheme's meaning is the row written for it, not a
                # glossary entry that happens to share its spelling: the entry
                # for ی is the indefinite article, while the piece in خورشیدی
                # is the relational adjective (critic batch 04, 2026-11-13).
                # The row's own example («(خورشید → خورشیدی 'solar')») is
                # written for the table, not for a line under a word.
                sense = _morph_gloss(form_piece, lang).split(" (")[0].strip() or sense
            pieces.append({
                "form": form_piece,
                "gloss": sense,
                "pos": str((piece or {}).get("pos") or ""),
                "reading": reading,
                "known": bool(piece),
                "lang": lang,
                "bound": bound,
                # The piece's own history, upward: the step draws it as a
                # branch of the timeline, not as a footnote (2026-11-12).  A
                # bound morpheme has none: it is not a word that was inherited
                # or borrowed.
                # A stem wears no dot, but it is still a word with a history:
                # باش (the stem of بودن) keeps the ladder that reaches PIE
                # *bʰewH- (critic batch 07, 2026-11-13).  Only a morpheme with
                # no entry of its own has no column.
                "branch": None if (bound and not piece) else _origin_node(lang, form_piece,
                                                          build_depth=build_depth,
                                                          hint=sense or "",
                                                          quoted=piece_anc,
                                                          given=piece),
        })
        # A join is two pieces or more — except a word the record states as
        # *formed from* a single word, which is the whole of its history:
        # *h₂entó- is "a combining form or allative formation from … *h₂énts",
        # and its timeline is that one step, not a bare rung with the step
        # hidden (admin, 2026-11-12).  Only a row whose own kind says so is
        # read this way; a one-piece row of any other kind is a truncated
        # analysis, not a construction.
        if len(pieces) < (1 if kind in _SINGLE_PIECE_KINDS else 2):
            continue
        # The root's grade in this formation, when the handbooks fix it: the
        # step then says why *ters- stands above *tr̥s-tó-s as *e over *r̥ —
        # the accent is on *-tó-, so the root is in zero grade (2026-11-12).
        # Only a root is graded; a compound member is a word of its own, and a
        # bound morpheme has no root to grade.
        lead = pieces[0]
        if not lead["bound"] and lead["pos"] == "root":
            info = root_grade(lead["form"], form,
                              [p["form"] for p in pieces[1:] if p["bound"]])
            if info:
                lead["grade"] = info["grade"]
                lead["grade_label"] = info["label"]
                lead["grade_note"] = info["note"]
        if kind == "reduplication":
            # Reduplication asks the root for a grade the formation carries
            # (the perfect/stative is o-grade, an i-reduplicated present is
            # zero grade) and `root_grade` cannot observe it through the
            # copied syllable: the morphology row states it instead.
            info = _reduplication_type(str(row.get("reduplication") or ""), stage)
            grade = str((info or {}).get("grade") or "")
            if grade in _GRADE_LABELS:
                lead["grade"] = grade
                lead["grade_label"] = _GRADE_LABELS[grade]
                lead["grade_note"] = str((info or {}).get("note") or "").strip()
        # The same analysis may be stored twice (one template run twice); it is
        # one construction, not two tabs.
        key = (str(row.get("kind") or ""), tuple(p["form"] for p in pieces))
        if key in seen_rows:
            continue
        seen_rows.add(key)
        found.append({"kind": str(row.get("kind") or "formation"),
                      "formation": str(row.get("formation") or ""),
                      "confidence": str(row.get("confidence") or "stated"),
                      "lang": lang, "lang_name": _lang(lang).get("name", lang),
                      "of": normalise_etymon(of) if of else "",
                      "pieces": pieces, "source": "record"})
    if len(found) > 1:
        # A record read twice, the second time stopping early, is one
        # construction and not a rival analysis: *sokʷh₂ṓy is stored as
        # *sekʷ- + *-éh₂ and again as *sekʷ- + *-éh₂ + *-ṓy.  The shorter row
        # is a prefix of the longer one, so it is the same analysis, not a tab
        # (admin, 2026-11-12).
        # Compared without notation: the same analysis may spell a piece
        # with the star its row carried (*h₂eḱ-) in one statement and without
        # it in the other (h₂eḱ-).
        sequences = [tuple(normalise_etymon(p["form"]) for p in b["pieces"])
                     for b in found]
        keep = []
        for k, seq in enumerate(sequences):
            if any(k2 != k and (
                       (len(other) > len(seq) and other[:len(seq)] == seq)
                       # The same pieces spelled once with the record's
                       # notation and once without are one analysis too, and
                       # the first row keeps the spelling the record stored
                       # (critic batch 02: *sokʷh₂ṓy drew two identical tabs).
                       or (len(other) == len(seq) and other == seq and k2 < k))
                   for k2, other in enumerate(sequences)):
                continue
            keep.append(found[k])
        found = keep
    if found or record_only:
        return found
    # Nothing in the record: the word may still be made of its own language's
    # words, and an unanalysed headword is exactly the case the seam reader
    # exists for.  The row says `source: ours`, so the page can print "built
    # from" rather than the record's "built as" (2026-11-10).
    entry_lang = str(entry.get("lang") or "")
    if data.stage_of(entry_lang) == stage and _same_form(form, str(entry.get("word") or "")):
        # The dictionary's own grammar label goes with the word here too, or a
        # rung would print no formation while the join view below prints one
        # (review, 2026-11-10).
        seam = seam_of(entry_lang, str(entry.get("word") or ""),
                       str(entry.get("pos_label") or ""),
                       _definition_stem(entry_lang, str(entry.get("word") or "")))
        if seam and seam.get("verdict") == "unique":
            return [{"kind": "compound", "lang": entry_lang,
                     "lang_name": _lang(entry_lang).get("name", entry_lang),
                     "of": normalise_etymon(str(entry.get("word") or "")),
                     "pieces": _seam_pieces(entry_lang, seam["parts"]),
                     "source": "ours", "sentence": seam.get("sentence", "")}]
    return []


def _rung_built(entry: dict, stage: str, form: str) -> dict | None:
    """The first construction the record states for a form, at its own stage."""
    builds = _rung_builds(entry, stage, form)
    return builds[0] if builds else None


@lru_cache(maxsize=8)
def seam_rules(lang: str) -> dict:
    """The curated rules for reading a seam in ``lang``, or an empty mapping.

    Only a language with a `data/compounds/<lang>.yaml` gets a seam read at
    all: which short words are safe elements, which are function words and
    which must never be used as a component is a judgement about one language
    and cannot be defaulted (2026-11-10).
    """
    path = data.DATA / "compounds" / f"{lang}.yaml"
    if not path.exists():
        return {}
    try:
        return data._load_yaml(path) or {}
    except Exception:  # noqa: BLE001 - a broken file is not a crash
        return {}


def _seam_lookup(lang: str):
    """``form -> {known, recorded, pos}`` over one language's headwords.

    A piece is "recorded" when its own entry states an ancestry or an
    etymology; that is the whole test, and it is the one `pie.compounds`
    documents, so a seam of two unrecorded words is refused rather than
    explained by itself (2026-11-10).
    """
    index = _lemma_index(lang)

    def lookup(form: str) -> dict | None:
        if not form:
            return None
        row = index.get(normalise_etymon(form)) or index.get(form)
        if not row:
            return None
        return {"known": True,
                "recorded": bool(row.get("anc") or row.get("etym")
                                 or row.get("built_as")),
                "pos": str(row.get("pos") or "") or None}

    return lookup


#: A definition that says what the word is relative to: مقنعی «منسوب به مقنعه».
_NISBA = re.compile(r"^\s*منسوب\s*(?:است\s*)?به\s*([^\s،؛:,.()«»\"]+)")


def _nisba_base(lang: str, word: str, glosses: Iterable[str]) -> str:
    """The entry a definition calls this word «منسوب به», or "".

    The base is read from the senses given — the entry the page is drawing, not
    a fresh lookup — so a caller cannot inherit a hint from another row.
    """
    for sense in glosses or []:
        found = _NISBA.match(str(sense))
        if not found:
            continue
        base = found.group(1).strip()
        if base and base != word and _lemma_entry(lang, base):
            return base
    return ""


@lru_cache(maxsize=8192)
def _definition_stem(lang: str, word: str) -> str:
    """The word a definition calls this one «منسوب به», if it is an entry.

    A nisba names its own base in the definition (critic batch 02, 2026-11-13:
    مقنعی «منسوب به مقنعه»), and that is a record statement about how the word
    was made — the base is a word of the language and the ending is one of its
    own suffixes.  The hint chooses which entry a suffix seam stands on; it
    never makes a cut by itself.
    """
    entry = _lemma_entry(lang, word) or {}
    return _nisba_base(lang, word, entry.get("gloss") or [])


@lru_cache(maxsize=16384)
def _suffix_seam(lang: str, word: str, said: str = "", hint: str = "") -> dict | None:
    """``word`` = a stored, recorded stem + one of the stage's own suffixes.

    A closed class is the strongest evidence the model can have about a word
    the record does not analyse: Persian -ی, -مند, -گاه are a list, not a cut
    position, and the stem has to be a headword with a recorded origin of its
    own.  Two suffixes that both fit are a tie and are refused, exactly as a
    two-way split is (2026-11-10).

    ``said`` is the dictionary's own grammar label for the word, when it prints
    one (`data/dehkhoda/structure.jsonl.gz`).  It changes one thing: a word the
    dictionary calls a *relative adjective* (ص نسبی) is a -ی formation by its
    own account, so its stem need not carry an etymology of its own — the
    dictionary has already said what the word is made of and how, and the band
    stays `built` rather than green (2026-11-10).
    """
    rows = (morphology(lang) or {}).get("suffixes") or []
    forms = sorted({str(r.get("form") or "").lstrip("-").strip()
                    for r in rows if str(r.get("form") or "").strip("-")},
                   key=len, reverse=True)
    # A row may say it is only readable when the dictionary's own label names
    # it (`licensed: ordinal`): ـم is the ordinal ending *and* the 1sg
    # possessive, so a word ending in م is not evidence of either (critic batch
    # 02, 2026-11-13: سیزدهم, which Dehkhoda prints as «عدد ترتیبی»).
    licensed = {str(r.get("form") or "").lstrip("-").strip()
                for r in rows if r.get("licensed")}
    if not forms:
        return None
    # A label licenses the suffix it names, not every suffix in the registry:
    # «ص نسبی» is the -ی formation and «مصغر» the diminutives, so a word the
    # dictionary calls a relative adjective cannot be cut with -ک (تئوریک),
    # and a diminutive is not a -ی formation (review, 2026-11-10).
    allowed = None
    if "ترتیبی" in said:
        allowed = {form for form in forms if form in ("م",)}
    elif "نسبی" in said:
        allowed = {form for form in forms if form in ("ی",)}
    elif "مصغر" in said:
        allowed = {form for form in forms if form in ("ک", "چه")}
    licensed -= allowed or set()
    derived = allowed is not None
    # The definition may name the base the word is «منسوب به» (مقنعی), and that
    # base is a stronger witness than the bare cut: مقنع is an entry too, but
    # it means "a mouth whose teeth turn inward", not the veil.  The hint only
    # chooses which entry the suffix stands on; it never makes a cut alone.
    if hint:
        bare = hint[:-1] if hint.endswith("ه") else hint
        for form in forms:
            if allowed is not None and form not in allowed:
                continue
            if word != bare + form:
                continue
            record = _lemma_entry(lang, hint) or {}
            if not record:
                continue
            elided = bare != hint
            return {"word": word, "parts": [hint, "-" + form], "stem": hint,
                    "suffix": form, "verdict": "unique", "elided": elided,
                    "alternatives": [["-".join([hint, form])]],
                    "gloss": _rung_gloss(record.get("gloss") or []),
                    "reason": (f"{hint} + -{form} (a recorded suffix of the stage"
                               + (", the stem's final ـه elided" if elided else "")
                               + "); the whole word is a formation, not a derivation")}
    hits = []
    for form in forms:
        if allowed is not None and form not in allowed:
            continue
        if form in licensed:
            continue
        if not word.endswith(form) or len(word) - len(form) < 3:
            continue
        stem = word[: -len(form)]
        record = _lemma_entry(lang, stem)
        # A label-derived stem must be a word that can take a suffix: a
        # preposition or adverb labelled -ی is a cut, not a formation (review,
        # 2026-11-10).
        usable = record and (record.get("anc") or record.get("etym")
                             or (derived and str(record.get("pos") or "")
                                 not in ("prep", "postp", "conj", "pron", "det",
                                         "part", "interj", "num", "adv")))
        if usable:
            hits.append((stem, form, record))
    if len(hits) != 1:
        return None
    stem, form, record = hits[0]
    return {"word": word, "parts": [stem, "-" + form], "stem": stem,
            "suffix": form, "verdict": "unique",
            "alternatives": [["-".join([stem, form])]],
            "gloss": _rung_gloss(record.get("gloss") or []),
            "reason": (f"{stem} + -{form} (a recorded suffix of the stage); the "
                       "whole word is a formation, not a derivation")}


@lru_cache(maxsize=16384)
def seam_of(lang: str, word: str, said: str = "", hint: str = "") -> dict | None:
    """Whether ``word`` can be cut into words of its own language, and how.

    This is *our* reading of an unanalysed headword, never a record: the entry
    may say nothing about where the word came from, and the seam is a fact
    about its shape.  `pie.compounds` refuses a tie and refuses a piece that is
    a function word, so a `unique` verdict is the only one a caller may use for
    a band; `verified` stays False so the page can say whose claim it is.

    ``said`` is the dictionary's grammar label; it never picks a cut, it only
    lets the page repeat what the dictionary already claimed (a compound, a
    relative adjective) beside the cut this model reads.
    """
    rules = seam_rules(lang)
    if not rules or not word:
        return None
    from . import compounds

    suffix = _suffix_seam(lang, word, said, hint)
    if suffix:
        suffix["kind"] = "suffix"
        suffix["verified"] = False
        whose = (f" The dictionary prints it as «{said}»." if said else "")
        elided = (" (its final ـه elided before the suffix)"
                  if suffix.get("elided") else "")
        suffix["sentence"] = (f"{suffix['stem']} + ‑{suffix['suffix']} → {word}{elided}, "
                              f"built in {rules.get('label') or lang} with one of its "
                              "own recorded suffixes; a formation, not a derivation."
                              + whose +
                              " The dictionary records no etymology for it.")
        return suffix
    try:
        found = compounds.analyse(word, _seam_lookup(lang), rules=rules)
    except Exception:  # noqa: BLE001 - a seam is never worth a 500
        return None
    if not found:
        return None
    found["kind"] = "compound"
    found["verified"] = False
    found["sentence"] = compounds.describe(found, str(rules.get("label") or lang))
    if "مرکب" in said and found.get("verdict") == "unique":
        found["sentence"] += (f" The dictionary itself prints the word as a compound "
                              f"(«{said}»); which words it is cut into is this model's "
                              "reading, not its.")
    return found


def _seam_payload(lang: str, entry: dict) -> dict | None:
    """The seam the page should show, or None when the record already speaks.

    A recorded construction is `joins`' job; this is only for the words the
    record leaves unanalysed, and it carries the sentence so the page never has
    to build the claim itself (2026-11-10).
    """
    if entry.get("anc") or entry.get("etym") or entry.get("built_as"):
        return None
    # A word whose record names the language it was borrowed from has one
    # history, and it is the borrowing: drawing a "built in Persian" join
    # beside it would offer a second pathway (2026-11-09; review,
    # 2026-11-10).  The exception is a word whose *definition* names the word
    # it is relative to (مقنعی «منسوب به مقنعه»): then the loan is the stem's
    # and the headword is the -ی formation on it (critic batch 02, 2026-11-13).
    word = str(entry.get("word") or "")
    hint = (_nisba_base(lang, word, entry.get("gloss") or [])
            if entry.get("borrowed_from") else "")
    if entry.get("borrowed_from") and not hint:
        return None
    seam = seam_of(lang, word, str(entry.get("pos_label") or ""), hint)
    if not seam:
        return None
    payload = dict(seam)
    payload["pieces"] = _seam_pieces(lang, seam.get("parts") or [])
    if hint:
        payload["sentence"] = str(seam.get("sentence") or "").replace(
            "The dictionary records no etymology for it.",
            f"The headword itself is formed in Persian; {hint} is the loan.")
    return payload


def _seam_join(lang: str, entry: dict) -> dict | None:
    """The seam in the shape the timeline's join view already draws.

    A recorded compound (`joins`) and a seam this model reads are the same
    picture — two words with their own origins meeting at a headword — so the
    page draws them with one renderer.  They are *not* the same claim, and the
    payload says which: `ours` is true here, and every caption says so
    (2026-11-10).
    """
    seam = _seam_payload(lang, entry)
    if not seam:
        return None
    # A suffix is not a word of the language: it is a bound morpheme the
    # registry lists, and it is drawn as a piece marked `bound` so the join
    # never calls it a source with an unrecorded origin (2026-11-10).
    suffix_gloss = ""
    if seam.get("kind") == "suffix":
        for row in (morphology(lang) or {}).get("suffixes") or []:
            if str(row.get("form") or "").lstrip("-").strip() == str(seam.get("suffix") or ""):
                suffix_gloss = str(row.get("gloss") or "")
                break
        # The registry's gloss for -ی is the *relational adjective* sense.  A
        # noun in -ی (آبخوری "a drinking vessel", گردروبی "sweeping") wears the
        # same ending for another sense, and printing "of, pertaining to" over a
        # noun would put a meaning on it that the word does not have (review,
        # 2026-11-10).
        if str(entry.get("pos") or "") != "adj":
            suffix_gloss = ""
    pieces = []
    for part in seam.get("parts") or []:
        if str(part).startswith("-"):
            pieces.append({"form": "‑" + str(part).lstrip("-"), "word": "",
                           "lang": lang, "gloss": suffix_gloss, "pos": "suffix",
                           "ancestry": [], "known": True, "recorded": True,
                           "bound": True})
            continue
        record = _lemma_entry(lang, str(part).lstrip("-")) or {}
        chain = _ancestry_forms(record) if record else []
        chain.reverse()          # oldest first, as a timeline reads
        pieces.append({"form": str(part),
                       "word": record.get("word") or str(part).lstrip("-"),
                       "lang": lang,
                       "gloss": (record.get("gloss") or [""])[0] if record else "",
                       "pos": (record.get("pos") or "") if record else "",
                       "ancestry": chain,
                       "known": bool(record),
                       "recorded": bool(record.get("anc") or record.get("etym"))})
    if len(pieces) < 2:
        return None
    return {"etym": seam.get("sentence", ""), "pieces": pieces, "ours": True,
            "kind": seam.get("kind") or "compound"}


def _seam_pieces(lang: str, parts: Iterable[str]) -> list[dict]:
    """Each part of a seam with the record it opens, for the timeline row."""
    out = []
    for part in parts:
        if str(part).startswith("-"):
            # A suffix of a seam says what it does, exactly as a suffix of a
            # recorded construction does; otherwise لگنچه, معلمی and قلمی print
            # their ending bare while باغچه prints "diminutive" (critic batch
            # 05, 2026-11-13).
            out.append({"form": "‑" + str(part).lstrip("-"),
                        "gloss": _morph_gloss(part, lang).split(" (")[0].strip(),
                        "known": True, "recorded": True, "bound": True, "lang": lang,
                        "branch": None})
            continue
        entry = _lemma_entry(lang, part) or {}
        out.append({"form": part,
                    "gloss": _rung_gloss(entry.get("gloss") or []),
                    "known": bool(entry),
                    "lang": lang,
                    "branch": _origin_node(lang, part),
                    "recorded": bool(entry.get("anc") or entry.get("etym")
                                     or entry.get("built_as"))})
    return out


def _own_construction(entry: dict, chain: list[str]) -> dict | None:
    """The record's statement that the word is built at its own stage.

    ``{{com|ira-pro|*cwáHdah|*pátiš}}`` and ``{{af|en|lexico-|-graphy}}`` name
    the pieces a word is made of; they are not ancestors.  Such a word starts
    at itself, and the pieces are printed beside that rung (proposals/011,
    2026-11-09).  A cross-stage *inherited* ancestor means the whole word does
    have a rung above, and the construction is not used as the start then.
    """
    own_stage = data.stage_of(entry.get("lang") or "") or entry.get("lang") or ""
    if own_stage not in chain:
        return None
    word = normalise_etymon(str(entry.get("word") or ""))
    # A record may state the formation in words rather than as a `built_as`
    # row: "Reduplicated stative of the root *h₂eyḱ-" is the whole of how
    # *h₂eh₂óyḱe was made, so the ladder starts at that word and not at the
    # root it repeats (admin, 2026-11-12).
    rows = list(entry.get("built_as") or [])
    if not any(_built_row_names(row, entry.get("word") or "", own_stage)
               for row in rows):
        rows.extend(_reduplication_rows(entry, own_stage))
    for row in rows:
        if (data.stage_of(row.get("lang") or "") or row.get("lang")) != own_stage:
            continue
        kind = str(row.get("kind") or "formation")
        pieces = row.get("pieces") or []
        # A join needs two pieces; a word the record states as *formed from*
        # one word is the whole of its history — *aiganaz is an adjectival
        # formation on *aiganą — and its timeline is that one step rather
        # than a climb to the piece's own PIE root (admin, 2026-11-12).
        if len(pieces) < (1 if kind in _SINGLE_PIECE_KINDS else 2):
            continue
        of = normalise_etymon(str(row.get("of") or ""))
        # The builder names the product when it can identify it; without that
        # name the row could belong to another form in the same entry, and a
        # start is too strong a claim to make on a guess.
        if not of or not _same_form(of, word):
            continue
        # An entry may carry both its history and a surface analysis ("beer,
        # equivalent to be + -er", but from Middle English beere).  A
        # cross-stage ancestry row is the word's own history unless it is the
        # ancestry of one of the pieces (cwáHdah + pátiš, where pátiš is from
        # PIE *pótis): only the second case makes the construction the start.
        cross = [(lg, w, rel) for lg, w, rel in _ancestry_triples(entry)
                 if (data.stage_of(lg) or lg) != own_stage]
        if cross and not _pieces_explain_ancestry(own_stage, pieces, cross):
            continue
        return {"stage": own_stage, "kind": kind, "pieces": pieces}
    return None


def _pieces_explain_ancestry(own_stage: str, pieces: list,
                             cross: list[tuple[str, str, str]]) -> bool:
    """Whether every cross-stage row is an ancestor of one of the pieces.

    ``pátiš`` is recorded from PIE *pótis, so the compound's only cross-stage
    row belongs to its second piece.  English *beer* from Middle English
    *beere* is not an ancestor of either *be* or *-er*, so the surface
    analysis is not the word's history.
    """
    forms = [str((piece or [""])[0] or "") for piece in pieces]
    for lang, word, _rel in cross:
        stage = data.stage_of(lang) or lang
        wanted = (stage, normalise_etymon(word))
        if not any(_reaches_ancestor(own_stage, form, wanted, 3, set())
                   for form in forms):
            return False
    return True


def _reaches_ancestor(stage: str, form: str, wanted: tuple[str, str],
                      depth: int, seen: set[tuple[str, str]]) -> bool:
    """Whether an entry records ``wanted`` at any point up its own chain.

    A compound's piece may reach the PIE form through one or two recorded
    steps (pátiš ← Proto-Indo-Iranian pátiš ← PIE pótis), so the check follows
    the record, not a single row.  It is bounded and cycle-safe.
    """
    key = (stage, normalise_etymon(form))
    if depth <= 0 or key in seen:
        return False
    seen.add(key)
    record = _lemma_entry(stage, form)
    if not record:
        return False
    for lg, word, _rel in _ancestry_triples(record):
        here = (data.stage_of(lg) or lg, normalise_etymon(word))
        if here == wanted:
            return True
        if _reaches_ancestor(here[0], here[1], wanted, depth - 1, seen):
            return True
    return False


# ------------------------------------------------- a construction that carries
#: Parts of speech that name a morpheme, not a word: a piece of a construction
#: with one of these is bound and needs no ancestry of its own — the stage's
#: morphology is where it stands (*-s is a nominative ending, not a word that
#: came from Proto-Indo-European).
_BOUND_POS = frozenset({"prefix", "suffix", "infix", "interfix", "circumfix",
                        "ending", "suffixoid", "prefixoid"})


@lru_cache(maxsize=None)
def _bound_forms(stage: str) -> frozenset[str]:
    """The morphemes this stage's own morphology table registers.

    ``-s`` is the athematic nominative singular in `data/morphology/ine-pro.yaml`
    and ``-naut`` is only an English dictionary headword: the first is the
    stage's grammar and the second is a word with a history of its own, so only
    the first is a piece that needs no ancestry (admin, 2026-11-13).
    """
    table = morphology(stage) or {}
    out = set()
    for row in list(table.get("suffixes") or []) + list(table.get("endings") or []):
        key = row.get("form") or row.get("id")
        if not key:
            continue
        out.add(normalise_etymon(str(key)))
        # A record writes a suffix with the ending it brings in one piece
        # (*-yeti, *-nós), and that is the same morpheme as the table's
        # *-ye- plus *-ti: the piece needs no ancestry either way.
        ending = str(row.get("ending") or "")
        if ending:
            out.add(normalise_etymon(str(key).strip("-") + ending.strip("-")))
    return frozenset(out)


def _piece_text(kind: str, index: int, count: int, form: str, gloss: str) -> str:
    """The piece as the record means it, hyphen and all.

    An arithmetic writes a bound morpheme with its hyphen (``-th``), but the
    older import dropped it for a row that names the kind instead
    (``growth`` = ``grow`` + ``th``, glossed "abstract nominal suffix").  The
    gloss and the row's kind say it is a morpheme, so the lookup has to be
    ``-th`` and not ``th`` — the word that happens to be spelled *th* is a
    different entry with a different history.
    """
    written = str(form or "").strip()
    # A reconstructed bound piece is written *-yeti: the asterisk comes first
    # and the hyphen marks the seam after it, so the hyphen is read past the
    # star (a plain ``written[:1] == "-"`` turned *-yeti into -*-yeti, and the
    # composed form then spelled nothing).
    star = "*" if written[:1] == "*" else ""
    body = written[len(star):]
    if not written or body[:1] == "-" or written[-1:] == "-":
        return written
    named = bool(re.search(r"\b(?:suffix|prefix|infix|ending)\b", str(gloss or ""), re.I))
    if kind == "suffix" and index == count - 1:
        named = True
    if kind == "prefix" and index == 0:
        named = True
    return (star + "-" + body) if named else written


def _piece_origin(stage: str, form: str, chain: list[str]) -> dict:
    """Where one piece of a construction stands: a PIE etymon, a non-PIE
    source, a registered morpheme — or nowhere this model can name.

    The admin's test is that every segment *start from PIE or a non-PIE
    language* (2026-11-13), so a piece is explained when:

    * its own record names a Proto-Indo-European etymon — the form it descends
      from, however many stages the sentence lists above it (*anda-, whose
      entry says "from pre-Germanic *h₂entó- … from the PIE root noun
      *h₂énts"); or
    * it is the Proto-Indo-European etymon itself; or
    * it comes from outside the family; or
    * it is a morpheme the stage's own morphology table registers (*-s is the
      athematic nominative singular), which is grammar rather than a word and
      has no origin to trace.

    An affix a dictionary merely heads (-naut, -th) is a word or a stem with a
    history of its own, so it is judged by that history like any other piece,
    and a morpheme the stage's table does not register is not explained.
    """
    raw = str(form or "").strip()
    key = normalise_etymon(raw)
    out = {"form": raw, "stage": stage, "origin": "", "why": "", "explained": False}
    if not key:
        out["why"] = "no form"
        return out
    bound = raw[:1] == "-" or raw[-1:] == "-"
    record = _lemma_entry(stage, raw) if stage != chain[0] else None
    if record is not None and bound:
        # The lookup retries a bound spelling without its hyphen (a notation
        # rule written for reconstructions), so it can land on a different
        # word: ``-th`` must not become the pronoun *th*.  A bound piece is
        # answered only by a bound headword.
        head = str(record.get("word") or "")
        if not (head[:1] == "-" or head[-1:] == "-"
                or str(record.get("pos") or "").lower() in _BOUND_POS):
            record = None
    if record is not None:
        pie = _pie_form(record)
        if pie:
            out.update(origin=f"PIE *{pie}", why="a recorded PIE etymon",
                       explained=True)
            return out
        from . import loans
        try:
            if loans.classify(record, stage) == "non_ie":
                out.update(origin="outside the family", why="a non-PIE source",
                           explained=True)
                return out
        except Exception:
            pass
    if key in _bound_forms(stage) and (bound or stage == chain[0]):
        out.update(origin="registered morpheme", why="a morpheme, not a word",
                   explained=True)
        return out
    if stage == chain[0]:
        out.update(origin=f"PIE *{key}", why="the Proto-Indo-European etymon",
                   explained=True)
        return out
    if bound:
        out["why"] = "a morpheme the stage does not register"
    else:
        out["why"] = ("no entry for this piece" if record is None
                      else "no recorded PIE origin above it")
    return out


def _joined_form(stage: str, kind: str, pieces: list[str]) -> str:
    """The form the pieces make when the stage joins them, as it writes them.

    A join may take a linker the stage's morphology registers
    (``morphology(stage).joining``); every other kind of row writes its pieces
    in the order the word wears them, so the join is their concatenation.  A
    one-piece formation names an ancestor form, not a spelling, and is not
    reproduced this way — it returns the piece itself and never equals the
    word unless the word *is* that form.
    """
    if len(pieces) <= 1:
        return pieces[0] if pieces else ""
    info = (morphology(stage) or {}).get("joining") or {}
    linker = str(info.get("linker") or "")
    out = pieces[0]
    for piece in pieces[1:]:
        out += linker + piece
    return out


def construction_path(entry: dict, lang: str, chain: list[str] | None = None) -> dict | None:
    """Whether a registered construction carries this word to its recorded form.

    A word may be made rather than inherited: ``andaswarō`` is ``*anda-`` +
    ``*swarō``, and neither piece has to become the whole word by a sound law.
    The construction is the record's own arithmetic, so it can stand in for the
    laws in a green path — but only when it really produces the word and every
    piece has somewhere to stand (admin, 2026-11-13):

    * the pieces, written in order, spell the recorded headword exactly
      (``exact``), and
    * each piece is explained — the PIE etymon itself, a non-PIE source, or a
      morpheme the stage's morphology registers (``explained``).

    Nothing is invented: the row is the one ``_own_construction`` reads from the
    record (``built_as`` and the reduplication sentences), a word the record
    does not state as a construction gets ``None``, and a piece with no
    recorded origin makes the whole construction fall short instead of being
    papered over.  The verdict decides what a passing construction is worth;
    this function only measures.
    """
    chain = list(chain or data.derivation_chain(lang))
    if not chain:
        return None
    row = _own_construction(entry, chain)
    if not row:
        return None
    kind = str(row.get("kind") or "formation")
    raw = [piece or [""] for piece in row.get("pieces") or []]
    pieces = [_piece_text(kind, index, len(raw), str(p[0] or ""),
                          str(p[1] if len(p) > 1 else ""))
              for index, p in enumerate(raw)]
    if not pieces:
        return None
    # A dictionary writes a bound piece with its hyphen; Persian writes the
    # seam of a compound with the tatweel (سامان + ـه), which is the same
    # notation and has to come off before the pieces are joined.
    written = [normalise_etymon(piece.replace("\u0640", "-")) or piece
               for piece in pieces]
    word = normalise_etymon(str(entry.get("word") or ""))
    composed = _joined_form(row["stage"], kind, written)
    grade = None
    exact = bool(composed) and (
        composed.casefold() == word.casefold()
        or stress_only(composed.casefold(), word.casefold()))
    # A composition takes the grade its suffix asks for (the rule the page's
    # own builder applies, v0.17.3): a record cites the root in the e-grade it
    # is listed under and writes the word in the zero or o-grade the suffix
    # makes (*bʰendʰ- + *-tós → *bʰn̥dʰtós).  Reading the row as a plain
    # concatenation called such a word a construction that "does not spell the
    # word".  Only a grade the morphology table documents is applied, and only
    # when the plain join has already failed (2026-11-13).
    if not exact and len(written) >= 2:
        stem = written[0].lstrip("-")
        suffix = "-" + written[-1].lstrip("-")
        graded, why = _formation_grade(stem, suffix, row["stage"])
        if why and graded:
            attempt = _joined_form(row["stage"], kind, [graded] + written[1:])
            if attempt and (attempt.casefold() == word.casefold()
                            or stress_only(attempt.casefold(), word.casefold())):
                composed, grade, exact = attempt, why, True
    origins = [_piece_origin(row["stage"], piece, chain) for piece in pieces]
    return {
        "kind": kind,
        "stage": row["stage"],
        "stage_name": _lang(row["stage"]).get("name", row["stage"]),
        "note": " + ".join(pieces),
        "form": composed,
        "grade": grade,
        # The pieces must spell the headword.  Two conventions are writing, not
        # sound, and are set aside the way the rest of the model sets them
        # aside: a capital's place in a proper name (ytterbium = Ytterby + -ium,
        # Greenleigh = green + -leigh) and the two ways of writing stress (a
        # dictionary's acute, the engine's ˈ).  Nothing else is forgiven.
        "exact": exact,
        "stated": True,
        "pieces": origins,
        "unexplained": [o["form"] for o in origins if not o["explained"]],
        "explained": bool(origins) and all(o["explained"] for o in origins),
    }


def _unexplained_branch(node: dict | None) -> dict | None:
    """The word a drawn climb ends a ``???`` above, or ``None`` when it ends.

    The construction tree draws one column per piece, and the column stops in
    one of the honest ways `_origin_node` documents — at Proto-Indo-European,
    at a language outside the family, at a donor, or at the record's stop.  A
    climb that ends in ``end`` or ``missing`` is drawn as a ``???``, and the
    reader sees a question mark where an explanation should be; so a band may
    never be green over it (admin, 2026-11-13: رضاقلی read "fully explained"
    above a ``???``).  This walks the same path `climbOf` walks in the page.
    """
    seen: set[int] = set()
    queue = [node]
    while queue:
        node = queue.pop(0)
        if node is None or id(node) in seen:
            continue
        seen.add(id(node))
        if node.get("terminal") in ("end", "missing"):
            return node
        builds = node.get("builds") or []
        if builds:
            # **Every column of the tree is the reader's**, not only the first
            # piece's: each piece draws its own ascent, so a ??? over the second
            # piece is as visible as one on the rail (2026-11-13).
            for build in builds[:1]:
                for piece in build.get("pieces") or []:
                    queue.append((piece or {}).get("branch"))
            continue
        for parent in node.get("parents") or []:
            queue.append(parent)
    return None


def unrecorded_ancestry(entry: dict, chain: list[str]) -> list[dict]:
    """Recorded ancestors of this word that no entry of their stage heads.

    A word is *fully* explained only when its whole recorded ancestry is a row
    of words this model holds: every stage it names exists as an entry, the
    laws carry the oldest one down, and the record's own construction, if any,
    is registered.  The first two clauses were measured; the third was not, so
    a timeline could print "no entry for this word" above a dark-green band
    (admin, 2026-11-13: Proto-Indo-Iranian *HwáHyati, whose PIE rung
    *h₁wéh₂-ye-ti* the PIE glossary did not hold).

    The check is the reader's own: the forms come from ``_ancestry_triples``,
    the lookup is ``_lemma_entry`` (so a hyphen, the engine's stress token and
    case are notation, not a second word), and a row is skipped when it is not
    a step of the word's chain:

    * a **root** is a relation, not a step (*h₁weh₂-* above *h₁wéh₂-ye-ti*),
      and a bound spelling (*anda-*, *bʰeh₂g-*) is a morpheme, not a word;
    * a **borrowing** and a **calque** are not inheritance, so their donor
      stages are not rungs of this timeline;
    * a **stage this model holds no glossary for** (Proto-Italic, Proto-Hellenic)
      is not measured at all.  The rung is a quotation, the page says the model
      has no glossary there, and an inventory this model never built is a gap
      of ours — not a hole in the record (`pie.dubious` makes the same
      distinction).

    The walk does not stop at the word's own record: a rung that *is* an entry
    has a timeline of its own, and the page draws it (`ownStep`), so a word the
    ancestor's record names and the glossary lacks is the same hole one step
    higher — and it must be reported, or a daughter is green above a dark-red
    row.  Only entries are followed (a hole has nothing to follow), depth is
    bounded and a form is visited once, so a record that names its own
    descendant cannot loop.

    Nothing is guessed: a form the record names but the glossary lacks is
    reported with the spelling the record used.

    A second shape of hole is the page's own ``???``: each reconstruction piece
    is drawn as a column that climbs until it stops, and a column that stops at
    a word whose origin no record states (*``end``*) is exactly what the
    question mark says.  Those rows are reported with ``kind: "origin"`` so the
    verdict can say "no recorded origin for X" instead of claiming a missing
    *entry* (admin, 2026-11-13: fa رضاقلی read "fully explained" above a ???).
    """
    out: list[dict] = []

    def walk(record: dict, depth: int, seen: set[tuple[str, str]]) -> None:
        own = data.stage_of(record.get("lang") or "") or record.get("lang") or ""
        for lang, word, rel in _ancestry_triples(record):
            if rel not in ("inherit", "derived"):
                continue
            stage = data.stage_of(lang) or lang
            if stage not in chain or stage == own or not _has_glossary(stage):
                continue
            for part in re.split(r"[,;]", word or ""):
                raw = part.strip()
                form = normalise_etymon(raw)
                # A row the extraction cut in the middle of an etymology can
                # hold the join itself ("+", from "*sok-éh₂ + *-nóm"): it is
                # punctuation, not a form, and naming it would invent a word.
                if (not form or raw.endswith("-") or form.endswith("-")
                        or not any(ch.isalpha() for ch in form)):
                    continue
                if (stage, form) in seen:
                    continue
                seen.add((stage, form))
                found = _lemma_entry(stage, form)
                if found is None:
                    out.append({"stage": stage,
                                "name": _lang(stage).get("name", stage),
                                "form": form,
                                "written": ("*" if kind_of(stage) == "proto" else "")
                                + form.lstrip("*"),
                                "rel": rel,
                                "via": str(record.get("word") or "")})
                    continue
                if depth > 0:
                    walk(found, depth - 1, seen)

    walk(entry, 3, set())
    # A word the record builds at its own stage has pieces the page draws as
    # columns of their own, each carrying that piece's recorded ancestors.  A
    # piece's ancestor the glossary does not head is therefore a hole in *this*
    # timeline, exactly like a hole in the word's own chain — which is why fa
    # آبجو could read “fully explained” beside a dark-red “no entry for this
    # word” over Old Persian *yáwaʰ: the walk started at the compound's record,
    # and a compound's record has no ancestry of its own (admin, 2026-11-13).
    # Only a piece this stage really heads is followed; an unheaded piece is a
    # morpheme, and `construction_path` already refuses one.
    own_stage = data.stage_of(entry.get("lang") or "") or entry.get("lang") or ""
    seen_forms = {(own_stage, normalise_etymon(str(entry.get("word") or "")))}
    pieces: list[tuple[str, tuple, bool]] = []
    own_row = _own_construction(entry, chain) or {}
    for index, piece in enumerate(own_row.get("pieces") or []):
        raw = str(piece[0] if isinstance(piece, (list, tuple)) else piece)
        pieces.append((raw,
                       _stated_piece_ancestry(piece[2])
                       if isinstance(piece, (list, tuple)) and len(piece) > 2 else (),
                       _bound_piece(str(own_row.get("kind") or ""), raw, index)))
    for join in _compound_pieces(entry, own_stage):
        pieces.extend((str(p.get("word") or ""), (), False)
                      for p in join.get("pieces") or [])
    for raw, piece_anc, bound in pieces:
        form = normalise_etymon(raw)
        if not form or (own_stage, form) in seen_forms:
            continue
        # The page draws this piece's climb, so a climb that ends in a `???` is
        # a hole in *this* timeline however complete the entry behind it looks:
        # a word whose origin the record does not state is exactly what the
        # question mark says, and green may not stand over it (admin,
        # 2026-11-13: fa رضاقلی over قلی).  The climb is the page's own, so the
        # origin the compounding row states for the piece is the one read.
        dead = (None if bound else
                _unexplained_branch(_origin_node(own_stage, raw, quoted=piece_anc)))
        if dead is not None:
            stage = data.stage_of(str(dead.get("lang") or "")) or str(dead.get("lang") or "")
            if (stage, str(dead.get("form") or "")) not in seen_forms:
                out.append({"stage": stage,
                            "name": dead.get("lang_name") or _lang(stage).get("name", stage),
                            "form": str(dead.get("form") or raw),
                            "written": ("*" if kind_of(stage) == "proto" else "")
                            + str(dead.get("form") or raw).lstrip("*"),
                            "rel": "",
                            "via": str(entry.get("word") or ""),
                            "kind": "origin"})
        found = _lemma_entry(own_stage, form)
        if found is None or found is entry:
            continue
        walk(found, 2, set(seen_forms))
    # Two pieces may share an ancestor (آب and جو both climb through Old
    # Persian), and the walk visits each piece on its own: the hole is one
    # rung of one page, so it is named once.
    unique: dict[tuple[str, str], dict] = {}
    for row in out:
        unique.setdefault((row["stage"], row["form"]), row)
    return list(unique.values())


def ancestor_starts(entry: dict, chain: list[str],
                    keep_formed: bool = False) -> list[tuple[str, str]]:
    """Every usable ancestor form recorded for this word, PIE first.

    This is the project rule (see ``tools/coverage.py``): a word may be derived
    from its PIE etymon **or from any ancestor recorded in its inheritance
    chain**; the question is whether the rules explain the last mile.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    # ``keep_formed`` is set when the word's own pathway switches on the very
    # formation law that builds it (گربه = *h₂wl̥pís + *-ka-): the ancestor the
    # dictionary calls a formation then *is* reachable, because a registered,
    # cited law supplies the morpheme. Without it the formed ancestor stays a
    # record quoted above the ladder, exactly as before (2026-11-08).
    formed = set() if keep_formed else _formed_from(entry)
    pie = _pie_form(entry)
    # Roots the record writes as such: the `{{root}}` row, and any ancestry form
    # the dictionary spells with a root's trailing hyphen (`*neybʰ-`).  The
    # hyphen is notation, so it is gone by the time the form is compared — the
    # set below keeps it, or a root would look like a word (2026-11-09).
    roots: set[tuple[str, str]] = set()
    unread: set[tuple[str, str]] = set()
    for lang, word, rel in _ancestry_triples(entry):
        if rel == "root" or str(word).strip().endswith("-"):
            stage = data.stage_of(lang) if rel != "borrow" else lang
            roots.add((stage, _phonological_form(stage, normalise_etymon(word))))
    cog_form = entry.get("cog", "").split(":", 1)[-1].strip()
    if cog_form.endswith("-"):
        roots.add((chain[0], normalise_etymon(cog_form)))
    if pie and inherited_from_pie(entry) and chain and (chain[0], pie) not in formed:
        out.append((chain[0], _phonological_form(chain[0], pie)))
        seen.add(pie)

    for lang, word, rel in _ancestry_triples(entry):
        # A register of a modelled stage is read at that stage: a Late Latin
        # form is a Latin form (data/language_varieties.yaml, 2026-11-09).  The
        # ancestry list above the ladder still prints the variety's own name.
        lang = data.stage_of(lang) if rel != "borrow" else lang
        if lang not in chain or lang == chain[-1] or rel == "borrow":
            continue
        for part in re.split(r"[,;]", word or ""):
            candidate = _phonological_form(lang, normalise_etymon(part))
            if not candidate or candidate in seen or len(candidate) > 60:
                continue
            if (lang, candidate) in formed:
                continue
            seen.add(candidate)
            out.append((lang, candidate))
            if _spelling_without_reading(lang, candidate):
                unread.add((lang, candidate))

    # A root is a form the word is *related* to, not one it was inherited from:
    # it carries no derivational morphology, so no law turns *sewh₁- into
    # Proto-Iranian *háwmah. When the record also names a word — at any stage —
    # the word is the start and the root stays above the ladder as the cognate
    # it is. A word whose record names nothing else keeps its root start and
    # keeps saying so (2026-11-09, proposals/010: 70 ladders).
    # A transliteration the record gives no reading for (Book Pahlavi bʾnwk',
    # whose reading bānūg stands beside it in the etymology but not in a form
    # the table can use) is a *spelling*: the laws cannot carry its letters, so
    # it is shown on the ladder but may not suppress the words above it.  Before
    # this, storing that row hid بانو's Old Persian *bānūka- start, and the
    # final *-ūg law stopped carrying the word (2026-11-10).
    words = [pair for pair in out
             if pair not in roots and pair not in unread
             and not _is_root_etymon(*pair)]
    out = words or out

    out.sort(key=lambda pair: chain.index(pair[0]) if pair[0] in chain else 10**6)
    return out


#: Book Pahlavi writes an aleph or an ayin that the reading leaves to the
#: reader; a transliteration carrying one is a spelling, not a form, unless the
#: record also states its reading (see `_phonological_form`).
_SPELLING_MARKS = "\u02be\u02bf'\u2019"


def _spelling_without_reading(lang: str, form: str) -> bool:
    """A recorded form that is still a spelling, because nothing reads it."""
    return (needs_reading(lang) and any(ch in form for ch in _SPELLING_MARKS)
            and _phonological_form(lang, form) == form)


def _variety_at(entry: dict, stage: str, form: str) -> str:
    """The register's own name when the start form was recorded under one.

    ``""`` when the form is written under the stage itself, and when the start
    is a composed or edited hypothesis rather than a record.
    """
    for lang, word, rel in _ancestry_triples(entry):
        if rel == "borrow" or data.stage_of(lang) != stage or lang == stage:
            continue
        named = (data.varieties().get(lang) or {}).get("name") or _lang(lang).get("name", lang)
        for part in re.split(r"[,;]", word or ""):
            if _phonological_form(stage, normalise_etymon(part)) == form:
                return named
    return ""


def _phonological_form(lang: str, word: str) -> str:
    """The form the sound laws may run on: a headword's reading.

    The laws are rewrites over *segments*, so a form written in a script is a
    writing, not an input: no rule can turn 𐎼𐎢𐎨 into anything, and handing it
    over produced a ladder that copied the cuneiform down every rung and called
    the recorded word "unreached" although no law had been tried
    (2026-11-11, Middle Persian lwc).  This function is the one place that
    decides what the laws see, and it reads a scripted form in this order,
    first answer winning and nothing invented:

    * the spelling table of the language itself (``data/readings_<lang>.json``
      — Book Pahlavi sng *sang*, the ideogram LWTE *abag*): an abjad writes no
      short vowels, so only the dictionary's own transcription can recover them
      (2026-11-09);
    * the entry's own ``phon``/``translit``/IPA (Book Pahlavi dyw'nk' is
      *dēwānag*);
    * a reading the corpus quotes for this spelling (``data/readings.json``) —
      Wiktionary's ``{{inh|pal|peo|𐎼𐎢𐎨|ts=raučah-}}`` states that the
      cuneiform is read *raučah-*, which is the same kind of record as the
      parenthesis "Old Persian 𐎱𐎠𐎼𐎿 (p-a-r-s /⁠pārsa⁠/)" (2026-11-11);
    * for an *alphabetic* script, the letter-by-letter transliteration, which
      is what the alphabet itself says (Πέρσης → Pérsēs).

    A syllabary's sign-by-sign string (𐎼𐎢𐎨 → ra-u-ca) is never used: its
    hyphens are an edition's way of printing signs, not a phonological form.

    Latin-alphabet words, proto-forms and a scripted headword with nothing
    recorded are returned unchanged, so no reading is ever invented here; an
    unreadable form then stops the laws at the engine's own guard
    (``rules.derive_detailed``) instead of being derived from its letters.
    """
    if not word or not needs_reading(lang):
        return word
    entry = _lemma_entry(lang, word)
    if entry and (entry.get("phon") or "").strip():
        return detokenize(tokenize(entry["phon"].strip())) or word
    stated = script.read(lang, word)
    if stated:
        return detokenize(tokenize(stated)) or word
    if entry:
        reading = readings_for(entry)["reading"]
        if reading and not _is_syllabic(reading):
            return detokenize(tokenize(reading)) or word
    quote = readings_index.for_form(lang, word)
    if quote.get("reading"):
        read = detokenize(tokenize(quote["reading"])) or ""
        if read and not _is_syllabic(quote["reading"]):
            return read
    if not translit.is_scripted(word):
        return word
    letters = translit.transliterate(word)
    if letters.get("reading") and not _is_syllabic(letters["reading"]):
        return detokenize(tokenize(letters["reading"])) or word
    return word


def _recorded_ancestor_forms(entry: dict, chain: list[str]) -> dict[str, list[str]]:
    """Every form the record names at each stage of this word's chain.

    Used to tell a *recorded* start from a typed one: a reader who asks the
    ladder to begin at the Proto-Iranian form the dictionary itself quotes is
    not making a hypothesis, so that rung must not wear the "edited" colour.
    """
    lang = entry.get("lang") or (chain[-1] if chain else "")
    out: dict[str, list[str]] = {}
    words = [entry["word"], *attested_spellings(entry)]
    if lang:
        out[lang] = [w for w in words if w]
    pie = _pie_form(entry)
    if pie and chain and inherited_from_pie(entry):
        out.setdefault(chain[0], []).append(normalise_etymon(pie))
    for stage, word, _rel in _ancestry_triples(entry):
        if stage not in chain:
            continue
        for part in re.split(r"[,;]", word or ""):
            form = normalise_etymon(part)
            if form and form not in out.setdefault(stage, []):
                out[stage].append(form)
                # The form the laws start from is the *reading* of that spelling
                # (𐎼𐎢𐎨 → raučah), and the page offers the ancestor's own
                # record as a start button.  Both are the same record, so a
                # reader who picks either must keep the "this is a record, not
                # a hypothesis" colour (2026-11-11).
                read = _phonological_form(stage, form)
                if read and read != form and read not in out[stage]:
                    out[stage].append(read)
    return out


def _script_fit(entry: dict, form: str) -> dict | None:
    """A reading of the word's own script that its record agrees with.

    The signs of an abjad cannot tell dōš from dūš, so a fit is only evidence
    when the dictionary's own reading agrees with it.  A word with no recorded
    reading keeps the older behaviour: the signs are all there is to go on
    (2026-11-12, the same rule the rungs follow).
    """
    lang = entry.get("lang") or ""
    word = entry.get("word") or ""
    if not lang or not script.writes(lang, word):
        return None
    found = script.match(lang, form, word)
    if not found or not found.get("ok"):
        return None
    readings = [readings_for(entry)["reading"], *attested_spellings(entry)]
    if not _same_reading(found, form, [r for r in readings if r]):
        return None
    return found


def _derive_each_start(entry: dict, chain: list[str], disabled: Iterable[str] = (),
                       enabled: Iterable[str] = ()) -> list[dict]:
    """Every recorded ancestor this word may start from, and whether it reaches.

    ``_derive_for_entry`` answers "which start explains the word best".  This
    answers the question the page puts *beside* the ladder: of all the ancestor
    forms the record names, which ones do the registered laws carry to the
    attested word, and which ones stop short.  A reader who sees that the PIE
    rung differs can then try the Proto-Iranian form the same record quotes,
    without typing anything (2026-11-09).

    Nothing here is a new claim: the forms come from ``ancestor_starts``, the
    reach test is the same one the coverage run uses, and a start that stops
    short says so instead of being hidden.
    """
    lang = entry.get("lang") or (chain[-1] if chain else "")
    target = detokenize(tokenize(entry["word"]))
    spellings = [target] + attested_spellings(entry)
    enabled = list(enabled)
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for stage, form in ancestor_starts(entry, chain, keep_formed=bool(enabled)):
        if (stage, form) in seen or stage not in chain:
            continue
        seen.add((stage, form))
        d = derive(form, chain[chain.index(stage):], data.rulesets(),
                   disabled=list(disabled), enabled=enabled)
        hit = _match_spelling(d.output, spellings)
        scripted = _script_fit(entry, d.output) if not hit else None
        # A stage written in another script whose word the glossary does not
        # hold cannot be read, so the laws cannot carry it anywhere: the chip
        # says that instead of pretending the laws gave the script back.
        unreadable = bool(needs_reading(stage) and any(ord(ch) >= 0x0370 for ch in form))
        out.append({
            "stage": stage,
            "name": _lang(stage).get("name", stage),
            "form": form,
            "output": d.output,
            "steps": len(d.steps),
            "missing": list(d.skipped),
            "unreadable": unreadable,
            "match": (hit is not None or scripted is not None) and not unreadable,
            "via_translit": bool(hit is not None and hit != target),
            "via_script": scripted is not None,
        })
    return out


def _category_of(entry: dict, chain: list[str], exact: dict | None,
                 own_pathway: dict | None, written_match: bool,
                 cited_stem: dict | None, deepest: dict | None,
                 mismatched_steps=(), start_stage: str = "") -> dict:
    """The coverage band this word belongs to, from the page's own facts.

    The same pure function the counter uses (`pie.categories.verdict`), so a
    word's page and the coverage page cannot disagree about it.  The page may
    not know every fact the counter knows (it does not try a word from every
    ancestor), so a word the counter would mark partial cannot come out green
    here: the inputs are only ever the match the ladder actually produced.
    """
    from . import categories as cats
    from . import loans

    try:
        loan = loans.classify(entry, entry.get("lang"))
    except Exception:
        loan = None
    matched_by, tiers = None, set()
    # Where the winning derivation started: the deepest ancestor the laws could
    # carry to this word.  Green needs it to be the PIE etymon itself, so a word
    # the engine only reproduces from Proto-Iranian or Middle English is yellow
    # (2026-11-09).
    match_stage = ""
    if exact:
        matched_by = "pathway" if own_pathway else "laws"
        match_stage = str(exact.get("stage") or "")
        tiers = {str(step.get("tier")) for step in (deepest or {}).get("steps", [])
                 if step.get("tier")}
    elif written_match:
        matched_by = "orthographic"
        match_stage = start_stage
    elif cited_stem:
        matched_by = "citation"
        match_stage = str(cited_stem.get("stage") or "")
    else:
        match_stage = start_stage
    from_pie = bool(chain) and match_stage == chain[0]
    # A word the record does not derive may still be made of words the language
    # already had.  The record's own statement comes first (`{{com}}`/`{{af}}`);
    # only when it says nothing is the seam this repo reads tried, and the note
    # says whose claim it is (2026-11-10).
    built_from, built_note = (), ""
    own_hint = _nisba_base(str(entry.get("lang") or ""), str(entry.get("word") or ""),
                           entry.get("gloss") or [])
    if not (entry.get("anc") or entry.get("etym")
            or (entry.get("borrowed_from") and not own_hint)):
        own_build = _own_construction(entry, chain)
        if own_build:
            built_from = tuple(str(p[0]) for p in own_build["pieces"])
            built_note = "as the record states"
        else:
            from . import compounds
            seam = seam_of(str(entry.get("lang") or ""), str(entry.get("word") or ""),
                           str(entry.get("pos_label") or ""), own_hint)
            if seam and seam.get("verdict") == "unique":
                built_from = tuple(seam["parts"])
                built_note = compounds.seam_note(entry)
    # A word the record builds out of its own words is not a last mile from an
    # ancestor: the construction is how it was made.  Measured here so the page
    # and the counter read one set of facts (admin, 2026-11-13).
    construction = None
    if exact is None and not written_match and not cited_stem:
        try:
            construction = construction_path(entry, entry.get("lang") or "", chain)
        except Exception:
            construction = None
    verdict = cats.verdict(
        recorded=bool(entry.get("anc") or entry.get("etym")),
        built_from=built_from,
        built_note=built_note,
        construction=construction,
        # `loans.classify` speaks of "non_ie"; the band is "non_pie".  Comparing
        # the two vocabularies directly made every Arabic loan a *partial* word
        # on its own page while the counter counted it non-PIE (fixed 2026-11-09).
        non_ie=loan == "non_ie",
        ie_loan=loan == "ie_loan",
        matched_by=matched_by,
        tiers=tiers,
        approved=cats.approved(entry.get("lang") or "", entry["word"]),
        mismatched_steps=mismatched_steps,
        # "Full" needs the record to reach Proto-Indo-European, not merely a
        # successful derivation: a word whose chain stops at Proto-Germanic
        # (English *et* from *ēt*) is *partially* explained, however exactly
        # the laws reproduce it (2026-11-09).
        pie_linked=any(l == "ine-pro" and rel != "borrow"
                       for l, _w, rel in _ancestry_triples(entry)),
        from_pie=from_pie,
        start_name=(_lang(match_stage).get("name", match_stage) if match_stage else ""),
        # Every rung of the recorded ancestry must be a word this model holds:
        # a timeline with a hole in it is partial however exact the last mile
        # (admin, 2026-11-13).
        missing_steps=unrecorded_ancestry(entry, chain),
    )
    if verdict["category"] == "unexplained":
        # The page says the same thing the counter says: not only that there is
        # no etymology, but what kind of word has none (2026-11-10).
        verdict = {**verdict,
                   "reason": cats.unexplained_reason(entry.get("structure"))}
    meta = cats.CATEGORIES[verdict["category"]]
    return {**verdict, "label": meta["label"], "colour": meta["colour"],
            "definition": meta["definition"]}


_CROSS_REFERENCE = re.compile(r"(?:و\s+)?رجوع به\s+")


#: Where a Dehkhoda sense stops stating the meaning and starts stating something
#: about the word: a grammar note, a cross-reference, or a quotation.
_GLOSS_NOTE = re.compile(
    r"(?:^|\.\s|،\s|\u06d4\s*|؛\s*)"
    r"(?:(?:و\s+)?رجوع\s+به|بمعنی\s|نعت\s|صفت\s|اسم\s|مصدر\s|مثنی\s|"
    r"تحریر[یی]\s+از|ج\s*ِ\s|در\s+نجوم|و\s+این\s+نسبت|"
    r"(?:اوستا|پهلوی|پازند|کردی|بلوچی|افغانی|پشتو|تاجیکی|عربی|ترکی|ارمنی|"
    r"سریانی|عبری|سانسکریت)\s*:|\(از\s)")
_LEAD_PAREN = re.compile(r"^\s*(?:\([^()]{0,60}\)\s*)+")
_ATTRIBUTION = re.compile(r"\.\s*\((?:از\s+)?[^()]{0,25}\)\s*\.?")


def _pointer_relation(lang: str, text: str, word: str) -> tuple[str, str] | None:
    """``(relation, base)`` when a sense says the word is a form of another.

    Dehkhoda defines many entries only by their relation to a base — بیلربی is
    «تحریری از بیگلربیگی» and نیازک is «ج ِ نیزک» (plural of نیزک) — and the
    page printed the pointer as if it were a meaning (critic batch 03,
    2026-11-13).  Only a short opening segment counts, and the base must be a
    headword this glossary holds.
    """
    whole = str(text or "").strip()
    # «بمعنی بادژفام است که …» states the other word and then defines it.
    synonym = re.match(r"^بمعنی\s+(\S+)\s+است\b", whole)
    if synonym and synonym.group(1) != word and _lemma_entry(lang, synonym.group(1)):
        return "the same as", synonym.group(1)
    for pattern, relation in ((r"^تحریر[یی]\s+از\s+(\S+)", "a writing of"),
                              (r"^ج\s*ِ\s*(\S+)", "plural of"),
                              (r"^مثنی\s+ی?\s*(\S+)", "dual of"),
                              (r"^مصغر\s+(\S+)", "diminutive of")):
        found = re.match(pattern, whole)
        if not found:
            continue
        base = _lookup_form(found.group(1)).strip(" .،[]")
        if base and base != word and _lemma_entry(lang, base):
            return relation, base
    return None


def _short_sense(entry: dict | None, lang: str = "") -> str:
    """One sense of an entry, cut at its first full stop.

    A sense may itself be written as a pointer («بمعنی بادژ است و سرخی …»);
    the clause that names the other word goes and its definition stays, because
    a page that quotes a cross-reference has not said what the word means
    (critic batch 03, 2026-11-13).
    """
    if not entry:
        return ""
    sense = next((str(g).strip() for g in entry.get("gloss") or [] if str(g).strip()), "")
    sense = _LEAD_PAREN.sub("", sense)
    sense = re.sub(r"^بمعنی\s+\S+\s+است\s*(?:که|و)?\s*", "", sense)
    sense = re.sub(r"\s*\([^()]{0,25}\)\s*", " ", sense)
    note = _GLOSS_NOTE.search(sense)
    if note and note.start() > 0:
        sense = sense[:note.start()]
    sense = re.split(r"\s\.\s|\.\s|\u06d4|\s*؛\s*", sense, 1)[0]
    return re.sub(r"\s+", " ", sense).strip(" .،؛")


def _is_respelling(token: str, headword: str) -> bool:
    """Whether a one-word "sense" is the headword written again.

    Dehkhoda often opens with the word re-spelled — اسقوربوط «اِسْقُربوط. مرضی
    ساری …» — and the page printed the respelling as the meaning (critic batch
    07, 2026-11-13).  A variant spelling shares the head of the word and differs
    by a letter or two; a different word does not.
    """
    if not token or not headword or " " in token or len(token) < 3:
        return False
    if abs(len(token) - len(headword)) > 3:
        return False
    if token == headword:
        return True
    if token[:3] != headword[:3]:
        return False
    import difflib
    # One letter apart is a spelling; two words of a variant list are not.
    return difflib.SequenceMatcher(None, token, headword).ratio() >= 0.8


def _page_gloss(lang: str, entry: dict, glosses) -> list[str]:
    """The meaning to print, cut down to what the record actually defines.

    Dehkhoda writes a whole paragraph under a headword: variant spellings, the
    meaning, a grammatical note («نعت فاعلی است از تدمیح»), the dictionary it
    was taken from, an Arabic example and its translation.  The page printed
    all of it as the meaning (critic batch 01: شکربره; batch 03: عشیش، مدمح،
    حبنبر، نیازک، بیلربی, 2026-11-13).  This reader keeps the meaning:

    * a definition that only names a base is printed with the base's own
      sense beside it — بیلربی «تحریری از بیگلربیگی» → "a writing of
      بیگلربیگی: …", نیازک «ج ِ نیزک» → "plural of نیزک: …";
    * an entry that only says "see the synonyms" (شکربره) quotes the sense
      filed under the variant it points at;
    * otherwise the meaning is the run before the first grammatical note,
      cross-reference, quotation or new sentence, with source attributions
      («(از ناظم الاطباء)») and a trailing hedge (فیرزانی «ظاهراً …») dropped.

    One hop only, and nothing is invented.
    """
    glosses = [str(g).strip() for g in (glosses or []) if str(g).strip()]
    if not glosses:
        return glosses
    first = _LEAD_PAREN.sub("", glosses[0]).strip()
    rest = glosses[1:]
    # The first "sense" may be the headword written again with its vowels —
    # اسقوربوط «اِسْقُربوط. مرضی ساری …» — and a respelling is not a meaning
    # (critic batch 07, 2026-11-13).
    lead = re.split(r"\.\s", first, 1)
    head_word = _lookup_form(str(entry.get("word") or ""))
    if (len(lead) == 2 and len(re.split(r"\s\.\s", lead[1], 1)[0].split()) >= 3
            and _is_respelling(_lookup_form(lead[0]).strip(" ."), head_word)):
        # The next sentence must be a definition; a variant list is not one.
        first = lead[1].strip()
    # A definition that only names the base is still a meaning, once the base's
    # own sense is quoted beside the relation (بیلربی، نیازک).
    pointer = _pointer_relation(lang, first, str(entry.get("word") or ""))
    if pointer:
        relation, base = pointer
        quoted = _short_sense(_lemma_entry(lang, base), lang)
        return [f"{relation} {base}" + (f": {quoted}" if quoted else ""), *rest]
    # A relative definition is a meaning in itself: «منسوب به مقنعه» says what
    # the word is about, and the clause after it explains the relation rather
    # than adding a sense.
    relative = re.match(r"^((?:منسوب|نسبت)\s*(?:است\s*)?به\s+[^\s.،؛]+)", first)
    if relative:
        return [relative.group(1), *rest]
    # An entry that is *only* a cross-reference points at the word it means:
    # بوعجرد «رجوع به ابوعجرد شود» printed a direction where a meaning should
    # be (critic batch 03, 2026-11-13).
    only_ref = re.fullmatch(r"\s*(?:و\s+)?رجوع\s+به\s+([^\s.،؛]+)\s*"
                            r"(?:شود|کنید|نمایید)?\s*[.،؛]?\s*", first)
    if only_ref:
        base = only_ref.group(1)
        other = _lemma_entry(lang, base)
        if other and other.get("word") != entry.get("word"):
            quoted = _short_sense(other, lang)
            if quoted:
                return [f"{base}: {quoted}", *rest]
    # An entry defined only by "see the synonyms of the word" quotes the variant.
    if _CROSS_REFERENCE.search(first) and "مترادفات" in first:
        head = first.split("(", 1)[0]
        for token in re.split(r"[.\u06d4]", head):
            token = token.strip()
            if not token or token == entry.get("word") or " " in token:
                continue
            other = _lemma_entry(lang, token)
            if other is None or other.get("word") == entry.get("word"):
                continue
            sense = _short_sense(other, lang)
            if not sense:
                continue
            # A variant whose own sense is another spelling has not defined the
            # word; keep looking for the one that does (شکربره → شکربرگ).
            if not _is_respelling(sense, token):
                return [f"{token}: {sense}", *rest]
    # The meaning is the run of sentences before the first grammatical note,
    # cross-reference or quotation; `_short_sense` holds the same rule.
    note = _GLOSS_NOTE.search(first)
    if note and note.start() > 0:
        first = first[:note.start()]
    # A dictionary's own hedge is not a meaning (فیرزانی «ظاهراً مخفف …»).
    hedge = re.search(r"\.\s*(?:ظاهراً|ظاهرا|شاید|گویا|احتمالاً)\b", first)
    if hedge and hedge.start() > 0:
        first = first[:hedge.start()]
    first = _ATTRIBUTION.sub(". ", first)
    # One sentence: Dehkhoda separates senses with " . " and examples with "؛".
    first = re.split(r"\s\.\s|\.\s|\u06d4|\s*؛\s*", first, 1)[0]
    first = re.sub(r"\s+", " ", first).strip(" .،؛ ")
    return ([first, *rest] if first else rest)


def _page_category(entry: dict, lang: str, ladder: dict | None,
                   published: str | None = None) -> dict | None:
    """The band for this page, from the ladder when it has one.

    A word with no ladder at all — a loan from Arabic, a word whose record names
    no modelled stage — still has a band, and it is exactly the band the
    counter gives it (`non_pie`, `unexplained`).  Before 2026-11-09 such a page
    printed no badge at all, which read as "not categorised".

    ``published`` is the band the last full coverage run recorded for this word
    (`data/category_index.json.gz`).  The ladder is a local view and can differ
    at the edges — it starts from the deepest recorded ancestor, while the
    counter tries every one and applies the writing layers — and when it does,
    the published measurement wins: a word may not be yellow in the glossary
    and green on its own page (2026-11-09).  An edited ladder passes
    ``published=None`` and keeps its own verdict, because there the reader is
    asking about the edited chain, not about the record.
    """
    own = None
    if ladder and ladder.get("category"):
        own = ladder["category"]
    elif not (ladder and ladder.get("levels")):
        try:
            own = _category_of(entry, data.derivation_chain(lang), None, None,
                               False, None, None)
        except Exception:
            own = None
    if published and (not own or own.get("category") != published):
        # A hole is not a difference of measurement.  The page draws the rung
        # and prints “no entry for this word” over it, so no published band may
        # call the word green beside it (admin, 2026-11-13: fa آبجو read
        # “fully explained” above exactly that line, because the index was
        # measured before a compound's pieces were walked).
        if own and own.get("category") == "partial" and own.get("missing_steps"):
            return own
        return _published_category(published, own)
    return own


#: Why a band was measured, for a page whose ladder did not reach the same
#: answer as the counter.  The counter's own reason is richer, but only the
#: band is published per word; this says what the band means without inventing
#: a measurement.
_BAND_REASON = {
    "full": "the published measurement reproduces it from a recorded PIE etymon with every recorded step agreeing",
    "adjusted": "the published measurement finds a recorded step that differs, or an approved change of ours",
    "partial": "the published measurement reproduces it only from a later ancestor, or not at all",
    "unexplained": "the published measurement finds no recorded etymology",
    "non_pie": "the published measurement has it coming from outside the family",
    "ie_loan": "the published measurement has it borrowed from another IE branch",
}


def _published_category(band: str, own: dict | None) -> dict | None:
    """The counter's band, wearing the ladder's details where it had any."""
    from . import categories as cats

    meta = cats.CATEGORIES.get(band)
    if not meta:
        return own
    row = {"category": band,
           "reason": _BAND_REASON.get(band, "published measurement"),
           "label": meta["label"], "colour": meta["colour"],
           "definition": meta["definition"]}
    steps = (own or {}).get("mismatched_steps")
    if steps:
        row["mismatched_steps"] = steps
    return row


def _script_aware_category(category: dict | None, trace: dict | None) -> dict | None:
    """Say when a green band was earned by the writing, not by the letters.

    ``full`` is also awarded when the laws reach a form the word's *signs*
    allow and the dictionary's own reading agrees — for Persian دوش the laws
    give dūš and the record reads dōš, and the page called that "fully
    explained" without a word about the layer (2026-11-12, the word that was
    asked about).  The band is the counter's, so it stays; the sentence beside
    it now says how it was reached.
    """
    if not category or not trace or not trace.get("match_via_script"):
        return category
    if category.get("category") not in ("full", "adjusted"):
        return category
    return {**category,
            "label": f"{category.get('label') or 'explained'} · read from the script",
            "reason": ("the laws reach a form the word's own signs allow, and the "
                       "dictionary's reading agrees with it — the spelling is a "
                       "separate layer from the sounds"),
            "via_script": True}


def _loan_of(entry: dict, lang: str) -> dict | None:
    """The donor the record names, for a word that came from outside the family.

    The page prints "borrowed from Arabic" — and, when the donor's history is
    tabulated, the window in which it reached this language — instead of the
    bare band name.  The band itself does not change: it is still ``non_pie``,
    and `categories.verdict` decides that before this is read (2026-11-09).
    """
    try:
        from . import loans

        row = loans.donor(entry, lang)
        if not row:
            return row
        # What the donor's own entry says above it (2026-11-10: "you can
        # also show the hierarchy above the source language in the etymology").
        # It is the donor word's own record, read from the donor's glossary —
        # not a claim about this word, which borrowed a finished form.
        donor_word = str(row.get("form") or "").strip()
        rows = word_index().get((row.get("code") or "", donor_word)) or []
        donor = next((e for e in rows if not e.get("recon")), rows[0] if rows else None)
        if donor:
            row["above"] = [
                {"lang": l, "lang_name": _lang(l).get("name", l), "form": w, "rel": rel}
                for l, w, rel in _ancestry_triples(donor) if rel != "root"
            ][:6]
            row["donor_pos"] = donor.get("pos") or ""
            row["donor_gloss"] = (donor.get("gloss") or [""])[0]
            # Only the donor's own sentence says whether its pieces were joined
            # ("δεινός + σαῦρος") or simply lie above it in a chain; two rows
            # are not by themselves a compound (2026-11-10).
            row["donor_joined"] = "+" in str(donor.get("etym") or "")
        return row
    except Exception:
        return None


def _backlog_of(entry: dict, chain: list[str]) -> list[dict]:
    """Backlog findings for this entry, empty for a record that agrees with itself."""
    try:
        from . import dubious
        return dubious.flags(entry, chain)
    except Exception:
        return []


def _derive_for_entry(entry: dict, chain: list[str],
                      disabled: Iterable[str] = (),
                      enabled: Iterable[str] = ()) -> dict | None:
    """Derive this word from the ancestor that explains it best.

    An exact match (the rules reproduce the attested form character for
    character) wins, and among exact matches the deepest one — the one that
    starts closest to Proto-Indo-European. Without an exact match the page
    shows the full PIE path, which is where the missing rules are.

    ``disabled`` carries the word's own pathway, so the answer the page gives
    at the top agrees with the ladder and the branch below it.
    """
    lang = entry.get("lang") or chain[-1]
    target = detokenize(tokenize(entry["word"]))
    spellings = [target] + attested_spellings(entry)
    enabled = list(enabled)
    candidates = ancestor_starts(entry, chain, keep_formed=bool(enabled))
    if not candidates:
        return None

    def fit_of(form: str) -> dict | None:
        """The reading of the word's own script that ``form`` may be.

        Old Persian is written in a syllabary: the laws produce *wˈarkah* and
        the monument writes 𐎺𐎼𐎣, and the two are the same word without
        either string being a misspelling of the other (2026-11-08).  An abjad
        fit must also agree with the reading the dictionary records — the
        signs alone cannot tell دوش read dōš from the laws' dūšā (2026-11-12).
        """
        return _script_fit(entry, form)

    chosen = None
    matched = None
    scripted = None
    for stage, form in candidates:
        start = chain.index(stage)
        d = derive(form, chain[start:], data.rulesets(), disabled=list(disabled),
                   enabled=enabled)
        if d.skipped:
            continue
        hit = _match_spelling(d.output, spellings)
        found = fit_of(d.output) if not hit else None
        if (hit or found) and d.steps:
            chosen = (stage, form, d)
            matched, scripted = hit, found
            break
    if chosen is None:
        stage, form = candidates[0]
        d = derive(form, chain[chain.index(stage):], data.rulesets(), disabled=list(disabled),
                   enabled=enabled)
        chosen = (stage, form, d)
        matched = _match_spelling(d.output, spellings)
        scripted = fit_of(d.output) if not matched else None
    stage, form, d = chosen
    start = chain.index(stage)
    return {
        "input": form,
        "start": stage,
        "start_name": _lang(stage).get("name", stage),
        "start_variety": _variety_at(entry, stage, form),
        "chain": [{"id": c, "name": _lang(c).get("name", c)} for c in chain[start:]],
        "forms": d.forms,
        "steps": [s.__dict__ for s in d.steps],
        "skipped": d.skipped,
        "target": target,
        "match": matched is not None or scripted is not None,
        # True when the rules reproduce the word's recorded romanisation rather
        # than its own script (پدر → pedar): the phonology is exact, the
        # orthography is a separate layer and the page says so.
        "match_via_translit": matched is not None and matched != target,
        # True when the form is a reading the word's own writing system allows
        # (𐎺𐎼𐎣 is va-ra-ka, and the laws give wˈarkah) — a claim about the
        # script, stated with the signs it was made from.
        "match_via_script": scripted is not None,
        "fit": scripted,
        "matched_form": matched,
    }


def _recorded_at(entry: dict, lang: str,
                 etymon: tuple[str, str] | None = None) -> dict[str, dict]:
    """The forms Wiktionary records at each stage of a word's ancestry.

    The order is the one the dictionary gives (the first is the lemma); a cell
    may hold several spelling variants. The word itself is always recorded at
    its own stage even when no ancestry row repeats it.

    ``etymon`` is the (stage, form) the ladder starts from when that start was
    not taken from the word's own ancestry rows — English *book* reaches
    Proto-Indo-European only through its cognate set. Without this the top rung
    of such a ladder claimed "nothing recorded" beside a cognate section that
    quoted the root's meaning (2026-11-07). The start is looked up in
    that stage's own glossary, so the rung shows the record the dictionary
    holds — a root with its gloss — and never an invented one.
    """
    out: dict[str, dict] = {}

    def add(stage: str, raw: str, origin: str) -> None:
        bucket = out.setdefault(stage, {"forms": [], "origin": origin})
        for part in re.split(r"[,;]", raw or ""):
            candidate = normalise_etymon(part)
            if candidate and candidate not in bucket["forms"]:
                bucket["forms"].append(candidate)
                # A script headword quoted from an ancestry row usually carries
                # its reading in the same sentence — "Old Persian 𐎲𐎠𐏀𐎢
                # (bāzu)" — and the rung must be readable without opening the
                # dictionary (2026-11-08). The reading is taken from
                # that sentence, never guessed from the letters.
                reading = (_etymology_reading(entry.get("etym") or "", candidate)
                           or (readings_index.for_form(stage, candidate) or {}).get("reading", ""))
                if reading:
                    bucket.setdefault("readings", {})[candidate] = reading

    # A row at the word's own stage that names the base of the word's own
    # construction is that construction's base, not another record of the
    # stage: *h₂eh₂óyḱe lists its root *h₂eyḱ- among the ancestry rows, and
    # the rung must not print the root's grammar and meaning beside the word
    # (admin, 2026-11-12).
    own = _own_construction(entry, [lang])
    own_bases = {normalise_etymon(str((piece or [""])[0] or ""))
                 for piece in (own or {}).get("pieces") or []}
    for stage, word, _rel in _ancestry_triples(entry):
        if (stage == lang and own_bases
                and normalise_etymon(word) in own_bases):
            continue
        add(stage, word, "ancestry")
    add(lang, entry["word"], "word")
    if etymon:
        stage, form = etymon
        if stage not in out:
            record = _lemma_entry(stage, form)
            if record:
                add(stage, record["word"], "glossary")
    for stage, bucket in out.items():
        if not bucket["forms"]:
            continue
        # What the word meant at that stage, when the stage's own glossary has
        # it: the ladder is a history, not only a string of spellings.
        # The word's own stage is read from the entry the page opened, not
        # from the first homograph of that spelling (2026-11-12, دوش).
        record = (entry if stage == lang and bucket["forms"][0] == entry.get("word")
                  else _lemma_entry(stage, bucket["forms"][0]))
        if record:
            bucket["pos"] = record.get("pos", "")
            bucket["gloss"] = _rung_gloss(record.get("gloss") or [])
            # The stage's own entry may record how its headword is read: the
            # supplement for Middle Persian 𐫀𐫡𐫘 (ars) is the record, not a
            # guess beside it (2026-11-08).
            reading = readings_for(record)["reading"]
            if reading:
                bucket.setdefault("readings", {})[bucket["forms"][0]] = reading
    return {stage: bucket for stage, bucket in out.items() if bucket["forms"]}


def _etymology_reading(etym: str, form: str) -> str:
    """The reading a dictionary writes beside a script form, if it writes one.

    An etymology names the older word and often reads it in the same
    parenthesis — "Old Persian 𐎲𐎠𐏀𐎢 (bāzu)", "Middle Persian 𐫀𐫡𐫘 (ʾrs
    /⁠ars⁠/, “tear”)". A slashed reading wins over the transliteration, and a
    parenthesis that is not a reading (a gloss, an author) yields nothing:
    the page must never invent a pronunciation from letters it cannot read
    (2026-11-08).
    """
    if not etym or not form:
        return ""
    found = re.search(re.escape(form) + r"\s*\(([^()]{1,90})\)", etym)
    if not found:
        return ""
    inside = found.group(1)
    slashed = re.search(r"/([^/]{1,60})/", inside)
    if slashed:
        return slashed.group(1).replace("\u2060", "").strip()
    token = inside.strip().split()[0].strip(" ,;.”\"'")
    # A transliteration is letters; a gloss such as “tear” is not a reading.
    return token if re.fullmatch(r"[^\W\d_][\w\u0300-\u036fʰʷʲˠʼ ]{0,40}", token) else ""


def _level_evidence(status: str, recorded_span: str, tiers: list[str], steps: int) -> str:
    """Which evidence colour a ladder rung earns (see ``_rebuild_evidence``)."""
    if status == "match":
        return "literary" if recorded_span == "proto" else "attested"
    if status in ("differs", "unverified"):
        return "weak"
    if not steps or any(tier != "established" for tier in tiers):
        return "weak"
    return "strong"


def _pathway_for(lang: str, word: str, disabled: Iterable[str],
                 pathway: bool) -> tuple[list[str], list[str], dict | None]:
    """The laws this word's ladder runs with: the reader's switches, plus its pathway.

    A stored *default* pathway says that a registered law never applied to this
    word (Middle English ``wolf`` is spelled with ⟨o⟩ but has /u/).  It is not a
    suggestion to load: the word's page opens with it, the ladder shows which
    law is off and why, and ``pathway=0`` is how a reader sees the law applied
    anyway.  Nothing is hidden: the switched-off law stays in the list.

    A pathway may also *switch a law on* (``enabled``): a formation law such as
    the animal suffix *-ka- is registered off by default, because it adds a
    morpheme and must never touch a word that does not wear that suffix. The
    word whose record says it is formed with it turns it on (Persian گربه,
    2026-11-08).  A law the reader has switched off stays off even when the
    pathway turns it on.
    """
    off = {d for d in disabled if d}
    on: set[str] = set()
    record = pathways.default_for(lang, word) if pathway else None
    if record:
        off |= {d for d in (record.get("disabled") or []) if d}
        on |= {e for e in (record.get("enabled") or []) if e}
    on -= off
    return sorted(off), sorted(on), record


def _offered_suffixes(stage: str) -> list[dict]:
    """The suffix choices a ladder rung may offer without listing the corpus.

    The full registry is the picker under the headword; a rung's chip line is a
    different question — which *registered formation* this word could have worn
    instead — so it keeps the hand-written rows and the ones that name a law,
    and leaves the hundred composed-here pieces to the picker (2026-11-08).
    """
    return [suf for suf in (morphology(stage) or {}).get("suffixes") or []
            if suf.get("curated") or suf.get("rule")]


def _suffix_hypothesis(entry: dict, suffix: str) -> dict | None:
    """What this word would be if it wore another registered suffix.

    A suffix is a formation law: it adds a cited morpheme to a base, and only a
    word whose record says it wears one has it switched on. The reader may ask
    the opposite question — what would the laws give with *-eh₂* instead of
    *-ka-*? — so the base the record names is composed with the chosen suffix
    and the ordinary chain then runs from there. Nothing here is substituted
    for the word: the payload's ``hypothesis`` names the suffix and the page
    says the ladder no longer describes this word (2026-11-08).
    """
    formed = entry.get("formed") or {}
    pairs = formed.get("from") or []
    if not suffix or not pairs:
        return None
    stage, base = pairs[0][0], normalise_etymon(pairs[0][1])
    composed = compose(base, suffix, stage)
    form = (composed or {}).get("form") or ""
    if not form or normalise_etymon(form) == base:
        return None
    options = [
        {"id": suf["id"], "form": suf["form"], "gloss": suf["gloss"],
         "law": bool(suf.get("rule")), "active": suf["id"] == suffix}
        for suf in _offered_suffixes(stage)
    ]
    return {
        "stage": stage,
        "stage_name": _lang(stage).get("name", stage),
        "base": base,
        "composed": form,
        "options": options,
        "suffix": composed.get("suffix") or {"id": suffix, "form": suffix},
        "law": composed.get("law"),
        "law_not_applied": composed.get("law_not_applied"),
        "steps": composed.get("steps") or [],
    }


def _formation_options(entry: dict, stage: str, rule: dict) -> dict | None:
    """The cited suffix a formation law adds, beside the ones it could have been.

    Only a word whose record is a formation gets the choice: for every other
    word a suffix would be an invention. The active suffix is the one whose
    registered law is the law that just applied, so the page can print it in the
    word and let the reader try a neighbour.
    """
    if not ((entry.get("formed") or {}).get("from")):
        return None
    options = []
    active = None
    for suf in _offered_suffixes(stage):
        item = {"id": suf["id"], "form": suf["form"], "gloss": suf["gloss"],
                "law": bool(suf.get("rule")),
                "active": suf.get("rule") == rule.get("key")}
        if item["active"]:
            active = suf
        options.append(item)
    if not options:
        return None
    return {
        "law": rule.get("key"), "name": rule.get("name"),
        "stage": stage, "stage_name": _lang(stage).get("name", stage),
        "suffix": (active or {}).get("form", ""),
        "surface": (active or {}).get("surface", ""),
        "options": options,
    }


def _own_stage_entry(stage: str, form: str, word_entry: dict | None) -> dict | None:
    """The page's own entry when this rung is the word the page is about.

    A spelling can carry several words — Persian دوش is a shower, a shoulder
    and *last night* — and they have different meanings, readings and even
    origins.  Looking the rung up by spelling returns the first homograph, so
    the shoulder's final rung printed "shower (bathing)" and was matched
    against the shower's reading.  The page's entry is the only correct
    record for that rung (2026-11-12).
    """
    if not word_entry:
        return None
    if (word_entry.get("word") or "") != form:
        return None
    if word_entry.get("lang") and stage != word_entry["lang"]:
        return None
    return word_entry


def _record_block(stage: str, here: dict | None, match_form: str | None,
                  word_entry: dict | None, prefer: str | None = None) -> dict | None:
    """What a stage records for a form, whether or not the laws produced it.

    ``here`` is what the word's own ancestry (or its glossary) holds for this
    stage; a record is read from it the way the word page reads it — by its
    headword, its recorded reading, or the signs its script allows — and the
    block says which. A stage the ancestry does not reach falls back to that
    stage's own glossary, so a rung carried further down still quotes a record
    (2026-11-08).
    """
    near = None
    if not here and match_form:
        # A stage the word's own ancestry does not reach — a descendant the
        # reader carried it into — still has a record of its own, and the
        # ladder quotes it the same way (2026-11-08).
        found = _record_for_form(stage, match_form)
        if found:
            here = {"forms": [found["w"]], "pos": found.get("pos", ""),
                    "gloss": found.get("gloss", ""),
                    "origin": "reading" if found.get("via") == "reading"
                    else ("script" if found.get("via") == "script" else "glossary")}
        else:
            # Nothing verifies the form, but a record may still reproduce every
            # sound of it but the ending. The rung quotes it and says the match
            # is unverified, so the record is neither hidden nor claimed
            # (2026-11-12).
            near = _near_record(stage, match_form) or _script_record(
                stage, match_form, loose=True)
            if near:
                here = {"forms": [near["w"]], "pos": near.get("pos", ""),
                        "gloss": near.get("gloss", ""), "origin": "near"}
    if not here:
        return None
    forms = here["forms"]
    primary = forms[0]
    # A stage may record more than one ancestor form — dáwxšati's PIE row holds
    # the root *dewk- and the word *déwk-s-eti the ladder starts from. The rung
    # must quote the form it actually starts from, not whichever the dictionary
    # listed first, or the page shows the root beside a ladder that begins
    # elsewhere (2026-11-09).
    for candidate in forms:
        if (prefer and _same_form(prefer, candidate)) or \
                (not prefer and match_form and _same_form(match_form, candidate)):
            primary = candidate
            break
    # The rung quotes the sense the child's sentence gives this ancestor, not
    # whichever homonym the glossary lists first (2026-11-12: *swer- "to ache"
    # stood under *swarō "oath", whose own sentence says "to speak").
    stage_entry = (_own_stage_entry(stage, primary, word_entry)
                   or _sense_entry(stage, primary,
                                   _ancestor_gloss(word_entry or {}, primary)))
    if stage_entry is word_entry:
        pron = {**readings_for(word_entry), "documented": True}
    else:
        pron = pronunciation(stage, primary)
    # A record quoted from an ancestry row carries the reading the
    # dictionary wrote beside it (𐎲𐎠𐏀𐎢 bāzu), so the rung never shows a
    # cuneiform word with no way to read it (2026-11-08).
    written = (here.get("readings") or {}).get(primary, "")
    if written and not pron["reading"]:
        pron["reading"] = written
    # A row may spell the word without a sign the headword carries — Old
    # Persian 𐎼𐎢𐎨 for 𐎼𐎢𐎨𐏃, whose final /h/ no cuneiform sign writes.
    # One reading then belongs to one word, and the stage does hold it: the
    # record is the spelling the row quoted, and `headword` is the entry the
    # page opens and takes the meaning from.  Without this the rung called a
    # word the glossary has "no entry for this word" (admin, 2026-11-12).
    headword = None
    if stage_entry is None:
        for spelled in (pron["reading"], written):
            key = _plain_form(spelled) if spelled else ""
            found = _reading_index(stage).get(key) if key else None
            if not found:
                continue
            candidate = _lemma_entry(stage, found[0])
            if candidate:
                stage_entry, headword = candidate, found[0]
                break
    matches = bool(match_form) and any(_same_form(match_form, f) for f in forms)
    via = None
    readings = [pron["reading"], *(attested_spellings(stage_entry) if stage_entry else [])]
    if not matches and match_form and any(readings):
        # A record written in its own script is matched by its reading:
        # Pahlavi gwlg is the word MacKenzie reads gurg, and the laws
        # produce gurg (2026-11-08, Persian گرگ). Every reading the
        # dictionary records is accepted — Persian پدر is padar, pidar and
        # pedar at once.
        via = _match_spelling(match_form, [r for r in readings if r])
        matches = via is not None
    fit = None
    if match_form:
        # The record is written in a script whose signs allow the form as a
        # reading: 𐎺𐎼𐎣 (va-ra-ka) for wˈarkah. The block carries what the
        # scribe wrote, so the page prints both (2026-11-08). It is computed
        # even when a recorded reading already matched: the reading and the
        # signs are two facts, and the page that shows the green must show the
        # letters it was read from (2026-11-09: k-a-r is not a spelling of
        # kāraʰ, and the rung had stopped naming the signs).
        for recorded_form in forms:
            candidate = script.match(stage, match_form, recorded_form)
            if not (candidate and candidate["ok"]):
                fit = None
                continue
            fit = candidate
            # The signs allow this form — but when the dictionary also says how
            # it *reads* the spelling, that reading is the target, and a fit
            # beside a different one is not a match.  An abjad's l-w-c can be
            # read rōč and rōz; the record says rōz, and a green rung would
            # claim the laws produced it (2026-11-11).  When the reading and
            # the form differ only in what the *writing* leaves out (the final
            # /h/ no Old Persian sign writes, a final -i closed by the y-sign),
            # the two are one reading and the fit stands (2026-11-08).
            if not any(readings) or _same_reading(candidate, match_form, readings):
                matches = True
                if via is None:
                    # Name the reading the match was made on when it is not the
                    # headword's first: دوش is read dōš, and dūš matches duš.
                    via = _abjad_reading(candidate, match_form, readings)
            break
    # One word, several headings: the rung stands for the *word*, so it prints
    # the parts of speech and meanings the glossary merges for it.  *aiganaz
    # is a participle and an adjective of one Wiktionary page with one
    # etymology, and a rung that quoted only the first heading said "past
    # participle of *aiganą" where the word means "own" (admin, 2026-11-12).
    pos_text = (stage_entry or {}).get("pos")
    gloss_list = list((stage_entry or {}).get("gloss") or [])
    if stage_entry and len(word_index().get((stage, primary)) or ()) > 1:
        readings_group = _group_of(_senses_for((stage, primary)), stage_entry)
        if readings_group and len(readings_group["entries"]) > 1:
            pos_text = " / ".join(readings_group["pos"])
            gloss_list = list(readings_group["gloss"])
    payload = _with_reading({
        "w": primary,
        "more": [f for f in forms if f != primary][:6],
        "evidence": evidence_for(primary, stage),
        "kind": kind_of(stage),
        "script": _lang(stage).get("script", ""),
        "in_script": _in_native_script(stage, primary),
        "recon": is_reconstructed(stage, primary),
        "show_reading": show_reading(stage, primary),
        "ipa": pron["ipa"],
        "reading": pron["reading"],
        # What this form means, from its own entry. The bucket's gloss and part
        # of speech belong to the form the dictionary listed first, and that is
        # not always the one the rung quotes (*déwk-s-eti is not the root
        # *dewk-, and the root's "to pull, to draw" is not the word's meaning),
        # so a form with no entry of its own claims nothing (2026-11-09).
        "pos": (pos_text if stage_entry else ""),
        "gloss": (_rung_gloss(gloss_list) if stage_entry
                  else (here.get("gloss", "") if primary == forms[0] else "")),
        # Where the record comes from. A green form must be able to say so;
        # a record quoted from Wiktionary's ancestry has no entry of its
        # own at this stage, so the word page it came from is the source.
        "sources": (_entry_sources(stage_entry) if stage_entry
                    else _entry_sources(word_entry or {})),
        # Only a page of *this* form is a door: a record quoted from the word's
        # own article has no entry of its own, and its corner shows no icon even
        # though the article it was read in has one (admin, 2026-11-12).
        "pages": (_entry_pages(stage_entry) if stage_entry else []),
        # Where the record comes from: the word's own ancestry rows, its
        # glossary entry, or the cognate set that supplied the etymon.
        "origin": here.get("origin", ""),
        "matches": matches,
        # The downstream verdict reads this: a record quoted from an ancestry
        # row that the laws do not reproduce is not a match (2026-11-08).
        "exact": bool(matches),
        "via": via,
        # What the script writes for a form it allows as a reading. Green
        # is a claim about the record; the form beside it is one reading of
        # that record, and the block says which signs it was read from.
        "fit": fit,
        # Two spellings, one consonant (OP *daivaʰ* / laws *daiwˈah*): the
        # page explains the letter instead of pretending to a match.
        "notation": None if (matches or fit) else _notation_only(match_form or "", pron["reading"]),
        # Whether the stage's own glossary holds this word. A record quoted
        # from Wiktionary's ancestry rows (Proto-Iranian *jráyah*) may have no
        # entry of its own, and then the page links to the "not recorded here"
        # view rather than a 404 (2026-11-08).  A quotation spelled without a
        # sign the headword carries is the same word, and `headword` says which
        # entry holds it (2026-11-12).
        "known": bool(stage_entry),
        # A stage without a glossary says nothing about the word: the rung is
        # a quotation, and the page prints that instead of "no entry".
        "modelled": _has_glossary(stage),
        "headword": headword or "",
    }, stage, primary)
    if near:
        payload["unverified"] = True
        payload["review"] = near.get("review") or {"form": match_form,
                                                   "record": near.get("reading", "")}
    if (payload.get("reading_auto") and stage_entry
            and stage_entry.get("source") == "dehkhoda"
            and not (stage_entry.get("translit") or stage_entry.get("translit_alt")
                     or stage_entry.get("ipa"))):
        # The rung shows a reading only when a dictionary records one: spelling
        # a Persian headword letter by letter (آب‌خانه → ā-b-x-ā-n-h) is the
        # alphabet, not the word (2026-11-10, the Dehkhoda headwords).
        payload.update({"reading": "", "reading_auto": False, "show_reading": False})
    return payload


def hierarchy(lang: str, form: str, disabled: Iterable[str] = (),
              from_stage: str | None = None, from_form: str | None = None,
              pathway: bool = True, suffix: str | None = None,
              path: Iterable[str] | None = None,
              enabled: Iterable[str] = (),
              from_recorded: bool = False,
              sense: int | str | None = None,
              build: str | None = None,
              _above: tuple = ()) -> dict | None:
    """The word's ancestry as a ladder, ancestor first, with its sound laws.

    Each rung is a language stage with the form the registered law chain
    produces for it, the date range the language was in use, and the laws that
    applied on the way down. A law may be switched off (``disabled``); the whole
    ladder is then recomputed, so every rung below shows the altered result and
    ``changed`` marks the forms a switched-off law moved. A second run with no
    laws disabled supplies ``baseline`` for that comparison.

    ``from_stage``/``from_form`` start the ladder at a form the reader typed
    instead of at the recorded ancestry, so the page can answer "what happens
    if this stage looked like *that*". That rung is marked ``edited`` and earns
    its own evidence colour: a typed form is a hypothesis, not a record.

    ``from_recorded`` says the form in ``from_form`` is not a hypothesis but
    one of the ancestor forms this word's own record quotes. The ladder then
    starts there as a *record*, without the edited badge, and the stages above
    it are listed rather than derived. The payload's ``starts`` names every
    such form and whether the laws reach the word from it, which is what the
    page offers as buttons (2026-11-09).

    ``pathway`` is on unless the reader asked to see the laws unfiltered: a
    stored default pathway for this word then switches its own laws off, and
    the record it comes from is returned in ``pathway`` so the page can say so.

    ``suffix`` asks a different question: what would the laws give if this word
    wore another registered suffix? A suffix is a formation law, so the answer
    is computed by composing the word's recorded base with the chosen suffix
    and then running the same chain — the payload says in ``hypothesis`` which
    suffix was tried, and every rung keeps saying what the record holds, so the
    reader is never shown a guess as the word (2026-11-08: change the
    suffix in the timeline view).

    ``build`` asks a third question: what would this word be if a stage's form
    were *made* rather than inherited?  A word may be built out of two recorded
    words of one stage, or out of one word plus a recorded suffix or ending, and
    that join belongs on the timeline at the stage it happened, between the rung
    it starts from and the rung it produces.  The composed rung is a formation,
    never a sound law: the payload marks it ``built`` and the page says so
    (2026-11-10).

    ``path`` carries the timeline on past the word's own stage: one stage per
    click, each a direct child of the rung above it (``data.descendants``),
    with the form its registered laws produce and, beside it, whatever that
    language records. A word in Old Persian can therefore be followed into
    Middle Persian and Persian without pretending to be a PIE etymon
    (2026-11-08). ``next`` in the payload is the list of children
    the reader may add next, each with its default reconstruction.

    The top of the ladder is not the end of the story.  A record often quotes
    the ancestor form and stops there — Proto-Iranian *čiθráh says "from
    Proto-Indo-Iranian *čitrás" and no more — while that ancestor's own page
    climbs to Proto-Indo-European and shows what built it.  The ladder then
    continues through the ancestor's own ladder, so the reader sees one
    timeline instead of a silence that only looks like a gap in the family
    (admin, 2026-11-12: there is no limit simply because a source is silent).
    ``_above`` carries the words already climbed through, so a record that
    names a word in terms of itself cannot loop.
    """
    entries = word_index().get((lang, form))
    if not entries and "\u200c" in form:
        twin = _seam_index(lang).get(form.replace("\u200c", ""))
        entries = word_index().get((lang, twin)) if twin else None
    if not entries:
        entries = word_entries(lang, form)
    if not entries:
        return None
    # The ladder belongs to a word, not to a spelling: on a page that shows
    # the second sense of  بار, the laws start from that sense's own chain
    # (2026-11-09).
    groups = sense_index().get((lang, form)) or senses.groups(entries)
    if len(groups) > 1:
        want = _sense_number(sense) or 1
        picked = next((g for g in groups if g["sense"] == want), groups[0])
        entries = picked["entries"]
    entry = next((e for e in entries if not e.get("recon")), entries[0])
    chain = data.derivation_chain(lang)
    if not chain:
        return None
    # A borrowed word has no sound-law ladder: its record states where it came
    # from and in one step, it is there.  Running the target language's chain
    # from a root recorded *inside the donor's* etymology invented six rungs
    # for Persian دایناسور (PIE *dwey- → Proto-Iranian → … → Persian), which is
    # the one thing the record does not say.  The page draws the two rungs the
    # record does state (English dinosaur → Persian دایناسور, *borrowed*), and
    # the donor's own history belongs to the donor's own page (2026-11-10).
    try:
        from . import loans as _loans

        if _loans.classify(entry, lang):
            return None
    except Exception:
        pass

    # The timeline may be carried on past the word's own stage. Each step has
    # to be the stage the registry records as the immediate child of the one
    # above it — a hand-written list of stages would be a second, unchecked
    # model of the family (2026-11-08).
    extra: list[str] = []
    cursor = chain[-1]
    for step in path or ():
        row = data.languages().get(step)
        if not row or step in extra or row.get("ancestor") != cursor:
            break
        extra.append(step)
        cursor = step

    cog = _cognate_payload(entry["cog"]) if entry.get("cog") else None
    # A law may also be switched on for this ladder alone (a citation going in,
    # not a stored pathway yet): store_pathway validates a candidate that way.
    requested_on = {e for e in enabled if e}
    disabled, enabled, own_pathway = _pathway_for(lang, entry["word"], disabled, pathway)
    if requested_on:
        enabled = sorted(set(enabled) | requested_on)
        disabled = sorted(set(disabled))
    # The pathway's formation law may be switched *off* by the reader right now;
    # the ladder must still start where that word's record starts, so they can
    # see what the word is without the suffix.
    formed_law = bool(enabled) or bool((own_pathway or {}).get("enabled"))
    # A word the record builds out of pieces *at its own stage* has no ancestor
    # above it: {{com|ira-pro|*cwáHdah|*pátiš}} says how the word was made, and
    # the PIE form of one piece is not the compound's inheritance. The ladder
    # starts at the word itself and prints the pieces beside that rung
    # (proposals/011, 2026-11-09). `ancestor_starts` stays a statement about
    # ancestors, so the coverage counter's `identified` column is unchanged.
    own = _own_construction(entry, chain)
    candidates = ancestor_starts(entry, chain, keep_formed=formed_law)
    if own:
        candidates = [(own["stage"], str(entry.get("word") or ""))]
    # A compound's cognate set belongs to one of its pieces, not to the whole
    # word: *pótis is the etymon of *pátiš, and a ladder may not start there.
    pie = None if own else ((cog or {}).get("pie") or _pie_form(entry))
    formed = bool(_formed_from(entry))
    linked_by_set = (bool(pie) and not formed
                     and not any(stage == chain[0] for stage, _w in candidates))
    # A cognate set that names only a *root* is not an ancestor to start from:
    # Proto-Iranian *háwmah is not derived from the PIE root *sewh₁ ('to
    # squeeze'), it is related to it, and no sound law turns a root into a
    # suffixed noun — the ladder then showed a red rung for a word its own
    # record derives exactly. The word's recorded Proto-Indo-Iranian form is
    # the honest start, and the root stays above the ladder as the cognate it
    # is (proposals/010, 2026-11-09). `linked_by_set` stays true: the word
    # still reaches PIE only through the set, and the page still says so.
    set_is_root = bool(linked_by_set) and _is_root_etymon(chain[0], pie)
    if linked_by_set and not set_is_root:
        # A cognate set links the word to an etymon even when Wiktionary's own
        # ancestry rows stop lower down; that is still a known ancestor.
        candidates.insert(0, (chain[0], normalise_etymon(pie)))
    if not candidates:
        # A word whose record names no ancestor still has a timeline: one rung,
        # itself, saying plainly that nothing above it is recorded.  Before this
        # such a word had no ladder at all, which left the Dehkhoda headwords
        # (2026-11-10) with a hole where the timeline is.  A reader who asked to
        # build one starts at the stage they named.
        # Proto-Indo-European has nothing above it, but it has a timeline all
        # the same: one rung for the word itself, and below it the daughter
        # stages the laws reach, one click each (admin, 2026-11-12).  The
        # page is a ladder like every other page's, not a second kind of view.
        spec = _parse_build(build) if build else None
        if spec and spec["stage"] in chain:
            candidates = [(spec["stage"], spec["base"] or entry["word"])]
        else:
            candidates = [(lang, entry["word"])]

    hypothesis = _suffix_hypothesis(entry, suffix) if suffix else None
    if hypothesis:
        # The composed form already wears the suffix, so the starting stage is
        # the base's own: the rest of that transition's laws still run on it,
        # but the word's own formation law is not switched on a second time.
        enabled = []

    # A *recorded* start: the reader picked one of the ancestor forms the word
    # itself quotes ("start from the Proto-Iranian form"), so the rung is a
    # record, not a typed hypothesis. It may sit above or below the default
    # topmost ancestor; either way the ladder begins there (2026-11-09).
    recorded_start: dict | None = None
    if from_recorded and from_stage and (from_form or "").strip():
        typed_here = from_form.strip()
        known = _recorded_ancestor_forms(entry, chain).get(from_stage, [])
        if any(_same_form(typed_here, form_) for form_ in known):
            recorded_start = {"stage": from_stage, "form": typed_here,
                              "name": _lang(from_stage).get("name", from_stage)}
        else:
            # Asked for a "recorded" start that this word's record does not
            # name: refuse rather than quietly showing some other ladder.
            return None
    if hypothesis:
        start_stage, start_form = hypothesis["stage"], hypothesis["composed"]
    elif recorded_start:
        start_stage, start_form = recorded_start["stage"], recorded_start["form"]
    else:
        start_stage, start_form = candidates[0]
    start = chain.index(start_stage) if start_stage in chain else 0
    edited: dict | None = None
    if from_stage and not recorded_start and (from_form or "").strip():
        # Any rung may be edited — above the word, the word itself, or a stage
        # the reader carried it into. A rung that is already on the ladder stays
        # where it is: the rungs above it are the laws' own work and keep their
        # place, and only the stages below the typed form are re-derived
        # (2026-11-08: editing a word in the hierarchy lost its
        # ancestors). A stage above the ladder's own start is not on the path;
        # typing it makes it the new starting point.
        typed = from_form.strip()
        if from_stage in chain:
            if chain.index(from_stage) < start:
                start, start_form = chain.index(from_stage), typed
        elif from_stage not in extra:
            # A stage the timeline was carried into may be edited where it
            # stands: the rungs above it are the word's own ancestry, not this
            # edit's business (2026-11-08).
            return None
        edited = {"stage": from_stage, "form": typed,
                  "name": _lang(from_stage).get("name", from_stage)}
    start_stage = chain[start]
    levels_chain = chain[start:] + extra

    def run(from_form_value: str, stages: list[str], **kw) -> tuple[Derivation, list]:
        return derive_detailed(from_form_value, stages, data.rulesets(), **kw)

    trace, hops = run(start_form, levels_chain, disabled=disabled, enabled=enabled)
    if lang == ROOT_LANG and not edited and not hypothesis and trace.forms:
        # The etymon's rung prints the form the dictionary heads, hyphen and
        # all: *ters- is a root, and *ters is only how the sound laws read it
        # (admin, 2026-11-12 — the PIE page's own rung read ters).
        own = str(entry.get("word") or "")
        if own:
            trace.forms[0] = own
    # The baseline is "the laws as registered for this word, with nothing the
    # reader switched off" — so a formation law its pathway enables is part of
    # the baseline too, and its syllable is not reported as a change.
    baseline, _ = run(start_form, levels_chain, enabled=enabled)
    if edited:
        # Splice the typed form into its rung and re-derive everything below
        # it; everything above is the chain as the laws give it.
        cut = levels_chain.index(edited["stage"])
        head, head_hops = run(start_form, levels_chain[:cut + 1],
                              disabled=disabled, enabled=enabled)
        tail, tail_hops = run(edited["form"], levels_chain[cut:],
                              disabled=disabled, enabled=enabled)
        trace = Derivation(input=start_form, chain=list(levels_chain),
                           forms=head.forms[:cut] + tail.forms,
                           steps=head.steps + tail.steps,
                           skipped=head.skipped + tail.skipped)
        hops = head_hops + tail_hops
        base_head, _ = run(start_form, levels_chain[:cut + 1], enabled=enabled)
        base_tail, _ = run(edited["form"], levels_chain[cut:], enabled=enabled)
        baseline = Derivation(input=start_form, chain=list(levels_chain),
                              forms=base_head.forms[:cut] + base_tail.forms,
                              steps=base_head.steps + base_tail.steps,
                              skipped=base_head.skipped + base_tail.skipped)

    # The rungs to print, one per (stage, form). A formation at a stage gives
    # that stage two rungs — the form the laws reach and what was built from it
    # — so the plan is longer than the chain, and every index below reads the
    # plan rather than the chain.
    rung_stages = list(levels_chain)
    rung_forms = list(trace.forms)
    rung_hops: list = [None] + list(hops)
    baseline_forms = list(baseline.forms)
    built: dict | None = None
    build_at: int | None = None
    built_above: list[str] = []
    if build and not edited and not hypothesis:
        spec = _parse_build(build)
        if spec and spec["stage"] in levels_chain:
            cut = levels_chain.index(spec["stage"])
            if spec.get("base"):
                # The base is a word of that stage in its own right — the first
                # piece of a compound — not the form the laws carried down from
                # the stage above.  The ladder then begins at that word and the
                # stages above it are listed, not derived.
                base = spec["base"]
                head = Derivation(input=base, chain=[spec["stage"]],
                                  forms=[base], steps=[], skipped=[])
                head_hops: list = []
                built_above = list(levels_chain[:cut])
            else:
                head, head_hops = run(start_form, levels_chain[:cut + 1],
                                      disabled=disabled, enabled=enabled)
                base = head.forms[cut]
            composed = _compose_build(
                spec, base, spec["stage"],
                script_ok=(spec["stage"] == levels_chain[-1]
                           and spelling.applies(spec["stage"])))
            if composed:
                tail, tail_hops = run(composed["form"], levels_chain[cut:],
                                      disabled=disabled, enabled=enabled)
                base_tail, _ = run(composed["form"], levels_chain[cut:], enabled=enabled)
                built = {**spec, **composed}
                built["stage_name"] = _lang(spec["stage"]).get("name", spec["stage"])
                built["base_chosen"] = bool(spec.get("base"))
                if built_above:
                    rung_stages = [spec["stage"]] + levels_chain[cut:]
                    rung_forms = [base] + tail.forms
                    rung_hops = [None, None] + list(tail_hops)
                    baseline_forms = [base] + base_tail.forms
                    build_at = 1
                else:
                    base_head, _ = run(start_form, levels_chain[:cut + 1],
                                       enabled=enabled)
                    rung_stages = levels_chain[:cut + 1] + levels_chain[cut:]
                    rung_forms = head.forms[:cut + 1] + tail.forms
                    rung_hops = [None] + head_hops + [None] + tail_hops
                    baseline_forms = base_head.forms[:cut + 1] + base_tail.forms
                    build_at = cut + 1
                trace = Derivation(input=start_form, chain=list(levels_chain),
                                   forms=rung_forms,
                                   steps=head.steps + tail.steps,
                                   skipped=head.skipped + tail.skipped)

    recorded = _recorded_at(entry, lang, None if edited else (start_stage, start_form))
    # The topmost stage *below PIE* that the word's own ancestry records. This,
    # not simply the next stage on the chain, is where its Wiktionary link
    # stops — the rungs between are gaps in the word's own record.
    # Read from the whole chain below PIE, not from the rungs the ladder chose
    # to print: a set-linked word's ladder starts lower, but its own record
    # still stops where it stops (book: Proto-Germanic, not Proto-West
    # Germanic). The note and the set's PIE-stage form are read from this
    # (2026-11-09).
    ancestry_top = next(
        ({"stage": stage, "name": _lang(stage).get("name", stage)}
         for stage in chain[1:] + extra if recorded.get(stage)),
        None,
    )
    # Loanwords (English *color* through Latin, Anglo-Norman and Old French)
    # record ancestors that are not stages of the chain this ladder walks. The
    # page has to say so: below the etymon rung it follows the chain, not the
    # borrowing.
    off_chain: list[dict] = []
    for stage, _word, _rel in _ancestry_triples(entry):
        if stage not in levels_chain and all(row["stage"] != stage for row in off_chain):
            off_chain.append({"stage": stage, "name": _lang(stage).get("name", stage)})
    # Whether the ladder actually opens at the set's etymon. A root cannot be
    # a start (above), so the page needs this beside `linked_by_set` to say
    # which of the two it did.
    set_start = bool(linked_by_set and not recorded_start and not hypothesis
                     and not (from_stage and (from_form or "").strip())
                     and start_stage == chain[0])
    set_source = None
    if linked_by_set and not edited and ancestry_top and entry.get("cog"):
        above = (recorded.get(ancestry_top["stage"]) or {}).get("forms") or []
        if above:
            candidate = _set_stage_source(entry["cog"], ancestry_top["stage"], above[0])
            # Only a derived word at the PIE stage explains why the ladder does
            # not start there; the etymon itself is already `etymon`.
            if candidate and not _is_root_etymon("ine-pro", normalise_etymon(candidate)):
                set_source = candidate
    spellings = [entry["word"], *attested_spellings(entry)]
    target_reading = readings_for(entry)

    def recorded_block(stage: str, match_form: str | None = None,
                       prefer: str | None = None) -> dict | None:
        return _record_block(stage, recorded.get(stage), match_form, entry, prefer)

    rows: list[dict] = []
    tiers_fired: list[str] = []
    edited_at = levels_chain.index(edited["stage"]) if edited else None
    for index, stage in enumerate(rung_stages):
        row = _lang(stage)
        era = row.get("era")
        version = rung_forms[index] if index < len(rung_forms) else trace.output
        before_disabling = (baseline_forms[index] if index < len(baseline_forms)
                            else baseline.output)
        hop = rung_hops[index] if index < len(rung_hops) else None
        if hop is not None:
            tiers_fired.extend(sorted({r["tier"] for r in hop.rules if r.get("fired")},
                                      key=lambda t: TIERS.index(t) if t in TIERS else 9))

        matched_form = None
        match_form = None if index == 0 else version
        # One verdict per rung, from the rung's own record: the laws produce
        # this form, and the stage holds this word (exactly, through its
        # romanisation, or as a reading of its script).
        # The top rung quotes the record it starts from, even when the stage's
        # ancestry lists another form first (2026-11-09).
        if build_at is not None and index in (
                build_at, build_at - 1 if (built or {}).get("base_chosen") else -1):
            # A built rung and the base it was built from are forms of their
            # own: the word's own record at this stage describes neither of
            # them, so each quotes what the stage's glossary holds of *it*.
            block_here = _record_block(stage, None, version, entry)
        else:
            prefer_here = start_form if index == 0 else None
            if (index == 0 and stage == lang
                    and _same_form(version, str(entry.get("word") or ""))):
                # The top rung prints the word itself, so the record it quotes
                # has to be the word's own entry.  A reduplicated stative lists
                # the root it repeats among its ancestry rows (a relation, not a
                # step), and preferring the ladder's start quoted the *root's*
                # grammar and meaning beside the word (admin, 2026-11-12).
                prefer_here = str(entry.get("word") or "")
            block_here = recorded_block(stage, match_form, prefer=prefer_here)
        if index == 0:
            status = "start"
        elif block_here is not None and block_here.get("matches"):
            status = "match"
            if stage == lang and not _same_form(version, block_here["w"]):
                matched_form = version
        elif block_here is not None and block_here.get("unverified"):
            status = "unverified"
        else:
            status = "differs" if block_here is not None else "derived"
        if index == edited_at:
            # A typed form is a hypothesis. If it happens to be the recorded
            # form at that stage it keeps its record colour; otherwise the rung
            # says plainly that nothing attests it.
            here = (recorded.get(stage) or {}).get("forms") or []
            same = any(_same_form(version, f) for f in here)
            evidence = evidence_for(version, stage) if same else "edited"
        else:
            evidence = ("literary" if kind_of(stage) == "proto" else "attested") if index == 0 else \
                _level_evidence(status, kind_of(stage), sorted(set(tiers_fired)), len(trace.steps))

        built_here = None
        if build_at is not None and index == build_at and built is not None:
            built_here = {**built, "of": version,
                          "recorded": bool(_lemma_entry(stage, version))}
        formation = None
        rules = []
        if hop is not None:
            for rule in hop.rules:
                if not rule.get("fired") and not rule.get("disabled"):
                    continue
                rules.append({
                    "key": rule.get("key") or rule["id"],
                    "id": rule["id"], "name": rule["name"], "tier": rule["tier"],
                    "before": rule["before"], "after": rule["after"],
                    "would": rule.get("would"),
                    "fired": bool(rule.get("fired")), "disabled": bool(rule.get("disabled")),
                })
                if rule.get("fired") and rule.get("tier") == "formation" and formation is None:
                    formation = _formation_options(entry, hop.src, rule)
        # The top rung is the ladder's starting point, not something derived:
        # it gets no ✓/differ verdict, only the record it starts from.
        block = block_here
        if block and block.get("reading") and version and _same_form(block["reading"], version):
            # The rung already prints the reading on the left — it is the form
            # the laws produced — so the record beside it does not repeat the
            # same string: 𐎼𐎢𐎨 · raučah is one layer written, one layer read
            # (2026-11-11).
            block["show_reading"] = False
        if block and stage == lang and status == "match":
            # The word is written in its own script; the laws produce its
            # recorded romanisation (پدر → pedar) or a reading its signs allow
            # (𐎺𐎼𐎣 for wˈarkah), so the rung is still a match — and
            # ``recorded_block`` has already said which of the two it is.
            block["matches"] = True
        if block:
            # Whether the form the laws produce *is* the recorded form, notation
            # aside (*bōks / bōks, bʰeh₂g- / bʰeh₂g). The ladder prints such a
            # rung once, glowing, instead of repeating the form below it.
            block["same"] = (bool(normalise_etymon(version))
                             and _same_form(normalise_etymon(version),
                                            normalise_etymon(block["w"])))
            # The ladder's first rung is the record it starts from, not
            # something a law derived: same form, different claim.
            block["starts"] = bool(index == 0 and not edited and block["same"])
        builds = _rung_builds(entry, stage, version)
        if not builds and stage != lang:
            # A rung above the headword is explained by its *own* entry: the
            # Proto-Indo-European ancestor of Proto-Iranian *háxā is
            # *sekʷ- + *-éh₂ + *-ṓy, stated in PIE's article and nowhere in the
            # Proto-Iranian one.  The page keeps going up, so the step that
            # made that ancestor belongs on its rung (admin, 2026-11-12).  Only
            # the record's rows are read: the seam reader's guess belongs to
            # the page the word has, not to an ancestor's rung.
            above = _lemma_entry(stage, version)
            if above:
                builds = _rung_builds(above, stage, version, record_only=True)
        rows.append({
            "stage": stage,
            "name": row.get("name", stage),
            "short": row.get("short", stage),
            "kind": kind_of(stage),
            # A rung of a language outside the family (Arabic above a Persian
            # word) is not a missing entry: the model keeps no glossary there,
            # and the page says "non-PIE word" (admin, 2026-11-13).
            "non_ie": stage in data.non_ie_sources(),
            "branch": row.get("branch", ""),
            "script": row.get("script", ""),
            "era": era,
            "era_label": era_label(era),
            "era_mid": era_midpoint(era),
            "form": version,
            "baseline": before_disabling,
            "changed": version != before_disabling,
            "status": status,
            "edited": index == edited_at,
            "evidence": evidence,
            "show_reading": False,
            "recorded": block,
            # Whether the laws' own form is a headword of this stage. Both the
            # produced and the recorded form open a page; this says which page
            # is the record and which one is the "not recorded here" view.
            "form_known": bool(_lemma_entry(stage, version)),
            "matched_form": matched_form,
            "rules": rules,
            "formation": formation,
            # The constructions the record states for this rung's form:
            # *déwk-s-eti is *dewk- + *-seti (2026-11-09), and a word may be
            # stated more than one way (2026-11-12: `builds` is the list the
            # tabs read, `built_as` the first for older callers).
            "built_as": builds[0] if builds else None,
            "builds": builds,
            # This rung is a formation the reader asked for — two words joined,
            # or a word with a suffix or ending — not a form the laws carried
            # down (2026-11-10).
            "built": built_here,
            "transition": {"from": hop.src, "to": hop.dst,
                           "missing": hop.missing,
                           "unreadable": bool(getattr(hop, "unreadable", False)),
                           "fired": sum(1 for r in hop.rules if r.get("fired")),
                           "silent": sum(1 for r in hop.rules
                                         if not r.get("fired") and not r.get("disabled")),
                           "switched_off": sum(1 for r in hop.rules if r.get("disabled"))}
                          if hop is not None else None,
        })

    # The orthographic layer is a separate claim, so it gets a separate field:
    # the phonemic form the laws produce, and the word the writing conventions
    # spell from it.  A spelling that lands on the recorded word is a *spelling*
    # match, not a sound-law reconstruction, and is never merged into `result`.
    written = None
    written_match = False
    if spelling.applies(lang):
        for row in rows:
            if row["stage"] == lang:
                candidate = spelling.spell(row["form"], lang)
                rec = row.get("recorded") or {}
                target_form = str(rec.get("w") or "")
                written_match = bool(target_form) and (
                    _comparison_key(candidate) == _comparison_key(target_form)) and (
                    spelling.confirms(row["form"], target_form,
                                      target_reading.get("ipa") or "", lang))
                # Only offer the written form when the conventions land on the
                # recorded word.  A guess that merely looks closer is noise on
                # a page whose job is to state what is explained and what is not.
                if written_match:
                    written = candidate
                    row["written"] = candidate
                    row["written_match"] = written_match
                    row["written_rules"] = len(spelling.steps(row["form"], lang))
                break
    # The dictionary may cite the stem while the laws end in an inflected form
    # (Sanskrit देव devá- against the nominative deváḥ).  That is the citation,
    # not a sound law, so it is reported as its own fact and never as a match
    # (2026-11-09).  Only an ending the language's file declares may be set
    # aside, and the remaining form must still spell the recorded word.
    cited_stem = None
    for row in rows if not written_match else []:
        if row["stage"] != lang or not row.get("recorded"):
            continue
        target_form = str((row.get("recorded") or {}).get("w") or "")
        for end, cited in citation.pairs(lang):
            form = row["form"]
            if not target_form or not form.endswith(end) or \
                    len(form) <= len(end) + len(cited):
                continue
            stem = form[: -len(end)] + cited
            if spelling.spell(stem, lang) == target_form and spelling.confirms(
                    stem, target_form, target_reading.get("ipa") or "", lang):
                cited_stem = {"stem": stem, "ending": end, "cited_as": cited,
                              "output": form,
                              "written": spelling.spell(stem, lang),
                              "stage": row["stage"]}
                row["cited_stem"] = cited_stem
                break
        if cited_stem:
            break
    if cited_stem:
        # The last rung's record is the word the dictionary cites, and the laws
        # ended on an inflected form of it: that is a citation, not a miss.  The
        # rung says so itself, so a timeline can never show a red "differs"
        # under a page that says "cited as its stem" (2026-11-09).
        last = rows[-1]
        if last["stage"] == cited_stem["stage"] and last["status"] == "differs":
            last["status"] = "cited"
    final = rows[-1]
    # What the reader may add to the timeline next: the direct children of the
    # last rung, each with the form its own transition gives. Only one level is
    # computed — the buttons are the *next* step, not the whole tree under it
    # (2026-11-08).
    next_rows = []
    if not hypothesis:
        for child in data.descendants(final["stage"]):
            if child in levels_chain:
                continue
            next_rows.append(_branch_node(
                final["stage"], final["form"], child, origin_records=recorded,
                claim=True, depth=len(levels_chain), seen=frozenset(levels_chain),
                recurse=False))
    deepest = _derive_for_entry(entry, chain, disabled, enabled)
    exact = None
    if deepest and deepest.get("match"):
        exact = {
            "stage": deepest["start"],
            "name": deepest["start_name"],
            "form": deepest["input"],
            "steps": len(deepest["steps"]),
            "via_translit": bool(deepest.get("match_via_translit")),
        }
    earlier = [
        {"id": stage, "name": _lang(stage).get("name", stage), "era_label": era_label(_lang(stage).get("era"))}
        for stage in chain[:start]
    ]

    # The stages above a recorded start are not a silence.  When the record
    # quotes an ancestor form and stops, that ancestor is a word of its own
    # with a page and a ladder, and the rest of the line is its history — the
    # construction that built it and the stages above that (admin, 2026-11-12:
    # keep going up and up, and do not stop just because a source states no
    # more).  The rungs are the ancestor ladder's own, with its own laws, so
    # nothing is invented here: the page shows one timeline where it used to
    # show two pages.
    if (start > 0 and rows and not edited and not hypothesis and not build
            and not own and not recorded_start and len(_above) < 4):
        key = (start_stage, start_form)
        if key not in _above:
            word_above = str((rows[0].get("recorded") or {}).get("w") or start_form)
            climbed = hierarchy(start_stage, word_above, pathway=pathway,
                                _above=_above + (key,))
            levels_above = list((climbed or {}).get("levels") or [])
            if len(levels_above) > 1 and levels_above[-1].get("stage") == start_stage:
                # The ancestor's last rung is this same form; keep this word's
                # own rung (it is the form this record names) and take the
                # status and laws the ancestor ladder earned for it, so the
                # rung says "the laws reach the record" instead of repeating
                # that no origin is recorded above it.
                top = dict(levels_above[-1])
                top["form"] = rows[0]["form"]
                top["edited"] = False
                top["changed"] = False
                record = top.get("recorded")
                if record:
                    record = dict(record)
                    record["same"] = bool(
                        normalise_etymon(top["form"])
                        and _same_form(normalise_etymon(top["form"]),
                                       normalise_etymon(str(record.get("w") or ""))))
                    record["starts"] = False
                    # Where *this* word's page read the form is still the truth
                    # for this page: the column above came from the ancestor's
                    # own ladder, not from this record (2026-11-12).
                    mine = (rows[0].get("recorded") or {}).get("origin")
                    if mine:
                        record["origin"] = mine
                    top["recorded"] = record
                for climbed_row in levels_above[:-1]:
                    climbed_row["climbed"] = True
                top["climbed_from"] = levels_above[0].get("stage")
                # The start rung now has a rung above it, so its verdict is the
                # ancestor ladder's, not this word's own: it is drawn, but the
                # coverage counter never measured it (2026-11-12).
                top["climb_start"] = True
                rows = levels_above[:-1] + [top] + rows[1:]
                earlier = []
    # Every recorded ancestor, with whether the laws carry it to the word: the
    # buttons beside the ladder ("try the Proto-Iranian form").  Only for a
    # ladder that starts at a record: an edited or composed start already asks
    # its own question, and adding more starts there would mix two hypotheses.
    starts: list[dict] = []
    if not hypothesis and not edited and not own:
        current = (start_stage, start_form)
        for row in _derive_each_start(entry, chain, disabled, enabled):
            row["current"] = (row["stage"], row["form"]) == current
            starts.append(row)
    switched = [r for row in rows for r in row["rules"] if r["disabled"]]
    # Every rung whose record the laws do not reproduce.  The word's own rung
    # is excluded: whether the last mile is exact is the match itself, and a
    # word may be reproduced from a later ancestor while the stages above it
    # are not (English *night* — 2026-11-09).
    steps_differ = [] if edited else [
        {"stage": row["stage"],
         "name": _lang(row["stage"]).get("name", row["stage"]),
         "recorded": (row.get("recorded") or {}).get("w", ""),
         "derived": row["form"]}
        for row in rows
        if row["stage"] != lang and row["status"] == "differs"
        and not row.get("built") and not row.get("climbed")
        and not row.get("climb_start")
    ]
    return {
        "lang": lang,
        "word": entry["word"],
        "start": start_stage,
        "start_name": _lang(start_stage).get("name", start_stage),
        # A recorded form may be named with a register of its stage ("inherited
        # from Late Latin").  The laws read it at the stage, so the rung is
        # called Latin; this says which register the record actually named, so
        # the page never presents a Late Latin form as a classical one
        # (data/language_varieties.yaml, 2026-11-09).
        "start_variety": _variety_at(entry, start_stage, start_form),
        # The reader named the start from the word's own record rather than
        # typing it: the page says so instead of "edited start".
        "start_recorded": ({"stage": recorded_start["stage"],
                            "name": recorded_start["name"],
                            "form": recorded_start["form"]} if recorded_start else None),
        # Every recorded ancestor form and whether it reaches the word, so the
        # page can offer the others without the reader typing anything.
        "starts": starts,
        "etymon": normalise_etymon(pie) if pie else None,
        # The etymon's own dictionary record, when the PIE glossary holds it:
        # a note that calls the etymon a root should quote the root's sense
        # whatever rung the ladder begins on (2026-11-09).
        "etymon_record": _etymon_record(chain[0], pie) if pie else None,
        "linked_by_set": linked_by_set and not edited,
        "set_start": set_start and not edited,
        "set_is_root": bool(set_is_root) and not edited,
        "ancestry_top": ancestry_top,
        "off_chain": [] if edited else off_chain,
        "set_source": set_source,
        "root": bool(pie) and (
            str(entry.get("cog", "")).endswith("-")
            or any(stage == "ine-pro" and normalise_etymon(word) == normalise_etymon(pie)
                   and (rel == "root" or word.strip().endswith("-"))
                   for stage, word, rel in _ancestry_triples(entry))
        ),
        "levels": rows,
        # The timeline carried past the word, and the children it can be
        # carried into next: the buttons under the last rung.
        "path": list(extra),
        "next": next_rows,
        "can_extend": bool(next_rows),
        "exact": exact,
        "category": (None if (edited or built) else _category_of(
            entry, chain, exact, own_pathway, written_match, cited_stem, deepest,
            [step["stage"] for step in steps_differ], start_stage)),
        # Which recorded stages disagree, with both forms: the page prints the
        # list under the band instead of leaving "with adjustments" unexplained.
        "steps_differ": steps_differ,
        "mismatched_steps": [step["stage"] for step in steps_differ],
        "backlog": [] if edited else _backlog_of(entry, chain),
        "earlier": [] if edited else earlier,
        "edited": edited,
        "disabled": disabled,
        "enabled": enabled,
        "switched_off": len(switched),
        # The word's own pathway, when one is recorded: which laws it turns
        # off and the reason it gives.  The page prints that reason beside the
        # switched-off law instead of leaving a bare warning badge.
        "pathway": ({
            "id": own_pathway.get("id"),
            "note": own_pathway.get("note", ""),
            "created": own_pathway.get("created", ""),
            "disabled": list(own_pathway.get("disabled") or []),
            "enabled": list(own_pathway.get("enabled") or []),
            "references": list(own_pathway.get("references") or []),
        } if own_pathway else None),
        # Whether a pathway exists even when the reader asked to see the laws
        # unfiltered: the page then offers to put it back instead of silently
        # forgetting the word has one.
        "pathway_available": bool(pathways.default_for(lang, entry["word"])),
        # Which way the pathway bends the laws, so the "laws unfiltered" bar can
        # say what the reader is currently *not* seeing.
        "pathway_enables": len(((pathways.default_for(lang, entry["word"]) or {}).get("enabled")) or []),
        "pathway_disables": len(((pathways.default_for(lang, entry["word"]) or {}).get("disabled")) or []),
        "missing": trace.skipped,
        "total_steps": len(trace.steps),
        "result": {
            "status": final["status"],
            "form": final["form"],
            "target": entry["word"],
            "match": final["status"] == "match",
            # A match may be a claim about a romanisation (پدر → pedar) or
            # about a reading the script allows (𐎺𐎼𐎣 → wˈarkah). The page
            # says which, because the two warrant different sentences.
            "match_via_script": bool((final.get("recorded") or {}).get("fit")),
            # Two facts, not alternatives: the laws can reproduce the
            # dictionary's romanisation *and* be a reading the signs allow
            # (پدر pedar, 𐎭𐎼𐎹 drayaʰ). The page says both (2026-11-09).
            "match_via_translit": final["status"] == "match"
            and bool((final.get("recorded") or {}).get("via"))
            and not _same_form(final["form"], entry["word"]),
            "ipa": target_reading["ipa"],
            "reading": target_reading["reading"],
            "attested": final["evidence"] == "attested",
            "written": written,
            "written_match": written_match,
            "cited_stem": cited_stem,
        },
        "target_name": _lang(lang).get("name", lang),
        "start_form": start_form,
        # A suffix the reader asked to try instead of the one the word wears
        # (`?suffix=eh2`): the ladder below is then a hypothetical derivation,
        # not this word's own answer, and the page says so.
        "hypothesis": hypothesis,
        # The formation the reader asked for at one stage, and what that stage
        # may be built with: this is the timeline's own construction kit.
        "build": built,
        "build_at": build_at,
        "build_above": [{"stage": st, "name": _lang(st).get("name", st)}
                        for st in built_above],
        "build_options": {st: build_options(st)
                          for st in dict.fromkeys(rung_stages)},
        "formed": (entry.get("formed") or None),
        # A word's own pathway is not a suggestion to load: it is already
        # applied, and the page says so above the ladder. Only paths the reader
        # can try out are listed here.
        "pathways": [p for p in pathways.for_word(lang, entry["word"])
                     if not p.get("default")],
        # A stored pathway is keyed by the rung the reader typed, not by the
        # top of the ladder it now keeps above that rung.
        "stored_pathway": (
            pathways.find(lang, entry["word"], edited["stage"], edited["form"], disabled)
            if edited else None
        ),
    }


def _check_law_keys(lang: str, disabled: Iterable[str]) -> list[str]:
    """Every switched-off law must exist on this language's chain.

    A typo in a key would otherwise be silently ignored, and a pathway that
    claims to switch a law off would switch nothing off while the page still
    looked complete.
    """
    off = sorted({d for d in disabled if d})
    if not off:
        return off
    chain = data.derivation_chain(lang)
    known: set[str] = set()
    rulesets = data.rulesets()
    for (src, dst), ruleset in rulesets.items():
        if src not in chain or dst not in chain:
            continue
        for rule in ruleset.rules:
            known.add(rule_key(ruleset, rule.id))
            known.add(rule.id)
    missing = [key for key in off if key not in known]
    if missing:
        raise ValueError(f"unknown law: {', '.join(missing)}")
    return off


def store_pathway(lang: str, word: str, from_stage: str, from_form: str,
                  disabled: Iterable[str] = (), note: str = "",
                  default: bool = False, references: Iterable[str] = (),
                  enabled: Iterable[str] = ()) -> dict:
    """Record a path — a starting form the reader typed, or the word's own laws.

    The server recomputes the path itself and refuses anything that does not
    land exactly on the recorded word, so a pathway in the file is always a
    claim the rules support — never something a client simply asked to save.

    ``default`` records the second kind: this word's own answer, applied every
    time its page opens. It needs a reason (a law can be left out of one word
    only because the change it states did not happen there, and the page has to
    be able to say which change and why), and the strict law-only derivation
    stays in the coverage figures: a word completed this way is counted apart,
    so no rule can be bent per word without the number showing it.
    """
    from_form = (from_form or "").strip()
    off = _check_law_keys(lang, disabled)
    on = [e for e in _check_law_keys(lang, enabled) if e not in set(off)]
    refs = sorted({r for r in references if r})
    unknown = [r for r in refs if r not in data.sources()]
    if unknown:
        raise ValueError(f"unknown source: {', '.join(unknown)}")
    if default:
        if not (lang and word):
            raise ValueError("a default pathway needs a language and a word")
        if not note.strip():
            raise ValueError("a default pathway needs a note saying why the law does not apply")
        if not off and not on:
            raise ValueError("a default pathway must switch at least one law on or off")
        row = hierarchy(lang, word, off, pathway=False, enabled=on)
        if not row:
            raise ValueError("this word has no ladder")
        if not row["result"]["match"]:
            raise ValueError("the laws, with these switched off, do not reproduce the recorded word")
        if not row["result"].get("attested"):
            raise ValueError("the end word is not attested, so it cannot carry a pathway")
        from_stage, from_form = row["start"], row["start_form"]
    else:
        if not from_stage or not from_form:
            raise ValueError("a pathway needs a starting stage and a form")
        row = hierarchy(lang, word, off, from_stage=from_stage, from_form=from_form, enabled=on)
        if not row or not row.get("edited"):
            raise ValueError("this starting stage is not on the word's chain")
        if not row["result"]["match"]:
            raise ValueError("the registered laws do not reproduce the recorded word from this form")
        if not row["result"].get("attested"):
            raise ValueError("the end word is not attested, so it cannot be stored as a pathway")

    # A pathway begins where the reader typed the form, not at the top of the
    # ladder: the rungs above the edit are the laws' own work and are not part
    # of the hypothesis being stored (2026-11-08: the timeline keeps them, the
    # record does not claim them).
    start_stage, start_form = row["start"], row["start_form"]
    edited = row.get("edited")
    if edited:
        start_stage, start_form = edited["stage"], edited["form"]
        start_name = edited.get("name") or _lang(start_stage).get("name", start_stage)
    else:
        start_name = row["start_name"]
    stages = [level["stage"] for level in row["levels"]]
    first = stages.index(start_stage) if start_stage in stages else 0
    levels = [{"stage": level["stage"], "form": level["form"], "name": level["name"]}
              for level in row["levels"][first:]]
    laws = []
    for index, level in enumerate(row["levels"][first:][1:], start=1):
        prev = row["levels"][first + index - 1]
        for rule in level["rules"]:
            if not rule["fired"]:
                continue
            laws.append({"step": f"{prev['stage']}→{level['stage']}",
                         "id": rule["id"], "name": rule["name"], "tier": rule["tier"]})
    identifier = pathways.signature(lang, row["word"], start_stage, start_form, off)
    record = {
        "id": identifier,
        "lang": lang,
        "word": row["word"],
        "created": pathways.now(),
        "start": {"stage": start_stage, "name": start_name, "form": start_form},
        "end": {"form": row["result"]["form"], "recorded": row["word"]},
        "disabled": off,
        "enabled": on,
        "levels": levels,
        "laws": laws,
        "note": (note or "").strip()[:400],
        "references": refs,
        "default": bool(default),
    }
    stored, created = pathways.store(record)
    return {"pathway": stored, "created": created}


FOCUS_LANGUAGES = ("fa", "en", "de")
"""Languages the word page always previews, before the rest of the family."""

TIER_ORDER = ("established", "proposed", "custom")


@lru_cache(maxsize=512)
def _rebuilt_from_pie(form: str) -> tuple[dict, ...]:
    """Run one PIE etymon through every complete stage chain.

    This is the "what would it look like if the rules were right" view: the
    registered laws and nothing else, applied from Proto-Indo-European to every
    language in the registry.  A stage counts as modelled only when its chain
    starts at PIE and every transition has a rule file; a gap is reported as a
    gap instead of being hidden behind an unchanged form.
    """
    rulesets = data.rulesets()
    rows: list[dict] = []
    for lang in data.languages():
        if lang == "ine-pro":
            continue
        chain = data.derivation_chain(lang)
        if not chain or chain[0] != "ine-pro":
            continue
        d = derive(form, chain, rulesets)
        row = _lang(lang)
        rows.append({
            "l": lang,
            "lang_name": row.get("name", lang),
            "branch": row.get("branch", ""),
            "kind": kind_of(lang),
            "script": row.get("script", ""),
            # The rebuilt form is already the engine's own phonological
            # transcription, so it needs no second spelling beside it.
            "show_reading": False,
            "form": d.output,
            "steps": len(d.steps),
            "tiers": sorted({s.tier for s in d.steps},
                            key=lambda t: TIER_ORDER.index(t) if t in TIER_ORDER else 9),
            "laws": [s.rule_id for s in d.steps],
            "skipped": list(d.skipped),
        })
    return tuple(rows)


def _rebuild_order(row: dict) -> tuple:
    focus = (FOCUS_LANGUAGES.index(row["l"]) if row["l"] in FOCUS_LANGUAGES
             else len(FOCUS_LANGUAGES))
    return (1 if row["skipped"] else 0, focus, row["branch"] or "zz", row["lang_name"])


def _recorded_forms(forms: list[dict]) -> dict[str, list[dict]]:
    """What the dictionaries already know, indexed by language."""
    recorded: dict[str, list[dict]] = {}
    for f in forms:
        bucket = recorded.setdefault(f["l"], [])
        meta = {k: f.get(k) for k in ("ipa", "reading", "reading_auto",
                                      "reading_how", "reading_note", "kind",
                                      "script", "evidence", "show_reading")}
        bucket.append({"w": f["w"], "r": f.get("r") or "", **meta})
        for reading in f.get("readings") or ():
            bucket.append({"w": f["w"], "r": reading, **meta})
    return recorded


@lru_cache(maxsize=512)
def cognate_set_for(form: str) -> str | None:
    """The cognate set whose PIE form is *form*, if one is registered.

    A word *in* Proto-Indo-European has no ``cog`` field of its own, so the
    root's set is found by its etymon instead — that is what supplies the forms
    the family records, for the reconstruction panel and the cognate table.
    """
    key = normalise_etymon(form)
    if not key:
        return None
    for rec in cognate_index().values():
        if normalise_etymon(rec.get("pie", "")) == key:
            return rec["id"]
    return None


def rebuilds_for_etymon(form: str) -> dict | None:
    """Rebuild from a bare etymon, using its cognate set when one is registered."""
    set_id = cognate_set_for(form)
    if set_id:
        payload = _cognate_payload(set_id)
        if payload:
            return rebuilds(payload.get("pie"), _recorded_forms(payload["forms"]))
    return rebuilds(form)


def _rebuild_evidence(row: dict) -> str:
    """Which of the four evidence colours a rebuilt form earns.

    ``attested``  the laws reproduced a form a glossary records (green).
    ``literary``  they reproduced a reconstruction the literature records,
                  i.e. a form normally written with an asterisk (gold).
    ``strong``    our own form, not in any dictionary, and every law that
                  applied is established (orange).
    ``weak``      our own form built on a proposed/custom law, on no law at
                  all, or one that contradicts a recorded cognate (red).
    """
    if row["status"] == "match":
        rec = row.get("recorded") or {}
        if rec.get("evidence"):
            return rec["evidence"]
        return "literary" if row["kind"] == "proto" else "attested"
    if row["status"] == "differs" or row["confidence"] != "high":
        return "weak"
    return "strong"


def rebuilds(form: str | None, recorded: dict[str, list[dict]] | None = None) -> dict | None:
    """Predicted cognates: derive the etymon into every modelled language.

    ``recorded`` maps a language to the forms the dictionaries and cognate sets
    already know for *this* etymon.  A rebuilt form that equals one of them is
    reported as a match (the rules independently reproduced an attested word);
    a rebuilt form with no recorded counterpart is the interesting case the
    interface marks in its own colour and italics.
    """
    if not form:
        return None
    etymon = normalise_etymon(form)
    if not etymon:
        return None
    recorded = recorded or {}
    rows: list[dict] = []
    for raw in _rebuilt_from_pie(etymon):
        row = dict(raw)
        candidates = recorded.get(row["l"], [])
        hit = None
        for cand in candidates:
            if any(cand.get(k) and _same_form(cand[k], row["form"]) for k in ("w", "r")):
                hit = cand
                break
        row["status"] = "match" if hit else ("differs" if candidates else "new")
        row["recorded"] = hit or (candidates[0] if candidates else None)
        row["confidence"] = "high" if row["steps"] and all(
            t == "established" for t in row["tiers"]) else "low"
        row["evidence"] = _rebuild_evidence(row)
        rows.append(row)
    rows.sort(key=_rebuild_order)

    modelled = [r for r in rows if not r["skipped"]]
    gaps = [{"l": r["l"], "lang_name": r["lang_name"], "missing": r["skipped"]}
            for r in rows if r["skipped"]]
    source = {
        "lang": "ine-pro",
        "lang_name": _lang("ine-pro").get("name", "Proto-Indo-European"),
        "form": etymon,
    }
    record = _lemma_entry("ine-pro", etymon)
    if record:
        source["pos"] = record.get("pos", "")
        source["gloss"] = _rung_gloss(record.get("gloss") or [])
    return {
        "source": source,
        "rows": rows,
        "counts": {
            "languages": len(modelled),
            "matched": sum(1 for r in modelled if r["status"] == "match"),
            "differs": sum(1 for r in modelled if r["status"] == "differs"),
            "unattested": sum(1 for r in modelled if r["status"] == "new"),
            "gaps": len(gaps),
            "steps": sum(r["steps"] for r in modelled),
            "proposed": sum(1 for r in modelled if "proposed" in r["tiers"] or "custom" in r["tiers"]),
            "attested": sum(1 for r in modelled if r["evidence"] == "attested"),
            "literary": sum(1 for r in modelled if r["evidence"] == "literary"),
            "strong": sum(1 for r in modelled if r["evidence"] == "strong"),
            "weak": sum(1 for r in modelled if r["evidence"] == "weak"),
        },
        "gap_languages": gaps,
    }


def _plain_form(form: str) -> str:
    """A form with its accent marks dropped, for matching a recorded reading.

    ``drˈayah`` (what the laws write), ``dráyah`` (what the page prints) and
    ``drayaʰ`` (the dictionary's romanisation) are one form; only the notation
    differs. Length marks stay: ``drayā`` is not ``draya``.
    """
    key = _comparison_key(form.replace("ˈ", "").replace("ˌ", ""))
    return unicodedata.normalize("NFC", "".join(
        ch for ch in unicodedata.normalize("NFD", key)
        if not unicodedata.combining(ch) or ch == "\u0304"))


def _lexicon_file(lang: str):
    """The file a glossary is read from, for naming a cache's input."""
    for name in (f"{lang}.jsonl.gz", f"{lang}.jsonl"):
        path = data.LEXICON_DIR / name
        if path.exists():
            return path
    return None


@lru_cache(maxsize=None)
def _reading_index(lang: str) -> dict[str, tuple[str, str]]:
    """Headwords by the form their own romanisation spells.

    A cuneiform, Greek or Persian entry is never spelled the way the laws write
    it — Old Persian 𐎭𐎼𐎹 is *drayaʰ* — so a branch row that matches a
    reading is the only way that stage can show its record. Matching a reading
    is how every other comparison on these pages works (``_same_form``), and
    the row says the match was made through the reading (2026-11-08).
    """
    if not needs_reading(lang):
        return {}

    def build() -> dict[str, tuple[str, str]]:
        out: dict[str, tuple[str, str]] = {}
        for word, rows in data.lexicon_index(lang).items():
            entry = rows[0]
            for spelling in attested_spellings(entry):
                out.setdefault(_plain_form(spelling), (word, spelling))
            out.setdefault(_plain_form(word), (word, word))
        return out

    # The index is a function of the glossary and of the readings it quotes,
    # so it is built once and kept between restarts, like the rows themselves
    # (2026-11-12).
    return data.cached(f"readings-{lang}", 1,
                       [_lexicon_file(lang), data.DATA / f"readings_{lang}.json"],
                       build)


@lru_cache(maxsize=None)
def _script_index(lang: str) -> dict[str, tuple[str, ...]]:
    """A stage's headwords by the consonants its own signs spell.

    Reading a script spelling is searching a space of readings (𐎺𐎼𐎣 writes
    *v-r-k*, and any vowel may fall between those consonants), so a lookup by
    the exact form is impossible. The consonants, though, are not in doubt:
    they are the skeleton every reading shares, and they turn the search into
    a handful of candidates that are then checked sign by sign
    (``script.match``, 2026-11-08).
    """
    if not script.table(lang):
        return {}

    def build() -> dict[str, tuple[str, ...]]:
        out: dict[str, list[str]] = {}
        for word in data.lexicon_index(lang):
            key = script.skeleton(lang, word)
            if key:
                out.setdefault(key, []).append(word)
        return {key: tuple(words) for key, words in out.items()}

    return data.cached(f"script-{lang}", 1,
                       [_lexicon_file(lang), data.DATA / "script" / f"{lang}.yaml"],
                       build)


def _script_record(lang: str, form: str, *, loose: bool = False) -> dict | None:
    """The word this stage records in its own script that ``form`` could read.

    Old Persian 𐎺𐎼𐎣 is written *va-ra-ka*; the laws produce ``wˈarkah``. The
    two are not the same string and are the same word: the syllabary does not
    write short vowels or a final /h/, and it spells a bare consonant with a
    vowel sign. So the record is found by its consonants and confirmed sign by
    sign, and the block carries what the scribe wrote so the page can print
    both forms — the record stays the record, the form stays a reading of it
    (2026-11-08).

    The letters alone are **not** a match where the writing leaves the vowels
    out. An abjad spells k-b-d and so spells کبد *kabid*, کبود *kabud* and
    کبوده *kabude* at once; without the dictionary's own reading agreeing there
    is nothing to verify, and the row goes to the unverified state instead
    (`_near_record`, 2026-11-12).
    """
    index = _script_index(lang)
    key = script.reading_skeleton(form)
    if not index or not key:
        return None
    for candidate in (key, key[:-1] if key.endswith("h") else ""):
        for word in index.get(candidate or "", ()):
            fit = script.match(lang, form, word)
            if not (fit and fit["ok"]):
                continue
            entry = _lemma_entry(lang, word) or {}
            pron = readings_for(entry)
            readings = [r for r in [pron["reading"], *attested_spellings(entry)] if r]
            letters_only = fit.get("abjad") and not readings
            if letters_only and not loose:
                continue
            if readings and not _same_reading(fit, form, readings):
                continue
            record = _with_reading({
                "w": word,
                "r": "",
                "evidence": _entry_evidence(lang, entry),
                "recon": bool(entry.get("recon")),
                "ipa": pron["ipa"],
                "reading": pron["reading"],
                "show_reading": show_reading(lang, word),
                "known": True,
                "via": "script",
                "exact": False,
                "fit": fit,
                "script": _lang(lang).get("script", ""),
                "in_script": _in_native_script(lang, word),
                "pos": entry.get("pos", ""),
                "gloss": _rung_gloss(entry.get("gloss") or []),
                "sources": _entry_sources(entry),
            }, lang, word)
            if letters_only:
                # An abjad leaves the vowels out, so its letters alone agree
                # with several words at once. The record is worth showing —
                # the reader can see the entry, its reading and its meaning —
                # but never as a match: it is queued for review (2026-11-12).
                record["unverified"] = True
                record["matches"] = False
                record["review"] = {"form": form, "record": pron["reading"] or word,
                                    # The letters agree and nothing records the
                                    # vowels: the reviewer is told which test the
                                    # row passed, because it is the weaker one.
                                    "basis": "letters"}
            return record
    return None


#: The letters whose loss at a word's end is a change of *ending* rather than
#: of the word: a dictionary reads کبود *kabud* where the laws give *kabūde*.
LOOSE_ENDINGS = "aeiouāēīōūăĕĭŏŭəâêîôûʰhwy"


def _near_keys(form: str) -> list[str]:
    """A form's reading, then that reading with one or two final letters off.

    Length is notation (`_reading_key`), so the same dictionary reading can be
    written *kabūd* or *kabud*; what the laws add or drop at the very end —
    کبوده against کبود — is the one difference this page is willing to call a
    near miss rather than a different word (2026-11-12).
    """
    key = _reading_key(form)
    out = [key]
    while key and len(out) < 3 and key[-1] in LOOSE_ENDINGS:
        key = key[:-1]
        if len(key) < 3:
            break
        out.append(key)
    return out


@lru_cache(maxsize=None)
def _near_reading_index(lang: str) -> dict[str, list[tuple[str, str, str]]]:
    """Headwords by the reading their dictionary gives, and by its bare stem.

    The stem keys let a form with an ending the laws produced — کبوده — find
    the word the dictionary heads as کبود *kabud*. A hit here is never a
    match: the ending is unexplained, so the row is shown as unverified for a
    human to look at (2026-11-12).
    """
    if not needs_reading(lang):
        return {}

    def build() -> dict[str, list[tuple[str, str, str]]]:
        out: dict[str, list[tuple[str, str, str]]] = {}
        for word, rows in data.lexicon_index(lang).items():
            entry = rows[0]
            spellings = attested_spellings(entry) or [word]
            for spelling in spellings:
                if not spelling:
                    continue
                full = _reading_key(spelling)
                for key in _near_keys(spelling):
                    bucket = out.setdefault(key, [])
                    if (word, spelling) not in [(w, s) for w, s, _ in bucket]:
                        bucket.append((word, spelling, full))
        return out

    return data.cached(f"near-{lang}", 1,
                       [_lexicon_file(lang), data.DATA / f"readings_{lang}.json"],
                       build)


def _near_record(lang: str, form: str) -> dict | None:
    """The record a form reproduces every sound of but the ending.

    Persian کبود is read *kabud*, and the laws carry Old Persian 𐎣𐎱𐎢𐎫𐎣 to
    *kabūde*: the word is the same one and the final -e is a change no
    registered law accounts for.  Saying "no recorded form" hides the word, and
    saying "match" claims a law this repo does not have, so the row quotes the
    record, says *match not verified*, and carries the two readings a reviewer
    needs.  A form that differs anywhere else (کبد *kabid* for *kabūde*) is not
    this record at all and finds nothing here (2026-11-12).
    """
    index = _near_reading_index(lang)
    if not index:
        return None
    full = _reading_key(form)
    for key in _near_keys(form):
        for word, spelling, record_key in index.get(key, ()):
            if record_key == full:
                # The readings agree: that is a match, not a near miss.
                continue
            entry = _lemma_entry(lang, word) or {}
            if not entry:
                continue
            pron = readings_for(entry)
            return _with_reading({
                "w": word,
                "r": "",
                "evidence": _entry_evidence(lang, entry),
                "recon": bool(entry.get("recon")),
                "ipa": pron["ipa"],
                "reading": pron["reading"],
                "show_reading": show_reading(lang, word),
                "known": True,
                "via": "near",
                "exact": False,
                "matches": False,
                # The two readings a reviewer compares, and what disagrees.
                "unverified": True,
                "review": {"form": form, "record": spelling,
                           "form_key": full, "record_key": record_key,
                           "basis": "reading"},
                "script": _lang(lang).get("script", ""),
                "in_script": _in_native_script(lang, word),
                "pos": entry.get("pos", ""),
                "gloss": _rung_gloss(entry.get("gloss") or []),
                "sources": _entry_sources(entry),
            }, lang, word)
    return None


def _reading_key(form: str) -> str:
    """A phonological form for comparison with a dictionary's reading.

    Length is notation — dictionaries write Persian /uː/ as ``u`` or ``ū``,
    and Wiktionary marks a short vowel with a breve — so the macron is folded
    away.  Vowel *quality* is not notation: a record that reads a word ``dōš``
    does not read ``dūšā``, however many vowels its abjad leaves unwritten
    (2026-11-12).
    """
    text = unicodedata.normalize("NFD", _comparison_key(form))
    text = "".join(ch for ch in text if ch != "\u0304")
    return unicodedata.normalize("NFC", text).replace("ˈ", "").replace("ˌ", "")


def _abjad_reading(fit: dict, form: str, readings: list[str]) -> str | None:
    """The dictionary reading an abjad fit actually produces, if one agrees.

    Returned so the rung can name it: the laws give Persian dūš for دوش, the
    entry records both dōš and duš, and the green means ``duš`` — a reader is
    owed the reading the match was made on (2026-11-12).
    """
    if not fit.get("abjad") or fit.get("unwritten") or fit.get("convention"):
        return None
    key = _reading_key(form)
    return next((r for r in readings if r and _reading_key(r) == key), None)


def _same_reading(fit: dict, form: str, readings: list[str]) -> bool:
    """Whether a record's own reading is the form the signs were read as.

    ``fit`` says which letters the writing cannot carry (Old Persian 𐎭𐎡𐎺 is
    *daivaʰ* and the final /h/ has no sign) and which conventions it used (a
    final -i is closed by the y-sign).  With those set aside, the consonants of
    the two forms are the test: 𐎭𐎡𐎺 read *daivaʰ* and the laws' *daivˈah* are
    one reading, while Pahlavi l-w-c read *rōz* and the laws' *rōč* are not
    (2026-11-11).
    """
    recorded = [r for r in readings if r]
    if not recorded:
        return True
    if fit.get("convention"):
        return True
    unwritten = set("".join(fit.get("unwritten") or []))
    if not unwritten and fit.get("abjad"):
        # An abjad writes the consonants and leaves the short vowels to the
        # reader, so the signs alone can never tell dōš from dūš.  The record
        # can, and when it states a reading the vowels are part of it: Persian
        # دوش is read dōš, and the laws' dūšā is a different word — the final
        # -ā comes from PIE *-eh₂ and no registered law drops it (2026-11-12).
        return _abjad_reading(fit, form, recorded) is not None
    if not unwritten:
        # A syllabary or a logogram: the sign-by-sign comparison is the
        # documented convention, and the consonants are the test (2026-11-11).
        return script.reading_skeleton(form) == script.reading_skeleton(recorded[0])
    # The letter is absent from *both* writings: *daivaʰ* is written da-i-va,
    # and the aspiration the transcription marks is the /h/ no sign carries.
    def without(text: str) -> str:
        return "".join(ch for ch in text.replace("ʰ", "h") if ch not in unwritten)
    return script.reading_skeleton(without(form)) == script.reading_skeleton(without(recorded[0]))


def _record_for_form(lang: str, form: str) -> dict | None:
    """What this stage records for a form the laws produced, if anything.

    Three ways a record can be this word: its glossary spells the headword
    exactly (Persian گربه is stored as گربه, read *gorbe*), its recorded
    romanisation is the form (Pahlavi gwlg is read *gurg*), or its writing
    system allows the form as a reading of the signs it writes (Old Persian
    𐎺𐎼𐎣, *va-ra-ka*, for ``wˈarkah``). Each answer says which way it was
    found; none of them substitutes the form for the record.
    """
    record = _stage_record(lang, form)
    if record:
        entry = _lemma_entry(lang, record["w"]) or {}
        return {**record, "pos": entry.get("pos", ""),
                "gloss": _rung_gloss(entry.get("gloss") or []),
                # Every reading the dictionary accepts for the word, not only
                # the first: Persian گرگ is printed *gurg* and also read
                # *gorg*, and a reconstruction that lands on either has
                # reproduced the record (2026-11-09).
                "readings": attested_spellings(entry) if entry else []}
    return _script_record(lang, form)


def _branch_node(parent: str, form: str, target: str, *,
                 origin_records: dict[str, dict], claim: bool, depth: int,
                 seen: frozenset[str], recurse: bool = True) -> dict:
    """One direct child of a stage, carrying the form there through its laws.

    ``parent``'s form is run through the one transition ``parent → target``;
    the child keeps the output for its own children, so a branch is a tree of
    transitions and nothing else — no language is skipped, and a language is
    only ever shown under its own recorded ancestor (2026-11-08).

    ``claim`` says whether a form that lands on a record may be coloured as a
    match (green/gold). On the "not recorded here" page it may not: that page's
    starting form is the reader's, not a recorded etymon.

    ``recurse=False`` computes this child and stops: the ladder's "carry it on"
    buttons need one level only, and PIE has descendants deep enough that
    building all of them for each click would be work nobody asked for.
    """
    row = data.languages().get(target, {})
    d = derive(form, [parent, target], data.rulesets())
    tiers = sorted({s.tier for s in d.steps},
                   key=lambda t: TIER_ORDER.index(t) if t in TIER_ORDER else 9)
    candidates: list[dict] = []
    hit: dict | None = None
    head = None if d.skipped else _headword_at(target, d.output)
    if not d.skipped:
        bucket = origin_records.get(target) or {}
        for rec_form in bucket.get("forms") or ():
            pron = pronunciation(target, rec_form)
            candidates.append({
                "w": rec_form, "via": "origin",
                **_form_meta(target, rec_form, pron["reading"]),
                "pos": bucket.get("pos", ""), "gloss": bucket.get("gloss", ""),
                "matches": bool(_same_form(d.output, rec_form)
                                or (pron["reading"] and _same_form(d.output, pron["reading"]))),
            })
        hit = next((c for c in candidates if c["matches"]), None)
        if head and hit is None:
            hit = {
                "w": head["word"], "via": "glossary",
                **_form_meta(target, head["word"]),
                "pos": head.get("pos", ""),
                "gloss": _rung_gloss(head.get("gloss") or []),
                "matches": True,
            }
        if hit is None:
            # The stage's own entry may be written in a script that allows this
            # form as a reading (Old Persian 𐎺𐎼𐎣 for *wˈarkah*): the record
            # is quoted with the signs it writes, exactly as a ladder rung does
            # (2026-11-08).
            scripted = _script_record(target, d.output)
            if scripted:
                hit = scripted
                candidates.append(hit)
        if hit is None:
            # Nothing verifies the form, but a record may reproduce every sound
            # of it but the ending (کبود *kabud* for *kabūde*).  That is not a
            # match and must not wear the ✓ — it is shown as unverified, for a
            # person or an agent to judge later (2026-11-12).
            near = _near_record(target, d.output) or _script_record(
                target, d.output, loose=True)
            if near:
                hit = near
                candidates.append(near)
        if hit is None:
            # The stage's own entry may be written in another script: quote it
            # only when its recorded romanisation is exactly this form.
            found = _reading_index(target).get(_plain_form(d.output))
            if found:
                word_, spelling = found
                lemma = _lemma_entry(target, word_) or {}
                hit = {
                    "w": word_, "via": "reading",
                    **_form_meta(target, word_, spelling),
                    "reading": spelling,
                    "pos": lemma.get("pos", ""),
                    "gloss": _rung_gloss(lemma.get("gloss") or []),
                    "matches": True,
                }
                candidates.append(hit)
        if hit is not None and hit["via"] != "origin":
            candidates.append(hit)
    if d.skipped:
        status = "gap"
    elif hit and hit.get("unverified"):
        status = "unverified"
    elif hit:
        status = "match"
    elif candidates:
        status = "differs"
    else:
        status = "new"
    high = bool(d.steps) and all(t == "established" for t in tiers)
    if claim and hit is not None and not hit.get("unverified"):
        # A match takes the record's own claim: a transliteration-only Old
        # Persian form is gold, not green (2026-11-08).
        evidence = hit.get("evidence") or evidence_for(hit["w"], target)
    else:
        evidence = _rebuild_evidence({"status": status, "kind": kind_of(target),
                                      "confidence": "high" if high else "low"})
    if not claim:
        # A start that is not a recorded etymon may never claim a match.
        evidence = "strong" if high else "weak"
    children = []
    if recurse and not d.skipped and target not in seen:
        children = _branch_children(target, d.output, origin_records=origin_records,
                                    claim=claim, depth=depth + 1,
                                    seen=seen | {target})
    return {
        "l": target,
        "lang_name": row.get("name", target),
        "short": row.get("short", target),
        "branch": row.get("branch", ""),
        "era": row.get("era"),
        "era_label": era_label(row.get("era")),
        "kind": kind_of(target),
        "script": row.get("script", ""),
        "show_reading": False,
        "form": d.output,
        "steps": len(d.steps),
        "tiers": tiers,
        "laws": [s.rule_id for s in d.steps],
        "skipped": list(d.skipped),
        "status": status,
        "recorded": hit or (candidates[0] if candidates else None),
        "form_known": bool(head),
        "confidence": "high" if high else "low",
        "evidence": evidence,
        "depth": depth,
        "children": children,
    }


def _branch_children(lang: str, form: str, *, origin_records: dict[str, dict],
                     claim: bool, depth: int, seen: frozenset[str]) -> list[dict]:
    """Every direct child of ``lang``, in registry order."""
    return [
        _branch_node(lang, form, child, origin_records=origin_records,
                     claim=claim, depth=depth, seen=seen)
        for child in data.descendants(lang)
        if child not in seen
    ]


def _journal_unverified(lang: str, form: str, rows: list[dict],
                        page: str = "", key: str = "l") -> None:
    """Put every row this page could not verify into the review queue once.

    The row itself already says *match not verified*; the queue is what makes
    the pile reviewable later — with both readings, both meanings and a link
    back to the page that showed it (admin, 2026-11-12).
    """
    out = []
    for row in rows:
        rec = row.get("recorded") or {}
        if row.get("status") != "unverified" or not rec:
            continue
        review = rec.get("review") or {}
        stage = row.get(key) or row.get("l") or row.get("stage") or ""
        out.append({
            "lang": stage,
            "lang_name": row.get("lang_name") or row.get("name", stage),
            "form": row.get("form", ""),
            "word": rec.get("w", ""),
            "reading": rec.get("reading", ""),
            "record_read": review.get("record", ""),
            "basis": review.get("basis", "reading"),
            "laws_form": review.get("form", ""),
            "gloss": rec.get("gloss", ""),
            "pos": rec.get("pos", ""),
            "step_lang": lang,
            "step_form": form,
        })
    if out:
        review_queue.record(out, source={"lang": lang, "word": page or form,
                                         "form": form})


def _flatten_branch(nodes: list[dict]) -> list[dict]:
    out: list[dict] = []
    for node in nodes:
        out.append(node)
        out.extend(_flatten_branch(node["children"]))
    return out


def _stage_descendants(lang: str, form: str,
                       origin: tuple[dict, str] | None = None,
                       claim: bool = True) -> dict:
    """Carry one stage's form down the branch, one direct child at a time.

    The view a form gets instead of a 404 is the family below it as a **tree**:
    the direct children of this stage, each with the form the registered laws
    produce for it, and under each child its own children, to the leaves. A
    language is only ever shown under the stage the registry records as its
    ancestor, so the page reads like the family tree rather than like a list of
    everything downstream (2026-11-08: "those are not direct
    descendant languages").

    ``origin`` is the (entry, stage) the form was reached from — the word page
    whose ladder the reader clicked. When that word's own ancestry records a
    form at a descendant stage, that record is quoted beside the produced form.
    ``claim`` is false on the "not recorded here" page, whose starting form is
    not a recorded etymon: there, a row is this repo's prediction (orange) or a
    tentative one (red), never green or gold.
    """
    origin_records = _recorded_at(origin[0], origin[1]) if origin else {}
    roots = _branch_children(lang, form, origin_records=origin_records,
                             claim=claim, depth=0, seen=frozenset({lang}))
    rows = _flatten_branch(roots)
    modelled = [r for r in rows if not r["skipped"]]
    gaps = [{"l": r["l"], "lang_name": r["lang_name"], "missing": r["skipped"]}
            for r in rows if r["skipped"]]
    _journal_unverified(lang, form, modelled,
                        page=(origin[0].get("word") or "") if origin else "")
    return {
        "source": {
            "lang": lang,
            "lang_name": _lang(lang).get("name", lang),
            "form": form,
        },
        "tree": roots,
        "rows": rows,
        "counts": {
            "direct": len(roots),
            "languages": len(modelled),
            "match": sum(1 for r in modelled if r["status"] == "match"),
            "unverified": sum(1 for r in modelled if r["status"] == "unverified"),
            "differs": sum(1 for r in modelled if r["status"] == "differs"),
            "new": sum(1 for r in modelled if r["status"] == "new"),
            "gaps": len(gaps),
            "steps": sum(r["steps"] for r in modelled),
            "strong": sum(1 for r in modelled if r["evidence"] == "strong"),
            "weak": sum(1 for r in modelled if r["evidence"] == "weak"),
        },
        "gap_languages": gaps,
    }


def _unrecorded_word(lang: str, form: str, via: str | None = None) -> dict | None:
    """The page a form without a glossary entry gets.

    A ladder rung is a form the laws produced, and the reader is entitled to
    open it — especially a rung marked ✓, whose *record* may come from
    Wiktionary's ancestry rows rather than from the stage's own glossary
    (Proto-Iranian *jráyah* has no entry here). Such a page says plainly that
    nothing is recorded at this stage and then follows the form down into the
    languages below it (`_stage_descendants`).
    """
    if lang not in data.languages():
        return None
    form = detokenize(tokenize(form))
    if not form:
        return None
    origin = None
    origin_recorded: list[str] = []
    origin_records: list[dict] = []
    origin_pair = None
    if via and "/" in via:
        origin_lang, origin_word = via.split("/", 1)
        rows = word_index().get((origin_lang, origin_word)) or []
        if rows:
            origin = {"lang": origin_lang, "word": origin_word,
                      "lang_name": _lang(origin_lang).get("name", origin_lang)}
            bucket = _recorded_at(rows[0], origin_lang).get(lang) or {}
            origin_recorded = list(bucket.get("forms") or ())
            origin_records = [_with_reading({
                "w": word_,
                "evidence": evidence_for(word_, lang),
                "in_script": _in_native_script(lang, word_),
                "recon": is_reconstructed(lang, word_),
                "script": _lang(lang).get("script", ""),
                "reading": (pronunciation(lang, word_).get("reading") or ""),
                "show_reading": show_reading(lang, word_),
            }, lang, word_) for word_ in origin_recorded]
            origin_pair = (rows[0], origin_lang)
    return {
        "word": form,
        "lang": lang,
        "lang_name": _lang(lang).get("name", lang),
        # A page with no entry still opens on the title's own margin: the
        # language and the years it was spoken, exactly as a word page does
        # (2026-11-11).
        "era_label": era_label(_lang(lang).get("era")),
        # The fourth state (2026-11-11): a word the glossary does not hold is
        # non-existent, and the page says so in the same place a word page says
        # attested or recorded.
        "attestation": attestation.payload(form, attestation.NON_EXISTENT,
                                           reason="No glossary entry of this stage is spelled this way."),
        "script": _lang(lang).get("script", ""),
        "kind": kind_of(lang),
        "evidence": "weak",
        "ghost": True,
        "show_reading": False,
        "reading": "",
        "pos": "",
        "gloss": [],
        "ipa": "",
        "translit": "",
        "translit_alt": [],
        "rtl": is_rtl(form),
        "etymology": "",
        "ancestry": [],
        "cognates": None,
        "rebuilds": None,
        "is_root": False,
        "derivation": None,
        "hierarchy": None,
        "variants": 0,
        "origin": origin,
        "origin_recorded": origin_recorded,
        "origin_records": origin_records,
        # The form is not in this stage's glossary, but the word page the
        # reader came from may still record it. Saying "not recorded" over a
        # form Wiktionary's own ancestry rows give was wrong (2026-11-08).
        "recorded_elsewhere": bool(origin_recorded),
        "descendants": _stage_descendants(lang, form, origin_pair, claim=False),
    }


ROOT_LANG = "ine-pro"
"""The family's root node: a word in it has no ancestor to be derived from."""

PIE_WORDS_BAND = "pie"
"""The glossary's default view: every headword except those borrowed from outside
the family.  It is a view, not a coverage band — the six bands are unchanged and
the word pages still say *non-PIE* — and ``band="pie"`` is how the web UI asks
for it (2026-11-09)."""


# ---------------------------------------------------------------------------
# grammar: cited derivational suffixes on a root
# ---------------------------------------------------------------------------
#: The inflectional endings a PIE word may be wearing in the nominative, longest
#: first. Composing a derivative needs the stem, and stripping the ending is a
#: mechanical step the page states, not a guess about the paradigm.
_NOM_ENDINGS = ("eh₂", "os", "om", "ōs", "ēs", "is", "us", "es", "s", "ē", "ō",
                "ā", "ī", "ū", "i", "u", "o", "a", "e")


@lru_cache(maxsize=16)
def _curated_suffixes(lang: str = ROOT_LANG) -> tuple[dict, ...]:
    """The suffixes written by hand for a stage (data/morphology/<lang>.yaml).

    Each row is a claim about a morpheme: what it means, how it attaches and
    the ending it brings. It is the one part of the registry a human wrote, and
    it takes a corpus piece of the same morpheme under its wing (see
    ``_curated_key``) instead of listing the same suffix twice.
    """
    path = data.DATA / "morphology" / f"{lang}.yaml"
    if not path.exists():
        return ()
    raw = data._load_yaml(path) or {}
    suffixes = []
    for row in raw.get("suffixes") or []:
        suffixes.append({
            "id": row["id"], "form": row.get("form", ""), "ending": row.get("ending", ""),
            "attach": row.get("attach", "drop"), "gloss": row.get("gloss", ""),
            "note": (row.get("note") or "").strip(), "outcomes": row.get("outcomes", ""),
            # How the suffix appears in the derived word (-nás → -nah after
            # *-Vs > *-Vh), so the ladder can highlight the morpheme itself
            # instead of guessing which letters a law inserted.
            "surface": row.get("surface", ""),
            "sources": [str(s) for s in row.get("sources") or []],
            "example": row.get("example", ""),
            # A suffix may name the registered law that *is* its formation
            # ("ine-pro~iir-pro:animal_ka"): then the same rule that carries
            # گربه down the ladder composes the form here, instead of the panel
            # gluing the morpheme on by hand (2026-11-08).
            "rule": row.get("rule", ""),
            "curated": True,
        })
    return tuple(suffixes)


@lru_cache(maxsize=16)
def _endings(lang: str = ROOT_LANG) -> dict[str, dict]:
    """The grammatical endings a construction may carry (data/morphology/).

    A row that states "‑ós" in *dl̥h₁gʰós* is naming the letters the word wears,
    and those letters are the paradigm's ending before they are a derivational
    suffix. The table says what the ending is; it is consulted only when the
    entry's own parenthesis says nothing (2026-11-08).
    """
    path = data.DATA / "morphology" / f"{lang}.yaml"
    if not path.exists():
        return {}
    raw = data._load_yaml(path) or {}
    out: dict[str, dict] = {}
    for row in raw.get("endings") or []:
        form = str(row.get("form") or "")
        if not form:
            continue
        out[form] = {"form": form, "name": str(row.get("name") or ""),
                     "note": str(row.get("note") or "").strip(),
                     "sources": [str(s) for s in row.get("sources") or []]}
    return out


def _strip_marks(text: str) -> str:
    """A form's letters without its accent marks (ḗ → e).

    The same morpheme is written at different grades (‑mō beside ‑mṓ); the
    marks move with the accent, so a blind match may say two spellings are one
    morpheme — but only when exactly one form answers.
    """
    return "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))


@lru_cache(maxsize=16)
def _suffix_entries(lang: str = ROOT_LANG) -> dict[str, tuple[dict, ...]]:
    """The stage's own suffix entries, by the headword they are recorded under.

    The dictionary's record of a morpheme — its meaning and its page — is the
    first place a construction piece is looked up, so a reader hovering a
    suffix sees the same sense the entry carries (2026-11-08).
    """
    out: dict[str, list[dict]] = {}
    for entry in data.lexicon(lang):
        pos = str(entry.get("pos") or "").lower()
        form = str(entry.get("word") or "")
        # An affix-shaped headword — one written with a leading hyphen — is a
        # morpheme even when the dictionary files it as a clitic (*-kʷe "and").
        # A prefix (n̥-, dus-) is written the other way round and is never read
        # as a suffix, so a piece and its homograph cannot be confused.
        if not form.startswith("-"):
            continue
        if pos != "suffix" and pos not in ("conj", "particle", "clitic", "postp"):
            continue
        out.setdefault(form, []).append({
            "word": form,
            "pos": pos,
            "gloss": next((g for g in entry.get("gloss") or [] if g), "").strip(),
            "glosses": [g for g in entry.get("gloss") or [] if g],
            "link": f"#/word/{lang}/{quote(form)}",
            "url": entry.get("url") or "",
        })
    return {form: tuple(rows) for form, rows in out.items()}


@lru_cache(maxsize=16)
def _suffix_blind(lang: str = ROOT_LANG) -> dict[str, tuple[str, ...]]:
    """The suffix headwords of a stage grouped by their letters alone."""
    out: dict[str, list[str]] = {}
    for form in _suffix_entries(lang):
        out.setdefault(_strip_marks(form.strip("-")), []).append(form)
    return {key: tuple(forms) for key, forms in out.items()}


def _suffix_senses(lang: str, form: str) -> tuple[tuple[dict, ...], str]:
    """The dictionary entries that record this form as a suffix.

    The exact spelling wins: *-os and *-ós are different formations (an
    action noun's stem beside an oxytone adjective) and merging them would put
    one meaning on the other's words. Only a form with no entry of its own may
    be matched accent-blind — ‑mō is the dictionary's ‑mṓ — and only when one
    form answers, never when the blind key is itself ambiguous (which is
    exactly the ‑os/‑ós case).
    """
    entries = _suffix_entries(lang)
    key = form.strip("*")
    if entries.get(key):
        return entries[key], "form"
    bare = _strip_marks(key.strip("-"))
    # The blind key has to answer with one spelling. ‑o‑ is not *‑ō and ‑ōm is
    # not *‑óm: when two forms share the letters, neither may be put on the
    # other's words (2026-11-08).
    family = _suffix_blind(lang).get(bare, ())
    hits = tuple(f for f in family if f.strip("-") != key.strip("-"))
    if len(family) == 1 and len(hits) == 1 and entries.get(hits[0]):
        return entries[hits[0]], "marks"
    return (), ""


def _curated_key(row: dict) -> str:
    """The whole suffixed form a hand-written row stands for (-ti- + -s → -tis).

    A handbook row writes the stem and the ending separately, so matching it to
    a corpus piece by the stem alone would put the *-ti-* abstract on the
    locative ‑ti. The key is the form the word actually wears.
    """
    return f"-{str(row.get('form') or '').strip('-')}{str(row.get('ending') or '').strip('-')}"


def _curated_for(lang: str, form: str) -> dict | None:
    """The hand-written row that is this piece, if there is one.

    A handbook row may be written at another grade (‑mō beside the
    dictionary's ‑mṓ), and that blind match is allowed only when the
    dictionary does not record this exact spelling itself: ‑éh₂ on an action
    noun is the dictionary's action-noun suffix, not the handbook's collective
    ‑eh₂ (2026-11-08).
    """
    rows = _curated_suffixes(lang)
    if not rows:
        return None
    key = form.strip("*")
    for row in rows:
        if _curated_key(row) == key:
            return row
    if _suffix_entries(lang).get(key):
        return None
    bare = _strip_marks(key.strip("-"))
    hits = [row for row in rows if _strip_marks(_curated_key(row).strip("-")) == bare]
    return hits[0] if len(hits) == 1 else None


def _piece_id(form: str) -> str:
    """A stable key for a piece that is not in the hand-written list.

    A piece written ‑i‑ is a stem-formative, not the adverbial ‑i, so it keeps
    a key of its own: a picker click has to name exactly one row
    (2026-11-08).
    """
    key = form.strip("*").strip("-")
    return f"stem-{key}" if form.strip("*").endswith("-") else key


#: The single-vowel pieces that are a stem-formative rather than an ending
#: (‑o‑, ‑i‑, ‑u‑): the noun they build wears its nominative *-s after it.
_STEM_PIECE_RE = re.compile(r"^-[aeiouāēīōū]-$")

#: The sections the recorded-morphology menu groups its rows into, in the order
#: it prints them (2026-11-08: a picker of 135 forms in one flat list cannot be
#: read; the record itself says what kind of word each morpheme builds, so the
#: menu can group by that and not by taste). The keys are stable — the front end
#: hangs the submenus on them — and the names are what the menu shows.
MORPH_SECTIONS = (
    ("derivation-noun", "noun-forming"),
    ("derivation-adj", "adjective-forming"),
    ("derivation-verb", "verb-forming"),
    ("derivation-adv", "adverb-forming"),
    ("derivation-other", "other derivation"),
    ("stem", "stem formatives"),
    ("ending", "inflectional endings"),
    ("clitic", "clitics"),
)

#: Which kind of word a dictionary sense builds, in the sources' own words
#: ("Forms adjectives from roots"). A sense that names no kind never claims a
#: noun's ending. The words are matched whole: "adverbial" contains "verb" and
#: must not pass for a verb's suffix (2026-11-08).
_SENSE_KINDS = (
    ("verb", re.compile(r"\bverbs?\b")),
    ("adj", re.compile(r"\badjectiv(?:e|es|al)\b")),
    ("noun", re.compile(r"\b(?:nouns?|feminine|collective|mass)\b")),
    ("adv", re.compile(r"\badverbi?al\b|\badverb\b")),
)

#: The part of speech a sense has to fit, when the source says which words it
#: builds.
_POS_SENSE_KIND = {"noun": "noun", "num": "noun", "pron": "noun",
                   "verb": "verb", "adj": "adj", "adv": "adv"}


def _morph_section(row: dict) -> str:
    """Which section of the picker a recorded morpheme belongs in.

    A hand-written row may name its own section (``section: stem`` in the
    morphology YAML); otherwise the kind of the row decides — an ending is an
    ending, a clitic is a clitic, a single vowel between dashes is a
    stem-formative — and a derivational suffix is grouped by the kind of word
    its gloss says it builds ("forms agent nouns" is a noun-forming suffix).
    A row that states no kind lands in *other derivation*: the menu says it is
    not classified rather than guessing (2026-11-08).
    """
    explicit = str(row.get("section") or "").strip()
    if explicit:
        return explicit
    kind = str(row.get("kind") or "suffix")
    if kind == "ending":
        return "ending"
    if kind == "clitic":
        return "clitic"
    form = str(row.get("form") or "").strip("*").strip()
    if _STEM_PIECE_RE.match(form) or str(row.get("id") or "").startswith("stem-"):
        return "stem"
    return {"noun": "derivation-noun", "adj": "derivation-adj",
            "verb": "derivation-verb", "adv": "derivation-adv"}.get(
                _sense_kind(str(row.get("gloss") or "")), "derivation-other")


def _sense_kind(gloss: str) -> str:
    """The kind of word a sense builds: the first kind it names.

    "Forms nouns from thematic adjectives" builds nouns; "creates possessive
    adjectives from nouns" builds adjectives. The head of the sentence is the
    first one written, so that is the one read.
    """
    low = (gloss or "").lower()
    best, at = "", len(low) + 1
    for kind, pattern in _SENSE_KINDS:
        m = pattern.search(low)
        if m is not None and m.start() < at:
            best, at = kind, m.start()
    return best


def _fitted_senses(senses: tuple[dict, ...], pos: str) -> tuple[dict, ...]:
    """The senses that build this kind of word, when the source names one."""
    kind = _POS_SENSE_KIND.get((pos or "").lower(), "")
    if not kind:
        return senses
    hits = tuple(s for s in senses if _sense_kind(s["gloss"]) == kind)
    return hits or senses


def _piece_is_tail(form: str, word: str) -> bool:
    """Whether these letters end the word (true when no word is named).

    The endings table says what letters are as a paradigm ending, and letters
    only are that ending when they close the word they are read on.
    """
    if not word:
        return True
    return _strip_marks(word).endswith(_strip_marks(form.strip("*").strip("-")))


def _piece_record(lang: str, form: str, stated: str = "", hint: str = "",
                  word: str = "", pos: str = "") -> dict:
    """What one construction piece means, and where its record lives.

    Four sources, in the order the page trusts them: the word's own parenthesis
    ("deverbal adjectival suffix"), the hand-written suffix row for the same
    morpheme, the grammatical ending the letters are, and finally the suffix
    entries the dictionary keeps for that spelling. Nothing is invented: a
    piece no source names keeps an empty gloss and the page says nothing.
    ``word`` and ``pos`` are the entry the piece stands in: they decide whether
    the letters really are that word's closing ending, and which of several
    recorded senses builds a word of its kind — ‑os closes ménos as an s-stem
    and h₂ŕ̥tḱos as an o-stem, and ‑ti in ḱréddʰeh₁ti is the verb's ending, not
    the adverbial suffix of the same spelling (2026-11-08).
    ``hint`` is what the row itself calls the piece — a stem-formative is the
    record's word, not a cited suffix, and says so.
    """
    curated = _curated_for(lang, form)
    ending = _endings(lang).get(form) or {}
    senses, how = _suffix_senses(lang, form)
    gloss = (stated or "").strip()
    basis = "stated" if gloss else ""
    detail = ""
    kind = hint or "suffix"
    if not gloss and curated and curated.get("gloss"):
        gloss, basis = curated["gloss"], "handbook"
    if not gloss and ending.get("name") and _piece_is_tail(form, word):
        gloss, basis = ending["name"], "ending"
        detail = ending.get("note") or ""
        kind = hint or "ending"
    if not gloss and senses:
        fitted = _fitted_senses(senses, pos)
        gloss, basis = fitted[0]["gloss"], "dictionary"
        if len(fitted) > 1:
            detail = "; ".join(s["gloss"].rstrip(". ") for s in fitted[:3])
    if gloss and basis != "dictionary" and senses:
        # The record's own words stay beside a reading taken from the paradigm
        # or the handbook, so a reader can see where the two differ.
        first = senses[0]["gloss"].rstrip(". ")
        note = f"the dictionary records {form} as “{first}”"
        detail = f"{detail}; {note}" if detail else note
    if kind == "suffix" and senses and senses[0].get("pos") in (
            "conj", "particle", "clitic", "postp"):
        # *-kʷe is recorded as a clitic, not a derivational suffix.
        kind = "clitic"
    return {
        "form": form,
        # The picker's key: the hand-written row's id when the morpheme has
        # one, so clicking the suffix in a word selects the same row the
        # handbook defines (eh2, tis …).
        "id": (curated or {}).get("id") or _piece_id(form),
        "kind": kind,
        "gloss": gloss,
        # Which source the gloss came from: the word's own words, the
        # handbook, the paradigm's ending, or the dictionary entry.
        "basis": basis,
        # The longer reading behind the one-line meaning: what the ending is
        # made of, or the dictionary's further senses.
        "detail": detail,
        # The dictionary entries for this spelling, with their own words, and
        # the page a reader can open to read them.
        "senses": [s["gloss"] for s in senses],
        "entry": senses[0]["link"] if senses else "",
        "entry_source": senses[0]["url"] if senses else "",
        "entry_match": how,
        "curated": bool(curated),
    }


def _piece_index(lang: str = ROOT_LANG) -> dict[str, dict]:
    """Every suffix a stage's own constructions name, with the words it builds.

    This is the "where it can be applied" half of the suffix panel: the pieces
    are read from the etymologies, never written down, so a word added to the
    corpus appears here and in the picker at the same time (2026-11-08: a suffix recorded on one root must be selectable on the others).
    """
    return _construction_scan(lang)[1]


@lru_cache(maxsize=16)
def morphology(lang: str = ROOT_LANG) -> dict:
    """Every suffix and ending a stage records, and where it is recorded.

    Three kinds of row share one list, because a reader choosing a suffix does
    not care which drawer it came from: the hand-written handbook suffixes, the
    pieces the stage's own constructions wear (with the words they build and
    the bases they attach to), and the stage's remaining suffix entries — a
    morpheme the dictionary records even though no etymology in the corpus
    happens to build a word with it (2026-11-08: if a suffix is
    recorded anywhere it must be selectable everywhere it applies).

    A reconstructed stage builds its words by hand, so it gets the whole menu.
    An attested stage keeps the picker empty — its words are known, not built —
    but the entries a human wrote for it still answer the timeline's form
    builder (Persian's suffixes and endings, 2026-11-10): the builder asks what
    a stage *would* make, and it may only offer morphemes the record holds.
    """
    path = data.DATA / "morphology" / f"{lang}.yaml"
    raw = (data._load_yaml(path) if path.exists() else {}) or {}
    if kind_of(lang) != "proto":
        return {"language": raw.get("language", lang), "note": "",
                "endings": list(raw.get("endings") or []),
                "suffixes": list(raw.get("suffixes") or []),
                "joining": dict(raw.get("joining") or {}),
                "sections": []}
    rows: list[dict] = []
    by_key: dict[str, dict] = {}
    for source in _curated_suffixes(lang):
        row = dict(source)
        row.update({"kind": "suffix", "recorded": 0, "examples": [], "bases": [],
                    "entry": "", "senses": [], "entry_match": "", "stated": "",
                    "detail": ""})
        rows.append(row)
        by_key[_strip_marks(_curated_key(row).strip("-"))] = row
    index = _piece_index(lang)
    for form, rec in sorted(index.items(), key=lambda kv: (-len(kv[1]["words"]), kv[0])):
        common = rec["glosses"].most_common(1)[0][0] if rec["glosses"] else ""
        # The menu states the general meaning of the morpheme — the grammatical
        # ending it is, else the dictionary's suffix entry — and keeps the
        # corpus's own phrasing as a note; the word's construction line still
        # quotes the word's own parenthesis first.
        piece = _piece_record(lang, form)
        if not piece["gloss"]:
            piece = _piece_record(lang, form, common)
        words = rec["words"]
        examples = [w["word"] for w in words[:3]]
        curated = _curated_for(lang, form)
        if curated:
            row = by_key.get(_strip_marks(_curated_key(curated).strip("-")))
            if row is not None:
                row["recorded"] = len(words)
                row["examples"] = examples
                row["bases"] = rec["bases"][:6]
                if not row.get("entry") and piece.get("entry"):
                    row["entry"] = piece["entry"]
                continue
        rows.append({
            "id": piece["id"], "form": form, "surface": "",
            # A stem-formative (‑i‑, ‑o‑, ‑u‑) owns the nominative *-s the noun
            # wears after it, so composing with it builds the whole word.
            "ending": "s" if _STEM_PIECE_RE.match(form) else "",
            # A generated piece composes the same way the hand-written ones do:
            # the word's own thematic vowel goes before the suffix.
            "attach": "drop", "gloss": piece["gloss"], "detail": piece["detail"],
            "note": (f"the words call it “{common}”" if common and
                     common != piece["gloss"] else ""),
            "outcomes": "", "sources": [], "stated": common,
            "example": f"{rec['bases'][0]} + {form} → {examples[0]}" if examples else "",
            "rule": "", "curated": False,
            "kind": piece["kind"],
            "recorded": len(words), "examples": examples, "bases": rec["bases"][:6],
            "entry": piece["entry"], "senses": piece["senses"],
            "entry_match": piece["entry_match"], "basis": piece["basis"],
        })
    # A suffix entry no construction wears yet is still a recorded suffix: the
    # dictionary says what it means and gives it a page, so the picker offers
    # it with `recorded: 0` and names no base it was seen on. The menu keys on
    # the exact spelling — ‑ónts and ‑onts are two recorded forms, and dropping
    # one for the other hid the accented entry altogether — and only a row with
    # no entry of its own takes a near-homograph's record (2026-11-08).
    forms = {row["form"] for row in rows}
    by_blind = {_strip_marks(row["form"].strip("*-").strip("-")): row for row in rows}
    for form, senses in sorted(_suffix_entries(lang).items()):
        if form in forms:
            continue
        host = by_blind.get(_strip_marks(form.strip("*-").strip("-")))
        if host is not None and not host.get("entry"):
            host["entry"] = senses[0]["link"]
            host["senses"] = [s["gloss"] for s in senses]
            host["entry_match"] = "marks"
            if not host.get("gloss"):
                host["gloss"] = senses[0]["gloss"]
            continue
        forms.add(form)
        rows.append({
            "id": _piece_id(form), "form": form, "surface": "", "ending": "",
            "attach": "drop", "gloss": senses[0]["gloss"], "detail": "", "note": "",
            "outcomes": "", "sources": [], "stated": "",
            "example": "", "rule": "",
            "curated": False,
            # *-kʷe is a clitic, and the menu says so instead of listing it
            # beside the derivational suffixes as one of them (2026-11-08).
            "kind": "clitic" if senses[0].get("pos") in (
                "conj", "particle", "clitic", "postp") else "suffix",
            "recorded": 0, "examples": [],
            "bases": [], "entry": senses[0]["link"],
            "senses": [s["gloss"] for s in senses], "entry_match": "form",
        })
    # Two rows may want the same key — the dictionary's ‑kos beside the
    # handbook's ‑ko‑ — and a click has to name exactly one of them, so a
    # repeat is numbered in the order the menu shows them (2026-11-08).
    used: dict[str, str] = {}
    for row in rows:
        key = row["id"]
        if key in used and used[key] != row["form"]:
            n = 2
            while f"{key}-{n}" in used:
                n += 1
            row["id"] = f"{key}-{n}"
        used[row["id"]] = row["form"]
    # The menu is a set of sections, each with a submenu: every row says which
    # section it belongs to, and the stage lists the sections it actually has
    # with the number of forms in each (2026-11-08).
    names = dict(MORPH_SECTIONS)
    for row in rows:
        section = _morph_section(row)
        row["section"] = section
        row["section_name"] = names.get(section, section)
    sections = [{"id": key, "name": name,
                 "count": sum(1 for row in rows if row["section"] == key)}
                for key, name in MORPH_SECTIONS]
    return {"language": raw.get("language", lang),
            "note": (raw.get("note") or "").strip(),
            "endings": list(_endings(lang).values()), "suffixes": rows,
            "sections": [sec for sec in sections if sec["count"]]}


#: The dictionary spells a derivative's construction out in its etymology:
#: "From *wĺ̥kʷos + *-íh₂s." That sentence is a record of the formation, so the
#: page can print the pieces under the headword instead of leaving the reader to
#: parse prose (2026-11-08). Only a starred base is accepted: any
#: other "From ..." sentence names a single source, not an arithmetic.
#: The dictionary often glosses the base and the suffix in parentheses
#: ("*ǵʰey- (“winter”) + *-mn̥ (action suffix)"), so a parenthesis may sit
#: between the pieces without breaking the arithmetic.
#: One *piece* of an arithmetic: a starred form and the gloss the entry puts
#: beside it.
_TERM_RE = re.compile(
    r"\*\s*(?P<form>[^\s+,;\[\]]+)\s*"
    r"(?:\((?P<gloss>(?:[^()]|\([^()]*\)){0,90})\)\s*)?")
#: The whole arithmetic, not just its first pair: an entry may chain three
#: pieces (*dus- + *ménes- + *-s) and dropping the first one would print a
#: construction that does not build the word at all (2026-11-08).
_ARITHMETIC_RE = re.compile(
    r"\*[^\s+,;\[\]]+?\s*(?:\((?:[^()]|\([^()]*\)){0,90}\)\s*)?"
    # A record may join its pieces with a conjunction before the plus — "From
    # *h₂eḱ- (“sharp”) + *h₂ṓws (“ear”) and + *-yéti (denominative verbal
    # suffix)" — and the chain used to stop at the word before the conjunction,
    # so the suffix the sentence names was missing from the timeline (admin,
    # 2026-11-13).
    r"(?:(?:\s*,?\s*(?:and|or|plus))?\s*\+\s*(?:[a-z]+\s+){0,3}"
    r"\*[^\s+,;\[\]]+\s*(?:\((?:[^()]|\([^()]*\)){0,90}\)\s*)?)+")

#: The words that make an arithmetic an etymology rather than a list: a
#: sentence is only read for a construction when it says how the word is
#: derived, not when it merely mentions two starred forms side by side.
_DERIVE_CUE_RE = re.compile(
    r"\b(?:from|deriv\w*|built on|formed (?:on|from)|analys\w+|analyz\w+|"
    r"formation|construction|rebuilt|equivalent to|"
    # A word the entry names as another form's product is a product, even
    # without the word "from": "an active participle of the root *h₃ed- +
    # *-ónts", "petrified instrumental singular of *h₁er- + *-éh₁", "a dvigu
    # compound of *ḱm̥tóm + *gʷṓws", "reanalyzed root of *(s)pen(h₁)- +
    # *-deti" (2026-11-08: a suffix the entry names is a recorded piece, and
    # the picker offers what the corpus states).
    r"nominali[sz]ation|compound|participle|petrified|construed as|"
    r"reanaly[sz]ed|frm)\b", re.I)

#: A second arithmetic in the same entry is an alternative analysis only when
#: the entry says so ("either … or", "other possibilities", "also"). Anything
#: else is a chain ("From earlier *póds, from *ped- + *-s"), not a rival.
_ALTERNATIVE_CUE_RE = re.compile(
    r"\b(?:or|alternatively|alternate|also|other|possibilit\w*|versus|"
    r"as opposed|on the other hand)\b", re.I)

#: A second analysis is often introduced by the scholar who argues it —
#: "Pokorny suggests a derivation from *(h₁)én + *-dʰi" — not by "or".
_AUTHOR_CUE_RE = re.compile(
    r"\b(?:argues|argued|suggests|suggested|proposes|proposed|according to|"
    r"reconstructs|reconstructed|takes)\b", re.I)

#: An entry may list its analyses without an arithmetic for the first one:
#: "Thus other possibilities listed by NIL and Ozoliņš (2015) are: …".
_ANALYSIS_CUE_RE = re.compile(
    r"\b(?:possibilit\w*|analys\w*|analyz\w*|analysis|argument|account|"
    r"reconstruct\w*|alternative)\b", re.I)

#: A hedged statement is an argument, not the entry's own reading.
_HEDGE_RE = re.compile(
    r"\b(?:may be|might|possibly|presumably|presumed|supposed|apparently|"
    r"probably|likely|unlikely|either|could|perhaps|maybe|alternatively|"
    r"alternate|candidate|possible)\b", re.I)

#: An etymology walks a chain backwards ("From Proto-Indo-European *prugʰ-ḱó-s,
#: from *prugʰ- + *-ḱós"): the arithmetic at the end of that chain is the
#: ancestor's formation, not this stage's. A stage name before the arithmetic
#: means the chain has crossed a boundary, so the row is dropped (2026-11-08).
_CHAIN_BOUNDARY_RE = re.compile(
    r"\b(?:Proto-[A-Z][A-Za-z-]*|Old [A-Z][a-z]+|Middle [A-Z][a-z]+|"
    r"Ancient [A-Z][a-z]+|Classical [A-Z][a-z]+|New [A-Z][a-z]+)\b")

#: A sentence may state the construction of a *related* word instead of this
#: one — "Reanalysed root of *ḱléyti, from *ḱel- + *-éyti", "Deadjectival form
#: of *úd-er-o-s", "the feminine is from …". That arithmetic belongs to the
#: other form, so it is not printed under this headword (2026-11-08).
_RELATED_FORM_RE = re.compile(
    r"\b(?:root|form|word|noun|adjective|stem|verb|participle|feminine|"
    r"masculine|neuter|plural|singular|dual|genitive|oblique|accusative|"
    r"vocative)\s+of\s+\*"
    r"|\b(?:feminine|masculine|neuter|plural|genitive|oblique|dual)\b"
    r"[^.;]{0,40}\bfrom\b", re.I)

#: A derivative stated in prose rather than as arithmetic — "An i-stem noun
#: built on the root *h₂wl̥p-", "u-stem derivation from the root *sewH-",
#: "n-stem noun of *gʷʰer-". The dictionary names both the base and the stem
#: class, so the row can print base + stem-formative instead of nothing
#: (2026-11-08: h₂wl̥pís showed no construction at all).
_STEM_CONSTRUCTION_RE = re.compile(
    r"\b(?P<stem>[a-zāēīōū]-stem)\s+"
    r"(?:derivation|noun|adjective|nominal|stem|form)\s+"
    r"(?:built on|formed from|formed on|derived from|derivation from|from|of)\s+"
    r"(?:the\s+)?(?:root|stem|adjective|verb)?\s*"
    r"(?P<base>\*[^\s,;()\[\]“”\"'’]+)", re.I)

#: Some entries name only the stem a word is cut from — dl̥h₁gʰós is "From the
#: stem *delh₁gʰ- (“to be long”)". The ending is the one the headword itself
#: wears, so the row prints base + that ending; the base must be a starred
#: ancestor the entry already lists, so a sentence about another word's stem
#: cannot be read as this word's construction (2026-11-08).
_FROM_STEM_RE = re.compile(
    r"\bfrom\s+the\s+stem\s+\*(?P<base>[^\s,;()\[\]“”\"'’]+)", re.I)

#: The endings a "from the stem" row may print: whatever the headword carries
#: after the stem. A tail outside this set means the stem was not really found
#: in the word, and no row is printed rather than a guessed one.
_TAIL_ENDINGS = frozenset({"os", "ós", "om", "óm", "on", "ón", "is", "ís",
                          "im", "ím", "us", "ús", "um", "úm", "ā", "ē", "ī",
                          "ō", "ū", "s"})

#: The dictionary's own gloss of a morpheme: "*‑rós (Caland system suffix)".
_MORPHEME_GLOSS_RE = re.compile(r"\s*\(([^()]{2,60})\)")

#: A hedged derivation that names only the root the word is built on — the bear
#: is "possibly nominalized from root *h₂retḱ-", the sea "perhaps from a root
#: *mer-". The entry states a base and no suffix, so the row prints that base;
#: when it calls the word a nominalization, the stem-formative the word itself
#: carries is printed beside it, because the ending is the record's word, not a
#: cited suffix (2026-11-08: show this as a possible construction).
_ROOT_CONSTRUCTION_RE = re.compile(
    r"\b(?P<hedge>possibly|perhaps|probably|presumably|may\s+be|might\s+be)\s+"
    r"(?P<how>nominali[sz]ed|derived|extended)?\s*"
    r"from\s+(?:a\s+|an\s+|the\s+)?(?:LIV\s+)?(?:verbal\s+)?root\s+"
    r"\*(?P<base>[^\s,;()\[\]“”\"'’]+)", re.I)

#: The same sentence without the word "root". Only a base that is a root
#: headword of this stage is accepted, so "probably from *meh₁-" is read while
#: "from earlier *méh₁n̥s-s" — a phonological pre-form, not a construction —
#: stays out.
_ROOT_FROM_RE = re.compile(
    r"\b(?P<hedge>possibly|perhaps|probably|presumably|may\s+be|might\s+be)\s+"
    r"(?P<how>nominali[sz]ed|derived|extended)?\s*"
    r"from\s+\*(?P<base>[^\s,;()\[\]“”\"'’]+)", re.I)

#: Grammatical words are not formations: "Possibly from *h₁én / *én" says where
#: an adverb comes from, not how it is built, so no row is printed for one.
_NO_FORMATION_POS = frozenset({"adv", "prep", "conj", "particle", "part", "interj"})

#: A root the entry enlarges with a suffix it names in prose — sterbʰ- is
#: "probably from *dʰer- … enlarged by *-bʰ" — so the row can wear it.
_ENLARGED_RE = re.compile(r"(?:enlarged|extended|suffixed)\s+(?:by|with)\s+\*(-\S+)", re.I)

#: A derivation introduced through another headword — "the synonym *káp-ōl,
#: which likewise may be from *kap-" — states that word's root, not this one's
#: (2026-11-08: gʰébʰōl was given *kap-).
_OTHER_WORD_RE = re.compile(r"\b(?:synonym|homonym|doublet|antonym|variant)\b", re.I)

#: The stem-formative a headword's own ending carries, used by a row whose
#: entry calls the word a nominalization but names no suffix (h₂ŕ̥tḱos → *-o-).
_ENDING_STEM = (("os", "o"), ("om", "o"), ("on", "o"), ("od", "o"),
                ("is", "i"), ("im", "i"), ("us", "u"), ("um", "u"))


def _sentences(text: str) -> list[str]:
    """Split an etymology into sentences, ignoring marks inside a gloss.

    The dictionary glosses morphemes in parentheses — *men- ("to think; mind")
    — and a plain split on [.;] cuts such a gloss in half, which then hides the
    arithmetic the entry states (ménos, gʰébʰōl and 33 others showed no
    construction for that reason; 2026-11-08).
    """
    out: list[str] = []
    start = depth = 0
    for i, ch in enumerate(text):
        depth += (ch == "(") - (ch == ")")
        if ch in ".;" and depth <= 0:
            out.append(text[start:i + 1])
            start = i + 1
    if text[start:].strip():
        out.append(text[start:])
    return out


def _stem_letter(stem: str) -> str:
    return stem.split("-")[0].lower()


def _morpheme_rows(lang: str, tokens: list[tuple[str, str]],
                  hint: str = "", word: str = "", pos: str = "") -> list[dict]:
    """Match the forms the entry names to the stage's cited suffixes.

    A form that is the same morpheme as a registered suffix carries its id, so
    the picker can offer to swap it; the entry's own parenthesis is kept as the
    gloss, and a piece that states nothing is given the meaning the stage's
    record holds for it — the hand-written row, the grammatical ending, or the
    dictionary's suffix entry (2026-11-08: `-ós` must say what it
    is). This is the raw read: it never consults ``_piece_index``, which is
    built from these rows in the first place.
    """
    rows = []
    table = _endings(lang)
    for form, gloss in tokens:
        piece = _piece_record(lang, form, gloss, hint, word=word, pos=pos)
        # A stem-formative is not an ending, so the noun it builds wears
        # its own nominative *-s after it (‑i‑ + *-s → h₂wl̥pís).
        ending = "s" if _STEM_PIECE_RE.match(form) else ""
        # The ending's own name, from the stage's table: the page must say
        # *-s is the athematic nominative singular and not leave the letter
        # unexplained (2026-11-09, the *h₂wl̥pís question).
        end_row = (table.get(f"-{ending}") or table.get(ending) or {}) if ending else {}
        rows.append({
            "form": form,
            "id": piece["id"],
            "gloss": piece["gloss"],
            "detail": piece["detail"],
            "ending": ending,
            "ending_name": str(end_row.get("name") or ""),
            # The entry's own words for this piece, before the registry filled
            # them in: the corpus phrasing ("deverbal adjectival suffix") is a
            # record of how the words name the morpheme, and the picker shows
            # it as a note, not as the meaning.
            "stated": (gloss or "").strip(),
            "kind": piece["kind"],
            "basis": piece["basis"],
            "entry": piece["entry"],
            "curated": piece["curated"],
        })
    return rows


def _base_row(lang: str, base: str, gloss: str = "") -> dict:
    """One piece of a construction, with the meaning its own entry gives it.

    The etymology quotes a gloss for some pieces — *mer- (“sea, lake, wetland”)
    — and says nothing for most (*anda- + *swarō).  The row used to print only
    the quotation, so a piece the stage's glossary *does* hold came back
    ``known: true`` with no meaning: the page could open its entry and still
    read as if the word had not been recognised (admin, 2026-11-12).  The
    piece is now answered by the same reader as the rung and the ✓
    (`_lemma_entry`), so a word known in one place is known in all three.
    """
    entry = _lemma_entry(lang, base)
    known = bool(entry)
    # The entry writes its gloss already quoted — *mer- (“sea, lake, wetland”)
    # — and the page quotes what it is given, so the marks are dropped here
    # instead of printing ““sea, lake, wetland”” (2026-11-08). A leading ``~``
    # is the dictionary hedging its own gloss ("~ to be long"), not part of it.
    said = gloss or _rung_gloss((entry or {}).get("gloss") or [], 70)
    return {"form": base, "known": known,
            "gloss": said.strip().strip("“”\"'").strip().lstrip("~").strip(),
            "link": f"#/word/{lang}/{quote((entry or {}).get('word') or base)}"
                    if known else ""}


def _raw_constructions(entry: dict, lang: str = ROOT_LANG) -> list[dict]:
    """Every construction the entry states, read from its own words only.

    This is the first pass: the entry is parsed, the pieces are matched to
    their records, and nothing is looked up in the corpus. ``constructions()``
    wraps it and adds the count and examples of the words that wear each piece,
    which needs the whole-corpus index — and that index is built from these
    rows, so it must not be read here (2026-11-08).
    """
    text = str(entry.get("etym") or "")
    word = str(entry.get("word") or "")
    rows: list[dict] = []
    # Only a reconstructed stage's pages read a construction from prose. An
    # attested word's "From *X + *Y" is almost always its *ancestor's*
    # formation — English lucre from PIE *leh₂w- + *-tlom — and printing that
    # under lucre would credit the modern word with the proto-word's build. The
    # ladder already carries the ancestor; the row belongs to the etymon
    # (2026-11-08).
    if text and kind_of(lang) == "proto":
        rows.extend(_stated_constructions(text, lang, word,
                                          str(entry.get("pos") or "")))
        # A formation stated in words rather than as an arithmetic: the
        # reduplicated stative/perfect ("Reduplicated stative of the root
        # *h₂eyḱ-") is one root repeated with a vowel of its own, and the
        # record names it as plainly as a suffix (admin, 2026-11-12).
        read = _reduplication_read(entry)
        if read:
            rows.append({
                "base": _base_row(lang, read["root"], read["gloss"]),
                "members": [], "suffixes": [],
                "etym": read["sentence"],
                "kind": "reduplication",
                "formation": read["formation"],
                "confidence": read["confidence"],
                "source": "the entry",
            })
        if not rows:
            stem = (_stem_construction(text, lang, word, str(entry.get("pos") or ""))
                    or _from_stem_construction(entry, text, lang))
            if stem:
                rows.append(stem)
        if (entry.get("pos") or "").lower() not in _NO_FORMATION_POS:
            rows.extend(_root_constructions(text, word, lang,
                                            str(entry.get("pos") or "")))
    for row in _stored_constructions(lang).get(word) or []:
        rows.append(_resolve_stored(row, lang))
    # The same analysis written twice (an arithmetic and a prose row) is one
    # construction; the rows are keyed by base and the pieces they name.
    seen: set[tuple] = set()
    unique: list[dict] = []
    for row in rows:
        key = (row["base"]["form"], tuple(s["form"] for s in row["suffixes"]))
        if key in seen or (not row["suffixes"] and row["base"]["form"] in
                           {r["base"]["form"] for r in unique}):
            # A row with no piece is kept only when its base is new: an entry
            # that names a bare root twice has said it once.
            continue
        seen.add(key)
        unique.append(row)
    return unique


def constructions(entry: dict, lang: str = ROOT_LANG) -> list[dict]:
    """Every construction the entry states, the main one first.

    Most entries state one, as an arithmetic (*wĺ̥kʷos + *-íh₂s) or as a stem
    class in prose (an i-stem noun built on *h₂wl̥p-). Some state two or more
    rival analyses — *kers- + *-nós or *ker-s- + *-nós — and some argue one in
    a later sentence instead of an arithmetic. Each candidate keeps the
    sentence it was read from and a confidence: ``stated`` (the entry presents
    it plainly), ``argued`` (an author's proposal or a hedged reading), or
    ``proposed`` (this repo's own, stored in data/constructions/). Nothing is
    invented: an entry with no stated construction gets no rows (2026-11-08: a word may have several, shown as possible reconstructions).
    """
    return [_with_piece_record(row, lang) for row in _raw_constructions(entry, lang)]


def _with_piece_record(row: dict, lang: str) -> dict:
    """Say where each piece of a construction is recorded, and what it means.

    A piece that states nothing takes the meaning the other words give the same
    form (‑né- is the nasal infix even in the row whose entry forgot to say so),
    and every piece carries the number of words that wear it plus a few of
    their names — the "places it can be applied" the picker shows beside the
    meaning (2026-11-08).
    """
    index = _piece_index(lang)
    for piece in row.get("suffixes") or []:
        rec = index.get(piece["form"]) or {}
        words = rec.get("words") or []
        piece["recorded"] = len(words)
        piece["examples"] = [w["word"] for w in words[:3]]
        if not piece.get("gloss") and rec.get("glosses"):
            piece["gloss"] = rec["glosses"].most_common(1)[0][0]
    return row


def construction(entry: dict, lang: str = ROOT_LANG) -> dict | None:
    """The entry's main construction, or ``None`` when it states none."""
    rows = constructions(entry, lang)
    return rows[0] if rows else None


def _construction_covers(parts: list[str], word: str = "", sentence: str = "") -> bool:
    """Whether these pieces, in this order, build *this* word.

    The first piece has to stand at the word's beginning.  A vowel may differ
    (ablaut), a laryngeal may be lost, an ``(s)`` may be mobile, and the entry
    may say that two sounds swapped places (metathesis) — all of those are
    statements about the same word.  A construction whose first piece is not
    there at all is describing a different form, and it is not shown
    (2026-11-08: "the constructions should obviously recreate the
    actual word").
    """
    if not word or not parts:
        return True
    first = letters(parts[0].strip("*-"))
    target = letters(word)
    if not first or not target:
        return True
    if first[0] == target[0] or target.startswith(first) or first.startswith(target):
        return True
    if first[:2] and first[:2] in target[:3]:
        return True                      # zero grade (*wed- > *ud-rós)
    if first[0] in "hH" and target[0] not in "hH":
        return True                      # a lost laryngeal
    if re.search(r"\bmetathes\w*|s-mobile|mobile s\b", sentence or "", re.I):
        return True
    return False


def _stated_constructions(text: str, lang: str, entry_word: str = "",
                          pos: str = "") -> list[dict]:
    """Every arithmetic the entry states, in the order it states them.

    The first becomes the word's construction when the sentence says how the
    word is derived; each later one is accepted only where the entry flags an
    alternative, and is then marked ``argued`` — a rival analysis is not the
    same claim as the entry's own header line.
    """
    out: list[dict] = []
    for sentence in _sentences(text):
        for m in _ARITHMETIC_RE.finditer(sentence):
            before = sentence[:m.start()]
            if _RELATED_FORM_RE.search(before) or _CHAIN_BOUNDARY_RE.search(before):
                continue
            if out:
                if not (_ALTERNATIVE_CUE_RE.search(before)
                        or _AUTHOR_CUE_RE.search(before)):
                    continue
                confidence = "argued"
            else:
                if not (_DERIVE_CUE_RE.search(before)
                        or (_ALTERNATIVE_CUE_RE.search(before)
                            and _ANALYSIS_CUE_RE.search(before))):
                    continue
                confidence = "argued" if _HEDGE_RE.search(before) else "stated"
            terms = [(t.group("form").strip(".,;:)"), (t.group("gloss") or "").strip())
                     for t in _TERM_RE.finditer(m.group(0))]
            if len(terms) < 2:
                continue
            base, bgloss = terms[0]
            rest = terms[1:]
            members = [(f, g) for f, g in rest if not f.startswith("-")]
            suffixes = [(f, g) for f, g in rest if f.startswith("-")]
            if not suffixes and not members:
                continue
            # A construction has to build *this* word: if its first piece does
            # not stand where the word begins, the entry is describing something
            # else (2026-11-08: "the constructions should obviously
            # recreate the actual word"). Ablaut changes a vowel, a laryngeal or
            # an s-mobile may be written differently, and a metathesis may swap
            # two letters — those pass; a missing first element does not.
            if not _construction_covers([base] + [f for f, _ in rest], word=entry_word,
                                        sentence=sentence):
                continue
            out.append({
                "base": _base_row(lang, base, bgloss),
                "members": [_base_row(lang, f, g) for f, g in members],
                "suffixes": _morpheme_rows(lang, suffixes, word=entry_word, pos=pos),
                "etym": sentence.strip(),
                "kind": "stated",
                "confidence": confidence,
                "source": "the entry",
            })
    return out


def _stem_construction(text: str, lang: str, word: str = "", pos: str = "") -> dict | None:
    """A stem-class derivative the dictionary states in prose.

    Only the form it names is used: the base is the starred word, and the
    suffix is the stem-formative its own stem class implies (*-i-* for an
    i-stem). The etymology below the row keeps the sentence it was read from,
    so the reader can check the reading.
    """
    m = _STEM_CONSTRUCTION_RE.search(text)
    if not m:
        return None
    base = m.group("base").lstrip("*").strip()
    if not base:
        return None
    letter = _stem_letter(m.group("stem"))
    suffixes = _morpheme_rows(
        lang, [(f"-{letter}-", f"{letter}-stem — the stem-formative the record names")],
        hint="stem", word=word, pos=pos)
    # The word stated as "an i-stem noun built on *h₂wl̥p-" is *h₂wl̥p- + *-i-
    # + the nominative *-s; the page has to show all three pieces, or the *s
    # of *h₂wl̥pís looks invented (2026-11-09). The recorded headword is used
    # when the arithmetic lands on it, so the accent stays the dictionary's.
    composed = ""
    if suffixes and suffixes[0].get("ending"):
        arith = detokenize(tokenize(base.rstrip("-") + suffixes[0]["form"].strip("-")
                                    + suffixes[0]["ending"]))
        if word and _same_form(arith, word):
            composed = word
        else:
            composed = arith
    return {
        "base": _base_row(lang, base),
        "members": [],
        "suffixes": suffixes,
        "composed": composed,
        "etym": text,
        "kind": "stem",
        "confidence": "argued" if _HEDGE_RE.search(text[:m.start()]) else "stated",
        "source": "the entry",
    }


def _from_stem_construction(entry: dict, text: str, lang: str) -> dict | None:
    """A word the dictionary cuts straight from a named stem.

    dl̥h₁gʰós is "From the stem *delh₁gʰ- (“to be long”)": the base is stated,
    the formation is the headword's own ending. So the row prints the stem the
    entry names plus the letters the word carries after it, and nothing else —
    the sentence it was read from stays on the row for the reader to check.
    The base must be an ancestor the entry itself lists, otherwise a sentence
    about some other form's stem would be read as this word's construction
    (2026-11-08: show dl̥h₁gʰós as a construction).
    """
    m = _FROM_STEM_RE.search(text)
    if not m:
        return None
    word = entry.get("word") or ""
    base = m.group("base").strip("*.,;:")
    if not base.endswith("-"):
        base += "-"
    named = {str(row[1]).split(":", 1)[-1].lstrip("*") for row in (entry.get("anc") or [])
             if len(row) > 1}
    if base not in named and base.rstrip("-") not in {n.rstrip("-") for n in named}:
        return None
    core = base.rstrip("-")
    tail = ""
    for k in range(len(core), 0, -1):
        cut = word.find(core[-k:])
        if cut >= 0:
            tail = word[cut + k:]
            break
    if tail not in _TAIL_ENDINGS:
        return None
    quote, read = _derivation_quote(text, m.start(), m.group("base"))
    gloss = _MORPHEME_GLOSS_RE.match(text, m.end())
    return {
        "base": _base_row(lang, base, (gloss.group(1) if gloss else read) or ""),
        "members": [],
        # The tail is the ending the headword wears, so it is read the way any
        # other piece is: the stage's endings table names it (‑ós is the
        # thematic nominative singular), and its suffix entry is quoted beside
        # that. It used to say "the ending this form carries" and nothing more
        # (2026-11-08: the ‑ós must explain itself).
        "suffixes": _morpheme_rows(lang, [(f"-{tail}", "")], word=word,
                                   pos=str(entry.get("pos") or "")),
        "etym": quote,
        "kind": "stem",
        "confidence": "stated",
        "source": "the entry",
    }


def _ending_stem(word: str) -> str:
    """The stem-formative a headword's own ending carries (h₂ŕ̥tḱos → ``o``)."""
    low = (word or "").lower()
    for end, letter in _ENDING_STEM:
        if low.endswith(end) and len(low) > len(end):
            return letter
    return ""


@lru_cache(maxsize=None)
def _root_headwords(lang: str = ROOT_LANG) -> frozenset[str]:
    """The stage's roots — the only bases a bare "from *X" may name.

    A root is a headword written with a trailing hyphen (*mer-), so a full word
    (*h₂éwsōs) is never read as the base of a formation the entry does not
    spell out.
    """
    return frozenset(form for form in lang_index(lang) if form.endswith("-"))


def _root_constructions(text: str, word: str, lang: str, pos: str = "") -> list[dict]:
    """Hedged derivations that name only the root — "perhaps from a root *mer-".

    The entry says the word is built on a root and names no suffix, so the row
    prints that root; a word the entry calls a nominalization also prints the
    stem-formative its own ending carries (*h₂ŕ̥tḱos → *h₂retḱ- + *-o-*). Every
    row is ``argued``: a hedged sentence is the entry offering an analysis, not
    stating one, and the etymology below keeps the words it was read from
    (2026-11-08: a possible construction should be shown as one).
    """
    roots = _root_headwords(lang)
    hits: list[tuple[int, str, str]] = []
    for m in _ROOT_CONSTRUCTION_RE.finditer(text):
        hits.append((m.start(), m.group("base"), m.group("how") or ""))
    for m in _ROOT_FROM_RE.finditer(text):
        base = m.group("base").strip(".,;:")
        if base not in roots:
            continue
        hits.append((m.start(), base, m.group("how") or ""))
    out: list[dict] = []
    seen: set[str] = set()
    for pos, base, how in sorted(hits):
        base = base.strip(".,;:").lstrip("*")
        if not base or base == word or base in seen:
            continue
        before = text[:pos]
        if _RELATED_FORM_RE.search(before) or _CHAIN_BOUNDARY_RE.search(before):
            continue
        # "the synonym *káp-ōl, which likewise may be from *kap-": a match in a
        # sentence that introduces another headword with it belongs to that
        # word, not to this one.
        if _OTHER_WORD_RE.search(text[_clause_start(text, pos):pos]):
            continue
        # The entry names this base with a suffix — "*wers- ("to rise") + *-ḗn".
        # That is an arithmetic, and the arithmetic reader prints it; a bare
        # row here would hide the suffix the entry states.
        tail = text[pos + len(base):]
        tail = tail.split("*", 1)[0]
        if re.search(r"\+\s*$", tail) or re.search(r"\+\s*[\w\ufb00-\ufb06]*\s*$", tail):
            continue
        seen.add(base)
        suffixes: list[dict] = []
        if how.lower().startswith("nominali"):
            letter = _ending_stem(word)
            if letter:
                suffixes = _morpheme_rows(
                    lang, [(f"-{letter}-",
                            f"{letter}-stem — the stem-formative this form carries")],
                    hint="stem", word=word, pos=pos)
        quote, gloss = _derivation_quote(text, pos, base)
        if not suffixes:
            grown = _ENLARGED_RE.search(quote, quote.find(base) + len(base))
            if grown:
                suffixes = _morpheme_rows(
                    lang, [(grown.group(1).strip(".,;:") or "",
                            "the suffix the entry names")], word=word, pos=pos)
        out.append({
            "base": _base_row(lang, base, gloss),
            "members": [],
            "suffixes": suffixes,
            "etym": quote,
            "kind": "root",
            "confidence": "argued",
            "source": "the entry",
        })
    return out


def _clause_start(text: str, pos: int) -> int:
    """Where the sentence holding ``pos`` begins, counting parentheses."""
    start = depth = 0
    for i, ch in enumerate(text[:pos]):
        depth += (ch == "(") - (ch == ")")
        if ch in ".;" and depth <= 0:
            start = i + 1
    return start


def _derivation_quote(text: str, pos: int, base: str) -> tuple[str, str]:
    """The clause a root derivation was read from, and the base's own gloss.

    The clause runs from the last sentence boundary before the match to the
    first after it, counting parentheses so a gloss's own ";" or "." does not
    end it; a tail that speaks of something else ("(see also …)", ", whence …")
    is dropped, because the row must show what the entry says about *this*
    word (2026-11-08).
    """
    start = _clause_start(text, pos)
    end, depth = len(text), 0
    for i in range(pos, len(text)):
        ch = text[i]
        depth += (ch == "(") - (ch == ")")
        if ch in ".;" and depth <= 0:
            end = i + 1
            break
    quote = text[start:end].strip()
    after = quote.find(base) + len(base)
    gloss = _MORPHEME_GLOSS_RE.match(quote, after)
    for cut in (" (see also", ", whence", " whence", ", compare", " (compare"):
        tail = quote.find(cut, after)
        if tail != -1:
            quote = quote[:tail].rstrip(" ,;")
    if len(quote) > 180:
        quote = quote[:quote.rfind(" ", 0, 180)].rstrip(" ,;") + "…"
    return quote, (gloss.group(1).strip() if gloss else "")


@lru_cache(maxsize=None)
def _stored_constructions(lang: str) -> dict[str, list[dict]]:
    """Analyses an entry argues in prose, recorded by hand (data/constructions/).

    A later sentence that names a rival base without an arithmetic — "Kloekhorst
    argues … the root *dʰeǵ- as opposed to *dʰeǵʰ-" — cannot be read the way
    *base + *suffix* can, so the reading is stored with its quote, author and
    confidence instead of being guessed at (2026-11-08).
    """
    path = data.DATA / "constructions" / f"{lang}.yaml"
    if not path.exists():
        return {}
    raw = data._load_yaml(path) or {}
    return {str(word): rows or [] for word, rows in raw.items()}


@lru_cache(maxsize=16)
def _construction_scan(lang: str) -> tuple:
    """One pass over a stage: the words built on each base, and each suffix.

    Both indexes are answers to the same question read from two ends — "what is
    this word built from" and "where is this morpheme recorded" — so they are
    built together and cached together. Reading the corpus twice would double
    the cost of the first page of a language for no gain (2026-11-08).
    """
    def build() -> tuple:
        return _scan_constructions(lang)

    # One pass over a whole glossary, so it is kept on disk between runs like
    # the parsed glossary itself (2026-11-12).  The version rises when the row
    # gains a field the index must recompute (2: the root's grade).
    return data.cached(f"constructions-{lang}", 2,
                       [data.LEXICON_DIR / f"{lang}.jsonl.gz",
                        data.LEXICON_DIR / f"{lang}.jsonl",
                        data.DATA / "constructions" / f"{lang}.yaml"], build)


def _scan_constructions(lang: str) -> tuple:
    by_base: dict[str, list[dict]] = {}
    by_piece: dict[str, dict] = {}
    seen: dict[str, set[tuple]] = {}
    for entry in data.lexicon(lang):
        for row in _raw_constructions(entry, lang):
            base = row["base"]["form"]
            suffixes = [s["form"] for s in row["suffixes"]]
            key = (entry["word"], tuple(suffixes))
            if key not in seen.setdefault(base, set()):
                seen[base].add(key)
                grade = root_grade(base, entry["word"], suffixes)
                by_base.setdefault(base, []).append({
                    "word": entry["word"],
                    "pos": entry.get("pos", ""),
                    "gloss": _rung_gloss(entry.get("gloss") or [], 80),
                    "suffixes": suffixes,
                    "confidence": row.get("confidence") or "stated",
                    "grade": grade or None,
                })
            for piece in row["suffixes"]:
                rec = by_piece.setdefault(piece["form"], {
                    "words": [], "glosses": Counter(), "bases": [], "seen": set()})
                stated = (piece.get("stated") or "").strip()
                if stated:
                    rec["glosses"][stated] += 1
                word_key = (entry["word"], base)
                if word_key in rec["seen"]:
                    continue
                rec["seen"].add(word_key)
                rec["words"].append({"word": entry["word"], "base": base,
                                     "pos": entry.get("pos", "")})
                if base not in rec["bases"]:
                    rec["bases"].append(base)
    return by_base, by_piece


def _construction_index(lang: str) -> dict[str, list[dict]]:
    """The words of one stage whose construction names a given base.

    A root is an entry like any other, and its page must show what is built on
    it: the reverse of the construction the word pages print. Nothing here is
    new data — the rows are the same analyses, read from the other end
    (2026-11-08: the roots in a construction should be entries).
    """
    return _construction_scan(lang)[0]


def _resolve_stored(row: dict, lang: str) -> dict:
    """Turn one stored analysis into the same shape the prose reader returns."""
    base = str(row.get("base") or "").lstrip("*").strip()
    suffixes = row.get("suffixes") or []
    tokens = []
    for item in suffixes:
        if isinstance(item, dict):
            tokens.append((str(item.get("form") or ""), str(item.get("gloss") or "")))
        else:
            tokens.append((str(item), ""))
    return {
        "base": _base_row(lang, base),
        "members": [],
        "suffixes": _morpheme_rows(lang, tokens),
        "etym": str(row.get("note") or "").strip(),
        "kind": "stored",
        "confidence": str(row.get("confidence") or "argued"),
        "source": str(row.get("source") or ""),
    }


# ------------------------------------------------------- building at a stage
#: The three ways a reader may build a form at a stage: join two recorded words
#: of that stage, add one of its cited suffixes, or swap one of its endings.
BUILD_KINDS = ("join", "suffix", "ending")


def _parse_build(spec: str) -> dict | None:
    """``stage:kind:argument`` as the address bar carries it.

    A join names the second word; a suffix names the affix's id (or form); an
    ending names the ending itself.  A leading ``base@`` names a different base
    than the rung's own form — the first piece of a compound that is a word of
    the stage in its own right, not the form above it.
    """
    if not spec or spec.count(":") < 2:
        return None
    stage, kind, arg = (part.strip() for part in spec.split(":", 2))
    if kind not in BUILD_KINDS or not stage or not arg:
        return None
    if stage not in data.languages():
        return None
    base = ""
    if "@" in arg:
        arg, base = (part.strip() for part in arg.rsplit("@", 1))
        if not arg:
            return None
    return {"stage": stage, "kind": kind, "arg": arg, "base": base}


@lru_cache(maxsize=None)
def _affix_entries(lang: str) -> tuple[dict, ...]:
    """Every affix a stage's own glossary heads with a leading hyphen.

    A word written ``-nás`` is a morpheme in that dictionary, not a word of the
    language, and it is exactly the set a reader may attach to a stem.  Reading
    it from the glossary means the picker offers the affixes *this* record has,
    with the gloss the record gives them, instead of a hand-written list.
    """
    out: list[dict] = []
    for word, rows in lang_index(lang).items():
        if len(word) < 2 or not word.startswith("-"):
            continue
        row = rows[0]
        out.append({
            "id": word, "form": word, "attach": "keep", "ending": "",
            "gloss": _rung_gloss(row.get("gloss") or [], 80),
            "pos": str(row.get("pos") or ""), "from_lexicon": True,
        })
    return tuple(out)


def _affix_rows(lang: str) -> list[dict]:
    """The stage's affixes: the hand-written registry first, then the lexicon's."""
    out: list[dict] = []
    seen: set[str] = set()
    for row in (morphology(lang) or {}).get("suffixes") or []:
        key = normalise_etymon(str(row.get("form") or "")) or row.get("id", "")
        if key in seen:
            continue
        seen.add(key)
        out.append({**row, "from_lexicon": False})
    for row in _affix_entries(lang):
        key = normalise_etymon(str(row.get("form") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_options(lang: str) -> dict:
    """What one rung may be built with, small enough to send with the ladder."""
    suffixes = [
        {"id": row["id"], "form": row.get("form", ""),
         "gloss": row.get("gloss", ""), "law": bool(row.get("rule")),
         # A grammatical ending in the same drawer is not a derivational
         # suffix: the endings have their own row (admin, 2026-11-12).
         "kind": row.get("kind", "suffix")}
        for row in _affix_rows(lang)
    ]
    endings = [
        {"id": row.get("form", ""), "form": row.get("form", ""),
         "gloss": row.get("name", ""), "law": False}
        for row in ((morphology(lang) or {}).get("endings") or [])
    ]
    joining = (morphology(lang) or {}).get("joining") or {}
    return {
        "stage": lang, "stage_name": _lang(lang).get("name", lang),
        "suffixes": suffixes[:60], "endings": endings[:24],
        "joining": {"linker": str(joining.get("linker") or ""),
                    "zwnj": bool(joining.get("zwnj")),
                    "note": str(joining.get("note") or "")},
        "join": True,
    }


def _piece_row(stage: str, form: str) -> dict:
    """One piece of a formation, with whatever the stage's glossary says of it."""
    entry = _lemma_entry(stage, form)
    return {
        "form": form, "word": (entry or {}).get("word", form), "lang": stage,
        "lang_name": _lang(stage).get("name", stage),
        "gloss": _rung_gloss((entry or {}).get("gloss") or [], 70),
        "pos": str((entry or {}).get("pos") or ""),
        "known": bool(entry),
    }


def _compose_build(spec: dict, base: str, stage: str,
                   script_ok: bool = False) -> dict | None:
    """The form a stage gives when its words are joined or a morpheme is added.

    Nothing here is a sound law and nothing here is checked against the target:
    the composed form is then run through the same chain as any other form, and
    whether it lands on the recorded word is the ordinary verdict below.  The
    steps are kept so the page can print the arithmetic.
    """
    base = normalise_etymon(base) or base
    kind, arg = spec["kind"], spec["arg"]
    if not base:
        return None
    if script_ok and (kind != "join" or not is_rtl(base)):
        # The rung may print a transliteration (dast) while the word itself is
        # written in its own script (دست).  A formation at the stage the word
        # belongs to is a written word, so its pieces are written too
        # (2026-11-10).
        written = spelling.spell(base, stage)
        if written and written != base:
            base = written
    if kind != "join":
        arg = arg.lstrip("-") if kind != "join" else arg
    if kind == "join":
        right = normalise_etymon(arg) or arg
        if not right or right == base:
            return None
        info = (morphology(stage) or {}).get("joining") or {}
        linker = str(info.get("linker") or "")
        form = base + linker + right
        if info.get("zwnj") and is_rtl(base) and is_rtl(right):
            form = base + "\u200c" + right
            linker = "\u200c"
        return {
            "form": form, "kind": "compound",
            "pieces": [_piece_row(stage, base), _piece_row(stage, right)],
            "steps": [{"label": "first word", "form": base},
                      {"label": "second word", "form": right},
                      {"label": "joined", "form": form}],
            "linker": linker,
            "note": (info.get("note") or
                     "Two words of one stage joined; the join adds no sound and "
                     "is not a sound law."),
        }
    if kind == "suffix":
        row = next((r for r in _affix_rows(stage)
                    if r["id"] == arg or r.get("form") == arg
                    or str(r.get("form") or "").strip("-") == arg.strip("-")), None)
        if not row:
            return None
        # One composition, one implementation: `compose` is the hand-written
        # morphology (a final nominative ending or thematic vowel may have to
        # drop, and the suffix brings its own ending), and the formation's law
        # when the suffix registers one.  A second suffix on the first result
        # must behave exactly like the first (2026-11-12).
        made = compose(base, row["id"], stage)
        form = str(made.get("form") or "")
        if not form or form == base:
            return None
        grade = made.get("grade")
        piece = _piece_row(stage, base)
        if grade:
            piece = {**piece, "grade": grade["grade"], "grade_label": grade["label"],
                     "grade_note": grade["note"]}
        return {"form": form, "kind": "suffix",
                "pieces": [piece,
                           {"form": row.get("form", ""), "word": row["id"],
                            "lang": stage, "lang_name": _lang(stage).get("name", stage),
                            "gloss": row.get("gloss", ""), "pos": "suffix",
                            "known": True, "affix": True}],
                "steps": made.get("steps") or [],
                "law": made.get("law"),
                "grade": grade,
                "note": ("The suffix is the registered formation law; the law "
                         "adds a morpheme, which no sound change may do."
                         if made.get("law") else
                         "A suffix is added to the word's stem; no sound change "
                         "and no register of sound laws produces it.")}
    if kind == "ending":
        rows = ((morphology(stage) or {}).get("endings") or [])
        endings = [str(r.get("form") or "").lstrip("-") for r in rows]
        arg = arg.lstrip("-")
        if arg not in endings:
            return None
        stem = base
        dropped = ""
        for end in sorted((e for e in endings if e), key=len, reverse=True):
            if stem.endswith(end) and len(stem) > len(end) + 1:
                stem, dropped = stem[: -len(end)], end
                break
        form = stem + arg
        return {"form": form, "kind": "inflection",
                "pieces": [_piece_row(stage, base),
                           {"form": arg, "word": arg, "lang": stage,
                            "lang_name": _lang(stage).get("name", stage),
                            "gloss": next((r.get("name", "") for r in rows
                               if str(r.get("form") or "").lstrip("-") == arg), ""),
                            "pos": "ending", "known": True, "affix": True}],
                "steps": [{"label": "word", "form": base},
                          {"label": "ending dropped", "form": dropped or "—",
                           "note": "" if dropped else "the word shows no ending to drop"},
                          {"label": "ending added", "form": arg},
                          {"label": "inflected", "form": form}],
                "note": "An inflection, not a derivation: the same word in "
                        "another paradigm cell."}
    return None


def build_at(spec: str, base: str = "") -> dict | None:
    """One construction step, composed on its own (no ladder below it).

    The construction row a reader opens from a rung asks the stage this
    question one piece at a time, so it needs the step alone: what the pieces
    are, what grade the stem stands in, and the form they make.  Nothing here
    is a law, and nothing is stored.
    """
    parsed = _parse_build(spec)
    if not parsed:
        return None
    if base:
        parsed["base"] = base
    composed = _compose_build(parsed, parsed.get("base") or "", parsed["stage"])
    if not composed:
        return None
    out = {**parsed, **composed}
    out["stage_name"] = _lang(parsed["stage"]).get("name", parsed["stage"])
    return out


def headwords(lang: str, limit: int = 4000) -> list[dict]:
    """The words of one stage, for a menu that joins one word to another.

    A bound morpheme (a headword written with a leading hyphen) is not a word
    and belongs to the suffix menu, so it is left out here.
    """
    out: list[dict] = []
    for word, rows in sorted(lang_index(lang).items()):
        if not word or word.startswith("-") or " " in word:
            continue
        # One row per word, described by its meaning: a headword the record
        # keeps under two readings (a participle and the adjective it became)
        # would otherwise enter the menu as "past participle of *aiganą" and
        # never say what the word means (2026-11-12).
        group = (senses.groups(rows) or [{}])[0]
        gloss = group.get("gloss") or (rows[0].get("gloss") if rows else []) or []
        out.append({"word": word, "gloss": _rung_gloss(gloss, 70)})
        if len(out) >= limit:
            break
    return out


def compose(form: str, suffix_id: str | None, lang: str = ROOT_LANG) -> dict:
    """Attach one cited suffix to a word's stem and say exactly what was done.

    The result is a *formation*: stem + suffix + the suffix's own nominative
    ending. It is this repo's hypothesis (no dictionary records the composed
    word), and the payload carries the step list so the page can print the
    arithmetic instead of presenting a new etymon as a record.
    """
    etymon = normalise_etymon(form)
    suffixes = (morphology(lang) or {}).get("suffixes") or []
    suffix = next((s for s in suffixes if s["id"] == suffix_id), None)
    if not etymon or suffix is None:
        return {"form": etymon, "suffix": None, "steps": []}
    # A cited formation law wins over hand composition: it is the same rule the
    # word's own ladder runs, so the PIE page and the Persian page cannot say
    # two different things about the same suffix.
    ref = suffix.get("rule") or ""
    unapplied = None
    if ref:
        law = next((r for (src, dst), rs in data.rulesets().items()
                    for r in rs.rules if rule_key(rs, r.id) == ref), None)
        if law is not None:
            new, changed = law.apply(tokenize(etymon))
            if changed:
                composed = detokenize(new)
                return {
                    "form": composed, "stem": etymon, "theme": "", "dropped": "",
                    "suffix": suffix,
                    "law": {"key": ref, "id": law.id, "name": law.name,
                            "tier": law.tier, "before": etymon, "after": composed},
                    "steps": [
                        {"label": "word", "form": etymon},
                        {"label": "suffix", "form": suffix["form"], "note": suffix["gloss"]},
                        {"label": "composed", "form": composed},
                    ],
                }
            if law is not None:
                # The law exists but this stem is not the kind it applies to;
                # the form below is composed by hand and the page says so.
                unapplied = ref
    word = detokenize(tokenize(etymon))
    dropped = ""
    # Only a *word* wears a nominative ending to drop: a root is a bound
    # morpheme, and *ters- is not *ter- + *-s.  Dropping the root's own final
    # consonant turned *ters- + *-eh₂ into *treh₂ (2026-11-12).
    for ending in (() if _is_root_etymon(lang, form) else _NOM_ENDINGS):
        bare_ending = detokenize(tokenize(ending))
        if word.endswith(bare_ending) and len(word) - len(bare_ending) >= 2:
            dropped = bare_ending
            word = word[: -len(bare_ending)]
            break
    stem = word
    theme = ""
    if suffix["attach"] == "drop":
        for vowel in ("eh₂", "ih₂", "o", "e", "ā", "i", "u"):
            bare_vowel = detokenize(tokenize(vowel))
            if stem.endswith(bare_vowel) and len(stem) - len(bare_vowel) >= 2:
                theme = bare_vowel
                stem = stem[: -len(bare_vowel)]
                break
    attach = suffix["form"].strip("-")
    steps = [{"label": "word", "form": etymon}]
    steps.append({"label": "nominative ending", "form": f"-{dropped}" if dropped else "—",
                  "note": "dropped to reach the stem" if dropped else "the word shows no ending to drop"})
    steps.append({"label": "stem", "form": stem + theme if theme or dropped else stem})
    if theme:
        steps.append({"label": "thematic vowel", "form": f"-{theme}", "note": "dropped before the suffix"})
    # The formation decides the root's grade before the suffix is added: *-nó-
    # is oxytone, so *ters- stands in zero grade and the composed word is
    # *tr̥s-nó-s, never *ters-nó-s (2026-11-12).
    stem, grade = _formation_grade(stem, suffix["form"], lang)
    if grade:
        steps.append({"label": grade["label"], "form": stem, "note": grade["note"]})
    composed = detokenize(tokenize(stem + attach + suffix["ending"]))
    steps += [
        {"label": "suffix", "form": suffix["form"], "note": suffix["gloss"]},
        {"label": "ending", "form": suffix["ending"] or "—"},
        {"label": "composed", "form": composed},
    ]
    return {"form": composed, "stem": stem, "theme": theme, "dropped": dropped,
            "suffix": suffix, "law": None, "law_not_applied": unapplied,
            "grade": grade, "steps": steps}


def _record_for_output(lang: str, form: str) -> dict | None:
    """The first recorded word in *lang* whose reading is ``form``.

    Used when a composed formation arrives somewhere a rebuild row does not
    describe: the laws produced *gorbe*, and Persian records گربه read *gorbe*.
    The record is quoted with its own script, exactly like a ladder rung.
    """
    record = _stage_record(lang, form)
    if not record:
        return None
    return {**record, "r": "", "known": True}


def _record_sources(lang: str, word: str, fallback: dict | None = None) -> list[dict]:
    """Resolve the citation for a recorded form, never leaving green bare."""
    entry = _lemma_entry(lang, word)
    if entry:
        return _entry_sources(entry)
    if fallback:
        return _entry_sources(fallback)
    known = data.sources().get("wiktionary") or {}
    found = wiktionary_pages.en_page(lang, word)
    return [{"id": "wiktionary", "title": known.get("title", "Wiktionary"),
             "url": known.get("url", ""), "kind": known.get("kind", ""), "ref": "",
             "entry": found["url"] if found else ""}]


def _stage_record(lang: str, form: str) -> dict | None:
    """A stage's own record of exactly this form, if its glossary has one.

    The ladder may quote a record through a native script's reading (Pahlavi
    𐫅𐫏𐫇 is read *dēw*); that is a match of the reading, and the block says
    so. No look-alike is accepted here: a stage that records a different form
    is handled by the caller as a difference, never as a match.
    """
    plain = normalise_etymon(form)
    if not plain:
        return None
    entry = _headword_at(lang, plain)
    via = "glossary"
    if not entry and needs_reading(lang):
        found = _reading_index(lang).get(_plain_form(detokenize(tokenize(plain))))
        rows = word_index().get((lang, found[0])) if found else None
        entry = rows[0] if rows else None
        via = "reading"
    if not entry:
        return None
    word = entry["word"]
    pron = readings_for(entry)
    return _with_reading({
        "w": word,
        "r": "",
        "evidence": _entry_evidence(lang, entry),
        "recon": bool(entry.get("recon")),
        "ipa": pron["ipa"],
        "reading": pron["reading"],
        "show_reading": show_reading(lang, word),
        "known": True,
        "via": via,
        "exact": True,
        "script": _lang(lang).get("script", ""),
        "in_script": _in_native_script(lang, word),
        "sources": _entry_sources(entry),
    }, lang, word)


def _candidate_record(lang: str, candidates: list[dict] | None) -> dict | None:
    """The first form this etymon's own record has at a stage, match or not.

    A rung may produce something the stage's glossary does not spell, while
    the etymon's recorded descendants include that stage's word. Showing it
    beside the produced form — with its script, reading and citation — is the
    same rule the word ladder follows, and it keeps an OP rung from hiding
    𐎭𐎡𐎺 behind a bare Latin guess (2026-11-08).
    """
    if not candidates:
        return None
    row = candidates[0]
    word = row.get("w") or ""
    if not word:
        return None
    entry = _lemma_entry(lang, word)
    pron = pronunciation(lang, word, row.get("r") or "")
    return _with_reading({
        "w": word,
        "r": row.get("r") or "",
        "evidence": row.get("evidence") or evidence_for(word, lang),
        "ipa": row.get("ipa") or pron["ipa"],
        "reading": row.get("reading") or pron["reading"],
        "show_reading": row.get("show_reading", show_reading(lang, word)),
        "known": bool(entry),
        "via": "cognate",
        "exact": False,
        "script": _lang(lang).get("script", ""),
        "in_script": _in_native_script(lang, word),
        "recon": is_reconstructed(lang, word),
        "sources": _entry_sources(entry) if entry else _record_sources(lang, word),
    }, lang, word)


def reconstruct(form: str, lang: str, suffix: str | None = None,
                disabled: Iterable[str] = (),
                from_stage: str | None = None,
                from_form: str | None = None) -> dict | None:
    """One PIE etymon reconstructed into one language, law by law.

    This is what a word *in* Proto-Indo-European gets instead of a ladder: the
    root has no ancestry to climb, so the question becomes where the word goes.
    Every form here is what the registered laws produce and nothing else; a form
    a cognate set records is quoted beside it, never substituted for it.

    A reader may switch any law off, exactly as on a word's own ladder: the
    chain is re-derived without it and the rung lists it as switched off, with
    what it would have done (2026-11-08: the laws on the etymon page
    could not be toggled).

    ``from_stage``/``from_form`` rewrite one rung where it stands (2026-11-08: "reconstructions should still be editable at any point"). The
    rungs above keep exactly what the laws produced for them; the typed form
    replaces that stage's form, and every law below it runs on the typed form
    instead. The timeline is never shortened by an edit, and the edit is marked
    as a hypothesis, not a record.
    """
    etymon = normalise_etymon(form)
    chain = data.derivation_chain(lang)
    if not etymon or not chain or chain[0] != ROOT_LANG or lang == ROOT_LANG:
        return None
    # An edit wins over a suffix hypothesis: the reader has replaced one rung,
    # so the composed start a suffix would give no longer describes the path.
    edited: dict | None = None
    start = 0
    if from_stage and (from_form or "").strip():
        if from_stage not in chain:
            return None
        start = chain.index(from_stage)
        edited = {"stage": from_stage, "form": from_form.strip(),
                  "name": _lang(from_stage).get("name", from_stage)}
    morph = None if edited else (compose(etymon, suffix) if suffix else None)
    if morph and morph.get("form"):
        etymon = morph["form"]
    # The form each part of the timeline starts from: the rungs above the edit
    # from the etymon (or the composed word), the rungs below from the typed
    # form. The rungs above the edit stay the laws' own work.
    root_form = etymon
    run_form = (edited or {}).get("form") or root_form
    rulesets = data.rulesets()
    switched_off = set(disabled)
    derivation, tail_levels = derive_detailed(run_form, chain[start:], rulesets,
                                              disabled=switched_off)
    levels = tail_levels
    all_steps = list(derivation.steps)
    all_skipped = list(derivation.skipped)
    if start:
        head, head_levels = derive_detailed(root_form, chain[:start], rulesets,
                                            disabled=switched_off)
        # The edited stage is a rung of its own: the typed form replaced what
        # the laws had there, so it carries no applied law of its own.
        levels = head_levels + [Level(chain[start - 1], chain[start], run_form)] + tail_levels
        all_steps = list(head.steps) + all_steps
        all_skipped = list(head.skipped) + all_skipped
    rebuilt = rebuilds_for_etymon(etymon) or {}
    row = next((r for r in rebuilt.get("rows", []) if r["l"] == lang), None)
    recorded_by_lang: dict[str, list[dict]] = {}
    set_id = cognate_set_for(etymon)
    if set_id:
        payload = _cognate_payload(set_id)
        if payload:
            recorded_by_lang = _recorded_forms(payload.get("forms") or [])
    record = _lemma_entry(ROOT_LANG, etymon) or {}
    block = (row or {}).get("recorded")
    if not block and morph and morph.get("law"):
        # A composed formation reaches a word whose dictionaries record it
        # under a formation the rebuild list does not know: the animal suffix
        # *-ka- produces *h₂wl̥paka > … > gorbe, and a *gorbe* needs a dictionary
        # to be quoted. The laws' output is therefore looked up against the
        # recorded readings of the target language — the same comparison the
        # ladder uses — and a hit is quoted, never substituted (2026-11-08).
        # Only for a registered formation: a hand-composed hypothesis is not
        # searched for a look-alike, which would cost seconds and claim a
        # warrant it does not have.
        block = _record_for_output(lang, derivation.output)
    if block:
        lemma = _lemma_entry(lang, block.get("w") or "") or {}
        block = {
            **block,
            "pos": lemma.get("pos", ""),
            "gloss": _rung_gloss(lemma.get("gloss") or []),
            # Green and gold are claims about a word, so the rung carries the
            # citation and, for Old Persian, whether the record is a cuneiform
            # headword or only a transliteration (2026-11-08).
            "sources": block.get("sources") or _record_sources(lang, block.get("w") or "", record),
            "script": block.get("script") or _lang(lang).get("script", ""),
            "in_script": block.get("in_script", _in_native_script(lang, block.get("w") or "")),
            "known": block.get("known", bool(lemma)),
        }
    tiers = sorted({s.tier for s in all_steps},
                   key=lambda t: TIERS.index(t) if t in TIERS else 9)
    if row:
        status, evidence = row.get("status", "new"), row.get("evidence", "weak")
    else:
        status = "new"
        evidence = "strong" if all_steps and set(tiers) <= {"established"} else "weak"
    # The laws' own result decides the verdict when the target language records
    # the word: by its headword, its romanisation (a composed *-ka- formation
    # reaches گربه read *gorbe*), or as a reading of its script (Old Persian
    # 𐎺𐎼𐎣 is *va-ra-ka*, and the laws give *wˈarkah*). 2026-11-08.
    final_here = _record_for_form(lang, derivation.output) or block
    block = final_here or block
    if final_here:
        hit = [final_here.get("w") or "", final_here.get("reading") or "",
               *(final_here.get("readings") or [])]
        if (final_here.get("fit") or {}).get("ok") or any(
                h and _same_form(derivation.output, h) for h in hit):
            status, evidence = "match", final_here.get("evidence") or "attested"
    same = bool(block) and bool(normalise_etymon(derivation.output)) and any(
        h and _same_form(normalise_etymon(derivation.output), normalise_etymon(h))
        for h in (block.get("w") or "", block.get("reading") or ""))
    # The target word's own ancestry is the best record of the stages on the
    # way here: Wiktionary may name Old Persian 𐎲𐎠𐏀𐎢 for Persian بازو even
    # when the cognate set stops at Persian (2026-11-08). Those
    # records are quoted beside the laws' forms, never substituted for them.
    target_entry = _lemma_entry(lang, (block or {}).get("w") or "") if block else None
    ancestry_records = _recorded_at(target_entry, lang) if target_entry else {}
    steps = []
    tiers_fired: list[str] = []
    laws_fired = 0
    for level in levels:
        fired = [r for r in level.rules if r.get("fired")]
        off = [r for r in level.rules if r.get("disabled") and not r.get("fired")]
        tiers_fired.extend(r.get("tier") or "" for r in fired)
        laws_fired += len(fired)
        dst_row = _lang(level.dst)
        era = dst_row.get("era")
        # Each rung quotes its own stage's record when the glossary has this
        # exact form. A rung with no record is this repo's reconstruction and
        # must never borrow the target language's green because that language
        # happens to be attested (2026-11-08: warpíš was green).
        here = block if level.dst == lang and block else _record_block(
            level.dst, ancestry_records.get(level.dst), level.form,
            target_entry or record)
        if not here:
            here = _candidate_record(level.dst, recorded_by_lang.get(level.dst))
        if here and not here.get("notation") and not here.get("fit"):
            # Two letters for one sign (OP 𐎺 read v, laws write *w) are a
            # transcription difference, not a match and not a mystery.
            notation = _notation_only(level.form, here.get("reading") or here.get("w") or "")
            if notation:
                here = {**here, "notation": notation}
        matches = bool(here) and (bool((here.get("fit") or {}).get("ok"))
                                  or bool(here.get("exact", level.dst != lang))) and (
            level.dst != lang or status == "match")
        if matches:
            evidence_here = here.get("evidence") or evidence_for(here.get("w", ""), level.dst)
            state_here = "match"
        else:
            evidence_here = ("weak" if here else
                             "strong" if laws_fired and
                             all(t == "established" for t in set(tiers_fired))
                             else "weak")
            state_here = "differs" if here else "derived"
        steps.append({
            "src": level.src,
            "dst": level.dst,
            "src_name": _lang(level.src).get("name", level.src),
            "dst_name": dst_row.get("name", level.dst),
            "kind": kind_of(level.dst),
            "era": era,
            "era_label": era_label(era),
            "era_mid": era_midpoint(era),
            "form": level.form,
            "form_known": bool(_headword_at(level.dst, level.form)),
            "status": state_here,
            "evidence": evidence_here,
            "recorded": here,
            "same": bool(matches and here and _same_form(
                normalise_etymon(level.form), normalise_etymon(here.get("w") or ""))),
            "missing": level.missing,
            # The rung the reader rewrote: a hypothesis, not a record, and the
            # laws below it ran on the typed form (2026-11-08).
            "edited": bool(edited and level.dst == edited["stage"]),
            "registered": len(level.rules),
            "fired": len(fired),
            "switched_off": len(off),
            # A law the reader switched off stays on its rung, with what it
            # would have done, so it can be switched back on (2026-11-08).
            "rules": [{"key": r.get("key"), "id": r.get("id"), "name": r.get("name"),
                       "tier": r.get("tier"),
                       "before": r.get("before"), "after": r.get("after"),
                       "would": r.get("would"),
                       "fired": bool(r.get("fired")), "disabled": bool(r.get("disabled"))}
                      for r in [*fired, *off]],
        })
    return {
        "source": {
            # The form printed on the first rung: the typed one when the reader
            # rewrote the starting stage itself, otherwise the etymon.
            "form": run_form if not start else root_form,
            "name": _lang(chain[0]).get("name", "Proto-Indo-European"),
            "stage": chain[0],
            "kind": kind_of(chain[0]),
            "pos": record.get("pos", ""),
            "gloss": _rung_gloss(record.get("gloss") or []),
            "base": normalise_etymon(form),
        },
        # The rung the reader rewrote, when there is one (stage, typed form,
        # language name), so the page can say the start is a hypothesis.
        "edited": edited,
        "morph": ({"suffix": morph["suffix"], "stem": morph.get("stem", ""),
                   "steps": morph.get("steps", []), "form": etymon,
                   "law": morph.get("law"), "law_not_applied": morph.get("law_not_applied"),
                   "recorded": bool(record.get("word")) and not suffix}
                  if morph else None),
        "lang": lang,
        "lang_name": _lang(lang).get("name", lang),
        "branch": _lang(lang).get("branch", ""),
        "kind": kind_of(lang),
        "script": _lang(lang).get("script", ""),
        "show_reading": bool((row or {}).get("show_reading")),
        "form": derivation.output,
        "form_known": bool(_headword_at(lang, derivation.output)),
        "steps": len(all_steps),
        "tiers": tiers,
        "disabled": sorted(set(disabled)),
        "skipped": all_skipped,
        "status": status,
        "evidence": evidence,
        "recorded": block,
        "same": same,
        "levels": steps,
        # The timeline the reader is on (PIE to the chosen language), and the
        # direct children of that language as buttons that carry it further.
        # This is the same interface a word page has: a reconstruction is a
        # timeline, and a timeline can always go one stage deeper
        # (2026-11-08).
        "path": [{"id": stage, "name": _lang(stage).get("name", stage),
                  "short": _lang(stage).get("short", stage)}
                 for stage in chain],
        "next": [
            _branch_node(lang, derivation.output, child,
                         origin_records={key: {"forms": [r["w"] for r in rows]}
                                         for key, rows in recorded_by_lang.items()},
                         claim=True, depth=len(chain), seen=frozenset(chain),
                         recurse=False)
            for child in data.descendants(lang)
        ],
    }


def _sense_number(sense) -> int | None:
    """The requested sense, or ``None`` when the link names none."""
    try:
        value = int(str(sense).strip())
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _senses_page(lang: str, form: str, groups: list[dict], via: str | None) -> dict:
    """The landing page of a spelling that holds more than one word.

    A reconstruction links to the spelling, not to a meaning; when the record
    holds several words under it the reader has to choose.  Nothing is guessed
    here: every sense is listed with its own part of speech, meaning, band and
    Wiktionary page, and each one opens its own word page (2026-11-09).
    """
    rows = []
    for group in groups:
        entry = group["rep"]
        readings = readings_for(entry)
        rows.append({
            "sense": group["sense"],
            "pos": " / ".join(group["pos"]),
            "gloss": group["gloss"],
            "etym": (entry.get("etym") or "")[:220],
            "band": band_for(lang, entry["word"], group["sense"]),
            "recon": bool(entry.get("recon")),
            "ipa": readings["ipa"],
            "reading": readings["reading"],
            "sources": _entry_sources(entry),
            "entries": len(group["entries"]),
        })
    first = groups[0]["rep"]
    # The spelling's own status, over every entry filed under it: a spelling
    # that a text writes is attested even when one of its senses is only a
    # reconstruction (2026-11-11).
    status = attestation.for_word(
        [row for group in groups for row in group["entries"]],
        proto=kind_of(lang) == "proto",
        in_script=_in_native_script(lang, form),
    )
    return {
        "pick": True,
        "word": form,
        "lang": lang,
        "lang_name": _lang(lang).get("name", lang),
        # The title reads the language's own years beside its name, on the
        # word page and on the list of the words one spelling holds alike
        # (2026-11-11).
        "era_label": era_label(_lang(lang).get("era")),
        "script": _lang(lang).get("script", ""),
        "rtl": is_rtl(form),
        "via": via or "",
        "variants": len(groups),
        "attestation": attestation.payload(
            form, status,
            reason=_attestation_reason(first, lang, status)),
        "senses": rows,
        # The reader has not chosen a sense yet: the page the spelling opens
        # is the one the Persian Wiktionary has for that spelling.
        "wiktionary": _wiktionary_page({"lang": lang, "word": form}),
        "sources": _entry_sources(first),
        "pages": _entry_pages(first),
    }


def word(lang: str, form: str, disabled: Iterable[str] = (),
         from_stage: str | None = None, from_form: str | None = None,
         ghost: bool = False, via: str | None = None,
         pathway: bool = True, suffix: str | None = None,
         path: Iterable[str] | None = None,
         from_recorded: bool = False,
         sense: int | str | None = None,
         build: str | None = None) -> dict | None:
    """One word page: the record, its ladder up, and the branch below it.

    ``via`` names the word page the reader came from (``lang/word``). A rung
    was clicked on that page, so its ancestry rows may record this word's form
    at a stage below — those records are quoted in the descendant tree rather
    than being thrown away because this page's own entry does not repeat them.

    ``sense`` picks one of the words a spelling carries.  A link that names
    none — a reconstruction rung, a cognate row — lands on the page that lists
    them, because the record has more than one answer and the choice is the
    reader's (2026-11-09).
    """
    entries = word_index().get((lang, form))
    if not entries and "\u200c" in form:
        # The seam is spelling: a link that writes آب‌خانه opens the headword
        # the dictionary spells آبخانه (2026-11-10).
        twin = _seam_index(lang).get(form.replace("\u200c", ""))
        entries = word_index().get((lang, twin)) if twin else None
    if not entries:
        entries = word_entries(lang, form)
    if not entries:
        # A link may carry the engine's stress token for a form a dictionary
        # writes with an acute (jrˈayah for headword jráyah) or writes plainly
        # (nˈaht for *naht*). Reading that notation is not a lookup.
        record = _headword_at(lang, detokenize(tokenize(form)))
        if record:
            entries = [record]
    if not entries and needs_reading(lang):
        # The stage writes its words in another script: 𐎭𐎼𐎹 is what the laws
        # call drˈayah, and its own romanisation (drayaʰ) is that form exactly.
        # A form that is a recorded reading opens the recorded word, rather than
        # claiming the stage records nothing (2026-11-08).
        found = _reading_index(lang).get(_plain_form(detokenize(tokenize(form))))
        if found:
            entries = word_index().get((lang, found[0])) or []
    if not entries:
        # A form the laws produced (or a record quoted from Wiktionary's
        # ancestry) may have no glossary entry: `ghost` asks for the page that
        # says so and follows it into the descendant languages instead of a 404.
        return _unrecorded_word(lang, form, via) if ghost else None
    groups = sense_index().get((lang, form)) or senses.groups(entries)
    # Several words can share a spelling (bank the institution, bank the
    # river's edge).  A link that names no sense opens the page that lists
    # them; anything else would be picking a meaning on the reader's behalf.
    sense_no = 1
    if len(groups) > 1:
        want = _sense_number(sense)
        if want is None:
            return _senses_page(lang, form, groups, via)
        picked = next((g for g in groups if g["sense"] == want), None)
        if picked is None:
            return _senses_page(lang, form, groups, via)
        sense_no = want
        entries = picked["entries"]
        entry = picked["rep"]
    else:
        entry = groups[0]["rep"]
    # The page describes one *word*, and the record may keep that word under
    # several headings: *aiganaz is a `===Participle===` ("past participle of
    # *aiganą") and an `===Adjective===` ("own") on one Wiktionary page with one
    # etymology.  The glossary already prints them as one row — "verb / adj",
    # "own; past participle of *aiganą" — so the page prints the same, and the
    # reader is never shown the grammar where they asked for the meaning
    # (admin, 2026-11-12: "multiple entries … for aiganaz").
    group = groups[sense_no - 1] if 0 < sense_no <= len(groups) else None
    head = entry
    if group and len(group["entries"]) > 1:
        head = dict(entry, pos=" / ".join(group["pos"]),
                    gloss=list(group["gloss"]) or list(entry.get("gloss") or []))
    # A word's own pathway (a law that never applied to it) is part of the
    # answer, so every view of this word — the headline derivation, the ladder
    # and the branch below it — is computed with the same laws switched off.
    # A plain view (no switches, no edited start, no composed suffix) quotes the
    # published band; an edited one asks its own question and keeps its own
    # verdict (2026-11-09, so the glossary and the page cannot disagree).
    disabled = tuple(disabled or ())
    path = tuple(path or ())
    plain_view = not (disabled or from_stage or ghost or suffix or path
                      or build or not pathway)
    disabled, enabled, _own = _pathway_for(lang, entry["word"], disabled, pathway)
    chain = data.derivation_chain(lang)
    trace = None
    if chain:
        trace = _derive_for_entry(entry, chain, disabled, enabled)
    cog = _cognate_payload(entry["cog"]) if entry.get("cog") else None
    if cog is None and lang == ROOT_LANG:
        # The root lexicon carries no ``cog`` row: find its set by the etymon so
        # the page does not deny a set whose forms it is about to quote.
        set_id = cognate_set_for(entry["word"])
        cog = _cognate_payload(set_id) if set_id else None
    if cog and trace and trace.get("matched_form"):
        # Show the reading the rules actually produce next to this word in the
        # cognate table, not an arbitrary one of its accepted romanisations.
        for row in cog["forms"]:
            if row["l"] == lang and row["w"] == entry["word"]:
                row["r"] = trace["matched_form"]
                # The compact reading beside the word should be the one the
                # laws produce, not another accepted variant (پدر → pedar).
                row["reading"] = trace["matched_form"]
                break
    # Rebuild the cognates of *this* word from its own etymon. The cognate set's
    # PIE form wins when there is one: an ancestry row may record a root rather
    # than the etymon the whole set is built on.
    pie = (cog or {}).get("pie") or _pie_form(entry)
    rebuilt = None
    if lang == ROOT_LANG:
        # A word *in* Proto-Indo-European is the etymon: there is no ancestry to
        # climb, so its page descends by its ladder's own next steps.  The
        # 40-row table of predictions the removed *reconstruct into* selector
        # used to read is no longer sent with the page: `rebuilds_for_etymon`
        # still answers it for tools and tests (admin, 2026-11-12).
        rebuilt = None
    elif pie:
        recorded = _recorded_forms((cog or {}).get("forms", []))
        bucket = recorded.setdefault(lang, [])
        meta = _with_reading({
                "ipa": (entry.get("ipa") or "").strip().strip("/[]").strip(),
                "reading": readings_for(entry)["reading"],
                "kind": kind_of(lang), "script": _lang(lang).get("script", ""),
                "show_reading": show_reading(lang, entry["word"]),
                "evidence": evidence_for(entry["word"], lang)}, lang, entry["word"])
        for reading in ["", *attested_spellings(entry)]:
            bucket.append({"w": entry["word"], "r": reading, **meta})
        rebuilt = rebuilds(pie, recorded)
        if rebuilt:
            # A root (``*terh₁``) is not a word: the predictions below still
            # start from it, but the page has to say that they are rough.
            key = normalise_etymon(pie)
            rebuilt["source"]["root"] = (
                str(entry.get("cog", "")).endswith("-")
                or any(lang_ == "ine-pro" and normalise_etymon(word_) == key
                       and (rel_ == "root" or word_.strip().endswith("-"))
                       for lang_, word_, rel_ in _ancestry_triples(entry))
            )
    if cog:
        cog["rebuilds"] = rebuilt
    readings = readings_for(entry)
    # The ladder belongs to the sense the reader opened, not to the spelling:
    # Persian دوش is a shower (sense 1), a shoulder (2) and 'last night' (3),
    # and only the first of those is the French loan.  Without the sense the
    # ladder was always sense 1's, so a page for sense 3 showed no timeline at
    # all and sense 2's badge had no ancestry under it (2026-11-12).
    ladder = hierarchy(lang, entry["word"], disabled,
                       from_stage=from_stage, from_form=from_form,
                       pathway=pathway, suffix=suffix, path=path,
                       from_recorded=from_recorded, sense=sense_no,
                       build=build)
    branch = None
    # The laws work on the engine's own phonological form, so the branch starts
    # from the last rung of the ladder, not from a script spelling. A word *in*
    # Proto-Indo-European has no ladder: the etymon itself is the form the
    # branch starts from (2026-11-08: PIE pages should open into
    # their daughters the way every other word page does). A stage whose entry
    # is written in another script and has no ladder still gets no branch: its
    # headword is not a phonological form the laws could carry anywhere.
    if ladder and ladder.get("levels") and not ladder.get("hypothesis"):
        # The branch starts from this stage's own rung, not from wherever the
        # reader extended the timeline: a page opened with `?path=pal,fa` ends
        # its ladder in Persian, and carrying *that* form down from Old Persian
        # produced a word nobody's laws ever made (2026-11-12).
        own = [lv for lv in ladder["levels"] if lv.get("stage") == lang]
        source = (own or ladder["levels"])[-1]["form"]
    elif lang == ROOT_LANG:
        source = entry["word"]
    else:
        source = None
    # A rung of the ladder that quotes a record nobody verified goes into the
    # same queue as a branch row, so one list holds every such question
    # (2026-11-12).
    if ladder and ladder.get("levels"):
        _journal_unverified(lang, entry["word"], ladder["levels"],
                            page=entry["word"], key="stage")
    if data.descendants(lang) and source:
        origin: tuple[dict, str] = (entry, lang)
        if via and "/" in via:
            origin_lang, origin_word = via.split("/", 1)
            rows = word_index().get((origin_lang, origin_word)) or []
            if rows and (origin_lang, origin_word) != (lang, entry["word"]):
                origin = (rows[0], origin_lang)
        branch = _stage_descendants(lang, source, origin)
    word_constructions = constructions(entry, lang)
    page = {
        "word": entry["word"],
        "lang": lang,
        "lang_name": _lang(lang).get("name", lang),
        "script": _lang(lang).get("script", ""),
        "kind": kind_of(lang),
        "era_label": era_label(_lang(lang).get("era")),
        "evidence": _entry_evidence(lang, entry),
        "in_script": _in_native_script(lang, entry["word"]),
        "recon": bool(entry.get("recon")),
        # attested / recorded / proposed, printed beside the coverage band: how
        # the word itself is known, which is a different question from how much
        # of its ancestry the laws reproduce (2026-11-11).
        "attestation": attestation_of(entry, lang),
        "show_reading": show_reading(lang, entry["word"]),
        "reading": readings["reading"],
        "pos": head.get("pos", ""),
        # The dictionary's own grammar label, verbatim, when it prints one
        # (Dehkhoda's (اِ مرکب), (ص نسبی), (اِخ)).  The page prints it beside
        # the part of speech and never instead of it (2026-11-10).
        "pos_label": entry.get("pos_label", ""),
        "says": dict(entry.get("structure") or {}),
        "gloss": _page_gloss(lang, head, head.get("gloss", [])),
        # Which dictionary the gloss above is quoted from: the tab is named
        # after its source, and 153,215 Persian entries take theirs from
        # Dehkhoda, not from Wiktionary (2026-11-12, critic P1-7).
        "gloss_source": entry.get("source") or "",
        "ipa": readings["ipa"],
        "translit": entry.get("translit", ""),
        "translit_alt": entry.get("translit_alt", []),
        "rtl": is_rtl(entry["word"]),
        "etymology": _prose_etym(lang, str(head.get("word") or ""),
                                 entry.get("etym") or ""),
        # What the Persian Wiktionary's own page says, when one was read: the
        # address first, the etymology as a quotation.  Kept apart from
        # `etymology`, which is the record this model derives from.
        "wiktionary": _wiktionary_page(entry),
        "sources": _entry_sources(entry),
        # Where this word itself can be opened: its Wiktionary article and its
        # dictionary entry, each only when the page is recorded (admin,
        # 2026-11-12).  The header draws one icon per page and nothing else.
        "pages": _entry_pages(entry),
        "ancestry": _ancestry_forms(entry),
        "cognates": cog,
        "rebuilds": rebuilt,
        "descendants": branch,
        # The root language has nothing above it: the page offers a selector
        # instead of an ancestry ladder (2026-11-07), and since 2026-11-08 also
        # the cited derivational suffixes it may wear before the laws run.
        "is_root": lang == ROOT_LANG,
        "morphology": morphology(lang),
        # What the dictionary says the word is built from: base + suffix(es),
        # printed under the headword and used by the suffix picker. An entry may
        # state more than one, with a confidence each; the first is the one the
        # page composes with, the rest are shown as rival analyses. Empty when
        # the etymology does not state a construction (2026-11-08).
        "constructions": word_constructions,
        "construction": word_constructions[0] if word_constructions else None,
        # A word built from pieces draws them as a join: each piece keeps its
        # own recorded ancestry, so two origins meet in one timeline instead
        # of one origin pretending to explain the whole word (2026-11-09).
        "joins": _compound_pieces(entry, lang),
        # The seam this model reads when the record names no construction: keep
        # it beside `joins` (the record's own pieces) and label it, because the
        # two are different kinds of claim (2026-11-10).
        "seam": (_seam_payload(lang, entry)),
        "seam_join": (_seam_join(lang, entry)),
        # The words the dictionary builds on this one, when it is a root or a
        # base other entries name: the other end of the construction line, so
        # a root page is a doorway rather than a dead end (2026-11-08).
        "built_from": (_construction_index(lang).get(entry["word"]) or []
                       if str(entry.get("pos") or "").lower() == "root"
                       else []),
        "derivation": trace,
        "hierarchy": ladder,
        # The coverage band and the review backlog for this word. Both are
        # facts about the record, not about this view: they come from the same
        # pure verdict the counter uses (2026-11-09). Proto-Indo-European is
        # not an attested language, so its pages carry neither.
        "category": None if lang == ROOT_LANG else _script_aware_category(
            _page_category(entry, lang, ladder,
                           published=(band_for(lang, entry["word"], sense_no)
                                      if plain_view else None)),
            trace),
        "backlog": [] if lang == ROOT_LANG else (ladder or {}).get("backlog", []),
        # Who the word was borrowed from, when the record says it came from
        # outside the family: the badge reads "borrowed from Arabic" rather
        # than a bare "non-PIE", and the page can draw the contact window.
        "loan": None if lang == ROOT_LANG else _loan_of(entry, lang),
        # The recorded stages our laws do not reproduce (empty when every one
        # agrees).  The band says "with adjustments"; this says which.
        "steps_differ": (ladder or {}).get("steps_differ", []),
        # How many words share this spelling, and which one this page is.
        "variants": len(groups),
        "sense": sense_no,
        "sense_list": [{"sense": g["sense"], "pos": " / ".join(g["pos"]),
                        "gloss": g["gloss"],
                        "band": band_for(lang, g["rep"]["word"], g["sense"])}
                       for g in groups],
    }
    page = _with_reading(page, lang, entry["word"])
    if (page.get("reading_auto") and not readings.get("reading")
            and not readings.get("ipa") and entry.get("source") == "dehkhoda"):
        # A headword no dictionary reads gets no reading here: spelling Persian
        # letter by letter (آب‌خانه → ā-b-x-ā-n-h) is the alphabet, not the
        # word, and Dehkhoda's own entry — when the reader opens it — prints the
        # vowels the script leaves out (2026-11-10, the Dehkhoda headwords).
        page.update({
            "reading": "", "reading_auto": False, "show_reading": False,
            "reading_note": ("No dictionary reading is recorded for this headword; "
                             "the sign-by-sign transliteration would spell the "
                             "alphabet, not the word."),
        })
    return page


def rules(from_stage: str | None = None, to_stage: str | None = None, tier: str | None = None) -> list[dict]:
    out = []
    for (src, dst), rs in sorted(data.rulesets().items()):
        if from_stage and src != from_stage:
            continue
        if to_stage and dst != to_stage:
            continue
        rules_rows = []
        for r in rs.rules:
            if tier and r.tier != tier:
                continue
            rules_rows.append({
                "id": r.id, "order": r.order, "name": r.name,
                "match": r.match, "replace": r.replace, "left": r.left, "right": r.right,
                "transform": r.transform, "tier": r.tier, "optional": r.optional,
                "description": r.change, "notes": r.notes,
                "references": r.references, "examples": r.examples,
            })
        out.append({
            "src": src, "dst": dst, "src_name": _lang(src).get("name", src),
            "dst_name": _lang(dst).get("name", dst),
            "name": rs.name, "description": rs.description,
            "date_start": rs.date_start, "date_end": rs.date_end,
            "references": rs.references, "rules": rules_rows,
        })
    return out


def _find_rule(key: str):
    """Locate one rule by its qualified key, falling back to a unique bare id."""
    key = (key or "").strip()
    if not key:
        return None
    hits = []
    for (src, dst), ruleset in sorted(data.rulesets().items()):
        for rule in ruleset.rules:
            if rule_key(ruleset, rule.id) == key:
                return src, dst, ruleset, rule
            if ":" not in key and rule.id == key:
                hits.append((src, dst, ruleset, rule))
    return hits[0] if len(hits) == 1 else None


def rule_page(key: str) -> dict | None:
    """One registered law as a page of its own.

    A law on a word page is a claim, so it has to be possible to open it: what
    it changes, in which environment, on what evidence, at what tier, and which
    other laws stand beside it in the same transition (2026-11-08).
    Labelled laws — established and proposed alike — are doors; nothing on a
    word page should name a law the reader cannot read.
    """
    found = _find_rule(key)
    if not found:
        return None
    src, dst, ruleset, rule = found
    keys = [{"key": rule_key(ruleset, r.id), "id": r.id, "name": r.name, "tier": r.tier}
            for r in ruleset.rules]
    where = next((i for i, row in enumerate(keys) if row["id"] == rule.id), 0)
    sources = data.sources()
    used = None
    covered = coverage()
    if covered.get("rules_used"):
        # A law that applies in no exact derivation is worth saying out loud:
        # either an earlier gap blocks it, or the words it would explain miss
        # elsewhere (2026-11-08).
        used = 0
        for row in covered["rules_used"] or []:
            if row.get("id") == rule.id and row.get("to") == dst:
                used = row.get("count")
                break
    return {
        "key": keys[where]["key"],
        "id": rule.id,
        "name": rule.name,
        "tier": rule.tier,
        "order": rule.order,
        "optional": rule.optional,
        "pattern": {
            "match": rule.match, "replace": rule.replace,
            "left": rule.left, "right": rule.right,
            "transform": rule.transform,
            "display": (f"transform: {rule.transform}" if rule.transform
                        else f"{rule.match} → {rule.replace or '∅'}"),
        },
        "description": rule.change,
        "notes": rule.notes,
        "examples": rule.examples,
        "transition": {
            "src": src, "dst": dst,
            "src_name": _lang(src).get("name", src),
            "dst_name": _lang(dst).get("name", dst),
            "name": ruleset.name, "description": ruleset.description,
            "date_start": ruleset.date_start, "date_end": ruleset.date_end,
            "rules": len(ruleset.rules),
        },
        "references": [
            {"id": ref, "title": (sources.get(ref) or {}).get("title", ref),
             "url": (sources.get(ref) or {}).get("url", ""),
             "kind": (sources.get(ref) or {}).get("kind", "")}
            for ref in rule.references
        ],
        "applications": used,
        "previous": keys[where - 1] if where else None,
        "next": keys[where + 1] if where + 1 < len(keys) else None,
    }


def _step_key(step) -> str:
    """The qualified key of the law a derivation step applied."""
    for (src, dst), ruleset in data.rulesets().items():
        if dst != step.stage:
            continue
        for rule in ruleset.rules:
            if rule.id == step.rule_id:
                return rule_key(ruleset, rule.id)
    return ""


def derive_form(form: str, lang: str, disabled: Iterable[str] = (), tiers: Iterable[str] | None = None) -> dict:
    chain = data.derivation_chain(lang)
    d = derive(form, chain, data.rulesets(), disabled=list(disabled), tiers=set(tiers) if tiers else None)
    return {
        "input": form,
        "target": lang,
        "target_name": _lang(lang).get("name", lang),
        "chain": [{"id": c, "name": _lang(c).get("name", c)} for c in chain],
        "forms": d.forms,
        # Each step names its law's page, so the lab can open what it applied.
        "steps": [{**s.__dict__, "key": _step_key(s)} for s in d.steps],
        "skipped": d.skipped,
    }


def cognates(q: str = "", limit: int = 60) -> list[dict]:
    sets = sorted(cognate_index().values(), key=lambda r: r["pie"])
    if q:
        ql = q.lower()
        sets = [r for r in sets if ql in r["pie"].lower() or ql in r["gloss"].lower()]
    out = []
    for rec in sets[:limit]:
        payload = _cognate_payload(rec["id"]) or rec
        out.append({
            "id": rec["id"], "pie": rec["pie"], "gloss": rec["gloss"],
            "pos": rec["pos"], "n": payload["n"], "branches": payload["branches"],
        })
    return out


def cognate(set_id: str) -> dict | None:
    payload = _cognate_payload(set_id)
    if payload is None:
        return None
    return {**payload,
            "rebuilds": rebuilds(payload.get("pie"), _recorded_forms(payload["forms"]))}


def compare(a: str, b: str) -> dict:
    def parse(spec: str) -> tuple[str | None, str]:
        if ":" in spec:
            lg, w = spec.split(":", 1)
            return lg, w
        return None, spec

    la, wa = parse(a)
    lb, wb = parse(b)
    res = []
    for lg, w in ((la, wa), (lb, wb)):
        if lg:
            res.append(word(lg, w))
        else:
            hits = [x for x in search(w, limit=5)]
            res.append(word(hits[0]["lang"], hits[0]["word"]) if hits else None)
    if not all(res):
        return {"error": "word not found", "a": res[0], "b": res[1]}
    ea, eb = res
    ca = (ea.get("cognates") or {}).get("id")
    cb = (eb.get("cognates") or {}).get("id")
    return {
        "a": {"lang": ea["lang"], "lang_name": ea["lang_name"], "word": ea["word"], "gloss": ea["gloss"]},
        "b": {"lang": eb["lang"], "lang_name": eb["lang_name"], "word": eb["word"], "gloss": eb["gloss"]},
        "same_etymon": bool(ca and ca == cb),
        "etymon": ca if ca == cb else None,
        "etymon_gloss": (ea.get("cognates") or {}).get("gloss") if ca == cb else None,
    }

@lru_cache(maxsize=4)
def _backlog_at(path_text: str, _mtime_ns: int) -> dict:
    import yaml

    try:
        payload = yaml.safe_load(Path(path_text).read_text(encoding="utf-8")) or {}
    except Exception:
        return {"words": [], "kinds": {}, "counts": {}, "truncated": {}}
    return payload


def backlog() -> dict:
    """The generated review backlog (`data/review_backlog.yaml`).

    Cached on the file's mtime so the server picks up a rewrite without a
    restart.  A word here is a record to re-read, never a repaired derivation.
    """
    path = data.DATA / "review_backlog.yaml"
    try:
        st = path.stat()
    except OSError:
        payload: dict = {"words": [], "kinds": {}, "counts": {}, "truncated": {},
                         "note": "run tools/backlog.py --write"}
    else:
        payload = dict(_backlog_at(str(path), st.st_mtime_ns))
    # The matches the engine could not verify are collected as the pages are
    # read, not generated: they are the queue a person works through, newest
    # last, and they ride the same page so there is one place to look.
    unverified = review_queue.entries()
    if unverified:
        payload["unverified"] = unverified
        payload.setdefault("kinds", {}).setdefault(
            "unverified_match",
            "a branch row reproduces every sound of a record but its ending, "
            "and no registered law accounts for the difference")
        # They ride the same table as the generated kinds, so there is one
        # reading list rather than two places to remember (2026-11-12).
        words = list(payload.get("words") or [])
        for row in unverified:
            read = row.get("record_read") or row.get("reading") or "—"
            words.append({
                "lang": row["lang"],
                "word": row["word"],
                "etymon": row.get("laws_form") or row.get("form") or "",
                "kind": "unverified_match",
                "detail": (f"the laws give {row.get('form', '')}; the entry is read "
                           f"{read}; no registered law accounts for the difference"
                           if (row.get("basis") or "reading") == "reading"
                           else f"the laws give {row.get('form', '')}; the glossary holds "
                                f"{row.get('word', '')} and records no reading for it, so "
                                f"the vowels cannot be checked"),
                "evidence": row.get("gloss") or "",
            })
        payload["words"] = words
        counts = dict(payload.get("counts") or {})
        by_kind = dict(counts.get("by_kind") or {})
        by_kind["unverified_match"] = len(unverified)
        counts["by_kind"] = by_kind
        payload["counts"] = counts
    return payload


@lru_cache(maxsize=2)
def _coverage_at(_stamp: int) -> dict:
    path = data.ROOT / "data" / "coverage.json"
    return json.loads(path.read_text(encoding="utf-8"))


def coverage() -> dict:
    """Exact-derivation coverage, as measured by tools/coverage.py.

    Cached on the file's mtime like the backlog: 384 KB parsed on every
    `/api/overview` and `/api/coverage` is a second of a page load for a
    document that changes once a measurement (2026-11-12).
    """
    path = data.ROOT / "data" / "coverage.json"
    if not path.exists():
        return {"languages": {}, "tiers": "all", "stale": False,
                "note": "run tools/coverage.py"}
    report = dict(_coverage_at(path.stat().st_mtime_ns))
    current = data.measurement_inputs()
    report["stale"] = (data.inputs_stale(report.get("inputs"), current)
                       or band_index().stale)
    return report
