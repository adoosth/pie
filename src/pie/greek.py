"""Writing a Greek phonemic form with the letters of the Greek alphabet.

The last sound-law stage of a Greek word leaves a phonemic string
(``patˈēr``, ``hˈippos``, ``kʰˈōra``); a dictionary writes πατήρ, ἵππος, χώρα.
Nothing about the sounds changes in that step, so the step belongs to the
orthographic layer (``data/spelling/grc.yaml``), never to a sound law, and a
word reached through it is counted as *spelled*, not as reconstructed.

Greek is an alphabet, so most of the work is the letter table below.  Four
conventions are not one-to-one, and each is written here as the rule a scribe
follows rather than as a rewrite of the form:

* the **breathing** (ψιλή / δασεῖα): every vowel-initial word carries one, a
  written /h/ *is* the rough breathing of the vowel it precedes, an initial ρ
  always takes the rough breathing, and over a diphthong the breathing stands
  on the second vowel (Smyth 1920, §§9-10);
* the **acute** (ὀξεῖα) on the stressed syllable, which the engine marks with
  its own ``ˈ`` token: on the second letter of a diphthong, on the vowel
  otherwise (Smyth 1920, §149);
* the **final sigma** ς (Smyth 1920, §3);
* the three **double letters** ξ ψ ζ, written for /ks ps zd/ (Smyth 1920, §1),
  and γ for a nasal before a velar (γγ γκ γχ are /ŋg ŋk ŋkʰ/, Smyth §1).

A circumflex or a grave is a different accent, not a different way of writing
the acute: the accent the laws place is the acute, and a headword with a
circumflex is left a miss rather than guessed (Smyth 1920, §149).  No letter
is invented for notation the table does not own: a surviving laryngeal, an
unresolved glide, an alternative separated by ``~`` stays in the string, so a
wrong spelling is visible as wrong.

The letters stand for the sounds Allen, *Vox Graeca* (3rd ed. 1987), gives
them; that is what lets the reading guard accept the spelling as a reading of
the dictionary's own IPA.
"""
from __future__ import annotations

import unicodedata

#: Combining marks, in the order they are written (breathing, then accent).
SMOOTH = "\u0313"     # ψιλή, smooth breathing
ROUGH = "\u0314"      # δασεῖα, rough breathing
ACUTE = "\u0301"      # ὀξεῖα

#: One letter per phoneme (Smyth §1; the sounds are Allen's).
_VOWELS = {
    "a": "α", "ā": "α", "e": "ε", "ē": "η", "i": "ι", "ī": "ι",
    "o": "ο", "ō": "ω", "u": "υ", "ū": "υ",
}
_CONSONANTS = {
    "p": "π", "b": "β", "t": "τ", "d": "δ", "k": "κ", "g": "γ",
    "tʰ": "θ", "pʰ": "φ", "kʰ": "χ", "m": "μ", "n": "ν", "r": "ρ",
    "l": "λ", "s": "σ", "z": "ζ", "w": "ϝ", "ŋ": "γ",
}
#: A syllabic resonant is notation the alphabet has no letter for.  It is
#: written as the plain resonant, which is *not* a claim that Greek had a
#: syllabic consonant: the form keeps the notation and the spelling will not
#: match an attested word unless the letters happen to be right.
_SYLLABIC = {"r̥": "ρ", "l̥": "λ", "m̥": "μ", "n̥": "ν"}

_UNITS = sorted(set(_VOWELS) | set(_CONSONANTS) | set(_SYLLABIC),
                key=len, reverse=True)

#: The diphthongs the alphabet writes with two letters (Smyth §7).
_DIPHTHONGS = {("a", "i"), ("e", "i"), ("o", "i"), ("u", "i"),
               ("a", "u"), ("e", "u"), ("o", "u"), ("ē", "u")}


def _units(form: str) -> list[str]:
    """Split a phonemic form into the units the alphabet writes."""
    text = unicodedata.normalize("NFC", form or "")
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


def _compose(base: str, marks: list[str]) -> str:
    return unicodedata.normalize("NFC", base + "".join(marks))


def write(form: str) -> str:
    """Write a phonemic form in the Greek alphabet.

    >>> write("patˈēr")
    'πατήρ'
    >>> write("hˈippos")
    'ἵππος'
    >>> write("polˈus")
    'πολύς'
    >>> write("tunkʰˈanō")
    'τυγχάνω'
    """
    raw = _units(form)
    stress_at = None
    letters: list[list] = []          # [source index, letter, kind, phoneme]
    for i, unit in enumerate(raw):
        if unit in {"ˈ", "ˌ"}:
            stress_at = i + 1
            continue
        if unit in _VOWELS:
            letters.append([i, _VOWELS[unit], "v", unit])
        elif unit in _CONSONANTS:
            letters.append([i, _CONSONANTS[unit], "c", unit])
        elif unit in _SYLLABIC:
            letters.append([i, _SYLLABIC[unit], "c", unit])
        else:
            letters.append([i, unit, "x", unit])

    # ξ ψ ζ: one sign for two letters (Smyth §1).
    merged: list[list] = []
    j = 0
    while j < len(letters):
        cur = letters[j]
        nxt = letters[j + 1] if j + 1 < len(letters) else None
        pair = (cur[3], nxt[3]) if nxt and cur[2] == "c" and nxt[2] == "c" else None
        if pair == ("k", "s"):
            merged.append([cur[0], "ξ", "c", "ks"])
            j += 2
            continue
        if pair == ("p", "s"):
            merged.append([cur[0], "ψ", "c", "ps"])
            j += 2
            continue
        if pair in (("z", "d"), ("d", "z")):
            merged.append([cur[0], "ζ", "c", "zd"])
            j += 2
            continue
        merged.append(cur)
        j += 1
    letters = merged

    # A nasal before a velar is written γ (Smyth §1).
    for k, (_, _, kind, phon) in enumerate(letters):
        if kind == "c" and phon in {"n", "ŋ"} and k + 1 < len(letters):
            if letters[k + 1][3] in {"k", "g", "kʰ", "ξ"}:
                letters[k][1] = "γ"

    # The vowel letters, grouped into nuclei: a diphthong is one nucleus.
    groups: list[list[int]] = []
    for k, (_, _, kind, phon) in enumerate(letters):
        if kind != "v":
            continue
        if groups and groups[-1][-1] + 1 == k and \
                (letters[groups[-1][-1]][3], phon) in _DIPHTHONGS:
            groups[-1].append(k)
        else:
            groups.append([k])

    def nucleus_of(index: int) -> list[int] | None:
        for group in groups:
            if group[0] <= index <= group[-1]:
                return group
        return None

    marks: dict[int, list[str]] = {}
    dropped: set[int] = set()

    def mark(k: int, what: str) -> None:
        marks.setdefault(k, []).append(what)

    # The breathing (Smyth §§9-10).
    if letters:
        first = letters[0]
        if first[3] == "h":
            # /h/ is not a letter: it is the rough breathing of the vowel it
            # precedes (or of an initial ρ, Smyth §10).  Before anything else
            # it stays in the string, where it can never pass as a spelling.
            if len(letters) > 1 and (letters[1][2] == "v" or letters[1][3] in {"r", "r̥"}):
                dropped.add(0)
                group = nucleus_of(1)
                mark(group[-1] if group else 1, ROUGH)
        elif first[3] in {"r", "r̥"}:
            mark(0, ROUGH)
        elif first[2] == "v":
            group = nucleus_of(0)
            mark(group[-1] if group else 0, SMOOTH)

    # The acute on the stressed nucleus (Smyth §149).
    if stress_at is not None:
        seat = next((k for k, row in enumerate(letters) if row[0] == stress_at), None)
        if seat is not None and letters[seat][2] != "v":
            seat = next((k for k in range(seat, len(letters)) if letters[k][2] == "v"), None)
        if seat is not None:
            group = nucleus_of(seat) or [seat]
            if len(group) > 1:
                mark(group[-1], ACUTE)
            else:
                mark(group[0], ACUTE)

    # The final sigma (Smyth §3).
    for k, row in enumerate(letters):
        if row[3] == "s" and k == len(letters) - 1:
            row[1] = "ς"

    out: list[str] = []
    for k, (_, base, _, _) in enumerate(letters):
        if k in dropped:
            continue
        here = marks.get(k) or []
        out.append(_compose(base, here) if here and base else base)
    return unicodedata.normalize("NFC", "".join(out))
