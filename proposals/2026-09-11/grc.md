# Greek: the last mile from Proto-Greek to Attic-Ionic

- **Status:** implemented and measured. 33 rules in `data/rules/grk-pro__grc.yaml`
  (11 kept verbatim from the old 14, 2 rewritten in place, 1 replaced, 19
  further new). `exact` in
  `tools/coverage.py` is still **0** — for a reason that is not the laws and is
  explained in §2. The law work is measured against the dictionary's own
  **romanisation** (the string the word page compares): **66 → 218 words**,
  nothing lost.
- **Session:** 2026-11-09, branch `main`, HEAD `af9433e`. Other batches
  were working in the same tree (Gothic: `data/rules/gem-pro__got.yaml`,
  `data/spelling/got.yaml`, a `data/sources.yaml` addition; also
  `proposals/2026-09-11/fa2/`, `sla-candidate.yaml`, `src/pie/service.py`);
  I touched none of them.
- **Writes:** `data/rules/grk-pro__grc.yaml` and this file only. No `src/`, no
  `tools/`, no `data/spelling/grc.yaml` (there is none), no git commit.
- **Gates:** in a snapshot of this tree with the concurrent Gothic workstream's
  `data/spelling/got.yaml` and `data/rules/gem-pro__got.yaml` set aside,
  `check-rules` is **0 problems** (681 examples verified) and
  `unittest discover -s tests -q` is **361 tests, OK**. The Greek transition
  itself contributes **0** problems in the live tree too; the live tree's
  remaining `check-rules` problems (24) and test failures are all in that
  Gothic spelling file, which is being written while I work and which I did
  not touch. (At the very end of the box, `src/pie/service.py` was briefly
  unparsable mid-write by another batch, so the last live measurement was
  echoed in a snapshot taken while it was valid — same rule file, same
  numbers: 66 → 218, 0 problems, 361 tests OK.)

## 1 · What the corpus asked for

Baseline (`tools/coverage.py --langs grc --limit 0`): `0/4918`, 3,102 identified,
2,951 PIE-linked, 0 rule applications. The worklist's 54 near misses are the
tail of a much larger set: 3,030 identified words carry an IPA and at least one
recorded ancestor, and under the old 14-rule file only **72** of them came out
right in the dictionary's IPA notation (normalised stress/​length); in the
romanisation the page compares, **66**.

Mining the edit scripts of the misses (alignment of the derived form with the
recorded IPA/romanisation) gave the same handful of changes over and over:
`w` deleted 67×, `ǣ/ā → ē` 108×, `ō → ɔ` 43×, `ē → ɛ` 31×, `u → y` 28×,
`ə → a` 10×, `ť/ď` 68×, `i → i̯` 32×, `n → ŋ` 9×. That list *is* the law set
below.

## 2 · The metric: three notations, and why coverage stays at 0

`tools/coverage.py` counts a word only when the derived **phoneme string** is
identical to `entry["word"]` — for Greek, the **Greek-script headword**
(`λύκος`). `_same_form` does not transliterate, and `data/spelling/grc.yaml`
does not exist, so every Greek word is `exact = 0` no matter what the laws do.
This is structural, not a failure of the rules: the same number would be 0 with
a perfect Proto-Greek→Greek phonology. The Greek writing layer belongs to the
other workstream; when it lands, this rule file is what it will write from.

The app has a second target, and the tests pin it: the word page compares the
derivation with the entry's **romanisation** (`πατήρ` → `patḗr`). That is why
η must be written **ē** and ω **ō**, not the IPA's ɛː/ɔː: with ɛ̄ the test
`test_greek_and_persian_are_compared_through_their_romanisation` fails. The
dictionary's IPA is a third notation (`/mɛ̌ː.tɛːr/`). The laws here therefore
speak the romanisation; the numbers below are measured with the same
comparison the page uses (`service._same_form` against `entry["translit"]`),
and the IPA is quoted only as evidence for a law. For the record, the shipped
file still raises the IPA-normalised count from **72 to 147** of 3,030; the
IPA-speaking variant of the same file reached 418 but breaks the page test,
so it was not shipped.

Consequence: aspirates are unreachable in this comparison (the transliteration
writes θ φ χ as **th ph kh**, the engine as `tʰ pʰ kʰ`), and so are ζ (written
**z**, the engine can only write `z d` or `z`) and ῥ (written **rh**, the
engine's `r̥` means syllabic). That is a notation fold in
`service._comparison_key`, not a sound law; reported, not patched.

## 3 · Rules added, and what each is worth

Measured by ablation against the romanisation target (words that stop matching
when the rule is removed; full set = 218). Every rule has a citation from
`data/sources.yaml` and an example verified by `check-rules`.

| rule | change | citation | worth |
|---|---|---|---:|
| `w_loss` | *w > ∅ everywhere (digamma not modelled) | sihler-1995, lejeune-1972, smyth-1920 | 53 |
| `schwa_to_a` | *ə > α (reflex of syllabic resonant) | sihler-1995, beekes-2011 | 23 |
| `long_a_to_eta` | *ā > η, written ē | sihler-1995, lejeune-1972, smyth-1920 | 16 |
| `palatal_t_geminate` | *ťť > σσ | sihler-1995 | 15 |
| `palatal_d_geminate` | *ďď > ζ (written z) | sihler-1995 | 11 |
| `ts_to_s` | *ts > σ | sihler-1995 | 11 |
| `palatal_t_after_consonant` | *ť > τ after a consonant | sihler-1995 | 7 |
| `palatal_n_geminate` | *ňň > ιν (κρίνω, φαίνω) | sihler-1995 | 7 |
| `palatal_l_geminate` | *ľľ > λλ | sihler-1995 | 7 |
| `y_loss_intervocalic_grc` | *y > ∅ between vowels | sihler-1995 | 6 |
| `ns_to_s` | *ns > σ (after lengthening) | sihler-1995 | 5 |
| `palatal_r_geminate` | *řř > ιρ | sihler-1995 | 2 |
| `h_loss_before_sonorant` | initial *h > ∅ before m l n (smooth breathing) | sihler-1995, lejeune-1972 | 2 |
| `palatal_t_to_s_initial` | *ť > σ word-initially (σήμερον) | sihler-1995 | 1 |
| `palatal_d_initial` | *ď > ζ word-initially (ζωός) | sihler-1995 | 1 |
| `palatal_d_after_consonant` | *ď > δ after a consonant (ἔρδω) | sihler-1995 | 1 |
| `lengthen_e_before_ns` | *e > ει before lost *ns (εἰς) | sihler-1995 | 1 |
| `lengthen_e_before_nts` | *e > ει before lost *nts | sihler-1995 | 1 |
| `lengthen_a_before_ns` | *a > ā before lost *ns (μέλας) | sihler-1995 | 1 |
| `ii_to_i` | *ii > ī (κρίνω) | sihler-1995 | 1 |

Kept verbatim from the old file (14 rules): the nine labiovelar splits
(100–122), the Grassmann transform and `ti_to_si`. Rewritten in place:
`lengthening_before_h` now produces **ει** (the spurious close vowel,
`*ehmi > *eimi`), and `h_loss_before_consonant` follows it (`*ēhmi > *ēmi`);
`long_a_to_eta` replaces the old `long_a_fronting` (ā > ǣ), whose ǣ matched
nothing in any notation and which was the single largest miss signature
(74 words). The other 19 ids are new.

The nine labiovelar rules, Grassmann, `ti_to_si` and the *h rules carry no
marginal worth in this notation because the words they feed end in an aspirate
or a ζ (above); they are correct and are the ones the IPA measuring would count.

## 4 · Rejected, with the measurement that killed it

1. **`n > ŋ` before a velar** — **−2**: the transliteration writes γγ/γκ as
   `ng`/`nk` (`ἄγγελος` *ángelos*), so `ŋ` costs two words and gains none.
   Removed.
2. **`s > z` before a voiced consonant** — **−1**: the transliteration writes
   σ as `s` in every position (`κόσμος` *kósmos*); only ζ is `z`. Removed.
3. **`*kʷʰ > tʰ / pʰ`** — **0 / 0**: correct (θέρος, φόνος, νεφρός, ὄφις,
   φθίσις are all in the corpus) but invisible while the transliteration writes
   θ as `th`; since a rule that gains nothing must go, it was removed, not
   shipped. It is the first rule to re-add when the comparison learns the
   digraphs.
4. **Final *-ā > -α after a consonant** (`γλῶσσα`, `μοῦσα` type) — **−14**
   net: it also shortens the η words (`δίκη` *díkē*), which outnumber them.
   Removed. The two outcomes are the same surface ā (from *-eh₂ vs *-yā) and
   the surface cannot tell them apart.
5. **`*ōw > ū`** (unconditional) — **−1** net: it buys `οὖς` but breaks
   `χρῶμα` and `ζωός`, where the *w is simply lost and ω remains. Restricted
   to *before *s*; in this notation the output would be `ou`, which the
   transliteration also writes (`oûs`), but the stress then sits on the wrong
   syllable, so the rule was dropped as worth 0.
6. **`*ei > ē`, `*u > y`, `*ō > ɔː`, `*ē > ɛː`** — the old file's ǣ rule's
   siblings. They are right in the IPA (εἶδος /êː.dos/, λύκος /lý.kos/) and
   were worth **23 / 50 / 116 / 31** when the target was the IPA; they are
   worth 0 in the romanisation, which writes ει `ei`, υ `u`, ω `ō`, η `ē`.
   They were removed because the app's target (and its test) is the
   romanisation. This is the honest shape of the trade: the IPA number and the
   app number are different languages.
7. **`n t s > s`, single intervocalic *ť, intervocalic *ď** — 0 each; the
   geminate rules and `ts_to_s` already cover every counted word. Removed as
   dead.
8. **Splitting *ā > η into "after every segment except ε/ι/ρ"** (obstruent +
   λ rules) — **−16**: the corpus fronts ā after vowels and after ρ more often
   than it retains it, so the blanket rule, with the residue stated in §5, is
   the measured-best generalisation.

## 5 · The largest remaining gap classes

Measured over the 3,091 identified words with a romanisation (classes by the
first reason the word fails; 235 hit in the final set here because duplicated
headwords collapse differently):

| n | class | example |
|---:|---|---|
| ~1,184 | morphology/ablaut: the recorded ancestor is a bare root or another cell (`*skeH`, `*kret`, `*mekʰ` → σκύλος, δημοκρατία, μύκης) | `σκύλος` *skŭ́los* ← `*(s)kewH-` |
| ~823 | long-vowel notation and the ᾱ residue: `κύων` *kŭ́ōn* ← `*ḱwṓ` (needs w-loss + the final -n restored), `ἀνήρ` *ā̆nḗr* ← `*h₂nḗr` (the prothetic ā), and the **77** words where ᾱ is retained after ε/ι/ρ (`χώρα`, `καρδία`, `γενεά`, `λαός`) | `χώρα` *khṓrā* |
| ~681 | aspirates: θ φ χ written `th ph kh`, engine `tʰ pʰ kʰ` (notation, not law) | `χώρα` *khṓrā* |
| 142 | **identity**: the recorded Proto-Greek form already *is* the Classical form and no law fires, which the programme refuses to count (`λόγος` ← `*lógos`, `μέγας`, `ἀγρός`) | `λόγος` *lógos* |
| 26 | initial ῥ: the transliteration writes `rh`, the engine's `r̥` means syllabic (notation collision) | `ῥίζα` *rhĭ́ză* |

Within the morphology class, the specific unreachable families are: roots
recorded without their suffix; a different paradigm cell (`-éyeti` 3sg vs the
1sg `-έω` the headword shows); and the great vowel contractions (`-έω`, `-όω`),
which are morphology, not phonology.

## 6 · Bugs found in `src/` or the neighbouring rules (not fixed)

1. **Stress-blind contexts in `ine-pro__grk-pro.yaml`.** `s_to_h_initial`
   (`env: left #, right V`) does not fire when the vowel is preceded by a
   stress token: `*sḿ̥teros` → `sˈateros`, never `hˈateros`; the same shape
   affects every rule whose right context is a segment and whose word starts
   with an accented syllable. A `ˈ?` in the context would fix them. I did not
   edit that file (out of my write set); the Greek side loses those words
   (e.g. `ἕτερος`, `ἕζομαι`, `ἕρπω`).
2. **`syllabic_l` does not exist** in `ine-pro__grk-pro.yaml` (m, n, r do), so
   `*l̥` survives into the Greek transition (`*wĺ̥kʷos` → `wˈl̥pos`). λύκος is
   saved only by its recorded Proto-Greek ancestor `*lúkos`. A rule belongs in
   the earlier file, not here.
3. **Grassmann applies across an onset cluster.** `*kʷʰtʰítis` → `ptʰisis`
   (φθίσις needs `pʰtʰ-`): the transform deaspirates the first of two
   aspirates in the same onset, where Grassmann's law does not apply.
4. **The context alternation `(s|t s)` never matches** the multi-segment
   alternative (`pattern._parse_atom` keeps the space as a literal). I split
   the ns/nts rules into two rules each instead.
5. **`r̥` is overloaded**: the tokenizer reads it as syllabic (ring below), the
   dictionaries use the same sign for voiceless [r̥] (ῥ, ρρ). No rule can
   produce the second meaning, which is why 26 ῥ words and the geminate
   `ἀγέρρω` cannot be reached.

## 7 · What I did not attempt

- **The breathings.** Rough/smooth breathing is not modelled: the presence of
  /h/ is decided by the writing layer (`ἵππος`, `ἕξ`, `ὁ`), and *h₁ is already
  deleted one stage earlier. `ἵππος` therefore stays a miss from the PIE
  etymon and is reached only through its recorded `*íkkʷos`.
- **Digamma.** *w loss is modelled as complete (Attic-Ionic); the dialects
  that kept ϝ, and the handful of words whose rough breathing continues *w
  (`ὕδωρ`, `ἕρμα`), are not.
- **Syllabic *l̥/*r̥ after a consonant** (`στρατός` < `*str̥h₃tós`, `βραδύς` <
  `*gʷr̥dus`): the earlier transition converts them to `ar` before I see them;
  the Greek `ρα` metathesis cannot be recovered from the surface.
- **The *-os, *-on, *-ti and other endings** are not touched: their words are
  right only when the recorded ancestor already carries the ending.
- **Anything morphological**: paradigm cells, vowel contraction, accent
  placement. They are the largest class above and they are W5's, not W3's.
- **The Greek writing layer**, including ť/ď/ň/ľ/ř as letters, breathings and
  iota subscript. `data/spelling/grc.yaml` does not exist and is owned
  elsewhere.

## 8 · Reproduce

```bash
PYTHONPATH=src python3 -m pie.cli check-rules                    # 0 from grk-pro__grc (live tree also shows the Gothic spelling file's)
PYTHONPATH=src python3 -m unittest discover -s tests -q          # 361 tests, OK (with got.yaml set aside)
PYTHONPATH=src python3 tools/coverage.py --langs grc --limit 0   # still 0/4918 (script target)

# the number in this report: derived form vs entry["translit"], same test as the word page
PYTHONPATH=src python3 - <<'EOF'
from pie import data
from pie.rules import derive
from pie.service import ancestor_starts, _same_form
ch = data.derivation_chain('grc'); rs = data.rulesets()
n = 0
for e in data.lexicon('grc'):
    if e.get('recon') or not e.get('translit'): continue
    for st, f in ancestor_starts(e, ch):
        d = derive(f, ch[ch.index(st):], rs)
        if d.skipped or not d.steps: continue
        if _same_form(d.output, e['translit']): n += 1; break
print(n)   # 218 with these rules; 66 with the previous file
EOF
```
