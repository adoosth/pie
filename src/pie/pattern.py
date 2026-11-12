"""A small pattern language for phonological contexts.

Examples of contexts used by the rule data::

    p                a literal segment
    V                any vowel (class name)
    !V               anything that is not a vowel
    #                word edge
    .                any single segment
    C? i             an optional consonant, then i
    (s|t)            alternation
    (n)?             optional group

Patterns match whole sequences (the ``match`` slot) or a suffix/prefix next to
the target (the ``left``/``right`` contexts).
"""

from __future__ import annotations

from dataclasses import dataclass

from .phonology import class_matches

CLASSES = {
    "V", "C", "STOP", "PSTOP", "BSTOP", "ASP", "FRIC", "SIB", "NAS", "LIQ", "RES",
    "GLIDE", "LARYN", "SYL", "LONG", "SHORT", "VF", "VB", "HIGH", "LOW", "VLOW",
    "ROUND", "LAB", "DENT", "VEL", "PAL", "PALATAL", "LABIOVEL", "VOICED",
    "VOICELESS", "ACC", "STRESS",
}


@dataclass(frozen=True)
class Atom:
    kind: str  # literal | class | any | boundary | group
    value: object = None
    optional: bool = False

    def matches(self, seg: str) -> bool:
        if self.kind == "any":
            return True
        if self.kind == "class":
            return class_matches(str(self.value), seg)
        if self.kind == "literal":
            return seg == self.value
        if self.kind == "group":
            return any(alt.matches(seg) for alt in self.value)  # type: ignore[union-attr]
        return False


def _split_top(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    cur = ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch.isspace() and depth == 0:
            if cur:
                parts.append(cur)
                cur = ""
            continue
        cur += ch
    if cur:
        parts.append(cur)
    return parts


def _parse_atom(raw: str) -> Atom:
    optional = False
    if raw.endswith("?") and len(raw) > 1:
        optional = True
        raw = raw[:-1]
    if raw == "#":
        return Atom("boundary", optional=optional)
    if raw in {".", "*"}:
        return Atom("any", optional=optional)
    if raw.startswith("(") and raw.endswith(")"):
        alts = tuple(_parse_atom(a.strip()) for a in raw[1:-1].split("|") if a.strip())
        return Atom("group", alts, optional)
    if raw in CLASSES or (raw.startswith("!") and raw[1:] in CLASSES):
        return Atom("class", raw, optional)
    if "|" in raw:
        alts = tuple(_parse_atom(a) for a in raw.split("|"))
        return Atom("group", alts, optional)
    return Atom("literal", raw, optional)


def parse(pattern: str | None) -> list[Atom] | None:
    if pattern is None:
        return None
    pattern = pattern.strip()
    if not pattern:
        return None
    return [_parse_atom(p) for p in _split_top(pattern)]


def _match_from(atoms: list[Atom], tokens: list[str], idx: int) -> list[int]:
    ends: list[int] = []

    def walk(ai: int, ti: int) -> None:
        if ai == len(atoms):
            ends.append(ti)
            return
        atom = atoms[ai]
        if atom.optional:
            walk(ai + 1, ti)
        if atom.kind == "boundary":
            if ti == 0 or ti == len(tokens):
                walk(ai + 1, ti)
            return
        if ti < len(tokens) and atom.matches(tokens[ti]):
            walk(ai + 1, ti + 1)

    walk(0, idx)
    return ends


def match_at(atoms: list[Atom], tokens: list[str], idx: int) -> int | None:
    ends = _match_from(atoms, tokens, idx)
    return max(ends) if ends else None


def match_left(atoms: list[Atom], tokens: list[str], idx: int) -> bool:
    if not atoms:
        return True
    if atoms[0].kind == "boundary":
        if idx != 0:
            return False
        return not atoms[1:]
    for start in range(idx, -1, -1):
        if idx in _match_from(atoms, tokens, start):
            return True
    return False


def match_right(atoms: list[Atom], tokens: list[str], idx: int) -> bool:
    if not atoms:
        return True
    if atoms[0].kind == "boundary":
        if idx != len(tokens):
            return False
        return not atoms[1:]
    return bool(_match_from(atoms, tokens, idx))
