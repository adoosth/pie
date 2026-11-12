"""The six coverage bands, and the precedence that decides one.

Each test states one fact the counter measured and asserts the band it must
produce, so the coverage page, the counter and a future report cannot drift
apart.  The last class checks the denominator rule: `unidentified` estimates
words outside the glossary and is never a counted word.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import categories


class OrderTest(unittest.TestCase):
    def test_the_six_bands(self):
        self.assertEqual(categories.SIX,
                         ["full", "adjusted", "partial", "unexplained",
                          "non_pie", "unidentified"])

    def test_every_band_has_a_colour_and_a_definition(self):
        for key in categories.CATEGORIES:
            meta = categories.CATEGORIES[key]
            self.assertTrue(meta["colour"].startswith("#"), key)
            self.assertTrue(meta["definition"], key)
            self.assertTrue(meta["label"], key)

    def test_ie_loan_sits_beside_the_six(self):
        self.assertNotIn("ie_loan", categories.SIX)
        self.assertTrue(categories.CATEGORIES["ie_loan"]["extra"])

    def test_a_formation_sits_beside_the_six_too(self):
        self.assertNotIn("built", categories.SIX)
        self.assertTrue(categories.CATEGORIES["built"]["extra"])


class VerdictTest(unittest.TestCase):
    def verdict(self, **kw):
        kw.setdefault("recorded", True)
        # Explicit, because the function's own default is now the strict one:
        # a word is PIE-linked only when the test says so, and green also needs
        # the derivation itself to start at the PIE etymon.
        kw.setdefault("pie_linked", True)
        kw.setdefault("from_pie", True)
        return categories.verdict(**kw)["category"]

    def test_a_non_ie_origin_wins_over_every_other_fact(self):
        self.assertEqual(self.verdict(non_ie=True, matched_by="laws",
                                      tiers={"established"}), "non_pie")

    def test_an_ie_loan_is_never_green(self):
        self.assertEqual(self.verdict(ie_loan=True, matched_by="laws",
                                      tiers={"established"}), "ie_loan")

    def test_no_record_is_unexplained(self):
        self.assertEqual(self.verdict(recorded=False), "unexplained")

    def test_a_seam_explains_a_word_the_record_does_not(self):
        self.assertEqual(self.verdict(recorded=False,
                                      built_from=("آب", "خانه")), "built")

    def test_a_recorded_etymology_outranks_a_seam(self):
        self.assertEqual(self.verdict(recorded=True, matched_by="laws",
                                      tiers={"established"},
                                      built_from=("آب", "خانه")), "full")

    def test_a_formation_is_never_green(self):
        for extra in ({}, {"matched_by": "laws", "tiers": {"established"}}):
            self.assertEqual(self.verdict(recorded=False, built_from=("آب", "خانه"),
                                          **extra), "built")

    def test_a_borrowing_that_also_has_a_seam_stays_a_borrowing(self):
        self.assertEqual(self.verdict(recorded=False, non_ie=True,
                                      built_from=("آب", "خانه")), "non_pie")

    def test_a_record_outside_the_pie_chain_is_partial(self):
        self.assertEqual(self.verdict(pie_linked=False, matched_by="laws",
                                      tiers={"established"}), "partial")

    def test_a_derivation_that_starts_below_pie_is_partial(self):
        """Old Persian 𐎣𐎠𐎶 is exact from Proto-Iranian, not from PIE."""
        row = categories.verdict(recorded=True, pie_linked=True, from_pie=False,
                                 matched_by="laws", tiers={"established"},
                                 start_name="Proto-Iranian")
        self.assertEqual(row["category"], "partial")
        self.assertIn("Proto-Iranian", row["reason"])
        self.assertIn("not from the PIE etymon", row["reason"])

    def test_a_writing_layer_below_pie_is_partial_too(self):
        row = categories.verdict(recorded=True, pie_linked=True, from_pie=False,
                                 matched_by="orthographic", tiers={"orthographic"},
                                 start_name="Middle English")
        self.assertEqual(row["category"], "partial")

    def test_cited_laws_with_nothing_of_ours_are_full(self):
        self.assertEqual(self.verdict(matched_by="laws",
                                      tiers={"established"}), "full")

    def test_one_of_our_laws_needs_approval(self):
        row = categories.verdict(recorded=True, matched_by="laws", pie_linked=True,
                                 from_pie=True, tiers={"established", "custom"})
        self.assertEqual(row["category"], "partial")
        self.assertIn("approval", row["reason"])

    def test_an_approved_modification_is_light_green(self):
        self.assertEqual(self.verdict(matched_by="laws", tiers={"proposed"},
                                      approved=True), "adjusted")

    def test_a_writing_layer_is_a_documented_convention(self):
        self.assertEqual(self.verdict(matched_by="orthographic",
                                      tiers={"orthographic"}), "full")
        self.assertEqual(self.verdict(matched_by="script", tiers={"script"}), "full")

    def test_an_unchanged_ancestor_proves_nothing(self):
        self.assertEqual(self.verdict(matched_by="identity"), "partial")
        self.assertEqual(self.verdict(matched_by=None), "partial")

    def test_a_join_and_a_bound_form_are_not_derivations(self):
        self.assertEqual(self.verdict(matched_by="joined"), "partial")
        self.assertEqual(self.verdict(matched_by="bound"), "partial")
        self.assertEqual(self.verdict(matched_by="citation"), "partial")

    def test_a_pathway_needs_approval_too(self):
        self.assertEqual(self.verdict(matched_by="pathway"), "partial")
        self.assertEqual(self.verdict(matched_by="pathway", approved=True), "adjusted")


class RecordedStepTest(unittest.TestCase):
    """Every recorded intermediate must agree, not only the two ends.

    The project's definition (2026-11-09): "fully explained" means all the
    reconstructed intermediary steps match what is recorded; one differing step
    makes the word "fully explained, with adjustments" even when the start and
    the end word are reproduced exactly.  A step difference is a fact about the
    record, so unlike one of our law changes it needs no approval.
    """

    def test_one_differing_step_makes_it_light_green(self):
        row = categories.verdict(recorded=True, pie_linked=True, from_pie=True,
                                 matched_by="laws", tiers={"established"},
                                 mismatched_steps=["gem-pro"])
        self.assertEqual(row["category"], "adjusted")
        self.assertIn("gem-pro", row["reason"])
        self.assertEqual(row["mismatched_steps"], ["gem-pro"])

    def test_the_step_row_names_the_stages(self):
        row = categories.step_row(["gem-pro", "gmw-pro", "ang"])
        self.assertEqual(row["category"], "adjusted")
        self.assertEqual(row["reason"], "recorded step differs: gem-pro, gmw-pro, ang")
        self.assertEqual(row["mismatched_steps"], ["gem-pro", "gmw-pro", "ang"])

    def test_a_long_list_is_shortened_but_kept_whole(self):
        stages = ["gem-pro", "gmw-pro", "ang", "enm", "x"]
        row = categories.step_row(stages)
        self.assertIn("and 1 more", row["reason"])
        self.assertEqual(row["mismatched_steps"], stages)

    def test_a_writing_layer_consults_the_steps_too(self):
        row = categories.verdict(recorded=True, pie_linked=True, from_pie=True,
                                 matched_by="orthographic", tiers={"orthographic"},
                                 mismatched_steps=["pal"])
        self.assertEqual(row["category"], "adjusted")

    def test_no_step_difference_leaves_a_clean_chain_full(self):
        row = categories.verdict(recorded=True, pie_linked=True, from_pie=True,
                                 matched_by="laws", tiers={"established"},
                                 mismatched_steps=())
        self.assertEqual(row["category"], "full")


class SummaryTest(unittest.TestCase):
    def test_unidentified_is_not_in_the_denominator(self):
        counts = {"full": 10, "adjusted": 2, "partial": 6, "unexplained": 1,
                  "non_pie": 1, "unidentified": 5000}
        out = categories.summarise(counts, glossary=20, unidentified=5000)
        self.assertEqual(out["total"], 20)
        self.assertEqual(out["explained"], 12)
        self.assertEqual(out["explained_rate"], 60.0)
        self.assertEqual(out["counts"]["unidentified"], 5000)
        self.assertAlmostEqual(sum(out["share"].values()), 100.0, places=1)

    def test_without_an_estimate_the_band_is_absent(self):
        out = categories.summarise({"full": 1}, glossary=1)
        self.assertNotIn("unidentified", out["counts"])
        self.assertEqual(out["explained_rate"], 100.0)


if __name__ == "__main__":
    unittest.main()
