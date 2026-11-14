# Middle Persian: reading the dictionary's own notation

**Date.** 2026-11-09, ~03:00–05:00.
**Branch.** `main`, on top of `29de0e4`. Nothing committed; nothing written
outside this file's scope. Rules were **measured, not added**: no law in
`data/rules/peo__pal.yaml` changed, and §4 says why.
**Read first.** `proposals/2026-09-11/pal-script.md` (the sign table and the
reading table that already exist) and `proposals/2026-09-11/pal.md` (ancestry,
ingest, the 27 ladders).

## 0 · Summary

| | before | after |
|---|---:|---:|
| `pal` entries explained | **2** | **18** |
| `pal` exact (laws, letter for letter) | 1 | 1 |
| `pal` through the script/notation column | 1 | **17** |
| `pal` orthographic | 0 | 0 |
| `fa` exact / explained | 0 / 373 | 0 / 373 (unchanged by this file) |
| readable Middle Persian spellings (lexicon pairs) | — | **48 of 80** (56 with the engine fix of §6) |
| tests | 502 | **509** |
| `check-rules` | 699/966/0 | **698/965/0** |

The wall named in the brief was "the recorded ancestor is a Pahlavi spelling
and nothing can read it". This file does not pretend to read the *script*
(it cannot: an abjad that writes no short vowel needs a lexicon, and this
repo's MacKenzie ingest lost the transliteration column). What it does is make
readable the notation the dictionary actually prints the spellings in — the
Latin transliteration — and that is 17 of the 61 identifiable `pal` entries,
with every one of the 17 checked against the entry's own transcription (§2).

## 1 · Inventory of the notation, not of the script

`data/lexicon/pal.jsonl.gz`, 616 entries, by what the headword is written in:

| headword | entries | of which carry an ancestor |
|---|---:|---:|
| Latin transcription (`abad`, `pistag`, `gurg`) | 549 | 49 |
| Book Pahlavi transliteration (`bʾg`, `hwʾb`, `gwlg`, `ʾp̄ʾt'`) | 63 | 19 |
| Manichaean script | 4 | 2 |
| **total** | **616** | **70** |

The 63 transliteration headwords are *not* unreadable: the letters are Latin,
and MacKenzie prints the transcription beside them in the same entry
(`gurg [gwlg]`, `abad [ypytl]`, `pistag [pstk1]` — the last two are Docling's
OCR of `ʾp̄ʾt'` and `pstk'`). That side-by-side pair is the evidence this file
uses, and it is the same evidence `data/readings_pal.json` already holds for
the scripted half.

Two columns of the glossary are inconsistent and it costs readings: sometimes
`word` is the transcription and `translit` the spelling (`abad` /
`ypytl | M y ydt N ~`), sometimes the reverse (`bʾg` / `bāğ`, `gwlg` / `gurg`).
Nothing here "fixes" that: the entries are recorded facts.

## 2 · What was built: the transliteration table

`data/script/pal.yaml` (in scope) gains **21 rows**, `kind: translit`, one per
letter of MacKenzie's own transliteration, each carrying the values of the sign
it renders (Table II, and the sentence that the system stops at the basic
Iranian value: *"it is neither necessary nor desirable to go beyond this by
attempting to give closer 'phonetic' values to the letters, such as r for
written l, or x for written h"*, Introduction, "Transliteration"):

| letter | renders | reads | letter | renders | reads |
|---|---|---|---|---|---|
| ʾ | aleph 𐭠 | ʾ ā a | n | nun 𐭭 | n |
| b | beth 𐭡 | b | s | samekh 𐭮 | s |
| g | gimel 𐭢 | g | p | pe 𐭯 | p b f |
| d | daleth 𐭣 | d | c | sadhe 𐭰 | c č z j |
| h | he/heth | h x | š | shin 𐭱 | š |
| w | waw 𐭥 | w ō ū u r ʿ | t | taw 𐭲 | t d |
| z | zayin 𐭦 | z | ʿ | ayin | ʿ w r |
| ḥ | heth 𐭧 | ḥ h x | č | sadhe read č | c č z j |
| y | yodh 𐭩 | y ē ī i | ẕ | dotted zayin | z |
| k | kaph 𐭪 | k g | | | |
| l | lamedh 𐭫 | l r | | | |
| m | mem 𐭬 | m q | | | |

Three small additions to the sign rows are stated in the code and in the test:
waw and yodh are *matres* and write a short u / i (`gurg [gwlg]` proves it for
waw), and the letter `h` renders **he and heth both**, so it carries heth's x —
which is exactly the "x for written h" MacKenzie declines to write but the
letter still stands for.

Why this is not a permissive layer. The same alignment as the abjad half of the
Old Persian model, and nothing else:

* a **short vowel is not a letter**, so a Latin *transcription* can never be
  mistaken for a transliteration: `script.match("pal", "abad", "ʾp̄ʾt'")` still
  has to treat the a's as unwritten, and `writes("pal", "abad")` is a refusal
  from `signs()` because `a` is no sign at all;
* every sign must be spent (`gwl` is not `gurg`);
* every consonant of the reading must be written (`glg` cannot be gurg — l can
  write r, so that one is a *possible* spelling and is accepted);
* ideograms stay out: capitals (`ŠM`, `LWTE`, `LKH`) are read as words from
  `data/readings_pal.json`, never letter by letter, and the test asserts that
  no capital is a sign.

**The pairs it reads.** Every glossary entry whose headword is a plain
transliteration and whose `translit` is a plain transcription is a test case
the dictionary states:

    accepted 48, refused 32 (56 / 24 with the engine fix in §6)

The refusals are the interesting part, and 24 of 32 are **damage or a polyphony
this table does not state**, not misses to paper over: `hʾn'` cannot be xānag
(the transcription has a g the spelling does not write), `kltk'` cannot be
kard (a final k with no letter in the reading), `škl` cannot be šqr (q is not a
letter). Two refusals point at a real value MacKenzie's table has that I did
**not** add without a citation:

* `dlgwš` = **daryōš** (MacKenzie, s.v. *driyōš*, prints `driyoS [dlgw? | N
  daryos]`): here gimel writes **y**. One attested pair is not enough to give
  gimel y in the table, but it is the next value to check against the printed
  Table II;
* `ktkhwtʿy` = **kadagxwadāy**: here ayin writes **ā**.

## 3 · Measured

`PYTHONPATH=src python3 tools/coverage.py --langs pal fa --limit 0`

| | before | after |
|---|---:|---:|
| pal: glossary / identified / tested | 616 / 61 / 61 | unchanged |
| pal: exact (strict, letter for letter) | 1 | 1 (`pistag`) |
| pal: through the script/notation column | **1** | **17** |
| pal: orthographic | 0 | 0 |
| pal: **explained** | **2** | **18** |
| fa: exact | 0 | 0 |
| fa: explained (orth 207 · script 299 · identity 65 · pathway 5) | 373 | 373 |

Every one of the 17 was read against its entry's own transcription, and none
contradicts it (the two without a transcription, `hm` and `hp̄t'`, are Manichaean
and the reading the laws give them is the transcription the dictionary prints
elsewhere):

    hm ham · bʾg bāğ · hwm hōm · hyn' hēn · gwlg gurg · hp̄t' hapt ·
    pstk' pistag · tʾht' taxt · tʾp̄k' tābag · wn' wīn · slt' sard ·
    spyt' spēd · lwcyk' rōzīg · ʾp̄ ap · ʾnʾhyt' anāhid · ʾp̄ʾt' ābād ·
    𐫅𐫇𐫏 dēw

`fa` is untouched by this file. The checkout shows `data/spelling/fa.yaml`
+47 lines from **a concurrent batch at 02:54**, which moves the Persian
orthographic column 207 → 227 on its own; that is not this work and I did not
touch the file.

## 4 · The laws: measured, and none added

Every registered law of `peo → pal` was dropped in turn and heard by the
council (`tools/council.py --drop … --stage peo --to pal --layers
exact,orthographic,script`; baseline `pal` 18, `fa` 251 in those three
layers). **Nothing was added, and nothing was deleted**: the audit says the
existing set carries words, and the two laws that look wrong are wrong only
word by word, which is not a law.

| law dropped | pal | fa | words lost | verdict |
|---|---|---|---|---|
| `g_to_y` | 18 | +1 | — | ACCEPT by the council (`خرگوش`), but see below |
| `d_to_y` | +1 | +2 | — | ACCEPT by the council (`nʾd`, `تیرداد`, `راد`), but see below |
| `b_to_w` | 0 | −1 | دستور, سوار | REJECT: it carries two Persian words |
| `p_to_b` | 0 | −5 | آباد, ابریشم, تاب, تب, نبید | REJECT |
| `k_to_g` | −1 | −6 | pistag, ماده, مگس, نیزه, پاره, کده, گوگرد | REJECT |
| `final_vowel_loss` | −2 | +4/−7 | hp̄t', pistag, درخت, لنگ, ماده … | REJECT |
| `final_h_loss` | −6 | −35 | gwlg, hm, lwcyk', spyt', tʾht', 𐫅𐫏𐫇, آرد, آزاد, باد … | REJECT |
| `final_am_loss` | 0 | −2 | شیر, صد, نون, نیزه, یخ | REJECT |
| `war_rounding` | −1 | −1 | gwlg, گر, گرس | REJECT |
| `w_to_g_before_ur` | −1 | −1 | gwlg, گر, گرس | REJECT |
| `theta_to_s` | −1 | −10 | slt', آس, رسن, سر, سرو, سپاس, شش, صد … | REJECT |

**The two that pass the council are the two that must not ship as they stand.**
Deleting `g_to_y` and `d_to_y` loses no word the counter can see and gains
four — but the gain is a *spelling* gain: `nʾd` is nʾd with the transcription
**nā̆y**, i.e. its own record shows the d becoming y, and `dlgwš` is *daryōš*,
where the g is a y. The council counts a script match when the letters fit, so
a lenition that the transcription states looks like a loss. The honest
conclusion is the one `pal.md` §5.5 already reached from the other side: the
intervocalic lenition of the voiced stops is **lexically split in Middle
Persian** (bāg, gurg, daryōš against nāy, and b>w is regular), so it is not a
stage-wide law. It belongs where `r_stem_oblique` lives: registered, tier
`proposed`, and switched **on per word** through `data/pathways.jsonl` for the
words whose record shows the glide. That file is outside this report's write
scope, so the exact change is proposed here and not made:

```yaml
# data/rules/peo__pal.yaml — d_to_y / g_to_y
tier: proposed
off_by_default: true
# data/pathways.jsonl — one row per word whose transcription shows the glide
{"lang": "pal", "word": "nʾd", "enabled": ["d_to_y"]}
{"lang": "pal", "word": "dlgwš", "enabled": ["g_to_y"]}
```

**Reordering tried and rejected.** Running all three lenitions *after*
`final_vowel_loss` (so only a vowel that survives triggers them, which is what
the records look like) measures `pal` 18 → 16 and `fa` 373 → 359: 18 Persian
words (دستور، سوار، آباد …) need the lenition to fire before the apocope in
this cascade. Recorded so nobody tries it twice.

**`data/rules/ira-pro__pal.yaml` was not written, and should not be.** The
chain of a language is not assembled from the rule files: it is
`data/languages.yaml` (`pal.ancestor: peo`), so a direct transition would be
dead code for every counter, and the same laws measured nothing from the
Proto-Iranian side either (§4 above, where the `ira-pro` starts already run
through `ira-pro → peo → pal`).

## 5 · What still does not fit, and why

* **494 of the 575 Persian ancestor spellings still have no reading.** The
  reading exists in MacKenzie's printed dictionary and this repo's ingest lost
  it to OCR (`ʾp̄ʾt'` → `ypytl`, `slt'` → `sit1`). No table may invent vowels.
  The one-line *engine* fix below does not help them either — the fix helps the
  **pal** side, not the Persian side, because `_phonological_form("pal", …)`
  only consults `data/readings_pal.json`.
* **`_phonological_form` ignores the entry's own transcription.** For a pal
  headword written in transliteration (`hwʾb`) the function returns the
  *spelling* unchanged, although the glossary entry beside it records
  `xwāb` in `translit`. A one-line change there would let Persian's
  transliteration ancestors start from their reading. It is `src/`, so it is
  proposed, not made:

  ```python
  # src/pie/service.py, _phonological_form, after `stated = script.read(...)`
  stated = script.read(lang, word)
  if not stated and entry:
      # The dictionary may record the transcription beside the spelling
      # (hwʾb / xwāb); a spelling is not a string of segments.
      stated = (entry.get("translit") or "").strip() or ""
  if stated and not any(ord(ch) >= 0x370 for ch in stated):
      return detokenize(tokenize(stated)) or word
  ```
  It must not be applied blind: 63 of 616 entries have a transcription in that
  field and some of those fields hold apparatus (`ypytl | M y ydt N ~`), so the
  guard must reject anything with `|`, `=`, a digit or a space.
* **The 27 ladders of `pal.md` §4b are unchanged**, and they are still the
  worklist: `hp̄t'` and `ʾp̄ʾt'` are pure notation (now read, #17 and #22/#23),
  `bpl`/`clp` need a *-lp → -rb law that no source states, `bywl` needs a final
  *-ā → -ar nobody has written, `kʾlwʾn'` and `nyšʾn'` have a wrong ancestor
  cell in the record itself (a data fault, not a law).

## 6 · A bug found in the engine, with its patch

`src/pie/script.py` folds the *reading* to one letter per sign
(`_base_letters`: `š` → s, `č` → c, `ḥ` → h) but never folds the table's
`sounds`, so **any sign whose value carries a diacritic can never match**:
`script.match("pal", "š", "𐭱")` is `False` today, and the same holds for
č, ž, ḥ, ṭ, ẓ — in `pal` and in every other table written with philological
diacritics. That is why `pal`'s script column was 1 and not more, and it costs
8 of the 32 refused dictionary pairs.

```python
# src/pie/script.py, in table():
def _fold(x: str) -> str:
    """A sound in the single-letter form _base_letters gives a reading."""
    letters = _base_letters(x)
    return letters[0][0] if len(letters) == 1 else x

"sounds": [_LENGTH_FOLD.get(_fold(s), _fold(s)) for s in sounds] or sounds,
```

Measured with that fold applied in-process (no file touched):

| | today | with the fold |
|---|---:|---:|
| `pal` explained | 18 | **20** |
| `pal` script column | 17 | **19** |
| dictionary pairs read | 48 / 80 | **56 / 80** |
| `fa` | 373 | 373 (no change) |

It cannot loosen anything: both sides of the comparison lose the same
distinction, exactly as `data/script/fa.yaml` already assumes when it says its
sounds "are written in that folded alphabet".

## 7 · Files

* `data/script/pal.yaml` — the 21 transliteration rows, the header paragraph
  that names the third notation, and the notes giving each letter's origin.
  No sign of the Pahlavi or Manichaean blocks was changed; no value was
  removed.
* `tests/test_batch_pal.py` — 7 tests: every letter renders the sign it
  claims and adds only the stated matres; no short vowel and no capital is a
  letter; an unfilled sign and a missing consonant are refused; the
  dictionary's six quoted pairs are read; and a floor (45) on the 80 pairs the
  lexicon states, so a later sign edit cannot quietly stop reading them.
* `proposals/2026-09-11-b/pal/report.md` — this file.
* Not written, and why: `data/spelling/pal.yaml` (a pal headword *is* a
  spelling, so an orthographic layer would duplicate this one, and the
  orthographic column also demands an IPA that pal entries do not carry);
  `data/rules/ira-pro__pal.yaml` (§4); every law change (§4).

## 8 · Gates

* `PYTHONPATH=src python3 -m pie.cli check-rules` — **29 rule files, 698
  rules, 965 examples, 0 problems**.
* `PYTHONPATH=src python3 -m unittest discover -s tests -q` — **509 tests, OK**
  (502 before, 7 new).
* `node tests/test_ui_render.js` — recorded starts, overall progress bar, join
  timeline and coverage buckets: ok.
