"""One spelling, several words (2026-11-09).

The project's request: a language stores words that are written exactly alike as
separate entries with a selector for each meaning, a glossary row each with a
subtext 1 2 …, reconstructions linking to the right homonym, and a landing page
when a link cannot say which one it means.  These tests hold the three things
that make that possible: the grouping in `pie.senses`, the landing page and
sense parameter in `service.word`, and the one-row-per-word glossary.
"""
from __future__ import annotations

import unittest

from pie import senses, service


def entry(word, pos, gloss, anc=(), etym=""):
    row = {"word": word, "pos": pos, "gloss": [gloss]}
    if anc:
        row["anc"] = [list(a) for a in anc]
    if etym:
        row["etym"] = etym
    return row


class GroupingTest(unittest.TestCase):
    def test_parts_of_speech_of_one_path_are_one_word(self):
        chain = [("ira-pro", "*daywánah", "inherit"), ("ine-pro", "*deywós", "inherit")]
        rows = [entry("دیوانه", "adj", "mad", chain, "Inherited from Middle Persian dyw'nk'"),
                entry("دیوانه", "noun", "madman", chain, "Inherited from Middle Persian dyw'nk'")]
        groups = senses.groups(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["pos"], ["adj", "noun"])
        self.assertEqual(groups[0]["gloss"], ["mad", "madman"])

    def test_a_chain_written_more_briefly_is_the_same_chain(self):
        """دیوانه the noun names Proto-Iranian only; the adjective goes on to PIE."""
        long_chain = [("ira-pro", "*daywánah", "inherit"),
                      ("iir-pro", "*daywás", "inherit"),
                      ("ine-pro", "*deywós", "inherit")]
        prose = "Inherited from Middle Persian (dyw'nk' /dēwānag/, “demonic; crazy”)"
        rows = [entry("دیوانه", "adj", "mad", long_chain, prose),
                entry("دیوانه", "noun", "madman", long_chain[:1], prose)]
        self.assertEqual(len(senses.groups(rows)), 1)

    def test_two_etymologies_are_two_words(self):
        rows = [entry("بار", "noun", "burden",
                      [("pal", "bʾl", "inherit"), ("ira-pro", "*bāra-", "inherit")],
                      "From Middle Persian bʾl (bār, “load”)"),
                entry("بار", "noun", "shore",
                      [("pal", "bʾl", "inherit"), ("ine-pro", "*bʰerH-", "derived")],
                      "From Middle Persian bʾl (bār, “bank”)")]
        groups = senses.groups(rows)
        self.assertEqual(len(groups), 2)
        self.assertEqual([g["sense"] for g in groups], [1, 2])

    def test_one_etymon_two_derived_words_stay_two_when_the_prose_differs(self):
        """Old English rīce “kingdom” and rīce “rich” share *rīkī, and are not one word."""
        chain = [("gmw-pro", "*rīkī", "inherit")]
        rows = [entry("rice", "noun", "kingdom", chain,
                      "From Proto-West Germanic *rīkī (“kingdom, realm”)."),
                entry("rice", "adj", "mighty", chain,
                      "From Proto-West Germanic *rīkī (“mighty, rich”).")]
        self.assertEqual(len(senses.groups(rows)), 2)

    def test_an_entry_with_nothing_recorded_is_its_own_word(self):
        rows = [entry("x", "noun", "a"), entry("x", "verb", "b")]
        self.assertEqual(len(senses.groups(rows)), 2)


class WordPageTest(unittest.TestCase):
    def test_a_homograph_opens_the_page_that_lists_its_words(self):
        page = service.word("fa", "سر")
        self.assertTrue(page.get("pick"), "a link that names no sense must not pick one")
        self.assertEqual(page["variants"], len(page["senses"]))
        self.assertGreater(page["variants"], 1)
        for row in page["senses"]:
            self.assertIn("gloss", row)
            self.assertIn("band", row)

    def test_a_named_sense_opens_that_word(self):
        page = service.word("fa", "سر", sense=2)
        self.assertFalse(page.get("pick"))
        self.assertEqual(page["sense"], 2)
        self.assertIn(page["category"]["category"], ("full", "adjusted", "partial",
                                                     "unexplained", "non_pie", "ie_loan"))
        self.assertTrue(any(g == "secret" for g in page["gloss"]), page["gloss"])

    def test_the_page_lists_its_siblings(self):
        page = service.word("fa", "سر", sense=1)
        self.assertEqual([row["sense"] for row in page["sense_list"]],
                         list(range(1, page["variants"] + 1)))

    def test_an_unrelated_spelling_is_untouched(self):
        """A word with one meaning still opens at once, as it always did."""
        page = service.word("fa", "پدر")
        self.assertFalse(page.get("pick"))
        self.assertEqual(page["sense"], 1)


class GlossaryRowsTest(unittest.TestCase):
    def test_a_homograph_has_one_row_per_word(self):
        page = service.glossary("fa", limit=4000, q="بار")
        rows = [r for r in page["rows"] if r["word"] == "بار"]
        self.assertGreater(len(rows), 1, "بار is several words")
        self.assertEqual([r["sense"] for r in rows], list(range(1, len(rows) + 1)))
        self.assertTrue(all(r["senses"] == len(rows) for r in rows))

    def test_a_single_word_with_two_parts_of_speech_is_one_row(self):
        page = service.glossary("fa", limit=4000, q="دیوانه")
        rows = [r for r in page["rows"] if r["word"] == "دیوانه"]
        self.assertEqual(len(rows), 1)
        self.assertIn("/", rows[0]["pos"])


if __name__ == "__main__":
    unittest.main()
