"""The Proto-Indo-Iranian → Proto-Iranian laws this session added or repaired.

Three things are pinned here:

* PII *-tt- (written *tˢt in the corpus) becomes PIr *-st- — the change behind
  Avestan vista- against Sanskrit vittá- (Hoffmann & Forssman 2004; Mayrhofer
  1986).  Its environment is the affricated spelling plus a following *t, so a
  plain geminate *tt and a *tˢ before anything else survive untouched.
* PII *l merges with PIr *r as an *established* law (it was `proposed` with a
  note saying the merger had not been verified; the merger is standard).
* The laws already in the file stay narrow: *s is kept before a stop, and the
  new law may not cost a word that already matched.

The regression test compares the transition against itself with the new law
switched off, so it measures the law and not the rest of the tree (other
workers own the files on either side of this transition).
"""
from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

spec = importlib.util.spec_from_file_location("coverage_tool", ROOT / "tools" / "coverage.py")
coverage_tool = importlib.util.module_from_spec(spec)
sys.modules["coverage_tool"] = coverage_tool
spec.loader.exec_module(coverage_tool)

from pie import data                       # noqa: E402
from pie.rules import derive               # noqa: E402

CHAIN = ["iir-pro", "ira-pro"]


def step(form: str, rs=None) -> str:
    return derive(form, CHAIN, rs or data.rulesets()).output


def kind(form: str, expected: str) -> str | None:
    """How the derivation meets a target: the engine writes stress as ˈ, the
    dictionary as an acute, and `exact_kind` knows the two are one accent."""
    return coverage_tool.exact_kind(step(form), expected)


def exact_words(rs) -> set[str]:
    """Headwords the transition carries from their own recorded ancestor."""
    out: set[str] = set()
    for entry in data.lexicon("ira-pro"):
        if entry.get("recon"):
            continue
        target = entry["word"].strip()
        for stage, form in coverage_tool.ancestor_starts(entry, CHAIN):
            d = derive(form, CHAIN[CHAIN.index(stage):], rs)
            if d.skipped:
                continue
            if d.steps and coverage_tool.exact_kind(d.output, target):
                out.add(target)
                break
    return out


class TestLawShape(unittest.TestCase):
    def setUp(self):
        self.rules = {r.id: r for r in data.rulesets()[("iir-pro", "ira-pro")].rules}

    def test_the_tt_law_is_registered_and_cited(self):
        rule = self.rules["tt_to_st"]
        self.assertEqual(rule.tier, "established")
        self.assertTrue(rule.references)
        self.assertEqual(rule.right, "t")

    def test_the_liquid_merger_is_established(self):
        # It used to be `proposed` with a note that the merger was unverified;
        # PII *l > PIr *r is standard (Av. raocah- : Skt. róka-).
        rule = self.rules["l_to_r"]
        self.assertEqual(rule.tier, "established")
        self.assertTrue(rule.references)


class TestTtToSt(unittest.TestCase):
    def test_the_affricate_plus_t_gives_s_plus_t(self):
        self.assertEqual(kind("*winátˢti", "winásti"), "notation")
        self.assertEqual(kind("*Háwāytˢt", "Háwāyst"), "notation")

    def test_a_plain_geminate_is_not_touched(self):
        # PII *kúttas is written with two *t, not with the affricate *tˢ; the
        # law must leave it alone (its PIr reflex is *kútah, not *kústah).
        self.assertNotIn("st", coverage_tool._stress_free(step("*kúttas")))

    def test_it_writes_s_and_not_h(self):
        # The law runs before s_to_h; the *s stands before *t, where s_to_h
        # keeps *s, so the output must not be *št or *ht.
        self.assertTrue(coverage_tool._stress_free(step("*winátˢti")).endswith("sti"))

    def test_it_carries_two_words_and_costs_none(self):
        full = data.rulesets()
        without = copy.deepcopy(full)
        without[("iir-pro", "ira-pro")].rules = [
            r for r in without[("iir-pro", "ira-pro")].rules if r.id != "tt_to_st"
        ]
        self.assertEqual(exact_words(full) - exact_words(without), {"winásti", "Háwāyst"})
        self.assertEqual(exact_words(without) - exact_words(full), set())


class TestNeighbouringLaws(unittest.TestCase):
    def test_s_is_kept_before_a_stop(self):
        # The exception in s_to_h is load-bearing: dropping it cost 10 words.
        self.assertEqual(step("*stā-"), "stā")
        self.assertEqual(kind("*ásuras", "áhurah"), "notation")

    def test_palatal_affricates_are_retracted(self):
        self.assertEqual(kind("*ćatám", "catám"), "notation")

    def test_liquid_merger_runs(self):
        self.assertEqual(kind("*lagúš", "ragúš"), "notation")


if __name__ == "__main__":
    unittest.main()


class TestMiddlePersianFinalIs(unittest.TestCase):
    """OP *-iš has no Middle Persian ending (OP būmiš > MP būm, bwm).

    The law is `proposed` and carries one word through the whole page path;
    what it may not do is cost a word that already matched (2026-11-12).
    """

    def test_the_law_is_registered_from_old_persian(self):
        rules = {r.id: r for r in data.rulesets()[("peo", "pal")].rules}
        self.assertIn("final_ish_loss", rules)

    def test_the_page_reaches_the_word(self):
        from pie import service

        page = service.word("pal", "bwm")
        self.assertTrue((page.get("derivation") or {}).get("match"),
                        "OP būmiš must reach MP būm through the laws")
