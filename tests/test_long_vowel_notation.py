"""Two romanisation schemes for one long vowel are one letter, not two.

The dictionaries print the Persian long vowels with the circumflex (bâz, târ,
dûr) while the sound laws write them with the macron (bāz, tār, dūr).  Both are
the same letter with the same length in the same place, so the counters and the
page compare them as one form; a short vowel is still a different form
(2026-11-09: 25 Persian words were missing from the identity column for the
character alone).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import coverage  # noqa: E402
from pie import service  # noqa: E402


class LongVowelNotationTest(unittest.TestCase):
    def test_the_page_reads_both_schemes_as_one_form(self):
        for pair in (("bâz", "bāz"), ("târ", "tār"), ("dûr", "dūr")):
            self.assertTrue(service._same_form(*pair), pair)

    def test_a_different_vowel_is_not_folded(self):
        self.assertFalse(service._same_form("bāz", "bōz"))
        self.assertFalse(service._same_form("bāz", "baz"))
        self.assertFalse(service._same_form("tār", "tär"))

    def test_the_counter_folds_the_record_the_same_way(self):
        entry = {"word": "باز", "translit": "bâz"}
        outputs = [("bāz", 0, "pal")]
        self.assertEqual(coverage._identity_hit(outputs, "باز", entry),
                         ("bāz", "pal"))
        # A zero-step form that is not the record's form is still no identity.
        self.assertIsNone(coverage._identity_hit([("bōz", 0, "pal")], "باز", entry))

    def test_the_fold_changes_no_letter(self):
        table = coverage._LONG_VOWEL_NOTATION
        self.assertEqual("bâz".translate(table), "bāz")
        self.assertEqual(len("bâz"), len("bâz".translate(table)))


if __name__ == "__main__":
    unittest.main()
