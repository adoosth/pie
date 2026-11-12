# Interface plan

An earlier front end was a static page that let you type a form and watch regex
substitutions happen. That is a demo of a mechanism, not a tool for
the question we actually care about: *where does this word come from, and how is
it connected to words in other branches?*

## Principles

1. **Words first, rules second.** The entry point is a word or a meaning, not a
   rule file. Rules appear as the *explanation* of a connection.
2. **Every claim is attributed.** A form is either attested (with a source) or
   reconstructed; a rule is either established (with a citation) or
   proposed/custom. The interface must never blur that line.
3. **Nothing is asserted that the data cannot show.** If a chain is incomplete
   (no rule file yet), say so instead of drawing a fake arrow.
4. **Fast, dependency-free.** Plain HTML/CSS/JS on a stdlib Python server: clone
   and run. No node_modules, no CDN.

## Screens

**Home.** The one screen that has to explain the tool without a manual: one
sentence of what the model is, a search box, three example cards that land on a
real word page / derivation lab run / comparison, a three-step tutorial
(search → open a word → test the rules), one worked derivation computed live by
the engine (`*ph₂tḗr` → `pedar`, so it can never drift from the rules), and a
single-line coverage status that links to the full report.

**Search / Word page.** One box searches every lexicon at once (word or gloss).
A word page shows, in this fixed order:

1. the form with its IPA, readings, glosses and evidence badge;
2. the **ladder** — the word's oldest recorded ancestor at the top and the word
   at the bottom, one rung per stage of the family. Each rung names the
   language in the **left column**, with the date range it was in use directly
   beneath it (so the rail doubles as a vertical timeline, its spacing
   compressed from those dates); the name's colour says what kind of stage it is
   — green attested, gold reconstructed — and its hover text says it in words,
   with the branch and script (no "attested language" badge in the rung body, so
   the form is the first thing on the right). The word itself and the form the
   dictionaries record stand there, on **one line** — the reconstruction, a small
   `recorded` tag, the record — and when they are the same form it is printed
   once, in a glowing pill with a ✓ disc on its top-right corner. A record
   written in another script matches when the laws produce its recorded
   **reading** (Pahlavi `gwlg` is read *gurg*), and the hover text says which
   reading the laws produced. No "the laws
   reproduce it / differ"
   sentence: the hover text carries that. The recorded part of speech and sense
   sit beneath, so a rung is a word with a meaning and not only a string of
   letters. The laws of a step sit **above the rung they produced**, as a row of
   the timeline between the two forms, each with a switch — reading down the
   rail you meet a form, then the laws it went through, then the form they made. A ladder that can only reach Proto-Indo-European through the word's
   **cognate set** says so, and shows the etymon's own record (English *book*:
   the root `bʰeh₂g-`, "to divide, distribute, allot") instead of an empty
   rung; when the set also records a derived PIE-stage form on the way down
   (`*bʰóh₂g-s ~ *bʰéh₂g-s`, above Proto-Germanic `*bōks`), that form is named
   and the page says why the ladder still starts from the root: picking one
   alternant would be this repo's reconstruction, not a record. On a phone the name and years move above the form rather than
   disappearing. Switching a law off re-derives every rung
   below it **in place** (no page reload or scroll jump; changed rungs pulse)
   and marks what changed; the switch state is in the URL. A stage reached by
   carrying the timeline on has a **change** button under its language name,
   which drops it and everything below it. Every rung except
   the word can also be **edited**: a typed form re-starts the ladder from
   there, is marked as a hypothesis, and lives in the URL too. An edited path
   that lands exactly on the attested word can be **stored as a pathway**
   (`data/pathways.jsonl`) and is listed under the ladder. A pathway stored as
   the word's **own** (`default`) is different: it is applied whenever the page
   opens, states which law never applied to this word and why, names its
   sources, and can be undone with one button (`?pathway=0`) — English *wolf*,
   whose ⟨o⟩ spells /u/ and not the *o that lowers to *ɔ (2026-11-08). There is
   no separate "sound-law derivation" section: the ladder *is* the derivation;
3. ~~**"If the rules ran everywhere"** — the same etymon predicted in every
   modelled language~~ — **dropped 2026-11-08**; the
   word page goes from the ladder straight to the branch. The rows are still
   computed (`pie rebuild`, `/api/rebuild`, the root page's selector);
4. **Cognates**, grouped by branch.

A word that *is* Proto-Indo-European has nothing above it, so it gets no ladder
and no "where it comes from" section. In their place the etymon **opens into its
family**: the same expandable branch every other word page draws, one row per
direct child, each carrying the form that one transition produces and opening
into its own children (2026-11-08). Above it a `reconstruct into` selector lists
the modelled languages (grouped by branch, chains with a gap marked) and shows
the registered laws' output for the chosen one: the derived form in its evidence
colour, the chain stage by stage with the laws that applied, and the form the
cognate set records quoted beside it (`/api/reconstruct`, `service.reconstruct`).

Colour is explained on hover, per form, not by a legend: a green form is
attested, gold is reconstructed in the literature, orange is rebuilt here from
established laws only, red is rebuilt here on thin or contradicted evidence.

A word borrowed from outside the family is drawn as the **same ladder**, not a
separate bar (2026-11-09): the donor language is the top rung, every recorded
stage between it and the word is a rung below it, and the row between two rungs
says how the word travelled — *borrowed from Arabic into Persian*, *derived in
Persian from Middle Persian*. The contact window (633–1100 for Arabic into
Persian) stands under the donor's name and its landmarks fold away beneath the
ladder; it dates the contact, never the word.

The headword itself carries the record's door (2026-11-09): a quotation mark on
the title's top-right corner opens the Wiktionary entry for every word that has
one — matched or not — and a word the laws reproduce exactly wears its ✓ *under*
that mark instead of in place of it. The row of "start from any recorded
ancestor" chips is gone: the ladder starts where the record starts, and the page
says why where the record's rung is not PIE.

**Glossary.** One stage's headwords, painted with their coverage band, with a
category selector. It opens on **PIE words** — everything the record keeps inside
the family — so the Arabic and Turkic loans of a Persian list stay out of the
default view; *all words* shows the whole stage. The counts beside each option
count whole-stage headwords, and a word's own page keeps its band whatever view
the glossary is in (2026-11-09).

**Tree.** The full family tree, one node per registered language, coloured by
branch, with badge counts (glossary size, rules in/out, chain complete or not).
Clicking a node gives the language page: era, script, sample inherited
vocabulary, the rules that produce it, and its children.

**Rules.** Rules grouped by stage transition, in chronological order, each card
carrying its pattern, environment, examples, tier and citation. Filters for
tier and branch; a "what-if" box that applies the whole transition (or a single
rule) to a form typed on the spot, with proposed/custom rules off by default.

**One law.** Every law named anywhere — on a ladder rung, in the branch, in a
lab step, in the coverage table, in the rules index — opens
`#/rule/<src>~<dst>:<id>`: the change and its environment stated in full, the
words the rule file itself cites, the sources by title (linked where a DOI or
URL is known), how often the law applies in exact derivations, its tier explained
in words, and links to the laws before and after it in the same transition
(2026-11-08). The key names the transition because rule ids repeat across
stages.

**Derivation lab.** Type any proto-form, pick a target language (or several),
and get the step-by-step output side by side with the attested reflexes found in
the lexicon. Toggle individual rules to see what changes. This is the view that
will later host rule-set A/B experiments.

**Cognates.** Browse PIE etyma by meaning; each shows all descendant forms
across branches as a matrix, with the intermediate proto-forms that Wiktionary
records. Filter by branch.

**Compare.** Two words from any two languages: do they share an etymon? Show
the common ancestor and both paths, or state plainly that they do not connect.

**About.** Method, sources and licences, per-chain completeness and accuracy,
and how to contribute a rule.

## Visual language

Dark slate background, warm off-white text, one accent colour per branch
(Germanic blue, Italic amber, Greek green, Indo-Iranian rose, others grey).
Reconstructions in italic monospace with a leading asterisk; stress marks and
diacritics rendered as-is. Dense but calm — this is a research tool, not a
landing page.

### Coverage bands (2026-11-09)

The coverage page leads with the six bands the project defined — dark green fully
explained, light green with approved adjustments, yellow partially explained,
red unexplained, dark grey non-PIE, light grey unidentified — and the IE-loan
facet in blue grey beside them.  One stacked bar per language and one for the
corpus; the layer-by-layer table is the evidence behind the bands and folds
away under *How the layers add up*.  Labels, colours and definitions come from
the measurement itself (`definitions` in `data/coverage.json`), so the legend
cannot drift from the counter.  The dark theme lifts the same hues for
contrast; no colour is reused for two bands.

## Data flow

```
data/*.yaml ──► engine (rules, derivations) ──► JSON API ──► static front end
data/lexicon/*.jsonl.gz ─┘
data/cognate_sets/*.jsonl.gz ─┘
```

## Roadmap

* **v1 (now)** — search, word pages, tree, rules, derivation lab, cognates,
  compare, about.
* **v1.1** — rule-set experiments: score a rule chain against held-out cognate
  pairs, diff two rule sets, let an agent propose a rule and see whether it
  improves the score.
* **v1.2 (done, 2026-11-09)** — one page per lexeme, so homographs are
  separate. The route gains `?sense=N` and a spelling that carries more than one
  word lists them on its landing page (`#/word/<lang>/<form>` with no sense);
  the glossary draws one row per word with a numbered subtext; the coverage
  counter measures a word rather than a part of speech, and
  `data/category_index.json.gz` stores a band per sense. The grouping is
  `pie.senses` — one word when the entries state the same ancestry *and* the
  same etymology sentence, so the noun and verb of *bank* are one word and the
  bank of a river is another. The rule is in `docs/PROGRAMME.md` ("One pathway
  per lexeme"): same spelling, different meaning is a different word with its
  own pathway, and the page may not imply otherwise. A link that cannot say
  which sense it means opens the landing page instead of picking one.
* **v2** — morphology: paradigms and inflectional endings as a second layer of
  rules, with words linked to their stems.
* **v2.1** — editing in the browser (write a rule, run it, open a pull request).

## v0.3 — the word view, for readers

The first build of the word page was designed around Latin transliterations and
broke on everything else. Three rules now govern it:

1. **The word is the word.** It is set in its own script, with `dir="auto"` so
   the browser applies bidi per form instead of wrapping it in a left-to-right
   box. Persian and Armenian are set in a script face (Vazirmatn → Noto Naskh),
   never in a slanted monospace: synthetic italics break the joining forms.
2. **Say which spelling was matched.** The sound laws output phonology, so for
   پدر and πατήρ the page compares against the romanisations Wiktionary records
   (*pedar · pidar · padar*, *pătḗr*) and states *exact — the rules reproduce the
   romanised form “pedar”*. "Differs" is reserved for a real mismatch.
3. **Never show a code.** Every row of a cognate table names its language and
   branch, groups by branch (attested languages before reconstructions), shows
   the native form with its romanisation, and marks the row being read.

Motion is CSS-only and supports the reduced-motion preference: the page fades
in, ancestry steps land one after another, derivation arrows drift, rows and
cards respond to hover, a skeleton covers the wait for a derivation, and every
animation is off under `prefers-reduced-motion: reduce`.

`tests/test_web.py` pins all of it: the JSON contract for a word page, the
necessity of `dir="auto"` and `.form.rtl`, the absence of remote resources, a
`node --check` pass over the front end, and a smoke test of the real server.

## v0.4 — rebuilt cognates

> **Dropped from the page 2026-11-08:** the *if the rules ran
> everywhere* table is gone, here and on the cognate page. The engine, the CLI
> and the root page's selector keep the data; the colour model below still
> governs every rebuilt form that is shown.

A word page no longer stops at the cognates the dictionaries happen to record.
From the word's PIE etymon the page runs every registered sound law of every
branch, so the reader can see what each language *would* have if the rules were
complete, in three states:

* **reproduced** — the rebuild equals a form already recorded for that etymon
  (cognate set or the glossary entry attached to it): green when that form is
  attested, gold when it is a literature reconstruction;
* **recorded, rules miss** — the language has a cognate and the rebuild does not
  reach it; both forms are shown and the prediction is red;
* **unattested** — a pure prediction within this dataset, orange when every law
  that produced it is established and red when one is not, always with a
  spelled-out label, because colour alone must never carry the distinction.

The four colours are the same everywhere a form appears (word page, ancestry
chain, cognate table): green **attested**, gold **reconstructed
in the literature** (asterisked), orange **rebuilt here, established laws
only**, red **rebuilt here on thin evidence or against a recorded form**. Any
form in a non-Latin script carries its IPA, or the dictionary's romanisation
where no IPA is recorded. The language name, not the word, is the link.

Persian, English and German are the always-visible cards; the remaining modelled
languages sit in a collapsible table with a link into the derivation lab. Stages
whose chain still lacks a rule file are listed as gaps, and a word whose only
recorded ancestor is a root (`*peh₂-`) carries a warning rather than pretending
the root is a word.

Since 2026-11-08 the ladder's forms are links as well: a rung opens the stage's
word page when its glossary holds the form, and otherwise the *not recorded
here* page, which states that the stage records nothing and carries the form
through the registered laws into its branch. The branch is drawn as a folder
tree — one row per **direct** child (`<details class="branchnode">`), each row
opening into that language's own children — and no link in the word view is
underlined (2026-11-08). (The rule above is
about the cognate table, whose rows are quotations; a ladder is a path to
follow.) Stress is printed the dictionary's way, as an acute
on the vowel (`jráyah`, `dráyah`), while the engine keeps the IPA `ˈ` token.
