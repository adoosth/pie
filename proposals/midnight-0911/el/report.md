# Modern Greek from Ancient Greek — night of 2026-11-09

**Status:** implemented in `data/rules/grc__el.yaml` (31 laws: 22 sound laws, 9
notation/orthographic normalisations) and `data/spelling/el.yaml` (a monotonic
letter table), measured, gates green.
**Scope (written):** only `grc → el`, its spelling layer, `tests/test_midnight_el.py`
and this proposal directory. No `src/`, no lexicon, no other rule or spelling
file, no doc, no `data/coverage.json`; nothing committed.
**Chain:** `ine-pro → grk-pro → grc → el`.

**Measured with:**

```bash
PYTHONPATH=src python3 tools/coverage.py --langs el --limit 0 --out /tmp/coverage_el.json
PYTHONPATH=src python3 tools/council.py --stage grc --to el --rules <candidate>.yaml --layers exact,orthographic,identity,script
PYTHONPATH=src python3 tools/whatif.py --to el --layers exact,orthographic,identity,bound --drop <law>
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q ; node tests/test_ui_render.js
```

## 1. Inventory: why the number was 0, and what is fixable in scope

The `el` headwords are Greek script, but the laws carry a Latin phonemic
notation; the two meet only through the orthographic layer (a law output is
spelled with `data/spelling/el.yaml` and compared to the headword). Before this
session there was **no** `data/spelling/el.yaml`, so `spelling.applies('el')`
was false and every law-carrying word was unreachable: `el` could only score
`identity` (a word whose path needs no law at all). That is the 109 explained
the task names.

The second, larger reason is a data gap. Of the 5,082 tested entries:

| | entries |
|---|---:|
| glossed headwords | 10,458 |
| with a recorded ancestor at a modelled stage (`identified`) | 5,083 |
| tested (reconstructions excluded) | 5,082 |
| **grc ancestor has a machine-readable (Latin) reading** | **1,219** |
| **grc ancestor is Greek-script only — absent from `data/lexicon/grc.jsonl.gz`** | **3,802** |
| no `grc` start at all (only `ine-pro`/`grk-pro` stubs) | 61 |

`_phonological_form('grc', word)` (`src/pie/service.py:1151`) returns a
recorded *reading* only when the ancestor is found in the `grc` glossary; when
it is not, it returns the Greek letters **unchanged**, and no sound law can
match `σ`, `ι`, `ς` as segments. So 3,802 of 5,082 words are unreachable by
construction, not missing a law. Only 1,219 words can be reached at all, and
the orthographic layer already explains 270 of them (22%). Every law below was
written against that reachable subset; none pretends to touch the other 3,802.

## 2. Before / after

`coverage.py` (layers are its own columns; `exact` is 0 for a script language by
definition — the laws never produce Greek letters, the spelling layer does):

| layer | before | after |
|---|---:|---:|
| exact (laws, character for character) | 0 | 0 |
| **orthographic** (laws + `data/spelling/el.yaml`) | 0 | **270** |
| identity (path needs no law) | 792 | 782 |
| bound form | 26 | 26 |
| joined formation (counted apart) | 190 | 190 |
| **explained** (`coverage.py` union) | **109** | **369** |
| **explained** (union of exact+orth+identity+bound, `whatif`) | 818 | **1,078** |
| of 5,082 tested | 2.1% | 7.3% |
| of the 1,219 reachable | — | 22% orthographic |

The two "explained" rows differ by a `coverage.py` accounting quirk: a word that
is explained only through `identity`, and whose output is *identical* to the
headword, hits `if best_distance == 0: continue` before `explained += 1`, so it
is reported in `identity` but not folded into `explained`. The `whatif` union
(the honest total) is 818 → 1,078, **+260 explained**, made of 270 orthographic
words minus 10 words that were `identity` (no law fired) and now have a law fire
and spell correctly. All 270 orthographic words rest on `established` laws; the
tier breakdown is below.

## 3. The laws — measured one at a time

Every count is the union layer (`exact,orthographic,identity,bound`) with that
law withdrawn, over the full corpus (one process, `tools/whatif.exact_words`).
"carried" is what the law adds; "breaks" is what a withdrawal would *gain* —
i.e. a word the law turned away. Two of the three "breaks" columns are an
artifact of the `identity` layer treating the record's own transliteration as a
pre-existing match (see §3.1); one is real (`final_n_loss`).

| law | tier | gained | lost | verdict | citation / change |
|---|---|---:|---:|---|---|
| `ph_digraph` | orthographic | 14 | 0 | ACCEPT | `ph` = one segment *pʰ* (transliteration, Smyth §1) |
| `th_digraph` | orthographic | 28 | 3† | ACCEPT † | `th` = *tʰ* |
| `kh_digraph` | orthographic | 19 | 0 | ACCEPT | `kh` = *kʰ* |
| `xi_digraph` | orthographic | 7 | 0 | ACCEPT | `x` = ξ = */ks/* |
| `circumflex_a_to_tonos` | orthographic | 1 | 0 | ACCEPT | ᾶ > ά (Horrocks 175-6) |
| `circumflex_e_to_tonos` | orthographic | 4 | 0 | ACCEPT | ῆ > ή |
| `circumflex_i_to_tonos` | orthographic | 2 | 0 | ACCEPT | ῖ/οἶ > ί |
| `circumflex_o_to_tonos` | orthographic | 6 | 0 | ACCEPT | ῶ > ώ |
| `circumflex_u_to_tonos` | orthographic | 2 | 0 | ACCEPT | ῦ > ύ |
| `iota_subscript_loss` | orthographic | 0 | 0 | ACCEPT (fires 0) | the iota subscript is not written (Horrocks 175-6) |
| `h_loss_initial` | established | 26 | 0 | ACCEPT | rough breathing lost (Horrocks 168-70; Browning 60-2) |
| `h_loss_after_rho` | established | 2 | 0 | ACCEPT | ῥ > ρ |
| `loss_of_long_quantity` | established | 3 | 0 | ACCEPT | *ā *ī *ū shorten (Horrocks 169-71) |
| `loss_of_long_i` | established | 4 | 0 | ACCEPT | *ī > i |
| `loss_of_long_u` | established | 2 | 0 | ACCEPT | *ū > u |
| `loss_of_breve_a` | established | 84 | 0 | ACCEPT | the breve is quantity only |
| `loss_of_breve_i` | established | 33 | 0 | ACCEPT | ” |
| `loss_of_breve_u` | established | 27 | 0 | ACCEPT | ” |
| `ph_to_f` | established | 16 | 0 | ACCEPT | *pʰ > f (Horrocks 168-71) |
| `th_to_theta` | established | 38 | 0 | ACCEPT | *tʰ > θ |
| `kh_to_chi` | established | 22 | 0 | ACCEPT | *kʰ > χ |
| `au_to_af` | established | 3 | 0 | ACCEPT | *au > af / _ voiceless (Horrocks 168-9; Holton 1.2) |
| `au_to_av` | established | 5 | 0 | ACCEPT | *au > av elsewhere |
| `eu_to_ef` | established | 1 | 0 | ACCEPT | *eu > ef / _ voiceless |
| `eu_to_ev` | established | 2 | 0 | ACCEPT | *eu > ev elsewhere |
| `b_to_v` | established | 18 | 0 | ACCEPT | β > v (Horrocks 168-71) |
| `d_to_delta` | established | 21 | 4† | ACCEPT † | δ > ð |
| `g_to_gamma` | established | 32 | 0 | ACCEPT | γ > ɣ (palatal ʝ / _ front) |
| `w_loss_initial` | established | 0 | 0 | ACCEPT (fires 0) | digamma lost word-initially (Smyth §24) — fires 0, the corpus writes no digamma |
| `pt_to_ft_initial` | established | 1 | 0 | ACCEPT | initial πτ > φτ (Horrocks 171; Browning 66) |
| `final_n_loss` | established | 24 | 2‡ | ACCEPT ‡ | final *-n lost (Horrocks 176-8) |

Sums are not a partition: the laws overlap and several fire in the same word.

**† identity-layer artifact.** With `th_digraph` or `d_to_delta` withdrawn, the
words θεσμός/θετός/πορθμός and ανάδρομος/δεινός/δεσμός/πέρδομαι stop firing any
law, so `identity` compares the record's own transliteration (`thesmós` …) to
itself and "counts" them — a match that demonstrates no reconstruction. With
the law present the derivation is correct (`θesmˈos` spells θεσμός), but these
entries carry no `ipa`, so the `plausible` guard cannot confirm the reading and
the word is left an honest miss. The laws are not wrong; the identity column is
generous. This is why the council `identity` layer can report a "loss" for a
correct law.

**‡ real over-application.** `final_n_loss` carries 24 words but turns away two
that keep their -n: **αμήν** (/aˈmin/) and **πύον** (/ˈpion/). Final -n is lost
by rule but retained in a lexical set (function words δεν/μην/σαν/τον/την and
learned words). The retention is not a phonological environment, so it cannot be
written as a segment `env`; the two words stay misses and the law is a net +22.

### 3.1 Notation vs history

The itacism (*ē *ei *oi *y > /i/), the loss of vowel quantity for η/ω, the loss
of gemination (ἄλλος keeps λλ) and the loss of the dative and infinitive are
stated in the stage prose, not as rewrites. Rewriting *ē > i would make the
modern spelling unreachable: the letter η would be spelled ι. The corpus shows
that the merged vowels keep their inherited letters (η, υ, ει, οι), so the
honest treatment is prose + a spelling table, and the laws do the changes whose
letters actually moved. See §7 for the one place this costs words.

## 4. Council: candidate laws heard and rejected

Each was measured on the whole subtree with the mandated layers
`exact,orthographic,identity,script`; the council baseline for `el` is 986.

| candidate | result | losing list / reason |
|---|---|---|
| `final_ion_to_i` (-ιον > -ι) | **REJECT** | 986 → 985, loses **κρανίο** (κρανίον keeps its -ο) — the synizesis is lexical, not general |
| `final_eus_to_eas` (-εύς > -έας) | **REJECT** | 986 → 986, gains nothing (the ancestors are unreadable or already explained) |
| `kt_to_xt` (κτ > χτ) | **REJECT** | 986 → 984, gains χτίζω but loses **άτρακτος, μυκτήρ, οκτώ** — the change is learned/colloquial, not systematic |
| `pt_to_ft` (medial πτ > φτ) | **REJECT** | 986 → 984, loses **επτά, κάμπτω** (standard επτά keeps πτ) |

No candidate passes "nothing loses and something gains", so none was added; the
files are kept here as the record of what was considered. The finding is real:
what Modern Greek still misses is not a broad sound law but (a) the 3,802
unreadable ancestors and (b) lexical/morphological one-offs (each suffix pattern
in the residue occurs in ≤4 words).

## 5. The spelling layer — `data/spelling/el.yaml`

A monotonic letter table, every rule `tier: orthographic` with a full-phonemic
example, and a `guard.equivalences` map that folds the IPA allophones the laws
write plainly (c:k, ɟ:g, ç:x, ʝ:ɣ, ʎ:l, ɲ:n, ɾ:r, χ:x, ŋ:n, nasal+stop
voicing, ɱ:m). It writes: the vowels and their tonos forms, every consonant,
the digraphs αυ/ευ (both voicing outcomes), γ for a nasal before a velar, ξ/ψ/ζ,
final ς, and it drops the engine's stress tokens (the tonos is the accent). Each
rule would apply to a word that does not exist yet — the REVIEW test for a
convention, not a lookup. No headword-specific spelling is written.

## 6. Residue: three words that still fail, and why

* **οστό** 'bone' ← ὀστέον. `οστέον` is not in the grc glossary, so the ancestor
  passes through as Greek letters and no law fires; the modern word also shows
  the Koine contraction -έον > -ό, which is a separate change. Unreadable
  ancestor + contraction = a miss (fixable only by §7 plus a contraction law).
* **θεσμός** 'institution' ← θεσμός. The laws derive `θesmˈos`, which spells
  θεσμός correctly, but the entry records **no IPA**, so the `plausible` guard
  cannot confirm the reading and the orthographic layer declines it. The
  letters are right; the evidence to count them is absent. (Same for θετός,
  πορθμός, ανάδρομος, δεινός, δεσμός, πέρδομαι.)
* **θεραπεία** 'therapy' ← θεραπεία. The laws give `θerapˈeia` → θεραπέια: the
  digraph ει is not rewritten (itacism is prose, §3.1), so the accent the laws
  place on the first ε lands on the wrong vowel. The letters agree except for
  the tonos; the stress shift (ancient on ει, modern on ί) is a change no law
  here states.

Also unreachable here: the 3,802 Greek-script-only ancestors (§1) and the 61
words whose only recorded start is `ine-pro`/`grk-pro`, above the `grc` rung.

## 7. Amendment — exact out-of-scope patch for the integrator

**`src/pie/service.py`, `_phonological_form`** (the 3,802-word gap). When the
ancestor is not in the `grc` glossary, the function returns the Greek letters
unchanged. Add a Greek letter→phoneme fallback so a script headword with no
glossary entry is still readable:

```python
# in _phonological_form, replace `if not entry: return word` with:
if not entry:
    from .translit import greek_reading   # a new table, below
    return detokenize(tokenize(greek_reading(word))) or word
```

with a small table (α a, β b, γ g, δ d, ε e, ζ z, η ē, θ tʰ, ι i, κ k, λ l,
μ m, ν n, ξ k s, ο o, π p, ρ r, σ/ς s, τ t, υ y, φ pʰ, χ kʰ, ψ p s, ω ō; the
breathings and accents mapped to h/ˈ/ ͂). A monkeypatched run of exactly this
(dictionary reading first, letter transliteration otherwise) measured
**orthographic ≈ 633, identity ≈ 334, explained ≈ 967** — versus 270/782/369
today. That patch needs `src/` and a committed tool; it is not in this scope.

**`data/sources.yaml`** has keys `horrocks-2010`, `smyth-1920`, `allen-1987` but
not Holton–Mackridge–Philippaki-Warburton 1997, Browning 1983 or Babiniotis, so
those are cited in the prose and the machine-checked `references` use
`horrocks-2010`/`smyth-1920`. Adding `holton-1997`, `browning-1983`,
`babiniotis-2002` (one line each) lets every rule carry its grammar in
`references` too.

## 8. Tests

`tests/test_midnight_el.py` — **20 tests**: the transition exists and is not
empty; every law states a tier and a known source and passes its own example;
the historical laws are `established` and the notation rules are `orthographic`;
the rough breathing is lost, the aspirates and voiced stops spirantise, the
αυ/ευ split follows the voicing, length is lost, final -n is lost but medial -n
is kept, initial πτ > φτ but medial πτ is not touched (the rejected candidate's
reason), itacism is not rewritten; the spelling layer writes η/υ with their
letters, both αυ/ευ outcomes, the tonos and final ς, and every convention
matches at most two segments (never a whole word); and two floors — the
readable-ancestor majority must not shrink and the orthographic layer must stay
≥ 260.

Gate results in the state left behind: `check-rules` — 32 rule files, 804 rules,
1,162 examples verified, 0 problems; `unittest discover -s tests -q` — OK (624
tests); `node tests/test_ui_render.js` — OK.
