#!/usr/bin/env python3
"""Cost of the two suspect laws under the *published* selection rule."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import covmirror as m  # noqa: E402

on = m.measure()
on_words = {e["word"].strip() for e, _ in on["counted"]}
print(f"law on   : counted {len(on['counted'])}  missed {len(on['missed'])}")

for law in ("peo~pal:final_h_loss", "peo~pal:xw_to_x_initial",
            "ira-pro~peo:laryngeal_lengthening"):
    off = m.measure((law,))
    off_words = {e["word"].strip() for e, _ in off["counted"]}
    gained = sorted(off_words - on_words)
    lost = sorted(on_words - off_words)
    print(f"\n{law} OFF: counted {len(off['counted'])}")
    print(f"  gains  {len(gained)}: {', '.join(gained)}")
    print(f"  losses {len(lost)}: {', '.join(lost)}")

# how often each law fires in the derivation the miss report shows
fired = {}
for entry, r in on["missed"]:
    if r.best is None:
        continue
    ids = {s.rule_id for s in r.best[3].steps}
    for k in ("final_h_loss", "xw_to_x_initial", "laryngeal_lengthening"):
        fired[k] = fired.get(k, 0) + (k in ids)
print(f"\nmisses whose nearest derivation fires: {fired}")
hits = sum(1 for e, r in on["counted"] if r.orth and any(
    s.rule_id == "final_h_loss" for s in r.orth[2].steps))
print(f"counted words whose counted derivation fires final_h_loss: {hits}")
