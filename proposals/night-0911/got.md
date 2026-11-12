# Gothic: the last transition, and the alphabet

Specialist: Gothic (`got`). Scope: `data/spelling/got.yaml`,
`data/rules/gem-pro__got.yaml`, three source entries in `data/sources.yaml`,
this file. Nothing else was touched (`src/`, `tools/`, `tests/` untouched; no
commit).

## 1. What was added

**`data/spelling/got.yaml`** — the writing layer for Wulfila's alphabet, 29
ordinary `match`/`replace` rules on the orthographic tier (a letter table, not
a syllabification, because the alphabet is one letter per segment).  Digraphs
are ordered before single letters: `/ɛː/` = ai 𐌰𐌹, `/ɔː/` = au 𐌰𐌿,
`/iː/` = ei 𐌴𐌹, `/iu/` = iu 𐌹𐌿, `/ʍ/` = ƕ 𐍈, `/kʷ/` = q 𐌵,
`/gʷ/` = g𐍅; then one letter each for a b g d e z h þ i k l m n j u p r s t w
f o.  Length is *not* written, so the same letter writes short and long a, e, u,
o (`(a|ā)` → 𐌰, `(e|ē)` → 𐌴, `(u|ū)` → 𐌿, `(o|ō)` → 𐍉); that is the
alphabet's convention, not a sound change.  Word-final -s needs no rule of its
own — it is the letter s, stated in its own description.  Two rules that
existed only for the short vowels (`letter_e` on `e`, `letter_o` on `o`) never
fired on any derived form, because the transition sends every short *e to i or
/ɛː/ and Gothic has no short o; they were merged into the short/long rules
rather than left dead.

**`data/rules/gem-pro__got.yaml`** — 26 established rules, orders 5–75:
consonants (hw kw gw as single segments, *jj > ddj, *ww > ggw), breaking,
`*e > i`, `*ai > /ɛː/`, `*au > /ɔː/`, `*ē/ū` before a vowel, and the endings.
Every rule has a `references` key, a prose statement and a conditioning
environment where the change is conditioned, and one example `check-rules`
verifies.

**`data/sources.yaml`** — `braune-ebbinghaus` (Braune & Ebbinghaus, *Gotische
Grammatik*), `wright-1910` (Wright, *A Grammar of the Gothic Language*, 1910),
`krause-1968` (Krause, *Handbuch des Gotischen*).

**Citation level (honest limitation).**  The references are to the grammars as
works; I did not add §/page numbers, because this session is offline and I will
not invent a paragraph number I cannot check.  Section-level pointers are left
for review (W6) with the books at hand.

## 2. Numbers

Command: `PYTHONPATH=src python3 tools/coverage.py --langs got --limit 0`
(the run writes no docs, so `--out /tmp/...` was added to read the JSON).

| measure | before | after |
|---|---|---|
| exact (historical) | **0** / 2,260 | **0** / 2,260 |
| orthographic | **0** | **276** (12.2 % of the glossary) |
| explained (any layer) | 0 | 276 |
| tested | 1,887 | 1,887 |
| identified (has a modelled ancestor) | 1,971 | 1,971 |
| errors during derivation | 0 | 0 |

`PYTHONPATH=src python3 -m pie.cli worklist --lang got`

| measure | before | after |
|---|---|---|
| spelled correctly by the orthographic layer | 0 | **203** |
| miss signatures | none (no comparison) | 30 signatures, 35 words blamed on `gem-pro→got` |
| `gem-pro→got` under "rule files that do not exist" | listed, blocking `got` | **gone** |
| dead rules / sterile rules in this transition | — | **0 / 0** |

**Why `exact` is still 0, and why that is the honest number.**  `exact`
compares the laws' phonemic output with the headword the glossary records —
here a string in Wulfila's alphabet (𐌷𐌿𐌽𐌳𐍃).  No sound law can write that
string; only the writing layer can.  Gothic is therefore in the position of
Old Persian and Sanskrit: its claim is an orthographic one.  Nothing was
bent to move this number (no case folding, no transliteration shortcut in the
historical column), and the orthographic number is kept in its own column.

**Why the worklist says 203 and coverage says 276.**  `coverage` tries the
orthographic layer on *every* recorded ancestor (PIE and Proto-Germanic);
`audit` (the worklist) probes only the single nearest candidate form.  Both are
the tools' own definitions; neither was changed.

**No previously matching word was lost.**  Before this work Gothic had 0
matches of either kind, so the floor was 0; every rule was also measured by
ablation (§3), and no rule with a positive effect was left out.

## 3. Every rule, its citation, and its measured effect

Effect = words lost from the 276 when that one rule is switched off (ablation
over all 1,887 tested entries).  A rule at 0 still fires, but no *counted* word
depends on it yet.

| # | rule | statement | citation | effect |
|---|------|-----------|----------|--------|
| 5 | `hw_to_labial` | *hw is one segment /ʍ/, written ƕ | Braune/Ebbinghaus, Wright, Krause | 0 (fires; orthography) |
| 6 | `kw_to_labial` | *kw is one segment /kʷ/, written q | same | 7 |
| 7 | `gw_to_labial` | *gw is one segment /gʷ/, written g𐍅 | Braune/Ebbinghaus, Wright | 0 (fires; orthography) |
| 10 | `jj_to_ddj` | *-jj- > -ddj- (*dajjaną > daddjan) | Braune/Ebbinghaus, Wright | 0 (daddjan has no IPA) |
| 11 | `ww_to_ggw` | *-ww- > -ggw- (*trewwō > triggwa) | Braune/Ebbinghaus, Wright | 0 (triggws blocked by IPA `ɡʷ`) |
| 20 | `breaking_i` | *i > /ɛː/ before r, h, ƕ | Braune/Ebbinghaus, Wright, Krause | 1 |
| 21 | `breaking_u` | *u > /ɔː/ before r, h, ƕ (*hurną > haurn) | same | 11 |
| 22 | `breaking_e` | *e > /ɛː/ before r, h, ƕ (*weraz > wair) | same | 16 |
| 30 | `e_to_i` | remaining *e > i (*meluks > miluks) | same | 38 |
| 40 | `ai_to_long_open_e` | *ai > /ɛː/ (written ai) | same | 24 |
| 41 | `au_to_long_open_o` | *au > /ɔː/ (written au) | same | 12 |
| 50 | `e_long_before_vowel` | *ē > /ɛː/ before a vowel (*wēaną > waian) | Braune/Ebbinghaus, Wright | 2 |
| 51 | `u_long_before_vowel` | *ū > /ɔː/ before a vowel (*būaną > bauan) | same | 1 |
| 52 | `final_ijan_to_jan` | *-ijaną > -jan (*sandijaną > sandjan) | same | 23 |
| 55 | `final_ą_loss` | word-final *-ą is lost (*akraną > akran) | same | **131** |
| 60 | `final_er_to_ar` | *-ēr > -ar (*brōþēr > brōþar) | Braune/Ebbinghaus, Wright | 0 (r-stems lack IPA) |
| 61 | `final_ijaz_to_is` | *-ijaz > -īs (*mēkijaz > mēkeis) | same | 8 |
| 62 | `final_jaz_to_jis` | *-jaz > -jis (*harjaz > harjis) | same | 1 |
| 63 | `final_az_to_s` | *-az > -s (*hundaz > hunds) | same | **46** |
| 64 | `final_iz_to_s` | *-iz > -s (*aihtiz > aihts) | same | 5 |
| 65 | `final_z_to_s` | word-final *-z > -s (*sunuz > sunus) | same | 19 |
| 66 | `final_d_to_th` | final *-d > -þ after a vowel (*gōdaz > gōþs) | same | 6 |
| 67 | `final_b_to_f` | final *-b > -f after a vowel (*hlaibaz > hlaifs) | same | 3 |
| 71 | `final_ō_to_a` | word-final *-ō > -a (*gebō > giba) | same | 12 |
| 72 | `final_ǭ_to_ō` | word-final *-ǭ > -ō (*sunnǭ > sunnō) | Braune/Ebbinghaus, Wright | 7 |
| 73 | `final_ô_to_a` | word-final *-ô > -a (*maþô > maþa) | same | 21 |
| 74 | `final_ê_to_ē` | word-final *-ê > -ē (*þandê > þandē) | Braune/Ebbinghaus, Krause | 1 |
| 75 | `final_į̄_to_ī` | word-final *-į̄ > -ī (*managį̄ > managei) | Braune/Ebbinghaus, Wright | 5 |

Writing rules were measured by the same ablation on their own file (letter
counts are not individual claims: every letter rule is required for any word to
be written at all).  The three rules that most shaped the table were measured
against their alternatives in §4.

## 4. Rejected rules, with the number that killed them

| proposed rule | what it would do | measured verdict |
|---|---|---|
| **word-final *-ą > -a** (as the brief suggested) | *akraną > *akrana, *juką > *juka | **refuted**: of the 1,748 Proto-Germanic ancestors, 587 end in *-ą, and 470 of them show -n (not -na) in the Gothic record (akran, juk, gras, haurn, tagr).  The corpus supports loss, not lowering. |
| word-final *-ô > -ō (all an-stems) | *maþô > *maþō | **refuted for the class**: 5 neuters want -ō (augō, hairtō, namō, ausō, underō), ~90 masculines want -a (maþa, guma, atta, blōma, batiza).  Gender is not in the form, so the majority class (-a) is registered; the 5 neuters are a paradigm gap (W5), and one of them (augō) is fixed only by its own PIE path. |
| final *-g > -h (devoicing of g) | *wainagaz > wainahs | **rejected**: gains 6 (wainahs, ainahs, stainahs, ganōhs, slahs, þlauhs), loses 35 (dags, wigs, mēgs, daigs, manags, hailags, grēdags).  The recorded difference is lexical, not phonological (hailagaz > hailags beside wainagaz > wainahs). |
| *-er- > -ar in an unstressed syllable | *anþeraz > anþar, *unseraz > unsar | **not expressible honestly**: 6 words (anþar, ƕaþar, unsar, izwar, unkar, igqar) would gain, but the environment is *unstress*, and the derived forms carry no stress mark here; every positional statement ("e before r") would also rewrite *weraz > wair, which must break.  Left as a gap (W5/W4), not written as a per-word rule. |
| *-raz > -r | *weraz > wair | **one word**: wair.  fagrs and the rest keep -s, so the rule would be a rule about a word. |
| *-ōu > -au | *ahtōu > ahtau | **one word** (ahtau). |
| *s-k > z-g (Verner in *askǭ) | *askǭ > azgō | **one word** (azgō). |
| final *-t > -þ | *melit > miliþ | **one word** (miliþ). |
| general *-ij- > -j- (not only the infinitive) | 80 verbs fixed, but *fijandz > fijands would become fands | **rejected as too broad**: the corpus has 3 forms of *fijandz that keep -ij- (fijands, fijand); the narrow class-1 infinitive rule (*-ijaną > -jan) keeps them and still wins 23 counted words. |
| keep *ai / *au as diphthongs | *stainaz > stainaz | **rejected**: costs 24 + 12 = 36 counted words, because the dictionary's IPA writes the monophthongs /ɛː/ and /ɔː/ (paying for `spelling.plausible`) and the digraphs of the alphabet are then written from one segment. |
| devoice b/d/g only after a short vowel (env `left: V`) | gōþs, dauþs | **rejected as written**: 272 instead of 276, because a long vowel written `ɛ ː`/`ɔ ː` is two segments and the environment missed *dauþs and *hlaifs-type forms.  The registered environment is `(V|ː)`. |
| keep *hw as h + w | *sehwaną > sehw... | **rejected**: the alphabet has one letter (𐍈) for the one segment; the same holds for *kw (q 𐌵) and *gw (g𐍅). |

## 5. The remaining gap, by class (with examples)

Of the 1,887 tested entries: 276 counted, 598 spelled correctly but **not
countable**, 51 spelled correctly but **rejected by the IPA guard**, 288 with
**no modelled ancestor**, and 963 with a derivation that does not reach the
headword.

1. **No recorded pronunciation (598).**  Only 695 of the 2,260 Gothic entries
   carry an IPA, and `spelling.plausible` refuses a spelling match without one
   (by design: a letter table can concatenate the right word from wrong
   sounds).  Examples that the table already writes exactly but cannot claim:
   harjis 𐌷𐌰𐍂𐌾𐌹𐍃, aljis 𐌰𐌻𐌾𐌹𐍃, daddjan 𐌳𐌰𐌳𐌳𐌾𐌰𐌽, ahtau 𐌰𐌷𐍄𐌰𐌿,
   waihts 𐍅𐌰𐌹𐌷𐍄𐍃.  This is a W1 data task (IPA), not a rule task.
2. **IPA notation the guard does not fold (51).**  The transition writes b d g f
   h and reads them back as the dictionary writes them; the dictionary
   sometimes writes the fricatives instead: fadar [ˈfaðar], dags [daxs],
   magan /ˈmaɣan/, aba /ˈa.βa/, þiuda [ˈθiu̯ða], fidwōr /ˈɸid.woːr/, ƕar
   /ʍar/, saiƕan /sɛ.ʍan/, triggws /ˈtriɡɡʷs/.  Writing β/ð/ɣ/ɸ/x/ʍ in the
   phonemic layer instead would *cost* the 250+ words whose IPA uses b d g f h,
   so it is not done; the fix belongs in `spelling._IPA_FOLD` (W7).
3. **Breaking in unstressed syllables (the largest remaining sound-law gap).**
   Breaking is registered before r, h, ƕ without a stress condition, so it also
   fires where Gothic did not break: anþeraz > anθɛːrs (want anþar), hwazuh >
   ƕazɔːh (want ƕazuh), unseraz > unsɛːrs (want unsar), izweraz > izwɛːrs
   (want izwar).  The forms carry no stress token, so the condition cannot be
   stated; the honest register for it is a paradigm/stress stream (W5) that
   hands the transition a stressed form.
4. **Weak-neuter -ô (5).**  augô, hairtô, watō, namō, ausō end in -ō while the
   masculine an-stems end in -a; the form does not carry gender.
5. **Final -g (6).**  wainahs, ainahs, stainahs, ganōhs, slahs, þlauhs show -h
   beside dags and hailags, lexically.
6. **Morphological citation differences and suppletion.**
   fōtus (the glossary cites a different cell than *fōts), triu (*dóru path),
   iddja (*gāną, suppletive), witān/witān (class-3 *-āną vs class-1 *-ijaną),
   and compounds recorded with a space (sehs tigiwis → 𐍃𐌰𐌹𐌷𐍃 𐍄𐌹𐌲𐌾𐌿𐍃).
7. **No ancestor in the model (288).**  Greek and Latin loans with no Germanic
   chain: aggilus (gr. ἄγγελος), kaisar (la. Caesar), paitrus (gr. Πέτρος).
   These need a loan layer, not a sound law.

## 6. Gates

- `PYTHONPATH=src python3 -m pie.cli check-rules` → **0 problems**, 751 examples
  verified (all sound-law *and* all Gothic spelling examples).
- `PYTHONPATH=src python3 -m unittest discover -s tests -q` → **373 of 374
  pass** (the suite grew while other sessions added tests).  The one
  failure is the test that this change makes stale:
  `tests/test_web.py::test_incomplete_chains_are_reported_not_faked` asserts
  that `got` is a *gap language* of the ētymon *nókʷts, i.e. that
  `gem-pro→got` does not exist.  It now does, so Gothic is derived instead of
  reported as a gap.  The test file was not edited (it is outside this
  session's write scope); the expectation needs updating by the integrator
  (e.g. assert on `non`, which still has no transition file).

## 7. For review (W6)

- The `hw/kw/gw → single segment` rules are stated in the *sound-law* file
  because they are phonemic claims; the letters are then written by the
  spelling file.  A reviewer may prefer them in a reading table
  (`data/script/got.yaml`), which this session was not allowed to create.
- `final_d_to_th` and `final_b_to_f` are illustrated on the intermediate form
  the ending rules produce (*gōds > *gōþs), not on the Germanic citation form;
  the reason is stated in their `notes`.
- Section/page numbers for the three grammars are still to be added (§1).
