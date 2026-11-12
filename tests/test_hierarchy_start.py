"""The ladder opens at the recorded ancestor its laws actually reach (2026-11-09).

The entry for Old Persian 𐎠𐎴𐎡𐎹 (aniya-) states Proto-Indo-Iranian *Hanyás and
then falls back on a cognate-set root for PIE.  A root is not an inheritance
row: the ladder therefore starts at the Proto-Indo-Iranian word the record
names, and the root stays above it as the cognate it is (proposals/010).  The
page and `tools/coverage.py` then agree on the same start.
"""

import unittest

from pie import service


class TestReachedFromARecordedAncestor(unittest.TestCase):
    def setUp(self):
        self.row = service.hierarchy("peo", "𐎠𐎴𐎡𐎹")

    def test_the_ladder_opens_at_the_recorded_word_the_laws_reach(self):
        # The start is still the Proto-Indo-Iranian word the laws reach; since
        # 2026-11-12 the rung above it is that word's own ladder (its article
        # climbs further), so the printed column may begin higher.
        self.assertEqual(self.row["start"], "iir-pro")
        iir = next(l for l in self.row["levels"] if l["stage"] == "iir-pro")
        self.assertEqual(iir["form"], "Hanyás", "the rung quotes the word it starts from")
        self.assertIn(self.row["levels"][0]["stage"], {"ine-pro", "iir-pro"})
        self.assertFalse(self.row["set_start"], "the set names a root, not a start")
        self.assertTrue(self.row["linked_by_set"], "but the set is still the PIE link")

    def test_the_full_path_reaches_and_the_page_says_so(self):
        self.assertEqual(self.row["result"]["status"], "match")

    def test_and_it_names_the_ancestor_the_laws_do_reach(self):
        self.assertEqual(self.row["exact"]["stage"], "iir-pro")
        self.assertEqual(self.row["exact"]["form"], "Hanyás")
        self.assertTrue(self.row["exact"]["via_translit"],
                        "the laws produce the romanisation the record writes")

    def test_the_offered_starts_agree_with_the_counter(self):
        starts = self.row["starts"]
        reached = [row["stage"] for row in starts if row["match"]]
        self.assertIn("iir-pro", reached)
        self.assertIn("ira-pro", reached)


if __name__ == "__main__":
    unittest.main()
