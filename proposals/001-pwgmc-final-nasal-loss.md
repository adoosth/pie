# 001 · Is Proto-West-Germanic final *-ą lost by a sound law?

- **Status:** rejected (2026-11-08)
- **Stream:** W4 (new laws)
- **Author:** integrator
- **Reviewer:** methods skeptic (independent agents, 2026-11-08)

## Claim

PGmc final *-ą of the neuter a-stems (*tiną, *þingą, *wurdą) has no reflex in
Proto-West-Germanic (*tin, *þing, *wurd); a rule `ą → ∅ / C _ #` in
`gem-pro→gmw-pro` would reproduce 556 sampled words at once.

## Why it looked attractive

A full-corpus audit put `−ą` at the top of the Proto-West-Germanic miss
signatures. The glossary contains **no** entry ending in `-ą`, so the rule
cannot break an existing match, and the gain would be the largest single rule in
the repo.

## The objection that killed it

1. **It is a change in the same transition for Gothic too.** Gothic has *waurd*
   with no final vowel, and Old English, Old Saxon, Old High German and Old Norse
   agree. A change that all the daughters share is Common Germanic, not a
   Proto-West-Germanic innovation; filing it under `gem-pro→gmw-pro` would make
   the transition claim a change it does not own.
2. **The PWGmc "targets" are headwords, not running words.** Wiktionary's
   Proto-West-Germanic entries cite stems without inflectional endings (e.g.
   `ail` for 'fire', whose PGmc source is *ailą). A rule that deletes the ending
   would be reproducing a **headword convention**, and counting it as a sound
   law would inflate the historical number — exactly the failure the one rule
   forbids.
3. **No independent evidence.** The rule's only examples are the same glossary
   entries it is scored against.

## What happens instead

Headword and notation conventions belong to the orthographic/notation layer
(`data/spelling/<stage>.yaml`), which is counted in its own bucket and can never
contribute to the historical number. If the convergence is real, the honest
place to model it is a **Common Germanic** transition (`gem-pro → gem-pro`
successor stage) with its own evaluation pairs — a W1/W3 task.

## Falsifier

A grammar that states, with a locator, that *-ą survives into Proto-West-Germanic
and is lost *there* (rather than before the split) would reopen this.

## Re-opened and still blocked (2026-11-08)

A **two-step** version was built and measured: `ą → a / _ #` (denasalisation)
followed by the existing `final_a_loss` (*tina > tin*). It does not delete the
ending directly, and it takes Proto-West-Germanic from **566 to 1,568 exact
words** (+1,002), with Old English +22, Middle English +8 and English unchanged.

It is still **not registered**:

1. The change is shared by Gothic, Old Norse, Old English, Old Saxon and Old
   High German, so it belongs to Common Germanic, not to the PWGmc transition.
   The model has no Common Germanic node to put it in.
2. The PWGmc targets are headwords; the absence of *-ą* in them is a headword
   convention, so scoring the rule against them would inflate the historical
   number with notation.

The honest route is a **Common Germanic stage** (W1/W3) with its own evaluation
pairs, then this rule can be registered where it belongs. The measured gain is
kept here so the task is not lost: 1,002 exact words are waiting for that node.
