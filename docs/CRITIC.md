# The critic — what a reader who distrusts the page must check

The model is only as good as the pages it prints. A critic is an agent (or a
person) that takes a random sample of word pages, compares each one against the
record it claims to summarise (Wiktionary's etymology, Dehkhoda, the cited
laws), and reports every place where the page says something the record does
not support. It **reports**; it does not edit `data/` or `src/` (2026-11-13:
the admin asked for a ruleset a subagent can run repeatedly, and a super agent
who fixes what it finds).

Start from `tools/critic.py sample --lang fa --n 20` and finish with
`tools/critic.py check --lang fa --n 20`, which pre-computes the mechanical
faults so a critic spends its attention on meaning.

## Rule 0 — notation is not spelling

A record writes what it read, and the page must look up the word beneath the
notation. Three forms of it are common and were each a reported fault
(batch 04, 2026-11-13): a stage key in front of the piece (`fa-cls:روز`), the
harakat of a quoted reading (`نَامَه`, `خِدْمَت`, `غَم`), and the non-breaking
hyphen or tatweel of a suffix (`‑ی`, `ـناک`). A page that prints them over "no
entry", or a suffix with no gloss, is broken even though the data are right:
report the piece and the entry that should have been found.

## The rules of the reading

1. **The record is the only evidence.** Every finding quotes the line that
   contradicts the page — the etymology sentence, the gloss, the ancestor row.
   A finding with no quoted source is not a finding, it is a guess.
2. **Never invent a word, a law or a source.** If the fix needs a form the
   corpus does not hold, the finding says so and the form is filed only from a
   page that records it (`ref` + `sources`), never from intuition.
3. **One pathway per lexeme.** A page that draws two rival analyses, or a
   construction whose pieces do not spell the word, is broken even if each
   piece is real.
4. **The band is a claim about the whole page.** "fully explained" above a
   `???`, a dark-red "no entry", a piece with no origin, or a timeline that
   stops short of PIE/outside the family is a lie the reader can see.
5. **A page is the meaning, the timeline and the sources.** Prose that explains
   the history instead of the word (dynasties, contact centuries, "this model
   explains...") is a finding of its own.
6. **Sample without looking at the band.** Random means random: a green page is
   as likely a subject as a yellow one, and a page that is *right* is worth
   saying so.

## What to check, in order of how often it is wrong

### 1. A piece points at the wrong word (`wrong_piece`)
The timeline says a construction's piece means something the record does not.
Worked example (admin, 2026-11-13): **fa دستمال** is "From دست (dast) + مال
(mâl-)" — the second piece is the present stem of **مالیدن** "to rub", not
Arabic **مال** "property", and the first is **دست** "hand", not Dehkhoda's
classifier homonym. Check every piece:
- does the gloss belong to the word the record names (the parenthetical, a
  trailing hyphen = a verb stem)?
- is the entry a homonym of the right spelling but the wrong sense?
- does the piece's own ancestry agree with the sense the child's sentence
  quotes?
Report: page, piece, what the page says, what the record says, and the entry
that should have been used (with its source line).

Two homonyms of one spelling are not interchangeable: آبرو's روی is "face",
not "bronze"; کمزور's زور is "strength", not the slang "cool"; باشنده's باش is
the present stem of بودن, not the jade. The record usually says which: a
parenthesis (`مال (mâl-)`), a phrase (`present stem form of بودن`), or the
child's own meaning. A piece that points at the wrong homonym is a finding of
kind `wrong_piece`, severity high, and it needs the entry that should have been
used.

### 2. An irrelevant meaning (`bad_gloss`)
The headword's gloss does not describe the word: metalinguistic text ("Used in
the singular with a subsequent ezâfe..."), a Dehkhoda editorial note, a
definition of a homonym, or a gloss in the wrong language. This is how a
wrongly matched word shows itself; find the sense that *is* the word and name
the entry it comes from.

### 3. A broken hierarchy or timeline (`broken_timeline`)
- the rail does not reach the top, or a rung floats with no parent and no
  terminal;
- a construction's pieces do not spell the headword;
- the same stage appears twice, or a stage is skipped between two recorded
  forms;
- the piece's climb differs from that piece's own page (the 2026-11-13 rule: a
  piece brings its whole ladder);
- a derived rung is presented as a recorded entry, or vice versa.

### 4. A band the page contradicts (`band_overclaim`)
"fully explained" while the page draws a `???`, "no entry for this word", a
piece with no recorded origin, or a step the record itself hedges. Also the
reverse: a page that explains everything and still reads partial without a
named reason.

### 5. The timeline against the etymology text (`etym_disagrees`)
The ladder says one chain and the sentence another: a piece the sentence names
is missing, a piece the sentence does not name is drawn, the order of stages is
reversed, a stage the record names is skipped. Quote both.

### 6. The source is not linked (`unlinked_source`)
The entry says `wiktionary` (or the word has a Wiktionary page in the ledger)
but the page carries no W, or the W opens the wrong sense/article, or a
Dehkhoda source exists and the book icon is missing. `pie.service.word()`
carries `pages`/`sources`; an entry with an etymology taken from Wiktionary and
no `wiktionary` page is a finding.

### 7. Recorded, but no entry (`missing_entry`)
The record (Wiktionary, or the entry's own `anc`) names a form this model's
glossary of that stage does not head, while the page draws it as an ordinary
rung instead of "no entry". The word is then not fully explained. (A stage the
model holds no glossary for at all is different: it says so.)

### 8. Anything else that makes the page untrue
A wrong language, a wrong era, a wrong reading, a linked word that opens
another word, a red link that opens nothing, a duplicated row, a text that
names the wrong donor. Say what is wrong and quote it.

## The output

Write one JSON object per finding, one per line, to
`tiago/files/admin/pie-critic/findings-<batch>.jsonl`:

```json
{"lang":"fa","word":"دستمال","kind":"wrong_piece","severity":"high",
 "page_says":"مال · Arabic · property, wealth",
 "record_says":"From دست (dast) + مال (mâl-) — the present stem of مالیدن",
 "evidence":"dehkhoda: fa/دستمال etym; fa/مالیدن entry",
 "fix":"use the verb stem مالیدن (to rub) for the piece, and دست noun 'hand'",
 "source":"https://en.wiktionary.org/wiki/دستمال"}
```

`kind` is one of the seven above (`wrong_piece`, `bad_gloss`,
`broken_timeline`, `band_overclaim`, `etym_disagrees`, `unlinked_source`,
`missing_entry`, `other`). `severity` is `high` (the page is false),
`medium` (the page misleads), `low` (cosmetic). Then write a short markdown
report for the batch with a table, the three worst cases quoted in full, and a
"pages that are right" count — a critic that only ever finds faults cannot tell
whether the model is improving.

## After the batch

The super agent fixes what it can, adds the reusable class to
`tools/critic.py` so the next batch finds it mechanically, records the rule in
`AGENTS.md` and `docs/DECISIONS.md`, and spawns the next critic on a fresh
random sample (a word may not be reviewed twice unless a fix changed it).
