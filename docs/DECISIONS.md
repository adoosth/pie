## 2026-11-13 — a rung must be an entry, and a composition takes its grade

**What.** `iir-pro/HwáHyati` was dark green with a PIE rung that printed "no
entry for this word": its record names *h₁wéh₂-ye-ti*, the laws reproduce the
daughter from it exactly, and the PIE glossary had no such entry. The reader
asked for the band to be *partial* until that entry exists, for the entry to be
made from the record's own suffix formation, and for Proto-Indo-Iranian to be
described correctly in the same way (admin, 2026-11-13).

**The clause the verdict never measured.** "Every segment starts from a PIE
etymon, the exact form is produced by the laws *or* a registered construction,
and everything matches the record": the first two clauses were measured, the
third was not. `service.unrecorded_ancestry` now reads the record's ancestry —
through `_ancestry_triples`, with `_lemma_entry` so a hyphen, the engine's stress
token, a stressless spelling and case are notation — and returns one row per
form no entry of its stage heads. `categories.verdict` refuses **every** green
route (laws, construction, writing layer) while that list is non-empty, and the
page and the counter read the same call, so a band cannot disagree with a rung.
Three kinds of row are not holes: a root or a bound spelling (a relation, a
morpheme), a borrowing (not inheritance), and a stage with no glossary at all
(Proto-Italic, Proto-Hellenic — a gap of ours, named as such). A row the
extraction cut mid-etymology ("+") is punctuation, not a word.

**The walk does not stop at the daughter's own record.** A rung that *is* an
entry has a timeline of its own and the page draws it (`ownStep`), so a word
*that* entry names and its glossary lacks is the same hole one stage higher:
Sanskrit तृण inherits Proto-Indo-Iranian *tŕ̥nam, which is an entry, whose own
record names PIE *tŕ̥nom, which is not. Depth is bounded (3) and a form is
visited once. Filling the rungs filled the bands: iir-pro full 347 → 240.

**The entry** (`data/lexicon/_supplement/ine-pro.jsonl.gz`, 40 rows).
*h₁wéh₂yeti, verb, "to become empty, die out" — the sense is quoted from the
Lithuanian *pavojus* record, which glosses *\*(h₁)wéh₂-ye-ti* so; the entry
quotes that record, Greek ἐάω and Proto-Indo-Iranian *HwáHyati, and states the
suffix formation those sentences give: *h₁weh₂- "to be/become empty" + *-yeti
"thematic present, 3rd singular". A morphology row `ye` in
`data/morphology/ine-pro.yaml` registers `-ye-` + `-ti` (Fortson, Sihler), and
`_bound_forms` now registers a suffix's form *with its ending* (`-yeti`, `-nós`,
`-m`), because that is the piece a record writes.

**A composition takes the grade its suffix asks for.** A record cites the root
under its e-grade and writes the word in the grade the suffix makes
("*bʰn̥dʰtós, from *bʰendʰ- + *-tós*"). Read as a plain concatenation the row
spelled *bʰendʰtós*, so 16 of the first 66 filed entries said their own
construction "does not spell the word". `construction_path` now retries with
`_formation_grade` — only for a grade the morphology table documents, and only
when the plain join has failed — and `_grade_stem` learned the diphthong rule
(a diphthong's zero grade is its second element: *leykʷ- → *likʷ-*, *wekʷ-* →
*ukʷ-*, *dewk-* → *duk-*, *peys-* → *pis-*; and a root-initial glide vocalises:
*wekʷ- → *ukʷ-*). 50 of the 66 now compose exactly; the 16 that do not name a
suffix whose grade the table does not state (*-is, *-us, *-ós, *-wós, *-trom)
and say so.

**The tool** (`tools/add_pie_ancestors.py`, new, idempotent). For each hole in a
daughter's record: the record's own `… from *A (“x”) + *B (y)` clause *for that
form*, every piece a PIE word or a registered morpheme, the consonant skeletons
equal (vowels, laryngeals, glides and stress set aside), no hedged sentence
(`uncertain|possibly|perhaps|…`), and the entry's own construction must compose
exactly. The gloss stays empty unless the record glosses the form; the citation
is the sentence and the page it came from. Run for Proto-Indo-Iranian it filed
68 entries and refused 259, each with its reason (the record states no
formation; the clause is about another form; the record hedges it; the model
cannot compose the suffix's grade yet). `--check` now reports 0.

**Measured.** iir-pro (799 entries): full 347 → 187 with the guard alone, 240
after the entries and the grade rule; partial 386 → 502; every demotion carries
a real hole, and no word moved up that was not green before. Corpus-wide
full+adjusted 1,238 → 906: sa 330 → 210, la 89 → 32, grc 128 → 72, en 184 → 175.
Those are the same class — a Latin word whose record names PIE *twé or *kʷóm,
forms the PIE glossary does not hold — and the same tool fills them
(`--lang la` finds 8, `--lang gem-pro` 26, 59 in all the affected stages); they
are the worklist, not a regression to hide.

**Not measured, and named as the next gap.** ~100-280 words per language have
an *existing* ancestor whose stored construction does not compose its form even
with the documented grades (e.g. iir-pro *éti < *ís + *-ti). The fix is more
morphology documentation, not a colour; a demotion there would be right but is a
different measurement.

**Tests.** `tests/test_build.IncompleteTimeline` (the hole, the recursive hole,
the "+" row, the band/rung agreement across the stage) and
`tests/test_build.GradedComposition` (zero and o grade, diphthongs, an
undocumented suffix still getting no grade, the PIE entry and its `*-yeti`
construction); `tests/test_categories.MissingRungTest` (a hole outranks every
green route and cannot be bought back by a construction).

## 2026-11-13 — a registered construction may carry a word to "fully explained"

**What.** The reader looked at `gem-pro/andaswarō`, saw that nothing was
inconsistent — *anda- "facing" and *swarō "oath" both climb to Proto-Indo-
European, and the record says the word is their sum — and asked that its band
say so (admin, 2026-11-13): *"andaswarō should be fully explained, because all
its segments start from PIE or a non-PIE language, and the exact word is
produced by sound laws in the engine, as well as valid registered constructions
of each stage."* The only difference from the rule of 2026-11-09 is that a
**registered construction** is allowed in a green path; everything else — a
recorded origin, an exact form, every recorded step agreeing, nothing invented —
stands unchanged.

**The rule, in one place.** Every segment starts from a PIE etymon or from a
non-PIE language; the exact recorded form is produced by the engine, by cited
laws **or** by the record's own registered constructions of each stage; and the
result matches what the literature records. Same conditions but the result is
not exactly what the literature records → *fully explained, with adjustments*
(light green). It is restated at the top of "Bands, colours and review" in
`AGENTS.md`, and the paragraphs that said it in three places now point there.

**How a construction is measured** (`service.construction_path`). The row is the
one `_own_construction` reads — `built_as` from the record and the reduplication
sentences — so a word the record does not state as a construction has none, and
the surface analysis of a word whose history is an inheritance (English
*blackbird*, "equivalent to black + bird") is still refused. Then:

1. **the pieces spell the headword.** Their recorded spellings, in order, joined
   by the stage's registered linker where its morphology has one, must equal the
   word; the two ways of writing stress (a dictionary's acute, the engine's `ˈ`)
   are one word, and nothing else is forgiven. A one-piece `derivation` names a
   base, not a spelling, so it cannot carry a form — *aiganaz stays as it was.
2. **every piece has somewhere to stand.** It is the PIE etymon itself, a word
   whose own record *names* a PIE etymon (*anda- says "from pre-Germanic
   *h₂entó- … from the PIE root noun *h₂énts"*; *swarō says *swer-*), a non-PIE
   source, or a morpheme the stage's own morphology table registers (`*-s` is
   the athematic nominative singular). A dictionary affix is a word with a
   history of its own and is judged by that history: *astro-* names Greek and
   nothing above it, so *astronaut* stays partial. A morpheme the table does not
   register is not explained either: *growth* = *grow* + *-th* passes because
   *-th* really is from PIE *-iteh₂, not because it ends in a hyphen.
3. **the record's row is the one that counts.** A construction this model
   composes itself never exists here; if one ever does, it is held to the
   approval rule (`data/adjusted.yaml`), exactly like a law of our own.

**Where it lands.** `categories.verdict` takes one new fact, `construction`,
and reaches it only when nothing else did (`matched_by` is `None` or `joined`):
a law always wins, and `identity`/`bound` never turn green this way. Exact
against the record is dark green; a recorded intermediate that disagrees is
light green, with the stage named (`step_row`). Both the page (`_category_of`)
and the counter (`tools/coverage.py`) call the same helper, so a colour cannot
differ between the glossary and the word's own page; the counter also reports
how much of the green rests on a construction (`constructed`).

**What moved.** Read over the whole corpus, 917 entries are carried by a
construction that spells them from explained pieces — 270 Persian, 223 English,
108 Proto-West-Germanic, 76 Sanskrit, 69 Proto-Germanic, 39 Proto-Celtic, 35
Gothic, 29 Proto-Indo-European. Of those, **573 are attested words in the six
bands**, and the bands rise from **full 518 to 1,091 and explained 665 to
1,238** (English 181, Persian 256, Sanskrit 277, Gothic 39, German 4). The
counter reports the figure beside them (`constructed`: 573 — every one of
English's 181 full words). Nothing else moves: a word whose construction
states a piece with no recorded origin, or which does not spell the headword,
keeps its band and now says why (`construction of non- + sense, but non- has no
recorded origin`; `construction of Ytterby + -ium does not spell the word`).
`gem-pro/andaswarō` reads **fully explained — construction of *anda- +
*swarō**. Two notation faults were found while reading those reasons and fixed
in the same pass: a capital's place in a proper name and the Persian tatweel
that writes a compound's seam.

**Tests.** `tests/test_build.ConstructionCarries`: *andaswarō is carried by its
construction and its page says so; *nonsense* is not (non- has no PIE origin);
*blackbird* has no construction at all (its history is inheritance); *aiganaz's
one-piece derivation cannot spell a form; the hyphen a row omits is restored
before the lookup (*-th*); and the verdict never greens a lawless word without
a construction, never lets one override a law, names the stage when a recorded
step disagrees, and holds our own composition to approval.

**Docs.** `AGENTS.md` now opens with what the project is, states "fully
explained" once, and lists the two shapes of a green path; the repeated
statements of the same rule in Ground rules and in the bands section are gone.

## 2026-11-12 — reduplication is a formation, and a line begins at its oldest mark

**What.** `ine-pro/h₂eh₂óyḱe` carried the sentence "Reduplicated stative of the
root *h₂eyḱ-" and no step above the word: reduplication existed in the corpus
only as prose. The reader asked whether it is part of the morphology and, if
not, for it to be researched, added, and given its constructions (admin,
2026-11-12). In the same pass two older faults surfaced — a rail that hung
over the top word of a timeline, and a homonym chosen by index order.

1. **Reduplication is a formation, not a sound law.** It copies the root's
   onset and asks the root for a grade, exactly as an ablaut type does, so it
   belongs in `data/morphology/ine-pro.yaml` beside `grades:` rather than in
   the rules. Four types are stated there, each with its syllable, its grade,
   its ending, its outcomes and its sources (Fortson, Sihler, Beekes, LIV):
   the **perfect/stative** (`Ce-`, o-grade, `-e`: *h₂e-h₂óyḱ-e, *de-dórḱ-e),
   the **i-reduplicated present** (`Ci-`, zero grade: *pí-ph₃-e-ti), the
   **e-reduplicated present** (`Ce-`, full grade: *dé-deh₃-ti), and the
   **thematic reduplicated aorist** (`Ce-`, no grade fixed: *wé-wk-e-t). A
   type whose grade the handbooks do not fix states none, and the step prints
   none.
2. **The record's sentence is one step of the timeline.** `_reduplication_read`
   reads the first sentence only, refuses a `+` (that is an arithmetic read
   elsewhere) and a hedge, requires the root to stand at the start of the word,
   and matches the type through `_REDUPLICATION_TYPES` — the table supplies
   the syllable and the grade, never the sentence. The row is a one-piece
   `reduplication`, so `_SINGLE_PIECE_KINDS` admits it, `_own_construction`
   starts the ladder at the word, `_rung_builds` draws the step and
   `_raw_constructions` indexes it for "words built on it".
3. **A descendant is not a reduplication of the root.** Proto-Germanic
   *bibāną's sentence is "From Proto-Indo-European *bʰe-bʰóyh₂-e …, reduplicated
   stative of *bʰeyh₂-" — the clause describes the *ancestor's* formation, and
   the chain has crossed a stage boundary before it (the test
   `_CHAIN_BOUNDARY_RE` already makes for an arithmetic). The reader refuses a
   sentence that opens with an ancestry cue and names a starred form before the
   clause, so the word climbs to the reduplicated PIE word instead. Read over
   the corpus, exactly 33 entries state a reduplication, all in PIE.
4. **A line begins at the oldest mark.** A step at the top of the ladder drew
   `.clead`'s rail — the segment that brings the line *down from the row above*
   — with nothing above it, so *h₂ent- wore a stub of line that met nothing
   (admin, 2026-11-12). `.constructstep:first-child` now hides that segment and
   the first row's one-pixel join, so the spine starts at the diamond and runs
   down. A step with something above keeps the segment.
5. **A homonym is chosen by the record, not by index order.** PIE heads
   `swer-` twice — "to ache, fester" and "to resound; to speak loudly" — and
   `_lemma_entry` returns the first. *swarō's own sentence quotes which one it
   continues ("from Proto-Indo-European *swer- (“to say, speak, talk, swear,
   curse”)"), so `_ancestor_gloss` reads that parenthesis and `_sense_entry`
   picks the entry whose gloss shares a content word with it, in the ladder, in
   the ancestry rows and in the review's sense check. With no hint, or no
   shared word, the first entry stands exactly as before. Measured: the rung
   over *swarō now reads "to resound; ringing, whistling", not "to ache".

**Not done.** No lemma was invented: all 33 reduplicated PIE words were already
in the glossary, so the release adds their constructions, not their spellings.
No grade was guessed for the aorist, and a sentence the reader cannot read
stays silent rather than filling the timeline with a formation the record does
not state.

**Tests.** `tests/test_build.py` pins the perfect's o-grade, the i-present's
zero grade, the e-present's full grade, the aorist's silence, the `argued`
confidence of *(me)mógʰe, the refusal of a hedged sentence and of a
descendant's clause, the ladder starting at the word, and the homonym choice.

## 2026-11-12 — a spine is not only the part above the word

**What.** On `gem-pro/andaswarō` the vertical line vanished in the two places
nobody had measured: between *h₂entó- and the diamond above *anda-, and from
that diamond all the way down to the *andaswarō* rung. The `+` between *anda-
and *swarō* also sat about 13px below the line it joins (admin, 2026-11-12:
"the line on the left has disappeared … the line around the + sign is shifted
vertically"). Both came out of v0.17.10's move of the diamond into the tree.

1. **The mark kept the line above it.** `.crail.mark::before` was blanked along
   with the sideways stub, because the mark used to be drawn *outside* the tree
   and had to hide a line that ran under it. Now the diamond stands **on** the
   spine: the row above ends where this row begins, and the mark's own segment
   hands the line to it. Only `.cterm > .crail.mark::after` — the stub into the
   word, which would run under the word that stands at the diamond — is gone.
2. **A step hands the spine to its word.** `.constructstep:first-child
   .rail::before` was `display: none`, from when the rule meant "nothing above
   the mark": but a step with no stage above it still has a word *below*, and
   that is the half of the line the reader was missing. The rule now draws the
   last `--bpad` of the step (the meaning strip under the tree) and nothing
   more; the tree's own rows draw from its oldest mark down to the piece's row
   (`.cpiece.first > .cterm > .crail::before { bottom: 0 }`), and the two meet
   at the rung's edge. A step *with* a stage above keeps its full-rail rule.
3. **The `+` is a term row, not a meaning row.** `.cplus` is one `--crow` cell
   so it hangs with the columns, but its content has to be the `--termh` band
   the words stand in: `padding-bottom: calc(var(--crow) - var(--termh))`
   centres the sign and its two stubs on the words' line instead of half a
   meaning-line (17px of `--foot`) below it. A `.cbuild` strip's `+` already
   did this, which is why the nested `+` looked right while the outer one did
   not.
4. **A phone's scrollbar is not part of the spine.** The tree scrolls sideways
   and its scrollbar is painted above the page, across the rail column, exactly
   where the line leaves the tree. On the narrow layout the strip stays
   scrollable by touch but its bar is hidden (`scrollbar-width: none`,
   `::-webkit-scrollbar`, the same treatment the nav gets), so the spine reaches
   the rung at 420px too.

**Tests.** `tests/test_ui_render.js` pins the four joins and the `+`'s line as
sheets, and each assertion was checked against the v0.17.10 sheet — where it
fails. Measured in the browser: the first piece's rail track and the step's
rail share one centre, the union of the rail segments covers the top mark to
the step's bottom with a largest gap of 0px on `gem-pro/andaswarō`,
`gem-pro/*anda`, `ine-pro/*h₂entó-`, `ine-pro/*h₂énts`, `ine-pro/*tr̥s-nó-s`,
`en/about` (two analyses), `de/überhitzen`, `de/entscheiden`, `gmw-pro/aikīn`,
`iir-pro/sambʰandʰás` (the last four have a step *not* first in the ladder), and
`plus error = 0.0px` on every `+`. Checked at 1500px, 1400px and 420px, light
and dark.

**Numbers.** 973 Python tests green, node suite green.

## 2026-11-12 — every column hangs from the pieces' line

**What.** On `gem-pro/andaswarō` the climb above *anda- stopped at *h₂énts: the
piece's own construction (*h₂ent- + *-s) was drawn as a nested strip crammed
into the column, one size down, and the rows of that column were not the rows of
the one beside it, so *h₂entó- (PIE, over *anda-) and *swer- (PIE, over *swarō)
stood two rows apart. The reader asked for two things: the climb above the piece
must keep going, and **two words that come from the same stage of the family
must stand on one horizontal line** (admin, 2026-11-12).

1. **One row per step, one height for every row.** `chainRow` is now a
   `.cnode` of the form, its meaning and its stage; `climbOf` turns a word whose
   own record states a construction into a `.cbuild` row and climbs on through
   that construction's first piece, so *anda-'s column reads *h₂ent- + *-s,
   *h₂énts, *h₂entó- — three equal rows — and *swarō's reads *swer-. Every row
   (`.cnode`, `.cbuild`, `.cterm`) is one grid, `--crail | the word`, exactly
   `--crow` high.
2. **A column is anchored at its bottom.** `.bline` is `align-items: flex-end`
   and `.cpiece` is `justify-content: flex-end`, so a column's k-th ancestor is
   k rows above the pieces' line. Same stage ⇒ same distance from the line ⇒
   same line. This is the invariant a change to this tree has to keep; it is why
   rows may not size themselves to their content.
3. **The stage stands beside the word.** `.cstage` replaces the label column
   (`.cwhen`, 128px): a column no longer has to be as wide as its longest
   language name, and the row itself says which stage a word is of, which is what
   two rows on one line are compared by. Era and the entry's sentence are on the
   row's hover.
4. **The diamond is the first piece's own mark.** The step's `.rail` is one
   unbroken segment and the diamond lives in the first column's rail track
   (`.crail.mark`), in the piece's row. Measuring it from the bottom of the step
   (`--spine`) was correct only while the tree had no horizontal scrollbar: on a
   phone the scrollbar's 15px moved every mark up off its word. `--spine` is
   gone.
5. **A built ancestor is not a smaller staircase.** `.cbuild` keeps the tree's
   own sizes and heights; a step a reader cannot read at the size of its
   neighbours is not a step.

**Tests.** `tests/test_ui_render.js`: the construction section was rewritten to
the column contract (one column per piece, oldest first, the last row of each
column the one next to the piece, the stage beside the word), and a new case
renders the reader's own example and asserts that *h₂entó- and *swer- are both
the last row of their column and both PIE — the markup half of the invariant —
with the sheet's half (`height: var(--crow)` on every row class, `flex-end` on
`.bline` and `.cpiece`) checked in the same case.

**Numbers.** 973 Python tests green (unchanged), node suite green; checked in the browser at
1400px and 420px, in both themes: the diamond, the dot and the word share a
centre to within half a pixel at both widths.

## 2026-11-12 — *anda- descends through *h₂entó-, and a one-word formation is a step

**What.** On `gem-pro/*anda` the timeline jumped from *anda- straight to PIE
*h₂énts, although Wiktionary says "From pre-Germanic *h₂entó-, a combining form
or allative formation from the Proto-Indo-European root noun *h₂énts". *h₂entó-
is the ancestor; *h₂énts is the word *h₂entó- was made from. The requested
order is *anda- → *h₂entó- → construction from *h₂énts → *h₂ent- + *-s.

1. **A `pre-` label is a label, not a stage.** `_prose_ancestry` (v0.17.8)
   skipped "pre-Germanic" because no stage is registered under that name and
   took the next registered stage it found in the sentence — one level too
   high. `_PROSE_PRE_STAGE_RE` reads the form the label marks, and resolves its
   stage from the nearest registered stage the same sentence names for it; the
   sentence's word order then decides which form is the ancestor. Read over the
   whole corpus, the change moves exactly two entries: *anda- (now *h₂entó-)
   and *aba- (now *h₂epó-, the same word the old row named without its hyphen).
2. **The ancestor needs an entry.** PIE *h₂entó- has no Wiktionary page of its
   own — it is recorded in the derived terms of *h₂énts ("*h₂entó ((fossilized)
   allative singular, with *-ó) or, less likely, a thematic combining form
   *h₂ent-o-") and in *anda-'s etymology sentence. The supplement row quotes
   both, carries the gloss *against* from the descendant the same line names,
   and cites the *h₂énts page it was read on.
3. **A formation may be one word.** A construction was required to join two or
   more pieces, so a one-piece row was dropped and *h₂entó-'s formation would
   have been invisible. `_SINGLE_PIECE_KINDS` (`combining`, `derivation`) is
   the only licence for a one-piece row: every other kind is a join, and a
   one-piece row of another kind is an analysis cut short, never a step.
4. **A built piece keeps its own construction.** `constructStep` drew the
   *ancestors* of a piece but never the construction of the piece itself, so
   *h₂entó-'s step would have named *h₂énts and stopped. `ownStep` draws a
   piece's own formation above it, in the same grammar, at both the first
   piece (on the diamond's line) and every later column.

**Tests.** `tests/test_build.PreStageAncestry` (the reader, the entry, its
one-piece construction, the nested step, and the refusal of a one-piece row of
another kind) and a node case in `tests/test_ui_render.js` that renders both
levels and checks the order.

**Numbers.** 973 Python tests green, node suite green.

## 2026-11-12 — every reconstructed word wears its star, and a prose origin is read

**What.** On `gem-pro/andaswarō` the piece *anda- printed bare beside a link
that read `/gem-pro/*anda-`, the word built at the end of the line printed
`andaswarō` under a title that read `*andaswarō`, and the branch card below it
printed a Proto-West Germanic form with no asterisk at all — while the timeline
above *anda- ended in a `???`, although the word's own page records where it
came from.

1. **One star test.** The asterisk was being added by whichever renderer drew
   the form, each with its own `/-pro$/` test, so a page could agree with itself
   in one place and not in another. `reconStage`/`starred` in `app.js` now
   answers for every word the page prints — rungs, records, construction
   pieces, chain nodes, drafts and their results, the merge word, branch cards,
   next-stage buttons, "words built on it" and the notes — from the stage's own
   `kind` (and a stage written in a reconstructed script); the code's `-pro`
   suffix is only the fallback for a payload carrying neither, and a form that
   already starts with `*` is never given a second. `attestation.written` is the
   same rule on the server, so the title, the payload and the page cannot
   disagree.
2. **A piece says what it means.** `_base_row` printed only the gloss the
   etymology quotes in brackets, and `From *anda- + *swarō.` quotes none — so
   the construction row came back `known: true` with `gloss: ""`: a link that
   opened a page, and nothing under the word. The piece now asks `_lemma_entry`,
   the same reader as the rung and the ✓; a quoted gloss still wins over the
   entry's first sense.
3. **A prose origin is read when no template states one.** *anda-'s entry has
   no `anc` rows: Wiktionary wrote the origin as a sentence, "From pre-Germanic
   *h₂entó- … from the Proto-Indo-European root noun *h₂énts". `_prose_ancestry`
   reads only the first sentence, only when it opens with an ancestry cue, and
   refuses a hedged, comparative or substrate sentence — and any sentence with a
   `+`, which is a construction, not an ancestor. The ancestor must be a
   **registered stage** naming a **starred form the stage's glossary heads**,
   so the ladder can open it; "pre-Germanic" is not a stage, and the same
   sentence is read on to Proto-Indo-European *h₂énts. It is a fallback inside
   the one reader (`_ancestry_triples`), so the ladder, the piece's own
   timeline and the coverage count all see the same rows: 60 entries
   corpus-wide, and a stage outside the word's own chain still cannot become a
   rung.

**Not done, deliberately.** A sentence that names only a stage this model does
not have (pre-Germanic, a substrate) is still silence, not a guessed `???`
filler; and an attested stage's bare word in prose is not read as an ancestor —
the asterisk is what makes the sentence unambiguous.

**Numbers.** 968 Python tests green, node suite green; `*andaswarō`'s timeline
now climbs *anda- → Proto-Indo-European *h₂énts (with its own *h₂ent- + *-s).

## 2026-11-12 — the dot opens the construction row, and a hyphen is notation

**What.** On Persian تشنه the PIE rung said *no entry for this word*, although
the form beside it linked to `ine-pro/tr̥s-nó-s`, a page that opens the entry
`tr̥snós` and shows its whole timeline. And on a PIE rung the construct line was
a button beside a row of pills, which did nothing when clicked.

1. **One word, two spellings.** Wiktionary quotes a reconstructed compound with
   its morpheme boundaries (`*tr̥s-nó-s`); the glossary heads the same word solid
   (`*tr̥snós`). `_lemma_entry` now retries the joined spelling, stress aside, for
   every reconstructed form — and only for one: in an attested language a hyphen
   can be part of the headword (English *well-being* is not *wellbeing*), so the
   fallback never runs there. The sense, the evidence and the ✓ all ask the
   same helper (`_notation_entries`), because fixing only the sense left the
   rung showing *no entry* under a correct gloss. Two more notations were doing
   the same thing: the engine's **stress token** (*Hnˈawa* for the dictionary's
   *Hnáwa*) and **case** (a stage heads *hā́fš*, an etymology row writes
   *Hā́fš*). `_lemma_entry` reads both, so a rung can no longer call a word
   missing while linking to the entry that holds it — 494 rungs over 325 pages
   now agree with the page each links to.
2. **The button and the pills are gone.** The dot beside a word is a button
   (`button.rdot`): clicking it opens a row *above* that word — a diamond on the
   rail, because a formation is not a sound change — holding the word itself
   (unchanged, at word size, in its evidence colour) and a menu of what the
   stage records: its cited suffixes, its endings, and its own headwords
   (`/api/words`, one fetch per stage per tab). Nothing is typed: the pencil is
   the door for typing, and a construction is a question put to the morphology.
3. **One step, composed by the stage.** `service.build_at` (behind `/api/build`)
   answers a single construction — the pieces, the grade the formation puts the
   stem in (`*ters-` → *zero grade*), and the form they make — so the row shows
   `*ters- zero grade + *-nó- → *tr̥snós` without a page reload, and its result
   links to the built word in the timeline (`?build=`). A second choice composes
   on the first result, so two suffixes stand on one line instead of a tab each,
   and a piece the word already wears says so instead of printing the same form
   again.

**Why.** The reader asked for a construction he could *do* rather than a menu he
had to decode: one click from the word, then the stage's own terms. The pills
looked clickable and the panel asked him to type a word he had not chosen yet.

**Numbers.** 964 Python tests and the render suite; the dot, the menu and the
joined-spelling lookup each have a test.

## 2026-11-12 · an icon is a page that was recorded

The reader clicked the W on Persian **کبود** and on Middle Persian **kpwt'** and
nothing happened, although `en.wiktionary.org/wiki/کبود` exists.

- **A page or nothing.** The server now resolves each record to its `pages`
  (`service._entry_pages`): the Wiktionary article when one exists, and the
  dictionary's entry for the *word* when the entry recorded one. Dehkhoda's
  rows carry `https://vajehyab.com/dehkhoda/<word>` (the page the entry was
  imported from), never `https://vajehyab.com/dehkhoda/`. Only pages are drawn;
  a form whose page is not recorded carries no icon at all, so `kpwt'` — named
  in the Persian etymology but with no entry and no page — loses its dead W.
- **One glyph per kind.** W for Wiktionary (the serif mark), an open book for a
  dictionary, a page for anything else; the corner (`recordTag`) and the head
  row (`sourceRow`) draw one `<a>` per page, so کبود now offers both.
- **Ancestry does not lend its pages.** A rung with no entry of its own used to
  borrow the headword's sources; it now gets `pages: []`, because the article
  it was quoted from is another word's page.
- **The index is the site's own title list.** `tools/en_wiktionary_index.py`
  reads `enwiktionary-latest-all-titles.gz` (namespace 0 for attested words,
  118 for `Reconstruction:` pages) and writes
  `data/sources/en_wiktionary/<lang>.jsonl.gz` with the headwords that really
  have a page — 428k headwords in fifteen seconds, where asking the API page by
  page was rate-limited and hours long. Absence from the file means "no page
  recorded", and the interface stays silent for it.
- **A reconstruction is titled without its asterisk.** `Reconstruction:
  Proto-Germanic/nahts` is the page; the link used to keep the `*` and opened
  nothing (`service._wiktionary_title`).

## 2026-11-12 · the tree keeps going, and the diamond is the first word's mark

Four things the reader found on one page (`peo/Ciçafarnāh`), all of them the
same complaint in different clothes: the timeline stopped where a source did.

- **The top of the tree is spaced like the ladder.** The first element's ascent
  is drawn as ladder rungs (`.rung.croot`) instead of tighter inset rows, and a
  rung that carries a construction above it gets the ladder's own air.
- **The diamond and the first word are one mark.** The 30px wire between them
  bought nothing and left a strip of empty sky above the pieces' line; the first
  word now stands at the diamond and the line leaves its own right edge.
- **A construction stated for an ancestor belongs to the ancestor.** Wiktionary
  writes *kit-ró-s = *keyt- + *-rós in its article on *čitrás; there is no
  article and no entry for *kit-ró-s. `_origin_node` now reads the child's own
  entry for a row about the parent's stage and form, so the *čitrás page and the
  Ciçafarnāh page draw the same step.
- **A ladder does not stop where a dictionary does.** When the start rung sits
  above the word's own stage, `hierarchy` splices that ancestor word's own ladder
  above it (`climbed`), guarded by a list of the words already climbed through
  and a depth of four. The `earlier` list disappears with it: those stages are
  drawn now, not merely named. Climbed rungs stay out of
  `steps_differ`/`mismatched_steps`, because the coverage counter measures the
  word's own recorded ancestry and the page must not name stages it never
  measured.

# Decisions

## 2026-11-12 — the construction is one tree, drawn at the scale of the word

**What.** The step above the word was right, but it was drawn as a row of small
boxes on a line of their own, with each piece's ancestry in a thinner, inset
sub-timeline. The reader asked for one tree (`peo/Ciçafarnāh`): a line leaves
the diamond that sits **on the main rail**, touches `𐎨𐎡𐏂 čiçaʰ`, then `+`,
then `*farnah`; the pieces are written like the headword itself; and each piece
then climbs a timeline that looks exactly like the ladder below — same rail
thickness, same language-and-years column on the left.

1. **One spine, on the rail.** The diamond is `.constructstep .rail i.cdiamond`,
   placed at `top: calc(100% - var(--spine))` so it sits on the same 2px line
   that runs through the whole timeline; the line above it stops at the mark and
   a short tail carries on to the rung that holds the word. `.cwire` leaves the
   diamond to the right, `.cterm .cline` runs under each piece's column, and
   `.cplus` breaks the line for the sign.
2. **The pieces are words.** `.cform.term`: 21px, mono italic, in the colour of
   its own evidence, opening its word page. A piece carries **no language
   label**: it is a word of the stage the step belongs to, and repeating the
   stage on every piece was noise. Bound morphemes stay plain (no link).
3. **Each piece is a full timeline.** Every ancestor is a `.cnode` row: the
   language's name and its years against the rail on the left (13px/11.5px, the
   ladder's own sizes and colours — `kind` now travels on every origin node so a
   proto form is gold and an attested one green), the form on the right, the same
   2px rail and the same 10px rung as the ladder. A piece with no branch drops
   the label column, so the line reaches it at once; a piece whose origin is not
   recorded hangs a `???` above itself exactly as before.
4. **The tree is the step's last row.** `--spine` is half a term row measured
   from the step's own bottom, which is where the horizontal line has to be, so
   the step's rail and the tree's line meet without a magic number. Tabs and the
   compact construction row stay above it.
5. **Cuneiform is set upright and spaced** (`.cunei`, detected from U+103A0–
   U+103DF): a synthesised oblique smeared `𐎨𐎡𐏂` into one shape at 21px.

Regression: the render test builds `peo/Ciçafarnāh` and pins one `.btree`, two
`.cterm` pieces at word size, four `.cnode` ancestors with their names and years,
no language label inside a piece, the wire before the first piece and the `+`
after it, and the tree as the step's last row; `TestAConstructionIsATree` pins
`kind` on a proto node and on an attested donor.


## 2026-11-12 — the construction stands above the word, one tab per analysis

**What.** The step added earlier the same day put the construction *below* the
form it builds, which is backwards: the timeline runs from old (top) to new
(bottom), so the pieces and their own histories come first and the word they
make is underneath them. The reader also named the three kinds of step a
timeline has — inheritance (the sound laws), **borrowing** (the record's donor,
whose rules are the donor's own: English s+consonant becomes Persian `es-`,
*starbucks* → *estārbāks*) and **construction** (pieces of the current language
plus affixes and morphology, in Proto-Indo-European as anywhere else) — and
asked that every construction be shown in the timeline, never under the word,
with a tab when a record states more than one.

1. **Above, not below.** `constructStep` is emitted before its rung, and the
   rail's segment is drawn between the diamond and the word. The header block
   (`#construct` under the title, 2026-11-08) is gone: the reader's tools — the
   suffix the word wears and the `(+)` that tries another cited suffix — travel
   into the step as a compact row (`constructHtml(…, compact)`), so nothing was
   lost. `renderJoin`'s "Where the pieces come from" section is suppressed when
   the timeline already draws the same pieces; a join the rung does not carry is
   still printed.
2. **Proto-Indo-European has a timeline.** A PIE word is built like any other,
   so `renderRoot` puts `renderHierarchy` above the reconstruct panel whenever a
   rung carries `builds` (ǵʰutós: *ǵʰew- + *-tós, then the word). Its badge says
   *top of the family* instead of *no origin recorded*.
3. **A tab per analysis.** `_rung_builds` returns every row the record states for
   the rung's form, de-duplicated by `(kind, pieces)`; `built_as` keeps the
   first for older callers. The step draws one `.btree` per build behind
   CSS-only radios, so switching tab needs no script and survives a ladder
   repaint (English *about*: `on + būtan`, `be + ūtan`).
4. **`???` is for a family word with no recorded origin.** `_origin_node` now
   ends a Proto-Indo-European form at `pie` **before** it asks whether the
   glossary holds it — the top of the family is not a gap — and gives a word of
   a language outside the family (`data.non_ie_sources()`: Arabic, Turkish, a
   Semitic proto-form) the terminal `outside`, so no `???` claims an ancestry it
   never had. A bound morpheme is `bound: true` with `branch: null` (leading
   hyphen or Persian tatweel), because a suffix was neither inherited nor
   borrowed.
5. **A piece is a form, never a printed structure.** 50 stored rows carried a
   piece written as `str(['کَم ', '>'])`; `_formed_piece` refuses one and
   `tools/clean_built_as.py` drops those rows from the built glossaries
   (idempotent, no kaikki dump needed).

Regression: `TestAConstructionIsATree` (11 tests) pins the tree on
`peo/Ciçafarnāh`, the PIE ending with and without an entry, the outside-family
terminal on `ar/كِتَاب`, the bound suffix on `fa/کتابدار`, the cleaned row on
`fa/کمزور` and the two tabs of `en/about`; the render test pins the ordering
(top before the rung), the tab markup, the `outside` wording and the `???` for
a family word with no origin.

## 2026-11-12 — a construction is a step of the timeline, not a line under the word

**What.** On `peo/Ciçafarnāh` the formation was printed as `CONSTRUCTION: 𐎨𐎡𐏂 čiçaʰ
+ *farnah` on its own line under the headword, and the timeline below said
"Recorded ancestry for this word begins at Old Persian. Earlier stages — … —
exist in the family, but no form of this word is linked to them." The reader
asked for three changes (2026-11-12, 10:18 and 10:24): the construction must
become part of the timeline, drawn with a diamond instead of a rung's circle;
each piece must climb its own ancestry upward, so the page shows an
upside-down tree; and with a `???` in the tree the "earlier stages exist"
paragraph is only noise. The section heading, `From X to Y`, became **Timeline**.

1. **The construction is a step.** `service._rung_built` now gives every piece
   `lang` and a `branch`; the front end renders the step with `constructStep`
   (`.constructstep`, a diamond on the rail, the pieces on the base line joined
   by `+`) and `builtLine` is gone. Nothing is printed twice: the step *is* the
   rung's statement of how its form was built. (This first pass drew the step
   below the rung; the entry above corrects it to above.)
2. **One word above, not the row list.** `service._origin_node(lang, form)`
   walks a piece's ancestry: the first `inherit`, else the first `borrow`, else
   the first `derived`. An entry can list nine alternatives (`non- … non … nān
   … *nainaz`), and drawing all of them made the tree a wall; a `root` is a
   relation rather than an ancestor (`_is_root_form`), so it is never the step
   above. Depth is capped at 8 and a revisited form stops the walk.
3. **Four honest endings.** `terminal` says why a climb stopped: `pie` (the
   form is Proto-Indo-European), `borrowed` (the record says the word was
   borrowed from here, so the donor's history belongs to the donor), `missing`
   (the record names a form the glossary has no entry for) and `end` (the entry
   records no origin). The page draws `???` for the last two — the reader's
   own mark for a word nothing explains — with the named form beside it, so a
   ??? never hides which form was meant. A borrowed donor is drawn as itself,
   in its own language, and is not turned into a ???.
4. **The heading is Timeline**, on the ancestry ladder and on a borrowed
   word's ladder alike; the paragraph announcing the stages above a start is
   gone (`earlier` keeps only the two cases where the reader chose the start,
   because those state a decision, not scenery).

Regression: `TestAConstructionIsATree` (6 tests) pins the tree on
`peo/Ciçafarnāh` (the branch to `*kit-ró-s`, the borrowed Old Median trunk),
`en/non-` (one parent, not nine), `iir-pro/*čitrás` (no root as a step) and
`en/livre` (an entry with no origin ends in `end`); the render test pins the
step's markup — the diamond, the pieces as doors, the `???` and its reason.

## 2026-11-12 — a code is not a language, and the mark is Wiktionary's W

**What.** The page for Old Persian *farnah said **"borrowed from xme-old"**
beside a sentence that said "Borrowed from Old Median". The badges and the
ladder each had their own name lookup; only the sentence read the table that
knew the name. Two smaller things came with the fix: several codes the
lexicons print are not codes at all, and the quotation mark on a record was
asked to become Wiktionary's own initial.

1. **One resolver.** `data.language_name` answers "what is this code called"
   for every reader — the loan badge, the ancestry rows, the ladder's stages,
   the construction pieces. The order is the registry, the names harvested
   from Wiktionary's descendant trees, the curated names for borrowers outside
   that tree, Wiktionary's full language table, a register of a modelled stage,
   and the donor register. `loans._display_name` now calls it instead of
   keeping a narrower copy; that copy is exactly why the badge and the sentence
   disagreed.
2. **Wiktionary's own table is in the repo.** `data/language_names.json` only
   reaches the descendant tree (363 codes). `tools/build_wiktionary_names.py`
   saves Module:languages/data, Module:etymology languages/data and
   Module:families/data as `data/sources/wiktionary_language_names.json.gz`:
   **10,172 names, 76 KB**. A borrowing can name any language at all; a rung
   may not print its code because that language was not in the PIE tree.
3. **Old Median is a stage of the model.** `xme-old` joined
   `data/languages.yaml` as a Northwest Iranian sister of Old Persian
   (c. 700–300 BCE, reconstructed script, provisional), so its rungs carry a
   branch and a date rather than a bare name. It is the fourth daughter of
   Proto-Iranian beside Avestan, Old Persian and Parthian.
4. **The codes that were not codes.** `tools/repair_anc_codes.py` rewrote 410
   lexicon entries: 103 codes with a leaked `['` prefix (and the 82 duplicate
   rows that came with them), 206 abbreviated Latin stages (`ML.` → `la-med`,
   `LL.` → `la-lat`, `NL.` → `la-new`, `VL.` → `la-vul`, `EL.` → `la-ecc`),
   29 marker rows that name no language (`ety`, `unc`, `w`), 62 Sanskrit root
   rows whose first field was the root's spelling rather than `sa`, and one
   `xcL` case typo.
5. **The mark is a W.** The quotation mark on a recorded word and in the source
   row is now a monoline W drawn as SVG: Wiktionary's initial, like Wikipedia's
   W, with no globe so the two are never confused (admin, 2026-11-12). It is
   the same mark at both sizes (15 px in the source row, 13 px on the word).

Tests: `test_language_names` pins the resolver (`xme-old`, Arabic, a borrower
outside the tree, a two-language row, the Latin abbreviations), the *farnah
page's loan name and wording, and a guard that every ancestry and cognate code
in the data resolves to a name. `test_web` and `test_council` now count Old
Median among Proto-Iranian's daughters. The render test pins the W and the
absence of the old quotation mark.

## 2026-11-12 — the title carries the claims, the rule carries the sources

**What.** Reading `peo/Ciçafarnāh`, four things on the page said more than the
page needed. The paragraph under the title repeated the two badges in words;
the quotation mark sat on the word's corner as if it were a mark *on the word*
rather than a door to its source; the record's label said `recorded (*)` beside
a headword that already began with the asterisk; and the timeline's
construction line printed each piece's gloss in full and a `· affix` tail, so
`built as 𐎨𐎡𐏂 “shining; appearance; lineage” + *farnah “glory” · affix`
carried three claims at once.

1. **No paragraph under the title.** The band and the record keep their
   tooltips (and the tap-to-pin behaviour); the sentence under them is gone.
   The definitions still print on the Coverage page, where a reader asks what a
   band means.
2. **Sources are icons on the rule under the word.** One icon per source that
   has a page: the quotation mark for a Wiktionary entry, a book for a
   dictionary, a page for anything else. A site's front page is not a source
   for this word and is not a link.
3. **The asterisk belongs to the word.** `LABELS["recorded"]` is `recorded`,
   not `recorded (*)` (and `proposed` likewise), and hovering the starred
   headword says the one thing the asterisk means: *No text spells this word.*
4. **A construction is one line:** `CONSTRUCTION: 𐎨𐎡𐏂 čiçaʰ + *farnah` — the
   writing, then the piece's reading when it is written in a script. The
   gloss, the kind of formation and whether the record states it or this model
   read the seam are on the line's and the pieces' tooltips, and each piece is
   a link to its own word page (`_rung_built` supplies `reading`).
   The link rule for pieces changed with it: a rung's own form stays plain
   because the page is already open, but another word in the *same* language is
   a door like any other — the old rule excluded the whole language, which left
   every construction piece in the language of the page unlinked.

Tests: `test_attestation` pins the labels, and the render test pins the
construction line (no gloss, no kind, both pieces linked) and the source row
(one icon per source; a front page with no entry is no icon).

## 2026-11-12 — a homograph's ladder belongs to the sense the page opened

**What.** The admin opened Persian دوش *last night* (`sense=3`) and found no
timeline at all; opening *shoulder* (`sense=2`) showed a green "fully
explained" badge over a box saying "no recorded ancestry for this word". The
record is complete for both: Wiktionary derives the shoulder from Middle Persian
*dōš* ← PIE *dóws*, and the adverb from PIE *dowséh₂*. The word page picked
the right sense — the ladder did not.

1. **The ladder was always sense 1's.** `service.word` computed `sense_no` and
   handed `entry` to every other view, but called `hierarchy(lang, entry["word"],
   …)` without a sense. `hierarchy` then defaulted to the first group — the
   French loan *shower*, whose etymology is a borrowing — and returned no ladder
   at all. The page therefore drew no timeline for sense 3, and sense 2's band
   (read from the published measurement) had no ancestry under it. The call now
   passes `sense=sense_no`.
2. **A rung's own record came from the first homograph.** `_record_block` and
   `_recorded_at` looked the word's own stage up in the glossary by *spelling*
   (`_lemma_entry(stage, primary)`), so the shoulder's final rung quoted
   "shower (bathing)", its /duːʃ/ IPA and its reading *duš*. A new
   `_own_stage_entry` makes the page's entry the record of its own rung, so the
   meaning, reading and IPA are the sense's own.
3. **A script fit may not overrule a recorded reading's vowels.** The 2026-11-11
   rule stopped a fit from overriding a *consonant* the record states (l-w-c
   *rōz* vs the laws' *rōč*), but an abjad's signs also leave the vowels to the
   reader: دوش fitted the laws' *dūšā* although the entry reads *dōš*. An abjad
   fit now counts only when it reproduces one of the readings the dictionary
   records, length notation aside (`_abjad_reading`; `script.match` marks the
   abjad case). The laws' *dūšā* is a different word — PIE *-eh₂'s final -ā has
   no registered loss — so the rung says *differs*, and the rung that does match
   names the reading it matched (*duš*, which Wiktionary also records for the
   shoulder beside *dōš*).
4. **The published band uses the same rule.** `tools/coverage.py`'s script layer
   now asks `service._script_fit` instead of `script.match`, so the badge, the
   glossary and the ladder cannot disagree. Persian دوش is published as
   *ie_loan · full · partial* (shower, shoulder, last night). The full run moved
   eleven words: Persian 13 → 11 fully explained and 18 → 11 with adjustments
   (the other nine to *partial*), and one Old Persian word whose sign fit
   disagreed with the reading its entry states. Nothing was bent to a word: the
   shoulder stays green because the dictionary records *duš* for it.

The glossary endpoint also dropped the `q` its service has accepted since
2026-11-10, and the page never sent one; the filter now works from the address
and from a box beside the language picker.

Tests: `tests/test_fa_sense_ladder.py` (7) — the loan has no ladder, sense 3 has
one that starts at *dowséh₂*, each sense's own rung quotes its own meaning, the
laws' *dūšā* does not match *dōš*, the shoulder matches *duš*, and the badge
equals the ladder's band.

## 2026-11-11 — the laws start from a reading, and every form has two layers

**What.** The admin opened the Middle Persian word *lwc* "day" and saw a ladder
that did not work: "it seems like it's trying to reconstruct from the script,
not the romanization. Obviously, reconstructing from the word in its own script
won't work, don't ever do that." It was — and he asked for the structure to be
revised, not just patched:

1. **The engine refuses a writing.** `rules.derive_detailed` returns
   `unreadable` and rewrites nothing when its input is written in a script, so
   no caller can derive from cuneiform, Pahlavi or Greek letters again. The
   ladder's input is `service._phonological_form`, which now reads a scripted
   form in a fixed order: the entry's `phon`, the language's spelling table, the
   entry's `translit`/IPA, a reading the corpus quotes for that spelling, and —
   for an alphabetic script only — the letter-by-letter transliteration. A
   syllabary's sign string (`ra-u-ca`) is never an input: hyphens print signs,
   they do not spell sounds. A rung with no reading says so in words.
2. **The readings the record states reach the table.** `tools/build_readings.py`
   now also harvests Wiktionary's `ts=`/`tr=` templates
   (`{{inh|pal|peo|𐎼𐎢𐎨|ts=raučah-}}`), so the Old Persian ancestor of *lwc* is
   read *raučah* instead of *ra-u-ca*, and every entry that quotes a form with
   its reading in a parenthesis is indexed too. `lang` in that file now names the
   language that *spells* the form, not the entry the sentence was read in, and
   a row is kept only when that language writes the word or an ancestry row
   names it at its stage.
3. **A form has two layers, printed once each.** `show_reading` is true for a
   headword in a script *and* for a transliteration of one (`script.writes`), so
   *lwc* prints `lwc · rōz`; `_with_reading` clears the flag when there is no
   reading, and a rung does not repeat a reading the form beside it already
   spells.
4. **A fit does not override the recorded reading.** The Pahlavi signs l-w-c can
   stand for *rōč* or *rōz*; the record says *rōz*, so the rung stays `differs`
   and prints "the writing allows it — the record reads rōz". What the script
   cannot write (a final /h/, the y-sign closing a final -i) is still set aside
   on both sides (`_same_reading`), which is what keeps the Old Persian
   cuneiform matches green.

**Why.** Three separate defects met on one page: the ladder derived from the
script, the record's own reading was not in the table that the laws consult, and
a transliterated headword was treated as if it were a romanisation. Fixing only
the first would have left a ladder "deriving" r-a-u-c-a; fixing only the third
would have printed rōz beside a rung that never ran.

**Numbers.** `lwc` now climbs from Old Persian *raučah* with three laws applied
(`au > ō`, final *-h* lost, final short vowel lost) and lands on *rōč*; the
record reads *rōz*, and the page says so. `data/readings.json` 93 → 522 rows.
The measured corpus does **not** move: `data/coverage.json` is byte-identical,
because the counter only ever counted a derivation that produced the attested
word, and a scripted start produced nothing to count. What changes is that all 5,028 Modern Greek words
with an Ancient Greek ancestor now hand the laws a reading instead of Greek
letters (`tests/test_midnight_el.py` pins the new floor), and the
ladders of every word whose ancestor had no glossary entry to read it.

One entry per decision that changed the model or the way it is measured.
Append-only; the newest first. Each entry says what changed, why, and which
number it moved (or that none did).

## 2026-11-11 — Persian words get their Wiktionary page, and the mark means Wiktionary

**What.** The glossary's Persian words come from Dehkhoda, which has no page on
the English Wiktionary, so the quotation mark on a Persian word opened
**vajehyab** — a dictionary site wearing the mark of a Wiktionary record, and the
one link on the page a reader is entitled to trust by its shape (admin,
2026-11-11). Two changes, one pass:

1. **`data/sources/fa_wiktionary.jsonl.gz`** — 1203 words asked of
   fa.wiktionary.org through `tools/fa_wiktionary.py`: 257 have a page (21%), 946
   are recorded as *missing* so no later pass asks again, and 72 of the pages
   print an etymology. The etymology is stored as the page's own sentence, with
   the revision it was read at.
2. **The mark is a Wiktionary page and nothing else.** `service._is_wiktionary_url`
   decides whether an address may stand behind the mark; a Persian entry's
   `url` (its vajehyab page) is no longer taken for one, and where a word has no
   Wiktionary page the mark is a mark, not a link — the tooltip still names
   Dehkhoda, and the meanings tab still links each Dehkhoda entry to vajehyab.
   `wiktionaryLine()` prints the Persian Wiktionary's own words beside this
   model's etymology, labelled and quoted, never merged into `etym`.

**Why it moved no number.** No rule, no band and no ancestry changed: the ledger
is a citation, and a citation is not evidence for a derivation. What changed is
that a reader can now open the page a Persian word was read on.

**Numbers.** 1203 words checked · 257 pages · 72 etymologies · 946 recorded as
having no page. `tests/test_wiktionary_pages.py` (16 tests) holds the page
reader, the ledger's shape, and the rule that the mark never leaves Wiktionary.

## 2026-11-11 — README for readers, AGENTS.md for rules

**What.** The README had grown into a specification: the word page's ladder was
described rule by rule — every rung, every glyph, every refusal — which is
material for whoever changes the code, not for someone who wants to know what
the project is. The admin asked for the split, so:

1. **`README.md` says what the project is and what it does.** Principles,
   repository structure, install, three commands, the interface (home page,
   header, a word page's ladder and branch, attested / recorded / proposed),
   what the colours mean, how a word is explained, the generated progress block
   and the licences. Its longest section is a page of prose about the ladder;
   there is no rule, no invariant and no CSS class name in it any more.
2. **`AGENTS.md` carries every rule**, compacted to one bullet per rule and
   ordered the way a change is made: build/test, where things live, ground rules
   (the exactness bar, tiers, citations, no target bending, measuring a law,
   never publishing a sample), the word page (title, ladder, readings,
   constructions), senses, data and generation, bands and colours, the
   orthographic layer, the programme, and how a change is measured. The rules
   the admin wrote for this pass — a scripted word is never printed alone, how a
   scripted word is compared with its reading, how a cognate table is drawn, one
   spelling = several words — sit in their own sections there.

Nothing in the model, the data or the counts moved; the README's generated
progress block keeps its `coverage:` markers so `tools/coverage.py --docs` still
refreshes it.

## 2026-11-11 — The title is a sentence, and the language stands in its margin

**What.** The admin asked for the pills to leave the word page's title: they
made a claim about the word look like a tag on a file. Nothing in the model
moved — this is the front end only (`src/pie/app/web/app.js`, `style.css`) —
but the title's parts changed place, so it is written down here.

1. **Where the word stands and how the word is known are one line.** The
   coverage band (`partially explained`) and the record (`attested`,
   `recorded (*)`, `proposed`) were a word and a pill side by side; they are now
   both plain italic text in the title's own size (`.catlead` + `.know`), each
   in the colour the site already gives it, set apart by a hairline dot. The
   attested badge stays where a list is scanned — glossary rows, search — and
   leaves the title.
2. **The language and its years stand in the margin.** `langRail` prints
   `lang_name` and the registry's `era_label` (the same pair a ladder rung
   carries) left of the headword. The margin is *spent*, not added: the grid
   pulls itself left by the rail's width and its gap, so the headword keeps the
   page's own left edge on a wide screen; below 1420px the rail stops borrowing
   the white space, and below 760px it becomes a line above the word.
3. **The category sits beside the meaning.** `catRail` puts the part of speech
   (`pos`) in that same margin on the row of the meaning block, level with the
   gloss. Persian's meaning block opens with the Wiktionary/Dehkhoda tabs, so
   the category drops past them (`.catrail.tabsabove`) instead of floating
   beside a button row.
4. **The review backlog trails the sentence.** `reviewNote` is a plain
   `.backlognote` link — `review backlog · 3`, smaller, muted — after the two
   claims, pushed right where the line has room, and it still opens
   `#/backlog?lang=…`. The pill-and-dot row (`.catline` / `.catbadge`) is gone.
5. **The other two titles follow.** The homograph picker and the
   "no entry here" page use the same grid, the same plain record text, and the
   same margin; the ghost page's "attested language / reconstructed stage" moved
   into the margin under the language, where it describes the language rather
   than sitting next to `non-existent` as if it were a second verdict.

`service.word(..., ghost=True)` and the picker payload now carry `era_label`
(the word page already did), so every title's margin can name the same years.

`tests/test_ui_render.js` pins the new pieces and fails if a `badge` returns to
the title. 864 Python tests and the render test pass; no band, count or
derivation changed.

## 2026-11-10 — A borrowed word has two rungs, and a root is never its ancestor

**What.** Persian دایناسور came out with a six-rung PIE ladder: Proto-Indo-
European *dwey- → Proto-Iranian → Old Persian → Middle Persian → Persian, with
the last rung "differs". Nothing in the record says that. The entry says
"Borrowed from English dinosaur"; the PIE root belongs to the etymology *of the
English word* (Wiktionary's tree puts *dwóh₁ and δεινός above it), and the
ladder took the deepest ancestor it could find and ran Persian's chain from
there (2026-11-10).

Three changes:

1. **A root row cannot decide what a word is.** `loans.classify` read the first
   ancestry row. When that row is a `{{root}}` — a relation, never an ancestor
   (proposals/010) — the row that decides classification is the first *non-root*
   one. 3,138 entries were borrowing from an Indo-European language while
   classified "inherited" (2,490 English, 251 Italian, 140 Persian, 44 Albanian):
   they were drawn a PIE ladder and called *partially explained* instead of the
   blue-grey *loan from another IE language*.
2. **A borrowed word has no sound-law ladder.** `service.hierarchy` returns
   nothing for a word `loans.classify` calls a loan, and the page draws the two
   rungs the record states — *English dinosaur* above, *Persian دایناسور* below,
   and a step row that reads *borrowed from English into Persian*. `loans.donor`
   now answers for `ie_loan` as well as `non_ie`, naming a sister-branch donor
   from the language registry (`data/language_names_extra.yaml` is the fallback).
3. **The donor's own history is text, not rungs.** The word page prints an
   *Above the donor* line under the etymology — "English dinosaur comes from
   δεινός, σαῦρος (a compound); this word borrowed the English form itself" —
   read from the donor word's own entry, with links into it. The stages above a
   donor are the donor's record; they are not this word's ancestry.

4. **A writing-layer match is not overruled by a weaker one.** The counter tried
   the script layer (a registered chain produces a form the word's own script
   can read), and then ran the fallbacks — orthographic, cited stem, unchanged
   ancestor — without testing whether something had already matched. Persian دان
   (`dʰoHnéh₂ → dānā`, read as د-ا-ن) was therefore re-labelled "unchanged
   ancestor" because the Middle Persian rung happens to equal the dictionary's
   transliteration, and reported as reproduced only from Middle Persian. The
   fallbacks now run only when nothing matched. 11 senses moved (*full* +3,
   *adjusted* +8, *partial* −11); in Persian the seven are مادر، بهار، درد،
   دوش، است، دان، کین — each yellow because a recorded rung still differs, as
   the rule requires.

**Persian.** Reading three templates the builder had skipped adds **1,403
Persian words** (9,939 → 11,608 entries):

* `{{ety|fa|:af|ایتالیا|ـیی}}` is an affix construction, not a chain
  (ایتالیایی, زیستشناسی, پیشگیری, کارمند … 1,088 words): the pieces are kept
  as `built_as`, so the word is *built from pieces*, never "unexplained".
* `{{inh|fa|pal|tr=z’hm|ts=zaxm}}` names the ancestor only in the dictionary's
  transliteration and transcription (زخم, تره, خروس, با …): the transcription is
  the form the laws start from.
* `{{uder|fa|ar|كَوْن}}` is the older "From the Arabic X" template — kept as
  *derived*, the relation the record is sure of (نعوظ, شجر … 251 words).

**Numbers** (published run, 2026-11-10). **516 full, 155 adjusted, 131,409
partial, 914 unexplained, 24,308 non-PIE, 70,425 IE loans** over 227,727
attested words; glossary 272,876; strict exact **6,415 / 272,876 = 2.4%** —
unchanged, because no law moved. The loan reclassification moves words out of
*partial* into *ie_loan* without touching a law (3,138 entries); the
writing-layer precedence fix moves 11 senses as listed above. Persian 13 / 18 /
5,063 / 3 / 4,083 / 1,379 over **10,559 words** (11,608 entries), Old Persian
14 / 2 / 158 / 66 / 13 / 17 over 270. The unidentified band sums to 2,053,052 —
a sum of other people's dictionary sizes, not a count of words.

## 2026-11-09 — One word per lexeme, and an estimate for what is not stored yet

**What.** Three changes that go together (2026-11-09):

1. **A spelling may carry several words, and now says so.** `pie.senses` groups
   the entries Wiktionary stores under one spelling into lexemes: entries are
   one word when they state the same ancestry chain (a shorter chain that is the
   beginning of a longer one is the same chain written more briefly) *and* the
   same etymology sentence. The noun and the verb of *bank* (one path) are one
   word; *bank* the institution and *bank* the river's edge are two. The word
   page takes `?sense=N`, draws a strip of numbered senses under the headword,
   and answers a link that names no sense with a **landing page** listing them —
   a reconstruction rung cannot say which meaning it means, so it asks. The
   glossary draws **one row per word** with a numbered subtext (1 2 …), and
   `data/category_index.json.gz` (schema 2) stores a band per sense.
2. **The counter counts words, not parts of speech.** `attested` is now one
   entry per sense (the first that is not a reconstruction), so the bands, the
   bars and the glossary rows are the same unit. Two changes move that number:
   24,116 rows were a second part of speech of a word already counted, and an
   inflected form (`form_of` / `alt_of`) is no longer a stored word at all, so
   `attested` falls 245,991 → 226,238 while the glossary as a whole grows
   266,740 → 271,207 (the 4,468 Persian and Old Persian entries outweigh the
   forms dropped).
3. **A vocabulary estimate per language, with its source.** `data/vocabulary_estimates.yaml`
   holds one figure per language for how many words it is thought to have — a
   dictionary's headword count, a floor, or an upper bound, each named and
   quoted — and the coverage page prints the grey band as
   `estimate − stored` beside the stored count, never inside a bar. Twelve of
   the 35 stages have a cited figure; fourteen candidates were looked for and
   are recorded as rejected with the reason, because no figure is invented
   here.

**Also.** `{{ety}}` (the single-line etymology template) is now read as an
ancestry chain, and a word built from named pieces counts as a word with a
recorded origin. Both together add **4,359 Persian words** to the glossary
(5,580 → 9,939 rows, every one with a Wiktionary page) and 109 to Old Persian;
2,492 of the Persian rows are Arabic borrowings that state `:bor` and were
silently dropped before. Inflected forms (`form_of` / `alt_of`) are no longer
stored as words.

**Why.** The project's rule is that one lexeme has exactly one pathway
(`docs/PROGRAMME.md`), which a page keyed by spelling could not honour: the
second word of a spelling was rendered as the first one behind an "N entries"
badge, and its band was whichever entry came first in the dump. A coverage
figure also needs a denominator: "2,006 of 5,580 Persian words are partly
explained" says nothing about Persian unless the language's own size is on the
page next to it.

**Numbers** (published run, 2026-11-09, `tools/coverage.py --docs`). Full
567 → 519, adjusted 160 → 147, partial 148,093 → 132,157, unexplained 967 → 914,
non-PIE 23,963 → 24,287, IE loans 72,241 → 68,214 over 226,238 attested words.
Part of every fall is the denominator: a word spelled two ways in one dictionary
entry is one word now. Persian: full 18 → 19, adjusted 14 → 11, partial
2,006 → 3,621, unexplained 1 → 3, non-PIE 2,721 → 4,048, IE loan 820 → 1,368,
over 9,070 words (from 5,580 before the Persian passes). Old Persian: partial
125 → 159, unexplained 107 → 66, over 270 words. The strict
exact figure (6,415 / 271,207) is unchanged, as it always is: no law moved.
The estimated-and-not-held band sums 2,054,541 across the twelve languages that
have a published figure — a sum of other people's counts, never a count of
ours.

## 2026-11-09 — The loan word's ladder, the glossary's default view, and the word's own citation mark

**What.** Four changes to the interface, none of them to a count:

1. A **non-PIE word is drawn as a normal ladder**, not a separate horizontal
   strip. The donor language is the top rung, every stage the record names
   between it and the word is a rung below it, and the row between two rungs
   states the relation the record uses (*borrowed from Arabic into Persian*,
   *derived in Persian from Middle Persian*). The contact window — 633–1100 for
   Arabic into Persian, from `data/loan_periods.yaml` — stands under the donor's
   name and its landmarks fold away beneath the ladder; the caption still says
   the dictionary dates no word.
2. The **headword carries the record mark**: a quotation mark on the title's
   top-right opens the Wiktionary entry for every word that has one, matched or
   not, and the ✓ of an exact reproduction sits *under* it. Before, the ✓ of a
   match replaced the mark, so the entry could not be opened from the word
   itself (and on a rung the two marks overlapped).
3. The **glossary opens on "PIE words"** — every headword whose band is not
   `non_pie` — with *all words* beside it; the six bands are unchanged and a
   word page still prints its own band in either view.
4. The row of "start from any recorded ancestor" chips is **removed** from the
   word page. The `starts` field stays in `/api/word` (the start is still a
   recorded form and the ladder still begins there), but the page does not
   offer the other ancestors as buttons.

**Also.** `data/language_names_extra.yaml` gives display names to codes the
descendant-tree harvest never reached (Middle Chinese `ltc`, Portuguese `pt`,
Koine Greek `grc-koi`, Yiddish `yi` …), so a rung of a loan ladder names the
language instead of printing its code. The file is display only and never
classifies anything: membership in `data/non_ie_sources.yaml` remains the one
test for "outside the family".

**Why.** The project's reading (2026-11-09): a borrowed word's timeline should be
*the same* timeline, with a foreign language where the ancestor would be; the
citation belongs to every word with a record; and a glossary of a language
should not open on the words that never came from PIE.

**Numbers.** Unchanged — full 567, adjusted 160, partial 148,093, unexplained
967, non-PIE 23,963, IE loans 72,241, strict exact 6,415 / 266,740. The
glossary's default view shows 2,431 of Persian's 4,823 headwords (2,392 non-PIE
hidden); every band, and every word page, is the same measurement as before.

## 2026-11-09 — The six coverage bands, and a backlog for records that contradict themselves

**What.** Every attested word in the corpus now carries exactly one of the six
bands the project defined: **fully explained** (dark green), **fully explained,
with adjustments** (light green, needs a report for the law and for the word
plus approval), **partially explained** (yellow, the worklist),
**unexplained** (red), **non-PIE** (dark grey) and **unidentified** (light grey,
an estimate of words the glossary does not hold). A borrowing from another IE
branch is reported beside them as `ie_loan` (blue grey) and is never green.
`src/pie/categories.py` turns the facts the counter already measured into a
verdict; `tools/coverage.py` counts every stored word, not only the ones a rule
could reach, and `docs/COVERAGE.md`, `README.md`, `docs/coverage.svg` and the
coverage page draw the six in one bar.

Separately, a dictionary entry that names an etymon the literature does not
have, contradicts its own cognate set, asserts a chain its prose hedges, or
gives a root a sense the word does not have is parked in
`data/review_backlog.yaml` and listed in `docs/REVIEW_BACKLOG.md`. Persian
باران is the worked example: ancestry `*weh₁r-` against cognate set
`ine-pro:wódr̥`. A parked word is not counted as explained and its ancestry is
not used as evidence until a human re-reads the source.

**Why.** "Exact by the sound laws" is one question and a reader asks several.
A word borrowed from Arabic, a word unexplained by any dictionary and a word
with a recorded chain the engine cannot reproduce all used to look like
failures of the same kind. More importantly, an entry can be wrong: building
a law to reproduce an etymology the record itself contradicts would make the
model fit its own noise. The backlog separates *our* miss from *the record's*
contradiction, and light green separates a documented adjustment of ours from
a derivation the literature already supports.

**Where it lives.** `src/pie/categories.py` (the taxonomy and the pure
verdict), `data/adjusted.yaml` and `reports/{laws,words}/` (approval),
`src/pie/loans.py` + `data/non_ie_sources.yaml` (outside the family),
`src/pie/dubious.py` + `tools/backlog.py` (the backlog),
`tools/coverage.py` (the counter), the coverage page and word pages (a band and
a backlog badge on each word), and `docs/PROGRAMME.md`, `docs/METHOD.md`,
`docs/UI_PLAN.md`, `docs/REVIEW.md`.

**Numbers.** A full run over the 26 attested glossaries that hold words,
**245,991 attested words**: **9,720 fully explained (3.95%)**, 0 with approved
adjustments, 139,100 partially explained, 967 unexplained, 23,963 non-PIE, and
72,241 recorded loans from a sister branch. The proto stages are measured in
the layer columns and excluded from the bands: they need their own scheme.

The strict exact figure is unchanged at **6,415 / 266,740 (2.4%)** — the bands
re-classify, they do not re-derive — and the difference between 6,415 and 9,720 is the orthographic, script and other
layer matches the bands count as full. Persian: 221 full, 1,817 partial, 2,721
non-PIE, 820 IE loans. The backlog pass found **90,698** suspect rows in
25 attested glossaries and keeps **3,900** under a per-kind cap (1,500
`cognate_conflict`, 1,200 `etymon_missing`, 800 `hedged_ancestry`, 400
`sense_mismatch`), with the omissions counted; `--check` fails when the file
drifts from the corpus.

**Open.** `adjusted` is empty until the first approved report pair exists, as
it should be. `unidentified` is not shown because no cited vocabulary estimate
has been entered in `data/vocabulary_estimates.yaml`; the mechanism is ready
and no number was invented for it. Reconstructed languages and dead languages
with incomplete dictionaries need their own scheme (recorded vs. proposed
reconstructions, words that existed but were not attested), which is the
programme's next step after the attested bands settle.

## 2026-11-09 — One lexeme, one pathway

**What.** The rule the linguistics must follow when deciding
between candidate etymologies: every word in every language has one and exactly
one true etymology pathway; several may be proposed, but only one happened. Words
that look and sound alike but mean different things are different words and may
have different pathways. A pathway that competes with a **known** pathway for
the same word, where the known one has the closer and more reasonable meaning,
is probably wrong.

**Why.** Two independent-looking derivations for one word are not two facts; at
most one is true, and treating both as "possible" inflates the model and hides
the disagreement. It also blocks the failure mode the coverage rule guards
against from the other side: a law written to give a word the nicer ancestry.

**Where it lives.** `docs/PROGRAMME.md` states it as a rule of the model;
`docs/METHOD.md` defines a pathway as a lexeme (language, headword, sense), not
as a spelling; `docs/REVIEW.md` makes it a review check — a rival known pathway
is evidence against, and homographs are not homonyms.

**Numbers.** None moved. This is a constraint on future decisions, not a change
to the data or the counter.

**Open.** The word page is addressed by `lang` + spelling, so a spelling with
several lexemes renders the first entry behind an "N entries" badge. Until the
page lists and separates homographs, no page may be read as claiming the forms
are one lexeme; `docs/UI_PLAN.md` (v1.2) carries this item.



## 2026-11-09 — One accent has two spellings, and the counter said no

**What.** The exact-derivation counter now accepts a form that differs from the
record only in how the stress is written: the dictionaries print an acute on the
vowel (*waydáyati*), the engine writes its own token before the syllable
(*waydˈayati*), and `service._same_form` has always called those one form — the
word page says *match* for them. `tools/coverage.py` compared raw strings, so
Proto-Iranian was reported as 7/338 exact while 206 of 338 are the same word,
character for character, once the two spellings of one accent are recognised.
`tools/whatif.py` now counts the same way. Nothing else is forgiven: a macron,
a length, a letter or a case still separates a form from the record, and the
strict string count is kept in `data/coverage.json` as `exact_strict` and in the
report beside the new one.

**Why.** A number that under-counts the model's own successes by a factor of 30
in the proto-stages is as wrong as one that over-counts them, and it made the
agents' rule work invisible: nine of eleven candidate laws measured "gains 0"
because the counter could not see the words they fixed.

**Numbers (full run).** exact **3,640 → 4,547** (strict 3,625 + 922 notation),
identified 108,946 → **109,317**, PIE-linked 43,501 → **43,714**, orthographic
2,147 → **2,155**, explained 5,905 → **6,764**. Per stage: Proto-Iranian 7 → 206,
Proto-Indo-Iranian 1 → 187, Proto-Germanic 8 → 87, Proto-Celtic 15 → 111,
Proto-West Germanic 567 → 670, Old English 550 → 647. Attested languages barely
move (English 607 → 636; Italian 1,057 → 1,118), which is the check that this is
notation and not leniency.


## 2026-11-09 — Persian gets a writing layer, and a word can switch a law on

**What.** `data/spelling/fa.yaml` states the conventions of New Persian writing
as 33 general laws: 22 consonant letters, ی/و for /y w/, the long vowels,
word-initial آ/ای/او, word-final -a/-e as ه, and short vowels unwritten. Each
is `tier: orthographic`, cited to Windfuhr (2009) and Sadeghi (1978), and
applies to any phonemic form — no word is named. `service.store_pathway()` now
records an `enabled` list beside `disabled`, so a word may switch a cited law
*on* (a Median outcome, a formation suffix) and `hierarchy()` can validate such
a candidate before it is stored. Two Median-reflex laws are registered for
Old Persian, both `tier: proposed`, `off_by_default: true`
(`ira-pro__peo: c_to_s_median`, `cw_to_s_median`), and 𐏀𐎴 zana- is stored
with `j_to_d` off and `j_to_z_median` on (Kent 1953 §88).

**Why.** Persian had 5,555 entries and 1,634 with a recorded ancestor but no
spelling layer at all, so the laws' Latin output was compared with Perso-Arabic
script and could never match. Middle Persian's supplement (MacKenzie via
Docling) carried no ancestry, so 616 entries had 2 measured. The Median words
were the largest single law-shaped defect among the 74 Old Persian misses, and
the measurement (this date) forbids either Median rule as a default: `c_to_s`
applied everywhere gains 𐎠𐎿 and loses 𐎰𐎼𐎭, 𐎠𐎼𐎰, 𐎧𐏁𐏂.

**Numbers.** Persian orthographic 0 → **57** (97 before the plausibility guard),
exact unchanged at 0. Middle Persian identified 2 → **61**, PIE-linked 2 → **20**,
exact 0 → **1**. Old Persian: 0 exact, 59 script, **3 pathway** (+𐏀𐎴), 510
rules / 632 examples / 0 problems, 317 tests. Corpus 3,640 / 264,489 unchanged
in the historical figure.

## 2026-11-09 — Coverage reports the record, not only the laws

**What.** Every language in `data/coverage.json` now carries `borrowed`,
`outside`, `non_ie`, `unlinked`, `no_etym` and `explained` beside the old
figures; `tools/coverage.py` classifies an entry by its own ancestry rows
(`['enm','dixionare','inherit']` names Middle English, `[':af','non-','prefix']`
names an affix and no language, `[':bor','ar:أَب','root']` names Arabic). The
coverage page draws two stacked bars per language — what the record says
(inherited / borrowed / other source / none) and what the model explains
(laws / pathway / orthography / script / open) — and a word completed by a
pathway that lands in another script counts as a pathway, not as a silent miss.

**Why.** A borrowed word shown beside a reconstructed one invited the reader to
read the second figure as a failure of the model. They are different claims:
Arabic loans in Persian and Latin loans in English are not supposed to be
derived from PIE, and the page now says so. `explained` is a union, never a sum
of overlapping counts.

**Numbers.** Corpus: 264,489 entries, 108,946 inherited, 85,711 borrowed,
38,651 another source, 22,892 unlinked, 1,646 with nothing recorded; 3,640
exact, 2,204 spelled, 59 through a script, 5,905 explained in all layers.

## 2026-11-09 — A compound is drawn as a join

**What.** `service._compound_pieces()` reads the entry's own "From X + Y",
"Compound of", "Blend of", "Equivalent to" sentence, keeps a piece only when
the same language's glossary records it as a headword, refuses a sentence that
names another language first ("From Latin focus + -alis" is a Latin formation),
and returns each piece's recorded chain oldest first. The word page prints the
pieces as parallel timelines that meet at the headword (`renderJoin`).

**Why.** astronaut is astro- + -naut and blackbird is black + bird: two origins
that meet in one word. The ladder drew only the headword's chain, so a join
looked like one etymon explaining everything. A join is a formation, not a
sound law; it is printed as the dictionary states it and counted nowhere.

**Numbers.** None: no rule, spelling file or lexicon changed. Five tests
(`tests/test_web.py::TestJoins`) and a render case.

## 2026-11-08 — 110 Old Persian words enter the glossary with their own cuneiform

**What.** `data/lexicon/_supplement/peo.jsonl.gz` gains 110 entries read from
the live English Wiktionary Old Persian categories (the read-only API the repo
already used, no account and no edit): each row records the cuneiform headword
as the page prints it, the sign-by-sign transliteration, the reading the entry
records, a part of speech, its glosses, a `ref` sentence and the exact URL.
Thirty-one rows are also checked against Kent (1953), whose lexicon is cited by
entry (`s.v.`); two rows carry the ancestry the source states (𐎭𐎭𐎠𐎬𐎢𐎺,
𐎲𐎼𐎫𐎡𐎹). The curated input is
`data/lexicon/_supplement/peo_entries.json`; `tools/ingest_op_entries.py`
fetches a candidate snapshot, verifies the curated rows against the live pages
and writes the supplement idempotently, preserving every hand-written row.
`data/sources.yaml` now gives Kent (1953) the archive.org address of the text
that was read.

**Why.** Old Persian had 265 glossary rows, most of them cuneiform lemmas from
an older Wiktionary dump; 100 more verified words were asked for, with 𐏃𐎢𐎺
(*hauv*) as the model. The new rows spread over royal names and toponyms
(𐎭𐎠𐎼𐎹𐎺𐎢𐏁, 𐎧𐏁𐎹𐎠𐎼𐏁𐎠, 𐎲𐎠𐎧𐎫𐎼𐎡𐏁, 𐎣𐎫𐎱𐎬𐎢𐎣), nouns
(𐎠𐎱𐎭𐎠𐎴, 𐎠𐎿𐎴, 𐎣𐎼𐏁), adjectives (𐎯𐎽𐎧𐎫, 𐎭𐎼𐎢𐎩𐎴,
𐏃𐎧𐎠𐎶𐎴𐎡𐏁𐎡𐎹), verbs (𐎠𐏃𐎷𐎹, 𐎲𐎼𐎫𐎡𐎹, 𐎭𐎭𐎠𐎬𐎢𐎺),
pronouns (𐎠𐎡𐎫, 𐏃𐎢𐎺, 𐏃𐎹𐎠) and a preposition (𐎼𐎠𐎮𐎡𐎹).

**Rules applied.** A cuneiform word is written only when a source prints it;
the reading is the one the entry records (`hauv`, `Dārayavaʰuš`), never a
reading derived from the letters. The sign transliteration follows
Wiktionary's Module:peo-translit and adds no vowel the syllabary does not
write. Letters of the script, number signs, reconstructed (starred) words,
multi-word phrases, inflection-only pages and alternative-form pages that
only point at another entry were not admitted. Overlap was checked on the
cuneiform word and on the normalised reading: four otherwise-new pages
(𐎧𐏁𐎠𐎹𐎰𐎡𐎹, 𐎲𐎥, 𐎶𐎦𐎢𐏁, 𐎿𐎣) were dropped because
the glossary already records that reading. A row from Kent alone was not
added: the OCR edition prints the lexicon in transliteration, and without a
printed cuneiform form it would not meet the bar the new rows are held to.

**Numbers.** Old Persian 265 → 375 entries, 219 with a recorded ancestor and
133 tested; the corpus 264,379 → 264,489, identified 108,944 → 108,946.
Exact derivations stay 3,640 (Old Persian exact stays 0: the syllabary and the
last mile are still not laws), the orthographic layer stays 2,147, the script
column stays 51, and `check-rules` stays 507/583/0. 268 tests pass.

## 2026-11-08 — the counterfactual table leaves the word page

**What.** "If the rules ran everywhere" — the etymon predicted into every
modelled language — is removed from the word page and from the cognate page.
The renderer (`renderRebuilds`, `rebuildStatus`, `rebuildForm`, the focus-card
grid, the collapsible table, the gap list) and its `.rb-*` CSS are deleted. The
data is untouched: `service.word()` still returns `rebuilds` (a PIE root page
reads its rows for the *reconstruct into* selector), `/api/rebuild` and
`pie rebuild` still work, and the rule that a rebuild is only a *reproduction*
when it equals a form recorded for that etymon still governs every place one is
shown. A word page now reads: the ladder, the branch below the stage, what is
built on the word, the cognates.

**Why.** The section was to be removed entirely. The ladder
already answers "what do the laws do on the way to this word"; a table of
predictions in twenty languages around it was noise, and most of its rows were
this repo's own reconstructions rather than evidence.

**Numbers.** None moved (3,616 / 264,379 exact, `check-rules` 491/567/0). 249
tests: the render tests for the deleted table are gone, and a new test pins the
removal so it cannot creep back.

## 2026-11-08 — the laws take their place in the gap, and a record is a quotation

**What (the timeline).** The law row of a step already came before its rung in
the markup, but it *looked* like a footnote to the word above: the row sat 4 px
under that word and the whole inter-rung space (14 px, or up to 88 px on the
dated ladder) fell below it. Now the space is shared — `stepGap()` gives the law
row the first half of the transition's gap and the rung it produced the second
half — and the rule under the word above is dropped when a law row follows
(`.rung:has(+ .lawstep) .rung-body`), because that rule is the bottom edge of
the word above and pulled the chips up to it. That rung's 16 px of bottom
padding went with the rule: it is part of the distance the eye measures from
the word above, while the rung below contributed only its own 4 px, so the row
sat high in the gap. The rail stays continuous through the row: the step's own
rail reaches up by its share of the gap and the next rung's reaches up by the
rest. Measured on Persian بازو's ladder, the first step now stands 14 px under
the word above and 15 px over the word below (it was 26 / 15), and the widest
step 49 / 54 (it was 61 / 54).

**What (the mark).** The record glyph is a **quotation mark** (`“`, 20 px in a
15 px badge) instead of an open book, and the tooltip no longer ends "Open where
it was recorded." — the mark is visibly a link, and every recorded word was
paying for the sentence. A page glyph read as a copy button, a book still read
as "a book"; a quotation mark says the only thing a record is — a form quoted
from a written source — and it survives at badge size, where drawn icons turn to
mush (checked at real size: a 15 px badge reads as quotation marks, not as two
chain links).

**Why.** On the timeline the laws still appeared to belong to
the word above rather than to the step, and asked for the record mark to be
changed again, without the click instruction in its tooltip.

**Numbers.** None moved: no rule, form or coverage figure is touched
(3,616 / 264,379 exact, `check-rules` 491/567/0). UI tests cover the shared gap,
the dropped rule, the quotation mark and the shortened tooltip.

## 2026-11-08 — a word cut from a named stem shows that stem as its construction

**What.** `service._from_stem_construction()` reads the one remaining way an
entry states a formation — "From the stem *delh₁gʰ- (“to be long”)", dl̥h₁gʰós —
by printing the stem the entry names plus the ending the headword itself
carries (`delh₁gʰ-` + `-ós`). Two checks keep it honest: the base must already be
a starred ancestor of the entry, and the word must actually contain the stem
(with a known ending after it). Only dl̥h₁gʰós matches in the stage. The stem
became a root entry through `tools/add_roots.py`, so the base is a door and its
page lists dl̥h₁gʰós under what is built on it. The construction panel is called
**construction(s)** whether or not the entry states one (it was *add a suffix*).

**Why.** dl̥h₁gʰós showed the stem the entry names
nowhere; the panel that should hold constructions was named after its button.

**Counts.** 515 → 516 PIE entries state a construction (527 → 529 rows); PIE
root entries 31 → 32. No rule, form or coverage figure moved (3,616 of 264,379
exact, `check-rules` 491/567/0).

## 2026-11-08 — a law stands between the two forms it changed, and Iranian gets its laryngeals

**What (the timeline).** A step's law chips left the rung body and became a row
of the ladder of their own, so they sit on the rail *between* the form they were
run on and the form they produced — above the rung, never under it. A word's
ladder and an etymon's reconstruction both read the same way: form, laws, form.
A stage reached by carrying the timeline on has a **change** button under its
language name (the old *cut here* beside the form). The record mark is an open
book rather than a page glyph, which read as a copy button, and the rung no
longer explains in words that the record stands beside the form the laws
produced.

**What (the laws).** Wikipedia's Proto-Iranian "Development into Old Iranian"
section and the Proto-Indo-Iranian correspondence table were read against what
was registered (2026-11-08). Four things were missing or
wrong:

- `ira-pro__peo:laryngeal_lengthening` and `ira-pro__ave:laryngeal_lengthening`
  (established). Proto-Iranian keeps the Indo-Iranian laryngeal (*bráHtā,
  *baHjúš); Old Iranian loses it and lengthens a short vowel before it — OP
  brātā-, bāzu-, Av. brātar-, bāzu- — while after a long vowel or a consonant it
  simply goes. This was the missing step behind every Old Persian word with a
  laryngeal.
- `iir-pro__ira-pro:ts_to_c` (established): PII *ts merges with *c
  (*matsya- > PIr *macya-). It runs before *s > *h, which had been taking the
  *s of the cluster for the later sibilant.
- `ira-pro__peo:j_to_z_median` (proposed, **switched off by default**): PIr
  *j [dz] > OP z, the Northwest Iranian/Median outcome. It contradicts the
  regular `j_to_d` (OP dasta-, dānu-), so that one stays the default and this
  one is registered for the words Old Persian took from Median. Recording both
  is the point; only one can be on.
- The satem rules now say what the affricates are — *ć [tɕ], *ȷ́ [dź], *ȷ́ʰ
  [dźʰ], the stage Nuristani keeps — instead of leaving them as bare letters.
  Avestan's *c > *s now states that it is younger than *s > *h.

**Also.** 𐎲𐎠𐏀𐎢 (bāzu, "arm") is an Old Persian glossary entry, with the
reading *bāzu* the Persian etymology gives it and its own chain (Old Median
*bāzuš ← PIr *baHjúš ← PII *bʰaHȷ́ʰúš ← PIE *bʰeh₂ǵʰús). Persian بازو's Old
Persian rung now derives *bāzúš — it used to be *bādúš. The dictionary
lemmatises the u-stem, so the nominative *-uš is the one letter that still
differs, and the entry's own citation says so on hover; nothing is bent to hide
it.

**Counts.** The strict reconstruction figure is unchanged — 3,616 of 264,379
(1.4%) — because a language written in its own script is compared sign by sign
and has a column of its own: that column rose **39 → 51**, the Old Persian words
whose derived form is a reading of the cuneiform the dictionary writes. Forms
inside Wiktionary's `Reconstruction:` namespace rose 28 → 29. Identified words
rose 108,942 → 108,944 (the new headword). On the word-page read model, 26 of
the 132 Old Persian entries whose data mention a laryngeal now reproduce their
recorded ancestor exactly, against 15 before. `check-rules` 487 → **491** rules /
563 → **567** examples / 0 problems; 247 tests.

## 2026-11-08 — a root the entry only suggests is still shown as its construction

**What.** `service._root_constructions()` reads a hedged derivation that names
only a base — "possibly nominalized from root *h₂retḱ-" (h₂ŕ̥tḱos), "perhaps from
a root *mer-" (móri) — and the row prints that base, `argued`, with the
entry's own gloss on hover. A word the entry calls a *nominalization* also wears
the stem-formative its own ending carries (h₂ŕ̥tḱos → `h₂retḱ-` + `-o-`), the
same way a named stem class does; a root the entry *enlarges* in prose takes
that suffix (sterbʰ- → `dʰer-` + `-bʰ`). The bare "from *X" form is read only
when X is a root headword of the stage, so an adverb placed by an adjunct
("ní, possibly from *h₁én") or a pre-form ("from earlier *méh₁n̥s-s") is not
turned into a formation, and a derivation introduced through another headword
("the synonym *káp-ōl, which likewise may be from *kap-") stays with that word.

**Why.** h₂ŕ̥tḱos was to show its possible construction the way
the rivals are shown — a base and the pieces it carries, labelled with how sure
the entry is — and for a couple of other words to follow.

**Also.** Two parser holes surfaced while measuring this. Parentheses and
semicolons inside a gloss ("*men- (“to think; mind”) + *-os") used to cut the
sentence in half: `_sentences()` now counts parentheses, so **35** more entries
state the arithmetic they always had (ménos, ǵénh₁tōr, pósti, h₁léwdʰeros …);
and a gloss with one level of nesting ("*wers- (“to rise (up)”) + *-ḗn") is
read by `_ARITHMETIC_RE`, adding **3** (wérsēn, ǵʰmṓ, deḱs(i)wós). `_base_row`
no longer keeps the quotation marks the entry writes around a gloss, which the
page then quoted a second time.

**Counts.** 515 PIE entries state a construction (527 rows: 457 stated, 70
argued), up from 457/468; 20 of the rows are root derivations, 11 entries state
more than one. No
rule, form or coverage figure moved (3,616 exact, `check-rules` 487/563/0);
243 tests.

## 2026-11-08 — an edit keeps its ancestors, and the timeline says less

**What.** `service.hierarchy(from_stage=, from_form=)` now splices the typed form
into **its own rung** and re-derives only the stages below it; the rungs above
stay the laws' own work, and `start` moves upward only for a stage above the
ladder's start. `store_pathway` slices the stored `levels` from the edited rung,
so a pathway still begins where the reader typed. In the front end the chips
that qualify a chain (verdict, *recorded pathway*, *laws unfiltered*, *edited
start*, *pathway stored*, *another suffix*, the switched-off count) moved from
bars under the heading onto the right of the heading line
(`.ladder-badges` / `.recon-badges`); the "apply the law anyway" button is gone
(a switched-off law's own switch is the control); the reconstruction's summary
line ("N laws fired between … . Tiers used: …") and the "a different form is
recorded at this stage" sentence are gone; a step reads `N of M applicable laws
applied` (a switched-off law is not applicable); and no `Source:` line is
printed under the word or a rung — `recordSourceText()` carries the citation in
the tooltip of the record badge, the matched form and the headword's evidence
badge.

**Why.** A rung edited on `#/word/en/wolf` and the timeline lost the
ancestors above it — the edit was being read as a new starting point. He also
asked for the timeline to stop narrating what the colours and the law chips
already show, and for the state chips to sit on the heading rather than in a
stack of bars.

**Cost.** None in the model: no rule, no form and no coverage figure moved
(3,616 exact, `check-rules` 487/563/0). `hierarchy`'s `start`/`start_form` no
longer name the edited rung, so anything reading them must take `edited`
instead (`store_pathway` and `stored_pathway` do).

## 2026-11-08 — every rung of a reconstruction is a rung you can type on

**What.** `service.reconstruct()` takes `from_stage`/`from_form` (the
`?from=gem-pro&edit=wulfaz` pair) and derives the timeline in two parts: the
rungs above the edit from the etymon exactly as before, and everything below
from the typed form. The edited stage is a rung of its own with no fired law,
marked `edited`; the page offers `reset to the laws' form`. The carry-on box
lost its heading and its explanation: the timeline's rail now runs into a box
that holds only the direct children, one tile each, and the box moves down when
a rung is added.

**Why.** The reconstructed words in
`#/word/ine-pro/wĺ̥kʷos?into=en` could not be edited — the timeline was a report
with no controls — and called `Carry X on · 1 direct descendant` plus its
paragraph too verbose for what is one obvious next step.

**Cost.** One more pair of state fields in the reconstruction payload and one
CSS junction. The rungs above an edit are still the laws' work, so the edit never
rewrites history; the text of the page says so before the ladder.

## 2026-11-08 — the construction is a panel, and the composed word belongs to it

**What.** The construction under a PIE headword is drawn as a bordered panel —
label on its own line with a hairline to the edge, the base and its suffixes
inside, rival analyses under a dashed rule in the muted ink — and the
composed-form line moved inside it: it is the panel's last line, hidden until a
suffix is chosen, with only its label in small caps. A stage the entry states
nothing about keeps the heading and the `(+)` but not the panel.

**Why.** The block read as a floating label over two words
("the CONSTRUCTION section needs to look better, especially the word
CONSTRUCTION itself is misplaced"), and the composed form sat below the header
as a separate line that could be read as part of the etymology. The box now
means one thing: the entry states this formation. Nothing stated → no box.

**Cost.** Only CSS and the renderer; no model change. The suffix picker still
opens from the panel, and the composed line is repainted with it, so the two
cannot drift.

## 2026-11-08 — a law is a switch on an etymon too, and a stem class is a construction

**What.** `service.reconstruct()` takes the laws a reader has switched off
(`disabled`), passes them to `derive_detailed`, and each level returns
`switched_off` plus the fired *and* disabled laws with what they would have
done; the endpoint forwards `off=` and the payload carries it back, so the PIE
etymon page has the same switches, URL state and one-button reset as a word's
own ladder (`?off=ine-pro~gem-pro:grimm_t`). `construction()` now falls back to
a prose reading when the etymology states a stem class instead of arithmetic —
*an i-stem noun built on the root \*h₂wl̥p-* becomes base `h₂wl̥p-` + `-i-` —
and the row's label is a heading on its own line, so it cannot read as a word
glued to the base. An etymon with nothing stated offers *add a suffix* instead
of calling itself a construction, and the empty composed-form line is hidden
rather than shown greyed.

**Why.** A law could not be switched off on
`#/word/ine-pro/nókʷts?into=en` (the switches existed only on word ladders),
h₂wl̥pís showed no construction although its own sentence names the root and the
stem class, and the row read as `construction h₂wl̥p-` in one line. Half-stated
constructions are worse than none: a stem-formative carries no cited suffix id,
so it is printed with its reading and is never offered as a swappable law.

**Also: one word may state several constructions.** `service.constructions()`
returns every analysis an entry states, the one it wears first, each with a
`confidence` — `stated` (the entry presents it plainly), `argued` (a named
author argues it, or the entry hedges: "presumed either …", "possibly from")
or `proposed` (this repo's own; none stored yet) — and the sentence it was read
from. The reader takes every `*base + *suffix` in an etymology, not only one
anchored at the start, so a base glossed in parentheses (`*ǵʰew- (“pour”) +
*-tós`) no longer hides the arithmetic; a later arithmetic is a rival only when
the entry says so (`or`, "other possibilities", "Pokorny suggests"), and a
sentence about a *related* form ("the reanalysed root of *ḱléyti, from …", "the
genitive of *swóp-r̥, from …", "the feminine is from …") is skipped rather than
printed under this headword. Rivals the prose cannot express as arithmetic are
recorded in `data/constructions/<lang>.yaml` with their quote and author
(Kloekhorst's `dʰeǵ-` for dʰéǵʰōm, Pooth's `negʷ-` for nókʷts). The page shows
the rivals under the primary row, read-only, labelled *also argued by …* with
the quote on hover; a hedged primary is labelled *construction argued* instead
of claiming the entry states it. Counts: 457 PIE entries state a
construction (468 rows: 423 stated, 45 argued), 10 of them more than one.

**What it does not do.** The reader is a sentence reader, not a parser: a
construction stated only as a cross-reference ("variant of X") or as a related
form's formation is still absent, and a rival cannot yet be chosen as the one
to *compose* with: the word wears one, and the others are shown as evidence.
Both are open.

## 2026-11-08 — the record is a second word, and its badge is its citation

**What.** On a rung that records a word, the record now stands *under* the
form the laws produced, with a small **RECORDED** badge beneath it; the badge
is a link to where the word was read — the source's own link when the
supplement has one, otherwise the entry's Wiktionary page. The read model
resolves that page (`_wiktionary_entry_url`: `Reconstruction:<language>/<word>`
for a reconstructed form, the headword itself for an attested one) and puts it
on the source row as `entry`, so the front end only prints an address it was
given. The edit affordance is a pencil icon, and it sits immediately after the
reconstructed form. The visible words *starting point* and *nothing recorded at
this stage* are gone: the first was obvious, the second is already what the
form's hover text says.

**Why.** The rung read as a single line whose tag described the
reconstructed form; with the tag between the two words it was not clear which
form an edit changed, and the citation could not be followed. Provenance is a
claim about the record, so it belongs to the record.

**The number.** None: this is presentation and provenance, not derivation.
Coverage, coverage counts and `check-rules` are untouched (487 rules / 563
examples / 0 problems); 218 tests and the Node render test are green.

## 2026-11-08 — a script states a form the laws produced

**What.** `data/script/peo.yaml` holds the Old Persian syllabary (34 signs:
vowels, consonant+vowel signs and the word divider, plus the logograms) with
Kent (1953) as the source, and `src/pie/script.py` turns a form into the
sequence of signs a monument would write (`𐎺𐎼𐎣` → `va-ra-ka`) and compares a
recorded headword with a reading the laws produce — allowing the vowels a
syllabary does not write, a filler vowel, *a* for syllabic resonants, /au/
written a+u, **v ≡ w**, and a final /h/ that has no sign at all. A rung whose
record says *wˈarkah* against 𐎺𐎼𐎣 now matches, with `fit.translit` beside it.

**Why.** *wárkah*, recorded as 𐎺𐎼𐎣, showed red. It was: the
laws produced `wˈarkah` and the glossary wrote `𐎺𐎼𐎣`, and a string comparison
of the two could never succeed. A script is a statement about the form, and the
syllabary is cited, so the reading is checkable — but it is a **reading**, not
the same string.

**The number.** It is reported as its own column, `through its script`, 39
words, all Old Persian, and is never added to the attested figure, which stays
**3,616 / 264,377**. The colour rule does not change either: green is still
only a cuneiform headword with its source; what changed is that the fit can be
checked and printed. All 151 Old Persian entries with a romanisation are
explained by the table (0 failures).

## 2026-11-08 — the timeline can be carried past the word, and every rung edits

**What.** `service.hierarchy(..., path=[...])` appends direct-child stages to
the word's own ladder (validated against `data.languages()[...]["ancestor"]`),
`word()`/`hierarchy()` return `next` — the target language's direct children,
each with the default form the laws produce, its era and whether it hits a
record — and every rung is editable in place, not only the ones above the word
(`from_stage` at or above the word's start replaces the start form; a rung in
`path` is spliced and the rest re-derived below it).

**Why.** Only PIE words could be reconstructed anywhere. Old Persian has two
daughters in the model (Middle Persian, then Persian) and the reader wants to
walk that line from any word, with the next step offered as a button instead
of a menu hunt. Editing a carried-on rung is the same right: a hypothesis is a
hypothesis wherever it sits.

**The number.** None: no rule changed, `check-rules` 487/563/0, exact 3,616
unchanged.

## 2026-11-08 — the construction under the title

**What.** The etymology `From *wĺ̥kʷos + *-íh₂s.` is parsed into
`word()["construction"]` (a base, one or more suffixes, the base's page when
the glossary holds it) and printed under the headword: base, `+`, suffix in the
accent colour, `(+)`. Clicking the suffix offers another cited suffix of the
stage; `(+)` attaches one to the word as it stands. The old "as it stands" chip
row beside the title is gone.

**Why.** The grammar of a recorded PIE word belongs in the
interface, not only on an etymon he had composed himself, and to be able to
change it there. A construction is what the dictionary says; the menu only
offers the suffixes the stage actually cites, and a composed form says whether
a registered formation law built it or this repo glued it by hand.

**The number.** None: no new word, no new rule. 74 PIE entries have a stated
construction, 62 of their bases are in the glossary.

## 2026-11-08 — a Reconstruction: entry is not an attested word

**What.** The lexicon build carries Wiktionary's reconstruction flag
(`recon`), set for every entry the dump keeps in its `Reconstruction:`
namespace (sense tag `reconstruction` or a `*` headword) and backfilled on the
built glossaries by `build_lexicons.py --mark-reconstructions`: 664 rows in 16
attested languages — Old English 278, Latin 104, Old Persian 97, Gothic 85,
Middle English 5, Sanskrit 5, Tocharian B 13, …; the proto-language rows need
no flag, since every proto form is gold already. Such a row is gold, its word
page says *reconstruction* and no longer calls a Latin-script Old Persian
reconstruction a "transliteration only", and the coverage figure keeps it out
of the attested count: **3,644 → 3,616 exact**, with the 28 reconstruction rows
the laws do reproduce counted apart (out of 559 reconstruction entries with a
recorded ancestor). The audit skips them too, so they cannot become worklist
tasks.

**Why.** Where the Old Persian script and source for a green
`wā́dar` were. The rung was fixed by colouring rungs from the record, but the
same lie sat in the data: Old Persian *madu*, Latin *alba*, Old English
*beġ* are reconstructions on Wiktionary and were stored and coloured as
attested words. Every one of the 237 Latin-titled Old Persian entries in the
dump is a reconstruction — the script test alone could not tell them from a
transliteration of a cuneiform word.

**Cost.** `recon` must reach the builder on every rebuild, or the flag silently
disappears; the backfill pass exists to patch a glossary without re-reading
7.8 GB of Wiktextract. Coverage's `identified` still counts those rows (they do
have a recorded ancestor), while `tested` does not, so the two denominators now
differ by the 559 flaggable rows and the report says which number is which.

## 2026-11-08 — a rung's colour is a claim about its form, not its language

**What.** The PIE reconstruction ladder now colours every intermediate rung by
what is recorded: an exact record (green for a written headword, gold for a
reconstruction or an Old Persian transliteration) or this repo's reconstruction
(orange when every fired law is established, red when a proposed one is on the
path). Each rung carries its record beside the produced form, with the record's
script, reading and citation. Old Persian green is reserved for cuneiform
headwords: a Latin-only entry is gold and says "no cuneiform spelling recorded".
Every rung — recorded or not — is a link to its own word page, and an unrecorded
one opens the existing "not recorded here" page.

**Why.** Opening `#/word/ine-pro/h₂wl̥pís?into=fa`: the Old Persian rung
*warpˈiš* glowed green although nothing records it, and it was a dead end. The
old renderer chose the colour from `kind_of(stage)` — whether the *language* is
attested — which turns every law output in a documented language into an
attested word. The same mistake could dress a Latin transliteration as a
cuneiform headword, and a green form had no visible source.

**Numbers.** None: this changes presentation and record lookup, not the rule
engine or coverage. Four regression tests cover an unrecorded rung, its ghost
page, an OP record's script/source, and the absence of Latin-only green OP
rungs; the Node render test checks the links and the v/w explanation.

## 2026-11-08 — suffixes on the way down, and a script headword is not a wall

**What.** Three things from a second reading of the گربه page.

1. **Intermediary stages have morphology.** `data/morphology/iir-pro.yaml` holds
   Proto-Indo-Iranian *-nás* (Wiktionary, Reconstruction:Proto-Iranian/-nah:
   "Inherited from Proto-Indo-Iranian *-nás, from Proto-Indo-European *-nós"),
   naming the registered formation law `iir-pro~ira-pro:suffix_nah`. The law adds
   the PII morpheme (*daywˈas > daywˈanas) and lets the established *-Vs > *-Vh
   change give *-nah, so the suffix is cited once and its surface form is a
   statement in the morphology record (`surface: "-nah"`), which is what the
   ladder highlights.
2. **The suffix is visible and changeable in the timeline.** The rung a
   formation law fires on carries a `formation` block: the suffix, its surface,
   and the other cited suffixes registered for that stage. A reader clicks one
   and the page re-derives with it (`?suffix=<id>`); the payload then says
   `hypothesis` — the ladder starts from the recorded base plus the chosen
   morpheme — and the page states in a bar that this is not the word as
   recorded. دیوانه now climbs from PIE *deywós → PII *daywás → PIr *daywánah
   with *-nah marked, because its record (Wiktionary) is *daywá- plus *-nah.
3. **A script headword no longer stops the chain.** `_phonological_form()`
   runs the laws on the reading a glossary records for a headword written in
   another script (Middle Persian 𐫅𐫏𐫇 *dēw*, Old Persian 𐎭𐎡𐎺 *daivaʰ*), and
   an entry may state that form outright with a `phon` field. Before this, the
   ladder ended at the Arameogram and the Persian word above it could not be
   derived from it.

**Why.** "add possible suffixes for these intermediary languages as
well … at least the suffix is highlighted with a different colour", and
"Arameograms can have romanization so the engine still works with them".

**Not done, deliberately.** Middle Persian 𐫅𐫏𐫇 and Old Persian 𐎭𐎡𐎺 now climb,
but the Old Persian rung says *differs* because the laws write *w* and the
transcription writes *v* (one sign, 𐎺). Making that a match needs a *w > v* law
and its *v > MP w* counterpart; measured across the Persian corpus (proposals/009)
the pair costs four words and gains one, so it stays out and the rung explains
the letter instead (`notation: "v/w"`). دیوانه's last mile (MP -ag, -āna) is
likewise not modelled yet — its ladder ends `dēwan` against `dēwāna`, and the
worklist says so.

**Numbers.** Corpus 264,376 → 264,377 (دیوانه); exact **3,644 unchanged**
(formation laws are off by default, so they cannot move it); identified
108,940 → 108,942. Gates: 194 tests, 487 rules / 563 examples / 0, Node render.

## 2026-11-08 — a suffix is a law, and گربه climbs from PIE

**What.** Three things follow a reading of the گربه page.

1. **A formation is a registered law that is off by default.** `-ka-` is now
   `ine-pro__iir-pro:animal_ka` (tier `formation`, `off_by_default: true`): it
   replaces the etymon's stem-final *-ís with *-aka- (*h₂wl̥pís > *h₂wl̥paka),
   citing de Vaan (2000) and Wiktionary. `data/rules` therefore has a rule kind
   that may add a morpheme — and the engine refuses to run it for any word that
   does not ask. A pathway may now **enable** a law (`enabled` in
   `data/pathways.jsonl`), not only disable one; `apply_ruleset_verbose`
   receives `enabled`, and `ancestor_starts(keep_formed=True)` stops skipping
   the ancestor the dictionary calls a formation when its law is present. The
   گربه pathway turns `animal_ka` on, so its ladder is
   *h₂wl̥pís → … → gurbag → gorbe*, the formation appears as a chip with a
   switch, and switching it off keeps the PIE start and shows what the word
   would be without the suffix.
2. **The etymon is in the PIE glossary.** Wiktionary enters only the root
   *h₂wl̥p-; the noun *h₂wl̥pís* that گربه quotes is now a cited supplement entry
   (`data/lexicon/_supplement/ine-pro.jsonl.gz`) with its own page and sources.
3. **The PIE page composes with the same law.** `data/morphology/ine-pro.yaml`
   gains `ka-animal`, whose `rule:` names the formation law, so choosing it runs
   the registered rule instead of gluing a morpheme on by hand; the resulting
   ladder reaches گربه and quotes it as the record.

**Why.** The suffix was to appear *in* the hierarchy rather than
as a note explaining why the ladder starts low, and for a suffix to be a law
that is disabled by default and enabled by the words that use it. Both are now
the same mechanism the wolf's pathway already used, in the opposite direction.

**Numbers.** None moved: the formation is off for every word that does not
enable it, so exact stays 3,644 / 264,376 and the orthographic layer 2,186.
گربه is exact *through its reading*, which is a per-page claim and not part of
the published coverage figure (Persian is compared by lemma).

## 2026-11-08 — the animal suffix *-āćá-, and a formation is not a derivation

**What.** de Vaan (2000) on the Indo-Iranian animal suffix *-āćá- is now the
source of record for the Persian animal names, and six items follow from it.
(1) The Persian supplement records گربه *gorbe* 'cat' (PIr *wr̥pa-ka-, MP gwlbk
*gurbag*) with an explicit `formed` statement: it is PIE *h₂wl̥pís 'wildcat,
marten' plus the animal suffix *-ka- (de Vaan §13), so the ladder begins at
Proto-Iranian and quotes the PIE etymon instead of pretending a law added a
syllable. (2) روباه *rūbāh* 'fox' gains its recorded Middle Persian link
(lwpʾh *rōbāh*) and the Iranian reading recorded by the Persian Wiktionary
([ruːˈbɒːh] beside [roːˈbɒːh]). (3) `peo__pal.yaml`: `rp_to_rb` (proposed) and
`athetah_to_ah` (proposed, OP final *-āθah > MP -āh) replace the earlier
`theta_to_h`; `final_h_loss` is narrowed to a short vowel, because -āh survives.
(4) `ira-pro__peo.yaml`: `laryngeal_loss_initial` and `aw_to_au` (the second
only in a closed syllable — PIr *náwah 'new' keeps its glide, OP nava-).
(5) `pal__fa.yaml`: `final_ag_to_e` (MP -ag > NP -e, gurbag > gorbe).
(6) `data/morphology/ine-pro.yaml` is new: nine cited PIE derivational suffixes
with their glosses, sources and attachment behaviour, so the PIE word page can
compose a real form before the laws carry it down.

**Why.** The paper is the first source here that explains a Persian animal name
by *formation* rather than by sound change, and the engine had no way to say
that: it either dropped the word or invented the suffix. Two of the paper's four
*-āćá- words (fox, cat) are now derivable; kargās 'vulture' and karbāš 'lizard'
need their Pahlavi spellings verified against MacKenzie before they enter.

**Numbers.** Corpus 264,371 → 264,376; exact 3,644 unchanged in the published
measure (Persian counts through its reading on its own page, which is a
measurement decision still open). Measured directly on the ladders: Old Persian
27 → 37 of 222, Persian 62 → 71 of 1,692. Gates: 484 rules / 560 examples / 0
problems; 180 tests + Node render.

## 2026-11-08 — Persian گرگ joins the wolf, and a rung may match its reading

**What.** (1) `data/rules/peo__pal.yaml` gains four `proposed` laws for the
Iranian wolf: `war_rounding` (*waR- > *wuR-), `w_to_g_before_ur` (initial *w- >
MP g- before *ur), `rk_to_rg` and `rt_to_rd` (a stop is voiced after *r).
(2) `data/rules/ine-pro__iir-pro.yaml` gains `syllabic_l_to_r` at the
Proto-Indo-Iranian transition, where the l/r merger belongs, and the two carrier
rules it makes unreachable are removed from the child transitions (no recorded
Proto-Indo-Iranian, Proto-Iranian or Indic headword contains *l̥). (3) The Persian supplement
gains گرگ (gorg) with its ancestry, its sources and its etymology.
(4) A rung of the ladder now compares its record with the record's own
**reading**: Pahlavi `gwlg` is the word MacKenzie reads *gurg*, the laws produce
*gurg*, and the rung matches — saying through which reading.

**Why.** (2026-11-08) *"for the Persian word گرگ (wolf) it should
similarly descend from that PIE word and also there was a 'proposed' rule that
change initial w + vowel to gu- (check the project's rules for that)."* The chain
used to run *wĺ̥kʷos → … → OP wˈarkah → MP wˈark → NP **bark***: past Old Persian
it took the ordinary *w- > b- of *wād*, which is not what this word did.
Middle Persian *gurg* is one of the etyma in which initial *u̯- went to g-
(Cathcart 2015, quoting Schwartz 1982: *u̯r̥ka- > MP gurg 'wolf' beside *u̯r̥tka-
> gurdag 'kidney', *u̯r̥paka- > gurba 'cat', while *u̯āta- keeps w-). The
environment registered is the one the sources show, and every one of these laws
is `proposed`: the correspondence is diffused over a handful of etyma, not a
regular change.

**Cost.** Four new `proposed` laws, so the Iranian chain leans on them and the
reports must say so. Persian پرت /part/, which keeps -rt-, records a pathway
that switches `rt_to_rd` off for that word — the record beats the theory, and
the exception is visible rather than silent. Old Persian still prints *w-* where
the sources write 𐎺 *v-*: a notation law there would need *v- > MP w- for the
wind, which is proposal 009, not a patch to this one.

**Numbers.** Corpus 264,371 → **264,372** (the one cited entry); exact
**unchanged at 3,644** (a proposed law may not turn a form into a lemma by
itself); identified 108,938 → 108,939; PIE-linked 43,494 → 43,495; near
22,403 → 22,408. Persian word pages now read exact for گرگ *gorg*, مرد *mard*
and گرس *gors*, and the ladder for the wolf is clean from Proto-Indo-European to
the Persian record. `check-rules` 476 → **479** rules / 551 → **554** examples /
0 problems; suite 175 → **180** tests.

## 2026-11-08 — a word may record that a law never applied to it, and a law opens

**What.** (1) `data/pathways.jsonl` gains a *default* pathway: a record that
applies every time a word's page opens, saying which registered laws never
applied to that word, why, and on which sources. `service.word` merges its
`disabled` list before anything is derived, so the headline derivation, the
ladder and the branch below it agree; `pathway=0` (URL, API) shows the laws
unfiltered, and the page keeps a bar naming the law, quoting the reason and
offering "apply the law anyway". `pie pathways --store --default` writes one and
refuses it without a note, without a known law key, or unless the remaining
laws reproduce the recorded word exactly. (2) Every law named in the interface
is a link to `#/rule/<src>~<dst>:<id>` — a page with the change, its
environment, the rule file's own examples, the cited works with titles and
links, how often the law fires in exact derivations, and its neighbours in the
transition (`service.rule_page`, `/api/rule`).

**Why.** *wolf* (2026-11-08): the ladder read *wĺ̥kʷos → … → wˈolf →
wˈɔlf* against the recorded **wolf**, so its last rung said "differs" although
nothing about the word had changed. Middle English ⟨o⟩ in *wolf* spells /u/ —
the convention that also writes *word*, *wonder*, *come* — not the short *o
that lowered to *ɔ in *dog*; the law is right and simply never applied here.
Not every law applies to every word, and the model needed a way to say so
without bending the law or the target. And a law a page names but cannot open
is a claim the reader cannot check.

**Why not the law.** Weakening the law was measured first: switching
`short_o_lowering` off altogether would add 364 English words to the exact
count (*son*, *cold*, *odd*, *open*, *boy*, *how* …) — the law is right and
ordinary, and only this word is exempt. Narrowing it to "not after ⟨w⟩" would
instead exempt *wrong*, *worst* and *womb*, whose English vowels are not /o/
either. A recorded per-word pathway states exactly what is known and no more.

**Scored apart.** A pathway word is counted in `data/coverage.json` as
`pathway`, never in `exact`: the strict law-only figure stays comparable with
every earlier release, so a per-word exception can never raise it quietly.
*Wolf* moves from the orthographic layer (where *wɔlf* spelled **wolf**
"correctly") to this count: same total, a stronger statement.

**Numbers.** Full run: exact **unchanged at 3,644 / 264,371**; orthographic
2,188 → **2,186** and near misses 22,404 → 22,403 (the two glossary entries for
*wolf* no longer needed the writing layer); **pathway 2**. Rules 476/551/0; no
rule, tier or corpus entry changed.

## 2026-11-08 — a PIE word opens into its family, and the wolf's *kʷ > *p

**What.** (1) A word page in the root language now carries the same
expandable branch as every other word page. `service.word` builds
`descendants` from the **etymon itself** when there is no ladder
(`source = ladder[-1].form if ladder else entry["word"]`), and the root page
appends `renderBranch(...)` after its "follow one path" panel, so the direct
children, their children and every recorded form are one row per transition,
each a door to its own page and that page's laws. (2) `data/rules/
ine-pro__gem-pro.yaml` gains `lkw_to_lp` (order 80, **proposed**):
`kʷ → p / l _`, cited to Kroonen's EDPG s.v. *wulfa- and Wiktionary's
*wulfaz entry, with the example *wúlkʷos → *wúlpos. `data/sources.yaml` gains
`kroonen-2013`.

**Why.** (2026-11-08) (a) "make it similar for PIE word pages as
well (expandable daughter languages, follow rules, etc.)"; (b) the engine gave
Proto-Germanic *wulhwaz for *wĺ̥kʷos but the literature has *wulfaz.

The second answer is not "a missing *hw > *f law". The regular Grimm outcome of
*kʷ is *hw, and the form *wulhwaz is exactly what the regular laws predict —
Wiktionary's *wulfaz entry says that if *wúlkʷos had not changed to *wúlpos "it
would look like **wulhwaz", citing EDPG. The recorded *wulfaz rests on the
pre-Germanic assimilation *wúlkʷos > *wúlpos (German *artikulatorischer
Sprung*), after which Grimm's *p > *f gives *wulfaz. That change is sporadic
(EDPG compares, rather than equates, *pénkʷe > *pémpe), so it is registered as
`proposed` and the page shows the tier: the ladder now reads
`wˈl̥kʷos → wˈulkʷos → wˈulpos → wˈulfos → wˈulfaz`, and PGmc *wulfaz's own page
reaches its headword exactly. *fimf and *fedwōr remain unmodelled; the same
literature treats both as separate irregular changes (proposals/007).

**Numbers.** Full-corpus coverage stays **3,644 / 264,371 = 1.4%** (no
phonemic output changed into a lemma — a proposed law may not claim a match it
did not earn), corpus size unchanged, orthographic layer unchanged. The one
word that leaves a miss list is the wolf itself: the worklist's `ine-pro→gem-pro`
near-miss count goes **944 → 943**, total near misses 22,538 → 22,537. The
evaluation pairs are unchanged (12/49 = 24.5% exact, 77.3% similarity):
*wĺ̥kʷos has no direct `ine-pro→gem-pro` edge pair, and no other recorded pair
contains *-lkʷ-. `check-rules` 476 rules / 551 examples / 0; suite 165 tests +
Node render green. No version bump: no published number moved.

## 2026-11-08 — the branch below a word is a tree, and a record is a record

**What.** (1) `service._stage_descendants` is a tree over `data.descendants()`:
one row per **direct** child, carrying the form that single transition produces
(`derive(form, [parent, child])`), with each row's own children beneath it.
`rows` is the tree flattened (each row carries `depth`), `counts.direct` counts
the children and `counts.languages` everything below. The page draws it as a
folder tree (`renderBranch` → `<details class="branchnode">`), so a grandchild
is never shown beside a daughter; it used to list every language below the
stage in one flat table. A row that reaches a record quotes it **and opens it**;
`recorded.via` says where the record came from — `origin` (the word page the
reader came from), `glossary` (a headword with exactly this form), or `reading`
(a non-Latin entry whose own romanisation is exactly the derived form, through
the new `service._reading_index`). (2) Proto-Iranian *jráyah* is a glossary entry
(`data/lexicon/_supplement/ira-pro.jsonl.gz`): Wiktionary's Old Persian entry
records it as the ancestor, so the stage does record it. The entry carries
`source: wiktionary` and the sentence it rests on (`ref`), and the word page
prints a *Source:* line for any entry that names one
(`service._entry_sources`). (3) A form that differs from a headword only in
notation now finds that headword: `service.printable_form` writes the engine's
`ˈ` as the acute a dictionary uses, and `_headword_at` tries that and the
stressless spelling too, so `jrˈayah` opens *jráyah* and `nˈaht` opens *naht*
instead of a page saying nothing is recorded. (4) No link in the word view is
underlined any more: a form keeps its evidence colour and lights its hit area on
hover.

**Why.** Three complaints on one page (2026-11-08): the Proto-Iranian
rung said *not recorded* although the Old Persian page's own ladder records it;
the page offered "into 4 descendant languages" and listed Old Persian, Middle
Persian, Persian and Avestan as if all four were daughters ("those are not
direct descendant languages … each should have an expand button … a little bit
similar to a file/folder structure tree"); and underlined links look wrong.

**Numbers.** Corpus 264,370 → 264,371 entries (the cited reconstruction:
Proto-Iranian 414 → 415 rows, identified 336 → 337). The exact count stays
**3,644**: coverage compares character for character, and this word's derived
output is `jrˈayah` while its headword is `jráyah` — the stress *notation*
dividend, i.e. the same comparison question (notation against phonology, bound
headwords written with a hyphen) left open on 2026-11-08. No rule, no
tier and no derivation changed.

**Also fixed.** `tools/build_lexicons.py`'s supplement merge rebuilt each
glossary through a dict keyed by headword, so it silently dropped homographs
whenever it ran (Proto-Iranian lost 13 rows on the first attempt at this data
change). It now keeps every row and merges into the first entry of a word, and
gained `--supplements-only` so the merge can run without re-reading the
Wiktionary dump.

## 2026-11-08 — a form is a door, and stress is printed as an acute

**What.** Two display decisions, no change to any rule, number or comparison.
(1) The rule engine marks stress with the IPA token `ˈ`; every form the page
prints now shows it the way the dictionaries do — an acute on the vowel that
carries it, for every vowel and after the vowel's own marks (`drˈayah` →
`dráyah`, `nˈōkʷθs` → `nṓkʷθs`). The stored form, the JSON and `_same_form`
keep the token: the laws are applied to segments and the comparison is a
phonological one. (2) Every form on a ladder is a link. A rung opens the
stage's word page when the stage's glossary holds the form, and otherwise a
*not recorded here* page (`service.word(..., ghost=True)` →
`_unrecorded_word`) which says the stage records nothing and carries the form
through the registered laws into every language below it
(`_stage_descendants`). Rungs carry `recorded.known`/`form_known` so the page
knows which link it needs; a record quoted from Wiktionary's ancestry rows
(Proto-Iranian *jráyah*) has no glossary entry of its own. Nothing on a ghost
page is green or gold: the start is not a recorded etymon of those words, so
every row is this repo's prediction (orange) or a tentative one (red). The
cognate table keeps the 2026-11-07 rule — its language name is the link and its
words stay plain — because a cognate row is a quotation, not a step.

**Why.** (2026-11-08) The Proto-Iranian rung showed `jráyah` with an
acute while Old Persian showed `drˈayah`, and neither the Proto-Indo-Iranian
nor the Proto-Iranian word could be clicked even though the rung wore a ✓. The
tick says the form is a record; a record the reader cannot open is a dead end,
and a record that this repo's glossary does not hold must say so rather than
404.

**Numbers.** None moved. Corpus, coverage, `check-rules` and every derivation
are unchanged; the page only gained links and a second rendering of a form it
already held. Tests: 151 (6 new in `TestWordsThatOpen`, plus the render test's
`pf()` and link assertions).

## 2026-11-08 — a silent record does not contradict a stress mark

**What.** Two dictionary conventions are now read as notation in
`service._comparison_key`, and derived-vs-recorded comparisons go through a new
`service._same_form`: a standalone superscript ʰ (Wiktionary's Old Persian
spelling of the final /h/ the syllabary leaves unwritten — the same entry's IPA
has it plain, `vazr̥kaʰ` = /waˈzr̩kah/) reads as *h*, and stress is compared only
when both sides mark it. Aspiration inside a stop (`kʰ`, `dʰ`) is untouched.
The ladder's first rung can now be lit too: `recorded.starts` marks it as the
record the ladder starts from, where `recorded.matches` stays false because no
law above it derived it. The same review found the opposite error next door:
attested spellings included sign-by-sign transliterations, so `k-a-r` was
accepted as a match for `kar` — a spelling, not a reading. Those are now
skipped, as `readings_for` already skipped them on the page.

**Why.** Old Persian 𐎭𐎼𐎹 *drayaʰ* "sea" (2026-11-08) — PIIr *ȷ́ráyas >
PIr *jráyah > OP *drayah* is produced by three registered laws, but the page
showed `drˈayah` red against the recorded reading. The phonology was right; the
comparison was reading two conventions as disagreement. The same page lit the
derived Proto-Iranian rung while leaving the Proto-Indo-Iranian record it was run
on unlit, which read as the ancestor being *less* certain than its descendant.

**Numbers.** Old Persian word pages: rungs that land on the recorded form
**5 → 17 of 253** distinct lemmas — and two of the old five (`k-a-r`, `u-p-a`)
were spelled, not pronounced, so the real move is 3 → 17. The historical coverage number is unchanged
at 3,644: `tools/coverage.py` compares the lemma string, and an Old Persian
lemma is cuneiform, so a Latin output can never equal it — that is the reading
layer, a separate task.

**Measured, not taken.** Pointing `tools/coverage.py` at `_same_form` (same
corpus, full run) gives 3,644 → **4,529**. Nearly all of it is not this fix:
`tokenize` already ignores the hyphen that marks a bound proto headword
(`fra-`, `dwi-`), so coverage counts 885 words the pages already call exact
(IIR 1 → 178, PIr 7 → 198, Celtic 15 → 111, PWGmc 566 → 668). That is a
definition of "explained" for the project to rule on, not a side effect of a
display fix, so the published number stays as it is.

**Cost.** One more concept in the page (`starts` vs `matches`), and one more
normalisation to keep honest: anything that is not a writing convention of the
same segments must still fail.

## 2026-11-08 — every PIE-to-child transition now carries the laws the corpus supports

**What.** The four existing PIE-to-child chains were completed and three missing
ones were written: `ine-pro__cel-pro`, `ine-pro__ine-bsl-pro` and
`ine-pro__ine-ana-pro`. Exact recorded pairs per transition, before → after:

| transition | before | after |
|---|---:|---:|
| PIE → Proto-Italic | 43 / 335 | **140 / 335** |
| PIE → Proto-Indo-Iranian | 169 / 388 | **258 / 388** |
| PIE → Proto-Celtic | 25 / 270 (no chain) | **138 / 270** |
| PIE → Proto-Hellenic | 43 / 246 | **96 / 246** |
| PIE → Proto-Balto-Slavic | 4 / 146 (no chain) | **50 / 146** |
| PIE → Proto-Germanic | 6 / 49 | **8 / 49** |
| PIE → Proto-Anatolian | 1 / 10 (no chain) | **2 / 10** |

**Why.** The programme's first task was to finish the transitions out of PIE
before adding depth further down the tree: a branch whose first hop is missing
blames every later hop for the same miss.

**What the laws are.** Laryngeal lengthening and vocalisation, syllabic
resonants, the centum and satem mergers, positional splits of the voiced
aspirates, Brugmann's law, Indo-Iranian palatalisation and laryngeal preservation
as *H, Celtic *p > *ɸ and *gʷ > *b, Balto-Slavic ruki and Winter's law, and
Grimm's law with its *s + stop exception. Every rule carries a source key and
single-step examples that `check-rules` verifies.

**Cost.** Three new files to maintain, and the Italic aspirate split changes the
shapes that `itc-pro__la` sees: measured, Latin stays at 73/632 (11.6%).

## 2026-11-08 — Italic *o > *a withdrawn, not re-conditioned

**What.** `o_to_a_medial` is removed from `ine-pro__itc-pro`. With it the
transition explains 43 words, without it 76 (now 140 with the other new laws).
Proposal 006 keeps the measurement.

**Why.** 132 of the 135 recorded pairs that carry a PIE *o keep *o in the
Proto-Italic target; three show *a. No segmental environment can be stated from
that, and the rule as written over-applied to a third of the corpus.

## 2026-11-08 — Proto-Anatolian is left without *o > *a

**What.** The new `ine-pro__ine-ana-pro` file states only the centum merger,
deaspiration and laryngeal preservation. The textbook change *o > *a is not
applied.

**Why.** The recorded pairs keep *o (*wedʰ-o-s > *wedos*, *sókʷ-o-s > *sṓgʷos*).
With ten comparable pairs and the node marked provisional, a rule the data
contradicts would be a guess, not a law. The file says so in its `description`.

## 2026-11-08 — Grimm's law is stated with its *s + stop exception

**What.** `grimm_p`, `grimm_t`, `grimm_k` are split into a word-initial rule
(`left: #`) and a non-sibilant rule (`left: (!SIB)`), so *sp, *st, *sk keep their
stop.

**Why.** Without the exception *strow-o-m* became *sθrawą* and *skid-i-s* became
*shitis*; with it they are *strawą* and *skitiz*. The split exists because the
pattern language cannot express "word edge or non-sibilant" in one atom.

**Open.** Verner's law still cannot fire on 8 of the 49 comparable Germanic
pairs because the recorded PIE forms carry no accent mark, and the engine treats
unmarked stress as unknown rather than guessing (W1 data task: accent marks).

## 2026-11-08 — the legacy project name is gone from the tree

**What.** The name of the earlier rule set was removed from the four rule
notes, the README tier list, `docs/METHOD.md`, `docs/UI_PLAN.md` and the About
page. The rules themselves and their `proposed`/`custom` status are unchanged.

**Why.** The project is published under its own name; a dead project name in
provenance notes is a factual claim about a source that no longer exists.

**Cost.** None. The only remaining "Cyrus" is the Latin headword *Cyrus*
(Italian *Ciro*) in generated data — a dictionary datum, not a reference.

## 2026-11-08 — Old English final syllables, one veto, one demotion

**What.** Twelve rules in `gmw-pro→ang`: final *-a* loss (after *-ą*
denasalisation), final *-u* loss (long and clustered), final *-ô > -a*, the
class-2 ending *-ōn > -ian*, *j*-loss, epenthesis before final *-r*, and i-umlaut
of *a* before a nasal; plus a narrowed breaking rule. `umlaut_ae` was withdrawn
and `final_ōn_to_ian` demoted to `proposed` after an independent skeptic review.

**Why.** The corpus said the final syllable was the largest missing layer:
Old English exact words go **277 → 583** and orthographic **302 → 561**. The
skeptic showed `umlaut_ae` moved 64 words away for 24 gained (it undoes the
regular *a > *æ umlaut), and that `final_ōn_to_ian` also fires on 14 recorded
weak feminine nouns. The first was removed; the second is kept as a labelled
hypothesis.

**Cost.** 31 exact words that the vetoed umlaut rule had borrowed; the
per-transition accuracy still rises from 18.8% to 31.2%. Proposal 004 records
the vetoes and the ordering.

## 2026-11-08 — Middle English gains six laws and three spellings

**What.** `ang→enm`: *æ > a*, palatal *ċ > tʃ*, *f > v* between vowels,
*-ian > -en*, *u > o* in an open syllable, *a > o* before *ng* (all `proposed`);
`data/spelling/enm.yaml` gains *ɔ̄ > o*, *æ > a* and *t ʃ > ch*. The
final-syllable transform and degemination were measured and held.

**Why.** These six are the part of the Middle English block that does not
disturb the English layer. Middle English goes **271 → 387 exact** and
**350 → 406 orthographic**; English stays flat (585→586 exact, 1,086→1,077
orthographic). The full block would have cost English 1,093 orthographic words
until `enm→en` is re-tuned, so it was not merged.

**Cost.** Three spelling conventions and six labelled hypotheses; proposal 005
records the blocked transforms and the measured negatives.

## 2026-11-08 — the PWGmc final nasal is still not a PWGmc law

**What.** A two-step denasalisation (*ą > a*) plus the existing apocope was
built and measured: Proto-West-Germanic **566 → 1,568 exact** words. It was
not registered.

**Why.** The change is shared by every Germanic daughter, so it belongs to
Common Germanic, not to the PWGmc transition; and the PWGmc targets are
headwords whose missing ending is a convention. Registering it would inflate
the historical number with notation. Proposal 001 keeps the 1,002-word
measurement for the day a Common Germanic node exists.

**Cost.** The 998-word signature stays at the top of `docs/WORKLIST.md` as a
structural task, not a rule task.

## 2026-11-08 — stress was tested as the missing condition and is not enough

**What.** A Latin stress declaration (`latin_weight`: penult if heavy, else
antepenult) was implemented and run against the Italian corpus, then withdrawn.

**Why.** It answered the falsifier in proposal 003 exactly: the merger
`ĭ > e / stressed` gains 68 inherited words and loses 108 learned ones
(*spirito, basilico, difficile, critico, timido, minimo, singolo, tigre*). The
blocking condition is the lexical stratum — Latinisms keep the vowel — and no
phonological parameter separates the two sets. Shipping the stress layer would
also have changed rule matching globally (every acute accent is already an `ˈ`
token in the corpus), moving curated examples in other families without a
measurement to justify it.

**Cost.** No number moved. The 80 Italian words stay misses and the stress
step is specified in proposal 003 as the W3 task that will need it.

## 2026-11-08 — an Italian merger is withdrawn, two endings are registered

**What.** `la→it`: `i_to_e` ("Latin short *i > *e") is withdrawn; `final_m_loss`
(*vīnum* > *vino*) and `final_is_to_e` (*canis* > *cane*) are registered. Italian
exact words go from **726 to 1,058** (+412, −80).

**Why.** The merger was unconditional but Italian keeps /i/ almost everywhere;
an open-syllable restriction scores *worse* than no rule (696 vs 843), and the 80
words that stop matching are exactly the stressed short-*i* cases (*pesce*,
*secco*, *fermo*, *legna*). `u > o` survives only because the identical test
shows it is real: restricting it to open syllables costs 464 words. The change
is stress-conditioned and the engine has no stress, so it is withdrawn rather
than mis-stated.

**Cost.** 80 Italian words lose their explanation until a prosody step can mark
Latin stress (W3 task, recorded in proposal 003).

**Numbers.** Historical 2,813 → 3,145 (see `docs/COVERAGE.md`).

## 2026-11-08 — the plausibility guard reads IPA notation, not the dictionary's letter choice

**What.** `spelling.plausible` now compares *segments*: combining marks (syllabic
`n̩`, non-syllabic `ɪ̯`, lowered `ɛ̝`, the tie bar of `t͡s`) are read away, `ɡ`
and `g` are one letter, a rhotic written `r ɾ ɹ ʁ ʀ` is one phoneme, a glottal
stop carries no segment, a syllabic consonant counts as a nucleus, and adjacent
identical consonants are one consonant for the skeleton.

**Why.** The guard was rejecting correct spellings for the dictionary's notation
(`god` against `/ɡod/`, `frei` against `/fʁaɪ̯/`, `bitten` against `/ˈbɪtn̩/`):
two code points for one letter and one phoneme behind five rhotic letters. That
made the orthographic number a measure of the transcriber's conventions as much
as of the letter table. The fold never adds or removes a consonant, so the
`æʌnt → aunt` and `liqʌid → liquid` failures stay blocked (pinned in
`tests/test_orthography.py`).

**Cost.** The orthographic bucket rises from 1,004 to **1,796** spelled words
(1,099 English, 302 Old English, 246 Middle English, 119 German, 25 Middle High
German, 5 Old High German), and the total from 3,817 to **4,609** (1.7%). The
historical number does not move: 2,813 of 264,370 = 1.1%. Vowels stay a
deliberately loose test — the layer still says "these are the right consonant
frame and syllable count", not "these phonemes are right".

## 2026-11-08 — final *-e* loss is morphology, not a sound law

**What.** Proposal 002 was measured and rejected: `e → ∅ / C _ #` in `gmh→de`
would have added 42 exact German words (192 → 227, seven of them only when the
rule is ordered *before* the lengthening rules) and lost 7. The rule is not
registered; the question is filed as a W5 (morphology) open task.

**Why.** One ancestor (`Franko`) has two targets (`Frank` loses -e, `Franke`
keeps it), so no phonological environment can decide — and the same ambiguity
returns at `-k` and `-tt`. Wiktionary's own `gmh→de` pairs are feminine nouns
that keep -e (*Stelze, Stolle, Darre, Klobe, Bürge, Dechse, Nixe, Bunge*): the
retention follows the declension class. A morphological change filed as a
phonological one is exactly what the one rule forbids; a lexical exception list
would reproduce the same 42 words while naming the words it must not touch.

**Kept anyway.** The ordering result: apocope must precede open-syllable
lengthening (*morgene* → *morgen*, not *mōrgen*; +7 words), which also matches
the chronology. Any future morphological -e rule belongs at `order: 90`.

**Numbers.** None published; the corpus stays at 192 exact German words, and
the 42 misses remain misses.

## 2026-11-08 — a spelling match needs plausible phonemes behind it

**What.** `spelling.plausible(form, ipa)` gates every orthographic count and the
word page's `written` field: the derived form must have the dictionary IPA's
consonant skeleton and the same number of vowel nuclei.

**Why.** Without it a letter table concatenates the right word out of the wrong
sounds — `æʌnt` → "aunt" (the word is /ɑːnt/), `liqʌid` → "liquid" — and the
orthographic number becomes a measure of the letter table rather than of the
language.  A reviewer found both in the first build.  The guard cut English's
ungated 4,287 to a defensible 488.

**Cost.** Stages with no recorded IPA cannot be spelling-checked at all (Old
English, Middle English and Proto-West-Germanic are partly in this position), so
their orthographic layer is measured only where the data allows.  The worklist
now lists the glossaries without pronunciation as a W1 data task rather than
letting the layer claim them.

## 2026-11-08 — a written form is a separate layer, not a sound law

**What.** New orthographic layer: `data/spelling/<lang>.yaml`, a new tier
`orthographic`, `src/pie/spelling.py`, `pie spell`, `pie derive --spell`, and an
`orthographic` count in `docs/COVERAGE.md` that is reported beside — never added
to — the historical number. English and German spelling files are the first.

**Why.** English misses were dominated by `/æ/ → a` (1,346 words in a full
audit), `/ɔ/ → o` (993), `/ʌ/ → u` (517), and by German's unwritten macrons and
`ai → ei`. Those are writing conventions, not sound changes. Calling them laws
would inflate the historical number and break the one rule; ignoring them left
the model unable to say "the laws are right, the spelling is a second step".

**Cost.** Two numbers to keep apart in every report, and a new tier the review
protocol must police. The layer may never be used to claim a sound change.

**Numbers.** None published yet at the time of writing; the first measured run
is in the release notes and `docs/COVERAGE.md`.

## 2026-11-08 — the worklist is generated, not curated

**What.** `pie worklist` (and `tools/worklist.py --write`) re-derives the corpus,
groups the misses into signatures, blames transitions, and writes
`docs/WORKLIST.md` + `data/worklist.json`.

**Why.** The roadmap asked for a gap worklist; hand-kept task lists drift from
the data within a day. A miss signature is one rule, not hundreds of bugs, and
only the corpus knows which signature is largest.

**Cost.** A `--write` run costs minutes and writes two files that must be
committed with the change that moved them.

## 2026-11-08 — case and identity are not misses

**What.** The audit classifies a capitalisation-only difference as `case` and an
unchanged form with no rule fired as `unchanged`; neither appears as a rule task.

**Why.** German noun capitalisation is a property of the sentence, not of the
word, and coverage already reports it separately (`case_only`). A form that is
already identical to the target is explained by nothing, and no rule can fix it
without breaking the "at least one rule must fire" contract.

## 2026-11-07 — the programme, the review gate, the decision log

**What.** `docs/PROGRAMME.md` (workstreams, roles, the loop, artefact contracts),
`docs/REVIEW.md` (the five questions, the veto, adversarial critique) and this
file.

**Why.** Parallel work by several linguist agents only stays trustworthy if the
artefacts have a shape, the tiers have a meaning, and a change nobody signs off
cannot land. The gate is the product.

## 2026-11-08 — a root the dictionary names is an entry, and a record carries the reading its own sentence gives it

**What.** `tools/add_roots.py` writes the 30 roots a construction names into
`data/lexicon/_supplement/ine-pro.jsonl.gz` as reconstructed entries with
`pos: root`, the gloss the entry gave them, `url` pointing at the Wiktionary
page where they were read, `ref` quoting that sentence, and `cited_by` naming
the word whose construction printed them. `service.word` returns `built_from`
for such an entry (the reverse of the construction index), and the page lists
the words built on it. `_recorded_at` now carries the reading a dictionary
writes beside a script form ("Old Persian 𐎲𐎠𐏀𐎢 (bāzu)") into the rung.
Middle Persian 𐫀𐫡𐫘 (ʾrs /ars/, "tear") — named only inside the Persian entry
ارس — is a supplement entry with its script headword, reading and gloss.

**Why.** The construction line printed h₂retḱ-, dʰeǵʰ-, teg- and 27 more roots
as plain text: they were doors with nothing behind them, and a reader who
clicked expected a page. The dictionary *does* record them — inside another
entry's etymology — so the entry exists, but its citation is that entry, not a
page of its own (Wiktionary has none for h₂retḱ-). Likewise a cuneiform word
without its reading is unreadable, and the reading is in the same sentence the
record is quoted from; inventing one from the letters would be a guess.

**Cost.** Thirty roots whose status is "named in a prose sentence", not a
dictionary headword: they are gold (reconstruction), their tooltip says so, and
nothing counts them as attested. The Middle Persian record is added honestly
and the ladder still *differs* there: the laws produce OP áçu (PIr *c > θ, θr >
ç) and MP áh, while the record is asru > ars. The missing pieces are a
conditioned *c > s before *r in Old Persian and the *sr > rs metathesis; no
rule is written for them here, because one rule stated on one word is the
target bending the programme forbids. It is now a visible miss on the word in
question, which is where it belongs until a source states it.

## 2026-11-08 — the reconstruction from PIE reads the target word's own record at every stage

**What.** `service.reconstruct` now loads the target word's own ancestry
(`_recorded_at`) and quotes its record on each intermediate rung, through the
same reader the word page uses (`service._record_block`). The parenthesised
reading follows the record (`𐎲𐎠𐏀𐎢 · bāzu`). The recorded word on the
reconstruction line is a link to its page, the pencil follows the form the laws
produced (never the recorded word), and the page glyph is anchored to the
word's own box (`.formblock`), not to a reading that can be wider.

**Why.** Persian بازو's own timeline names Old Persian 𐎲𐎠𐏀𐎢, but
`bʰeh₂ǵʰús → fa` showed no record there: the path was re-derived from the
etymon and the cognate set alone, and the cognate set stops at Persian. The
target word's ancestry is a record of the same path and must not be ignored.
The glyph floated 40 px off an RTL word because it was pinned to the stack
(word + IPA) instead of the word.

**Cost.** A record quoted from the target's ancestry is marked `differs` until
the laws reproduce it — the OP rung prints `baHdúš` beside `𐎲𐎠𐏀𐎢`, which is
an honest miss, not a match. Nothing in coverage moves.

## 2026-11-08 — a construction builds the whole word, and Kroonen's Proto-Germanic is read into the laws

**What.** Three changes, in the order they were asked for.

*The coverage cell.* `viewCoverage` printed the law table's first cell with
`lawLink`, which escapes its argument — correctly, because a law's name may
contain a `<` — so the cell's own `<span class="rid mono">` markup came out as
text. `lawCell(r)` now builds that cell (id + one-line claim, wrapped in the
law's link) and `lawLink` keeps its escaping. The cell's hover colour lives in
`a.lawopen:hover .rid`.

*The construction rule.* A construction is a row that adds up to the headword,
so it must chain every piece the entry states and it must begin the word.
`_TERM_RE` now reads a chain (`*dus- + *ménes- + *-s`, with up to three filler
words after each `+`, so "the root …" is read whole), each row carries
`members` for the middle pieces, `equivalent to` is a derivation cue, a
members-only row (a compound with no suffix) is accepted, and
`_construction_covers()` rejects a row whose first piece does not stand at the
word's beginning — while still allowing ablaut (`*sed-` > `sodéyeti`), a lost
laryngeal (`*h₁wers-` > `wérsēn`), s-mobile, a stated metathesis and a zero
grade (`*wed-` > `*ud-`). The panel prints base + members + suffix left to
right. Result: 509 built words → **531 words / 544 rows**; *dusmenēs* is
`dus- + ménes- + -s`, *wiḱpótis* is `weyḱ- + pótis`, *písdeh₂* is `h₁épi +
sed-`. Capital *H* (`*priHós`) is a laryngeal to `tags()` now; the book writes
whole laryngeals that way and the laryngeal laws could not see them.

*Kroonen 2013.* Sixteen laws from the introduction's own survey of PGmc
phonology, every one cited `kroonen-2013` with the book's examples verified by
`check-rules`: *h₂ and *h₃ colour a following *e (orders 8–9), vowel
lengthening before *h₁, *h₃ and any laryngeal (14–16), *iH > *ī and *uH > *ū
(17–18), *oi > *ai and *ou > *au (40–41), dental assibilation *tt/*dt/*dʰt >
*ss (86–88), *gʷ > *w (137) and its word-initial *gʷ > *g before *u/*r as
*proposed*, off by default beside it (136), and *e > *i before a nasal plus a
consonant and word-finally (215–216). `check-rules`: 491 rules / 567 examples
→ **507 / 583**, 0 problems.

Vocabulary: `tools/ingest_kroonen.py` reads the PDF's text layer and writes
`data/lexicon/_supplement/gem-pro.jsonl.gz` — **1,235 PGmc entries** now cite
Kroonen with a page and headword (1,013 with the page number, 222 from a
headword the parser could not page), 514 carrying the pre-Germanic form the
entry states. It **adds no headword**: the book's ClearScan layer drops
macrons (`fōt` prints `fot`), so the book never contributes a spelling. A
headword is matched to the existing Wiktionary lemma length-blind and scored
on gloss overlap (1,035 stem matches, 200 fuzzy), and only the citation,
gloss and pre-form are taken. The audit table is
the match audit is kept outside the repository.

**Why.** The coverage cell was a rendering bug, not a data bug. The
construction rule was a correctness bug: a row that drops the first piece is
not a construction of the word, it is a fragment — and the test case
(*dusmenēs*) is exactly a compound. The laws were missing in a way that
mattered: *h₂ep-ō > *abō* could not be derived because only *e before *h₂* was
coloured, and no dental cluster reached *ss.

**Cost.** Coverage **3,616 → 3,640 of 264,379 exact (1.4%)**, 130 straight
from the PIE etymon (was 92); orthographic layer 5,762 → 5,787 (2,147 more
spellings, never added). PGmc exact 5 → 8, English 589 → 609, Proto-West
Germanic 566 → 567. The gain is small on purpose: a PGmc glossary lemma is a
citation form (`-aną`, `-az`) that the PIE etymon does not carry, so the laws
that reach the stem often still differ in the ending — reported, not bent.
Deliberately **not** applied, because the engine cannot state them honestly
yet: Dybo's law (needs a pretonic environment), Kluge's law (requires moving
Grimm's second act after aspirate lenition — a structural proposal first),
overlong shortening (needs a degemination transform), Osthoff's law, *u
epenthesis, and delabialisation before *j.

## 2026-11-08 — a construction piece is a recorded morpheme, and the picker is the stage's morphology

*The request:* "it doesn't explain what the suffix -ós means when hovering, but
that's fine (maybe it's not recorded yet). BUT, if a suffix or grammatical
change is recorded anywhere, it should also be selectable for all applicable
'roots'. So I should still be able to see -ós as a possible suffix for other
words as well. Do the same for all the constructions you have for all words.
Ideally, find the meanings and the places where they can be applied."

**What a piece is.** The suffix under a headword was an anonymous string. It is
now a *recorded piece*: a row of the stage's morphology with an id, a meaning,
the number of words the corpus builds with it, a few of those words, the bases
it is recorded on, and — when the dictionary keeps an entry for the form — a
door to that entry. `_construction_scan()` builds the whole-corpus index once
per stage and serves both ends of the same question: what is a word built from
(`_construction_index`, the root page's *words built on it*) and where is a
morpheme recorded (`_piece_index`, the picker).

**Where the meaning comes from**, in the order the page trusts it:

1. the word's own parenthesis (*"deverbal adjectival suffix"*) — the entry's
   words about this word;
2. the hand-written row in `data/morphology/<lang>.yaml`, which absorbs the
   corpus pieces of the same morpheme (`-ti-` + `-s` = `-tis`, so the `-ti-`
   abstract does not swallow the locative ‑ti);
3. the new `endings:` table in the same file — the grammatical reading of the
   letters a word wears (*-ós* is the thematic nominative singular of an
   oxytone stem, *-ó- + *-s);
4. the stage's own suffix entries, exact spelling first. `-os` and `-ós` are
   never merged: the corpus uses both, for different formations. An
   accent-blind match (`-mō` → `-mṓ`) is allowed only when one form answers.

A form no source glosses keeps an **empty** gloss, and the picker says *no
meaning recorded yet* rather than inventing one. Fifteen of the 126 PIE rows
are in that state (`-n̥`, `-tu`, `-ér`, `-lom`, `-plos` …), and the test caps that number
so the panel cannot silently rot.

**What the picker lists.** Every suffix the stage records — the hand-written
handbook rows, every piece the corpus's constructions wear, and every suffix
entry the dictionary keeps even where no etymology builds a word with it
(`-iskos`, `-kos`, `-iHnos`). Rows are ordered by how many words wear them, so
a suffix recorded on one root is one click away on any other root. A piece a
word *composes* is labelled as this repo's composition; no formation law is
claimed for it.

**Why not merge the corpus's spellings.** The corpus writes the same morpheme
at different grades and with different segmentation (`-né-` the nasal infix,
`-tós` and `-tos`, `-íh₂s` and `-ih₂s`). Merging would put one meaning on
another's words; the registry keeps the forms apart and lets the shared
meaning come from the entries that record them.

**Cost.** No rule, form or coverage figure moved (`check-rules` 507/583/0,
coverage unchanged at 3,640 / 264,379): the registry is read from data that
already existed. The first page of a stage pays one scan of its lexicon
(~2 s for PIE, cached for the process); afterwards the index is a dictionary
lookup. 257 Python tests and the Node renderer pin the behaviour, including
`dl̥h₁gʰós`'s `-ós`, a suffix that is offered on a stem that never wore it, and
a suffix entry no construction uses yet.

## 2026-11-08 — a piece says what it means *on this word*

**Decision.** A meaning taken from the paradigm or the dictionary is fitted to
the word that wears the piece, or it is not claimed at all.

1. The `endings:` table fires only when the piece's letters really close the
   word (`_piece_is_tail`), and each row names **every** paradigm value those
   letters have. `-os` is the o-stem's nom./acc. sg. *and* the s-stem's
   (`ménos`, `nébʰos`, `ǵénh₁os`); `-ōm` is the n-stem's nom./acc. sg.
   (`dʰéǵʰōm`, `ǵʰéyōm`) as well as the genitive plural. Saying "thematic
   nominative singular" on `ménos` was wrong, and so was "genitive plural" on
   `dʰéǵʰōm`.
2. Among several dictionary senses for one spelling, the sense whose **first**
   named kind matches the word's part of speech is the one shown: `-ti` in
   `ḱréddʰeh₁ti` (a verb) is "Forms regular imperfective verbs", not the
   adverbial `-ti`. "Adverbial" must not match "verb" — the kind patterns are
   whole words.
3. A handbook row may be matched to a piece at another grade only when the
   dictionary has no entry of that exact spelling: `-éh₂` on an action noun is
   the dictionary's action-noun suffix, not the handbook's collective `-eh₂`.
4. A blind match needs **one** form under the letters: `-o-` may not borrow
   `-ō`, `-ōm` may not borrow `-óm`.
5. The dictionary-only rows are keyed on the exact spelling. `-ónts` and
   `-onts` are two recorded forms, and dropping one for the other hid the
   accented entry altogether; only a row with no entry of its own takes a
   near-homograph's record.
6. Every picker row has its own id — `stem-i` for the i-stem formative, `-kos`
   numbered beside the handbook's `-ko-` — so a click names exactly one row.
   A stem-formative carries the nominative `-s` it builds with, so `-i-` on
   `h₂wl̥p-` composes `h₂wl̥pˈis` and `-o-` on `h₂retḱ-` gives `h₂retḱos`.
7. `-kʷe` and `-we` are offered as the clitics the dictionary records, not as
   derivational suffixes.

**Constructions the entries state in prose.** The arithmetic reader now also
accepts a word named as another form's product — "an active participle of the
root …", "petrified instrumental singular of …", "a dvigu compound of …",
"reanalyzed root of …", "nominalization of …" — so eleven more words carry the
construction their entry states (`h₃dónts`, `h₁réh₁`, `ǵn̥h₁tós`, `ḱm̥tógʷus` …),
and the pieces they name (`-ónts`, `-éh₁`, `-deti`, `-éh₁ti`) become
selectable. A named scholar's suggestion counts as `argued`, not `stated`.

**Cost.** 528 → 539 words with a construction (555 rows); the picker 127 → 135
rows, 119 with a meaning and 16 without. No rule, form or coverage figure moved
(`check-rules` 507/583/0, coverage 3,640 / 264,379). 264 Python tests and the
Node renderer pin it: `ménos`'s `-os`, `dʰéǵʰōm`'s `-ōm`, `ḱréddʰeh₁ti`'s
`-ti`, `bʰugéh₂`'s `-éh₂`, unique ids, the stem composition and the
`-ónts`/`-onts` pair.

**The picker is a menu of sections, and the word's own morphemes come first**
(2026-11-08). A flat list of 135 recorded forms is not a chooser anyone can
read, so the construction panel's menu is now a menu of headings that open
their forms beside them, the way a desktop context menu opens a submenu.

1. The morphemes the word's own constructions wear are printed at the top, in
   the colour of a record (green), before any choice. A piece an entry names
   but no row records is still shown there, as a non-clickable line: the word
   states it, so the menu may not drop it.
2. Everything else is grouped by what each row's own record says it builds —
   noun-forming, adjective-forming, verb-forming, adverb-forming, other
   derivation, stem formatives, inflectional endings, clitics. The section is
   derived in `service.morphology` (`MORPH_SECTIONS`): row `kind` first, then
   the stem-formative pattern, then `_sense_kind` over the row's own gloss. The
   front end never classifies a morpheme; it only prints the sections it is
   given, so a payload without them still renders under one heading.
3. Hover or click opens one heading's list at a time; the arrow keys walk it,
   Escape returns the keyboard to the heading and then closes the menu. Below
   780 px a 340 px menu and a 360 px list cannot stand side by side, so the
   list opens under its heading and the menu itself scrolls; above it, the
   panel is a measured flyout that flips left when the right edge is short and
   lifts when the floor is near.
4. A heading carries no tooltip: the count is already in the row, and a tooltip
   that follows the pointer covered the list it had just opened.

`tests/test_web.py::TestTheSectionsOfThePicker` pins the taxonomy, the worn
morphemes of `dl̥h₁gʰós`, and the front-end hooks; `tests/test_ui_render.js`
renders the menu and pins the order (worn first), one submenu per section and
the fallback heading.

**A glide before a consonant is the diphthong, and a final -i is closed with y**
(2026-11-08). 𐎠𐎡𐎫𐎡𐎹 *a-i-t-i-y* "goes" came out of the ladder as `ˈayti`
and the rung said *differs*: the laws kept the Proto-Iranian glide *y where the
monument has the diphthong, and the script table could not consume the closing
y-sign. Two facts were not yet registered, one in each of the two places where
this repo states facts.

1. **The law.** `ay_to_ai` (ira-pro → peo, order 13, established): PIr *-ay-
   before a consonant is OP -ai-. Old Persian has the diphthongs ai and au and
   no way to write a glide *y before a consonant, so PIr *Háyti is OP aiti,
   *daywáh is daiva (by `ayw_to_aiv`, which names the whole group and runs
   first). The environment *is* the law: a *y before a vowel is an ordinary
   glide and stays one — PIr *dāráyati is OP dārayati — and a *y after a
   consonant (xšayah) is not this diphthong. The wider rule broke dārayati and
   gained nothing.
2. **The convention.** A word-final short -i is written with the i-sign and the
   y-sign, which adds no sound: 𐎠𐎿𐎫𐎡𐎹 *a-s-t-i-y* is /asti/,
   𐎠𐎡𐎫𐎡𐎹 *a-i-t-i-y* is /aiti/. `data/script/peo.yaml` now declares it
   under `conventions:` (id, name, the two signs, and examples `check`-style
   tests read), and `script.match` retries the word without the closing sign,
   reporting which convention it used in `fit.convention`. The rung prints that
   name beside *read a-i-ta-i-ya*, so a green claim still says why.

**What the convention may not do.** It drops one closing sign, and only the
sign the table names, only at the end: `ait` is still no reading of
a-i-t-i-y, and `aiti` is no reading of a-i-t. It also does not excuse a wrong
diphthong — `ˈayti` stays refused, because that word is not Old Persian; the
law, not the reader, is where the glide becomes i.

**Cost.** `check-rules` 508 rules / 585 examples / 0 problems. Coverage: exact
**3,640 / 264,489 unchanged**, orthographic unchanged, `through its script`
**51 → 59** (astiy, abiy ×2, aiti, dārayatiy, hainā, upariy, gaubataiy,
brtiy); no word that fitted before stopped fitting. 275 Python tests and the
Node renderer pin the law, the convention, the three refusals above and this
word's page.

**No scripted word is ever printed without a reading** (2026-11-08). A word
page showed 𐎱𐎠𐎼𐎿 with nothing beside it: the entry records no
romanisation, and the page only ever showed what a dictionary records. That is
a resolution bug, not a data gap — 566 headwords across ten glossaries were in
the same state — so the promise is now three-layered and total.

1. **Recorded.** The entry's own IPA or romanisation, printed as before.
2. **Quoted.** Wiktionary's etymology sentences read a form in the same
   parenthesis — "Old Persian 𐎱𐎠𐎼𐎿 (p-a-r-s /⁠pārsa⁠/)", "Middle Persian
   𐫀𐫡𐫘 (ʾrs /⁠ars⁠/)" — and those are the dictionary's reading of that
   spelling, not ours. `tools/build_readings.py` harvests them into
   `data/readings.json` for the script headwords whose own entry has none
   (97 forms), and the page names the entry the reading was read in. Only a
   sentence that is *about* the form counts: an entry that descends from it, or
   a parenthesis that spells the reading outright after a slash; a bare
   parenthesis must also share the form's consonants, so a gloss
   (*-akъ (masculine)*) never becomes a "reading".
3. **Automatic.** `src/pie/translit.py` reads the script itself: letter by
   letter for an alphabet (Πέρσης → *Pérsēs*, 𐌻𐌹𐌿𐌸𐍃 → *liuþs*), sign by
   sign for a syllabary or abugida (𐎱𐎠𐎼𐎿 → *pa-a-ra-sa*, 𒄀𒈠𒀭 →
   *gi-ma-an*, पशु → *paśu*), and consonant-vowel-less for an abjad
   (هفته → *hfth*) — no vowel is invented, no length inferred, and an unknown
   character is kept rather than guessed. `script.transliterate` supplies the
   table-driven scripts.

**Automatic readings are coloured.** `.reading.auto` / `.translit.auto` are
blue with a dotted underline and say so in the tooltip ("No reading recorded —
transliterated from the Gothic alphabet letter by letter"); a recorded reading
keeps the ordinary colour and names its source. The payload carries
`reading_auto`, `reading_how` (`recorded` | `quoted` | `signs` | `letters`) and
`reading_note`, so nothing about the claim is colour-only.

**The predicate was wrong too.** `show_reading` used `ord(ch) >= 0x370`, which
asked for a reading beside Latin words with a diacritic (Tocharian B *ṣar*,
Proto-Slavic *-akъ*) while a cuneiform word could slip through. It now asks
`translit.is_scripted`, i.e. whether the word is written in a non-Latin script
(non-Latin letters at least half of its letters).

**Cost and guarantee.** Corpus unchanged (264,489 entries; coverage exact
3,640, orthography and `through its script` untouched; `check-rules`
508/585/0). Every scripted headword now carries a reading: 33,594 recorded,
99 quoted, 663 letter-by-letter, 8 sign-by-sign, 0 bare —
`tests/test_readings.py` walks the whole corpus and fails on a single bare one.

## A final *-ā is not shortened, and the kinship -a is not a sound law (2026-11-09)

**Trigger.** A word page showed Old Persian 𐎱𐎠𐎮𐎹 *pādiy* 'protects' reaching
Persian as **pa**, and the Persian rung explained it with
`final_long_a_shortening`, a law whose own note says *-ā survives in open
syllables and before glides (MP xwadāy > NP xodā). The word ends in -ā with an
open syllable, so the law should not have fired — and it was not the word that
was wrong.

**The bug.** The context was written `right: "(NAS|LIQ)? #"`. The sonorant was
optional, so the pattern matched a bare word boundary: the law fired on **every**
word-final *-ā of the language. Measured over the Persian glossary, it changed
118 derivations and shortened the final vowel of 83 of them — NP nām became
*nam*, māh > *ma*, kār > *kar*, dādār > *dādar*, پا > *pa*. The rule's own note
said dādār keeps its long ā, so the file contradicted itself.

**The deeper fault.** Correcting the context would not have saved the law: New
Persian keeps a word-final *-ā, before a sonorant as anywhere else (nām, māh,
kār, nān, jān, dādār). The short -a of pedar and mādar is not a shortened *-ā at
all: the Old Persian kinship nouns are r-stems, the nominative ends in -tā (pitā,
mātā, brātā — Kent 1953), and the form the next stage continues is the **oblique
stem -tar-**, which already has a short a. Middle Persian really has *pidar*
(MacKenzie pytl) and mādar; New Persian pedar/mādar follow from them by the
ordinary *i > e. The law was a Late-Persian patch for a stage whose rung had the
wrong vowel, and it was shortening 83 correct forms to make six wrong ones
green.

**What replaced it.**

1. `pal~fa:final_long_a_shortening` is **deleted**. Its page
   (`#/rule/pal~fa:final_long_a_shortening`) is no longer a law; this entry is
   its record.
2. `peo~pal:r_stem_oblique` (order 19, tier `custom`, `off_by_default`) states
   what actually happened: the r-stem kinship nouns continue their oblique stem,
   so *-tār > MP -tar before *-t- is voiced (*-tā́r > *-tar > pidar). It cannot
   tell the kinship suffix from the agent-noun *-tār of NP dādār 'creator',
   which keeps its long ā — both end -tār and no phonological feature separates
   them, so the rule *would* shorten dādār too. That is why it is registered
   switched off, and the test says so out loud.
3. Four default pathways switch it on for the words whose record states the
   short vowel: fa پدر, fa مادر, and peo 𐎱𐎡𐎫𐎠, 𐎶𐎠𐎫𐎠 (so the timeline
   carried from Old Persian into Middle and New Persian shows the same forms).
   It is off for every other word, like the formation laws *-ka- and *-nah.

**Measured.** Persian word pages whose own rung matches its record: 42 → **39**
(lost دانه، توده، نر and the prefix مـ — chains that never produce the Middle
Persian -ag or the inflection, so they were only green through the false law;
gained نام). 130 Persian forms changed, 83 of them a final ā the old law had
shortened. Old Persian words carried into Persian (`path=pal,fa`): 29 → **34**
match a Persian headword — 𐎱𐎠𐎮𐎹 *pādiy* → **پا**, 𐎴𐎠𐎶(𐎠) *nāma* → **نام**,
𐎶𐎠𐏃 *māh* → ما, 𐎱𐎡𐎫𐎠 *pitā* → **پدر**, 𐎶𐎠𐎫𐎠 *mātā* → **مادر**. The Middle
Persian rung of پدر and مادر now *matches* its own record (pidar, mādar)
instead of contradicting it and being patched one stage later. Coverage exact
**3,640 / 264,489 unchanged** (Persian still counts 0 of 5,555: the glossary is
written in Perso-Arabic and the stage has no orthographic layer).
`check-rules` 508 rules / **586** examples / 0 problems; 299 tests.

**Tried, measured, rejected.** Two other changes this stage needs were written
and removed the same session: `final_ay_to_a` (MP -āy > NP -ā) and
`a_to_o_after_w` (MP xwad > NP xod). Together they changed 17 Persian forms and
gained **no** new match, while moving several further from their recorded
reading (خواب *hwap* > *hwop*, خواندن *hwan* > *hwon*, سرای *thrāy* > *thrā*,
دایه *dāy* > *dā*, همایون *Homāy* > *Homā*). The glide loss is real but
lexically split — pāy, xwadāy, jāy, rāy lose it, sarāy, dāye, homāyūn keep it —
and the rounding only helps once the -y has gone. They stay open, stated as gaps
in the `pal__fa` stage description rather than shipped as laws that over-apply.

**Note on the match.** A Persian rung matches a glossary headword by its
**reading**, not by its sense: 𐎱𐎠𐎮𐎹 'protects' and پا 'foot' are the same
reading *pā*, and the page says the match is through the romanisation. That is
the existing matching rule and is unchanged here.

## A tree's relation label is a label, not a suffix (2026-11-09)

**What.** Every etymology tree stored in `data/lexicon/*.jsonl.gz` now reads its
relation labels in brackets: `Proto-Indo-European *peh₂- [der.] Proto-Germanic
*fōdô …` instead of `*peh₂-der.`. `src/pie/etymtext.py` holds the label table
(the `abbrev` field of each entry in `Module:etymon/data`'s `export.keywords`:
`der.` "derived terms", `bor.`, `lbor.`, `slbor.`, `obor.`, `ubor.`, `calq.`,
`pcalq.`, `psm.`, `influ.`, `redup.`, `vṛd.`, `denom.`, `deverb.`, `aph.`,
`bf.`, `clip.`, `ellip.`, `nom.`, `translit.`, `abbr.`, `syl. abbr.`, `univ.`,
`init.`, `meta.`, `sl.`, plus the two the module spells without a full stop,
`acronym` and `blend`), locates the tree block, and brackets the labels inside
it. `tools/build_lexicons.py` applies it to new dumps;
`tools/repair_etym_labels.py` applied it to the glossaries already in the tree
(14,420 of 266,451 records rewritten, every other field byte-identical).

**Why.** A reader asked where the `-der` in *food*'s `*peh₂-der` came from. It
came from nowhere: the page's etytree JSON says
`"keyword_abbrev": "der.", "keyword_label": "[[Appendix:Glossary#derived_terms|Derived]] from"`
and the term is `*peh₂-`. Wiktextract flattens the rendered tree and the label
span touches the term span, so 28,013 labels across 19,860 records arrived
welded onto their words. Nothing in the string marked the boundary, so a suffix
that Proto-Indo-European never had appeared to exist — and a reader is right not
to trust a page that shows one.

**How the block is found.** A block opens with a capitalised language name and
closes with one term (plus a gloss in parentheses); the next block follows
directly, or after a further term of the same block (`*welk- /*wilk-`,
`via strāta`) when two language names known to `data/language_names.json` resume
there. That is what separates a tree from the sentence after it: `related to
yonder.`, `sono- + -graph.` and `… from English border.` each have one
"block" and no continuation, and are left exactly as Wiktionary wrote them.

**Measured.** Against the English Wiktionary dump's own line structure — the
labels are line-final there — the parse reproduces the source's placement
exactly for **57,212 of 57,798 trees (98.99%)**. In the stored glossaries
**318 labels remain welded**, in 152 records: multi-word terms whose gloss
follows them (`ἐγκύκλιος παιδείᾱ (enkúklios paideíā)`), trees whose nodes name a
variety the language registry does not hold (`Yoruba`, `Itsekiri`), and
etymologies cut at the 300-character limit before the block is complete. They
stay visible rather than guessed. Corpus, ancestry links, coverage
(3,640 / 264,489), the orthographic layer and `check-rules` (508/586/0) are
unchanged; `data/readings.json` is byte-identical (97 readings); 312 tests.

**What this does not do.** It does not turn the tree's `der.` into a `derive`
relation in `anc`: the ancestry rows still come from the entry's templates, and
26,366 of them carry the `etymon` template's keyword (`:inh`, `:af`, `:bor`) in
the language column — `[':inh', 'enm:fode', 'root']` instead of
`['enm', 'fode', 'inherit']`. They are filtered out of every view, so no page
shows them, but the relation the tree states is still not carried. That is the
next piece of work, not this one.

## Sanskrit: the laws now reach the letters (2026-11-09)

**What.** Three layers were missing between Proto-Indo-Iranian and a Sanskrit
dictionary entry, and each got its own fix.

*The phonology.* The Indo-Aryan transition still produced Proto-Indo-Iranian:
`*bʰaHgas` kept its laryngeal (2,947 derived forms carried an `H`), and the
affricates `*č` and `*ǰ` kept their caron spelling. The laryngeal rules
(`laryngeal_loss_initial`, `laryngeal_lengthening`) moved from
`iir-pro→inc-pro` to `inc-pro→sa`, because the corpus's Proto-Indo-Aryan
records still write the laryngeal — a word entering the chain at that stage
never saw the rule. `iir-pro→inc-pro` keeps the affricate changes and gains
`č / ǰ / ǰʰ`, and `inc-pro→sa` states the same outcomes for the spellings its
own records use (`ć`, `ȷ́`, `ȷ́ʰ`), so no form is left carrying a character no
later rule owns.

*The writing.* `src/pie/writing.py` writes a phonemic form in Devanagari —
inherent `a`, matras, virama, visarga, anusvāra — from the standard table
(Whitney 1889). `data/spelling/sa.yaml` is one `transform: devanagari` rule on
the orthographic tier; an abugida's letters depend on their neighbours, which
no segment rewrite can express.

*The citation.* The laws end where the recorded ancestor ends, and `*deywós`
is a nominative: the chain gives `deváḥ` while the entry's lemma is देव
`devá-`. That is neither a sound law nor a spelling convention, so
`data/citation/sa.yaml` declares the four endings a Sanskrit record may be
cited without (`aḥ`, `aH`, `as`, `ḥ`), the coverage page gets a `cited as
stem` column and its own colour, and the word page says *"cited as its stem —
विश्व, from vˈiśva + ḥ"*. Nothing about it is folded into `exact`.

**A bug this exposed.** `tools/coverage.py` tried the spelling layer only on
the single candidate form whose Latin letters were nearest the attested word.
For a language written in another script that distance is noise: देव was thrown
away before its spelling was ever applied, and Sanskrit reported **0** spelled
words while 269 were spelled correctly. The spelling is now tested on every
derived candidate (`orthographic_hit`).

**Measured.** Sanskrit 0 → **266** spelled, 0 exact, **285** cited as stem,
**551 of 3,789** tested words explained (4,724 in the glossary, 3,791 with a
recorded ancestor, 2,997 PIE-linked). `check-rules` 0 problems; 354 tests.

## Latin and Italian write themselves (2026-11-09)

Two languages with no orthographic layer, ranked by identified words without an
explanation. Latin: 3,226 of 3,233 unexplained; seven cited conventions
(Meiser, Weiss, Sihler) — no stress, no macrons, `/kʷ/` is `qu`, `/k/` is `c`,
`/w/` is `v`. Italian: 9,543 of 10,661 unexplained, the largest pool in the
family; four conventions (Maiden, Sihler) — no stress, `/ɛ/` and `/ɔ/` are `e`
and `o`, `y` is `i`. Measured: Latin orthographic 0 → 41, Italian 0 → 271,
`exact` unchanged in both (7 and 1,118). Rejected with numbers in
`proposals/night-0911/family.md`: Latin `j → i` (guard rejections 8 → 9, no
gain), Italian `x → ss` and `ʒ → g`, and extending German and the English
stages, whose residual is law and notation rather than spelling.

The plausibility guard also learned the IPA's own letters for segments the
philological notation writes differently — `ɡʱ`/`gʰ`, `ɕ`/`ś`, `ʂ`/`ṣ`,
`ɦ`/`h`, `ʋ`/`v`, `t͡ʃ`/`č`, `ʃ`/`š` — and the tied affricates. One segment
written in two alphabets is notation, and it had been rejecting correct
spellings. Persian gained 15 words from that fold alone (orthographic
103 → 118).

## The exact count keeps stress only (2026-11-09)

`ec90860` turned `exact` from 3,640 to 4,547 by accepting a derived form whose
only difference from the record was how stress is written. The rule took its
looseness from the comparison key, and the key strips hyphens, brackets and the
difference between the letters `þ` and `θ`. An audit of **all 922** accepted
pairs (`proposals/night-0911/notation-audit.md`) found **397 differed by
something other than stress**: 238 a hyphen (`un-` against `un`; 305 entries,
208 of them suffixes), 152 `þ` against `θ`, 5 an optional segment in brackets,
3 a breve, 2 a two-word lemma. Only 367 pairs had an accent on both sides, and
every one of them put it on the same nucleus.

`exact_kind` now asks `service.stress_only()`: the letters must agree character
for character once the accent is set aside, and one side may be silent about
stress (an old reconstruction makes no claim, it is not wrong). A hyphen, a
bracket, a space or one letter for another is not notation. Measured: exact
**4,547 → 4,150**; Old English 619 → 559 while its spelling layer takes 49 of
those words back (orthographic 484 → 533), so the explained total barely moves
and the word *exact* says what it means.

## whatif measured the wrong thing (2026-11-09)

`tools/whatif.py` carried its own copy of `ancestor_starts` and a wider
equality test, so it disagreed with the published counter (200 against 206
words for one law, 2,624 entries never compared), and it only measured `exact`,
which made it report *fires nowhere* for Persian, Sanskrit and Italian —
languages explained by their writing conventions. It now imports
`ancestor_starts` and `exact_kind` from `tools/coverage.py` and takes
`--layers exact,orthographic,cited`. Measured: dropping `pal→fa u_to_o` loses
2 words (سکان, چادر), a regression the old tool could not see.

## A ladder may start at any ancestor the record names (2026-11-09)

The word page begins every ladder at the topmost ancestor the entry records,
and that stays the default (`test_it_starts_at_the_topmost_recorded_ancestor`
pins it).  But a record names several ancestors: پدر carries PIE `*ph₂tḗr`,
Proto-Iranian `*pHtā́`, Old Persian `pitā` and Middle Persian 𐭓𐭐𐭃.  Until then
the only way to ask what the laws do from the Proto-Iranian form was to
type it, which turns the start into an `edited` hypothesis and says, correctly,
that nothing attests it.

`hierarchy()` now returns `starts`: every form `ancestor_starts()` yields, with
the same reach test the coverage run uses (the derived form equals the headword,
its recorded romanisation, or a reading its script allows).  The page prints
them as chips under the ladder, a tick where one reaches, and a chip says when
a form in another script has no recorded reading so the laws cannot carry it.

`?recorded=1` marks a start taken from the record: the rung keeps its record
colour, there is no edited badge, and the stages above it are listed rather
than derived.  A form the word's record does not name is refused rather than
silently replaced by the default ladder.

## Two counts where no rule demonstrated anything (2026-11-09)

The miss audit (`proposals/night-0911/miss-surgery.md`) found two classes that
could never be counted: a path whose ancestor already equals the attested form
(the counter demanded one fired rule first) and a word the record writes as a
bound morpheme with a hyphen no law writes (`a-` for *a*, `-kas` for *kas*).
They are now their own columns and enter `explained`, never `exact`: a no-op
path is not evidence that a sound law explains anything.  Proto-Iranian 32 + 11
(explained 206 → 238), Proto-Indo-Iranian 1 + 36 (153 → 189).  The audit's own
snippet counted 61 bound forms; 47 survive the stricter test, the rest differ by
more than the hyphen.

## Joins read the gloss out of the piece (2026-11-09)

The construction sentence keeps each piece's gloss inside it — `sesqui- (“one
and a half”) + pedalian (“of the foot”)` — so the lookup failed on pieces that
are headwords.  The piece is now the text up to its first parenthesis or comma,
and what remains still has to be a headword: nothing is guessed.  English went
from 4,416 to 8,682 words with a drawn join, German 636 → 1,001, Persian
3 → 127, Italian 75 → 1,086.

One guard learned from the first run: a hyphen may be stripped only to find an
AFFIX entry.  `-en` is the suffix; stripping the hyphen landed on the letter
*en* and drew a false join (brazen = brass + the letter N).

## Greek speaks its romanisation, and its writing layer is the next step (2026-11-09)

`grk-pro → grc` was 14 laws and 66 matching words.  The corpus asked for
eleven more: *w loss (67 words), long *ā > ē (108), *ō > ɔ and *ē > ɛ, *u >
y, schwa > a, the palatal geminates (68).  The rewritten file has 33 rules,
each with its tier, its references (Sihler, Lejeune, Smyth, Beekes, Fortson)
and a `check-rules` example, and it takes **66 → 218** words with nothing lost.
Rules rejected with their killing number: `n > ŋ` (−2), `s > z` (−1), final
`*-ā > -α` (−14), splitting the ā-fronting (−16).

`coverage.exact` stays **0** for Greek, and that is structural: the counter
compares phonemes with the Greek-script headword and `data/spelling/grc.yaml`
does not exist yet.  The laws are what that layer will write from.

## Gothic: the last transition, and an alphabet (2026-11-09)

`gem-pro → got` did not exist, so a cognate set could name a Gothic form and no
rule file could carry anything to it.  26 established rules (Braune/Ebbinghaus,
Wright, Krause) close it, and `data/spelling/got.yaml` writes Wulfila's
alphabet as 29 orthographic substitutions with the digraphs first.  Measured:
Gothic explained 0 → **276** of 2,260 (12.2%), spelled 203; `exact` stays 0
because the headword is in that alphabet.  598 more words are spelled correctly
but carry no IPA for `spelling.plausible`, which is a data gap, not a law gap.

## Avestan: an alphabet writes itself, and the reader had seven letters wrong (2026-11-09)

`data/spelling/ave.yaml` is one orthographic rule (`transform: avestan`) with
three stated conventions: Avestan writes no accent, *y* and *w* between vowels
are the doubled 𐬌𐬌/𐬎𐬎, and a doubled sign is written once when the vowel
before it is already that letter (Hoffmann & Forssman 2004, pp. 44–46).

`src/pie/translit.py` gave seven Avestan letters another letter's value, so the
reading beside a headword named the wrong sign: 𐬓 is *xᵛ* not *x́*, 𐬂/𐬃/𐬅
are *å/ā̊/ą̇*, 𐬧 is *ṇ*, 𐬪 is *ẏ*.  40 readings changed, 31 of them a real
letter; display only, no count moved.

The layer found a missing law: `ira-pro → ave` had no word-initial *H loss
although the stage's note claimed it and Old Persian has it.  It lands at order
2 with +2 words and 0 lost.  Measured: Avestan 0 → 7 spelled, 0 → 8 explained
of 352.  The ceiling is the data: 39 of 352 entries carry an IPA and the
plausibility guard needs one, so 313 words cannot be scored through this layer.

Also fixed, in the same class as the Sanskrit bug: `src/pie/audit.py` probed
the spelling layer on the candidate closest to the word instead of on every
candidate, so the worklist said 6 spelled for Avestan where coverage found 7
(𐬥𐬏 *nū*).

## A label is a label: the form a ladder starts from (2026-11-09)

Wiktionary writes three kinds of apparatus around an etymon, and
`normalise_etymon` merged all three into the word itself: a sense label after a
hash (`*kʷís#Determiner`), a gloss in trailing parentheses (`*per- (fare)`),
and the second member of an alternation (`*ḱḗr ~ *ḱr̥d-`).  The ladder then
started from forms no dictionary holds — `per- fare`, `kʷísDeterminer` — and a
word that named a real etymon could not reach it.

All three are now removed whole, before the movable-s brackets are resolved
(the `(s)` in `*(s)pend-` is part of the word and survives as `s`).  A genuine
two-word lemma such as `newe founde` carries none of the three and is left
whole: a space is a word boundary, never a label.  621 English links carried a
trailing gloss and 568 of them now resolve to a real lemma of the ancestor
language.  Measured over en, de, it, la, ang, enm, sa, grc, sq, chu: exact
2,826 → 2,829, unchanged +4 (English), nothing lost.

## Progress is measured on the words the family has to explain (2026-11-09)

The coverage page divided everything by the whole glossary, where borrowed and
non-IE words sit too.  English is a third Latin loans, so a correct model of
English read as a 0.5% success; Persian is half Arabic loans and read worse.

Each language now carries a progress bar over the words whose record names an
ancestor in the family: green for the sound laws, pale green for the other
explained layers, amber for a reconstruction the record itself marks as such
(the glossary's star-forms) and the laws have not reproduced, grey for what is
still open.  The overall block leads with the same share and keeps the
whole-corpus bar, and the record's own composition, below it: the two answer
different questions and are never read as one.  A fourth card reports the
glossary's own reconstructions and how many the laws reproduce.

## The council: a law is measured on the whole subtree (2026-11-09)

The project's condition for a hypothesised rule: it may be added if the agents
agree and it does not disturb what is already reconstructed.  A rule written
for one rung is read by every language below it, so the unit of judgement is
the subtree, not the rung.  `tools/council.py` finds every attested language
whose derivation chain contains the transition, measures exact words before and
after in one run, and accepts only when nothing that matched stops matching
and something gains; otherwise it prints the lost words by language.

Measured on the new law `iir-pro → ira-pro: tt_to_st`: it carries
two Proto-Iranian words (Háwāyst, winásti), so dropping it loses, it is not a
free simplification.  `whatif.py` stays the fast single-language probe; the
council is the final hearing.

## Two endings the citation layer was offered, and refused (2026-11-09)

The Sanskrit worker measured two additions to `data/citation/sa.yaml` and left
them outside its write scope: `m` (+48 words) and `ṣ` (+143), 191 together at
zero loss, the biggest single number was left.  Both are refused
after inspection, and the numbers are kept because a refusal is a finding.

`ṣ` credits the wrong word.  Its first example is Sanskrit इ *i* "to go"
through a derived `ˈiṣ`: the laws produced the root इष् *iṣ* "to seek", a
different root that differs by one consonant, and stripping the sibilant
folded one into the other.  A blanket permission that gains 143 words is
exactly the shape of a target bend, and one inspection is enough to reject it.

`m` credits the accusative singular of the same noun (devám for the stem
devá-).  That is the same lexeme, but it is not the citation relationship the
column exists for: Sanskrit dictionaries cite the **stem**, and the ancestor
the laws start from is a nominative, so `-aḥ`/`-ḥ` is the ending that records
the dictionary's habit.  The accusative is an ordinary inflection, and the
existing test (`test_only_an_endings_of_the_file_may_be_dropped`) deliberately
says that `-am` is not this relationship.  Widening the column to any
inflection would inflate "cited as its stem" by 5% and make the figure mean
something else.

## The second half: what a label is, what a join is, and three transitions that did not exist (2026-11-09)

The first half built the spellings and the citation columns (see
the sections above).  The second half went after vocabulary, and four of its
findings changed what a figure means.

**A tree's connector is not part of the form.**  Wiktextract welds the
etymology-tree label onto the term (`*peh₂-der.`), and 621 English ancestry
links carried a gloss, a `#label` or a `~alternation` in the same string.
`normalise_etymon` now strips all three as apparatus: 568 of those links
resolve.  Measured over ten languages, exact 2,826 -> 2,829, and nothing lost.
A two-word lemma is still never joined into one form.

**A join is a formation, not a derivation.**  Thousands of words state that
they are built from two recorded pieces.  They are now counted as `joined`
(11,164 as measured, English 5,558, Persian 41), never added to `explained`, and
drawn as a join in the timeline with one origin per piece.  The header names
the origins; a piece with no recorded ancestry is "an unrecorded source", not
a third share of the other piece's origin (کتابخانه is not "both from
Middle Persian").

**Progress is measured on the words the family has to explain** (the section
above), and the record's three numbers (identified / non-IE / borrowed) are
written out per language instead of being implied by a percentage.

**Old Persian is complete where the record is.**  375 rows: 225 with a modelled
ancestor (137 attested, 88 the glossary marks as reconstructions), and **none**
of the other 150 names Proto-Iranian, Proto-Indo-Iranian or Proto-Indo-European
in its etymology (108 no etymology, 32 donor borrowings, 4 formations, 3
cognate-only, 2 "probably from", 1 disputed).  Four rows whose own etymology
names a modelled stage but whose ancestry carried no usable form are repaired
idempotently by `tools/ingest_op_entries.py --repair-ancestry`.  Two laws:
`epenthetic_i_before_y` (+3 script, 0 losses) and `long_vowel_contraction`
(+2 reconstructions).  Refused with numbers: *s > h (-5), *w > v (+1 but costs
Middle Persian its only script match), *n > ∅/_C, *ȷ́ > d, *H > h.

**Proto-Indo-Iranian: +30 exact** from five ablated changes (*tḱ > *ćš, *ćt >
*št, *s > *z before a voiced obstruent, *z > *ž after ruki, ruki widened),
Brugmann narrowed, Grassmann removed (it gained six words and lost none: the
corpus keeps both aspirates), and the rule order repaired.  Refused: final
*-r loss (+7 in PII but it kills Persian pedār, mādar, dādār and eleven web
tests), palatalisation before *e (+7/-1), ruki after *H (+1/-5).

**Proto-Iranian: the phonology is complete.**  `tt_to_st` carries two words;
the 95 residual misses are punctuation, morphology and compound elements, not
sound laws.

**Old Norse and Latin had no usable transition at all.**  `gem-pro → non` did
not exist: 47 cited laws now take Old Norse from 0 to **692 of 3,011** (23%).
`itc-pro → la` had a dozen laws and 7 exact words; 37 laws (and three repaired
environments) now give **121 exact, 329 explained** of 3,267.  Rejected with
numbers on the Latin side: *o > u / _rC (+2/-7), / _m (+4/-3), / _nd (+1/-2),
final *-i > -e (+4/-1), unrestricted *-ei > ī (+20/-2).  Italian reads the same
transition and lost nothing.

**Sanskrit is explained through its spelling, not its laws** (every target is
Devanagari, so exact is 0 by construction): four laws and fifteen guard
equivalences take explained 633 -> **992**.  Blanket final *-ṣ > -ḥ was refused
(+107/-8, and the eight are root citations).

**The lesson this keeps relearning:** a law that gains words in one
language and loses them in another is mis-stated, not bold.  The council is
now the gate for every candidate, and the losing list is kept in the
proposal's report even when the law is withdrawn.

## A register is a name for one stage, not a stage of its own (2026-11-09)

Wiktionary records ancestors with the code of a **register**: `la-lat` (Late
Latin), `la-vul` (Vulgar Latin), `la-med`, `la-new`, `la-cla`, `la-eme`.  The
model holds one node per language, so those rows named nothing the laws could
start from: 2,850 words across English, German and Italian were filed as
"outside" the family although the record said they were Latin.

The decision: a register is read at its stage.  `data/language_varieties.yaml`
maps the code to the node (`-> la`), `ancestor_starts` uses it, and nothing
else changes - the laws must still produce the attested word from the recorded
form, a borrowing stays a borrowing (a loanword is not inherited from a
register), and only registers of a language the model holds may be listed
(Frankish and Old Irish are different languages, not registers).

The honesty is in the labels, not in silence: the ancestry list keeps printing
the register's own name, and the ladder says "the record names this form New
Latin; it is read at the Latin stage, so the laws out of Latin apply to it
unchanged" (`derivation.start_variety`).

Measured: Italian identified 10,680 -> 12,040, exact 1,070 -> 1,282, explained
1,399 -> 1,712.  English and German unchanged: their Latin-variety links are
borrowings and are still skipped - the number's growth is exactly the words
whose record claims inheritance.

## The labiovelars palatalise before *e, and only there (2026-11-09 dawn)

Indo-Iranian's first palatalisation had been registered for plain velars and
left out the labiovelars, so four, five, wheel and the clitic *-ča could not be
derived while *kʷ > k elsewhere worked.  Three rules now name the labiovelar
itself, at order 44, before the merger: *kʷ > *č before *e plus an obstruent,
nasal or *l; the same before word-final *e; *gʷʰ > *ǰʰ before *e.

The environment is the finding.  Before *r the labiovelar keeps its stop (PIE
*kʷer- "make" gives Avestan kar- and OP kāra-, which is the same exception the
plain-velar rule states), and before *y it keeps it (PIE *kʷeys- > PII *kayšás,
MP kēš, Skt. keśa-).  The wide version of the law wins Middle Persian kyš and
Avestan 𐬐𐬀𐬭 and was withdrawn with those two words named.

Proto-Iranian also gains the superlative's laryngeal loss, *H > ∅ between *t
and a vowel (*názdištHas > *názdištah), tier `proposed`: three etyma, one
suffix, so the environment is stated as segments and the corpus records nothing
else of that shape.

Measured: iir-pro exact 197 -> 203, explained 237 -> 244; ira-pro exact
202 -> 205, explained 245 -> 248; nothing lost in any descendant.  Refused with
numbers: final *-r loss (+7 in PII, costs Persian پدر and نر), *gʷ > ǰ /_e (one
etymon, contradicted by gátiš), geminate *tt (one etymon), and the Brugmann
narrowing that silently broke the Old Persian water rung pinned by test_web.

## One *-h, two transcriptions; and a word-final ç that becomes s (2026-11-09 dawn)

Middle Persian could not read the final *-h its own ancestor carries.  The
cuneiform reading writes Proto-Iranian *-ah sometimes as `h` and sometimes as
the modifying `ʰ`, and `final_h_loss` matched only `h`: the aspirated spellings
skipped both the loss and the apocope behind it.  It now matches either
notation.  This is not two laws: it is one segment under two transcriptions,
and the entry says so.

OP word-final *-çah > MP -s (puça > pus) is a new `proposed` law confined to
the word end, because the same ç continues as h inside a word (xšaça- > šahr)
and the grammars consulted do not state the split as one conditioned rule.
Measured: pal exact 1 -> 2, explained 20 -> 21; fa +2 (داس, پاس), nothing lost.

The Pahlavi readings table was rebuilt from that day's lexicons (waw writes b,
heth x/ẖ, ṣade also č): 651 spellings, every one still quoted from an etymology
sentence, none invented; Persian gains 30 explained on the harvest alone.
Refused: `a_to_o_before_nasal`, which "gains" 37 by changing no letter and only
moving already-correct spellings out of the identity column. A written-layer
column can be inflated that way, and the integrator is told to look for it.

## Avestan's 8 of 352 is not a missing law (2026-11-09 dawn)

The session set out to add Avestan laws and measured first.  Two walls stand in
front of the laws, neither of them in the rule files.

The orthographic layer verifies a spelling against the entry's IPA
(`spelling.plausible`), and only 39 of 352 Avestan entries carry one: the laws
spell 32 headwords exactly today and 7 can be counted.  Old Persian has the
same gap, 9 of 375, and the whole Iran chain inherits it.

The dictionary cites a noun by its stem (aspa-, kāma-, brātar-, ərəzu-) while
the chain ends on the nominative (aspō, kāmō, brātā, ərəzuš), and `citation_hit`
only drops an ending, so it cannot express those relations: -ō/-a 25, -ā/-ar 11,
-š/∅ 7, -əm/-a 4, -ō/-ah 3, -mō/-ma 3.  A scratch rewrite of exactly those
endings, under the same plausibility guard, measures 7 -> 14 today and carries
the rest once the IPA exists.

Four candidates were measured and kept rather than shipped (*ay > aē changes 41
forms and gains 0; *hw > xᵛ 8 and 0; *an > ą fires on nothing; the ar-stem
rewrite gains brātar and is a citation, not a sound change).  The next piece is
`data/citation/ave.yaml` and the paradigm layer, not more laws.

## The ancestor the template states, the root that is not one, and a construction's place (2026-11-09 afternoon)

A reader reported *dáwxšati* (Proto-Iranian): its entry says "from PIE *déwk-s-eti,
from *dewk- + *-seti", while the timeline began at the bare root *dewk-.

**The link was in argument 4.**  `{{inh|ira-pro|ine-pro||*déwk-s-eti}}` writes the
form in the fourth argument because the third is the (empty) on-page term.  The
builder read only argument 3, so the PIE word the entry states was dropped and
the ladder fell back to the root in the cognate set.  The same pass reads
`{{etymon}}` properly: the template packs a whole chain into one argument with
nested markup (`pal:𐭓𐭐𐭃<ety:inh<peo:𐎱𐎡𐎫𐎠>>`), and stripping the tags had
welded the hops together.  `etymtext.parse_chain` now returns every hop with its
relation and its own language, and the builder stores each one.

Re-read over the corpus: 266,740 entries (was 264,489; +2,251 entries kept
because they record an origin the old reader discarded), **113,814 identified**
(was 111,371), **47,324 PIE-linked** (43,842), **14,224 explained** (13,807).
Exact **6,149 -> 6,415 / 266,740 = 2.4%**; of those, **975 start at the PIE
etymon** (724).  666 tests, `check-rules` 809 rules / 1,177 examples / 0
problems.  `dáwxšati` now runs `*déwk-s-eti -> dáwkšati -> dáwxšati`, and its
PIE rung prints the construction `*dewk- + *-seti` (the new `built_as` line).

**A root is not an ancestor (proposals/010).**  `ancestor_starts` treated a
cognate-set root as a start, so Proto-Iranian *háwmah began at PIE *sewh₁-
("to squeeze") and showed a red rung for a word its own record derives exactly.
Roots are now removed from the candidate starts when the record names a word
at any stage; the root stays on the page as the relation it is (`etymon_record`,
`root`, and the note under the ladder).  Words whose record names only a root
keep the root start and keep saying so.  The published exact figure *falls*
for English by 53 (615 -> 562), and that is the point: 21 entries such as
*win*, *bed*, *help*, *hen* were "exact" only because a bare root happened to
produce the modern word (`*wenh₁ -> win`); the word's own chain runs through
Proto-Germanic *winnaną and does not.  `exact_pie` rises overall because the
fourth-argument links are now read.

**A word built at its own stage starts at itself (proposals/011, first part).**
`{{com|ira-pro|*cwáHdah|*pátiš}}` states a construction, not an inheritance:
the only ancestry row on cwaHdapatiš is PIE *pótis, the etymon of its second
piece, and the ladder began there.  The word now starts at itself, its rung
prints both pieces (and their glosses) through `built_as`, and its `etymon` is
empty because one piece's etymon is not the compound's.  The guard matters:
English *beer* also carries a surface analysis ("be + -er") beside its real
origin (Middle English beere), so a same-stage construction becomes the start
only when every cross-stage ancestry row belongs to one of its pieces (traced
through up to three recorded hops).  `ancestor_starts` itself is unchanged in
this respect, so the counter's `identified` column still means "a recorded
ancestor exists"; the construction is counted, as before, in `joined`.

**Every letter of *h₂wl̥pís* is accounted for.**  The construction row showed
`*h₂wl̥p- + *-i-` and left the final *-s* unexplained.  The stem-formative's
own row already carries `ending: s`; the page now prints it as a third piece,
names it from the morphology table (athematic nominative singular), and shows
the composed form at once (`composed: h₂wl̥pís`) instead of an empty slot.  The
etymology text states the arithmetic as well.

**Sources are checked, not trusted.**  A reader reported that
`10.1023/A:1004157407338` (de Vaan 2000) returned 404.  Crossref gives the
article as **10.1023/A:1003961021383**; the citation is fixed.  Two more links
were dead: Ringe 2006 pointed at a non-existent `oso/9780199284139` DOI (the
2006 book is `acprof:oso/9780199284139.001.0001`) and Whitney's grammar at a
removed sacred-texts page (now the archive.org printing).  `tools/check_sources.py`
resolves every source URL through doi.org or the host, reports 403/429 as
*blocked* rather than broken, and with `--crossref` verifies a DOI's registered
title and year: 10 URLs, 0 broken.

**A faithful alphabet is its own reading, and a citation may replace a stem
vowel (proposals/night-0911/ave3).**  Avestan sat at 6 explained of 352 because
two facts were missing, not because a law was.  First: 313 of its 352 entries
carry no IPA, so the orthographic layer's guard — the derived phonemes must have
the same consonant skeleton and vowel count as the dictionary's own pronunciation
— had nothing to compare against, and five words were counted as spelled where
twenty-nine spell the record exactly.  The script is an alphabet with a known
value for every letter (Hoffmann & Forssman 2004, pp. 44-46), so a word's letters
*are* its pronunciation; `data/spelling/ave.yaml` now declares
`guard: {reading: avestan}` and `spelling.record_reading` uses that reading when
an entry has no IPA, through one call (`spelling.confirms`) that the counter, the
word page and the audit all share.  The reading is deliberately *not* the writer
inverted: the writer doubles a glide's vowel between vowels, the reader keeps both
signs, so 𐬀𐬎𐬎𐬀 reads auua and never ava — of the 29 letter-exact words 26 are
counted, one needs no law, and three are turned away (auua, nauua, xšaθriya),
which is the coincidence the guard exists to stop.  Second: Avestan is cited by
the stem (aspa-) while the laws end at the nominative (aspō), and
`data/citation/` could only *drop* an ending (Sanskrit deváḥ → devá-).  A
citation pair may now also *replace* one: `data/citation/ave.yaml` states -ō for
-a, -əm for -a, -iš for -i and -uš for -u, the rest of the form must still spell
the lemma exactly, and the guard must still confirm the stem.  Avestan explained
**6 → 60** of 352 (spelled 5 → 26, cited as the stem 0 → 33, exact 0 throughout —
a Latin-alphabet derivation cannot be the Avestan word, and the table says so).
Corpus explained **14,224 → 14,278**, orthographic 4,831 → 4,852, `exact` 6,415
unchanged, and a language-by-language diff of `data/coverage.json` shows `ave`
alone moved.  Refused: reading Wiktionary's `translit` as the IPA (only 11 of 181
round-trip through the letter table, and the field carries other languages' words
— 𐬓𐬀 glossed `svá`, 𐬀𐬵𐬨𐬀 `asmā́n`, 𐬛𐬀𐬉𐬥𐬁 `dyn'`), and waiving the guard
outright, which would have accepted ava and nava.  `tools/coverage.py` now also
exports `orthographic_examples`, the layer that had a number and no examples.

**The bands report their review load.**  A backlog word is still a word whose
form was reproduced: parking it changes what the record *says*, not what the
rules *do*, so `tools/coverage.py` does not move it out of its band — demoting
it by hand would make the band a mixture of a measurement and a judgement and
nothing in `data/coverage.json` could be re-derived.  What it does instead is
report the load: `attach_review()` reads `data/review_backlog.yaml` and writes a
per-language `review` count (from `counts.by_language`, so every finding counts,
not only the 3,900 listed rows) and a top-level `review` block (90,698 findings:
46,190 `etymon_missing`, 25,989 `sense_mismatch`, 13,640 `hedged_ancestry`,
4,879 `cognate_conflict`).  The coverage page prints it as an **in review**
column, the markdown table carries it, and the cell links to `#/backlog`.  A green
number with a large grey one beside it reads as what it is — reproduced, not yet
believed.  Persian: 1,573 findings beside 221 full; English: 31,163 beside 1,855.

**Dark green means the whole recorded chain, and it must reach PIE.**  Two
definitions were tightened on the project's instruction (2026-11-09 evening) and
both cost words their green.  First: "fully explained" requires **every**
recorded intermediate stage to be the form our laws produce there; one differing
step makes the word *fully explained, with adjustments* even when the start and
the end word are reproduced exactly (`categories.step_row`, `pie.steps`, the
`mismatched_steps` field and the *recorded step differs* line on the word page).
This is a fact about the record, not a change of ours, so it needs no report and
no approval — the report requirement stays for a law or etymon of our own.
Second: green needs the record itself to reach a PIE etymon.  English *et* is
derived perfectly from Proto-Germanic *ēt and has no ancestor above it in
Wiktionary, so it is *partially* explained (`pie.categories.verdict` now takes
`pie_linked`, defaulting to **False**, and both the page and the counter pass a
real test of the entry's ancestry rather than "a derivation succeeded").
Measured over the published run: **full 9,720 → 1,890 (0.77%)**, **adjusted
0 → 1,714 (0.70%)**, partial 139,100 → 145,216, everything else unchanged
(967 unexplained, 23,963 non-PIE, 72,241 IE loans; 3,604 explained, 1.47%).
The strict exact figure did not move: **6,415 / 266,740 = 2.4%** — 111,283 of
the yellow words are exact derivations whose *record* stops above PIE, and
yellow now says so in one reason: *recorded outside the PIE chain*.  Persian
221 → **47 full** and 0 → **53 adjusted** (1,938 partial, 2,721 non-PIE, 820 IE
loans; 100 explained); English 1,855 → **232 full**, 0 → **561 adjusted** (793
explained).  *night* is the worked example of the step rule: exact from Middle
English *nighte*, light green because the laws write something else than
*nahts*, *naht*, *niht* and *nighte* at the four stages above it.  Refused:
keeping the old green for words that reproduce their last mile (that is what the
`exact` column already measures), and making a step difference need approval
(nothing of ours changed; the measurement is the claim).

**A band on every word, not only on a count.**  The glossary
words to be coloured like the coverage page.  A list of 400 words cannot be
measured per request without letting the UI disagree with the report, so the
full run now publishes a second artefact, `data/category_index.json.gz`
(`lang → word → band`, 1.1 MB gzipped, written by the same pass), and
`service.glossary()` paints each headword with it.  Proto stages are absent on
purpose: the six bands are for attested languages.  A sample of 480 words across
eight languages showed 7 disagreements between the page's own ladder and the
counter (the ladder starts at the deepest recorded ancestor, the counter tries
every one and applies the writing layers); the page now quotes the published
band on a plain view and keeps its own verdict only for an edited ladder, and
the same sample is 0 of 480.  While wiring the colours, the swatches turned out
to carry the band keys verbatim (`cat-non_pie`) against a stylesheet that spells
them `cat-non-pie`, so the dark-grey and blue-grey segments of every coverage bar
had no colour at all; one `bandClass()` mapping now feeds every swatch, bar
segment and coloured word.

**A borrowed word says who lent it.**  A Persian word whose record states
"borrowed from Arabic" now prints **borrowed from Arabic** beside its headword
instead of a bare *non-PIE*, and, under the etymology, a dossier: the donor form
the dictionary quotes (آخرت ← آخِرَة), the relation it states, and the window in
which the two languages were in contact — 633–1100 for Arabic into Persian, with
the Islamic conquest (633–651), the Umayyad administration (651–750) and
Classical New Persian (750–1100) marked (`data/loan_periods.yaml`, from
Encyclopaedia Iranica and Perry).  The window is explicitly a window: the
dictionary says *that* the word was borrowed and never *when*, and the panel says
so in the caption rather than inventing a date.  The band is untouched — the
word is dark grey whatever the sound laws can do with it.  `tools/loan_check.py`
audits one donor/target pair: **2,079 of 5,580 stored Persian words** state a
borrowing from Arabic in the leading row of their ancestry; 1,819 of them are
the entry their own page shows and every one comes back `non_pie` from
`pie.service.word` (the other 260 are second entries of a spelling whose page
still shows another word — the homograph gap, v1.2), and `docs/LOANS_FA_AR.md`
is the quotable table.  This also fixed a real bug on the way: `service._category_of`
compared `loans.classify()`'s `non_ie` against the band name `non_pie`, so every
Arabic loan was *partially* explained on its own page while the counter counted
it non-PIE.

**Green needs the engine to carry the PIE etymon all the way down.**  The
the project's third tightening of 2026-11-09 (2026-11-09, with Old Persian 𐎣𐎠𐎶 as
the example): a word is *fully explained* only when it goes up to PIE, the
engine reproduces it from there to the attested form, **and** every recorded
intermediate agrees.  The band used to accept a word reproduced from any
recorded ancestor as long as some PIE row existed in its record, which made
𐎣𐎠𐎶 green on the strength of Proto-Iranian *káHmah alone — the engine never
showed PIE becoming it, and the PIE row is a *root* (`*keh₂-`), not the word's
etymon.  `categories.verdict` now takes `from_pie` (the winning derivation
started at `chain[0]`, the PIE etymon) for every green and light-green route —
laws, the orthographic and script layers, an approved pathway — and the counter
records which stage the winning layer's form came from (`layer_stage` in
`tools/coverage.py`); a word that fails it is yellow with the reason it can be
worked on: *reproduced only from Proto-Iranian, not from the PIE etymon*.
Measured over the published run: **full 1,890 → 567 (0.23%)**, **adjusted
1,714 → 160 (0.07%)**, partial 145,216 → 148,093, unexplained 967, non-PIE
23,963, IE loans 72,241; **727 explained (0.30%)**.  English goes from 232 full
and 561 adjusted to **0 full and 7 adjusted** — the model carries no English
word from PIE with its recorded intermediates intact (English *night* is
reproduced from Middle English only, and its PIE run writes nˈahwθs where the
record has *nahts*).  Persian 47/53 → **18/14** (1,938 → 2,006 partial);
Sanskrit 279/183 → **238/55**; Old Persian **14/2** of 271 banded.  The strict
exact figure is untouched: **6,415 / 266,740 = 2.4%** — exactly what a band that
demands the whole chain is for.  *thin* and 𐎱𐎠𐎭 remain light green: the engine
reaches the word from PIE, but writes θˈinuz for *þunnuz* at Proto-Germanic.

**A formation is not a derivation, so it gets a band beside the six.**  The
request (2026-11-10) was that a timeline be able to show a stage
*combining* two or more of its own words, or adding a suffix, "in a
grammatically reasonable way for that language".  The builder answers that
question (`?build=stage:kind:arg@base`); the band answers the question
the coverage page asks, which is different: *how much of a language does this
model explain?*  A word like Persian آبخانه is not inherited and no sound law
derives it, and calling it "unexplained" hides what is known about it; calling
it "explained" would be a lie, because the seam is not a law.  So `built` joins
`ie_loan` as a facet **beside** the six: brown, never green, counted in the
denominator, and never in `explained` (which stays full + adjusted).

What may be claimed is fixed in three tiers, strongest first, and the reason
string on every page names the tier:
1. **a recorded suffix** — the word is a stored, recorded stem plus one of the
   stage's own suffixes (`data/morphology/fa.yaml`, ten cited rows).  A closed
   class is evidence in a way a cut position is not.  3,921 Persian words.
2. **a split whose second element is a productive head** — `heads:` in
   `data/compounds/fa.yaml` (خانه، گاه، یاب، سازی …).  1,998 words.
3. nothing else.  A general split at any position was measured at 27,311 words
   and rejected: one sample read ابوالفرج and فالامس as two words of Persian,
   and 60–70% precision is not a claim this repo makes.

Refusals are as important as claims: `pie.compounds` splits on the exact
characters (Persian آ U+0622 is not ا U+0627, so آب "water" never becomes اب
"father"), refuses a function word, a stop word and a piece with no recorded
origin, and **refuses a tie** — 1,953 Persian words have two candidate splits
and are left unclassified, because a tie means the model does not know.  A
zero-width non-joiner is treated as the writer's own seam (گوشت‌پلو is written
as two words held together), which is a spelling fact, not a normalisation.

The rung says whose claim the row is: `built as` when the record itself states
the construction (`{{com}}`/`{{af}}`, already read since proposals/011), and
`built from … · our reading of the seam` when it does not.  `source: ours` is
on the payload, so no page can present our reading as a quotation.

**A dictionary's own mark is a record.**  Dehkhoda prints a language beside a
headword — (ع اِ) Arabic, (فرانسوی) French — and that is the dictionary saying
where the word came from, not us.  `tools/dehkhoda_glosses.py` reads it, the
mark itself is kept verbatim in `source_note`, and `loans.classify` honours
`borrowed_from` **only for an entry that states no ancestry of its own**, so a
mark can never overrule a recorded pathway.  Of the 153,195 words read,
**69,147 carry a mark**: 67,608 are `non_ie` (the Arabic, Turkic, Mongolian,
Chinese and Syriac vocabulary) and **1,539 are `ie_loan`** — French, Russian,
English, Latin — because a sister branch is a loan too, and counting
«آبونمان» as "no recorded etymology" was wrong however small the number.  A
mark naming the word's *own ancestor* is not a loan at all: Dehkhoda writes
(پهلوی) on inherited Persian words, and Pahlavi is where they came from, not
where they were borrowed from.  The first reader missed three marks in five
because Dehkhoda writes a pronunciation in brackets before the tag
(«آءة. [ ءَ ] (ع اِ) …»); the corrected reader is re-run over the stored pages
with `--from-cache`, which is why the pages are cached at all.

## 2026-11-10 · the grey band is measured in words, and the words are counted exactly

`data/vocabulary_estimates.yaml` now lets a row carry the number of **words**
its figure really describes, because a dictionary's entries are not all words.
Dehkhoda's own index decomposes exactly: 343,420 headwords = **160,802 single
Persian words** + 77,459 phrases (the index writes the space as a hyphen) +
103,033 numbered homograph pages (آب-2, آب-3 — the same word again, and every
one of those bases also has a plain page) + 2,126 headwords not in Persian
script. The grey band is measured against 160,802, and Persian's band is **0**:
the glossary holds 163,774 single words, more than the dictionary heads. A
dictionary figure is a floor, never a ceiling.

The first pass printed 160,769 — it had subtracted the numbered homograph pages
as if they were phrases, and its own arithmetic did not close. The figure, the
note beside it, `docs/COVERAGE.md` and the table on `#/coverage` are corrected;
the sum of the remaining grey bands therefore moves from 2,054,541 to
**1,720,145**, which is still a sum of other people's dictionary counts and not
a count of anything.

## 2026-11-11 · attested, recorded, proposed — and non-existent

Every word now says how it is *known*, in the same place the page says how much
of its ancestry the laws reproduce. The two are different questions and were
being read as one.

- **attested** — a text or a dictionary writes this exact word in the
  language's own script; the headword is that writing. Old Persian
  𐎭𐎠𐎼𐎹𐎺𐎢𐏁 is attested; `madu` is not, because only a transliteration is
  recorded for it.
- **recorded** — a reconstruction the literature proposes. No text spells it,
  it is printed with a leading asterisk (*madu, *ph₂tḗr), and a dictionary
  records it as the probable word. A proto stage is recorded as a whole.
- **proposed** — a guess of this model. Also asterisked, with no literature
  behind it. Nothing is filed this way today; an entry must say
  `proposal: true` (or `source: pie`) to be read as one, so a word the model
  invents can never pass for a word the record has.
- **non-existent** — the page of a form no glossary of the stage holds. It says
  so, instead of leaving the reader to infer it from an empty ladder.

The status is one pure verdict (`src/pie/attestation.py`), printed as a badge
beside the coverage band on the word page and as a chip on every glossary and
search row, and the recorded form carries its asterisk in the headword. A
homograph is attested when any of its entries is attested; `proposed` only when
the model proposed every one.

## 2026-11-12 · the Iranian lexicons, a harvested lemma list, and three guards

Old Persian had 484 entries, Middle Persian 616, and Parthian none at all.
The dictionaries these three languages are read from do not appear in kaikki,
so the glossary now has a second door: `tools/wiktionary_lemmas.py` walks a
Wiktionary lemma category (and its subcategories, two levels deep), stores one
row per page in a resumable ledger under `data/sources/wikt_lemmas/`, and
merges rows into `data/lexicon/<lang>.jsonl.gz` only when `emit` is run.

- **The ledger is the evidence.** One row per page: title, script form, the
  reading the page states (`ts=` before `tr=`), and the ancestry templates it
  names. A page that is fetched twice is not fetched again; a language whose
  ledger is complete is reported complete.
- **An ancestry template's first positional argument is the word's own
  language.** `{{inh|pal|ira-pro|*huštā-}}` says Middle Persian inherits from
  Proto-Iranian; the stage is argument 2 and the form argument 3. Reading it
  the other way round files a word as its own ancestor.
- **Two pages never claim one entry.** Join order is title, headword, reading,
  then transliteration, and a row that would be the second claim on an entry is
  dropped (Parthian `lwc` and `𐭩𐭥𐭬` both printed *rōz*).
- **Parthian is a Northwest Iranian language**, so its ancestor is
  Proto-Iranian, not Proto-Indo-Iranian: `ine-pro, iir-pro, ira-pro, xpr`, and
  `data/rules/ira-pro__xpr.yaml` carries the five isoglosses that separate the
  two branches (θr > hr, j > z, ai > e, au > o, anaptyxis). The old
  `iir-pro__xpr.yaml` was written for a chain that no longer exists and could
  not fire for a single word; it is removed rather than left to look
  registered, and `docs/EVALUATION.md` is regenerated from the rulesets that
  are actually in use.

Three faults found while measuring:

- **`/static/` served anything the user could read.** The path came from the
  URL and was handed to the file system unresolved, so `/static/../../etc/passwd`
  was answered. The candidate is resolved and must stay inside the web root;
  a symlink pointing out is refused the same way.
- **A broken `category_index.json.gz` looked like a colourless project.** Every
  glossary row silently lost its band. A missing index is still a fresh clone
  (no bands is honest); an index that exists and cannot be read now raises.
- **The measurement published three files one at a time.** A kill between them
  left new counts beside an old band table. Each artifact is written to a
  temporary file beside its destination and renamed, so a reader sees the old
  one or the new one and never a fragment.

## 2026-11-12 · a reading of the signs is not a writing, and a filter is not a measurement

The word the admin opened, Persian **دوش**, taught the page two things about
how it talks about itself, and the audit found a third.

- **A transliteration was badged *attested*.** `service._in_native_script`
  special-cased Old Persian and returned `True` for every other stage, so 617
  Middle Persian and 231 Tocharian B headwords — Latin readings of a Pahlavi or
  Brahmi word — wore a badge whose own definition says "in the language's own
  script". The check now reads the stage's spelling table: a headword with at
  least one real sign is a writing, one made only of the table's
  `kind: translit` characters is not, and a stage with no table falls back to
  the letters themselves. A word that is a reading is a fourth status,
  **transliterated** — a real word, no asterisk, and no claim to be a writing.
  Old Persian 𐎭𐎠𐎼𐎹𐎺𐎢𐏁 stays attested; `madu` stays recorded; Middle
  Persian `lwc` now says transliterated.
- **"Fully explained" beside a ladder that reads the signs.** دوش *shoulder* is
  green because the laws give **dūš** and دوش can be read that way, while the
  dictionary's own reading is **dōš**. The band is the counter's and is not
  moved; the sentence beside it now says *how* it was reached — **"fully
  explained · read from the script"** — and the ✓ explains the same thing. A ✓
  also no longer appears over a ladder whose result *differs* from the record:
  it was printed from the band alone, and 221 pages carried a tick contradicting
  the ladder on the same page.
- **A search rewrote the stage's numbers.** Filtering the glossary for "ab"
  replaced the stage-wide counts, so the selector read "all words · 204" for a
  stage of 7,613, and "4 not banded" counted the page rather than the list.
  `q` now marks rows and the counts are taken before it; `banded` describes the
  filtered list.

Smaller things in the same pass:

- **The meanings tab is named after its source.** It was hard-coded
  "Wiktionary" while 153,215 Persian glosses come from Dehkhoda, which
  misattributed both the text and its licence. The first tab now reads
  dehkhoda, Wiktionary or Glossary, and the Dehkhoda panel is fetched when its
  tab is first opened instead of on every page view (a cache miss costs up to
  six requests to vajehyab.com).
- **A filtered page could not be re-fetched after a POST.** Storing a pathway
  cleared nothing, so the page re-read the pre-POST answer from the promise
  cache and the button looked dead. A successful POST clears it.
- **The cache files were the repository's weight.** `data/meanings/` held one
  543-byte gzip per word: 83 MB of text taking 612 MB of disk in 4 KB blocks.
  `tools/pack_meanings.py` folds them into 256 shards (34 MB), readers consult
  the shard, a loose file still wins because it is newer, and the tree is
  44 MB instead of 612 MB. No row is changed.
- **Whitespace in the stored etymologies.** A dropped `{{der}}` template left
  "from (compare ), from"; `tidy_etym` removes only empty brackets, and 85
  stored rows were rewritten.
- **One notation table, not two.** `tools/coverage.py` carried a byte-for-byte
  copy of `service._LONG_VOWEL_NOTATION`; it imports it now.

## 2026-11-12 · a measurement names the data it measured

`data/coverage.json` and `data/category_index.json.gz` now carry an optional
`inputs` digest of the lexicon files and rule files a run read. The schema stays
2: an artifact without `inputs` is simply not called stale, so an old publish
does not crash the reader. `service.band_index()` exposes the comparison as
`stale`, `/api/coverage` and `/api/overview` carry it, and the coverage page
says "measured before the last data change — rerun `tools/coverage.py`" when it
is true.

The glossary tests now count `banded` from the payload rows and check that a
published `full` or `adjusted` row opens a ladder whose verdict is `match`.
Middle Persian `pal/lwc` is pinned as `transliterated`, not `attested`.

## 2026-11-12 · the rail never breaks, and every word on it says what it means

Two things the reader saw on `peo/Ciçafarnāh` were one bug and one gap.

**The column vanished between stages.** Each rung draws its own rail segment
above itself with `top: calc(-1 * var(--gap))`, and the ancestor rows a
construction climbs through were emitted with `style="--gap:0"`. A bare `0` is a
valid custom-property value but makes the `calc()` around it invalid at
computed-value time: the segment kept `bottom` and lost `top`, so it collapsed to
nothing and the 2px line was missing between Proto-Indo-European,
Proto-Indo-Iranian and Proto-Iranian, and above the construction. `.rung.croot`
now sets `--gap: 6px` in the sheet and emits no inline style, and the UI test
asserts that every `--gap` in the ladder markup is a length. The diamond's
`--spine` is measured from the step's bottom, so a column that hangs lower than
its neighbour — Old Median *farnah against Proto-Iranian — cannot shorten the
rail that passes beside it.

**The meanings were only on hover.** Every word of the timeline now prints its
sense under itself, the way the headword's line does (`name · “a male given
name”`): `level.recorded.gloss`/`pos` on a rung, the same pair on
`_origin_node`, and `gloss`/`pos` on every piece — the stored parenthesis first,
then the piece's own entry, which is what lets a bound suffix say what it does
(`*-rós`: forms adjectives from Caland-system roots) instead of leaving the line
empty. `_rung_gloss` also drops the leading colon some rows were extracted with
(`": type, form, lineage"`). The layout reserves a line under each term
(`--foot`), so the wire through the pieces does not move and the diamond stays
level with the words it marks. The loan ladder reads the same two fields, so a
borrowed word's rungs say what they meant at each stage.

## 2026-11-12 · no entry is not a word, and the note says so

On `peo/𐎣𐎱𐎢𐎫𐎣` the Proto-Iranian and Proto-Indo-Iranian rungs were gold with
the ✓ of a match and a note reading "transliteration only — no reconstructed
spelling recorded". Neither stage's glossary holds the form; the etymology row
names it and the laws run from it, and that was enough for the page to present it
as a word. Three separate claims were wrong.

**Existence is its own colour.** `recorded.known === false` (the same flag
`service._record_block` already sets from `_own_stage_entry`/`_lemma_entry`) now
prints `ev-missing`: dark red `--missing`, upright, and it is *not* italic like
the literature's reconstructions, because there is no word here to reconstruct.
It wears no halo and no `matched` class — the halo and the ✓ claim the laws
reproduced a record, and there is no record to reproduce. The same rule runs
through every surface that prints a record: the ladder rungs, the construction
tree's pieces and chain rows, the reconstruct view, and the branch rows.

**"No entry" is a claim about the glossary, so it is checked by reading, not
by spelling.** Wiktionary quotes Old Persian 𐎼𐎢𐎨 for the entry 𐎼𐎢𐎨𐏃, because
the syllabary writes no final /h/; the first version of the dark-red rule called
that real word non-existent. `_record_block` now asks `_reading_index` when the
exact spelling is not a headword: when the quotation's own reading is the
reading of a headword, that headword is the record's entry — `known` is true,
`gloss`/`pos` come from it, and `headword` is the spelling the rung opens, so the
page never sends a reader to the ghost view of a spelling no page holds. The
index is cached; the lookup only runs when the spelling itself missed.

**The line under a word is its meaning, or that it has none.** The
"transliteration only" note is gone from the rung and from the title block. A
rung prints the entry's `pos · “gloss”` when the entry exists (as before), and
`no entry for this word` when it does not. "No spelling in the native script
recorded" is gone too: it fired on entries that *do* exist, read in
transliteration, and told the reader about the machinery instead of the word.

**The ✓ no longer hides a letter.** A rung that is both a record and a match
carries the W and the ✓ side by side above the word's top-right corner; the ✓
used to hang under the word, where it landed on the sense line. The W itself is
a serif glyph now, not a stroked path: "Times New Roman", Times, Liberation
Serif, DejaVu Serif, Georgia — Wikipedia's W without its globe.

## 2026-11-12 · a page is read in milliseconds, and the corpus is still editable

A word page took ten seconds after every restart, and the first thing anyone did
after a change was wait for one. The work was not the derivation — it was
loading it: 591k glossary rows parsed from gzip JSON at 4.5 s, forty-three rule
files composed in YAML at 2.4 s, and then a full pass over every glossary to
index readings, scripts, lemmas, cognates and constructions.

**Derived data is cached on disk, keyed on the files it was built from.** A cache
key is the name, size and modification time of every input (the glossary, the
readings file, the script table, the rule files), never a timestamp of "when we
last built it", so **editing a word or a rule invalidates exactly what depends on
it and nothing has to be remembered or re-run**. Nothing is committed: the cache
lives in `~/.cache/pie` (`PIE_CACHE_DIR` overrides it), rebuilding is always
correct, and deleting it costs one slow page. Cached: the parsed glossary, the
reading index, the script index, the compiled rule sets, the cognate map, the
per-stage construction scan, the published bands, and every YAML file (composed
once per mtime).

**Glossaries load one language at a time.** `word_index()` used to parse all 37
glossaries before answering a question about one word; `service.lang_index(lang)`
loads a stage the first time it is asked for it, and the case-insensitive
fallback and the glossary listing search that stage only instead of walking the
whole family.

**The server reads the corpus before the reader asks.** `serve` starts a daemon
thread that loads the registry, the laws, the bands, every glossary and the
cognate map — the same cache entries the first request would build, built while
the window is still opening. A failure there is printed and swallowed; the
request path does the work itself.

Measured on this machine, a single word from a cold process: `en/night` 4.7 s →
0.28 s, `peo/𐎣𐎱𐎢𐎫𐎣?path=pal,fa` 3.0 s → 0.02 s warm and ~3.9 s only in the
first second after a restart (the warm-up is still running), against 10.6 s
before the work began.

## 2026-11-12 · the branch starts from this page's own rung

A page opened with `?path=pal,fa` has a ladder whose last rung is Persian. The
branch below the word was carried down from *that* rung while still calling
itself Old Persian, so `𐎣𐎱𐎢𐎫𐎣` produced a Middle Persian `kawūye` that no law
ever made. The branch now starts from the last rung **of the page's own stage**;
the path the reader extended only affects the ladder above.

## 2026-11-12 · an abjad's letters are not a match

Persian کبد "liver" was shown as the Persian record of Old Persian 𐎣𐎱𐎢𐎫𐎣
*blue*, with the ✓ of a match. The path there: the laws give *kabūde*, the
Persian glossary was searched by the consonants of the writing, and an abjad
spells کبد *kabid*, کبود *kabud* and کبوده *kabude* with the same k-b-d. The
letters were the whole test, and they cannot be a test.

**A record is verified** when the dictionary's own reading is the form the laws
produced (allowing only what the script provably cannot write — the final /h/ no
cuneiform sign carries). Where the writing leaves the vowels out and the entry
records no reading, nothing can be verified, so the record is shown but never
with the ✓; where the letters are the evidence a syllabary writes — cuneiform's
vowel signs — the sign-by-sign reading still stands.

**A record can be nearly right, and then it is a question, not an answer.**
کبود is read *kabud* and the laws give *kabūde*: every sound agrees but the
ending, and no registered law drops it. `service._near_record` finds that record
by its reading with a final vowel folded away (`_reading_key`, macron-insensitive
because length is notation), the rung quotes it, and the row says
**`match not verified`** in yellow (`--unverified`, amber in the light theme,
light amber in the dark) with a ⚠ disc — never the ✓, never counted in the
band, and never silently dropped. A form that differs anywhere but the ending —
کبد *kabid* against *kabūde* — finds nothing here and is not shown as a match of
any kind.

**Every unverified match is queued for review.** `pie.review` appends one line
per (stage, form, record) to `data/review/unverified_matches.jsonl` (gitignored
working state, like `data/meanings/`), with both readings, both meanings and the
page it was seen on; `pie unverified` prints it and the review page lists it as
the kind `unverified_match`. The queue is what makes the pile reviewable by a
person or an agent later, and it is the only place a "maybe" lives.

## 2026-11-12 · one construction, one line

*sokʷh₂ṓy's record prints its seam twice — `*sekʷ- + *-éh₂` and
`*sekʷ- + *-éh₂ + *-ṓy` — and the page read the two as rival analyses and drew a
tab for each: two tabs of one construction, which is what the reader saw and
rejected. **A row whose pieces are a prefix of another row's is the same finding
read twice, not a second analysis**, so `_rung_builds` drops it, and one
construction now draws one line. The tabs stay for the case they were built for
— English *about* really does have two formations — and each is labelled with
the formation (`on + būtan`, `be + ūtan`) instead of `affix 1` / `affix 2`,
which named nothing a reader could choose by.

**The step above the headword belongs to the ancestor's own entry.** Proto-Iranian
*háxā's Proto-Indo-European rung is *sokʷh₂ṓy*, and *sokʷh₂ṓy was built from
three pieces — a fact stated in PIE's article and in no Iranian one. The rung
had only asked the *page's* entry, so the page showed the ancestor without the
step that made it. A rung whose stage is not the page's stage now reads
`_rung_builds` of the ancestor's own lemma entry (record rows only: the seam
reader's guess belongs to the page a word has, not to a form above it).

**Nothing under a construction repeats it.** The `suffix it wears` card and the
`-éh₂ -ṓy` tokens beside it were a second printing of the pieces the tree draws,
so they are gone; the composition controls stay where they were. A **bound
morpheme wears no dot**: a dot marks a word whose own line continues above it,
and the line from the `+` reaches a suffix and stops. Its cell keeps the empty
rail column, because the cell is a three-column grid and a missing child slides
the word into an 18px track and off the line.

**A suffix's gloss wraps.** `-éh₂` is *"Creates collective nouns and mass nouns,
corresponding to thematic formations with accent on the suffix"` — a sentence,
not a sense, and as one nowrap line it ran into the next piece and broke the
timeline. It now wraps under the piece into a strip every construction step
reserves below its terms (`--bpad`), which is part of `--spine` so the diamond
still sits exactly on the line. The strip is out of the term's own height, so a
three-line gloss never lifts a word off the shared line, and nothing is
truncated.

## 2026-11-12 · ablaut is a grade, not a law

The reader asked why *ters- keeps its *e in *térs-e-tor but shows *r̥ in
*tr̥s-nó-s and *tr̥s-tó-s, and whether the model knows why. It does now, and the
answer is not a sound law.

**What the phenomenon is.** Indo-European roots have three grades — full (e),
o-grade and zero — and the handbooks tie the choice to the accent of the
formation: an accented syllable takes the full grade, an unaccented one
reduces. A suffix that carries the accent (*-tó-, *-nó-, *-yé-, *-sḱé-, *-néw-)
therefore leaves the root unaccented and in zero grade, which is why *tr̥s-tó-
and *tr̥s-nó- have no *e; the causative *-éye- is the type that is built on the
o-grade (*tors-éye-ti). For a root of the shape *CeR the zero grade is *CR̥ —
the vowel goes and the sonorant becomes the syllable — so the *e of *ters- is
an *r̥ there, while the root-accented *térs-e-tor keeps it. The clearest
internal evidence is inside one paradigm: *térs-ti-s ~ *tr̥s-téy-s, *térs-u-s ~
*tr̥s-éw-s (Fortson, *Indo-European Language and Culture*, the ablaut chapter;
Sihler, *New Comparative Grammar*; Beekes, *Comparative Indo-European
Linguistics*; the Wiktionary entry for *ters- lists the grades side by side).

**Why it cannot be a rule in a ruleset.** A law in this repo rewrites sounds on
the way from one stage to the next and is cited from a grammar of the
transition; ablaut does not change a word between stages, it selects the shape
a morpheme takes inside one formation, in the stage where the formation
happens. Recording it as `ine-pro~x` would have been a category mistake, and
recording it as a sound change would have turned *térs-e-tor into *tr̥s-e-tor.

**What is recorded.** `data/morphology/ine-pro.yaml` now carries a `grades:`
table: one row per formation type whose grade the handbooks fix, with the note
that explains it and the sources. `service.root_grade()` reads the grade off
the two forms (it must *observe* the *r̥ / *o / *e before it says anything) and
adds the note only when the suffix matches a documented type. The grade then
appears in two places: beside the root on the construction step (*ters- `zero
grade`, hover: the accent is on *-tó-) and in the "words built on it" list of a
root page (*torséyeti* o-grade, *tr̥syéti* and *tr̥stós* zero grade).

**What is deliberately not recorded.** *-ró- and *-ti- are left out: *ud-rós
and *n̥bʰrós are zero grade and *gʰóstis is o-grade, but the handbooks do not
fix a grade for those types, so a formation in them carries no note. The model
says nothing rather than guessing, which is the same rule the rest of the repo
follows for laws.


## 2026-11-12 — the PIE page is a ladder, and a root constructs from its rung

**What.** A word in Proto-Indo-European now gets the timeline every other word
page gets, instead of a *reconstruct into* selector. `service.hierarchy` no
longer returns `None` for the root language: the etymon is one rung (`next` is
its daughter stages, `path=` carries the timeline down into them one click at a
time, `data-cut` prunes it), and `word()` returns that ladder as `hierarchy`.
The selector, `renderRoot`, `wireRoot`, `renderReconstruct` and the header
construction block that had not been drawn since v0.16.15 (`constructHtml`,
`constructionInner`, `suffixMenuHtml` and their wiring) are deleted — about 900
lines of front end. An old link's `?into=fa` is read as the same descent by
`app.server._path`. The page payload stops sending the 40-row `rebuilds` table
(`rebuilds_for_etymon` still answers it), and `d.rebuilds` becomes `null` on a
root page.

**Still true about the root, and new about it.** The etymon's rung prints the
form the dictionary heads — `*ters-`, hyphen and all, not the laws' `*ters` —
and its status reads *top of the family*; a stage the reader descends into
reads *descended by the laws*. The rung carries `construct…` and the stage's
cited suffixes as chips, so a root is where a word is built, on the timeline,
above the rung it stands on (`?build=ine-pro:suffix:no@ters-` → *tr̥snós* with
its pieces and their grade).

**A composition takes the grade of its suffix.** `_formation_grade` reads the
`grades:` table of `data/morphology/ine-pro.yaml` and `_grade_stem` writes it, so
*ters- + *-nó- is *tr̥s-nó-s* and not *ters-nó-s*; the built step and the
composed preview print *zero grade* with the handbook's reason, and only a grade
the table states is applied. `compose` also stopped stripping a final nominative
`-s` from a *root* (it turned *ters- + *-eh₂ into *treh₂) — an ending belongs to
a word, and a root is not one. `-nó-` was added to the suffix table (id `no`,
quoted in YAML, or `no` parses as a boolean), with its ending, attach mode,
outcome and sources, so the suffix that builds *tr̥snós* is also one the picker
offers.

**Why.** The selector asked the reader to name a destination before the page had
shown them one stage; a timeline answers the same question with a step they can
see, keep, compare and link. `*tr̥snós` is in the PIE supplement now
(`built_as` `*ters- + *-nó-s`, the grade from `_rung_builds`), and building it
by hand from the root had to give the same word — which it does, through the
same morphology table.

**Numbers.** `tests/test_ui_render.js` passes (its root-page and `renderReconstruct`
sections were rewritten to test the ladder); the Python suite runs 963 tests,
all green.

## 2026-11-12 · the climb above a construction is a timeline again

v0.17.10 wrote each piece's language *beside* its word, to stop a 128px label
column from widening the tree and to keep two ancestors of one stage on one
line. The reader opened *andaswarō and rejected it on sight: "it doesn't show
the language name on the left side of the words in the timeline — why are you
writing PIE to the right of the word? The rest of the timeline above the
construction should look exactly like a regular timeline." He is right, and the
beside-the-word label was my invention, not his. **The climb above a
construction is the same timeline as the ladder below it, and it is measured the
same way**: `--clabel` 156px (right-aligned, the name and its years stacked),
`--crail` 20px, `--cgap` 14px. The tree's first column therefore starts at the
page's own left edge — no negative margin, no inset — so the first piece's rail
*is* the step's rail: at a 1500px window the step rail, the tree's first rail
and every `.rung .rail` sit at x = 360, every label's right edge is 336 and every
word starts at 384, on every page and at every width, and no column can drift
sideways from the spine it hangs on. `--clabel` collapses to 0 on a phone
(`--clabelh: 28px`): the language and its years stand in a band above the word,
exactly as a rung writes them there, and *every* row reserves the band whether
it is labelled or not, so two rows of one depth still stand on one line.

**Every diamond says "construction", on its own line, to its left.** v0.17.11
printed the step's name once, under the whole tree (`.when`), and inside a
nested formation not at all — so a page with two steps showed the word once and
a reader could not tell what the lower diamond was. The name now travels with
the mark: `constructionLabel` puts `construction` and the formation the record
states (`affix`, `combining form`, … `· our reading` when the source is ours) in
the label cell of the diamond's own row — the first piece's row, and every
`.cbuild` row (a built ancestor such as `◇ *h₂ent- + *-s`). The step prints no
label of its own, and a later piece's label cell stays empty with the line from
the `+` running across it (`--cgap`) to its dot, so nothing is written twice.

**Why the first piece wears the step's label, not its own.** The diamond is the
step's mark and the first piece stands immediately at it (v0.17.11), so that row
*is* the step: a language name there would name the step after its first piece —
the confusion the reader had just rejected, one column to the left instead of
one to the right. A piece that itself has ancestors climbs in its own column
(`.cchain`) under its own language label, which is where a reader looks for a
stage; and a one-piece formation (v0.17.9's `combining`/`derivation`) would
otherwise print the same word twice and leave the step unnamed.

**The spine is three segments, because the tree is a scroll box.** `.rail.top`
brings the line down from the rung above; the line *through* the tree belongs to
the tree's first column (`.clead` plus each row's own `.crail::before`), so it
scrolls with the column it belongs to instead of hanging in the middle of
another one; `.rail.foot` carries it across the meaning strip (`--bpad`) and the
15px horizontal scrollbar band (`--sbar: 18px`) to the rung it builds — the
scrollbar was the measured gap under `gmw-pro/aikīn` and `de/überhitzen`. A step
with nothing above it draws no top segment, and a top `???` draws no line into
it (`en/about`). The line from the top mark to the foot now measures a gap of
0 on ten pages at three widths, with one rail x per column, a `+` error of 0
and a label offset of 0.

**The timeline's last circle owns the line to the picker.** The descendant
selector was drawn with the circle at the top of its stub and the horizontal
line 11px below it, so the two read as unconnected marks. The rail now comes
down to the circle's centre, the circle is drawn on that centre, and the line
leaves the circle's *right edge* (`left: calc(50% + 5px)`) and runs to the box.
The picker itself is untouched.

## 2026-11-12 · one word, however many headings the record gives it

The reader typed `aiganaz` and saw it twice: "past participle of *aiganą" and
"own".  It is one word.  Wiktionary's page has **one etymology** and **one
pronunciation**, then two headings — `===Participle===` (`past participle of
*aiganą`) and `===Adjective===` (`own`) — and the dump stores a row per heading,
which is the only thing a dump can do.  The model has grouped those rows into
words since 2026-11-09 (`pie.senses`, the glossary's "one row per word"), but three
views still read the rows directly, and each of them showed the same word twice
or under the wrong name.

**Search and the suggestion list ask the sense grouper.** `search()` now emits
one row per (language, word, sense) — the same key the glossary uses — and
prints the group's parts of speech and meanings (`verb / adj`, "own; past
participle of *aiganą").  Two etymologies stay two rows with their numbers, so
*bank* the institution and *bank* the river bank are still two words, and
Proto-Germanic *wistiz* is still "1/2" and "2/2".  `headwords()`, the menu the
construction row composes from, names a word by its first meaning instead of by
the heading that happened to come first.

**The page and its rung print the word, not the first heading.** `word()` keeps
the entry it measures (the pathway, the band, the sources are the entry's own)
and prints `head`: the group's parts of speech and its glosses.  `_record_block`
— which builds the rung that stands above *andaswarō or beside the headword —
does the same, because a rung stands for a word too.  So gem-pro/*aiganaz now
reads **"verb / adj · own"** in the title and on its own rung, and its etymology
line ("Adjectival formation from *aiganą") still says how the word was made.

**A form-of note is not a meaning.** A gloss that begins *past participle of*,
*inflection of*, *alternative form of* … points at another word; the rest name a
sense.  `senses.meanings_first` keeps both but prints the meanings first, so a
page never answers "what does it mean?" with a description of an ending.  Only
the order changes: nothing is dropped, and a word whose only gloss is a pointer
(*aiginaz* → "alternative form of *aiganaz") reads exactly as before.

**What was not done.** The glossary keeps both rows: they are the record's own
headings, and deleting one would be this repo inventing a fact about Wiktionary.
Nor was the class widened by guesswork — a participle that became a noun
(Sanskrit *भूत*, Old English *búandi*) is a separate word only when its own
etymology says so, and the grouper already decides that from the prose and the
chain, not from the part of speech.

**A row is found by what it says, not by its address in memory.** The search
table (`_search_rows`, an LRU of prepared rows) and the grouping index
(`_senses_for`, over `lang_index`) are two caches over the same glossary, and a
parse-cache eviction — the 61st `data.lexicon()` call, or an edited word file —
can leave one holding rows the other has re-read.  They are equal rows with new
objects.  Both the search and the rung looked their row up with `is`, found no
group, and fell back to the first heading: *aiganaz read "past participle of
*aiganą" and lost "own", and Proto-Germanic *wistiz's two origins collapsed
into one row.  The first full-suite run after this release failed on exactly
these three assertions.  `_group_of` now matches a row the way `senses.groups`
identifies it — part of speech, meanings, etymology — so the two caches cannot
disagree about which word a row is.

**Numbers.** 388 pages sampled over ten stages: the page's part of speech and
first meaning are the grouped row's in every one (the three "misses" are words
with no gloss at all, where both are empty).  `tests/test_senses.py` gains
`MeaningBeforeGrammarTest` and `OneWordIsListedOnceTest` (11 new tests, one of
them reproducing the cache-eviction state that broke the first run), and
`service.search("aiganaz")` answers one row where it answered two.

## 2026-11-12 · a word the record forms from one word starts at itself

The reader asked that Wiktionary's *aiganą be listed in the Proto-Germanic
glossary and used as a construction element of *aiganaz (admin, 2026-11-12).
*aiganą was already a complete entry — verb, "to possess, to own, to have",
PIE *h₂eh₂óyḱe, descendants — so what was missing was the link: *aiganaz's
Wiktionary page says "Adjectival formation from *aiganą ('to own, possess')"
and lists it under Participle as "past participle of *aiganą", a **derivation
from one word**, and the timeline showed nothing above *aiganaz.

**The step existed but could not be reached.** `_own_construction` — the rule
that a word built at its own stage starts the ladder at itself instead of
climbing to a piece's PIE root — required two pieces. It now reads
`_SINGLE_PIECE_KINDS` (`derivation`, `combining`), the same licence
`_rung_builds` has used since v0.17.9, so *aiganaz starts at gem-pro and its
rung carries the step. The guard is unchanged: a cross-stage ancestry row must
belong to the piece (`_pieces_explain_ancestry`), and a one-piece row of any
other kind is still a truncated analysis, never a construction. Only two rows
in the corpus are one piece — PIE *h₂entó- (`combining`) and *aiganaz
(`derivation`) — so the change moves exactly this entry.

**The supplement records the link.** `tools/build_lexicons.py` already let a
supplement row carry `built_as` (it *replaces* the dump's row rather than
unioning into it); the `aiganaz` row now states
`{"kind": "derivation", "of": "aiganaz", "pieces": [["*aiganą", "to possess, to own"]]}`,
cites the reconstruction page, and marks `cited_by: ["aiganą"]`. Written into
`data/lexicon/gem-pro.jsonl.gz` by `--supplements-only`.

**What the timeline says.** gem-pro/*aiganaz, upward: *aiganaz → construction
(derivation) ◇ *aiganą → PIE *h₂eh₂óyḱe → … — the piece's own climb is drawn
above it (`branch`), and *aiganą and *h₂eh₂óyḱe are links. It is the same
shape as *anda → *h₂entó-, with the formation at the word's own stage. At
1400px and 420px the construction label, the diamond and the word share their
line; nothing in the header changed.

**Tests.** `tests/test_build.OneWordBuildsAnother`: the entry states *aiganą
as its base (one derivation piece, known, glossed, with *h₂eh₂óyḱe above it);
the ladder's last rung is gem-pro *aiganaz and carries the step; a one-piece
row of another kind still starts nothing.

## 2026-11-13 — one drawing of a construction, one reading of a chain, and
## the suffix a template stopped short of

**The pieces section is gone** (admin: "I thought we completely got rid of the
WHERE THE PIECES COME FROM section. Please remove this section from all word
pages entirely; what it wants to show is already shown in the timeline"). The
block stood between the header and the timeline and drew each piece with its
own ancestry, meeting again at the headword; `builtInTimeline` suppressed it
only when the timeline's step carried *exactly* the same piece list. So it was
either a second copy of the step or — when the two disagreed — a rival analysis
of one word. `renderJoin` and its section are deleted; `joins`/`seam_join` stay
on the payload because the timeline's step and the band's reading are built
from them.

**A chain joined with "and" no longer stops short.** *h₂ḱh₂owsyéti's own
sentence reads "From *h₂eḱ- (“sharp”) + *h₂ṓws (“ear”) and + *-yéti
(denominative verbal suffix)", and `_ARITHMETIC_RE` required the `+` to follow
the previous term directly, so the suffix after "and +" was never read. It is
read now, and a word whose *stored* template stopped short of its own sentence
takes the longer statement: `_rung_builds` accepts a stated row that starts with
the stored one and adds a piece, and the prefix-merge (compared without
notation) drops the shorter — one construction, three pieces, the suffix
carrying its morphology gloss.

**A hole in a piece's chain is a hole in the word's** (admin: fa آبجو "I can
still see 'no entry for this word' on the page but it's still 'fully
explained'. This should be impossible"). `unrecorded_ancestry` walked the
entry's own record, and a compound's record has no ancestry of its own: the
pieces' rungs are drawn by the page but were never measured. It now walks each
piece the stage heads (from `_own_construction` and `_compound_pieces`) to depth
two and reports what it finds once per (stage, form). A **hole also outranks the
published band** in `_page_category`: the rung is on the page, so no index may
call the word green beside it.

**Two notations that hid a word.** A record that names the two stems of one
ablauting noun writes them together (`*h₂ṓp-s ~ *h₂ép-s`); `_lemma_entry` now
tries each side, so the rung resolves to the word rather than to nothing.

**Three entries the pages were missing**, each filed from the record that names
it, in `data/lexicon/_supplement/`: Old Persian *yáwaʰ "barley" (Wiktionary's
Persian جو: "from Middle Persian …, from Old Persian *yáwaʰ, from Proto-Iranian
*yáwah"), the Middle Persian jaw it names, and PIE *h₂ṓp-s ~ *h₂ép-s, the root
noun of *h₂ep- (Wiktionary's *Hā́ps: "From Proto-Indo-European *h₂ṓp-s ~
*h₂ép-s, from *h₂ep-"). With them, fa آبجو is complete on both branches:
آب → PIE *h₂ṓp-s, جو → PIE *yéwos.

**`-lom` is a registered PIE suffix** (admin: "Do we have an established
morphology that would add a -lom suffix to a PIE word? If so, it would help with
gem-pro/ailą"). `data/morphology/ine-pro.yaml` gains the `lom` row — `-lo-` plus
the neuter nom.sg. `-m`, attach `drop` — beside `-tro-`, with the record that
names it: Proto-Germanic *ailą "from earlier *aidlą, from Proto-Indo-European
*h₂éydʰ-lom, from *h₂eydʰ- (‘to burn’)". The PIE word is an entry
(`h₂éydʰlom`, one construction of *h₂eydʰ- + *-lom), so gem-pro/ailą's ladder
now climbs *ailą → ◇ *h₂eydʰ- + *-lom → *h₂éydʰlom and the rung is a word of its
stage. The laws that carry *h₂éydʰlom down give *íydlą, not *ailą — the page
says "differs — the worklist", which is a law question, not a morphology one.
