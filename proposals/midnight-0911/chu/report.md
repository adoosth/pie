# Old Church Slavonic from Proto-Slavic — night of 2026-11-09

**Status:** implemented in `data/rules/sla-pro__chu.yaml` and
`data/script/chu.yaml`, measured, all four gates green.
**Scope:** only the `sla-pro → chu` transition, its script table and
`tests/test_midnight_chu.py`.  No `src/`, no other rule or spelling file, no
lexicon, no doc was touched, and nothing was committed.
**Measured with:**

```bash
PYTHONPATH=src python3 tools/coverage.py --langs chu --limit 0
PYTHONPATH=src python3 tools/whatif.py --to chu --drop <law> --layers exact,orthographic,script,identity
PYTHONPATH=src python3 tools/council.py --stage sla-pro --to chu --rules <cand> --layers exact,orthographic,script
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q ; node tests/test_ui_render.js
```

---

## 1. Inventory: why the number was 0

The chain is `ine-pro → ine-bsl-pro → sla-pro → chu`, and **no rule file
existed for `sla-pro → chu`**.  `data/rulesets()` therefore had no entry for
that key, `derive()` recorded the hop in `Derivation.skipped`, and the counter
drops every word with a skipped hop before it compares anything
(`if d.skipped: continue`).  Every one of the 1,798 tested entries missed *by
construction*: not one letter was ever compared.

| | entries |
|---|---:|
| glossed headwords | 1,997 |
| with a recorded ancestor at a modelled stage (`identified`) | 1,799 |
| tested (reconstructions excluded) | 1,798 |
| **explained before** | **0** |
| — of which start at a Proto-Slavic ancestor | 1,811 recorded ancestor forms |
| — PIE-linked | 269 |
| — recorded as borrowed | 116 |
| written in Cyrillic | 1,785 (+201 mixed with a Latin gloss) |
| written in Glagolitic | 11 |

The probe the task named: **432** entries whose Proto-Slavic ancestor is
already character-identical to the entry's own `translit` (о, вода, нога, баба,
мати, зима, трава …).  Those need no sound change at all — the model simply has
to say so, which is what the counter's `identity` column does.

## 2. The script layer — `data/script/chu.yaml`

Old Church Slavonic is an **alphabet**, so this table is the strictest in the
repo: one sign writes one letter of the reading, and neither a sign nor a
letter may be left over (`one_letter_one_segment`).  Values are the
transliteration the record itself uses (ъ = ŭ, ь = ĭ, ѣ = ě, ѫ = ǫ, ѧ = ę,
ы = y, щ = št, ж = ž, ч = č, ш = š, ц = c), following Schenker (1995, 71-74),
Carlton (1991, ch. 1 and 118), Lunt (1974, 24-30), Huntley (in Comrie &
Corbett 1993, 148-152) and the letter values of Vaillant (1950, §§1-8).

| | count |
|---|---:|
| signs (Cyrillic, capitals, Glagolitic) | 118 |
| Cyrillic letters (50 lower-case + 23 capitals) | 73 |
| Glagolitic letters | 45 |
| capitals | 23 |
| iotified signs writing j + a vowel (ѥ ю ꙗ я є ѩ ѭ Є ⱓ ⱖ ⱗ ⱙ) | 12 |
| signs writing two **consonants** (щ ѕ ꙃ ꙉ ѯ ѱ, capital Ѯ, Glagolitic ⰷ ⱋ ⱜ) | 10 |
| conventions declared | 5 |

Coverage: **917 words matched through their own letters** (script column of the
published counter), plus **432** words that need no change at all (identity).
Every letter any headword writes is in the table (a test pins that: `ѷ` was
missing on the first run and was added).

No `data/spelling/chu.yaml` is written, on purpose: the orthographic layer is
only counted when `spelling.plausible()` can compare the derived form with the
entry's own IPA, and only **16** of the 1,997 OCS entries record an IPA, so a
spelling file could speak about at most sixteen words.  The letters are the
script table's job here, exactly as they are for Old Persian.

The table states four limits instead of hiding them: a **digraph оу** writes one
/u/ (101 headwords are misses because of it), the **two-consonant signs** щ ѕ ꙃ ꙉ
ѯ ѱ cannot be aligned by a one-letter-per-sign matcher (86 headwords), the
matcher **folds diacritics** so ѣ/е, ѫ/о and ѧ/е are one letter each (which is
why the script column, not the historical one, holds these matches), and the
**Glagolitic** rows are the alphabet's letters, only 18 of which this glossary
happens to use.

## 3. The law file — `data/rules/sla-pro__chu.yaml`

40 rules: 13 notation rules (tier `orthographic`) and 27 historical laws
(26 `established`, 1 `proposed`).  Δ = words the file loses when that one rule
is removed (`whatif --drop`, layers `exact,orthographic,script,identity`);
"lost" = words the rule *breaks* that another rule or the parent chain
reconstructs.  Sums do not add: laws overlap.

| law | tier | Δ | lost | what it does |
|---|---|---:|---:|---|
| `soft_jer_transliteration` | orthographic | 349 | 0 | ь → ĭ (last) |
| `hard_jer_transliteration` | orthographic | 461 | 0 | ъ → ŭ (last) |
| `liquid_or_to_ra` | established | 48 | 0 | *TorT > TraT medially |
| `liquid_ol_to_la` | established | 40 | 0 | *TolT > TlaT |
| `yer_r_soft_metathesis` | established | 35 | **1** | *TьrT > TrьT |
| `liquid_er_to_rě` | established | 32 | 0 | *TerT > TrěT |
| `initial_jer_i` | established | 19 | 0 | initial *jь- > i- |
| `dl_to_l` | established | 16 | 0 | *dl > l (before the metatheses) |
| `liquid_or_to_ra_initial` | established | 16 | 0 | *orT- > raT- |
| `l_palatal_to_lj` | established | 15 | 0 | *ľ > lj before a back vowel |
| `yer_r_hard_metathesis` | established | 13 | 0 | *TъrT > TrъT |
| `d_palatal_to_zhd` | established | 10 | 0 | *ď > žd |
| `yer_l_hard_metathesis` | established | 9 | **1** | *TъlT > TlъT |
| `accent_grave_a` | orthographic | 8 | 0 | accent/macron on a is notation |
| `liquid_el_to_lě` | established | 7 | 0 | *TelT > TlěT |
| `yer_l_soft_metathesis` | established | 7 | 0 | *TьlT > TlьT |
| `accent_yer_hard` | orthographic | 6 | 0 | accent on ъ is notation |
| `prothesis_e` | **proposed** | 5 | 0 | initial *e- > je- / _s, z |
| `accent_grave_i` | orthographic | 4 | 0 | accent on i is notation |
| `n_palatal_to_n` | established | 4 | 0 | *ň > n elsewhere |
| `soft_jer_jь_to_ii` | established | 4 | 0 | final *-ьjь > -ii |
| `liquid_ol_to_la_initial` | established | 3 | 0 | *olT- > laT- |
| `prothesis_ě` | established | 3 | 0 | initial *ě- > ja- |
| `n_palatal_to_nj` | established | 3 | 0 | *ň > nj before a back vowel |
| `zt_to_st` | established | 3 | 0 | *zt > st |
| `accent_grave_e` | orthographic | 2 | 0 | accent on e is notation |
| `accent_grave_o` | orthographic | 2 | 0 | accent on o is notation |
| `prothesis_ę` | established | 2 | 0 | initial *ę- > ję- |
| `initial_ji_to_i` | established | 2 | 0 | initial *ji- > i- |
| `kv_to_cv` | established | 2 | 0 | *kv > cv / _ front V |
| `accent_grave_ě` `_ę` `_y` `_yer_soft` | orthographic | 1 each | 0 | one word each |
| `t_palatal_to_sht` | established | 1 | 0 | *ť > št (only the Glagolitic word escapes щ) |
| `r_caron_to_r` | established | 1 | 0 | *ř > r |
| `stress_token_dropped`, `accent_grave_u`, `shch_to_sht`, `l_palatal_to_l` | ortho./est. | **0** | 0 | fire, carry no word (stated, not claimed as evidence) |

Citations: Vaillant 1950, §§5-9, 61-78, 84-88; Meillet 1934, ch. 3-5;
Shevelov 1964, 391-424; Fortson 2004; with Schenker 1995, Carlton 1991, Lunt
1974 and Huntley 1993 named in each rule's prose.  `data/sources.yaml` holds no
key for Schenker, Carlton, Lunt or Huntley, so the machine-checked `references`
use the four keys that exist and the others are cited in the description —
adding those four keys to `data/sources.yaml` is outside this task's scope
(§7 amendment).

Two laws still cost one word each, and that is reported, not papered over:
`yer_r_soft_metathesis` loses **вьрзати** (the record keeps the jer before r
against the regular *TьrT > TrьT) and `yer_l_hard_metathesis` loses **дългъ**
(the record has a soft jer there, against *dьlgъ > dlъgъ).

## 4. The council

Rules are measured on the whole subtree, and the subtree of this transition is
one language.  Accepting the file as a candidate against an empty transition:

```text
$ council.py --stage sla-pro --to chu --rules candidates/all-final.yaml --layers exact,orthographic,script
  chu   33 ->  903  (+870)  lost 0    ACCEPT
$ ... --layers exact,orthographic,script,identity
  chu  426 -> 1,291 (+865)  lost 0    ACCEPT
```

Every accepted candidate, measured alone against the file with that law removed:

| candidate | verdict | gained | lost |
|---|---|---:|---:|
| `dl_to_l` | **ACCEPT** | 16 | 0 |
| `zt_to_st` | **ACCEPT** | 3 | 0 |
| `kv_to_cv` | **ACCEPT** | 2 | 0 |
| `initial_ji_to_i` | **ACCEPT** | 2 | 0 |
| `soft_jer_jь_to_ii` | **ACCEPT** | 4 | 0 |
| `prothesis_e` (narrowed to _s, z) | **ACCEPT** | 5 | 0 |

### Rejected candidates, with their losing lists

| candidate | claimed law | gained | **lost** | why it fails |
|---|---|---:|---:|---|
| `initial_ja_to_a` | initial *ja- > a- | 2 (азъ ×2) | **12** | ꙗдра, ꙗдъ, ꙗздити, ꙗко ×2, ꙗма, ꙗмо, ꙗрость, ꙗръ, ꙗсли, ꙗснъ, ꙗсти — every other initial ja- keeps its j.  азъ is the exception, not the rule. |
| `soft_jer_to_hard_after_liquid` | *ь > *ъ / liquid _ C | 8 (врътъ, врътъпъ, дръжава, дръжати, жлътъ, смръдъ, тлъкнѫти, трънъ) | **81** | It hardens влькъ, вльна, врьхъ, дльгъ, срьдьце, прьстъ and 75 more: the yers' quality is not conditioned by the liquid. |
| `prothesis_e` (general) | initial *e- > je- | 5 (ѥзеро, ѥсень, ѥси, ѥсмъ, ѥсмь) | **3** | единъ, етеръ, еще keep their e-.  Kept only in the narrower `_ s, z` environment, tier `proposed`. |
| `soft_jer_j_to_i` | *ьj > ij | 0 | 0 | Dead: the diacritic fold already lets ьj align with иѥ.  Removed from the file. |

All four files are kept in `proposals/midnight-0911/chu/candidates/`.

## 5. The numbers

Published counter (`tools/coverage.py --langs chu --limit 0`), 1,798 tested
entries:

| | before | after |
|---|---:|---:|
| **exact** (historical) | **0** | **0** |
| **orthographic** | 0 | 0 |
| **script** (letters read off the headword) | 0 | **917** |
| **identity** (path needs no change) | 0 | **432** |
| **explained** (union of the layers) | **0** | **1,317** |
| explained rate | 0 % | **73.2 %** |
| near miss (≤ len/4) | — | 5 |

`exact` stays 0 for the honest reason that gives the script layer its name: the
laws produce a *reading* (Latin letters) and the glossary holds *Cyrillic and
Glagolitic letters*, so no string can ever be equal.  The script column is the
claim that the letters are the letters of the derived form, and it is never
added to the historical figure.  Note that the counter counts identity even
when the script branch already counted the word, so 917 + 432 = 1,349 against
1,317 explained — 32 words are in both columns; **1,317 is the union**.

## 6. The residue: 481 words, and three worked examples

(1798 − 1317 = 481; the miss probe prints 482 rows because it also looks at
the one reconstruction row the published counter excludes.)

| class | entries | why |
|---|---:|---|
| the **оу** digraph writes /u/ in two signs | 102 | one-sign-one-letter matcher |
| **щ ѕ ꙃ ꙉ ѯ ѱ** write two consonants in one sign | 86 | same |
| **bound forms and prefixes** (`на-`, `-ити`, `въ-` …) | 21 | the counter's `bound` column compares Latin strings; a Cyrillic target never pairs |
| morphology the model lacks (prefixed verbs, n-stem `корень`, `писмѧ`) | 273 | a formation, not a sound law |

Three worked examples that still fail:

1. **доухъ** *duxŭ* "spirit".  The parent chain gives PSl *duxъ* → laws →
   `duxŭ` (2 rules fire), exactly the recorded reading.  The headword writes
   д-о-у-х-ъ: five signs for four letters.  The matcher has one letter to spend
   on each sign, so the word is a miss.  *This is a limit of
   `src/pie/script.py`, not of the phonology* — see §7 for the exact patch.
2. **нощь** *noštĭ* "night".  PSl *noťь* → `noštĭ` (the *ť > št law fires and
   is right), but щ is one sign for two segments.  71 headwords contain щ.
   Honest miss; the rule that produces the right letters is in the file.
3. **царь** *carĭ* "king".  PSl *cěsařь* → `cěsarĭ`: the model keeps the jat'
   and the record has a.  OCS *cěsařь > carь* is the change *ě > a after c*,
   which the corpus shows only in this word (цена keeps ě), so it is **not**
   written as a law: a rule for one word is a lookup.  It stays a miss and the
   report says why.

A fourth class worth naming: **корень** *korenĭ* "root" and its family
(прьстень, ремень, степень) come from *-y* stems in the record's Proto-Slavic
ancestor, and the OCS word adds the *-en-* of the n-stems.  That is a
derivational formation, not a sound change; no rule file can carry it.

## 7. Out-of-scope findings, with exact patches

1. **`tests/test_web.py` used to pin `chu` as a gap.**  At 04:30 it still
   asserted `self.assertIn("chu", gaps)`, which this file makes false.  Another
   worker edited the same shared worktree while this session ran, and the
   assertion is now the registry-wide invariant (a language is a gap iff some
   step of its chain has no rule file) — so no patch is needed and the suite is
   green.  Recorded here because the number changed under my feet.
2. **The matcher cannot spend two letters on one sign.**  `src/pie/script.py`
   `_align_letters` walks signs and tokens one-to-one.  A table row whose value
   is two segments (`щ` = št) should consume two tokens.  Minimal change in
   `_align_letters`:
   ```diff
   --- a/src/pie/script.py
   +++ b/src/pie/script.py
   @@ def walk(i, j):
   -        if token in (signs[i].get("sounds") or [signs[i]["value"]]) and walk(i + 1, j + 1):
   -            return True
   +        sounds = signs[i].get("sounds") or [signs[i]["value"]]
   +        for sound in sounds:
   +            n = len(_base_letters(sound))
   +            if n > 1 and [t for t, _v in _base_letters(sound)] == \
   +                    [t for t, _v in tokens[j:j + n]] and walk(i + 1, j + n):
   +                return True
   +        if token in sounds and walk(i + 1, j + 1):
   +            return True
   ```
   With `sounds: [št]` on щ this would read ≈ 185 more words (the 86
   two-consonant-sign misses plus most of the 102 оу misses once the digraph is
   declared as one sign's worth of letters).
3. **`data/sources.yaml` lacks Schenker 1995, Carlton 1991, Lunt 1974 and
   Huntley 1993**, which the task asks to cite.  They are cited in the rules'
   prose; adding the keys (id, title, kind) would let them be machine-checked:
   ```yaml
   - id: schenker-1995
     title: Schenker, The Dawn of Slavic (1995)
     kind: grammar
   - id: carlton-1991
     title: Carlton, Introduction to the Phonological History of the Slavic Languages (1991)
     kind: grammar
   - id: lunt-1974
     title: Lunt, Old Church Slavonic Grammar (6th ed. 1974)
     kind: grammar
   - id: huntley-1993
     title: Huntley, Old Church Slavonic, in Comrie & Corbett, The Slavonic Languages (1993)
     kind: handbook
   ```

## 8. Gates

```text
PYTHONPATH=src python3 -m pie.cli check-rules
  30 rule files, 740 rules, 1010 examples verified, 0 problems
  (count is a shared-worktree snapshot; 0 problems is the gate)

PYTHONPATH=src python3 tools/coverage.py --langs chu --limit 0
  chu  0/1997 exact; 1,317 explained of 1,798 tested (917 script + 432 identity)

node tests/test_ui_render.js
  script reading and timeline ok / construction menu ok / recorded starts ok /
  overall progress bar ok / join timeline and coverage buckets ok

PYTHONPATH=src python3 -m unittest discover -s tests -q
  Ran 560 tests — OK  (shared worktree; this file contributes 28)
```

`tests/test_midnight_chu.py` adds **28 tests**: every law's tier and citation,
each law's examples re-derived alone, the script sign table (no headword letter
unknown, every Cyrillic letter witnessed), the readings it must accept and
reject (a written vowel cannot be dropped, a wrong vowel of the same letter is
rejected, a written consonant is not forgiven, the iotified letters write j),
the words each law must **not** touch (*gora*, *dolnь*, *dъlgъ*, *kvasъ*,
*prьstъ*, *vьlkъ*, *trьnъ*, *jazъ*, *edinъ*, *ešče*), and a floor of 850
script words and 1,200 explained.
