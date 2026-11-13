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

## Where a ladder may begin (Old Persian round 1, 2026-11-13)

Four faults of the same shape — the timeline explaining a *different* word:

- **a root named by the ancestry** is a relation, not a start (𐎠𐎿𐎲𐎠𐎼 ran
  from *h₁eḱ "horse", one piece's root, and printed **aθ**);
- **an aside ancestor** (`derived … whence spear`) may not outrank the inherited
  chain when the laws do not reach the word from it (𐎠𐎼𐏁𐎫𐎡𐎣 printed the
  spear's reading as the spearman's);
- **a compound's cognate set** belongs to one piece (Vahumanāh ← PIE "good");
- **a hedged etymology** ("uncertain; possibly related to") is a relation, and a
  ladder may not start there (𐎱𐎠𐎼𐎿 → pˈarθuš).

A critic reports each as `broken_timeline`, quoting the sentence and naming the
form the word's own row must print. Since 0.17.23 a differing last rung also
carries a sentence («the laws produce X, not the recorded Y») — its absence is a
finding.

### What the Old Persian rounds added (2026-11-13)

- **Two readings of the same signs are not one reading.** A syllabary writes its
  vowels, so *r̥štiš* and the laws' *arštˈiš* are different words even though the
  consonant skeleton agrees. A ✓ beside the first while the page prints the
  second is a `band_overclaim`.
- **A bound piece is not a letter.** −𐎠/−𐎣/−𐎹 must not resolve to the entry of
  the sign 𐎠, and a band may not say «no recorded origin for Old Persian 𐎣»
  over a suffix the record glosses.
- **A branch starts from a reading.** "The record gives no reading" beside a
  reading the page prints is a contradiction; so is a cuneiform form copied into
  the Pahlavi row.
- **The sampler has two layers.** `sample --layered` takes half a batch from
  entries that state an origin: a sample of etymology-less one-line headwords
  tests nothing.

## Other languages (from the Old Persian round on)

The rules do not change with the language; the *evidence* does. What to read
first in each one:

- **Persian (fa)** — Dehkhoda's own entry (`vajehyab.com/dehkhoda/<word>`) is
  the definition; the entry's first clause is often notation (a respelling, a
  comparative etymology list, the name a name entry is about), so check that
  the page's meaning is the clause that actually defines the word.
- **Old Persian (peo)** — the writing is a **syllabary**. A rung can only climb
  from a *reading*: the entry's `translit`/`phon`, the language's spelling
  table, or a reading the corpus quotes. A page whose cuneiform form has no
  reading, or whose reading disagrees with the entry's own transliteration, is a
  broken rung — the laws were handed a syllabary and refused it (`unreadable`).
  A form the record quotes that the glossary does not head must print **no
  entry**, and its Proto-Iranian/PII/PIE rungs must each be entries of their
  stage. Wiktionary: `Reconstruction:Old_Persian/<form>` and the attested
  article.
- **Middle Persian (pal)** — the Book Pahlavi spelling is ambiguous; the entry
  needs a transliteration (MacKenzie's) before anything can be derived. A page
  that shows a Book Pahlavi word with no reading, or that treats a Manichaean
  spelling as another Book Pahlavi spelling of the same word, is a finding.

A batch on a new language starts with `tools/critic.py sample --lang <code>`;
if its Persian-oriented filters starve the sample, take the words from
`data.lexicon(<code>)` by hand and say so in the report.

## Persian, round 4 (batch 11)

- **A parenthesis after a piece belongs to that piece** — جانشین's
  «جا (“place”) + نشین present stem of نشستن» gave the verb to جا. Report the
  piece and the entry the parenthesis names.
- **A suffix or prefix is chosen by what the sentence says it does**, never by
  the first homonym: اسبی's ـی is «suffix forming adjectives», not the
  indefinite article; بجای's بـ is the preposition, not the subjunctive prefix.
- **Dehkhoda states etymology in the gloss** («مرکب است از جه … و مرز …»,
  «اصل در آن تایب آباد بوده و تایباد مخفف آن است») while the page says «no
  recorded etymology» — that contradiction is a finding.
- **A name entry's notice is not a meaning**: اعبدة opens «[ اَ ب ُ دَ ] (اِخ )»,
  اردشیرگان quotes Hamza al-Isfahani, تایباد adds a biography.

## Persian, round 5 / Old Persian, round 4 (2026-11-13, second half)

- **A spelling capital is not a sound.** A reconstruction is often written with
  a capital (`*SáraswatiH`), and the laws match literal tokens, so `s_to_h`
  never fires on the first letter: the page prints `SˈarahwatiH` beside a record
  that says the PIr form begins in *h*. Report it as a `law_not_applied`, with
  the position — but say plainly that folding the capital alone does not close
  the word (`*ā`, `*ī` length is unmodelled too), so it is a *model* gap, not a
  page bug.
- **A reconstruction records the page it was read from.** Every reconstructed
  headword carries `Reconstruction:<language name>/<word>` as its `url`; an
  entry with no W beside a Wiktionary reconstruction that clearly exists is a
  `missing_source_link`, and so is a *supplement* row with no `source`.
- **An ancestor the record names is an entry.** 𐏃𐎼𐎢𐎺𐎫𐎡𐏁's record says
  «from Proto-Iranian *HárahwatiH»; if the rung prints «no entry» the glossary
  is incomplete, and filing the ancestor is the fix — the verdict then says what
  is really missing (here: the laws produce Sˈarahwatī, not Harauvatiš).
- **A name entry is a last resort for a meaning.** When Dehkhoda's only entry is
  a proper name (غزالی، اعبدة، اردشیرگان), the page must say so in the meaning
  line; it must not borrow the biography as a definition. (Open question for the
  admin: whether such a page should carry a meaning at all.)

## What the branch still gets wrong (peo-04 diagnosis, 2026-11-13)

The descendant panel is the last place a page answers with a *form* where it
should answer with a *word*. Measured on 532 Old Persian pages: 447 fa and 447
pal rows, 236 carrying a recorded entry; of the first 60 fa rows ~40 gloss an
unrelated word, several with a ✓ — 𐎠𐎿𐎫𐎡𐎹 «to be» → fa **است «bone»**,
𐎠𐎼𐎫 «truth» → **آرد «flour»**, 𐎠𐎭𐎶 «I» → **ای «that is to say»**,
𐎱𐎠𐎮𐎹 «to protect» → **پا «leg»**, dariš «golden» → **در «door»**.

Three distinct causes, and they need three different fixes — do not "fix" them
by hiding the branch:

1. **`_near_record`/`_reading_index` return the first entry of a spelling**
   (fa است heads «bone» before the copula). The fa pieces already solve this
   with `_homonym_by_meaning`: gather every entry the reading can be, then pick
   the one whose meaning the carried sense asks for. Thread the sense down
   `_stage_descendants → _branch_children → _branch_node` (the origin entry's
   gloss is the only sense a page has).
2. **A form coincidence wears the ✓.** 𐎠𐎭𐎶 *adam* → fa *ay* «that is to say»
   is the laws' output landing on an unrelated Persian word; the Persian “I” is
   من. A ✓ needs *both* the form and the sense; with neither evidence a row may
   show the form the laws produce and no record at all.
3. **The laws themselves are wrong for that word**: peo 𐎠𐎿𐎫𐎡𐎹 is fa است
   (*ast*, no final -iy), so no homonym choice can rescue it — that is a missing
   law (OP final -iy > NP ∅), and the row must say *differs*.

**The band contradicts its own ladder on 37 pages** — the verdict names a hole
(«no entry for Proto-Iranian *Habí») while the same page's rung at that stage is
marked `matches: true`. Read the JSON before believing it: `matches` is about
the laws' output, `known` is about the entry, and the two lookups should never
be asked to agree on different keys.

**Ātr̥pātah explains the wrong half of its own name**: the record says
*HáHtr̥š + *paHtáh, the page draws the ladder of «protected» and prints it as
the word. A compound whose record states its pieces must draw those pieces.
