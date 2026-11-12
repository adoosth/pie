# Persian (`fa`) orthography — second pass: the layer is complete, and *h-loss is not the law at fault

**Artefact.** No change to `data/spelling/fa.yaml` (33 rules, byte-identical; `md5 6c886e10cbdd…`).
Everything below is measurement, plus the answer to the open question in
`proposals/night-0911/fa.md` §8.
**Author.** 2026-11-09, measured on `b066202`, re-verified on
`af9433e` (the Latin/Italian spelling commit) and again with the Greek stream's
uncommitted edits in the tree; fa is identical in all three states: **103,
exact 0, 51 of 4,806 pages**.
**Why nothing was added.** A writing convention can only win a word when the
derived *phonemes* are right and the *letters* are wrong. The corpus has
exactly one such word (صد, whose only difference is the Arabic letter ص for
/s/) and it is lexical. Every remaining miss differs in a segment, so it belongs
to the laws, not to the script. §2 is the proof, and each candidate convention
the brief named is measured and rejected there.

## 1 · Where the numbers actually stand (the 57 in the brief is stale)

The earlier figures were fa orthographic **57** and **39 of 4,806** pages. Those were
measured before commit `b066202` (*Sanskrit: the laws now speak Sanskrit*), which
changed `tools/coverage.py`: the orthographic layer is now tried on **every**
ancestor derivation (`orthographic_hit`), not only on the closest one. The same
`fa.yaml` therefore now scores:

| measure | value |
|---|---:|
| glossary | 5,555 |
| identified (a recorded ancestor) | 1,634 |
| PIE-linked | 806 |
| tested | 1,634 |
| **exact (sound laws)** | **0** |
| **orthographic** | **103** |
| orth_rate | 1.8542 % |
| near misses (≤ len/4 edits) | 1 |
| word pages with a spelled rung | **51 of 4,806** |

`proposals/night-0911/fa_probe.py` still mirrors the *old* selection and now
prints **59** counted, not 103; its miss diagnostics are still useful, but its
headline number is no longer the published one (see §5.4).

Reproduce the published figure without touching the repo reports:

```bash
PYTHONPATH=src python3 tools/coverage.py --langs fa --limit 0 --out /tmp/cov_fa.json
PYTHONPATH=src python3 proposals/night-0911/fa2/pages.py     # 51 of 4,806
```

**Before/after for this pass: 103 → 103, exact 0 → 0, pages 51 → 51.** The file
was not edited, because §2 shows there is nothing honest left to add.

## 2 · Step 2 — is any *writing convention* still missing? No, and here is the measurement

`fa2/covmirror.py` reproduces `coverage.py`'s current selection exactly (it
returns 103). On top of it:

* `fa2/letter_gap.py` — for every one of the 1,531 misses, walk **all** ancestor
  derivations and ask whether any of them has the same segments as the entry's
  own recorded IPA (folding notation only: `č=t͡ʃ š=ʃ ž=ʒ ǰ=d͡ʒ y=j`,
  `ā=aː ī=iː ū=uː`, and the vowel qualities the model does not name) while the
  letters are still wrong. **3 hits, 2 of them clitic fragments (`ـتر`, `ـین`)**;
  the only real word is **صد** (derived *sad*, written سد) — an Arabic loan whose
  letter ص is lexical, exactly like German ⟨v⟩/⟨w⟩.
* `fa2/letter_only.py` — of the 1,394 misses that carry an IPA, **13** have a
  derivation that is segment-for-segment equal to the record. All 13 are already
  spelled right by the file; they are lost to the guard's *notation*, not to the
  script (§5). 1,381 differ in a segment; 137 misses have no IPA at all.
* `fa2/guard_gap.py` — 177 entries' spelling equals the record: 103 counted,
  21 where no law fired (identity is not an explanation), 53 rejected by
  `spelling.plausible`, of which **17 are notation-only** (16 distinct words:
  چشم، شیر، گوش، دوش، میش، پشم، ریش، می، روی، پای، دشت، شید، کوش).
* `fa2/candidates.py` — whole-word rewrite probes for the suffix/initial
  conventions that could still be imagined; none has a positive honest net.

Miss signatures under the current selection (spelled guess → record):
`∅→ن` 284, `∅→ا` 214, `∅→ی` 155, `∅→د` 126, `∅→ه` 120, `∅→ر` 97, `∅→ت` 92,
`'→∅` 87, `ا→∅` 70, `ل→ر` 68, `ʾ→ا` 67, `∅→و` 67. 677 of the 1,394 guesses are
*shorter* than the word: those are consonants the phonemes do not contain.

### 2.1 The candidates the brief named, each measured

| candidate | evidence | verdict |
|---|---|---|
| word-final `-ī` written ی | already `long_i` (order 41) | nothing to add |
| ه for final `-e/-a` | already `final_short_a` (order 30) | nothing to add |
| `/v/` as و | already `v_letter` (order 50) | nothing to add |
| **tanwīn** (ً ٌ ٍ) | **1** glossary word, **0** identified; headwords are unvocalised | no reachable input |
| **hamza seats** (ء أ إ ؤ ئ) | 89 glossary words, **3** identified — all پائین, whose only ancestor is Pahlavi script; the model's ʾ in outputs is the *Pahlavi aleph sign* of a transliteration (34 otherwise-phonemic outputs, all debris such as `ʾwl`, `bʾčʾl`) | no phonemic glottal stop ever reaches the layer |
| **silent و in خوا-** | real in the script, but the /w/ is deleted upstream (`peo~pal:xw_to_x_initial`), and the /w/ can't be recovered from /xā/: 28 glossary words begin خا- vs 10 خوا- (identified 6 vs 9) | lexical; the law fires in **0** nearest derivations, so even a law fix wins nothing here |
| **gemination written once** (no shadda) | true, but 26 derived forms have doubled consonants and collapsing them wins **0**; the pattern language has no back-reference, so it cannot be stated as one rule | no gain, not expressible |
| **Arabic letter choice** (ز/ذ/ض/ظ, س/ص/ث, ت/ط, ه/ح, ک/ق, ع/ء) | 30 identified words contain one; exactly **1** is same-length and differs only in allographs (آس, where the real difference is a/ā), and **0** would be won | lexical, like ⟨v⟩ vs ⟨w⟩ |
| **final `-ā` written ه** | would "win" 5 (توده، دانه×2، کله، مه) with 0 breaks **today** — but Persian writes پا، تا، خدا with ا; the 5 are words whose derivation wrongly has ā where the record has -a/-e (`-eh₂`/`-ag`) | **target bending**, rejected |
| **final `-o` as ه** | 0 outputs end in /o/; the file already records the letter as lexical | no input |
| **initial /a/ as آ** | 1 fix / 1 break, and it is a vowel-length fact | false as a rule |
| **initial /ay/ /aw/ as ای/او** | already produced by composition (`a→ا` then `y→ی`/`w→و`) | no rule needed |
| **Arabic article ال** | explicitly out of scope; lexical | rejected |
| **ezafe / indefinite -ī / ZWNJ compounds** | morphology, not spelling; the ezafe is not in the headword and 6 identified compounds carry a ZWNJ boundary that the phonemic form does not have | rejected |

Nothing in the 33-rule file was found to be *false* either: the letter table
covers every segment the laws produce (the only unmapped character in any output
is the transliteration ʾ, §2.1).

## 3 · Step 3 — `peo~pal:final_h_loss`: the law is right, and it is not what breaks ماه

### 3.1 What fa.md claimed, and what the corpus shows

fa.md §8 said the law deletes a stem-final *h < PII *s that Persian keeps, and
listed 9 entries / 7 words (ماه، جیوه، دشنه، سگرنه، مرده، باده، روده). Two
corrections:

1. **Six of those seven are not about /h/ at all.** Their record ends in the
   *letter* ه, but their own IPA ends in a vowel: مرده /mur.ˈda/, باده /baː.ˈda/,
   روده /roː.ˈda/, جیوه /d͡ʒiː.ˈwa/, سگرنه /su.ɡur.ˈna/ (دشنه has no IPA). The ه
   there writes -a/-e (from `-ag`), and the spelling coincidence appears only
   because ه writes both. Only **ماه** /ˈmaːh/ among them really ends in /h/.
2. **ماه does not keep the h the law deletes.** The law deletes the reflex of the
   nominative *-s; the h Persian keeps is the *stem* consonant (PIE *h₁ of
   *mḗh₁n̥s). The model deletes that one a transition earlier:

```
mḗh₁n̥s → mˈāHas → mˈāHah      (final_s_to_h: nom. *-s > *-h)
       → mˈāah                (laryngeal_lengthening: stem *H deleted after ā)  ← the h Persian keeps
       → mˈā                  (final_h_loss: ending *-h deleted — correct)
```

Switch only `final_h_loss` off and the form becomes `mˈāah` → ماه, but the guard
rejects it (`āa` is two nuclei, the IPA has one). Switch
`laryngeal_lengthening` off and the form keeps a capital `H` (`māH`) that no
Persian rule maps. So **no setting of `final_h_loss` can produce ماه.**

### 3.2 Size of the population, and what changing the law costs

| measure | value |
|---|---:|
| entries whose nearest derivation fires the law | 194 of 1,531 misses |
| counted words whose *counted* derivation fires it | 39 |
| **counted words when the law is switched off** | **65 (was 103): gains 0, losses 30** |
| words whose *spelling* changes at all when it is switched off | 7 (the seven above) |
| of those, lexically in /h/ | 1 (ماه), and it is not counted either way |
| words in the corpus whose IPA ends in /h/ and whose derivation fired it | 4 (ماه، سیاه×2، سنه، زراه) — the last three are wrong in another segment too (syāw, hnoš, dray) |

`fa2/law_ablation.py`, `fa2/hloss_evidence.py`, `fa2/hloss2.py`.

### 3.3 The evidence the law was written for is sound

30 counted words stand on it and every one is an a-stem/thematic nominative
whose ending is the h: مرد ← mr̥tós (`mr̥tˈah`), کام ← kóh₂mos (`kˈāmah`),
اسب ← h₁éḱwos (`ˈaspah`), پس ← pós (`pˈah`). Removing the law costs all 30 and
gains none.

MacKenzie's Middle Persian entries (`data/lexicon/pal.jsonl.gz`) show the same
split: the h that Persian keeps is the stem consonant — `pnʾh` panāh ‘refuge’,
`zyh` zīh ‘bowstring’, `glyh` girih ‘knot’, `nkys … ngʾh` nigāh ‘look’ — while a
final **-ah** ending surfaces as the letter ه with no /h/: `dwazdah` ‘twelve’ →
دوازده, `panzdah` ‘fifteen’ → پانزده. There is no Book-Pahlavi `māh` headword in
the lexicon; the fa entry quotes `byʿḥ /māh/` (an ideogram) and OP 𐎶𐎠𐏃 m-a-h,
where the h is the stem consonant again. The three OP words in the corpus that
end in -h are all s-stems (māh, manah, raucah), i.e. the corpus's OP -h is never
the a-stem ending the law was written for — but the law is needed for the
*PIE/PII* nominative, which is where its 30 counted words come from.

### 3.4 Decision

**(b) a paradigm fact — and no clean law.** The surface sequence Vh# is
ambiguous between the case ending (which Middle Persian loses) and a stem-final
*h (which Persian keeps); no phonological environment separates them, and a
reconditioning such as “after ā.a” would describe an artefact of
`laryngeal_lengthening`, not a class. **The law is left untouched**; removal or
restriction would cost 30 counted words and gain 0. The honest home for the
distinction is the paradigm layer (W5: mark the loss as an *ending* — note that
`src/pie/rules.py`'s `TIERS` has no `paradigm` member yet) or a per-word pathway
(`data/pathways.jsonl`, already holds 8 fa entries), both outside this pass's
write scope. For ماه specifically the missing rule is at the laryngeal stage
(stem *H → h in *mā́Has), which is a W2 question, not a spelling one.

## 4 · Gates

```
PYTHONPATH=src python3 -m unittest discover -s tests -q   # see the note below
PYTHONPATH=src python3 -m pie.cli check-rules             # 26 rule files, 530 rules,
                                                          # 671 examples, 0 problems
```
`check-rules` lists 11 spelling files (ang, de, en, enm, fa, gmh, gmw-pro, goh,
it, la, sa) and reports 0 problems, `fa.yaml` included.

**The full suite currently fails one test, and it is not Persian.**
`test_web.TestWordPage.test_greek_and_persian_are_compared_through_their_romanisation`
fails on `grc:πατήρ` (the chain gives patˈɛ̄r). While this pass ran, another
workstream left the shared working tree with uncommitted edits to
`data/rules/grk-pro__grc.yaml`, `src/pie/service.py`, `tools/coverage.py`,
`src/pie/citation.py` and their tests. The suite passed **342/342** at the start
of this pass (tree `b066202`); it fails only after those edits appeared. Persian is unaffected: all fa tests pass
(`tests.test_orthography`, `tests.test_readings`), the fa word pages still match
(پدر → pedar, نام written نام), and fa coverage re-measured **103 / exact 0 /
51 pages** with those edits in place.

## 5 · For the super agent to review by hand

1. **The guard's notation gap is a real false negative (`src/pie/spelling.py`).**
   `plausible()` folds the *dictionary's* notation (ɡ, ɾ, the tie bar) but not
   the *model's* philological letters, so `č` is compared with `t͡ʃ` and `ā` with
   `aː` as if they were different segments — although the docstring promises
   "a dictionary's notation cannot decide the count". Measured effect for fa
   (`fa2/fold_effect.py`, `fa2/fold_alone.py`, patch applied in memory only):
   **103 → 127 entries** and **51 → 57 pages** once the fold is complete. One
   fold at a time: `ʃ→š` +15, `j→y` +9, the others only in combination. It would
   move the published orthographic column for **every** spelling language, so it
   is a W7 decision, not a bug fix I should make silently. The 13/17 words it
   would recover are listed in §2.
2. **`fa.md` §8 is wrong about ماه** (§3.1) — the h Persian keeps is the stem
   laryngeal, and `final_h_loss` is the law that correctly removes the ending.
   The proposal's conclusion (leave the law, W5 owns it) stands; its evidence
   for it does not.
3. **The largest orthographically visible class is W5, not spelling**: 177
   misses have a record ending in ه whose written form does not — 132 with an
   IPA ending in a vowel (the missing `-ag`/`-a`), 36 with /h/ (this §3), 9 other.
   A `formation`-tier `-ag` rule (the tier already exists, off by default) is the
   honest instrument; a spelling rule cannot write a vowel that is not there.
4. **`proposals/night-0911/fa_probe.py` is stale**: it still selects only the
   closest derivation and prints 59 where coverage publishes 103. Either update
   it to `orthographic_hit` or stop quoting its headline.
5. Nothing in this pass edited `src/`, `data/` or another proposal; only
   `proposals/night-0911/fa2/` is new (`covmirror.py`, `misses.py`,
   `letter_gap.py`, `letter_only.py`, `guard_gap.py`, `candidates.py`,
   `hloss.py`, `hloss2.py`, `hloss_evidence.py`, `law_ablation.py`,
   `fold_effect.py`, `fold_alone.py`, `pages.py`, `pages_fold.py`, `report.md`,
   plus the generated `misses.tsv` and `pages.txt`).

## 6 · Reproduce

```bash
# published numbers (no repo reports written)
PYTHONPATH=src python3 tools/coverage.py --langs fa --limit 0 --out /tmp/cov_fa.json

# the mirror, the miss dump and the four analyses
PYTHONPATH=src python3 proposals/night-0911/fa2/misses.py
PYTHONPATH=src python3 proposals/night-0911/fa2/letter_gap.py
PYTHONPATH=src python3 proposals/night-0911/fa2/letter_only.py
PYTHONPATH=src python3 proposals/night-0911/fa2/guard_gap.py
PYTHONPATH=src python3 proposals/night-0911/fa2/candidates.py

# the law question
PYTHONPATH=src python3 proposals/night-0911/fa2/law_ablation.py
PYTHONPATH=src python3 proposals/night-0911/fa2/hloss_evidence.py

# the guard question (in-memory patch; src untouched)
PYTHONPATH=src python3 proposals/night-0911/fa2/fold_effect.py
PYTHONPATH=src python3 proposals/night-0911/fa2/fold_alone.py
PYTHONPATH=src python3 proposals/night-0911/fa2/pages.py          # ~60 s
PYTHONPATH=src python3 proposals/night-0911/fa2/pages_fold.py     # ~60 s
```
