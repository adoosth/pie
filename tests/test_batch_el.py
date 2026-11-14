"""Modern Greek from Ancient Greek: the last step of the Hellenic chain.

The chain is ``ine-pro → grk-pro → grc → el``.  Modern Greek writes a
different script from the phonemic notation the laws carry, so no law can ever
produce the attested headword character-for-character: the historical figure
stays 0 for ``el`` and the honest measure is the *orthographic* layer, where
the laws give a phonemic form and ``data/spelling/el.yaml`` writes it in the
monotonic alphabet.  Two artefacts carry the transition — the law file
``data/rules/grc__el.yaml`` and that spelling table — and these tests pin the
parts that must stay true: every law states a tier and a source and passes its
own example, the spelling file is a convention and not a lookup, and the laws
fire exactly where the grammar says they do and nowhere else.

The corpus numbers are a floor, not a target.  Until 2026-11-11 only 1,219 of
the 5,082 tested words had a *machine-readable* ancestor: the other 3,802 handed
the sound laws the Greek letters themselves, because the ancestor is missing
from ``data/lexicon/grc.jsonl.gz`` and no law can rewrite a letter.  The reading
now comes from the script itself (``service._phonological_form``: the alphabet
is read letter by letter, Πέρσης → *Pérsēs*), so every one of the 5,028 words
with a Greek ancestor has a form the laws can take.  Which is why the number
that matters here is still the orthographic one: the laws end in a phonemic
form and ``data/spelling/el.yaml`` writes it in the monotonic alphabet, and no
law ever produces the Greek letters character for character.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling, translit           # noqa: E402
from pie.phonology import detokenize, tokenize     # noqa: E402
from pie.rules import apply_ruleset, derive        # noqa: E402

SRC, DST = "grc", "el"


def _ruleset():
    return data.rulesets()[(SRC, DST)]


def _one(rule_id: str, form: str) -> str:
    rule = next(r for r in _ruleset().rules if r.id == rule_id)
    out, _steps = apply_ruleset(
        form, type("RS", (), {"rules": [rule], "target_stage": ""})(), enabled=[rule.id])
    return out


def _run(form: str) -> str:
    chain = data.derivation_chain(DST)
    return derive(form, chain[chain.index(SRC):], data.rulesets()).output


def _spell(form: str) -> str:
    return spelling.spell(_run(form), DST)


class LawSet(unittest.TestCase):
    def test_the_transition_exists_and_is_not_empty(self):
        self.assertIn((SRC, DST), data.rulesets())
        self.assertGreaterEqual(len(_ruleset().rules), 30)

    def test_every_law_states_a_tier_and_a_known_source(self):
        known = set(data.sources())
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.tier, {"established", "proposed", "orthographic"})
                self.assertTrue(rule.references, "a law without a source is a guess")
                for ref in rule.references:
                    self.assertIn(ref, known)

    def test_every_law_has_a_verified_example(self):
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.examples)
                for ex in rule.examples:
                    self.assertEqual(_one(rule.id, ex["in"]), detokenize(tokenize(ex["out"])))

    def test_the_historical_laws_are_established(self):
        ids = {r.id: r.tier for r in _ruleset().rules}
        for rid in ("h_loss_initial", "h_loss_after_rho", "loss_of_long_quantity",
                    "ph_to_f", "th_to_theta", "kh_to_chi", "au_to_af", "au_to_av",
                    "eu_to_ef", "eu_to_ev", "b_to_v", "d_to_delta", "g_to_gamma",
                    "final_n_loss", "pt_to_ft_initial", "loss_of_breve_a",
                    "loss_of_breve_i", "loss_of_breve_u"):
            self.assertEqual(ids[rid], "established", rid)

    def test_the_notation_rules_are_orthographic_not_laws(self):
        # The digraph and circumflex rules normalise the dictionary's
        # transliteration and the accent; they claim no sound change.
        ids = {r.id: r.tier for r in _ruleset().rules}
        for rid in ("ph_digraph", "th_digraph", "kh_digraph", "xi_digraph",
                    "circumflex_a_to_tonos", "iota_subscript_loss"):
            self.assertEqual(ids[rid], "orthographic", rid)


class Laws(unittest.TestCase):
    def test_the_rough_breathing_is_lost(self):
        self.assertEqual(_run("hˈippos"), "ˈippos")
        self.assertEqual(_run("rhˈētōr"), "rˈētōr")

    def test_the_aspirates_become_fricatives(self):
        self.assertEqual(_run("pʰōnˈē"), "fōnˈē")
        self.assertEqual(_run("tʰerapˈeia"), "θerapˈeia")
        self.assertEqual(_run("kʰōrˈa"), "χōrˈa")

    def test_the_voiced_stops_spirantise(self):
        self.assertEqual(_run("bˈasis"), "vˈasis")
        self.assertEqual(_run("dˈōron"), "ðˈōro")
        self.assertEqual(_run("gˈala"), "ɣˈala")

    def test_the_au_eu_split_by_the_following_voicing(self):
        # Voiceless before a voiceless consonant, voiced otherwise.
        self.assertEqual(_run("autˈos"), "aftˈos")
        self.assertEqual(_run("aulˈē"), "avlˈē")
        self.assertEqual(_run("eukʰˈē"), "efχˈē")
        self.assertEqual(_run("eugnōmˈōn"), "evɣnōmˈō")

    def test_length_is_lost(self):
        # The macron shortens and the final -n falls: λιμήν > λιμή.
        self.assertEqual(_run("līmˈēn"), "limˈē")
        self.assertEqual(_run("psūkʰˈē"), "psuχˈē")

    def test_final_n_is_lost(self):
        self.assertEqual(_run("dˈōron"), "ðˈōro")
        # The law is stated for the word-final position only: an *n inside the
        # word is untouched (ἄνθρωπος keeps its ν).
        self.assertEqual(_run("anˈthrōpos"), "anˈθrōpos")

    def test_initial_pt_but_not_medial_pt_becomes_ft(self):
        self.assertEqual(_run("ptˈuō"), "ftˈuō")
        # Medial pt is untouched: the candidate that changed it everywhere was
        # rejected on the council because επτά and κάμπτω keep their πτ.  The
        # initial breathing is lost, so ἑπτά gives επτά with πτ intact.
        self.assertEqual(_run("hepˈta"), "epˈta")

    def test_the_diglossia_rules_do_not_rewrite_itacism(self):
        # η, υ, ει, οι keep their inherited letters: the itacism is a fact
        # about the sound, stated in the stage prose, and rewriting ē > i would
        # make the modern spelling unreachable (η would be written ι).  So a
        # staged *ē must still spell η.
        self.assertEqual(_spell("mētˈera"), "μητέρα")
        self.assertEqual(_spell("psūkʰˈē"), "ψυχή")


class Spelling(unittest.TestCase):
    def test_the_spelling_layer_exists_and_owns_the_order(self):
        self.assertTrue(spelling.applies(DST))
        rs = spelling.ruleset(DST)
        self.assertTrue(rs.rules)
        self.assertGreaterEqual(len(rs.rules), 40)

    def test_the_alphabet_writes_the_merged_vowels_with_their_letters(self):
        self.assertEqual(_spell("mētˈera"), "μητέρα")
        self.assertEqual(_spell("lˈoɣos"), "λόγος")
        self.assertEqual(_spell("psūkʰˈē"), "ψυχή")

    def test_the_au_eu_digraphs_write_both_voicing_outcomes(self):
        self.assertEqual(_spell("autˈos"), "αυτός")
        self.assertEqual(_spell("aulˈē"), "αυλή")
        self.assertEqual(_spell("eukʰˈē"), "ευχή")

    def test_the_score_is_the_tonos_and_the_sigma_is_final(self):
        self.assertEqual(_spell("dˈōron"), "δώρο")
        self.assertEqual(_spell("kanˈenas"), "κανένας")
        self.assertEqual(_spell("lˈoɣos")[-1], "ς")

    def test_the_conventions_are_writing_rules_not_lookups(self):
        rs = spelling.ruleset(DST)
        for rule in rs.rules:
            with self.subTest(rule=rule.id):
                self.assertEqual(rule.tier, "orthographic")
                self.assertTrue(rule.examples)
                # A convention matches a segment or a digraph, never a word.
                self.assertLessEqual(len(tokenize(rule.match or "")), 2)


class Floors(unittest.TestCase):
    """The corpus floors: a regression below these means something broke."""

    def test_every_greek_ancestor_can_be_read(self):
        # Guards the inventory the report rests on.  Before 2026-11-11 this was
        # the opposite assertion — 3,802 of 5,082 words had an ancestor no law
        # could carry, because Greek letters were handed to the engine as if
        # they were segments.  The alphabet is read letter by letter now
        # (service._phonological_form), so the floor is the other way round: a
        # Greek word whose ancestor is still a writing is a bug.
        from coverage import ancestor_starts

        chain = data.derivation_chain(DST)
        readable = unreadable = 0
        still_written: list[str] = []
        for entry in data.lexicon(DST):
            if entry.get("recon"):
                continue
            starts = [(st, f) for st, f in ancestor_starts(entry, chain) if st == SRC]
            if not starts:
                continue
            if any(not translit.is_scripted(f) for _, f in starts):
                readable += 1
            else:
                unreadable += 1
                still_written.append(f"{entry['word']}: {starts[0][1]}")
        self.assertGreaterEqual(readable, 5000,
                                f"readable ancestors shrank: {still_written[:5]}")
        self.assertEqual(unreadable, 0,
                         f"an ancestor in Greek letters reached the laws: {still_written[:5]}")

    def test_the_spelling_layer_explains_a_floor_of_words(self):
        # A measured floor (2026-11-09): 270 orthographic words.  It may only
        # rise; the test fails if a later change drops it.
        from coverage import orthographic_hit
        chain = data.derivation_chain(DST)
        rs = data.rulesets()
        orth = 0
        for entry in data.lexicon(DST):
            if entry.get("recon"):
                continue
            target = str(entry.get("word") or "").strip()
            if not target:
                continue
            ipa = entry.get("ipa") or ""
            for stage, form in [(s, f) for s, f in _starts(entry, chain, SRC)]:
                try:
                    d = derive(form, chain[chain.index(stage):], rs)
                except Exception:
                    continue
                if d.skipped or not d.steps:
                    continue
                if orthographic_hit([(d.output, len(d.steps), stage)], DST, target, ipa):
                    orth += 1
                    break
        self.assertGreaterEqual(orth, 260, f"orthographic layer fell to {orth}")


def _starts(entry, chain, stage):
    from coverage import ancestor_starts
    return [(s, f) for s, f in ancestor_starts(entry, chain) if s == stage]


if __name__ == "__main__":
    unittest.main()
