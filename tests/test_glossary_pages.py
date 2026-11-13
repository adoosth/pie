"""The glossary is read in pages, not in its first 400 words.

A stage of 17,000 words (Middle Persian after the MPCD import, 2026-11-13)
showed the first 400 with no way on: the list has to say which slice it is and
answer for the next one, and two pages must never hold the same word.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import service


class TestPages(unittest.TestCase):
    def test_the_first_page_says_how_many_there_are(self):
        page = service.glossary("pal", band="all")
        self.assertEqual(page["page"], 1)
        self.assertEqual(page["first"], 1)
        self.assertEqual(page["last"], len(page["rows"]))
        self.assertEqual(page["pages"], -(-page["total"] // page["limit"]))
        self.assertGreater(page["pages"], 1, "Middle Persian is longer than one page")

    def test_the_second_page_starts_where_the_first_stops(self):
        one = service.glossary("pal", band="all")
        two = service.glossary("pal", band="all", page=2)
        self.assertEqual(two["first"], one["last"] + 1)
        self.assertFalse({r["word"] for r in one["rows"]} & {r["word"] for r in two["rows"]})
        self.assertEqual(one["total"], two["total"])

    def test_a_page_past_the_end_is_the_last_page(self):
        one = service.glossary("pal", band="all")
        last = service.glossary("pal", band="all", page=one["pages"])
        over = service.glossary("pal", band="all", page=one["pages"] + 7)
        self.assertEqual(over["page"], one["pages"])
        self.assertEqual([r["word"] for r in over["rows"]], [r["word"] for r in last["rows"]])
        self.assertEqual(over["last"], one["total"])

    def test_every_word_is_reachable_and_each_page_is_dressed(self):
        # A row is a word *of one sense*: a spelling that carries two words is
        # two rows, and both are reachable (2026-11-09).
        seen: set[tuple[str, int]] = set()
        for number in (1, 2, 3):
            page = service.glossary("pal", band="all", limit=50, page=number)
            self.assertTrue(page["rows"])
            for row in page["rows"]:
                self.assertIn("gloss", row)
                self.assertIn("attestation", row)
                self.assertIn("transcription", row)
                self.assertIn("transliteration", row)
                seen.add((row["word"], row.get("sense") or 1))
        self.assertEqual(len(seen), 150)

    def test_a_filter_keeps_its_own_pages(self):
        page = service.glossary("pal", band="all", q="garm", limit=2, page=2)
        self.assertTrue(all("garm" in r["word"] for r in page["rows"]))
        self.assertEqual(page["page"], 2)

    def test_a_middle_persian_row_prints_its_reading_and_its_spelling(self):
        page = service.glossary("pal", band="all", q="garm", limit=10)
        row = next(r for r in page["rows"] if r["word"] == "garm")
        self.assertEqual(row["attestation"], "attested")
        self.assertEqual(row["transcription"], "garm")
        self.assertEqual(row["transliteration"], "glm · g03lm · g03lmtl")


if __name__ == "__main__":
    unittest.main()
