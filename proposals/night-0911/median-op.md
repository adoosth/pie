# Old Persian words with the Median reflex: what the laws can and cannot reach

Source: `proposals/night-0911/op.md` §3.2 (the 74 misses, word by word), measured
2026-11-09 against `083dfe5` + the day's work.  Kent 1953 §§85–91;
Hoffmann–Forssman 2004.

## The claim

Old Persian's own outcomes of PIr *c and *j are **θ** and **d** (`c_to_theta`,
`j_to_d`: 𐎰𐎼𐎭 θarda- 'year', 𐎭𐎿𐎫 dasta- 'hand').  A set of OP words shows
**s** and **z** instead — the Northwest Iranian (Median) outcome — and Kent
assigns each one to Median or to an outside source rather than to the inherited
lexicon.  Eleven of the 74 OP misses are exactly this.

## What was registered (off by default, cited)

| law | claim | why it cannot be the default |
|---|---|---|
| `ira-pro__peo: c_to_s_median` | PIr *c > OP s in Median words | measured: applied everywhere it gains 𐎠𐎿 and loses 𐎰𐎼𐎭, 𐎠𐎼𐎰, 𐎧𐏁𐏂 |
| `ira-pro__peo: cw_to_s_median` | PIr *cw > OP s (asa- 'horse') | aspa- is also recorded; a default flip is net zero |
| `ira-pro__peo: j_to_z_median` | PIr *j [dz] > OP z (bāzu-) | already registered 2026-11-08; five d-words would lose |

All three are `tier: proposed`, `off_by_default: true`, with examples, and
`check-rules` stays green.  A word turns one on with its **pathway**, which now
records `enabled` as well as `disabled` (`service.store_pathway`), and the word
page says which law it switched on and why.

## What the engine could actually complete (measured)

Tested with `service.hierarchy(..., enabled=[…])`; a match means the laws'
form is a possible reading of the recorded signs.

| word | record | with the Median law | verdict |
|---|---|---|---|
| 𐏀𐎴 zana 'man' | z | zˈanah | **match** — pathway stored, Kent §88 |
| 𐎲𐎠𐏀𐎢 bāzu 'arm' | z | bāzˈuš | differs only in the final case vowel: the ancestor is the nom. sg., the record is the stem |
| 𐎠𐎿 asa 'horse' | s | aθ | the recorded ancestor is the bare root *h₁eḱ (the *-wo- is not in the chain), so *cw never appears |
| 𐎠𐎿𐎲𐎠𐎼 asabāra | s | aθ | same: the *-wo- is missing from the ancestry |
| 𐎠𐎿𐎶𐎴 asman 'sky' | sm | ˈasmā | the ancestor is the nom. sg. *aćmā; the record is the -an stem |
| 𐎣𐎠𐎿𐎣 kāsaka 'glass' | s | kˈāsti | wrong etymon (*kā́ćti, not *kā́ćakah) |
| 𐎱𐎠𐎼𐎿 pārsa 'Persian' | s | pˈarsuš | wrong etymon shape (*párcuš, not *pā́rçah) and a different formation |
| 𐎺𐏀𐎼𐎣 vazraka | z | waz | the ancestor is the noun *wáȷ́ras 'club', not the adjective |
| 𐏃𐏀𐎠𐎴𐎶 hazānam | z | hizwˈā | the OP word has an *n* the ancestor lacks (*hazāna-* vs Av. *hizuuā-*) |

**One word in eleven is a law question; the other ten are ancestry or paradigm
questions** (W1/W5), not new laws.  That is the finding: the Median rule is
right and it is already there — what is missing is the etymon each record
actually states, which is a lexicon job, not a sound-law job.

## Reproduce

```bash
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 - <<'PY'
from pie import service
print(service.hierarchy('peo', '𐏀𐎴', ['ira-pro~peo:j_to_d'],
                        enabled=['ira-pro~peo:j_to_z_median'])['result'])
PY
PYTHONPATH=src python3 tools/coverage.py --langs peo --limit 0 --out /tmp/peo.json
```
