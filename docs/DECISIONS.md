# Decisions that still bind

The reasoning behind every change is in `docs/archive/DECISIONS-2026-11.md.gz`
(134 entries, append-only, newest first). This file keeps only what a future
change has to obey; when a decision below is superseded, replace it here and
leave the reasoning to the archive. Anything that a reader could *notice* on a
page also belongs in `AGENTS.md` ("What a word page must keep true").

## The model

1. **One etymology pathway per lexeme.** Several may be proposed; only one
   happened. Homographs are different words with their own paths. A route that
   competes with a known path and has a closer, more ordinary meaning is
   probably wrong.
2. **A derivation is what cited laws do to a form.** Case, macrons, apostrophes
   and near-misses never move a number; that is the orthographic layer, counted
   apart.
3. **A match is verified, or it is a question.** A ✓ and a band need the
   dictionary's own reading to *be* the form the laws produced; a record that
   agrees on every sound but the ending is `unverified` (⚠, queued in
   `data/review/unverified_matches.jsonl`), never silently dropped.
4. **A writing is not a sound.** The laws refuse a form written in its own
   script; every caller hands over a reading.
5. **A rung the laws produce is not an entry.** It says *no entry for this word*
   and counts as a hole.
6. **A word is never greener than the words above it** — every rung, piece and
   ancestor a page draws is asked for its own band.
7. **A registered construction may carry a word to fully explained**, and only a
   construction the *record* states; one this model composes needs the approval
   route (`data/adjusted.yaml` + a report per law and per word).
8. **A verb stem is a word, never a suffix** (دستمال = دست + مال «present stem
   of مالیدن»), and a piece the record glosses as grammar is bound.
9. **Ablaut is a grade, not a law**: the oxytone types leave the root
   unaccented (*tr̥s-tó-s), *-éye- is the o-grade causative, *CeR loses its verb
   to *CR̥. Only documented types are recorded. Table: `grades:` in
   `data/morphology/ine-pro.yaml`.
10. **Reduplication is morphology**, not a sound law (`reduplications:`).
11. **A root is a relation, not a step**; a bound morpheme is grammar; a
    borrowing is not inheritance; a stage this model has no glossary for is our
    gap, named as such.

## Reading and writing

12. **One romanisation per stage** (`data/notation/<lang>.yaml`, folded at load,
    `LEXICON_VERSION`): a headword and every ancestor a record names are read in
    the stage's own alphabet. `pie notation <lang>` fails on a variant.
13. **A transliteration keeps its spelling beside its reading** (`translit_quoted`):
    *lwc · rōz*, *hwʾb · xwāb*. A spelling the stage's alphabet cannot write is
    never promoted to a headword.
14. **Three layers, shown in this order:** romanisation (required), the sign
    transliteration (computed from the sign table, never stored), IPA (optional,
    word page only). Nothing but a romanisation rides a timeline.
15. **A timeline reads, it does not spell**: a rung whose form is a spelling
    prints its reading and keeps the spelling for links and construction.
16. **Duplicate rows merge only when they mean the same** — same word *and* same
    senses; containment is not enough (MacKenzie bundles homographs).

## Data and tooling

17. **Editable JSONL/gz + YAML is the source of truth; derived data is cached,
    never committed** (`~/.cache/pie`, keyed on name+size+mtime). A data edit
    needs no build step.
18. **Never edit a generated file by hand** — change the tool and rerun it.
19. **Never publish a sample as a number**: only a full `tools/coverage.py
    --docs` run rewrites `docs/COVERAGE.md`, the README block and
    `coverage.svg`.
20. **A rule needs a source key, a tier and verifying examples.** A missing
    `tier` defaults to `established` and silently promotes a hypothesis;
    `check-rules --strict` refuses it.
21. **Cite a locator**, not just an author.
22. **One artefact per commit**, and a bug found on the way is named in the
    message — no unrelated refactoring rides along.
23. **A transcription is not a transliteration.** A transcription says how a
    word sounds (`garm`, `vr̥kaʰ`), a transliteration how it is written in Latin
    letters (`glm`, `v-r-k`), and the script is the letters themselves. A record
    that gives a transcription has attested the word: `attested` no longer
    needs the headword to be the writing, and the old `transliterated` status is
    gone.
24. **Spellings are a field, not a row.** A word's written variants (`glm`,
    `g03lm` …) are `translit` (commonest) + `translit_variants` (at most eight
    more, most frequent first), marked by `spellings_n`; `translit_alt` stays
    *alternate readings*. A variant spelling never becomes its own entry.
25. **The glossary shows both Latin layers when they exist**: `transcription`
    and `transliteration` per row, each column printed only when a row has a
    value that is not already the form. A computed transliteration is shown only
    where the script's table states how (the Old Persian syllabary); elsewhere
    it would repeat the form's own letters.
26. **A row is only changed by the supplement that owns it.** The MPCD merge
    updates `source: mpcd` rows and appends the ones it does not have; it never
    writes its senses, url, `pos` or spellings onto a row another dictionary
    heads (71 such rows had to be put back, 2026-11-13).
27. **A page never pays for a whole stage to answer about one word.** A
    glossary is read by offset (`data.lexicon_rows`), a stage's rows are a disk
    artefact (`_glossary_rows`), and a loop over 17,000 words may not stat
    `data/`. Measure with `AGENTS.md` → "Measure it"; the cache's dead files are
    dropped by `pie cache --prune`.
28. **A timeline continues on its own reconstruction.** The model does not
    borrow a record's transcription for the next step: a romanised rung is
    carried as itself, and only a form in the stage's own writing is replaced by
    its reading (`service._descends_from`). So 𐎺𐎼𐎣𐎠𐎴 goes PIr. *Wŕ̥kānah →
    OP Wˈarkānah → MP Wˈargān (the record's Vr̥kānaʰ stands beside the OP rung
    and is not the input), while a cuneiform headword with no ancestor is read
    and then continued from that reading. The same rule seeds the pencil: what
    is edited is the printed romanisation, never the script.
29. **A rung's sub-line says what the word means, not how to read it.** The
    sense (`noun · "Gorgan; Vahrkana"`) stays; "read v-r-k-a-n", "the script
    leaves h unwritten", "the writing allows it — the record reads …" are gone
    from the page, because the transcription and the signs are already printed
    on the rung (admin, 2026-11-13). "No entry for this word" and "match not
    verified" stay: they are facts about the word. The pencil reads its seed
    from the payload (`level.edit`, the printed form), never from a character
    test — `Wˈarkānah` is a romanisation even though `ˈ` is a letter — and it
    seeds that form **as printed**: the page turns the stress token `ˈ` into the
    dictionary's acute (`pf`), so the box opens `Wárkānah`, not the engine's
    `Wˈarkānah` (admin, 2026-11-14). Handing the acute back is safe: the engine
    canonicalises it before the laws run (`GET /api/derive?form=Wárkānah`
    returns `Wˈarkānah`).

## Interface

23. **A timeline is one tree**, not a set of inset pictures: the diamond sits on
    the rail, the first piece stands at it, and pieces are word-sized.
24. **A construction is drawn once** (the timeline draws it; there is no second
    list of pieces under the headword).
25. **Every word of a tree says what it means, under itself**; a bound
    morpheme's gloss says what it does.
26. **A bound morpheme opens its own entry or nothing** — never a letter's page,
    never a word that happens to share the signs.
27. **A word is listed once** wherever the reader meets it (search, glossary,
    construction menu, API): language + word + sense is the key.
28. **Evidence colour is the contract** and it has no key on the page: green and
    gold mark recorded forms, a rebuilt form is never green, and every form
    carries its own tooltip.
29. **No pills in a title**: language and years in the left margin, the band and
    the record as one italic line.
30. **The interface is stdlib and dependency-free** (no bundler, no framework);
    a new dependency is a decision, not an implementation detail.

## Process

31. **Tests are a budget**: the tests a change touches, under a minute; the full
    suite is for a release (`tools/quick_tests.py` is the everyday run).
32. **Measure both ways** — per transition (`tools/evaluate.py`) and per corpus
    (`tools/coverage.py`). A rule that helps one and hurts the other is a
    finding, not a win.
33. **A change is written down where it is seen**: a page rule in `AGENTS.md`, a
    model rule here, the reasoning in the archive.
