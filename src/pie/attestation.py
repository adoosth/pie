"""How a word is known: attested, recorded or proposed.

Three states, and a word is exactly one of them (2026-11-11):

``attested``
    A text or a dictionary records this word.  The form above is either the
    writing itself (Old Persian 𐎭𐎠𐎼𐎹𐎺𐎢𐏁) or the record's transcription of
    it (Middle Persian ``garm``) — a Latin reading still attests the word, and
    a record that gives one has recorded it (2026-11-13).

``recorded``
    A reconstruction the literature itself proposes — no text spells it, but
    a dictionary records it as the probable word, and it is written with an
    asterisk: Old Persian *madu* "wine", Proto-Indo-European *ph₂tḗr*.

``proposed``
    A reconstruction this project proposes: an asterisk, and nothing in the
    literature behind it.  Nothing is filed this way yet; the flag exists so a
    word the model invents can never read as a word the record has.

A form with no glossary entry at all is ``non-existent`` — the word page says
so instead of pretending the stage records it.

The classification is a pure function of the entry: whether it is a
reconstruction, and who proposes it.  The headword's script no longer decides
the status; `service.word` reports what the form above *is* as
``attested_how`` (writing or transcription).
"""
from __future__ import annotations

STATUSES = ("attested", "recorded", "proposed")
NON_EXISTENT = "non-existent"

# The asterisk is *on the word*, not in the label (2026-11-12): a
# recorded form already prints as *madu, so "recorded (*)" said it twice and
# read as a footnote.  The word's own mark carries the meaning, and hovering it
# says the one thing it means: no text spells this word.
LABELS = {
    "attested": "attested",
    "recorded": "recorded",
    "proposed": "proposed",
    NON_EXISTENT: "non-existent",
}

DEFINITIONS = {
    "attested": ("A text or a dictionary records this word — the form above is the "
                 "writing, or the transcription the record gives it."),
    "recorded": ("Reconstructed in the literature: no text spells it, so it is "
                 "written with an asterisk, and a dictionary records it as the "
                 "probable word of the language."),
    "proposed": ("Proposed by this model: an asterisk, with no literature behind "
                 "it. It is a guess at a probable word, not a record."),
    NON_EXISTENT: ("No glossary entry of this stage is spelled this way."),
}

#: Entry fields that make a reconstruction this project's own proposal rather
#: than the literature's.  Nothing writes them today; a word the model invents
#: must say `proposal: true` (or name `source: pie`) to be filed as proposed.
PROPOSAL_FLAGS = ("proposal", "proposed")
PROPOSAL_SOURCES = ("pie", "proposal")


def _is_proposal(entry: dict) -> bool:
    if any(entry.get(flag) for flag in PROPOSAL_FLAGS):
        return True
    return str(entry.get("source") or "").lower() in PROPOSAL_SOURCES


def _is_reconstruction(entry: dict, proto: bool) -> bool:
    if _is_proposal(entry):
        return True
    if entry.get("recon"):
        return True
    if str(entry.get("word") or "").startswith("*"):
        return True
    return proto


def classify(entry: dict, *, proto: bool = False, in_script: bool = True) -> str:
    """One entry's status.

    ``in_script`` is kept so existing callers need not change, but it no longer
    decides the status: a recorded transcription attests its word as surely as
    a recorded writing does (2026-11-13).  What the headword *is* —
    writing or transcription — travels beside the status as ``attested_how``.
    """
    if _is_proposal(entry):
        return "proposed"
    if _is_reconstruction(entry, proto):
        return "recorded"
    return "attested"


def for_entry(entry: dict, *, proto: bool = False, in_script: bool = True) -> str:
    return classify(entry, proto=proto, in_script=in_script)


def for_word(entries, *, proto: bool = False, in_script: bool = True) -> str:
    """One spelling's status, over every entry filed under it.

    A homograph counts as attested when any of its entries is attested: the
    spelling occurs in a text.  Otherwise the strongest record wins, and
    ``proposed`` only when the model proposed every one of them.
    """
    rows = [row for row in entries or () if isinstance(row, dict)]
    if not rows:
        return NON_EXISTENT
    seen = {classify(row, proto=proto, in_script=in_script) for row in rows}
    for status in STATUSES:
        if status in seen:
            return status
    return NON_EXISTENT


def written(word: str, status: str) -> str:
    """The form to print: an asterisk in front of anything not attested."""
    form = str(word or "")
    if status in ("recorded", "proposed"):
        return "*" + form.lstrip("*")
    return form


def payload(word: str, status: str, *, reason: str = "") -> dict:
    """What the page and the glossary need to print one status."""
    return {
        "status": status,
        "label": LABELS.get(status, status),
        "definition": DEFINITIONS.get(status, ""),
        "written": written(word, status),
        "reason": reason,
    }
