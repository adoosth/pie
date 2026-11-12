# 012 · Are PII final *-r and *-n lost after a long vowel?

- **Status:** open — measured, awaiting review
- **Stream:** W4 (new laws)
- **Author:** auditor of Proto-Iranian range A (audit-a.md, rows 1–105)
- **Reviewer:** `tools/council.py` (2026-11-09, `ine-pro → iir-pro`, exact layer)

## Claim

The nominative singular of the PIE *-ēr/*-ēn stems ends in *-ā in Proto-Indo-Iranian:
the stem-final *-r or *-n is not kept. Two laws in `ine-pro__iir-pro.yaml` state it:

```yaml
- {id: final_r_after_long_vowel, order: 200, match: r, replace: "",
   env: {left: "(ā|ē|ō)", right: "#"}}
- {id: final_n_after_long_vowel, order: 201, match: n, replace: "",
   env: {left: "(ā|ē|ō)", right: "#"}}
```

Registered after the vowel laws, the left context is already *ā, so the environment is
"a long vowel immediately before the end of the word". Candidate YAML:
`/tmp/cand/final_nr.yaml` (two rules, `tier: proposed`, references
`hoffmann-forssman-2004`).

## Why it is needed

The model currently keeps the resonant, so the PIE→PII rung of every kinship and
n-stem nominative contradicts the record by one segment:

| PIE (recorded) | PII (recorded) | model's PII rung today |
|---|---|---|
| *bʰréh₂tēr | *bʰráHtā | *bʰrˈaHtār |
| *dʰugh₂tḗr | *dʰúgdʰā | *dʰugHtˈār |
| *(h₂)uksḗn | *ukšā́ | *ukšˈān |
| *pḱtḗn | *pćā́ 'comb' | *pštˈān |
| *wérsēn | *(w)ŕ̥šā | *wˈaršān |
| *h₂nḗr | *Hnā́ | *Hnˈār |
| *médʰ-tēr | *máHtā | *máHtār |

Sanskrit bhrā́tā, Av. brātā, Skt. ukṣā́, pánthāḥ-type endings agree: the *-r/-n belongs to
the oblique stem, not to the nominative (Hoffmann & Forssman 2004, Lautlehre on the
*-ēr/*-ēn stems; Mayrhofer 1986 on the Sanskrit nominatives).

## Measurement

`python3 tools/council.py --rules /tmp/cand/final_nr.yaml --stage ine-pro --to iir-pro`
(2026-11-09):

```
iir-pro   337 -> 351 (+14) lost 0
   gained: Hnā́, Hstā́, HyánHtā, Hádʰwā, bʰráHtā, dáHtā, dʰaHtā́, máHtā, paHmā́, swásā, twárštā, ukšā́ …
ira-pro   217 -> 219 (+2)  lost 0
   gained: Hstā́, máHtā
ACCEPT: +16 word(s) across 9 language(s), nothing lost
```

Derived by hand, `*bʰréh₂tēr → brˈaHtā`, which is the headword `bráHtā` up to the accent
spelling (`service._same_form` is true, so the rung is green), and likewise
`*(h₂)uksḗn → uxšˈā` and `*pḱtḗn → pštˈā` — the last two still need the arg-4 form (row 3)
and *pḱ > *fš (row 96) respectively, but the ending is no longer the blocker.
`Hstā́` and `máHtā` are the two Proto-Iranian words the council run moves to exact today.

## Risks

- The law is a nominative rule stated as a phonotactic one. A PII word whose record keeps
  *-ār/-ān word-finally after a long vowel in another case form would lose a match; the
  council run says none does today, and the corpus is the check.
- Only the *loss* is stated; the *-ēn > *-ā vowel change is already in the file
  (`ē > ā`), so the two must stay ordered after it.
- Vocative and oblique forms are unaffected (the environment needs a long vowel before
  the resonant), so `*bʰréh₂tēr`'s oblique stem in a compound is not touched.

## Falsifier

A recorded PII form ending in `-ār#` / `-ān#` after a long vowel, with at least one
registered law firing on it, that the counter counts as exact today. The council run
would list it under `lost`.
