# Persian and Middle Persian — fourth pass (night of 2026-11-09)

Scope: continue the Middle Persian readings harvest, register what the
`peo → pal` laws still owe, and audit the Persian misses by cause.  Two laws
were registered (one new, one widened), the reading table grew 600 → 651
spellings, and no previously-correct word was moved.

Commands:

```bash
PYTHONPATH=src python3 tools/coverage.py --langs fa pal --out /tmp/fa3-before.json
PYTHONPATH=src python3 tools/coverage.py --langs fa pal --out /tmp/fa3-after.json
PYTHONPATH=src python3 tools/council.py --stage peo --to pal --rules <candidate> --layers exact,orthographic,script
PYTHONPATH=src python3 tools/whatif.py --to pal --drop <rule-id> --layers exact,orthographic,script
PYTHONPATH=src python3 tools/build_pal_readings.py --check
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q
node tests/test_ui_render.js
```

## Before / after

| | fa before | fa after | pal before | pal after |
|---|---:|---:|---:|---:|
| glossary rows | 5,555 | 5,555 | 616 | 616 |
| identified | 1,692 | 1,692 | 61 | 61 |
| **exact** (laws, character for character) | **0** | **0** | **1** | **2** |
| **orthographic** (writing conventions) | **231** | **252** | 0 | 0 |
| **script** (read sign by sign) | **307** | **331** | 19 | 19 |
| identity (spelling right, no law fired) | 88 | 93 | 0 | 0 |
| built from pieces (join, never explained) | 41 | 41 | 0 | 0 |
| **explained** (all honest columns) | **410** | **440** | **20** | **21** |
| readings `data/readings_pal.json` | 600 | **651** | 600 | **651** |

fa explained 410 → 440 (**+30**, 7.4 % → 7.9 % of the glossary; 24.1 % → 26.0 %
of the 1,692 identified).  pal explained 20 → 21, exact 1 → 2 (3.2 % → 3.4 % of
the glossary).  `exact` for fa stays 0: the Persian target is Perso-Arabic, so
a letter-for-letter Latin match is impossible by construction and the two
written layers carry the number — the same rule the earlier passes stated.

## What moved, and by how much

1. **`final_h_loss` widened from `h` to `(h|ʰ)`** (`data/rules/peo__pal.yaml`,
   tier unchanged: established).
   The record transcribes the Old Persian final *-h two ways: plain `h`
   (`*aspah`) and the modifying `ʰ` the cuneiform readings use (`puçaʰ`).  It
   is one Proto-Iranian *-ah, so one law must catch both notations; the
   aspirated spelling previously skipped both this rule and the apocope behind
   it.  Carried, measured by ablation:
   - pal **+6 words** (gwlg, hm, lwcyk', spyt', tʾht', 𐫅𐫏𐫇) — dropping the
     law loses 7, one of which (`pus`) also needs the next law;
   - fa **+40 words** — dropping it loses 47 and gains 7 (the 7 are correct
     under the earlier misanalysis only, and are counted as the rule's net
     contribution).
2. **`cedilla_to_s_before_final_a`, new** (`data/rules/peo__pal.yaml`, order 30,
   `tier: proposed`, env `right: "a ʰ? #"`).
   OP word-final *-ça(h) gives MP -s (puça > pus), while intervocalic ç still
   gives h (xšaça- > šahr, the registered `cedilla_to_h`).  Carries pal **+1**
   (pus), fa **+2** (داس, پاس); dropping it costs exactly those three and
   nothing else.  Council over the subtree: ACCEPT (+3, nothing lost).
3. **Readings harvest, 600 → 651 spellings** (`tools/build_pal_readings.py`,
   `data/readings_pal.json`).
   - Three book-Pahlavi sign values the table was missing, each a real value of
     the sign and each exercised by the record: waw writes **b** (`wʾčʾl` =
     bāzār), heth writes **x** (`hwtʾy` = xwadāy), and the same ṣade sign is
     written `č` as well as `c` (`wʾčʾl`); `ẖ` added as the same heth.
   - The etymology harvest had grown stale against that day's lexicons: the
     shipped table held 600 rows where the builder now finds 627 before the
     sign fixes and **651** after.  `--check` is identical.
   - Rows by tier: recorded 210, quoted 404, script-quoted 37.  Every *quoted*
     row passes the builder's letter test (`tests/test_night_fa3.py`).
   - Contribution on its own (old table restored, both laws in place):
     fa orthographic **+15**, script **+17**, identity **+5**, explained
     **+23**; pal unchanged (its own spellings were already read).

## Persian audit: the 1,253 remaining misses, by cause

| cause | n | verdict |
|---|---:|---|
| other segmental difference (stem allomorphy, learned forms, vowel quality) | 725 | sound-law work, one class at a time; no single law spans them |
| infinitive vs present stem (`کردن` ← `kar`, `آمدن` ← `ad`) | 227 | morphology (W5), not a sound law |
| target or ancestor still a script form | 99 | reading layer: the Pahlavi/Manichaean/cuneiform spelling is the target |
| initial cluster (`گرو`, `خواب` ← `grab`, `hwop`) | 137 | needs an epenthesis law the pattern language cannot state (no back-reference) |
| ancestor is an unread transliteration (`bʾg`, `pgtʾmbl`) | 46 | readings: the record states no reading for these spellings |
| spelled exactly, IPA/guard rejects | 19 | notation of the entry's own IPA, not the letters |

The 46 unread transliterations are the tail of the same harvest: the etymology
sentences quote a reading for most of them, but this builder refuses a spelling
whose signs cannot say the stated reading (335 refusals from the MacKenzie OCR,
215 from etymology sentences) — the largest remaining class is Book Pahlavi
script forms whose final vowel is unwritten (`𐭯𐭠𐭫𐭮𐭩` pārs), and choosing
between `pārs` and `pārsī` there would be inventing a reading.

## Rejected candidates (with the numbers that rejected them)

All four are kept in `proposals/night-0911/fa3/candidates/` with gain/loss:

- **`theta_to_h_before_r`** (OP Miθra- > mihr): 0 gained / 0 lost.  The words
  that would show it are targeted by their spellings, so a reading-level change
  moves no sign.  Dead rule, not registered.
- **`final_aka_to_ag`** (OP final *-akah > MP -ag): 0 / 0 — the existing
  `final_h_loss` + `final_vowel_loss` path already derives every visible word.
- **`final_ah_to_nothing`** (delete *-aʰ in one step): **+1 pal / +7 fa, 0
  lost** — rejected only because it duplicates the two-step derivation;
  widening `final_h_loss` gives the same measurement with one law instead of
  two (this is the alternative that was not chosen, recorded).
- **`cedilla_to_s` with env `right: "a #"`**: 0 / 0 — the environment was
  narrower than the data, because the final *-h is a separate `ʰ` token.
- **`a_to_o_before_nasal`** (*a > o / _n): claimed **+37 fa, 0 lost** — and
  rejected because the gain is a **counter artefact**.  Persian keeps /a/ before
  a nasal (رنگ /ˈraŋɡ/, سنگ /ˈsanɡ/) and the rule moves no letter, since /a/
  and /o/ are both unwritten.  It "gained" because `orthographic_hit` and the
  script layer require at least one law to fire: a word whose spelling was
  already right but had no step was counted as *identity*, and a no-op law
  manufactures the step (`--layers exact,script` alone still shows +33 on the
  same words).  A rule whose only effect is to satisfy the counter's
  precondition is in the same class as a lookup.
- **`y_to_j_before_u`, `w_to_v_between_vowels`** (جوان < MP yuwān, گوهر < MP
  gōhar): 0 / 0 — both changes are real in New Persian but no corpus word
  reaches them through a Middle Persian ancestor the laws can start from.

### Finding for the integrator

The written-layer columns can be inflated by any vacuous law over a segment pair
that shares a letter or is unwritten on both sides.  `tools/whatif.py` should be
read with `--layers exact` first: a candidate that gains only in
`orthographic`/`script` while changing no letter and no plausibility verdict is
not a law.  (Not changed here: `tools/whatif.py` is outside this pass's write
set and the measurement is shared with every stream.)

## Files changed

- `data/rules/peo__pal.yaml` — one new proposed law, one widened established law,
  prose and examples for both.
- `tools/build_pal_readings.py` — waw = b, heth = x/ẖ, ṣade written č, with the
  reason in the table.
- `data/readings_pal.json` — regenerated (600 → 651 spellings).
- `tests/test_night_fa3.py` — new: quoted rows spellable, every row sourced and
  tiered, the two recorded readings, table matches the builder, the two laws
  fire and the ç split stays split.
- `proposals/night-0911/fa3/` — this report and the four candidate files.

No change to `data/spelling/fa.yaml`, `data/spelling/pal.yaml`,
`data/script/fa.yaml`, `data/script/pal.yaml` (unchanged: the remaining Persian
misses are segments, not letters — the earlier pass's measurement still holds),
`data/sources.yaml` (no new source: every citation was already registered).

## Gates

- `pie check-rules`: **0 problems**, 32 rule files, 809 rules, 1,178 examples
  (805/1,164 when this pass's own gate ran; the rest are the concurrent
  Proto-Indo-Iranian stream's).
- `unittest discover -s tests -q`: **650 tests, 1 failure**, and the failure is
  not this pass's: `tests/test_web.py::TestReconstructedRungs::
  test_an_unrecorded_old_persian_rung_of_water_is_not_attested` expects the Old
  Persian rung `wˈādar` and the tree now derives `wˈadar` — a change upstream of
  `peo → pal`, in the concurrent worker's `ine-pro__iir-pro` palatalisation
  work.  Left to its author, per the brief.
- `node tests/test_ui_render.js`: ok.
- `tools/build_pal_readings.py --check`: identical (651).
- fa/pal measured with `tools/coverage.py --langs fa pal --out /tmp/…`
  (always `--out`, so `docs/COVERAGE.md`, the README block and
  `data/coverage.json` are untouched).

## Ceiling

`pal` can only grow where a target is a Latin reading; 40 of its 61 tested rows
target the spelling itself, so they can be *script* matches at best.  `fa` needs
the two layers that are out of reach tonight: an epenthesis law (137 words) and
the morphology layer (227 words).  Neither is faked here.
