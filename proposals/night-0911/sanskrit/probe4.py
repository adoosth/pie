from __future__ import annotations
import sys, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
from pie import data, spelling
from pie.rules import derive
from coverage import ancestor_starts
LANG="sa"; chain=data.derivation_chain(LANG); rs=data.rulesets()
def deb(t): return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c)!="Mn")
for word in sys.argv[1:]:
    for entry in [e for e in data.lexicon(LANG) if e["word"]==word and e.get("pos")][:2]:
        print("==", entry["word"], entry.get("translit"), entry.get("ipa"), entry["pos"], entry.get("etym","")[:120])
        for stage, form in ancestor_starts(entry, chain):
            d=derive(form, chain[chain.index(stage):], rs)
            print(f"  {stage:8s} {form:18s} -> {d.output:20s} steps={[s.rule_id for s in d.steps]}")
