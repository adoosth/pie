"""The six coverage categories, and the test for each.

The counter in `tools/coverage.py` answers one question — does a registered rule
chain turn a recorded ancestor into the attested form? — and reports the answer
as a dozen overlapping columns. That is a measurement, not a verdict: "exact but
only by switching a law off", "explained by the writing system" and "near miss"
all look alike to a reader who wants to know how much of the language the model
actually explains.

This module turns the facts the counter already establishes into one verdict per
word, with the colours set on 2026-11-09:

======================  ==========  ==========================================
category                colour      definition
======================  ==========  ==========================================
``full``                dark green  a PIE etymon recorded in the literature,
                                    derived by cited laws with no change of
                                    ours, reproducing the attested form exactly,
                                    from a chain the record itself states
``adjusted``            light green  the same, but at least one applied rule is an
                                    adjustment of ours that the project approved,
                                    with a report file for the law and one for
                                    the word
``partial``             yellow      a recorded chain from PIE that the engine
                                    does not reproduce exactly — the worklist
``unexplained``         red         no recorded etymology at all
``non_pie``             dark grey   recorded as coming from outside the family
                                    (Arabic into Persian, Turkic, Semitic …)
``unidentified``        light grey  not in the glossary yet; a number to be
                                    estimated per language, never counted
======================  ==========  ==========================================

One category sits beside the six rather than among them: ``ie_loan`` — a word
borrowed from *another* Indo-European language (French ``table`` in English).
It has a recorded origin, so it is not "unexplained", and its origin is inside
the family, so it is not "non-PIE"; but the model does not derive it either.
Counting it as a failure of the PIE model would be dishonest, and counting it as
explained would be worse, so it is reported separately and never in green.

A word explained only by a *writing* layer is `full` when the laws produce the
reading the script records and the script layer writes it (Old Persian 𐎺𐎼𐎣 is
`varkah` read sign by sign) — that is a documented convention, not a lookup. A
word that needed a per-word law switch, a formation from pieces, or an unchanged
form is not a law derivation and stays `partial` with that reason named.

The verdict is a pure function of facts the caller has already measured, so the
counter, the word page and any later report cannot disagree about a word.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

#: Ordered, because this is the order every table and bar chart uses.
CATEGORIES: dict[str, dict] = {
    "full": {
        "label": "fully explained",
        "colour": "#1b5e20",
        "short": "dark green",
        "definition": ("A recorded PIE etymon carried by cited laws to the attested "
                       "form, exactly, with every recorded intermediate matching."),
    },
    "adjusted": {
        "label": "fully explained, with adjustments",
        "colour": "#8bc34a",
        "short": "light green",
        "definition": ("The same, but a recorded intermediate disagrees, or one step is "
                       "an approved adjustment of ours."),
    },
    "partial": {
        "label": "partially explained",
        "colour": "#f2b705",
        "short": "yellow",
        "definition": ("A recorded chain that does not reach the word from the PIE "
                       "etymon: it starts lower, or the laws do not reproduce it."),
    },
    "unexplained": {
        "label": "unexplained",
        "colour": "#c62828",
        "short": "red",
        "definition": "No recorded etymology.",
    },
    "non_pie": {
        "label": "non-PIE",
        "colour": "#424242",
        "short": "dark grey",
        "definition": "Recorded as borrowed from outside the family.",
    },
    "unidentified": {
        "label": "unidentified",
        "colour": "#bdbdbd",
        "short": "light grey",
        "definition": "Not held yet; an estimate, never a counted word.",
    },
    "ie_loan": {
        "label": "loan from another IE language",
        "colour": "#78909c",
        "short": "blue grey",
        "definition": "Borrowed from a sister branch; recorded, not derived by this chain.",
        "extra": True,
    },
}

#: A word whose whole form no etymology explains but whose seam does.  It sits
#: beside the six like `ie_loan`: a formation is real knowledge about a word and
#: it is not a derivation, so it may never be green (2026-11-10).
def unexplained_reason(labels: dict | None) -> str:
    """Why a word with no recorded etymology has none — as far as it is known.

    ``labels`` is what the dictionary itself prints beside the headword
    (`entry["structure"]`, read by `tools/dehkhoda_structure.py`).  It cannot
    explain the word, but it can say what kind of word is unexplained, and
    that is the difference between a page that says "76,568 words have no
    etymology" and one that says most of them are names (2026-11-10).
    """
    says = labels or {}
    if says.get("name"):
        return "no recorded etymology (the dictionary labels it a proper name)"
    if says.get("huzvarish"):
        return "no recorded etymology (the dictionary labels it a huzvarish)"
    if says.get("compound"):
        return "no recorded etymology (a compound the model cannot cut)"
    if says.get("relational"):
        return ("no recorded etymology (a relative adjective whose stem is not stored)")
    if says.get("affix"):
        return "no recorded etymology (a bound morpheme, not a word)"
    return "no recorded etymology"


CATEGORIES["built"] = {
    "label": "built from its own words",
    "colour": "#8d6e63",
    "short": "brown",
    "definition": ("Made of the language's own words, or of one plus a suffix: a "
                   "formation, not a derivation."),
    "extra": True,
}

#: The six bands, in order, without the extra facets.
SIX = [key for key, meta in CATEGORIES.items() if not meta.get("extra")]

#: Rules whose tier means "this is our reasoning, not the literature's".
OUR_TIERS = frozenset({"custom", "proposed"})

#: Layers that write an already-derived reading, as opposed to deriving it.
WRITING_LAYERS = frozenset({"orthographic", "script"})

#: Layers that are a formation or a non-derivation; never a law explanation.
WEAK_LAYERS = frozenset({"identity", "joined", "bound", "citation"})


def step_row(stages) -> dict:
    """The verdict for a word whose recorded intermediate steps differ.

    A named list, so the page and the report can say *which* stages disagree
    ("Proto-Germanic, Proto-West Germanic") instead of "something differed".
    """
    named = ", ".join(str(s) for s in list(stages)[:4])
    more = "" if len(list(stages)) <= 4 else f" and {len(list(stages)) - 4} more"
    return {"category": "adjusted",
            "reason": f"recorded step differs: {named}{more}",
            "mismatched_steps": [str(s) for s in stages]}


def verdict(*, recorded: bool, non_ie: bool = False, ie_loan: bool = False,
            matched_by: str | None = None, tiers=(), approved: bool = False,
            pie_linked: bool = False, mismatched_steps=(),
            from_pie: bool = False, start_name: str = "",
            built_from=(), built_note: str = "") -> dict:
    """One word's category from the facts the counter measured.

    ``matched_by`` is the strongest thing that worked: ``laws`` (the derived form
    equals the attested form), ``pathway`` (a per-word law switch), or the layer
    that wrote it (``orthographic``, ``script``, ``citation``, ``identity``,
    ``joined``, ``bound``), or ``None`` when nothing did.

    ``tiers`` are the tiers of the rules that applied; ``approved`` says whether
    this word is listed in `data/adjusted.yaml` with its reports.

    ``from_pie`` says the winning derivation **started at the PIE etymon and was
    carried by the laws all the way down**; ``start_name`` names the stage it did
    start at when it did not.  Green needs the whole chain, not a last mile: Old
    Persian 𐎣𐎠𐎶 is reproduced exactly from Proto-Iranian *káHmah, but the engine
    never shows PIE becoming it, so it is yellow (2026-11-09: "only words
    that go up to PIE and are engine-reproducible to the bottom *and* follow the
    recorded intermediary steps are fully explained").

    ``pie_linked`` says the *record* reaches a PIE etymon at all.  Both default
    to **False**: a caller that has not established them has not earned green.
    """
    if non_ie:
        return {"category": "non_pie", "reason": "non-ie source"}
    if ie_loan:
        return {"category": "ie_loan", "reason": "loan from an IE branch"}
    # A seam explains a word only when nothing else does: where an etymology is
    # recorded, the record is the word's history and a surface analysis is a
    # comment on it, not a second verdict (2026-11-09, one pathway).
    if built_from and not recorded:
        parts = " + ".join(str(p) for p in built_from)
        note = f" ({built_note})" if built_note else ""
        return {"category": "built", "parts": [str(p) for p in built_from],
                "reason": f"built from {parts}{note} — a formation, not a derivation"}
    if not recorded:
        return {"category": "unexplained", "reason": "no recorded etymology"}

    used = set(tiers or ())
    ours = used & OUR_TIERS

    if matched_by in (None, "identity", "joined", "bound"):
        reason = {"identity": "unchanged ancestor (no law applied)",
                  "joined": "built from pieces, not derived",
                  "bound": "bound form, not a word"}.get(matched_by, "no rule applied")
        return {"category": "partial", "reason": reason}

    if matched_by == "citation":
        return {"category": "partial", "reason": "cited as a stem, not derived"}

    # Every green and light-green route needs the whole chain: the laws must
    # carry the PIE etymon itself down to the attested form.  A word reproduced
    # only from a later recorded ancestor is the worklist — the transitions
    # above that ancestor are missing or wrong (2026-11-09).
    if not (from_pie and pie_linked):
        if pie_linked or start_name:
            where = start_name or "a later recorded ancestor"
            return {"category": "partial",
                    "reason": f"reproduced only from {where}, not from the PIE etymon"}
        return {"category": "partial", "reason": "recorded outside the PIE chain"}

    if matched_by in WRITING_LAYERS:
        if ours and not approved:
            return {"category": "partial", "reason": "needs approval of our modification"}
        if ours:
            return {"category": "adjusted", "reason": f"{matched_by} layer + our modification"}
        if mismatched_steps:
            return step_row(mismatched_steps)
        return {"category": "full", "reason": f"{matched_by} layer"}

    if matched_by == "gap":
        return {"category": "partial", "reason": "chain step has no rule file"}

    if matched_by == "pathway":
        return {"category": "adjusted" if approved else "partial",
                "reason": "per-word law switch" + ("" if approved else " (unapproved)")}

    if matched_by == "laws":
        if ours:
            if approved:
                return {"category": "adjusted", "reason": "our modification, approved"}
            return {"category": "partial", "reason": "needs approval of our modification"}
        # The start and the end can be exact while a recorded stage between
        # them is not: the laws then reproduce the word and do not reproduce
        # the history the dictionary writes for it.  That is light green, never
        # dark green (2026-11-09).
        if mismatched_steps:
            return step_row(mismatched_steps)
        return {"category": "full", "reason": "cited laws, no change"}

    return {"category": "partial", "reason": f"unrecognised match {matched_by!r}"}


@lru_cache(maxsize=8)
def _approved_at(path_text: str, _mtime_ns: int) -> frozenset[tuple[str, str]]:
    import yaml

    try:
        payload = yaml.safe_load(Path(path_text).read_text(encoding="utf-8")) or {}
    except Exception:
        return frozenset()
    return frozenset(
        (str(row.get("lang")), str(row.get("word")))
        for row in (payload.get("words") or [])
        if row.get("lang") and row.get("word")
    )


def approved_words(path: Path | None = None) -> frozenset[tuple[str, str]]:
    """``(lang, word)`` pairs the project has approved as adjusted.

    Read from `data/adjusted.yaml`; cached on the file's mtime, so a long-lived
    server sees an edit without a restart and a coverage run reads it once.
    """
    path = path or Path(__file__).resolve().parents[2] / "data" / "adjusted.yaml"
    try:
        st = path.stat()
    except OSError:
        return frozenset()
    return _approved_at(str(path), st.st_mtime_ns)


def approved(lang: str, word: str) -> bool:
    """Is this exact word on the approved adjusted list?"""
    return (str(lang), str(word)) in approved_words()


def empty_counts() -> dict:
    """A counter for every category, so a language with none still reports zero."""
    return {key: 0 for key in CATEGORIES}


def summarise(counts: dict, glossary: int | None = None,
              unidentified: int | None = None) -> dict:
    """Add the percentages a stacked bar needs.

    Every counted word belongs to exactly one of the six categories or to the
    ``ie_loan`` facet, so the denominator is those together.  ``unidentified``
    is a guess about words that are not in the glossary and is reported beside
    the total, never in it.
    """
    counted = [key for key in CATEGORIES if key != "unidentified"]
    total = sum(counts.get(key, 0) for key in counted) or 1
    out = {"counts": {key: counts.get(key, 0) for key in CATEGORIES},
           "total": sum(counts.get(key, 0) for key in counted)}
    if unidentified is not None:
        out["counts"]["unidentified"] = unidentified
    else:
        out["counts"].pop("unidentified", None)
    explained = counts.get("full", 0) + counts.get("adjusted", 0)
    out["explained"] = explained
    out["explained_rate"] = round(100.0 * explained / total, 2)
    out["of_glossary"] = round(100.0 * explained / glossary, 2) if glossary else None
    out["share"] = {key: round(100.0 * counts.get(key, 0) / total, 2) for key in counted}
    return out
