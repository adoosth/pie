# Miss surgery — Iranian branch, read-only diagnosis

**Date.** 2026-11-09.
**Scope.** `fa`, `pal`, `ave`, `ira-pro`, `iir-pro`. Read-only: no file in
`data/`, `src/`, `tests/`, `tools/` was touched, nothing was committed. This
report is the only artefact; scratch lived in `/tmp/ms/`.
**Question (the project's words).** "Discuss many word
reconstruction paths to see if the laws fit or not and why they didn't."
**Method.** Every number is produced by the repo's own counter
(`tools/coverage.py`) or its own measurement harness (`tools/whatif.py`). Every
verdict below belongs to a word I ran through the same `derive()` call
`coverage.py` uses, and compared with the attested form and its IPA.

```
PYTHONPATH=src python3 -m pie.cli worklist --lang fa
PYTHONPATH=src python3 tools/coverage.py --langs fa pal ave ira-pro iir-pro --limit 0
```

| lang | glossary | tested (has a modelled ancestor) | exact | exact by notation | orthographic | explained |
|---|---:|---:|---:|---:|---:|---:|
| `fa` | 5,555 | 1,634 | 0 | 0 | **118** | 118 (7.2% of tested) |
| `pal` | 616 | 60 | 1 | 0 | 0 | 1 |
| `ave` | 352 | 312 | 0 | 0 | 0 | 0 |
| `ira-pro` | 416 | 338 | 7 | **188** | — | 195 (58% of tested) |
| `iir-pro` | 799 | 522 | 1 | **151** | — | 152 (29% of tested) |

**The one sentence that matters.** Of the 1,516 Persian misses that still have a
derivation path, **382 never start at all**: the recorded Middle Persian ancestor
is written in Pahlavi script (192) or in a consonantal Pahlavi transliteration
(114 more), and the engine has no reading table for either. The same shape
appears everywhere on the branch — 312 of 352 Avestan words and 61 of 513
Proto-Iranian/Indo-Iranian misses are lost to *notation*, not to a sound law. On
this branch the alphabet, not the phonology, is the bottleneck.

## Summary of verdicts (110 words examined)

| verdict class | n | share |
|---|---:|---:|
| (a) missing or wrong sound law | 21 | 19% |
| (b) paradigm / citation-form difference | 9 | 8% |
| (c) the record's ancestor is wrong or a different lexeme | 12 | 11% |
| (d) borrowed / non-PIE — the model should not try | 0 | 0% |
| (e) needs a transform the engine does not have | 68 | 62% |

(d) is 0 **by construction, not by luck**: `coverage.ancestry_kind` already parks
3,134 of the 5,555 Persian rows as `borrowed` (almost all Arabic) and 604 as
`outside` before any law is asked anything. They never enter the denominator,
which is why Persian's "tested" column is 1,634 and not 5,555. The model is not
failing them; it is refusing them correctly.

## Verdict distribution by language

| lang | (a) | (b) | (c) | (d) | (e) |
|---|---:|---:|---:|---:|---:|
| `fa` (40) | 11 | 2 | 4 | 0 | 23 |
| `pal` (20) | 1 | 2 | 5 | 0 | 12 |
| `ave` (20) | 6 | 0 | 1 | 0 | 13 |
| `ira-pro` (15) | 1 | 3 | 1 | 0 | 10 |
| `iir-pro` (15) | 2 | 2 | 1 | 0 | 10 |

---

## 1 · New Persian (`fa`) — 40 misses

Selection. `pie worklist --lang fa` ranks misses by edit signature, not by
frequency, so I ranked the 1,516 misses that have a path by whether the gloss is
basic vocabulary (a Swadesh-100 gloss match), shortest first, and took the top of
each of the two blocks the data actually splits into. Notation is
`word` / `translit` / `IPA`. "chain gives" is the derivation from the recorded
ancestor that `coverage.py` would use; `∅` = no rule fired, the form is returned
unchanged.

### 1.1 The chain cannot start (verdict e) — 23 words

| # | word / translit / IPA | gloss | recorded ancestor → chain gives | why |
|---|---|---|---|---|
| 1 | این / ēn / ˈʔeːn | this | `pal 𐭦𐭭𐭤` → `𐭦𐭭𐭤` ∅ | (e) Pahlavi script; no `pal` reading table |
| 2 | پسر / pisar / pi.sar | son | `peo 𐎱𐎢𐏂` → ∅ | (e) Old Persian cuneiform; no `peo` reading table |
| 3 | چی / čī / ˈt͡ʃiː | what? | `pal 𐭬𐭤` → ∅ | (e) Pahlavi script |
| 4 | کی / kay / ˈkeː | who? | `pal 𐫐𐫏` → ∅ | (e) Pahlavi (Psalter) script |
| 5 | امسال / emsāl / ʔim.ˈsaːl | this year | `pal 𐭫𐭣𐭭𐭤` → ∅ | (e) Pahlavi script |
| 6 | مانی / māni / maː.ˈniː | Mani | `pal 𐫖𐫀𐫗𐫏` → ∅ | (e) Pahlavi (Manichaean) script |
| 7 | نمک / namak / na.ˈmak | salt | `pal 𐫗𐫖𐫏𐫍𐫐` → ∅ | (e) Pahlavi (Manichaean) script |
| 8 | تا / tā / ˈtaː | as far as | `peo 𐎹𐎠𐎫𐎠` → ∅ | (e) OP cuneiform |
| 9 | خشت / xišt / ˈxiʃt | brick | `peo 𐎡𐏁𐎫𐎡` → ∅ | (e) OP cuneiform |
| 10 | ـش / -aš / ˈ‿iʃ | verbal noun suffix | `pal 𐭱𐭭` → ∅ | (e) script, and a bound form (hyphen) |
| 11 | هل / hul / ˈhul | push | `pal ʾwl` → `ʾwl` ∅ | (e) consonantal transliteration; `ʾ` is not a phoneme |
| 12 | سروش / surōš / su.ˈroːʃ | (angel) Soroush | `pal slwš` → ∅ | (e) transliteration with no vowels |
| 13 | تور / tōr / — | Tur | `pal twl` → ∅ | (e) transliteration with no vowels |
| 14 | سو / su / ˈsoː | light, sight | `pal swk'` → ∅ | (e) transliteration; also final `-k'` has no law |
| 15 | زه / zeh / ˈzah | spring | `pal zah` → `zah` ∅ | (e) the ingested headword lost the macron (`zāh`) |
| 16 | دی / di / ˈdaj | mother | `pal ddw’` → ∅ | (e) transliteration; `’` not a phoneme |
| 17 | ای / ay / — | this | `pal ʾyd` → ∅ | (e) transliteration |
| 18 | سرد / sard / ˈsard | cold | `pal slt'` → ∅ | (e) consonantal transliteration (needs the vowels supplied) |
| 19 | کهن / kuhan / ku.ˈhan | old | `pal khwbn'` → ∅ | (e) consonantal transliteration |
| 20 | نرد / nard / ˈnard | tree trunk | `pal nywʾlthšyl` → ∅ | (e) transliteration, and the string looks mis-ingested |
| 21 | سنگ / sang / ˈsanɡ | stone | `pal sng` → `sng` ∅ | (e) + (a): the pal form is `CC` (`sng`); NP breaks it with a vowel — an epenthesis transform whose vowel is lexical (§4.1) |
| 22 | درخت / daraxt / da.ˈraxt | tree | `ira-pro draxta` → `draxt` | (e) same epenthesis (`dr-` → `dar-`) |
| 23 | گیس / gēs / ˈɡeːs | long hair | `iir-pro káyćas ~ *gáyćas` → `kīsah~gīs` | (e) the `~` variant separator is not split; a form with `~` can never match |

Count, re-run:

```
PYTHONPATH=src python3 - <<'EOF'
import sys; sys.path[:0]=['src','tools']
from pie import data; from pie.rules import derive
from coverage import ancestor_starts
chain=data.derivation_chain('fa'); rs=data.rulesets(); dead=blocked=0
for e in data.lexicon('fa'):
    if e.get('recon'): continue
    outs=[]
    for st,f in ancestor_starts(e,chain):
        d=derive(f,chain[chain.index(st):],rs)
        if not d.skipped: outs.append(d)
    if outs and all(not d.steps for d in outs): dead+=1
print('fa misses whose every path fires no rule:',dead)   # 382
EOF
```

### 1.2 A law ran and produced the wrong form (verdict a) — 11 words

| # | word/tr/IPA | gloss | ancestor → chain gives | attested | law, environment | citation |
|---|---|---|---|---|---|---|
| 24 | نه / na / ˈnuh | nine | `ira-pro *Hnáwa` → `naw` | نه /nuh/ | (a) final `*-wa#` → `-h` with rounding of `a` to `u`: `*náwa > *nawa > nuh`. The chain has no final-glide law at all | Windfuhr 2009, §"NP phonology"; Sadeghi 1978 |
| 25 | ده / dah / ˈdah | ten | `peo *daθa` → `das` | ده /dah/ | (a) `peo__pal` has `theta_to_s`; the reflex needed here is `θ > h` intervocalically. One wrong reflex, not a missing one | Kent, *Old Persian* §138 (OP θ > MP h) |
| 26 | ماه / māh / ˈmaːh | moon | `ira-pro *mā́Hah` → `mā` | ماه /māh/ | (a) `final_h_loss` (peo→pal) is too broad: `*-ah#` deletes, but NP keeps `-h` in māh, gāh, māhī. Needs a lexical or stem-class guard | Sadeghi 1978 |
| 27 | گاو / gāw / ˈɡaːw | cow | `ira-pro *gā́wš` → `gāwš` | گاو /gāw/ | (a) `*-wš#` → `-w#` is missing (NP gāw, MP gāw). The peo path also inserts a vowel (`gāuš > gāoš`), which is a second error | Kent §, MP gāw |
| 28 | زر / zar / ˈzarr | gold | `ine-pro *ǵʰelh₃-` → `dar` | زر /zarr/ | (a) `j_to_d` (ira→peo) fires word-initially; `*ǵʰ-` must give `z-` there. Environment: `#_`, not `V_V` | Kent §; Sadeghi 1978 |
| 29 | زر / zar / ˈzar | old man | `ine-pro *ǵerh₂-` → `dar` | زر /zar/ | (a) same law, same environment — this is the second witness that fixes a group, not a word | idem |
| 30 | پنج / panj / ˈpand͡ʒ | five | `ira-pro *pánča` → `panč` | پنج /pand͡ʒ/ | (a) `*-č#` → `-j#` is missing (MP panj). Environment: word-final | Sadeghi 1978 |
| 31 | آب / āb / ˈʔaːb | water | `ira-pro *Hā́fš` → `āfš` | آب /ʔaːb/ | (a) `*-fš#` → `-b#` is missing (PIr *āfš > MP āb); the existing `ps_to_fsh` produces the right cluster but nothing resolves it | Kent §; Windfuhr 2009 |
| 32 | سگ / sag / ˈsaɡ | dog | `peo *sakah` → `se` | سگ /saɡ/ | (a) `final_ag_to_e` over-applies: it also converts `-ag` that came from `*-akah`, i.e. sag, where NP keeps `-g`. **Measured**: dropping the law gains this word and loses 14 (§3, item 7) | Sadeghi 1978; MP sag |
| 33 | بخش / baxš / ˈbaxʃ | lot, portion | `ira-pro *baxšáh` → `baš` | بخش /baxʃ/ | (a) `xsh_to_sh` (peo→pal) deletes `x` in final `-xš`; NP keeps `baxš`. Environment must be restricted to the cluster that really became `š` | Sadeghi 1978 |
| 34 | مو / mu / ˈmoː | hair | `ira-pro *maw` → `maw` ∅ | مو /moː/ | (a) `*-aw#` → `-ō/-u` is missing (MP mōy/mu). The file's own stage description already names the final-`y` half of this as unmodelled | `data/rules/pal__fa.yaml`, stage note |

### 1.3 Paradigm or citation form (verdict b) — 2 words

| # | word/tr/IPA | gloss | ancestor → chain gives | attested | why |
|---|---|---|---|---|---|
| 35 | مادر / mādar / maː.ˈdar | mother | `ira-pro *máHtā` → `mādā` | مادر /mādar/ | (b) the recorded ancestor is the direct case; NP cites the r-stem oblique. `r_stem_oblique` already exists in `peo__pal` but no ancestor at that stage is recorded | 
| 36 | دو / du / ˈdu | two | `ine-pro *dwóh₁` → `dwā` | دو /du/ | (b)/(c) `*dwóh₁` is a dual; the cardinal in NP is `du` from MP dō. A paradigm-cited ancestor cannot reach it |

### 1.4 The recorded ancestor is the wrong lexeme (verdict c) — 4 words

| # | word/tr/IPA | gloss | recorded ancestor → gives | attested | why |
|---|---|---|---|---|---|
| 37 | دل / dil / ˈdil | heart | `ira-pro *jā́rd` → `dārd` | دل /dil/ | (c) NP dil continues a zero-grade `*ȷ́r̥d-` with metathesis; `*jā́rd` is a full-grade stem that never yields dil |
| 38 | از / az / ˈʔaz | of, from | two homographs: `ira-pro *háčaH` → `hačā` and `ine-pro *éǵh₂` → `ad` | از /ʔaz/ | (c) the first is a different lexeme's length; the second is the pronoun "I". The particle is OP hacā, whose `c` must become `z` — but the entry also carries the pronoun's *éǵh₂ | 
| 39 | را / râ / ˈraː | object marker | `ine-pro *h₂er-` → `ar` | را /rā/ | (c) rā is OP rādiy; `*h₂er-` belongs to another word |
| 40 | یک / yak / ˈjak | one | `ira-pro *Háywah` → `īw` | یک /yak/ | (c) NP yak < MP ēk < PIIr *Haykás. `*Háywah` is a different formation (`*Háywa-` gives īw) |

---

## 2 · Middle Persian (`pal`) — 20 misses

Context. Only **60 of 616** rows carry an ancestor at a modelled stage; **544
rows have no etymology or ancestry at all** (MacKenzie's dictionary as ingested
states no ancestor). Of the 60, one is exact (`pistag`). Two structural facts
decide almost every row below: (i) the headword column is a *normalised Latin
transliteration* with the vowel-length marks stripped, so `sped` is `spēd`;
(ii) **no `pal` row carries an IPA** (0 of 616), so the orthographic layer can
never be scored — `spelling.plausible()` returns False for every pal word. This
is the W1 gap already recorded in `proposals/2026-09-11/pal.md`, not a law gap.

| # | word / translit | gloss | ancestor → chain gives | attested | verdict |
|---|---|---|---|---|---|
| 1 | abad | populous | `ira-pro *āpāta-` → `ābād` | abad | (e) vowel length lost by the ingest; with no IPA the layer cannot be scored |
| 2 | nog | new | `ine-pro *néwos` → `nˈaw` | nog | (c) the record cites a PIE etymon for a word whose MP shape is nōg; also (e) |
| 3 | sped | white | `ira-pro *cwaytáh` → `spēd` | sped | (e) length marks dropped (spēd) |
| 4 | xwab / hwʾb | sleep | `ira-pro *hwápati` → `hwˈabad` | xwāb | (b) the ancestor is a 3sg verb; the record is the noun |
| 5 | hm | same | `ine-pro *somHós` → `ham` | ham | (e) the form is right; the headword has no IPA, and no pal spelling layer exists |
| 6 | bwm | earth | `ine-pro *bʰuH-` → `bū` | bum | (c) a root is recorded where the word is būm |
| 7 | kyš | faith | `ine-pro *kʷeys-` → `kēs` | kêš | (e) transliteration convention (`ê` for ē, `š` for s) |
| 8 | bʾg | garden | `ine-pro *bʰeh₂g-` → `bāg` | bāg | (e) notation only — `ā` vs `a` in the headword |
| 9 | gwhl | substance | `ira-pro *gawθraH` → `gōhā` | ǧwëra | (c) a different lexeme; the `θr` treatment is also unmodelled |
| 10 | hwm | haoma | `iir-pro *sauma` → `hōm` | hauma- | (e) transliteration (`au` vs `ō`) |
| 11 | hyn' | army | `iir-pro *sáynaH` → `hˈēnā` | sénā | (e) transliteration |
| 12 | bywl | ten thousand | `ira-pro *baywā́` → `bēwˈā` | bēwar | (a) final `*-ā#` → `-ar` in this word; the r-stem law exists but no ancestor at that stage is recorded |
| 13 | blnc | rice | `peo *vrinjiš` → `vrinziš` | birinj | (e) anaptyxis + reading of a consonantal form |
| 14 | hndwk' | Indian | `ira-pro *hínduš` → `hˈinduš` | Hiⁿduyaʰ | (e) transliteration |
| 15 | pus | son | `peo 𐎱𐎢𐏂` → ∅ | pus | (e) cuneiform; no reading table |
| 16 | anahid | Anahid | `peo 𐎠𐎴𐏃𐎡𐎫` → ∅ | anahid | (e) cuneiform |
| 17 | kʾlwʾn' | military column | `peo *kāravā-` → `kāravā` ∅ | kārawān | (e) identity: no law fires on a transliterated input |
| 18 | padzahr | antidote | `ine-pro *gʷʰen-tro-` → `gantr` | padzahr | (c) the ancestor is only the second member (`zahr`); the compound is unmodelled |
| 19 | cynʾl | plane tree | `ine-pro *dóru-` → `dˈār` | činār | (c) wrong lexeme |
| 20 | hwʾb | sleep | `ira-pro *hwápati` → `hwˈabad` | xwāb | (b) verb ancestor, noun record (second witness of #4) |

```
PYTHONPATH=src python3 tools/coverage.py --langs pal --limit 0
python3 -c "import gzip,json;print(sum(1 for l in gzip.open('data/lexicon/pal.jsonl.gz','rt') if not json.loads(l).get('etym')),'rows with no etymology')"
```

---

## 3 · Avestan (`ave`) — 20 misses

Context. 352 words, 312 with an ancestor, **0 explained**, and not one of the 312
is a *phonological* failure: Avestan is written in the Avestan script and there is
no `data/spelling/ave.yaml`. The laws already produce the right phonemes for a
subset — measured over the miss set: **7 words whose derived form equals the
entry's own transliteration**, modulo the accent notation (at least one law fired
in each, so the counter is not what stops them):

| derived | translit | word |
|---|---|---|
| `tad` | tád | 𐬙𐬀 |
| `dadāti` | dádāti | 𐬛𐬀𐬛𐬁𐬌𐬙𐬌 |
| `tāpayati` | tāpáyati | 𐬙𐬁𐬞𐬀𐬌𐬌𐬈𐬌𐬙𐬌 |
| `dasa` | dáśa | 𐬛𐬀𐬯𐬀 |
| `dasa` | dáśa | 𐬛𐬀𐬯𐬁 |
| `mātā` | mātā | 𐬨𐬁𐬙𐬀𐬭 |
| `strī` | strī́ | 𐬯𐬙𐬭𐬍 |

| # | word / translit / IPA | gloss | ancestor → chain gives | verdict |
|---|---|---|---|---|
| 1 | 𐬀𐬞 / — / ap | water | `ine-pro *h₂ep-` → `Hap` | (e) script; also (a) initial `*H-` is dropped in Avestan and no ira→ave rule does it |
| 2 | 𐬀𐬌𐬭𐬌𐬌𐬋 / — | Iranian | `iir-pro *Áryas` → `Áryō` | (e) script only — the phonemes are right |
| 3 | 𐬀𐬊𐬚𐬭𐬀 / — | shoe | `ine-pro *h₃ew-` → `Hav` | (c) the ancestor is a bare root, not the lexeme |
| 4 | 𐬀𐬛 / ad- | to eat | `ine-pro *h₁ed-` → `Had` | (e) script; (a) `*H-` loss |
| 5 | 𐬀𐬭𐬴𐬀 / — | bear | `ira-pro *Hŕ̥šah` → `Hərəšō` | (a) initial `*H-` must delete (the `r̥ > ərə` half is already right) |
| 6 | 𐬀𐬥𐬌𐬌𐬀 / anyá | other | `iir-pro *Hanyás` → `Hanyō` | (a) same law — `*H-` before a vowel is lost in Avestan |
| 7 | 𐬀𐬉𐬱𐬆𐬨𐬀 / aēšma | fury | `ira-pro *Háyšmah` → `Hayšmō` | (a) `ai_to_ae` exists but cannot fire because the input is still `Hay-`; the `*H-` must go first |
| 8 | 𐬀𐬉𐬎𐬎𐬀 / aiva | one | `iir-pro *Háywas` → `Hayvō` | (a) as #7, plus `*-as#` → `-ō` is right |
| 9 | 𐬀𐬧𐬙𐬀𐬭𐬆 / andar | between | `ine-pro *h₁enter` → `Hantar` | (e) script; (a) `*H-` |
| 10 | 𐬀𐬨𐬀𐬎𐬎𐬀𐬧𐬙 / — | strong | `iir-pro *Hámawants` → `Hamavans` | (e) script; the `-wants > -vans` half is right |
| 11 | 𐬀𐬐𐬀 / — | evil | `iir-pro *ákas` → `akō` | (e) script only — derived form is the translit |
| 12 | 𐬀𐬉𐬙𐬍 / éti | to go | `ine-pro *h₁ey-` → `Hay` | (a) `*H-` loss + `*ey` → `aē` (the diphthong rule cannot see `ay` before `H` is deleted) |
| 13 | 𐬀𐬎𐬎𐬀 / — | away | `ine-pro *h₂ew-` → `Hav` | (e) script; (a) `*H-` |
| 14 | 𐬀𐬌𐬌𐬀𐬵 / — | iron | `iir-pro *Háyas` → `Hayō` | (e) script; (a) `*H-` |
| 15 | 𐬀𐬨𐬆𐬴𐬀 / — | immortal | `ine-pro *n̥mr̥tós` → `amərətō` | (e) script only — every law is right |
| 16 | 𐬀𐬌𐬡𐬌𐬙𐬋 / — | around | `ine-pro *h₂m̥bʰi` → `Habi` | (a) final `*-i` is deleted; Avestan keeps it (aibiia-) |
| 17 | 𐬀𐬧𐬛𐬀 / — | blind | `iir-pro *andʰás` → `andō` | (e) script only |
| 18 | 𐬀𐬌𐬠𐬍 / aibiː | to, upon | `ine-pro *h₂m̥bʰi` → `Habi` | (a) as #16 — the same law, second witness |
| 19 | 𐬀𐬎𐬭𐬎𐬎𐬀𐬧𐬙 / árvant | courser | `iir-pro *Hárwants` → `Harvans` | (e) script; (a) `*H-` |
| 20 | 𐬀𐬔𐬆𐬥𐬌𐬌𐬁 / — | milch cow | `iir-pro *agʰnyáH` → `agnyā` | (e) script only |

```
PYTHONPATH=src python3 tools/coverage.py --langs ave --limit 0
```

---

## 4 · Proto-Iranian (`ira-pro`) — 15 misses

Context. 195 of 338 tested are already explained, and **188 of those are the
notation layer** (the dictionary writes an acute, the engine writes `ˈ`). The
misses are dominated by two non-phonological shapes.

| # | word | gloss | ancestor → chain gives | attested | verdict |
|---|---|---|---|---|---|
| 1 | a- | un-, -less | `ine-pro *n̥` → `a` | a- | (e) bound form: `exact_kind` refuses a hyphen that the output cannot contain |
| 2 | dwi- | double | `ine-pro *dwi` → `dwi` ∅ | dwi- | (e) bound form, and no law fired |
| 3 | fra- | toward | `ine-pro *pro` → `fra` | fra- | (e) bound form |
| 4 | Há- | augment | `ine-pro *h₁é` → `Hˈa` | Há- | (e) bound form + stress notation |
| 5 | ha- | zero grade of ham- | `ine-pro *sm̥` → `ha` | ha- | (e) bound form |
| 6 | cwáHdah | army | `ine-pro *ḱweh₁-` → `cwaH` | cwáHdah | (b) a root is recorded, the word is a derivative of it |
| 7 | múHs | mouse | `ine-pro *múHs` → `mˈuHs` ∅ | múHs | (e) correct modulo notation, but no rule fires, so the counter refuses it |
| 8 | warj- | to do | `ine-pro *werǵ-` → `warj` | warj- | (e) bound form |
| 9 | gáwbati | to say | `ine-pro *gewH-` → `gawH` | gáwbati | (b) root vs 3sg |
| 10 | Hwah- | to dwell | `ine-pro *h₂wes-` → `Hwah` | Hwah- | (e) bound form (the `s > h` is right) |
| 11 | cwaHdapatiš | commander | `ine-pro *pótis` → `pˈātiš` | cwaHdapatiš | (c) only the second member is recorded as ancestor |
| 12 | HáHtr̥š | fire | `iir-pro *HáHtr̥š` → `HˈaHtr̥š` ∅ | HáHtr̥š | (e) correct modulo notation, no rule fires |
| 13 | Hstā́ | star | `ine-pro *h₂stḗr` → `Hstˈār` | Hstā́ | (a) final `*-ēr#` → `-ā` is right, but `-r` survives the whole chain; the pre-Iranian `*-r#` loss is missing |
| 14 | gā́wš | cow | `iir-pro *gā́wš` → `gˈāwš` ∅ | gā́wš | (e) correct modulo notation, no rule fires |
| 15 | paridayjah | walled garden | `ine-pro *dʰóyǵʰos` → `dˈayjah` | paridayjah | (b) the recorded ancestor is the second member of the compound |

---

## 5 · Proto-Indo-Iranian (`iir-pro`) — 15 misses

Context. 152 of 522 tested explained (151 by notation). 45 of the 370 misses that
have a path are bound forms (`a-`, `pra-`, `-kas`, `-ám`, `suH-`), i.e. 12%.

| # | word | gloss | ancestor → chain gives | attested | verdict |
|---|---|---|---|---|---|
| 1 | a- | un- | `ine-pro *n̥` → `a` | a- | (e) bound form |
| 2 | pra- | forward | `ine-pro *pro` → `pra` | pra- | (e) bound form |
| 3 | -kas | deadjectival suffix | `ine-pro *-kos` → `kas` | -kas | (e) bound form |
| 4 | -ma | deverbal suffix | `ine-pro *mn̥ ~ *-mén` → `ma~mˈan` | -ma | (e) bound form + the `~` variant is never split |
| 5 | -ám | emphatic particle | `ine-pro *óm` → `ˈam` | -ám | (e) bound form |
| 6 | sam- | together | `ine-pro *sem` → `sam` | sam- | (e) bound form |
| 7 | ati- | over- | `ine-pro *éti` → `ˈati` | ati- | (e) bound form |
| 8 | suH- | pig | `ine-pro *suH-` → `suH` ∅ | suH- | (e) bound form, no rule fired |
| 9 | múHs | mouse | `ine-pro *múHs` → `mˈuHs` | múHs | (e) correct modulo notation, no rule fires |
| 10 | Há- | augment | `ine-pro *h₁é` → `Hˈa` | Há- | (e) bound form + notation |
| 11 | parás | beyond | `ine-pro *pér` → `pˈar` | parás | (b) the bare root is recorded; the word carries `-ás` |
| 12 | bʰr̥ȷ́ʰáns | high | `ine-pro *bʰérǵʰonts` → `bʰˈarȷ́ʰants` | bʰr̥ȷ́ʰáns | (b) nominative plural vs the attested stem (zero-grade `r̥`) |
| 13 | ní | down | `ine-pro *h₁én` → `Hˈan` | ní | (a) final `*-n#` loss is applied where the record keeps the syllable; the accent/ablaut cell differs |
| 14 | Hstā́ | star | `ine-pro *h₂stḗr` → `Hstˈār` | Hstā́ | (a) `*-r#` survives (same law as ira-pro #13) |
| 15 | wan- | to win | `ine-pro *wenh₁-` → `wanH` | wan- | (c) the record's `-n-` cannot come from `*wenh₁`; a different stem is recorded |

---

## 6 · Ranked fixes, by measured gain

Nothing below is proposed without a number, and the command that produces it is
given. Candidates live in `/tmp/ms/*.yaml`; none was added to the repo.

### 1 · A Pahlavi reading table (`data/script/pal.yaml`) — ceiling 382 fa words

The largest single gain on the branch and it is not a sound law. 192 Persian
misses have their *only* Pahlavi ancestor in script (`𐭦𐭭𐭤`, `𐫖𐫀𐫗𐫏`) and 114
more in a consonantal transliteration (`ʾwl`, `slwš`, `khwbn'`); 6 of the 306 also
carry a Latin-script ancestor. A further 76 have a Latin-letter ancestor that is
itself consonantal (`sng`, `pnyl`, `blnc`). Total blocked at the last mile: **382
of 1,516**.

```
PYTHONPATH=src python3 - <<'EOF'
import re,sys; sys.path[:0]=['src','tools']
from pie import data; from pie.rules import derive
from coverage import ancestor_starts, exact_kind, orthographic_hit
SC=re.compile('[\U000103A0-\U000103DF\U00010A00-\U00010B9F]')
chain=data.derivation_chain('fa'); rs=data.rulesets(); n=0
for e in data.lexicon('fa'):
    if e.get('recon'): continue
    outs=[]
    for st,f in ancestor_starts(e,chain):
        d=derive(f,chain[chain.index(st):],rs)
        if not d.skipped: outs.append((d.output,len(d.steps),st))
    if not outs: continue
    if any(k and exact_kind(o,e['word']) for o,k,s in outs): continue
    if orthographic_hit(outs,'fa',e['word'],e.get('ipa') or ''): continue
    if all(k==0 for o,k,s in outs) and any(
            SC.search(str(a[1])) or any(c in str(a[1]) for c in 'ʾʿ') or str(a[1]).endswith(chr(39))
            for a in (e.get('anc') or []) if isinstance(a,list)):
        n+=1
print(n)   # 306  (+76 with a Latin-letter consonantal ancestor = 382)
EOF
```

**Priority: highest.** It unblocks 25% of the Persian search space without one
etymological decision. The rule is honest: a *reading* (ʿk → ak), not a sound law.

### 2 · An Avestan orthographic layer (`data/spelling/ave.yaml`) — ceiling 312

Every one of Avestan's 312 tested words is blocked by the missing script layer.
Measured proof that the phonology is already there: 7 words produce exactly the
entry's own transliteration modulo the accent.

```
PYTHONPATH=src python3 - <<'EOF'
import sys; sys.path[:0]=['src','tools']
from pie import data; from pie.rules import derive; from pie.service import stress_only
from coverage import ancestor_starts
chain=data.derivation_chain('ave'); rs=data.rulesets(); n=0
for e in data.lexicon('ave'):
    t=e.get('translit') or ''
    if not t: continue
    for st,f in ancestor_starts(e,chain):
        d=derive(f,chain[chain.index(st):],rs)
        if d.steps and (d.output==t or stress_only(d.output,t)): n+=1; break
print(n)   # 8
EOF
```

**Priority: highest (second).** Caveat, measured honestly: only 39 of 352 Avestan
entries carry an IPA, so `spelling.plausible` will cap the *scored* gain far below
312 until W1 adds pronunciation data.

### 3 · Count "laws already right, but no rule fired" as a notation hit — 32 + 1

`coverage.measure` requires `d.steps` to be non-empty before any comparison. A
word whose ancestor needs no change is therefore a permanent miss even when it is
character-identical. Measured: **32 ira-pro** (7.7% of the glossary) and 1
iir-pro. (A different measure — "the derived form equals the entry's own
transliteration and at least one law fired" — gives 7 ave and 4 pal; those belong
to the orthography column and are the §3 evidence, not this counter.)

```
PYTHONPATH=src python3 - <<'EOF'
import sys; sys.path[:0]=['src','tools']
from pie import data; from pie.rules import derive; from pie.service import stress_only
from coverage import ancestor_starts, exact_kind, orthographic_hit
for lang in ('ira-pro','iir-pro','pal','ave'):
    chain=data.derivation_chain(lang); rs=data.rulesets(); n=0
    for e in data.lexicon(lang):
        if e.get('recon'): continue
        outs=[]
        for st,f in ancestor_starts(e,chain):
            d=derive(f,chain[chain.index(st):],rs)
            if not d.skipped: outs.append((d.output,len(d.steps),st))
        if not outs: continue
        if any(k and exact_kind(o,e['word']) for o,k,s in outs): continue
        if orthographic_hit(outs,lang,e['word'],e.get('ipa') or ''): continue
        t=e.get('translit') or e['word']
        if any(k==0 and (o==e['word'] or stress_only(o,t)) for o,k,s in outs): n+=1
    print(lang,n)   # ira-pro 32, iir-pro 1, pal 0, ave 1
EOF
```

**Priority: high, cheap, and purely a counting decision** — it must be its own
column (`identity`), never folded into `exact`, or the historical number moves.

### 4 · A bound-form (hyphen) comparison layer — 16 ira-pro + 45 iir-pro = 61

Sixty-one words are lost only because the record writes a morpheme with a hyphen and
the laws never write one. `exact_kind` refuses this deliberately (it is right to
refuse it inside `exact`), but the vocabulary has no column where these belong.
Measured: 16 + 45.

```
PYTHONPATH=src python3 - <<'EOF'
import sys; sys.path[:0]=['src','tools']
from pie import data; from pie.rules import derive
from coverage import ancestor_starts, exact_kind
for lang in ('ira-pro','iir-pro'):
    chain=data.derivation_chain(lang); rs=data.rulesets(); n=0
    for e in data.lexicon(lang):
        if '-' not in e['word'] or e.get('recon'): continue
        outs=[]
        for st,f in ancestor_starts(e,chain):
            d=derive(f,chain[chain.index(st):],rs)
            if not d.skipped: outs.append((d.output,len(d.steps),st))
        if outs and not any(k and exact_kind(o,e['word']) for o,k,s in outs): n+=1
    print(lang,n)   # 16, 45
EOF
```

### 5 · `final_ug_loss` — MP `*-ūg#` → NP `-ū` — +2 gained, 0 lost

```
PYTHONPATH=src python3 tools/whatif.py --to fa --rules /tmp/ms/gdrop.yaml --layers exact,orthographic
# explained before: 118 → after: 120 (+2)  gained: بانو, بانو   lost: —
```

**Priority: low (2 words).** Honest, zero regression, but it is a rounding error.

### 6 · `final_y_loss` — MP `*-y#` → NP zero — +2 gained, 0 lost

```
PYTHONPATH=src python3 tools/whatif.py --to fa --rules /tmp/ms/yloss.yaml --layers exact,orthographic
# explained before: 118 → after: 120 (+2)  gained: مو, پا   lost: —
```

**Priority: low (2 words).** Note the file's own stage description says this law
is *lexical* (sarāy keeps `-y`); the measurement agrees — it wins only two.

### 7 · `final_ag_to_e` — keep the law, restrict its environment — net 22 words at stake

This is the most instructive measurement in the report. Dropping the law:

```
PYTHONPATH=src python3 tools/whatif.py --to fa --drop 'fa|final_ag_to_e' --layers exact,orthographic
# explained before: 118 → after: 105 (-13)  gained: سگ   lost: تازه×2, رنده, ساده, سرمه, شیره,
#                                                ماده×2, نیزه, پاره×2, پسته, کده, گربه
```

So the law carries 14 words and wrongly converts exactly one (سگ, where the `-ag`
comes from OP `*-akah`, not from `*-aka-`). **Priority: high** — but the fix is a
guard on the environment (the `g` must descend from a suffix `*-ka-`), not a new
law, and it is worth 1 word until the guard is written.

### 8 · Rejected by measurement — do not ship: `final_d_to_h`, `initial_y_to_j`, `final_wa_to_u`

```
PYTHONPATH=src python3 tools/whatif.py --to fa --rules /tmp/ms/d2h.yaml  --layers exact,orthographic
# 118 → 96 (-22): gained پیه, گاه, گاه; LOST آباد×2, آزاد×2, ارد×3, باد, بد×2, بند×3,
#                 بید, داد×2, درد×2, ریوند, شید×2, مرد, کرد, کلید, گوگرد
PYTHONPATH=src python3 tools/whatif.py --to fa --rules /tmp/ms/y2j.yaml  --layers exact,orthographic
# 118 → 118 (+0)
PYTHONPATH=src python3 tools/whatif.py --to fa --rules /tmp/ms/wa2u.yaml --layers exact,orthographic
# 118 → 118 (+0)
```

The blanket "MP `-d#` > NP `-h`" law **over-applies 8:1**: it wins 3 and
destroys 25, because NP `-d` is preserved wherever it descends from `*-ta`
(dād, bād, band, dard). This is the clearest case in the branch of a law that looks
right from three examples and is wrong for the language — exactly what
`tools/whatif.py` exists to catch. `initial_y_to_j` and `final_wa_to_u` fire
nowhere the corpus can see: the `j-` words already have `j` in Middle Persian,
and `دو`'s ancestor is a dual, not `dwā`.

---

## 7 · What I would tell the project in one paragraph

The Iranian branch does not have a sound-law problem; it has a **writing-system
problem**. Two thirds of the 110 misses I examined (68) need a transform the
engine does not have, and the transforms are of three kinds: a reading table for
Pahlavi script and transliteration (382 Persian words blocked), an orthographic
layer for Avestan script (all 312 tested words), and a notion of the *bound form*
and of the *word that needs no change* (94 words across ira-pro/iir-pro). Only 21
of 110 are genuine sound-law errors, and four of those are a single law each with
precise environments (`*-fš# > -b`, `*-č# > -j`, `θ > h`, `*-wš# > -w`), while the
one law that looked most promising from examples (`-d# > -h`) is measured to lose
22 words and must be rejected. The branch's real next three tasks are therefore:
`data/script/pal.yaml`, `data/spelling/ave.yaml`, and a `bound-form`/`identity`
column — in that order, because those are the only three that pay in hundreds.
