"""A homograph's ladder belongs to the sense the page opened (2026-11-12).

Persian دوش is three words: the French loan *shower*, the inherited *shoulder*
and the adverb *last night*.  The word page picked the sense correctly, but the
ladder was always built for sense 1 — the loan, which has no sound laws — so
sense 3 showed no timeline at all, and sense 2 showed a "fully explained" badge
with no ancestry under it.  Even when the ladder did reach a homograph's own
rung, it quoted the *first* entry of that spelling: the shoulder's timeline
read "shower (bathing)".

These tests hold the three properties the page needs:

* the ladder follows the sense, not the spelling;
* its own rung quotes that sense's meaning and reading;
* a script fit does not stand in for a recorded reading — دوش is read dōš, and
  the laws' dūšā is a different word (the final -ā has no registered loss).
"""
from __future__ import annotations

import unittest

from pie import data, service

INDEX = data.DATA / "category_index.json.gz"


class DooshSenses(unittest.TestCase):
    """The three words spelled دوش, as the word page builds them."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {sense: service.word("fa", "دوش", sense=sense) for sense in (1, 2, 3)}

    def ladder(self, sense: int) -> dict:
        row = self.pages[sense].get("hierarchy")
        self.assertIsNotNone(row, f"sense {sense} has a recorded ancestry and must have a ladder")
        return row

    def test_the_loan_has_no_sound_law_ladder(self):
        self.assertIsNone(self.pages[1].get("hierarchy"),
                          "the French borrow has no PIE chain to walk")

    def test_sense_three_has_a_timeline(self):
        row = self.ladder(3)
        self.assertEqual(row["levels"][0]["stage"], "ine-pro")
        self.assertEqual(row["levels"][0]["form"], "dowséh₂")
        self.assertIn("pal", [level["stage"] for level in row["levels"]],
                      "the Middle Persian step the record states is on the ladder")

    def test_the_two_inherited_senses_walk_different_chains(self):
        shoulder = self.ladder(2)["levels"]
        last_night = self.ladder(3)["levels"]
        self.assertEqual(shoulder[0]["form"], "dóws")
        self.assertEqual(last_night[0]["form"], "dowséh₂")

    def test_the_ladder_quotes_the_sense_it_belongs_to(self):
        for sense, meaning in ((2, "shoulder"), (3, "last night")):
            recorded = self.ladder(sense)["levels"][-1]["recorded"]
            self.assertEqual(recorded["gloss"], meaning,
                             f"sense {sense}'s own rung must not quote the shower entry")

    def test_a_recorded_reading_is_not_overridden_by_the_signs(self):
        """دوش writes d-w-š; the signs allow dūšā, the record does not read it."""
        row = self.ladder(3)
        self.assertEqual(row["levels"][-1]["form"], "dūšā")
        self.assertEqual(row["levels"][-1]["status"], "differs",
                         "PIE *-eh₂'s final -ā has no registered loss")
        self.assertFalse(row["starts"][0]["match"], "the page may not say the laws reach it")
        self.assertEqual(row["levels"][-1]["recorded"]["via"], None)

    def test_the_shoulder_matches_the_reading_the_dictionary_also_records(self):
        """The laws give dūš; Wiktionary records both dōš and duš for this word."""
        final = self.ladder(2)["levels"][-1]
        self.assertEqual(final["status"], "match")
        self.assertEqual(final["recorded"]["via"], "duš",
                         "the rung names the recorded reading the match was made on")


@unittest.skipUnless(INDEX.exists(), "no published measurement (data/category_index.json.gz)")
class TheBadgeAgrees(unittest.TestCase):
    """The band on the page is the band the glossary prints (2026-11-12)."""

    def test_each_sense_shows_the_band_its_own_ladder_gives(self):
        for sense in (2, 3):
            page = service.word("fa", "دوش", sense=sense)
            self.assertEqual(page["category"]["category"],
                             page["hierarchy"]["category"]["category"],
                             f"sense {sense}: the badge and the timeline disagree")
        self.assertEqual(service.word("fa", "دوش", sense=3)["category"]["category"], "partial",
                         "PIE *-eh₂'s -ā is not dropped by any registered law")


class TheGlossaryRow(unittest.TestCase):
    def test_each_row_prints_its_own_reading(self):
        """دوش is duš the shower and dōš the shoulder — one reading per row."""
        rows = {r["sense"]: r for r in service.glossary("fa", q="دوش", limit=50)["rows"]
                if r["word"] == "دوش"}
        self.assertEqual(rows[1]["reading"], "duš")
        self.assertEqual(rows[2]["reading"], "dōš")
        self.assertEqual(rows[3]["reading"], "dōš")


class ReadingFit(unittest.TestCase):
    def test_an_abjad_fit_agrees_with_the_reading_or_not_at_all(self):
        entries = {g["sense"]: g["rep"] for g in service.sense_index()[("fa", "دوش")]}
        self.assertIsNone(service._script_fit(entries[3], "dūšā"),
                          "the shoulder's node reads dōš/duš, not dūšā")
        self.assertIsNotNone(service._script_fit(entries[2], "dūš"),
                             "dūš reproduces the recorded spelling duš")


if __name__ == "__main__":
    unittest.main()
