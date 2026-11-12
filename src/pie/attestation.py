"""How a word is known: attested, recorded or proposed.

Three states, and a word is exactly one of them (2026-11-11):

``attested``
    A text or a dictionary writes this exact form, in the language's own
    script.  The glossary prints it in that script, never as a Latin reading.

``transliterated``
    A text writes the word, but the glossary keeps the reading of its signs,
    not the signs themselves: Middle Persian lwc (rōz), Tocharian B war.  It is
    a real word of the language and it is not printed with an asterisk, but the
    headword is not the writing the other two statuses talk about, so it does
    not claim to be attested either (2026-11-12).

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

The classification is a pure function of the entry: the caller supplies what it
knows about the stage (a proto stage is reconstructed as a whole; a stage with
its own script has to show it).
"""
from __future__ import annotations

STATUSES = ("attested", "transliterated", "recorded", "proposed")
NON_EXISTENT = "non-existent"

# The asterisk is *on the word*, not in the label (admin, 2026-11-12): a
# recorded form already prints as *madu, so "recorded (*)" said it twice and
# read as a footnote.  The word's own mark carries the meaning, and hovering it
# says the one thing it means: no text spells this word.
LABELS = {
    "attested": "attested",
    "transliterated": "transliterated",
    "recorded": "recorded",
    "proposed": "proposed",
    NON_EXISTENT: "non-existent",
}

DEFINITIONS = {
    "attested": ("A text or a dictionary writes this exact word in the language's "
                 "own script — the form above is that writing."),
    "transliterated": ("A text writes this word; the glossary keeps the reading of "
                       "its signs rather than the signs themselves, so the headword is "
                       "not itself the writing."),
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
    """One entry's status.  ``in_script`` is whether its headword is written in
    the stage's own script, which is what makes an attestation an attestation."""
    if _is_proposal(entry):
        return "proposed"
    if _is_reconstruction(entry, proto):
        return "recorded"
    if not in_script:
        return "transliterated"
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
