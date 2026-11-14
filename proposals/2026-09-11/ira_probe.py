#!/usr/bin/env python3
"""Measure a candidate sound law against both yardsticks before it is shipped.

``tools/evaluate.py`` scores a transition against Wiktionary's own reconstruction
pairs (the per-transition accuracy of the programme's five numbers).  The
worklist scores it against this repo's own glossary.  A candidate must be tested
on both, because a law can help this corpus by hurting the language:

    python3 proposals/2026-09-11/ira_probe.py --from iir-pro --to ira-pro
    python3 proposals/2026-09-11/ira_probe.py --from iir-pro --to ira-pro \
        --add '{"id": "x", "match": "ǰ ʰ", "replace": "ǰ", ...}'
    python3 proposals/2026-09-11/ira_probe.py --from iir-pro --to ira-pro --drop l_to_r
    python3 proposals/2026-09-11/ira_probe.py --from iir-pro --to ira-pro --pairs

Nothing is written: a candidate is compiled in memory as a ``RuleSet`` for one
transition and the whole lexicon (and, with ``--pairs``, every recorded pair of
``data/graph/edges.jsonl.gz``) is re-derived with and without it.

Two comparison modes are reported side by side, because they answer different
questions and the programme forbids confusing them:

``exact``      character for character (the published historical number);
``printable``  the same after the page's own stress convention (``ˈa`` prints as
               ``á``).  This is a *diagnostic*: a difference that vanishes here is
               notation, and must never be fixed with a sound law.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data  # noqa: E402
from pie.phonology import detokenize, tokenize  # noqa: E402
from pie.rules import RuleSet, apply_ruleset_verbose  # noqa: E402
from pie.service import _same_form, printable_form  # noqa: E402
from pie.textio import enable_utf8_stdio  # noqa: E402


def clean(form: str) -> str:
    """The form a rule chain can start from: no asterisk, no brackets, no dash."""
    return (form or "").strip().strip("*").replace("(", "").replace(")", "").strip("-").strip()


def ancestor_forms(entry: dict, src: str) -> list[str]:
    """Every form this entry records for ``src`` (the ``anc`` links, in order)."""
    out: list[str] = []
    for lang, word, rel in entry.get("anc") or []:
        if lang != src or rel == "borrow":
            continue
        # an ancestry field may list variants ("*A ~ *B") or alternatives
        for part in re.split(r"[,;~]", word or ""):
            part = clean(part)
            if part and part not in out:
                out.append(part)
    return out


def distance(a: str, b: str) -> int:
    ta, tb = tokenize(a), tokenize(b)
    prev = list(range(len(tb) + 1))
    for i, x in enumerate(ta, 1):
        cur = [i]
        for j, y in enumerate(tb, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def bare(form: str) -> str:
    return detokenize([t for t in tokenize(form) if t not in {"ˈ", "ˌ"}])


def load_candidates(specs: list[str]) -> list[dict]:
    rules: list[dict] = []
    for spec in specs:
        text = spec
        if Path(spec).is_file():
            text = Path(spec).read_text(encoding="utf-8")
        doc = yaml.safe_load(text)
        if isinstance(doc, dict) and "rules" in doc:
            doc = doc["rules"]
        elif isinstance(doc, dict) and "match" in doc:
            doc = [doc]
        if not isinstance(doc, list):
            raise SystemExit(f"--add {spec}: expected a rule or a list of rules")
        rules.extend(doc)
    return rules


def build_ruleset(src: str, dst: str, extra: list[dict] = (), drop: tuple[str, ...] = ()) -> RuleSet:
    base = data.rulesets().get((src, dst))
    doc = {"stage": {"name": f"{src} → {dst}"}, "rules": []}
    for rule in (base.rules if base else []):
        if rule.id in drop:
            continue
        doc["rules"].append({
            "id": rule.id, "order": rule.order, "name": rule.name,
            "match": rule.match, "replace": rule.replace,
            "env": {"left": rule.left, "right": rule.right} if (rule.left or rule.right) else {},
            "tier": rule.tier, "transform": rule.transform, "params": rule.params,
            "optional": rule.optional, "off_by_default": rule.default_off,
        })
    doc["rules"].extend(extra)
    return RuleSet.from_dict(doc, src, dst)


def run_lexicon(rs: RuleSet, entries: list[dict], src: str) -> dict:
    """Derive every target entry from its own recorded ``src`` ancestry."""
    rows = {}
    for entry in entries:
        target = entry["word"].strip()
        forms = ancestor_forms(entry, src)
        if not forms:
            continue
        best = None
        for form in forms:
            out, _steps, _report = apply_ruleset_verbose(form, rs)
            cand = (distance(out, target), out, form)
            if best is None or cand < best:
                best = cand
        _d, out, form = best
        rows[target] = {
            "ancestor": form, "output": out,
            "exact": out == target,
            "printable": printable_form(out) == target,
            "same": _same_form(out, target),
            "bare": bare(out) == bare(target),
        }
    return rows


def run_pairs(rs: RuleSet, src: str, dst: str) -> dict:
    """Score every recorded ancestor/descendant pair from the cognate graph."""
    import evaluate

    rows = {}
    for index, (set_id, before, expected) in enumerate(evaluate.direct_pairs(src, dst)):
        if evaluate.similarity(expected, before) < 0.55:
            continue
        out, _steps, _report = apply_ruleset_verbose(before, rs)
        # a cognate set may record more than one descendant form, so the pair,
        # not the set id, is the row
        rows[f"{index:03d} {set_id} · {expected}"] = {
            "ancestor": before, "output": out, "expected": expected,
            "exact": out == expected,
            "bare": bare(out) == bare(expected),
            "copy": bare(expected) == bare(before),
        }
    return rows


def run_chain(lang: str, rulesets) -> dict:
    """Derive every entry of ``lang`` from the earliest ancestor it records.

    This is the level ``pie worklist`` reports "explained by the sound laws"
    at: the whole chain from PIE (or whatever stage the entry names) down to
    the word itself.
    """
    from pie import audit
    from pie.rules import derive_detailed

    chain = data.derivation_chain(lang)
    rows = {}
    for entry in data.lexicon(lang):
        if entry.get("recon"):
            continue
        target = entry["word"].strip()
        starts = audit._starts(entry, chain)
        if not starts:
            continue
        best = None
        for stage, form in starts:
            try:
                derivation, _levels = derive_detailed(form, chain[chain.index(stage):], rulesets)
            except Exception:
                continue
            if derivation.skipped:
                continue
            score = (derivation.output != target, printable_form(derivation.output) != target)
            if best is None or score < best[0]:
                best = (score, derivation.output, form, stage)
        if best is None:
            continue
        _score, out, form, stage = best
        rows[target] = {
            "ancestor": form, "output": out, "stage": stage,
            "exact": out == target,
            "printable": printable_form(out) == target,
            "same": _same_form(out, target),
            "bare": bare(out) == bare(target),
        }
    return rows


def compare(base: dict, cand: dict, keys: tuple[str, ...], show: int) -> None:
    for key in keys:
        before = {w for w, r in base.items() if r[key]}
        after = {w for w, r in cand.items() if r[key]}
        gained, lost = sorted(after - before), sorted(before - after)
        print(f"  {key:<9} baseline {len(before):>4} / {len(base):<4}  "
              f"candidate {len(after):>4} / {len(cand):<4}  gain {len(gained):>3}  loss {len(lost):>3}")
        for word in gained[:show]:
            r = base[word]
            print(f"    + {r['ancestor']:>16} → {cand[word]['output']:<16} = {word}")
        for word in lost[:show]:
            r = cand[word]
            print(f"    - {r['ancestor']:>16} → {r['output']:<16} ≠ {word} (was {base[word]['output']})")


def main() -> int:
    enable_utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--add", action="append", default=[], metavar="YAML|FILE",
                    help="a candidate rule (YAML text, or a file holding rules)")
    ap.add_argument("--drop", action="append", default=[], metavar="ID",
                    help="a registered rule to leave out (for a law that hurts)")
    ap.add_argument("--pairs", action="store_true", help="also score the recorded cognate pairs")
    ap.add_argument("--chain", action="store_true",
                    help="also derive the target language from PIE (the worklist's level)")
    ap.add_argument("--match", choices=("exact", "printable", "same", "bare", "both"), default="both")
    ap.add_argument("--show", type=int, default=8)
    args = ap.parse_args()

    extra = load_candidates(args.add)
    which = {"exact": ("exact",), "printable": ("printable",), "same": ("same",),
             "bare": ("bare",), "both": ("exact", "printable")}[args.match]

    base_rs = build_ruleset(args.src, args.dst)
    cand_rs = build_ruleset(args.src, args.dst, extra, tuple(args.drop))
    print(f"{args.src} → {args.dst}: {len(extra)} candidate rule(s), {len(args.drop)} dropped")

    entries = data.lexicon(args.dst)
    base = run_lexicon(base_rs, entries, args.src)
    cand = run_lexicon(cand_rs, entries, args.src)
    print(f"\nglossary: {len(entries)} entries, {len(base)} with a recorded {args.src} ancestor")
    compare(base, cand, which, args.show)
    print(f"  words the candidate alters at all: "
          f"{sum(1 for w in cand if w in base and cand[w]['output'] != base[w]['output'])}")

    if args.chain:
        chain_base = run_chain(args.dst, data.rulesets())
        chain_sets = {k: v for k, v in data.rulesets().items() if k != (args.src, args.dst)}
        chain_sets[(args.src, args.dst)] = cand_rs
        chain_cand = run_chain(args.dst, chain_sets)
        print(f"\nwhole chain into {args.dst}: {len(chain_base)} words derived")
        compare(chain_base, chain_cand, ("exact", "printable", "same"), args.show)

    if args.pairs:
        pb = run_pairs(base_rs, args.src, args.dst)
        pc = run_pairs(cand_rs, args.src, args.dst)
        print(f"\nrecorded pairs: {len(pb)} comparable")
        compare(pb, pc, ("bare",), args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
