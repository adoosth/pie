"""Old Irish from Proto-Celtic: the missing last step of the Goidelic chain.

The chain is ``ine-pro → cel-pro → sga`` and ``data/rules/cel-pro__sga.yaml``
did not exist, so all 1,719 tested entries missed by construction before this
file.  Two artefacts close it — the law file and ``data/spelling/sga.yaml``,
the writing conventions (c for /k/, th for /θ/, ch for /x/, the acute for
length) — and these tests pin the parts that must stay true: every law states
a tier and a source and passes its own example, the spelling file is a
convention and not a lookup, and the laws fire exactly where the grammar says
they do and nowhere else.  The corpus numbers are a floor, not a target: the
Proto-Celtic transition above this one may move.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling                    # noqa: E402
from pie.phonology import detokenize, tokenize     # noqa: E402
from pie.rules import apply_ruleset, derive        # noqa: E402

SRC, DST = "cel-pro", "sga"


def _ruleset():
    return data.rulesets()[(SRC, DST)]


def _one(rule_id: str, form: str) -> str:
    rule = next(r for r in _ruleset().rules if r.id == rule_id)
    out, _steps = apply_ruleset(
        form, type("RS", (), {"rules": [rule], "target_stage": ""})(), enabled=[rule.id])
    return out


def _run(form: str) -> str:
    return derive(form, [SRC, DST], data.rulesets()).output


def _spell(form: str) -> str:
    return spelling.spell(_run(form), DST)


class LawSet(unittest.TestCase):
    def test_the_transition_exists_and_is_not_empty(self):
        self.assertIn((SRC, DST), data.rulesets())
        self.assertGreaterEqual(len(_ruleset().rules), 15)

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

    def test_every_law_names_the_grammar_in_its_prose(self):
        # The machine-checked `references` are the source keys this repo holds;
        # Thurneysen, Pedersen, McCone, Stifter and Matasović are named in the
        # description, so every rule carries a locator of the form §nnn or a
        # chapter reference.
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertTrue("§" in rule.change or "ch." in rule.change,
                                rule.change[:60])

    def test_the_named_laws_are_established(self):
        ids = {r.id: r.tier for r in _ruleset().rules}
        for rid in ("p_loss_initial", "w_to_f", "kw_to_k", "t_to_theta_intervocalic",
                    "k_to_x_intervocalic", "final_os_loss", "final_om_loss",
                    "final_is_loss", "final_long_a_loss", "i_affection_a",
                    "a_affection_i", "s_to_h", "h_loss_intervocalic"):
            self.assertEqual(ids[rid], "established", rid)


class Laws(unittest.TestCase):
    def test_apocope_leaves_the_bare_stem(self):
        self.assertEqual(_run("*branos"), "bran")
        self.assertEqual(_run("*benā"), "ben")
        self.assertEqual(_run("*klutom"), "kloθ")
        self.assertEqual(_run("*dubus"), "dub")

    def test_initial_phi_is_lost_and_initial_w_becomes_f(self):
        self.assertEqual(_run("*ɸatīr"), "aiθīr")
        self.assertEqual(_run("*windos").startswith("f"), True)
        # A medial *w is lost instead: *towe > toe, not *tofe.
        self.assertEqual(_run("*towe"), "toe")

    def test_labiovelars_split_by_the_following_vowel(self):
        self.assertEqual(_run("*kʷennom"), "kenn")
        self.assertEqual(_run("*gʷenom"), "gen")
        self.assertEqual(_run("*gʷarnos").startswith("b"), True)

    def test_lenition_is_intervocalic_only(self):
        self.assertEqual(_run("*kritos"), "kreθ")
        self.assertEqual(_run("*kritos")[0], "k")           # no initial lenition
        # *k after a consonant is not spirantised: *skeyeti keeps its k.
        self.assertEqual(_run("*skeyeti").startswith("sk"), True)

    def test_affection_needs_the_following_vowel(self):
        self.assertEqual(_run("*galis"), "gail")             # i-affection
        self.assertEqual(_run("*limos"), "lem")              # a-affection
        # With a high vowel in the next syllable the a stays an a.
        self.assertEqual(_run("*damos"), "dam")

    def test_the_endings_are_not_lost_when_they_are_not_final(self):
        # Only the final syllable goes: the o of *damos is the stem vowel and
        # survives, and only the *-ā of *westā is lost.
        self.assertEqual(_run("*damos"), "dam")
        self.assertEqual(_run("*westā"), "fest")


class Spelling(unittest.TestCase):
    def test_the_spelling_layer_exists(self):
        self.assertTrue(spelling.applies(DST))

    def test_the_alphabet_has_no_k_and_marks_length_with_the_acute(self):
        self.assertEqual(_spell("*kʷennom"), "cenn")
        self.assertEqual(_spell("*sekʷos"), "sech")
        self.assertEqual(_spell("*klutom"), "cloth")
        self.assertEqual(_spell("*matus"), "math")
        self.assertEqual(_spell("*ɸatīr"), "aithír")

    def test_the_conventions_are_writing_rules_not_lookups(self):
        # Every spelling rule is a tier `orthographic` rule with an example of
        # a full form, and none of them matches a whole word as a lookup.
        rs = spelling.ruleset(DST)
        self.assertTrue(rs.rules)
        for rule in rs.rules:
            with self.subTest(rule=rule.id):
                self.assertEqual(rule.tier, "orthographic")
                self.assertTrue(rule.examples)
                self.assertLessEqual(len(rule.match or ""), 2)


if __name__ == "__main__":
    unittest.main()
