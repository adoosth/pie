# Review protocol

Every change to `data/` passes through a reviewer who did not write it. The
reviewer's job is not to be agreeable; it is to make the claim falsifiable.

`docs/PROGRAMME.md` says *what* is reviewed. This file says *how*, and what
"no" looks like.

## The five questions

A review answers these in order. A "no" on 1–3 stops the merge; a "no" on 4–5
is recorded and fixed in a follow-up.

1. **Is the claim stated?** Can it be written in one sentence without the rule
   id? ("PIE *p becomes PGmc *f word-initially and after a consonant except
   after *s.") If the sentence needs the word "sometimes", the environment is
   not described yet.
2. **Is the evidence independent?** At least three examples, from different
   etyma, and at least one that the rule must *not* touch. An example list
   that consists of the word the rule was written for is not evidence.
3. **Does the rule over-apply?** Re-derive the examples by hand from the
   trace. Then run the transition's evaluation and the corpus; a rule that
   raises the count while lowering per-transition accuracy is a red flag, not
   a win.
4. **Is the tier honest?** Cited and uncontroversial → `established`. A real
   hypothesis → `proposed`, and named as such. This repo's own reasoning →
   `custom`. A writing convention → `orthographic`, in a spelling file, never
   in a sound-law file.
5. **Is the artefact shaped right?** One coherent change, its examples, its
   sources key, its prose, and the regenerated reports. No unrelated edits.

## Specific checks

**Sound laws.** The `env` must be expressed in segments, not in whole words.
A rule may not match on a form's length ("only forms under six segments") and
call that conditioning. The `order` must be justified by the derivation it
needs: colouring before deletion, Grimm before Verner, and so on — if the order
matters, say why in `notes`.

**Orthographic rules.** They may state a convention ("/æ/ is written a") but not
a lookup ("this word is spelled this way"). The test is: would the rule apply to
a word that does not exist yet? If not, it is a lookup and belongs in a
dictionary, not a rule file. Every example gives the full phonemic input and the
written output, because a spelling rule is normally one step of a convention and
a single-step example would be unreadable.

**Lexicon supplements.** Each entry names its source; nothing overwrites
kaikki; the ingest tool is committed with the data it produced. A lexicon change
that lowers `identified` is a regression unless the drop is explained.

**Pathways.** One lexeme has one etymology pathway (PROGRAMME.md, "One pathway
per lexeme"). Ask, for every derivation that is about to be published:

- *Does a known pathway already explain this word?* If the word's ancestry is
  recorded and reproduces its form, a second route to the same word is not an
  alternative — it is a competitor that must be rejected, with the reason.
- *Is a homograph being confused with a homonym?* Same spelling, same sound,
  different meaning means different words and different pathways; the same word
  with two proposed ancestors means one of them is wrong. Check `variants` on the
  word page: more than one lexeme entry for a spelling may not be silently
  merged.
- *Which candidate has the better sense?* Where two paths both fit the form, the
  one whose meaning development is ordinary in that branch wins. A path chosen
  only because it is phonologically convenient, against a known competitor with
  a closer meaning, is rejected even if it raises the exact count.
- *Does the rule make the model claim less?* If a new law exists only to give a
  word a second, nicer etymology, the honest output is "unexplained", not the new
  law.

**Backlog.** A word whose recorded ancestry fails these pathway checks is
parked, not repaired. `python3 tools/backlog.py --list` reads the file,
`--write` regenerates `data/review_backlog.yaml` and the human page
`docs/REVIEW_BACKLOG.md`, and `--check` fails when the stored file disagrees
with a fresh pass over the corpus. The four kinds are defined in
`pie.dubious`; a parked word is not counted as explained, and its ancestry is
not used as evidence, until a reviewer opens the cited source and the entry
changes in `data/`.

**Numbers.** A diff of `docs/COVERAGE.md` must be explained in the commit
message: which count moved, which language, and why. A number that moved without
a rule change means the data pipeline changed — say so.

**Proposals.** A rejected proposal stays in `proposals/` with the reason. "Not
now" is a valid rejection; "because it would lower the number" is not.

## Adversarial critique, in practice

The skeptic writes their review as an argument, not a checklist. Useful forms:

- *Show me a word this rule must not touch, and its trace.*
- *What is the smallest environment that still explains your examples?*
- *Which of these examples would also be explained by a rule you already have?*
- *If this rule is wrong, which published number will be inflated, and by how
  much?*
- *Where does the citation actually say this? Give the section, not the author.*

Two linguists who disagree produce a `docs/DECISIONS.md` entry with both
positions and the deciding rule (see PROGRAMME.md, "How a disagreement is
settled"). The point is not consensus; it is that the disagreement is visible to
the next reader.

## The reviewer's veto

A reviewer may block a merge for exactly four reasons:

1. the claim cannot be stated, or the environment is unexplained;
2. the examples are not independent, or fail in `check-rules`;
3. a target was bent, or a lookup is dressed as a rule;
4. the tier overstates the evidence.

Everything else is a comment. A veto is recorded in the commit message or the
decision log, so the next reviewer knows what was already fought over.

## Reviewing a published number

Before a number goes into the README or a release note, one person who did not
produce it runs the command from a clean checkout and compares. If it differs,
the number is withdrawn until it explains itself.

## The council: a law is measured on the whole subtree

A rule written for one rung is read by every language below it. The
Proto-Indo-Iranian → Proto-Iranian transition is not only Proto-Iranian: it is
also Avestan, Old Persian, Middle Persian and Persian. A law that adds two
words to the rung and breaks one word of Persian is not a gain.

`tools/council.py` makes that measurement one command:

```bash
python tools/council.py --stage iir-pro --to ira-pro --rules candidate.yaml
python tools/council.py --stage iir-pro --to ira-pro --drop tt_to_st
```

It finds every attested language whose derivation chain contains the
transition, counts the words each one explains before and after, and speaks a
verdict. The verdict is strict by construction:

- **ACCEPT** only when no language loses a word that already matched and at
  least one language gains a word;
- **REJECT** otherwise, with the lost words printed by language.

`whatif.py` remains the fast single-language probe (and the way to ablate one
law inside a transition). The council is the final hearing: a hypothesis that
cannot pass it does not enter `data/rules/`. The losing list is kept in the
proposal's `report.md` even when the law is rejected: a rule that fails is a
finding about the corpus, not nothing.

`--layers` names what counts as explained, and it must match the question the
law is for: `exact` for a language written in Latin letters, and
`exact,script` for Old Persian, Middle Persian, Greek or Persian, where the
laws can never produce the headword character for character but can produce a
reading of its signs. Measured 2026-11-09: dropping `final_ig_to_i` costs Persian
six script matches (بینی، تهی، درزی، روزی، زنگی، پارسی), and dropping
`epenthetic_i_before_y` costs Old Persian exactly the three words it was
written for (𐎠𐎴𐎡𐎹, 𐎠𐎼𐎡𐎹, 𐎶𐎼𐎫𐎡𐎹).
