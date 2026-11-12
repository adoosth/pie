"""Automatic romanisation of a headword the dictionary does not read for us.

The word page promises that a form written in another script is never shown
bare (2026-11-08): IPA when the dictionary records it, its romanisation when a
dictionary or a neighbouring etymology records one, and otherwise a
*transliteration the script itself supplies*.  This module is that last layer:
it turns the letters of a headword into Latin letters by the script's own
values, and it says plainly that it did so, so the interface can print the
automatic reading in its own colour.

Two kinds of writing are handled differently, and the difference is stated:

* an **alphabet** (Greek, Gothic, Cyrillic, Armenian, Avestan …) is read letter
  by letter — ``Πέρσης`` is *Pérsēs*, ``𐌻𐌹𐌿𐌸𐍃`` is *liuþs*;
* a **syllabary or abugida** (Old Persian, Hittite cuneiform, Devanagari,
  Cypriot) is read sign by sign, and a syllable sign before another sign
  carries its consonant alone, exactly as an edition prints it: Old Persian
  𐎱𐎠𐎼𐎿 is *p-a-r-s*, cuneiform 𒄀𒈠𒀭 is *gi-ma-an*.

Nothing here claims a pronunciation: the vowels an abjad leaves out stay out
(Persian درجه حرارت is *drjh ḥrrt*), no length is invented, and a character the
tables do not know is kept as it is instead of being guessed.  A dictionary's
own reading always wins over this.
"""
from __future__ import annotations

import re
import unicodedata

#: What each script is called in the interface, keyed by the Unicode name
#: prefix its letters carry.
_LABELS = {
    "GREEK": "Greek alphabet",
    "CYPRIOT": "Cypriot syllabary",
    "GOTHIC": "Gothic alphabet",
    "AVESTAN": "Avestan alphabet",
    "ARMENIAN": "Armenian alphabet",
    "CYRILLIC": "Cyrillic",
    "GLAGOLITIC": "Glagolitic",
    "ARABIC": "Perso-Arabic",
    "DEVANAGARI": "Devanagari",
    "BRAHMI": "Brahmi",
    "CUNEIFORM": "cuneiform",
    "MANICHAEAN": "Manichaean",
    "RUNIC": "runes",
    "OLD": "Old Persian cuneiform",
}


def _name(ch: str) -> str:
    return unicodedata.name(ch, "")


def is_scripted(word: str) -> bool:
    """Whether a form is *written in* a script other than the Latin alphabet.

    A letter whose Unicode name starts with ``LATIN`` (``ā``, ``ṣ``, ``ñ``) or
    that is a modifier (``ʰ``) is Latin: the word already *is* a romanisation,
    and a second one beside it would only be noise.

    The test is about which writing the word uses, not about one odd letter:
    a Slavicist transliteration with a soft sign (``-akъ``) or a Persian name
    with one theta (``Ciθrafarnāh``) is written in Latin letters, so it needs
    no reading.  A word counts as scripted when non-Latin letters are at least
    half of its letters (2026-11-08).
    """
    latin = other = 0
    for ch in word or "":
        if not unicodedata.category(ch).startswith("L"):
            continue
        name = _name(ch)
        if not name or name.startswith("LATIN") or name.startswith("MODIFIER"):
            latin += 1
        elif name.split(" ")[0] in {"COMBINING", "FULLWIDTH"}:
            continue
        else:
            other += 1
    return other > 0 and other >= latin


def script_name(word: str) -> str:
    """The script a headword is written in, by its first non-Latin letter."""
    for ch in word or "":
        if not unicodedata.category(ch).startswith("L"):
            continue
        name = _name(ch)
        if not name or name.startswith("LATIN") or name.startswith("MODIFIER"):
            continue
        prefix = name.split(" ")[0]
        return _LABELS.get(prefix, prefix.lower())
    return ""


# --------------------------------------------------------------------------
# alphabets
# --------------------------------------------------------------------------

GREEK = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
    "φ": "ph", "χ": "kh", "ψ": "ps", "ω": "ō", "ϝ": "w", "ϙ": "q", "ϳ": "j",
}
#: Combining marks of the polytonic orthography, and what a romanisation does
#: with them.  A rough breathing becomes an *h* before the letter (ῥ → *rh*),
#: a smooth one is dropped, an iota subscript is written after the vowel, and
#: an accent stays on the Latin vowel it stood on.
_GREEK_MARKS = {
    "\u0301": "acute", "\u0300": "grave", "\u0342": "circumflex",
    "\u0308": "diaeresis", "\u0314": "rough", "\u0313": "smooth",
    "\u0345": "iota", "\u0304": "macron", "\u0306": "breve",
}
_ACCENT = {"acute": "\u0301", "grave": "\u0300", "circumflex": "\u0302",
           "diaeresis": "\u0308", "macron": "\u0304", "breve": "\u0306"}


def _greek(word: str) -> str:
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch):
            mark = _GREEK_MARKS.get(ch)
            if mark == "rough":
                # ῥ is rh, not hr: the breathing belongs to the rho.
                out.insert(len(out) - 1 if out else 0, "h")
            elif mark == "iota":
                out.append("i")
            elif mark in _ACCENT:
                for i in range(len(out) - 1, -1, -1):
                    if out[i][:1].lower() in "aeiouy":
                        out[i] = out[i] + _ACCENT[mark]
                        break
            continue
        base = ch.lower()
        if base in GREEK:
            latin = GREEK[base]
            if ch.isupper():
                latin = latin[:1].upper() + latin[1:]
            out.append(latin)
        else:
            out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "ë",
    "ж": "ž", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "c", "ч": "č", "ш": "š", "щ": "šč", "ъ": "ʺ",
    "ы": "y", "ь": "ʹ", "э": "è", "ю": "ju", "я": "ja", "ѣ": "ě", "ѧ": "ę",
    "ѩ": "ję", "ѫ": "ǫ", "ѭ": "jǫ", "ѥ": "je", "ї": "ji", "є": "je",
    "ѕ": "dz", "ѱ": "ps", "ѳ": "f", "ѵ": "y", "ѯ": "ks", "ѡ": "ō",
    "Ꙁ": "z", "ꙃ": "dz", "ꙉ": "dž", "ꙑ": "y", "ꙗ": "ja", "і": "i",
}
GLAGOLITIC = {
    "азъ": "a", "ⰰ": "a", "ⰱ": "b", "ⰲ": "v", "ⰳ": "g", "ⰴ": "d", "ⰵ": "e",
    "ⰶ": "ž", "ⰷ": "dz", "ⰸ": "z", "ⰹ": "i", "ⰺ": "i", "ⰻ": "i", "ⰼ": "đ",
    "ⰽ": "k", "ⰾ": "l", "ⰿ": "m", "ⱀ": "n", "ⱁ": "o", "ⱂ": "p", "ⱃ": "r",
    "ⱄ": "s", "ⱅ": "t", "ⱆ": "u", "ⱇ": "f", "ⱈ": "x", "ⱉ": "ō", "ⱊ": "št",
    "ⱋ": "c", "ⱌ": "č", "ⱍ": "dž", "ⱎ": "š", "ⱏ": "ʺ", "ⱐ": "ʹ",
    "ⱑ": "ě", "ⱒ": "ę", "ⱓ": "ju", "ⱔ": "ę", "ⱕ": "ǫ", "ⱖ": "jo",
    "ⱗ": "jǫ", "ⱘ": "ǫ", "ⱙ": "jǫ", "ⱚ": "θ", "ⱛ": "i", "ⱜ": "i",
}
ARMENIAN = {
    "ա": "a", "բ": "b", "գ": "g", "դ": "d", "ե": "e", "զ": "z", "է": "ē",
    "ը": "ə", "թ": "tʿ", "ժ": "ž", "ի": "i", "լ": "l", "խ": "x", "ծ": "c",
    "կ": "k", "հ": "h", "ձ": "j", "ղ": "ł", "ճ": "č", "մ": "m", "յ": "y",
    "ն": "n", "շ": "š", "ո": "o", "չ": "čʿ", "պ": "p", "ջ": "ǰ", "ռ": "ṙ",
    "ս": "s", "վ": "v", "տ": "t", "ր": "r", "ց": "cʿ", "ւ": "w",
    "փ": "pʿ", "ք": "kʿ", "օ": "ō", "ֆ": "f", "և": "ew",
}
GOTHIC = {
    "𐌰": "a", "𐌱": "b", "𐌲": "g", "𐌳": "d", "𐌴": "e", "𐌵": "q",
    "𐌶": "z", "𐌷": "h", "𐌸": "þ", "𐌹": "i", "𐌺": "k", "𐌻": "l",
    "𐌼": "m", "𐌽": "n", "𐌾": "j", "𐌿": "u", "𐍀": "p", "𐍁": "q",
    "𐍂": "r", "𐍃": "s", "𐍄": "t", "𐍅": "w", "𐍆": "f", "𐍇": "x",
    "𐍈": "ƕ", "𐍉": "o", "𐍊": "þ",
}
#: The alphabet's letters, transcribed as Hoffmann & Forssman (2004, pp. 44-46)
#: transcribe them.  Each letter keeps its own value: the four nasal vowels are
#: å (𐬂), ā̊ (𐬃), ą (𐬄) and ą̇ (𐬅), and 𐬓 is xᵛ, not a second sign for x́
#: (2026-11-09: the table used to read 𐬓, 𐬕, 𐬂, 𐬃, 𐬅, 𐬧 and 𐬪 as another
#: letter's value, so a word written with them was read as one it is not).
AVESTAN = {
    "𐬀": "a", "𐬁": "ā", "𐬂": "å", "𐬃": "ā̊", "𐬄": "ą", "𐬅": "ą̇",
    "𐬆": "ə", "𐬇": "ə̄", "𐬈": "e", "𐬉": "ē", "𐬊": "o", "𐬋": "ō",
    "𐬌": "i", "𐬍": "ī", "𐬎": "u", "𐬏": "ū", "𐬐": "k", "𐬑": "x",
    "𐬒": "x́", "𐬓": "xᵛ", "𐬔": "g", "𐬕": "ġ", "𐬖": "γ", "𐬗": "c",
    "𐬘": "j", "𐬙": "t", "𐬚": "θ", "𐬛": "d", "𐬜": "δ", "𐬝": "t̰",
    "𐬞": "p", "𐬟": "f", "𐬠": "b", "𐬡": "β", "𐬢": "ŋ", "𐬣": "ŋ́",
    "𐬤": "ŋᵛ", "𐬥": "n", "𐬦": "ń", "𐬧": "ṇ", "𐬨": "m", "𐬩": "m̨",
    "𐬪": "ẏ", "𐬫": "y", "𐬬": "v", "𐬭": "r", "𐬮": "l", "𐬯": "s",
    "𐬰": "z", "𐬱": "š", "𐬲": "ž", "𐬳": "š́", "𐬴": "ṣ̌", "𐬵": "h",
}
RUNIC = {
    "ᚠ": "f", "ᚢ": "u", "ᚦ": "þ", "ᚨ": "a", "ᚱ": "r", "ᚲ": "k", "ᚴ": "k",
    "ᚷ": "g", "ᚹ": "w", "ᛁ": "i", "ᛅ": "æ", "ᛈ": "p", "ᛋ": "s", "ᛏ": "t",
    "ᛒ": "b", "ᛖ": "e", "ᛚ": "l", "ᛡ": "j", "ᛦ": "ʀ",
}
MANICHAEAN = {
    "𐫀": "ʾ", "𐫁": "b", "𐫂": "β", "𐫃": "g", "𐫄": "γ", "𐫅": "d",
    "𐫆": "h", "𐫇": "w", "𐫈": "z", "𐫉": "ž", "𐫊": "ḥ", "𐫋": "ṭ",
    "𐫌": "y", "𐫍": "k", "𐫎": "x", "𐫏": "y", "𐫐": "k", "𐫑": "l",
    "𐫒": "m", "𐫓": "n", "𐫔": "s", "𐫕": "ʿ", "𐫖": "p", "𐫗": "f",
    "𐫘": "s", "𐫙": "ṣ", "𐫚": "q", "𐫛": "r", "𐫜": "š", "𐫝": "t",
    "𐫞": "θ", "𐫟": "x", "𐫠": "h", "𐫡": "r", "𐫢": "š", "𐫣": "t",
    "𐫤": "t", "𐫥": "p", "𐫦": "s",
}
ARABIC = {
    "ء": "ʾ", "آ": "ā", "أ": "ʾa", "إ": "ʾi", "ؤ": "ʾu", "ئ": "ʾi",
    "ا": "ā", "ب": "b", "پ": "p", "ت": "t", "ث": "θ", "ج": "j", "چ": "č",
    "ح": "ḥ", "خ": "x", "د": "d", "ذ": "δ", "ر": "r", "ز": "z", "ژ": "ž",
    "س": "s", "ش": "š", "ص": "ṣ", "ض": "ż", "ط": "ṭ", "ظ": "ẓ", "ع": "ʿ",
    "غ": "ġ", "ف": "f", "ق": "q", "ك": "k", "ک": "k", "گ": "g", "ل": "l",
    "م": "m", "ن": "n", "ه": "h", "ة": "t", "و": "w", "ی": "y", "ي": "y",
    "ى": "ā", "ٹ": "ṭ", "ڈ": "ḍ", "ڑ": "ṛ", "ں": "n", "ہ": "h", "ھ": "h",
}

_ALPHABETS = {
    "GREEK": GREEK, "CYRILLIC": CYRILLIC, "GLAGOLITIC": GLAGOLITIC,
    "ARMENIAN": ARMENIAN, "GOTHIC": GOTHIC, "AVESTAN": AVESTAN,
    "RUNIC": RUNIC, "MANICHAEAN": MANICHAEAN, "ARABIC": ARABIC,
}


#: Digraphs that are one sound in the script's own orthography.
_DIGRAPHS = {"ու": "u", "Ու": "U", "ՈՒ": "U"}


def _alphabet(word: str, table: dict[str, str], prefix: str) -> str:
    if prefix == "ARMENIAN":
        for pair, value in _DIGRAPHS.items():
            word = word.replace(pair, value)
    out = []
    for ch in word:
        key = ch if ch in table else ch.lower()
        latin = table.get(key)
        if latin is None and prefix == "CYRILLIC":
            latin = CYRILLIC.get(ch.lower())
        if latin is None:
            out.append(ch)
            continue
        if ch.isupper() and prefix in {"CYRILLIC", "ARMENIAN"}:
            latin = latin[:1].upper() + latin[1:]
        out.append(latin)
    return "".join(out)


# --------------------------------------------------------------------------
# Devanagari and Brahmi: an abugida writes a consonant with an inherent *a*
# --------------------------------------------------------------------------

_DEVA_CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ṅ", "च": "c", "छ": "ch",
    "ज": "j", "झ": "jh", "ञ": "ñ", "ट": "ṭ", "ठ": "ṭh", "ड": "ḍ", "ढ": "ḍh",
    "ण": "ṇ", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p",
    "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l",
    "ळ": "ḷ", "व": "v", "श": "ś", "ष": "ṣ", "स": "s", "ह": "h",
}
_DEVA_VOWEL = {
    "अ": "a", "आ": "ā", "इ": "i", "ई": "ī", "उ": "u", "ऊ": "ū", "ऋ": "r̥",
    "ॠ": "r̥̄", "ऌ": "l̥", "ॡ": "l̥̄", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "ॐ": "oṃ",
}
_DEVA_SIGN = {
    "ा": "ā", "ि": "i", "ी": "ī", "ु": "u", "ू": "ū", "ृ": "r̥", "ॄ": "r̥̄",
    "ॢ": "l̥", "ॣ": "l̥̄", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "ṃ", "ः": "ḥ", "ँ": "m̐", "ऽ": "ʼ",
}
_DEVA_VIRAMA = "्"


def _abugida(word: str, cons: dict[str, str], vowels: dict[str, str],
              marks: dict[str, str], virama: str) -> str:
    out: list[str] = []
    pending: str | None = None
    for ch in word:
        if ch in cons:
            if pending is not None:
                # A consonant before another keeps its inherent vowel: पशु is
                # pa-śu, not p-śu. Only the virama takes it away (2026-11-08).
                out.append(pending + "a")
            pending = cons[ch]
            continue
        if ch == virama:
            if pending is not None:
                out.append(pending)
                pending = None
            continue
        if ch in marks:
            if pending is not None:
                out.append(pending)
                pending = None
            out.append(marks[ch])
            continue
        if ch in vowels:
            if pending is not None:
                out.append(pending)
                pending = None
            out.append(vowels[ch])
            continue
        if pending is not None:
            out.append(pending + "a")
            pending = None
        out.append(ch)
    if pending is not None:
        out.append(pending + "a")
    return "".join(out)


#: Brahmi letters carry their value in the Unicode name (``BRAHMI LETTER KA``),
#: so the table is read from the name rather than copied by hand.
_BRAHMI_VOWELS = {"A": "a", "AA": "ā", "I": "i", "II": "ī", "U": "u", "UU": "ū",
                  "VOCALIC R": "r̥", "VOCALIC RR": "r̥̄", "E": "e", "AI": "ai",
                  "O": "o", "AU": "au"}
_BRAHMI_MARKS = {"AA": "ā", "I": "i", "II": "ī", "U": "u", "UU": "ū",
                 "VOCALIC R": "r̥", "E": "e", "AI": "ai", "O": "o", "AU": "au"}


def _brahmi(word: str) -> str:
    cons: dict[str, str] = {}
    vowels: dict[str, str] = {}
    marks: dict[str, str] = {}
    virama = ""
    for ch in word:
        name = _name(ch)
        if not name.startswith("BRAHMI"):
            continue
        if name.startswith("BRAHMI LETTER"):
            value = name[len("BRAHMI LETTER "):]
            if value in _BRAHMI_VOWELS:
                vowels[ch] = _BRAHMI_VOWELS[value]
            elif value == "KA":
                cons[ch] = "k"
            else:
                cons[ch] = value.lower()
        elif name.startswith("BRAHMI VOWEL SIGN"):
            value = name[len("BRAHMI VOWEL SIGN "):]
            marks[ch] = _BRAHMI_MARKS.get(value, value.lower())
        elif name == "BRAHMI SIGN VIRAMA":
            virama = ch
        elif name == "BRAHMI SIGN ANUSVARA":
            marks[ch] = "ṃ"
        elif name == "BRAHMI SIGN VISARGA":
            marks[ch] = "ḥ"
    if not (cons or vowels or marks):
        return ""
    return _abugida(word, cons, vowels, marks, virama)


# --------------------------------------------------------------------------
# syllabaries: Old Persian and Hittite cuneiform, Cypriot
# --------------------------------------------------------------------------

def _cuneiform(word: str) -> str:
    """Sign names as an edition transliterates them: ``gi-ma-an``."""
    out: list[str] = []
    for ch in word:
        name = _name(ch)
        if not name.startswith("CUNEIFORM"):
            out.append(ch)
            continue
        value = name.split(" SIGN ", 1)[-1].split(" NUMERIC SIGN ", 1)[-1]
        if value.startswith("SIGN "):
            value = value[len("SIGN "):]
        value = value.replace("TIMES", " × ").split(" × ")[0].strip().lower()
        value = value.replace("sh", "š")
        # A numbered sign is the same read value: GAN2 is gan₂.
        value = re.sub(r"2$", "₂", value)
        value = re.sub(r"3$", "₃", value)
        out.append(value.replace(" ", "-") or ch)
    return "-".join(out)


def _cypriot(word: str) -> str:
    out = []
    for ch in word:
        name = _name(ch)
        if name.startswith("CYPRIOT SYLLABLE"):
            out.append(name.split("SYLLABLE ")[-1].lower())
        else:
            out.append(ch)
    return "-".join(out)


# --------------------------------------------------------------------------
# the one entry point
# --------------------------------------------------------------------------

def transliterate(word: str) -> dict:
    """A romanisation the script itself gives, and the script it is from.

    ``{"reading": "Pérsēs", "script": "Greek alphabet", "automatic": True}``.
    The reading is letter-by-letter (or sign-by-sign) and never a claim about
    the sounds a word had; a character no table knows is kept as written.
    """
    text = (word or "").strip()
    if not text:
        return {"reading": "", "script": "", "automatic": False}
    first = next((ch for ch in text if unicodedata.category(ch).startswith("L")), "")
    prefix = _name(first).split(" ")[0] if first else ""
    label = _LABELS.get(prefix, prefix.lower())
    if prefix == "GREEK":
        return {"reading": _greek(text), "script": label, "automatic": True}
    if prefix in _ALPHABETS:
        return {"reading": _alphabet(text, _ALPHABETS[prefix], prefix),
                "script": label, "automatic": True}
    if prefix == "DEVANAGARI":
        return {"reading": _abugida(text, _DEVA_CONS, _DEVA_VOWEL, _DEVA_SIGN,
                                    _DEVA_VIRAMA),
                "script": label, "automatic": True}
    if prefix == "BRAHMI":
        out = _brahmi(text)
        if out:
            return {"reading": out, "script": label, "automatic": True}
    if prefix == "CUNEIFORM":
        return {"reading": _cuneiform(text), "script": label, "automatic": True}
    if prefix == "CYPRIOT":
        return {"reading": _cypriot(text), "script": label, "automatic": True}
    return {"reading": "", "script": label, "automatic": False}
