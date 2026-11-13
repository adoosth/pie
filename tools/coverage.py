#!/usr/bin/env python3
"""Measure how much of each lexicon the registered rules can derive exactly.

The project rule (2026-11-07) is strict: a word counts as *reconstructed*
only when a registered rule chain turns an ancestor form into the attested word,
character for character.  Approximations are reported, never counted.

A word may start from the PIE etymon **or from any ancestor recorded in its
Wiktionary inheritance chain**: the question is whether the rules explain the
last mile, not whether every earlier stage happens to be modelled.

    python tools/coverage.py                  # full corpus (all eligible words)
    python tools/coverage.py --limit 500      # quick sample per language
    python tools/coverage.py --tiers established

Writes:
  data/coverage.json     machine-readable report (web UI + CLI)
  docs/COVERAGE.md       per-language table with progress bars
  docs/coverage.svg      progress chart embedded in the README
  README.md              refreshes the block between the coverage markers
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time

import yaml
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import categories as cats  # noqa: E402
from pie import steps as chain_steps  # noqa: E402
from pie import citation, data, pathways, script, senses as lexemes, service, spelling  # noqa: E402
try:                                      # the loan table is optional
    from pie import loans                  # noqa: E402
except Exception:                          # pragma: no cover
    loans = None
from pie.phonology import detokenize, tokenize
from pie.rules import derive
from pie.textio import enable_utf8_stdio         # noqa: E402
from pie.service import (_ancestry_triples, _compound_pieces,    # noqa: E402
                        _own_construction, _phonological_form,
                         _pie_form, _same_form, normalise_etymon, seam_of,
                         stress_only)

README_START = "<!-- coverage:start -->"
README_END = "<!-- coverage:end -->"

#: Every stored headword's band, for the pages that list words instead of
#: measuring them (the glossary).  Written beside coverage.json by the same run,
#: so a colour on a glossary row and a number in the report can never come from
#: two different measurements (2026-11-09).
INDEX = ROOT / "data" / "category_index.json.gz"

# Languages the README always shows, in this order, when they have a glossary.
KEY_LANGS = [
    "ine-pro", "hit", "gem-pro", "ang", "en", "goh", "de", "got", "non",
    "la", "it", "grc", "el", "iir-pro", "ira-pro", "peo", "pal", "fa",
    "ave", "sa", "sla-pro", "lt", "sq", "hy", "xcl", "sga", "txb",
]


def inherited(entry: dict) -> bool:
    """True when Wiktionary records this word as *inherited* from PIE.

    Loanwords that merely share a PIE etymon (English ``book`` vs. German
    ``Buch``) never travelled through the chain and must not be counted.
    """
    return any(l == "ine-pro" and rel != "borrow" for l, _w, rel in _ancestry_triples(entry))


def approved_words() -> frozenset[tuple[str, str]]:
    """Words the project approved as "fully explained with adjustments"."""
    return cats.approved_words(ROOT / "data" / "adjusted.yaml")


def _estimate_label(estimate: dict) -> str:
    """The figure an estimate row is measured against, with its entries beside it.

    Dehkhoda's 343,466 are *entries*, and 180,492 of them are phrases; the row
    carries its own `words` count, so the table says "160,802 words (of 343,466
    entries)" instead of letting the entry count stand as a word count
    (2026-11-10).
    """
    words = estimate.get("words")
    total = f"{int(estimate.get('total') or 0):,}"
    if not words:
        return total
    return f"{int(words):,} words (of {total} entries)"


def vocabulary_estimates() -> dict[str, dict]:
    """``lang -> estimate`` from `data/vocabulary_estimates.yaml`.

    Used only for the `unidentified` band: words a language is thought to have
    that no glossary here holds.  A missing or empty file means no estimate, and
    then the band is not reported at all.

    The whole row travels with the number — source, URL, year, what it counts
    and how to read it — because a grey band is worthless without the sentence
    behind it: 343,466 is Dehkhoda's entry count, not "how many Persian words
    exist", and the page has to say so where the number is printed
    (2026-11-09).
    """
    path = ROOT / "data" / "vocabulary_estimates.yaml"
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for row in payload.get("estimates") or []:
        lang, total = row.get("lang"), row.get("total")
        if lang and isinstance(total, (int, float)) and total > 0:
            out[str(lang)] = {k: v for k, v in row.items() if k != "lang"}
    return out


def attach_review(report: dict) -> dict:
    """Add the review backlog's per-language finding counts to a coverage report.

    The backlog (`data/review_backlog.yaml`, written by `tools/backlog.py`)
    holds the words whose recorded chain contradicts itself.  A word there is
    still in its band — the measurement of the form did not change — but the
    page has to say how many words in a language are *under review*, or a green
    number reads as settled when the record itself is not (2026-11-09).
    Counts come from the file's `counts.by_language`, which covers every
    finding, not only the 3,900 rows the file lists.
    """
    path = ROOT / "data" / "review_backlog.yaml"
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return report
    counts = payload.get("counts") or {}
    by_language = {lang: sum((kinds or {}).values())
                   for lang, kinds in (counts.get("by_language") or {}).items()}
    if not by_language:
        return report
    langs = report.get("languages") or {}
    for lang, n in by_language.items():
        if lang in langs:
            langs[lang]["review"] = n
    report["review"] = {
        "generated": payload.get("generated"),
        "findings": sum((counts.get("by_kind") or {}).values()),
        "by_kind": counts.get("by_kind") or {},
        "by_language": by_language,
        "listed": len(payload.get("words") or []),
    }
    return report


def loan_class(entry: dict) -> str | None:
    """``non_pie`` / ``ie_loan`` / ``None`` for a recorded borrowing.

    Uses `pie.loans` when it is present; otherwise falls back to the older
    ancestry test, which can tell "outside the family" from "inside" but not
    which sister branch.
    """
    if loans is not None:
        try:
            kind = loans.classify(entry, entry.get("lang"))
            # The loan module speaks of "non_ie"; the coverage band is
            # "non_pie".  One adapter, so the two vocabularies cannot drift.
            return "non_pie" if kind == "non_ie" else kind
        except Exception:
            pass
    borrow = {_row_lang([l, w, rel]) for l, w, rel in (entry.get("anc") or [])
              if str(rel).lower() in BORROW_RELATIONS}
    borrow.discard("")
    if not borrow:
        return None
    return "non_pie" if _is_non_ie(borrow) else "ie_loan"


def distance(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sample(rows: list[dict], limit: int) -> list[dict]:
    if not limit or len(rows) <= limit:
        return rows
    step = len(rows) / limit
    return [rows[int(i * step)] for i in range(limit)]


def ancestor_starts(entry: dict, chain: list[str]) -> list[tuple[str, str]]:
    """Every usable ancestor form recorded for this word, PIE first.

    This is the page's own function, called rather than copied: a counter with
    its own idea of where a ladder starts drifted from the word page twice
    (2026-11-09: the "root promotion" the audit found in 46 ladders was green in
    the release and red on the page). A published number must be the number the
    page shows.
    """
    return service.ancestor_starts(entry, chain)


# --- how a word's recorded ancestry is classified (2026-11-09) ---------------
# The coverage page shows, per language, what the corpus *is*: how many words
# have an ancestor at a modelled stage, how many are recorded as borrowed,
# how many record an etymology the model cannot place, and how many record
# none.  The classification is a fact about the record, not a run of the laws,
# so it is computed once per entry and never folded into `exact`.
BORROW_KEYS = {":bor", ":lbor", ":slbor", ":obor", ":ubor"}
BORROW_RELATIONS = {"borrow", "borrowed", "lbor", "slbor", "obor", "ubor"}
_LANG_BRANCH: dict[str, str] | None = None


def _lang_branch() -> dict[str, str]:
    global _LANG_BRANCH
    if _LANG_BRANCH is None:
        try:
            raw = json.loads((ROOT / "data" / "language_names.json").read_text(encoding="utf-8"))
            _LANG_BRANCH = {k: v.get("branch", "") for k, v in raw.get("languages", {}).items()}
        except Exception:
            _LANG_BRANCH = {}
    return _LANG_BRANCH


def _known_codes() -> set[str]:
    """Every language code the data knows: the registry plus the names table."""
    try:
        return set(_lang_branch()) | set(data.languages())
    except Exception:
        return set()


def _row_lang(row: list) -> str | None:
    """The language a row names, or None.

    A row is ``[target, word, relation]`` where the target is either a
    language code (``['enm', 'dixionare', 'inherit']`` names Middle English)
    or a keyword whose word carries the language (``[':bor', 'ar:أَب',
    'root']`` names Arabic).  An affix target (``[':af', 'non-', 'prefix']``)
    names no language and must not count as an unmodelled ancestor.
    """
    if not row:
        return None
    head = str(row[0])
    known = _known_codes()
    if not head.startswith(":"):
        return head if head in known else None
    if len(row) > 1 and isinstance(row[1], str) and ":" in row[1]:
        code = row[1].split(":")[0]
        return code if code in known else None
    return None


def _root_langs(entry: dict) -> set[str]:
    return {c for c in (_row_lang(r) for r in (entry.get("anc") or [])
                        if isinstance(r, list) and r) if c}


def ancestry_kind(entry: dict, modelled: set[str]) -> str:
    """``inherited`` | ``borrowed`` | ``outside`` | ``unlinked`` | ``none``.

    * inherited — an ancestry row names an ancestor at a modelled stage;
    * borrowed  — the record marks the etymon borrowed (``:bor`` and family);
    * outside   — an ancestry row names a language the model does not hold
                  (Arabic, French, Chinese …) without a borrowing keyword;
    * unlinked  — an etymology is recorded but no ancestor language survived;
    * none      — neither an etymology nor an ancestry row.
    """
    rows = [r for r in (entry.get("anc") or []) if isinstance(r, list) and r]
    langs = _root_langs(entry)
    if langs & modelled:
        return "inherited"
    if any(str(r[0]) in BORROW_KEYS or (len(r) > 2 and str(r[2]) in BORROW_RELATIONS) for r in rows):
        return "borrowed"
    if langs:
        return "outside"
    if rows or entry.get("etym"):
        return "unlinked"
    return "none"


def _is_non_ie(roots: set[str]) -> bool:
    branch = _lang_branch()
    return any(branch.get(r, "").startswith("Contact") or not branch.get(r) for r in roots)


def exact_kind(output: str, target: str) -> str | None:
    """``strict`` | ``notation`` | None — how the laws' form meets the record.

    ``strict`` is the same string.  ``notation`` is the same phonological
    string with the stress written differently: the dictionaries print an acute
    on the vowel (*waydáyati*) and the engine writes its own stress token
    (*waydˈayati*).  The word page has always called those two a match
    (`service._same_form`); the coverage counter compared raw strings and
    therefore reported Proto-Iranian as 7/338 exact when 207 of the first 416
    words are the same form, character for character, once the two spellings of
    one accent are recognised (2026-11-09).  Nothing else is forgiven: the
    comparison still rejects every letter, macron and length that differs.

    The strict figure stays in the report (``exact_strict``) so an older number
    can be compared with a newer one without the notation rule in between.
    """
    if output == target:
        return "strict"
    # A morpheme boundary is not notation: the laws never write a hyphen, so a
    # hyphen in the record marks a bound form or an affix, and a word whose
    # only difference is "un-" against "un" is not a character-for-character
    # reconstruction.  The same holds for a lemma the record writes as two
    # words.  Mill's audit of this rule (proposals/night-0911/notation-audit.md,
    # 2026-11-09) measured 238 hyphen pairs, 152 thorn pairs, 5 bracket pairs,
    # 3 breve pairs and 2 space pairs hiding in the "notation" count; the
    # spelling layer can win them back honestly, this counter cannot.
    if ("-" in target) != ("-" in output):
        return None
    if bool(re.search(r"\s", target)) != bool(re.search(r"\s", output)):
        return None
    if stress_only(output, target):
        return "notation"
    return None


def _stress_free(form: str) -> str:
    """The form with its stress marks removed, everything else untouched.

    Two dictionaries write one accent two ways; they do not write one letter two
    ways here.  þ against θ, or a hyphen the laws never produce, is a different
    claim and is left to the orthographic layer.
    """
    return detokenize([t for t in tokenize(form) if t not in {"ˈ", "ˌ"}])


#: The notation table is the page's own (`service._LONG_VOWEL_NOTATION`), never
#: a copy: a counter with its own idea of which characters are the same letter
#: drifts from the page it is supposed to measure (2026-11-12, critic P2).
_LONG_VOWEL_NOTATION = service._LONG_VOWEL_NOTATION


def _bound_pair(output: str, target: str) -> bool:
    """Whether the only difference is the hyphen the record writes.

    The laws never write a morpheme boundary, so ``a-`` against *a* and
    ``-kas`` against *kas* can never be a character-for-character match.  It
    is still the same form: the dictionary marks that the word is bound, and
    the derivation is about its letters.  Its own column, never ``exact``
    (2026-11-09, after the miss audit measured 16 Proto-Iranian and 45
    Proto-Indo-Iranian words lost to this and nothing else).
    """
    if "-" not in target or "-" in output:
        return False
    return exact_kind(output.replace("-", ""), target.replace("-", "")) is not None


def _identity_hit(outputs: list[tuple[str, int, str]], target: str,
                  entry: dict) -> tuple[str, str] | None:
    """The form the path already has, when no law had to fire.

    A word whose ancestor is character-identical to the attested form (موش /
    *múHs) was a permanent miss: the counter required one applied rule before it
    would compare anything, and a correct path that needs no change has no
    rule to fire.  Counting it in ``exact`` would break the figure's meaning
    (no law demonstrated anything), so it is measured apart, with the accent
    read as notation exactly as everywhere else (2026-11-09: 32 Proto-Iranian,
    1 Proto-Indo-Iranian).
    """
    record = (entry.get("translit") or "").translate(_LONG_VOWEL_NOTATION)
    for output, steps, stage in outputs:
        if steps:
            continue
        heard = output.translate(_LONG_VOWEL_NOTATION)
        if output == target or stress_only(output, target) or (
                record and (heard == record or stress_only(heard, record))):
            # ``stress_only`` answers False for two identical forms when
            # neither writes an accent, so the identity a recorded reading
            # reaches exactly would otherwise never be counted (2026-11-09:
            # Persian سنگ from pal sang, whose laws apply no rule because the
            # reading already is the form).
            return output, stage
    return None


def _exact_under_laws(entry: dict, chain: list[str], rulesets, tiers) -> bool:
    """Whether the rules reproduce this (reconstruction-only) row exactly.

    The same strict test the attested figure uses, so the number reported
    beside it means the same thing: a recorded ancestor, at least one law
    applied, and the output identical to the form the glossary holds.
    """
    target = entry["word"].strip()
    for stage, form in ancestor_starts(entry, chain):
        try:
            d = derive(form, chain[chain.index(stage):], rulesets, tiers=tiers)
        except Exception:
            return False
        if d.skipped:
            continue
        if d.output == target and d.steps:
            return True
    return False


def pct(x: float) -> str:
    p = 100 * x
    if p == 0:
        return "0%"
    if p < 0.01:
        return f"{p:.4f}%"
    if p < 1:
        return f"{p:.2f}%"
    if p < 10:
        return f"{p:.1f}%"
    return f"{p:.0f}%"


def bar(frac: float, width: int = 20) -> str:
    filled = int(round(max(0.0, min(1.0, frac)) * width))
    if frac > 0 and filled == 0:
        return "▏" + "░" * (width - 1)
    return "█" * filled + "░" * (width - filled)


def orthographic_hit(outputs: list[tuple[str, int, str]], lang: str, target: str,
                     ipa: str) -> tuple[str, int, str] | None:
    """The derived form whose spelling of the attested word is right, if any.

    The orthographic layer has to be tried on **every** candidate form, not only
    on the one whose Latin letters happen to be nearest to the attested word:
    for a language written in another script that distance is noise, and a word
    whose spelling is exact would be thrown away before the spelling was ever
    applied (2026-11-09, Sanskrit: the laws' form is written देवस् and the record
    writes देव, and no Latin-ASCII distance can see that the letters agree).
    """
    if not spelling.applies(lang):
        return None
    for output, steps, stage in outputs:
        if steps and spelling.spell(output, lang) == target and \
                spelling.confirms(output, target, ipa, lang):
            return output, steps, stage
    return None


def citation_hit(outputs: list[tuple[str, int, str]], lang: str, target: str,
                 ipa: str) -> tuple[str, int, str, str] | None:
    """The derived form that is the *stem* of a lemma the laws produce inflected.

    Sanskrit dictionaries cite a noun by its stem (देव devá-), while the laws
    end where the recorded ancestor ends (*deywós is a nominative, so the chain
    gives deváḥ).  That is a fact about how the dictionary cites the word, not
    about the sound laws, so it is counted in its own column and never in
    `exact`.  Only an ending the language file declares may be dropped, the
    remaining form must spell the lemma exactly, and the phonemes must still be
    a plausible reading of the entry's own IPA (2026-11-09).
    """
    pairs = citation.pairs(lang)
    if not pairs or not spelling.applies(lang):
        return None
    for output, steps, stage in outputs:
        if not steps:
            continue
        for end, cited in pairs:
            if not output.endswith(end) or len(output) <= len(end) + len(cited):
                continue
            stem = output[: -len(end)] + cited
            if spelling.spell(stem, lang) == target and \
                    spelling.confirms(stem, target, ipa, lang):
                return stem, steps, stage, end, output
    return None


def measure(lang: str, meta: dict, chain: list[str], rulesets, tiers, limit: int,
            default_paths: dict | None = None) -> dict:
    entries = data.lexicon(lang)
    glossary = len(entries)
    pie_linked = sum(1 for e in entries if inherited(e))
    # A glossed word Wiktionary keeps in its Reconstruction: namespace is not
    # an attested word, and the figure is a count of attested forms the laws
    # reproduce. Its rows are measured on their own and reported beside the
    # number, never inside it (2026-11-08: green must mean a text
    # spells it).
    modelled = set(chain)
    kinds = [ancestry_kind(e, modelled) for e in entries]
    borrowed = sum(1 for k in kinds if k == "borrowed")
    outside = sum(1 for k in kinds if k == "outside")
    unlinked = sum(1 for k in kinds if k == "unlinked")
    no_etym = sum(1 for e in entries if not (e.get("anc") or e.get("etym")))
    non_ie = sum(1 for k, e in zip(kinds, entries)
                 if k in ("borrowed", "outside") and _is_non_ie(_root_langs(e)))
    recon = [e for e in entries if e.get("recon")]
    eligible = [e for e in entries if ancestor_starts(e, chain)]
    identified = len(eligible)
    used = sample([e for e in eligible if not e.get("recon")], limit)
    recon_eligible = [e for e in recon if ancestor_starts(e, chain)]
    recon_exact = sum(1 for e in recon_eligible if _exact_under_laws(e, chain, rulesets, tiers))
    # The six categories describe attested vocabulary.  A row the glossary
    # itself marks as a reconstruction is measured in its own column and never
    # counted as an attested word (2026-11-09).
    # A word, not a part of speech and not a dictionary row: the entries that
    # share a spelling *and* an etymology are one lexeme (noun and verb of
    # *bank*), while two unrelated words that happen to be spelled alike are
    # two (2026-11-09).  The count of words a language holds is therefore the
    # number of senses, and the bands index stores one band per sense.
    sense_rows = lexemes.for_lexicon(entries)
    attested = [g["rep"] for g in sense_rows
                if any(not e.get("recon") for e in g["entries"])]
    # The six bands are for attested languages only (2026-11-09).  A proto
    # stage's words are reconstructions and need their own scheme, which is
    # deliberately later; it is still measured in the layer columns above.
    categorical = str(meta.get("kind", "attested")) == "attested"

    exact = exact_pie = case_only = near = errors = 0
    explained = 0
    exact_noted = 0
    pathway = 0
    orth = 0
    lemma = 0
    constructed = 0
    construct_examples: list[dict] = []
    identity = 0
    bound_form = 0
    joined = 0
    joined_examples: list[dict] = []
    scripted = 0
    script_examples: list[dict] = []
    from_stage: Counter[str] = Counter()
    rules_used: Counter[str] = Counter()
    examples: list[dict] = []
    pathway_examples: list[dict] = []
    orth_examples: list[dict] = []
    lemma_examples: list[dict] = []
    identity_examples: list[dict] = []
    bound_examples: list[dict] = []
    closest: list[dict] = []
    approved = approved_words()
    verdicts: dict[int, dict] = {}
    #: word -> the words its page draws above it, for the pass that keeps a
    #: word no greener than its ancestors (`demote_below_ancestors`).
    above: dict[str, list[tuple[str, str]]] = {}
    counts = cats.empty_counts()
    bands: dict[str, dict[int, str]] = {}
    sense_of = {id(g["rep"]): g["sense"] for g in sense_rows}
    reasons: Counter[str] = Counter()
    category_examples: dict[str, list] = {key: [] for key in cats.CATEGORIES}
    untested = 0
    started = time.time()

    for entry in used:
        target = entry["word"].strip()
        here = False
        # A join is a formation, not a derivation: two recorded pieces meet at
        # the headword and no single etymon has to become it.  Counted apart,
        # never as explained and never as a failure (2026-11-09).
        pieces = _compound_pieces(entry, lang)
        if pieces:
            joined += 1
            if len(joined_examples) < 8:
                joined_examples.append({
                    "word": target,
                    "etym": pieces[0].get("etym", ""),
                    "pieces": [p.get("form", "") for p in pieces[0].get("pieces", [])],
                })
        candidates = ancestor_starts(entry, chain)
        if not candidates:
            continue
        best_output = None
        best_steps = 0
        best_distance = 10**6
        best_stage = None
        matched_stage = None
        matched_by = None
        # Where the winning layer's form came from: green needs the PIE etymon.
        layer_stage = None
        tiers_fired: set[str] = set()
        tier_map: dict[str, set[str]] = {}
        orth_hit = None
        citation = None
        outputs: list[tuple[str, int, str]] = []

        for stage, form in candidates:
            start = chain.index(stage)
            try:
                d = derive(form, chain[start:], rulesets, tiers=tiers)
            except Exception:
                errors += 1
                break
            if d.skipped:
                continue
            outputs.append((d.output, len(d.steps), stage))
            tier_map[stage] = {step.tier for step in d.steps}
            if orth_hit is None:
                orth_hit = orthographic_hit([outputs[-1]], lang, target,
                                            entry.get("ipa") or "")
            if citation is None and orth_hit is None:
                citation = citation_hit([outputs[-1]], lang, target,
                                        entry.get("ipa") or "")
            # At least one registered rule must fire: an unchanged ancestor is
            # not evidence that the rules explain the attested form.
            kind = exact_kind(d.output, target) if d.steps else None
            if kind:
                matched_stage = stage
                matched_by = "laws"
                layer_stage = stage
                tiers_fired = tier_map.get(stage, set())
                here = True
                exact += 1
                if kind == "notation":
                    exact_noted += 1
                if stage == chain[0]:
                    exact_pie += 1
                from_stage[stage] += 1
                for step in d.steps:
                    rules_used[f"{step.stage}|{step.rule_id}"] += 1
                if len(examples) < 10:
                    examples.append({"stage": stage, "ancestor": form, "word": target, "output": d.output})
                break
            dist = distance(d.output.lower(), target.lower())
            if dist < best_distance:
                best_distance = dist
                best_output = d.output
                best_steps = len(d.steps)
                best_stage = stage

        if matched_stage is None and default_paths and (lang, target) in default_paths:
            # A word may record that one registered law never applied to it
            # (Middle English ``wolf`` is spelled with ⟨o⟩ but has /u/, so the
            # lowering of short *o to *ɔ misses it).  Such a word is counted
            # here and not in ``exact``: the strict law-only figure stays
            # comparable with older releases, and a per-word exception can
            # never raise it quietly (2026-11-08).
            off = list(default_paths[(lang, target)].get("disabled") or [])
            on = list(default_paths[(lang, target)].get("enabled") or [])
            for stage, form in candidates:
                start = chain.index(stage)
                try:
                    d = derive(form, chain[start:], rulesets, tiers=tiers, disabled=off, enabled=on)
                except Exception:
                    errors += 1
                    break
                if d.skipped:
                    continue
                # A word in another script can be completed by its own
                # pathway too: the laws give zˈanah and the record writes
                # 𐏀𐎴, which is the same word read sign by sign.  It counts as
                # a pathway, not as a letter-for-letter match (2026-11-09).
                fit = script.match(lang, d.output, target) if d.steps else None
                if (d.output == target and d.steps) or (fit and fit.get("ok")):
                    pathway += 1
                    here = True
                    matched_stage = stage
                    matched_by = "pathway"
                    layer_stage = stage
                    tiers_fired = {step.tier for step in d.steps}
                    if len(pathway_examples) < 8:
                        pathway_examples.append({"stage": stage, "ancestor": form, "word": target,
                                                 "output": d.output, "disabled": off, "enabled": on,
                                                 "translit": (fit or {}).get("translit", "")})
                    break

        if matched_stage is None and outputs:
            # A language written in its own script cannot be compared string for
            # string: the laws write *wˈarkah* and Old Persian writes 𐎺𐎼𐎣. The
            # script layer asks whether the form is a possible reading of those
            # signs, and counts it in its own column — never inside the attested
            # figure, which stays a claim about the dictionary's own spelling
            # (2026-11-08).
            for output, steps, stage in outputs:
                # The script layer asks whether the signs allow this reading.
                # For an abjad the signs allow far too much: Persian دوش can be
                # read dōš, duš or dūšā, and only the first two are what the
                # dictionary records.  A fit is therefore accepted only when
                # the entry's own reading agrees with it (2026-11-12 — the
                # same rule the word page's rungs follow).
                fit = service._script_fit(entry, output, strict=True)
                if not (fit and fit["ok"]) or not steps:
                    continue
                scripted += 1
                here = True
                matched_by = "script"
                layer_stage = stage
                tiers_fired = tier_map.get(stage, set())
                if len(script_examples) < 8:
                    script_examples.append({"stage": stage, "output": output,
                                            "word": target, "translit": fit["translit"]})
                break

        # The weaker layers below are a fallback, not an override: a word the
        # script layer already reads from the PIE etymon must not be re-labelled
        # "unchanged ancestor" because a later rung happens to equal the
        # dictionary's transliteration.  Before this guard Persian دان (whose
        # laws give dānā from PIE, with the recorded Middle Persian dān
        # differing) fell from the script layer to the identity layer and was
        # reported as reproduced only from Middle Persian (2026-11-10).
        if matched_stage is None and matched_by is None:
            if best_output is None:
                # Every derivation was skipped: a step of this chain has no
                # rule file.  The word is still classified — that gap is a
                # fact about the model, not a reason to leave the word out of
                # the bands (2026-11-09).
                matched_by = "gap"
            # The orthographic layer is scored on its own: a word the written
            # conventions reproduce is *spelled* right, not reconstructed by a
            # sound law.  Both numbers are reported; neither replaces the other.
            if orth_hit is not None:
                written, _steps, where = orth_hit
                orth += 1
                here = True
                matched_by = "orthographic"
                layer_stage = where
                tiers_fired = tier_map.get(where, set())
                if len(orth_examples) < 8:
                    orth_examples.append({"stage": where, "ancestor": written,
                                          "word": target, "output": written,
                                          "written": spelling.spell(written, lang)})
            if orth_hit is None and citation is not None:
                stem, _n, where, end, cited_output = citation
                lemma += 1
                here = True
                matched_by = "citation"
                layer_stage = where
                tiers_fired = tier_map.get(where, set())
                if len(lemma_examples) < 8:
                    lemma_examples.append({"stage": where, "word": target,
                                           "output": cited_output, "stem": stem,
                                           "ending": end,
                                           "written": spelling.spell(stem, lang)})
            # Two ways a word's letters are right without a law having moved
            # them: the path needed no change at all, or the record writes the
            # same form as a bound morpheme with a hyphen.  Both are their own
            # column and neither touches the historical ``exact`` figure.
            if orth_hit is None and citation is None and "-" not in target:
                ident = _identity_hit(outputs, target, entry)
                if ident is not None:
                    identity += 1
                    here = True
                    matched_by = "identity"
                    layer_stage = ident[1]
                    tiers_fired = tier_map.get(ident[1], set())
                    if len(identity_examples) < 8:
                        identity_examples.append({"word": target, "output": ident[0],
                                                  "stage": ident[1]})
            if orth_hit is None and citation is None and "-" in target:
                for output, _steps, stage in outputs:
                    if _bound_pair(output, target):
                        bound_form += 1
                        here = True
                        matched_by = "bound"
                        layer_stage = stage
                        tiers_fired = tier_map.get(stage, set())
                        if len(bound_examples) < 8:
                            bound_examples.append({"word": target, "output": output,
                                                   "stage": stage})
                        break
            # A form that already equals the word is not a near miss.  It is
            # still classified: the verdict below needs every entry, and a
            # `continue` here used to drop identical forms out of the bands.
            if best_output is not None and best_distance:
                if best_output.lower() == target.lower():
                    case_only += 1
                if best_distance <= max(1, len(target) // 4):
                    near += 1
                if len(closest) < 8:
                    closest.append({"pie": _pie_form(entry) or candidates[0][1],
                                    "stage": best_stage, "word": target,
                                    "output": best_output, "distance": best_distance})

        if here:
            explained += 1
        if matched_by is None and pieces:
            matched_by = "joined"
        # A word the record builds out of its own words is produced by that
        # construction rather than by a law: *andaswarō is *anda- + *swarō.
        # Measured with the same helper the word page uses, and only when no
        # derivation reached the word — a construction never overrides a law
        # (admin, 2026-11-13).
        construction = None
        if matched_by in (None, "joined"):
            try:
                construction = service.construction_path(entry, lang, chain)
            except Exception:
                construction = None

        kind_of_loan = loan_class(entry)
        # The recorded intermediate stages must agree too, not only the ends
        # (2026-11-09).  One extra walk of the chain, and only for a
        # word whose last mile already came out exact: a word that is not
        # reproduced cannot be green either way.
        differ: list[str] = []
        if matched_by in ("laws", "orthographic", "script"):
            try:
                differ = [row["stage"] for row in chain_steps.mismatches(
                    entry, lang, chain, rulesets, tiers=tiers)]
            except Exception:
                differ = []
        # A word with no etymology may still be made of its own language's
        # words: the record's own pieces first, then the seam this model reads.
        # A formation stands beside the six and is never green (2026-11-10).
        built, built_note = _formation_of(entry, lang, pieces)
        verdict = cats.verdict(
            recorded=bool(entry.get("anc") or entry.get("etym")),
            non_ie=kind_of_loan == "non_pie",
            ie_loan=kind_of_loan == "ie_loan",
            matched_by=matched_by,
            built_from=built,
            built_note=built_note,
            construction=construction,
            mismatched_steps=differ,
            tiers=tiers_fired,
            approved=(lang, target) in approved,
            # A word is PIE-linked only when its own record reaches a PIE
            # etymon.  `bool(matched_by)` used to stand in for that, which made
            # every word the laws derive somewhere "full" even when its chain
            # stopped at Proto-Germanic (English *et*; 2026-11-09).
            pie_linked=inherited(entry),
            # And green needs the derivation itself to start at the PIE etymon:
            # Old Persian 𐎣𐎠𐎶 is exact from Proto-Iranian, but nothing in the
            # model shows PIE becoming it, so it is yellow (2026-11-09).
            from_pie=bool(layer_stage) and layer_stage == chain[0],
            start_name=(data.languages().get(layer_stage or "", {}).get("name")
                        or layer_stage or ""),
            # Every rung of the recorded ancestry must be a word this model
            # holds, or the timeline has a hole and the band cannot be green
            # (admin, 2026-11-13).
            missing_steps=service.unrecorded_ancestry(entry, chain),
        )
        verdicts[id(entry)] = verdict
        # The words this page draws above it, kept for the second pass that
        # holds a word to its ancestors' bands (admin, 2026-11-13).  Only a
        # green word can be demoted, so only a green word keeps the list.
        if verdict["category"] in _MAYBE_WEAK:
            above.setdefault(target, []).extend(
                _drawn_pairs(candidates, pieces, lang))

    # Every attested word gets a verdict, not only the ones a rule could
    # reach: a borrowing, a word with no etymology and a word outside the
    # modelled chain are exactly the categories the project asked for.  In a
    # sampled run the eligible words that were not sampled stay out of the
    # count and are named, so a sample can never look like a measurement.
    for entry in attested if categorical else ():
        if id(entry) in verdicts:
            continue
        # A word the record builds out of its own words has no ancestor to
        # start from, so it is measured here rather than skipped: the
        # construction is what produces it, exactly as on its own page.
        try:
            construction = service.construction_path(entry, lang, chain)
        except Exception:
            construction = None
        if construction is None and ancestor_starts(entry, chain):
            untested += 1
            continue
        kind_of_loan = loan_class(entry)
        pieces = _compound_pieces(entry, lang)
        built, built_note = _formation_of(entry, lang, pieces)
        verdict = cats.verdict(
            recorded=bool(entry.get("anc") or entry.get("etym")),
            non_ie=kind_of_loan == "non_pie",
            ie_loan=kind_of_loan == "ie_loan",
            matched_by=None,
            built_from=built,
            built_note=built_note,
            construction=construction,
            pie_linked=inherited(entry),
            missing_steps=service.unrecorded_ancestry(entry, chain),
        )
        verdicts[id(entry)] = verdict
        if verdict["category"] in _MAYBE_WEAK:
            above.setdefault(entry["word"].strip(), []).extend(
                _drawn_pairs(ancestor_starts(entry, chain), pieces, lang))
    for entry in attested if categorical else ():
        verdict = verdicts.get(id(entry))
        if verdict is None:
            continue
        category = verdict["category"]
        if category == "unexplained":
            # The dictionary's own label does not explain the word, but it says
            # what kind of word is unexplained — a name, a compound the model
            # cannot cut, a bound morpheme (2026-11-10).
            verdict = {**verdict,
                       "reason": cats.unexplained_reason(entry.get("structure"))}
            verdicts[id(entry)] = verdict
        counts[category] = counts.get(category, 0) + 1
        if (category in ("full", "adjusted")
                and str(verdict.get("reason", "")).startswith("construction of")):
            # A word carried by its own registered construction instead of a
            # law.  Counted apart so the report says how much of the green
            # rests on a construction — never the partials that name one and
            # fail to spell the word (admin, 2026-11-13).
            constructed += 1
            if len(construct_examples) < 8:
                construct_examples.append({"word": entry["word"].strip(),
                                           "reason": verdict["reason"]})
        # One band per headword, first entry wins: the word page is keyed by
        # spelling and shows the first entry, so the glossary must colour the
        # same entry.  A homograph whose other reading would fall in another
        # band is the open gap named in docs/archive/UI_PLAN-2026-11.md.gz, not a second colour
        # (2026-11-09: the glossary words get the same colours).
        bands.setdefault(entry["word"].strip(), {})[sense_of[id(entry)]] = category
        reasons[f'{category}: {verdict["reason"]}'] += 1
        if len(category_examples[category]) < 8:
            category_examples[category].append({
                "word": entry["word"].strip(),
                "gloss": " · ".join(entry.get("gloss") or [])[:60],
                "reason": verdict["reason"],
            })

    n = len(used)
    estimate = vocabulary_estimates().get(lang)
    # A dictionary's entries are not all words: when the row names a `words`
    # figure (Dehkhoda heads 180,492 phrases), the grey band is measured against
    # the words, and the quoted entry count is still printed beside it
    # (2026-11-10).
    estimate_total = int(estimate.get("words") or estimate["total"]) if estimate else 0
    return {
        "name": meta.get("name", lang),
        "glossary": glossary,
        "bands": bands,
        "above": above,
        "attested": len(attested),
        "categorised": len(attested) if categorical else 0,
        # What the language is thought to hold, and where that figure comes
        # from.  The grey band is this minus the words we hold; never a count.
        "estimate": (dict(estimate, unidentified=max(0, estimate_total - len(attested)),
                          band_base=estimate_total) if estimate else None),
        "identified": identified,
        "pie_linked": pie_linked,
        "reconstruction": len(recon_eligible),
        "reconstruction_exact": recon_exact,
        "eligible": len(eligible),
        "tested": n,
        "exact": exact,
        "exact_strict": exact - exact_noted,
        "exact_notation": exact_noted,
        "exact_pie": exact_pie,
        "explained": explained,
        "borrowed": borrowed,
        "outside": outside,
        "non_ie": non_ie,
        "unlinked": unlinked,
        "no_etym": no_etym,
        "pathway": pathway,
        "categories": (cats.summarise(
            counts, len(attested),
            unidentified=max(0, estimate_total - len(attested)) if estimate_total else None)
            if categorical else None),
        "category_reasons": dict(reasons.most_common(24)),
        "category_examples": category_examples,
        "categories_untested": untested,
        "case_only": case_only,
        "near": near,
        "errors": errors,
        "exact_rate": round(exact / glossary, 6) if glossary else 0.0,
        "orthographic": orth,
        # The words the writing conventions spell, with the phonemic form each
        # one came from: the report quotes them instead of asking the reader to
        # take the count on trust (2026-11-09: the column had a number and no
        # examples, unlike every other layer).
        "orthographic_examples": orth_examples,
        "lemma": lemma,
        "lemma_examples": lemma_examples,
        # Counted apart from every other layer: the laws were not shown to do
        # anything, the forms simply already agree.
        "identity": identity,
        "bound_form": bound_form,
        "joined": joined,
        # Of the words in the green bands, how many were produced by a
        # registered construction rather than by a chain of sound laws.
        "constructed": constructed,
        "construction_examples": construct_examples,
        # A step with no rule file is a gap in the model, not a failure of the
        # words: no law can reach them however good the data is (2026-11-09).
        "gaps": [f"{a} → {b}" for a, b in data.missing_stages(chain)],
        "joined_examples": joined_examples,
        "identity_examples": identity_examples,
        "bound_examples": bound_examples,
        "exact_orth": exact + orth + lemma,
        "script": scripted,
        "script_examples": script_examples,
        "orth_rate": round((exact + orth) / glossary, 6) if glossary else 0.0,
        "exact_of_tested": round(exact / n, 6) if n else 0.0,
        "identified_rate": round(identified / glossary, 6) if glossary else 0.0,
        "pie_rate": round(pie_linked / glossary, 6) if glossary else 0.0,
        "near_rate": round((exact + case_only) / n, 6) if n else 0.0,
        "from_stage": dict(from_stage.most_common()),
        "top_rules": rules_used.most_common(20),
        "seconds": round(time.time() - started, 2),
        "examples": examples,
        "pathway_examples": pathway_examples,
        "closest_misses": closest,
    }


def rule_index(rulesets) -> dict[str, dict]:
    """``target-stage|rule-id`` -> metadata (rule ids repeat across transitions)."""
    out = {}
    for (src, dst), rs in rulesets.items():
        for r in rs.rules:
            out[f"{dst}|{r.id}"] = {"id": r.id, "name": r.name, "from": src, "to": dst, "tier": r.tier}
    return out


# --- a word is never greener than the words above it -------------------------
# The admin's rule (2026-11-13): "A word can't be fully explained if any
# ancestor of it is partially explained or non-existent."  The page applies it
# live (`service._page_ancestors`), and the published index must apply it too,
# or a glossary row would stay green over a page that reads "partially
# explained" — the row and the page are the same claim in two places.
#
# The counter cannot ask a page for its ancestor's band: that is a whole
# ladder per word, and this run measures 591,000 of them.  It does not need to.
# Every word it has measured is in `bands` already, so the rule is a second
# pass over the words the page draws: oldest stage first, so an ancestor's band
# is final before the word below it is read.
_MAYBE_WEAK = frozenset({"full", "adjusted"})
_WEAK_BANDS = frozenset({"partial", "unexplained"})


def _band_key(form: str) -> str:
    """A form as the index spells it: no asterisk, hyphen, stress or space.

    A record names its ancestor the way the dictionary writes it (*h₂entó-),
    the glossary heads it the way the language spells it (h₂entó-).  The
    comparison is one spelling, so the notation around it is dropped — the same
    rule the rest of the project follows (notation is not spelling).
    """
    return re.sub(r"[\s*\-\u00ad]+", "", str(form or ""))


def _drawn_pairs(candidates, pieces, lang: str) -> list[tuple[str, str]]:
    """The words a page draws above its headword, as (language, word).

    Two shapes reach a timeline and both are ancestors of the word: the rungs
    of its recorded ancestry (``ancestor_starts``, the page's own function) and
    the pieces of a construction, each of which is a word with its own page.
    """
    out: list[tuple[str, str]] = []
    for stage, form in candidates or ():
        out.append((str(stage), str(form)))
    for join in pieces or ():
        for index, piece in enumerate(join.get("pieces") or ()):
            if not piece.get("known"):
                continue
            # A bound morpheme is grammar, not a word: it has no page whose
            # band could be weaker, and the page skips it for the same reason
            # (`service.drawn_words`).  ـدان and ـی are pieces of چایدان and
            # واری; neither may cost the word its band.
            if service._bound_piece(str(piece.get("pos") or ""),
                                    str(piece.get("form") or ""), index):
                continue
            out.append((str(piece.get("lang") or lang),
                        str(piece.get("word") or piece.get("form") or "")))
    return out


def demote_below_ancestors(bands: dict[str, dict[str, dict[int, str]]],
                           above: dict[str, dict[str, list]],
                           order: list[str]) -> dict[str, Counter]:
    """Turn a green word to `partial` when a word it draws above it is not green.

    `bands` is mutated in place, one entry per sense, and the counts dropped per
    language are returned so the report can say the same thing the index does.
    The sweep repeats until nothing changes: a demotion makes the word a weak
    ancestor for the words below it, and a language order is not a proof when a
    record names a form in its own stage.
    """
    exact: dict[tuple[str, str], str] = {}
    loose: dict[tuple[str, str], str] = {}
    for lang, words in bands.items():
        for word, senses in words.items():
            for band in senses.values():
                exact.setdefault((lang, word), band)
                loose.setdefault((lang, _band_key(word)), band)

    def band_above(lang: str, form: str) -> str:
        found = exact.get((lang, form))
        if found is None:
            found = loose.get((lang, _band_key(form)))
        return str(found or "")

    dropped: dict[str, Counter] = {}
    for _ in range(8):
        changed = False
        for lang in order:
            for word, needs in (above.get(lang) or {}).items():
                senses = (bands.get(lang) or {}).get(word) or {}
                for sense, band in list(senses.items()):
                    if band not in _MAYBE_WEAK:
                        continue
                    if not any(band_above(stage, form) in _WEAK_BANDS
                               for stage, form in needs):
                        continue
                    senses[sense] = "partial"
                    dropped.setdefault(lang, Counter())[band] += 1
                    changed = True
        if not changed:
            break
    return dropped


def write_index(bands: dict[str, dict[str, dict[int, str]]], generated: str,
                inputs: dict[str, str] | None = None) -> None:
    """Write every headword's band: the glossary colours words, not counts.

    `data/coverage.json` holds counts and examples; a page that draws 400 words
    needs their bands, and re-measuring them per request would let the web UI
    disagree with the report.  A gzipped object ``lang -> word -> [band]`` is
    small enough to ship and exact enough to quote.

    The value is a *list* since 2026-11-09, one band per sense in the order the
    glossary stores them: ``bank`` the institution and ``bank`` the river's
    edge are different words and may sit in different bands, and a single band
    for the spelling could only ever colour one of them correctly.  A one-sense
    word stores a one-element list, so the schema stays uniform.

    Proto stages are absent on purpose: the six bands are for attested
    languages, and a reconstructed stage needs its own scheme.
    """
    bands = {lang: {word: [senses_[n] for n in sorted(senses_)]
                    for word, senses_ in words.items()}
             for lang, words in bands.items() if words}
    payload = {"schema": 2, "generated": generated,
               "inputs": inputs or {}, "bands": bands}
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    _atomic(INDEX, gzip.compress(raw, compresslevel=9, mtime=0))


def _atomic(path: Path, data: bytes) -> None:
    """Write a published artifact in one step.

    A nine-minute measurement ends with three files that a page reads
    immediately; a kill between the counter and the index used to leave new
    numbers beside an old band table, and a half-written index read back as
    "no colours at all".  Each file is written beside its destination and
    renamed, so a reader sees the old one or the new one and never a fragment
    (2026-11-12).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_markdown(report: dict, rows: list[tuple[str, dict]]) -> None:
    t = report["totals"]
    cat = report.get("categories") or {"counts": {}, "share": {}, "total": 0,
                                       "explained": 0, "explained_rate": 0}
    lines = [
        "# Exact-derivation coverage",
        "",
        "![Exact-derivation coverage by language](coverage.svg)",
        "",
        "Generated by `tools/coverage.py` on "
        f"{report['generated']}.  A word counts as **reconstructed** only when a registered",
        "rule chain turns an ancestor form into the attested word, character for character.",
        "The chain may start at the PIE etymon **or at any ancestor recorded in the word's",
        "inheritance chain**; approximations are reported as misses, never as matches.",
        "",
        "## The bands",
        "",
        "Every attested word in the glossary is counted once, so the shares below add up",
        "to 100%.  Five bands say how far the model explains it: **full**, **adjusted**,",
        "**partial**, **unexplained**, **non-PIE**.  Two facets are counted in the same",
        "total and are never green: `ie_loan` (a borrowing from another IE branch —",
        "recorded, inside the family, and not derived here) and `built` (a formation",
        "from the stage's own words — knowledge about the word, never a derivation).",
        "`unidentified` estimates the words the glossary does not hold yet, so it is",
        "never a count and never in a denominator.",
        "",
        "| band | words | share | definition |",
        "|---|---:|---:|---|",
        *[f"| **{meta['label']}** ({meta['short']}) | {cat['counts'].get(key, 0):,} | "
          f"{cat['share'].get(key, 0):.1f}% | {meta['definition']} |"
          for key, meta in (report.get("definitions") or {}).items() if key != "unidentified"],
        "",
        f"**{cat.get('explained', 0):,} of "
        f"{cat.get('total', 0):,} attested words are fully explained "
        f"({pct(cat.get('explained_rate', 0) / 100)}), and "
        f"{cat['counts'].get('ie_loan', 0):,} more are recorded loans from a",
        "sister branch. Both greens need a recorded origin carried all the way to the",
        "word — by cited laws, or by the record's own registered construction (the",
        "pieces spell it, each piece starts from a PIE etymon or from outside the",
        "family, and no recorded step disagrees). Light green is reached when a recorded",
        "intermediate stage disagrees, or when a change of ours is needed — never",
        "applied by the counter without a report for the law and one for the word in",
        "`data/adjusted.yaml`, and approval. A word reproduced only from a later",
        "ancestor (Old Persian 𐎣𐎠𐎶 from Proto-Iranian) is yellow.",
        "",
        "### By language",
        "",
        # The brown band is a column of its own: a per-language table that
        # leaves it out sends a reader looking for why a language's bands do
        # not add up to its stored words (2026-11-10).
        "| language | full | adjusted | partial | unexplained | non-PIE | IE loan | built | in review | explained | stored |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        *[f"| {r['name']} (`{lang}`) | {c['counts'].get('full', 0):,} | "
          f"{c['counts'].get('adjusted', 0):,} | {c['counts'].get('partial', 0):,} | "
          f"{c['counts'].get('unexplained', 0):,} | {c['counts'].get('non_pie', 0):,} | "
          f"{c['counts'].get('ie_loan', 0):,} | {c['counts'].get('built', 0):,} | "
          f"{r.get('review', 0):,} | {c.get('explained', 0):,} | "
          f"{c.get('total', 0):,} |"
          for lang, r in sorted(rows, key=lambda kv: (-(kv[1].get("categories") or {}).get("explained", 0),
                                                      kv[0]))
          if (c := (r.get("categories") or {})).get("total")],
        "",
        "## What a language is thought to hold",
        "",
        "The grey band is the difference between a language's estimated vocabulary and the",
        "words this glossary holds. It is printed apart from every count, because it is not a",
        "measurement: it is somebody's figure for how many words exist, and the figures are",
        "not the same kind of thing. A dictionary's headword count is what one dictionary",
        "collected; a *floor* is a dictionary that says outright it covers only a core; an",
        "*upper bound* includes phrases or inflected forms and overstates lemmas. Each row",
        "below names its source and quotes it, and a language with no cited figure reports",
        "no grey band at all (`data/vocabulary_estimates.yaml`).",
        "",
        "| language | estimated | not in the glossary | what the figure counts | source |",
        "|---|---:|---:|---|---|",
        *[f"| {r['name']} (`{lang}`) | {_estimate_label(e)} | {e.get('unidentified', 0):,} | "
          f"{e.get('counts', '')} ({e.get('basis', '')}) | "
          f"[{e.get('source', '')}]({e.get('url', '')}), {e.get('year') or 'n.d.'} |"
          for lang, r in sorted(rows, key=lambda kv: -(kv[1].get('estimate') or {}).get('total', 0))
          if (e := (r.get("estimate") or {}))],
        "",
        "Every figure above was read on the page it cites on 2026-11-09; the quotation for",
        "each one lives with the number in `data/vocabulary_estimates.yaml`, together with the",
        "candidates that were looked for and rejected.",
        "",
        "## The layers behind the bands",
        "",
        "**identified** = the entry has a recorded ancestor at a modelled stage.",
        "**PIE-linked** = the entry's recorded ancestry reaches Proto-Indo-European.",
        "**created as borrowed** = the record marks the etymon borrowed (`:bor` and family).",
        "**other source** = the record names an ancestor outside the word's modelled chain",
        "  (Latin into English, Arabic into Persian) without a borrowing keyword.",
        "**cited as stem** = the laws produce the word in another grammatical form and the",
        "dictionary cites the stem (`data/citation/sa.yaml`; the difference is the citation, not",
        "a sound change, so it is counted apart from both the laws and the spelling).", "",
        "**explained** = the union of the layers: reconstructed by the laws, a stored pathway,",
        "  spelled by the writing conventions, or reached through the language's own script.",
        "**reconstructed** = the registered rules reproduce the attested form exactly.",
        "  Stress is notation and not a difference: the dictionaries print an acute",
        "  (*waydáyati*) where the engine writes its own token (*waydˈayati*), and the",
        "  word page has always called those one form (`service._same_form`).  Every",
        "  letter, length and macron still has to agree; the strict string count is kept",
        "  in `data/coverage.json` as `exact_strict`.",
        "**+ orthography** = those plus the words the writing conventions"
        " (`data/spelling/`) spell correctly.  The two are reported apart on purpose:",
        "spelling is not a sound law, and a number that mixed them could not be compared",
        "with an older release.",
        "**unchanged** = the ancestor needs no change at all and the laws' form (which had",
        "  nothing to do) equals the record modulo its accent.  **bound form** = the record",
        "  writes the same form with a morpheme hyphen the laws never write (`a-`, `-kas`).",
        "  Both are counted apart: in neither did a rule demonstrate anything.",
        "",
        f"Corpus: **{t['glossary']:,} glossary entries**, {t['identified']:,} with a recorded ancestor,",
        f"**{t['exact']:,} reconstructed exactly**, of which **{t['exact_pie']:,} start at the",
        f"PIE etymon** ({pct(t['exact_rate'])} of the whole glossary,",
        f"{t['exact_orth']:,} once the orthographic layer is allowed ({pct(t['orth_rate'])}),",
        f"{pct(t['exact_of_identified'])} of words with a recorded ancestor; "
        f"{t['pie_linked']:,} reach a PIE etymon).  "
        f"Rules used: {report['tiers']}; sample: {report['sample']}.",
        "",
        *([f"**{t['pathway']:,} more** are completed by a word's own recorded pathway — a",
           "registered law that does not apply to that word, with the reason stored beside it",
           "(`data/pathways.jsonl`). They are counted apart and never added to the figure above:",
           "a per-word exception must be visible, not silent.", ""] if t.get("pathway") else []),
        *([f"**{t.get('script', 0):,} more** are reached through a language's own writing system, out of",
           "the words written in a script with a table in `data/script/` (Old Persian: the laws",
           "produce *wˈarkah* and the monument writes 𐎺𐎼𐎣, *va-ra-ka*). The signs do not spell",
           "every sound: a syllabary leaves a final /h/ unwritten and closes a final -i with a y-sign",
           "that adds no sound (𐎠𐎡𐎫𐎡𐎹 *a-i-t-i-y* is /aiti/), and an abjad leaves the short vowels",
           "to the reader, so such a word is a **reading** of the spelling rather than the same",
           "string; it is counted apart and never added to the figure above, which stays a claim",
           "about the dictionary's own spelling (2026-11-08).", ""]
          if t.get("script") else []),
        *([f"**{t.get('reconstruction_exact', 0):,} more** reproduce a form the glossary itself",
           "marks as a **reconstruction** (Wiktionary's `Reconstruction:` namespace), out of",
           f"{t.get('reconstruction', 0):,} reconstruction entries with a recorded ancestor.",
           "They are counted apart and never added:",
           "a reconstruction is not a word a text spells, and a figure of *attested* forms that",
           "included one could not be checked against the record (2026-11-08).", ""]
          if t.get("reconstruction") else []),
        "| language | identified | PIE-linked | borrowed | other source | reconstructed (laws) | + orthography | cited as stem | unchanged | bound form | through its script | built from pieces | explained | glossary | progress (explained / glossary) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for lang, r in rows:
        explained = r.get("explained", 0)
        lines.append(
            f"| {r['name']} (`{lang}`) | {pct(r['identified_rate'])} "
            f"({r['identified']:,}) | {r['pie_linked']:,} | {r.get('borrowed', 0):,} | "
            f"{r.get('outside', 0):,} | **{r['exact']:,}** | "
            f"{r['orthographic']:,} | {r.get('lemma', 0) or '—'} | "
            f"{r.get('identity', 0) or '—'} | {r.get('bound_form', 0) or '—'} | "
            f"{r.get('script', 0) or '—'} | {r.get('joined', 0) or '—'} | "
            f"{explained:,} | {r['glossary']:,} | "
            f"`{bar(explained / r['glossary'] if r['glossary'] else 0, 14)}` "
            f"{pct(explained / r['glossary'] if r['glossary'] else 0)} |"
        )
    lines += ["", "Glossaries with 0 identified words (for example Avestan and Middle Persian)",
              "have no ancestry links in the current data, so they are a data gap, not a rule",
              "failure.  They enter the metric as soon as their Wiktionary/MacKenzie entries",
              "are connected to an ancestor.", "",
              "## Rules used in successful reconstructions", "",
              "A rule that never applies in an exact derivation is unused, blocked by an earlier",
              "rule, or waiting for the orthography/morphology layers.  Counts come from the",
              "exact derivations above; use them to compare rule sets and to spot rules that",
              "apply often but never contribute to a match.", "",
              "| rule | transition | tier | applications |", "|---|---|---|---:|"]
    for row in report["rules_used"][:80]:
        lines.append(f"| `{row['id']}` {row['name']} | {row['from']} → {row['to']} | {row['tier']} | {row['count']:,} |")
    (ROOT / "docs" / "COVERAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_svg(report: dict, rows: list[tuple[str, dict]]) -> None:
    """One bar per language, banded by the six categories (2026-11-09).

    The old figure drew identified and exact as two nested widths; that said
    how much of the dictionary the model reached but not what happened to the
    rest.  Every stored word now occupies one band of the same bar, in the
    the project's colours, so a glance separates "not explained yet" from "not ours
    to explain".
    """
    rows = [(lang, r) for lang, r in rows if r.get("categorised")]
    width, row_h, top = 860, 27, 132
    name_w, bar_w = 170, 470
    height = top + row_h * len(rows) + 58
    colour = {"full": "#43a35e", "adjusted": "#9ccc65", "partial": "#f2c14e",
              "unexplained": "#ef6b6b", "non_pie": "#7a7a7a", "ie_loan": "#90a4ae"}
    order = ["full", "adjusted", "partial", "unexplained", "non_pie", "ie_loan"]
    labels = {"full": "fully explained", "adjusted": "with adjustments",
              "partial": "partially explained", "unexplained": "unexplained",
              "non_pie": "non-PIE", "ie_loan": "IE loan"}
    total = report.get("categories", {})
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">',
        f'<rect width="{width}" height="{height}" fill="#0d1117"/>',
        f'<text x="24" y="36" fill="#e8e6e1" font-size="19" font-weight="600">'
        f'pie — coverage by category</text>',
        f'<text x="24" y="60" fill="#8b98a8" font-size="12">'
        f'{total.get("explained", 0):,} of {total.get("total", 0):,} attested words fully explained '
        f'({pct((total.get("explained_rate", 0)) / 100)}) · {report["generated"]}</text>',
    ]
    x = 24
    for key in order:
        if key == "ie_loan" and not total.get("counts", {}).get("ie_loan"):
            continue
        parts.append(f'<rect x="{x}" y="73" width="12" height="12" fill="{colour[key]}" rx="2"/>')
        parts.append(f'<text x="{x + 18}" y="84" fill="#8b98a8" font-size="11">'
                     f'{labels[key]} {total.get("counts", {}).get(key, 0):,}</text>')
        x += 22 + len(labels[key]) * 6 + len(f'{total.get("counts", {}).get(key, 0):,}') * 6
    for i, (lang, r) in enumerate(rows):
        y = top + i * row_h
        name = str(r["name"])
        parts.append(f'<text x="24" y="{y + 11}" fill="#e8e6e1" font-size="12">{name}</text>')
        parts.append(f'<rect x="{name_w}" y="{y}" width="{bar_w}" height="14" fill="#161f2b" rx="3"/>')
        c = r.get("categories") or {}
        counts, denom = c.get("counts") or {}, c.get("total") or 0
        at = 0.0
        if denom:
            for key in order:
                n = counts.get(key, 0)
                if not n:
                    continue
                w = bar_w * n / denom
                parts.append(f'<rect x="{name_w + at:.1f}" y="{y}" width="{max(w, 1.2):.1f}" '
                             f'height="14" fill="{colour[key]}"/>')
                at += w
        parts.append(
            f'<text x="{name_w + bar_w + 14}" y="{y + 11}" fill="#8b98a8" font-size="11">'
            f'{c.get("explained", 0):,} / {denom:,} · {pct((c.get("explained_rate", 0)) / 100)}</text>'
        )
    parts.append(f'<text x="24" y="{height - 18}" fill="#5f6d7d" font-size="10">'
                 f'generated by tools/coverage.py · rerun after adding words or rules</text>')
    parts.append("</svg>")
    (ROOT / "docs" / "coverage.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_readme(report: dict, rows: list[tuple[str, dict]]) -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    if README_START not in text or README_END not in text:
        print("README markers missing; not updating README", file=sys.stderr)
        return
    t = report["totals"]
    key = [(lang, r) for lang, r in rows if lang in KEY_LANGS][:16]
    lines = [
        README_START,
        f"_Generated by `tools/coverage.py` on {report['generated']} from "
        f"{report['sample']}.  `identified` = a recorded ancestor exists; "
        f"`reconstructed` = registered rules reproduce the attested word exactly._",
        "",
        "```text",
        f"{'language':<20}{'identified':>16}{'reconstructed':>22}   progress (exact / glossary)",
    ]
    for lang, r in key:
        ident = f"{r['identified']:,} ({pct(r['identified_rate'])})"
        recon = f"{r['exact']:,} / {r['glossary']:,} ({pct(r['exact_rate'])})"
        lines.append(f"{r['name'][:19]:<20}{ident:>16}{recon:>22}   {bar(r['exact_rate'], 18)}")
    lines += [
        "```",
        "",
        *([f"**By the bands: {report['categories']['counts'].get('full', 0):,} fully explained, "
           f"{report['categories']['counts'].get('adjusted', 0):,} with approved adjustments, "
           f"{report['categories']['counts'].get('partial', 0):,} partially explained and waiting "
           f"for a law, {report['categories']['counts'].get('unexplained', 0):,} with no recorded "
           f"etymology, {report['categories']['counts'].get('non_pie', 0):,} non-PIE** — plus "
           f"{report['categories']['counts'].get('ie_loan', 0):,} recorded loans from a sister "
           f"branch, counted in the same total and never in green — and "
           f"{report['categories']['counts'].get('built', 0):,} words the record does not analyse "
           f"but whose own language's words do (a formation, never a derivation, so never green "
           f"either).", ""]
          if report.get("categories", {}).get("total") else []),
        f"**{t['exact']:,} of {t['glossary']:,} glossary entries reconstructed exactly "
        f"({pct(t['exact_rate'])}; {t['exact_pie']:,} of them straight from the PIE etymon); "
        f"{t['identified']:,} have a recorded ancestor and "
        f"{t['pie_linked']:,} reach a recorded PIE etymon.** "
        f"The orthographic layer adds {t.get('orthographic', 0):,} more spellings "
        f"({t.get('exact_orth', 0):,} in total, {pct(t.get('orth_rate', 0))}) — reported "
        "separately, because a writing convention is not a sound law. "
        + (f"{t.get('script', 0):,} more are reached through a language's own writing system "
           f"(Old Persian cuneiform: the laws produce *wˈarkah* and the monument writes 𐎺𐎼𐎣) — "
           f"counted apart, because the signs do not spell every sound (a syllabary leaves a "
           f"final /h/ to the reader, an abjad the short vowels). " if t.get("script") else "")
        + (f"{t['pathway']:,} further word{'s' if t.get('pathway') != 1 else ''} "
           f"{'are' if t.get('pathway') != 1 else 'is'} completed by a word's own recorded "
           f"pathway (a law that does not apply to it, with the reason stored) — also counted "
           f"apart, never added. " if t.get("pathway") else "")
        + "The percentage moves as words and rules are added — that is the point. "
        "Full table: [`docs/COVERAGE.md`](docs/COVERAGE.md).",
        "",
        "![Exact-derivation coverage by language](docs/coverage.svg)",
        README_END,
    ]
    text = text[: text.index(README_START)] + "\n".join(lines) + text[text.index(README_END) + len(README_END):]
    path.write_text(text, encoding="utf-8")


def _formation_of(entry: dict, lang: str, joins: list) -> tuple[tuple, str]:
    """The pieces a word is built from, and whose claim that is.

    The record's own construction (`{{com}}`/`{{af}}`, already read as `joins`)
    comes first; only a word the record leaves unanalysed is offered to the
    seam reader, and the note says so, because one is a quotation and the other
    is this repo's reading of a headword (2026-11-10).
    """
    if joins:
        pieces = tuple(str(p.get("form") or "")
                       for p in (joins[0].get("pieces") or []) if p.get("form"))
        if len(pieces) >= 2:
            return pieces, "as the record states"
    if entry.get("anc") or entry.get("etym") or entry.get("borrowed_from"):
        return (), ""
    # A `{{com}}`/`{{af}}` construction is the record's own statement even when
    # it sits on a word with no ancestry chain.  The page reads it with
    # `_own_construction`, so the counter must read it the same way or a word
    # would be brown in the list and red on its page (2026-11-10).
    own = _own_construction(entry, data.derivation_chain(lang))
    if own:
        pieces = tuple(str(p[0]) for p in own.get("pieces") or [] if p and p[0])
        if len(pieces) >= 2:
            return pieces, "as the record states"
    # The dictionary's own grammar label goes with the word, but it never picks
    # the cut: it is quoted beside the cut this model reads (2026-11-10).
    said = str(entry.get("pos_label") or "")
    seam = seam_of(lang, str(entry.get("word") or "").strip(), said)
    if seam and seam.get("verdict") == "unique":
        from pie import compounds
        return tuple(seam["parts"]), compounds.seam_note(entry)
    return (), ""


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--render-only-under", dest="unused_flag", nargs="?", help=argparse.SUPPRESS)
    ap.add_argument("--limit", type=int, default=0, help="words sampled per language (0 = all)")
    ap.add_argument("--tiers", default="", help="comma list, e.g. established (default: all registered)")
    ap.add_argument("--langs", nargs="*", help="only these language ids")
    ap.add_argument("--out", default=str(ROOT / "data" / "coverage.json"))
    ap.add_argument("--render-only", action="store_true",
                    help="rewrite the docs from an existing coverage.json (no measurement)")
    ap.add_argument("--docs", action="store_true",
                    help="also rewrite docs/COVERAGE.md, docs/coverage.svg and README (full runs only)")
    args = ap.parse_args()
    if args.render_only:
        report = json.loads(Path(args.out).read_text(encoding="utf-8"))
        attach_review(report)
        langs = report["languages"]
        rows = sorted(langs.items(), key=lambda kv: (-kv[1]["exact"], -kv[1]["glossary"]))
        write_markdown(report, rows)
        write_svg(report, rows)
        write_readme(report, rows)
        print(f"rewrote docs/COVERAGE.md, docs/coverage.svg and README.md from {args.out}")
        return 0

    tiers = set(args.tiers.split(",")) if args.tiers else None
    rulesets = data.rulesets()
    default_paths = pathways.defaults()
    known_rules = rule_index(rulesets)
    total_rules: Counter[str] = Counter()
    report = {
        "schema": 2,
        "generated": date.today().isoformat(),
        "inputs": data.measurement_inputs(),
        "tiers": sorted(tiers) if tiers else "all",
        "sample": "all eligible words" if not args.limit else f"{args.limit} words per language",
        "languages": {},
    }

    for lang, meta in data.languages().items():
        if args.langs and lang not in args.langs:
            continue
        chain = data.derivation_chain(lang)
        if not chain or lang == "ine-pro":
            continue
        if not any(l == lang for l, _ in data.available_lexicons()):
            continue
        r = measure(lang, meta, chain, rulesets, tiers, args.limit, default_paths)
        report["languages"][lang] = r
        total_rules.update(dict(r["top_rules"]))
        print(f"{lang:<10} {r['exact']:>5}/{r['glossary']:<7} glossary  "
              f"{r['exact']:>5}/{r['tested']:<6} tested  "
              f"{pct(r['exact_rate']):>8}  ({r['seconds']}s)")

    langs = report["languages"]
    # The per-word bands leave the published report: 245,000 words would dwarf
    # the numbers and the page does not read them from here.  They are written
    # as their own small index beside coverage.json (write_index).
    bands = {lang: r.pop("bands", {}) for lang, r in langs.items()}
    above = {lang: r.pop("above", {}) for lang, r in langs.items()}
    # Oldest stage first: the ancestor's band is final before the word below it
    # is read (see `demote_below_ancestors`).
    order = sorted(langs, key=lambda code: len(data.derivation_chain(code) or ()))
    demoted = demote_below_ancestors(bands, above, order)
    for lang, drop in demoted.items():
        row = langs.get(lang) or {}
        summary = row.get("categories") or {}
        counts_ = dict(summary.get("counts") or {})
        for band, n in drop.items():
            counts_[band] = max(0, counts_.get(band, 0) - n)
        counts_["partial"] = counts_.get("partial", 0) + sum(drop.values())
        row["categories"] = cats.summarise(
            counts_, row.get("categorised") or 0,
            unidentified=summary.get("counts", {}).get("unidentified"))
        reasons_ = row.get("category_reasons") or {}
        key = "partial: its ancestors are not fully explained"
        reasons_[key] = reasons_.get(key, 0) + sum(drop.values())
        row["category_reasons"] = dict(sorted(reasons_.items(),
                                              key=lambda kv: -kv[1])[:24])
    if any(demoted.values()):
        print(f"   {sum(sum(d.values()) for d in demoted.values()):,} green "
              "words demoted to partial: an ancestor they draw is not green")
    report["totals"] = {
        "glossary": sum(r["glossary"] for r in langs.values()),
        "attested": sum(r.get("categorised", 0) for r in langs.values()),
        "identified": sum(r["identified"] for r in langs.values()),
        "pie_linked": sum(r["pie_linked"] for r in langs.values()),
        "eligible": sum(r["eligible"] for r in langs.values()),
        "tested": sum(r["tested"] for r in langs.values()),
        "exact": sum(r["exact"] for r in langs.values()),
        "exact_strict": sum(r.get("exact_strict", r["exact"]) for r in langs.values()),
        "exact_notation": sum(r.get("exact_notation", 0) for r in langs.values()),
        "exact_pie": sum(r["exact_pie"] for r in langs.values()),
        "reconstruction": sum(r.get("reconstruction", 0) for r in langs.values()),
        "reconstruction_exact": sum(r.get("reconstruction_exact", 0) for r in langs.values()),
        "pathway": sum(r.get("pathway", 0) for r in langs.values()),
        "explained": sum(r.get("explained", 0) for r in langs.values()),
        "borrowed": sum(r.get("borrowed", 0) for r in langs.values()),
        "outside": sum(r.get("outside", 0) for r in langs.values()),
        "non_ie": sum(r.get("non_ie", 0) for r in langs.values()),
        "unlinked": sum(r.get("unlinked", 0) for r in langs.values()),
        "no_etym": sum(r.get("no_etym", 0) for r in langs.values()),
        "case_only": sum(r["case_only"] for r in langs.values()),
        "near": sum(r["near"] for r in langs.values()),
        "orthographic": sum(r.get("orthographic", 0) for r in langs.values()),
        "lemma": sum(r.get("lemma", 0) for r in langs.values()),
        "identity": sum(r.get("identity", 0) for r in langs.values()),
        "bound_form": sum(r.get("bound_form", 0) for r in langs.values()),
        "joined": sum(r.get("joined", 0) for r in langs.values()),
        "script": sum(r.get("script", 0) for r in langs.values()),
        "exact_orth": sum(r.get("exact_orth", r["exact"]) for r in langs.values()),
        "errors": sum(r["errors"] for r in langs.values()),
    }
    t = report["totals"]
    category_totals = cats.empty_counts()
    for r in langs.values():
        for key, value in ((r.get("categories") or {}).get("counts") or {}).items():
            category_totals[key] = category_totals.get(key, 0) + value
    unidentified = sum(((r.get("categories") or {}).get("counts", {})
                        .get("unidentified", 0)) for r in langs.values())
    report["categories"] = cats.summarise(category_totals, t["attested"],
                                          unidentified=unidentified or None)
    # The page draws its legend from the measurement, so a definition is
    # written once, here, and no template can drift from it (2026-11-09).
    report["definitions"] = {
        key: {k: v for k, v in meta.items()} for key, meta in cats.CATEGORIES.items()
    }
    t["exact_rate"] = round(t["exact"] / t["glossary"], 6) if t["glossary"] else 0.0
    t["identified_rate"] = round(t["identified"] / t["glossary"], 6) if t["glossary"] else 0.0
    t["exact_of_identified"] = round(t["exact"] / t["identified"], 6) if t["identified"] else 0.0
    t["pie_rate"] = round(t["pie_linked"] / t["glossary"], 6) if t["glossary"] else 0.0
    t["orth_rate"] = round(t["exact_orth"] / t["glossary"], 6) if t["glossary"] else 0.0
    t["explained_of_identified"] = (round(t["explained"] / t["identified"], 6)
                                    if t["identified"] else 0.0)
    report["rules_used"] = [
        {**known_rules.get(key, {"id": key.split("|")[-1], "name": "", "from": "?", "to": "?", "tier": "?"}),
         "key": key, "count": count}
        for key, count in total_rules.most_common()
    ]
    report["rule_applications"] = sum(total_rules.values())
    attach_review(report)

    # A sampled run must never overwrite the published reports: a sample
    # numerator over a full-corpus denominator is a wrong number, and a number
    # that cannot be reproduced is not a result (docs/PROGRAMME.md).
    publish = args.limit == 0 and args.docs and not args.langs
    if publish or args.out != str(ROOT / "data" / "coverage.json"):
        _atomic(Path(args.out), json.dumps(report, indent=1, ensure_ascii=False).encode("utf-8"))
        print(f"\n→ {args.out}")

    rows = sorted(langs.items(), key=lambda kv: (-kv[1]["exact"], -kv[1]["glossary"]))
    if publish:
        write_index(bands, report["generated"], report["inputs"])
        write_markdown(report, rows)
        write_svg(report, rows)
        write_readme(report, rows)
        print(f"→ {INDEX}  ({sum(len(v) for v in bands.values()):,} words banded)")
        print(f"→ {ROOT / 'docs' / 'COVERAGE.md'}")
        print(f"→ {ROOT / 'docs' / 'coverage.svg'}")
        print(f"→ README.md")
    else:
        print("sample run — docs/COVERAGE.md, README and coverage.svg left untouched "
              "(publish with a full run: no --limit, add --docs)")
    print(f"\ntotal: {t['exact']:,} / {t['glossary']:,} reconstructed exactly "
          f"({pct(t['exact_rate'])}); {t['identified']:,} with an ancestor, {t['pie_linked']:,} PIE-linked; "
          f"{report['rule_applications']:,} rule applications in matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
