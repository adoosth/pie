# Middle Persian: the wall was the alphabet

**Date.** 2026-11-09.
**Scope.** `pal` (Middle Persian) and the Persian words that record a Middle
Persian ancestor. Read the report of the miss audit first
(`proposals/night-0911/miss-surgery.md` §1.1): 382 of Persian's 1,516
path-bearing misses never start, because the ancestor is a Pahlavi spelling.
This report builds what the record allows, measures it, and names what it does
not.

Nothing here bends a target, adds a per-word rule or changes a recorded
ancestor. Every reading in the table is copied from a source and carries its
locator.

## 1 · Inventory

`data/lexicon/pal.jsonl.gz` holds **616** entries. The Persian glossary records
**720** Middle Persian ancestor links (**575** distinct spellings). Each one,
by what it is written with:

| what the ancestor is | occurrences | distinct | reading now resolved | distinct resolved |
|---|---:|---:|---:|---:|
| Book / Inscriptional Pahlavi script | 270 | 203 | 28 | 23 |
| Manichaean script | 44 | 40 | 5 | 4 |
| Psalter Pahlavi script | 4 | 4 | 0 | 0 |
| Avestan script (mis-filed as `pal`) | 8 | 5 | 0 | 0 |
| transliteration, consonants only | 329 | 264 | 47 | 38 |
| heterogram (Aramaic ideogram) | 13 | 11 | 1 | 1 |
| Latin, with vowels | 52 | 48 | 0 (already readable) | 0 |
| **total** | **720** | **575** | **81 (11%)** | **66 (11%)** |

`pal` headwords themselves: 519 Latin, 71 transliterations (ʾ, ʿ, ḥ, p̄ …),
2 Manichaean script, 24 other. **597 of 616 entries carry a `translit`
field**, and that field is the dictionary's own headword line
(`abag [LWTE < A … | M y ygt N (a) d]`): its first token is the spelling, and
the entry's `word` is the reading. So the record *does* state a reading for
about 464 entries — the join is the problem, not the absence of data.

## 2 · The script table

`data/script/pal.yaml` (new): **51 signs**, each with the sounds it can write,
and two conventions.

* **Book Pahlavi / Inscriptional Pahlavi** (19 signs used) is an Aramaic-derived
  abjad. It writes no short vowel, and three classes of sign are polyphonic:
  𐭥 = w, r, ʿ; 𐭬 = m, q; kaph/pe/taw write g/b/d as well. Values after
  MacKenzie 1971 (`mackenzie-1971`).
* **Manichaean** (23 signs used) is alphabetic and marks the long vowels with
  ʾ, y, w. Values after Durkin-Meisterernst 2014
  (`durkin-meisterernst-2014`).
* **Psalter Pahlavi** (11 signs used) has the same letter inventory; it is in
  the same table with its own signs.

Conventions: `short_vowels_unwritten` (what the matcher uses) and
`final_silent_letter` (MacKenzie's closing apostrophe, `swk'`).

The matcher (`script._align_letters`, new) is the abjad half of the Old
Persian model: each sign must take exactly one letter of the reading, from the
sounds that sign can stand for; a short vowel the reading has and the script
does not write costs no sign; a vowel *written* by a sign may not be dropped.
Nothing else is forgiven.

    script.match("pal", "sang", "𐭮𐭭𐭢")   # True  (s-n-g, short a unwritten)
    script.match("pal", "sng",  "𐭮𐭠𐭭𐭢")   # False (the ʾ writes a vowel)
    script.match("pal", "daw",  "𐫅𐫏𐫇")     # False (y is ē/ī, not a)

## 3 · The reading table

`data/readings_pal.json` (new, built by `tools/build_pal_readings.py`):
**280 spellings → reading**, each row with its source and tier.

| source | rows | tier |
|---|---:|---|
| MacKenzie's headword lines (phonetic spellings) | 90 | `recorded` |
| MacKenzie's headword lines (Aramaic ideograms) | 29 | `recorded` |
| MacKenzie's headword lines (spelling-headed entries) | 83 | `recorded` |
| Wiktionary Middle Persian entries (`ts=`, in `data/readings_pal_wiktionary.json`) | 78 | `quoted` (38) / `script-quoted` (40) |

A pair is kept only when the reading is **spellable by the spelling**: every
consonant of the reading is written by a sign that can spell it, and no sign is
left unexplained. That check is what refuses the ingest's damage:
**338 of 466** headword lines were refused, and the reason is visible —
Docling's 2014 conversion of MacKenzie's transliteration column reads aleph
(ʾ) as `y` and the closing apostrophe as `l` (`ypytl` for `ʾpʾt'`, `sit1` for
`slt'`), and prints `1` for `l`, `I` for `l`, `V` for `y`. A garbled key cannot
spell the reading stored beside it, so it is refused rather than repaired.
Repairing it would mean guessing per word, which is exactly what the project
rule forbids.

**Heterograms.** An Aramaic ideogram is not read letter by letter: `LWTE` is
not l-w-t-e, it is *abag*. 29 such readings are in the table under
`recorded`, each citing the dictionary entry they come from
(`MacKenzie 1971 s.v. abag`), and the script table deliberately says nothing
about them. Of the 11 heterogram spellings Persian records, **1** could be
joined to the dictionary; the other 10 (`BNPŠE`, `KDBA`, `KLYTA`, `KYNA`,
`TYMA`, `NKḆ`, `NPŠE`, `TYNA`, `Y`, `ŠM`) are spellings the pal glossary does
not hold under that form.

## 4 · Measured

`PYTHONPATH=src python3 tools/coverage.py --langs pal fa --limit 0`

| | before | after |
|---|---:|---:|
| fa explained | 118 | **139** |
| fa orthographic (laws + Persian writing) | 118 | **125** |
| fa identity (reading is already the form) | 0 | **14** |
| fa exact | 0 | 0 |
| pal explained | 1 | **2** |
| pal exact | 1 | 1 |

`tested` is unchanged (1,634 fa, 61 pal): no word entered the denominator
because of this layer, and no recorded ancestor was altered.

The 21 words: **7** are orthographic (the laws run from the dictionary's own
transcription and the Persian writing conventions spell the result) and **14**
are identity (the reading already is the attested form, so no law has to fire:
رنگ، اگر، نمک، پنیر، سال، شاه، لب، سنگ …). Examples of the orthographic ones: `𐭦𐭭𐭤` → *ēn* →
**این**, `𐭬𐭤` → *čē* → **چی**, `wʾčʾl` → *wāzār* → **بازار**,
**A bug found and fixed on the way.** `tools/coverage.py::_identity_hit`
compares the derived form with the entry's recorded transliteration through
`service.stress_only`, which answers **False for two identical forms when
neither writes an accent** (`stress_only("sang", "sang") == False`). So a
scripted word whose ancestor's reading is already the attested form could
never be counted at all. The comparison now accepts an exact equality before
asking about stress; the identity column goes 0 → 14, and the same fix applies
to every language (`tools/coverage.py`).

## 5 · What cannot be done, and the exact next step

**494 of the 575 distinct spellings still have no reading**, and no table can
give them one: the reading exists only in MacKenzie's printed dictionary, and
this repo's ingest of it lost the transliteration column to OCR noise. Adding a
sign value would be inventing vowels; adding a per-word reading would be
inventing a record.

Three exact routes, in order of yield:

1. **A clean machine-readable MacKenzie.** The dictionary is the source for
   every spelling Persian quotes. Re-converting the PDF with the transliteration
   column preserved (or keying the 464 brackets by hand, ~6 hours of work)
   would raise the join from 81 of 720 to an estimated 400+, because every
   refused pair above already *has* its reading in `word`.
2. **Wiktionary's own Middle Persian lemmas.** `en.wiktionary.org` has only
   **253** Middle Persian entries, of which 148 state a transcription; 87 of
   those survived the consistency check and are in the table. A `tr=`/`ts=`
   harvest of the full dump (rather than the category walk used here) would add
   the alternative-form spellings for words the category does not reach.
3. **A Pahlavi script reader with a lexicon.** For the 270 Pahlavi-script
   ancestors, the signs give the consonants and only a lexicon can give the
   vowels; the Manichaean spellings of the same words (44 in the corpus) often
   do write them, and 5 already joined.

Nothing in this layer claims a reading it was not given: `script.read` returns
`""`, the ladder keeps the spelling, and the word page shows what the record
states, with its source.

## 6 · Gates

* `check-rules`: 27 rule files, 569 rules, 770 examples, **0 problems**.
* `unittest discover`: **385 tests, OK** (10 of them new in
  `tests/test_pal_script.py`: every sign exercised by a recorded form, every
  convention present, every table reading spellable, unwritten short vowels
  free, a written vowel not droppable, a wrong vowel refused).
* `node tests/test_ui_render.js`: recorded starts, overall progress bar, join
  timeline and coverage buckets — ok.
* The full `coverage.py` run currently **aborts on Greek**:
  `data/rules/grk-pro__grc.yaml` (another agent's in-flight file) uses
  `transform: greek`, which `src/pie/rules.py` does not know yet. That is not
  this layer; the fa/pal run above is complete.

## Files

New: `data/script/pal.yaml`, `data/readings_pal.json`,
`data/readings_pal_wiktionary.json`, `tools/build_pal_readings.py`,
`tests/test_pal_script.py`, this report.
Changed: `src/pie/script.py` (reading table, abjad matcher, convention kinds),
`src/pie/service.py` (`_phonological_form` reads a recorded spelling),
`tools/coverage.py` (ancestors start from the recorded reading; identity bug).
