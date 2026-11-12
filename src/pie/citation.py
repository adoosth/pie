"""How a dictionary cites a word, when that is not the form the laws produce.

The sound laws end where the recorded ancestor ends.  Sanskrit *deywós is a
nominative, so the chain gives deváḥ, while the entry's lemma is देव devá- —
the stem the whole paradigm is built on.  Nothing about that difference is a
sound change or a spelling convention: it is the dictionary's citation form.

Keeping it in its own file (``data/citation/<lang>.yaml``) lets the coverage
counter report it as its own fact — "the same word, cited as the stem" — instead
of either bending the target into `exact` or losing a word the laws really do
explain.  Only the endings a file lists may be dropped, and the caller still
requires that the rest of the word spells the lemma exactly and that the
phonemes fit the entry's own recorded pronunciation.
"""
from __future__ import annotations

from functools import lru_cache

from . import data

CITATION_DIR = data.DATA / "citation"


@lru_cache(maxsize=None)
def pairs(lang: str) -> tuple[tuple[str, str], ...]:
    """``(ending, stem vowel)`` pairs a record of ``lang`` may be cited without.

    The second member says what the ending stands for when the dictionary cites
    the *stem* instead of the inflected form: Sanskrit cites devá- for the
    nominative deváḥ and the stem is just the form minus -ḥ, so its pairs carry
    an empty string, while an Avestan a-stem cites aspa- for the nominative
    aspō and the ending -ō replaces the stem vowel -a.  Nothing else is
    added or removed, and the record's own word must still be spelled exactly
    (2026-11-09).
    """
    path = CITATION_DIR / f"{lang}.yaml"
    if not path.exists():
        return ()
    rows = data._load_yaml(path).get("endings") or []
    out = []
    for row in rows:
        form = (row or {}).get("form")
        if form:
            out.append((str(form), str((row or {}).get("cited_as") or "")))
    return tuple(out)


@lru_cache(maxsize=None)
def endings(lang: str) -> tuple[str, ...]:
    """The inflectional endings a record of ``lang`` may be cited without."""
    return tuple(form for form, _cited in pairs(lang))


@lru_cache(maxsize=None)
def stage(lang: str) -> dict:
    path = CITATION_DIR / f"{lang}.yaml"
    return data._load_yaml(path) if path.exists() else {}


def available() -> list[str]:
    return sorted(p.stem for p in CITATION_DIR.glob("*.yaml")) if CITATION_DIR.is_dir() else ()
