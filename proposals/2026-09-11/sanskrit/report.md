# Sanskrit from Proto-Indo-Aryan — 2026-11-09

**Scope.** `inc-pro → sa` (`data/rules/inc-pro__sa.yaml`), the Sanskrit reading
guard (`data/spelling/sa.yaml`), and this directory. Nothing upstream was
touched. Every number below is reproducible with the command quoted beside it.

## The result

```
PYTHONPATH=src python3 tools/coverage.py --langs sa inc-pro --out /tmp/sa-night-after.json
```

| measure | before | after | Δ |
|---|---:|---:|---:|
| glossary rows | 4,724 | 4,724 | — |
| identified / tested | 3,937 / 3,935 | 3,937 / 3,935 | — |
| **exact (reconstructed)** | **0** | **0** | **0** |
| **spelled (orthographic)** | **280** | **465** | **+185** |
| **cited as stem (citation)** | **295** | **482** | **+187** |
| identity (no law fired) | 58 | 45 | −13 |
| **explained (all layers)** | **633** | **992** | **+359** |

`exact` stays 0 **by construction**, not by failure: every one of the 4,724
rows of the Sanskrit glossary has a Devanagari target, and the historical column
compares a phonemic string with the attested word character for character. A
phonemic string can never equal a Devanagari word, and bending the target into a
transliteration is exactly what the programme forbids. Sanskrit is therefore a
language whose honest numbers are *spelled* and *cited*, and that day's work is
measured there. (The same structural fact is why `tools/council.py` is silent at
its default `exact` layer for this language: it must be run with
`--layers exact,orthographic,cited` to hear anything.)

### Attribution (measured, not assumed)

| state | explained | orth | cited |
|---|---:|---:|---:|
| old laws, old spelling file | 633 | 280 | 295 |
| old laws, new spelling guard | 744 | 344 | 351 |
| new laws, old spelling file | 687 | 302 | 328 |
| **new laws, new spelling guard** | **992** | **465** | **482** |

The laws alone (+54) are worth little without the guard, because a Sanskrit
phonemic form is written with the dot-below letters the guard mis-reads. The
guard alone (+111) is worth little without the laws, because the phonemes it
lets through are still wrong. Together: +359.

### The laws are not paid for with a loss

```
PYTHONPATH=src python3 tools/council.py --stage inc-pro --to sa \
  --layers exact,orthographic,cited --drop ai_to_e --drop au_to_o \
  --drop ai_to_e_final --drop w_to_v_recorded \
  --drop n_to_retroflex_after_ruki --drop t_to_retroflex_after_sh
  sa  723 -> 551 (-172)  lost 172
```

Removing the six registered laws costs 172 words and gains none: each law pays
for itself, and `tests/test_sanskrit_batch.py::test_every_new_law_pays_for_itself`
re-measures it rule by rule (gain > 0, loss = 0 for every one).

## Laws added

| # | id | claim | tier | citation | words carried alone |
|---|---|---|---|---:|---:|
| 1 | `ai_to_e` | PIA *ai > Skt e, in both notations the corpus uses (`*daiwás`, `*daywás`) | established | Mayrhofer 1986, Lautlehre §§8–9; Whitney 1889 §22 | 85 (with 3) |
| 2 | `au_to_o` | PIA *au > Skt o (`*kapáwtas` > kapóta-, `*yawni` > yóni-) | established | Mayrhofer 1986 §§8–9; Whitney 1889 §22 | incl. in the 85 |
| 3 | `ai_to_e_final` | PIA *-ai > Skt -e at the word's edge (middle 3 sg. váste, jāyate) | established | Whitney 1889 §22, §735 | 38 |
| 4 | `w_to_v_recorded` | a recorded PIA *w is Sanskrit v (vádati, áśva-) | established | Whitney 1889 §50; Mayrhofer 1986 §6 | 43 |
| 5 | `n_to_retroflex_after_ruki` | n > ṇ after r, ṛ or ṣ **and before a vowel** (tṛṇá-, kṛṣṇá-, gṛṇā́ti) | established | Whitney 1889 §196 | 6 |
| 6 | `t_to_retroflex_after_sh` | t > ṭ after ṣ (piṣṭá-, uṣṭrá-, iṣṭá-) | established | Whitney 1889 §197 | 10 |

Two of the six needed a second statement of the *same* law because of the
corpus's notation, and the file says so where it does it:

- **The diphthong as a glide.** The records write PIA *ai, *au as `ay`, `aw`
  (`*daywás`, `*kapáwtas`), not as the two vowels the older rule matched. Rules
  1–2 were rewritten with an alternation on the second element, so one cited law
  covers both spellings; rule 3 exists because the pattern language cannot put
  the word edge `#` inside a group, so the word-final position is his own rule.
  Evidence that the environment is needed: Skt kanyā́ keeps its y (a glide
  opening the next syllable is not a diphthong), and the root अव् av- keeps its
  v.
- **Recorded PIA.** Rules 4–6 and the pre-existing `c_caron_to_c_recorded`
  family state the same developments for a word that enters the chain at
  Proto-Indo-Aryan; the file already had this convention, and the comment there
  is the argument.

## The reading guard (orthographic layer, no count in the historical column)

`data/spelling/sa.yaml` gained a `guard.equivalences` block. The guard is not a
sound law and not a spelling rule: it is the check that stops two wrong vowels
from concatenating into the right letters. It compares the **consonant skeleton
and syllable count** of the laws' form with the dictionary's own IPA, so it must
fold the shapes in which the two sides write one segment — the same job the Greek
file's guard does for ει/η and ζ/zd. Sanskrit needed:

- `y: j` — Devanagari य is IPA /j/ (Whitney 1889 §5).
- `ai: e`, `au: o` — the dictionaries still write the diphthongs ai̯, au̯
  (Whitney §22); one nucleus, two letters.
- `ər, əl, əm, ən, əŕ → r, l, m, n` — r̥/l̥ are one vocalic segment
  (Whitney §§11–13); the dictionary writes /r̩/, which the guard's reader
  expands to schwa + consonant.
- `ŕ: r` — an acute on the syllabic r is the stress accent, not another
  consonant.
- `ṣ ṭ ḍ ṇ ś ñ ḥ → s t d n s n h` — see the caveat below.

**Caveat, stated where it bites.** The guard's reader (`spelling._readable`)
treats *every* combining mark as transcription detail, so it strips the dot of
ṣ ṭ ḍ ṇ ḥ and the acute of ś from the **laws'** side while the IPA side arrives
with those letters precomposed. The folds above make the two sides agree by
comparing the base letters. This weakens the guard's shape test (a dental and a
retroflex can no longer disagree *in the guard*), and it can never create a false
match, because the spelling itself must still be the attested word character for
character — ष and स are different letters. The strict fix is one line in
`src/pie/spelling.py` (`_readable` must keep a dot-below letter, which is a
letter and not a mark); it was out of that day's write scope.

## Rejected candidates, with killing numbers

| candidate | measured | why it is not in the file |
|---|---|---|
| `final_sh_to_visarga` — final *-ṣ > Skt -ḥ (sūnúḥ, agníḥ, háriḥ) | **+107 / −8** | The law is right (Whitney §188: final s and its substitute ṣ become ḥ) but the model cannot see morphology: the eight words it breaks (इष्, तुष्, दुष्, मक्ष्, रक्ष्, वक्ष्, शिक्ष्) are **root citations**, whose root really ends in ṣ, and they were matched as *spelled* words before. The council vetoes a loss. The same 107 words are won with **no** loss by the citation layer (see the ceiling below), so the law is left unregistered until that layer lands. |
| `au_to_o_final` — word-final *-au > -o | +1 / −1 | प्रो pró is won, the root अव् av- is lost to -o. Net zero, so no. |
| `th_to_retroflex_after_sh` — ṭh after ṣ (váriṣṭha) | fires nowhere | The aspiration is already gone upstream: *-stH- reaches this stage as plain t (`vˈariṣtaḥ`). Not a Sanskrit law's job. |
| `d_to_retroflex_after_sh` — ḍ after ṣ | fires nowhere | No word of the corpus exposes it at this stage. |
| `k > c` before a front vowel | 11 words, all blocked | The c comes from PIE *kʷ (vā́c-, rúc-), which `ine-pro → iir-pro` resolves to k before this transition sees it. Upstream's job. |
| final *-as > -aḥ as a *stem* fix | 85 words | मनस् mánas- is the stem and manaḥ the nominative; a citation strips, it cannot restore. Citation-layer work, numbers below. |

Also measured and **not** added: `s > ṣ` (ruki) and `*ai/*au` as two vowels are
upstream (`iir-pro → inc-pro`) and already registered there; `*-āti`/`*-nti`
endings need morphology (the ancestor of वमति is the bare root, not a verb form).

## The honest ceiling: what the remaining 2,943 misses are

Measured over the 3,935 tested rows (`proposals/2026-09-11/sanskrit/ceiling.py`).

| class | count | why no sound law can reach it |
|---|---:|---|
| **consonant-final citations** (virama: कृ, इष्, मनस्, -इक) | 781 | the record cites a stem/root; the laws end at an inflected word |
| **etymology names a compound** (`+` in the entry's etymology) | 706 | a compound is a join of two ancestors, not one path |
| derivation *within* Sanskrit* (-ana-, -man-, -tā, denominatives) | ~150 | a formation, not a sound change (the `formation` tier exists for it) |
| the nominative -ḥ vs the stem (PIA *-ṣ/-s) | 107 | see the rejected visarga law: needs `data/citation/sa.yaml` |
| -as stems cited as मनस् | 85 | the citation layer can only strip, not restore the -s |
| neuter -am cited as -a (बीज, मूत्र, युग) | 48 + 59 | the citation layer has no `m` ending |
| -an stems cited as अश्मन्, कर्मन् | 39 | same |
| ablaut grade of the recorded ancestor (कृ kṛ vs *kʷer-, ऋ ṛ vs *ar) | ~51 | the ancestor is a different grade of the root; no rule may bend it |
| upstream transitions (l > r 19+11, e > i 43, o > u 41, kʷ > c 11) | ~125 | `iir-pro → inc-pro` and `ine-pro → iir-pro`, owned elsewhere |
| already right, no law fired | 70 | see the counter gap below |
| notation junk in the records (ᶻ 22, ˢ 20, capitals 5, corrupted etymology strings 17) | 64 | data defects of the records themselves |

Two things that are **one small change away** and are *not* in that day's write
scope:

1. **The citation layer, extended.** `data/citation/sa.yaml` declares the
   endings `aḥ, aH, as, ḥ`. Measured during this batch, one extra ending each:
   `m` (neuter nom./acc. -am) **+48**, `ṣ` (the stage's own notation for a
   nominative -s after ruki, exactly as `as` already is) **+143** — 191 words,
   and **no** losses, because a root like इष् is matched by its full spelling
   before the citation layer is ever consulted. This is the single best next
   change for Sanskrit.
2. **The counter gap.** 70 words (the `=` signature) spell the attested word
   exactly with **no law fired** — खादति, यदि, कन्या. For a script language the
   `identity` column compares the phonemic form with the Devanagari target, which
   it can never equal, and `orthographic_hit` requires `steps`. They are the same
   kind of fact as `identity` and belong in a column of their own.

## Files changed

- `data/rules/inc-pro__sa.yaml` — four laws added, two rewritten to the corpus's
  notation, stage description updated.
- `data/spelling/sa.yaml` — `guard.equivalences` (15 notation folds), documented.
- `tests/test_sanskrit_batch.py` — 18 tests: account, laws, ablations, guard,
  and the two ceilings.
- `proposals/2026-09-11/sanskrit/{report.md,probe*.py,ceiling.py,candidates/}`.
- No source file, no other transition, no other spelling file, no docs.

## Upstream defects worth a ticket (not fixed here)

- 17 rows carry etymology text in the ancestry field (शुक्र's PIA ancestor is
  the string `*śukrásMerhofer…`) — the word can never be derived.
- 22 rows write a voicing mark (`bʰúdᶻdʰiš`) and 20 a devoicing mark
  (`*utˢtara`) that no rule owns; the writing table folds them, the law engine
  does not.
- The aspiration of *-stH- is lost at `iir-pro → inc-pro`, which costs
  वरिष्ठ, पृष्ठ, अङ्गुष्ठ and the rest of the -iṣṭha family.
