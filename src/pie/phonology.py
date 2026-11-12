"""Segment-level model of reconstructed and attested Indo-European forms.

Sound laws are rewrites over *segments*, not over raw strings: a form such as
``kʷʰel-`` is three segments (``kʷʰ``, ``e``, ``l``) and stress is a separate
prosodic token (``ˈ``).  Everything the rule engine does is expressed in these
terms, which makes contexts such as "voiceless stop before a resonant"
expressible without fragile regexes.
"""

from __future__ import annotations

import re
import unicodedata

# Multi-character segments, longest first.  Diphthongs are deliberately *not*
# merged: PIE *ai is a sequence of two vowel segments.
MULTI_SEGMENTS = sorted(
    {
        "gʷʰ", "kʷʰ", "kʷ", "gʷ", "ǵʰ", "ḱʰ", "dʰ", "bʰ", "gʰ", "pʰ", "tʰ", "kʰ",
        "h₁", "h₂", "h₃", "H₁", "H₂", "H₃", "xʷ", "ɣʷ", "kʷʰ", "gʷʰ",
        "i̯", "u̯",
    },
    key=len,
    reverse=True,
)

_MULTI_BY_FIRST: dict[str, list[str]] = {}
for _seg in MULTI_SEGMENTS:
    _MULTI_BY_FIRST.setdefault(_seg[0], []).append(_seg)

STRESS_TOKENS = {"ˈ", "ˌ"}

ACUTE = "\u0301"
MACRON = "\u0304"
RING_BELOW = "\u0325"
DOT_BELOW = "\u0323"
TILDE = "\u0303"
CIRCUMFLEX = "\u0302"
BREVE = "\u0306"
CARON = "\u030c"
DIAERESIS = "\u0308"

VOWEL_LETTERS = set("aeiouyəɛɔæœøɨɤɯɪʊɐɑɒɵʌ")


def _nfd(seg: str) -> str:
    return unicodedata.normalize("NFD", seg)


def letters(seg: str) -> str:
    """Latin letters of a segment, diacritics removed: ``ḱ`` → ``k``."""
    return "".join(c for c in _nfd(seg) if unicodedata.category(c) in {"Ll", "Lu"})


def marks(seg: str) -> set[str]:
    return {c for c in _nfd(seg) if unicodedata.combining(c)}


ALIASES = {"þ": "θ", "ð": "ð", "đ": "ð", "γ": "ɣ", "ƀ": "β", "ʋ": "w"}


def strip_form(text: str) -> str:
    text = unicodedata.normalize("NFC", text.strip())
    for a, b in ALIASES.items():
        text = text.replace(a, b)
    text = text.replace("*", "").replace("–", "-")
    text = re.sub(r"[\[\]{}()/<>]", "", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """Split a form into segments, keeping stress marks as separate tokens."""
    out: list[str] = []
    for chunk in strip_form(text).split():
        chunk = chunk.replace("-", "")
        i = 0
        while i < len(chunk):
            ch = chunk[i]
            if ch in STRESS_TOKENS:
                out.append(ch)
                i += 1
                continue
            if unicodedata.combining(ch) and out and out[-1] not in STRESS_TOKENS:
                out[-1] += ch
                i += 1
                continue
            for cand in _MULTI_BY_FIRST.get(ch, ()):
                if chunk.startswith(cand, i):
                    out.append(cand)
                    i += len(cand)
                    break
            else:
                out.append(ch)
                i += 1
    return _split_acute(out)


def _split_acute(tokens: list[str]) -> list[str]:
    """Turn accented vowels into a stress mark plus a plain vowel.

    ``é`` becomes ``ˈ e`` so that rules can talk about ``e`` while a rule about
    accent (Verner's law, pretonic reduction) can still see the stress.
    """
    out: list[str] = []
    for tok in tokens:
        if tok in STRESS_TOKENS:
            out.append(tok)
            continue
        let = letters(tok)
        syllabic = let in {"r", "l", "m", "n"} and (RING_BELOW in marks(tok) or DOT_BELOW in marks(tok))
        if let and (let[0] in VOWEL_LETTERS or syllabic) and ACUTE in marks(tok):
            plain = "".join(c for c in _nfd(tok) if c != ACUTE)
            out.append("ˈ")
            out.append(unicodedata.normalize("NFC", plain))
        else:
            out.append(tok)
    return out


def detokenize(tokens: list[str]) -> str:
    return unicodedata.normalize("NFC", "".join(tokens))


def is_long(seg: str) -> bool:
    return seg.endswith("ː") or MACRON in marks(seg)


def is_vowel(seg: str) -> bool:
    if seg in STRESS_TOKENS:
        return False
    let = letters(seg)
    if not let:
        return False
    if let[0] in VOWEL_LETTERS or let[0] == "r" and RING_BELOW in marks(seg):
        return True
    return RING_BELOW in marks(seg) or DOT_BELOW in marks(seg)


def is_syllabic_resonant(seg: str) -> bool:
    return letters(seg) in {"r", "l", "m", "n"} and (
        RING_BELOW in marks(seg) or DOT_BELOW in marks(seg)
    )


def tags(seg: str) -> frozenset[str]:
    """Phonological feature tags used by rule contexts."""
    if seg in STRESS_TOKENS:
        return frozenset({"STRESS"})
    let = letters(seg)
    mk = marks(seg)
    found: set[str] = set()

    if seg in {"i̯", "u̯"}:
        return frozenset({"GLIDE"})

    if is_vowel(seg) and not is_syllabic_resonant(seg):
        found.add("V")
        found.add("LONG" if is_long(seg) else "SHORT")
        if ACUTE in mk:
            found.add("ACC")
        if let and let[0] in "eiyæɛɪøœəɵ":
            found.add("VF")
        if let and let[0] in "aouɑɒɔʊʌ":
            found.add("VB")
        if let and let[0] in "iuɪʊy":
            found.add("HIGH")
        if let and let[0] in "aeæɑ":
            found.add("LOW")
        if let and let[0] in "ouɔɒøœy":
            found.add("ROUND")
        if let and let[0] in "aæɑ":
            found.add("VLOW")
        return frozenset(found)

    if is_syllabic_resonant(seg):
        found.add("V")
        found.add("SYL")
        found.add("SHORT")
        found.add("RES")
        if letters(seg) in {"m", "n"}:
            found.add("NAS")
        else:
            found.add("LIQ")
        return frozenset(found)

    # Wiktionary writes an unspecified laryngeal as a capital *H* (*priHós);
    # it is a laryngeal for every context a rule can ask about, even though the
    # letter is upper case (2026-11-08, reading Kroonen's PGmc laws).
    if let.lower() == "h" and (seg.endswith(("₁", "₂", "₃")) or seg.upper() in {"H", "H₁", "H₂", "H₃"}):
        found.add("LARYN")
    if seg in {"h₁", "h₂", "h₃", "H"} or let in {"ħ", "ʕ", "ʔ"}:
        found.add("LARYN")
    if let in {"j", "w", "y"} or seg in {"i̯", "u̯"}:
        found.add("GLIDE")
    if let in {"m", "n", "ŋ", "ɲ"}:
        found.add("NAS")
    if let in {"l", "r", "ɬ"}:
        found.add("LIQ")
    if found & {"NAS", "LIQ"}:
        found.add("RES")
    if let in {"s", "z"}:
        found.add("SIB")
    if let in {"f", "θ", "ð", "ɸ", "β", "ɣ", "x", "χ", "ç", "h", "v", "s", "z"}:
        found.add("FRIC")
    if let in {"p", "t", "k", "b", "d", "g", "ɟ", "ɖ", "ʈ", "q", "c"}:
        found.add("STOP")
        if let in {"p", "t", "k", "q", "c", "ʈ"}:
            found.add("PSTOP")
            found.add("VOICELESS")
        else:
            found.add("BSTOP")
            found.add("VOICED")
        if let in {"k", "g", "c", "ɟ"} and ACUTE in mk:
            found.add("PALATAL")
    if "ʰ" in seg:
        found.add("ASP")
    if let in {"p", "b", "ɸ", "β", "m", "f", "v"}:
        found.add("LAB")
    if let in {"t", "d", "θ", "ð", "n", "s", "z", "l", "r"}:
        found.add("DENT")
    if let in {"k", "g", "x", "ɣ", "ŋ"} and ACUTE not in mk and "ʷ" not in seg:
        found.add("VEL")
    if let in {"k", "g", "c"} and ACUTE in mk:
        found.add("PAL")
    if let in {"s", "z"} and ACUTE in mk:
        found.add("PAL")
    if seg.endswith("ʷ") or "ʷ" in seg:
        found.add("LABIOVEL")
    if let == "k" and ACUTE in mk:
        found.add("PAL")
    if let == "g" and ACUTE in mk:
        found.add("PAL")
    found.add("C")
    return frozenset(found)


def class_matches(name: str, seg: str) -> bool:
    """Match one segment against a named class (``V``, ``STOP``, ``!V``...)."""
    negate = name.startswith("!")
    if negate:
        name = name[1:]
    ok = name in tags(seg)
    return (not ok) if negate else ok
