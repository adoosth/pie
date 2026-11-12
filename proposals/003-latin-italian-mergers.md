# 003 · Which Latin–Italian vowel mergers are laws, and which are stress-conditioned?

- **Status:** partially accepted (2026-11-08): `i > e` withdrawn, `-is > -e`
  and final `-m` loss added
- **Stream:** W3 (sound laws from the literature)
- **Author:** integrator
- **Evidence:** the Italian glossary (22,231 words, 18,635 with an ancestor)

## Claim under test

`data/rules/la__it.yaml` carried two unconditioned mergers, both marked
`established`: `short *i > *e` and `short *u > *o`. The Italian corpus says one
of them is not a law of Italian as written.

## Measurement (full Italian glossary)

| configuration | exact Italian words |
|---|---:|
| HEAD (both mergers unconditional) | 726 |
| `i > e` restricted to an open syllable | 696 |
| `i > e` removed | 843 |
| `u > o` restricted to an open syllable | 262 (from 726) |
| `i > e` removed + final `-m` loss added | 941 |
| … + `-is > -e` added | **1,058** |

Gain 412, loss 80 against HEAD. The 80 lost words are exactly the **stressed
short *i*** cases: *pesce* < piscis, *secco* < siccus, *fermo* < firmus,
*legna* < ligna, *seno* < sinus, *cesta* < cista, *stelo* < stilus.

## What the numbers say

1. **`i > e` is not a general merger.** Italian keeps /i/ in the great majority
   of words (*vino* < vīnum, *spirito* < spiritus, *acido* < acidus, *in*, *il*,
   *lingua*). As written the rule explains *pera* and breaks hundreds more; both
   an open-syllable restriction and no rule at all score better.
2. **`u > o` is real, but not where the theory puts it.** Restricting it to open
   syllables drops the score from 726 to 262 — almost exactly the score with no
   rule at all — so the merger that Italian really shows is the general Latin
   /u/ > /o/ of the learned and popular vocabulary, not a conditioned one.
3. **Two regular endings were simply missing.** Final `-m` (*vīnum* > *vino*)
   and the ending `-is` > `-e` (*canis* > *cane*, *piscis* > *pesce* after the
   loss of final *-s*) are documented Romance developments and together explain
   most of what the withdrawn merger had been borrowing credit for.

## What is registered now

- `final_m_loss`: `m → ∅ / _ #` (Maiden 1995, Weiss 2009).
- `final_is_to_e`: `i → e / _ s #` (Maiden 1995), with the note that it is the
  ending, and that the later final-consonant law removes the *-s*.
- `i_to_e`: **withdrawn**. The change is real but stress-conditioned
  ("Latin short *ĭ* > Ital. *e* in the stressed syllable"), and the engine has
  no stress to test it against.

## Falsifier and next step

A prosody step that assigns Latin stress (penult if heavy, else antepenult) and
lets a rule say "in the stressed syllable" would recover the 80 lost words and
make `ĭ > e` a law again. That is a W3 task; `docs/WORKLIST.md` now carries the
Italian mergers as evidence that stress, not syllable shape, is the missing
condition.

## The falsifier was tested (2026-11-08, same night)

A Latin stress step was built and run against the corpus: the mark is written
before the transition's laws and read away after them (`data/prosody/la.yaml`,
penult if heavy else antepenult; Weiss 2009, Sihler 1995). With it the merger
`ĭ > e / stressed` gains the 68 popular words the corpus wanted (*pesce*,
*cesta*, *pero*, *fermo*, *secco*, *legna*, *messo*, *vetro*) and loses 108 —
all of them **learned words**: *spirito*, *basilico*, *difficile*, *critico*,
*timido*, *minimo*, *singolo*, *biblico*, *tigre*, *Tito*. Italian keeps the
Latin vowel in the Latinisms and merges it in the inherited layer, so the
remaining condition is **lexical stratum**, not stress; no phonological
parameter separates the two sets.

Consequence: the stress step is **not registered**. It is specified, measured
and written down here as the W3 task it will be needed for (a transition whose
laws are stress-conditioned *and* whose stratum is uniform), not merged as dead
machinery. The Italian merger stays out, with its 80 words honestly counted as
misses.
