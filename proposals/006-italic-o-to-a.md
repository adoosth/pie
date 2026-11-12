# 006 · Is PIE *o > Proto-Italic *a a law?

- **Status:** withdrawn (2026-11-08): the rule is removed from
  `data/rules/ine-pro__itc-pro.yaml`
- **Stream:** W3 (sound laws from the literature)
- **Author:** integrator, sceptic review
- **Evidence:** 335 comparable recorded PIE → Proto-Italic pairs

## Claim under test

`data/rules/ine-pro__itc-pro.yaml` carried `o_to_a_medial` as `established`:
"short *o becomes *a when it stands after a consonant in a non-initial syllable",
with the example *gʷónos > *gʷónas*.

## Measurement

| configuration | exact Proto-Italic words |
|---|---:|
| HEAD | 43 / 335 |
| rule removed | **76 / 335** |

The rule never pays for itself. Every one of the 135 recorded pairs that carries
a PIE *o has *o in the Proto-Italic target as well, with the sole exceptions of
*soks-ó-m* > *saksom*, *bʰors-* > *fars* and *ksow-ó-s* > *(k)sawos*, which do
show *a*.

## What the numbers say

The change is real in Latin (*saxum*, *trabs*, *farcīre*) but it is not
conditioned by "medial syllable", and with 3 supporting words against 132
counter-examples no segmental environment can be stated from this corpus. The
honest options were to withdraw it or to invent an environment; the rule is
withdrawn.

## What replaces it

The same transition now carries the laws the corpus does support: the lengthening
of a vowel before a lost laryngeal (*-eh₂- > *-ā-*, *-eh₁- > *-ē-*), syllabic
*l̥ > *ol*, word-initial *h₂ before a consonant > *a*, progressive colouring, and
the positional split of the aspirates (*bʰ *dʰ *gʰ > *f *ð *ɣ word-initially,
*β *ð *ɣ medially). Together with the removal of this rule they take the
transition from 43 to 140 exact words with no rule left unsupported.

## Kept for the record

If a future source states the conditioning (Weiss 2009 § 42 is cited for the
change but gives no segmental environment that the corpus confirms), the rule
should be re-tested with `tools/evaluate.py --from ine-pro --to itc-pro` before
it is registered again.
