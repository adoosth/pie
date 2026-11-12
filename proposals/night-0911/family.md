# The wider family: Latin and Italian get an orthographic layer

- **Status:** implemented and measured. Two new artefacts, no sound law touched,
  `exact` unchanged in both languages.
- **Session:** 2026-11-09, HEAD `ec90860`. Another workstream was editing
  `src/pie/{spelling,transforms}.py`, `tools/coverage.py`, `data/spelling/enm.yaml`
  and adding `data/spelling/sa.yaml` while this file was written; every number
  below was re-measured with my two files temporarily moved out and restored, so
  it is not contaminated by that work.
- **Writes:** `data/spelling/it.yaml` (new), `data/spelling/la.yaml` (new), this
  file. No rule file, no `src/`, no other proposal.
- **Reproduce:** commands in §6.

## 1 · Ranking: identified words with no explanation

Baseline at session start (`tools/coverage.py --langs it de la grc sa ang enm
--limit 0`, `/tmp/x.json`). "Unexplained" = `identified − explained`. Greek and
Sanskrit were ranked first and second by this table but were withdrawn from my
scope by the super agent (its Greek/Devanagari writers); they are listed for
completeness only.

| rank | language | identified | explained | unexplained | share | has a spelling file? |
|---:|---|---:|---:|---:|---:|---|
| 1 | Italian (`it`) | 10,661 | 1,118 | **9,543** | 89.5% | **no** |
| 2 | German (`de`) | 8,077 | 320 | 7,757 | 96.0% | yes |
| 3 | Old English (`ang`) | 6,309 | 1,119 | 5,190 | 82.3% | yes |
| 4 | Middle English (`enm`) | 4,692 | 808 | 3,884 | 82.8% | yes |
| 5 | Latin (`la`) | 3,233 | 7 | **3,226** | **99.8%** | **no** |
| — | Greek (`grc`) | 3,102 | 0 | 3,102 | 100% | out of scope |
| — | Sanskrit (`sa`) | 3,791 | 0 | 3,791 | 100% | out of scope |

**Chosen: Italian and Latin.** Italian is the largest pool in the family and has
no layer at all; four general conventions buy 271 words. Latin has the highest
share unexplained of any language in the table, has no layer, and its letter
table is a prerequisite for measuring every Romance descendant. German, Old and
Middle English already have layers whose measured residual is law and notation,
not spelling (see §5).

## 2 · Diagnosis of the top miss signatures

Signatures from `pie worklist --lang <x>` at session start; the classification
is mine. `D` = a difference of dictionary notation (orthography), `L` = a
missing or wrong sound law, `M` = morphology (a different cell or a derived
stem), `I` = genuine irregularity.

### Italian (9,543 unexplained)

| n | signature | example | class |
|---:|---|---|---|
| 147 | `ɛ→e` | `dɛ` ≠ **de** | **D** — Italian spelling does not mark open/close mid vowels |
| 113 | `o→u` | `lopa` ≠ **lupa** | L — the Latin short *u is not carried (wrong-law/quality) |
| 84 | `ɔ→o` | `ɔ` ≠ **o** | **D** — same convention, back vowel |
| 77 | `−i` | `Armienia` ≠ **Armenia** | L — an inserted glide vowel the language does not have |
| 74 | `o→a +r +e` | `do` ≠ **dare** | M — the target is the infinitive, the ancestor a root |
| 74 | `−u` | `luoco` ≠ **loco** | L — the `uo > o` monophthongisation is missing |
| 59 | `t→z +n +e` | `inondatio` ≠ **inondazione** | L — Latin `-tiō` > Italian `-zione` (affricate + suffix) |
| 54 | `i→e` | `pisce` ≠ **pesce** | L — Latin short *i > e before a consonant |
| 34 | `+t +e` | `fron` ≠ **fronte** | L/M — final consonant of the stem restored |
| 33 | `+-` | `ab` ≠ **ab-** | M — bound-form hyphen in the headword, not a sound |

Italian's orthographic share is small and clean: `ɛ→e`, `ɔ→o`, and the loanword
letter `y→i`. Everything else is the law chain, which is why one small file is
the right size of artefact here.

### Latin (3,226 unexplained, 7 explained)

| n | signature | example | class |
|---:|---|---|---|
| 35 | `ō→o` | `dō` ≠ **do** | **D** — the dictionary writes no macron |
| 32 | `o→u` | `tauros` ≠ **taurus** | L — final *-os > -us is not registered |
| 12 | `ā→a` | `stāmen` ≠ **stamen** | **D** |
| 11 | `o→u +m` | `so` ≠ **sum** | M/L — the copula's suppletive stem |
| 9 | `k→c ō→o` | `karrō` ≠ **carro** | **D** — c for /k/, no macron |
| 8 | `+-` | `tri` ≠ **tri-** | M — bound form |
| 7 | `−t` | `ponts` ≠ **pons** | L — final cluster simplification |
| 7 | `k→c` | `kinis` ≠ **cinis** | **D** |
| 6 | `w→v` | `wel` ≠ **vel** | **D** — v for /w/ |
| 6 | `ē→e` | `dē` ≠ **de** | **D** |
| 6 | `+u +s` | `gen` ≠ **genus** | M — suffixed stem vs root |

Latin is the mirror image of Italian: almost all of its *cheap* misses are
notation (macron, c, v), and almost all of its *expensive* misses are laws
(`-os > -us`, final clusters) that need `itc-pro__la.yaml`, which was outside
this session's write set.

### The three languages not chosen

German (7,757 unexplained): top rows are `ē→e` (63) and `ā→a` (47), already
fixed by `de.yaml`, then `a→e` (62), `−e` (37), `+ch` (34) — real sound-law and
morphology work (`gmh__de` was not in my write set). Middle English (3,884):
`ē→e` (256) and `ā→a` (74) are length notation already in `enm.yaml`, then
`i→y` (68) and `+e` (66). Old English (5,190): the layer already earns 484
words; the residual is law (`+ch`, `−e`, umlaut). None of the three offered a
spelling gain this session (measured pool in §5).

## 3 · What shipped

### 3.1 `data/spelling/it.yaml` — Italian writing conventions

Five rules, tier `orthographic`, applied after `la → it`:

| order | rule | convention |
|---:|---|---|
| 5 | `drop_stress` | ordinary Italian lemmas carry no accent mark |
| 50 | `y_to_i` | the letter y belongs to loans; the vowel is written i (Siria, ginnasio) |
| 100 | `open_e` | /ɛ/ and /e/ are both written e (bene, festa) |
| 101 | `open_o` | /ɔ/ and /o/ are both written o (sole, cosa) |

**Citations.** `maiden-1995` (Maiden, *A Linguistic History of Italian*),
locator: the chapter on the written language — the orthography section states
that the spelling does not distinguish open and close mid vowels, that y occurs
only in learned loans, and that stress is normally unmarked. `sihler-1995` for
the letter inventory. Locators are chapter/section, not page numbers: no copy is
on this machine, and inventing a page would be worse than naming the section.

**Measured** (`tools/coverage.py --langs it --limit 0`, full corpus, my file
moved out and back):

| measure | before | after |
|---|---:|---:|
| tested | 10,661 | 10,661 |
| **exact** (sound laws) | **1,118** | **1,118** |
| **orthographic** | **0** | **271** |
| explained (exact + orthographic) | 1,118 | 1,389 |
| orthographic rate of glossary | 0.0000% | 1.2190% |

### 3.2 `data/spelling/la.yaml` — Latin writing conventions

Seven rules, tier `orthographic`, applied after `itc-pro → la`:

| order | rule | convention |
|---:|---|---|
| 5 | `drop_stress` | Latin marks neither stress nor pitch |
| 10 | `labiovelar_qu` | /kʷ/ is written qu (quod, aqua) |
| 20 | `k_to_c` | /k/ is written c in every position (cūr, dīcō) |
| 30 | `w_to_v` | /w/ is written v (via, servus) |
| 100–104 | `long_a … long_u` | vowel quantity is not written: ā ē ī ō ū are a e i o u |

**Citations.** `meiser-1998` (Meiser, *Historische Laut- und Formenlehre der
lateinischen Sprache*), locator: the introduction on the alphabet and
orthography — quantity is marked only in pedagogical and epigraphic texts, c
writes /k/, qu writes /kʷ/, v writes /w/. `weiss-2009` (Weiss, *Outline of the
Historical and Comparative Grammar of Latin*), locator: the orthography and
phonology section; `sihler-1995` for the letter inventory.

**Measured** (`tools/coverage.py --langs la --limit 0`, full corpus, my file
moved out and back):

| measure | before | after |
|---|---:|---:|
| tested | 3,205 | 3,205 |
| **exact** (sound laws) | **7** | **7** |
| **orthographic** | **0** | **41** |
| explained (exact + orthographic) | 7 | 48 |
| orthographic rate of glossary | 0.0000% | 0.5365% |

Why the probe counts fewer (27 and 269) than coverage (41 and 271): the probe
derives only the *closest* recorded ancestor attempt and spells that one, while
`coverage.py` tries every ancestor in the chain and counts a word when any
spelled derivation lands and passes `spelling.plausible`. The published number
is coverage's, and the two agree on the mechanism: no `exact` word moved.

## 4 · Ablations (what each convention is worth)

Counted words with one rule switched off (probe, same selection rule as above):

| Italian | counted | gain |
|---|---:|---:|
| (none) | 269 | — |
| `open_e` off | 89 | +180 |
| `open_o` off | 174 | +95 |
| `y_to_i` off | 259 | +10 |
| `drop_stress` off | 268 | +1 |

| Latin | counted | gain |
|---|---:|---:|
| (none) | 27 | — |
| `long_a` off | 15 | +12 |
| `drop_stress` off | 16 | +11 |
| `long_o` off | 19 | +8 |
| `k_to_c` off | 20 | +7 |
| `long_e` off | 23 | +4 |
| `long_u` off | 24 | +3 |
| `labiovelar_qu` off | 24 | +3 |
| `w_to_v` off | 25 | +2 |
| `long_i` off | 25 | +2 |

No rule gains nothing: every convention in both files is load-bearing.

## 5 · Rejected, with the measurement

1. **Latin `j → i`** (consonantal i written i, iam). Probe: counted **27 → 27**,
   spelled-right 194 → 206, plausible rejections 8 → 9. Zero gain and one
   previously counted word becomes a rejection: rejected, the rule was removed
   from `la.yaml`.
2. **Italian `x → ss` and `ʒ → g`** (lasso, gente). Probe: counted **269 → 269**,
   spelled-right 626 → 646, plausible rejections 266 → 284. Both are sound
   changes (`ks > ss`, palatalisation) masquerading as letters, and the letter
   choice is lexically conditioned (xilofono keeps x): rejected.
3. **Extending `de.yaml` / `ang.yaml` / `enm.yaml`.** The measured pool left for
   a spelling layer is exhausted by the guard and by the zero-step rule:
   German spelled-right 1,034, counted 119, zero-step 697, plausible-rejected
   218; Middle English 863 / 406 / 192 / 265; Old English 908 / 521 / 228 / 159.
   The residue is phonology, not convention; no extension was measured to a
   gain, so none was shipped. (`enm.yaml` was also being edited by another
   workstream.)
4. **A law in `la__it.yaml`** (the worklist's `t→z +n +e`, 59 words, i.e. Latin
   `-tiō` > `-zione`). It is a genuine missing law, but a law needs its own
   proposal, examples and a measured `whatif.py` run; not attempted in the time
   available, therefore not shipped rather than shipped unmeasured.
5. **A "reading" layer for Latin's c/v/w before the laws.** Most of Italy's 266
   plausible rejections are the law layer carrying Latin *letters* (`c` where the
   dictionary's IPA has `k`, geminates written `cc` against `k.k`). That is a
   notation fold in `spelling._readable`/W7, not a writing convention: reported
   here, not patched (out of scope).

## 6 · Reproduce

```bash
# published numbers (writes /tmp only; never the repo reports)
PYTHONPATH=src python3 tools/coverage.py --langs la it --limit 0 --out /tmp/after.json

# the same measurement before my files: move them out, run, move them back
mv data/spelling/la.yaml /tmp/la.yaml; mv data/spelling/it.yaml /tmp/it.yaml
PYTHONPATH=src python3 tools/coverage.py --langs la it --limit 0 --out /tmp/before.json
mv /tmp/la.yaml data/spelling/la.yaml; mv /tmp/it.yaml data/spelling/it.yaml

# the layers by hand
PYTHONPATH=src python3 -m pie.cli spell --lang it "dɛ"      # de
PYTHONPATH=src python3 -m pie.cli spell --lang it "sɔl"     # sol
PYTHONPATH=src python3 -m pie.cli spell --lang la "dō"      # do
PYTHONPATH=src python3 -m pie.cli spell --lang la "kʷo"     # quo

# gates
PYTHONPATH=src python3 -m pie.cli check-rules               # 0 problems
PYTHONPATH=src python3 -m unittest discover -s tests -q     # 342 tests, OK
```

The diagnostic probe is `proposals/night-0911/fa_probe.py --lang it|la` (it
reproduces coverage's ancestor choice). Its Persian-specific `notation_junk`
heuristic treats the letter `c` as debris; for Latin and Italian I ran a copy
with `c` removed from that set. That changes only the diagnostic tallies, never
the counted number.

## 7 · Review questions (`docs/REVIEW.md`)

1. **Is the claim stated?** Each rule is one sentence about a letter, with no
   "sometimes" and no lexeme named.
2. **Is the evidence independent?** Every example is a different etymon, and the
   files' positional rules are exercised by words the vowel rules do not touch
   (`kˈorpos`, `kʷo`, `wel`, `ˈlupa`; `syria`, `sɔl`, `dɛ`).
3. **Does the rule over-apply?** The conventions are order-free letter maps,
   except the stress rule; measured: no exact word changed in either language,
   and the counted spellings pass `spelling.plausible`.
4. **Is the tier honest?** All rules are `orthographic`; no `data/rules/` file
   was touched. The macron and the c/v letter choices are writing conventions of
   the dictionaries, not sound changes — and they are scored only in the
   orthographic column.
5. **Is the artefact shaped right?** Two spelling files and this proposal; no
   generated report was rewritten (`coverage.py` ran with `--langs`, which never
   publishes).
