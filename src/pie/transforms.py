"""Whole-word phonological operations that are awkward to write as rewrites.

Some sound laws are dissimilations or assimilations defined over the whole word
(Grassmann, Bartholomae).  They are expressed as named transforms and invoked
from a rule file with ``transform: <name>`` instead of ``match``/``replace``.
"""

from __future__ import annotations

from .phonology import letters, marks, ACUTE

ASPIRATE_TO_PLAIN = {"bʰ": "b", "dʰ": "d", "gʰ": "g", "ǵʰ": "ǵ", "ȷ́ʰ": "ȷ́",
                     "gʷʰ": "gʷ", "kʰ": "k", "pʰ": "p", "tʰ": "t"}
PLAIN_TO_VOICED = {"p": "b", "t": "d", "k": "g", "ḱ": "ǵ", "kʷ": "gʷ", "s": "z"}
STOP_TO_ASPIRATED_VOICED = {"p": "bʰ", "t": "dʰ", "k": "gʰ", "ḱ": "ǵʰ", "kʷ": "gʷʰ"}


def _is_aspirate(tok: str) -> bool:
    return tok in ASPIRATE_TO_PLAIN


def _is_voiceless_stop(tok: str) -> bool:
    return tok in STOP_TO_ASPIRATED_VOICED


def grassmann(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Deaspirate every aspirate except the last one in the word."""
    idx = [i for i, t in enumerate(tokens) if _is_aspirate(t)]
    if len(idx) < 2:
        return tokens, []
    out = list(tokens)
    changed = []
    for i in idx[:-1]:
        out[i] = ASPIRATE_TO_PLAIN[out[i]]
        changed.append(i)
    return out, changed


def bartholomae(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Voiced aspirate + voiceless stop → voiced stop + voiced aspirate."""
    out = list(tokens)
    changed = []
    i = 0
    while i < len(out) - 1:
        if _is_aspirate(out[i]) and _is_voiceless_stop(out[i + 1]):
            nxt = STOP_TO_ASPIRATED_VOICED[out[i + 1]]
            out[i] = ASPIRATE_TO_PLAIN[out[i]]
            out[i + 1] = nxt
            changed.extend([i, i + 1])
            i += 2
            continue
        i += 1
    return out, changed


def syllabic_laryngeals(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Turn laryngeals that carry a syllable into vowels.

    A laryngeal is syllabic only when it cannot attach to the preceding
    syllable, i.e. when the segment before it is a consonant that is itself at
    the start of the word or preceded by a consonant: *ph₂tḗr has a syllabic
    *h₂, *dʰugh₂tḗr does not.
    """
    from .phonology import is_vowel

    mapping = {"h₁": "a", "h₂": "a", "h₃": "a"}
    if params:
        mapping.update({k: v for k, v in params.items() if k in mapping})
    out = list(tokens)
    changed = []
    for i, tok in enumerate(tokens):
        if tok not in mapping:
            continue
        if i == 0:
            continue
        prev = tokens[i - 1]
        if is_vowel(prev) or prev in {"ˈ", "ˌ"}:
            continue
        if i - 2 >= 0 and is_vowel(tokens[i - 2]):
            # the consonant before the laryngeal belongs to a preceding
            # syllable, so the laryngeal is not a nucleus (*dʰugh₂tḗr)
            continue
        out[i] = mapping[tok]
        changed.append(i)
    return out, changed


def laryngeal_lengthening(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Lose the Iranian laryngeal, lengthening the vowel it stood after.

    Proto-Iranian keeps *H as a segment (PIr *bráHtā, *baHjúš). Old Iranian
    loses it: after a short vowel the vowel lengthens (OP brātā, bāzu-), after a
    long vowel or a consonant it simply goes. A word-initial *H is handled by
    the older rule that names it, so a laryngeal with nothing before it is left
    alone here.
    """
    short = {"a": "ā", "i": "ī", "u": "ū"}
    long_v = {"ā", "ī", "ū", "ē", "ō"}
    out: list[str] = []
    changed: list[int] = []
    for tok in tokens:
        if tok == "H" and out:
            prev = out[-1]
            if prev in short:
                out[-1] = short[prev]
                changed.append(len(out) - 1)
                continue
            if prev in long_v or prev not in {"ˈ", "ˌ"}:
                changed.append(len(out) - 1)
                continue
        out.append(tok)
    return out, changed


def devanagari(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Write the whole form in Devanagari (orthography, not a sound law).

    Used by a spelling file only: ``data/spelling/sa.yaml`` declares one rule
    with ``transform: devanagari``, so the writing of Sanskrit is one cited
    convention rather than a list of letter substitutions.  The function is
    whole-word because an abugida's letters depend on their neighbours (क is ka
    but क् is k), which no segment rewrite can express.
    """
    from .writing import devanagari as write

    form = "".join(tokens)
    written = write(form)
    if not written or written == form:
        return tokens, []
    return [written], [0]


def avestan(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Write the whole form in the Avestan alphabet (orthography, not a law).

    Used by a spelling file only: ``data/spelling/ave.yaml`` declares one rule
    with ``transform: avestan``, so the writing of Avestan is one cited
    convention (Hoffmann & Forssman 2004, pp. 44-46) rather than a list of
    letter substitutions.  Whole-word because the two glides are written by the
    vowel around them: *y* between vowels is 𐬌𐬌 *ii*, not 𐬫.
    """
    from .writing import avestan as write

    form = "".join(tokens)
    written = write(form)
    if not written or written == form:
        return tokens, []
    return [written], [0]


def greek(tokens: list[str], params: dict | None = None) -> tuple[list[str], list[int]]:
    """Write the whole form in the Greek alphabet (orthography, not a law).

    Used by a spelling file only: ``data/spelling/grc.yaml`` declares one rule
    with ``transform: greek``, so the writing of Greek is one cited convention
    (Smyth 1920, §§1-15 and 149; Allen 1987) rather than a list of letter
    substitutions.  Whole-word because the breathing and the acute depend on
    the nucleus they stand over and the final sigma on the end of the word.
    """
    from .greek import write

    form = "".join(tokens)
    written = write(form)
    if not written or written == form:
        return tokens, []
    return [written], [0]


TRANSFORMS = {
    "devanagari": devanagari,
    "greek": greek,
    "avestan": avestan,
    "grassmann": grassmann,
    "laryngeal_lengthening": laryngeal_lengthening,
    "bartholomae": bartholomae,
    "syllabic_laryngeals": syllabic_laryngeals,
}
