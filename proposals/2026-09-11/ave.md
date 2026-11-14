# Avestan writing layer — the alphabet, and what it wins

**Date.** 2026-11-09.
**Files.** `data/spelling/ave.yaml` (new), `src/pie/writing.py` (the `avestan`
writer), `src/pie/transforms.py` (`transform: avestan`), `tests/test_ave.py`
(new, 14 tests), `data/rules/ira-pro__ave.yaml` (one law added),
`src/pie/translit.py` (seven reading-table bugs fixed). Nothing committed.
**Method.** Every number comes from the repo's own counters:
`tools/coverage.py --langs ave --limit 0` and `tools/whatif.py`. Nothing here
is fitted to a word: the table is the alphabet as Hoffmann & Forssman describe
it, and a word matches only if the letters that table produces are the letters
the manuscript writes.

## 1 · What the table states

The Avestan script is an **alphabet**: 16 vowel letters and 37 consonants, one
letter per phoneme, length written, no inherent vowel. So unlike Old Persian's
syllabary, or Devanagari's abugida, writing a phonemic form needs no
syllabification rule — it is a transcription, and the whole alphabet is one
convention. `data/spelling/ave.yaml` is therefore one rule with one citation
(Hoffmann & Forssman, *Avestische Laut- und Flexionslehre*, 2nd ed. 2004,
pp. 44–46; Skjærvø 2009), plus three statements that are conventions rather
than substitutions:

- **Stress is not written.** The alphabet marks no accent, so `aˈēšəma` and
  `aēšəma` are the same word, and a reconstruction's accented capital
  (`Áryō`, PII `*Áryas`) is the plain vowel.
- **A glide between vowels is the vowel doubled.** *y* is 𐬌𐬌 *ii* and *w* is
  𐬎𐬎 *uu* — the signs the table reads /ii̯/ and /uu̯/: *friia-* 𐬟𐬭𐬌𐬌𐬀,
  *aēuua-* 𐬀𐬉𐬎𐬎𐬀, *daēuua-* 𐬛𐬀𐬉𐬎𐬎𐬀. Next to a consonant each keeps its
  own letter (𐬫, 𐬬).
- **The doubled sign is the glide's own vowel**, so it is written once when the
  vowel before it is already that letter: *xšaθriya-* is 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀 with two
  i, not three. My own first cut wrote three and the corpus caught it — that is
  the one defect this report found in its own table, and it is now a test.

Nothing is a sound change, nothing turns one form into another, and a match is
counted in the orthographic column, never in `exact`. A character the table does
not own (a laryngeal that survived, a nasal vowel the phonological layer does
not produce) is kept as written, so it cannot pass as a spelling.

**Eight letters the table carries but no headword uses:** 𐬒 x́, 𐬕 ġ, 𐬣 ŋ́,
𐬤 ŋᵛ, 𐬩 m̨, 𐬪 ẏ, 𐬮 l, 𐬅 ą̇. They are in the writer, so a future word with one is
written correctly, but no headword of the 352-word glossary writes one and the
last phonological stage never produces them, so today they neither win nor lose
a word. `tests/test_ave.py` pins that the unexercised set is *exactly* those
eight, so the table cannot quietly grow a letter nothing earns.

The writer and the reader of the alphabet are inverses: 350 of 352 headwords
round-trip (`transliterate` → `avestan` = the headword). The two that do not
carry punctuation (⸱) the writer does not own.

## 2 · Measured

```
PYTHONPATH=src python3 tools/coverage.py --langs ave --limit 0
```

| | before | after |
|---|---:|---:|
| glossary | 352 | 352 |
| identified (a modelled ancestor) | 312 | 312 |
| **exact (sound laws)** | 0 | **0** |
| **orthographic** | 0 | **7** |
| cited as stem | 0 | 0 |
| identity (no law fired) | 0 | 1 |
| **explained** | **0** | **8** |

The seven spellings are 𐬀𐬞 *ap*, 𐬁𐬙𐬀𐬭 *ātar*, 𐬀𐬵𐬨𐬀 *ahma*, 𐬐𐬀𐬭 *kar*,
𐬨𐬀𐬥 *man*, 𐬥𐬏 *nū*, 𐬰𐬁𐬥𐬎 *zānu*. `exact` stays 0: no word became a
sound-law reconstruction, which is the point of keeping the layer separate.

## 3 · The ceiling, stated plainly

`spelling.plausible` requires a recorded pronunciation: a spelling match counts
only when the derived phonemes have the skeleton and the syllable count of the
entry's own `/.../`. That gate is right — for a lossy orthography two wrong
vowels can concatenate into the right letters — but it makes the IPA count the
real ceiling here:

- **39 of 352 entries carry an IPA** (11.1%). 313 cannot be scored through this
  layer at all, whatever the table says.
- **31 headwords are spelled letter-for-letter by the current laws**; 8 of those
  have an IPA and are counted (7 spelled + the one that the y/j fold still
  blocks, §6.2).
- So **23 more words would already be won if the other 23 had a recorded
  pronunciation.** The layer is not the bottleneck; the dictionary's IPA
  coverage is.

An Avestan headword is written in a script that marks every vowel and every
length, so a letter-exact spelling is arguably its own pronunciation check
(see §6.3 and §9). That is a proposal, not a shipped change: relaxing the guard
is exactly the kind of edit that must not be made quietly the day before a
report.

## 4 · Why the other 32 IPA-bearing words still miss

Every one of these was run through the same `derive()` the counter uses; the
"chain gives" column is the last modelled stage's output, and "spell" is what
this table writes for it.

| # | word | IPA | chain gives → spell | verdict |
|---|---|---|---|---|
| 1 | 𐬀𐬯𐬞𐬀 *aspa* | /aspa/ | Haspō → aspō | (d) citation: the dictionary cites the stem, the laws end in the nom. -ō |
| 2 | 𐬀𐬱𐬙𐬀 *ašta* | /aʃta/ | Haštā → aštā | (d) citation: nom./acc. -ā vs stem -a |
| 3 | 𐬎𐬛𐬭𐬀 *udra* | /udra/ | udrō → 𐬎𐬛𐬭𐬋 | (d) citation |
| 4 | 𐬎𐬱𐬙𐬭𐬀 *uštra* | /uʃtra/ | uštrō | (d) citation |
| 5 | 𐬐𐬁𐬨𐬀 *kāma* | /kaːma/ | kāmō | (d) citation |
| 6 | 𐬞𐬎𐬚𐬭𐬀 *puθra* | /puθra/ | puθrō | (d) citation |
| 7 | 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀 *xšaθriia* | /xʃaθrija/ | xšaθriya → 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀 ✓ | **letters exact** — the guard's segment fold reads IPA *j* ≠ notation *y* (§6.2) |
| 8 | 𐬫𐬀𐬰𐬀𐬙𐬀 *yazata* | /jazata/ | yazatō | (d) citation **and** the same y/j fold |
| 9 | 𐬀𐬉𐬱𐬆𐬨𐬀 *aēšəma* | /aeːʂəma/ | ayšmō → aēšmō | (a) ə not produced; (d) -ō |
| 10 | 𐬀𐬌𐬠𐬍 *aibī* | /aibiː/ | abi | (a) final -ī, and the epenthetic i (§6.4) |
| 11 | 𐬀𐬉𐬥𐬀𐬵 *aēnah* | /aˈeː.nah/ | aynō → aēnō | (a) *-ah# > -ō is applied where the record keeps -ah (stem) |
| 12 | 𐬀𐬴𐬀 *aṣ̌a* | /aʂa/ | ərətō | (c) the recorded ancestor is a different lexeme (*h₂r̥tós 'truth' vs the chain's *Hŕ̥šah 'bear' shape) |
| 13 | 𐬓𐬀 *xᵛa* | /xʷa/ | hvō | (a) no law turns *sw- into xᵛ- |
| 14 | 𐬔𐬀𐬊𐬱𐬀 *gaoša* | /ɡao.ʃa/ | gavšō | (a) PIr *au > ao not applied on this path; (d) -ō |
| 15 | 𐬛𐬀𐬉𐬎𐬎𐬀 *daēuua* | /dai̯uu̯a/ | dayvō | (a) the diphthong is written aē, and the glide is uu here, not v |
| 16 | 𐬚𐬭𐬌 *θri* | /θri/ | θrayō | (c) the record is the i-stem θri-, the chain's *θrayah is another class |
| 17 | 𐬛𐬀𐬥𐬙𐬀𐬥 *dantan* | /dantan/ | dantā | (d) the record cites the participle stem in -ant- |
| 18 | 𐬞𐬌𐬙𐬀𐬭 *pitar* | /pitar/ | ptā | (d) kinship r-stem: the record cites pitar-, the laws give the nom. ptā (the same split that `peo~pal:r_stem_oblique` carries for پدر) |
| 19 | 𐬟𐬭𐬌𐬌𐬀 *friia* | /frija/ | frīō | (a) ī where the record has short i; (d) -ō |
| 20 | 𐬞𐬁𐬜𐬀 *pāδa* | /paːða/ | pādō | (a) *d > δ in this position is not a law; (d) -ō |
| 21 | 𐬛𐬎𐬱𐬨𐬀𐬥𐬀𐬵 *dušmanah* | /duʃmanah/ | dušmanāh | (a/d) the record is the -ah stem, the laws lengthen to -āh |
| 22 | 𐬠𐬭𐬁𐬙𐬀𐬭 *brātar* | /braːtar/ | brātā | (d) r-stem cited whole (as #18) |
| 23 | 𐬠𐬏𐬨𐬌 *būmi* | /buːmi/ | būmiš | (d) nominative -š vs the stem |
| 24 | 𐬨𐬀𐬌𐬥𐬌𐬌𐬎 *mainiiu* | /ˈmai̯nʲii̯u/ | manyuš | (a) the record is the u-stem mainiiu-; ń + y written ii |
| 25 | 𐬨𐬀𐬉𐬖𐬀 *maēγa* | /mai̯ɣa/ | maygō → maēgō | (a) γ vs g; (d) -ō |
| 26 | 𐬬𐬆𐬵𐬭𐬐𐬀 *vəhrka* | /ˈwər̥ka/ | vərəkō | (a) *r̥ > ərə is right but the h and the -ō are not |
| 27 | 𐬫𐬏𐬲𐬆𐬨 *yūžəm* | /juːʒəm/ | yūs | (a) ž lost and ə not produced |
| 28 | 𐬨𐬄𐬚𐬭𐬀 *mąθra* | /mãθra/ | manθrō | (a) the nasal vowel ą is not produced (*-an- before a consonant); (d) -ō |
| 29 | 𐬨𐬂𐬢𐬵𐬀 *måŋha* | /mɒŋha/ | māō | (a) *-aH- > å is not a law on this path |
| 30 | 𐬯𐬁𐬭𐬀 *sāra* | /saːra/ | sərəō | (a) *r̥ > ərə applies where the record has a plain r |
| 31 | 𐬰𐬀𐬭𐬀𐬦𐬌𐬌𐬀 *zarańiia* | /zaraɲia/ | zərəanyəm | (a) ń, and the nominal ending |
| 32 | 𐬬𐬍𐬯𐬞𐬀 *vīspa* | /wiː.spa/ | vispō | (a) ī vs i; (d) -ō |

Counted: **6 are the citation question only** (#1–6), **2 are the guard's y/j
fold** (#7, #8), and **24 need a sound law or a stem class the model does not
have.** In 15 of the 24 the citation question is *also* present, so the two
layers compound.

## 5 · Shipped with this report: the missing initial *H law

`data/rules/ira-pro__ave.yaml` already said "A word-initial *H is handled by
the older rule that names it" — and no such rule existed in the Avestan stage.
The Old Persian stage has it (`laryngeal_loss_initial`, order 2). It is one
`sound law, added with the same id, text and citations:

```
# before installing, from the candidate file (proposals/2026-09-11/ave-h.yaml):
PYTHONPATH=src python3 tools/whatif.py --from ira-pro --to ave --rules proposals/2026-09-11/ave-h.yaml
  explained before: 5   after: 7  (+2)   gained: 𐬀𐬞, 𐬁𐬙𐬀𐬭   lost: 0

# now that it is installed, the same measurement from the other side:
PYTHONPATH=src python3 tools/whatif.py --to ave --drop laryngeal_loss_initial --layers exact,orthographic
  explained before: 7   after: 5  (-2)   lost 2 word(s): 𐬀𐬞, 𐬁𐬙𐬀𐬭
```

Measured on the working tree after the law: 5 → **7** spelled, 0 → 0 exact,
nothing lost, `check-rules` 0 problems, the whole suite green apart from one
failure another batch's in-flight Gothic rules cause (§7). It also unblocks #1
and #2 above for the citation layer (`aspō` → *aspa*, `aštā` → *ašta*).

## 6 · Measured proposals, deliberately not shipped

Every number below was measured with the same `derive()` + `spelling.spell()` +
`spelling.plausible()` chain the counter uses. None of them is in the tree.

**6.1 · A citation layer, `data/citation/ave.yaml`** (the sa precedent). A
dictionary cites an Avestan noun by its stem (Skjærvø 2009; Hoffmann &
Forssman 2004 on the a-stem nominative -ō), while the laws end where the
recorded ancestor ends, in the nominative. `citation.py` today only *strips* an
ending, which is enough for Sanskrit (deváḥ → devá) and not for Avestan
(udrō → udra needs `-ō` **replaced** by `-a`, not dropped). With the pairs
`ō→a, ā→a, əm→a, uš→u` the gain is:

- without the *H law: **+4** (udrō, uštrō, kāmō, puθrō);
- with it: **+6** (those four plus aspō, aštā);
- and 23 more words of the corpus already reach the right letters this way but
  have no IPA to score against.

Cost: a `replace:` key in `data/citation/*.yaml` plus four lines in
`citation_hit()`. It touches `src/pie/citation.py` and `tools/coverage.py`,
both of which were being edited during this batch, so it is left for review.

**6.2 · Two notations of one glide (`y` / IPA `j`).** 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀 *xšaθriia* is
spelled exactly and still not counted, because `plausible()` compares the
engine's *y* with the dictionary's IPA *j* — the same segment in two alphabets,
which is exactly what `_IPA_FOLD` exists for elsewhere (ɡ/ɡ, ś/ɕ, ṣ/ʂ). A
`j → y` fold cannot be global (Persian writes *j* for /dʒ/, whose IPA dʒ folds
to ǰ), so the honest fix is a glide class in `_skeleton`. Gain: **+1** here now
(+2 with 6.1), unmeasured elsewhere.

**6.3 · `phonemic_script: true` for an alphabetic writing system.** The guard
exists because a lossy orthography can make two wrong vowels concatenate into
the right letters. In a script that writes every vowel and every length, the
letters determine the phonemes: a letter-exact spelling *is* the pronunciation
check. Declaring that per language would score 23 more Avestan words that have
no IPA — but it is a change to the meaning of a green, so it belongs in a
decision entry with a reviewer present, not as an urgent patch.

**6.4 · The epenthetic i.** *airiia-* is written a-i-r-i-i-ā, with an i between
a and r that carries no phoneme (Hoffmann & Forssman's *Gleitlaut*); the same
habit gives *aibī* its i. It affects one headword here (`𐬀𐬌𐬭𐬌𐬌𐬋`, whose
chain gives Áryō) and I could not state the environment from the corpus, so it
is not in the table. A grammar citation of the exact § would add it.

## 7 · Bugs found

1. **The reading table misread seven letters** (`src/pie/translit.py`,
   fixed). 𐬓 was read *x́* (a second sign for 𐬒 instead of xᵛ), 𐬕 *ǵ* (ġ),
   𐬂 *ą* (å), 𐬃 *ą̄* (ā̊), 𐬅 *ą̄* (ą̇), 𐬧 *n* (ṇ), 𐬪 *y* (ẏ). **40 headword
   readings changed, 31 of them a real letter** (19 headwords with 𐬧, now *ṇ*:
   𐬀𐬧𐬙𐬀𐬭𐬆 *aṇtarə*; 8 with 𐬓, now *xᵛ*: 𐬓𐬀 *xᵛa*; 4 with 𐬃, now *ā̊*: 𐬥𐬃
   *nā̊*; 1 with 𐬂, now *å*: 𐬨𐬂𐬢𐬵𐬀 *måŋha*. The other 9 are punctuation the
   reader used to drop or keep, and one Devanagari entry). The entry's
   own IPA backs the å: 𐬨𐬂𐬢𐬵𐬀 is /mɒŋha/. Readings are display only — no
   matching path reads an automatic transliteration — so no count moved.
2. **A stage note named a rule that did not exist** (§5): the Avestan file's
   `laryngeal_lengthening` said a word-initial *H "is handled by the older rule
   that names it", and the Avestan stage had no such rule. Fixed.
3. **My own glide table wrote iii for ii** (fixed in the same commit's file,
   pinned by a test): *xšaθriya-* came out 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬌𐬀. The fix is the
   "written once when the vowel before it is that letter" rule now in §1.
4. **The worklist probes the spelling layer on one candidate only** (found, not
   fixed). `src/pie/audit.py` calls `spell_probe` on `best.output`, the single
   candidate nearest to the attested word by Latin edit distance, and for a word
   written in another script that distance is noise. It reports **6** spelled
   words for Avestan where `tools/coverage.py` reports **7**; the missing one is
   𐬥𐬏 *nū*, whose nearest-Latin candidate is *nu* (one letter short of ū) while
   another recorded ancestor of the same word gives *nū*, which spells exactly.
   It is the same defect the counter had before 2026-11-09 (`orthographic_hit`
   now tries every candidate). The fix is to probe every candidate, as the
   counter does, but it moves the worklist's published column for every
   language, so it is left for review rather than changed at 02:00.
5. **Not mine:** `tests/test_web.py::test_incomplete_chains_are_reported_not_faked`
   fails because a concurrent batch's in-flight `data/rules/gem-pro__got.yaml` means
   Gothic is no longer an incomplete chain. Left alone.

## 8 · Reproduce

```
PYTHONPATH=src python3 tools/coverage.py --langs ave --limit 0 --out /tmp/ave.json
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest tests.test_ave -q
node tests/test_ui_render.js
```

Restart the server to see it on a word page: `𐬀𐬵𐬨𐬀` now carries
`written: 𐬀𐬵𐬨𐬀`, `written_match: true` and a "spelled" badge beside the ladder
that says the sound laws stop at *ahma*.

## 9 · What a future pronunciation layer would need

The layer's real bottleneck is not this table. 313 of 352 Avestan entries carry
no `/.../`, and the guard (rightly) refuses to score a spelling without one. Two
honest routes, in the order I would take them:

1. **More recorded IPA.** Wiktionary has it for 39 of 352 here; the Avestan
   dictionaries (Bartholomae's *Altiranisches Wörterbuch*, airWb) print a
   transcription for every lemma. An ingest of that column, cited, would let
   this layer score the 23 words it already spells and the 23 the citation layer
   reaches.
2. **A declared phonemic script** (§6.3), per language, with the argument
   written down: an alphabet that writes every vowel and length makes its own
   letters the pronunciation evidence. That would cover the 313 without
   inventing a single transcription — but it changes what a green means, so it
   needs a decision entry, not a patch.
