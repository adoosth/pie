# Avestan, third pass: read the record, and cite the stem

**Status:** merged (2026-11-09). Two artefacts, no new sound law.

## What was wrong

The second pass measured Avestan at 6 explained of 352 and said the figure was
not a missing law. It was right about that and wrong about nothing else, but it
stopped at the diagnosis. Two facts stood in the way:

1. **313 of the 352 Avestan entries carry no IPA.** The orthographic layer ends
   its match with a guard — the derived phonemes must have the same consonant
   skeleton and vowel count as the dictionary's own pronunciation
   (`spelling.plausible`) — so a corpus with no pronunciation confirmed nothing.
   Five words were counted as spelled; twenty-nine spell the record exactly.
2. **Avestan is cited by the stem.** The laws end at the nominative (aspō),
   the dictionary's lemma is the stem (aspa), and `data/citation/` could only
   *drop* an ending (Sanskrit deváḥ → devá-), never replace one (aspō → aspa-).

## The two claims

**1. A writing with one value per letter is its own reading.**
The Avestan script is an alphabet (Hoffmann & Forssman 2004, pp. 44-46), so a
word's letters *are* its pronunciation: 𐬀𐬵𐬨𐬀 is ahma. The Avestan spelling
file now declares `guard: {reading: avestan}`, and `spelling.record_reading`
falls back to that reading when an entry has no IPA. The guard still runs; it
just has something to compare against.

The reading is **not** the writer run backwards. The writer spells a glide
between vowels with the matching vowel doubled (𐬌𐬌 ii, 𐬎𐬎 uu), and the reader
keeps both signs: 𐬀𐬎𐬎𐬀 reads *auua*, never *ava*. Of the 29 words whose letters
the layer spells, **26 are confirmed and counted** as spelled, one needs no law
at all (𐬞𐬀𐬌𐬭𐬌 pari, counted as unchanged) and **three are turned away** — the
test is not decoration:

| word | record reads | laws write | verdict |
|---|---|---|---|
| 𐬀𐬎𐬎𐬀 | auua | ava | turned away: the record has a glide, the laws have v |
| 𐬥𐬀𐬎𐬎𐬀 | nauua | nava | turned away, same reason |
| 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀 | xšaθriia | xšaθriya | turned away: y against the recorded ii (the entry's own IPA writes /j/) |

The letters 𐬗 and 𐬘 are one letter each, written c and j by this layer and č/ǰ
by a dictionary; that fold is declared in the file's `guard.equivalences` and it
is *notation*, not a relaxation — it changes no letter of the manuscript
(𐬗𐬀 is counted as spelled *ča*).

**2. A citation may replace a stem vowel, not only drop an ending.**
`data/citation/ave.yaml` declares four pairs — -ō for -a (a-stems, aspō ~
aspa-), -əm for -a (neuter a-stems, xšaθrəm ~ xšaθra-), -iš for -i (i-stems,
čistiš ~ čisti-) and -uš for -u (u-stems, ərəzuš ~ ərəzu-), citing Hoffmann &
Forssman and Skjærvø. The rest of the form must still spell the lemma exactly
and the guard must still confirm the stem, so the column cannot absorb a word
the laws got wrong in the middle.

## The numbers

| | before | after |
|---|---|---|
| Avestan explained | 6 / 352 | **60 / 352** |
| — of which spelled (orthographic) | 5 | 26 |
| — of which cited as the stem | 0 | 33 |
| — of which exact (laws) | 0 | 0 |
| corpus explained | 14,224 | **14,278** |
| corpus exact | 6,415 | 6,415 (unchanged) |
| corpus orthographic | 4,831 | 4,852 |
| other languages | — | not one number moved |

Avestan's `exact` stays 0 and always will while its record is the script: an
exact match is a character-for-character comparison between the laws' output and
the word a dictionary writes, and no Latin-alphabet derivation can be the
Avestan word. Its explanations are therefore spelled words and cited stems, and
the coverage table says so.

## Review (the five questions)

1. **Is the claim stated?** Yes, two sentences: *a faithful alphabet is its own
   reading, and a language may cite the stem whose vowel the nominative ending
   replaces.*
2. **Is the evidence independent?** The reader is tested against the letter
   table it inverts, one letter at a time, and against the words it must reject
   (the glide pairs). The citation pairs are four paradigms with several words
   each from different etyma (aspa- h₁éḱwos, akō ákas, xšaθrəm kšatrám,
   čistiš, ərəzuš, bāzuš).
3. **Does it over-apply?** No other language declares a reader, and no other
   citation file carries `cited_as`; a full run changed exactly one row.
   `data/coverage.json` was diffed language by language: `ave` alone moved.
4. **Is the tier honest?** Both artefacts are *orthographic / citation* facts,
   never sound laws, and both are counted in their own columns. The reading is
   a fact about how the script is written; the citation is a fact about how the
   dictionary cites.
5. **Is the artefact shaped right?** Two coherent changes: a spelling file with
   its guard, and a citation file with its four pairs; plus the mechanism each
   needed, its tests (`tests/test_batch_ave3.py`, 9 tests) and the regenerated
   reports.

## What was refused

- **Reading the Wiktionary `translit` as the IPA.** Cheap and wrong: only 11 of
  the 181 transliterations round-trip through the letter table, and the field is
  contaminated with readings that belong to other languages — 𐬓𐬀 is glossed
  `svá` (Sanskrit), 𐬀𐬵𐬨𐬀 `asmā́n`, 𐬛𐬀𐬉𐬥𐬁 `dyn'` (Pahlavi), 𐬑𐬱𐬀𐬚𐬭𐬀 `kṣatrá`.
  Using it would have imported other languages' words as Avestan evidence.
- **Waiving the guard outright** for languages without IPA. It would have
  accepted *ava* for 𐬀𐬎𐬎𐬀 and *nava* for 𐬥𐬀𐬎𐬎𐬀 — the exact coincidence the
  guard exists to stop. Reading the letters instead keeps the check.
- **A new sound law.** None was needed for any of the 54 words; every one of
  them was explained by a citation or a spelling fact. The remaining 292 misses
  are law-shaped and are the next worklist item (see below).

## What is left in Avestan (measured, not guessed)

- 292 words with a recorded ancestor still unexplained. The dominant signature
  is still phonological (*ay > aē, *-ah > -ō/-əm, anaptyxis in clusters,
  *θr/*θw), which is law work, and the orthographic reading now makes a law's
  effect visible the moment it is right.
- One notation fold is missing: Avestan y is IPA /j/ (xšaθriya against
  /xʃaθrija/). It is a fold in the guard, not a rule, and it needs its own
  review because j is also the letter for /dʒ/.
- 157 entries carry neither a transliteration nor an IPA (171 have no
  transliteration, 313 no IPA); the reading now covers every word whose letters
  the table owns, which is why the misses can be blamed on the laws again.
