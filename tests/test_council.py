"""The council: find the subtree a law can reach, and speak a strict verdict."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("council_tool", ROOT / "tools" / "council.py")
council = importlib.util.module_from_spec(spec)
sys.modules["council_tool"] = council
spec.loader.exec_module(council)


class TestDownstream(unittest.TestCase):
    def test_the_iranian_subtree_is_found(self):
        langs = council.downstream("iir-pro", "ira-pro")
        self.assertEqual(
            set(langs),
            {"ira-pro", "ave", "peo", "pal", "fa", "xpr", "xme-old"},
            "Proto-Iranian and every attested language below it, and nothing else — "
            "Parthian since it was given the Iranian chain, Old Median as its "
            "Northwest Iranian sister (2026-11-12)")

    def test_the_rung_comes_before_its_descendants(self):
        langs = council.downstream("iir-pro", "ira-pro")
        self.assertEqual(langs[0], "ira-pro")
        self.assertLess(langs.index("peo"), langs.index("fa"))

    def test_a_transition_nothing_uses_is_empty(self):
        self.assertEqual(council.downstream("ine-pro", "got"), [])


class TestLayers(unittest.TestCase):
    def test_the_script_layer_is_counted_like_the_published_figure(self):
        """Old Persian can never match a Latin string; its gain is a reading."""
        from pie import data
        from whatif import exact_words
        chain = data.derivation_chain("peo")
        rulesets = data.rulesets()
        exact = exact_words("peo", chain, rulesets, None, 0, ("exact",))
        with_script = exact_words("peo", chain, rulesets, None, 0, ("exact", "script"))
        self.assertEqual(len(exact), 0)
        self.assertGreater(len(with_script), 40,
                           "the script layer counts the words the laws read sign by sign")


class TestVerdict(unittest.TestCase):
    def row(self, lang, before, after, lost=()):
        return {"language": lang, "before": before, "after": after, "lost": list(lost)}

    def test_gains_without_losses_are_accepted(self):
        ok, sentence = council.verdict([self.row("peo", 60, 64), self.row("fa", 130, 130)])
        self.assertTrue(ok)
        self.assertIn("+4", sentence)

    def test_one_lost_word_rejects_the_law(self):
        ok, sentence = council.verdict([self.row("peo", 60, 66, lost=["nāma"])])
        self.assertFalse(ok)
        self.assertIn("REJECT", sentence)

    def test_a_law_that_gains_nothing_is_not_a_rule(self):
        ok, sentence = council.verdict([self.row("peo", 60, 60)])
        self.assertFalse(ok)
        self.assertIn("gains nothing", sentence)

    def test_an_empty_subtree_is_not_an_acceptance(self):
        ok, _sentence = council.verdict([])
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
