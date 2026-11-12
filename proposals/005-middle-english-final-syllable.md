# 005 · Middle English: the final syllable, the suffix, and the consonants

- **Status:** partially accepted (2026-11-08): six laws and three spelling
  conventions merged; the two transform repairs are held for a later change
- **Stream:** W3 (sound laws) + W2 (orthography)
- **Author:** descriptive/historical linguist (read-only study, 2026-11-08)
- **Evidence:** the Middle English glossary (8,027 entries, 4,692 with an ancestor)

## Registered

Baseline after proposal 004 and the first spelling additions: **271 exact +
350 orthographic**. With the six laws and the affricate convention:
**387 exact + 406 orthographic**.

| id | law | example | tier |
|---|---|---|---|
| `ae_to_a` | OE short *æ > ME *a | *cræft > *craft* | proposed |
| `c_caron_to_ch` | palatal *ċ > ME *tʃ | *ċild > *tʃild* | proposed |
| `f_to_v` | *f voices between vowels | *ofer > *over* | proposed |
| `ian_to_en` | OE *-ian > ME *-en | *hangian > *hangen* | proposed |
| `u_to_o_open` | short *u > *o in an open syllable | *cuma > *come* | proposed |
| `a_to_o_ng` | *a > *o before *ng | *sang > *song* | proposed |

Orthographic additions in `data/spelling/enm.yaml`: long open *ɔ̄ > o* (the
reflex of OE *ā, *stɔ̄n > ston*), short *æ > a* (*cræft > craft*), and the
affricate *t ʃ > ch* (*tʃild > child*).

## Held for a later change

- **The final-syllable repair.** `final_a_to_e`, `final_o_to_e` and
  `final_u_to_e` use `right: "C? #"`, which also weakens the only vowel of a
  monosyllable (*man > men*, *for > fer*). A transform that restricts the
  weakening to a non-initial final syllable recovers 27 words and loses one
  (*leap*), but it changes shapes the English layer is calibrated on.
- **Degemination** (*catt > cat*, *full > ful*): +20 exact/−1 orthographic in
  Middle English, but it removes a segment the English spelling layer depends
  on.
- **The full block together** gives `enm` +185 exact/+206 orthographic but
  English exact +30 and orthographic −1,093 (1,447→354) until `enm→en` and
  `data/spelling/en.yaml` are re-tuned. The six merged here were chosen because
  English stays flat: exact 585→586, orthographic 1,086→1,077.

## Measured negatives (not registered)

Final *-e* loss: −52/−76. OSL of *o/i/u*: −18/−20/−2. Short *i > e* in an open
syllable: −12/−6. Initial *h* loss: −4/−5. *a > o* before *nd*: +2/−1.
*sc > ʃ*: +5 orthographic, −1. *e > o* before *r*: −4/−2. *i/ī > y* is free
variation (+25/−24) and is not rule-decidable.

## Citations

Luick, *Historische Grammatik der englischen Sprache* (1914), Middle English
vowel system and final syllables; Campbell, *Old English Grammar* (1959),
§§345–352 (final syllables), §§735–738 (class-2 weak verbs); Dobson, *English
Pronunciation 1500–1700* (1968). The locators are the ones the repo already
uses for the same chapters; the new rules are `proposed` until their pages are
checked against the printed grammar.

## Falsifier

A rule that lowers per-transition accuracy (`tools/evaluate.py --from ang --to
enm`) or loses more words than it gains when switched on alone is withdrawn and
this file records the number.
