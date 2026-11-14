# pie — how to work on this repo

One model of the Indo-European family: Proto-Indo-European down to the
attested languages, word by word, with **every step cited and nothing
invented**. `README.md` is for readers. This file is for whoever changes the
model — human or agent — and it is the only file that must be read in full.
Deeper background, when a task needs it: `docs/METHOD.md` (how a derivation is
decided), `docs/RULE_FORMAT.md` (law files), `docs/FORMATIONS.md` (a stage
building its own word), `docs/REVIEW.md` (review protocol), `docs/SOURCES.md`
(licences and citation keys). Everything else under `docs/` is generated or
archived.

## The one rule

> A word is **fully explained** when every step of its path starts from a PIE
> etymon (or from a non-PIE language, for a borrowing), the exact recorded form
> is produced by the engine — by cited sound laws **and** by the constructions
> the record itself states — and every recorded intermediate agrees with what
> the literature records. Otherwise the word is on the worklist, with the
> reason. Nothing is ever bent, guessed or looked up to make a word count.

Two consequences that decide most arguments:

- **A writing is not a sound.** The laws rewrite phonemes, so a form written in
  its own script is refused (`rules.derive_detailed` → `unreadable`); every
  caller hands over the form's *reading* (`service._phonological_form`). A
  reconstruction, by contrast, is carried as itself: only a writing is replaced
  by its reading, and the record's separate transcription is printed beside it
  and never fed to the laws (`service._descends_from`, 2026-11-13).
- **A green word is never greener than the words above it.** Every rung, piece
  and ancestor a page draws is asked for its own band; a weak one makes the word
  partial (`service.unrecorded_ancestry`, `categories.verdict`).

The progress number is counted, never estimated: `tools/coverage.py` measures
the corpus, `tools/evaluate.py` measures each transition.

## Words you need

| word | meaning |
|---|---|
| **rung** | one word on a timeline: a language, its years, the form, its meaning |
| **timeline / ladder** | the rungs above a word, oldest at the top, each joined by the laws that carry the form down |
| **construction** | a word the record says was built from pieces (a compound, a root + suffix) |
| **piece** | one part of a construction; a bound morpheme (suffix, ending) wears no dot and opens its own entry or nothing |
| **transcription / transliteration** | a **transcription** says how a word sounds (`garm`, `rōz`, `vr̥kaʰ`); a **transliteration** says how it is written in Latin letters (`glm`, `lwc`, `v-r-k`), and a **sign transliteration** is the mechanical one, from the script table |
| **band** | the colour of a word's explanation: full / adjusted / partial / unexplained / non-PIE / unidentified |
| **attested / recorded / proposed** | how a form is known: a text or a dictionary records it (in its writing **or** in a transcription of it), the literature states it as a reconstruction (asterisked), or this model guessed it (asterisked, never banded) |
| **worklist** | the honest remainder: every word the chain does not explain, with the reason (`pie worklist`) |

## Run it

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
pie serve                                   # http://127.0.0.1:8100 (stdlib server, no deps)
pie doctor                                  # python, encoding, data report — paste this in a bug report
pie stats                                   # what the corpus holds
pie cache                                   # where derived data is kept, and how big
pie cache --prune                           # drop artefacts an edit or a bump retired
```

The glossary and the word pages are read from `data/lexicon/*.jsonl.gz`
directly; there is **no build step for a data edit** and none may be introduced.
Derived data (parsed glossaries, indexes, compiled laws, measured bands) is
cached under `~/.cache/pie` (`PIE_CACHE_DIR`), keyed on the name, size and mtime
of every input file — so editing a word or a law invalidates exactly what
depends on it. Deleting the cache costs one slow page, nothing else. Bump the
version beside a cached value when its *shape* changes (`data.cached`,
`LEXICON_VERSION`).

## Measure it

A page must feel instant, and a change to speed is a claim until it is measured:

```bash
PYTHONPATH=src python3 - <<'PY'
import time; from pie import service
for label, fn in (("word en/night", lambda: service.word("en", "night")),
                  ("word fa/آب",    lambda: service.word("fa", "آب")),
                  ("glossary pal",  lambda: service.glossary("pal", 400, True, None, None, 1))):
    t = time.time(); fn(); print(label, round(time.time() - t, 2))
PY
```

Report two numbers: a **cold process** (the first call above, which is what a
restart costs) and a **warm** one. Watch for these shapes of slowness, all of
which have bitten us:

- a `stat`/glob of `data/` inside a per-word loop (`available_lexicons` was
  called 17,000 times by one glossary request);
- loading a whole stage when the question is about one spelling
  (`service.lang_index` is for iteration, `service.word_entries` for one word);
- walking `word_index().items()` to answer a question about one stage;
- dressing rows the reader never sees (a 400-row page of 17,000 must dress 400);
- grouping senses or loading a stage per request when the answer is the same for
  every page of it (`_glossary_rows` is a disk artefact, `_senses_for` is cached).

## Where things live

**Data** — the model's only truth, all hand-editable:

- `data/languages.yaml` — the stage registry: id, name, ancestor, era, script,
  kind (`proto` / `attested`). `data/language_varieties.yaml` — registers of a
  stage ("Late Latin").
- `data/rules/<src>__<dst>.yaml` — ordered sound laws per transition (see
  `docs/RULE_FORMAT.md`): each rule needs a `source` key, a `tier`, a `from` and
  the examples it verifies. `data/spelling/<stage>.yaml` — writing conventions,
  applied after the last law, never counted as a law.
- `data/lexicon/<lang>.jsonl.gz` — the glossaries, one JSON object per line
  (`word`, `pos`, `gloss`, `anc` = `[[lang, form, relation], …]`, `phon`,
  `translit` = the recorded spelling, `translit_variants` = its other spellings
  (`spellings_n` says how many), `translit_alt` = alternate readings, `etym`,
  `ref`, `url`, `occurrences`, `source`). Generated by
  `tools/build_lexicons.py` from the dumps — a row added by hand goes into
  `data/lexicon/_supplement/`, which a rebuild merges and never drops.
- `data/morphology/<lang>.yaml` — the stage's cited suffixes/endings (with the
  meaning the construction prints); `data/constructions/` — analyses a record
  states; `data/notation/<lang>.yaml` — the stage's standard alphabet and the
  folds into it; `data/script/<lang>.yaml` — sign tables; `data/readings*.json` —
  readings the sources quote; `data/sources.yaml` — every citation key.
- Measured: `data/coverage.json` (`tools/coverage.py`), `data/review_backlog.yaml`
  (`tools/backlog.py --write`), `data/worklist.json` (`pie worklist --write`),
  `data/adjusted.yaml` + `reports/` (approved adjustments only — never hand-made).

**Code** — `src/pie/`: `phonology.py` (segments), `pattern.py` (rule matching),
`rules.py` + `transforms.py` (the engine), `service.py` (every read model the
API returns), `data.py` (loading + the disk cache), `attestation.py`,
`categories.py` (bands), `script.py` / `translit.py` / `readings.py` (writing vs
reading), `loans.py`, `compounds.py`, `senses.py`, `dubious.py`, `worklist.py`,
`app/server.py` + `app/web/` (stdlib HTTP server and the front end, no bundler).

**Tools** — `tools/` is where anything repeatable belongs, one file per job,
`--help` on each: `build_lexicons.py`, `coverage.py`, `evaluate.py`, `whatif.py`,
`worklist.py`, `backlog.py`, `check_sources.py`, `critic.py`, `unify_notation.py`,
`quick_tests.py`.

## Change recipes

**Add or fix a word.** Edit a row in `data/lexicon/_supplement/<lang>.jsonl`,
or the per-language supplement list, then check it opens: `pie lookup <lang>
<word>`. A row states its senses (`gloss`), its ancestry (`anc`) exactly as the
record writes it, and its `ref` with a locator. Never rewrite a whole glossary
by hand — change the tool and rerun it.

**Add a sound law.** Append to `data/rules/<src>__<dst>.yaml` with `from`, `to`,
`source`, `tier` and `examples`; then
`pie check-rules --strict` (a missing `tier` defaults to `established` and
silently promotes a hypothesis — `--strict` refuses it) and
`tools/whatif.py --to <lang> --rules <file>` for gain **and** loss against the
corpus. A law that helps one transition and hurts the corpus is a finding, not a
win.

**Add a suffix or ending.** A row in `data/morphology/<lang>.yaml` with the
gloss a construction will print; the word page then lets a reader build with it
and `service.construction_path` will use it to explain a registered formation.

**Add a spelling convention.** `data/spelling/<stage>.yaml`, tier
`orthographic`, examples that give a whole phonemic form and the written word
(`spelling.check` applies the whole file). It never enters `data/rules/` and its
count is never added to `exact`.

**State a construction.** `data/construction/<lang>.yaml`: the pieces, the
formation (`compound`, `derivation`, `combining`), and the record's sentence.
Only a construction the record states may make a word green; one this model
composes for itself needs the approval route (`data/adjusted.yaml`).

**Re-measure.** `PYTHONPATH=src python3 tools/evaluate.py --all --markdown` (per transition) and
`tools/coverage.py --docs` (corpus, README block, `coverage.svg`). A sampled
run (`--limit`, `--langs`) writes elsewhere and is never published as a number.
Commit the regenerated reports with the change; never accept a drop in exact
coverage without saying why.

## What a word page must keep true

These are the invariants a UI change must not break. Each has a test that names
it; if you change one, change its test in the same commit.

1. **Title, not pills.** Language and years in the left margin, the category by
   the meaning, band + record as one italic line.
2. **A timeline reads, it does not spell.** The leftmost text of a rung is a
   romanisation; a script follows it with the record's reading and the mechanical
   sign layer (`𐎺𐎼𐎣 · vr̥kaʰ · v-r-k`). IPA is optional, on the word's own page
   only, never on a rung. The pencil seeds that romanisation and the stage below
   continues from it — a form in its own script is never edited and never an
   input to the next step.
3. **Every rung is an entry of its stage** — or it says *no entry for this word*
   in dark red, upright, with no ✓. A form the laws produce is not an entry.
4. **No ✓ without the record's own reading.** The laws' form must *be* the
   reading; a near-miss is shown as a question (`unverified`, ⚠), never counted.
5. **One romanisation per stage.** `data/notation/<lang>.yaml` holds the standard
   alphabet; headwords and the ancestors a record names are folded into it at
   load (`pie notation <lang>` reports anything outside it).
6. **A construction is drawn once**, as one tree above the form it builds; its
   pieces are word-sized, carry their own meaning, and a bound morpheme opens its
   own entry or nothing — never a letter's page.
7. **A word met twice is one word.** Search, the glossary, the construction menu
   and the API agree on language + word + sense.
8. **Evidence colour is the contract**: green/gold mark recorded forms, a
   rebuilt form is never green, and there is no colour key on the page — every
   form carries its own tooltip.
9. **A timeline ends where the record ends.** A ladder whose top rung is not
   Proto-Indo-European carries on upward to a `???` — nothing recorded names
   what came before — and the family below a word is drawn on the timeline
   only, never as a second tree under the page (2026-11-14).

## Bands and attestation

Six bands, one verdict (`categories.py`) shared by the word page, the glossary
row and the counter: `full`, `adjusted` (the same path, with a recorded step
that differs or an approved change of ours), `partial`, `unexplained`,
`non_pie`, `unidentified`. Two facets sit beside them and are never green:
`ie_loan` and `built` (a formation from the language's own words).

Three things are **not** a hole in a timeline: a root (a relation, not a step), a
bound morpheme (grammar, not a word), a borrowing (not inheritance) — and a stage
this model holds no glossary for at all is *our* gap, named as such.

Attestation is separate from the band: `attested` (a text or a dictionary writes
it in the language's own script), `recorded` (a reconstruction the literature
proposes, printed with an asterisk), `proposed` (our own guess, also
asterisked). A form no glossary of its stage spells is *non-existent* and says so.

## Tests — a budget, not a ceremony

**One minute, and only the tests your change touches.** The repo is in
development; a change is proven by the handful of tests that pin what it
changed, not by the whole suite.

```bash
python3 tools/quick_tests.py            # curated fast set, hard 60 s budget
python3 tools/quick_tests.py --list     # what it runs and why
PYTHONPATH=src python3 -m unittest tests.test_web tests.test_notation   # by name
node tests/test_ui_render.js            # only when app.js / style.css changed
```

The full suite (`python3 -m unittest discover -s tests`, ~1,000 tests) is for a
**release** or for a run that is asked for by name — never for an ordinary
edit (2026-11-13). Add a test when a rule can silently regress; do not add tests for a
sentence on a page. Keep `tests/test_syntax.py` green: the repo must parse on
Python 3.10 (the Windows machine runs 3.11, this box 3.14).

## Voice of the repo

The repository speaks for itself. Nothing in it — code, comments, docstrings,
docs, tests, proposals, commit messages — names a person, an operator, a shift,
or an internal organisation: no "admin", no "night shift"/"night", no
"super agent"/"sub agent", no "integrator", and no private workspace paths.
Provenance is a **bare date** — `(2026-11-13)` — never a date plus a person.
Who asked for what, and when, is recorded outside the repository; the repository
keeps the decision, the date and the reason.

## Commits and reports

- One artefact per commit — a rule, a spelling row, a supplement file. Never
  reformat unrelated files; a bug fixed on the way is named in the message and
  stays inside the same artefact.
- Commit as the repo's own identity (already configured: `Ali Doosthosseini
  <adoosth@gwdg.de>`); never add an author or a co-author trailer.
- Say what changed and **why**, with the numbers that moved (coverage, timings).
  A rule **applies**, it never "fires"; nothing published names who commissioned
  the work or how many hours it took.
- Fix what you find — inside the change you are already
  making, with a `docs/DECISIONS.md` line if a reader could notice it.

## Working with delegated agents

The repo is small enough to split by area; each agent gets a **write set** and a
**measurement**, and reports back in numbers.

- Give an agent one area: `src/` (engine + service), `app/web/` (front end),
  `data/` (a corpus question), `tools/`, or one documentation file. Two agents
  never edit the same file in the same round.
- Every agent brief names: the files it may edit, the behaviour that must stay
  (the invariants above), the tests it may run (the budget above), and the
  measurement it must report before and after.
- A critic agent (`docs/CRITIC.md`) reads pages and reports — it never edits
  `data/` or `src/`. A worklist agent proposes the next task from
  `pie worklist` and says what "done" would mean.
- The reviewer of the batch reviews the diff, re-runs the numbers, and
  decides what lands. Nothing lands on an agent's word alone.

## Open fronts

Where the model is thin, in the order the worklist ranks them: law coverage for
the transitions with the most misses (`docs/EVALUATION.md`), the stages with a
large `unexplained` share (Middle Persian and Persian above all), the
reconstruction pages that still start at a form rather than at an entry, and the
front-end speed budget. `pie worklist` is the live list; `docs/COVERAGE.md` is
the published measurement.
