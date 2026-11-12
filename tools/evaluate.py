#!/usr/bin/env python3
"""Score a rule chain against the reconstruction pairs recorded by Wiktionary.

For every cognate set, the descendant tree gives us pairs such as
PIE *pṓds → PGmc *fōts.  Feeding the PIE form through the rule chain and
comparing with the recorded proto-form is an objective accuracy measure, and it
is how a proposed rule set can be compared with the established one.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data  # noqa: E402
from pie.phonology import detokenize, tokenize  # noqa: E402
from pie.rules import derive
from pie.textio import enable_utf8_stdio  # noqa: E402


def bare(form: str) -> str:
    return detokenize([t for t in tokenize(form) if t not in {"ˈ", "ˌ"}])


def edit_distance(a: str, b: str) -> int:
    """Levenshtein over segments."""
    ta, tb = tokenize(a), tokenize(b)
    prev = list(range(len(tb) + 1))
    for i, x in enumerate(ta, 1):
        cur = [i]
        for j, y in enumerate(tb, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def similarity(a: str, b: str) -> float:
    a, b = bare(a), bare(b)
    if not a and not b:
        return 1.0
    return 1.0 - edit_distance(a, b) / max(len(tokenize(a)), len(tokenize(b)), 1)


def direct_pairs(parent: str, child: str) -> list[tuple[str, str, str]]:
    path = ROOT / "data" / "graph" / "edges.jsonl.gz"
    if not path.exists():
        return []
    pairs = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["p"][0] == parent and row["c"][0] == child:
                pairs.append((row["set"], row["p"][1], row["c"][1]))
    return pairs


def evaluate(src: str, dst: str, tiers=None, limit=None, show=15) -> dict:
    rs = data.rulesets()
    ruleset = rs.get((src, dst))
    if ruleset is None:
        return {"error": f"no rule file for {src}→{dst}"}
    pairs = direct_pairs(src, dst)
    if limit:
        pairs = pairs[:limit]
    ok = 0
    misses = []
    comparable = 0
    sims = []
    rule_hits = Counter()
    for set_id, before, expected in pairs:
        d = derive(before, [src, dst], rs, tiers=tiers)
        got = d.output
        sim = similarity(expected, before)
        if sim < 0.55:
            # the two forms differ morphologically (derived vs. base form); the
            # sound laws alone cannot be expected to bridge that
            continue
        comparable += 1
        s_got = similarity(got, expected)
        sims.append(s_got)
        if bare(got) == bare(expected):
            ok += 1
            for s in d.steps:
                rule_hits[s.rule_id] += 1
        else:
            misses.append((set_id, before, expected, got, [s.rule_id for s in d.steps]))
    total = comparable
    return {
        "transition": f"{src}→{dst}",
        "total": total,
        "correct": ok,
        "accuracy": ok / total if total else 0,
        "similarity": sum(sims) / len(sims) if sims else 0,
        "rules_fired": dict(rule_hits.most_common()),
        "misses": misses[:show],
        "n_misses": len(misses),
    }


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src")
    ap.add_argument("--to", dest="dst")
    ap.add_argument("--all", action="store_true", help="score every registered transition")
    ap.add_argument("--markdown", action="store_true", help="emit a Markdown table (with --all)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.all:
        rows = []
        for (src, dst) in sorted(data.rulesets()):
            res = evaluate(src, dst, limit=args.limit, show=0)
            rows.append(res)
            if "error" in res:
                continue
            print(f"{res['transition']:<22} {res['correct']:>4}/{res['total']:<5} "
                  f"{res['accuracy']*100:>5.1f}% exact  {res['similarity']*100:>5.1f}% similar")
        if args.markdown:
            out = ROOT / "docs" / "EVALUATION.md"
            lines = ["# Per-transition accuracy", "",
                     "Each row: recorded ancestor/descendant pairs from Wiktionary spot-checked against the rule chain.",
                     "", "| transition | exact | comparable pairs | mean similarity |", "|---|---|---|---|"]
            for r in rows:
                if "error" in r:
                    continue
                lines.append(f"| {r['transition']} | {r['accuracy']*100:.1f}% | {r['total']} | {r['similarity']*100:.1f}% |")
            out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"\n→ {out}")
        return 0
    if not (args.src and args.dst):
        print("give --from/--to, or --all", file=sys.stderr)
        return 2
    res = evaluate(args.src, args.dst, limit=args.limit)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    if "error" in res:
        print(res["error"])
        return 1
    print(f"{res['transition']}: {res['correct']}/{res['total']} = {res['accuracy']*100:.1f}% exact, "
          f"{res['similarity']*100:.1f}% mean segmental similarity")
    print("\nmisses:")
    for set_id, before, expected, got, rules in res["misses"]:
        print(f"  {before:>14} → {got:<14} (expected {expected:<14}) [{', '.join(rules)}]")
    print(f"\n{res['n_misses']} mismatches total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
