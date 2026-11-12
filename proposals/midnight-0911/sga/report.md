# Old Irish from Proto-Celtic — night of 2026-11-09

**Status:** implemented in `data/rules/cel-pro__sga.yaml` (22 laws) and
`data/spelling/sga.yaml` (10 writing conventions), measured, gates green.
**Scope:** only `cel-pro → sga`, its spelling layer and `tests/test_midnight_sga.py`.
No `src/`, no other rule or spelling file, no lexicon, no doc, no
`data/coverage.json`; nothing committed.
**Measured with:**

```bash
PYTHONPATH=src python3 tools/coverage.py --langs sga --limit 0
PYTHONPATH=src python3 tools/council.py --stage cel-pro --to sga --drop <law> --layers exact,orthographic,identity
PYTHONPATH=src python3 tools/council.py --stage cel-pro --to sga --rules proposals/midnight-0911/sga/candidate_final_u_loss.yaml
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q ; node tests/test_ui_render.js
```

## 1. Inventory: why the number was 0

The chain is `ine-pro → cel-pro → sga`, and `data/rules/` had no
`cel-pro__sga.yaml`.  `data.rulesets()` therefore had no entry for that key,
`derive()` recorded the hop in `Derivation.skipped`, and the counter drops
every word with a skipped hop before comparing anything.  All 1,719 tested
entries missed by construction.

| | entries |
|---|---:|
| glossed headwords | 1,984 |
| with a recorded ancestor at a modelled stage (`identified`) | 1,720 |
| tested (reconstructions excluded) | 1,719 |
| recorded ancestor is Proto-Celtic (immediate) | 783 |
| recorded ancestor is Proto-Celtic (anywhere in the chain) | 1,359 |
| **explained before** | **0 exact, 0 orthographic, 0 identity** |

Old Irish headwords are Latin letters, so the laws can in principle reach the
word character for character: the conventions that stand between a phonemic
form and the written word — `c` for /k/, `th` for /θ/, `ch` for /x/, the acute
for length — are *writing*, and they live in the spelling layer, not in the
sound laws.

## 2. Before / after

| layer | before | after |
|---|---:|---:|
| exact (laws) | 0 | **108** |
| orthographic (laws + `data/spelling/sga.yaml`) | 0 | **66** |
| identity (no law needed) | 0 | **4** |
| **explained (union of the layers)** | **0** | **183** |
| of 1,719 tested | 0% | 10.6% |

All 108 exact words rest on `established` laws; no `proposed` or `custom` rule
is in the file, so 0 of the gain is hypothesis.

## 3. The laws — measured one at a time

Every number below is the council's own measurement of the file with that one
law removed (`--drop <law> --layers exact,orthographic,identity`; the council
counts 154 explained in this transition, the published counter's union counts
183, because the two treat a cited stem and a bound form differently).  "words
lost" is the losing list the council prints when the law is withdrawn: it is
what the law carries.  No law, tested alone, gains a word when withdrawn, so
none is over-applying as stated.

| law | tier | explained when dropped | words lost by the drop | what it does |
|---|---|---:|---:|---|
| `final_os_loss` | established | 81 (−73) | 73 | *-os > ∅ (o-stem nom. sg.) |
| `final_long_a_loss` | established | 134 (−20) | 20 | *-ā > ∅ (ā-stem nom. sg.) |
| `final_us_loss` | established | 136 (−18) | 18 | *-us > ∅ (u-stem) |
| `t_to_theta_intervocalic` | established | 137 (−17) | 17 | *t > θ / V_V (written th) |
| `final_om_loss` | established | 138 (−16) | 16 | *-om > ∅ (neuter nom./acc.) |
| `a_affection_u` | established | 141 (−13) | 13 | *u > o before a non-high vowel |
| `a_affection_i` | established | 142 (−12) | 15 | *i > e before a non-high vowel |
| `final_is_loss` | established | 145 (−9) | 9 | *-is > ∅ (i-stem) |
| `k_to_x_intervocalic` | established | 146 (−8) | 8 | *k > x / V_V (written ch) |
| `p_loss_initial` | established | 146 (−8) | 8 | *#ɸ > ∅ |
| `w_to_f` | established | 147 (−7) | 7 | *#w > f |
| `h_loss_intervocalic` | established | 150 (−4) | 4 | *h > ∅ / V_V |
| `s_to_h` | established | 150 (−4) | 4 | *s > h / V_V |
| `kw_to_k` | established | 151 (−3) | 3 | *kʷ > k (written c) |
| `gw_to_g_before_front` | established | 152 (−2) | 2 | *gʷ > g before a front vowel |
| `i_affection_a` | established | 152 (−2) | 2 | *a > ai before *i |
| `i_affection_e` | established | 152 (−2) | 2 | *e > i before *i |
| `p_loss_medial` | established | 153 (−1) | 1 | *VɸV > V |
| `final_ti_to_d` | established | 154 (0) | 0 | *-ti > -d (3 sg. pres.) |
| `gw_to_b` | established | 154 (0) | 0 | *gʷ > b before a non-front vowel |
| `i_affection_o` | established | 154 (0) | 0 | *o > u before *i |
| `w_loss_intervocalic` | established | 154 (0) | 0 | *VwV > V |

Sums do not add: the laws overlap, and the column is one law's own
contribution, not a partition of 183.  The four laws with a zero are stated
because the grammars state them and they fire in matching words (the counter's
`top_rules` shows `final_ti_to_d` in 1, `w_loss_intervocalic` in 1,
`i_affection_o` in 1), but no word depends on them alone in this corpus.

One ordering defect was found and fixed by this measurement: while
`t_to_theta_intervocalic` ran before `final_ti_to_d`, withdrawing the θ law
*raised* the count by three (154 → 157) while breaking 17 words — because the
*-ti of the verb ending was being spirantised before the ending rule could see
it.  `final_ti_to_d` now runs at order 55, before the lenition (a gerund's
*-ti is not a spirant environment), and the θ law carries its 17 words with
nothing lost.

**Rejected candidate** (`proposals/midnight-0911/sga/candidate_final_u_loss.yaml`):
"The final short *-u is lost".  Council:

```
cel-pro -> sga · added final_u_loss · layers: exact, orthographic, identity
  sga  154 -> 155 (+1) lost 4
       gained: dind, ith, scáth, sruth, tráth
       LOST:   rogu, togu, tú, áu
  REJECT: 4 word(s) that already matched stop matching
```

The four lost words are exactly the u-stems that keep their vowel (`rogu`,
`togu`) plus `tú` and `áu`, where the record writes a final u.  The law is
true for *loku > loch and false as stated, so it is not in the file; the
candidate stays here as its own refutation (the finding: final *-u loss is
restricted to the u-stems and cannot be written as one environment).

## 4. The spelling layer — `data/spelling/sga.yaml`

| convention | rule |
|---|---|
| /k/ is written c (no k in the alphabet) | `k_to_c` |
| /θ/ is written th | `theta_to_th` |
| /x/ is written ch | `x_to_ch` |
| /ɸ/ (in a borrowing) is written f | `phi_to_f` |
| length is the acute, not the macron | `long_a/e/i/o/u` |
| stress is not written | `drop_stress` |

Each is a convention that would apply to a word that does not exist yet, which
is the test `docs/REVIEW.md` sets for the layer.  The dotted letters ḃ ċ ḋ ḟ ġ
ṁ ṗ ṡ ṫ are **not** used by this corpus's headwords (checked: no headword in
`data/lexicon/sga.jsonl.gz` writes one), so no spelling rule is written for
them, and no law is bent to avoid them.

## 5. Residue: three words that still fail, and why

* `*uɸer` 'over' → `uer`, the record writes **for** (/ɸoɾ/).  Two changes are
  missing: the *u is not lost before a following vowel, and *ɸ between vowels
  becomes f (not ∅) in this word.  Written as one law, `uɸ > f` would be a
  per-word exception in disguise — the corpus shows it in this word alone.
* `*monis` 'neck' → `mun`, the record writes **muin** (/munʲ/).  The vowels
  are right (i-affection *o > u, *-is lost); what is missing is the
  palatalisation of the final *n before the lost *i and the orthographic rule
  that writes that palatalisation as i *before* the consonant.  That is a
  consonant law plus a spelling convention, and both are for a later pass.
* `*windos` 'white' → `fend`, the record writes **find** (/ɸʲin̪d̪/).  The
  a-affection rule is stated for a single following consonant and two
  consonants, and here an *n + stop cluster blocks it.  The environment needs
  the stated exclusion ("not across a nasal and a stop"), which the pattern
  language cannot yet express without also excusing the words that do lower.

Also outside the reach of any law here: `*sonts` 'they' > os (the *-nts
outcome), `*sweseros` > for (the *-sw- > f- path), and the 265 Celtic words
whose ancestor is written with a case ending the model does not reconstruct.

## 6. Tests

`tests/test_midnight_sga.py` — 14 tests: every law states a tier and a known
source, every example verifies, every law names a grammar section, the named
laws are `established`, apocope leaves the bare stem, initial *ɸ and *w behave,
labiovelars split by the following vowel, lenition fires only between vowels,
affection needs its conditioning vowel, and the spelling layer's rules are
conventions (tier `orthographic`, whole-word matches forbidden).

Gate results in the state left behind: `check-rules` —
32 rule files, 786 rules, 1,091 examples verified, 0 problems;
`unittest discover -s tests -q` — OK; `node tests/test_ui_render.js` — OK.

## 7. Amendment (outside scope)

`data/sources.yaml` has no key for Thurneysen 1946, Pedersen 1909 or Stifter
2006, so those three are cited in the prose of the rules and the machine-checked
`references` use `matasovic-2009`, `mccone-1996` and `fortson-2004`.  Adding
`thurneysen-1946`, `pedersen-1909` and `stifter-2006` to `data/sources.yaml` is
a one-line-each patch for the integrator, and then every rule here can cite its
grammar in `references` too.
