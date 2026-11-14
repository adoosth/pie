# Persian (`fa`), second pass: the misses classified, the guard repaired, two *-g laws

**Date.** 2026-11-09.
**Author.** descriptive linguist.
**Scope written.** `data/rules/pal__fa.yaml`, `data/spelling/fa.yaml`,
`proposals/2026-09-11-b/fa2b/**`, `tests/test_batch_fa.py`. Nothing else.
**Not committed** (merged by the reviewer).

## 1 · What changed, in one paragraph

Three artefacts, all in `pal__fa` and the Persian writing layer. (1) The reading
guard of the orthographic layer was comparing alphabets: the dictionary's **/j/**
is the laws' `y`, its **/ŋ/** is the laws' `n`, and the Perso-Arabic abjad **does
not write short vowels**, so their number cannot be evidence about a spelling.
Folding those into the guard (`data/spelling/fa.yaml`, `guard.equivalences`)
adds ten words to `explained` and spells 24 more. (2) One narrow sound law,
**MP final *-ūg > NP -ū** (`final_ug_to_u`, order 14), adds five and loses none.
(3) Its other half, **MP final *-āg > NP -ā** (`final_long_ag_to_a`, order 12.5),
adds three (دانا) and loses none. Measured on the whole language with the
council's layers `exact,orthographic,script`: explained **373 → 391**,
orthographic **207 → 231**, script **299 → 307**, exact unchanged at 0 (a final
stage cannot produce a Persian letter string), `pal` untouched.

## 2 · The miss audit

Every Persian entry with a recorded ancestor at a modelled stage is tested
exactly as `tools/coverage.py` tests it (all seven layers: exact, pathway,
script, orthographic, citation, identity, bound). The 1,301 that remain are
classified by the **nearest recorded ancestor** (the transition that decides the
last mile) and by what would have to change:

| cause | n | of which nearest ancestor is Middle Persian |
|---|---:|---:|
| **a** a law ran and left a different form (missing or over-broad law) | 410 | **94** |
| **b** morphology / citation form (bound headword, infinitive, plural) | 210 | **33** |
| **c** orthography or notation only (segments equal the record's IPA) | 21 | **19** |
| **d** the recorded ancestor is a different lexeme | 290 | **61** |
| **e** the nearest ancestor has no reading (script or consonantal transliteration), so no law can start | 370 | **295** |

| nearest ancestor | a | b | c | d | e | total |
|---|---:|---:|---:|---:|---:|---:|
| `pal` (Middle Persian) | 94 | 33 | 19 | 61 | 295 | **502** |
| `peo` (Old Persian) | 38 | 13 | 1 | 27 | 23 | 102 |
| `ira-pro` (Proto-Iranian) | 186 | 108 | 1 | 98 | 26 | 419 |
| `iir-pro` (Proto-Indo-Iranian) | 30 | 17 | 0 | 21 | 6 | 74 |
| `ine-pro` (PIE only) | 62 | 39 | 0 | 83 | 20 | 204 |

Read the table this way: the **`pal` row is this transition's work**; the rows
below are upstream (the `peo__pal` rules and the readings are not this transition's), but they
still pass through `pal → fa`, so a final-stage law can sometimes shorten them.
The 295 `pal` rows in column **e** are the Pahlavi wall the brief told me to
skip: a Book-Pahlavi or consonantal ancestor with no reading. Column **a** at
`pal` (94 words) is where a law could act; most of it is lexical, as §5 shows
— the *-āg law of §3.3 took three of them.

Reproduce:

```
PYTHONPATH=src python3 proposals/2026-09-11-b/fa2b/audit.py      # misses.tsv
python3        proposals/2026-09-11-b/fa2b/classify.py           # classified.tsv
```

`misses.tsv` / `classified.tsv` carry one row per word (word, ancestor,
derivation ladder, spelling, distance, cause). The heuristics are stated in
`classify.py` and every bucket was hand-checked on its first 25 rows.

## 3 · The artefacts

### 3.1 Reading guard: segments, not alphabets

`data/spelling/fa.yaml`, new top-level `guard.equivalences` (the same mechanism
`sa.yaml` and `grc.yaml` already use; applied to both sides, never to a rule's
output):

| fold | why | citation |
|---|---|---|
| `y: j` | ی is the palatal approximant /j/; the laws write `y`, the dictionaries /j/ | Thackston 1993 §1–3; Windfuhr 2009, Persian consonant inventory |
| `ŋ: n` | /ŋ/ is the velar allophone of /n/, not a phoneme | Windfuhr 2009, Persian phonology |
| `aː iː uː eː oː ɑː ɒː` → `ā ī ū ī ū ā ā` | the long vowels the abjad *does* write | Thackston 1993 §1–3 |
| `a e o i u æ ɑ ɒ ɛ ɔ ɪ ʊ ə ɐ` → ∅ | the short vowels the abjad does **not** write | Thackston 1993 §1–3 |

The last line is the substantive one. The guard exists so that two wrong vowels
cannot concatenate into the right letters; in an abjad the short vowels have no
letters, so their number is not evidence. Persian also breaks initial clusters
with an unwritten anaptyctic vowel (درخت is d-r-x-t and /da.ˈraxt/), which the
old guard refused for every such word. The consonants and the **long** vowels
are still compared (test: `draxt` against /da.ˈraːxt/ is refused).

Words gained (10, each now counted as *spelled*, never as reconstructed):
بادیه، دایه، سرای، پای، پیاده×2، می، روی×3. Note سرای and پای: the old guard
refused them because the dictionary writes /sa.ˈraːj/ and /ˈpaːj/ with an
anaptyctic vowel and /j/; the model's `srāy`/`pāy` were right all along. That
also means a blanket final *-āy > -ā is now *measurably harmful* (§5.2).

### 3.2 `pal__fa: final_ug_to_u`

```yaml
- id: final_ug_to_u
  order: 14
  match: g
  replace: ""
  env: {left: ū, right: "#"}
  tier: proposed
```
MP hindūg > NP hindū, bānūg > bānū, anōš-dārūg > anūšdārū (the initial *a is
unwritten in نوش‌دارو, so the script layer is what sees the word). The environment is
**long ū only**, because the same *-g is kept after *ō in sōg > sūg and after
*ē in dēg > dīg; see §5.1. Citations: MacKenzie 1971 (b'nwk' bānūg, hndwk'
hindūg), Sadeghi 1978, Windfuhr 2009.

Measured (whatif, whole language, layers `exact,orthographic,script`):
`+5 words (بانو×2, هندو×2, نوش‌دارو), 0 lost`. Council (`--stage pal --to fa`)
**ACCEPT: +3, nothing lost** (the two duplicate بانو/هندو rows collapse there).
`check-rules` verifies all three examples.

### 3.3 `pal__fa: final_long_ag_to_a`

```yaml
- id: final_long_ag_to_a
  order: 12.5
  match: g
  replace: ""
  env: {left: ā, right: "#"}
  tier: proposed
```
The other half of the *-ag ending. After a long *ā the velar goes and the vowel
stays long, so the word ends in **-ā** where the short *-ag class ends in **-e**.
MacKenzie enters the adjective dʾnʾk' *dānāg* 'wise, knowing' and its New
Persian continuation is dānā; the same -āg is the productive possessive suffix
of Middle Persian (Skjærvø, *Middle Persian*, in Windfuhr 2009, on the -āg/-ā
adjectives). It must not be folded into `final_ag_to_e`: MP murtag > NP **morte**
and nāmag > nāme are the short class, and the test pins both.

Measured: `+3 (دانا×3), 0 lost`. Council `--drop final_long_ag_to_a` reports the
law's whole load — `fa 262 → 261, LOST: دانا, REJECT` in the drop direction —
i.e. it carries exactly one headword and nothing else moves. Its three rows are
the same word from three records, so the honest reading is **one word gained**,
and that is how §4 counts the attribution.

Note what it does *not* claim: MP hmʾk' *hamāg* continues as NP hame with a
short final vowel, so the *-āg class is split exactly like *-ōg (§5.1). The law
carries dānāg and the rule's own example shows hamāg producing hamā, which is
*not* the word — visible in `check-rules` and left as a miss rather than
repaired by bending the environment.

## 4 · Numbers

Same checkout, HEAD versus this working tree, one command each
(`tools/coverage.py --langs fa pal --limit 0`):

| `fa` | HEAD | now | Δ |
|---|---:|---:|---:|
| exact | 0 | 0 | 0 |
| orthographic (spelled right) | 207 | **231** | **+24** |
| script (a possible reading of the signs) | 299 | **307** | **+8** |
| **explained (all layers)** | **373** | **391** | **+18** |
| identity (no law needed) | 65 | 65 | 0 |
| pathway (per-word exception) | 5 | 5 | 0 |
| joined (formation) | 41 | 41 | 0 |
| tested | 1,692 | 1,692 | 0 |

`pal`: unchanged (exact 1, script 19, explained 20 — the 19 script matches are
the other batch's Middle Persian reading table, measured here but not mine).

Attribution, computed by diffing the explained sets: the guard adds 10
(بادیه، دایه، سرای، پای، پیاده×2، می، روی×3), `final_ug_to_u` adds 5
(بانو×2، هندو×2، نوش‌دارو), `final_long_ag_to_a` adds 3 (دانا×3 — one headword
from three records). The orthographic column gains 24 rather than 10 because a
word can be both script-read and spelled right (اشتر، انگشت، درخت، درنگ، سرود،
سروش، سپر، فریدون، گران، گروه …), and the two *-g laws' words are spelled right
too: the columns overlap by design and `explained` counts each word once.

**Tests.** `tests/test_batch_fa.py` — **15 tests**: the two laws' witnesses
(hindūg > hendū, bānūg > bānū, anōš-dārūg > anūšdārū, dānāg > dānā), that
neither fires on the wrong class (*-ōg, *-ēg, short *-ag), that each law gains
words and hides none (measured against the same transition with the law
disabled), the four guard folds and two negative guard tests.
`check-rules`: 30 files, **740 rules, 1,010 examples, 0 problems** (the count
includes another batch's in-flight Old Church Slavonic file).
`node tests/test_ui_render.js`: green. `unittest discover`: **560 tests, all
pass** (the `chu` failure of §6.3 is gone — that batch fixed it).

## 5 · The residue, with the discussion that produced it

### 5.1 The *-ōg class is split, so it is not a law

A law `*-ōg > -ū` would gain **10** (بانو…, تیهو, سو×3, مینو, هندو…) and lose
**1**: سوگ sūg 'mourning'. The record derives both سو (sū) and سوگ (sūg) from
the *same* Middle Persian form `sōg` (swk'), so no phonological environment can
separate them; the council therefore **REJECTs** it. The *-ūg subclass is clean
and is what §3.2 ships. Trace:

```
pal sōg → sūg   (long_o_to_long_u)
pal sōg → sūg   (long_o_to_long_u)   ← the same path spells both words
```

This is the same shape as `final_long_a_shortening` (deleted earlier in the batch):
a law that is right for most words but describes a class the record contradicts
is not a law. It is reported, not shipped.

### 5.2 A final *-āy deletion now costs two explained words

Measured `+3 / −2`: it gains هما×2 and پا, and **loses سرای and پای**, which the
guard repair (§3.1) has just made explainable. The glide loss is real but
lexically split (پای، خدای، جای lose it; سرای keeps it), so it is a citation-form
fact (the -y belongs to the oblique), not a sound law. Classified **(b)**.

### 5.3 A law that is right on average but has a lexical residue: `final_ag_to_e`

Dropping it costs **40** words (آماده، باده، باره، …) and gains only two (سترگ،
سگ), so it stays; but it also derives رگ rag > re and سگ sag > se, which are
wrong. The suffix *-ag and a stem-final *g are the same two segments, so a
segment environment cannot separate them. This is the clearest case in the
language where the model is right for the class and wrong for the word, and it
is published as a miss rather than repaired by a lexical exception.

### 5.4 Three words that still cannot be explained, and why

1. **جوز jowz** /ˈd͡ʒawz/ ← MP gōz. Trace `gōz → gūz` (only
   `long_o_to_long_u`). Needed: g > j and ō > aw. Both are lexical: گوهر
   gōhar > gohar keeps g, and درویش daryōš > darwēš keeps ē/ō. Class **(d)**:
   the ancestor is the right lexeme but the word's history is not the regular
   one.
2. **آب āb** /ˈʔaːb/ ← the nearest reading is MP `ap`, which fires no law; the
   PIE path `h₂ep → ap` lacks *p > b and the initial glottal. The miss is
   upstream (the Pehlevi reading does not contain the *b), class **(e)/(u)**;
   `pal__fa` cannot fix it.
3. **بخش baxš** /ˈbaxʃ/ ← PIE bʰeh₂g → bāg. The pal ancestor is not recorded;
   the word needs the *-g > -xš and *ā > a changes of earlier stages. Class
   **(u)**: another transition owns it.

### 5.5 A labialisation fold for /xʷ/ is right but currently inert

The dictionaries write خو- as **/xʷ/** (خواب, خوش, خوردن, خواستن, خود … — 31
records). The laws write the two segments `xw`, and the guard has no
`xʷ → xw` fold, so a correctly derived `xwāb` cannot be compared with
`/ˈxʷaːb/`. Adding the fold and dropping `xw_to_x_initial` looks like the fix,
and it is not: measured, both together gain **0** and lose **0**, because every
one of those words takes its ancestor from the *Pahlavi script* (خواب ← 𐭧𐭥𐭠𐭡),
so no law starts at all. Adding the fold alone also measures 391 → 391. It is
therefore not shipped — an inert convention in the guard would only widen the
comparison without evidence — and it is recorded here as the exact follow-up
for the day the Pahlavi reading table covers those 295 rows: then
`xʷ → xw` plus dropping `xw_to_x_initial` should be re-measured together.
`xw_to_x_initial` itself carries nothing in this corpus today (§7, ablations).

## 6 · Bugs found outside my write scope (exact patches, not applied)

### 6.1 `_identity_hit` compares the dictionary's romanisation literally

`src/pie/service.py` / `tools/coverage.py`: a zero-step derivation whose
spelling is the headword is not counted when `entry["translit"]` writes the long
vowels `â ê î ô û` where the laws write `ā ē ī ō ū`. **25 words** (تار، باز،
راست×2، هزار، پادزهر، ناز، کمان، یزدان، بامداد×2، آفتاب، بار×3، پای، …) are
lost to that alone. Minimal patch in `tools/coverage.py`:

```python
_NOTE = str.maketrans({"â": "ā", "ê": "ē", "î": "ī", "ô": "ō", "û": "ū",
                       "Â": "Ā", "Ê": "Ē", "Î": "Ī", "Ô": "Ō", "Û": "Ū"})

def _identity_hit(outputs, target, entry):
    record = (entry.get("translit") or "").translate(_NOTE)
    for output, steps, stage in outputs:
        if steps:
            continue
        heard = output.translate(_NOTE)
        if output == target or stress_only(output, target) or (
                record and (heard == record or stress_only(heard, record))):
            return output, stage
    return None
```

Measured: +25 words in the `identity` column, none lost (the fold is a
notation fold, not a target bend; `src/pie/service.py` uses the same comparison
for the word page and should get the same fold).

### 6.2 `_bound_pair` knows only the ASCII hyphen

Persian bound headwords are written with the **tatweel** U+0640 (ـی، ـتر، ـین،
ـدیس، مـ، ـه). `_bound_pair` tests `"-" in target`, so **35 words** never reach
the bound-form column although the derivation is their letters exactly.
Patch:

```python
def _bound_pair(output: str, target: str) -> bool:
    marks = ("-", "\u0640")                     # hyphen and tatweel
    if not any(m in target for m in marks):
        return False
    if any(m in output for m in marks):
        return False
    clean = lambda s: s.replace("-", "").replace("\u0640", "")
    return exact_kind(clean(output), clean(target)) is not None
```

### 6.3 The web test hard-coded `chu` as a missing transition — resolved

`tests/test_web.py::test_incomplete_chains_are_reported_not_faked` asserted
`"chu" in gaps`; when the Old Church Slavonic rules landed the assertion went
red on the shared tree. It was not this work's, and its owner has now fixed it —
`unittest discover` is green at 560 tests in the state I leave. Kept here only
so the reviewer does not read the 551/550/1 figure of an earlier draft as
current.

### 6.4 `_identity_hit` also refuses an unwritten anaptyctic vowel

`ابر` has the reading `abar` and the record `abr`; the spelling is the same and
no law fired. 11 words are in that state. Unlike 6.1 this one cannot be fixed by
a notation fold alone: deleting short vowels from both sides would also make the
consonantal reading `drwd` "equal" to `durūd`, which is exactly the kind of
identity the layer must refuse. It needs a distinction between a *phonemic*
short vowel and a *transliteration* with no vowels, which the entry does not
currently carry. Reported, not patched.

### 6.5 Not a bug, but a boundary worth a decision: the `steps > 0` gate

`tools/coverage.py` offers a form to the orthographic layer and to the script
layer only when `d.steps` is non-empty — "an unchanged ancestor is not evidence
that the rules explain the attested form" (the comment is deliberate, and the
`identity` column exists for exactly that case). The consequence is that a word
whose nearest reading *is already* its New Persian phonemic form is invisible to
the writing conventions: نām → نام, nān → نان, rang → رنگ, mādar → مادر,
āzād → آزاد, yazdān → یزدان, frahang → فرهنگ … `zerostep.py` measures that set
with the same spelling layer and the same guard the counter uses:

```
PYTHONPATH=src python3 proposals/2026-09-11-b/fa2b/zerostep.py fa
   would be spelled by the orthographic layer : 129
   would be read through its own script      : 34
   identical form, no layer claims it        : 0
```

So **129 words** would move into `orthographic` (and 34 into the script column)
if the gate were lifted for those columns alone. I did **not** treat that as a bug and did **not** touch the tool:
the gate protects the meaning of `exact`, and moving a word into `orthographic`
is a claim that the *writing conventions* explain it — true for all 129, but it
would raise `explained` by a third in one stroke and make the Persian figure
incomparable with every other language's. It is a policy decision for the project,
with one number attached: 129, and a `--zero-step-orthography` flag would be the
honest way to publish it (counted, never added to `exact`). My own laws avoid
the question rather than answer it by accident: `final_long_ag_to_a` fires on
dānāg, so دانا is counted through the script layer, not through the gate.

## 7 · Candidates measured and rejected

All on the whole language, layers `exact,orthographic,script`; council verdict
in the last column where it was run.

| candidate | gain | loss | verdict |
|---|---:|---:|---|
| `*-ōg/-ūg > -ū` (both vowels) | 10 | 1 (سوگ) | REJECT (council) |
| `final -āy > -ā` | 3 | 2 (سرای، پای) | REJECT, and it is morphology |
| `initial y- > j-` | 8 | 0 | REJECT: the same environment keeps y in یاد، یوغ، یوز; the gains are script-only |
| `initial gy- > j-` | 1 (جانور) | 0 | not shipped: one witness in the corpus (the change is real; keep for when Middle Persian grows) |
| `intervocalic b > v` | 4 | 9 | REJECT |
| `final -st > -s` | 3 | 9 | REJECT |
| `-sp- > -sf-` | 1 | 4 | REJECT |
| narrower `w- > b-` (by following vowel) | 1–6 | 1–18 | REJECT: the split is lexical (واش keeps w, باد does not) |
| `xʷ → xw` guard fold (+ dropping `xw_to_x_initial`) | 0 | 0 | not shipped: every witness starts at a Pahlavi-script ancestor (§5.5) |
| `xʷ → xw` guard fold alone | 0 | 0 | not shipped, inert |

**Shipped during this batch** (for contrast, same measurement): `final_ug_to_u` +5 / −0;
`final_long_ag_to_a` +3 / −0; the four guard folds +10 / −0.

Ablations of the existing laws, for the record: dropping `final_ag_to_e` costs
40 and gains 2; `w_to_b_initial` costs 14 and gains 6; `long_o_to_long_u` costs
24; `i_to_e` 15; `long_e_to_long_i` 14; `u_to_o` 13; `final_ig_to_i` 7;
`a_to_o_after_w` 2; `v_to_b_initial` 1; `final_ug_to_u` 3 (بانو، نوش‌دارو، هندو — the council
counter merges the duplicate records); `final_long_ag_to_a` 1 (دانا);
`xw_to_x_initial` carries nothing in this corpus (a rule that fires nowhere the
counter can see — kept, because the Wörterbuch reading of خواب and خوش is /xʷ/
and the law is what will have to be re-measured when the Pahlavi ancestors of
§5.5 gain readings; §5.5 shows the two must be changed together).

## 8 · What I would do next

1. Land 6.1 and 6.2 (25 + 35 words; both are notation, neither touches a
   published historical number).
2. Ask for a ruling on §6.5: 129 words are one flag away, and the flag
   is a policy decision, not a fix.
3. Give `final_ag_to_e` a stem-class guard via the paradigm layer (W5): the
   suffix *-ag vs a stem-final *g, so رگ/سگ stop being mis-derived without a
   per-word exception.
4. When the Middle Persian reading table covers the remaining 295 `pal` rows,
   re-run §5.1, §5.2 and §5.5: the *-ōg class, the -āy class and the /xʷ/ fold
   can then be measured against real MP spellings instead of homographic
   readings.

## 9 · Files

| file | state | what |
|---|---|---|
| `data/rules/pal__fa.yaml` | modified | `final_ug_to_u` (order 14), `final_long_ag_to_a` (order 12.5) |
| `data/spelling/fa.yaml` | modified | `guard.equivalences` (long vowels, short vowels dropped, `y: j`, `ŋ: n`) |
| `tests/test_batch_fa.py` | new | 15 tests over the two laws and the guard |
| `proposals/2026-09-11-b/fa2b/report.md` | new | this report |
| `proposals/2026-09-11-b/fa2b/audit.py` | new | writes `misses.tsv` |
| `proposals/2026-09-11-b/fa2b/classify.py` | new | writes `classified.tsv`, prints the tables |
| `proposals/2026-09-11-b/fa2b/diffgroup.py` | new | groups the misses by the shape of the difference |
| `proposals/2026-09-11-b/fa2b/zerostep.py` | new | measures what the `steps > 0` gate hides |
| `proposals/2026-09-11-b/fa2b/guard_probe.py` | new | the guard's before/after on the whole layer |
| `proposals/2026-09-11-b/fa2b/explained_set.py` | new | the explained set, for attribution by diffing |
| `proposals/2026-09-11-b/fa2b/cand/*.yaml` | new | every candidate law measured, shipped and rejected |
| `proposals/2026-09-11-b/fa2b/misses.tsv`, `classified.tsv` | new | the audit's output (1,301 rows) |

Nothing outside those files was written. `data/script/fa.yaml` is in my scope
and is unchanged: the script layer needed nothing during this batch (the two *-g laws are
seen through it, not by it).
