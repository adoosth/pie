# Middle Persian: ancestry, orthography, and what the laws still block

Status: **open** (W1 + W2 work; no rule was edited, nothing was committed).
Date: 2026-11-09. Branch `main`, based on `083dfe5`.

## 0 · Summary

| measure | before | after |
|---|---|---|
| glossary rows | 616 | 616 |
| rows with a **recorded ancestor at a modelled stage** (`identified`) | **2** | **61** |
| PIE-linked | 2 | **20** |
| exact (laws reproduce the word) | **0** | **1** (`pistag`) |
| rows carrying `anc` in the supplement | 2 | 70 |

Three separate facts, not one: (i) the dictionary the glossary comes from states
no ancestor, so the ancestry had to be joined from the one source that records
it; (ii) the headword column mixes two notations, and the Pahlavi half cannot be
derived from phonemes at all; (iii) only 38 of the 61 new ancestry links give the laws a Latin-script
ancestor to start from; the other **23** point at a cuneiform form the engine
never transliterates, so no law fires at all.

## 1 · Why only 2 of 616 rows had an ancestry link

The supplement is two corpora in one file (`data/lexicon/_supplement/pal.jsonl.gz`,
616 rows):

- **489 rows** parsed from the Docling Markdown of MacKenzie's *A Concise Pahlavi
  Dictionary* by `tools/ingest_mackenzie.py`;
- **127 rows** fetched from Wiktionary's *Middle Persian lemmas* category by
  `tools/fetch_wiktionary.py` (they carry `"source": "wiktionary"`).

Neither tool records an ancestor, and the dictionary cannot supply one:

- MacKenzie's bracket gives the Pahlavi spelling, the **Aramaic logogram** a
  heterogram is written with (`abag [LWTE < A Iwt-h …]`, 249 occurrences of
  `< A`) and the **Avestan form of a learned loan** (`= Av.`, 93 occurrences).
  Neither is an etymological ancestor: a logogram is a *spelling* of an Iranian
  word, and Avestan is a sister branch, not the parent. The book's own
  introduction says so — "justification of the transcription of each word would
  require the discussion of a mass of etymological and comparative evidence far
  beyond the scope of this dictionary" (Introduction, §"The entries"). Grepping
  the whole text for `OP`, `Old Persian` or `Proto-Iranian` returns **0** hits.
- `fetch_wiktionary.py` keeps `word`, `gloss`, `pos` and the transliteration and
  **drops `etymology_templates`**, which is exactly where Wiktionary records
  `{{inh|pal|peo|…}}`. So the whole 127-row Wiktionary half arrived without the
  ancestry it was fetched for.

The two linked rows (`𐫅𐫏𐫇` *dēw*, `𐫀𐫡𐫘` *ars*) were added by hand on
2026-11-08 with their Wiktionary chain, which is why `ancestor_starts()` could
only ever see two candidates: **the pipeline has no ancestry source for this
language, not a parser bug.**

## 2 · The ingest change (`tools/ingest_mackenzie.py`, +367/−10 lines)

The tool now carries the one recorded ancestry that exists for these words, from
the page that records it, keyed by the dictionary's **own reading**:

1. `--ancestry` fetches the Middle Persian wikitext of every page in
   `Category:Middle Persian lemmas` (265 pages, batched, 429-aware, cached at
   `--cache`, refresh with `--refetch`).
2. Each supplement row is joined to a page by its **transcription** (MacKenzie's
   headword, macron-folded) against the page's `tr=`/`ts=` headword reading, or
   else by its Pahlavi transliteration against the page title. A join is only
   accepted when the **gloss overlaps** (a content word of the dictionary's gloss
   occurs in the page's own section), so a homograph cannot lend its etymon.
3. From that page's `===Etymology===` the tool copies only `{{inh}}`, `{{inh+}}`,
   `{{inherited}}`, `{{bor}}`/`{{lbor}}`… templates and `{{etymon|pal|:inh|…}}`.
   `{{der}}` and `{{root}}` are **deliberately not copied**: they name a
   derivation base or a root (`*bʰer-`, `*peh₂-`), not the word's etymon.
   Placeholder forms (`-`, `/`-variants, `tr=…` leftovers) are dropped.
4. Each linked row gets `anc`, `sources`, `url`, and a `ref` that quotes the
   Wiktionary etymology and, when the page cites this very dictionary, the
   **MacKenzie headword and page** (`{{R:pal:Mackenzie|page=21|čandal}}`).
5. `merge_curated()` keeps the hand-added rows and their fields (`etym`, `ref`,
   `anc`, `ipa`…) across a re-ingest, so the dictionary and the curated rows
   coexist; `--no-merge` reproduces the old destructive behaviour.

Result of `python3 tools/ingest_mackenzie.py --ancestry`:

```
ancestry: 65 of 616 entries name an etymon (30 of them through Old Persian)
616 Middle Persian entries → data/lexicon/_supplement/pal.jsonl.gz
```

and after the (unchanged) merge into the glossary, `tools/coverage.py --langs pal`:

```
pal   1/616  glossary   1/61  tested   0.16%
total: 1 / 616 reconstructed exactly (0.16%); 61 with an ancestor, 20 PIE-linked
```

Ancestry by stage: `ira-pro` 38, `peo` 32, `iir-pro` 25, `ine-pro` 22 (plus
`grc` 3, `ae` 2, `xbc` 2, `arc`/`pgd`/`sog` borrowings). No link was invented:
every one is a template with a page and a quoted sentence.

> **Integrator step (outside this file's write scope):** the merged
> `data/lexicon/pal.jsonl.gz` was **not** rewritten here. The numbers above were
> measured on a scratch copy after `python3 tools/build_lexicons.py
> --supplements-only`. In the real tree `pal` still reads 2/616 until that one
> command is run.

## 3 · Orthography: no `data/spelling/pal.yaml` (decision: do not ship)

**The headword column is not one notation.** Of the 616 rows, **521** are Latin
*transcriptions* (`abad`, `gwhl`, `xwab`) and **95** are Pahlavi
*transliterations* (`ʾp̄ʾt'`, `nmk'`, `hp̄t'`, `wn'`), plus 4 bare logograms
(`ŠNT`, `KHMA`, `LHMA`, `LBA`). A spelling file maps a phonemic string to *one*
written system; here two systems share the target column, and one of them (the
abjad) is not a letter-for-phoneme system at all:

- **short vowels are not written**: the laws derive `hapt`, the record is
  `hp̄t'`; `namadk` vs `nmk'`;
- **heterograms** write an Iranian word with an Aramaic logogram (`LWTE` *abāg*,
  `QDM` *abar*, `ŠNT` *sāl*, `KHMA` *xar*, `LHMA` *nān*, `LBA` *wuzurg*), so for
  those words no phoneme chain produces the spelling — it would be a per-word
  table, which the programme forbids;
- **historical spellings** keep letters the pronunciation lost
  (`kʾlwʾn'` *xarwār*), and the alphabet is **multi-valued** (one sign for
  r/l, one for k/g, y for /y ī ē/), so the letter sequence underdetermines the
  sound and the sound underdetermines the letters.

**Measured ceiling.** Of the 61 words that now have an ancestor, that ancestor is
in cuneiform for **23** (see §4) and Latin-script for **38**. Of those 38, only
**3** records equal the laws' output once macrons and acutes are folded away
(`ābād`~`abad`, `spēd`~`sped`, and `pistag`, the one true match); none of the
three is fixed by a *convention of the language* — they are **damage to the
source text**: the PDF's text layer has no macrons at all. Rendering p. 60 and reading it back proves the
book prints them (`galōg`, `gām`, `gandanāg`, `dō`); the extraction lost every
`ā ē ī ō ū š č γ`. So a `pal.yaml` written today would be a file that *undoes*
MacKenzie's own orthography to fit an OCR artefact — precisely the target
bending the programme forbids.

**Decision.** Do not add `data/spelling/pal.yaml`. The honest layer for this
stage is not spelling but a **script table** (`data/script/pal.yaml`, the mechanism
already used for Old Persian cuneiform in `src/pie/script.py`: signs, readings,
unwritten short vowels, logograms, closing conventions), which can state
"`hp̄t'` is a reading of `hapt`" as a *reading*, scored in the `through its
script` column and never in the attested figure. Prerequisite: repair the
headword column (re-extract the dictionary from page images so the macrons
survive, or key the transliteration rows to their `translit` field).

## 4 · Ladders and the law that blocks each one

Every line is `record ← recorded ancestor (stage) → laws' output | blocking law`.
Commands to reproduce a single ladder: §6.

**4a · Blocked before the first law — the ancestor is cuneiform (23 words).**
`ancestor_starts()`/`derive()` hand the Old Persian *cuneiform* string to the rule
engine, so **no law fires at all** (`[]` steps, output = input):

| record | ancestor | note |
|---|---|---|
| `padzahr`, `pʾtzhl` | OP 𐎱𐎠𐎮𐎹 *p-a-di-y* | 2 rows, same ancestor |
| `anahid`, `ʾnʾhyt'` | OP 𐎠𐎴𐏃𐎡𐎫 *a-n-h-i-t* | |
| `hm` | OP 𐏃𐎶 *ham* | |
| `bwm` | OP 𐏏 *būmiš* | |
| `pus` | OP 𐎱𐎢𐏂 *puçaʰ* | |
| `sng` | OP 𐎠𐎰𐎥 | |
| `ʾswbʾl` | OP 𐎠𐎿𐎲𐎠𐎼 | |
| `gwptn'`, `bwltn'`, `mtr'`, `LBA`, `ŠNT`, `ŠM`, `ʾp̄`, `hyn'`, `hndwk'`, `hndwk'ʾn`, `lwc`, `tn'`, `hwm`, `𐫅𐫏𐫇` | OP forms | 20 of them have a `translit` in the `peo` glossary; 3 have none |

**Defect (W7, 2 lines).** `coverage.ancestor_starts()` should pass a non-Latin
ancestor through the reading chain that already exists (`service._reading_index`
→ `translit.py` → `data/readings.json`), not into `derive()` raw. Feeding the
recorded readings by hand (e.g. `a-n-h-i-t`, `p-a-di-y`, `a-s-b-a-r`) makes the
laws fire (→ `anhit`, `payiy`, `asbar`), so the **predicted gain is 23 words
that become measurable** (0 are exact today; none of them can move until this is
fixed). Second finding on the same path: Wiktionary's OP readings write a final
/h/ as `ʰ` (`daivaʰ`), which the tokeniser does not read as `h`, so
`final_h_loss` never fires — `dēw` derives `dēvaʰ` instead of `dēw`.

**4b · Latin-script ancestors: the laws' output vs the record.**

| # | record | ancestor | output | blocking law |
|---|---|---|---|---|
| 1 | `pistag` | peo *pistaka | **pistag** ✓ | — (`k_to_g`, `final_vowel_loss`) |
| 2 | `abad` | ira-pro *āpāta | ābād | none: the source text lost the macrons |
| 3 | `sped` / `spyt'` | ira-pro *cwaytáh | spēd | none: macron loss; `cw_to_sp`, `ai_to_e` right |
| 4 | `gwlg` | ira-pro *wŕ̥kah | gˈurg | none: `r_syllabic_to_ar`+`war_rounding`+`w_to_g`+`rk_to_rg` all right |
| 5 | `xwab`, `hwʾb` | ira-pro *hwápati | hwˈabad | **no `hw → xw` law**; and `final_vowel_loss` leaves `-ad`, record `xwāb` |
| 6 | `nog` | ira-pro *náwah | nˈaw | **no *-aw → -ōg**; `final_h_loss`+`final_vowel_loss` give `-aw`, record `nōg` |
| 7 | `bʾg` | peo *bāgah | bāy | **`g_to_y` over-applies**: record `bāγ`/`bāg` keeps the stop before the lost *-ah |
| 8 | `nʾd` | peo *nadah | nay | same over-application (`d_to_y`); record `nʾd` = *nāy*/*nād* |
| 9 | `kyš` | ira-pro *kayšás | kēšˈas | **no loss of final *-as**; `final_vowel_loss` cannot delete a closed final syllable |
| 10 | `gwhl` | ira-pro *gawθraH | gōhā | `theta_r_to_cedilla`+`cedilla_to_h` drop the *r*: record `gōhr` |
| 11 | `blnc` | peo *vrinjiš | vrinziš | **no `wr → br` / `vri → bri`** (record `birinj`) |
| 12 | `cynʾl` | ira-pro *čanah-dāra | čanahdār | compound: no law reduces `-ah-d-` to `-ār` (record `činār`) |
| 13 | `bpl` | iir-pro *wyHāgʰrás | wyāgr | the record (`babr`?) is not this etymon's shape; `final_s_to_h` fires without a following `h_loss` |
| 14 | `clp` | ine-pro *selp | harp | `l_to_r`+`s_to_h` fire correctly; **no *-lp → -rb** (record `čarb`) |
| 15 | `bywl` | ira-pro *baywā́ | bēwˈā | **no final *-ā → -ar** (record `bēwar`) |
| 16 | `ʾp̄ʾt'` | ira-pro *āpāta | ābād | notation only: the target is a transliteration, not a sound |
| 17 | `hp̄t'` | ira-pro *haptá | hapt | notation: short vowels unwritten + `p̄` letter-name |
| 18 | `nmk'` | ira-pro *namadka | namadk | notation + `final_vowel_loss` did not reach the inner `-a-` |
| 19 | `tʾp̄k'` | ira-pro *tāpaka | tābag | notation (`p_to_b`, `k_to_g` right) |
| 20 | `wn'` | ira-pro *wīnaH | wīnā | notation (record `wīn` with unwritten short vowel and `'`) |
| 21 | `tʾht'` | ira-pro *táxtah | tˈaxt | notation (`final_h_loss` right) |
| 22 | `lwšn'` | peo *rauxšnā | rōšnā | notation: **`r` is written `l`** — a general letter convention, not a sound |
| 23 | `slt'` | peo *θarta | sard | notation (`rt_to_rd`, `theta_to_s` right) |
| 24 | `lwcyk'` | ira-pro *ráwčikah | rˈōčig | notation (`aw_to_au`+`au_to_o`+`k_to_g` right) |
| 25 | `zyh` | iir-pro *ǰyáH | ǰyˈā | notation: `ǰ` is written `z` (record `zēh`) |
| 26 | `ʾslwn'` | iir-pro *átʰarwā | ˈasarwā | notation + `θ`/`l` letter conventions |
| 27 | `nyšʾn'` | ira-pro *ni | n | the ancestor cell is wrong: *ni* is a particle; the record is *nišān* |

Read together, 4b splits cleanly: **#16–26 are orthography** (the phonology is
already right, the target is letters), **#5–15 are real gaps** (a law or an
etymon cell), **#2–4 are source damage**.

**4c · What the peo→pal laws actually carry (`tools/whatif.py --to pal --drop …`).**
Every registered rule of `data/rules/peo__pal.yaml` was dropped in turn on the
merged lexicon (scratch copy, `exact` 1/616 before the drop):

```
k_to_g            exact after: 0  (-1)   lost: pistag
final_vowel_loss  exact after: 0  (-1)   lost: pistag
war_rounding, w_to_g_before_ur, b_to_w, d_to_y, g_to_y, p_to_b, t_to_d,
r_stem_oblique, rk_to_rg, rt_to_rd, rp_to_rb, athetah_to_ah, theta_to_s,
cedilla_to_h, xsh_to_sh, ai_to_e, au_to_o, final_h_loss, final_am_loss,
j_to_z, wk_to_k                              (+0, gained 0, lost 0)
```

Two readings, both important. (i) Only **2 of 23** laws are *observable* on this
corpus at all — the other 21 fire (or do not) with no match to show for it.
(ii) That blindness is structural: `whatif` counts exactly as `coverage` does, so
a word whose ancestry is a cuneiform string contributes nothing, and 61 − 38 =
**23 words never enter the measurement**. The audit cannot say `g_to_y`
over-applies on `bāgah` because no such word can be *counted* — the ladder in §4b
#7 shows it, and the number is invisible until W7's reading fix lands. So: **no
law edit is justified by this audit**, and any proposal to change one must be
re-run after the transliteration fix; deleting a rule today would be a change
nobody can measure.

## 5 · Minimal fixes proposed (no rule edited here)

1. **W7 — transliterate the ancestor before deriving** (2 lines in
   `coverage.ancestor_starts`/`service`): unblocks 23 words; predicted exact gain
   unknown but currently 0 is guaranteed. Highest value per line.
2. **W7 — read `ʰ` as `h`** in the form the laws consume: `dēw`, `wazr̥kaʰ`.
3. **W3 — `hw_to_xw`** (OP/PIr `hw-` → MP `xw-`, cited Skjærvø 2009b;
   `xwāb`, `xwar-`, `xwadāy`): 2 rows today, a systematic prelude.
4. **W3 — a final-syllable law for `*-as#`** (`kayšás` → `kēš`): 1 row now, and
   the same law is needed by dozens of `-as` stems.
5. **W6 review of `g_to_y`/`d_to_y`**: intervocalic lenition is applied before a
   lost final vowel (`bāgah`→`bāy`, `nadah`→`nay`); the narrower environment
   ("before a vowel that survives") is the one the records support.
6. **W1 — re-extract MacKenzie from page images** so macrons and `š č γ`
   survive: without it no transcription row can ever match exactly, whatever the
   laws say.

## 6 · Reproduce

```bash
cd /home/cloud/code/seanet/pie
python3 tools/ingest_mackenzie.py --ancestry          # 65 of 616 name an etymon, 30 via OP
python3 tools/build_lexicons.py --supplements-only    # fold the supplement (integrator step)
PYTHONPATH=src python3 tools/coverage.py --langs pal --limit 0
PYTHONPATH=src python3 -m pie.cli worklist --lang pal
PYTHONPATH=src python3 tools/whatif.py --to pal --drop g_to_y   # per-law audit (§4c)
PYTHONPATH=src python3 - <<'PY'                       # one ladder
from pie import data
from pie.rules import derive
chain = data.derivation_chain("pal"); rs = data.rulesets()
r = derive("kayšás", chain[chain.index("ira-pro"):], rs)
print(r.output, [s.rule_id for s in r.steps])
PY
```

Not run in the real tree: `data/lexicon/pal.jsonl.gz` (merge), `docs/*`, `src/`,
`data/rules/*`, `docs/DECISIONS.md` — all outside this file's write scope.
