#!/usr/bin/env python3
"""Test a candidate sound law against a whole language, before it is shipped.

The programme's rule is that a proposal is measured before it becomes a rule:
the claim, the environment, the examples, and the corpus gain all come first
(docs/PROGRAMME.md, W4).  This is that measurement, in one command.

    # what does adding candidate.yaml to pal -> fa gain or lose?
    python tools/whatif.py --from pal --to fa --rules candidate.yaml

    # what does an existing law actually carry in fa?
    python tools/whatif.py --to fa --drop fa:u_to_o

    # only the first 2,000 words of the language (fast), JSON out
    python tools/whatif.py --to fa --rules candidate.yaml --limit 2000 --json

A word counts exactly as `tools/coverage.py` counts it: a recorded ancestor in
the word's own chain, at least one law applied, and the output identical to the
attested form.  Nothing here may bend a target — if a candidate gains words by
being permissive, the gained list shows it and the reviewer rejects it.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, script              # noqa: E402
from pie.rules import RuleSet, derive     # noqa: E402

# One definition of "a word is explained", shared with the published counter.
# Importing them is the point: this tool used to carry its own copy of
# ancestor_starts and a wider notion of equality (_same_form), so it disagreed
# with tools/coverage.py — 200 against 206 words for one law, and 2,624 corpus
# entries that never reached the comparison at all (Mill's audit, 2026-11-09).
sys.path.insert(0, str(ROOT / "tools"))
from coverage import (ancestor_starts, citation_hit, exact_kind,   # noqa: E402
                      orthographic_hit, _bound_pair, _identity_hit)


def exact_words(lang: str, chain: list[str], rulesets, tiers=None,
                limit: int = 0, layers: tuple[str, ...] = ("exact",)) -> list[tuple[str, str]]:
    """(attested word, stage it was derived from) for every entry the laws explain.

    A **list**, not a dict keyed by the headword: two entries may share a
    headword (a noun and an adjective), and collapsing them made the tool count
    fewer words than the release does.
    """
    out: list[tuple[str, str]] = []
    entries = data.lexicon(lang)
    if limit:
        entries = entries[:limit]
    for entry in entries:
        target = str(entry.get("word") or "").strip()
        if not target or entry.get("recon"):
            continue
        outputs: list[tuple[str, int, str]] = []
        matched = None
        for stage, form in ancestor_starts(entry, chain):
            try:
                d = derive(form, chain[chain.index(stage):], rulesets, tiers=tiers)
            except Exception:
                continue
            if d.skipped:
                continue
            outputs.append((d.output, len(d.steps), stage))
            if d.steps and "exact" in layers and exact_kind(d.output, target):
                matched = stage
                break
        if matched:
            out.append((target, matched))
            continue
        if "orthographic" in layers:
            hit = orthographic_hit(outputs, lang, target, entry.get("ipa") or "")
            if hit:
                out.append((target, hit[2]))
                continue
        if "cited" in layers and citation_hit(outputs, lang, target, entry.get("ipa") or ""):
            out.append((target, outputs[0][2]))
            continue
        # A language written in its own script (Old Persian, Middle Persian,
        # Greek, Persian) can never match the headword character for character:
        # the question there is whether the derived form is a possible reading
        # of the signs.  This is the coverage page's own script layer, so a law
        # measured here counts what the published figure counts (2026-11-09).
        if "script" in layers:
            for output, steps, stage in outputs:
                if not steps:
                    continue
                fit = script.match(lang, output, target)
                if fit and fit.get("ok"):
                    out.append((target, stage))
                    break
            else:
                fit = None
            if fit and fit.get("ok"):
                continue
        if "identity" in layers and _identity_hit(outputs, target, entry):
            out.append((target, outputs[0][2]))
            continue
        if "bound" in layers and "-" in target and any(
                _bound_pair(output, target) for output, _s, _stage in outputs):
            out.append((target, outputs[0][2]))
    return out


def load_candidate(path: Path, src: str, dst: str) -> RuleSet:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(raw, list):
        raw = {"rules": raw}
    if "rules" not in raw:
        raise SystemExit(f"{path}: no `rules:` list")
    for row in raw["rules"]:
        row.setdefault("source", raw.get("stage", {}).get("source", src))
    return RuleSet.from_dict(raw, src, dst)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--to", required=True, help="target language id (fa, pal, ave …)")
    ap.add_argument("--from", dest="src", default=None,
                    help="source stage of the transition (default: the target's last ancestor)")
    ap.add_argument("--rules", type=Path, help="YAML file with the candidate rule(s)")
    ap.add_argument("--drop", action="append", default=[], metavar="ID",
                    help="remove an existing law (repeatable) and measure what it carries")
    ap.add_argument("--tiers", help="comma list of tiers to allow")
    ap.add_argument("--limit", type=int, default=0, help="first N words of the language")
    ap.add_argument("--layers", default="exact",
                    help="comma list of the layers that count as explained: exact, "
                         "orthographic, cited, script, identity, bound (default: exact only)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    chain = data.derivation_chain(args.to)
    if not chain:
        raise SystemExit(f"{args.to}: no derivation chain in the registry")
    src = args.src or chain[-2]
    rulesets = data.rulesets()
    key = (src, args.to)
    if key not in rulesets:
        raise SystemExit(f"no rules file for {src} -> {args.to} ({sorted(rulesets)[:3]} …)")
    tiers = set(args.tiers.split(",")) if args.tiers else None
    layers = tuple(x.strip() for x in args.layers.split(",") if x.strip())

    base = exact_words(args.to, chain, rulesets, tiers, args.limit, layers)

    after_sets = copy.deepcopy(rulesets)
    rs = after_sets[key]
    notes: list[str] = []
    if args.rules:
        cand = load_candidate(args.rules, src, args.to)
        ids = {r.id for r in rs.rules}
        for rule in cand.rules:
            if rule.id in ids:
                raise SystemExit(f"rule {rule.id} already exists in {src} -> {args.to}")
            rule.compile()
        rs.rules = sorted(rs.rules + cand.rules, key=lambda r: (r.order, r.id))
        notes.append(f"added {', '.join(r.id for r in cand.rules)}")
    for rule_id in args.drop:
        before = len(rs.rules)
        rs.rules = [r for r in rs.rules if not (r.id == rule_id or f"{args.to}|{rule_id}" == rule_id
                                                or rule_id.endswith("|" + r.id))]
        if len(rs.rules) == before:
            raise SystemExit(f"no rule {rule_id} in {src} -> {args.to}")
        notes.append(f"dropped {rule_id}")
    if not notes:
        raise SystemExit("nothing to test: pass --rules and/or --drop")

    after = exact_words(args.to, chain, after_sets, tiers, args.limit, layers)
    base_words = Counter(w for w, _s in base)
    after_words = Counter(w for w, _s in after)
    gained = sorted((after_words - base_words).elements())
    lost = sorted((base_words - after_words).elements())

    if args.json:
        print(json.dumps({"language": args.to, "transition": f"{src}->{args.to}",
                          "changes": notes, "before": len(base), "after": len(after),
                          "gained": gained, "lost": lost,
                          "gained_by_stage": {w: s for w, s in after[:200] if w in set(gained)},
                          "limit": args.limit}, ensure_ascii=False, indent=1))
        return 0

    print(f"{args.to}: {src} -> {args.to} · {', '.join(notes)}"
          f" · layers: {', '.join(layers)}")
    print(f"  explained before: {len(base):,}")
    print(f"  explained after:  {len(after):,}  ({len(after) - len(base):+,})")
    print(f"  gained {len(gained)} word(s): {', '.join(gained[:25]) or '—'}")
    print(f"  lost   {len(lost)} word(s): {', '.join(lost[:25]) or '—'}")
    if lost:
        print("  A lost word is a regression: the law changed a form that already matched.")
    if not gained and not lost:
        print("  The law applies nowhere this corpus can see — a finding, not a fix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
