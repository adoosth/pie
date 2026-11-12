# 002 · Is Middle High German final *-e lost by a sound law?

- **Status:** rejected as a sound law (2026-11-08); the question moves to W5
  (morphology) as an open task
- **Stream:** W4 (new laws)
- **Author:** integrator
- **Reviewer:** the corpus itself (the recorded `gmh→de` pairs) plus the
  phonological-ambiguity test below

## Claim

MHG final *-e is lost in New High German (*tage > Tag*, *herze > Herz*,
*vrouwe > Frau*), so the rule `e → ∅ / C _ #` in `gmh→de` should explain the
largest German miss signature.

## Measurement (full corpus, 17,107 German entries, 8,077 with a recorded ancestor)

| configuration | exact | gain | loss |
|---|---|---|---|
| no rule (HEAD) | 192 | — | — |
| rule at order 200 (after lengthening) | 220 | 35 | 7 |
| rule at order 90 (**before lengthening**) | **227** | **42** | **7** |

The 7 words that stop being explained are `Hesse`, `Elbe`, `heute`, `dritte`,
`neunte`, `Franke` (×2 entries). The 29 distinct words gained include `an`,
`mit`, `vor`, `als`, `dann`, `wann`, `denn`, `gar`, `oben`, `morgen`, `dick`,
`still`, `hart`, `klein`, `dünn`, `Bonn`, `Frank`, `Eifel`, `Ursel`, `Lausitz`.

### The ordering result is real and should be kept

Placed **before** the lengthening rules the apocope explains seven more words
(`gar`, `Oder`, `morgen`, `oben`, `Eifel`, `Ursel`) because it closes the
syllable first: *morgene* → *morgen*, not *mōrgen*. That is also the
chronology (late MHG apocope, 13th–15th c.; NHG open-syllable lengthening,
14th–16th c.). Any future morphological treatment of -e loss must sit at
order 90, not after the vowel rules.

## Why it still cannot be a sound law

1. **One ancestor, two targets.** OHG `Franko` is the recorded ancestor of both
   `Frank` (which loses -e) and `Franke` (which keeps it). No phonological
   environment can separate them: the difference is lexical/morphological
   (name/adjective vs. inhabitant noun), not phonological. The same ambiguity
   appears at `-k` (`Türke` is gained, `Franke` is lost) and at `-tt`
   (`wette` is gained, `dritte` is lost), so consonant-class conditioning cannot
   rescue the rule either.
2. **The recorded pair set contradicts it.** Wiktionary's own `gmh→de` pairs
   are 18, and 10 of them end in -e that survives: *Stelze, Stolle, Darre,
   Klobe, Spähe, Bürge, Dechse, Nixe, Bunge*. The pair set explains none of them
   exactly to begin with; the rule takes its mean segmental similarity down from
   71.4% to 54.5%. Every one of these is a feminine noun of the -e declension.
   The retention is a property of the declension class, not of the sounds around
   it.
3. **The exceptions are systematic, not noise.** Ordinals in -te (`dritte`,
   `neunte`), adverbs (`heute`), river and tribal names (`Elbe`, `Hesse`,
   `Franke`) keep -e; prepositions, particles and uninflected adjectives lose
   it. That is a part-of-speech split.

## Verdict

Rejected as a sound law. The rule would have been the second-largest single
gain in the repository (+42 exact, 192 → 227), and it is **not** taken, because
it would be a morphological change filed as a phonological one — the failure the
one rule forbids. A lexical exception list would reproduce the same 42 words
while naming the words it must not touch, which is a lookup table in disguise.

## What happens instead

W5 (morphology) open task, with this measurement as its evidence: a rule
conditioned on the inflecting class (strong masculine/neuter a-stems and
uninflected adjectival/adverbial forms lose final -e; feminine ō-stems and weak
nouns keep it), evaluated on the same corpus. The engine currently passes no
part of speech or declension class into `derive`; the lexicons do record `pos`,
so the data exists. Until then German's final -e stays a miss, and that miss is
honest.

## Falsifier

A grammar that states the loss with a purely phonological environment (for
example "only after a heavy syllable") and that predicts the *Franke*/*Frank*
split would reopen this as a W4 proposal.
