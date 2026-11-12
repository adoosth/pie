"""Turn coverage misses into priorisited work items.

The coverage tool answers *how much* the registered laws explain.  This module
answers *what to work on next*: it re-derives every eligible word, compares the
produced form with the attested one, and groups the remaining differences into
signatures that can be counted, cited and fixed.

Three kinds of finding fall out of that:

* a **miss signature** — the same small edit (``æ → a``, ``+ e``, ``- n``)
  recurring across hundreds of words is one missing rule, not hundreds of bugs;
* a **silent transition** — a stage a word passes through without any rule
  firing is the place where a law is missing (or where the form needed no
  change and the next stage is the culprit);
* an **orthographic probe** — a miss that a plain phoneme→letter table would
  already fix belongs to the spelling layer, not to the sound laws.  The probe
  measures the size of that layer before a single rule is written.

Nothing here changes a derivation or a published number: the audit is a
read-only instrument over the same corpus ``tools/coverage.py`` measures.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Iterable

from . import data
from .rules import derive_detailed

STRESS = {"ˈ", "ˌ"}

#: A draft phone→letter table per descendant, used only by :func:`spell_probe`.
#: It is deliberately dumb — one letter (or letter pair) per segment, no
#: context, no exceptions — because its job is to answer "how many misses are
#: spelling at all?" before the real, ordered orthographic rules exist.
LETTER_TABLE: dict[str, dict[str, str]] = {
    "en": {
        "æ": "a", "ɑ": "a", "ɒ": "o", "ɔ": "o", "ʌ": "u", "ə": "e", "ɜ": "er",
        "ɪ": "i", "i": "i", "e": "e", "ɛ": "e", "ʊ": "u", "u": "u", "y": "y",
        "θ": "th", "ð": "th", "ʃ": "sh", "ʒ": "s", "tʃ": "ch", "dʒ": "j",
        "ŋ": "ng", "j": "y", "w": "w", "x": "ch", "ɣ": "g", "c": "c",
        "ː": "", "ˑ": "", "ē": "e", "ā": "a", "ī": "i", "ō": "o", "ū": "u",
    },
    "de": {
        "ɪ": "i", "ɛ": "e", "ɔ": "o", "ʊ": "u", "ə": "e", "ɐ": "er",
        "ʏ": "ü", "œ": "ö", "ø": "ö", "y": "ü", "ç": "ch", "x": "ch",
        "ʃ": "sch", "ts": "z", "tʃ": "tsch", "dʒ": "dsch", "ŋ": "ng",
        "j": "j", "v": "w", "z": "s", "ː": "", "ˑ": "",
        "ē": "e", "ā": "a", "ī": "i", "ō": "o", "ū": "u", "ë": "e",
        "ȩ": "e", "ą": "a",
    },
    "it": {"ɛ": "e", "ɔ": "o", "ə": "", "j": "i", "w": "u", "ts": "z", "dʒ": "g", "ː": ""},
    "la": {"j": "i", "w": "u", "kʷ": "qu", "ː": "", "ˑ": ""},
}

#: Segments that are phonemic but never written as such in a Latin-script
#: language: phonemic length, stress marks, syllabicity below.
UNWRITTEN = STRESS


@dataclass
class Miss:
    lang: str
    word: str
    stage: str
    ancestor: str
    output: str
    distance: int
    ops: tuple
    silent: tuple[str, ...] = ()
    spelled: str = ""
    probe: bool = False
    blamed: tuple[str, ...] = ()

    @property
    def signature(self) -> str:
        return edit_signature(self.ops)


def edit_ops(a: str, b: str) -> tuple[tuple[str, str], ...]:
    """A minimal edit script turning ``a`` into ``b``.

    Deletions are reported before insertions at a tie, so the same difference
    always gets the same signature regardless of which side is "wrong".
    """
    n, m = len(a), len(b)
    if not n:
        return (("ins", b),) if m else ()
    if not m:
        return (("del", a),) if n else ()
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, nxt = dp[i], dp[i + 1]
        for j in range(m - 1, -1, -1):
            row[j] = nxt[j + 1] + 1 if a[i] == b[j] else max(nxt[j], row[j + 1])
    ops: list[tuple[str, str]] = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            ops.append(("del", a[i]))
            i += 1
        else:
            ops.append(("ins", b[j]))
            j += 1
    while i < n:
        ops.append(("del", a[i]))
        i += 1
    while j < m:
        ops.append(("ins", b[j]))
        j += 1
    return tuple(ops)


def _pair_ops(ops: Iterable[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    return tuple(ops)


def edit_signature(ops: Iterable[tuple[str, str]]) -> str:
    """A compact, human-readable key for an edit script (``æ→a +e -n``)."""
    out: list[str] = []
    pending_del: str | None = None
    for kind, ch in ops:
        if kind == "del":
            if pending_del is not None:
                out.append("−" + pending_del)
            pending_del = ch
        else:
            if pending_del is not None:
                out.append(f"{pending_del}→{ch}")
                pending_del = None
            else:
                out.append("+" + ch)
    if pending_del is not None:
        out.append("−" + pending_del)
    return " ".join(out)


def spell_probe(form: str, lang: str) -> str:
    """Spell a phonemic form: the real orthographic file if one exists.

    For a stage with `data/spelling/<lang>.yaml` this is the layer's own answer,
    so the worklist's "spelling probe" column is the measured effect of the
    conventions, not an estimate.  For a stage without a file the draft letter
    table stands in, and the column is an estimate of what such a file could do.
    """
    from . import spelling

    if spelling.applies(lang):
        return spelling.spell(form, lang)
    table = LETTER_TABLE.get(lang)
    if not table:
        return form
    out = []
    for seg in _segments(form):
        if seg in STRESS:
            continue
        out.append(table.get(seg, seg))
    return "".join(out)


def _segments(form: str) -> list[str]:
    from .phonology import tokenize

    return tokenize(form)


def _units(ops: tuple) -> list[tuple]:
    """Group adjacent delete+insert pairs into one substitution."""
    units: list[tuple] = []
    i = 0
    while i < len(ops):
        kind, ch = ops[i]
        if kind == "del" and i + 1 < len(ops) and ops[i + 1][0] == "ins":
            units.append(("sub", ch, ops[i + 1][1]))
            i += 2
        else:
            units.append((kind, ch))
            i += 1
    return units


def classify(ops: tuple, lang: str) -> str:
    """Best single label for a miss signature (for grouping in the worklist).

    The labels decide *who* fixes a miss, and whether it is a miss at all:

    ``unchanged``  the produced form is the attested form but no rule applied
                   (identity is not an explanation — not a rule task);
    ``case``       only capitalisation differs (a writing convention, and
                   already counted separately as ``case_only`` by coverage);
    ``stress``     only stress marks differ (the phonemic layer's bookkeeping);
    ``spelling``   a plain phoneme→letter table would already fix it;
    ``phonology``  the sound laws themselves have to change.
    """
    if not ops:
        return "unchanged"
    plain = [u for u in _units(ops) if not (u[0] in ("del", "ins") and u[1] in STRESS)]
    if not plain:
        return "stress"
    if _case_only(plain):
        return "case"
    table = LETTER_TABLE.get(lang)
    if not table:
        return "phonology"
    return "spelling" if all(_letter_ok(u, table) for u in plain) else "phonology"


def _base(ch: str) -> str:
    return ch.replace("\u0304", "").replace("\u0306", "").replace("\u032f", "")


def _letter_ok(unit: tuple, table: dict[str, str]) -> bool:
    """True when this one edit is a writing convention, not a sound change."""
    kind = unit[0]
    if kind == "sub":
        _k, a, b = unit
        if b == table.get(a):
            return True
        if b == _base(a) and b in table.get(a, b):
            return True
        if a in table and table[a] and b in table[a]:
            return True
        return b.lower() == a.lower()
    if kind == "ins":
        return unit[1] in "e\u02bc'"
    # deletion
    return unit[1] in STRESS or table.get(unit[1]) == "" or unit[1] in "\u02d0\u02d1"


def _case_only(units: list[tuple]) -> bool:
    """True when the difference is capitalisation alone (``s → S``)."""
    text_a, text_b = [], []
    for u in units:
        if u[0] == "sub":
            text_a.append(u[1]); text_b.append(u[2])
        elif u[0] == "del":
            text_a.append(u[1])
        else:
            text_b.append(u[1])
    a, b = "".join(text_a), "".join(text_b)
    return bool(a) and a.lower() == b.lower()


#: Labels that are work for a lexicographer/rule writer, in ranking order.
ACTIONABLE = ("phonology", "spelling")


def _blame(levels, target: str) -> tuple[str, ...]:
    """The transitions that moved a word *away* from its attested form.

    A stage that increases the distance to the target is the first place to
    read the rules again: either one of them over-applies, or the target
    continues a different paradigm cell.  When no stage makes things worse the
    last transition is named, because that is where a final law is missing.
    """
    hops: list[str] = []
    prev = levels[0].form if levels else None
    for lv in levels:
        nxt = lv.form
        if prev is not None and lv.src != lv.dst:
            before, after = _distance(prev, target), _distance(nxt, target)
            if after > before:
                hops.append((after - before, f"{lv.src}→{lv.dst}"))
        prev = nxt
    if not hops:
        return (f"{levels[-1].src}→{levels[-1].dst}",) if levels else ()
    hops.sort(reverse=True)
    return tuple(h for _d, h in hops[:2])


def _silent_stages(levels) -> tuple[str, ...]:
    return tuple(f"{lv.src}→{lv.dst}" for lv in levels if not lv.missing and not any(r["fired"] for r in lv.rules))


def audit_language(lang: str, limit: int | None = None, max_edits: int = 4,
                   rulesets=None, tiers: set[str] | None = None) -> dict:
    """Audit one descendant's misses and return a machine-readable report."""
    from . import service

    rulesets = rulesets or data.rulesets()
    chain = data.derivation_chain(lang)
    entries = data.lexicon(lang)
    rows = sample(entries, limit)

    exact = near = spelling_fixed = far = case_only = unchanged = 0
    signatures: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    examples: dict[str, list[dict]] = defaultdict(list)
    silent: Counter[str] = Counter()
    stage_hits: Counter[str] = Counter()
    rule_fired: Counter[str] = Counter()
    rule_exact: Counter[str] = Counter()
    misses: list[Miss] = []
    errors = 0

    for entry in rows:
        # A word Wiktionary keeps in its Reconstruction: namespace is not an
        # attested target, so a rule that misses it is not a bug worth a task:
        # the glossary itself says no text spells it (2026-11-08).
        if entry.get("recon"):
            continue
        target = entry["word"].strip()
        candidates = _starts(entry, chain)
        if not candidates:
            continue
        best = None
        spell_hit: tuple[str, str] | None = None
        hit = False
        for stage, form in candidates:
            try:
                derivation, levels = derive_detailed(
                    form, chain[chain.index(stage):], rulesets, tiers=tiers
                )
            except Exception:
                errors += 1
                hit = True
                break
            if derivation.skipped:
                continue
            if derivation.output == target and derivation.steps:
                hit = True
                for step in derivation.steps:
                    rule_fired[f"{step.stage}|{step.rule_id}"] += 1
                    rule_exact[f"{step.stage}|{step.rule_id}"] += 1
                break
            for step in derivation.steps:
                rule_fired[f"{step.stage}|{step.rule_id}"] += 1
            if spell_hit is None:
                written = spell_probe(derivation.output, lang)
                if written and written == target:
                    from . import spelling as _spelling0

                    if _spelling0.confirms(derivation.output, target,
                                           entry.get("ipa") or "", lang):
                        spell_hit = (derivation.output, written)
            cand = Miss(lang, target, stage, form, derivation.output,
                        _distance(derivation.output, target),
                        edit_ops(derivation.output, target),
                        _silent_stages(levels),
                        blamed=_blame(levels, target))
            if best is None or len(cand.ops) < len(best.ops):
                best = cand
        if hit or best is None:
            if hit:
                exact += 1
            continue
        # The spelling layer is tried on every candidate, not only on the one
        # closest to the word: a scripted headword has nothing to do with the
        # distance of a Latin string (the same bug tools/coverage.py had, where
        # Sanskrit read 0 spelled).  Avenst 𐬥𐬏 *nū* was the visible cost: the
        # worklist said 6 spelled where the counter found 7 (2026-11-09).
        from . import spelling as _spelling

        if spell_hit is not None:
            best.output, best.spelled = spell_hit
            best.probe = True
        else:
            best.spelled = spell_probe(best.output, lang)
            # A spelling only counts when the phonemes behind it are plausible;
            # see spelling.plausible for why (letter tables can concatenate to
            # the right word from the wrong sounds).
            best.probe = (bool(best.spelled) and best.spelled == target
                          and _spelling.confirms(best.output, target,
                                                 entry.get("ipa") or "", lang))
        if best.probe:
            spelling_fixed += 1
        miss = best
        # When the stage has an orthographic file and that file lands on the
        # word, the miss is a writing convention by definition — the layer says
        # so itself, which is better evidence than the draft table below.
        kind = "spelling" if miss.probe and not (
            len(miss.ops) == 0) else classify(miss.ops, lang)
        if kind == "case":
            case_only += 1
            continue
        if kind == "unchanged":
            unchanged += 1
            continue
        if len(miss.ops) <= max_edits:
            near += 1
            kinds[kind] += 1
            signatures[miss.signature] += 1
            stage_hits[miss.stage] += 1
            for st in miss.blamed:
                silent[st] += 1
            bucket = examples[miss.signature]
            if len(bucket) < 3:
                bucket.append({
                    "word": target, "stage": miss.stage, "ancestor": miss.ancestor,
                    "output": miss.output, "probe": miss.spelled if miss.probe else "",
                })
            misses.append(miss)
        else:
            far += 1

    return {
        "lang": lang,
        "glossary": len(entries),
        "tested": len(rows),
        "exact": exact,
        "case_only": case_only,
        "unchanged": unchanged,
        "near": near,
        "spelling_probe": spelling_fixed,
        "far": far,
        "errors": errors,
        "kinds": dict(kinds),
        "signatures": [
            {"signature": sig, "count": n, "kind": classify(_sig_ops(sig), lang),
             "examples": examples[sig]}
            for sig, n in signatures.most_common(30)
        ],
        "stages": dict(stage_hits.most_common()),
        "silent": dict(silent.most_common(20)),
        # The full miss list is an in-process detail; the report keeps a bounded
        # sample (the signatures above already carry the examples).
        "misses": [asdict(m) | {"signature": m.signature} for m in misses[:200]],
        "misses_total": len(misses),
        "rule_fired": dict(rule_fired),
        "rule_exact": dict(rule_exact),
    }


def _sig_ops(sig: str) -> tuple[tuple[str, str], ...]:
    """Reconstruct a coarse op list from a signature, for classification only."""
    ops: list[tuple[str, str]] = []
    for part in sig.split():
        if part.startswith("+") and len(part) > 1:
            ops.append(("ins", part[1]))
        elif part.startswith("−") and len(part) > 1:
            ops.append(("del", part[1]))
        elif "→" in part:
            a, _, b = part.partition("→")
            ops.append(("del", a))
            ops.append(("ins", b))
    return tuple(ops)


def _distance(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sample(rows: list, limit: int | None) -> list:
    """A representative stride sample (same policy as ``tools/coverage.py``)."""
    if not limit or len(rows) <= limit:
        return rows
    step = len(rows) / limit
    return [rows[int(i * step)] for i in range(limit)]


def _starts(entry: dict, chain: list[str]) -> list[tuple[str, str]]:
    """Every usable ancestor form, PIE first (same rule as the coverage tool)."""
    from .service import _pie_form, normalise_etymon

    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    pie = _pie_form(entry)
    inherited = any(l == "ine-pro" and rel != "borrow" for l, _w, rel in entry.get("anc") or [])
    if pie and inherited and chain:
        out.append((chain[0], pie))
        seen.add(pie)
    for lang, word, rel in entry.get("anc") or []:
        if lang not in chain or lang == chain[-1] or rel == "borrow":
            continue
        for part in re.split(r"[,;]", word or ""):
            form = normalise_etymon(part)
            if not form or form in seen or len(form) > 60:
                continue
            seen.add(form)
            out.append((lang, form))
    out.sort(key=lambda x: chain.index(x[0]) if x[0] in chain else 10**6)
    return out
