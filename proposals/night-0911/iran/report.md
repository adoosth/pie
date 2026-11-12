# Proto-Indo-Iranian → Proto-Iranian: one law added, one repaired, and the ceiling

Night of 2026-11-09. Write scope: `data/rules/iir-pro__ira-pro.yaml`,
`proposals/night-0911/iran/**`, `tests/test_iran_rules.py`. Nothing else was
touched. (Other workers were editing `ine-pro__iir-pro.yaml`,
`ira-pro__peo.yaml`, `pal__fa.yaml`, `data/sources.yaml` and `src/pie/service.py`
while this ran, so every number below names the instant it was measured and the
law's own contribution is measured by ablation, not by a before/after of the
whole tree.)

## Baseline

`PYTHONPATH=src python3 tools/coverage.py --langs iir-pro ira-pro ave peo --out /tmp/iran-before.json`
(02:14, the tree as handed over):

| language | glossary | tested | exact | explained |
|---|---:|---:|---:|---:|
| iir-pro | 799 | 555 | 167 | — |
| ira-pro | 416 | 340 | **196** | 240 (196 exact + 32 identity + 12 bound) |

`exact_strict` was 7: 189 of the 196 are the same phonological form with the
dictionary's acute where the engine writes its own `ˈ` (the repo's 2026-11-09
notation decision, `tools/coverage.py::exact_kind`). That convention is what most
of this transition's number rests on, not sound laws, and the report says so.

The miss list (`pie worklist --lang ira-pro`, and a dump of every failing word
with its best ancestor) is dominated by two groups that are **not** sound laws:

* 197 words whose only difference is the accent's spelling (`-ˈ a→á`, `ˈ→́`);
* ~50 words where the record's Proto-Iranian form needs a morpheme the recorded
  ancestor does not have (a prefix of a compound, `-ka-`, `-iš`, `-āna-`), or
  where the ancestor is one element of a compound (`Hacwa-bāráh` from `bʰorós`).

So the work was: verify that the laws the transition is supposed to own are
registered with the right environments, add what is genuinely missing, and
measure every candidate before shipping it.

## Laws added

### `tt_to_st` — PII *-tt- (*tˢt) > PIr *-st-

```yaml
match: "t ˢ"     replace: "s"     env: {right: t}
```

The dental stop + *t that Proto-Indo-Indo-Iranian already writes as an affricate
(`*winátˢti` < PIE *wi-né-d-ti; `*Háwāytˢt` < *wḗyd-s-t) becomes PIr *-st-. This
is the change that separates the branches in the participle and the 3sg:
**Avestan vista- 'known, found' against Sanskrit vittá-, both from PIE
*wid-tó-** (Hoffmann & Forssman 2004, Lautlehre, on *-tt- > *-st-; Mayrhofer
1986 on the same correspondence).

Environment: the affricated spelling plus a following *t, nothing else.

* it must not touch a plain geminate: PII *kúttas → PIr *kútah (the record's
  `-tt-` is written as two *t, and the target has no *s), and it does not;
* it must not touch *tˢ before another segment (`*utˢčáH`);
* it runs before `s_to_h`, but the *s it writes stands before *t, which `s_to_h`
  keeps, so the output is *st and never *št/*ht.

Ablation (`tools/whatif.py --to ira-pro`): full ruleset 204 explained, without
the law 202 — **+2 exact (`winásti`, `Háwāyst`), 0 lost**, at every instant
measured.

### `l_to_r` repaired (tier `proposed` → `established`)

The rule was registered as a hypothesis with the note "the merger has not been
independently verified in the literature used here". It is standard: Iranian
merges *l with *r — PII *lawkáh 'light' → PIr *rawkáh, Avestan raocah- against
Sanskrit róka- (Hoffmann & Forssman 2004; Mayrhofer 1986; Beekes 2011). The tier
and the description now say that, with the corpus word the law actually carries
(`*Hlagʰúš → *Hragúš`, Av. ragu-) as the second example. No count moved: the
coverage counter admits every tier by default.

Note for the integrator (no edit made, wrong write scope): `ine-pro__iir-pro.yaml`
registers its **own** `l_to_r` at the Proto-Indo-Iranian stage. PII *l → PIr *r
is an Iranian change; the earlier file applying it means a word that enters at
Proto-Indo-Iranian usually has lost its *l before this transition sees it, which
is why this rule only carries one word (Ablation: −1 `Hragúš`, 0 gained).

## Ablation of every law in the file (whatif, explained = 204)

| law | words lost when dropped | law | words lost when dropped |
|---|---:|---|---:|
| final_s_to_h | 105 | th_to_theta | 4 |
| c_from_palatal | 39 | ps_to_fsh | 4 |
| j_from_palatal | 21 | cluster_t_deaspiration | 4 |
| s_to_h | 20 | palatal_plus_sibilant | 3 |
| deaspirate_palatal | 18 | p_to_f before sonorant (internal) | 3 |
| deaspirate_dh | 18 | **tt_to_st (new)** | 2 |
| t_to_theta before sonorant | 13 | t_to_theta before sonorant (initial) | 2 |
| k_to_x_internal | 10 | p_to_f before sonorant (initial) | 2 |
| deaspirate_bh | 9 | ts_to_c | 1 |
| deaspirate_gh | 8 | ph_to_f | 1 |
| k_to_x_initial | 5 | l_to_r | 1 |
| | | kh_to_x | 1 |

**No law in the file is harmful**: dropping any single one gains 0 words. The
`tier: formation` rule `suffix_nah` stays switched off and cannot move a number.

The environments are not accidentally narrow — widening them loses words:

| variant tested | net | why it was rejected |
|---|---:|---|
| `s_to_h` without the "not before a stop" exception | **−9** (lost `HgráHscati, HástH, br̥jáns, cáHsti, spr̥jā́, stuHnáH, stuHráh, stáwrah, wadúHs, yascáti`) | the stop exception is real and load-bearing |
| `s_to_h` only before a vowel | **−8** (lost `Háhmi, hmáwčati, hráwtah, hwāh, hwāhā, …`) | *s > *h also before glides and nasals |
| `t_to_theta` before a sonorant with no left context | **−2** (`mártyah, úštrah`) | a *t in the coda after a liquid/sibilant is not spirantised |
| `p_to_f` before a sonorant with no left context | **−1** (`tr̥práh`) | same, for *p in the coda |
| `k_to_x` with no left context (one rule for both) | 0 | identical result here, so the "not after a sibilant" restriction is not contradicted by this corpus (kept, not removed) |

## Rejected candidates (measured, with the killing numbers)

Each candidate is kept as the YAML that was tested, in `proposals/night-0911/iran/candidates/`.

| candidate | claim | result | verdict |
|---|---|---|---|
| `geminate.yaml` | PII *tt > PIr *t | +1 `kútah`, 0 lost | **rejected** — one word, and it contradicts `tt_to_st`: the record writes *kúttas with a plain geminate whose PIr reflex is *kútah, while every *tˢt is *st. A rule for the one word is the thing this project forbids. |
| `sc_palatal.yaml` | PII *sć > PIr *š | +1 `tr̥šáti`, **−2** (`HgráHscati`, `yascáti`) | rejected — the record keeps *sc elsewhere; the net is negative and the claim false for two words. |
| `sc_sibilant_c.yaml` | PII *ść > PIr *c | +1 `caHyáH`, 0 lost | rejected — the word is PIE *(s)ḱeh₃ih₂, an **(s)-movable** root: the record dropped an optional *s. That is not a sound change; one word, no independent example. |
| `palatal_plus_z.yaml` | PII *ȷ́ž > PIr *ȷ́ | +1 `jā́h`, 0 lost | rejected — one word (PIE *dʰéǵʰōm), and the Iranian treatment of that cluster is *z* (Av. zəm-), not the *j this record writes. The form is a record variant, not a law. |
| `pc_to_fs.yaml` | PII *pć > PIr *fš | +1 `fšā́`, 0 lost | rejected — it is the word the rule would be written for, with no second etymon. (It is the same shape as the existing *ps > *fš, and belongs in a cluster note, not as a law.) |
| `t_before_h.yaml` | PII *t > PIr *θ before *H | **−1** (`HástH`) | rejected — the record keeps *t before a final *H. |
| `final_ns.yaml` | PII *-ns# > PIr *-h | +1 `Hr̥táHwāh`, **−1** (`br̥jáns`) | rejected — the record writes both outcomes; no law satisfies both. |
| `h_coda_loss.yaml` | PII *H > ∅ after a consonant | **+4 / −5** (`HráθHah, HwárHuš, HástH, bádHr̥, járHitah`) | rejected — the five losses are the record keeping *H after a consonant. See "the ceiling" for what the four gains really are. |
| `h_in_superlative` (tested as part of the same family) | *H lost after *t before a vowel | **+3 / −3** | rejected — same mixed record (θH, dH, rH survive; only the *-ištHa- suffix drops it). |
| `final_s_v.yaml` | final *-Vs > *-h after *any* vowel | 0 / 0 | no evidence either way; left unshipped. |

## Descendants

This transition feeds Avestan, Old Persian, Middle Persian and Persian. Measured
at 2026-11-09 with and without `tt_to_st` (one snapshot, `naive` set of exact
headwords; identical computation both sides):

| language | exact with the law | exact without | gained | **lost** |
|---|---:|---:|---|---|
| ira-pro | 197 | 195 | `Háwāyst, winásti` | — |
| ave | 0 | 0 | — | — |
| peo | 0 | 0 | — | — |
| pal | 1 | 1 | — | — |
| fa | 0 | 0 | — | — |

**No previously matching descendant word stopped matching.** The descendant
counts are what they are because `ira-pro__ave.yaml` and `ira-pro__peo.yaml`
belong to other workers and are being written tonight; `tools/coverage.py` at
the same instant reports ave 0/312, peo 0/137, pal 1/61, fa 0/1692 exact (with
7, 67, 2 and 374 *explained* in their wider layers — orthographic and citation
hits, never `exact`).

## The honest ceiling

At one snapshot (`tools/coverage.py`, 2026-11-09, late evening). **The tree is
moving under this table**: other workers were adding rules to the files on either
side of this transition all night, and the same command twenty minutes later
reads `exact 202 / identity 31 / explained 245` — two words crossed from `exact`
to `identity`, and *explained* did not move. Read this number with its clock
attached, never as a standing claim.

| measure | ira-pro |
|---|---:|
| glossary | 416 |
| tested (a recorded ancestor exists) | 340 |
| **exact** | **204** (60.0% of tested) |
| of which `exact_strict` (identical strings) | 7 |
| of which `exact_notation` (the accent written two ways) | 197 |
| identity (the form is already right, no law fires) | 29 |
| bound form (the record writes a hyphen) | 12 |
| **explained** (exact + identity + bound) | **245** (72.1%) |
| residual | 95 |
| borrowed / no usable recorded ancestor | 1 / 76 |

Delta, honestly attributed: the handed-over baseline was **196** exact
(240 explained); the last two readings are **202–204** exact with **245**
explained. Of that movement exactly **+2 exact / +2 explained is `tt_to_st`**
(ablation: dropping it costs `winásti` and `Háwāyst` and nothing else); the
remaining **+4 to +6** came from `ine-pro__iir-pro.yaml` and other files that
other workers were editing the same night, not from anything in this report.

`204` counts a word as exact when the dictionary prints the accent as an acute
and the engine writes its own `ˈ`; only **7** are the same string. That
convention is the repo's 2026-11-09 decision and it is doing most of the work in
this number, not the sound laws. It is also why 197 of the 256 "misses" in the
worklist are not misses at all: they are one accent, written twice.

I read every residual word. A dump that compares stress-free strings re-prints
four rows that coverage books as identity or attached form, so it lists 99 rows
for the 95 residual words; with those included, the causes partition exactly as
follows, and not one bucket is a missing law:

| what would have to change | n | words |
|---|---:|---|
| punctuation / case only (hyphen, brackets, capital `C`) | 11 | `fra-, ha-, warj-, Hwah-, ham-, (H)adári, (h)rabā́š, da(H)inúš, jr̥dáyam, (H)uxšā́, war(H)ana-` |
| the record writes *H where the laws write *h (or a vocalised *H) | 10 | `dmáHnaH, makácaH, ǰámaHnaH, xáHh, daHtáh, názdištah, kácištah, bárjištah, cáywaH, Háyšmah` |
| needs a morpheme the ancestor does not carry, or the record holds another shape of the stem | 23 | `-akah, -ayHnah, ráwčakah, ráwčikah, háxtiš, dáwgah, dā́rukah, HaHcúkah, namaHčah, CyaHmakáh, karah, láyjati, pā́dah, carHdáh, cwáHdah, HhuHā́pah, tā́wHā, Hr̥táHwāh, Hnā́fah, káwfš, Háyxam, HmíčaH, ǰúǰakah` |
| the recorded ancestor is one element of a compound/derived word, or the wrong lexeme | 44 | `paridayjah, kánjuš, jr̥níš, HhutawcáH, gawnah ×2, Habigāwáyati, spr̥Hgah, dáyHanaH, gayHθáH, frajanHtáh, Hárjičah, wr̥pa-ka, gáwbati, hamdaHma, dáwxšati, Hacwabāráh, bišajkah, Hanguǰatu, axšáyHnah, patikárah, kā́rawā, spr̥Hgmáh, máyθanam, Hwáhumanāh, cwaHdapatiš, HacwaHastiš, arpacyaH, huHarnáh, kā́rawāh, dmaHnapaθniH, ǰáwati, br̥ǰnáH, fragāwah, hwatā́wHniH, HárǰyaHnah, čaxštanah, niwaydáyati, niyascáti, wicápuθrah, udzwaydáyati, hamwátati, dušHáhuš, aHfrináHti` |
| *l and *r disagree with the record | 3 | `lupiš, rā́nah, lagžnáh` |
| one segment, measured and rejected above | 8 | `kútah, tr̥šáti, caHyáH, jā́h, fšā́, ǰāmáyati, Háčart, mayθaH` |

So the transition's own phonology is essentially complete for this corpus. All
six families the assignment lists are registered and load-bearing: `s_to_h`
(+20 when dropped, and its stop exception is worth 9 words if removed),
`c_from_palatal`/`j_from_palatal` (+39/+21), the *p *t *k > *f *θ *x laws
(+2/+2/+13 for *p initial/medial and *t, +5/+10 for *k), `l_to_r` (+1), and the
deaspiration set (+9 bh, +18 dh, +8 gh, +18 palatal). What is left is
morphology (formations and paradigms, W5), the record's own habits in writing *H
and in choosing a citation stem (W1/W2), and ancestry links that point at one
element of a compound.

How much of the 340 is *derived inside Proto-Iranian itself*? 204 exact + 29
identity (the recorded ancestor already is the attested form) + 12 bound = 245;
the other 95 need something this transition cannot supply. Of the 416 glossary
rows, 76 have no usable recorded ancestor at all (61 unlinked + 12 without an
etymology, minus overlap) and 1 is recorded as borrowed, so no law of any
transition can reach them: the available ceiling for rule work on the 416 is
340, and at 204 that is 60%.

## Files changed

* `data/rules/iir-pro__ira-pro.yaml` — new `tt_to_st`; `l_to_r` tier and
  description repaired. Order 109 keeps it before `s_to_h`.
* `tests/test_iran_rules.py` — new: the law's mechanics, its two "must not
  touch" cases, the s-before-stop exception, the repaired tier, and a
  rule-local regression test (with/without the law, gained ⊆ the two words,
  lost = ∅) that is immune to the other files moving.
* `proposals/night-0911/iran/report.md` (this file) and
  `proposals/night-0911/iran/candidates/*.yaml` — the rejected candidates as
  tested.

## Gates

* `PYTHONPATH=src python3 -m pie.cli check-rules` → **0 problems** (618 rules,
  852 examples; the count moves because other workers are adding rules tonight).
* `PYTHONPATH=src python3 -m unittest discover -s tests` → **green, 447 tests**,
  including the nine in `tests/test_iran_rules.py`. For part of the day one
  test of the script/reading layer
  (`tests/test_web.py::TestNotationComparison`) failed because another worker
  had `src/pie/service.py` half-edited; it failed with the original rule file
  restored too, and went green when their edit landed. Nothing here patched it.
