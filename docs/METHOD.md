# Method

## Two kinds of evidence

**Ancestry.** Wiktionary records, for most words, exactly which older word they
continue: `{{inh|en|ang|fōt}}`, `{{der|fa|pal|ʾwl}}`, `{{bor|it|ar|...}}`. The
Wiktextract dumps expose these as structured templates, so a word's chain
(`English foot ← Old English fōt ← Proto-West Germanic *fōt ← Proto-Germanic
*fōts`) is stored as data rather than guessed. Borrowings are recorded too, with
`rel: borrow`, because "not connected to PIE" is a finding.

**Rule application.** Separately, the Proto-Indo-European etymon is pushed
through the ordered sound laws of the branch. The engine works on segments, not
strings, so `kʷʰ` is one segment and `r̥` is a syllable; contexts are patterns
over segment classes (`V`, `STOP`, `!V`, `#`), and accent-conditioned laws such
as Verner's see the stress token `ˈ`.

The two are compared but never conflated: a derivation that differs from the
attested form is shown as a different, still informative path.

## What counts as a sound law

A rule is written as `match → replace` with an optional left/right environment,
an order, a tier and a citation. Rules apply in order; each later rule sees the
previous rule's output. Some laws are dissimilations or assimilations defined
over the whole word (Grassmann, Bartholomae, syllabic laryngeals); those are
named transforms in `src/pie/transforms.py` so the rule file stays readable.

Tiers:
- `established` — in the standard literature; used for cited reconstructions.
- `proposed` — a testable hypothesis, not yet verified against the literature.
- `custom` — personal working rules, kept separate from both.

## Coverage is a hard count

`tools/coverage.py` is the project's progress meter, and it is deliberately
unforgiving.  A glossary entry is **reconstructed** only when all of these hold:

1. the entry has a recorded Proto-Indo-European ancestry (or a recorded ancestor
   at a stage in the model);
2. a registered rule chain is applied from the PIE etymon **or from any ancestor
   recorded in that word's inheritance chain** — a chain may start at "the PIE
   root or any root in one of the ancestors";
3. at least one registered rule applies (an unchanged ancestor is not evidence);
4. the final string equals the attested form **character for character**.

Anything else is a miss.  A one-segment difference is reported as a near miss
for diagnosis, never folded into the count.  The denominator is the whole
glossary for that language, so the headline number answers "how much of the
language do we actually explain?", not "how easy is the filtered subset?".

The word pages use the same rule when they choose where a trace starts: the
deepest recorded ancestor that reproduces the attested form exactly — PIE if
possible, Middle English if that is what the rules can actually explain. If no
ancestor does, the page shows the PIE path and states that it differs, which is
the missing-law worklist rather than a claim.

Each successful derivation records which rules applied.  `data/coverage.json`
keeps a per-language and a global tally, so a proposed rule set can be compared
with the established one on the same corpus and the same bar.  Rules that fire
often but never reach an exact form are the first candidates for revision;
words that fail for the same short edit are the first candidates for a new law.

## From a measurement to a band (2026-11-09)

The six bands are not a second measurement.  `src/pie/categories.py` turns the
facts `tools/coverage.py` has already established into one verdict per word,
and the precedence is fixed:

1. a word whose recorded origin is outside the family is **non-PIE**, whether or
   not a rule could reach it;
2. a borrowing from another IE branch is **`ie_loan`** — beside the six, never
   green;
3. no ancestry and no etymology is **unexplained**;
4. a recorded origin that never reaches a modelled PIE stage is **partial**;
5. nothing applied, an unchanged ancestor, a join of pieces, a bound form or a
   stem citation is **partial**, with the reason named — none of those is a law
   derivation;
6. a writing layer (`orthographic`, `script`) that lands on the attested word is
   **full** when every rule it used is the literature's, and **adjusted** when
   one is ours and approved;
7. a per-word pathway is **adjusted** only with approval, otherwise **partial**;
8. an exact law derivation is **full** when every applied rule sits at
   `established`; if any is `proposed` or `custom` it is **partial** with
   *needs approval of our modification*, and **adjusted** only when the word is
   in `data/adjusted.yaml` and its reports exist.

The verdict is a pure function of those facts, so the counter, the coverage
page and any later report cannot disagree about the same word.  A word in the
review backlog is a data question, not a verdict: `tools/coverage.py` measures
what the record says, and the backlog says which records must be re-read before
their measurement is quoted.

## One pathway per lexeme (2026-11-09)

A *pathway* is one lexeme's history: this written word, in this meaning, in this
language, continued from one ancestor, through one chain of stages, by one set of
laws. The rule the model follows is that a lexeme has exactly one such history.
Proposals may compete — that is how the wrong ones are eliminated — but only one
survives into `data/`, and the losers are recorded in `docs/DECISIONS.md` with
the reason they lost.

Two things this does **not** say:

- It does not say a spelling has one history. Homographs are separate lexemes:
  German *Bank* "bench" and *Bank* "money institution" are one shape and two
  words, and the model may — must — give them different ancestries. The glossary
  is keyed by language, headword **and part of speech** for that reason, and an
  ingest that keys by headword alone loses words (the 2026-11-08 decision on
  dropped homographs).
- It does not say the record is complete. A word with no recorded ancestor is
  *unexplained*, not free to be attached to whichever etymon fits best. Absence
  of evidence is not permission to choose the prettier path.

Where two pathways are proposed for the same lexeme, the comparison order is:
(1) does each one produce the attested form exactly under cited rules; (2) which
one has the more reasonable meaning development; (3) which one needs fewer or
better-cited laws. A candidate that loses on (1) is a miss; one that loses on (2)
against a *known* competitor is probably false, and is rejected rather than kept
as an alternative.

## Limits, stated plainly

1. Rules produce phonological forms. Modern English and German spellings are not
   predicted; the derivation stops at a phonemic representation.
2. Inflection is not modelled yet. A PIE root and its suffixed descendant
   (`*pént-e-ti` vs. `*finþaną`) will not converge, which is why the evaluation
   only scores pairs whose shapes are comparable.
3. Not every branch has a rule chain; the registry marks those `provisional`
   and the interface says "no rules yet" instead of inventing arrows.
4. Wiktionary coverage is uneven and occasionally wrong. Cognate sets come from
   its descendant trees and should be spot-checked against a dictionary before
   being treated as authoritative.

## Evaluation

`tools/evaluate.py` pushes every recorded PIE form through a transition and
compares the output with the proto-form Wiktionary records for that stage. It
reports exact matches and mean segmental similarity, and lists the mismatches
with the rules that applied, which is the fastest way to find a missing or
misordered law. This is also the harness for comparing a proposed rule set with
the established one: same pairs, same metric, two rule files.


## The orthographic layer (2026-11-08)

A derivation stops at a phonemic form; the attested word is written. The step
between them is neither a sound change nor a free choice: it is a set of
conventions (which letters a stage uses, whether it writes vowel length, how it
writes /k/ or /θ/), recorded in `data/spelling/<stage>.yaml` with the tier
`orthographic`.

* A spelling rule has the same shape as a law — ordered, contextual, cited,
  with examples that `pie check-rules` verifies — but its examples give a whole
  phonemic form and the written word, because one convention is usually one
  step of a longer mapping.
* `tools/coverage.py` reports `exact` (the laws) and `orthographic` (the
  conventions, on top) as two columns. The historical number never includes the
  second.
* A convention that cannot be decided from the phonemic form is **not** written:
  German noun capitalisation (a property of the sentence), German ⟨v⟩ vs ⟨w⟩
  (the Middle High German symbol covers both /f/ and /w/), English ⟨ea⟩ vs ⟨ee⟩
  (a historical accident of the vowel). Those remain misses.
* Reconstructed stages may have a file too, but only for notation that is
  uniform in the literature (thorn for /θ/). A headword convention that differs
  between authors — the presence of a final ending, for instance — is an
  editorial choice and stays a miss; see `proposals/001`.
