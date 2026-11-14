"""What a word written in its own script is read as, and where that comes from.

The interface never prints a scripted headword bare (2026-11-08).  There are
three places a reading may come from, and they are never mixed:

* **recorded** — the entry's own IPA or romanisation (``readings_for`` in the
  service), printed plainly;
* **quoted** — a reading the glossary's own etymology sentences or Wiktionary
  templates write beside the same script form (Wiktionary's "Old Persian
  𐎱𐎠𐎼𐎿 (p-a-r-s /⁠pārsa⁠/)" or `{{inh|pal|peo|𐎼𐎢𐎨|ts=raučah-}}`), taken
  by ``tools/build_readings.py`` into ``data/readings.json``; printed plainly
  too, with the entry it was read in — and, unlike ``automatic``, usable as the
  form the sound laws start from;
* **automatic** — the script's own values (``script.transliterate`` for a
  tabulated syllabary, ``translit.transliterate`` for every other script),
  printed in the colour of an automatic reading because no dictionary states
  it.

Nothing here is a sound law and nothing enters the attested figure: a reading
is how a word is written aloud, not a derivation.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from . import data, script, translit
from .script import reading_skeleton

READINGS_PATH = data.DATA / "readings.json"

#: A parenthesis that prints a transliteration and, after a slash, a reading.
_SLASHED = re.compile(r"([^\s/]{1,40})\s*/\s*([^/]{1,60})\s*/")
_WORDISH = re.compile(r"[^\W\d_][\w\u0300-\u036fʰʷʲˠʼ·\-]{0,40}")


@lru_cache(maxsize=None)
def quoted() -> dict[str, dict]:
    """Readings the corpus quotes for a script form, built by the data tool."""
    if not READINGS_PATH.exists():
        return {}
    try:
        rows = json.loads(READINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return rows if isinstance(rows, dict) else {}


def for_form(lang: str, form: str) -> dict:
    """The reading the corpus quotes for *this language's* spelling of a form.

    The table is keyed by the form as the dictionary prints it, because that is
    what the sentences name, and a row may state which language it belongs to.
    A row from another language with the same spelling is not this form's
    reading: Pahlavi ``lwc`` and anything else written ``lwc`` are two words
    (2026-11-11).
    """
    row = quoted().get((form or "").strip())
    if not row:
        return {}
    row_lang = (row.get("lang") or "").strip()
    if row_lang and lang and row_lang != lang:
        return {}
    return row


def fits(form: str, token: str) -> bool:
    """Whether a bare token can be the reading of *form* (same consonants).

    A parenthesis may hold a gloss — Proto-Slavic ``-akъ (masculine)`` — and a
    gloss is not a reading.  A reading spells the word, so it keeps the
    consonants the script writes (2026-11-08).
    """
    source = reading_skeleton(translit.transliterate(form).get("reading", ""))
    return bool(source) and source == reading_skeleton(token)


def long_enough(form: str) -> bool:
    """Whether a form has enough consonants for a bare token to be its reading.

    A one-consonant affix matches too many words by shape alone (-ъkъ and ŭkŭ
    share their only consonant), so a bare parenthesis is only trusted for a
    form that can be told apart (2026-11-08).
    """
    return len(reading_skeleton(translit.transliterate(form).get("reading", ""))) >= 2


def parse_quote(inside: str, form: str = "") -> dict:
    """The transliteration and reading a parenthesis prints, if it prints one.

    "p-a-r-s /⁠pārsa⁠/, “Persian”" is a transliteration and a reading; "bāzu"
    is a reading; "“tear”" and "(Kent 1953)" are neither, and yield nothing.
    """
    text = (inside or "").replace("\u2060", "").strip()
    if not text:
        return {}
    found = _SLASHED.search(text)
    if found:
        translit_ = found.group(1).strip(" ,;.")
        reading = found.group(2).strip().strip("-")
        if translit.is_scripted(reading):
            return {}
        return {"translit": translit_ if _WORDISH.fullmatch(translit_) else "",
                "reading": reading}
    token = text.split(",")[0].strip().split()[0].strip(" ,;.”\"'-")
    if not token or not _WORDISH.fullmatch(token) or translit.is_scripted(token):
        return {}
    if form and not fits(form, token):
        return {}
    return {"translit": "", "reading": token}


def beside(etym: str, form: str) -> dict:
    """The reading an etymology sentence writes right after a script form."""
    if not etym or not form or not translit.is_scripted(form):
        return {}
    found = re.search(re.escape(form) + r"\s*\(([^()]{1,90})\)", etym)
    if not found:
        return {}
    return parse_quote(found.group(1), form)


def signs_for(lang: str, word: str) -> str:
    """The sign-by-sign transliteration of a word written in its own script.

    A word has two Latin layers and they answer different questions: its
    **romanisation** is how the language is read (*Vr̥kānaʰ*, *gorg*), and its
    **transliteration** is what the signs spell (``va-ra-ka-a-na``, ``g-r-g``).
    The second is not a pronunciation and may not stand in for the first
    (2026-11-13), but a script is unreadable without it, so the page
    prints both.  A Latin-script or reconstructed word has no such layer and
    gets an empty string.
    """
    if not translit.is_scripted(word):
        return ""
    if script.table(lang):
        written = script.transliterate(lang, word)
        if written:
            return written
    # A script this model keeps no sign table for still has letters
    # (Greek, Gothic): the letter-by-letter transliteration is its layer.
    return translit.transliterate(word).get("reading", "")


def display(lang: str, word: str, ipa: str = "", reading: str = "") -> dict:
    """The reading line for one form: recorded, quoted, or automatic.

    ``auto`` is true only for the third kind, so the page can print it in its
    own colour; ``how`` says which of the three it is and ``note`` explains it
    in one sentence for the tooltip.  A scripted word never leaves this
    function without a reading (2026-11-08).

    ``signs`` is the second Latin layer and is filled whenever the word is
    written in a script, whether or not a romanisation was recorded: the
    romanisation says how the word is read, the signs say what the scribe
    wrote, and a page shows both (2026-11-13).

    A headword already written in Latin letters *is* a kind of reading — Book
    Pahlavi ``lwc`` — and the sign-by-sign layer has nothing to add to it:
    ``l-w-c`` is the same letters a third time, not a pronunciation.  So that
    layer is only reached by a word written in a script, and a transliteration
    shows a reading only when a dictionary states one (2026-11-11).
    """
    out = {"ipa": ipa or "", "reading": reading or "", "translit": "",
           "signs": signs_for(lang, word),
           "auto": False, "how": "recorded" if reading else "", "note": "",
           "script": ""}
    # A recorded IPA is a reading: an automatic transliteration beside it
    # would only add a second, weaker claim (2026-11-08).
    if out["ipa"] or out["reading"] or not translit.is_scripted(word):
        return out
    quote = for_form(lang, word)
    if quote and quote.get("reading"):
        out.update(reading=quote["reading"], how="quoted",
                   translit=quote.get("translit", ""),
                   note=(f"Read in the glossary's own etymology for "
                         f"{quote.get('source', 'another entry')}"))
        return out
    # A spelling the language's own table reads wins over reading the signs
    # one by one: Book Pahlavi 𐭢𐭥𐭫𐭢 is *gurg* in MacKenzie, and the signs
    # alone give g-w-l-g (2026-11-09).  This is a recorded reading, not an
    # automatic one, so it is not marked as a guess.
    stated = script.read(lang, word)
    if stated:
        out.update(reading=stated, how="stated",
                   note=(f"Read in the language's own table of spellings "
                         f"(data/readings_{lang}.json)"))
        return out
    if not translit.is_scripted(word):
        # Nothing is recorded for this transliteration: leave it bare rather
        # than spell the same letters back at the reader.
        return out
    if script.table(lang):
        signs = script.transliterate(lang, word)
        if signs:
            out.update(reading=signs, how="signs", auto=True,
                       script=translit.script_name(word),
                       note=("No reading recorded — transliterated from the "
                             f"signs: {signs}"))
            return out
    letters = translit.transliterate(word)
    if letters.get("reading"):
        out.update(reading=letters["reading"], how="letters", auto=True,
                   script=letters["script"],
                   note=(f"No reading recorded — transliterated from the "
                         f"{letters['script']} letter by letter"))
        return out
    out.update(reading="?", how="none", auto=True,
               script=translit.script_name(word),
               note="No reading recorded, and no table reads this script yet.")
    return out
