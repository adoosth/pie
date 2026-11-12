# Old Norse from Proto-Germanic — night of 2026-11-09

`data/rules/gem-pro__non.yaml`, new.  Old Norse had no transition file, so every
one of its words was a miss *by construction*: no law could fire between
`gem-pro` and `non`.  This file registers 47 laws (46 `established`, 1 `proposed`), each with a tier, a source
key and an example `pie check-rules` verifies.

## The number

| | before | after |
|---|---|---|
| glossary (entries) | 3,177 | 3,177 |
| tested (eligible, non-reconstruction) | 3,011 | 3,011 |
| **exact (historical)** | **0** | **692 (23.0% of 3,011)** |
| — of which strict | 0 | 601 |
| — of which notation (acute vs stress token) | 0 | 91 |
| explained (exact + identity/pathway) | 0 | 710 |
| errors | 0 | 0 |

Commands (both reproducible):

```bash
PYTHONPATH=src python3 tools/coverage.py --langs non --out /tmp/non-before.json
PYTHONPATH=src python3 tools/coverage.py --langs non --out /tmp/non-after.json
PYTHONPATH=src python3 -m pie.cli check-rules      # 29 files, 698 rules, 965 examples, 0 problems
```

671 of the 692 start at the recorded Proto-Germanic etymon itself (the frame
at `from_stage`); 21 also match when started from PIE.

## The laws, and what each is for

Tiers are all `established` except `final_ô_to_i`, which is `proposed` because
its outcome depends on the paradigm (see below).  Every rule carries its
citation; locators are given here.

**Consonants that feed the vowels.** `w_loss_before_u` (*wulfaz > ulfr,
*wundrą > undr) and `w_loss_before_r` (*wrekaną > reka) — Gordon 1957 § 44,
Noreen 1923 § 240, Haugen 1982 § 36.4.  `w_to_v` (*weraz > verr, *hwelpaz >
hvelpr) — Noreen § 240.2.

**Final vowels that trigger umlaut.** `final_ō_to_u` (§ 20: *gebō > *gebu >
gjǫf, the -u that rounds and breaks, later lost) — Noreen § 180, Gordon § 47;
`final_ǭ_to_a` (*gatwǭ > gata, *tungǭ > tunga, no u-umlaut) — Noreen § 180.3;
`final_ô_to_i` (*agô > agi, *banô > bani) — **proposed**: the neuter n-stem of
the same shape ends in -a (*hertô > hjarta, *augô > auga) and the engine cannot
see the paradigm, so the neuters are recorded misses (see the test file).

**u-umlaut.** `u_umlaut_a` (*laguz > lǫgr, *handuz > hǫnd, *barnu > bǫrn),
environment *a* + one or two consonants + *u; the *a of the diphthong *au is
excluded by requiring a consonant — Noreen §§ 71–76, Gordon § 47, Haugen § 34.

**Diphthongs, before the umlauts that would misread them.** `ai_to_ei`
(*stainaz > steinn, *aiganą > eiga) — Gordon § 48, Noreen § 90; `au_h_to_a`
(*hauhaz > hár) and `ai_h_to_a` (*taihwǭ > tá) — Noreen § 92; `eu_to_jo`
(*beudaną > bjóða, *keulaz > kjóll) and `eu_to_ju` before a voiceless stop
(*deupaz > djúpr, *seukaz > sjúkr) — Noreen § 74, Gordon § 48.

**i-umlaut** (one rule per vowel, environment *i* or *j* up to two consonants
away): `a > e` (*satjaną > setja, *harjaz > herr, *gastiz > gestr), `ā > æ`
(*mārijaz > mærr), `o > ø`, `ō > œ` (*dōmijaną > dœma, *sōkijaną > sœkja),
`u > y` (*kunją > kyn, *fullijaną > fylla), `ū > ý`, `au > ey` (*hauzijaną >
heyra) — Noreen §§ 55–70, Gordon § 48, Haugen § 35.

**Breaking.** `breaking_e_u` (*meluks > mjǫlk, *gebu > gjǫf, *eburaz > jǫfurr),
`breaking_e_a` (*hertô > hjarta, *harþaz > harðr) restricted to *r* or *l* plus
a consonant plus *a* — that restriction is the difference between hjarta and
verr/hverr, which do **not** break — Noreen §§ 61–62, Gordon § 46.

**Long vowel.** `e_long_to_a`: *ē > á (*hērą > hár, *lētaną > láta, *blēwaz >
blár) — Gordon § 48, Ringe & Taylor 2014 ch. 4 (the change that separates Norse
from Gothic, which keeps ē).

**Consonants.** `d_to_eth` *d > ð after a vowel (*laidō > leið, *braudą >
brauð, *hirdijaz > hirðir) — Noreen § 228; `th_to_d` *þ > ð in voiced position
(*brōþēr > bróðir, *aiþaz > eiðr) — Noreen § 227; `hs_to_ks` (*lahsaz > lax) —
Noreen § 231; `h_loss_after_vowel` (*hauhaz > hár, *saihwaną > sjá) — Noreen
§ 233; `n_assimilation` *nþ > nn (*finþaną > finna, *sinþaz > sinn) — Gordon
§ 45; `z_to_r` (*stainaz > steinn, *laguz > lǫgr) — Gordon § 44, Krause 1968
§ 62; `j_loss` after a consonant (*harjaz > herr, *kunją > kyn) — Noreen § 269.

**Endings.** `r_stem_ēr_to_ir` (*brōþēr > bróðir, *fadēr > faðir, *swestēr >
systir) and `final_ijaz_to_ir` (*hirdijaz > hirðir) — Noreen § 302; `final_b_to_f`
(*gebō > gjǫf) — Noreen § 229; `infinitive_ijaną` (*sandijaną > senda), `infinitive_janą`
(*satjaną > setja), `infinitive_ōną` (*kallōną > kalla), `infinitive_aną`
(*nemaną > nema, *draganą > draga) — Noreen §§ 130–133, Gordon § 130;
`final_az_to_r`, `final_iz_to_r`, `final_uz_to_r` (*dagaz > dagr, *gastiz >
gestr, *laguz > lǫgr); `r_geminate_n`, `r_geminate_l` (*stainaz > steinn,
*stōlaz > stóll) against `r_loss_after_s` (*hwassaz > hvass) and
`r_loss_after_consonant` (*hrafnaz > hrafn, *erlaz > jarl) — Noreen § 302,
Gordon § 55; `final_ą_loss` (*landą > land) — Gordon § 54; `final_u_loss_*`
(*rūnō > rún, *gebō > gjǫf); `final_i_loss` (*gasti > gest) — Noreen § 180.

## What was tried and rejected (with the number that killed it)

- **`u > o` before *a* (a-umlaut of u).**  Citable (Noreen § 78) and it fixes
  kot, horn, fold, koma — but it also fires on ulfr, undr, gull, fullr, where
  the record keeps u.  Measured on the file as it stood that minute: **574 →
  512 exact (−62)**.
  Rejected; the condition that separates the two groups is not a segmental
  environment the engine can state (it is syllable weight plus paradigm), so
  the loss is published as a miss instead of hidden in a broader rule.
- **Breaking *e > ja* with a general "…*a*" environment.**  Fires on *weraz,
  *hweraz, *hertō-like material without the liquid+consonant context and turns
  verr into vjarr.  Rejected in favour of the narrower environment above; the
  narrower rule leaves fjall-type words as misses rather than inflating the
  count with a wrong law.
- **Final *-ō > -a** (the outcome the task list mentions).  In this corpus the
  ō-stem nominative is endingless (gjǫf, ben, egg, rún, sorg), and only the
  ōn-stems keep -a (gata, saga, tunga), which `final_ǭ_to_a` already states.
  A *-ō > -a rule fires on 187 words and matches almost none of them.
- ***-ô > -a** (neuter n-stem).  Fits hjarta and auga but breaks the 169
  recorded weak masculines in -i (agi, bani, maki).  Kept as the `proposed`
  minor rule `final_ô_to_i` with the neuters named as its known misses.
- **A `data/spelling/non.yaml` layer** was considered and **not written**: no
  written form in this corpus needed a convention that the transition does not
  already produce (the acute is read as notation by the counter, see below).

## The ceiling, stated honestly

The 18% is not the whole language, and the reasons are systematic:

1. **Vowel length is not a letter.**  The normalized headword writes long
   vowels with an acute (móðr, hár, lǫgr).  This project's engine writes length
   as a macron/length segment and stress as the acute, and the counter reads
   the acute as *notation*.  92 of the 572 matches rest on that read
   (`exact_notation`); the strict figure, 480, is the one to compare with older
   releases.  A word whose only mismatch is a macron the rules still carry
   (ō, ī, ū) counts as a miss, not a match.
2. **Syncope of medial short vowels** (*anadōną > anda, *þiudijaną > þýða,
   *hringijaną > hringja) is not modelled.  Without stress in the recorded
   ancestor the engine cannot tell a stressed from an unstressed vowel, so a
   syncope rule would delete first-syllable vowels too; that is a W5
   (morphology/paradigm) task, not a sound law.
3. **Paradigm-dependent endings.**  *-ô gives -i in the masculine and -a in the
   neuter; *-ō gives -u (then lost) in the ō-stems.  One surface rule cannot do
   both, and the file says which majority it chose.
4. **Word-formation and compound material** (names, prefixes like *-laus,
   compounds such as *Gudąlaibaz > Guðleifr) needs the morphology layer.
5. **The u > o a-umlaut** (item 1 of the rejected list) is worth roughly 60
   words on its own if the environment can ever be stated.

A realistic next target with this same file shape is 30–40% once syncope and
syllable-weight-conditioned a-umlaut exist; neither belongs to the sound-law
stream alone.

## Gates

- `pie check-rules`: **0 problems** (29 files, 698 rules, 965 examples).
- `python3 -m unittest discover -s tests`: one failure,
  `test_web.TestRebuiltCognates.test_incomplete_chains_are_reported_not_faked`,
  which asserts `"non" in gaps` — it is the fixture that records Old Norse as a
  language *without* a transition file.  That assertion is now false by
  construction and belongs to the integrator to update (editing `test_web.py`
  was outside this task's write scope).  No other test regressed.
- `tests/test_norse_rules.py` (new): the file is registered, every rule states
  tier, sources and examples, the cited forms derive exactly, a law that must
  not fire stays put, and the corpus count is above 600.
- `tools/council.py --stage gem-pro --to non` finds nothing to test once the
  laws are registered (it measures *candidate* additions); each candidate was
  measured with `tools/whatif.py --to non --drop <id>` instead — e.g.
  `--drop d_to_eth` loses 56 words, `--drop infinitive_ijaną` loses 43,
  `--drop w_loss_before_r` loses 5.
