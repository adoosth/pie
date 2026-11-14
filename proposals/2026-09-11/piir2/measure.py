#!/usr/bin/env python3
"""Measure a candidate law (added or *replaced*) over the whole subtree.

`tools/council.py` can add a rule and drop a rule, but not restate an existing
one with a narrower environment — and narrowing an environment is the commonest
decision the corpus asks for (Brugmann, ruki, palatalisation).  This script does
exactly what the council does (it imports its `measure`) and additionally
accepts a YAML whose rule *ids already exist*: those rules are replaced in
memory, nothing on disk changes.

    PYTHONPATH=src python3 proposals/2026-09-11/piir2/measure.py \
        --stage ine-pro --to iir-pro --replace c.yaml
    ... --add c.yaml --layers exact,script
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data                                    # noqa: E402
from pie.rules import RuleSet                           # noqa: E402
from council import downstream                          # noqa: E402
from whatif import exact_words                          # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--add", type=Path)
    ap.add_argument("--replace", type=Path)
    ap.add_argument("--layers", default="exact")
    ap.add_argument("--langs", nargs="*", default=None)
    args = ap.parse_args()

    layers = tuple(x.strip() for x in args.layers.split(",") if x.strip())
    langs = args.langs or downstream(args.src, args.dst)
    rulesets = data.rulesets()
    before_sets = copy.deepcopy(rulesets)
    after_sets = copy.deepcopy(rulesets)
    rs = after_sets[(args.src, args.dst)]
    ids = {r.id: i for i, r in enumerate(rs.rules)}
    for path, replace in ((args.add, False), (args.replace, True)):
        if not path:
            continue
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cand = RuleSet.from_dict(raw, args.src, args.dst)
        for rule in cand.rules:
            if rule.id in ids:
                if not replace:
                    raise SystemExit(f"{rule.id} already exists; use --replace")
                rs.rules[ids[rule.id]] = rule
            elif replace:
                raise SystemExit(f"{rule.id} does not exist; use --add")
            else:
                rs.rules.append(rule)
    rs.rules.sort(key=lambda r: (r.order, r.id))

    gained_total = 0
    lost_total = 0
    for lang in langs:
        chain = data.derivation_chain(lang)
        before = {w for w, _ in exact_words(lang, chain, before_sets, None, 0, layers)}
        after = {w for w, _ in exact_words(lang, chain, after_sets, None, 0, layers)}
        lost = sorted(before - after)
        gained = sorted(after - before)
        gained_total += len(gained)
        lost_total += len(lost)
        print(f"  {lang:8s} {len(before):5d} -> {len(after):5d}  ({len(after)-len(before):+d})"
              + (f"  gained {', '.join(gained)}" if gained else "")
              + (f"  LOST {', '.join(lost)}" if lost else ""))
    verdict = "ACCEPT" if not lost_total and gained_total else "REJECT"
    print(f"{verdict}: +{gained_total} gained, {lost_total} lost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
