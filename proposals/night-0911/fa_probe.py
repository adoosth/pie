#!/usr/bin/env python3
"""Score a Persian (``fa``) orthographic layer against the whole glossary.

The orthographic layer is one step beyond the sound laws: ``pal__fa`` ends at a
phonemic form (``nām``, ``čeh``, ``gūš``) and ``data/spelling/fa.yaml`` says how
New Persian *writes* that form.  This probe asks, for every Persian word that
has a recorded ancestor:

* does the pipeline's closest derivation, written by the conventions, equal the
  recorded word character for character;
* and would ``coverage.py`` count it — the same match **plus** the
  ``spelling.plausible`` guard (same consonant skeleton and syllable count as
  the dictionary's own IPA), because a letter coincidence is not a spelling.

It reproduces ``tools/coverage.py``'s selection exactly: the ancestor attempt
whose output is closest (by character distance) to the attested word is the one
the spelling layer sees — chosen over every derivation, including one in which
no law fired — and only a spelling of a derivation that *did* fire a law is
counted.  A word whose nearest ancestor already equals the recorded word is
therefore reported separately (`zero-step picks`) instead of inflating the count.

    # before: no layer
    python3 proposals/night-0911/fa_probe.py --spelling /dev/null
    # default: the installed data/spelling/fa.yaml, if it exists
    python3 proposals/night-0911/fa_probe.py
    # a candidate file, not yet installed
    python3 proposals/night-0911/fa_probe.py --spelling /tmp/fa.yaml
    # ablation: what one convention is worth
    python3 proposals/night-0911/fa_probe.py --disable short_vowels

The miss tally is the worklist's question asked at the letter level: which
character pairs dominate the remaining gap.  It is diagnostic only — a pair that
recurs is not by itself a convention, and nothing here writes a rule.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling                     # noqa: E402
from pie.rules import RuleSet, apply_ruleset, derive  # noqa: E402
from pie.textio import enable_utf8_stdio          # noqa: E402
import coverage as cov                            # noqa: E402


def load_layer(path: Path | None) -> RuleSet | None:
    """Compile a spelling file the way ``pie.spelling.ruleset`` does."""
    if path is None:
        return None
    raw = data._load_yaml(path)
    if not isinstance(raw, dict):
        return None
    rs = RuleSet.from_dict(raw, "fa~", f"{path.stem}#spelling")
    rs.name = (raw.get("stage") or {}).get("name", f"{path.stem} spelling")
    written = {row.get("id"): row.get("replace") for row in (raw.get("rules") or [])}
    for rule in rs.rules:
        rep = written.get(rule.id)
        if isinstance(rep, str):
            rule._replace = list(rep)
    return rs


def write(form: str, layer: RuleSet | None, disabled=()) -> str:
    if layer is None:
        return form
    return apply_ruleset(form, layer, disabled=disabled)[0]


def spelled_problems(layer: RuleSet) -> list[str]:
    problems = []
    for rule in layer.rules:
        for ex in rule.examples:
            got = apply_ruleset(ex["in"], layer)[0]
            if got != ex["out"]:
                problems.append(f"{rule.id}: {ex['in']} -> {got} (expected {ex['out']})")
    return problems


#: Letters the pipeline can leave behind when the *closest* ancestor it tries is
#: itself a Pahlavi/Manichaean transliteration rather than a phonemic form: those
#: "misses" are a data and notation question, not a writing convention.
def other_script(form: str) -> bool:
    for ch in form:
        if not unicodedata.category(ch).startswith("L"):
            continue
        name = unicodedata.name(ch, "")
        if not name.startswith(("LATIN", "MODIFIER")):
            return True
    return False


#: Non-phonemic Latin debris of a transliterated ancestor (uppercase letters,
#: the Semitic ʾ for hamza, aspiration marks, the Turkish ğ, a stray c).
NOTATION = set("ʾʰğcΘŝṛ~'\u2060")


def notation_junk(form: str) -> bool:
    return any(ch in NOTATION or ch.isupper() for ch in form)


def signatures(spelled: str, word: str) -> Counter:
    """Character-level edit pairs between the written guess and the word."""
    out: Counter = Counter()
    sm = SequenceMatcher(a=spelled, b=word, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        left, right = spelled[i1:i2], word[j1:j2]
        if op == "replace":
            for k in range(max(len(left), len(right))):
                a = left[k] if k < len(left) else "∅"
                b = right[k] if k < len(right) else "∅"
                out[f"{a}→{b}"] += 1
        elif op == "delete":
            for a in left:
                out[f"{a}→∅"] += 1
        else:
            for b in right:
                out[f"∅→{b}"] += 1
    return out


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="fa")
    ap.add_argument("--spelling", type=Path, default=None,
                    help="candidate/installed spelling YAML (default: the installed layer)")
    ap.add_argument("--limit", type=int, default=0, help="0 = every identified word")
    ap.add_argument("--examples", type=int, default=12, help="matched examples to print")
    ap.add_argument("--top", type=int, default=25, help="miss signatures to print")
    ap.add_argument("--disable", default="",
                    help="comma-separated spelling rule ids to switch off (ablation)")
    args = ap.parse_args()

    path = args.spelling
    if path is None:
        installed = spelling.SPELLING_DIR / f"{args.lang}.yaml"
        path = installed if installed.exists() else None
    layer = load_layer(path)

    problems = spelled_problems(layer) if layer is not None else []
    rs = data.rulesets()
    chain = data.derivation_chain(args.lang)
    entries = data.lexicon(args.lang)
    eligible = [e for e in entries if cov.ancestor_starts(e, chain)]
    tested = cov.sample([e for e in eligible if not e.get("recon")], args.limit)

    off = [x for x in args.disable.split(",") if x]
    spelled = counted = plausible_blocked = 0
    best_count = 0
    examples: list[tuple[str, str, str, str]] = []
    tally: Counter = Counter()
    blocked: list[tuple[str, str, str]] = []

    errors = 0
    zero_step = 0
    misses = script_miss = junk_miss = 0
    for entry in tested:
        word = entry["word"].strip()
        candidates = cov.ancestor_starts(entry, chain)
        if not candidates:
            continue
        # Exactly coverage.py's choice: the ancestor attempt whose output is
        # closest to the word is the one the spelling layer sees, and it is
        # chosen over *all* derivations — including one in which no law fired —
        # so this probe and the published number agree by construction.
        best = None
        best_distance = 10**6
        best_steps = 0
        matched = False
        for stage, form in candidates:
            try:
                d = derive(form, chain[chain.index(stage):], rs)
            except Exception:
                errors += 1
                break
            if d.skipped:
                continue
            if d.output == word and d.steps:
                matched = True
                break
            dist = cov.distance(d.output.lower(), word.lower())
            if dist < best_distance:
                best_distance = dist
                best = (stage, form, d.output)
                best_steps = len(d.steps)
        if matched or best is None:
            continue
        best_count += 1
        stage, ancestor, output = best
        written = write(output, layer, off)
        if written != word:
            misses += 1
            if other_script(output):
                script_miss += 1
            elif notation_junk(output):
                junk_miss += 1
            else:
                tally.update(signatures(written, word))
            continue
        spelled += 1
        if not best_steps:
            zero_step += 1
            continue
        if spelling.plausible(output, entry.get("ipa") or ""):
            counted += 1
            if len(examples) < args.examples:
                examples.append((output, written, word, ancestor))
        else:
            plausible_blocked += 1
            if len(blocked) < 12:
                blocked.append((output, written, entry.get("ipa") or ""))

    print(f"layer            {path or '(none)'}")
    print(f"glossary         {len(entries)}")
    print(f"identified       {len(eligible)}")
    print(f"tested           {len(tested)}")
    print(f"spelled right    {spelled}")
    print(f"zero-step picks  {zero_step}  (closest ancestor fired no law: not counted)")
    print(f"counted (plaus.) {counted}")
    print(f"plaus. rejected  {plausible_blocked}")
    if tested:
        print(f"orth rate        {counted / len(entries):.4%} of glossary")
    if problems:
        print("\nexample failures in the layer:")
        for p in problems:
            print("  " + p)
    if examples:
        print("\nmatched examples (end form → written = recorded):")
        for output, written, word, ancestor in examples:
            print(f"  {ancestor} → {output} → {written} = {word}")
    if blocked:
        print("\nspelled right but the phonemes do not fit the recorded IPA:")
        for output, written, ipa in blocked:
            print(f"  {output} → {written}   (ipa {ipa})")
    print(f"\nmisses           {misses} of {best_count} attempted")
    print(f"  ancestor still in another script   {script_miss}")
    print(f"  ancestor left non-phonemic letters {junk_miss}")
    print(f"  ordinary spelling misses           {misses - script_miss - junk_miss}")
    if tally:
        print(f"\ntop miss signatures (character pairs, spelled guess → recorded word):")
        for sig, n in tally.most_common(args.top):
            print(f"  {n:4d}  {sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
