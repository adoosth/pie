# 010 · Is a cognate-set root the word's ancestor?

- **Status:** implemented 2026-11-09 (`service.ancestor_starts`, `hierarchy.etymon_record`; docs/DECISIONS.md, "The ancestor the template states")
- **Stream:** W1 (sources & ancestry) / the word page
- **Author:** auditor of Proto-Iranian range C (audit-c.md, rows 211–315)
- **Reviewer:** the ancestry rows themselves, `tools/coverage.py`, `docs/PROGRAMME.md` (the one rule)

## Claim

When a Proto-Iranian entry records a **PII (or PIr) word** as its ancestor and its cognate
set names a bare PIE **root**, the ladder must start at the recorded word, not at the root.
A root is an etymon to which the word is related; it is not a stage the word was inherited
from, and it cannot produce the word's derivational morphology, so a ladder that starts
there shows a red rung for a word whose own record is exact.

This is not a sound law and not a new layer. It is a start-selection rule: among the forms
the entry quotes, the ladder starts at the lowest one whose laws reach the headword, and the
root stays visible as a cognate above the ladder (the shape `dáwxšati` already has, where the
PIE rung quotes both the root `*dewk-` and the word `*déwk-s-eti`).

## What the model does now

`service.hierarchy` builds `candidates = ancestor_starts(entry, chain)` from `entry['anc']`,
then:

```python
linked_by_set = (bool(pie) and not formed
                 and not any(stage == chain[0] for stage, _w in candidates))
if linked_by_set:
    candidates.insert(0, (chain[0], normalise_etymon(pie)))
...
start_stage, start_form = candidates[0]
```

`pie` falls back to `entry['cog']` (`_pie_form`), so for any entry whose ancestry stops below
PIE and whose cognate set is a root, the root is inserted **first** and becomes the start —
even though `ancestor_starts` documents itself as "every usable ancestor form recorded for
this word, PIE first" and the word's own record stops lower down.

## Measurement (2026-11-09)

Across all 402 headwords of `data/lexicon/ira-pro.jsonl.gz`: 354 have a ladder; **46 rows
(43 distinct words)** start at a bare PIE root while a lower recorded form already reaches
the headword (`starts[…].match == true`). **38 of those 46 are already counted exact** by
`tools/whatif.py`/`tools/coverage.py`, i.e. the release and the word page disagree; 4 are
zero-step identities the counter does not count, and 4 need a second fix.

Inside audit range C (rows 211–315) the same condition holds for 20 rows, of which 18 reach
the headword from the recorded form:

| word | recorded ancestor | ladder starts at | what the record's form gives |
|---|---|---|---|
| `háwmah` | PII *sáwmas | PIE *sewh₁ | `hˈawmah` (match) |
| `háxā` | PII *sákʰā | PIE *sekʷ | `hˈaxā` (match) |
| `járati` | PII *ȷ́ʰárati | PIE *ǵʰer | `jˈarati` (match) |
| `naybah` | PII *naybʰas | PIE *neybʰ | `naybah` (match) |
| `puθráh` | PII *putrás | PIE *peh₂w | `puθrˈah` (match) |
| `paycáh` | PII *payćás | PIE *peyḱ | `paycˈah` (match) |
| `pištáh` | PII *pištás | PIE *peyḱ | `pištˈah` (match) |
| `pančaHcát` | PII *pančaHćát | PIE *pénkʷedḱomth₂ | `pančaHcˈat` (match) |
| `jā́mātā` | PII *ȷ́ā́mātā | PIE *ǵem | `jˈāmātā` (match) |
| `Hā́fš` | PII *Hā́ps | PIE *h₂ep | `Hˈāfš` (match) |

The templates, as written (all from `Reconstruction:Proto-Iranian/<word>`, checked 2026-11-09):

- `{{inh|ira-pro|iir-pro|*sáwmas}}` (háwmah) — no PIE row at all; the root `sewh₁` comes only from the cognate set.
- `{{inh|ira-pro|iir-pro|*sákʰā}}` + `{{root|ira-pro|ine-pro|*sekʷ-}}` (háxā).
- `{{inh|ira-pro|iir-pro|*ȷ́ʰárati}}` (járati) — again the root is only `{{root|ira-pro|ine-pro|*ǵʰer-}}`.
- `{{inh|ira-pro|iir-pro|*naybʰas}}` + `{{der|ira-pro|ine-pro|*neybʰ-}}` (naybah).
- `{{inh|ira-pro|iir-pro|*pištás|t=flour, meal}}` (pištáh) — the cognate set names `*peyḱ-` 'to crush'.

## Why not simply drop the cognate link

The cognate set is what lets the ladder go above the ancestry (and it is right to: `Háǰiš`,
`mazgáh`, `párcah` start at full PIE words taken from the cognate set and are exact). The
change is only about **roots**: a form the stage glossary itself stores with `pos: root`, or a
form the ancestry writes with a trailing hyphen (`*kʷer-`). Where the record names nothing
below PIE and only a root (rows 250, 261, 271, 281 in audit C: `karah`, `káwfš`, `mayθaH`,
`máyθanam`), the root start is the honest one and must be kept — those words are not
explained, and the page should keep saying so.

## Predicted gain

- 46 ladders (43 distinct words) correct by construction; 38 of them currently contradict the
  published exact count. No law, no lexicon edit, no change to the counter's definition.
- In audit range C: 18 rows green, 2 (`Háčart`, `jr̥dáyam`) still need a law/accent decision,
  and the 6 root-only/no-record rows are untouched.
- Side effect: the PIE rung stops being the ladder's start for these words, so the rung must
  be quoted as a record above the ladder (as `dáwxšati` does) rather than disappear.

## Risks

- A word whose *only* word-level ancestor is the root loses its PIE rung from the derived
  chain; if the reviewer wants that rung, it has to be shown as a record, not a derivation.
- `cog['pie']` is also used to link a word to an etymological root for display; the change
  must keep that link (it is a cognate, not an ancestor).
- Some of the 46 may have a recorded form that reaches the headword only through a pathway
  (a formation law switched on for that word); the selection must respect `keep_formed`, or
  `h₂wl̥pís + *-ka-` would start at a form that only exists when its own law runs.

## What would close it

Implement the start rule in `service.hierarchy`/`ancestor_starts`, then re-run the ladder over
all 354 ladder-bearing ira-pro words and assert: (a) every word whose recorded form reached the
headword now has that rung green, (b) no word that was green becomes red, (c) the 6 root-only
and no-record words in this range are unchanged. The check is the payload's own `starts` field,
so it is a before/after diff of `hierarchy.exact`, not a new metric.
