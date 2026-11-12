# 004 · The Old English final syllable, and the verbs that keep it

- **Status:** partially accepted (2026-11-08): the final-syllable laws merged;
  `umlaut_ae` withdrawn; `final_ōn_to_ian` demoted to `proposed`
- **Stream:** W3 (sound laws from the literature)
- **Author:** integrator
- **Reviewer:** methods skeptic (independent agent, 2026-11-08)
- **Evidence:** the Old English glossary (6,895 words, 6,309 with an ancestor)

## Claim

The Old English transition was missing the ordinary developments of the final
syllable and of *j*. Twelve rules were tested; ten were kept after review.

## Registered (measured on the full `ang` glossary)

| id | law | example | status |
|---|---|---|---|
| `umlaut_a_nasal` | *a > *e by i-umlaut before a nasal | *manniz > *menniz* | established |
| `final_ą_to_a` | recorded final *-ą > *-a (denasalisation) | *tiną > *tina* | established |
| `final_a_loss` | final *-a is lost | *tina > *tin* | established |
| `final_u_deletion` | final *-u is lost after a heavy syllable | *rūnu > *rūn* | established |
| `final_u_deletion_cluster` | final *-u is lost after a heavy cluster | *handu > *hand* | established |
| `final_ô_to_a` | final *-ô > *-a | *namô > *nama* | established |
| `final_ōn_to_ian` | final *-ōn > *-ian (class-2 weak infinitive) | *manōn > *manian* | **proposed** |
| `j_loss` | *j is lost after a consonant | *biddjan > *biddan* | established |
| `r_epenthesis` | epenthetic *e before final *r after a consonant | *fingr > *finger* | established |
| `r_epenthesis_o` | the same after a rounded vowel + one consonant | *fōdr > *fōdor* | established |
| `r_epenthesis_o_cluster` | the same after a rounded vowel + two consonants | *wuldr > *wuldor* | established |

The breaking repair is in the same file: `breaking_e_lc` now names the
consonants that actually trigger breaking (`l b`, `l t`, …), so a geminate *ll*
does not break (*fell* stays *fell*) and *lp* is excluded (*helpan > helpan*).

## Withdrawn after review

- **`umlaut_ae` (*æ > *e).** The skeptic showed it undoes the rule above it:
  *æ is the regular i-umlaut product of *a, so the rule moved 64 words further
  from their record while gaining 24 (*fastijan > festijan*, *lakkjan >
  lekkan*, *naglijan > neglijan*, *wæj > wej*, *dægiz > degiz*). Its single
  declared exception was not the only one. Removed.
- **`final_ōn_to_ian` as `established`.** It fires on any final *-ōn*, and 14
  recorded weak feminine nouns in *-ōn would be mis-derived (*dōn*, *bōn*,
  *smittōn*, *kippōn*, *tūsōn*, *gailisōn*, *flōisōn*, *hlakarōn*, *ūfōn*,
  *hruzōn*, *tehwōn*). The law is real for class-2 weak verbs but the engine
  cannot see part of speech, so it is registered as `proposed`; 86 of the
  file's exact words rest on it and the report says so.

## Measurement

| configuration | exact | orthographic |
|---|---:|---:|
| HEAD before this change | 277 | 302 |
| all twelve rules (before review) | 606 | 557 |
| after withdrawing `umlaut_ae` | 583 | 561 |

Net after review: **+306 exact, +259 orthographic**. The per-transition
accuracy in `docs/EVALUATION.md` rises from 18.8% to **31.2%** on the recorded
PWGmc→OE pairs. Two words are lost to the final-vowel rules (*stapiz > stæpe*
is a dialect variant; *teuną > teona* is a weak noun whose final *-a* the loss
rule removes).

## Ordering

- `final_ą_to_a` (490) before `final_a_loss` (495).
- `final_a_loss` (495) before `final_ô_to_a` (520); reversing it deletes the
  *-a* that comes from *-ô* and breaks the weak masculines (*namô > *nam*).
- `j_loss` (530) after i-umlaut (409–420), because *j must still be there to
  trigger the umlaut.
- The two final *-u* rules share order 501; both delete, so the tie is harmless.

## Risks and falsifiers

- `final_a_loss` is the same apocope registered in `gem-pro__gmw-pro.yaml`. It
  is restated here because a derivation whose first recorded ancestor is
  Proto-West-Germanic never passes through the earlier stage. The duplicate is
  deliberate and is not a second claim.
- `final_ą_to_a` reads the final ą written in recorded Proto-West-Germanic
  headwords; it is the denasalisation step, not a deletion. The PWGmc target
  itself is *not* scored with this rule (see proposal 001).
- `r_epenthesis` models the vowel as *e* except after rounded vowels; the
  harmonised *-or* class is registered separately. Vowel quality is still a
  simplification.
- If a rule lowers per-transition accuracy or loses more words than it gains
  when switched on alone, it is withdrawn and this file records the number.
