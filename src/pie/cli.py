"""Command line interface: inspect languages, rules, lexicons and derivations."""

from __future__ import annotations

import argparse
import json
import platform
import sys

from . import data
from . import service
from . import spelling
from .phonology import detokenize, tokenize
from .textio import enable_utf8_stdio


def _norm(form: str) -> str:
    return detokenize(tokenize(form))
from .rules import TIERS, Rule, apply_ruleset, derive


def _fmt_chain(chain: list[str]) -> str:
    return " → ".join(data.languages().get(c, {}).get("short", c) for c in chain)


def cmd_languages(args: argparse.Namespace) -> int:
    for lang in data.languages().values():
        chain = data.derivation_chain(lang["id"]) if lang["id"] != "ine-pro" else []
        gap = "" if not chain or not data.missing_stages(chain) else "  [rules missing]"
        print(f"{lang['id']:<14} {lang['name']:<26} {lang.get('branch',''):<24}{gap}")
        if args.verbose and chain:
            print(f"{'':<14} {_fmt_chain(chain)}")
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    rs = data.rulesets()
    if args.from_stage:
        rs = {k: v for k, v in rs.items() if k == (args.from_stage, args.to_stage)}
    for (src, dst), ruleset in sorted(rs.items()):
        print(f"\n== {ruleset.name} ({len(ruleset.rules)} rules) ==")
        for r in ruleset.rules:
            env = ""
            if r.left or r.right:
                env = f"  / {r.left or ''}_{r.right or ''}"
            print(f"  {r.order:>4} {r.id:<28} {r.match} → {r.replace or '∅'}{env}  [{r.tier}]")
    return 0


def _rule_from_example(rule: Rule, form: str) -> str:
    # An example is the rule being exercised, so a rule that is off by default
    # (the animal suffix *-ka-) is switched on for its own example.
    out, steps = apply_ruleset(  # type: ignore[arg-type]
        form, type("RS", (), {"rules": [rule], "target_stage": ""})(),
        enabled=[rule.id])
    return out


def cmd_check_rules(args: argparse.Namespace) -> int:
    ok = bad = 0
    known_sources = data.sources()
    implicit = []
    for path in sorted(data.RULE_DIR.glob("*.yaml")):
        raw = data._load_yaml(path)
        for row in raw.get("rules", []) or []:
            if "tier" not in row:
                implicit.append(f"{path.stem}:{row.get('id', '?')}")
    if implicit:
        print(f"{len(implicit)} rules rely on the implicit `established` default "
              f"(state the tier explicitly in new rules)")
        if args.strict:
            bad += len(implicit)
            for item in implicit:
                print(f"  MISSING tier: {item}")
    spelling_files = spelling.available()
    for lang in spelling_files:
        rs = spelling.ruleset(lang)
        ids = set()
        for rule in rs.rules:
            if rule.id in ids:
                print(f"DUPLICATE rule id {rule.id} in spelling/{lang}.yaml")
                bad += 1
            ids.add(rule.id)
            for ref in rule.references:
                if ref not in known_sources:
                    print(f"UNKNOWN source key '{ref}' in spelling rule {rule.id} ({lang})")
                    bad += 1
        problems = spelling.check(rs)
        bad += len(problems)
        ok += sum(len(r.examples) for r in rs.rules) - len(problems)
        for line in problems:
            print(line)
    for (src, dst), ruleset in sorted(data.rulesets().items()):
        ids = set()
        for rule in ruleset.rules:
            if rule.id in ids:
                print(f"DUPLICATE rule id {rule.id} in {src}__{dst}")
                bad += 1
            ids.add(rule.id)
            for ref in rule.references:
                if ref not in known_sources:
                    print(f"UNKNOWN source key '{ref}' in rule {rule.id} ({src}__{dst})")
                    bad += 1
            if rule.tier not in TIERS:
                print(f"BAD tier '{rule.tier}' in rule {rule.id}")
                bad += 1
            for ex in rule.examples:
                before = ex.get("in")
                expected = ex.get("out")
                if before is None or expected is None:
                    continue
                got = _rule_from_example(rule, before)
                if got != _norm(expected):
                    print(f"EXAMPLE FAIL {src}__{dst} {rule.id}: {before} → {got} (expected {expected})")
                    bad += 1
                else:
                    ok += 1
    spelled = ", ".join(spelling_files) if spelling_files else "none"
    print(f"\n{len(data.rulesets())} rule files, {sum(len(r.rules) for r in data.rulesets().values())} rules, "
          f"{ok} examples verified, {bad} problems; spelling files: {spelled}")
    return 0 if bad == 0 else 1


def cmd_derive(args: argparse.Namespace) -> int:
    if args.chain:
        chain = data.derivation_chain(args.chain)
        if not chain:
            print(f"unknown language {args.chain}")
            return 1
    else:
        chain = data.ancestor_chain(args.to_stage or args.lang or "en")
        if args.from_stage:
            full = data.derivation_chain(args.lang or args.to_stage or "en")
            chain = full[full.index(args.from_stage) :]
    rs = data.rulesets()
    if args.disable:
        disabled = set(args.disable.split(","))
    else:
        disabled = set()
    d = derive(args.form, chain, rs, disabled=disabled)
    if args.json:
        print(json.dumps(d.to_dict(), ensure_ascii=False, indent=1))
        return 0
    print(f"{args.form}  ({_fmt_chain(chain)})")
    stage_forms = list(zip(chain, d.forms))
    for (stage, form) in stage_forms:
        print(f"  {stage:<10} {form}")
    print()
    for step in d.steps:
        print(f"  · {step.before} → {step.after}   [{step.rule_id}] {step.rule_name}")
    if d.skipped:
        print(f"  (no rules for: {', '.join(d.skipped)})")
    if args.spell:
        target = args.spell if isinstance(args.spell, str) else chain[-1]
        if spelling.applies(target):
            written = spelling.spell(d.output, target)
            steps = spelling.steps(d.output, target)
            print(f"\n  written ({target}): {written}  "
                  f"[{len(steps)} orthographic rule{'s' if len(steps) != 1 else ''}]")
        else:
            print(f"\n  (no orthographic file for {target})")
    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    rows = data.lexicon(args.lang)
    if not rows:
        print(f"no lexicon for {args.lang}")
        return 1
    idx = data.lexicon_index(args.lang)
    hits = idx.get(args.word.lower(), [])
    if not hits:
        hits = [e for e in rows if args.word.lower() in e["word"].lower()][:20]
    for e in hits[: args.limit]:
        print(f"{e['word']}  [{e.get('pos','')}]  {'; '.join(e.get('glosses', [])[:3])}")
        if e.get("cognate"):
            print(f"    ← {e['cognate']}")
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    """Predict the etymon's descendants in every modelled language."""
    from . import service

    rb = service.rebuilds_for_etymon(args.form)
    if not rb:
        print("no form given")
        return 1
    if args.json:
        print(json.dumps(rb, ensure_ascii=False, indent=1))
        return 0
    print(f"{rb['source']['form']}  →  {rb['counts']['languages']} modelled languages"
          f"  ({rb['counts']['unattested']} unattested, {rb['counts']['gaps']} stages with gaps)")
    for row in rb["rows"]:
        if row["skipped"] and not args.gaps:
            continue
        mark = "~" if row["status"] == "new" else " "
        state = row["status"] if row["status"] != "new" else "unattested"
        print(f" {mark} {row['l']:<10} {row['form']:<22} {row['steps']:>2} laws  {state}")
    return 0


def cmd_pathways(args: argparse.Namespace) -> int:
    """List recorded pathways, or store one from a form you supply."""
    from . import pathways

    if args.store:
        if not args.default and not (args.lang and args.word and args.from_stage and args.form):
            print("--store needs --lang, --word, --from and --form"
                  " (or --default with --lang, --word, --disable and --note)",
                  file=sys.stderr)
            return 2
        try:
            result = service.store_pathway(
                args.lang, args.word, args.from_stage, args.form,
                [d for d in (args.disable or "").split(",") if d], args.note,
                default=args.default,
                references=[r for r in (args.references or "").split(",") if r],
            )
        except ValueError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 1
        rec = result["pathway"]
        print(f"{'stored' if result['created'] else 'already stored'} {rec['id']}")
        print(f"  {rec['start']['form']} ({rec['start']['name']}) → {rec['word']} "
              f"· {len(rec['laws'])} laws")
        return 0

    rows = pathways.for_word(args.lang, args.word) if (args.lang or args.word) else pathways.load()
    if not rows:
        print("no pathways recorded yet")
        return 0
    for rec in rows:
        print(f"{rec['id']}  {rec['lang']}:{rec['word']}  "
              f"{rec['start']['form']} ({rec['start']['name']}) → {rec['end']['form']}"
              f"  · {len(rec.get('laws', []))} laws  · {rec.get('created', '?')}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    langs = data.languages()
    print(f"languages: {len(langs)}")
    print(f"rule files: {len(data.rulesets())}, rules: {sum(len(r.rules) for r in data.rulesets().values())}")
    for lang, size in data.available_lexicons():
        print(f"  lexicon {lang:<10} {size/1024/1024:6.1f} MB")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    from . import __version__

    print(f"pie {__version__}")
    print(f"python {sys.version.split()[0]}  ·  {platform.platform()}")
    print(f"data {data.DATA}")
    print(f"stdout {sys.stdout.encoding}  ·  stderr {sys.stderr.encoding}  ·  "
          f"filesystem {sys.getfilesystemencoding()}  ·  default {sys.getdefaultencoding()}")
    print(f"languages {len(data.languages())}  ·  rule files {len(data.rulesets())}  ·  "
          f"lexicons {len(data.available_lexicons())}")
    missing = data.missing_stages(data.derivation_chain("en"))
    print("chain en: " + ("complete" if not missing else f"missing {missing}"))
    return 0


def cmd_unverified(args: argparse.Namespace) -> int:
    """Print the matches the engine refused to verify, for a person to judge.

    Each line is one branch row that reproduced every sound of a record but its
    ending: the record, the reading the dictionary gives it, the form the laws
    produced, and both meanings.  Nothing here is edited — the queue is a list
    of questions, and a row leaves it when a human or an agent decides whether
    the two are the same word (2026-11-12).
    """
    from . import review

    rows = review.entries(args.lang)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print(f"no unverified matches recorded{'' if not args.lang else ' for ' + args.lang}"
              f" — the queue fills as word pages are read ({review.path()})")
        return 0
    for row in rows:
        gloss = f" · {row['gloss']}" if row.get("gloss") else ""
        seen_at = row.get("from") or {}
        where = (f"{seen_at.get('lang', '')}/{seen_at.get('word', '')}"
                 if seen_at.get("word") else "")
        read = row.get("record_read") or row.get("reading") or ""
        if (row.get("basis") or "reading") == "letters":
            read = "no reading recorded — letters only"
        print(f"{row['lang']:<10} {row['form']:<18} ⚠ {row['word']} "
              f"({read}){gloss}"
              f"{f'   [seen on {where}]' if where else ''}")
    print(f"\n{len(rows)} unverified match{'es' if len(rows) != 1 else ''} · {review.path()}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .app.server import run

    run(host=args.host, port=args.port)
    return 0


def _pct(x: float) -> str:
    p = 100 * x
    if p == 0:
        return "0%"
    if p < 0.01:
        return f"{p:.4f}%"
    if p < 1:
        return f"{p:.2f}%"
    return f"{p:.1f}%"


def _bar(x: float, width: int = 16) -> str:
    filled = int(round(max(0.0, min(1.0, x)) * width))
    if x > 0 and filled == 0:
        return "▏" + "░" * (width - 1)
    return "█" * filled + "░" * (width - filled)


def cmd_coverage(args) -> int:
    cov = service.coverage()
    if not cov.get("languages"):
        print("no coverage data — run tools/coverage.py", file=sys.stderr)
        return 1
    t = cov.get("totals", {})
    if t:
        print(f"reconstructed exactly: {t.get('exact', 0):,} / {t.get('glossary', 0):,} "
              f"({_pct(t.get('exact_rate', 0))})  ·  identified: {t.get('identified', 0):,} "
              f"({_pct(t.get('identified_rate', 0))})")
        if t.get("orthographic"):
            print(f"plus orthographic layer: {t.get('orthographic', 0):,} more → "
                  f"{t.get('exact_orth', 0):,} ({_pct(t.get('orth_rate', 0))})")
        print(cov.get("sample", ""), f"· generated {cov.get('generated', '?')}\n")
    rows = sorted(cov["languages"].items(), key=lambda kv: (-kv[1].get("exact", 0),
                                                             -kv[1].get("glossary", 0)))
    print(f"{'language':<9}{'identified':>17}{'reconstructed':>25}  progress")
    for lang, r in rows[: args.top]:
        ident = f"{r.get('identified', 0):,} ({_pct(r.get('identified_rate', 0))})"
        recon = f"{r.get('exact', 0):,} / {r.get('glossary', 0):,} ({_pct(r.get('exact_rate', 0))})"
        print(f"{lang:<9}{ident:>17}{recon:>25}  {_bar(r.get('exact_rate', 0))}")
    if args.rules and cov.get("rules_used"):
        print("\nrules used in exact derivations:")
        for r in cov["rules_used"][: args.rules]:
            print(f"  {r['count']:>8,}  {r['id']:<28} {r['from']} → {r['to']}  [{r['tier']}]")
    return 0


def cmd_spell(args: argparse.Namespace) -> int:
    if not args.form:
        for lang in spelling.available():
            rs = spelling.ruleset(lang)
            print(f"{lang:<12} {len(rs.rules):>3} rules  {rs.name}")
        if not spelling.available():
            print("no spelling files yet — see docs/PROGRAMME.md, workstream W2", file=sys.stderr)
        return 0
    written = spelling.spell(args.form, args.lang)
    steps = spelling.steps(args.form, args.lang)
    if args.json:
        print(json.dumps({"input": args.form, "lang": args.lang, "written": written,
                          "steps": [st.__dict__ for st in steps]}, ensure_ascii=False, indent=1))
        return 0
    print(f"{args.form} → {written}")
    for st in steps:
        print(f"  {st.rule_id:<22} {st.before} → {st.after}")
    return 0


def cmd_notation(args: argparse.Namespace) -> int:
    """The stage's standard alphabet, and every headword that leaves it."""
    from . import data, notation
    langs = [args.lang] if args.lang else notation.languages()
    if not langs:
        print("no notation tables yet — see data/notation/", file=sys.stderr)
        return 1
    status = 0
    for lang in langs:
        table = notation.table(lang)
        if not table:
            print(f"{lang}: no notation table", file=sys.stderr)
            status = 1
            continue
        words = [row.get("word") or "" for row in data.lexicon(lang)]
        variants = notation.variants(lang, words)
        bad = notation.offenders(lang, words)
        quoted = [w for w in words if notation.is_quoted(lang, w)]
        if args.json:
            print(json.dumps({"lang": lang, "letters": "".join(sorted(notation.letters(lang))),
                              "basis": table.get("basis"), "words": len(words),
                              "variants": variants, "outside": bad,
                              "quoted": len(quoted)}, ensure_ascii=False, indent=1))
            continue
        print(f"{lang}: {table.get('name') or lang} — standard {table.get('basis')}")
        print(f"  letters  {table.get('letters')}")
        for variant, folded in (table.get("folds") or {}).items():
            print(f"  fold     {variant} → {folded}")
        print(f"  {len(words)} headwords · {len(quoted)} quoted · "
              f"{len(variants)} variants · {len(bad)} outside the alphabet")
        for word, maths in variants[:20]:
            print(f"    variant  {word} ({maths})")
        for word, maths in bad[:20]:
            print(f"    outside  {word}  {maths}")
        if variants:
            status = 1
    return status


def cmd_worklist(args: argparse.Namespace) -> int:
    from . import worklist

    report = worklist.run(None if args.full else (args.limit or None), args.lang)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1, default=str))
        return 0
    text = worklist.render(report)
    if args.write:
        worklist.OUT_MD.write_text(text, encoding="utf-8")
        worklist.OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str) + "\n",
                                     encoding="utf-8")
        print(f"wrote {worklist.OUT_MD} and {worklist.OUT_JSON}")
        return 0
    print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pie", description="Indo-European language family model")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("languages", help="list language registry")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.set_defaults(func=cmd_languages)

    sp = sub.add_parser("rules", help="list sound-law rules")
    sp.add_argument("--from", dest="from_stage")
    sp.add_argument("--to", dest="to_stage")
    sp.set_defaults(func=cmd_rules)

    sp = sub.add_parser("check-rules", help="validate rule files and examples")
    sp.add_argument("--strict", action="store_true",
                    help="also fail on rules that do not state their tier")
    sp.set_defaults(func=cmd_check_rules)

    sp = sub.add_parser("derive", help="apply a sound-law chain to a form")
    sp.add_argument("form")
    sp.add_argument("--chain", help="language id whose full chain is used, e.g. en")
    sp.add_argument("--from", dest="from_stage")
    sp.add_argument("--to", dest="to_stage")
    sp.add_argument("--lang", dest="lang")
    sp.add_argument("--disable", help="comma separated rule ids to skip")
    sp.add_argument("--spell", nargs="?", const=True, metavar="LANG",
                    help="also write the result the way LANG spells it (default: the chain's last stage)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_derive)

    sp = sub.add_parser("lookup", help="look a word up in a language lexicon")
    sp.add_argument("lang")
    sp.add_argument("word")
    sp.add_argument("--limit", type=int, default=5)
    sp.set_defaults(func=cmd_lookup)

    sp = sub.add_parser("rebuild", help="predict an etymon's descendants in every modelled language")
    sp.add_argument("form")
    sp.add_argument("--gaps", action="store_true", help="also list stages whose rule chain is incomplete")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_rebuild)

    sp = sub.add_parser("coverage", help="exact-derivation coverage per language")
    sp.add_argument("--top", type=int, default=40)
    sp.add_argument("--rules", type=int, default=0, help="show the N most-used rules")
    sp.set_defaults(func=cmd_coverage)

    sp = sub.add_parser("pathways", help="list or record derivation pathways stored from a word page")
    sp.add_argument("--lang")
    sp.add_argument("--word")
    sp.add_argument("--store", action="store_true")
    sp.add_argument("--from", dest="from_stage")
    sp.add_argument("--form")
    sp.add_argument("--disable", help="comma separated rule keys switched off on this path")
    sp.add_argument("--note", default="")
    sp.add_argument("--default", action="store_true",
                    help="apply this pathway whenever the word's page opens (needs --note)")
    sp.add_argument("--references", help="comma separated source ids supporting the pathway")
    sp.set_defaults(func=cmd_pathways)

    sp = sub.add_parser("spell", help="apply a language's orthographic layer (no form: list the files)")
    sp.add_argument("form", nargs="?")
    sp.add_argument("--lang", default="en")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_spell)

    sp = sub.add_parser("worklist", help="priorisited worklist from the corpus (miss signatures, gaps, dead rules)")
    sp.add_argument("--limit", type=int, default=12000, help="sample per language (0 = all)")
    sp.add_argument("--full", action="store_true")
    sp.add_argument("--lang", action="append")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--write", action="store_true", help="write docs/WORKLIST.md and data/worklist.json")
    sp.set_defaults(func=cmd_worklist)

    sp = sub.add_parser("notation", help="a stage's standard alphabet, and headwords outside it")
    sp.add_argument("lang", nargs="?")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_notation)

    sp = sub.add_parser("stats", help="dataset overview")
    sp.set_defaults(func=cmd_stats)

    sp = sub.add_parser("doctor", help="python, encoding and data report (paste this in bug reports)")
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("unverified", help="matches the engine could not verify, queued for review")
    sp.add_argument("--lang", default=None, help="only this stage's rows")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_unverified)

    sp = sub.add_parser("serve", help="run the web interface")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8100)
    sp.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    enable_utf8_stdio()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
