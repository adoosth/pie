"""Reading a language's own script: what a written word can say.

The glossary stores a headword the way a text writes it — Old Persian
``𐎺𐎼𐎣`` — and, sometimes, the romanisation a dictionary gives it.  When the
two stand in the relation of a *syllabic writing system rather than of letters, a
comparison of strings says nothing: the Old Persian syllabary spells
consonants and some vowels, leaves a word-final /h/ unwritten and lets a
vowel sign carry a bare consonant as a filler (𐎭𐎼𐎹 d-a-r-y is /draya/,
𐎤𐎢𐎽𐎢𐏁 k-u-r-u-š is /kuruš/).  A word-final short -i is closed with the
y-sign, which adds no sound of its own (𐎠𐎡𐎫𐎡𐎹 a-i-t-i-y is /aiti/, not
/aitiya/; 𐎠𐎿𐎫𐎡𐎹 a-s-t-i-y is /asti/).  So ``wˈarkah`` is not a different
word from 𐎺𐎼𐎣 — it is one of the readings that spelling allows
(2026-11-08).

This module is that relationship and nothing else: it decodes a headword to
the signs a scribe wrote, and it answers whether a phonological form is a
possible reading of those signs.  It is not a sound law: it may never turn one
form into another, and it never says what a word *means*.

A table lives in ``data/script/<lang>.yaml``:

    stage: {id: peo, name: Old Persian cuneiform, references: [kent-1953]}
    signs:
      - {char: "𐎠", value: "a", kind: vowel}
      - {char: "𐎣", value: "ka", kind: cv}
    logograms:
      - {char: "𐏋", value: "xšāyaθiya", kind: logogram}

``value`` is the sign's transliteration (a vowel, a consonant plus its
inherent vowel, or a whole word for a logogram).  A table may also declare
reading conventions — sign pairs that close a word without adding a sound:

    conventions:
      - {id: final_i_iy, name: "a word-final -i is written i-y",
         vowel_sign: "𐎡", final_sign: "𐎹"}

Nothing here is a pronunciation: the vowels a scribe wrote are evidence about
a reading, not a transcription of it.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from . import data

SCRIPT_DIR = data.DATA / "script"

#: Length is writing, not a letter (``_base_letters`` drops it), so the sound
#: lists of an abjad's signs are compared without it: ā and a are one letter.
_LENGTH_FOLD = {"ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u"}

#: Marks that belong to a dictionary's notation, not to a letter: the
#: superscript of aspiration, the nasalisation of ``Hiⁿduš``, the breve.
#: '\u02be' aleph and '\u02bf' ayin are NOT such marks: Semitic and Iranian
#: transliteration writes a real letter with a modifier glyph, so the range
#: skips those two code points (2026-11-09, Middle Persian's ʾp̄ʾt').
_SUPERSCRIPTS = re.compile(r"[\u02b0-\u02bd\u02c0-\u02ff\u1d00-\u1dbf\u2070-\u209f\u207a-\u209c]")


def _base_letters(text: str) -> list[tuple[str, bool]]:
    """Split a form into (letter, is_vowel) pairs, notation aside.

    Length, stress, aspiration and syllabicity are writing, not letters: the
    syllabary writes ``r`` whether the phonologist writes ``r`` or ``r̥``, and
    it does not mark a long vowel.  ``ʰ`` becomes *h* — the same convention the
    rest of the service uses for Old Persian's final /h/.
    """
    return list(_split_letters(text or ""))


@lru_cache(maxsize=8192)
def _split_letters(text: str) -> tuple[tuple[str, bool], ...]:
    """The work of `_base_letters`, cached: a script table writes the same few
    hundred sign values over and over, and indexing Persian's 164k headwords
    called it once per sign (2026-11-12)."""
    return tuple(_parse_letters(text))


def _parse_letters(text: str) -> list[tuple[str, bool]]:
    # ʰ is a letter here: the syllabary's final /h/ is written with it.
    text = text.replace("ʰ", "h")
    out: list[tuple[str, bool]] = []
    for char in unicodedata.normalize("NFD", unicodedata.normalize("NFC", text)):
        if unicodedata.combining(char) or _SUPERSCRIPTS.match(char):
            continue
        for letter in unicodedata.normalize("NFD", char.lower()):
            if unicodedata.combining(letter):
                continue
            if letter.isalpha():
                out.append((letter, letter in "aeiou"))
    return out


@lru_cache(maxsize=None)
def table(lang: str) -> dict[str, dict]:
    """Every sign of one script, by the character a text writes."""
    path = SCRIPT_DIR / f"{lang}.yaml"
    if not path.exists():
        return {}
    raw = data._load_yaml(path)
    rows: dict[str, dict] = {}
    for row in (raw.get("signs") or []) + (raw.get("logograms") or []):
        if not row.get("char"):
            continue
        sounds = [s for s in (row.get("sounds") or []) if s]
        if not row.get("value") and not sounds:
            continue
        rows[row["char"]] = {
            "char": row["char"],
            "value": row.get("value") or sounds[0],
            "sounds": [_LENGTH_FOLD.get(x, x) for x in sounds] or sounds,
            "kind": row.get("kind") or ("cv" if len(row["value"]) > 1 else "vowel"),
            "gloss": row.get("gloss", ""),
        }
    return rows


@lru_cache(maxsize=None)
def conventions(lang: str) -> list[dict]:
    """The sign pairs a table declares as a closing convention, if any.

    A convention says two signs write one vowel at the end of a word — the
    y-sign after i marks a final -i and carries no sound of its own — so a
    reading that ends on the vowel alone is still a reading of those signs.
    It is orthography, not phonology: nothing here ever changes a sound.
    """
    path = SCRIPT_DIR / f"{lang}.yaml"
    if not path.exists():
        return []
    out: list[dict] = []
    for row in data._load_yaml(path).get("conventions") or []:
        if not row.get("id"):
            continue
        # A closing convention names a sign pair and is used by the aligner; a
        # statement about what the script does not write (an abjad leaves the
        # short vowels out) has no pair and is documentation the matcher obeys
        # by its ``kind`` alone (2026-11-09).
        out.append({"id": row["id"], "name": row.get("name") or row["id"],
                    "kind": row.get("kind") or "closing",
                    "vowel_sign": row.get("vowel_sign", ""),
                    "final_sign": row.get("final_sign", ""),
                    "note": row.get("note", "")})
    return out


@lru_cache(maxsize=None)
def readings(lang: str) -> dict[str, dict]:
    """The readings the record states for this language's spellings.

    A script does not read itself when it is an abjad: Book Pahlavi writes no
    short vowels, so ``sng`` is sang, sing and sung at once, and the only
    honest reading of a spelling is one the record states.  Those readings live
    in ``data/readings_<lang>.json`` (built by ``tools/build_pal_readings.py``),
    one row per spelling:

        "swk'": {reading: "saxwan", source: "MacKenzie 1971 s.v. saxwan"}

    ``read`` is the lookup and nothing else: it never guesses a vowel, and a
    spelling the table does not hold has no reading here (2026-11-09).
    """
    path = data.DATA / f"readings_{lang}.json"
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return rows if isinstance(rows, dict) else {}


def read(lang: str, form: str) -> str:
    """The recorded reading of a spelling, or ``""`` when none is recorded."""
    row = readings(lang).get((form or "").strip())
    if not row:
        return ""
    return (row.get("reading") or "").strip()


def _closing(lang: str, decoded: list[dict]) -> dict | None:
    """The declared convention the last two signs of a headword are spelled by."""
    if len(decoded) < 2:
        return None
    last, before = decoded[-1]["char"], decoded[-2]["char"]
    for rule in conventions(lang):
        if rule["final_sign"] == last and rule["vowel_sign"] == before:
            return rule
    return None


def available() -> list[str]:
    """The languages this repo can read in their own script."""
    return sorted(p.stem for p in SCRIPT_DIR.glob("*.yaml")) if SCRIPT_DIR.is_dir() else []


def stage(lang: str) -> dict:
    path = SCRIPT_DIR / f"{lang}.yaml"
    if not path.exists():
        return {}
    return data._load_yaml(path).get("stage") or {}


def writes(lang: str, word: str) -> bool:
    """Whether this form is spelled in a script the table knows.

    A word written in Latin letters (Old Persian ``madu``, a reconstruction)
    is not: there is nothing to decode, and the sound laws compare it as it is.
    """
    rows = table(lang)
    return bool(rows) and any(char in rows for char in word or "")


def signs(lang: str, word: str) -> list[dict] | None:
    """The signs of a headword, in order, or ``None`` if a character is unknown.

    Punctuation a dictionary writes around a form (a hyphen on an affix) is
    skipped; a character the table does not know is a fact the caller has to
    see, not something to guess past.
    """
    rows = table(lang)
    if not rows:
        return None
    out: list[dict] = []
    for char in word or "":
        if char in rows:
            out.append(rows[char])
        elif unicodedata.category(char).startswith("L"):
            return None
    return out or None


def skeleton(lang: str, word: str) -> str:
    """The consonants a headword's signs spell, which any reading must share.

    This is the index key for finding the records a form could be a reading
    of: the vowels are the part the script underdetermines, so they cannot
    narrow the search, but the consonants can.  ``v`` and ``w`` are one
    consonant here for the same reason they are one in ``match``.  A logogram
    has no skeleton (it is a whole word in one sign).
    """
    decoded = signs(lang, word)
    if not decoded or any(sign["kind"] == "logogram" for sign in decoded):
        return ""
    out: list[str] = []
    for sign in decoded:
        out.extend(letter for letter, vowel in _base_letters(sign["value"]) if not vowel)
    return "".join(_key_letter(letter) for letter in out)


def reading_skeleton(form: str) -> str:
    """The consonants of a phonological form, as ``skeleton`` spells them."""
    return "".join(_key_letter(letter) for letter, vowel in _base_letters(form) if not vowel)


def _key_letter(letter: str) -> str:
    return "v" if letter == "w" else letter


def transliterate(lang: str, word: str) -> str:
    """The sign-by-sign transliteration of a headword: ``va-ra-ka``.

    A hyphen joins the signs, exactly as an edition of the inscriptions prints
    them.  This is what the script *writes* — it is not a pronunciation and
    the service never treats it as one (``attested_spellings`` rejects
    hyphenated transcriptions for that reason).  An unknown character is kept
    as it is, so the string never claims more than it knows.
    """
    decoded = signs(lang, word)
    if not decoded:
        return ""
    return "-".join(sign["value"] for sign in decoded)


def _same_letter(sign_letter: str, form_letter: str) -> bool:
    """One letter, two transcriptions: the sign 𐎺 is read v, the laws write *w."""
    return sign_letter == form_letter or {sign_letter, form_letter} == {"v", "w"}


def _align(signs: list[dict], tokens: list[tuple[str, bool]],
           index: int = 0, at: int = 0, memo: dict | None = None
           ) -> tuple[list[int], list[int]] | None:
    """Fit the signs to a form's letters, allowing the script's own gaps.

    Returns the letters the signs spell and the signs that stand for a bare
    consonant.  A fit must consume the whole form except the word-final /h/ the
    script leaves unwritten; anything else is no fit at all.  Alternatives are
    tried in the order a reader would: the sign's own vowel first, then a
    filler, because a filler is the reading of last resort (2026-11-08).
    """
    memo = {} if memo is None else memo
    key = (index, at)
    if key in memo:
        return memo[key]
    result = None
    if index == len(signs):
        if at == len(tokens) or [t for t, _v in tokens[at:]] == ["h"]:
            result = ([], [])
        memo[key] = result
        return result
    sign = signs[index]
    value = _base_letters(sign["value"])
    consonants = [t for t, vowel in value if not vowel]
    vowels = [t for t, vowel in value if vowel]
    if sign["kind"] == "cv" and consonants:
        # A sign may write more than one consonant: щ is št, ѯ is ks.  The
        # consonants must stand in the reading one after another, exactly as a
        # single-consonant sign must match its one letter; without this every
        # word with such a sign was a miss no law could repair (Old Church
        # Slavonic, 2026-11-09: 71 headwords contain щ and 86 write two
        # consonants in one sign).
        width = len(consonants)
        if width > 1 and at + width <= len(tokens) and all(
                not tokens[at + k][1] and _same_letter(consonants[k], tokens[at + k][0])
                for k in range(width)):
            after = at + width
            own = vowels[0] if vowels else ""
            spelled: list[int] = list(range(at, after))
            if own and after < len(tokens) and tokens[after][1] \
                    and _same_letter(own, tokens[after][0]):
                found = _align(signs, tokens, index + 1, after + 1, memo)
                if found is not None:
                    result = (spelled + [after] + found[0], found[1])
            if result is None:
                found = _align(signs, tokens, index + 1, after, memo)
                if found is not None:
                    result = (spelled + found[0], found[1])
        if result is None and at < len(tokens) and not tokens[at][1] \
                and _same_letter(consonants[0], tokens[at][0]):
            after = at + 1
            own = vowels[0] if vowels else ""
            tries: list[tuple[int, list[int], list[int]]] = []
            if own and after < len(tokens) and tokens[after][1] and _same_letter(own, tokens[after][0]):
                tries.append((after + 1, [], [at, after]))        # the sign's own vowel
            if own and after + 1 < len(tokens) and tokens[after][1] and tokens[after][0] == "a" \
                    and tokens[after + 1][1] and _same_letter(own, tokens[after + 1][0]):
                tries.append((after + 2, [after], [at, after, after + 1]))  # /au/ written ku
            tries.append((after, [index], [at]))                  # a bare consonant
            for stop, filler, spelled in tries:
                found = _align(signs, tokens, index + 1, stop, memo)
                if found is not None:
                    result = (spelled + found[0], filler + found[1])
                    break
    elif sign["kind"] == "vowel" and vowels:
        own = vowels[0]
        if at < len(tokens) and tokens[at][1] and _same_letter(own, tokens[at][0]):
            found = _align(signs, tokens, index + 1, at + 1, memo)
            if found is not None:
                result = ([at, *found[0]], found[1])
        if result is None and own == "a":
            # A lone a-sign may spell a syllabic resonant (a-r-š-t-i-š is r̥štiš).
            found = _align(signs, tokens, index + 1, at, memo)
            if found is not None:
                result = (found[0], [index, *found[1]])
    memo[key] = result
    return result


_SHORT_VOWELS = set("aiueo")


def _align_letters(signs: list[dict], tokens: list[tuple[str, bool]]) -> bool:
    """Whether a reading can be what an abjad's signs write.

    Each sign writes exactly one letter of the reading, and that letter has to
    be one of the sounds the sign can stand for (Book Pahlavi's 𐭥 is w, r or
    ʿ; 𐭬 is m or q).  A short vowel the reading has and the script does not
    write is simply skipped: it costs no sign.  Nothing else is forgiven — a
    consonant the reading has and no sign writes is no fit, and neither is a
    sign the reading cannot fill (2026-11-09).
    """
    def walk(i: int, j: int) -> bool:
        if i == len(signs):
            return all(token[0] in _SHORT_VOWELS for token in tokens[j:])
        if j >= len(tokens):
            return False
        token = tokens[j][0]
        if token in (signs[i].get("sounds") or [signs[i]["value"]]) and walk(i + 1, j + 1):
            return True
        if token in _SHORT_VOWELS and walk(i, j + 1):
            return True
        return False

    return walk(0, 0)


def match(lang: str, reading: str, headword: str) -> dict | None:
    """Whether ``reading`` is a possible reading of the script's ``headword``.

    ``None`` when there is nothing to say: no table for this language, a word
    not written in the script, a character the table does not know, or an
    empty form.  Otherwise the answer carries what the scribe wrote
    (``translit``), whether the form fits (``ok``), the signs that stood for a
    bare consonant (``filler``), the letters the script left unwritten
    (``unwritten``) and, when the word only fitted after dropping a closing
    sign, the convention that says so (``convention``) — so a page can print
    both forms and let the reader judge.

        >>> match("peo", "wˈarkah", "𐎺𐎼𐎣")["translit"]
        'va-ra-ka'

    A logogram is a whole word in one sign and is compared by value, with a
    dictionary's notation (case, stress, length) aside.
    """
    tokens = _base_letters(reading)
    # A leading superscript ʰ is the convention that the sound is *not written*:
    # Old Persian 𐎢 is read ʰu "good" (Proto-Iranian *Hsu-), one sign for the
    # vowel, with no sign for the /h/ the language still had. It is a letter of
    # the reading the script leaves out, exactly like a word-final /h/, so the
    # alignment is run without it and the answer says so (2026-11-09: the first
    # headword the corpus gained that the sign table could not read).
    leading_h = str(reading or "").startswith("ʰ")
    if leading_h:
        tokens = tokens[1:]
    if not tokens or not writes(lang, headword):
        return None
    decoded = signs(lang, headword)
    if not decoded:
        return None
    if not (len(decoded) == 1 and decoded[0]["kind"] == "logogram") \
            and all(sign.get("sounds") for sign in decoded):
        # An abjad: the signs write consonants (and a few long vowels) and
        # leave the short vowels to the reader.
        translit = transliterate(lang, headword)
        # ``abjad`` tells the caller that the signs write consonants, so the
        # short vowels come from the reader.  A comparison between a derived
        # form and the dictionary's reading cannot rest on the signs alone
        # there: the record states the vowels, and a long one the writing would
        # spell is part of the word (2026-11-12).
        return {"ok": _align_letters(decoded, tokens), "translit": translit,
                "logogram": False, "filler": [], "unwritten": [],
                "convention": None, "abjad": True}
    if len(decoded) == 1 and decoded[0]["kind"] == "logogram":
        wanted = [t for t, _v in _base_letters(decoded[0]["value"])]
        written = [t for t, _v in tokens]
        # A logogram stands for the word the dictionary glosses it with; the
        # final /h/ the syllabary leaves unwritten is still not written, and an
        # edition may abbreviate the logogram by its first letters (𐏋 is read
        # XŠ for *xšāyaθiya*) — never by an arbitrary subsequence.
        abbreviated = len(written) >= 2 and written == wanted[:len(written)]
        final_h = bool(wanted) and written[:-1] == wanted and written[-1] == "h"
        return {
            "ok": written == wanted or final_h or abbreviated,
            "translit": decoded[0]["value"],
            "logogram": True,
            "filler": [],
            "unwritten": [],
            "convention": None,
        }
    found = _align(decoded, tokens)
    closing = None
    if found is None:
        # The word may close with a sign that writes no sound of its own (a
        # final -i spelled i-y).  Read the word again without it; the answer
        # says which convention was used, so the page can print the reason
        # instead of leaving a green rung unexplained (2026-11-08).
        closing = _closing(lang, decoded)
        if closing is not None:
            found = _align(decoded[:-1], tokens)
    translit = transliterate(lang, headword)
    if found is None:
        return {"ok": False, "translit": translit, "logogram": False,
                "filler": [], "unwritten": [], "convention": None}
    spelled, filler = found
    unwritten = [tokens[i][0] for i in range(len(tokens)) if i not in set(spelled)]
    if leading_h:
        unwritten.insert(0, "h")
    return {
        "ok": True,
        "translit": translit,
        "logogram": False,
        "filler": filler,
        "unwritten": unwritten,
        "convention": closing,
    }


def reading_letter(letter: str) -> str:
    """A letter of the alignment back in the notation a page prints."""
    return "h" if letter == "h" else letter
