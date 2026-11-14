# Lithuanian from Proto-Balto-Slavic — 2026-11-09

**Status:** implemented in `data/rules/ine-bsl-pro__lt.yaml`, measured, all four
gates green.  No spelling file was written (Lithuanian is written in the Latin
alphabet, so the laws reach the headword itself).
**Scope:** only the `ine-bsl-pro → lt` transition and `tests/test_batch_lt.py`
(plus this directory).  No `src/`, no other rule file, no lexicon, no doc was
touched; `sla-pro` is untouched.  Nothing was committed.
**Measured with:**

```bash
PYTHONPATH=src python3 tools/coverage.py --langs lt --limit 0 --out /tmp/lt.json
PYTHONPATH=src python3 tools/council.py --stage ine-bsl-pro --to lt --drop <id> --layers exact
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q ; node tests/test_ui_render.js
```

---

## 1. Inventory: why the number was 0

The chain is `ine-pro → ine-bsl-pro → lt`, and **no rule file existed for
`ine-bsl-pro → lt`**.  `data.rulesets()` therefore had no entry for that key,
`derive()` recorded the hop in `Derivation.skipped`, and the counter drops every
word with a skipped hop before it compares anything (`if d.skipped: continue`).
Every tested entry missed *by construction*; not one letter was ever compared.

| | entries |
|---|---:|
| glossary headwords | 2,449 |
| with a recorded ancestor at a modelled stage (`identified`) | 1,057 |
| tested (reconstructions excluded) | 1,057 |
| of which record a Proto-Balto-Slavic ancestor | 621 |
| PIE-linked | 825 |
| **explained before** | **0** (251 exact after) |

The name of the game here is different from OCS: Lithuanian writes Latin
letters, so the laws can produce the headword itself.  Of the 621 entries with a
PBS ancestor there are 578 distinct ancestor→headword pairs, and **69 of them
are character-identical once the notation is dropped** (ba, ir, ne, po, per,
anas, kas, kaklas, galas, dubus …): they need no sound change at all.  The
counter's `identity` column is where those belong; the laws must not invent a
step for them.

## 2. The law file — 24 rules

22 historical laws (20 `established`, 2 `proposed`) and 2 notation rules
(`orthographic`), each with a citation key that `check-rules` verifies and at
least one example it re-derives.

| law | tier | citation | Δ carried | broken |
|---|---|---|---:|---:|
| `register_mark_dropped` | orthographic | Fortson 2004, Ringe 2006 | +120 | 0 |
| `stress_token_dropped` | orthographic | Fortson 2004, Sihler 1995 | +32 | 0 |
| `final_ei_to_i_after_t` | established | Fortson 2004, Sihler 1995 | +84 | 0 |
| `w_to_v` | established | Fortson 2004, Sihler 1995, Meillet 1934 | +40 | 0 |
| `long_a_to_a_final` | established | Fortson 2004, Meillet 1934 | +38 | 0 |
| `s_caron_to_s` | established | Fortson 2004, Meillet 1934 | +21 | 0 |
| `long_e_to_e_dot` | established | Fortson 2004, Sihler 1995, Meillet 1934 | +21 | 0 |
| `long_i_to_y` | established | Fortson 2004, Sihler 1995, Meillet 1934 | +20 | 0 |
| `long_a_to_o` | established | Fortson 2004, Sihler 1995, Meillet 1934 | +18 | 0 |
| `z_caron_to_z` | established | Fortson 2004, Meillet 1934 | +17 | 0 |
| `long_o_to_uo` | established | Fortson 2004, Sihler 1995, Meillet 1934 | +12 | 0 |
| `final_an_to_as` | **proposed** | Fortson 2004, Olander 2015 | +7 | 0 |
| `lj_to_li` | established | Fortson 2004, Sihler 1995 | +3 | 0 |
| `s_w_to_s` | **proposed** | Fortson 2004, Meillet 1934 | +2 | 0 |
| `t_l_to_k_l` | established | Fortson 2004, Sihler 1995 | +2 | 0 |
| `s_j_to_s_i` | established | Fortson 2004, Sihler 1995 | +2 | 0 |
| `a_nasal_before_s` | established | Fortson 2004, Sihler 1995 | +2 | 0 |
| `eu_to_au` | established | Fortson 2004, Sihler 1995, Meillet 1934 | +1 | 0 |
| `final_long_i_to_i` | established | Fortson 2004, Sihler 1995 | +1 | 0 |
| `s_to_z_before_voiced` | established | Fortson 2004, Sihler 1995 | +1 | 0 |
| `u_nasal_before_s` | established | Fortson 2004, Sihler 1995 | +1 | 0 |
| `i_nasal_final` | established | Fortson 2004, Sihler 1995 | +1 | 0 |
| `a_nasal_final` | established | Fortson 2004, Sihler 1995 | 0 (1 bound) | 0 |
| `u_nasal_final` | established | Fortson 2004, Sihler 1995 | 0 (1 bound) | 0 |

"Δ carried" = unique exact words that leave when the law is removed
(`council.py --drop`, layer `exact`; base 239 unique words / 251 entries).
"Broken" = words the law changes that matched before it was added; **no law in
the file breaks one**.  Sums do not add: laws overlap.

Citations in the file: Fortson 2004, Sihler 1995, Meillet 1934, Ringe 2006 and
Olander 2015 (all present in `data/sources.yaml`).  The two standard Lithuanian
grammars — **Stang 1966** and **Ambrazas 1997** — are not in `sources.yaml` and
could not be cited machine-checkably; see §7.

**What the corpus does not evidence.**  Five of the changes the task expected
have no lawful environment in this glossary, and writing them would be a
one-word rule or a guess:

- ***tj / *dj / *skj***: only seven PBS→Lithuanian pairs contain one, and they
  disagree — *pláutja* > plautis, *degutjas* > degutas, *tjautāˀ* > tauta and
  *medjas* > medis keep a plain stop, while *walˀdjāˀ* > valdžia and *tuskjas* >
  tuščias show dž/šč.  A general law would break four words to explain two.
- **3rd person *-ti > -a**: every verb in the glossary is an infinitive; there
  is no 3rd-person form to measure.
- **The retracted accent**: the headwords write no accent at all, so a prosodic
  law cannot be tested against them (the IPA records the stress, the laws do
  not read IPA).
- **Yers**: Proto-Balto-Slavic has none — the yers are the Slavic development of
  short *i/*u, and Lithuanian keeps *-as/-is/-us unchanged (this is where the
  28 identity entries come from).
- ***ę***: no word in the corpus shows *en > ę (blęsti needs the *-d of the
  stem, and `en` before *d is not the sibilant environment); only ą, į and ų are
  written.

The two rules that reach no *exact* word (`a_nasal_final`, `u_nasal_final`)
fire on `są-` and `-ų`, which the counter scores in its **bound** column (12
entries today).  They are kept because they are true and measured; a `bound`
layer run gives each of them +1.

## 3. The numbers

Published counter over the full eligible set (1,057 tested entries):

| | before | after |
|---|---:|---:|
| tested | 1,057 | 1,057 |
| **exact** (historical) | **0** | **251** |
| — phonological (a real law fired) | 0 | 209 |
| — notation only (stress/register dropped) | 0 | 42 |
| **explained** (the counter's headline: exact + bound) | **0** | **263** |
| identity (ancestor already the headword, own column) | 0 | 28 |
| bound form | 0 | 12 |
| orthographic (separate column) | 0 | 0 |
| exact from the PIE etymon itself | 0 | 25 |

Exact rate on the tested set: **23.7%**; on the whole glossary: 10.2%.

**A counter quirk, named rather than hidden.**  `explained` is 263 = 251 exact
+ 12 bound; the 28 identity entries are *not* in it.  In `tools/coverage.py` an
identity match sets `here = True` and then hits `if best_distance == 0:
continue`, which skips the `explained += 1` at the end of the loop.  The
identity column is published correctly, the headline understates it.  The
one-line patch is in §7; it changes no `exact` number and is out of this task's
scope.
The 42 notation-only matches are stated separately on purpose: they show that
the notation rules are doing work, and a reader who does not accept notation as
a step should read the historical figure as **209**.

Ancestry did not change: identified 1,057, PIE-linked 825, borrowed 1,010,
outside 365, unlinked 16 — the same as before the file existed.

## 4. Rejected candidates (kept, with their losing lists)

Measured with `council.py --rules <candidate> --stage ine-bsl-pro --to lt
--layers exact`; a candidate is accepted only if nothing loses and something
gains.

| candidate | gained | lost | verdict |
|---|---:|---|---|
| **`*ei > ie` unconditionally** | +12 (briedis, dievas, liepa, lieti, lietus, mielas, mieras, niekas, prie, priedas, siela, šviesti) | **−5** (*eiti, geisti, kreivas, veidas, šeima* — whose recorded ancestor already writes ei) | **REJECTED**, not in the file |
| **`*tl > kl` with no environment** | +1 (tinklas) | **−1** (*atlaikas*: the *t belongs to the prefix *at-*) | **REJECTED**; narrowed to `left: !V`, now +2 / −0 |
| `*aN > ą` before any consonant | 0 | **−2** (*mandras, rankā* would nasalise) | REJECTED; narrowed to `_s` |
| `final *-ū > -u` | 0 | 0 | removed: a dead rule is a claim with no evidence |
| final `*-ā > -o` (i.e. *ā > o even word-finally) | 0 | **−38** (*daina, alga, rasa …*) | REJECTED; the final law is `*-ā > -a` |
| `final *-u > -us` (u-stem nominative) before the vowel laws | +2 (*alus, medus*) | **−1** (*tu*, whose PBS form is already short) | REJECTED |
| `final *-a > -as` and `final *-i > -is` (same convention, run before the ā law) | +8 (*vardas, linas, bernas, dvaras, vokas …*) | **−3** (*ašaka, valka* are ā-stems; *-i > -is* alone breaks 89 infinitives) | REJECTED |

The last two rows are the same *citation* idea as `final_an_to_as` (the record
cites a stem or a neuter, Lithuanian cites the masculine nominative).  They were
tried at order 15, before `long_a_to_a_final`, so that only *short* final vowels
were seen — otherwise they swallowed 41 ā-stems.  Even narrowed they break real
words, so only the *-an* variant, which breaks nothing, is in the file.

The `*ei` case is the interesting one.  The six forms the broad law breaks sit
in exactly the same segmental contexts as forms it explains (`d`: briedis vs
veidas; `s`: šviesti vs geisti; `r`: priedas vs kreivas; `#`: prie vs nei;
`m`: mielas vs šeima).  No segmental environment separates them: they are
lexical exceptions in the record, and the programme forbids carving a word out
of a law.  The file therefore has **no `*ei` law**, and those 12 words stay
misses.  A reviewer who wants them counted needs a per-word pathway, not a law.

## 5. The residue, with three worked examples

**766 entries** still miss (1,057 − 251 exact − 28 identity − 12 bound).  They
are not all phonology; this is a mechanical proxy over the miss list, not a
hand audit:

| class (proxy) | entries |
|---|---:|
| the recorded ancestor is a bare root/stem and the headword adds an infinitive or a derived noun (*dirb-* → dirbti, *mak-* → makas, *aul-* → aulas) | 344 |
| the derived form is one segment short (a suffix the model does not have: *pel-* → pelė, *bud-* → budė) | 32 |
| near miss (edit distance ≤ ¼ of the word: declensional recategorisation, ā-stem → ė-stem, i-stem → -ys) | 140 |
| the rest (homonyms, dissimilations, analogical remodelling) | 250 |

Three that still fail, and why:

1. **kasa** *braid*.  PBS *kāˀsā́ˀ* → `kosa`: the law `*ā > o` is stated for
   every non-final *ā and fires on the first syllable, but Lithuanian writes a
   short a there.  The record's long ā is not what the attested word shows, and
   a rule "not in this word" is a lookup, so the word stays a miss.  (The other
   direction is real: `*ā > o` carries 18 exact words.)
2. **kar̃vė** *cow*.  PBS *kárˀwāˀ* → `karva`; the headword is `karvė`.  The
   change is the ā-stem → ė-stem recategorisation, not a sound law: a rule
   `*-ā > -ė` would also rewrite *daina, alga, rasa* (38 exact words).  It
   belongs in a paradigm table.
3. **rugỹs** *rye*.  PBS *rugís* → `rugis`; the headword writes `y`.  The y is
   the reflex of the *-ij-* suffix in the i-stems, not of the recorded short
   *i*.  A rule `i > y` in this position would rewrite *dantis, naktis, mintis*
   (all exact today).

## 6. Gates

```text
PYTHONPATH=src python3 -m pie.cli check-rules
  32 rule files, 786 rules, 1091 examples verified, 0 problems
  (the file count is a shared-worktree snapshot; 0 problems is the gate)

PYTHONPATH=src python3 tools/coverage.py --langs lt --limit 0
  lt  251/2449 glossary, 251/1057 tested exact; 263 explained
      (209 phonological + 42 notation, 28 identity, 12 bound)

node tests/test_ui_render.js
  script reading and timeline ok / construction menu ok / recorded starts ok /
  overall progress bar ok / join timeline and coverage buckets ok

PYTHONPATH=src python3 -m unittest discover -s tests -q
  Ran 604 tests — OK  (shared worktree; this file contributes 26)
```

`tests/test_batch_lt.py` adds **26 tests**: every law's tier and citation,
every law's examples re-derived alone, the notation rules' tier, the vowel shift
(*ā/*ō/*ē/*ī), the infinitive ending and its failure on *prei*, *w > v, *ś/*ź,
*lj/*sj, *tl only after a consonant (atlaikas untouched), *s voicing only before
a voiced stop, the nasal vowels and the nasals that must stay, and a floor of
240 exact entries.

## 7. Out-of-scope findings, with exact patches

1. **`data/sources.yaml` lacks Stang 1966 and Ambrazas 1997**, the two standard
   Lithuanian grammars the task asks to cite.  Add:
   ```yaml
   - id: stang-1966
     title: Stang, Vergleichende Grammatik der baltischen Sprachen (1966)
     kind: grammar
   - id: ambrazas-1997
     title: Ambrazas (ed.), Lithuanian Grammar (1997)
     kind: grammar
   ```
2. **The PIE → PBS stage turns PIE *e into *e where the record has *a**
   (*kʷékʷlos* → `keklas`, but PBS *kaklas*; *h₂éngʷʰis* → `engis`, but *angis*).
   Those words are still explained from their PBS ancestor, but the PIE-first
   derivation is wrong.  The fix is in `data/rules/ine-pro__ine-bsl-pro.yaml`,
   not here; a candidate law is `*e > *a` after *kʷ (needs a council run across
   Slavic too).  Recorded, not touched.
3. **`final_an_to_as` is morphological.**  It states that the record cites an
   o-stem in its PBS neuter *-an while the Lithuanian word is the masculine
   nominative in -as (7 words, +7/−0).  It is marked `proposed` and its prose
   says what it is; a future paradigm layer should own it.
4. **`explained` drops the identity column.**  In `tools/coverage.py`, the
   identity branch reaches `if best_distance == 0: continue` before the loop's
   `if here: explained += 1`, so an entry that matched with no law fired is
   counted in `identity` but not in `explained` (Lithuanian: 28 entries; every
   language with pure identity matches loses them the same way).  Exact patch:
   ```diff
   --- a/tools/coverage.py
   +++ b/tools/coverage.py
   @@
                if best_distance == 0:
   -                continue
   +                if here:
   +                    explained += 1
   +                continue
   ```
5. **The corpus has no spelling/IPA problem here**: no `data/spelling/lt.yaml`
   is needed.  Lithuanian is written with the same letters the laws produce, and
   the 42 notation matches are already strict string matches.
