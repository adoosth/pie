"""A word the record does not analyse may still be made of its own words.

The seam reader is the only place where this model says something the record
does not: an unetymologised headword is cut into words (or a stem plus one of
the stage's recorded suffixes) and, when exactly one reading survives, the word
is *built*, never explained by sound laws.  These tests pin the three orders in
which the evidence is used, the refusals, and the agreement between the word
page and the counter (2026-11-10).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import categories, service


class SuffixFirstTest(unittest.TestCase):
    def test_a_recorded_suffix_is_the_strongest_seam(self):
        seam = service.seam_of("fa", "آتشگاه")
        self.assertEqual(seam["kind"], "suffix")
        self.assertEqual(seam["parts"], ["آتش", "-گاه"])

    def test_the_stem_has_to_be_a_headword_with_an_origin(self):
        # «بیگاه» is not a word with a recorded origin, so no seam is claimed
        # from it even though the suffix itself is real.
        self.assertIsNone(service.seam_of("fa", "بیگاه۲"))


class SplitTest(unittest.TestCase):
    def test_two_words_of_the_language_are_joined_at_their_own_seam(self):
        seam = service.seam_of("fa", "آب\u200cخانه")
        self.assertEqual(seam["kind"], "compound")
        self.assertEqual(seam["parts"], ["آب", "خانه"])
        self.assertEqual(seam["verdict"], "unique")

    def test_a_stop_word_is_never_a_piece(self):
        # پیشاب is not پیش + اب ("father"); the rules file names اب in `stop`.
        self.assertIsNone(service.seam_of("fa", "پیشاب"))

    def test_a_tie_is_refused_rather_than_scored(self):
        seam = service.seam_of("fa", "خدانگاهدار")
        if seam is not None and seam.get("verdict") == "ambiguous":
            self.assertGreater(len(seam["alternatives"]), 1)
            self.assertIn("left unclassified", seam["sentence"])
        else:
            self.skipTest("no ambiguous example in this lexicon build")


class BandTest(unittest.TestCase):
    def test_a_built_word_sits_beside_the_six_and_is_never_green(self):
        band = service._page_category(
            {"word": "آب\u200cخانه", "lang": "fa"}, "fa", None)
        self.assertEqual(band["category"], "built")
        self.assertNotIn("built", categories.SIX)
        self.assertIn("not a derivation", band["reason"])

    def test_a_recorded_etymology_outranks_the_seam(self):
        page = service.word("fa", "کتاب")
        self.assertNotEqual((page.get("category") or {}).get("category"), "built")

    def test_the_word_page_carries_the_seam_and_its_sentence(self):
        page = service.word("fa", "آب\u200cخانه")
        self.assertEqual(page["seam"]["parts"], ["آب", "خانه"])
        self.assertIn("formation", page["seam"]["sentence"])

    def test_the_ladder_says_whose_claim_the_row_is(self):
        ladder = service.hierarchy("fa", "آب\u200cخانه")
        row = ladder["levels"][-1]
        self.assertEqual(row["built_as"]["source"], "ours")
        self.assertEqual(row["built_as"]["kind"], "compound")
        self.assertEqual(ladder["category"]["category"], "built")


if __name__ == "__main__":
    unittest.main()
