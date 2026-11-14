# Old Persian, 2026-11-09

Scope: `data/rules/ira-pro__peo.yaml`, `data/script/peo.yaml`,
`tools/ingest_op_entries.py`, `proposals/2026-09-11/peo/`,
`tests/test_peo_batch.py`, one append-only line of `data/sources.yaml`.  No
change to `src/`, to another transition's rules, to another script table, to
`docs/`, or to `data/coverage.json`.

## Numbers

`PYTHONPATH=src python3 tools/coverage.py --langs peo ave`, peo only.  The two
columns are the same tree with only the named files swapped (cell C = committed
`ira-pro__peo.yaml` + `script/peo.yaml` + committed lexicon; cell A = the new
rules, committed lexicon; last = the new rules and the repaired lexicon):

| | before (cell C) | +2 laws (cell A) | +2 laws + repair |
|---|---|---|---|
| glossary | 375 | 375 | 375 |
| identified (a modelled ancestor) | 225 | 225 | 225 |
| tested (attested rows) | 137 | 137 | 137 |
| reconstruction rows | 88 | 88 | 88 |
| explained, all layers | **63** | **66** | **66** |
| — through the cuneiform script | **60** | **63** | **63** |
| — reconstructed exactly (Latin rows) | **2** | **4** | **4** |
| — orthographic / pathway | 0 / 3 | 0 / 3 | 0 / 3 |
| borrowed / other source / unlinked / no etymology | 29 / 5 / 8 / 108 | same | same |
| derivations that raised | 0 | 0 | 0 |

So the two laws pay +3 script matches, +2 exact reconstructions and +3 explained
rows, with **zero losses**; the ancestry repair pays in the record, not in the
counter (see (a)).  Cell C reproduces the task's baseline exactly (375 / 225 /
137 / 60 / 63 / 2), which is what makes the attribution trustworthy.

## (a) Ancestry repair — from each entry's own etymology text

`tools/ingest_op_entries.py` gained `--repair-ancestry` (and `--dry-run`).  For
every entry whose **own etymology sentence** says *"From / Inherited from /
Borrowed from Proto-Iranian|Proto-Indo-Iranian|Proto-Indo-European \*X"* it adds
that row when the ancestry list has no usable form for that stage.  It never
adds a word the record does not print, never turns a cognate into an inheritance
link, and never touches a borrowed etymon: Avestan, Old Median, Elamite,
Akkadian, Semitic, Greek and Egyptian donors stay outside the chain and stay
counted as borrowed.

Result: **4 rows repaired**, written to `data/lexicon/_supplement/peo.jsonl.gz`
with the generator `op-ancestry-repair` and merged by
`tools/build_lexicons.py --supplements-only`.  A second `--dry-run` reports
`0 ancestry repairs` — the tool is idempotent.

| word | stated link added | what it replaces |
|---|---|---|
| 𐎭𐎠𐎫𐎶 dātam- | `ira-pro dātam` | nothing usable at that stage (only the bare root *deh₃-) |
| baivaram | `ira-pro baywáram` | the grab-bag rows `ira-pro:*baywā́*baywā́>` and `['ira-pro:*baywā́, '>']` |
| 𐎰𐎵𐎢𐎺𐎴𐎡𐎹 θanuvaniya- | `iir-pro dʰánwr̥` | nothing at Proto-Indo-Iranian (only *dʰénwr̥ at PIE) |
| 𐎭𐎢𐏁𐎫𐎠 dauštā- | `ira-pro jawštā́` | the malformed `:inh ira-pro:*jawštā́>>` |

**Honest result: the repair moves no counter column.**  Measured cell A vs the
full tree: identical script set (63 rows), identical explained (66), identical
reconstructions (4).  The reason is that `coverage.ancestor_starts` already
recovers a start form from the older rows (it strips the `>>` and the
`*baywā́*baywā́` mess differently from the strict reader), so those four words
were already derivable.  What the repair buys is the record itself: 176 entries
state a modelled stage in their etymology and now **176 have a clean, usable row
for it** (before: 4 entries stated a stage the strict reader could not use), and
`baivaram` no longer has a form like `baywā́*baywā́` in its ancestry list.  An
earlier measurement in this session reported +1 script for the repair; that came
from a botched ablation cell (a built glossary dropped into `_supplement/`), and
it is withdrawn here.

Honest accounting of the 150 rows that still have no link to a modelled stage
(`proposals/2026-09-11/peo/audit.py` reproduces it):

| cause | rows |
|---|---|
| no etymology text at all | 108 |
| borrowed from a non-modelled language (Avestan 7, Old Median 9, Elamite 2, Akkadian 10, Sumerian 3, Sanskrit 2, Egyptian 4, Aramaic, Greek, Scythian, Semitic…) | 32 |
| internal formation (suffix or compound of recorded pieces) | 4 |
| cognate only ("Akin to", "Compare") | 3 |
| "probably from X" (Greek / Egyptian) | 2 |
| disputed or uncertain origin | 1 |

**0 of the 150 name Proto-Iranian, Proto-Indo-Iranian or Proto-Indo-European**,
so the bug class seen on the Greek ladder (an etymology names a stage that the
ancestry rows never carry) is gone for Old Persian: 176 rows state a modelled
stage in prose and 176 have a usable row for it.  Nothing was invented to raise
a number; the remaining 150 stay counted as glossary rows without a modelled
lineage.

266 rows carry an ancestry list at all.  41 of them name only donor languages
the chain does not model (Akkadian 10, Old Median 9, Avestan 7, Egyptian 4,
Sumerian 3, Saka/Sogdian 3, Elamite 2, Sanskrit 2, Aramaic, Greek, Scythian,
Proto-West-Semitic); **0 of those 41 names a modelled stage**.

## (b) "tested 137 of 225 identified" is the definition, not a lost link

225 identified = 137 **attested** rows + 88 rows Wiktionary keeps in its
`Reconstruction:` namespace (`recon: true`, Latin titles such as *fšupā).  The
`tested` column is defined on attested words only; reconstructions are measured
in their own column (`reconstruction` / `reconstruction_exact`), which this
batch moved 2 → 4.  `tests/test_peo_batch.py::PeoAccounting` pins the identity
225 = 137 + 88 so the two columns cannot drift apart silently.

The other half of the question — an identified word that is never attempted —
does not occur: every one of the 225 rows produces at least one derivation with
at least one applied law, and `coverage` records 0 errors.  Walks of
`ancestor_starts()` over the whole glossary find **0 entries with a modelled
ancestor and no start form**, and **0 entries with a modelled ancestor whose
derivation is skipped**.

One real (pre-existing) gap is visible on the word page, not in the counter:
`service.hierarchy` derives from the *primary* ancestor, while the counter tries
every ancestor.  𐎠𐎴𐎡𐎹 aniya- therefore counts as a script match in coverage
(from `ira-pro Hanyáh`) but prints `an` on its page (from `ine-pro h₂enh₁`).
That selector lives in `src/pie/service.py`, which this task may not touch.

## (c) Laws added — Proto-Iranian → Old Persian

Both `tier: proposed` (the sources state the outcome for the words; neither
formulates an exceptionless law), both with examples including a no-fire case.

1. **`epenthetic_i_before_y`, order 25** — PIr `*-Cy-` > OP `-Ciy-`.
   `match: y`, `replace: i y`, env *consonant … *y* + vowel*.  Cites Kent (1953),
   Schmitt (2014), Skjærvø (2009).  **+3 script matches, 0 losses**:
   𐎶𐎼𐎫𐎡𐎹 `mártyah → mˈartiyah` (ma-r-ta-i-ya), 𐎠𐎼𐎡𐎹
   `Áryah → Áriyah` (a-ra-i-ya), 𐎠𐎴𐎡𐎹 `Hanyáh → Haniyˈah` (a-na-i-ya).
   The environment is what keeps it honest: a *y after a vowel is a glide and
   must not be broken (𐎭𐎠𐎼𐎹𐎫𐎡𐎹 `dāráyati` is d-a-r-y-t-i-y, the law's
   no-fire example).  An unrestricted `*-Cy-` insertion was measured and missed
   `Canyá-` (anˈyah) while still firing on dārayati-type forms; the
   consonant-plus-vowel statement is the one that fits both.
2. **`long_vowel_contraction`, order 42** — PIr `*-aHā` > OP `-ā`.
   `match: "ā ā"`, `replace: ā`; stated as the coalescence of two adjacent long
   *ā left by `laryngeal_lengthening` (Kent 1953; Hoffmann & Forssman 2004;
   Schmitt 2014).  **+2 exact reconstructions, 0 losses**: *fšupā
   (`fšupāā → fšupā`) and *gaupā (`gaupāā → gaupā`).  It does not fire on
   `dāráyati` (no adjacent long vowels).  A broader `ā (a|ā)` contraction was
   rejected: it also contracts the PIE etymon of `mḗh₁n̥s` in the Persian chain,
   which must stay `ˈāah`.

Stage description and `references` updated; `data/sources.yaml` gained one
append-only line, `schmitt-2014` (Schmitt, *Die altpersischen Inschriften der
Achaimeniden*, 2nd ed. 2014).

Correspondence coverage in this transition after the day — implemented and
cited here: laryngeal loss and lengthening, `*cw > sp`, `*c > θ`, `*θr > ç`,
`*ṛ > ar`, diphthongs `*ay > ai`, `*aw > au`, anaptyxis before `pt`/`pat`,
`*j > d`, `*-Cy- > -Ciy-`, `*-aHā > -ā`.  Carried one stage upstream and
deliberately **not** repeated here: `*s > h` and word-final `*-ah`
(`iir-pro__ira-pro.yaml`), which is also why re-adding `*s > h` here destroys
five words (below).  `*w` remains a bilabial in OP and `*z` remains *z — nothing
to change, and the `*w > v` test shows the change would be wrong.  The
"unwritten vowels" are forms of the writing system, so they belong to
`data/script/peo.yaml` (see (d)), not to a sound law.

`tools/whatif.py --to peo` reports "0 explained" for any candidate because its
default layer is exact Latin orthography and Old Persian has no Latin attested
form; the payment of these laws is on the script layer, so the ablations here
were measured with `tools/coverage.py` on the matched cells above and are
cross-checked in `tests/test_peo_batch.py`.

### Rejected candidates, with the killing numbers

Measured by adding the candidate to a copy of the tree and running
`tools/coverage.py --langs peo`; the baseline there is 63 script / 4
reconstruction-exact / 66 explained (my two laws in, no candidate).

| candidate | script | recon exact | verdict |
|---|---|---|---|
| `*w > v` (unconditional) | 63 → 63 | 4 → **5** | buys one reconstruction (*hvatah) and one Persian orthographic row, but costs Middle Persian its only script match (pal 1 → 0, explained 2 → 1), gains no attested OP word, and would force re-notating 𐎺 from `w` to `v` in every reading |
| `*s > h` at this stage | 63 → **59** | 4 → **3** | −5 script, −1 reconstruction, −4 explained: *s > h already happened at Proto-Iranian; repeating it destroys words whose *s survives |
| `*n > ∅ / _C` (general nasal loss) | 63 → 63 | 4 | no gain and no source formulates general nasal loss for OP; the gap is recorded in the script table instead |
| `*ȷ́ > d` (palatal) | 63 → 63 | 4 | no gain: already reached by `j_from_palatal` + `j_to_d` |
| `*H > h / _[+long]` | 63 → 63 | 4 | no gain: one word's guess, nothing on the corpus |
| anaptyxis inserted before `-ry-` only | — | — | would fire on `dārayati` (d-a-r-y-t-i-y); the consonant+vowel environment is the defensible statement |
| unrestricted `ā (a|ā)` contraction | — | — | tested and withdrawn: it also contracts the PIE etymon of `mḗh₁n̥s` (`ˈāah`) in the Persian chain |

## (d) `data/spelling/peo.yaml` — not written

The evidence does not support a spelling layer here.  What the syllabary does
that is *not* sound (inherent a, unwritten final h, final `-i` closed with the
y-sign, unwritten nasal) is already declared in `data/script/peo.yaml` and
scored in the script column.  Everything else that separates a derived form from
the transliteration — g/k, t/d, b/p voice classes — is a sound question for the
laws, not a spelling convention; a `spelling` table would be a per-word lookup
dressed as a rule, which the project law forbids.  This agrees with
`proposals/2026-09-11/op.md` §5.

The one convention added to the **script** table is documentary, not forgiving:
`nasal_before_consonant` (`kind: unwritten`) records that 𐏃𐎡𐎯𐎢𐏁 Hiⁿduš,
𐎠𐎰𐎥 aθaⁿga- and 𐏃𐎥𐎶𐎫𐎠𐎴 Haⁿgmatāna- have no sign for the nasal.  The
matcher still refuses them (pinned by a test), so the gap stays visible instead
of being papered over.

## Remaining ceiling

- **θātiy** 𐎰𐎠𐎫𐎡𐎹: the ladder gives `cˈanhati → θˈanhati`; the record is
  θātiy (θ- for PIr *c before ā, plus loss of the nasal and *-ah, Kent 1953
  §79).  Needs a *c > θ before a long vowel plus an *an > ā contraction;
  neither is citable as a general law from the sources used here.
- **three nasal words** above: the sign for a pre-consonantal nasal does not
  exist, so no consonant-skeleton matcher can accept them.
- **the identity column cannot see Old Persian**: `_identity_hit` compares a
  no-law-fired output with `entry["translit"]` (sign by sign) but not with
  `entry["translit_alt"]` (the reading), so 𐎭𐎠𐎫𐎶, whose Proto-Iranian
  ancestor *dātam* is its reading, can never be counted.  A one-line change in
  `tools/coverage.py`, which is outside this task's write scope.
- **anaptyxis beyond `pt` and `*-Cy-`** (duruvā → duvarayā type) and the
  genitive plural in *-ām* (`hātām`): no formulation yet that does not also
  break a word that is already right.
- **the 150 unlinked rows**: 108 have no etymology text in the record at all;
  they can only be linked by new dictionary evidence, not by this model.
- The repair has no counter effect today (§a); a selector that used the
  repaired row instead of the first ancestry entry would make it visible, but
  that lives in `src/pie/service.py`.

## Note on scope

Repairing ancestry necessarily writes the built glossary: the four links live in
`data/lexicon/_supplement/peo.jsonl.gz` (and the rebuilt
`data/lexicon/peo.jsonl.gz`), both written by
`tools/ingest_op_entries.py --repair-ancestry` and
`tools/build_lexicons.py --supplements-only`, not by hand.  This is outside the
literal file list of the task and is flagged here deliberately.  No other
lexicon was regenerated by this work.

The counts in this report were taken on the settled tree; a parallel batch was
editing `ine-pro__iir-pro.yaml` and `iir-pro__ira-pro.yaml` during the day, so
an intermediate run of the same files read 64 script / 67 explained.  The
cell-by-cell numbers above are reproducible at any time with the commands below.

## Reproduce

```bash
PYTHONPATH=src python3 tools/coverage.py --langs peo ave --out /tmp/peo-after.json
PYTHONPATH=src:tools python3 proposals/2026-09-11/peo/audit.py
PYTHONPATH=src python3 tools/ingest_op_entries.py --repair-ancestry --dry-run   # 0 repairs
PYTHONPATH=src python3 -m unittest tests.test_peo_batch -q
PYTHONPATH=src python3 -m pie.cli check-rules
```
