# 008 · Is *u > *o before *a (a-umlaut) blocked by a following labial?

- **Status:** open; not implemented (2026-11-08)
- **Stream:** W3/W4 (sound laws, deliberation)
- **Author:** reviewer
- **Reviewers sought:** Ringe & Taylor (2014), EDPG s.v. *wulfa-

## The observation

English *wolf* now reaches its attested form (see the 2026-11-08 decision on a
word's own pathway), but two rungs of its ladder still carry the wrong vowel:
the recorded Proto-West Germanic form is **\*wulf** and the recorded Old English
form is **wulf**, while the engine produces **\*wˈolf** and **wˈolf**, because
`u_lowering` (*u > *o before *a, `data/rules/gem-pro__gmw-pro.yaml`, order 150)
fires on **\*wulfaz → \*wolfaz**.

The rule's own note admits the conditioning is incomplete: "only partly
regular: lowering is blocked by a following nasal or by a geminate in words
such as *wundrą and *fullaz". In *wulfaz* what follows is **\*f**, a labial —
and the recorded West Germanic and Old English forms keep *u*. The literature
states the same blocking: the change is a-umlaut of the Northwest Germanic /
Old High German side, and it does not reach Old English *wulf*, whose *u* is
kept before the labial.

## Prediction

1. Adding a labial block (`env.right` must not pass a labial) should raise the
   exact count at Proto-West Germanic and Old English, and leave Old High
   German — where the umlaut does happen (*wolf*) — unchanged.
2. The rule may belong to the Old High German transition rather than to
   Proto-West Germanic at all; the recorded German *Wolf* shows the lowered
   vowel, the recorded English *wolf* shows /ʊ/ from a *u* that never lowered.

## What was measured (2026-11-08, first ancestor only, per language)

Deriving every eligible word of a stage from its deepest recorded ancestor,
with and without `u_lowering`:

| stage | eligible | exact with the law | exact without it | gains | losses |
|---|---:|---:|---:|---:|---:|
| Proto-West Germanic (`gmw-pro`) | 3,561 | 498 | **569** | 93 | 22 |
| Old English (`ang`) | 6,334 | **373** | 358 | 10 | 25 |
| Old High German (`goh`) | 1,568 | 112 | **113** | 5 | 4 |

Removing the law outright is therefore **not** the fix: it wins 71 in West
Germanic and 1 in Old High German but loses 15 in Old English. A conditioning
that blocks lowering before a labial (and keeps it elsewhere) is the shape the
evidence supports; it must be measured over the full corpus before it is
registered, and the two transitions may end up needing separate rules.

## Why it is not implemented here

The change would move published numbers in three stages and needs the full
`tools/coverage.py` run plus a review of a sample of the 22 losses; the
2026-11-08 session was about the ladder's last law and the law pages. Logged
here with the measurement so the next session starts from evidence, not from a
suspicion.
