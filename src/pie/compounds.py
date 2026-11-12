"""Formations from two or three words of the same language.

A word the dictionary gives no etymology for is not therefore a blank.  If the
written word can be cut into two or three stored headwords of the same language,
the model may say that it was *built* from them.  That is a formation — a fact
about the shape and the words, not a sound law and not a proposed ancestry — and
this module keeps the two apart in every result it returns.

The tests are deliberately strict, because a wrong claim of structure is as bad
as a wrong etymology:

* the cut is made on the exact characters.  Persian آ (U+0622) and ا (U+0627)
  are different letters, and آب "water" is not اب "father"; nothing is
  normalised, transliterated or joined.  A zero-width non-joiner is a character
  like any other, so a headword written with one can only be cut where the
  stored strings themselves agree.
* every piece must be a known headword of the same language, long enough to be
  an element rather than a seam, and not a function word.
* a short piece is accepted only when `short_ok` names that exact spelling.
* `stop` is for the short, frequent words that make false seams (اب "father"
  beside آب "water").
* at least one piece must have a recorded origin: two words with no origin
  explain nothing about a third.
* a two-piece cut always wins.  A three-piece cut is tried only when no
  two-piece cut passes.
* if more than one cut passes at the winning size, the answer is *ambiguous*:
  every cut is returned and the caller must not assign a coverage band.  There
  is no score and no tie-break, because a tie means the model does not know.

`rules` is the parsed contents of `data/compounds/fa.yaml`.  The module does no
I/O and keeps no cache: the same word and the same lookup always give the same
answer.
"""

from __future__ import annotations

#: The POS codes a function word can carry.  `data/compounds/fa.yaml` repeats
#: this list; the default is here so an incomplete rules dict still refuses to
#: call a preposition a compound element.
FUNCTION_POS = frozenset({
    "prep", "postp", "conj", "pron", "det", "part", "interj", "num", "adv",
})


def analyse(word: str, lookup, *, rules: dict) -> dict | None:
    """Show ``word`` as built from two or three stored words, or return ``None``.

    ``lookup(form)`` returns ``{"known": bool, "recorded": bool, "pos": str |
    None}`` for a headword of the same language, or ``None`` when the form is
    not stored.  ``recorded`` means the entry states an ancestry or etymology at
    all; it is not a claim that the etymology is correct.

    The result is ``{"word", "parts", "verdict", "alternatives", "reason"}``.
    ``verdict`` is ``"unique"`` when exactly one cut passes and ``"ambiguous"``
    when several do.  For an ambiguous word ``parts`` is the first candidate,
    ``alternatives`` repeats every candidate, and ``reason`` says that no band
    may be assigned.  Callers must check ``verdict`` before using ``parts`` as a
    decision, not merely as one of the possibilities.
    """
    candidates = split_candidates(word, lookup, rules=rules)
    if not candidates:
        return None

    if len(candidates) == 1:
        parts = candidates[0]
        return {
            "word": word,
            "parts": list(parts),
            "verdict": "unique",
            "alternatives": [],
            "reason": _unique_reason(parts),
        }

    return {
        "word": word,
        "parts": list(candidates[0]),
        "verdict": "ambiguous",
        "alternatives": [list(parts) for parts in candidates],
        "reason": _ambiguous_reason(candidates),
    }


def split_candidates(word: str, lookup, *, rules) -> list[list[str]]:
    """Every cut of ``word`` that passes the tests, ordered by part count.

    A two-part cut suppresses all three-part cuts: the three-part pass is only
    made when the two-part pass found nothing.  Within one part count the cuts
    come left to right by their first seam, which is deterministic but is not a
    ranking — when several cuts survive they are all genuinely possible.
    """
    settings = _settings(rules)
    if len(word) < settings["min_word"]:
        return []

    for size in (2, 3):
        # A zero-width non-joiner is the writer's own seam: گوشت‌پلو is written
        # as two words held together, so that cut is tried before any cut the
        # model would have to invent (2026-11-10).
        passing = [
            parts for parts in list(_zwnj_shapes(word, size)) + list(_shapes(word, size))
            if _passes(parts, word, lookup, settings)
        ]
        if passing:
            return passing
    return []


def seam_note(entry: dict) -> str:
    """How to name a seam beside the dictionary's own label for the word.

    The note is the provenance of a `built` row: `as the record states` when a
    dictionary's construction template named the pieces, and otherwise this
    model's cut — which reads differently when the same dictionary prints a
    grammar label saying the word *is* a compound or a relative adjective
    (`data/dehkhoda/structure.jsonl.gz`, 2026-11-10).  The label never picks
    the cut; it only lets the note say what the dictionary already claimed.
    """
    says = entry.get("structure") or {}
    for flag, what in (("compound", "a compound"),
                       ("relational", "a relative adjective"),
                       ("diminutive", "a diminutive")):
        if says.get(flag):
            return f"the model's cut of a word the dictionary prints as {what}"
    return "the seam this model reads, which the record does not name"


def describe(result, lang_label="Persian") -> str:
    """One plain sentence for the word page, with the Persian forms inline.

    The sentence says what kind of claim this is.  A formation is built from
    words, not derived by sound laws, and the whole word still has no recorded
    etymology.  For an ambiguous result it names every candidate cut and says
    that the model will not choose between them.
    """
    if not result:
        return ("No clean formation could be shown from stored words of the "
                "language.")

    word = str(result.get("word") or "")
    alternatives = [
        list(parts) for parts in (result.get("alternatives") or []) if parts
    ]
    if result.get("verdict") == "ambiguous" or len(alternatives) > 1:
        splits = alternatives or [list(result.get("parts") or [])]
        named = " or ".join(
            " + ".join(str(part) for part in parts)
            for parts in splits if parts
        )
        return (
            f"{word} has {len(splits)} candidate splits — {named} — so it is "
            f"left unclassified; built in {lang_label} from its own words, a "
            "formation, not a derivation. The dictionary records no etymology "
            "for it."
        )

    parts = [str(part) for part in (result.get("parts") or [])]
    named = " + ".join(parts)
    from_word = _number_word(len(parts))
    return (
        f"{named} → {word}, built in {lang_label} from {from_word} of its own "
        "words; a formation, not a derivation. The dictionary records no "
        "etymology for it."
    )


def _number_word(count: int) -> str:
    return {2: "two", 3: "three"}.get(count, str(count))


def _string_set(value) -> set[str]:
    """Exact strings from a YAML list (or one scalar), with no normalisation."""
    if not value:
        return set()
    if isinstance(value, str):
        return {value}
    return {item for item in value if isinstance(item, str)}


def _rule_int(rules: dict, key: str, default: int) -> int:
    value = rules.get(key, default)
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 1 else default


def _settings(rules: dict) -> dict:
    return {
        "min_part": _rule_int(rules, "min_part", 2),
        "min_word": _rule_int(rules, "min_word", 4),
        "long_part": _rule_int(rules, "long_part", 3),
        "short_ok": _string_set(rules.get("short_ok")),
        "function_words": _string_set(rules.get("function_words")),
        "function_pos": _string_set(rules.get("function_pos", FUNCTION_POS)),
        "stop": _string_set(rules.get("stop")),
        "heads": _string_set(rules.get("heads")),
    }


def _shapes(word: str, size: int):
    """Candidate cuts of ``word`` into ``size`` non-empty exact substrings."""
    if size == 2:
        for first in range(1, len(word)):
            yield [word[:first], word[first:]]
    elif size == 3:
        for first in range(1, len(word) - 1):
            for second in range(first + 1, len(word)):
                yield [word[:first], word[first:second], word[second:]]


def _zwnj_shapes(word: str, size: int):
    """Cuts made exactly where the word is already written with a ZWNJ.

    The non-joiner is dropped, because it is a joining convention and not a
    letter: the pieces it separates are the words as the glossary heads them.
    """
    cuts = [i for i, ch in enumerate(word) if ch == "\u200c"]
    if size == 2:
        for i in cuts:
            yield [word[:i], word[i + 1:]]
    elif size == 3:
        for a, i in enumerate(cuts):
            for j in cuts[a + 1:]:
                yield [word[:i], word[i + 1:j], word[j + 1:]]


def _passes(parts: list[str], word: str, lookup, settings: dict) -> bool:
    """Do all the acceptance tests hold for this exact cut?"""
    if len(parts) < 2 or len(parts) > 3:
        return False
    if len(word) < settings["min_word"]:
        return False
    if any(part == word for part in parts):
        return False

    infos: dict[str, dict] = {}
    for part in parts:
        if not part:
            return False
        if len(part) < settings["min_part"]:
            return False
        if len(part) < settings["long_part"] and part not in settings["short_ok"]:
            return False
        if part in settings["function_words"] or part in settings["stop"]:
            return False

        if part not in infos:
            info = lookup(part)
            infos[part] = info if isinstance(info, dict) else {}
        info = infos[part]
        if not info.get("known"):
            return False
        pos = info.get("pos")
        if pos is not None and str(pos) in settings["function_pos"]:
            return False

    # A curated list of heads turns a general cut into a morphological claim:
    # Persian builds words with a known set of second elements (خانه، گاه، یاب،
    # سازی), and a cut whose second element is not one of them is a guess about
    # a seam rather than a fact about the language.  When the list is empty the
    # rule is off (2026-11-10).
    if settings["heads"] and parts[-1] not in settings["heads"]:
        return False

    return any(bool(info.get("recorded")) for info in infos.values())


def _unique_reason(parts: list[str]) -> str:
    named = " + ".join(parts)
    return (
        f"the only split that passes the tests is {named}; at least one part "
        "has a recorded origin, and the whole is a formation, not a "
        "derivation by sound laws"
    )


def _ambiguous_reason(candidates: list[list[str]]) -> str:
    named = "; ".join(" + ".join(parts) for parts in candidates)
    return (
        f"{len(candidates)} splits pass the tests ({named}); the model will "
        "not choose between them, and an ambiguous formation must not be given "
        "a band"
    )
