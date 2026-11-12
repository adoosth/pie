"""Words that entered a language from outside the Indo-European family.

The coverage categories fixed on 2026-11-09 ask a different question from the
sound laws: not "can the registered rules reproduce this form" but "where did
the word come from at all".  A Persian word borrowed from Arabic and an English
word borrowed from Latin are both loans, and only one of them left the family.

``data/non_ie_sources.yaml`` is the register of source languages that are not
Indo-European.  Membership in that file is the only test: every node the model
holds is Indo-European (``data/languages.yaml``), so a language absent from the
register has no recorded non-Indo-European origin.

The leading ancestry row is the authority, the way Wiktionary writes the entry:
the nearest recorded ancestor is what the word is said to come from, and later
rows extend that chain.  A word whose leading row is an inheritance from an
Indo-European stage keeps that pathway even when a later row names an outside
language as an influence (Persian فارسی beside Arabic فَارِسِيّ is the clear
case).  A word whose leading row is a loan, or whose chain passes through a
borrowed non-Indo-European form (Persian جوراب through Middle Persian and
Arabic), is counted outside the family.
"""

from __future__ import annotations

from functools import lru_cache

import yaml

from . import data

#: The relation names a record uses for a loan.  They are the same set the
#: coverage counter reads (``tools/coverage.py``, ``BORROW_RELATIONS``), plus
#: the shorthand keys that carry the donor in the word field (``:bor`` and its
#: long/short/orphan/unadapted variants).
BORROW_RELATIONS = {"borrow", "borrowed", "lbor", "slbor", "obor", "ubor"}
_BORROW_KEYS = {":bor", ":lbor", ":slbor", ":obor", ":ubor"}

#: Ancestry codes that name no language: ``mul`` is Wiktionary's translingual
#: bucket for scientific names and symbols, and ``mul-tax`` its taxonomy
#: variant.  A word borrowed from translingual nomenclature has no donor family
#: and is left unplaced rather than called an Indo-European loan.
NON_LANGUAGE = {"mul", "mul-tax"}


@lru_cache(maxsize=1)
def sources() -> dict[str, dict]:
    """The register of non-Indo-European source languages, keyed by code."""
    return data.non_ie_sources()


@lru_cache(maxsize=1)
def _codes() -> frozenset[str]:
    return frozenset(sources())


def rows(entry: dict) -> list[tuple[str, str]]:
    """``(language, relation)`` pairs an entry records, nearest ancestor first.

    A row is normally ``[code, word, relation]``.  The ``:inh`` shorthand keeps
    the donor inside the word field (``[':inh', 'ine-pro:*ḱwṓ', 'inherit']``)
    and is expanded; affix rows, which name no language, are skipped.  A root
    row names a language and is kept: it is not an ancestor, but it is what the
    entry's first record says the word belongs to, and the classifier reads it
    as one more piece of evidence rather than as an inheritance.
    """
    out: list[tuple[str, str]] = []
    for row in entry.get("anc") or []:
        if not isinstance(row, list) or not row:
            continue
        code = str(row[0])
        word = str(row[1]) if len(row) > 1 else ""
        rel = str(row[2]) if len(row) > 2 else ""
        if code == ":inh":
            if ":" not in word:
                continue
            code, word = word.split(":", 1)
            rel = "inherit"
        elif code in _BORROW_KEYS:
            if ":" not in word:
                continue
            code = word.split(":", 1)[0]
        elif code.startswith(":"):
            continue
        if code:
            out.append((code, rel))
    return out


def _mark_band(entry: dict) -> str | None:
    """What a dictionary's own language mark says about a word.

    Outside the family it is a ``non_ie`` borrowing; inside it, a loan from a
    sister branch — Persian فرانسوی words are French loans, and counting them
    as "no recorded etymology" was wrong however small the number.  A mark that
    names the word's own language says nothing at all.
    """
    lang = str(entry.get("lang") or "")
    mark = str(entry.get("borrowed_from") or "")
    if not mark or mark == lang:
        return None
    if mark in _codes():
        return "non_ie"
    known = (mark in data.languages()
             or bool((data.language_name_extras().get(mark) or {}).get("family")))
    if not known:
        return None
    # A mark naming the word's own ancestor (Dehkhoda's (پهلوی) on an inherited
    # Persian word) is not a loan: the word came from there, and a loan is a
    # borrowing *sideways* (2026-11-10).
    if lang and mark in data.derivation_chain(lang):
        return None
    return "ie_loan"


def source_language(entry: dict) -> str | None:
    """The outside language a word classified ``non_ie`` came from.

    The nearest outside row is the donor a reader would name: Persian جوراب is
    a loan from Arabic even though Middle Persian is recorded first, because
    the Arabic row is the borrowing in its chain.  A word whose leading pathway
    stays inside the family answers ``None`` even when a later row names an
    outside language as an influence (Persian فارسی beside Arabic فَارِسِيّ).
    """
    if classify(entry) != "non_ie":
        return None
    for code, _rel in rows(entry):
        if code in _codes():
            return code
    mark = str(entry.get("borrowed_from") or "")
    return mark if mark in _codes() else None


def mark_donor(entry: dict) -> str | None:
    """The donor a dictionary's mark names, for a word with no ancestry rows."""
    if rows(entry):
        return None
    mark = str(entry.get("borrowed_from") or "")
    return mark if _mark_band(entry) else None


def source_family(entry: dict) -> str | None:
    """The family of the donor ``source_language`` names, or ``None``."""
    code = source_language(entry)
    if not code:
        return None
    return (sources().get(code) or {}).get("family")


def _display_name(code: str) -> str:
    """What to call a donor language whose code the register does not hold.

    A loan from a sister branch has no row in `data/non_ie_sources.yaml` (it is
    inside the family), so its name comes from `data.language_name` — the one
    resolver the word page also reads.  Keeping a second, narrower lookup here
    is how the badge said "borrowed from xme-old" beside a sentence that said
    "Borrowed from Old Median" (2026-11-12).
    """
    return data.language_name(code) or code


def _ie_donor(entry: dict) -> str | None:
    """The sister-branch language an ``ie_loan`` was borrowed from.

    The first row that is not a root and states a borrowing — the same row
    `classify` reads, so the badge and the donor cannot disagree.
    """
    for code, rel in rows(entry):
        if rel == "root":
            continue
        if rel in BORROW_RELATIONS and code not in NON_LANGUAGE:
            return code
        return None
    return mark_donor(entry)


def classify(entry: dict, lang: str | None = None) -> str | None:
    """``non_ie``, ``ie_loan`` or ``None`` for one glossary entry.

    ``non_ie`` means the recorded pathway leaves the Indo-European family,
    whether the word was borrowed (Arabic into Persian) or inherited from a
    non-Indo-European stage.  ``ie_loan`` means it was borrowed, but from an
    Indo-European language (Latin into English, French into English).  ``None``
    means the leading pathway stays inside the family, or the entry records no
    ancestry at all.

    ``lang`` names the attested target language and is accepted so a caller can
    measure per language; the register decides the source side, so it does not
    change the answer for the lexicons the model holds.
    """
    recs = rows(entry)
    if not recs:
        # A dictionary's own mark can stand where no ancestry chain does:
        # Dehkhoda prints (ع اِ) beside an Arabic headword, and that is the
        # dictionary saying "Arabic" — a record, quoted, not a guess.  Only an
        # entry with no ancestry at all is read this way, so a mark never
        # overrules a stated pathway (2026-11-10).
        return _mark_band(entry)
    # A root row is a relation, not an ancestor (the project's rule), and it is
    # as often the root behind a *donor* as one behind the word: English
    # abattoir records French abattoir first and PIE *bʰedʰ- above it, Persian
    # دایناسور records English dinosaur first and *dwey- above that.  The row
    # that decides whether the word was borrowed is therefore the first one
    # that is not a root; taking the first row outright called 3,138 loans
    # "inherited" and drew them a full PIE ladder (2026-11-10).
    code, rel = next(((c, r) for c, r in recs if r != "root"), recs[0])
    if code in _codes():
        return "non_ie"
    if any(c in _codes() for c, _r in recs):
        if rel == "inherit":
            return None
        return "non_ie"
    if rel in BORROW_RELATIONS and code not in NON_LANGUAGE:
        return "ie_loan"
    return None


@lru_cache(maxsize=1)
def periods() -> list[dict]:
    """The donor/target contact windows in `data/loan_periods.yaml`."""
    path = data.DATA / "loan_periods.yaml"
    try:
        with path.open(encoding="utf-8") as fh:
            payload = yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return []
    return [row for row in (payload.get("loans") or []) if row.get("donor")]


def period(donor: str | None, target: str | None) -> dict | None:
    """The recorded contact window for a donor into a target, or ``None``.

    A window, not a date: the record states that the word was borrowed and the
    two languages' history states when the borrowing could have happened.  The
    caller must print the word's own date as unknown (`docs/DECISIONS.md`).
    """
    if not donor or not target:
        return None
    for row in periods():
        if str(row.get("donor")) == donor:
            targets = row.get("targets") or ([row["target"]] if row.get("target") else [])
            if target in targets or "*" in targets:
                return {**row, "targets": list(targets)}
    return None


def _full_rows(entry: dict) -> list[tuple[str, str, str]]:
    """``(language, word, relation)`` per ancestry row, nearest first.

    `rows()` drops the donor form because the classifier does not need it; the
    word page does — "borrowed from Arabic أَخِرَة" is a different statement
    from "borrowed from Arabic".
    """
    out: list[tuple[str, str, str]] = []
    for row in entry.get("anc") or []:
        if not isinstance(row, list) or not row:
            continue
        code = str(row[0])
        word = str(row[1]) if len(row) > 1 else ""
        rel = str(row[2]) if len(row) > 2 else ""
        if code == ":inh":
            if ":" not in word:
                continue
            code, word = word.split(":", 1)
            rel = "inherit"
        elif code in _BORROW_KEYS:
            if ":" not in word:
                continue
            code = word.split(":", 1)[0]
        elif code.startswith(":"):
            continue
        if code:
            out.append((code, word, rel))
    return out


def donor(entry: dict, lang: str | None = None) -> dict | None:
    """What the entry itself says about a non-PIE loan, for display.

    Returns ``{code, name, family, form, relation, period, wording}`` when the
    word is classified ``non_ie`` and the dossier names the donor, else
    ``None``.  ``form`` is the donor's own spelling as the record gives it;
    ``period`` comes from `data/loan_periods.yaml` and is a contact window.
    """
    kind = classify(entry, lang)
    if kind not in ("non_ie", "ie_loan"):
        return None
    code = source_language(entry) if kind == "non_ie" else _ie_donor(entry)
    if not code:
        return None
    meta = sources().get(code) or {}
    form, relation = "", ""
    for c, w, rel in _full_rows(entry):
        if c == code:
            form, relation = w, rel
            break
    name = str(meta.get("name") or _display_name(code))
    return {
        "code": code,
        "name": name,
        "family": meta.get("family")
        or str((data.languages().get(code) or {}).get("branch") or ""),
        "kind": kind,
        "form": form,
        "relation": relation,
        "period": period(code, lang),
        "wording": f"borrowed from {name}",
    }
