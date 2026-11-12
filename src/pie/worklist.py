"""Build the priorisited worklist from the corpus.

``pie worklist`` renders the digest, ``tools/worklist.py --write`` stores it in
``docs/WORKLIST.md`` and ``data/worklist.json``.  Nothing here changes the
model: it only reads the corpus, re-derives it, and groups the misses into
tasks for the programme in ``docs/PROGRAMME.md``.
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from . import audit, data

OUT_MD = ROOT / "docs" / "WORKLIST.md"
OUT_JSON = ROOT / "data" / "worklist.json"

#: Order and inclusion for the per-language digest.
HOME_LANGS = ["en", "de", "it", "la", "fa", "el", "sa", "pal", "peo", "ave",
              "ang", "enm", "goh", "gmh", "non", "got", "sga", "lt", "chu",
              "sq", "hy", "xcl", "txb", "hit", "gmw-pro", "gem-pro",
              # the stages out of PIE that now have rule files of their own: a
              # transition that is never audited reports all its rules as dead.
              "cel-pro", "ine-bsl-pro", "ine-ana-pro"]


def run(limit: int | None, langs: list[str] | None = None) -> dict:
    registry = data.languages()
    rulesets = data.rulesets()
    order = langs or [k for k in HOME_LANGS if k in registry]
    reports: dict[str, dict] = {}
    started = time.time()
    for lang in order:
        if not data.lexicon(lang):
            continue
        reports[lang] = audit.audit_language(lang, limit=limit, rulesets=rulesets)
    out = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "limit": limit,
        "seconds": round(time.time() - started, 1),
        "languages": reports,
        "structural": structural(registry, rulesets),
        "rules": rule_hygiene(reports),
    }
    return out


def structural(registry: dict, rulesets) -> dict:
    """Chain holes and lexicons without rules — tasks no single rule can fix."""
    holes: dict[str, list[str]] = defaultdict(list)
    no_rules: list[dict] = []
    no_ancestry: list[dict] = []
    no_ipa: list[dict] = []
    for lang, row in registry.items():
        if lang == "ine-pro":
            continue
        chain = data.derivation_chain(lang)
        missing = [f"{a}→{b}" for a, b in data.missing_stages(chain)]
        for hop in missing:
            holes[hop].append(lang)
        entries = data.lexicon(lang)
        if entries and not missing and not any((a, b) in rulesets for a, b in zip(chain, chain[1:])):
            no_rules.append({"lang": lang, "glossary": len(entries)})
        if entries:
            linked = sum(1 for e in entries if any(l in chain for l, _w, _r in e.get("anc") or []))
            if linked < 0.05 * len(entries):
                no_ancestry.append({"lang": lang, "glossary": len(entries), "linked": linked})
            # A stage with no recorded pronunciation cannot be spelling-checked:
            # `spelling.plausible` needs the dictionary's IPA to keep a letter
            # table from manufacturing a match.  This is a data task (W1).
            spoken = sum(1 for e in entries if e.get("ipa"))
            if spoken < 0.5 * len(entries):
                no_ipa.append({"lang": lang, "glossary": len(entries), "ipa": spoken})
    return {
        "missing_transitions": [
            {"transition": hop, "languages": sorted(ls)} for hop, ls in sorted(holes.items(), key=lambda kv: -len(kv[1]))
        ],
        "no_rules": no_rules,
        "no_ancestry": sorted(no_ancestry, key=lambda r: -r["glossary"]),
        "no_ipa": sorted(no_ipa, key=lambda r: -r["glossary"]),
    }


def rule_hygiene(reports: dict[str, dict]) -> dict:
    """Rules that never apply, and rules that apply without ever landing a word."""
    fired: Counter[str] = Counter()
    exact: Counter[str] = Counter()
    for rep in reports.values():
        fired.update(rep.get("rule_fired") or {})
        exact.update(rep.get("rule_exact") or {})
    registered = {}
    for (src, dst), rs in data.rulesets().items():
        for r in rs.rules:
            registered[f"{dst}|{r.id}"] = {"id": r.id, "from": src, "to": dst, "tier": r.tier, "name": r.name}
    dead = [registered[k] | {"fired": 0} for k in registered if fired.get(k, 0) == 0]
    sterile = [
        registered[k] | {"fired": fired[k], "exact": exact.get(k, 0)}
        for k in registered
        if fired.get(k, 0) >= 5 and exact.get(k, 0) == 0
    ]
    sterile.sort(key=lambda r: -r["fired"])
    dead.sort(key=lambda r: (r["to"], r["id"]))
    return {"dead": dead, "sterile": sterile[:25]}


def _fmt_example(ex: dict) -> str:
    return f"`{ex['ancestor']}` → `{ex['output']}` ≠ **{ex['word']}**"


def render(report: dict) -> str:
    reps = report["languages"]
    total_glossary = sum(r["glossary"] for r in reps.values())
    total_exact = sum(r["exact"] for r in reps.values())
    total_probe = sum(r["spelling_probe"] for r in reps.values())
    total_near = sum(r["near"] for r in reps.values())
    total_unchanged = sum(r["unchanged"] for r in reps.values())
    lines: list[str] = []
    add = lines.append

    add("# Worklist")
    add("")
    add(f"Generated by `pie worklist` on {report['generated']} "
        f"({report['seconds']} s, sample per language: {report['limit'] or 'full corpus'}). "
        "**Do not edit by hand** — change the model or the tool and regenerate.")
    add("")
    add("## Snapshot")
    add("")
    add("| measure | value |")
    add("|---|---|")
    add(f"| glossaries in this run | {total_glossary:,} words |")
    add(f"| explained by the sound laws (phonemic) | {total_exact:,} |")
    add(f"| spelled correctly by the orthographic layer | {total_probe:,} |")
    add(f"| near misses (≤4 edits) | {total_near:,} |")
    add(f"| no rule applied (identity is not an explanation) | {total_unchanged:,} |")
    add("")

    add("## 1 · Miss signatures — the rule candidates")
    add("")
    add("The same small edit recurring across a language is **one missing rule**, not "
        "hundreds of bugs. `kind` names the layer that owns it: `phonology` is a "
        "sound law, `spelling` a writing convention (orthographic tier, measured with "
        "`spelling.plausible`, so a letter coincidence does not count).")
    add("")
    add("| n | language | signature | kind | hurts | example |")
    add("|---:|---|---|---|---|---|")
    rows = []
    for lang, rep in reps.items():
        for sig in rep["signatures"]:
            if sig["kind"] not in audit.ACTIONABLE:
                continue
            rows.append((sig["count"], lang, sig))
    rows.sort(reverse=True, key=lambda r: r[0])
    for count, lang, sig in rows[:40]:
        blame = ", ".join(f"`{b}`" for b in (sig.get("blamed") or [])) or "—"
        example = _fmt_example(sig["examples"][0]) if sig["examples"] else "—"
        add(f"| {count} | `{lang}` | `{sig['signature']}` | {sig['kind']} | {blame} | {example} |")
    add("")

    add("## 2 · Where the words break (transition blamed)")
    add("")
    add("A transition is blamed when it moved the form *away* from the attested word, "
        "or when it is the last one and added nothing. This is where to read the rules again.")
    add("")
    add("| n | transition | languages |")
    add("|---:|---|---|")
    blamed: Counter[str] = Counter()
    who: dict[str, set[str]] = defaultdict(set)
    for lang, rep in reps.items():
        for hop, n in rep["silent"].items():
            blamed[hop] += n
            who[hop].add(lang)
    for hop, n in blamed.most_common(15):
        add(f"| {n} | `{hop}` | {', '.join(sorted(who[hop]))} |")
    add("")

    add("## 3 · Structural gaps")
    add("")
    add("### Rule files that do not exist yet")
    add("")
    add("| missing transition | languages blocked |")
    add("|---|---|")
    for row in report["structural"]["missing_transitions"]:
        add(f"| `{row['transition']}` | {', '.join(row['languages'])} |")
    add("")
    silent = report["structural"].get("no_ipa") or []
    if silent:
        add("### Glossaries without recorded pronunciation")
        add("")
        add("A spelling match is only counted when the derived phonemes are plausible "
            "against the dictionary's IPA (`spelling.plausible`); where a stage has no "
            "IPA, its orthographic layer cannot be measured at all.  This is a data task "
            "for W1, not a rule task.")
        add("")
        add("| language | glossary | with IPA |")
        add("|---|---:|---:|")
        for row in silent[:12]:
            add(f"| `{row['lang']}` | {row['glossary']:,} | {row['ipa']:,} |")
        add("")
    low = report["structural"]["no_ancestry"]
    if low:
        add("### Lexicons with almost no ancestry links")
        add("")
        add("| language | glossary | linked |")
        add("|---|---:|---:|")
        for row in low[:12]:
            add(f"| `{row['lang']}` | {row['glossary']:,} | {row['linked']:,} |")
        add("")

    add("## 4 · Rule hygiene")
    add("")
    dead = report["rules"]["dead"]
    add(f"**Registered but never applied in this run ({len(dead)}).** Either the context is "
        "wrong, the rule is dead weight, or the corpus has no word that reaches it. "
        "A rule that never applies cannot explain anything and is a false claim on the rules page.")
    add("")
    for r in dead[:25]:
        add(f"- `{r['to']}|{r['id']}` ({r['tier']}, {r['from']}→{r['to']}): {r['name']}")
    if len(dead) > 25:
        add(f"- … and {len(dead) - 25} more (see `data/worklist.json`)")
    add("")
    sterile = report["rules"]["sterile"]
    if sterile:
        add("**Applies often, never lands a word.** These need a context fix or an example "
            "that shows what they are for.")
        add("")
        add("| rule | applied | exact | name |")
        add("|---|---:|---:|---|")
        for r in sterile:
            add(f"| `{r['to']}|{r['id']}` | {r['fired']} | {r['exact']} | {r['name']} |")
        add("")

    add("## 5 · Per language")
    add("")
    add("| language | glossary | explained | spelling probe | near | blamed | top signatures |")
    add("|---|---:|---:|---:|---:|---|---|")
    for lang, rep in reps.items():
        tops = [s for s in rep["signatures"] if s["kind"] in audit.ACTIONABLE][:3]
        sig_txt = "; ".join(f"`{s['signature']}` ×{s['count']}" for s in tops) or "—"
        top_blame = next(iter(rep["silent"]), "—")
        add(f"| `{lang}` | {rep['glossary']:,} | {rep['exact']:,} | {rep['spelling_probe']:,} | "
            f"{rep['near']:,} | `{top_blame}` | {sig_txt} |")
    add("")

    add("## 6 · Suggested next tasks")
    add("")
    add("Ranked from the numbers above: spelling work first where the probe is large, "
        "then the sound law that is blamed for the most words. Each task is one pull "
        "request with its own citations and a measured delta.")
    add("")
    spelling_first = sorted(
        ((r["spelling_probe"], lang) for lang, r in reps.items() if r["spelling_probe"] >= 50),
        reverse=True,
    )
    n = 0
    from . import spelling as _spelling

    for probe, lang in spelling_first[:5]:
        n += 1
        if _spelling.applies(lang):
            add(f"{n}. **Extend `data/spelling/{lang}.yaml`** — {probe:,} words in this "
                "language are still one writing convention away (see the signatures above).")
        else:
            add(f"{n}. **Write `data/spelling/{lang}.yaml`** — a plain letter table would "
                f"already fix {probe:,} words; cite the conventions and keep the tier "
                "`orthographic`.")
    for hop, count in blamed.most_common(5):
        n += 1
        langs = ", ".join(f"`{x}`" for x in sorted(who[hop])[:4])
        add(f"{n}. **Read `{hop}` again** — blamed for {count:,} misses ({langs}); "
            "check for an over-applying law, then for the missing one.")
    for row in report["structural"]["missing_transitions"][:4]:
        n += 1
        add(f"{n}. **Write the `{row['transition']}` rule file** — "
            f"{len(row['languages'])} languages cannot be measured without it "
            f"({', '.join(row['languages'][:4])}).")
    add("")
    return "\n".join(lines) + "\n"
