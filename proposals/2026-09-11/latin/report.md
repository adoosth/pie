# Latin from Proto-Italic — 2026-11-09

**Status:** implemented in `data/rules/itc-pro__la.yaml`, measured, gates green.
**Scope:** only the Proto-Italic → Latin transition.  No `src/`, no other rule
file, no spelling file, no other test was touched.
**Measured with:**

```bash
PYTHONPATH=src python3 tools/coverage.py --langs la it --out /tmp/la-night-before.json   # before
PYTHONPATH=src python3 tools/coverage.py --langs la it --out /tmp/la-night-final.json    # after
PYTHONPATH=src python3 tools/whatif.py --to la --layers exact,orthographic --drop <id>   # every law
PYTHONPATH=src python3 tools/council.py --stage itc-pro --to la --drop <id>              # Italian
```

---

## 1. The numbers

The published counter over the full eligible set (3,267 Latin entries with a
recorded ancestor at a modelled stage):

| | before | after |
|---|---:|---:|
| tested | 3,267 | 3,267 |
| **exact** (historical) | **7** | **121** |
| — strict | 3 | 103 |
| — stress notation only | 4 | 18 |
| **explained** (exact + orthographic + identity + bound) | **68** | **329** |
| orthographic (separate column) | 42 | 181 |
| identity | 32 | 35 |
| bound form | 14 | 22 |

Italian, which reads the same transition:

| | before | after |
|---|---:|---:|
| exact | 1,066 | **1,070** |
| explained | 1,398 | **1,399** |
| orthographic | 271 | 268 |

Italian gains 5 exact words (`agro, almo, duomo, muno, poto`) and loses 1
(`muodo`, a dialect form): net +4, and one more word is explained overall
(1,398 → 1,399).  The three orthographic words that disappear from the Italian
column (`agro, almo, poto`) are exactly three of the five exact gains — they
moved up a layer, not out of the model.  `council.py --drop` for the main laws
reports `it` gaining or unchanged in every case (`final_o_to_u_s` alone carries
5 Italian exact words: dropping it loses `agro, almo, duomo, muno, poto`).

**What the change costs in Latin.**  Against 106 exact and 129 orthographic
entries gained (unique headwords), 2 exact entries are lost and 3 orthographic
ones: `oinos` and `deivos` are archaic spellings whose own ancestors now
correctly derive `ūnus` / `dīvus`; `castro` is a variant of `castrum`; and
`similis`, `cinis` were only ever matched by the withdrawn medial *e*
weakening, which was firing on the **first** syllable (`semalis > similis`,
`kenis > cinis`).  No rule was narrowed to keep them: the losses are reported
as misses.

---

## 2. Laws added or repaired

Δ = what the **whole** rule file loses when this one law is removed
(`whatif --to la --layers exact,orthographic`, 302 explained before).  Sums do
not add: laws overlap, and a word removed by one is often re-derived from
another recorded ancestor.

| law | tier | Δ | what it does |
|---|---|---:|---|
| `final_o_to_u_s` | established | −107 | final *-os > -us |
| `final_long_a` | established | −24 | final *-ā > -a |
| `final_o_to_u_m` | established | −21 | final *-om > -um (replaces the old deletion of *-m) |
| `j_to_i` | established | −20 | *j > i after a consonant |
| `ei_to_i` | established | −18 | *ei > ī before a non-glide consonant |
| `z_to_r` (kept) | established | −16 | rhotacism |
| `ao_to_o` | established | −13 | final *-āō > -ō |
| `ai_to_ae` | established | −12 | *ai > ae |
| `ou_to_u` (kept) | established | −11 | *ou > ū |
| `beta_to_b` / `eth_to_d` | established | −10 / −8 | *β *ð > b d (the stops Latin writes) |
| `oi_to_u` | established | −9 | *oi > ū before a consonant |
| `final_i_loss_t` | proposed | −8 | final *-i lost after *t |
| `s_loss_voiced` | established | −6 | *s lost between a vowel and a voiced consonant |
| `final_s_to_r` | established | −6 | final *-s > -r after a long vowel in a polysyllable |
| `gw_to_w` (kept) | established | −6 | *gʷ > w |
| `t_loss_s` | established | −5 | *t lost before final *-s |
| `o_to_u_l` | established | −5 | *o > u before dark *l |
| `s_loss_initial` | established | −4 | initial *s- lost before a nasal/liquid |
| `medial_a_weakening` (repaired) | established | −3 | non-initial syllable only |
| `e_to_i_gn` | established | −3 | *e > i before *gn |
| `ios_to_ius` | established | −3 | -ios > -ius |
| `final_ei_to_i` | established | −3 | final *-ei > -ī |
| `oi_to_i` | established | −2 | final *-oi > -ī |
| `rs_to_rr` | established | −2 | *rs > rr before a front/low vowel |
| `gammaw_to_w` | established | −2 | *ɣʷ > w |
| `e_loss_initial_s` | proposed | −1 | initial *e- lost before *s (sum) |
| `final_i_loss_l` | proposed | −1 | final *-i lost after *l |
| `rs_to_r_final` | established | −1 | final *-s lost after *r |
| `final_e_before_d` + `final_d_loss` | established | −1 each | ablative *-d lost after lengthening |
| `x_to_h`, `theta_to_f` (kept) | established | −1 / 0 | *x > h; *θ > f |
| `e_to_o_l` | established | 0 | *e > o before *l + long back vowel |
| `gamma_to_g` | established | 0 | *ɣ > g |

Citations: Sihler 1995 (New Comparative Grammar of Greek and Latin), Weiss 2009
(Outline of the Historical and Comparative Grammar of Latin), Meiser 1998,
de Vaan 2008 (individual etymologies only), all already in `data/sources.yaml`.

### Repaired environments

* `medial_a_weakening` and `medial_e_weakening` were stated with
  `left: C`, which fires on the **first** syllable: `*ferō` → `firō`.  The
  environment is now `V C? C? C?`, i.e. a non-initial syllable.
* `medial_e_weakening` itself was **withdrawn**: with the narrow environment it
  still loses more than it gains (dropping it: +15 gained, 5 lost — *Tiberis,
  aedilis, caenus, caecus, caedo, catena, haedus, hedera, maereo, posterus,
  quaero, saeta, scaevus, superus, taedeo*).  Latin medial weakening is real
  but stress-conditioned, and without stress the segmental environment cannot
  be stated.  This repeats the finding of `proposals/006-italic-o-to-a.md`.
* `final_m_loss` was **removed**.  Latin writes final `-m`; deleting it in the
  phonemic layer made `argentum`, `dōnum`, `forum` … unspellable, because no
  spelling rule can restore a letter the laws deleted.  The transition now
  states `*-om > -um` instead, and the `la → it` law still deletes the *-m*
  for Italian (`argento`).
* `final_s_to_r` is now limited to a long vowel in a polysyllable
  (`honōs > honor`, `kelōs > color`); monosyllables keep `-s` (`flōs, mōs,
  rēs`) and a final short *i* is untouched (`similis`).

---

## 3. Rejected candidates, with the numbers that killed them

| candidate | measured | verdict |
|---|---|---|
| `*o > *u / _ r C` (*orsos > ursus*) | +2 gained, **−7 lost** (*dorsum, formus, hortus, orbis, orbita, porta*) | rejected: not a general change; *ursus* is isolated |
| `*o > *u / _ m` (*homos > humus*) | +4, **−3** (*communis, domus, kom*) | rejected |
| `*o > *u / _ nd` (*ɣrondā > grunda*) | +1, **−2** (*pondus, sponda*) | rejected |
| `*rs > rr` before any vowel | +2, **−2** (*dorsum*) | rejected; narrowed to front/low vowels (+2, −0) |
| `*ei > ī` without a following-consonant restriction | +20, **−2** (*deiva, deivos*) | rejected; narrowed to `_ C !GLIDE` (+18, −0) |
| final `*-om > -um` without the left-C environment | **−1** (*kom*, and it broke stressed forms) | rejected; moved before `j > i` instead, which recovers *labium, odium, pretium* with no loss |
| final `*-i > -e` after any consonant | +4, **−1** (*heri*) | rejected: the change is morphological (neuter -e vs locative -i), not segmental |
| `*e > *o / _ l (short back vowel)` | **−1** (*prelum* → *prolum*) | rejected; narrowed to long back vowels (`kelōs`, `welō`) |
| `*e > *u / _ l (back vowel)` | +2 (*famulus*), **−1** (*prelum*) | rejected |
| `*e > *i / _ n #` (*en > in*) | +1, **−1** (*genimen*) | rejected |
| `kw_to_labiovelar` (notation fold) | 0 gained, 0 lost | removed: a dead rule is a claim with no evidence |
| `*-nts` lengthening | kept although ablation is +4 when dropped | **kept**: `pōns, dēns, mōns` are phonologically right; the counter cannot see it because the dictionary's IPA writes a nasalised vowel (`[põːs]`) and the reading guard does not fold nasality.  Removing a true law to win letters would be target bending. |

---

## 4. The ceiling, honestly

3,267 entries have a modelled ancestor.  After the laws they decompose as:

| class | entries |
|---|---:|
| **exact** (historical) | 121 |
| **orthographic** (spelling layer, separate) | 181 |
| **only a root is cited**, no word ancestor (*acanthus*, a Greek word built on *h₂eḱ-*; *spectrum*, built on *speciō* + *-trum*) | **491** |
| needs a **derivational suffix the model does not have** (target ≥2 segments longer, or the etymology names a suffix; proxy) | **574** |
| output is 2+ segments shorter than the target (weaker suffix/noise proxy) | 596 |
| spelling reaches the letters but **no law fires** (the counter requires one rule) | **171** |
| spelling reaches the letters but the **reading guard** rejects the IPA (ɫ vs l, nasalised vowels, a silent g in the dictionary's IPA) | **70** |
| recorded as **borrowed** | **101** |
| near miss (distance ≤ len/4) | 125 |
| **genuinely irregular / unexplained** | **837** |

The first row is the historical claim; the second is never added to it.  The
biggest single ceiling is therefore not sound law at all: **491 words cite a
root rather than a word**, and another **574** need a derivational morpheme the
model does not register (a formation, not a sound law).  The 171 + 70 are
measurement artefacts: the orthographic layer is only tried when at least one
law fired, and `spelling.plausible` compares consonant skeletons against the
dictionary's IPA.  Both are properties of the counter and the spelling guard,
not of this rule file; they are named here so the next batch does not mistake
them for phonological failure.

---

## 5. What to do next

1. **Morphology (largest honest gain).**  The 491 root-only entries and the 574
   suffix entries need a derivational layer (root + cited suffix → stem), not a
   sound law.  `formation` rules already exist in the engine and are counted
   only through a word's own pathway.
2. **Stress.**  `medial_e_weakening` cannot be stated without stress.  A Latin
   prosody step would let the rule return with its real environment (and would
   also let `-ĭ- > -e` in Italian be re-tested, see proposal 003).
3. **Spelling guard.**  Latin `ɫ`, nasalised `[õː]`, and the dictionary's
   silent `g` in `gnārus` block 70 words whose letters the laws already reach.
   That is a `data/spelling/la.yaml` guard change, outside this task's scope.
4. **Remaining phonology.**  125 near misses cluster in: final `-i` (mare,
   ante — morphological), `-s` after short vowels (augur, lar — sporadic),
   *-rn- > -n- (*pernis > penis*), and wrong recorded ancestors (lens < nīdus,
   sol < *sōh₂wl̥).

---

## 6. Gates

```text
PYTHONPATH=src python3 -m pie.cli check-rules
  29 rule files, 698 rules, 965 examples verified, 0 problems

PYTHONPATH=src python3 -m unittest discover -s tests -q
  Ran 502 tests — OK

PYTHONPATH=src python3 tools/coverage.py --langs la it --out /tmp/la-night-after.json
  la  121/3267 tested, 329 explained
  it 1070/10680 tested, 1399 explained
```

New test file: `tests/test_latin_batch.py` (20 tests) — pins every law's tier and
citation, verifies its own examples, and states the forms that must **not**
change (`*ferō` stays `ferō`, `*ad` keeps its *-d*, `*flōs` keeps its *-s*,
`*similis` does not rhotacise, `*preslom > prelum`, `*kʷoi > kʷī`).  It also
asserts a floor of 250 words explained directly from a Proto-Italic ancestor, a
number that depends only on this transition and the glossary.
