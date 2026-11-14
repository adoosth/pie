"""Miss analysis for Sanskrit against the inc-pro→sa transition (batch 0911)."""
from __future__ import annotations
import sys, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling, citation       # noqa: E402
from pie.rules import derive                    # noqa: E402
from coverage import (ancestor_starts, exact_kind, orthographic_hit,   # noqa: E402
                      citation_hit, _identity_hit, distance)

LANG = sys.argv[1] if len(sys.argv) > 1 else "sa"
chain = data.derivation_chain(LANG)
rulesets = data.rulesets()
print("chain", chain)
entries = data.lexicon(LANG)

rows = []
for entry in entries:
    target = str(entry.get("word") or "").strip()
    if not target or entry.get("recon"):
        continue
    cands = ancestor_starts(entry, chain)
    if not cands:
        continue
    outputs = []
    for stage, form in cands:
        try:
            d = derive(form, chain[chain.index(stage):], rulesets)
        except Exception as exc:
            outputs.append((f"ERR {exc}", 0, stage))
            continue
        if d.skipped:
            continue
        outputs.append((d.output, len(d.steps), stage))
    exact = any(exact_kind(o, target) and n for o, n, s in outputs)
    orth = orthographic_hit(outputs, LANG, target, entry.get("ipa") or "")
    cit = citation_hit(outputs, LANG, target, entry.get("ipa") or "")
    ident = _identity_hit(outputs, target, entry)
    rows.append({"word": target, "pos": entry.get("pos"), "translit": entry.get("translit"),
                 "ipa": entry.get("ipa"), "outputs": outputs, "exact": exact,
                 "orth": orth, "cit": cit, "ident": ident,
                 "anc": entry.get("anc")})

n = len(rows)
print("eligible", n,
      "exact", sum(r["exact"] for r in rows),
      "orth", sum(1 for r in rows if r["orth"]),
      "cit", sum(1 for r in rows if r["cit"]),
      "ident", sum(1 for r in rows if r["ident"]))

# misses: compare the spelled form of the best output to the target
def spelled(o):
    return spelling.spell(o, LANG)

def diffsig(a, b):
    # signature of the difference a->b as multiset of char edits, using simple alignment
    import difflib
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    parts = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        parts.append(f"{a[i1:i2]}→{b[j1:j2]}")
    return " ".join(parts) or "="

sigs = Counter()
examples = defaultdict(list)
miss = [r for r in rows if not (r["exact"] or r["orth"] or r["cit"] or r["ident"])]
for r in miss:
    best = min(r["outputs"], key=lambda o: distance(o[0], r["word"]))
    out = best[0]
    sig = diffsig(spelled(out), r["word"])
    sigs[sig] += 1
    if len(examples[sig]) < 4:
        examples[sig].append((r["word"], out, spelled(out), r["translit"], r["ipa"], best[2]))

print("\nmiss count", len(miss))
for sig, c in sigs.most_common(45):
    print(f"{c:5d}  {sig}")
    for ex in examples[sig][:2]:
        print("        ", ex)

if len(sys.argv) > 2 and sys.argv[2] == "--json":
    json.dump(rows, open("/tmp/sa_rows.json", "w"), ensure_ascii=False, indent=1)
