# PIE → Proto-Indo-Iranian, 2026-11-09

Task: push `exact` on `ine-pro → iir-pro` with cited laws only, grouping the
misses by shared signature and never by word. This is the record of what shipped,
what it bought, what was measured and refused, and where the ceiling is.

Command for every number below (sample run, no `--docs`):

```
PYTHONPATH=src python3 tools/coverage.py --langs iir-pro ira-pro --out /tmp/pii-after.json
```

## The numbers

| measure | iir-pro before | after | Δ |
|---|---|---|---|
| tested | 555 | 555 | — |
| **exact** | **167** | **197** | **+30** |
| exact (strict string, no accent notation) | 1 | 1 | — |
| exact (accent read as notation, the rest of the 197) | 166 | 196 | +30 |
| explained (exact + bound forms + identity) | 204 | 237 | +33 |
| near misses (≤4 edits) | 39 | 37 | −2 |
| bound forms (record writes a hyphen) | 36 | 39 | +3 |
| ira-pro exact | 196 | 202 | +6 |
| ira-pro identity (a path that needed no law) | 32 | 31 | −1: one word now needs a law and reaches exact |

Regressions, measured word-by-word over every language whose chain contains
`iir-pro` (iir-pro, inc-pro, sa, ira-pro, ave, peo, pal, fa, xpr): **none.**
The one word that an intermediate build did lose — `wr̥kíHs` — is back, because
the palatalisation environment that cost it is not shipped (below). `pal` keeps
its one match, `fa` and `peo` are unchanged.

Gates: `pie check-rules` reported **0 problems** (618 rules, 852 examples
verified) and `python3 -m unittest discover -s tests -q` reported **454 tests,
OK** at the point this work settled; 11 `test_web` tests failed while the
final-*-r law was still in the tree (see the rejection below) and the suite went
green again once it was removed. Late in the session other batches began editing
`src/pie/service.py`, the Germanic rules and `data/sources.yaml` in the same
working tree: ten `test_web` hierarchy/ladder tests then failed and fail
identically with this file reverted to its original state, and a repository-wide
`check-rules` run is red only on the brand-new `gem-pro__non.yaml` (19 example
failures). Nothing in either set names `ine-pro__iir-pro`; the 11
`test_pii_rules` tests pass with this file, and `test_engine` passes once
`data/sources.yaml` is parseable again. Both failures are reproducible without
this change.

Thirty entries (28 distinct headwords) are new: `Háwiš Háǰʰiš Hŕ̥ćšas bʰábʰruš×2
bʰáwdʰati dr̥štás dyā́wš dáwš dʰráwgʰas dʰádʰaHti dʰáwgdʰi gā́wš kr̥šnás káti mayšás
mazgʰás niždás názdyas×2 pr̥šćáti pátiš spáćš síždati táćšā ćšáyti ćšáytram ǰíHwati
ȷ́áwšati ȷ́ʰáyšas`.

## What shipped

Every rule in `data/rules/ine-pro__iir-pro.yaml` now states its tier, its
environment, what it does **and what it does not**, and examples that
`check-rules` verifies by running the rule alone.

**Added**

| rule | claim | tier | gain |
|---|---|---|---|
| `tk_to_cs` | `*tḱ > *ćš` (`*h₂ŕ̥tḱos > *Hŕ̥ćšas`, `*tḱéyti > *ćšáyti`) | established | 4 |
| `ct_to_st` | `*ćt > *št` (`*dr̥ḱtós > *dr̥štás`, `*oḱtṓm > *oštṓm`) | established | 1 |
| `s_voice` | `*s > *z` before a voiced obstruent (`*nisdós > *nizdás`, `*mosgʰós > *mozgʰás`) | established | 5 |
| `z_ruki` | `*z > *ž` in the ruki environment (`*nizdás > *niždás`) | proposed | 2 |

Citations: Mayrhofer 1986, Lautlehre (the IIr. treatment of the palatovelar +
dental clusters; the voicing of *s before voiced obstruents; the ruki sibilant and
its voiced counterpart); Beekes 2011 (the Indo-Iranian consonant system); Fortson
2004 (the Indo-Iranian chapter). Skt. `ṛ́kṣa-`, `kṣáyati`, `aṣṭā́(u)`, `dr̥ṣṭá-`,
`nīḍá-`, Av. `mazga-` are the outcomes the examples reproduce.

**Changed**

| rule | change | why | gain |
|---|---|---|---|
| `ruki_s` | left environment `(r\|u\|k\|i)` → `(r\|r̥\|u\|ū\|k\|i\|ī\|y\|ć\|ȷ́\|w)` | the handbook ruki set includes the glide counterparts of *i/*u* and the satem affricates that continue *ḱ/*ǵ*; the corpus needed every member (`gā́wš`, `kr̥šnás`, `mayšás`, `pr̥šćáti`, `spáćš`) | see below |
| `brugmann_o_a` | environment restricted to a following non-high vowel | the wide rule lengthens `*h₂ówis`, `*pótis`, `*kʷóti`, `*h₁ógʷʰis`, whose records keep short *a* | 4 |
| palatal order | `labiovelar_*` → `palatal_*` → `l_to_r` → `syllabic_l_to_r` → `vowel_merger_a` → `long_vowel_merger` → `syllabic_m/n` | the first palatalisation is fed by *e* and must see it; the labiovelars must merge first so that `*kʷe` can palatalise | see below |
| `palatal_g`, `palatal_gh` | environment `(ˈ\|ˌ)? (i\|y)` | the engine writes stress as its own token, so the plain environment missed every stressed syllable: `gʷíh₃weti > ǰíHwati` was unreachable | 1 |
| `ruki_s` example | the old example (`*wĺ̥kos → wˈl̥kos`) demonstrated nothing: the *s follows *o and the rule cannot fire there. Replaced with `*gʷṓws → *gʷṓwš`, `*kr̥snós → *kr̥šnós`, `*moysós → *moyšós` | a dead example is a false claim | — |

The ruki and the ordering changes are not separable in the numbers: the whole
set of shipped edits takes 167 → 197 with 0 losses. Ablated one at a time
against the pre-existing file, the pieces were: ruki + *w alone +4; ruki's full
set +3 more; `s_voice` + `z_ruki` +5; Brugmann restriction +4; `*tḱ` +4;
`*ćt` +1; dropping Grassmann +6 (see the rejection list); the palatal order and
the stress allowance together +1 net after the *e and stressed-*í halves were
refused.

**Removed**

`grassmann` (Grassmann's law). Ablating it gained 6 entries and lost none
(`bʰábʰruš×2`, `bʰáwdʰati`, `dʰráwgʰas`, `dʰádʰaHti`, `dʰáwgdʰi`), and no word
that matches today depends on it: the corpus keeps both aspirates in PII and puts
the deaspiration in Indo-Aryan. The handbooks place Grassmann in Indo-Aryan rather
than PII (the position argued in Lubotsky 2018 on IIr. phonology — cited for the
position, not for a page, which we did not verify); the corpus is the evidence
that decided it here. The stage description says so, so the file no longer claims
a PII law it does not model.

## Measured and rejected

| candidate | gain | loss | killing number |
|---|---|---|---|
| **final *-r loss after *ā** (`final_r_loss`, `candidates/final_r_loss.yaml`) | +7 | 0 in iir-pro | it deletes the *r of Persian **pedār, mādar, dādār**, which the off-by-default `peo→pal` pathway law `r_stem_oblique` owns: 11 `test_web` tests fail and three matched Persian words stop matching. PII *pHtā́ is real (Skt. pitā́) but the *r of the Persian words is the oblique stem's; a sound law cannot choose the cell. Not shipped; the word needs a pathway, which is outside this task's write scope. |
| **palatalisation before *e** (`pánča`, `čatwā́ras`, `ǰátu`, `ǰʰánti`, `dʰáǰʰati`, `páčati`, `čárHati`) | +7 | −1 (`wr̥kíHs`) | it turns PIE `*ker` "make" into `*čar`, and the Old Persian record is 𐎣𐎠𐎼 **kāra-** (Skt. karóti): `test_web`'s script-layer match goes from `match` to `differs`, i.e. the law over-applies to a word whose *k is a lexical exception to the first palatalisation. The *i/*y* half ships; the *e* half is a proposal that needs the pathway layer. |
| **palatalisation before a stressed *i** (`palatal_k` with `(ˈ\|ˌ)?`) | 0 | −1 (`wr̥kíHs`) | 196 against 197: it buys nothing and costs the one word whose record keeps *k before stressed *í. The same *-íH- palatalises *g* in ǰíHwati, so the two records disagree; the narrower environment wins (PROGRAMME, "How a disagreement is settled" §2). |
| **ruki with *H in the left environment** (`candidates/ruki_after_H.yaml`) | +1 (`yúHš`) | −5 (`HbʰrúHs`, `Hstā́`, `Hsumánās`, `náHs`, `pántaHs`), −1 in ira-pro | a law may not name a segment its own corpus shows outside the environment. |
| **Brugmann's law without the *i restriction** | 0 | −4 (`Háwiš`, `Háǰʰiš`, `káti`, `pátiš`) | the wide environment is the shipped rule's superset; every word it adds is a word the record keeps short. |
| **devoicing of a voiced aspirate before *s** (`candidates/asp_devoice_s.yaml`) | +1 (`Hnā́kš`) | 0 | measured, not shipped: one word in this corpus cannot meet the review protocol's three-etymon bar, and a one-word law is the shape the programme forbids. Worth revisiting when a lexicon brings more `-Dʰs` words. |

## The honest ceiling

555 entries are tested. 358 remain misses, and they are not one kind of thing:

| kind | n | derivable from PIE by a sound law? |
|---|---:|---|
| the record writes a hyphen the laws never write (`a-`, `-kas`, `wan-`) | 45 | no — it is a bound form; the counter has its own `bound_form` column for it |
| the target adds material the recorded ancestor does not have (`dʰer > dʰárati`, `h₂ewg > Háwgas`) | 87 | no — that is derivation or inflection, and a sound law may not add a morpheme |
| stress position differs and nothing else | 7 | no — the accent is not a segment and no PII law moves it here |
| the letters differ | 219 | some, not most |

Inside the 219, the largest families are:

- **final *-r after *ā** (7): real, refused above (Persian).
- **`tˢ` in the record** (6): `Hátˢti`, `witˢtás`, `bʰinátˢti` — a notation of the
  dictionary this model does not read; not a sound law.
- **palatalisation before *e** (5): real, refused above (Old Persian kāra-).
- **`gʰ/ǰʰ` before a syllabic nasal** (4): `gʷʰn̥tós > *ǰʰatás` (Skt. hatá-).
  A palatalisation before a syllabic resonant is the next candidate, but it
  needs its own environment study and was not measured during this batch.
- ***k* before a stressed *í*** (3): the wr̥kíHs conflict above.
- **`*o` before a syllabic resonant** (3): `yákr̥`, `wásr̥`, `wáHr̥` keep short
  *a* where Brugmann's law would lengthen it; either the record has a different
  ablaut grade or the law needs a restriction we could not state without the
  counter-example `*h₁nómn̥ > *Hnā́ma`.
- **`*h₁` kept as *H in the record** (3): `dʰh₁tós > *dʰHtás` — the record keeps
  the laryngeal where this model writes the syllabic vowel *i*. A difference
  between two reconstruction conventions, not a sound change.

**How much of the 555 is not derivable from PIE at all.** This is a judgement,
and the defensible statement is this: at least **139** of the 555 cannot be
reached by a sound law on principle — the 45 bound forms and the 87 words whose
target contains material no recorded ancestor has (plus the 7 accent-only cases,
where the accent is not a segment any law here touches). Above that, **129** of
the misses have nothing but a bare **root** recorded as their ancestor, so their
ancestry links cannot carry a derivation at all: that is a W1 (lexicon) gap, not
a rule gap. The rest — some 90–100 words — differ by letters and are the real
remaining sound-law worklist; several of them (the rejected *e* and *-r* laws,
`tˢ`, `ʰ` notation) are not law-shaped at all.

Two honest caveats on the citations: the works are not in this workspace, so the
locators in the rule files are **chapter-level** ("the IIr. treatment of *s") and
no page number is invented; and the palatalisation and Grassmann decisions rest on
the corpus's own records, where two records disagree (`ǰíHwati` vs `wr̥kíHs`,
`čárHati` vs kāra-). In each case the narrower environment was shipped and the
wider one is recorded here with its numbers.

## Files

- `data/rules/ine-pro__iir-pro.yaml` — the transition: 4 rules added, 2
  environments narrowed, the palatal order fixed, `grassmann` removed, the one
  example that demonstrated nothing replaced (and the three palatal examples
  rewritten to the narrowed environment), and every rule's prose now says what it
  does not do.
- `tests/test_pii_rules.py` — 14 derived words from their own PIE ancestors, the
  ordering the model depends on, and the three rejected candidates pinned so a
  later edit has to fail a test before it can ship them.
- `proposals/2026-09-11/pii/candidates/*.yaml` — the rejected rules, with the
  numbers in the header comments.
- `data/sources.yaml` — **not touched**: every citation used was already there.
