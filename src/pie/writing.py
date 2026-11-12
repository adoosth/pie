"""Writing a phonemic form in a language's own script.

This is the inverse direction of :mod:`pie.translit`, which *reads* a script.
Here the question is how a language would write a phonological form: Sanskrit
writes *devás* as देवः and *śatám* as शतम्.  Nothing about a sound changes, so
this belongs to the orthographic layer (``data/spelling/<lang>.yaml``), never to
a sound law, and a word matched through it is counted in the orthographic
column, never in the historical one.

Devanagari is an abugida: a consonant sign carries an inherent *a* (क is ka),
a following vowel replaces that *a* with a dependent sign (कि is ki), and a
following consonant takes the inherent *a* away with the virama (क् is k).  The
table below is the standard one (Whitney, *Sanskrit Grammar*, 1889, ch. 1-2),
and the algorithm is the syllabification a writer performs, not a rule that may
rewrite one form into another.

Unknown notation (a laryngeal that survived, an affricate the last stage did
not resolve) is kept as it stands rather than guessed at, so a spelling that
comes out wrong is visible as wrong instead of looking like a match.
"""
from __future__ import annotations

import unicodedata

VIRAMA = "्"

#: Consonants, by the phoneme the last sound-law stage writes.
_CONSONANTS = {
    "k": "क", "kh": "ख", "g": "ग", "gh": "घ", "ŋ": "ङ",
    "c": "च", "ch": "छ", "j": "ज", "jh": "झ", "ñ": "ञ",
    "ṭ": "ट", "ṭh": "ठ", "ḍ": "ड", "ḍh": "ढ", "ṇ": "ण",
    "t": "त", "th": "थ", "d": "द", "dh": "ध", "n": "न",
    "p": "प", "ph": "फ", "b": "ब", "bh": "भ", "m": "म",
    "y": "य", "r": "र", "l": "ल", "v": "व", "w": "व",
    "ś": "श", "ṣ": "ष", "s": "स", "h": "ह", "ḷ": "ळ",
}

#: Independent vowel signs (word-initial, or after another vowel).
_VOWELS = {
    "a": "अ", "ā": "आ", "i": "इ", "ī": "ई", "u": "उ", "ū": "ऊ",
    "r̥": "ऋ", "r̥̄": "ॠ", "l̥": "ऌ", "e": "ए", "ai": "ऐ", "o": "ओ", "au": "औ",
}

#: Dependent vowel signs, used after a consonant (``a`` is the inherent vowel).
_MATRAS = {
    "a": "", "ā": "ा", "i": "ि", "ī": "ी", "u": "ु", "ū": "ू",
    "r̥": "ृ", "r̥̄": "ॄ", "l̥": "ॢ", "e": "े", "ai": "ै", "o": "ो", "au": "ौ",
}

#: Signs that are written after the syllable they qualify.
_MARKS = {"ṃ": "ं", "m̐": "ँ", "ḥ": "ः", "ʼ": "ऽ"}

#: The notation some dictionaries and reconstructions use, folded before the
#: table is consulted: a superscript h is the aspiration of the letter before
#: it (bʰ is bh), a superscript w is labialisation, and ᶻ / ˢ are the voicing
#: detail a reconstruction writes on a sibilant.  Folding never adds a sound a
#: word does not have; it only lets the table see the letter.
_FOLD = {"ʰ": "h", "ʷ": "w", "ᶻ": "z", "ˢ": "s", "ʋ": "v", "ɐ": "a",
         "ē": "e", "ō": "o", "ă": "a", "ĕ": "e"}

_UNITS = sorted(set(_CONSONANTS) | set(_VOWELS) | set(_MARKS),
                key=len, reverse=True)


def _fold(form: str) -> str:
    form = unicodedata.normalize("NFC", form or "")
    out = []
    for ch in form:
        if ch in {"ˈ", "ˌ", "-", " "}:
            continue
        out.append(_FOLD.get(ch, ch))
    # The acute accent is *not* folded away: ś and ṣ and ṭ are letters, and
    # removing their diacritic would turn a palatal into a dental.  Stress is
    # already a separate mark in the engine's notation (``ˈa``), not ``á``.
    return unicodedata.normalize("NFC", "".join(out))


def _units(form: str) -> list[str]:
    """Split a phonemic form into the units the script writes."""
    text = _fold(form)
    out: list[str] = []
    i = 0
    while i < len(text):
        for unit in _UNITS:
            if text.startswith(unit, i):
                out.append(unit)
                i += len(unit)
                break
        else:
            out.append(text[i])
            i += 1
    return out


def devanagari(form: str) -> str:
    """Write a phonemic form as Devanagari writes it.

    >>> devanagari("dˈevas")
    'देवस्'
    >>> devanagari("śatˈam")
    'शतम्'
    """
    out: list[str] = []
    pending: str | None = None      # a consonant sign still carrying inherent a
    for unit in _units(form):
        if unit in _CONSONANTS:
            if pending is not None:
                out.append(pending + VIRAMA)
            pending = _CONSONANTS[unit]
        elif unit in _VOWELS:
            if pending is not None:
                out.append(pending + _MATRAS[unit])
                pending = None
            else:
                out.append(_VOWELS[unit])
        elif unit in _MARKS:
            if pending is not None:
                out.append(pending + VIRAMA)
                pending = None
            out.append(_MARKS[unit])
        else:
            if pending is not None:
                out.append(pending + VIRAMA)
                pending = None
            out.append(unit)
    if pending is not None:
        # A word ending in a consonant writes the virama (tat is तत्, not तत).
        out.append(pending + VIRAMA)
    return "".join(out)


def readable(form: str) -> bool:
    """Whether every unit of the form is one the Devanagari table owns."""
    return all(unit in _CONSONANTS or unit in _VOWELS or unit in _MARKS
               for unit in _units(form))


# --------------------------------------------------------------------------
# Avestan
# --------------------------------------------------------------------------
#: The Avestan alphabet, one letter per phoneme.  The script is an *alphabet*:
#: every vowel has a letter of its own and length is written, so the step from
#: a phonemic form to the manuscript's letters is a transcription, not the
#: reconstruction a syllabary forces.  The inventory and the transliteration of
#: each letter are Hoffmann & Forssman, *Avestische Laut- und Flexionslehre*
#: (2nd ed. 2004), pp. 44-46 and Skjærvø 2009; the four nasal vowels are
#: distinguished as the table distinguishes them (𐬂 å /ɒ/, 𐬃 ā̊ /ɒː/, 𐬄 ą
#: /ã/, 𐬅 ą̇ /ãː/) rather than lumped into one.
_AV_VOWELS = {
    "a": "𐬀", "ā": "𐬁", "å": "𐬂", "ā̊": "𐬃",
    "ą": "𐬄", "ą̄": "𐬅", "ą̇": "𐬅", "ə": "𐬆", "ə̄": "𐬇",
    "e": "𐬈", "ē": "𐬉", "o": "𐬊", "ō": "𐬋",
    "i": "𐬌", "ī": "𐬍", "u": "𐬎", "ū": "𐬏",
}

_AV_CONSONANTS = {
    "k": "𐬐", "x": "𐬑", "x́": "𐬒", "xᵛ": "𐬓", "xʷ": "𐬓",
    "g": "𐬔", "ġ": "𐬕", "γ": "𐬖", "c": "𐬗", "č": "𐬗",
    "j": "𐬘", "ǰ": "𐬘",
    "t": "𐬙", "θ": "𐬚", "d": "𐬛", "δ": "𐬜", "t̰": "𐬝",
    "p": "𐬞", "f": "𐬟", "b": "𐬠", "β": "𐬡",
    "ŋ": "𐬢", "ŋ́": "𐬣", "ŋᵛ": "𐬤", "ŋʷ": "𐬤",
    "n": "𐬥", "ń": "𐬦", "ṇ": "𐬧", "m": "𐬨", "m̨": "𐬩",
    "ẏ": "𐬪", "y": "𐬫", "v": "𐬬", "w": "𐬬",
    "r": "𐬭", "l": "𐬮",
    "s": "𐬯", "z": "𐬰", "š": "𐬱", "ž": "𐬲", "š́": "𐬳", "ṣ̌": "𐬴",
    "h": "𐬵",
}

#: A stressed vowel is written with an accent on the vowel in a reconstruction
#: (PII *Áryas) or with the engine's ``ˈ`` before it; Avestan writes no accent,
#: so an accented vowel letter is the plain vowel (Hoffmann & Forssman 2004,
#: §5: the alphabet marks no stress).
_AV_ACCENTED = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
                "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
                "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u"}

#: Two transcriptions of one letter, not two letters: Hoffmann writes ŋᵛ where
#: Gippert writes ŋᵘ, and the phonological stage may write w for v or č for c
#: (the affricate Avestan writes with the letter it calls c).  Folding one to
#: the other changes no letter of the manuscript.
_AV_ALIASES = {"w": "v", "xʷ": "xᵛ", "ŋʷ": "ŋᵛ", "č": "c", "ǰ": "j", "ą̄": "ą̇"}

_AV_UNITS = sorted(set(_AV_VOWELS) | set(_AV_CONSONANTS) | set(_AV_ACCENTED),
                   key=len, reverse=True)


def _avestan_fold(form: str) -> str:
    """Drop accent and stress notation; keep every letter as written."""
    out: list[str] = []
    for ch in unicodedata.normalize("NFC", form or ""):
        if ch in {"ˈ", "ˌ"}:
            continue
        out.append(_AV_ACCENTED.get(ch, ch))
    text = unicodedata.normalize("NFC", "".join(out))
    for alias, letter in _AV_ALIASES.items():
        text = text.replace(alias, letter)
    return text


def _avestan_units(form: str) -> list[str]:
    text = _avestan_fold(form)
    out: list[str] = []
    i = 0
    while i < len(text):
        for unit in _AV_UNITS:
            if text.startswith(unit, i):
                out.append(unit)
                i += len(unit)
                break
        else:
            out.append(text[i])
            i += 1
    return out


def avestan(form: str) -> str:
    """Write a phonemic form as the Avestan script writes it.

    >>> avestan("ahma")
    '𐬀𐬵𐬨𐬀'
    >>> avestan("friia")
    '𐬟𐬭𐬌𐬌𐬀'

    Between vowels *y* is written 𐬌𐬌 *ii* and *w* is written 𐬎𐬎 *uu*
    (Hoffmann & Forssman 2004, §5; the signs are read /ii̯/ and /uu̯/).
    Everywhere else *y* and *v* have their own letters, 𐬫 and 𐬬.  The doubled
    sign is the glide's own vowel, so it is written once when the vowel before
    it is already that letter: *xšaθriya-* is 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀 with two i, not
    three, and *friia-* is 𐬟𐬭𐬌𐬌𐬀.  A letter the table does not own is kept as
    it stands, so an unresolved notation can never pass as a spelling.
    """
    units = _avestan_units(form)
    out: list[str] = []
    for i, unit in enumerate(units):
        prev = units[i - 1] if i else ""
        nxt = units[i + 1] if i + 1 < len(units) else ""
        between_vowels = prev in _AV_VOWELS and nxt in _AV_VOWELS
        if unit in {"y", "ẏ"} and between_vowels:
            out.append("𐬌" if out and out[-1].endswith("𐬌") else "𐬌𐬌")
        elif unit in {"v", "w"} and between_vowels:
            out.append("𐬎" if out and out[-1].endswith("𐬎") else "𐬎𐬎")
        elif unit in _AV_VOWELS:
            out.append(_AV_VOWELS[unit])
        elif unit in _AV_CONSONANTS:
            out.append(_AV_CONSONANTS[unit])
        else:
            out.append(unit)
    return "".join(out)


def avestan_readable(form: str) -> bool:
    """Whether every unit of the form is one the Avestan table owns."""
    return all(unit in _AV_VOWELS or unit in _AV_CONSONANTS or unit in _AV_ACCENTED
               for unit in _avestan_units(form))


#: The letters read back: one phoneme per letter, with the aliases resolved to
#: the form the phonological stage writes (𐬬 is v, 𐬗 is c, 𐬘 is j, 𐬓 is xᵛ,
#: 𐬤 is ŋᵛ, 𐬅 is ą̇).  A letter the table does not own is kept as it stands, so
#: an unreadable sign never passes for a reading.
_AV_READ: dict[str, str] = {}
for _phoneme, _letter in {**_AV_VOWELS, **_AV_CONSONANTS}.items():
    if _letter in _AV_READ:
        continue
    if _phoneme in _AV_ALIASES:          # ą̄, xʷ, ŋʷ, w, č, ǰ: aliases, not letters
        continue
    _AV_READ[_letter] = _phoneme
_AV_READ["𐬅"] = "ą̇"
_AV_READ_EXTRA = {"\u2060": "", "⸱": "", "·": ""}


def avestan_reading(form: str) -> str:
    """Read an Avestan word back to phonemes, letter by letter.

    The Avestan record is written in an alphabet whose value for each letter is
    known (Hoffmann & Forssman 2004, pp. 44-46), so the word's own letters are
    its pronunciation: 𐬀𐬵𐬨𐬀 is *ahma*.  This is the reading the dictionary
    would print, and it is what the orthographic layer's guard compares a
    phonemic form against when a corpus carries no IPA of its own (2026-11-09:
    313 of the 352 Avestan entries have none, and the layer was therefore
    unable to confirm any of them).

    Reading back is *not* the inverse of :func:`avestan`: the writer spells a
    glide between vowels with the matching vowel doubled (𐬌𐬌 *ii*, 𐬎𐬎 *uu*),
    and the reader keeps both signs, so 𐬀𐬎𐬎𐬀 reads *auua* and never *ava*.
    A form the laws wrote with a glide is therefore still rejected unless the
    record really writes one letter for it.

    >>> avestan_reading("𐬀𐬵𐬨𐬀")
    'ahma'
    >>> avestan_reading("𐬀𐬎𐬎𐬀")
    'auua'
    """
    out: list[str] = []
    for ch in unicodedata.normalize("NFC", form or ""):
        if ch in _AV_READ_EXTRA:
            continue
        out.append(_AV_READ.get(ch, ch))
    return "".join(out)


def avestan_readable_word(form: str) -> bool:
    """Whether every letter of ``form`` is one the reading table owns."""
    return all(ch in _AV_READ or ch in _AV_READ_EXTRA
               for ch in unicodedata.normalize("NFC", form or ""))
