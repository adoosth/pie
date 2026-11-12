# 011 · Give Proto-Iranian-internal derivation a rung it can stand on

- **Status:** partially implemented 2026-11-09 — own-stage constructions start at the word and print their pieces (`service._own_construction`, `built_as`); a separate formation rung and formation laws are still open
- **Stream:** W1 (sources & ancestry) / the word page / formation laws
- **Author:** auditor of Proto-Iranian range D (audit-d.md, rows 316–402)
- **Reviewer:** the templates that state the derivation (`{{com}}`, `{{af}}`, `{{participle of}}`), `data/pathways.jsonl`, `docs/DECISIONS.md`

## Claim

When a Proto-Iranian entry says its word is **built out of Proto-Iranian material**
(`{{com|ira-pro|*ráwčah|*-kah}}`, `{{af|ira-pro|*xšáfš|*kawráh}}`, `{{participle of|ira-pro|*táwHti}}`),
the record has named an ancestor the ladder cannot hold: `ancestor_starts()` skips anything at
`chain[-1]`, because a chain has no Proto-Iranian → Proto-Iranian step. The word therefore either
starts lower and stops at the bare base, or (when the builder records no ancestry at all) has no
ladder. The derivation the entry states — base **+ morpheme** — is never shown, and the page
silently implies the headword is an underived inheritance.

The fix is **not** a sound law and **not** a licence to accept a form. It is a second kind of
rung: a *formation* rung, which carries the record's own pieces, a cited formation law for the
morpheme it adds, and the same "no rule, no rung" discipline as the sound laws.

## What the model does now

```python
for lang, word, rel in _ancestry_triples(entry):
    ...
    if lang not in chain or lang == chain[-1] or rel == "borrow":
        continue          # a Proto-Iranian base can never be a start
```

`built_as` rows are only used by `_rung_built()` to *print* the pieces on a rung; they do not
enter `ancestor_starts()`. Consequently:

| word | record states | ladder today |
|---|---|---|
| `ráwčakah` | `{{com|ira-pro|*ráwčah|*-kah}}` | starts at PIE *léwkos (cognate set), ends `rˈawkah` |
| `ráwčikah` | `{{com|ira-pro|*ráwčah|*-ikah}}` | same, ends `rˈawkah` |
| `ráwčaka` | `{{desc|ira-pro|*ráwčah}}` | **no ladder at all** |
| `xšapkawráh` | `{{af|ira-pro|*xšáfš|*kawráh}}` | **no ladder** |
| `xšáfnyah` | `{{m|ira-pro|*xšápā}} ~ {{af|ira-pro||*xšáfnah|*-yah}}` | **no ladder** |
| `WindáhuHarnāh` | `{{af|ira-pro|*windáns|*huHarnáh}}` | **no ladder** |
| `udzwaydáyati` | `{{af|ira-pro|*udz-|*waydáyati}}` | starts at root *weyd, ends `wayd` |
| `ÁryānaHm` | “genitive plural of `{{m|ira-pro|*Áryah}}`” | **no ladder** |
| `tuHáns` (verb + adj) | `{{participle of|ira-pro|*táwHti}}` | **no ladder** (both entries) |
| `windáns` (verb + adj) | `{{participle of|ira-pro|*winásti}}` | **no ladder** (both entries) |

Every base in that table is itself explained: `*ráwčah` is exact from PII *ráwčas,
`*xšáfš` exact from PII *kšáps, `*xšápā` exact from PII *kšápā, `*Áryah` exact from PII *Áryas,
`*táwHti` exact from PIE *téwh₂-ti, `*winásti` exact from PII *winátˢti, `*waydáyati` exact from
PIE *woydéyeti. So the model is one morphological step away from twelve rows in this range, and
nothing phonetic is missing.

## Measurement (2026-11-09, `data/lexicon/ira-pro.jsonl.gz`, 416 rows)

- 79 rows carry a `built_as` row whose `lang` is `ira-pro` — the derivation is stated and unusable.
- 32 of those 79 have no ladder at all; only 9 are exact today. **70 rows are blocked** (upper
  bound: a formation law will not close all of them).
- 30 rows have neither `anc` nor `built_as`; one of those (`xšwáš`) has a parse gap
  (`{{ety|…|tree=+}}`), the other 29 record nothing usable.
- In range D (rows 316–402) this is the single largest cause: **12 rows**, against 6 for the
  root-start cause (`proposals/010`) and 6 for "nothing recorded".

## What to build

1. **Keep a same-stage piece as an ancestor.** In `_ancestry_triples()`, a `rel == "derived"`
   row at the word's own stage should survive into `ancestor_starts()` as a *formation* start
   (`(ira-pro, *ráwčah)`, `joined=<morpheme>`). It is not a stage transition; the ladder must not
   run `derive()` across it, and the rung must be labelled a formation, not an inheritance.
2. **Register formation laws, one per morpheme, with a citation** — the same `tier` discipline as
   sound laws (`established` / `proposed`). The project already has one: `ine-pro~iir-pro:animal_ka`
   (`*wr̥pa-ka`, de Vaan 2000 §13). The set this range needs is small:
   `*-kaH` (`ráwčaka`, `ráwčakah`), `*-ikaH` (`ráwčikah`), `*-yah` (`xšáfnyah`), `*-aH`
   (`spr̥Hgah`, `wardah`), `*-má-` (`spr̥Hgmáh`), the present participle `*-ant-s`
   (`tuHáns`, `windáns`), prefix `*wi-` (`wiHr̥Háh`), and a compounding join (`xšapkawráh`,
   `WindáhuHarnāh`, `udzwaydáyati`, `wicápuθrah`).
3. **Make a pathway follow the record, not one language's word.** `animal_ka` is enabled only by
   the pathway stored on Persian گربه, so the Proto-Iranian word it builds (`wr̥pa-ka`) does not see
   it. A formation named in an entry should be available to every word whose record states it,
   with the pathway stored once per formation (the reason for switching it off elsewhere — it adds
   a syllable — is a property of the formation, not of the language).

## Predicted gain

- **+12 rows in range D** (the table above), 6 of which have no ladder at all today.
- Up to **70 rows across the Proto-Iranian glossary** where the derivation is already stated
  (79 same-stage `built_as` rows, 9 exact today).
- The page stops saying "PIE root → PIr rˈawkah" for a word whose own record says
  `*ráwčah + *-kah`.

## Risks and guardrails

- A formation law must be **cited and reversible**, exactly like a sound law; "the record suggests
  a suffix" is not enough (`wardah` is marked `unc:1` in its own etymon tree and must stay
  uncertain — it is not in the 12).
- The formation must be **printed as a formation**: a rung that says `*ráwčah + *-kah` is a
  statement about morphology, and must never be counted as a sound-law explanation in
  `tools/coverage.py`. The published exact number should not move; a new, separate layer
  ("built from recorded pieces") should carry these rows, or they should be reported as
  `formation` beside `exact`.
- A base must be **explained on its own** before it can be joined: `WindáhuHarnāh` needs
  `*huHarnáh`, which no entry records (the name stays half-unattested until one does).
- Compounding is not free word order: `xšapkawráh` is `*xšáfš + *kawráh` with the first piece in
  its stem form, and the join rule has to state what happens to the pieces' endings, or it will
  invent forms. Where the record does not state the joined shape, the rung stays a record, not a
  derivation.
