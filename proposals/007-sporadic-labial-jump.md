# 007 · Is PIE *kʷ > PGmc *p a sound law? (wolf, five, four)

- **Status:** open; implemented only for the one case the literature states
  explicitly (the wolf), as a `proposed` rule `lkw_to_lp` (2026-11-08)
- **Stream:** W4 (new laws)
- **Author:** reviewer
- **Reviewer:** EDPG and Wiktionary's own *wulfaz / *fimf / *fedwōr entries

## Claim

Three recorded Proto-Germanic words have *f where regular Grimm's law predicts
*hw: *wulfaz 'wolf', *fimf 'five', *fedwōr 'four'. If a single rule
`kʷ → p` in the neighbourhood of a labial were a sound law, one rule would
explain all three (Grimm's *p > *f then applies unchanged).

## What the sources actually say

- **wolf.** EDPG s.v. *wulfa- reconstructs *wĺ̥kʷos > *wúlkʷos > *wúlpos >
  *wulfaz and calls the change "a kind of assimilation at a distance"
  (*artikulatorischer Sprung*). Wiktionary's *wulfaz entry adds the decisive
  sentence: if *wúlkʷos had not changed to *wúlpos, the form would look like
  **wulhwaz** in Proto-Germanic. The change is compared with *pénkʷe > *pémpe,
  not equated with it.
- **five.** Wiktionary's *fimf entry calls the second *p "an irregular
  consonant change" of *pénkʷe, "perhaps influenced by the initial *p"; the
  expected form would have been **finhw** (EDPG s.v. *fimfe).
- **four.** Wiktionary's *fedwōr entry calls *petwṓr an "irregular consonant
  change" and says "the expected outcome would have been **hwedwōr" (EDPG
  s.v. *fedwar-), probably under the influence of *fimf.

None of the three is presented as a regular law, and the wording is
lexically specific in all three. That is why `lkw_to_lp` is `proposed` and why
it states only the environment the cited case has: *kʷ after *l.

## Measurement (2026-11-08)

| form | recorded PGmc | derived (HEAD) | derived (with `lkw_to_lp`) |
|---|---|---|---|
| *wĺ̥kʷos | *wulfaz | wˈulhwaz | **wˈulfaz** |
| *pénkʷe | *fimf | fˈenhwe | fˈenhwe |
| *kʷetwóres | *fedwōr | hwedwˈarez | hwedwˈarez |

The 1,351 recorded `ine-pro→gem-pro` pairs are unchanged by the rule (0 pairs
changed, 87 exact before and after): no other pair contains *-lkʷ-. The full
corpus also holds at 3,644 exact.

## What would settle five and four

A rule that captures the shared trigger would have to say which labial counts
and at what distance, and no source states that. The two candidates that were
tried and rejected:

- "any labial elsewhere in the word" — changes 11 recorded pairs, including
  *kʷélpeti hwˈelfedi → fˈelfedi against the recorded *hwelbaną and *kʷólpo-
  hwˈalfa → fˈalfa against *hwalbą, i.e. it breaks words whose *kʷ is
  word-initial.
- "*kʷ after a resonant before a vowel, with a labial elsewhere" — leaves the
  five and four cases unexplained anyway (their *kʷ is not followed by the
  right vowel / is followed by *t) and wrongly changes *pŕ̥kʷ-eh₂ to furfō
  against the recorded *furhō.

Until a source states the conditioning, they stay listed as misses with this
note, rather than being bent into shape.
