# Persian and Middle Persian — 2026-11-09

Scope: a Perso-Arabic reading layer for `fa`, a cited Middle→New Persian law
set, and the Middle Persian reading coverage that both depend on.  Nothing here
is a lookup: the script table says what a letter *can* say, the readings table
copies what the record *does* say, and every sound law is cited, exemplified
and ablated on the whole corpus.

Commands that produced the numbers:

```bash
PYTHONPATH=src python3 tools/coverage.py --langs fa pal --out /tmp/fanight-before.json
PYTHONPATH=src python3 tools/coverage.py --langs fa pal --out /tmp/fanight-after.json
PYTHONPATH=src python3 tools/whatif.py --from pal --to fa --rules <candidate> --layers exact,orthographic
PYTHONPATH=src python3 tools/whatif.py --to fa --drop <rule-id> --layers exact,orthographic
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

## Before / after

| | fa before | fa after | pal before | pal after |
|---|---|---|---|---|
| glossary rows | 5,555 | 5,555 | 616 | 616 |
| identified (has a modelled ancestor) | 1,692 | 1,692 | 61 | 61 |
| **exact** (laws, character for character) | **0** | **0** | **1** | **1** |
| **orthographic** (writing conventions) | **130** | **207** | 0 | 0 |
| **script** (spelling read sign by sign) | **0** | **299** | 1 | 1 |
| identity (spelling right, no law fired) | 15 | 65 | 0 | 0 |
| **explained** (all honest columns) | **145** | **373** | 2 | 2 |
| readings `data/readings_pal.json` | 280 | **600** | 280 | **600** |

`exact` stays 0 for fa and 1 for pal: no registered rule chain yet turns a
recorded ancestor into a Persian headword *letter for letter in Latin
transcription*.  The gain is in the two layers the programme keeps separate
(spelling and script) and in the data that lets the laws see Middle Persian at
all — never in the historical figure.

## 1. Middle Persian readings: 280 → 600 spellings

`tools/build_pal_readings.py` now has a third source beside MacKenzie's headword
line and the shipped Wiktionary extraction: **the repo's own etymology
sentences**, which quote the Middle Persian spelling with its reading
(`𐭠𐭥𐭣 (ʾʿd /ud/)`, `LHMA (nān, “bread”)`, `ʾp̄ (āb)`).  The sentences were
already in `data/lexicon/*.jsonl.gz`; nothing is typed in by hand.

- A pair is kept only if the spelling's **signs can spell the reading**, tested
  through the letters the signs stand for (`𐭪` k/g, `𐭥` w/ō/ū/r), or if the
  spelling is a heterogram written in capitals (read as a whole word, its value
  the dictionary's own).
- A form quoted with two different readings is **left out**, not chosen between
  (12 forms).
- 324 spellings added from etymology sentences; 234 forms refused because the
  signs cannot say the reading.
- One real defect repaired: the glossary headword `ŠM` was paired with `pad`
  (the first word of MacKenzie's bracket `pad '''nām''' ī yazdān`).  The
  reading of a spelling headword is the word MacKenzie prints in bold, so `ŠM`
  is now `nām`, as the Persian entry and the bracket itself say.
- Tiers stay honest: `recorded` (MacKenzie headword line) 201, `quoted` (a
  Wiktionary sentence or page) 359, `script-quoted` (an Arameogram read as a
  whole word) 40.

Effect: fa spelling 130 → 195 and identity 15 → 68 **before any new law**,
because 323 of the 670 Middle Persian spellings the Persian ancestry cites now
have a reading (was 66).

## 2. Persian script layer: `data/script/fa.yaml` (new)

The abjad matcher that reads Book Pahlavi now reads the Perso-Arabic script:
one sign per letter of the reading in order, an unwritten short vowel costs no
sign, no written letter goes unaccounted for.  42 letters are listed, each with
the sounds it can spell (ا as a vowel seat, آ, و = /v/ ū /w/, ی = /j/ ī /i/,
ه = /h/ -e, the Arabic loan letters ث ص ض ط ظ ح ذ, the hamza seats, the Arabic
spellings ي ك ة ى), and every one is exercised by a recorded Persian word
(`tests/test_fa_script.py` fails on a sign no word writes).  Conventions stated
and documented rather than enforced by the table: short vowels unwritten, the
initial alef seat, word-final -a/-e written ه, the shadda as a mark (U+0651 is
combining, so a geminate costs one letter), the historic و of خواب/خواهر, and
the Arabic tanwīn marks.

The silent و is the honest boundary the task named: خواب is read **xwāb** by
the letters, and modern /xāb/ is a *sound change* (`xw_to_x_initial`), not a
reading convention.  So `match("fa","xwāb","خواب")` is true and
`match("fa","xāb","خواب")` is false — and the spelling layer, which runs from
xwāb, still writes خواب correctly.

Result: **script 0 → 299**.  The column is audited, because two leniencies are
the matcher's and not the table's:

- length folds (ā and a are one letter), so نام cannot tell nām from nam;
- an unwritten short vowel of the reading may pass a written sign unspent.

Audit of the 288 script hits reproduced directly: **74** are identical to the
dictionary's own romanisation, **190** share its consonants and differ only in
short-vowel quality (a permitted reading of an abjad), **24** read و/ی as a
vowel where the dictionary reads a glide (still a possible reading of the
letter, but not the word's reading).  No hit has a consonant the spelling does
not write.  This is why script stays out of the historical figure.

## 3. pal → fa sound laws

Accepted (each cited, each ablated on all 1,692 tested words with
`--layers exact,orthographic`):

| rule | order | claim | gain | loss |
|---|---|---|---|---|
| `a_to_o_after_w` | 13 | MP *wa > NP wo (xwadāy > xwodāy > xodā) | +2 (پروردن, گوزن) | 0 |
| `final_ig_to_i` | 15 | MP final -īg > NP -ī (pārsīg > pārsī) | +7 (بینی, تهی, درزی, روزی, زنگی, پارسی ×2) | 0 |
| `final_ih_to_i` | 63 | MP final -īh > NP -ī (xwadāyīh > xodāyī) | +2 (پیروزی, گرمی) | 0 |

Order is load-bearing and measured: `final_ig_to_i` at order 61 (after
`long_e_to_long_i`) **loses دیگ** (dēg is *-ēg, not *-īg); at order 15 it loses
nothing.  `a_to_o_after_w` must run before `xw_to_x_initial`, which deletes its
conditioning *w.

Rejected, with the numbers that rejected them:

- **`final_long_a_y_loss`** (MP final *-āy > NP -ā, `match: "ā y"`, env right
  `#`): measured **+3 / −0** (هما, پا), but (i) the corpus records no سرای from
  *sarāy*, so the rule would silently change a word the literature says keeps
  the glide — a lexical exception the segmental environment cannot state; and
  (ii) it breaks the project's invariant that a pal→fa law leaves `xadāy`
  unchanged and the r̥-stem pathway of پدر intact
  (`tests/test_web.py::TestTheFinalLongA`).  Kept out; the missing پا stays a
  miss and is published as one.
- **`final_agan_to_egan`** (MP -agān > NP -egān): **0 / 0** — fires nowhere the
  corpus can see.  A dead rule is a false claim, so it is not registered.
- Narrowing `w_to_b_initial`: dropping it **gains 3** (ویس …) and **loses 18**;
  the 3 are written with و but have /v/ from Proto-Iranian *w, and the pal
  stage cannot tell the two sources apart without the earlier stage's history.
  The rule stays as it is, and the false positive is on the record here.

Existing laws ablated (what each carries): `long_e_to_long_i` 49,
`long_o_to_long_u` 36, `final_ag_to_e` 30 (and +1 سگ when dropped),
`w_to_b_initial` 18, `u_to_o` 10, `i_to_e` 9, `v_to_b_initial` 2,
`xw_to_x_initial` 0 in fa (it still feeds xodā through the pathway).

## 4. The orthographic file: a measured negative result

No new convention was added to `data/spelling/fa.yaml`, because the remaining
misses are not spelling gaps.  Of the 1,692 tested words, 207 are now spelled
and 65 more have the right spelling with no law firing.  The next classes are:

- **52** words whose spelling is already exact but whose phonemes the
  dictionary's IPA rejects (`درخت` is spelled right from *draxt*, but the word
  is darraxt; `گروه` from *grūh*, but goruh).  Persian breaks initial clusters
  with an epenthetic vowel, and the rule language's `replace` is a literal
  string with no back-reference, so a general epenthesis law cannot be written
  here.  That is a sound-law and pattern-language task, not an orthographic
  one.
- **morphology**: the ancestry often records a present stem or a 3sg
  (`dārayad`, `barad`, `rīd`) while the headword is the infinitive
  (داشتن, بردن, ریدن).
- **unread spellings**: transliterations such as `hʾmwš`, `plwhtn'` reach the
  spelling layer as Latin letters (see §7).

## 5. Files changed

- `data/script/fa.yaml` — new: 42 signs, 6 conventions, cited to Thackston 1993
  and Windfuhr 2009 (2009 handbook).
- `data/rules/pal__fa.yaml` — three proposed laws (§3) and the stage text.
- `data/readings_pal.json`, `tools/build_pal_readings.py` — etymology source,
  heterogram/bold-reading rule, refusals counted.
- `data/sources.yaml` — one appended entry, `thackston-1993`.
- `tests/test_fa_script.py` — new: signs exercised, conventions declared,
  written consonants read, unwritten short vowels free, no forgiveness of an
  unwritten consonant, the vowel seat, final ه, ZWNJ, and the two documented
  leniencies.

## 6. Remaining ceiling (what the model still cannot reach)

- **fa, whole glossary (5,555)**: 3,134 recorded as borrowed, 604 outside the
  modelled chain, **2,567 non-Indo-European** at the root.  These are not
  failures of the laws; they are vocabulary the family model does not claim.
- **fa, no pronunciation**: 397 rows have no IPA at all (139 of the 1,692
  tested).  Without a pronunciation the *spelling guard* cannot confirm a
  written form, so those words can be read sign by sign but never "spelled".
- **fa, no Middle Persian ancestor**: 903 of the 1,692 tested words start from
  PIE/Proto-Iranian/Old Persian only; no pal→fa law can help them.
- **fa, unread Middle Persian spellings**: 670 Middle Persian spellings are
  cited by Persian ancestry; **323 now have a reading, 347 still do not**
  (mostly Arameograms and OCR-damaged transliterations the signs refuse).
- **pal**: of the 616 MacKenzie rows, 544 still carry no etymology (the
  dictionary's remit), so only 61 are measurable; 37 glossary headwords are
  spellings with no reading.  Across every language, 722 Middle Persian
  spellings are cited and 344 have a reading.
- **exact = 0**: with the readings now in place the laws can *reach* many
  Persian forms (`xāne`, `gurbe`, `rang`), but no chain is yet registered from
  the Middle Persian stage to the attested Persian headword letter for letter;
  closing that is the next exact-number task, not this batch's.

## 7. Gates

`pie check-rules`: 0 problems, 28 rule files, 618 rules, 852 examples verified,
spelling files ang ave de en enm fa gmh gmw-pro goh got grc it la sa.
`unittest discover -s tests -q`: green (446→454 tests; the count moves because
other batches are adding modules concurrently).
