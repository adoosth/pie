#!/usr/bin/env python3
"""The council: measure a candidate law against every language it can touch.

`whatif.py` answers "what does this law do to *this* language".  A law is not
a rule until the whole subtree underneath it has been heard: a change in the
Proto-Indo-Iranian -> Proto-Iranian transition also reaches Avestan, Old
Persian, Middle Persian and Persian.  This tool measures all of them, in the
same instant, and speaks a verdict.

    # a proposed law, everywhere it can reach
    python tools/council.py --rules proposals/x/candidate.yaml --stage iir-pro --to ira-pro

    # what an existing law carries, everywhere
    python tools/council.py --drop tt_to_st --stage iir-pro --to ira-pro

    # the published counter's looser layers, and JSON for a report
    python tools/council.py --rules c.yaml --stage peo --to pal --layers exact,orthographic --json

A word is counted exactly as the published counter counts it (`coverage.py`):
a recorded ancestor in the word's own chain, at least one law applied, and the
output identical to the attested form.  The verdict is deliberately strict:

    ACCEPT only if, in every downstream language, no word that already matched
    stops matching and at least one language gains a word.

That is the project's condition (2026-11-09): a new rule stands only if it does
not disturb what is already reconstructed.  A law that gains in one language
and loses in another is REJECTED and printed with both lists, because a sound
law that breaks a known word is either mis-stated or mis-environmented.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data                                  # noqa: E402
from whatif import exact_words, load_candidate        # noqa: E402


def downstream(src: str, dst: str) -> list[str]:
    """Every attested language whose derivation chain contains ``src -> dst``.

    The target of the transition is included; a language that only *starts*
    at ``src`` is not, because the law applies in the step out of it.  Order is
    shallow to deep, so a reader sees the rung before its descendants.
    """
    out: list[str] = []
    for lang in sorted(data.languages()):
        chain = data.derivation_chain(lang)
        if any(a == src and b == dst for a, b in zip(chain, chain[1:])):
            out.append(lang)
    out.sort(key=lambda lang: (len(data.derivation_chain(lang)),
                              0 if lang == dst else 1, lang))
    return out


def verdict(rows: list[dict]) -> tuple[bool, str]:
    """(accept, sentence) from one row per language: {lang, before, after, lost}."""
    gained = sum(max(0, r["after"] - r["before"]) for r in rows)
    lost = sum(len(r.get("lost") or []) for r in rows)
    if not rows:
        return False, "no language downstream of this transition has a lexicon"
    if lost:
        return False, f"REJECT: {lost} word(s) that already matched stop matching"
    if not gained:
        return False, "REJECT: the law gains nothing anywhere in the subtree"
    return True, f"ACCEPT: +{gained} word(s) across {len(rows)} language(s), nothing lost"


def measure(langs: list[str], rules_path: Path | None, drops: list[str],
            src: str, dst: str, tiers: set[str] | None,
            layers: tuple[str, ...]) -> list[dict]:
    rulesets = data.rulesets()
    key = (src, dst)
    if key not in rulesets:
        raise SystemExit(f"no rules file for {src} -> {dst}")
    after_sets = copy.deepcopy(rulesets)
    rs = after_sets[key]
    notes: list[str] = []
    if rules_path:
        cand = load_candidate(rules_path, src, dst)
        ids = {r.id for r in rs.rules}
        for rule in cand.rules:
            if rule.id in ids:
                raise SystemExit(f"rule {rule.id} already exists in {src} -> {dst}")
            rule.compile()
        rs.rules = sorted(rs.rules + cand.rules, key=lambda r: (r.order, r.id))
        notes.append("added " + ", ".join(r.id for r in cand.rules))
    for rule_id in drops:
        before = len(rs.rules)
        rs.rules = [r for r in rs.rules if not (
            r.id == rule_id or f"{dst}|{rule_id}" == rule_id or rule_id.endswith("|" + r.id))]
        if len(rs.rules) == before:
            raise SystemExit(f"no rule {rule_id} in {src} -> {dst}")
        notes.append(f"dropped {rule_id}")
    if not notes:
        raise SystemExit("nothing to test: pass --rules and/or --drop")

    rows: list[dict] = []
    for lang in langs:
        chain = data.derivation_chain(lang)
        base = exact_words(lang, chain, rulesets, tiers, 0, layers)
        after = exact_words(lang, chain, after_sets, tiers, 0, layers)
        before_words = {w for w, _ in base}
        after_words = {w for w, _ in after}
        rows.append({
            "language": lang,
            "chain": " > ".join(chain),
            "before": len(before_words),
            "after": len(after_words),
            "gained": sorted(after_words - before_words),
            "lost": sorted(before_words - after_words),
        })
    rows[0]["changes"] = notes
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stage", dest="src", required=True, help="source stage of the transition")
    ap.add_argument("--to", dest="dst", required=True, help="target stage of the transition")
    ap.add_argument("--rules", type=Path, help="YAML file with the candidate rule(s)")
    ap.add_argument("--drop", action="append", default=[], metavar="ID",
                    help="remove an existing law (repeatable) and measure what it carries")
    ap.add_argument("--langs", nargs="*", default=None,
                    help="measure only these languages (default: the whole subtree)")
    ap.add_argument("--layers", default="exact",
                    help="layers that count as explained: exact, orthographic, cited")
    ap.add_argument("--tiers", help="comma list of tiers to allow")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    langs = args.langs or downstream(args.src, args.dst)
    tiers = set(args.tiers.split(",")) if args.tiers else None
    layers = tuple(x.strip() for x in args.layers.split(",") if x.strip())
    rows = measure(langs, args.rules, args.drop, args.src, args.dst, tiers, layers)
    ok, sentence = verdict(rows)

    if args.json:
        print(json.dumps({"transition": f"{args.src}->{args.dst}",
                          "changes": rows[0].get("changes", []),
                          "layers": list(layers), "rows": rows,
                          "accept": ok, "verdict": sentence},
                         ensure_ascii=False, indent=1))
        return 0 if ok else 1

    print(f"{args.src} -> {args.dst} · {', '.join(rows[0].get('changes', []))}"
          f" · layers: {', '.join(layers)}")
    for row in rows:
        delta = row["after"] - row["before"]
        print(f"  {row['language']:<10} {row['before']:>6,} -> {row['after']:>6,}"
              f"  ({delta:+,})  lost {len(row['lost'])}")
        if row["gained"]:
            print(f"             gained: {', '.join(row['gained'][:12])}"
                  + (" …" if len(row["gained"]) > 12 else ""))
        if row["lost"]:
            print(f"             LOST:   {', '.join(row['lost'][:12])}"
                  + (" …" if len(row["lost"]) > 12 else ""))
    print(f"  {sentence}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
