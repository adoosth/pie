# Old Persian: what the 375 entries are, what is missing, and why 74 of 133 tested words miss

- **Status:** open — measurements, defects and ready-to-run commands; no rule, script, or
  data file outside the write scope was touched.
- **Stream:** W1 (inventory/completeness), W2/W3 (measured defects), W4 (proposals), W7 (metric gap).
- **Author:** subagent, night of 2026-11-09. **Repo:** `083dfe5` + other agents' uncommitted work.
- **Write scope used:** `data/lexicon/_supplement/peo.jsonl.gz` (tool-written; left byte-identical) and
  this file. `data/spelling/peo.yaml` was investigated and deliberately **not** written (§5).
- **Headline:** the Old Persian glossary is complete under the project's own entry bar; the 74 misses
  are 8 words where no law can fire, 12 words whose ancestry is a bare root, 11 words written with the
  **Median** consonant (the biggest law-shaped defect), and the rest ancestry/paradigm shape. Three
  concrete defects and their minimal fixes are in §4.

Reproduce every number below from the repo root:

```bash
PYTHONPATH=src python3 tools/coverage.py --langs peo --limit 0 --out /tmp/cov_before.json
PYTHONPATH=src python3 -m pie.cli check-rules
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

(The uncommitted changes another agent has made to `tools/coverage.py` only add the ancestry
classification; `measure()` — the numbers used here — is unchanged.)

## 1 · Inventory

### Where the 375 rows come from

| source | rows | how it reaches the glossary |
|---|---:|---|
| Wiktextract dump (`OldPersian.jsonl`) | 262 | `tools/build_lexicons.py` |
| hand-written supplement rows | 3 | `data/lexicon/_supplement/peo.jsonl.gz` (`raupāθah`, `𐎭𐎡𐎺`, `𐎲𐎠𐏀𐎢`) |
| curated Wiktionary/Kent rows | 110 | `data/lexicon/_supplement/peo_entries.json` → `tools/ingest_op_entries.py` |
| **total** | **375** | 365 distinct headwords — 10 headwords are two lexical entries (`𐎱𐎠𐎼𐎿` noun + name, `𐎠𐎲𐎡𐎹` prefix + prep, `𐎸𐎭𐎼𐎠𐎹` adj + name, `𐎱𐎼𐎰𐎺` adj + name, `𐏂` ×2, `𐎿𐎣𐎠` ×2, plus `𐎠𐎡𐎺`, `naftah`, `ciθrah`, `kapautah`) |

`data/lexicon/peo.jsonl.gz` holds the *merged* result; `data/lexicon/_supplement/peo.jsonl.gz` holds
113 rows (3 hand + 110 curated). A supplement row never overwrites a dump row.

### What `exact` and `script` mean for Old Persian

- **exact** (`tools/coverage.py:179–212`): derive from any ancestor the entry records at a modelled
  stage (`ancestor_starts`), require **at least one law to fire**, and require `d.output == entry["word"]`
  character for character. For a cuneiform headword this is unreachable *by construction*: the laws
  write a phonemic string (`wˈarkah`) and the glossary stores `𐎺𐎼𐎣`. Hence **0** exact, and
  `exact` for OP can only move if the headword were phonemic.
- **script** (`tools/coverage.py:245–260`, `src/pie/script.py:match`): the laws' output is a *possible
  reading* of the cuneiform signs — consonants must match, vowels the scribe wrote must be present, and
  the declared gaps of the syllabary are allowed (a sign's inherent vowel unused as a filler, a word-final
  /h/ unwritten, a final -i closed with the y-sign). It requires ≥1 law, is its own column, and is never
  added to `exact`.
- **through their script** therefore means: *the form the laws produced is one of the readings the
  monument's signs allow* — not that the dictionary's transliteration was reproduced.

### The funnel (peo, full run)

| stage | rows | share |
|---|---:|---:|
| glossary rows | 375 | 100% |
| with a recorded ancestor at a modelled stage (`identified`) | 219 | 58.4% |
| PIE-linked | 84 | 22.4% |
| reconstruction rows (`recon`, Latin headwords) | 97 | — |
| … of which eligible for derivation | 86 | — |
| … of which derived exactly | 2 | `daθapatiš`, `spādapatiš` |
| attested rows | 278 | — |
| … with no usable ancestor | 145 | — |
| … **tested** (ancestor + ≥1 law possible) | **133** | 100% of attested eligible |
| … **exact** | **0** | 0% |
| … **through their script** | **59** | 44.4% of tested |
| … **miss** | **74** | 55.6% of tested |
| orthographic (no `data/spelling/peo.yaml`) | 0 | — |

Details of the 59 script matches: 17 start at PIE, 23 at Proto-Indo-Iranian, 19 at Proto-Iranian;
7 rest on the `final_i_iy` convention; 27 involve at least one unwritten letter (usually the final /h/);
**2 are logograms** compared by value (`𐏎` *baga*, `𐏏` *būmiš*), 57 are read sign by sign.

> Caveat worth keeping: because coverage tries *every* recorded ancestor, a script match may rest on a
> law from an earlier transition. `𐎭𐎠𐎼𐎹𐎫𐎡𐎹 dārayatiy` is the clearest case — the OP transition
> fires nothing; the only law in its whole ladder is `deaspirate_dh` (PIIr→PIr). With `ira-pro *dāráyati`
> as the start it would not count at all.

## 2 · Completeness (the fetch and what it found)

### Command

```bash
# snapshot Wiktionary's Old Persian lemma and form pages through the tool's own parser
PYTHONPATH=src python3 - <<'PY'
import sys, json; sys.path.insert(0, "tools")
import ingest_op_entries as ing
json.dump({"rows": ing.candidate_rows()}, open("/tmp/peo_candidates.json", "w"),
          ensure_ascii=False, indent=1)
PY
```

`tools/ingest_op_entries.py --fetch` is the same call and writes
`data/lexicon/_supplement/peo_candidates.json`, which is git-ignored; I kept the snapshot in `/tmp`
to avoid writing anything outside the declared scope. The parser, User-Agent and category walk
(`Old Persian lemmas` depth 3 + non-lemma/verb/noun form categories) are the tool's, unmodified.

### Result: 594 candidate pages

| candidate kind | pages | already in the glossary | genuinely missing |
|---|---:|---:|---:|
| cuneiform headwords | 337 | **268** | 69 |
| `Reconstruction:Old Persian/…` (Latin, not attested) | 257 | 94 (as `recon` rows) | 163 |

The glossary therefore covers **268 of 337 = 79.5%** of Wiktionary's cuneiform Old Persian pages.
The 69 that are not in it, one by one against the entry bar the corpus documents in `AGENTS.md`
(“letters of the script, number signs, starred reconstructions, phrases and inflection-only pages are
not entries”; overlap is checked on the headword and the normalised reading):

| why it is not an entry | pages | examples |
|---|---:|---|
| letter of the syllabary | 34 | `𐎠` “first letter of the Old Persian cuneiform script” |
| number sign or the word divider | 5 | `𐏑` 1, `𐏒` 2, `𐏓` 10, `𐏔` 20, `𐏕` 100, `𐏐` |
| multi-word phrase | 9 | `𐎹𐎢𐎴𐎠 𐏐 𐎫𐎹𐎡𐎹 𐏐 𐎱𐎼𐎭𐎼𐎹` |
| inflection or alternative-form page | 14 | `𐎠𐎼𐎷𐎡𐎴𐎶` “acc s of 𐎠𐎼𐎷𐎡𐎴”, `𐏃𐎫𐎡𐎹` “3 p pres ind of 𐎠𐎿𐎫𐎡𐎹”, `𐎳𐎼𐎠𐎲𐎼` “he gave” |
| logogram or spelling of a lexeme already entered | 7 | `𐏊` (gen. of `𐏉`), `𐏌`/`𐏍` *country* (= `𐎭𐏃𐎹𐎠𐎢`), `𐎶𐎦𐎢𐏁` (= `𐎶𐎦𐏁`), `𐎹𐎢𐎴𐎠` (= `𐎹𐎢𐎴`), `𐎿𐎣` (= `𐎿𐎣𐎠`), `𐏃𐎾𐎮𐎫` (= `𐏃𐎾𐎮𐎡𐎫`) |
| **total** | **69** | |

**Nothing was added.** The identical check the previous ingest used (2026-11-08, “four otherwise-new
pages … dropped because the glossary already records that reading”: `𐎧𐏁𐎠𐎹𐎰𐎡𐎹`, `𐎲𐎥`,
`𐎶𐎦𐎢𐏁`, `𐎿𐎣`) is still the right answer for today's snapshot. **Before → after: 375 → 375 rows;
supplement 113 → 113.** The tool is idempotent and keeps the hand rows; this run proves it:

```
$ sha256sum data/lexicon/_supplement/peo.jsonl.gz
aa2923f0…8bb4e8
$ PYTHONPATH=src python3 tools/ingest_op_entries.py
data/lexicon/_supplement/peo.jsonl.gz: 3 hand rows + 110 curated rows
$ sha256sum data/lexicon/_supplement/peo.jsonl.gz
aa2923f0…8bb4e8      # identical bytes
```

If the integrator decides that a **logogram is an entry** (the dump already carries `𐏈`, `𐏉`, `𐏋`,
`𐏎`, `𐏏`, so `𐏌`/`𐏍` are the only missing ones), these are the two rows the tool accepts as-is
(`sources`, `ref`, `url` from the live page of 2026-11-09; `translit` is the sign, `translit_alt` the
reading):

```json
{"word": "𐏌", "lang": "peo", "pos": "noun", "gloss": ["country"], "translit": "DH",
 "translit_alt": ["dahyāuš"], "sources": ["wiktionary"], "source": "wiktionary",
 "ref": "en.wiktionary.org, Old Persian 𐏌 (dahyāuš), noun: “country”.",
 "url": "https://en.wiktionary.org/wiki/%F0%90%8F%8C", "generator": "op-ingest"}
{"word": "𐏍", "lang": "peo", "pos": "noun", "gloss": ["country"], "translit": "DH",
 "translit_alt": ["dahyāuš"], "sources": ["wiktionary"], "source": "wiktionary",
 "ref": "en.wiktionary.org, Old Persian 𐏍 (dahyāuš), noun: “country”.",
 "url": "https://en.wiktionary.org/wiki/%F0%90%8F%8D", "generator": "op-ingest"}
```

They would make 377 rows, all with no ancestor (no number moves). My recommendation is **not** to add
them: they write a lexeme the glossary already has, exactly like the four pages the 2026-11-08 ingest
rejected. That is a reviewer decision, and it needs a new artefact (`data/lexicon/_supplement/peo_entries.json`)
which is outside this session's write scope anyway.

## 3 · Verification, word by word

Format: the ladder the laws actually produce (each stage named), the laws that fired, what the signs
say, and — for a miss — the law, the step and the segment that decides it. Every ladder below was
generated from `data/lexicon/peo.jsonl.gz` with `tools/coverage.py`'s own `ancestor_starts()`; the
largest ancestor form is the one printed first, the nearest one last.

### 3.1 What lands (6 of the 59)

#### `𐎠𐎡𐎫𐎡𐎹` aiti ‘goes’ — **script ✓**
`PIE h₁éyti → PIIr Hˈayti → PIr Hˈayti → OP ˈaiti`
laws: `laryngeal_to_H`, `vowel_merger_a`, `laryngeal_loss_initial` (deletes word-initial *H-),
`ay_to_ai` (*-ay- → -ai- before t). Signs `a-i-ta-i-ya`: the *ta* sign's own a is a filler, the final
*y* is the `final_i_iy` convention. **It lands** because the last two laws change the only two segments
the record needs (*ai* and the final *i*), and the syllabary's filler and closing sign are declared
gaps. Dropping `ay_to_ai` loses it (`-2` script matches, §4).

#### `𐎭𐎠𐎼𐎹𐎫𐎡𐎹` dārayatiy ‘to hold’ — **script ✓**
`PIE dʰer → PIIr dʰāráyati → PIr dārˈayati → OP dārˈayati`
laws: `vowel_merger_a` (PIE), `deaspirate_dh` (PIIr→PIr). Signs `da-a-ra-ya-ta-i-ya`: fillers `[1, 4]`,
final *i* closed as `i-y`. **It lands** on the *script* reading of `dārˈayati` (the record writes the
final *-iy*, the laws stop at *-i*). **Caveat:** no Old Persian law fires — the only law in the whole
ladder is `deaspirate_dh`, an earlier transition. Coverage counts it because it accepts any ancestor;
from the nearest ancestor (`PIr dāráyati`) it would be a zero-law miss (see §4.4).

#### `𐎭𐎿𐎫` dastaʰ ‘hand’ — **script ✓**
`PIE ǵʰóstos → PIIr ȷ́ʰástas → PIr jˈastah → OP dˈastah`
laws: `vowel_merger_a`, `satem_gh`, `deaspirate_palatal`, `final_s_to_h`, `j_from_palatal`, **`j_to_d`**.
Signs `da-sa-ta` (the *sa* sign's a is a filler; final *h* unwritten). **It lands** because `j_to_d`
turns PIIr *ȷ́ʰ- into OP d-, the pure-OP reflex of Kent (1953) §88. This is the law the Median words
below need switched *off*, and the measurement (§4) shows it carries five script matches.

#### `𐎲𐎼𐎠𐎫𐎠` brātā ‘brother’ (reconstruction row) — **script ✓**
`PIE bʰréh₂tēr → PIIr bʰráHtā → PIr brˈātā`
laws: `h2_colours_e`, `laryngeal_to_H`, `long_vowel_merger`, `deaspirate_bh`, **`laryngeal_lengthening`**.
Signs `ba-ra-a-ta-a` (three fillers). **It lands** on `laryngeal_lengthening` (*aH > ā), the law that
carries 2 of the 59 (with `𐎭𐎠𐎫`).

#### `𐎧𐏁𐏂𐎶` xšaçam ‘realm’ — **script ✓**
`PIIr kšatrám → PIr xšaθrˈam → OP xšaçˈam`
laws: `t_to_theta_before_sonorant`, `k_to_x_initial`, **`theta_r_to_cedilla`**. Signs `xa-ša-ça-ma`
(fillers `[0, 3]`). **It lands** on the *θr > ç* law (Kent 1953 §80); dropping it loses 4 script
matches (`xšaçam`, `puça`, `čiça`, `Artaxšaça`).

#### `𐎱𐎡𐎫𐎠` pitā ‘father’ — **script ✓**
`PIr pHtā́ → OP pitˈā`
laws: **`laryngeal_lengthening`** (deletes the *H, leaves ptā), **`anaptyxis_initial_pt`** (*pt- > pit-,
`tier: proposed`, `optional: true`). Signs `pa-i-ta-a` (fillers `[0, 3]`). **It lands**, but on an
optional proposed rule: dropping it loses exactly this word (§4). The honest status is "explained by
one proposed law", not "explained".

### 3.2 What misses, and exactly where (31 of the 74)

#### `𐎱𐎠𐎼𐎿` pārsa ‘Persian’ (two rows: noun ‘a Persian’, name ‘Persis’) — **miss**
`PIr párcuš → OP pˈarθuš` (laws: `c_to_theta`). Record: `pa-a-ra-sa` = **pārsa**.
Segments: *p* = p ✓; *á* vs *ā* (the cuneiform writes a, length invisible); **θ vs s — the fatal one**;
final *-uš* vs *-a* (a different formation).
Kent (1953) §9, s.v. *Pārsa*: “with s from ḱ … the name seems to have been imposed by an outside
source”; §86: OP has **θ and d in pure OP, s and z in words borrowed from Median**. So `c_to_theta` is
not wrong — it is the pure-OP law, and *Pārsa* is not pure OP, plus Wiktionary's etymon `*párcuš` has
the wrong shape. **Minimal fix:** an off-by-default Median `c → s` rule (the twin of the registered
`j_to_z_median`) enabled by *Pārsa*'s pathway, and the right ancestor (`*pā́rçah`); no change to
`ira-pro__peo.yaml`. Measured: swapping the default gains only `𐎠𐎿` and loses `𐎰𐎼𐎭`, i.e. a default
flip is wrong (§4).

#### `𐎠𐎿` asaʰ ‘horse’ — **miss**
Two ladders: `PIE h₁eḱ → … → OP aθ` (the root only: *-wo- is absent from the ancestry) and
`PIr Hácwah → OP ˈaspah` (`laryngeal_loss_initial`, **`cw_to_sp`**). Record `a-sa` = asa.
**Segment: sp vs s.** Kent §90: PIE *ḱw became **Med. sp, Av. sp, OP s** — the OP word is
asa- (acc. *asam*, *asabāra-*), *aspa-* is the Median form (Vištāspa, Aspacanā). `cw_to_sp` is
therefore the **Median** outcome registered as the OP default. **Minimal fix:** keep `cw_to_sp` for
the Median words and add an off-by-default OP `cw → s` for asa/asabāra's pathways — a default flip is
measured to be net zero (`+asa +asabāra −aspa −spāda`).

#### `𐎠𐎿𐎲𐎠𐎼` asabāra ‘horseman’ — **miss**
`PIIr Haćwabʰāras → PIr Hacwabārah → OP aspabārah` (`deaspirate_bh`, `final_s_to_h`,
`c_from_palatal`, `laryngeal_loss_initial`, `cw_to_sp`). Record `a-sa-ba-a-ra` = asabāra.
Same segment as asa: **sp vs s**, both from *ćw; Kent §90 names *asabāra-* as the OP form.

#### `𐎠𐎿𐎶𐎴` asman ‘sky’ — **miss**
`PIIr Háćmā → PIr Hˈacmā → OP ˈaθmā` (`c_from_palatal`, `laryngeal_loss_initial`, `c_to_theta`).
Record `a-sa-ma-na` = asman. Two segments: **θ vs s** (Kent §87 lists *asman-* with Median s), and
final *-ā* vs *-an*: the ancestor is the nom. sg. *aćmā*, the OP word is the *-an* stem. Even a
`c → s` pathway would leave *asma* vs *asman*, so this one needs W1/W5 (stem) as well.

#### `𐎣𐎠𐎿𐎣` kāsakaʰ ‘glass’ — **miss**
`PIIr kā́ćti → PIr kˈācti → OP kˈāθti` (`c_from_palatal`, `c_to_theta`); the nearer ancestor
`PIr kā́šti` fires nothing (`kˈāšti`). Record `ka-a-sa-ka` = kāsaka.
Segments: **θ vs s** (Kent §9: “kāsaka … with s from ḱ”), **and** the ancestral stem is wrong (*-ti*,
*š*, no *-ka*). Needs the Median pathway **and** the right etymon (*kā́çakah*).

#### `𐏀𐎴` zana ‘man’ — **miss**
`PIE ǵónh₁os → PIIr ȷ́ˈanHas → PIr jˈanHah → OP dˈanah` (`satem_g`, `final_s_to_h`, `j_from_palatal`,
`laryngeal_lengthening`, **`j_to_d`**). Record `za-na`. **Segment: d vs z.** Kent §88: “PIr *ǵ > OP d,
Med. z … OP zana- ‘man’ **with Med. z**; OP d is seen in *visa-dana-*”. The off-by-default
`j_to_z_median` already exists **for this class**; zana has no pathway enabling it (and `j_to_d` must
be disabled on that pathway). Measured: the swap gains zana and vazraka, loses five d-words → the
default is right, the pathway is missing.

#### `𐎺𐏀𐎼𐎣` vazr̥kaʰ ‘great’ — **miss**
`PIIr wáȷ́ras → PIr wˈajrah → OP wˈadrah` (`final_s_to_h`, `j_from_palatal`, `j_to_d`). Record
`va-za-ra-ka` = vazraka. **Segment: d vs z** (Kent §9: “vazraka ‘great’, with z from ǵ”), **and** the
ancestor is the noun *wáȷ́ras* ‘club’, not the adjective *wazraka-*: the *-ka* is not in the chain.

#### `𐎲𐎠𐏀𐎢` bāzu ‘arm’ — **miss**
`PIE bʰeh₂ǵʰús → PIIr bʰaHȷ́ʰúš → PIr baHjˈuš → OP bādˈuš` (`satem_gh`, `ruki_s`, `deaspirate_bh`,
`deaspirate_palatal`, `j_from_palatal`, `laryngeal_lengthening`, `j_to_d`). Record `ba-a-za-u` = bāzu.
**Segments: d vs z and final -uš vs -u.** The Median rule `j_to_z_median` was *written for this word*
(its examples name bāzu) but bāzu has **no pathway** turning it on, and the ancestor is the nom. sg.
*-uš* while the record is the stem *bāzu*. Two fixes, neither a new law.

#### `𐏃𐏀𐎠𐎴𐎶` hⁱzānam ‘tongue’ — **miss**
`PIr hijwáH → OP hidwˈā` (`laryngeal_lengthening`, `j_to_d`). Record `ha-za-a-na-ma` = hazānam.
**Segments: j→z (Median; Kent §91), and *-wā vs -āna-**: the OP word has an *n* the ancestor does not
(*hazāna-* vs Avestan *hizuuā-*). Median pathway + a different stem.

#### `𐎠𐏀𐎭𐎠` azdā ‘known’ — **miss**
`PIIr adᶻdʰáH → PIr adᶻdˈā` (`deaspirate_dh`, `laryngeal_lengthening`). Record `a-z-da-a` = azdā.
**Segment: the affricate *-dz- vs z** — the ancestor's `dᶻ` is one affricate, the record has a simple z
(Kent §85, *-dzd-/-tst-* outcomes). Single word; a general rule *dz > z would need its own evidence.

#### `𐎠𐎼𐏁𐎴𐎡` arašni ‘cubit’ — **miss**
`PIIr Haratníš → PIr Haraθnˈiš → OP araθnˈiš` (`t_to_theta_before_sonorant`,
`laryngeal_loss_initial`). Record `a-ra-ša-na-i` = arašni. **Segments: θ vs š** before *n*, and final
*-iš* vs *-i*. The θ-before-sonorant law is right for *θarda-* etc.; OP *arašni* shows the further step
*θn > šn* (Kent s.v. *arašni*, Skt. *aratní-*), and the ancestor is the nom. sg.

#### `𐎱𐎠𐎮𐎹` pādiy ‘to protect’ — **miss**
`PIE peh₂ → PIIr paH → PIr paH → OP pā` (`h2_colours_e`, `laryngeal_to_H`,
`laryngeal_lengthening`). Record `pa-a-di-y` = pādiy. **Segment: the whole suffix is absent** — the
ancestry is the bare root *peh₂ / *paH, the word is the present stem *pādaiya-*. No sound law can
invent a suffix: this is a **formation/paradigm** gap (W5) plus a W1 ancestry link. The final *-iy* is
the script's `final_i_iy` and would read *pādi* correctly.

#### `𐎣𐎠𐎶` kāmaʰ ‘wish’ — **miss**
`PIE keh₂ → OP kā` (`h2_colours_e`, `laryngeal_to_H`, `laryngeal_lengthening`). Record `ka-a-ma` =
kāma. **Segment: the -ma- suffix is absent** (ancestry is the root only). W1/W5, not a law.

#### `𐎭𐎠𐎫𐎶` dātam ‘law’ — **miss**
`PIE deh₃ → OP dā` (`h3_colours_e`, `laryngeal_to_H`, `vowel_merger_a`,
`laryngeal_lengthening`). Record `da-a-ta-ma` = dātam. **Segment: the participial -ta- is absent**.
Same root-only ancestry.

#### `𐎭𐏃𐎹𐎠𐎢` dahyau ‘land’ — **miss**
`PIE des → OP dah` (`vowel_merger_a`, `final_s_to_h`) and `PIIr dásyuš → PIr dˈahyuš → OP dˈahyuš`
(`s_to_h`, no OP law). Record `da-ha-ya-a-u` = dahyau. **Segments: the *-yu-* is missing from the root
start, and the nom. sg. *-uš* must be *-au*.** Ancestry + ending, not a law.

#### `𐎣𐎠𐎼` kāraʰ ‘people, army’ — **miss (no law fires)**
`PIr kā́rah → OP kˈārah` — **zero laws**. The record is `ka-a-ra` + unwritten final *h*: the script fit
is **yes** (`kˈārah` reads `ka-a-ra`), but coverage refuses a word with no law
(“an unchanged ancestor is not evidence”). The PIr reconstruction *is* the OP word. This is a
**metric** fact, not a gap: 8 words are in this bucket (§4.4).

#### `𐎧𐏁𐎱` xšapaʰ ‘night’ — **miss (no law fires)**
`PIr xšáfš → OP xšˈafš` — **zero laws**. Record `xa-ša-pa` = xšapa. The ancestor is the nom. sg. of
the *f*-stem *xšap-*; the OP word is the thematic *xšapa-*. A paradigm mismatch (W5), and nothing
changed, so no law is credited.

#### `𐎱𐎫𐎡𐎣𐎼` patikaraʰ ‘image’ — **miss (no law fires)**
`PIr patikárah → OP patikˈarah` — **zero laws**. Record `pa-ta-i-ka-ra`; the script fit is **yes**
(the *ta* sign's a is a filler, final *h* unwritten). Same bucket as kāra.

#### `𐎭𐎠𐎽𐎢𐎺` dāruv ‘wood’ — **miss (no law fires)**
`PIr dā́ru → OP dˈāru` — **zero laws**. Record `da-a-ru-u-va`; the script **does** read `dˈāru`
(fillers `[1, 2, 4]`), so even the final *-v* of Kent §114 is covered by the table's fillers. The only
thing missing is a law that fires.

#### `𐎢𐎱𐎼𐎡𐎹` upariy ‘over’ — **miss (no law fires)**
`PIr upári → OP upˈari` — **zero laws**; the script fits with the `final_i_iy` convention. Same bucket.

#### `𐎶𐎼𐎫𐎡𐎹` martiyaʰ ‘man’ — **miss (no law fires)**
`PIr mártyah → OP mˈartyah` — **zero laws**. Record `ma-ra-ta-i-ya`: the *i*-sign between *t* and *y*
writes **no vowel** (Kent §31: the sequence *-arty-*; the syllabary writes *-ti-y-* for *-ty-*).
Dropping that sign from the alignment makes the fit exact (verified): the missing piece is a **script
convention** (“an i-sign before the y-sign adds no vowel”), not a law.

#### `𐎠𐎼𐎡𐎹` Aryaʰ ‘Iranian’ — **miss**
`PIIr Áryas → PIr Áryah → OP Áryah` (`final_s_to_h`). Record `a-ra-i-ya` = arya. The same i-before-y
convention; with the i-sign read as graphic the fit is exact (verified). Note the capital *Á*: the
script comparison lowercases, so it is harmless here, but any **word-initial law** matching `a` would
silently skip a capitalised reconstruction (see harauvatiš).

#### `𐎠𐎴𐎡𐎹` aniyaʰ ‘other’ — **miss**
`PIIr Hanyás → PIr Hanyˈah → OP anyˈah` (`final_s_to_h`, `laryngeal_loss_initial`). Record
`a-na-i-ya` = anya. The same i-before-y convention (+1 with it, verified).

#### `𐎠𐎰𐎥` aθaⁿgaʰ ‘stone’ — **miss**
`PIr Hacangáh → OP aθangˈah` (`laryngeal_loss_initial`, `c_to_theta`). Record `a-θa-ga` = aθaⁿga:
the **n is not written**. Kent §111 “OP Unwritten Medial Nasals” lists precisely *abaⁿga-* ‘stone’.
Allowing one unwritten nasal makes the fit exact (verified).

#### `𐎠𐎫𐎼` aⁿtar ‘inside’ — **miss**
`PIE h₁énteros → PIIr Hántaras → PIr Hántarah → OP ˈantarah` (`laryngeal_to_H`, `vowel_merger_a`,
`final_s_to_h`, `laryngeal_loss_initial`). Record `a-ta-ra` = aⁿtar. **The n is unwritten** (Kent §111
lists *aⁿtar*). With the nasal convention the fit is exact (verified).

#### `𐏃𐎡𐎯𐎢𐏁` Hiⁿduš ‘India’ — **miss (no law fires)**
`PIr hínduš → OP hˈinduš` — **zero laws**. Record `ha-i-du-u-ša`; the *n* is unwritten (Kent §111
lists *Hiⁿduš*). It needs the nasal convention *and* a law that fires.

#### `𐏃𐎼𐎢𐎺𐎫𐎡𐏁` Harauvatiš ‘Arachosia’ — **miss**
`PIIr SáraswatiH → PIr SˈarahwatiH → OP Sˈarahwatī` (`s_to_h`, `laryngeal_lengthening`).
Two defects: (a) the reconstruction's **capital S** is notation, and `s_to_h` matches lowercase `s`,
so the word-initial law skips it — feeding `sáraswatiH` gives `hˈarahwatiH` (verified
`pie derive --from iir-pro --to peo 'sáraswatiH'`); (b) PIr *-ahw- becomes OP **-auv-** (`ha-ra-u-va`),
which no rule models. Even then, final *-ī* vs *-iš* remains.

#### `𐎬𐎺𐎶` tuvam ‘you’ — **miss**
`PIE túh₂ → OP tˈū` and `PIr tuHám → OP tūˈam` (`laryngeal_lengthening`). Record `tu-va-ma` = tuvam.
**Segment: *-H- vs -v-** between vowels: *tuHám > tuvam* (Kent §114: “acc. @uvām, Skt. tvam; but
dissyllabic OP tuvam”). `laryngeal_lengthening` is right word-initially; an intervocalic *H* becomes
*v*, and that rule is missing.

#### `𐎭𐎭𐎠𐎬𐎢𐎺` dadātūv ‘to give’ — **miss**
`PIr dádaHti → OP dˈadāti` (`laryngeal_lengthening`). Record `da-da-a-tu-u-va` = dadātūv.
**Segments: -ti vs -tūv** — the record is the 2 sg. imperative in *-tūv*, the ancestor is the 3 sg.
present. A paradigm/ending gap (W5); no law turns *-ti* into *-tūv*.

#### `𐎰𐎠𐎫𐎡𐎹` θātiy ‘says’ — **miss**
`PIIr ćánsati → PIr cˈanhati → OP θˈanhati` (`s_to_h`, `c_from_palatal`, `c_to_theta`). Record
`θa-a-ta-i-ya` = θātiy. **Segment: the whole stem** — θ- is right (`c_to_theta` is doing its job), but
the ancestor is the present *ćánsati* ‘announces’ and the word is the *θā-* stem: the derived
*θanhati* is a different word. Ancestry/formation, not a sound law.

#### `𐏃𐎥𐎶𐎫𐎠𐎴` Haⁿgmatānaʰ ‘Ecbatana’ — **miss**
The only ancestry is the PIE root `sem → sam → ham` (`vowel_merger_a`, `s_to_h`). Record
`ha-ga-ma-ta-a-na`. **The whole word is absent** from the ancestry (root-only), plus the unwritten
nasal (Kent §111). W1, not a law.

#### `𐎻𐎡𐎭𐎳𐎼𐎴𐎠` Viⁿdafarnāʰ ‘Intaphernes’ — **miss**
`PIr WindáhuHarnāh → OP Windˈahūarnāh` (`laryngeal_lengthening`). Record `vi-i-da-fa-ra-na-a`.
**Segments:** (a) *-hū-* vs *-far-* — the second element should be *farnāh* (Kent §118.IV), the
ancestor's shape is wrong; (b) the nasal before *d* is unwritten (Kent §111 lists *Viⁿdafarnā*);
(c) initial *wi-* vs *viⁿ-* is notation. Ancestry + nasal convention.

### 3.3 Appendix — all 74 misses, with the first segment where the best derivation leaves the record

`reading` is the dictionary's own reading where the entry records one (`—` when it records only a
sign transliteration); `derived` is the closest form the laws produce; the last column shows the
derived string against the recorded reading at the first divergence (`∅` = one side is exhausted).
Reproduce with `tools/coverage.py --langs peo --limit 0 --out /tmp/cov.json` plus the ladder dump in §5.

| headword | reading | derived | first divergence |
|---|---|---|---|
| `-𐎡𐎣` | -ikah | `ikah` | [i] vs [-] |
| `-𐎨𐎠` | — | `ka` | — |
| `𐎠𐎫𐎼` | aⁿtar | `ˈantarah` | a[n] vs a[ⁿ] |
| `𐎠𐎰𐎥` | aθaⁿgaʰ | `aθangˈah` | aθa[n] vs aθa[ⁿ] |
| `𐎠𐎱𐎡𐎹𐎠` | apiyā | `ap` | ap[∅] vs ap[i] |
| `𐎠𐎴𐎡𐎹` | aniyaʰ | `anyˈah` | an[y] vs an[i] |
| `𐎠𐎶𐏃𐎹` | aʰmahạy | `hmˈah` | [h] vs [a] |
| `𐎠𐎼𐎡𐎹` | Aryaʰ | `Áryah` | aryah[∅] vs aryah[∅] |
| `𐎠𐎼𐎭𐎫` | — | `ˈardatam` | — |
| `𐎠𐎼𐎭𐎿𐎫𐎠𐎴` | ardastānaʰ | `ˈardah` | arda[h] vs arda[s] |
| `𐎠𐎼𐏁𐎣` | R̥šakaʰ | `ˈaršah` | [a] vs [r] |
| `𐎠𐎼𐏁𐎴𐎡` | arašni | `araθnˈiš` | ara[θ] vs ara[s] |
| `𐎠𐎿` | asaʰ | `ˈaspah` | as[p] vs as[a] |
| `𐎠𐎿𐎱𐎨𐎴` | Aspacanāʰ | `čˈanah` | [c] vs [a] |
| `𐎠𐎿𐎲𐎠𐎼` | asabāra | `aspabārah` | as[p] vs as[a] |
| `𐎠𐎿𐎶𐎴` | asman | `ˈaθmā` | a[θ] vs a[s] |
| `𐎠𐏀𐎭𐎠` | azdā | `adᶻdˈā` | a[d] vs a[z] |
| `𐎢` | ʰu | `su` | [s] vs [h] |
| `𐎢-` | ʰu- | `hu` | hu[∅] vs hu[-] |
| `𐎢𐎫𐎠𐎴` | ʰUtānaʰ | `tˈānah` | [t] vs [h] |
| `𐎢𐎱𐎼𐎡𐎹` | upariy | `upˈari` | upari[∅] vs upari[y] |
| `𐎣𐎠𐎶` | kāmaʰ | `kā` | ka[∅] vs ka[m] |
| `𐎣𐎠𐎼` | kāraʰ | `kˈārah` | karah[∅] vs karah[∅] |
| `𐎣𐎠𐎿𐎣` | kāsakaʰ | `kˈāšti` | kas[t] vs kas[a] |
| `𐎣𐎢𐎳` | kaufaʰ | `kˈaufš` | kauf[s] vs kauf[a] |
| `𐎧𐏁𐎱` | xšapaʰ | `xšˈafš` | xsa[f] vs xsa[p] |
| `𐎫𐎢𐎶𐎠` | taumā | `tˈauxma` | tau[x] vs tau[m] |
| `𐎬𐎺𐎶` | tuvam | `tūˈam` | tu[a] vs tu[v] |
| `𐎭𐎠𐎫𐎶` | dātam | `dā` | da[∅] vs da[t] |
| `𐎭𐎠𐎽𐎢𐎺` | dāruv | `dˈāru` | daru[∅] vs daru[v] |
| `𐎭𐎭𐎠𐎬𐎢𐎺` | dadātūv | `dˈadāti` | dadat[i] vs dadat[u] |
| `𐎭𐎼𐎴𐎡𐎹` | — | `daranyam` | — |
| `𐎭𐏃𐎹𐎠𐎢` | dahyau | `dˈahyuš` | dahy[u] vs dahy[a] |
| `𐎯𐎢𐎼𐎡𐎹` | dūraiy | `dūrˈah` | dura[h] vs dura[i] |
| `𐎯𐎺𐎼𐎹𐎠` | duvarayā | `dwˈār` | d[w] vs d[u] |
| `𐎰𐎠𐎫𐎡𐎹` | θātiy | `θˈanhati` | θa[n] vs θa[t] |
| `𐎰𐎢𐎼𐎺𐎠𐏃𐎼` | θūravāharaʰ | `wāharˈah` | [w] vs [θ] |
| `𐎰𐎵𐎢𐎺𐎴𐎡𐎹` | θanuvaniyaʰ | `dˈanwar` | [d] vs [θ] |
| `𐎱𐎠𐎭` | pādaʰ | `pˈādah` | padah[∅] vs padah[∅] |
| `𐎱𐎠𐎮𐎹` | pādiy | `pā` | pa[∅] vs pa[d] |
| `𐎱𐎠𐎼𐎿` | — | `pˈarθuš` | — |
| `𐎱𐎠𐎼𐎿` | — | `pˈarθuš` | — |
| `𐎱𐎫𐎡𐎣𐎼` | patikaraʰ | `patikˈarah` | karah[∅] vs karah[∅] |
| `𐎱𐎫𐎡𐏁` | — | `pati` | — |
| `𐎱𐎼𐎭𐎹𐎭𐎠𐎶` | paradayadām | `paridaidah` | par[i] vs par[a] |
| `𐎱𐎼𐎰𐎺` | Parθavaʰ | `parθwˈī` | parθ[w] vs parθ[a] |
| `𐎱𐎼𐎰𐎺` | Parθavaʰ | `parθwˈī` | parθ[w] vs parθ[a] |
| `𐎱𐎽𐎢𐎺` | — | `parˈuš` | — |
| `𐎱𐎿𐎫𐎡` | pasti | `pastˈiš` | pasti[s] vs pasti[∅] |
| `𐎲𐎠𐎪𐎶` | — | `bāg` | — |
| `𐎲𐎠𐏀𐎢` | — | `bādˈuš` | — |
| `𐎲𐎥𐎲𐎢𐎧𐏁` | Bagabuxšaʰ | `bˈauxšati` | ba[u] vs ba[g] |
| `𐎴𐎠𐏃𐎶` | — | `nˈās` | — |
| `𐎴𐎡𐎹` | — | `nˈa` | — |
| `𐎴𐎱𐎠` | napā | `nˈapāθ` | napa[θ] vs napa[∅] |
| `𐎶𐎴𐎠` | manā | `mˈana` | mana[∅] vs mana[∅] |
| `𐎶𐎹𐎧` | mayuxa | `mayˈūxah` | ayuxa[h] vs ayuxa[∅] |
| `𐎶𐎼𐎫𐎡𐎹` | martiyaʰ | `mˈartyah` | mart[y] vs mart[i] |
| `𐎺𐏀𐎼𐎣` | vazr̥kaʰ | `wˈadrah` | [w] vs [v] |
| `𐎻𐎡𐎭𐎳𐎼𐎴𐎠` | Viⁿdafarnāʰ | `Windˈahūarnāh` | [w] vs [v] |
| `𐎿𐎢𐎦𐎢𐎭` | Suguda | `skaud` | s[k] vs s[u] |
| `𐏀𐎴` | — | `dan` | — |
| `𐏁𐎡𐎹𐎠𐎫𐎡𐏁` | — | `čyˈātiš` | — |
| `𐏂` | — | `çˈayah` | — |
| `𐏂` | — | `çˈayah` | — |
| `𐏃𐎡𐎯𐎢𐏁` | Hiⁿduš | `hˈinduš` | hi[n] vs hi[ⁿ] |
| `𐏃𐎣𐎼𐎶𐎨𐎡𐎹` | — | `hakart` | — |
| `𐏃𐎥𐎶𐎫𐎠𐎴` | Haⁿgmatānaʰ | `ham` | ha[m] vs ha[ⁿ] |
| `𐏃𐎶𐎼𐎴` | hamarana | `hamˈaranam` | arana[m] vs arana[∅] |
| `𐏃𐎼𐎢𐎺𐎫𐎡𐏁` | Harauvatiš | `Sˈarahwatī` | [s] vs [h] |
| `𐏃𐏀𐎠` | — | `didwˈā` | — |
| `𐏃𐏀𐎠𐎴𐎶` | hⁱzānam | `hidwˈā` | h[i] vs h[ⁱ] |
| `𐏃𐏁𐎡𐎹𐎶` | hašiyam | `haθyˈah` | ha[θ] vs ha[s] |
| `𐏋` | xšāyaθiyaʰ | `xšˈayati` | xsaya[t] vs xsaya[θ] |
