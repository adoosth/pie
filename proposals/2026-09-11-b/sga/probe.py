import sys
sys.path.insert(0,'src'); sys.path.insert(0,'tools')
import coverage
from pie import data
m = coverage.measure('sga', {}, data.derivation_chain('sga'), data.rulesets(), None, 0)
if isinstance(m, tuple): m = m[0]
for k in ('glossary','identified','tested','exact','orthographic','identity','explained','near','closest_misses','top_rules','errors','gaps','bound_form','lemma'):
    v=m.get(k)
    if k=='closest_misses':
        print(k, len(v or []))
        for x in (v or [])[:40]: print('   ', x)
    else: print(k, '=', v)
