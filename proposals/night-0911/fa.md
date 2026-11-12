# Persian (`fa`) gets an orthographic layer

**Artefact.** `data/spelling/fa.yaml` — 33 conventions, tier `orthographic`, no
sound law touched.
**Status.** implemented and measured; review questions answered in §7.
**Author.** 2026-11-09. Commit `083dfe5`, branch `main`.

## 1 · The claim

New Persian writes the phonemic output of `pal → fa` in the Perso-Arabic abjad.
That script is a consonant alphabet: every consonant phoneme has one letter, the
long vowels have the three letters ا ی و, and the short vowels are **not written**
— except in two positions, word-initially (where a vowel needs a seat and gets
ا) and word-finally (where `-a`/`-e` are written ه). Stated as conventions, each
applies to any word, not to the words in the glossary:

* `/p b t d k g č ǰ f v s z š ž x ɣ h m n r l/` → `پ ب ت د ک گ چ ج ف و س ز ش ژ خ غ ه م ن ر ل`;
* `/y w/` → `ی و` (the same two letters the script uses for /ī/ and /ū/);
* `/ā ī ū/` → `ا ی و`, but word-initially `/ā/` → `آ`, `/ī/` → `ای`, `/ū/` → `او`;
* `/a e o i u/` are unwritten, but a word-initial short vowel is carried by `ا`
  and word-final `/-a -e/` are written `ه`;
* stress is not written.

Nothing in the file is keyed to a lexeme, and no rule names a word.

## 2 · What the pipeline actually hands the layer

`pal__fa` ends with `stress_not_written` (order 90), so the form the layer sees
carries no accent token. The segment inventory of the 1,634 tested Persian words,
counted on the *closest* ancestor derivation that `coverage.py` selects:

| segment | n | segment | n | segment | n | segment | n |
|---|---:|---|---:|---|---:|---|---:|
| a | 790 | ā | 290 | r | 455 | d | 390 |
| s | 234 | n | 229 | b | 220 | y | 187 |
| h | 167 | p | 167 | g | 154 | t | 149 |
| k | 142 | m | 136 | š | 132 | e | 131 |
| ū | 128 | w | 118 | o | 117 | ī | 104 |
| f | 29 | č | 28 | x | 28 | z | 17 |
| l | 15 | ʾ | 14 | ǰ | 13 | ž, v, c | 6, 5, 6 |

The tail of that list matters for §5: when the nearest recorded ancestor is a
Pahlavi or Manichaean *transliteration* (`ʾwl` for هل, `bʾčʾl` for بازار, even the
Aramaic ideogram `TYNA` for گل) or a proto-form that only partly reached Persian
(`dʰ`, `r̥`), the derivation ends in letters no Persian convention can map.

On the other side, the recorded word is the dictionary's Perso-Arabic headword,
normally unvocalised — of 5,555 words, 1 carries ḥarakāt, 52 use tatweel, 71
contain a ZWNJ and 92 are multi-word. The comparison is therefore letter for
letter against a spelling with no short-vowel marks, which is exactly what the
abjad writes.

## 3 · Conventions and citations

The whole file is one ruleset applied after `pal__fa`. Order is what makes the
positional rules possible: the word-initial and word-final rules fire while the
form is still phonemic (`order` 20–30), the context-free letter table follows
(40–50), and the deletion of the unwritten short vowels comes last (60).

| order | rule | convention |
|---|---|---|
| 10 | `drop_stress` | stress is not written |
| 20 | `initial_long_a` | word-initial `/ā/` = `آ` (آب, آسمان) |
| 21 | `initial_long_i` | word-initial `/ī/` = `ای` (ایران) |
| 22 | `initial_long_u` | word-initial `/ū/` = `او` (او) |
| 23 | `initial_short_vowel` | a word-initial short vowel is carried by `ا` (ابر, اسم, امید) |
| 30 | `final_short_a` | word-final `/-a -e/` = `ه` (خانه, گربه, نامه) |
| 40–42 | `long_a`, `long_i`, `long_u` | `/ā ī ū/` = `ا ی و` |
| 50 | 22 letter rules | one letter per consonant phoneme |
| 60 | `short_vowels` | `/a e o i u/` are not written |

**Sources** (both already registered in `data/sources.yaml`; no new key was
added, and the write scope allowed no other file):

* `windfuhr-2009` — Windfuhr (ed.), *The Iranian Languages* (Routledge 2009);
  locator: the Persian chapter (Windfuhr & Perry, "Persian and Tajik"), §2
  "Phonology and orthography" — the Perso-Arabic letter inventory (consonants,
  the three long-vowel letters) and the statement that the short vowels are not
  written.
* `sadeghi-1978` — Sadeghi, *Tārix-e zabān-e fārsi*; locator: the chapter on the
  Arabic-Persian alphabet (letter→phoneme table) and the orthography section on
  the writing of the vowels (initial seat, final `-a`/`-e` as ه).

The locators are chapter-and-section, not page numbers: no copy of either work is
on this machine, and inventing a page would be worse than naming the section.
Each rule carries its `references`; `pie check-rules` verifies every example
against the whole file (`spelling.check`), because one convention is a step of a
longer mapping.

Examples are drawn from different etyma and include words the file must not
touch — the letter rules are exercised by پدر, باد, تو, دادار, کار, گوش, چه, جان,
فرد, وزن, سر, زیر, شیر, ژرف, خر, غم, ماه, مرد, نام, روز, لب, گاو, یار, and the
vowel rules by ابر, اسم, امید, خانه, گربه, نامه, آب, آسمان.

## 4 · Measured before and after

`tools/coverage.py --langs fa --limit 0` (full corpus, no sampling):

| measure | before (`fa.yaml` absent) | after |
|---|---:|---:|
| glossary | 5,555 | 5,555 |
| identified (a recorded ancestor) | 1,634 | 1,634 |
| PIE-linked | 806 | 806 |
| tested | 1,634 | 1,634 |
| **exact** (sound laws) | **0** | **0** |
| **orthographic** | **0** | **57** |
| exact + orthographic | 0 | 57 |
| **orth_rate** | **0.0000 %** | **1.0261 %** |

The historical number is untouched — as it must be: a writing convention is
scored in its own column and never added to `exact`.

Measured 2026-11-09 01:05 (Europe/Berlin) on `083dfe5` plus the working tree's
uncommitted edits. Another workstream was editing the `iir-pro → ira-pro` law file
at the same time; that transition is upstream of `pal → fa`, so it can move the
last digit of the diagnostic counts below (it moved one word from 98 to 97 while
this file was being written). The orthographic figure was re-measured after that
edit and did not change: **0 exact, 57 orthographic**.

The probe agrees with the published number by construction (it reproduces
`coverage.py`'s choice of the closest ancestor derivation) and adds the
diagnostics coverage cannot show:

| diagnostic | n |
|---|---:|
| the layer spells the word exactly | 97 |
| of those, counted after `spelling.plausible` | 57 |
| of those, rejected by `spelling.plausible` | 32 |
| of those, the closest derivation fired no law (not counted) | 8 |

The 32 rejections are the guard doing its job — with one instrumentation
wrinkle worth recording. 8 words have no IPA at all (so `plausible` is false by
definition). 12 are rejected only by **notation**: the guard compares segments
but does not fold the philological letters the model writes onto the ones the
dictionary's IPA uses — `č š ž ǰ` against `t͡ʃ ʃ ʒ d͡ʒ` and `ā ī ū` against
`aː iː uː` — so چشم (*čašm* for /ˈt͡ʃaʃm/) and شیر (*šīr* for /ˈʃiːr/) are
rightly spelled and wrongly refused. With those folded (`č→t͡ʃ`, `š→ʃ`,
`ā→aː` …) they pass; they are counted here as misses because the published
number uses the guard as it stands, and the folding belongs to W7, not to the
spelling file. The remaining 12 are genuine phoneme disagreements (`gūz` for
/ˈɡawz/, `grān` for /ɡi.ˈraːn/, `srāy` for /sa.ˈraːj/), i.e. the sound laws'
vowel approximation, exactly what the guard exists to keep out.

Ablation — counted words with one rule switched off (`--disable`):

| rule off | counted | gain |
|---|---:|---:|
| (none) | 57 | — |
| `short_vowels` | 28 | +29 |
| `long_a` | 44 | +13 |
| `long_i` | 47 | +10 |
| `final_short_a` | 48 | +9 |
| `long_u` | 51 | +6 |
| `initial_short_vowel` | 53 | +4 |
| `initial_long_a` | 57 | 0 |

`initial_long_a` gains nothing on this corpus (no counted word begins with ā) but
states a convention that is true and is verified by آب and آسمان; it stays, with
the zero gain reported rather than hidden.

Integration: `service.word('fa', 'نام')['hierarchy']['result']['written']` is
`نام`, and a miss such as زبان exposes no `written` — the read model shows the
written form only where the conventions land on the recorded word.

## 5 · What still misses, and why no convention can fix it

1,537 of 1,634 tested words miss. They fall into three groups:

| group | n | what it is |
|---|---:|---|
| nearest derivation still in another script | 253 | the recorded ancestor is written in Pahlavi, Manichaean or Old Persian cuneiform, so the derivation prints signs, not phonemes — موز ← 𐭬𐭅𐭆, نه ← 𐎴𐎺, شیر ← 𐫢𐫃𐫡, پسر ← 𐎱𐎢𐏂 |
| nearest derivation kept non-phonemic Latin | 176 | uppercase letters and `ʾ ʰ ğ c` from a transliterated ancestor — هل ← `ʾwl`, بازار ← `bʾčʾl`, گل ← `TYNA`, مهندس ← `handʾc` |
| ordinary spelling misses | 1,108 | the phonemic form itself differs from the word |

The ordinary misses, as character pairs (spelled guess → recorded word):

| signature | n | signature | n | signature | n |
|---|---:|---|---:|---|---:|
| `∅→ن` | 273 | `∅→ا` | 202 | `∅→ی` | 149 |
| `∅→د` | 125 | `∅→ه` | 116 | `∅→ر` | 97 |
| `∅→ت` | 89 | `ا→∅` | 65 | `∅→و` | 65 |
| `∅→م` | 55 | `∅→ش` | 50 | `∅→س` | 49 |
| `د→ز` | 39 | `∅→ز` | 36 | `د→∅` | 35 |

`∅→X` means the phonemic form lacks a segment the Persian word has: 714 of the
1,108 guesses are shorter than the word. That is the sound laws' work, not the
orthography's — no letter choice adds a consonant the phonemes do not contain.
The substitutions and deletions (`د→ز`, `∅→ز`, `د→∅`) are the same story: the
wrong consonant, not the wrong letter for a consonant.

The specific groups the task asked about:

* **Arabic ظ ض ط ص (and ث ح ق ع ة).** 1,476 of the 5,555 glossary words contain
  one of these letters, but only **30 of the 1,634 identified** words do —
  Arabic loans are borrowed from Arabic, so no ancestor in the chain exists for
  them and they never reach the comparison. Among the ordinary misses **0** would
  be fixed by choosing an Arabic letter at the same position (same length, only
  Arabic-only letters differing), and 16 misses contain one at all. The script
  writes the same /z/ as ز, ذ, ض or ظ; that choice is lexical and stays a miss,
  exactly like German ⟨v⟩ vs ⟨w⟩.
* **⟨و⟩ for /v/ vs /u/.** Ambiguous when *reading* the script, deterministic
  when *writing*: /v/, /w/ and /u/ all map to و. Reading it back is the harder
  problem, and it is not this layer's job.
* **100 words whose derivation ends in a long vowel the word does not have**
  (پاد ← پا, گوشت ← گوشتا, مادر ← مادا). This is the residual of the deliberate
  decision not to shorten every final `-ā` (`docs/DECISIONS.md`, commit
  `180af5c`); the law question was answered there, and it is not a spelling
  convention.
* **127 words ending in ه where the derivation ends in a consonant** (پروانه,
  انوشه, میوه): the final `-e` is not in the phonemic form at all, so there is
  nothing for a convention to write.
* **خوا- spellings.** 7 missing words begin with خوا (خواب, خواهر), where Persian
  writes a silent و. /xā/ is also written خا (خاک, خام), so the choice depends on
  the word's history, not its phonemes: it cannot be a convention (the test —
  would it apply to a word that does not exist yet? — fails). Left as a miss.

## 6 · Reproduce

```bash
# the probe: before (no layer), a candidate, and the installed layer
PYTHONPATH=src python3 proposals/night-0911/fa_probe.py --spelling /dev/null
PYTHONPATH=src python3 proposals/night-0911/fa_probe.py --spelling data/spelling/fa.yaml
PYTHONPATH=src python3 proposals/night-0911/fa_probe.py --spelling data/spelling/fa.yaml --disable short_vowels

# the published number (writes /tmp, never the repo reports)
PYTHONPATH=src python3 tools/coverage.py --langs fa --limit 0 --out /tmp/cov_fa.json

# the layer by hand, and the gates
PYTHONPATH=src python3 -m pie.cli spell --lang fa nām        # nām → نام
PYTHONPATH=src python3 -m pie.cli spell --lang fa "xāne"     # xāne → خانه
PYTHONPATH=src python3 -m pie.cli check-rules                # 0 problems, spelling files fa included
PYTHONPATH=src python3 -m unittest discover -s tests -q      # 317 tests, OK
```

## 7 · Review questions (`docs/REVIEW.md`)

1. **Is the claim stated?** Yes: one sentence per rule, no "sometimes"; the two
   positional rules are named by position, not by word.
2. **Is the evidence independent?** Every example is a different etymon, and the
   letter table is exercised by words the vowel rules do not touch.
3. **Does the rule over-apply?** Measured above: no exact match was created, the
   historical column is unchanged, and the counted spellings are additionally
   filtered by `spelling.plausible`. The one rule that gains nothing
   (`initial_long_a`) is reported as such.
4. **Is the tier honest?** Every rule carries `tier: orthographic`; nothing here
   claims a sound change, and no rule was added to `data/rules/`.
5. **Is the artefact shaped right?** One spelling file, its probe, this
   proposal. No generated report was rewritten (`coverage.py` was run with
   `--langs`, which never publishes).

## 8 · A law defect the layer exposed (reported, not fixed)

`peo__pal:final_h_loss` deletes every word-final `/h/` after a short vowel. The
derivation of ماه shows what that costs:

```
PII *mā́Has  → final_s_to_h          *māHah
             → laryngeal_lengthening *mˈāah
             → final_h_loss          *mˈāa       (h after short a, word-final)
             → final_vowel_loss      *mˈā
pal → fa                                 mā       ≠ ماه (māh)
```

Persian keeps that h. It is not the Old Persian nominative ending `-ah` that the
law was written for (OP aspa(h) > MP asp), but the stem-final *h < PII *s, which
Middle and New Persian preserve: MP māh, NP ماه. On the surface both are `Vh#`,
so **no phonological environment can separate them**; a reconditioning such as
"after ā.a" would describe two words, not a class. The minimal honest fix is
morphological: mark the loss as an ending (`paradigm` tier / W5) so it applies
only to the case ending, not to a stem-final h.

Measured population: 9 entries (7 distinct words) end in ه exactly where the
chain applied `final_h_loss` — ماه, جیوه, دشنه, سگرنه and the -e nouns مرده,
باده, روده, whose ending is lost by the same two rules for a different reason. The defect is therefore small and
recorded, not repaired — repairing it belongs to the paradigms stream, not to a
spelling file.
