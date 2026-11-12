"""Sanskrit: what the remaining misses are, and what an ending would win."""
from __future__ import annotations
import sys, re
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
from pie import data, spelling, citation
from pie.rules import derive
from coverage import ancestor_starts, exact_kind, orthographic_hit, citation_hit, _identity_hit

LANG="sa"; chain=data.derivation_chain(LANG); rs=data.rulesets()
resolved=0; miss=[]
for e in data.lexicon(LANG):
    t=str(e.get("word") or "").strip()
    if not t or e.get("recon"): continue
    outs=[]
    for stage,form in ancestor_starts(e,chain):
        d=derive(form,chain[chain.index(stage):],rs)
        if not d.skipped: outs.append((d.output,len(d.steps),stage))
    if not outs: continue
    ok = any(exact_kind(o,t) and n for o,n,s in outs) or orthographic_hit(outs,LANG,t,e.get("ipa") or "") \
         or citation_hit(outs,LANG,t,e.get("ipa") or "") or _identity_hit(outs,t,e)
    if ok: resolved+=1
    else: miss.append((e,outs))
print("resolved",resolved,"miss",len(miss))

# composition of the misses
pos=Counter(e.get("pos") for e,_ in miss)
print("pos of misses", pos.most_common(10))
virama=sum(1 for e,_ in miss if e["word"].endswith("\u094d"))
print("consonant-final (virama) misses", virama)
cy=sum(1 for e,_ in miss if e.get("etym") and ("compound" in e["etym"].lower() or " + " in e["etym"] or "Compounded" in e["etym"]))
print("etym mentions compound/+", cy)
borrow=sum(1 for e,_ in miss if any(r in ("borrow","lbor","slbor","obor") for _l,_w,r in (e.get("anc") or []) if len((_l,_w,r))==3))
print("ancestry marks a borrowing", borrow)

# what an extra citation ending would win (measured, one ending at a time)
print()
extra = ["am","m","as","ā","ī","ū","n","s","ṣ","ḥ","aḥ","e","o","āḥ","īḥ","ūḥ","us","um","im","anam"]
for end in extra:
    won=0; ex=[]
    for e,outs in miss:
        t=e["word"]; ipa=e.get("ipa") or ""
        for out,n,stage in outs:
            if not n or not out.endswith(end) or len(out)<=len(end): continue
            stem=out[:-len(end)]
            if spelling.spell(stem,LANG)==t and spelling.plausible(stem,ipa,LANG):
                won+=1; ex.append(t); break
    print(f"  ending {end!r}: +{won}  e.g. {', '.join(ex[:5])}")
