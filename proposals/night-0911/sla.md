# Proto-Balto-Slavic → Proto-Slavic: a measured candidate

**Status:** open (proposal only — nothing in `data/` was touched).
**Date:** 2026-11-09 (night probe, W4/W3).
**Artefact:** `proposals/night-0911/sla-candidate.yaml` (40 rules, `stage:` + `rules:`).
**Measured with:** `tools/whatif.py --from ine-bsl-pro --to sla-pro`, layer `exact`.

---

## 1. The gap this fills

The transition `ine-bsl-pro → sla-pro` has no rule file, so every Proto-Slavic
entry with a recorded ancestor derives to nothing: `derive()` records the
missing hop in `Derivation.skipped` and `coverage.exact_words` drops the word
before comparing (`if d.skipped: continue`).  That is also why
`pie worklist --lang sla-pro` reports no misses — there is nothing to miss.

1,993 of the 5,388 glossary rows are eligible (they carry an ancestor at a
modelled stage and are not borrowings): 939 record only a PIE etymon, 754
record a PBS ancestor *and* a PIE one, 300 only a PBS one.

## 2. How it was measured

`whatif.py` refuses a transition whose file does not exist
(`no rules file for ine-bsl-pro -> sla-pro`), and the task forbids writing into
`data/`.  The measurement therefore injects an **empty** ruleset for that key
in memory and lets the candidate supply the whole transition — exactly what the
tool does when it appends a candidate to an existing file:

```bash
PYTHONPATH=src python3 -c "
import sys, runpy
sys.path.insert(0,'src'); sys.path.insert(0,'tools')
import pie.data as d
from pie.rules import RuleSet
orig = d.rulesets
def patched():
    rs = dict(orig())
    rs.setdefault(('ine-bsl-pro','sla-pro'),
                  RuleSet.from_dict({'rules': []}, 'ine-bsl-pro', 'sla-pro'))
    return rs
d.rulesets = patched
sys.argv = ['whatif.py','--from','ine-bsl-pro','--to','sla-pro',
            '--rules','proposals/night-0911/sla-candidate.yaml','--layers','exact']
runpy.run_path('tools/whatif.py', run_name='__main__')
"
```

No `data/`, `src/`, `tools/` or `tests/` file was modified; nothing was
committed.

Rule-file contract check (same test `pie check-rules` applies to `data/rules`):
all **40 examples** were recomputed rule-by-rule and verified
(`r.apply(tokenize(in)) == out`), every rule states its `tier` explicitly, and
every rule cites at least one source key.

## 3. Result

| | entries | head-words |
|---|---|---|
| explained before | **2** | 2 |
| explained after | **502** | 494 |
| net gain | **+500** | |

502 / 1,993 eligible entries = **25.2 %** (the published `exact` counter);
1,491 entries remain unexplained.

Where the winning derivation starts: **432 from a PBS ancestor**, 70 from the
PIE etymon through the whole chain.

**Honest decomposition of the 502** (this matters, so it is stated up front):

- **500** are character-for-character identical to the PSl lemma *and* fire at
  least one historical law;
- **1** (`ne` ← PIE `*né`) is identical only because the stress-notation rule
  fires; no sound change happened.  It is counted by the tool's
  "at least one law fired" test, but it is not a historical win;
- **1** (`śěrъ` ← `*śáiˀras`, output `sěrъ`) is admitted only by the counter's
  stress leniency: `exact_kind` reads the acute of `ś` as a stress mark.  The
  letters differ and the claim is not character-for-character.

So the defensible headline is **500 strict, law-driven entries**; the tool's
`exact` layer prints 502.  The two notation rules (`stress_token_dropped`,
`register_mark_dropped`, tier `orthographic`) are unavoidable: the PBS record
writes stress as an acute and the acute register as `ˀ`, the PSl lemma writes
neither.  246 of the 502 cannot be matched at all without dropping `ˀ`, and 15
cannot be matched without dropping the stress token (its position also blocks
five conditioned laws, e.g. `*mangjás`).

## 4. Laws kept, with what each one carries

Δ = what the whole set loses when that law alone is removed (ablation, after
everything else is in place).  Sums do not add up: laws overlap, and a word
removed by one law is often re-derived through another recorded ancestor.

| # | law | tier | Δ |
|---|---|---|---|
| 1 | `stress_token_dropped` (notation) | orthographic | −15 |
| 2 | `register_mark_dropped` (notation) | orthographic | −246 |
| 3 | `palatal_s_to_s` *ś > s*, before the final-syllable laws | established | −4 |
| 4 | `palatal_z_to_z` *ź > z* | established | −12 |
| 5–6 | `nasal_front` *(e,i)+nasal > ę*; `nasal_back` *(a,u)+nasal > ǫ* | established | −18, −31 |
| 7 | `final_as_soft_to_yer` *-as > -ь* after a palatal | established | −13 |
| 8 | `final_as_to_yer` *-as > -ъ* | established | −162 |
| 9 | `final_us_to_yer` *-us > -ъ* | established | −7 |
| 10 | `final_is_to_yer` *-is > -ь* | established | −44 |
| 11 | `final_an_to_o` *-an > -o* | established | −22 |
| 12 | `final_long_s_dropped` *-s* lost after a long vowel | established | −6 |
| 13 | `initial_i_to_ji` *i- > jь-* before a consonant | established | −10 |
| 14 | `short_i_to_yer` *i > ь* (not after a vowel) | established | −48 |
| 15 | `short_u_to_yer` *u > ъ* (not after a vowel) | established | −36 |
| 16–19 | `ai_to_e_caron` *ai > ě*; `au_to_u` *au > u*; `ei_to_i` *ei > i* | established | −26, −46, −143 |
| 20–24 | `short_a_to_o` *a > o*; `long_a_to_a` *ā > a*; `long_o_to_a` *ō > a*; `long_e_to_e_caron` *ē > ě*; `long_i_to_i` *ī > i*; `long_u_to_y` *ū > y* | established | −127, −122, −21, −38, −52, −18 |
| 25 | `w_to_v` *w > v* | established | −94 |
| 26 | `ruki_s_to_x` RUKI *š > x* | established | −3 |
| 27 | `sk_to_sc` *sk > šč* before a front vowel | established | −2 |
| 28 | `gt_to_t_palatal` *gt > ť* | established | −7 |
| 29 | `bt_to_t` *bt > t* | established | −3 |
| 30–31 | `k_to_c_before_front`, `g_to_z_caron_before_front` (1st palatalisation) | established | −24, −18 |
| 32–33 | `kj_to_c`, `gj_to_z_caron` | established | −4, −4 |
| 34 | `x_to_s_caron_before_front` (2nd palatalisation) | established | −3 |
| 35–36 | `lj_to_l_palatal` *lj > ľ*; `rj_to_r_palatal` *rj > ř* | established | −10, −2 |
| 37–40 | `sj_to_s_caron`, `zj_to_z_caron`, `tj_to_t_palatal`, `dj_to_d_palatal` | established | −4, −2, −1, −4 |

Ordering that was measured, not guessed:

- **nasals before the final-syllable laws** (order 8).  After yers exist, the
  engine's `C` class counts `ь`/`ъ` as consonants and the nasal law over-fires
  (`*damús` → `dǫъ`); moving it earlier is worth **+17** with no loss.
- **`*ś > *s`, `*ź > *z` before the final-syllable laws** (order 7): a final
  `*-iś` must reduce like `*-is` (`*dalˀniś` → `dolnь`).  Worth **+11**, no loss.
- **yers before monophthongisation**, and the yers must not fire inside a
  diphthong (`env: left: !V`); without that guard `*nei` became `*neь` and 102
  words were lost.
- **`*k > *č` before front vowels excludes `j`**, with `*kj` and `*gj` handled
  as clusters that absorb the glide: **+7**.

## 5. Ten words won

| PSl | PBS (resp. PIE) ancestor | stage | laws that fired |
|---|---|---|---|
| `lava` | `lā́ˀwāˀ` | PBS | stress → ˀ → ā>a → w>v |
| `korva` | `kárˀwāˀ` | PBS | stress → ˀ → a>o → ā>a → w>v |
| `dobrъ` | `dabras` | PBS | -as>-ъ → a>o |
| `veslo` | `weslan` | PBS | -an>-o → w>v |
| `rěka` | `raikāˀ` | PBS | ˀ → ai>ě → ā>a |
| `gvězda` | `gwaizdā́ˀ` | PBS | stress → ˀ → ai>ě → ā>a → w>v |
| `kuna` | `kaunā́ˀ` | PBS | stress → ˀ → au>u → ā>a |
| `mǫžь` | `mangjás` | PBS | stress → an>ǫ → -as>-ь (after j) → gj>ž |
| `želǫdь` | `gelandis` | PBS | an>ǫ → -is>-ь → g>ž |
| `čьstь` | `kistis` | PBS | -is>-ь → i>ь → k>č |
| `zǫbъ` | `ǵómbʰos` | PIE | ḱ>ǵ… (PBS stage) → nasal ǫ → -as>-ъ |

(That is eleven rows; `zǫbъ` is the one full-chain example, to show that the
70 PIE-started wins come through the same transition.)

## 6. Laws tried and rejected — with the number that killed them

A rule was kept only if it gained **more than one** word (or belonged to a
natural class that did) and never if it cost more than the two accidental
identities discussed in §7.  Every number below is the whole-set change when
that one law is added or left out.

| candidate law | measured | verdict |
|---|---|---|
| `st > šč / _front` | **−16** (`blęsti, bresti, estь, gnesti, gъrstь, …`) | rejected: it destroys *st |
| `d > ∅ / _ C` | **−31** | rejected |
| `t > ∅ / _ s` | **−32** | rejected |
| word-initial `ę > ǫ` | **−3** (`ędro, ęga, ętro`) | rejected: the record keeps `ę-` |
| `ew > u` | **−1** (`devętъ`) | rejected |
| `us > ov` | **−3** (`duša, luskati, pustъ`) | rejected |
| `dl > l` | **−1** (`edlь`) | rejected |
| `sn > n` | **−1** (`sněgъ`) | rejected |
| `p > ∅ / _ s` | +1, loses `opsa` | rejected |
| `kt > ť` | +2, loses `telkti` | rejected |
| `pt > t` | +1, loses `čerpti` | rejected |
| `tt > st`, `dt > st` | 0 | rejected: fires nowhere |
| final `-t/-d` dropped | 0 | rejected |
| final `-m > ъ` | 0 | rejected |
| final `-s` lost after a consonant | 0 | rejected |
| final `-š > sь` | 0 | rejected (`voltьš` still fails elsewhere) |
| `nj > ň`, `mj > mľ`, `xj > š` | 0 | rejected: no gain |
| `tl > l` | 0 | rejected |
| `final_am_to_o` *-am > -o* | 0 with the rest in place (+3 in isolation) | rejected as redundant |
| `z > ∅ / _ s` (`maslo`) | +1 | rejected: one word |
| `k > ∅ / _ s` (`brutъ`) | +1 | rejected: one word |
| `č j > č` (`tъščь`) | +1 | rejected: one word |
| `š > ∅ / _ n` (`čьrnъ`) | +1 | rejected: one word |
| final `-os > ъ`, final `-es > e` | +1 each | rejected: one word each |
| `oi > ě` | 0 after the other vowels | **removed from the file** (measured dead) |
| final `*-om > *-o` | 0 | **removed from the file** (no PBS form in the corpus ends in `-om`; the `-am` spellings are covered by the other rules) |
| `ʔ` deleted | 0 | **removed from the file** (3 forms, none derivable) |

`tj > ť` survives with Δ = 1, but only because it is one of the four
*j*-cluster laws (`sj, zj, tj, dj`), which are one natural class; it is not a
one-word invention.

## 7. The two regressions

The empty transition scored **2** entries (their earlier-stage output already
equalled the PSl lemma).  Two laws change them:

- **`ba`** ← PBS `*ba`: `short_a_to_o` yields `bo`.  The record has both `*ba`
  (particle, "likely from PIE `*bʰoh₁`") and `*bo` (conjunction, from `*bʰo`);
  the derivation reaches the entry through the short-vowel ancestor, and `*bo`
  is itself won.  Losing `ba` costs one identity, and `a > o` is worth −127.
- **`esi`** ← PBS `*ési`: `short_i_to_yer` yields `esь`, but the athematic 2sg
  keeps `-i` (OCS `esi`).  This is a **morphological** exception, not a
  phonological one: conditioning `*i > ь` on a following consonant would save
  `esi` and lose six real words (`esmь, estь, gъrstь, nъ, sętь, čь`).

Both are reported, not hidden: the candidate's net is +500 on a base of 2.

## 8. What this candidate cannot do (needs another stream, not another rule)

Measured on the 1,491 unexplained entries, the residual differences are mostly
not sound laws:

- **Morphology (W5).**  `∅ → ъ` 169×, `∅ → ati` 92×, `∅ → iti` 73×, `∅ → ь` 54×,
  `∅ → ъkъ` 17×, `∅ → nǫti` 17× — the PSl lemma is a *derived* word (verb,
  diminutive, adjective) while the recorded ancestor is a bare root.
- **PIE ablaut already fixed in the record.**  `e → o` 124×, `e → a` 69× —
  `*gʷerH → gora`, `*gelH → golva` are o-grade forms; a sound law that turned
  every `e` into `o` would destroy `*nesti`, `*perti`, …
- **A gap in the PBS stage, not in this one.**  `e → ě` 34× (`*bʰedʰ → běda`,
  `*strel → strěla`) is laryngeal lengthening, which
  `ine-pro__ine-bsl-pro.yaml` only performs for `a + h₂`; `ъ → y` 11×
  (`*túh₂ → ty`) is the same missing `u + H` lengthening.  `e → ь` 91×
  (`*welH → vьlna`, `*dʰwer → dvьrь`) comes from syllabic resonants that the PBS
  file resolves as `*el/er` rather than `*ьl/*ьr`.
- **Orthographic/lexical noise.**  `s → ∅` 68× is mostly PIE *s*-mobile
  (`*(s)pey- → pila`, `*skerp- → čerpъ`); `e → ∅` 60× is PIE root material.
- **No transform exists** for the cluster simplifications that would be needed
  (`*ps > s`, `*ks > s`, `*zd > z` with a stated environment); each measured at
  ±1 word, so none was written.  Likewise there is no transform for
  "a rule that sees the segment before a stress token", which is why the
  notation rule is used instead of conditioning five laws on stress position.

## 9. Sources

The rules cite `fortson-2004` (already in `data/sources.yaml`) plus seven works
that are **not** in the store.  Per the task, `data/sources.yaml` was not
edited; the block below is a copy of it (all 59 stored entries) with the seven
new entries appended at the end.  Every key used by the candidate resolves
here:

| key | work | used for |
|---|---|---|
| `meillet-1934` | Meillet, *Le slave commun* (2nd ed., 1934) | vowel system, yers, final syllables, palatalisations |
| `vaillant-1950` | Vaillant, *Manuel du vieux slave* I (1950) | the same, plus the nasal vowels |
| `shevelov-1964` | Shevelov, *A Prehistory of Slavic* (1964) | relative chronology, monophthongisation, clusters |
| `derksen-2008` | Derksen, *Etymological Dictionary of the Slavic Inherited Lexicon* (2008) | item-by-item check of the lexemes cited |
| `olander-2015` | Olander, *Proto-Slavic Inflectional Morphology* (2015) | final `*-as/-us/-is`, `*-an`, the nominative in `*-ъ` |
| `kortlandt-1978` | Kortlandt, "On the history of the Slavic nasal vowels" (1978) | nasal vowels and their conditioning |
| `kortlandt-1994` | Kortlandt, "From Proto-Indo-European to Slavic" (1994) | the accent/notation question |
| `fortson-2004` | (already stored) | the satem/RUKI and laryngeal background |

```yaml
# copy of data/sources.yaml (unchanged) + the seven new entries appended at the end
- id: ringe-2006
  title: Ringe, From Proto-Indo-European to Proto-Germanic (2006)
  url: https://doi.org/10.1093/oso/9780199284139.001.0001
  kind: monograph
- id: ringe-2017
  title: Ringe & Taylor, The Development of Old English (2014); The Linguistic History of English (2017)
  kind: monograph
- id: kroonen-2013
  title: Kroonen, Etymological Dictionary of Proto-Germanic (Leiden Indo-European Etymological
    Dictionary Series 11, 2013)
  kind: dictionary
- id: kloekhorst-2007
  title: Kloekhorst, Etymological Dictionary of the Hittite Inherited Lexicon (2007)
  kind: dictionary
- id: fortson-2004
  title: Fortson, Indo-European Language and Culture (2nd ed. 2010)
  kind: handbook
- id: beekes-2011
  title: 'Beekes, Comparative Indo-European Linguistics: An Introduction (2nd ed. 2011)'
  kind: handbook
- id: szemerenyi-1996
  title: Szemerényi, Introduction to Indo-European Linguistics (1996)
  kind: handbook
- id: mayrhofer-1986
  title: 'Mayrhofer, Indogermanische Grammatik I/2: Lautlehre (1986)'
  kind: grammar
- id: hoffmann-forssman-2004
  title: Hoffmann & Forssman, Avestische Laut- und Flexionslehre (2nd ed. 2004)
  kind: grammar
- id: skjaervo-2009
  title: Skjærvø, The Avestan Language (Iranian Studies 37, 2009)
  kind: article
- id: kent-1953
  title: 'Kent, Old Persian: Grammar, Texts, Lexicon (2nd ed. 1953)'
  url: https://archive.org/details/old-persian-grammar-texts-lexicon
  kind: grammar
- id: mackenzie-1971
  title: MacKenzie, A Concise Pahlavi Dictionary (1971/2014)
  kind: dictionary
- id: durkin-meisterernst-2014
  title: Durkin-Meisterernst, Grammatik des Westmitteliranischen (2014)
  kind: grammar
- id: skjaervo-2009b
  title: Skjærvø, Middle Persian (in The Iranian Languages, ed. Windfuhr 2009)
  kind: chapter
- id: windfuhr-2009
  title: Windfuhr (ed.), The Iranian Languages (2009)
  kind: handbook
- id: korn-2016
  title: Korn, A New Locative Case in Transitional Middle Persian (2016); Iranian sound changes
  kind: article
- id: lumsden-2006
  title: Lumsden, Early Parthian and Middle Persian (2006)
  kind: article
- id: sadeghi-1978
  title: Sadeghi, Tarikh-e zabān-e fārsi (1978)
  kind: monograph
- id: brugmann-1897
  title: Brugmann, Grundriss der vergleichenden Grammatik der indogermanischen Sprachen (1897)
  kind: grammar
- id: grassmann-1863
  title: Grassmann, Über die Aspiraten (1863)
  kind: article
- id: bartholomae-1882
  title: Bartholomae, Die arische Aspiration (1882)
  kind: article
- id: verner-1877
  title: Verner, Eine Ausnahme der ersten Lautverschiebung (1877)
  kind: article
- id: grimm-1822
  title: Grimm, Deutsche Grammatik I (2nd ed. 1822)
  kind: grammar
- id: sievers-1878
  title: Sievers, Zur accent- und lautlehre der germanischen sprachen (1878)
  kind: article
- id: vennemann-1988
  title: Vennemann, Preference Laws for Syllable Structure (1988)
  kind: monograph
- id: meiser-1998
  title: Meiser, Historische Laut- und Formenlehre der lateinischen Sprache (1998)
  kind: grammar
- id: sandoz-1985
  title: Sandoz, The Proto-Greek verbal system; Greek sound changes
  kind: article
- id: lejeune-1972
  title: Lejeune, Phonétique historique du mycénien et du grec ancien (1972)
  kind: grammar
- id: neri-2010
  title: Neri, Il sistema di vocali del germanico; Germanische Lautgesetze
  kind: article
- id: wiktionary
  title: Wiktionary, etymology sections (CC BY-SA 4.0)
  url: https://en.wiktionary.org
  kind: corpus
- id: kaikki
  title: Wiktextract / kaikki.org machine-readable Wiktionary (CC BY-SA 4.0)
  url: https://kaikki.org/dictionary/
  kind: corpus
- id: wikipedia-ie
  title: Wikipedia, Proto-Indo-European and daughter-language articles
  url: https://en.wikipedia.org/wiki/Proto-Indo-European_language
  kind: encyclopedia
- id: campbell-1959
  title: Campbell, Old English Grammar (1959)
  kind: grammar
- id: wright-1908
  title: Wright & Wright, Old English Grammar (1908)
  kind: grammar
- id: luick-1914
  title: Luick, Historische Grammatik der englischen Sprache (1914–1940)
  kind: grammar
- id: dobson-1968
  title: Dobson, English Pronunciation 1500–1700 (2nd ed. 1968)
  kind: monograph
- id: braune-2004
  title: Braune & Reiffenstein, Althochdeutsche Grammatik I (15th ed. 2004)
  kind: grammar
- id: paul-2007
  title: Paul, Mittelhochdeutsche Grammatik (25th ed. 2007)
  kind: grammar
- id: kluge-2011
  title: Kluge, Etymologisches Wörterbuch der deutschen Sprache (25th ed. 2011)
  kind: dictionary
- id: wells-1985
  title: 'Wells, German: A Linguistic History to 1945 (1985)'
  kind: handbook
- id: devaan-2008
  title: de Vaan, Etymological Dictionary of Latin and the Other Italic Languages (2008)
  kind: dictionary
- id: weiss-2009
  title: Weiss, Outline of the Historical and Comparative Grammar of Latin (2009)
  kind: grammar
- id: maiden-1995
  title: Maiden, A Linguistic History of Italian (1995)
  kind: monograph
- id: sihler-1995
  title: Sihler, New Comparative Grammar of Greek and Latin (1995)
  kind: grammar
- id: horrocks-2010
  title: 'Horrocks, Greek: A History of the Language and its Speakers (2nd ed. 2010)'
  kind: monograph
- id: smyth-1920
  title: Smyth, A Greek Grammar for Colleges (1920)
  kind: grammar
- id: carney-1994
  title: Carney, A Survey of English Spelling (1994)
  kind: monograph
- id: scragg-1974
  title: Scragg, A History of English Spelling (1974)
  kind: monograph
- id: duden-2017
  title: Duden — Die deutsche Rechtschreibung (27th ed. 2017)
  kind: reference
- id: matasovic-2009
  title: Matasović, Etymological Dictionary of Proto-Celtic (2009)
  url: https://brill.com/display/title/16280
  kind: dictionary
- id: mccone-1996
  title: McCone, Towards a Relative Chronology of Ancient and Medieval Celtic Sound Change (1996)
  url: ''
  kind: monograph
- id: cathcart-2015
  title: Cathcart, Iranian Dialectology and Dialectometry (PhD dissertation, UC Berkeley, 2015)
  url: ''
  kind: monograph
- id: de-vaan-2000
  title: 'de Vaan, The Indo-Iranian animal suffix *-āćá-?, Indo-Iranian Journal 43 (2000) 279–293'
  url: https://doi.org/10.1023/A:1003961021383
  kind: article
- id: schrijver-1998
  title: 'Schrijver, The British word for *fox and its Indo-European origin, JIES 26 (1998) 421–434'
  kind: article
- id: whitney-1889
  title: Whitney, A Sanskrit Grammar, including both the classical language and the older dialects of Veda and Brāhmaṇa (2nd ed. 1889)
  url: https://www.sacred-texts.com/hin/sans/sgr/index.htm
  kind: grammar
- id: braune-ebbinghaus
  title: Braune & Ebbinghaus, Gotische Grammatik (20th ed. 2004; 1st ed. 1880)
  url: https://www.degruyter.com/document/doi/10.1515/9783110938923/html
  kind: grammar
- id: wright-1910
  title: Wright, A Grammar of the Gothic Language (1910)
  url: https://archive.org/details/grammarofgothicl00wrig
  kind: grammar
- id: krause-1968
  title: Krause, Handbuch des Gotischen (3rd ed. 1968)
  kind: handbook
- id: allen-1987
  title: Allen, Vox Graeca. The Pronunciation of Classical Greek (3rd ed. 1987)
  url: ''
  kind: grammar
- id: meillet-1934
  title: Meillet, Le slave commun (2nd ed. 1934)
  kind: grammar
- id: vaillant-1950
  title: Vaillant, Manuel du vieux slave, I (1950)
  kind: grammar
- id: shevelov-1964
  title: Shevelov, A Prehistory of Slavic (1964)
  kind: monograph
- id: derksen-2008
  title: Derksen, Etymological Dictionary of the Slavic Inherited Lexicon (2008)
  kind: dictionary
- id: olander-2015
  title: Olander, Proto-Slavic Inflectional Morphology (2015)
  kind: monograph
- id: kortlandt-1978
  title: Kortlandt, On the history of the Slavic nasal vowels (1978)
  kind: article
- id: kortlandt-1994
  title: Kortlandt, From Proto-Indo-European to Slavic (1994)
  kind: article
```

