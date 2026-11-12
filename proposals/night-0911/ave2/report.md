# Avestan (`ave`) — night 0911: the chain is blocked by citation and IPA, not by its laws

Worker: Avestan (write set: `data/rules/ira-pro__ave.yaml`, `data/spelling/ave.yaml`,
`data/script/ave.yaml` if warranted, `data/sources.yaml` append-only,
`tests/test_night_ave2.py`, `proposals/night-0911/ave2/`).
Measured 2026-11-09, 04:25–05:55 CET. **No law was added.** Four candidates were
written, measured, and kept below with their numbers; the reason none could be
shipped is a measurement, not a preference.

## Numbers

| figure | before | after |
|---|---:|---:|
| exact (laws reproduce the headword) | 0 / 352 | 0 / 352 |
| identified (a recorded ancestor in the chain) | 312 | 312 |
| explained (union: 7 spelled + 1 identity) | **8** | **8** |
| orthographic (spelled, plausibility-guarded) | 7 | 7 |
| words the laws *spell exactly* (unguarded audit) | 32 | 32 |

A prior session's published `data/coverage.json` row for `ave`: exact 0,
orthographic 7, identity 1, explained 8 — the same 8 after this session, because
nothing in this session's write set can be counted until the citation and IPA
walls fall.

`PYTHONPATH=src python3 tools/coverage.py --langs ave` →
`0/352 … 0/312 tested`; `pie worklist --lang ave` → "sound laws 0, spelled 7";
`tools/whatif.py --to ave --layers exact,orthographic` → "explained before: 7"
(the published 8 is those 7 plus one `identity` word; `data/coverage.json`,
2026-11-09 run).  The write set of this session reaches none of the three.

Exact can never move for Avestan for the same reason it cannot for Old Persian:
the headword is written in a script (𐬀𐬯𐬞𐬀), the laws end in phonemes (`aspō`).
The counted figure for a scripted language is the union, and all of it comes
through `data/spelling/ave.yaml`.

## Why the union is 7 and not 32: two walls, both outside this write set

**Wall 1 — the glossary is cited by the stem.** Avestan dictionaries (and
Wiktionary with them) enter a noun as its stem: 𐬀𐬯𐬞𐬀 `aspa-`, 𐬐𐬁𐬨𐬀 `kāma-`,
𐬠𐬭𐬁𐬙𐬀𐬭 `brātar-`, 𐬆𐬭𐬆𐬰𐬎 `ərəzu-`. The chain ends where the recorded
ancestor ends — a nominative: `aspō`, `kāmō`, `brātā`, `ərəzuš`. The difference is
the dictionary's citation form, exactly what `data/citation/<lang>.yaml` exists
for. Miss classes over the 312 identified entries:

| class (spelled output vs headword) | n | belongs to |
|---|---:|---|
| final `-ō` vs stem `-a` (`aspō` ≠ aspa) | 25 | citation / paradigm (W5) |
| final `-ā` vs stem `-ar` (`θrātā` ≠ θrātar) | 11 | citation / paradigm |
| final `-š` vs bare stem (`ərəzuš` ≠ ərəzu) | 7 | citation (drop `-š`) |
| final `-əm` vs stem `-a` (`xšaθrəm` ≠ xšaθra) | 4 | citation / paradigm |
| final `-ō` vs stem `-ah` (`manō` ≠ manah) | 3 | citation / paradigm |
| superlative `-mō` vs stem `-ma` (`aštamō` ≠ aštəma) | 3 | citation / paradigm |
| letter-level residues (see below) | ~25 | **sound laws (my file)** |
| no recorded ancestor, hyphen, accent-only, other | ~10 | W1 / notation |

The existing layer cannot take the first five classes: `citation_hit` **drops** a
declared ending (`deváḥ` → `devá`) and can never *replace* `-ō` with `-a`.
Measured with a scratch rewrite of exactly those endings, honouring the same
plausibility guard: **7 → 14** counted words on today's IPA alone
(aspa, udra, uštra, kāma, puθra, brātar, būmi), and the same mechanism is what
would carry the other ~30 once they have IPA (next wall). That is the single
largest available gain for Avestan, and it is one file,
`data/citation/ave.yaml`, plus (or instead) the paradigm layer W5 that does not
exist yet. **Recommendation to the integrator: assign it, or widen
`citation_hit` to a replacement ending.**

**Wall 2 — 39 of 352 entries carry an IPA string.** The orthographic layer is
guarded by `spelling.plausible(form, ipa)`, so an entry without IPA cannot be
counted at all. Avestan: 39/352 (11 %). Compare Greek 4,741/4,918 (96 %),
Sanskrit 4,585/4,724 (97 %), and Old Persian 9/375 — the Iran chain's other
language has the same gap, which is why the chain "barely works". This is a W1
lexicon task (supplement entries with IPA), not a rule task.

Consequence: of the 32 headwords the laws *spell* exactly today, 25 are correct
and uncountable for want of an IPA string. A new law that fixes a form without
IPA moves no number — that is why every candidate below measures `+0`.

**Refused: `data/script/ave.yaml`.** The Avestan script is an alphabet, so a
script table would be a second copy of `data/spelling/ave.yaml` whose only
effect is to skip the plausibility guard. The precedent is Greek: also
alphabetic, also handled by its spelling file (`data/spelling/grc.yaml`), no
script table. Adding one would inflate the "through its script" column with
words that the orthographic layer already spells, on less evidence. Not written.

## Candidates, measured (`tools/whatif.py --to ave --layers exact,orthographic`)

| candidate | laws it changes | gained | lost | verdict |
|---|---|---:|---:|---|
| `ay_to_ae` — PIr *ay > Av. aē | 41 forms | 0 | 0 | held: the law fires widely and correctly (aēuua, vaēda, maēšī) but every affected lemma is stem-cited or lacks IPA |
| `hw_to_xv` — PIr *hw > Av. xᵛ | 8 forms | 0 | 0 | held: same wall (xᵛafna, xᵛasura, xᵛa) |
| `an_to_nasal` — PIr *an > Av. ą / _C | 0 forms | 0 | 0 | held: the environment as written matched no form; needs a narrower statement (ą before a consonant, mąθra, dąhišta) and the same wall applies |
| `ar_stem` — final *-ār > -ar, replacing `final_ar_to_a` | 1 word | **+1** (𐬠𐬭𐬁𐬙𐬀𐬭 `brātar`), 0 lost | | **rejected**: the -ar of `brātar-` is the stem, not a sound change (the nominative is `brāta`); selling a citation fact as a law for one word is exactly the veto in `docs/REVIEW.md` §4 |

Losing lists: **empty for all four** (no candidate removes a word the laws
explain). Each file carries its claim, environment, examples and the numbers in
its header; `tests/test_night_ave2.py` re-measures the no-loss invariant.

## Letter-level residues still open (no candidate written, ranked by corpus)

These are the genuine phonological misses left after the citation classes. None
was written tonight because each gains 0 counted words today (wall 2); each is a
lead for the session that lands the citation layer first.

- PIr *hw > Av. xᵛ: xᵛafna-, xᵛasura-, xᵛa- 'own', xᵛaēδa- (5 words).
- PIr *an > Av. ą / _C: mąθra- 'formula', dąhišta- (2 counted; more unguarded).
- PIr *ay > Av. aē: vaēd-, maēšī-, aēuua-, aētī-, daēza- (41 forms touched).
- PIr *d > Av. δ after a vowel: pāδa- 'foot', xᵛaēδa-, aiβiδāna- (3).
- PIr *r̥t > Av. ṣ̌: aṣ̌a- 'truth' (PII *Hr̥tás), aməṣ̌a- 'immortal' (*amr̥tah) —
  the classic pair; `r_syllabic_to_ere` currently rewrites both into ərə-, which
  no reading of 𐬀𐬴𐬀 / 𐬀𐬨𐬆𐬴𐬀 can accept.
- The Avestan letter 𐬬 vs 𐬎𐬎 for /w/ beside a consonant (`duuar-`, `hizuuā-`) is a
  writing convention, not a law; it would be a `data/spelling/ave.yaml` rule and
  gains 0 today (no IPA on those entries).

## Files

- added `proposals/night-0911/ave2/report.md` (this file),
- added `proposals/night-0911/ave2/candidates/{ay_to_ae,hw_to_xv,an_to_nasal,ar_stem}.yaml`,
- added `tests/test_night_ave2.py` (7 tests: law-file contract, examples
  re-derived, spelling stays orthographic, candidates parse, cite, and lose
  nothing),
- unchanged: every law file, every spelling file, `data/sources.yaml`,
  `data/coverage.json`, `docs/`.
