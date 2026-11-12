# Formations — a stage building its own word

A language does not only inherit: it joins two words it already has, and it adds
its own suffixes and endings.  The model keeps that apart from inheritance, in
two places — a band for words the record does not analyse, and a control on the
timeline that lets a reader build a form at any rung and watch the laws carry it
down.

## The rule this page exists to defend

A **formation** is not a **derivation**.  A derivation is what registered,
cited sound laws do to a form; a formation is what a speaker does with two
words or a suffix.  A formation may explain *what a word is made of*; it may
never make a word green.  Everywhere below, a formed rung is marked `built`, and
the word's own band is unaffected by it.

## The band (`built`, brown)

`src/pie/categories.py` gives a word the `built` band only when the record does
not analyse it and the stage's own material does, in a fixed order:

1. **A cited suffix on a stored stem** — the word ends in a suffix the stage's
   morphology file registers (`data/morphology/<lang>.yaml`) and what remains is
   a stored headword of that stage.  Persian: 3,921 words.
2. **A split with a curated productive head** — the second element is a head
   listed under `heads:` in `data/compounds/<lang>.yaml` and both pieces are
   stored words.  Persian: 1,998 words.
3. **A dictionary label that licenses exactly its own ending** — when Dehkhoda
   prints «ص نسبی» (relative adjective) the word *is* a -ی formation by the
   dictionary's own account, so its stem need not carry an etymology of its own;
   «مصغر» licenses -ک/‑چه, and no label licenses any other suffix.

`src/pie/compounds.py` does the cutting under deliberately strict tests: exact
characters (Persian آ U+0622 and ا U+0627 are different letters), ZWNJ treated
as spelling, no function words or adverbs as pieces, at least one piece with a
recorded origin, a two-piece cut beating a three-piece one, and **a tie is
refused** — when two cuts pass at the winning size the word is left unclassified
rather than scored.  A word whose record names a borrowing gets no formation at
all: one lexeme has one pathway.

`categories.unexplained_reason` says what kind of unexplained word the rest are
(names, compounds with no allowed cut, huzvarish, affixes, nothing recorded), so
the brown band and the grey one can be read honestly against each other.

## The builder on the timeline

Any rung whose stage has a morphology file offers a `build…` control.  It writes
the question into the address, so an answer can be linked and compared:

```
?build=<stage>:<kind>:<arg>@<base>
```

| kind | arg | what it does |
|---|---|---|
| `join` | the second word | joins two words of that stage with the stage's own linker (Persian: a ZWNJ) |
| `suffix` | a suffix id or form from the morphology file | adds a cited suffix; a suffix backed by a registered formation law is added by that law |
| `ending` | an ending from the morphology file | adds or replaces one of the stage's endings (inflection, not derivation) |

The composed form is spliced in **at the stage it happened**, and the same laws
then carry it down as they carry any form — so the page shows both the
arithmetic of the formation and whether the result lands on the recorded word.
`service.build_options()` sends each rung the small list it may be built with:
the stage's suffixes (with their glosses), its endings, and its joining rule.

Three details that are spelling, not sound:

- a base that arrives as a transliteration is written in the stage's own script
  before it is joined (`dast` + `ی` is دستی, not `dastی`);
- a ZWNJ is treated as spelling when the result is looked up, because the
  dictionary may write the same compound without one;
- a suffix piece is drawn as a **bound morpheme** carrying the registry's gloss,
  never as a word with an unrecorded origin.

## What is refused

- **A general split at any position.**  `tools/coverage.py` measured 27,311
  candidates at 60–70% precision (ابوالفرج read as a compound; فالامس read as
  two words) — not one of them is in a band.
- **Dropping the curated-head rule** for the 15,119 Persian words Dehkhoda calls
  compounds.  It yields 7,309 unique cuts, and a spot check of 25 shows about
  three in four with the boundary shifted by a letter (خرفروش read as خرف +
  روش for خر + فروش).  The number is recorded in `docs/DECISIONS.md` so the
  experiment need not be repeated; the words wait for a reader to bracket the
  pieces.
- **Building as evidence.**  A formed rung is a question asked of the laws, not
  a claim about the word's history: it never changes the band, never enters
  `explained`, and the page says so beside the result.

The full decision history — including the two reviews of the Dehkhoda label —
is in `docs/DECISIONS.md`.
