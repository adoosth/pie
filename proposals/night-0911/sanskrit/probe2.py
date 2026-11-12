"""Group Sanskrit misses by the phonemic difference between the laws' output and
the dictionary's own transliteration (diagnosis only — never a match target)."""
from __future__ import annotations
import sys, difflib, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from pie import data, spelling
from pie.rules import derive
from coverage import (ancestor_starts, exact_kind, orthographic_hit,
                      citation_hit, _identity_hit, distance)

LANG = "sa"
chain = data.derivation_chain(LANG)
rs = data.rulesets()


def norm_translit(t: str) -> str:
    import unicodedata
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return t.replace("ˈ", "").replace("ṛ", "r̥").replace("ḷ", "l̥").replace("ṝ", "r̥̄")


def sig(a, b):
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    parts = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        parts.append(f"{a[i1:i2]}→{b[j1:j2]}")
    return " ".join(parts) or "="


rows = []
for entry in data.lexicon(LANG):
    target = str(entry.get("word") or "").strip()
    if not target or entry.get("recon"):
        continue
    cands = ancestor_starts(entry, chain)
    if not cands:
        continue
    outputs = []
    for stage, form in cands:
        d = derive(form, chain[chain.index(stage):], rs)
        if d.skipped:
            continue
        outputs.append((d.output, len(d.steps), stage))
    if not outputs:
        continue
    exact = any(exact_kind(o, target) and n for o, n, s in outputs)
    orth = orthographic_hit(outputs, LANG, target, entry.get("ipa") or "")
    cit = citation_hit(outputs, LANG, target, entry.get("ipa") or "")
    ident = _identity_hit(outputs, target, entry)
    rows.append(dict(word=target, pos=entry.get("pos"), translit=entry.get("translit"),
                     ipa=entry.get("ipa"), outputs=outputs, exact=exact, orth=orth,
                     cit=cit, ident=ident, anc=entry.get("anc")))

resolved = [r for r in rows if r["exact"] or r["orth"] or r["cit"] or r["ident"]]
miss = [r for r in rows if r not in resolved]
print("eligible", len(rows), "resolved", len(resolved), "miss", len(miss))

sigs = Counter()
ex = defaultdict(list)
for r in miss:
    if not r["translit"]:
        continue
    want = norm_translit(r["translit"])
    best = min(r["outputs"], key=lambda o: distance(o[0].replace("ˈ", ""), want))
    got = norm_translit(best[0])
    s = sig(got, want)
    sigs[s] += 1
    if len(ex[s]) < 3:
        ex[s].append((r["word"], r["translit"], got, best[2], r["pos"]))

print()
for s, c in sigs.most_common(60):
    print(f"{c:5d}  {s:28s}", "; ".join(f"{e[0]}({e[1]}:{e[2]})" for e in ex[s][:2]))

json.dump(rows, open("/tmp/sa_rows.json", "w"), ensure_ascii=False)
