# Roadmap

The target is a family tree fine-grained enough to answer, for any word in any
descendant language, *which PIE etymon does it come from, through which stages,
by which rules* — and to answer "no connection" honestly when there is none.

One rule governs everything: **a derivation counts only when the registered
rules produce the exact attested form.** Approximations are shown as misses, not
as matches. That makes the metric unforgiving and comparable across rule sets,
which is the point: later, competing rule sets (human or model-proposed) can be
scored on the same corpus.

## Where we are (v0.11, 2026-11-08)

- 40 language and proto-language nodes, 266,300 glossary entries, 18.8k ancestor
  links, 475 rules in 26 transitions, 1,739 PIE etyma with descendant trees.
- Rule engine with a segment model (laryngeals, syllabic resonants, labiovelars,
  stress), ordered rules with contexts, tiers and citations.
- Web interface (search, word pages, tree, rules, derivation lab, cognates,
  compare) and a CLI.
- Measured baselines: `docs/COVERAGE.md` (exact derivation per language, with a
  progress box in the README and on `#/coverage`), `docs/EVALUATION.md`
  (accuracy per transition against Wiktionary's own reconstruction pairs), and a
  per-rule usage tally fed by the exact derivations.
- Coverage starts from the PIE etymon **or any recorded ancestor**, but a word
  counts only when at least one registered rule applies and the final form matches
  the attested word character for character.

## The three layers between "phonology" and "the exact word"

### 1. Orthographic finalisation (largest single win) — **started 2026-11-08**

The engine currently stops at a phonemic form: `*pṓds → fˈūt`. English `foot`,
German `Fuß`, Italian `piede` are spelling, and spelling is itself rule-governed
(after the Great Vowel Shift, `ū` is written `oo`; `θ` is written `th`; German
`ū` is `u` + lengthening mark, etc.).

Plan: a new tier `orthographic`, applied after phonology, one file per language
(`data/rules/en__spelling.yaml`, `de__spelling.yaml`, …). Rules are ordinary
pattern rules over segments plus letter classes, so they stay inspectable and
countable. Start with the regular correspondences and add exceptions with a
citation; an exception that needs a lookup is *not* allowed — it becomes a gap.

Status (2026-11-08): the layer exists (`data/spelling/`, `src/pie/spelling.py`,
`pie spell`) with the tier `orthographic` and its own coverage column, and files
for English, German and five historical stages. The orthographic bucket
currently adds 2,193 words across the stages; the historical numbers are
unchanged, as they must be. Persian and Greek still need the script/notation half of this work,
which is a *transliteration* problem, not a spelling one.

Acceptance: exact coverage for English, German, Italian, Persian rises above 50%
on the inherited vocabulary, with no word counted twice and no lookup tables.

### 2. Morphology: the right form of the right word

Wiktionary lemmas are citation forms; the sound laws usually act on a stem.
Latin *pater* (nom. sg.) vs Italian *padre* (< acc. *patrem*), English *foot*
vs *feet*, Persian *pedar* vs *pidar*. Two pieces:

- a **paradigm layer**: each etymon carries the case/number/tense the reflex
  continues (`*ph₂tḗr` nom. → Latin, `*ph₂térm̥` acc. → Italian);
  **current stand-in:** `peo~pal:r_stem_oblique`, a `custom` law switched off
  for every word but the kinship nouns whose record states the oblique stem
  (پدر, مادر, and the Old Persian pitā, mātā they come from), so the model no
  longer shortens a word-final *-ā to fake the same result (2026-11-09);
- **analogical levelling rules**: explicitly registered, because they are real
  history and must be cited, not hidden inside a lookup.

Acceptance: the derivation shows which paradigm cell it is deriving, and the
coverage tool can measure "derivable in *some* cell" separately from
"derivable in the citation form".

### 3. Endings, clusters and laryngeal bookkeeping

Known systematic gaps, each a small rule task with a verifiable example:

- PGmc unstressed endings: `-om → -ą`, `-os → -az`, `-ō → -ô`, `-i → -iz`;
- laryngeals written `H` (unspecified) need the colouring/lengthening rules that
  `h₁ h₂ h₃` already have;
- syllabic resonants before obstruents, and Sievers/Lindeman interactions;
- Iranian: hypocoristic and Middle Persian developments that currently only
  fire in one direction (`peo → pal → fa` has almost no comparable pairs because
  the graph has no direct links for those stages).

## Interface: from demo to instrument

The v1 interface answers "where does this word come from". The next version
turns it into a workbench:

1. **Gap worklist** — every miss from `tools/coverage.py`, sorted by rule that
   would fix the most words ("missing rule candidates"). This is the single most
   valuable screen: it turns the metric into tasks. **Done 2026-11-08** as
   `pie worklist` + `docs/WORKLIST.md` (miss signatures, blamed transitions,
   structural gaps, dead rules, suggested tasks).
2. **Rule experiments** — save a named rule set (base + patch), score it on the
   corpus, and show the delta per transition. The lab already applies a form
   through a chain; it needs a comparison mode and stored variants.
3. **Rule usage heatmap** — the global tally is now in `data/coverage.json`
   and on the coverage page; the next step is a by-transition/by-word matrix and
   a list of rules that fire often but never reach an exact form.
4. **Per-word explanation sheet** — exportable (Markdown/PDF) chain with
   citations, for a single word.

Not to be built: user accounts, database, JS framework. Data files + stdlib
server stay the constraint.

## Sequence

1. `orthographic` tier and English/German spelling rules (biggest coverage win).
2. PGmc endings + laryngeal `H` completion (small, high value per rule).
3. Gap worklist screen + `rules --unused`.
4. Persian chain: Middle Persian → New Persian comparables (needs graph links
   from MacKenzie entries to their NP reflexes).
5. Paradigm layer for Latin/Italian and Germanic.
6. Rule-set experiment harness (A/B against established), then model-proposed
   rule sets.
7. Coverage for the remaining branches (Celtic, Balto-Slavic, Tocharian,
   Armenian, Albanian, Anatolian) — data exists, rules do not.
