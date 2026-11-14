# 009 · Should Old Persian write *w as v?

- **Status:** open — not implemented
- **Stream:** W4 (new laws) / W6 (notation)
- **Author:** reviewer
- **Reviewer:** Kent (1953), Skjærvø (2009), the Old Persian glossary

## Claim

Proto-Iranian *w- is written 𐎺 and transcribed *v-* in Old Persian grammars
(OP 𐎺𐎼𐎣 *varka-* 'wolf', 𐎺𐎠𐏃𐎼 *vāhara-* 'spring', 𐎺𐏁𐎴 *vašna-*
'favour'). The engine keeps *w-* through the Old Persian rung, so the ladder for
گرگ reads `peo wˈarkah` where the sources write *varka-*.

## Measurement (2026-11-08)

Of the 216 Old Persian entries whose ancestry gives a form to derive from, only
two have a romanisation that is a reading rather than a sign-by-sign
transliteration:

| recorded | derived (HEAD) | ancestor |
|---|---|---|
| `vāhara` | `wˈāhar` | PIr *wósr̥ |
| `vašna` | `waθ` | PIr *weḱ |

No recorded Old Persian entry in the corpus begins with *w-*. The rest of the
glossary is cuneiform or syllabic (`v-r-k-a-n`), which coverage does not compare
against a derived form at all.

## Why it was not simply added

A *w > OP v* rule cannot stand alone. It changes the input of the next
transition, and the Old Persian *v-* that becomes Middle Persian *w-* — OP
*vāta-* 'wind' > MP *wād* — is not modelled; today the wind gets its *w* from
the Old Persian stage and derives exactly. Adding *v* without *v- > MP w-* turns
*wād* into *vād*. And a rule in the sound-law set would claim a **change** where
the sources describe a **spelling**: Old Persian's 𐎺 is one sign for the
labiovelar, and whether the phoneme was [w] or [v] is a separate question.

## What would close it

Either (a) an `orthographic` rule for Old Persian in a spelling layer (the tier
exists and is never counted in a historical number), or (b) a proposal for
*v- > MP w-* measured across the Old Persian→Middle Persian pairs — which the
corpus cannot do yet, because the Middle Persian glossary still carries no
ancestry links (`pal` identified: 0 of 612).

## Predicted gain

2 rungs closer at the Old Persian stage (the two entries above), and the wolf's
Persian ladder would print *varka-* where the sources do. No change to any
published coverage number either way: Old Persian targets are compared in
cuneiform.

## Measurement 2026-11-08 (option b, now that the chain exists)

The blocker named above is gone: Middle Persian now carries ancestry links
(گربه, گرگ, دیو …), so *v- > MP w-* can be measured. Both laws were written
(`ira-pro~peo:w_to_v`, `peo~pal:v_to_w`), run, and removed again:

| | without the pair | with the pair |
|---|---|---|
| Persian ladders that end exact | **51** | 50 |
| Old Persian rungs matching their record | **17** | 12 |
| Middle Persian rungs matching their record | **8** | 7 |

The one gain is the word in question (دیو ends exact, OP rung
𐎭𐎡𐎺 *daivaʰ* matches); the losses are روباه (which took its *w* from the
*b > w* path), کبوتر, جو and کبود. **The pair is net negative, so it stays
unimplemented at the sound-law level.**

What the pages do instead: a rung whose form and record differ only in the
letter (laws *daiwˈah*, record *daivaʰ*) now carries `notation: "v/w"` and says
in words that the source transcribes one sign, the laws write the other
consonant — explained on the page, never counted as a match. The remaining
honest fix is still the spelling layer (a Copy), not a sound law.

Also settled here: a script headword no longer stops the ladder. `_phonological_form()`
takes the reading the glossaries record for Middle Persian 𐫅𐫏𐫇 (*dēw*) and
Old Persian 𐎭𐎡𐎺 (*daivaʰ*), so both climb the full chain, and an entry may
state the form outright with a `phon` field when its headword is a
transliteration rather than a reading.
