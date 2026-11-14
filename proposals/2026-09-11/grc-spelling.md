# Greek: the writing layer (`data/spelling/grc.yaml`)

- **Status:** implemented and measured. Greek had no spelling file, so the
  coverage counter compared a phonemic string with a Greek-script headword and
  every Greek word was `exact = 0` no matter what the laws did
  (`proposals/2026-09-11/grc.md` §2). This is the other half: the laws write
  `patˈēr`, `kʰˈōra`, `tunkʰˈanō`, and the writing layer writes πατήρ, χώρα,
  τυγχάνω.
- **Measured:** **0 → 262 spelled** of 4,918 entries (0 → 8.5% of the 3,097
  tested). `exact` stays **0** by design: the writing layer is its own tier and
  never raises the historical figure. `explained` (exact + spelled + cited stem
  + pathway + identity) **331** of 4,918.
- **Session:** 2026-11-09, branch `main`, based on `530f571` (the 33-rule
  Greek file). Other batches were writing Gothic, Avestan and Middle Persian
  files in the same tree; none of their files is touched here.
- **Writes:** `data/spelling/grc.yaml` (new), `src/pie/greek.py` (new),
  `src/pie/transforms.py` (one transform + one registry line),
  `src/pie/spelling.py` (the per-language guard folds), `tools/coverage.py`
  (pass the language to the guard, 2 lines), `src/pie/service.py` (same, 2
  lines), `data/sources.yaml` (one appended entry, `allen-1987`),
  `tests/test_grc_spelling.py` (new), this report. No commit.
- **Gates:** `check-rules` **569 rules, 770 examples, 0 problems**;
  `unittest discover` **385 tests OK**; `node tests/test_ui_render.js` green.

## 1 · What the laws hand the writer

The last stage (`grk-pro → grc`) leaves a phonemic string in the engine's
notation: vowels `a e i o u` and `ā ē ī ō ū`, the aspirates `pʰ tʰ kʰ`, the
other consonants `p b t d k g m n r l s z`, stress as `ˈ` before the syllable,
an `/h/` as a literal `h`, and an initial voiceless rho as `hr` (or `r̥` where a
recorded form carries the syllabic notation). 3,422 candidate forms reach the
writer over the 3,105 tested entries.

## 2 · The letter table

| phoneme | letter | phoneme | letter | phoneme | letter |
|---|---|---|---|---|---|
| a ā | α | p | π | m | μ |
| e | ε | b | β | n | ν |
| ē | η | t | τ | r | ρ |
| i ī | ι | d | δ | l | λ |
| o | ο | k | κ | s | σ / ς finally |
| ō | ω | g | γ | z | ζ |
| u ū | υ | pʰ tʰ kʰ | φ θ χ | w | ϝ |

Citations: Smyth, *A Greek Grammar* (1920), §1 (the letters), with the sounds
of Allen, *Vox Graeca* (3rd ed. 1987).

## 3 · The five conventions that are not one-to-one

Each is a rule a scribe follows, not a rewrite of the form; each has an example
in the YAML that `check-rules` verifies, and the "worth" is the number of the
262 spelled words that the convention is needed for.

| convention | Smyth | worth |
|---|---|---:|
| a vowel-initial word takes the breathing (smooth, or rough where the form has /h/ or an initial ρ); over a diphthong it stands on the second vowel | §§9-10 | 83 (61 smooth, 22 rough) |
| the acute stands on the stressed nucleus, on the second vowel of a diphthong | §149 | 260 (16 on a diphthong) |
| a word ends in ς | §3 | 127 |
| ξ ψ ζ are one sign for /ks ps zd/ | §1 | 8 (ξ 7, ψ 1, ζ 0) |
| a nasal before a velar is written γ (γγ γκ γχ) | §1 | 4 |

The rough breathing is not decoration: `/h/` has no letter in Greek, so a form
that writes `h` and a headword that writes `ἁ` can only meet through this rule.
22 of the 263 carry a rough breathing and the writer produced every one; a
further 9 rough-breathing words are in the accent class below (§6), where the
breathing is right and only the accent is not. **No word in the corpus differs
from its written form by a breathing alone** (measured: 0 of 3,105).

## 4 · Measured, before and after

| | before | after |
|---|---:|---:|
| spelled (orthographic tier) | 0 | **262** |
| exact (laws only) | 0 | 0 |
| explained (all tiers) | 70 | **331** |
| near misses (worklist, distance ≤ len/4) | 54 | 3 |
| entries tested | 3,097 | 3,097 |

262 / 4,918 = 5.3% of the glossary, 8.5% of the tested set. The hard ceiling is
**3,030**: the reading guard needs the dictionary's own IPA, and 75 of the
3,105 tested entries record none (four of them are otherwise spelled exactly:
μισθός, κε, γραπτός, πληγή).

The number the *laws* are measured by, the dictionary's romanisation
(`proposals/2026-09-11/grc.md`), is 235. Of those 235:

| the writer's output | n |
|---|---:|
| writes the headword exactly | 168 |
| no stress token in the form, so no acute (μελισσα, κειρω, βαρυς …) | 41 |
| a bound form the dictionary writes with a hyphen (δι-, -ίζω, -τής) | 21 |
| a capitalised proper noun (Ζεύς, Χριστός) | 2 |
| a clitic, which Greek writes without an accent (ἐν, τις, πω) | 3 |

## 5 · The 100 words the script wins and the romanisation cannot

Of the **263** forms the writer produces (the counter reports 262: the one
word only the full ancestor reader reaches is κέρας, §9.1), **163** also match
the dictionary's romanisation. So **100 words are reached only through the
script**. The transliteration writes θ φ χ as `th ph kh`, ξ as `x`,
and marks a short vowel with a breve (ἀνήρ *ā̆nḗr*); one Greek letter is one
symbol.

| why the romanisation comparison could not see it | n |
|---|---:|
| θ φ χ are one letter | 71 |
| ξ ψ are one letter | 7 |
| the transliteration writes a breve (ă ĭ) | 3 |
| other (ῥ written rh, ει under the accent, …) | 19 |

This is the part of the Greek work that only a writing layer could have won;
the laws had already produced the right phonemes.

## 6 · The accent: 92 words the layer cannot write, and what a quantity layer needs

The accent the engine states is stress, and Greek writes stress as the acute.
A circumflex and a grave are different accents, not different spellings of the
acute, and the engine's phonology does not model which of the three falls (that
needs Attic quantity and the ablaut/sandhi history). So the writer writes an
acute and nothing else, and a headword written with a circumflex or a grave is
left a miss rather than guessed.

Accents in the 3,105 tested headwords: **acute 2,727, circumflex 277, grave 0,
none 101**.

Words whose letters and breathing are right and only the accent is not: **92**.

| the form | the headword | n |
|---|---|---:|
| no stress token at all | acute | 48 |
| no stress token at all | circumflex | 6 |
| stress on another vowel | acute | 9 |
| stress on another vowel | circumflex | 26 |
| stress where the headword writes none (a clitic) | none | 3 |

Two different layers would win these, and neither is a spelling convention:

- **a stress-placement layer** for the 48: the recorded ancestor carries no
  stress and no law adds one (τυγχάνω ← `tunkʰanō`, χαίρω ← `kʰairō`). Greek
  accentuation is largely predictable (recessive in verbs, the limitation law
  in nouns, Smyth §§149-180), but it is morphology, not orthography.
- **a quantity layer** for the 32 circumflex words: the acute is the right
  place only if the vowel is short; πνεῦμα and εἶδος are written with a
  circumflex because the stressed vowel is long and the ultima short. The
  writer would need the vowel lengths the laws already carry in part (`ē ō`
  are long; `a i u` are ambiguous) and Smyth's rules on the penult and ultima.

The 3 clitics (ἐν, τις, πω) are a lexical property: Greek writes them without
an accent, and no phonemic form can say that a word is enclitic.

## 7 · The reading guard: four folds, declared per language

A spelling is only counted when `spelling.plausible()` accepts the phonemes
behind it against the dictionary's own IPA. Four things the two sides write
differently made it refuse a spelling whose letters are right:

| the form | the IPA | n |
|---|---|---:|
| `ei` `ou` (the long close vowels, written as digraphs) | `eː` `uː` | 13 |
| `n` before a velar | `ŋ` | 5 |
| `hr` (from *sr-, *sw-) | `r̥` (the voiceless rho) | 4 |
| `z` (the letter ζ) | `zd` / `dz` | 4 |

The guard's job (refusing two wrong vowels that concatenate into the right
letters) is unchanged, and the folds must not leak into other languages, so
they are declared in the language's own spelling file under `guard:` and
applied to **both** sides of the comparison (`spelling.reading_folds`). The two
sides then still have to agree on the consonant skeleton and the number of
nuclei. Worth: **32 words** (262 with the folds, 230 without). The alternative
would have been a global fold of ŋ→n, which is wrong for Sanskrit, where ŋ is a
phoneme of its own.

## 8 · What the writer cannot reach, and why it should not

| class | entries | example |
|---|---:|---|
| every derivable form keeps a laryngeal `H` | 103 | σκύλος ← `skeH`; φύσις ← `pʰuH` |
| every derivable form keeps an unresolved glide `y` | 28 | ἀλλά ← `ˈalyos`; Ζεύς ← `dyˈēs` |
| every derivable form keeps a syllabic resonant | 8 | λύκος ← `ˈl̥pos` |
| the headword is capitalised (a proper noun) | 126 | Ζεύς, Χριστός |
| the headword is a bound form with a hyphen | 117 | -ίζω, δι-, ἡμι- |
| the headword is not written in Greek letters | 119 | Cypriot 𐠐𐠞𐠩𐠪𐠵, Latin |
| the headword carries a diaeresis (ϊ ϋ) | 22 | — |
| the headword is written with digamma ϝ | 3 | — |

None of these is a spelling convention: the first three are gaps in the laws
(a laryngeal loss, a glide law, a syllabic-resonant rule in the earlier
transition), capitalisation is a fact about the word being a name, and a
hyphen is the dictionary marking a bound morpheme (14 of the 117 would match if
the hyphen were simply dropped; the laws never write one). Keeping the
notation visible is what makes a wrong spelling look wrong.

## 9 · Bugs found (not fixed)

1. **`tools/coverage.py` reads ancestors with a stale copy of the reader.**
   Its own `ancestor_starts` iterates `entry["anc"]` rows as
   `(lang, word, rel)`, but Wiktionary also stores a row as
   `[':inh', 'grk-pro:*kérats>>', 'root']`, where the relation is the first
   column and the language is the prefix of the second. `service.ancestor_starts`
   reads those through `_ancestry_triples` (and `_phonological_form` for a
   script headword with a recorded reading); coverage does not. Measured over
   the whole corpus: **1,234 entries have an ancestor that only the service
   reader finds** (English 344, Sanskrit 177, Persian 97, Latin 90 …). In Greek
   it is 24, and one of them is spelled: κέρας ← grk-pro *kérats gives κέρας,
   which is why this report says **262** where the full reader says **263**.
   Not patched here: the counter is shared with three other workstreams whose
   reports quote its numbers, and changing it mid-batch would silently move
   every one of them.
2. **A dictionary label reaches the derivation.** ποῦ records its ancestor as
   `*kʷís#Determiner`; `normalise_etymon` strips `*`, brackets and hyphens but
   not the `#` label, so the form derived is `tˈis#Determiner` and no letter
   table can write it. One line in `normalise_etymon` (`split("#", 1)[0]`) would
   fix it for every language; not done here for the same reason as (1).
3. **A prose ancestor.** οὗ records
   `*hwe*ϝ̔έ (*whé), representing the accusative case>`; nothing in the pipeline
   rejects a value that is a sentence, so the derivation starts from a string
   with Greek letters and commas in it.
4. **Laryngeals survive into Greek** — 103 entries have no candidate without
   `H` (σκύλος, φύσις, ἰχθύς, πρῶτος). The Greek transition has no laryngeal
   loss, and the Sanskrit work moved its own loss to `inc-pro → sa`, so the
   earlier `ine-pro → grk-pro` stage is where it belongs.
5. **A glide survives** — 28 entries (ἀλλά ← `*h₂élyos`, Ζεύς ← `*dyḗws`); the
   palatal rules cover *ť *ď *ň *ľ *ř but not a bare *y after a consonant.
6. **No syllabic *l̥** in `ine-pro → grk-pro` (μ, ν, ρ exist), so λύκος
   reaches the writer as `ˈl̥pos`.

## 10 · Tried, measured, removed

- **The iota subscript** (ᾳ ῃ ῳ for `āi ēi ōi`): won **0** words. Worse, the law
  `long_a_to_eta` turns *ā into ē, so `*āi` arrives as `ēi` and the rule would
  have written ῃ for αἷμα. Removed.
- **Diaeresis** on a stressed vowel after another vowel: 0 of the 22
  diaeresis headwords is otherwise reachable, and the phonemic form carries no
  syllable boundary to decide hiatus from a diphthong. Not added.
- **Capitals**: 126 headwords are capitalised and exactly **1** would match if
  case were ignored; the phonemic form cannot say that a word is a name.
- **Writing the smooth breathing on `r`** (as if every ρ were ῥ): rejected —
  Smyth §10 gives the rough breathing to an *initial* ρ only, and the rule as
  written already reaches all 6 initial-rho words in the set.

## 11 · Reproduce

```bash
PYTHONPATH=src python3 -m pie.cli check-rules          # 569 rules, 770 examples, 0 problems
PYTHONPATH=src python3 -m unittest discover -s tests -q   # 385 tests, OK
node tests/test_ui_render.js                              # green
PYTHONPATH=src python3 tools/coverage.py --langs grc --limit 0 --out /tmp/cov-grc.json
# grc: exact 0, orthographic 262, identity 70, explained 331 of 4,918
PYTHONPATH=src python3 -m pie.cli spell patˈēr --lang grc     # πατήρ
```
