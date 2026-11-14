# The "one accent, two spellings" rule, audited

**Artefact.** `tools/coverage.py::exact_kind` (commit `ec90860`), the rule that
turned `exact` 3,640 → 4,547 by accepting a derived form whose only difference
from the record is how stress is written.
**Status.** audited; **verdict: guard** (keep the rule, narrow it). §8 records a
partial guard that appeared in the working tree while the audit ran.
**Author.** 2026-11-09. Audited commit `ec90860`; the branch moved
on while the probe ran (`af9433e`, `08b35ce`, other sessions' work), and
`exact_kind`, `_same_form` and `_comparison_key` are unchanged in every commit
through `08b35ce` (`exact_kind`, `_same_form` and `tokenize` are identical
between the two commits; the working tree now carries an in-progress guard,
§8). The full run was
repeated on `08b35ce` with the same totals. No write outside this proposal and
`proposals/2026-09-11/notation_probe.py`.
**Reproduce.**

```bash
PYTHONPATH=src python3 proposals/2026-09-11/notation_probe.py            # all 35 languages
PYTHONPATH=src python3 proposals/2026-09-11/notation_probe.py --langs ira-pro iir-pro
PYTHONPATH=src python3 proposals/2026-09-11/notation_probe.py --json /tmp/notation_pairs.json
PYTHONPATH=src python3 proposals/2026-09-11/notation_probe.py --guard   # the proposed guard's effect
```

The probe replicates `tools/coverage.py::measure`'s matching loop line for line
(same `ancestor_starts`, same "at least one law must fire", first matching
ancestor wins, same sampling), so its strict and notation totals are the
published ones: **strict 3,625 + notation 922 = 4,547**, over 35 languages with
a glossary. Every one of the 922 pairs below is from that run, not a sample.

## 1 · What the rule actually compares

`exact_kind(output, target)` is two lines: raw equality → `strict`, else
`service._same_form` → `notation`. So the rule's real content is `_same_form`,
and `_same_form` is far wider than its name:

| step | code | what it erases |
|---|---|---|
| `phonology.tokenize` | `strip_form()` line 67 | `* [ ] { } ( ) / < >` |
| `phonology.tokenize` | `.split()` line 74 | whitespace (two-word lemmas become one word) |
| `phonology.tokenize` | `chunk.replace("-", "")` line 75 | every hyphen, i.e. the morpheme/word boundary |
| `phonology.tokenize` | `ALIASES` line 59 | `þ→θ đ→ð γ→ɣ ƀ→β ʋ→w` — letters |
| `tokenize`/`_split_acute` | line 113 | an acute on a vowel becomes `ˈ` before it — **this part is the rule** |
| `service._comparison_key` | line 673 | standalone `ʰ` → `h` |
| `service._comparison_key` | line 675 | breve `̆` dropped (Wiktionary short-vowel mark) |
| `service._same_form` | line 737 | `ˈ`/`ˌ` stripped from **both** sides when only one side marks stress — position is then not checked |

The first five are older than this commit and are right for the word page (a
link that carries `-mā` must find `mā`). They are not right for a counter that
says *character for character*. `exact_kind` (coverage line 211–212) adopts all
of them under the label "notation".

## 2 · Counts

The 922 pairs split three ways. "Stress-position" means both sides state the
accent and it sits on the same nucleus; "one side silent" means one side writes
no accent at all, so nothing can disagree; "other chars" means something other
than a stress mark differs.

| language | tested | strict | notation | stress-position | one side silent | other chars |
|---|---:|---:|---:|---:|---:|---:|
| `gem-pro` | 2,880 | 8 | 79 | 0 | 63 | 16 |
| `gmw-pro` | 3,544 | 567 | 103 | 0 | 1 | 102 |
| `ang` | 6,033 | 550 | 97 | 0 | 10 | 87 |
| `enm` | 4,687 | 382 | 20 | 0 | 3 | 17 |
| `en` | 37,514 | 607 | 29 | 0 | 3 | 26 |
| `goh` | 1,481 | 151 | 3 | 0 | 1 | 2 |
| `gmh` | 471 | 80 | 1 | 0 | 1 | 0 |
| `de` | 8,077 | 192 | 9 | 0 | 0 | 9 |
| `la` | 3,205 | 3 | 4 | 0 | 4 | 0 |
| `it` | 10,661 | 1,057 | 61 | 0 | 4 | 57 |
| `iir-pro` | 522 | 1 | 186 | 144 | 8 | 34 |
| `ira-pro` | 338 | 7 | 199 | 186 | 2 | 11 |
| `pal` | 61 | 1 | 0 | 0 | 0 | 0 |
| `cel-pro` | 1,015 | 15 | 96 | 0 | 87 | 9 |
| `ine-bsl-pro` | 344 | 4 | 35 | 27 | 6 | 2 |
| **total (15 languages with any match; 35 tested, 108,758 tested entries, 264,489 glossary entries)** | 108,758 | **3,625** | **922** | **357** | **193** | **372** |

- **367 pairs have a mark on both sides, and all 367 put it on the same
  nucleus.** Zero exceptions. This is the rule doing exactly what it says.
- Of the 193 one-sided pairs, **183 have the engine marking stress and the
  record silent** (Wiktionary prints no accent for Proto-Germanic, Proto-Celtic,
  most Old English): the record makes no claim, so no comparison is possible
  and accepting it is defensible — but see §4, where some of those engine
  accents are demonstrably wrong for the stage.
- **10 have the record marking stress and the engine silent** — the reverse,
  and not defensible in the same way: the model is not saying "stress is
  unknown", it is not saying anything. One of them is a different lexeme:
  **`it` `sé` ← `se`** (the stressed pronoun vs the clitic; Latin `sē` gives
  `se`, the record is `sé`). The others are segmentally right but unaccented
  because the chain starts from an unaccented PIE etymon:
  `iir-pro` `naHwíyas`, `Habʰí`, `Háćru`, `mr̥dúš`, `dušmánās`, `Hsumánās`;
  `ira-pro` `draHǰáh`, `dušmánāh`; `ine-bsl-pro` `dwínas`.

### Genuine pairs (examples; the per-language split is in §2)

| language | recorded | derived | characters that differ |
|---|---|---|---|
| `iir-pro` | `ná` | `nˈa` | `−́ +ˈ` |
| `iir-pro` | `ćatám` | `ćatˈam` | `−́ +ˈ` |
| `ira-pro` | `waydáyati` | `waydˈayati` | `−́ +ˈ` |
| `ira-pro` | `cánhati` | `cˈanhati` | `−́ +ˈ` |
| `ine-bsl-pro` | `źámbas` | `źˈambas` | `−́ +ˈ` |
| `ine-bsl-pro` | `deiwás` | `deiwˈas` | `−́ +ˈ` |
| `iir-pro` | `wŕ̥kas` | `wˈr̥kas` | `−́ +ˈ` (acute after the ring, on a syllabic sonorant) |
| `ira-pro` | `Hnā́ma` | `Hnˈāma` | `−́ +ˈ` (acute written after the macron) |
| `gem-pro` | `in` | `ˈin` | `+ˈ` (record silent) |
| `cel-pro` | `genus` | `gˈenus` | `+ˈ` (record silent) |

The rule is real and it is large: 357 pairs are one word written with two
spellings of one accent, plus 183 where the dictionary writes no accent (168 of
those differ in nothing but the accent; 15 also carry a hyphen or bracket and
are listed again in §3).

## 3 · The 397 pairs that are not stress at all

**362 of the 922 pairs (39%) have no accent on either side.** Every pair that
differs by something other than a stress mark is in one of these classes; there
are 397 such pairs, and 35 of them also differ in stress (e.g. `þat` → `θˈat`):

| class | pairs | example | what the difference is |
|---|---:|---|---|
| hyphen | 238 | `gem-pro` `un-` → `un`; `ira-pro` `ha-` → `ha`; `it` `-a` → `a` | a morphological boundary, not a sound |
| þ / θ | 152 | `gem-pro` `-þrą` → `θrą`; `ang` `þing` → `θing` | a *letter*: Wiktionary's `þ` vs the engine's `θ` |
| brackets | 5 | `iir-pro` `(H)íšuš` → `Hˈišuš` | an optional segment: the record says *maybe* h₁, the engine asserts it |
| breve | 3 | `it` `insensibile` → `insensibĭle` | Wiktionary's short-vowel mark |
| space | 2 | `gmw-pro` `fimf tigiwi` → `fimftigiwi` | a two-word lemma counted as one word |

(Hyphen and thorn overlap in 3 pairs; the table sums to 397 with that overlap.)

The hyphen class is the serious one. It covers **200 distinct headwords, 305
entries**: 208 suffixes, 65 prefixes, 19 roots and 13 other entries whose
headword carries a dash. `coverage.py` counts entries, and `exact` is now 305 entries
richer for no phonological reason whatever — the laws never produce a hyphen.
If a morpheme count is wanted it belongs in its own column, like the
orthographic and script layers.

**The line to change.** `exact_kind` gets its looseness from
`_comparison_key` → `tokenize`, and from `_same_form`'s one-sided branch:

- `src/pie/phonology.py:75` `chunk = chunk.replace("-", "")` — this single line
  is the whole hyphen class;
- `src/pie/phonology.py:67` `re.sub(r"[\[\]{}()/<>]", "", text)` — the bracket
  class;
- `src/pie/phonology.py:74` `.split()` — the space class;
- `src/pie/phonology.py:59` `ALIASES` — the thorn class (a *letter*);
- `src/pie/service.py:673/675` — `ʰ→h` and breve;
- `src/pie/service.py:737` — strips `ˈ`/`ˌ` position-blind when only one side
  marks stress (not the source of §3, but the source of §5 and §6);
- `tools/coverage.py:211–212` — the label: everything `_same_form` accepts is
  called "notation".

None of these needs to change for the word page. `coverage.py` needs its own
predicate.

## 4 · Record-silent matches: what the stage can still check

The record makes no claim about stress, but some stages do. The engine has no
stress-assignment law (`grep stress data/rules/ine-pro__gem-pro.yaml` finds only
Verner's environments), so a derived form keeps the PIE etymon's accent — which
for Proto-Germanic, Old English and Old High German is the wrong syllable:

| stage | stress of the stage | record-silent pairs | engine accent elsewhere | examples |
|---|---|---:|---:|---|
| `gem-pro` | initial (fixed) | 63 | 10 | `ubˈer`, `fadˈēr`, `duhtˈēr`, `kurnˈą` |
| `ang` | initial (fixed) | 10 | 2 | `idˈes`, `fædˈer` |
| `goh` | initial (fixed) | 1 | 1 | `fatˈer` |
| `cel-pro` | initial in the handbooks (`matasovic-2009`, `mccone-1996`) | 87 | 36 | `entˈer`, `segˈos`, `somˈos`, `rotˈos` |
| `iir-pro`, `ira-pro`, `ine-bsl-pro` | mobile / inherited accent | 15 | not checkable | — |

The first three are facts about the attested stage, so those 13 derived accents
are knowably wrong while the counter calls the word exact. Proto-Celtic's
initial stress is the handbooks' reconstruction, not a recorded fact, so that
row is a hypothesis — but 36 of 87 is too many to leave unmentioned. The
Indo-Iranian and Balto-Slavic stages have mobile accent; nothing is claimed
there, and the record's silence is all there is.

This is a modelling gap, not a counting bug — but the column must not be read
as "the accent was verified". It was not verified; it was not even asked.

## 5 · Boundary cases, one by one

Run with `service._same_form` / `coverage.exact_kind` directly:

| case | call | result | defensible? |
|---|---|---|---|
| acute on the vowel vs `ˈ` before it | `waydˈayati`, `waydáyati` | `notation` (keys equal) | yes — the rule |
| both marked, different syllables | `wˈaydayati`, `waydáyati` | `None` | yes — position checked |
| record acute, engine stress on another vowel | `waydˈayati`, `wáydayati` | `None` | yes |
| primary vs secondary on the same word | `waydaˌyati`, `waydáyati` | `None` | conservative, fine |
| engine `ˌ` only, record unmarked | `waydaˌyati`, `waydayati` | `notation` | arguable: a secondary stress satisfies "stress is stated" |
| stress token on a glide, record acute elsewhere | `ˈyā`, `yā́` | `None` | yes (`y` is a vowel letter to the tokenizer, so positions differ) |
| stress token on a glide, record silent | `ˈyā`, `yā` | `notation` | **no**: an accent on a non-nucleus glides through when the record is silent. 0 occurrences in the corpus |
| stress on a syllabic sonorant | `ˈr̥`, `ŕ̥` | `notation` | yes |
| acute written after the macron | `ˈā`, `a◌̄◌́` | `notation` | yes |
| acute written before the macron | `ˈā`, `a◌́◌̄` | `notation` | yes (NFD) |
| macron differs | `nˈām`, `nˈam` | `None` | yes |
| case differs | `Wˈarkah`, `wˈarkah` | `None` | yes |
| hyphen only, no stress anywhere | `un`, `un-` | `notation` | **no** |
| brackets only | `Hˈišuš`, `(H)íšuš` | `notation` | **no** (optional segment) |
| space only | `fimftigiwi`, `fimf tigiwi` | `notation` | **no** (phrase) |
| thorn vs theta | `θrą`, `-þrą` | `notation` | not stress; a spelling convention |
| breve dropped | `insensibile`, `insensibĭle` | `notation` | not stress; a dictionary mark |
| `ʰ` vs `h` | `wˈr̥kah`, `wˈr̥kaʰ` | `notation` | not stress; old lemma convention, 0 occurrences here |
| grave vs acute | `waydˈayati`, `waydàyati` | `None` | **too narrow**: a grave is the same accent. Today 0 pairs are lost by this; recognizing it would add 7 Italian words (`virtù, carità, sanità, rarità, vivacità, vicinità, patavinità`) and must still reject `kapò` (`kˈapo`: the engine puts the stress on the first syllable) |

So: the rule is a **one-acute** rule, not a "one accent" rule. It checks stress
position correctly whenever both sides state it, and it does not check it at
all when one side is silent.

## 6 · Effect on `tools/whatif.py`

`whatif.exact_words` uses the same `_same_form` (line 57), so every one of the
922 pairs is in its baseline, including the 397. Measured consequences:

1. **The rule is needed.** `--to ira-pro --drop final_s_to_h` loses 101 words;
   93 are pure stress spelling, 5 are strict, 2 record-silent, 1 an affix.
   Under raw string equality the same law would have looked like it carried 5
   words, and the proposer would have discarded a law that carries 93 correct
   outcomes. This is the strongest argument for the change.
2. **The gate and the published number are two different measurements.**
   `whatif --to ira-pro` reports 200 "exact" where coverage reports 206:
   `exact_words` keys its result by the word (7 duplicated spellings collapse)
   and it imports `service.ancestor_starts`, while coverage has its own copy
   that cannot read a keyword ancestry row (`[':inh', 'iir-pro:*dʰúgdʰā>>',
   'root']`), so whatif counts `dúgdā` and coverage cannot. This is not a
   one-word quirk: **2,624 corpus entries** have at least one ancestor form
   that only `service.ancestor_starts` can see (Old Persian `𐎴𐎠𐎶` is
   "inherited" to coverage's `ancestry_kind` but has no candidate to derive
   from, so it leaves `tested` without a miss, for example). `identified`,
   `exact` and `whatif` all need the same function.
3. **A candidate law can look good only through notation.** The probe law
   `match: "ˈ", replace: ""` — a "law" that deletes the model's own stress and
   changes no segment — measures:

   | language | `whatif` (current) | raw equality (old) |
   |---|---|---|
   | `ira-pro` | **+35 / −0** | +0 / −0 |
   | `cel-pro` | **+23 / −0** | +98 / −0 |
   | `gem-pro` | +4 / −39 | +17 / −0 |

   In `ira-pro` the 35 are words that were already string-equal modulo the
   accent but that no real law touched; deleting the stress token is enough for
   a rule to "fire", and a stressless output then matches a marked record, so
   the fake law scores. In `cel-pro`, where the records never print stress,
   erasing the model's accent is rewarded outright. No real sound law should
   ever be able to score by removal of a marker, and the gate must not let one.

## 7 · Verdict and the minimal fix

**Keep the principle, guard the implementation.** The 367 both-marked pairs are
genuine and the gate needs them; the 397 non-stress pairs are not stress and
must not ride in on the same label; the 10 engine-silent pairs must not be
called notation; the hyphen class must leave `exact` altogether.

Numbers under a guard that accepts **only** a difference in stress marks (or a
record with no accent at all, as against an engine that marks one):

- `exact` 4,547 → **4,150** = 3,625 strict + 525 (357 position-verified + 168
  record-silent);
- the 10 engine-silent words (including `it` `sé`/`se`) move to their own
  column or out: **4,140**;
- the 397 leave for their own counters: 238 hyphen/morpheme, 149 thorn-only,
  5 optional-segment, 3 breve, 2 phrase.

Proposed predicate, next to `printable_form` (both `coverage.exact_kind` and
`whatif.exact_words` call it; nothing on the word page changes). It does **not**
go through `tokenize`, so nothing but an accent can be forgiven, and it compares
the accent's *nucleus* on the two sides. It is executable in the probe
(`stress_only`) and measured there on all 922 pairs: **525 kept, 397 dropped, 0
of the 357 position-verified pairs lost**:

```python
_VOWELS = set("aeiouyəɛɔæœøɨɤɯɪʊɐɑɒɵʌʉɘ")
_SONORANTS, _STRESS, _SYLLABIC = set("rlmn"), {"ˈ", "ˌ"}, {"\u0325", "\u0329"}


def stress_only(output: str, target: str) -> bool:
    """True when the two forms differ only in how (or whether) stress is written."""
    def profile(form: str) -> tuple[str, tuple[int, ...]]:
        text = unicodedata.normalize("NFD", form)
        segs: list[list[str]] = []                  # [base, *kept marks]
        stress: list[tuple[int, int | None]] = []   # (segment, acute sits here?)
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in _STRESS:                       # marks the next nucleus
                stress.append((len(segs), None))
            elif unicodedata.combining(ch) and segs:
                if ch == "\u0301":
                    stress.append((len(segs) - 1, 0))   # a stress acute
                else:
                    segs[-1].append(ch)             # ring, macron, ć's acute …
            else:
                segs.append([ch])
            i += 1
        skeleton = "".join("".join(seg) for seg in segs)
        ordinals: list[int | None] = []
        n = 0
        for seg in segs:
            base, marks = seg[0], "".join(seg[1:])
            if base in _VOWELS or (base in _SONORANTS and any(m in _SYLLABIC for m in marks)):
                ordinals.append(n)
                n += 1
            else:
                ordinals.append(None)
        positions = []
        for at, acute in stress:
            if acute is not None:
                if ordinals[at] is None:
                    return skeleton, (-1,)          # accent on a non-nucleus
                positions.append(ordinals[at])
                continue
            nxt = next((ordinals[j] for j in range(at, len(segs))
                        if ordinals[j] is not None), None)
            positions.append(-1 if nxt is None else nxt)
        return skeleton, tuple(positions)

    a, pa = profile(printable_form(output))
    b, pb = profile(target)
    if a != b:                       # a hyphen, space, breve, þ or letter differs
        return False
    if pa and pb:                    # both say where: it must be the same nucleus
        return pa == pb
    return bool(pa or pb)            # one side writes no accent at all

```
and `exact_kind` becomes

```python
    if output == target:
        return "strict"
    return "notation" if stress_only(output, target) else None
```

Tests to add to `tests/test_coverage.py`. The first four fail on `ec90860` and
pass after the guard; the last already passes and pins the boundary that must
not regress:

```python
    def test_a_hyphen_is_not_a_stress_mark(self):
        self.assertIsNone(coverage_tool.exact_kind("un", "un-"))

    def test_an_optional_segment_is_not_a_stress_mark(self):
        self.assertIsNone(coverage_tool.exact_kind("Hˈišuš", "(H)íšuš"))

    def test_a_phrase_is_not_a_word(self):
        self.assertIsNone(coverage_tool.exact_kind("fimftigiwi", "fimf tigiwi"))

    def test_thorn_and_theta_are_different_letters(self):
        self.assertIsNone(coverage_tool.exact_kind("θrą", "-þrą"))

    def test_a_wrong_stress_position_is_still_a_miss(self):
        self.assertIsNone(coverage_tool.exact_kind("waydˈayati", "wáydayati"))
```

Also required, and outside this audit's write scope:

1. `docs/DECISIONS.md` (2026-11-09): "Nothing else is forgiven: a macron, a
   length, a letter or a case still separates a form from the record" is false
   as shipped — a hyphen, a bracket, a space, a breve and the letter þ are all
   forgiven. Correct the entry and report `exact_stress` / `exact_unstressed`
   beside `exact_strict`.
2. `tools/whatif.py` must import the same predicate and the same
   `ancestor_starts` as coverage, and report strict/notation separately.
3. W3: stress-assignment laws for the fixed-stress stages (PGmc, OE, OHG, and
   Proto-Celtic if the handbooks' reconstruction is accepted) so the 13 clear
   non-initial engine accents above — 36 more by the Celtic hypothesis — stop
   being invisible.
4. W2: if þ/θ or the breve is to be counted, it is a spelling layer, like
   `data/spelling/*.yaml`, with its own number.

## 8 · Postscript: the guard that landed while this audit ran

At the time of writing, `tools/coverage.py` in the **working tree** (HEAD
`08b35ce`, uncommitted) already carries a guard of the same shape as §7's: it
rejects a hyphen mismatch, a whitespace mismatch, and requires
`_same_form(...) and _stress_free(output) == _stress_free(target)`. Its own
comment says "þ against θ … is a different claim and is left to the
orthographic layer", but `_stress_free` is `detokenize(tokenize(...))`, so it
inherits exactly the tokenizer the audit identifies: `þ→θ`, brackets deleted.
Measured on the 922 pairs: it keeps **679** (357 position-verified + 177
one-side-silent + 145 others) and drops 243. **149 thorn pairs and all 5
bracket pairs are still counted as "notation"** — `exact_kind("θˈat", "þat")`
and `exact_kind("Hˈišuš", "(H)íšuš")` both return `notation` — so `exact` under
that guard is 3,625 + 679 = **4,304**, not 4,150, and its comment describes a
stricter rule than its code. It does reject the breve and the phrase.

`stress_only` (§7) is the predicate that closes all three classes, and it
depends on nothing that erases a letter; it should replace `_stress_free` rather
than sit beside it.

## Appendix A — every pair whose difference is not (only) stress

`−` is what the record has and the derived form lacks, `+` the reverse. This is
the complete set — 400 rows for 397 pairs, because 3 pairs differ by both a
hyphen and a thorn and appear under both headings. The 525 stress-only pairs
are summarised in §2 and listed in full by `notation_probe.py --json`.


### Hyphen (238 pairs; 200 distinct headwords)

| language | recorded | derived | chars |
|---|---|---|---|
| `gem-pro` | `un-` | `un` | `−-` `+∅` |
| `gem-pro` | `twi-` | `twi` | `−-` `+∅` |
| `gem-pro` | `-aną` | `aną` | `−-` `+∅` |
| `gem-pro` | `fra-` | `fra` | `−-` `+∅` |
| `gem-pro` | `-þrą` | `θrą` | `−-þ` `+θ` |
| `gem-pro` | `bō-` | `bō` | `−-` `+∅` |
| `gem-pro` | `aba-` | `abˈa` | `−-` `+ˈ` |
| `gem-pro` | `swin-` | `swin` | `−-` `+∅` |
| `gem-pro` | `pamp-` | `pamp` | `−-` `+∅` |
| `gem-pro` | `skup-` | `skup` | `−-` `+∅` |
| `gem-pro` | `-slą` | `slą` | `−-` `+∅` |
| `gem-pro` | `-ō` | `ˈō` | `−-` `+ˈ` |
| `gem-pro` | `-ō` | `ō` | `−-` `+∅` |
| `gem-pro` | `-ō` | `ō` | `−-` `+∅` |
| `gem-pro` | `-snō` | `snō` | `−-` `+∅` |
| `gem-pro` | `-nē` | `nˈē` | `−-` `+ˈ` |
| `gem-pro` | `uba-` | `ubˈa` | `−-` `+ˈ` |
| `gem-pro` | `-ī` | `ī` | `−-` `+∅` |
| `gem-pro` | `-iwi` | `iwi` | `−-` `+∅` |
| `gem-pro` | `-ū` | `ū` | `−-` `+∅` |
| `gmw-pro` | `-ing` | `ing` | `−-` `+∅` |
| `gmw-pro` | `-ward` | `ward` | `−-` `+∅` |
| `gmw-pro` | `-sam` | `sam` | `−-` `+∅` |
| `gmw-pro` | `-ling` | `ling` | `−-` `+∅` |
| `gmw-pro` | `-r` | `r` | `−-` `+∅` |
| `gmw-pro` | `-g` | `g` | `−-` `+∅` |
| `gmw-pro` | `-il` | `il` | `−-` `+∅` |
| `gmw-pro` | `-il` | `il` | `−-` `+∅` |
| `gmw-pro` | `-il` | `il` | `−-` `+∅` |
| `gmw-pro` | `-gim` | `gim` | `−-` `+∅` |
| `gmw-pro` | `-skapi` | `skapi` | `−-` `+∅` |
| `gmw-pro` | `-ī` | `ī` | `−-` `+∅` |
| `gmw-pro` | `-īn` | `īn` | `−-` `+∅` |
| `gmw-pro` | `-dōm` | `dōm` | `−-` `+∅` |
| `gmw-pro` | `-līk` | `līk` | `−-` `+∅` |
| `gmw-pro` | `-haidu` | `haidu` | `−-` `+∅` |
| `gmw-pro` | `kuni-` | `kuni` | `−-` `+∅` |
| `gmw-pro` | `-þi` | `θi` | `−-þ` `+θ` |
| `gmw-pro` | `-iwi` | `iwi` | `−-` `+∅` |
| `gmw-pro` | `-iwi` | `iwi` | `−-` `+∅` |
| `gmw-pro` | `-ū` | `ū` | `−-` `+∅` |
| `ang` | `un-` | `un` | `−-` `+∅` |
| `ang` | `-ian` | `ian` | `−-` `+∅` |
| `ang` | `-ing` | `ing` | `−-` `+∅` |
| `ang` | `-a` | `a` | `−-` `+∅` |
| `ang` | `-a` | `a` | `−-` `+∅` |
| `ang` | `-an` | `an` | `−-` `+∅` |
| `ang` | `-u` | `u` | `−-` `+∅` |
| `ang` | `-ung` | `ung` | `−-` `+∅` |
| `ang` | `-ol` | `ol` | `−-` `+∅` |
| `ang` | `wan-` | `wan` | `−-` `+∅` |
| `ang` | `be-` | `be` | `−-` `+∅` |
| `ang` | `-end` | `end` | `−-` `+∅` |
| `ang` | `sam-` | `sam` | `−-` `+∅` |
| `ang` | `and-` | `and` | `−-` `+∅` |
| `ang` | `-weard` | `weard` | `−-` `+∅` |
| `ang` | `ut-` | `ˈut` | `−-` `+ˈ` |
| `ang` | `æt-` | `æt` | `−-` `+∅` |
| `ang` | `-uma` | `uma` | `−-` `+∅` |
| `ang` | `-lian` | `lian` | `−-` `+∅` |
| `ang` | `ymb-` | `ymb` | `−-` `+∅` |
| `ang` | `ang-` | `ang` | `−-` `+∅` |
| `ang` | `hund-` | `hund` | `−-` `+∅` |
| `ang` | `-ga` | `ga` | `−-` `+∅` |
| `ang` | `bile-` | `bile` | `−-` `+∅` |
| `ang` | `-heort` | `heort` | `−-` `+∅` |
| `ang` | `-weorþ` | `weorθ` | `−-þ` `+θ` |
| `ang` | `æl-` | `æl` | `−-` `+∅` |
| `ang` | `-gian` | `gian` | `−-` `+∅` |
| `enm` | `-ed` | `ed` | `−-` `+∅` |
| `enm` | `-en` | `en` | `−-` `+∅` |
| `enm` | `-en` | `en` | `−-` `+∅` |
| `enm` | `-en` | `en` | `−-` `+∅` |
| `enm` | `-en` | `en` | `−-` `+∅` |
| `enm` | `-e` | `e` | `−-` `+∅` |
| `enm` | `-e` | `e` | `−-` `+∅` |
| `enm` | `-re` | `re` | `−-` `+∅` |
| `enm` | `-ene` | `ene` | `−-` `+∅` |
| `enm` | `-el` | `el` | `−-` `+∅` |
| `enm` | `-es` | `es` | `−-` `+∅` |
| `enm` | `-es` | `es` | `−-` `+∅` |
| `enm` | `-eren` | `eren` | `−-` `+∅` |
| `enm` | `and-` | `and` | `−-` `+∅` |
| `enm` | `kine-` | `kine` | `−-` `+∅` |
| `enm` | `-len` | `len` | `−-` `+∅` |
| `en` | `in-` | `ˈin` | `−-` `+ˈ` |
| `en` | `in-` | `in` | `−-` `+∅` |
| `en` | `-er` | `er` | `−-` `+∅` |
| `en` | `-er` | `er` | `−-` `+∅` |
| `en` | `-er` | `er` | `−-` `+∅` |
| `en` | `-ing` | `ing` | `−-` `+∅` |
| `en` | `-ing` | `ing` | `−-` `+∅` |
| `en` | `-ing` | `ing` | `−-` `+∅` |
| `en` | `-ess` | `ess` | `−-` `+∅` |
| `en` | `-ed` | `ed` | `−-` `+∅` |
| `en` | `-ed` | `ed` | `−-` `+∅` |
| `en` | `-ed` | `ed` | `−-` `+∅` |
| `en` | `-th` | `th` | `−-` `+∅` |
| `en` | `-th` | `th` | `−-` `+∅` |
| `en` | `-en` | `en` | `−-` `+∅` |
| `en` | `-en` | `en` | `−-` `+∅` |
| `en` | `-en` | `en` | `−-` `+∅` |
| `en` | `-en` | `en` | `−-` `+∅` |
| `en` | `-en` | `en` | `−-` `+∅` |
| `en` | `-t` | `t` | `−-` `+∅` |
| `en` | `-ling` | `ling` | `−-` `+∅` |
| `en` | `-es` | `es` | `−-` `+∅` |
| `en` | `-kind` | `kind` | `−-` `+∅` |
| `en` | `-k` | `k` | `−-` `+∅` |
| `en` | `-ern` | `ern` | `−-` `+∅` |
| `en` | `-red` | `red` | `−-` `+∅` |
| `en` | `mer-` | `mer` | `−-` `+∅` |
| `goh` | `un-` | `un` | `−-` `+∅` |
| `goh` | `hadu-` | `hadu` | `−-` `+∅` |
| `de` | `un-` | `un` | `−-` `+∅` |
| `de` | `in-` | `in` | `−-` `+∅` |
| `de` | `ge-` | `ge` | `−-` `+∅` |
| `de` | `wider-` | `wider` | `−-` `+∅` |
| `de` | `-haft` | `haft` | `−-` `+∅` |
| `de` | `-wert` | `wert` | `−-` `+∅` |
| `de` | `ober-` | `ober` | `−-` `+∅` |
| `de` | `-falt` | `falt` | `−-` `+∅` |
| `de` | `-heim` | `heim` | `−-` `+∅` |
| `it` | `semi-` | `semi` | `−-` `+∅` |
| `it` | `de-` | `de` | `−-` `+∅` |
| `it` | `-io` | `io` | `−-` `+∅` |
| `it` | `-cida` | `cida` | `−-` `+∅` |
| `it` | `-cida` | `cida` | `−-` `+∅` |
| `it` | `-a` | `ˈa` | `−-` `+ˈ` |
| `it` | `-a` | `a` | `−-` `+∅` |
| `it` | `-a` | `a` | `−-` `+∅` |
| `it` | `-a` | `a` | `−-` `+∅` |
| `it` | `-a` | `a` | `−-` `+∅` |
| `it` | `intra-` | `intra` | `−-` `+∅` |
| `it` | `-oso` | `oso` | `−-` `+∅` |
| `it` | `-o` | `o` | `−-` `+∅` |
| `it` | `-o` | `o` | `−-` `+∅` |
| `it` | `-i` | `i` | `−-` `+∅` |
| `it` | `-are` | `are` | `−-` `+∅` |
| `it` | `-ico` | `ico` | `−-` `+∅` |
| `it` | `-ico` | `ico` | `−-` `+∅` |
| `it` | `-ide` | `ide` | `−-` `+∅` |
| `it` | `-ide` | `ide` | `−-` `+∅` |
| `it` | `-ate` | `ate` | `−-` `+∅` |
| `it` | `stibio-` | `stibio` | `−-` `+∅` |
| `it` | `-astro` | `astro` | `−-` `+∅` |
| `it` | `-astro` | `astro` | `−-` `+∅` |
| `it` | `-ile` | `ile` | `−-` `+∅` |
| `it` | `-ino` | `ino` | `−-` `+∅` |
| `it` | `-ino` | `ino` | `−-` `+∅` |
| `it` | `-ito` | `ito` | `−-` `+∅` |
| `it` | `-ando` | `ando` | `−-` `+∅` |
| `it` | `-ando` | `ando` | `−-` `+∅` |
| `it` | `-ismo` | `ismo` | `−-` `+∅` |
| `it` | `-ura` | `ura` | `−-` `+∅` |
| `it` | `-ano` | `ano` | `−-` `+∅` |
| `it` | `-aste` | `aste` | `−-` `+∅` |
| `it` | `-asti` | `asti` | `−-` `+∅` |
| `it` | `-ato` | `ato` | `−-` `+∅` |
| `it` | `-ato` | `ato` | `−-` `+∅` |
| `it` | `-ato` | `ato` | `−-` `+∅` |
| `it` | `-ato` | `ato` | `−-` `+∅` |
| `it` | `-ato` | `ato` | `−-` `+∅` |
| `it` | `-uto` | `uto` | `−-` `+∅` |
| `it` | `-ola` | `ola` | `−-` `+∅` |
| `it` | `-eta` | `eta` | `−-` `+∅` |
| `it` | `-olo` | `olo` | `−-` `+∅` |
| `it` | `-eto` | `eto` | `−-` `+∅` |
| `it` | `sopra-` | `sopra` | `−-` `+∅` |
| `it` | `-ale` | `ale` | `−-` `+∅` |
| `it` | `-tura` | `tura` | `−-` `+∅` |
| `it` | `-esimo` | `esimo` | `−-` `+∅` |
| `it` | `-cidio` | `cidio` | `−-` `+∅` |
| `it` | `-torio` | `torio` | `−-` `+∅` |
| `it` | `-atico` | `atico` | `−-` `+∅` |
| `it` | `-tico` | `tico` | `−-` `+∅` |
| `it` | `-ucolo` | `ucolo` | `−-` `+∅` |
| `it` | `-otico` | `otico` | `−-` `+∅` |
| `iir-pro` | `a-` | `a` | `−-` `+∅` |
| `iir-pro` | `pra-` | `pra` | `−-` `+∅` |
| `iir-pro` | `-kas` | `kas` | `−-` `+∅` |
| `iir-pro` | `sam-` | `sam` | `−-` `+∅` |
| `iir-pro` | `ati-` | `ˈati` | `−-` `+ˈ` |
| `iir-pro` | `-ám` | `ˈam` | `−-́` `+ˈ` |
| `iir-pro` | `Há-` | `Hˈa` | `−́-` `+ˈ` |
| `iir-pro` | `wayd-` | `wayd` | `−-` `+∅` |
| `iir-pro` | `Had-` | `Had` | `−-` `+∅` |
| `iir-pro` | `Has-` | `Has` | `−-` `+∅` |
| `iir-pro` | `dʰar-` | `dʰar` | `−-` `+∅` |
| `iir-pro` | `Hsu-` | `Hsu` | `−-` `+∅` |
| `iir-pro` | `swap-` | `swap` | `−-` `+∅` |
| `iir-pro` | `waȷ́ʰ-` | `waȷ́ʰ` | `−-` `+∅` |
| `iir-pro` | `yawg-` | `yawg` | `−-` `+∅` |
| `iir-pro` | `warš-` | `warš` | `−-` `+∅` |
| `iir-pro` | `sarȷ́-` | `sarȷ́` | `−-` `+∅` |
| `iir-pro` | `-nás` | `nˈas` | `−-́` `+ˈ` |
| `iir-pro` | `duš-` | `duš` | `−-` `+∅` |
| `iir-pro` | `daH-` | `daH` | `−-` `+∅` |
| `iir-pro` | `bʰaH-` | `bʰaH` | `−-` `+∅` |
| `iir-pro` | `Hwas-` | `Hwas` | `−-` `+∅` |
| `iir-pro` | `smar-` | `smar` | `−-` `+∅` |
| `iir-pro` | `-tamas` | `tamas` | `−-` `+∅` |
| `iir-pro` | `-tás` | `tˈas` | `−-́` `+ˈ` |
| `iir-pro` | `-ištHas` | `ištHas` | `−-` `+∅` |
| `iir-pro` | `rać-` | `rać` | `−-` `+∅` |
| `iir-pro` | `Hyawdʰ-` | `Hyawdʰ` | `−-` `+∅` |
| `iir-pro` | `-yās` | `yās` | `−-` `+∅` |
| `iir-pro` | `upa-` | `upa` | `−-` `+∅` |
| `iir-pro` | `-wants` | `wˈants` | `−-` `+ˈ` |
| `iir-pro` | `garȷ́ʰ-` | `garȷ́ʰ` | `−-` `+∅` |
| `iir-pro` | `yaw-` | `yaw` | `−-` `+∅` |
| `iir-pro` | `ȷ́ʰwar-` | `ȷ́ʰwar` | `−-` `+∅` |
| `ira-pro` | `a-` | `a` | `−-` `+∅` |
| `ira-pro` | `fra-` | `fra` | `−-` `+∅` |
| `ira-pro` | `Há-` | `Hˈa` | `−́-` `+ˈ` |
| `ira-pro` | `ha-` | `ha` | `−-` `+∅` |
| `ira-pro` | `warj-` | `warj` | `−-` `+∅` |
| `ira-pro` | `Hwah-` | `Hwah` | `−-` `+∅` |
| `ira-pro` | `duš-` | `duš` | `−-` `+∅` |
| `ira-pro` | `ham-` | `ham` | `−-` `+∅` |
| `cel-pro` | `ambi-` | `ambi` | `−-` `+∅` |
| `cel-pro` | `an-` | `an` | `−-` `+∅` |
| `cel-pro` | `ad-` | `ˈad` | `−-` `+ˈ` |
| `cel-pro` | `-man` | `man` | `−-` `+∅` |
| `cel-pro` | `su-` | `su` | `−-` `+∅` |
| `cel-pro` | `-ākos` | `ākos` | `−-` `+∅` |
| `cel-pro` | `kom-` | `kˈom` | `−-` `+ˈ` |
| `cel-pro` | `sɸer-` | `sɸer` | `−-` `+∅` |
| `cel-pro` | `ɸro-` | `ɸrˈo` | `−-` `+ˈ` |
| `cel-pro` | `uɸer-` | `uɸˈer` | `−-` `+ˈ` |
| `cel-pro` | `uɸo-` | `uɸo` | `−-` `+∅` |
| `cel-pro` | `-ālos` | `ālos` | `−-` `+∅` |
| `cel-pro` | `-mā` | `mā` | `−-` `+∅` |
| `cel-pro` | `ɸeri-` | `ɸˈeri` | `−-` `+ˈ` |
| `cel-pro` | `-sketi` | `skˈeti` | `−-` `+ˈ` |
| `ine-bsl-pro` | `sam-` | `sam` | `−-` `+∅` |
| `ine-bsl-pro` | `-iškas` | `iškas` | `−-` `+∅` |
| `ine-bsl-pro` | `-was` | `wˈas` | `−-` `+ˈ` |


### Thorn vs theta (152 pairs)

| language | recorded | derived | chars |
|---|---|---|---|
| `gem-pro` | `þat` | `θˈat` | `−þ` `+θˈ` |
| `gem-pro` | `þū` | `θˈū` | `−þ` `+θˈ` |
| `gem-pro` | `tanþs` | `tˈanθs` | `−þ` `+ˈθ` |
| `gem-pro` | `brōþēr` | `brˈōθēr` | `−þ` `+ˈθ` |
| `gem-pro` | `hwaþeraz` | `hwˈaθeraz` | `−þ` `+ˈθ` |
| `gem-pro` | `ferþuz` | `fˈerθuz` | `−þ` `+ˈθ` |
| `gem-pro` | `þarmaz` | `θˈarmaz` | `−þ` `+θˈ` |
| `gem-pro` | `-þrą` | `θrą` | `−-þ` `+θ` |
| `gem-pro` | `þekuz` | `θˈekuz` | `−þ` `+θˈ` |
| `gem-pro` | `kinþiz` | `kˈinθiz` | `−þ` `+ˈθ` |
| `gmw-pro` | `þegn` | `θegn` | `−þ` `+θ` |
| `gmw-pro` | `þorn` | `θorn` | `−þ` `+θ` |
| `gmw-pro` | `smiþ` | `smiθ` | `−þ` `+θ` |
| `gmw-pro` | `dauþu` | `dauθu` | `−þ` `+θ` |
| `gmw-pro` | `ābanþ` | `ābanθ` | `−þ` `+θ` |
| `gmw-pro` | `þimstr` | `θimstr` | `−þ` `+θ` |
| `gmw-pro` | `paþ` | `paθ` | `−þ` `+θ` |
| `gmw-pro` | `þistil` | `θistil` | `−þ` `+θ` |
| `gmw-pro` | `þarm` | `θarm` | `−þ` `+θ` |
| `gmw-pro` | `friþu` | `friθu` | `−þ` `+θ` |
| `gmw-pro` | `maiþm` | `maiθm` | `−þ` `+θ` |
| `gmw-pro` | `mānōþ` | `mānōθ` | `−þ` `+θ` |
| `gmw-pro` | `þīn` | `θīn` | `−þ` `+θ` |
| `gmw-pro` | `brōþer` | `brōθer` | `−þ` `+θ` |
| `gmw-pro` | `tanþ` | `tanθ` | `−þ` `+θ` |
| `gmw-pro` | `hrinþ` | `hrinθ` | `−þ` `+θ` |
| `gmw-pro` | `stuþ` | `stuθ` | `−þ` `+θ` |
| `gmw-pro` | `gulþīn` | `gulθīn` | `−þ` `+θ` |
| `gmw-pro` | `laiþ` | `laiθ` | `−þ` `+θ` |
| `gmw-pro` | `swinþ` | `swinθ` | `−þ` `+θ` |
| `gmw-pro` | `gunþi` | `gunθi` | `−þ` `+θ` |
| `gmw-pro` | `stinþ` | `stinθ` | `−þ` `+θ` |
| `gmw-pro` | `jugunþi` | `jugunθi` | `−þ` `+θ` |
| `gmw-pro` | `magaþ` | `magaθ` | `−þ` `+θ` |
| `gmw-pro` | `balþ` | `balθ` | `−þ` `+θ` |
| `gmw-pro` | `aiþ` | `aiθ` | `−þ` `+θ` |
| `gmw-pro` | `arbaiþi` | `arbaiθi` | `−þ` `+θ` |
| `gmw-pro` | `rīþ` | `rīθ` | `−þ` `+θ` |
| `gmw-pro` | `þwangi` | `θwangi` | `−þ` `+θ` |
| `gmw-pro` | `sanþ` | `sanθ` | `−þ` `+θ` |
| `gmw-pro` | `þursti` | `θursti` | `−þ` `+θ` |
| `gmw-pro` | `haliþ` | `haliθ` | `−þ` `+θ` |
| `gmw-pro` | `þangil` | `θangil` | `−þ` `+θ` |
| `gmw-pro` | `darōþu` | `darōθu` | `−þ` `+θ` |
| `gmw-pro` | `liþu` | `liθu` | `−þ` `+θ` |
| `gmw-pro` | `felþu` | `felθu` | `−þ` `+θ` |
| `gmw-pro` | `weþru` | `weθru` | `−þ` `+θ` |
| `gmw-pro` | `walþu` | `walθu` | `−þ` `+θ` |
| `gmw-pro` | `þuli` | `θuli` | `−þ` `+θ` |
| `gmw-pro` | `þuldi` | `θuldi` | `−þ` `+θ` |
| `gmw-pro` | `þrūþi` | `θrūθi` | `−þþ` `+θθ` |
| `gmw-pro` | `þurstu` | `θurstu` | `−þ` `+θ` |
| `gmw-pro` | `þiudisk` | `θiudisk` | `−þ` `+θ` |
| `gmw-pro` | `hrōþi` | `hrōθi` | `−þ` `+θ` |
| `gmw-pro` | `þuris` | `θuris` | `−þ` `+θ` |
| `gmw-pro` | `þurhil` | `θurhil` | `−þ` `+θ` |
| `gmw-pro` | `aiþastab` | `aiθastab` | `−þ` `+θ` |
| `gmw-pro` | `numþi` | `numθi` | `−þ` `+θ` |
| `gmw-pro` | `Rādagunþi` | `Rādagunθi` | `−þ` `+θ` |
| `gmw-pro` | `aþuling` | `aθuling` | `−þ` `+θ` |
| `gmw-pro` | `þwerh` | `θwerh` | `−þ` `+θ` |
| `gmw-pro` | `wraiþ` | `wraiθ` | `−þ` `+θ` |
| `gmw-pro` | `faþm` | `faθm` | `−þ` `+θ` |
| `gmw-pro` | `āþm` | `āθm` | `−þ` `+θ` |
| `gmw-pro` | `irþīn` | `irθīn` | `−þ` `+θ` |
| `gmw-pro` | `sinþ` | `sinθ` | `−þ` `+θ` |
| `gmw-pro` | `Friþurīk` | `Friθurīk` | `−þ` `+θ` |
| `gmw-pro` | `harbistamānōþ` | `harbistamānōθ` | `−þ` `+θ` |
| `gmw-pro` | `þwiril` | `θwiril` | `−þ` `+θ` |
| `gmw-pro` | `þoll` | `θoll` | `−þ` `+θ` |
| `gmw-pro` | `erþōhnut` | `erθōhnut` | `−þ` `+θ` |
| `gmw-pro` | `sunþr` | `sunθr` | `−þ` `+θ` |
| `gmw-pro` | `sunþr` | `sunθr` | `−þ` `+θ` |
| `gmw-pro` | `sunþr` | `sunθr` | `−þ` `+θ` |
| `gmw-pro` | `niþanā` | `niθanā` | `−þ` `+θ` |
| `gmw-pro` | `norþanā` | `norθanā` | `−þ` `+θ` |
| `gmw-pro` | `kunþīg` | `kunθīg` | `−þ` `+θ` |
| `gmw-pro` | `unkunþīg` | `unkunθīg` | `−þ` `+θ` |
| `gmw-pro` | `-þi` | `θi` | `−-þ` `+θ` |
| `gmw-pro` | `gaburþi` | `gaburθi` | `−þ` `+θ` |
| `gmw-pro` | `burþi` | `burθi` | `−þ` `+θ` |
| `gmw-pro` | `unfriþu` | `unfriθu` | `−þ` `+θ` |
| `gmw-pro` | `friþil` | `friθil` | `−þ` `+θ` |
| `gmw-pro` | `holþ` | `holθ` | `−þ` `+θ` |
| `gmw-pro` | `haþu` | `haθu` | `−þ` `+θ` |
| `gmw-pro` | `nanþ` | `nanθ` | `−þ` `+θ` |
| `gmw-pro` | `þanā` | `θanā` | `−þ` `+θ` |
| `gmw-pro` | `þurnīn` | `θurnīn` | `−þ` `+θ` |
| `gmw-pro` | `swinþalīk` | `swinθalīk` | `−þ` `+θ` |
| `gmw-pro` | `sanþalīk` | `sanθalīk` | `−þ` `+θ` |
| `ang` | `þing` | `θing` | `−þ` `+θ` |
| `ang` | `þe` | `θe` | `−þ` `+θ` |
| `ang` | `þær` | `θær` | `−þ` `+θ` |
| `ang` | `þorn` | `θorn` | `−þ` `+θ` |
| `ang` | `weorþan` | `weorθan` | `−þ` `+θ` |
| `ang` | `þæt` | `θæt` | `−þ` `+θ` |
| `ang` | `þæt` | `θæt` | `−þ` `+θ` |
| `ang` | `þæt` | `θæt` | `−þ` `+θ` |
| `ang` | `þæt` | `θæt` | `−þ` `+θ` |
| `ang` | `feþer` | `feθer` | `−þ` `+θ` |
| `ang` | `þennan` | `θennan` | `−þ` `+θ` |
| `ang` | `morþor` | `morθor` | `−þ` `+θ` |
| `ang` | `þunor` | `θunor` | `−þ` `+θ` |
| `ang` | `weorþ` | `weorθ` | `−þ` `+θ` |
| `ang` | `weorþ` | `weorθ` | `−þ` `+θ` |
| `ang` | `fæþm` | `fæθm` | `−þ` `+θ` |
| `ang` | `heorþ` | `heorθ` | `−þ` `+θ` |
| `ang` | `þridda` | `θridda` | `−þ` `+θ` |
| `ang` | `þridda` | `θridda` | `−þ` `+θ` |
| `ang` | `pæþ` | `pæθ` | `−þ` `+θ` |
| `ang` | `seoþan` | `seoθan` | `−þ` `+θ` |
| `ang` | `swæþ` | `swæθ` | `−þ` `+θ` |
| `ang` | `swæþ` | `swæθ` | `−þ` `+θ` |
| `ang` | `leþer` | `leθer` | `−þ` `+θ` |
| `ang` | `þingian` | `θingian` | `−þ` `+θ` |
| `ang` | `weorþian` | `weorθian` | `−þ` `+θ` |
| `ang` | `forþ` | `forθ` | `−þ` `+θ` |
| `ang` | `forþ` | `forθ` | `−þ` `+θ` |
| `ang` | `þwang` | `θwang` | `−þ` `+θ` |
| `ang` | `þweorh` | `θweorh` | `−þ` `+θ` |
| `ang` | `þyld` | `θyld` | `−þ` `+θ` |
| `ang` | `þegnian` | `θegnian` | `−þ` `+θ` |
| `ang` | `þel` | `θel` | `−þ` `+θ` |
| `ang` | `breoþan` | `breoθan` | `−þ` `+θ` |
| `ang` | `bæþ` | `bæθ` | `−þ` `+θ` |
| `ang` | `þearm` | `θearm` | `−þ` `+θ` |
| `ang` | `weþer` | `weθer` | `−þ` `+θ` |
| `ang` | `þeorf` | `θeorf` | `−þ` `+θ` |
| `ang` | `þeorf` | `θeorf` | `−þ` `+θ` |
| `ang` | `þost` | `θost` | `−þ` `+θ` |
| `ang` | `þeotan` | `θeotan` | `−þ` `+θ` |
| `ang` | `þweran` | `θweran` | `−þ` `+θ` |
| `ang` | `smiþian` | `smiθian` | `−þ` `+θ` |
| `ang` | `mearþ` | `mearθ` | `−þ` `+θ` |
| `ang` | `þroht` | `θroht` | `−þ` `+θ` |
| `ang` | `þunrian` | `θunrian` | `−þ` `+θ` |
| `ang` | `þindan` | `θindan` | `−þ` `+θ` |
| `ang` | `-weorþ` | `weorθ` | `−-þ` `+θ` |
| `ang` | `þweal` | `θweal` | `−þ` `+θ` |
| `ang` | `þancung` | `θancung` | `−þ` `+θ` |
| `ang` | `þyle` | `θyle` | `−þ` `+θ` |
| `ang` | `stæþ` | `stæθ` | `−þ` `+θ` |
| `ang` | `wiþer` | `wiθer` | `−þ` `+θ` |
| `ang` | `Friþugeorn` | `Friθugeorn` | `−þ` `+θ` |
| `ang` | `Friþuweald` | `Friθuweald` | `−þ` `+θ` |
| `ang` | `seorþan` | `seorθan` | `−þ` `+θ` |
| `ang` | `geniþerian` | `geniθerian` | `−þ` `+θ` |
| `ang` | `wriþa` | `wriθa` | `−þ` `+θ` |
| `ang` | `Friþubeorht` | `Friθubeorht` | `−þ` `+θ` |
| `ang` | `Friþumund` | `Friθumund` | `−þ` `+θ` |
| `ang` | `fæþmian` | `fæθmian` | `−þ` `+θ` |
| `enm` | `griþen` | `griθen` | `−þ` `+θ` |


### Bracket / optional segment (5 pairs)

| language | recorded | derived | chars |
|---|---|---|---|
| `iir-pro` | `(H)íšuš` | `Hˈišuš` | `−()́` `+ˈ` |
| `iir-pro` | `(H)adʰás` | `Hadʰˈas` | `−()́` `+ˈ` |
| `ira-pro` | `(H)adári` | `Hadˈari` | `−()́` `+ˈ` |
| `ira-pro` | `(h)rabā́š` | `hrabˈāš` | `−()́` `+ˈ` |
| `ira-pro` | `da(H)inúš` | `daHinˈuš` | `−()́` `+ˈ` |


### Breve (3 pairs)

| language | recorded | derived | chars |
|---|---|---|---|
| `it` | `insensibile` | `insensibĭle` | `−∅` `+̆` |
| `it` | `vituperabile` | `vĭtŭpĕrabĭle` | `−∅` `+̆̆̆̆` |
| `it` | `catello` | `catĕllo` | `−∅` `+̆` |


### Space / two-word lemma (2 pairs)

| language | recorded | derived | chars |
|---|---|---|---|
| `gmw-pro` | `fimf tigiwi` | `fimftigiwi` | `− ` `+∅` |
| `gmw-pro` | `sebun tigiwi` | `sebuntigiwi` | `− ` `+∅` |

## Appendix B — the 10 pairs where the engine writes no stress

| language | recorded | derived | record's accent |
|---|---|---|---|
| `it` | `sé` | `se` | primary on nucleus 0 |
| `iir-pro` | `naHwíyas` | `naHwiyas` | primary on nucleus 1 |
| `iir-pro` | `Habʰí` | `Habʰi` | primary on nucleus 1 |
| `iir-pro` | `Háćru` | `Haćru` | primary on nucleus 0 |
| `iir-pro` | `mr̥dúš` | `mr̥duš` | primary on nucleus 1 |
| `iir-pro` | `dušmánās` | `dušmanās` | primary on nucleus 1 |
| `iir-pro` | `Hsumánās` | `Hsumanās` | primary on nucleus 1 |
| `ira-pro` | `draHǰáh` | `draHǰah` | primary on nucleus 1 |
| `ira-pro` | `dušmánāh` | `dušmanāh` | primary on nucleus 1 |
| `ine-bsl-pro` | `dwínas` | `dwinas` | primary on nucleus 0 |

`it sé ← se` is the only one where the accent separates two lexemes: the stressed pronoun `sé` and the clitic `se` are different words, and the laws derive the clitic.

## Appendix C — sample of the genuine pairs, per language

| language | recorded | derived | chars | how the accent is known |
|---|---|---|---|---|
| `gem-pro` | `in` | `ˈin` | `−∅` `+ˈ` | silent |
| `gem-pro` | `sa` | `sˈa` | `−∅` `+ˈ` | silent |
| `gem-pro` | `mari` | `mˈari` | `−∅` `+ˈ` | silent |
| `gmw-pro` | `halh` | `hˈalh` | `−∅` `+ˈ` | silent |
| `ang` | `ut` | `ˈut` | `−∅` `+ˈ` | silent |
| `ang` | `ides` | `idˈes` | `−∅` `+ˈ` | silent |
| `ang` | `ears` | `ˈears` | `−∅` `+ˈ` | silent |
| `enm` | `wolf` | `wˈolf` | `−∅` `+ˈ` | silent |
| `enm` | `ars` | `ˈars` | `−∅` `+ˈ` | silent |
| `enm` | `werk` | `wˈerk` | `−∅` `+ˈ` | silent |
| `en` | `nit` | `nˈit` | `−∅` `+ˈ` | silent |
| `en` | `nit` | `nˈit` | `−∅` `+ˈ` | silent |
| `goh` | `fater` | `fatˈer` | `−∅` `+ˈ` | silent |
| `gmh` | `wolf` | `wˈolf` | `−∅` `+ˈ` | silent |
| `la` | `ad` | `ˈad` | `−∅` `+ˈ` | silent |
| `la` | `me` | `mˈe` | `−∅` `+ˈ` | silent |
| `la` | `hostis` | `hˈostis` | `−∅` `+ˈ` | silent |
| `it` | `tu` | `tˈu` | `−∅` `+ˈ` | silent |
| `it` | `sé` | `se` | `−́` `+∅` | silent |
| `it` | `ara` | `ˈara` | `−∅` `+ˈ` | silent |
| `iir-pro` | `ná` | `nˈa` | `−́` `+ˈ` | positions |
| `iir-pro` | `sá` | `sˈa` | `−́` `+ˈ` | positions |
| `iir-pro` | `ćatám` | `ćatˈam` | `−́` `+ˈ` | positions |
| `iir-pro` | `naHwíyas` | `naHwiyas` | `−́` `+∅` | silent |
| `ira-pro` | `waydáyati` | `waydˈayati` | `−́` `+ˈ` | positions |
| `ira-pro` | `hmáwčati` | `hmˈawčati` | `−́` `+ˈ` | positions |
| `ira-pro` | `cánhati` | `cˈanhati` | `−́` `+ˈ` | positions |
| `ira-pro` | `draHǰáh` | `draHǰah` | `−́` `+∅` | silent |
| `cel-pro` | `en` | `ˈen` | `−∅` `+ˈ` | silent |
| `cel-pro` | `genus` | `gˈenus` | `−∅` `+ˈ` | silent |
| `cel-pro` | `enter` | `entˈer` | `−∅` `+ˈ` | silent |
| `ine-bsl-pro` | `źámbas` | `źˈambas` | `−́` `+ˈ` | positions |
| `ine-bsl-pro` | `snáigas` | `snˈaigas` | `−́` `+ˈ` | positions |
| `ine-bsl-pro` | `śís` | `śˈis` | `−́` `+ˈ` | positions |
| `ine-bsl-pro` | `medu` | `mˈedu` | `−∅` `+ˈ` | silent |

Every language with a genuine pair appears; the full 525 are in the probe's JSON. `sé`/`se` is the one pair in this table the audit does not accept (§2, Appendix B).
