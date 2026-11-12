"""Do the *intermediate* stages of a word's chain match what the record says?

The project rule for dark green is not only "the ends agree": the project's
definition (2026-11-09) is that **every reconstructed intermediate step the
dictionary records** must also be the form our laws produce there.  English
*night* is the worked example.  The laws reproduce it from Middle English
*nighte* exactly — but run from Proto-Indo-European they write something else
at Proto-Germanic than the recorded *nahts*, so the word is **fully explained,
with adjustments**, not fully explained.

The word page has always computed this per rung (`service.hierarchy` marks each
rung "match" or "differs").  This module gives the coverage counter the same
answer without building a whole page:

    from pie import steps
    steps.mismatches(entry, "en", chain, data.rulesets())

It walks the chain from the topmost recorded ancestor — the same start
`service.ancestor_starts` gives the page — and compares the derived form at
every stage the record names, except the word's own stage (that comparison is
the match itself, measured apart).
"""
from __future__ import annotations

from . import service
from .rules import derive_detailed


def mismatches(entry: dict, lang: str, chain: list[str], rulesets: dict,
               tiers=None, disabled=(), enabled=()) -> list[dict]:
    """Recorded stages whose law-derived form is not the recorded one.

    Returns ``[{"stage", "recorded", "derived"}]``, ancestor first.  Empty when
    every recorded intermediate agrees — or when there is nothing to compare,
    which the caller must treat as "no evidence of a difference", never as a
    pass: a chain with no modelled start is not a chain that matched.
    """
    starts = service.ancestor_starts(entry, chain)
    if not starts:
        return []
    stage0, form0 = starts[0]
    if stage0 not in chain:
        return []
    index = chain.index(stage0)
    # `skipped` (a transition with no rule file) leaves the form unchanged,
    # so every recorded stage below it compares unequal: the rung says
    # "differs" for exactly this reason on the page, and so does this.
    derivation, _levels = derive_detailed(form0, chain[index:], rulesets,
                                          disabled, tiers, enabled)
    recorded = service._recorded_at(entry, lang)
    out: list[dict] = []
    for offset, stage in enumerate(chain[index + 1:], start=1):
        if stage == lang:
            continue
        here = recorded.get(stage)
        if not here:
            continue
        derived = derivation.forms[offset] if offset < len(derivation.forms) else derivation.output
        block = service._record_block(stage, here, derived, entry)
        if block is not None and not block.get("matches"):
            out.append({"stage": stage,
                        "name": (service._lang(stage) or {}).get("name", stage),
                        "recorded": block.get("w", ""),
                        "derived": derived})
    return out
