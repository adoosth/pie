# 011 · Proto-Indo-Iranian → Proto-Iranian → Avestan: what the misses say

- **Status:** open — one law shipped (`deaspirate_palatal` generalised), one law
  measured and held back (`tse_to_s_before_stop`), Avestan ancestry ingested.
- **Session:** 2026-11-09; started at HEAD `083dfe5`, verified green at
  `c621fa6` (another session committed the Median law, the Middle Persian
  enrichment and the new `tools/whatif.py` gate during the day; nothing shipped
  here touches those files or `data/rules/ira-pro__peo.yaml`).
- **Writes:** `data/rules/iir-pro__ira-pro.yaml`,
  `tools/ingest_ave.py` (new), `data/lexicon/_supplement/ave.jsonl.gz` (only
  through that tool), `proposals/night-0911/irapro.md`,
  `proposals/night-0911/ira_probe.py` (the measuring tool).
  `data/rules/ira-pro__peo.yaml` and `iir-pro__inc-pro.yaml`: untouched.
- **Reproduce:** commands at the end.

## 0 · The measurement problem comes first

The worklist's headline number for Proto-Iranian is **7 of 338**. It is not a
statement about the laws: the glossary writes stress as an acute (`waydáyati`)
and the engine writes the stress token (`waydˈayati`), and
`audit.audit_language`, `tools/coverage.py` and `tools/whatif.py` compare the
two as raw strings (`d.output == target`). The repo's own comparison for the
word page, `service._same_form`, normalises exactly this (`_comparison_key`
turns an acute into the stress token) and depends on the distinction
(`AGENTS.md`: "the engine and the JSON keep the IPA token … the front end's
`pf()` prints `ˈa` as `á`").

Measured on the same 293 Proto-Iranian entries that record a Proto-Indo-Iranian
ancestor (`ira_probe.py --from iir-pro --to ira-pro`):

| comparison | words | note |
|---|---:|---|
| exact, as the worklist counts it | **7 / 293** | the published number |
| after `service.printable_form` (ˈa → á) | **221 / 293** | 214 words differ only in the glyph |
| after `service._same_form` | **238 / 293** | also counts a record that marks no stress |

The whole chain into Proto-Iranian (`--chain`): 330 words derived, **7 exact,
219 printable, 232 `_same_form`**. The same gap exists one stage up
(Proto-Indo-Iranian: 1 exact, 146 printable, 190 `_same_form` of 522).

Consequence for this session: **no sound law can move the Proto-Iranian exact
count**, because 273 of the 300 entries that record a Proto-Indo-Iranian
ancestor mark stress in the target with an acute. Every candidate below
therefore reports two numbers — the gate's (`whatif.py`, exact) and the
notation-aware one (the same derivation compared through `_same_form`). The fix
is one line in `audit.py`/`coverage.py`/`whatif.py` (compare
`printable_form(d.output)` or `_same_form`, as the page already does); it is a
W7 change and outside this session's write scope. It is the single largest
number in the programme that is currently wrong.

## (a) The misses, and what each one is

### Proto-Iranian (`pie worklist --lang ira-pro`: 416 words, 338 tested, 7 exact, 256 near)

| n | signature | example | diagnosis |
|---:|---|---|---|
| 178 | `−ˈ a→á` | `waydˈayati` ≠ **waydáyati** | **(d) orthography** — the dictionary's acute vs the engine's `ˈ`; not a sound change (§0) |
| 19 | `ˈ→́` | `Hnˈāma` ≠ **Hnā́ma** | **(d)** the same, on a form whose only stress mark is the acute |
| 10 | `+-` | `a` ≠ **a-** | **(c)/(d)** a headword convention: prefixes and bound forms are written with a hyphen (`a-`, `dwi-`, `fra-`, `-akah`); never a law |
| 9 | `−ˈ u→ú` | `mˈuHs` ≠ **múHs** | **(d)** stress notation |
| 5 | `−ˈ i→í` | `cwˈišah` ≠ **cwíšah** | **(d)** stress notation |
| 5 | `−ˈ a→á −H` | `nˈazdištHah` ≠ **názdištah** | **(d) + (e)** notation plus a laryngeal the record drops: `*názdištHas`, `*káćištHas` (both `-iHas`) lose it, `*náHuš` keeps it — no stated environment, data inconsistency |
| 4 | `−ˈ r→ŕ` | `wˈr̥kah` ≠ **wŕ̥kah** | **(d)** stress notation on a syllabic sonorant |
| 2 | `a→á` | `draHǰah` ≠ **draHǰáh** | **(e)** the source ancestor carries no stress mark, the target stresses the final syllable: a missing stress-assignment layer, not a segmental law |
| 1 each | `−H r→l`, `−H −á`, `−ˈ a→ā +́` … | `Hlupiš`→`Hrupiš` ≠ **lupiš** | **(e)** the recorded ancestor is a different word (here an `H`-initial variant of *lupiš*) |

Two signatures that were in the worklist at the start of the session are gone
after the shipped law: `−ˈ a→á −ʰ` (3) and `−ʰ −ˈ a→á` (2) — the palatal
aspirate.

### Proto-Indo-Iranian (`pie worklist --lang iir-pro`: 799 words, 522 tested, 1 exact, 309 near)

These all break in `ine-pro → iir-pro`, which this session may not edit. They
are listed because they are the largest block in the branch:

| n | signature | example | diagnosis |
|---:|---|---|---|
| 121 | `−ˈ a→á` | `nˈa` ≠ **ná** | **(d)** stress notation (§0) |
| 29 | `+-` | `a` ≠ **a-** | **(c)/(d)** bound-form hyphens |
| 9 | `−ˈ u→ú`, 6 `−ˈ i→í`, 5 `−ˈ r→ŕ`, 7 `ˈ→́` | — | **(d)** stress notation |
| 7 | `−ˈ ā→á` | `Hˈāwiš` ≠ **Háwiš** | **(a)** PIE *o > PII *a with the accent on the first syllable (`h₂ówis`): a real accent/ablaut question in `ine-pro__iir-pro.yaml` |
| 7 | `a→á +a +s` | `Hawg` ≠ **Háwgas** | **(c) morphology**: the target is a derived stem, the recorded ancestor a root |
| 6 | `−ˈ a→ʰ +á` | `ȷ́ˈanuš` ≠ **ȷ́ʰánuš** | **(a)** a missing aspiration (`ǵ` > `ȷ́ʰ`) and accent shift |
| 5 | `a→̥ +ú +š` | `Hraȷ́` ≠ **Hr̥ȷ́úš** | **(c)** root vs. suffixed stem |

### Avestan (`pie worklist --lang ave`: 352 words, 0 tested)

No signatures at all before this session: not one entry recorded an ancestor, so
there was nothing to derive. After the ancestry ingest (§d): 312 words
tested, still 0 exact, because the target is Avestan script (`𐬀𐬞`) and the
counter compares it with a Latin derivation (`Hap`). See the Avestan section.

## (b) The candidates, measured

Every candidate was tested on both yardsticks before it was written into a rule
file: `tools/evaluate.py`'s 569 recorded pairs, and the glossary. The gate now
is `tools/whatif.py` (exact, as `coverage.py` counts).

### 1 · SHIPPED — the palatal aspirate loses its aspiration (the law already there, three spellings)

**Claim.** PII *ȷ́ʰ > PIr *ȷ́. The aspiration of the Iranian voiced aspirates is
lost and the voice kept (the *bʰ *dʰ *gʰ laws above). The palatal member is
already registered (`deaspirate_palatal`), but with `match: "ȷ́ ʰ"` only.

**Environment.** The aspiration mark, after one of the three spellings of that
segment that the corpus uses: ȷ́ʰ (49 forms), ǰʰ (12), žʰ (5). The mark — not the
segment — is what changes, so the law says nothing about which of the three the
author meant.

**Examples** (four that change, from four etyma, and one that must not — all
five verified by `check-rules`):

| in | out | word |
|---|---|---|
| *ȷ́ʰimás | *ȷ́imás | winter |
| *ǰʰatráH | *ǰatráH | poison (PIr *ǰaθráH) |
| *tʰanǰʰáyati | *tʰanǰáyati | pulls, weighs down (PIr θanǰáyati) |
| *Háǰʰiš | *Háǰiš | snake (PIr Háǰiš) |
| *dʰárati | *dʰárati | must not change: *dʰ is one token, `deaspirate_dh`'s business |

**Predicted** (before running): +4 glossary words (the ǰʰ group; žʰ a fifth),
+9 pairs. **Measured:** glossary printable **+5 / −0** (`Hárǰati`, `Háǰiš`,
`wábžah`, `ǰaθráH`, `θanǰáyati`), `_same_form` **+6**, pairs **+9 / −0**.
`whatif.py` (exact): dropping the law loses **jr̥Hanyam** (7 → 6), i.e. the law
also carries the one word of this transition the exact counter can see.

**Over-application check.** The law alters 9 glossary words; the four it does
not solve were broken elsewhere and still are: `draHǰáh` (the PII source marks
no stress, the target does), `ȷ́ʰžʰā́s` (a sandhi the model does not have),
`slagžʰnás` (word-initial *s lost), `ǰáǰʰukas` (dissimilation *ǰʰ…ǰʰ > ǰ…ǰ plus
vowel changes). No word that already matched is lost, on either yardstick.

### 2 · MEASURED, NOT SHIPPED — PII *tˢ > PIr *s before a dental stop

**Claim.** The affricate *tˢ [ts] loses its stop closure before another stop:
PII *Háwāytˢt 'recognised' > PIr *Háwāyst, *winátˢti 'finds' > *winásti. The
sibilant is the affricate's, not the following *t*'s (`*-tˢt-` > `*-st-`, not
`*-tst-`).

**Environment.** `t ˢ` before *t*, *d*, *dʰ* — the narrowest environment the
recorded outcomes need (the one *utˢčáH is left alone; no Proto-Iranian form is
recorded for it).

**Examples.** *Háwāytˢt → *Háwāyst (ine-pro:weyd-), *winátˢti → *winásti
(glossary `winásti`), *matˢtás → *mastás (participle), *utˢtaHnás → *ustaHnáh
(ine-pro:tenh₂-).

**Predicted** +2 glossary / +4 pairs. **Measured** glossary printable **+2 / −0**,
pairs **+4 / −0**. **`whatif.py`: gained 0, lost 0** — "the law fires nowhere
this corpus can see" (§0: both words carry an acute). The gate was written to
be the authority, so the law is *not* in the rule file. It is ready below and is one paste away
once the counter compares `_same_form`:

```yaml
  - id: tse_to_s_before_stop
    order: 109
    tier: proposed
    name: "PII *tˢ > PIr *s before a dental stop"
    match: "t ˢ"
    replace: s
    env: {right: "(t|d|dʰ)"}
    description: >
      The affricate *tˢ [ts] loses its stop closure before another stop and is
      left as the sibilant: PII *Háwāytˢt 'recognised' is PIr *Háwāyst,
      *winátˢti 'finds' is *winásti, *utˢtaHnás is *ustaHnáh.  The sibilant is
      the affricate's, not the following *t*'s, which is why *-tˢt- gives *-st-
      and not *-tst-.  Before *č (*utˢčáH) the affricate is left alone: no
      recorded outcome stands there.
    references: [wiktionary]
    notes: >
      Locators: Reconstruction:Proto-Iranian/*Háwāyst (cognate set
      ine-pro:weyd-), *HáHnāyst (ine-pro:h₃neyd-), *ustaHnáh
      (ine-pro:tenh₂-) and the glossary entry winásti (from PII *winátˢti).
      Attribution: this is the repo's reading of those pairs, not a sentence
      quoted from a grammar, hence `proposed`.
    examples:
      - {in: "*Háwāytˢt", out: "*Háwāyst", gloss: "recognised (PIr *Háwāyst)"}
      - {in: "*winátˢti", out: "*winásti", gloss: "finds (PIr winásti)"}
      - {in: "*matˢtás", out: "*mastás", gloss: "drunk (past participle)"}
      - {in: "*utˢčáH", out: "*utˢčáH", gloss: "above — the next segment is not a dental stop"}
```

**Over-application check.** Every *ˢ* in either glossary (13 PII forms) stands
before *t* except `*utˢčáH`; the rule cannot reach a vowel, a word edge or a
liquid. It changes 12 words and breaks none.

### 3 · REJECTED — laryngeal loss "between vowels"

The 5 recorded pairs that lose *H (`*bʰáwHati` > *báwati, `*HáHuǰʰyas` >
*Hauǰʰyah, `*bʰárištHas` > *bárištah, `*kšHáyati` > *xšáyati) look like one law
until the rest of the corpus is counted — where Proto-Iranian **keeps** *H in
exactly those environments (`*náHuš` > náHuš, `*múHs` > múHs, `*Hnā́ma`).
Measured: `match: H, env: V_V` gives glossary **+0 / −8** and pairs **+1 / −18**.
Rejected: the environment is not the one the exceptions suggest; the recorded
set is internally inconsistent and that is a data finding, not a law.

### 4 · REJECTED — final *-i > *-ī

10 recorded pairs end `-ati`/`-ti` in PII and `-atī`/`-tī` in PIr, which looks
like a rule. It is a per-entry reconstruction convention: the law also hits the
54 glossary words that genuinely end in *-i*. Measured: pairs **+10 / −137**,
glossary **+0 / −29**. Rejected.

### 5 · REJECTED — the other small families

| candidate | evidence | measured | why not |
|---|---|---|---|
| `s ć > š` (reverse of the registered `ć š > š`) | `*tr̥sćáti` > *tr̥šáti | +1 / −2 | loses `HgráHscati`, `yascáti` |
| `ś ć > c` | `*śćaHyáH` > *caHyáH | +1 / −0 | one word only |
| `t t > t` (degemination) | `*kúttas` > *kútah | +1 / −0 | one word only |
| `-Hs > -Hh` | `*kʰáHs` > *xáHh | +1 / −4 | breaks `múHs`, `pántaHs`, `wadúHs`, `ǰánHs` |
| `p ć > f š` | `*pćā́` > *fšā́ | +0 | gains nothing |
| `d ᶻ > z / _ stop` | `*bʰúdᶻdʰiš` > *búzdiš, `*wadᶻdʰás` > *wazdáh | +0 / −0 | 2 words, and both pairs fall below `evaluate.py`'s 0.55 similarity filter (the superscript counts as an edit), so no yardstick can see them |
| drop `l_to_r` | the 14 recorded pairs that keep *l (`*lap-` > *lap-, `*lukšás` > *luxšáh) | pairs +10 / −4 net +6 for removal; glossary **−1** (`Hlagʰúš`), `whatif` 0/0 | the corpus needs it once, the pairs dislike it 10 times — the tension `proposals/009` already recorded. Left as it is (`proposed`), not silently removed |
| drop `t_to_theta_before_sonorant`, `ts_to_c`, `th_to_theta`, `ps_to_fsh` | — | glossary −10, −1, −3, −4 | each carries more corpus words than the pairs dislike; kept |

## (c) What shipped, and the numbers

One law, generalised in place (`data/rules/iir-pro__ira-pro.yaml`,
`deaspirate_palatal`, order 103, tier `established`, 4 new examples,
`check-rules` green: 510 rules, 632 examples, 0 problems).

| measure | before | after |
|---|---|---|
| `evaluate.py --from iir-pro --to ira-pro` | 422 / 569 = **74.2 %** | **431 / 569 = 75.7 %** |
| glossary, `printable_form` comparison (293 words) | 216 | **221** |
| glossary, `_same_form` (293 words) | 232 | **238** |
| glossary, exact as `whatif`/`coverage` count (338 words) | 7 | **7** |
| `whatif.py --to ira-pro --drop deaspirate_palatal` | — | exact 7 → **6** (loses `jr̥Hanyam`) |

The exact count does not move; §0 is why, and that is the report's main finding.

## (d) The Avestan problem: 0 of 352

**Why it was 0.** Two causes, in this order:

1. **No ancestry.** All 352 keyed Wiktionary entries were fetched by
   `tools/fetch_wiktionary.py`, which keeps the headword and the glosses and
   throws the etymology away. `identified`: 0.
2. **No way to read the target.** Every headword is Avestan script (`𐬀𐬞`).
   `audit` compares `entry["word"]` with a Latin derivation, and
   `data/script/ave.yaml` does not exist, so `script.match("ave", …)` returns
   `None` and the script column cannot count either. Even a perfect derivation
   scores 0.

**What can be carried, and now is.** Yes: the pages name the ancestors with
inheritance templates, so the supplement can carry them. `tools/ingest_ave.py`
(new) reads the Etymology section of each page, keeps the templates
`{{inh}}`/`{{der}}`/`{{etymon|…|:inh|…}}` (never `{{bor}}` as inheritance),
writes `etym` + `anc` (nearest stage first, the shape the Proto-Iranian entries
already have) and nothing else, and is idempotent (`gzip mtime=0`, byte-identical
on a rebuild; `--check` re-reads the pages and reports 0 mismatches). It reuses
`fetch_wiktionary.api` and caches the wikitext under `~/.cache/pie/ave`, so a
rebuild needs no network (`--offline`).

| measure | before | after |
|---|---:|---:|
| entries with an ancestor at a modelled stage (`identified`) | 0 | **312 / 352** |
| nearest ancestor: Proto-Iranian / PII / PIE | — | 172 / 121 / 19 |
| entries with a PIE etymon row | 0 | 195 |
| ancestor forms that are themselves recorded entries of their own glossary | — | PIr 47, PII 109, PIE 169 |
| worklist `ave`: tested / exact / near | 0 / 0 / 0 | **312 / 0 / 8** |

**What still cannot move, and why.** With the ancestry in place, **22 of the 312**
derive to exactly the automatic transliteration of their own script headword
(`𐬵𐬀` `ha`, `𐬛𐬀𐬯𐬀` `dasa`, `𐬟𐬭𐬀` `fra`, `𐬀𐬵𐬨𐬀` `ahma` …) — a diagnostic, not a
result: an automatic reading is not a recorded one (`AGENTS.md`: never derive a
reading from a script the repo cannot read), and the counter does not read it
anyway. The two honest routes out, both outside this session's scope:
`data/script/ave.yaml` (a sign table, like `peo.yaml`, which gives Old Persian
59 scripted matches), or the reading-aware comparison of §0. Note that
`data/lexicon/ave.jsonl.gz` is generated: the supplement reaches the app after
`python3 tools/build_lexicons.py --supplements-only` (run by another session
during this one, which is why the numbers above are live).

## (e) Commands

```bash
PYTHONPATH=src python3 tools/evaluate.py --from iir-pro --to ira-pro
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m pie.cli worklist --lang ira-pro      # and iir-pro, ave
PYTHONPATH=src python3 tools/whatif.py --to ira-pro --drop deaspirate_palatal
PYTHONPATH=src python3 proposals/night-0911/ira_probe.py --from iir-pro --to ira-pro \
    --chain --pairs                                   # exact / printable / _same_form
PYTHONPATH=src python3 proposals/night-0911/ira_probe.py --from iir-pro --to ira-pro \
    --drop deaspirate_palatal --add '<the narrow ȷ́ʰ rule>'   # the law's own share
PYTHONPATH=src python3 tools/ingest_ave.py            # fetch (cached), write the supplement
PYTHONPATH=src python3 tools/ingest_ave.py --check    # stored rows vs the pages
```
