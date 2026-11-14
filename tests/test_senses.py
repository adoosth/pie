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

from pie import data, senses, service


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


class MeaningBeforeGrammarTest(unittest.TestCase):
    """One word, two headings: the meaning is printed, the grammar after it.

    *aiganaz is a `===Participle===` ("past participle of *aiganą") and an
    `===Adjective===` ("own") on one Wiktionary page, with one etymology — one
    word, which the reader met as two entries in the search box and as a page
    that never said "own" (2026-11-12).
    """

    def test_a_form_of_note_is_not_a_meaning(self):
        self.assertTrue(senses.points_elsewhere("past participle of *aiganą"))
        self.assertTrue(senses.points_elsewhere("Inflection of bēon:"))
        self.assertTrue(senses.points_elsewhere("alternative form of *aiganaz"))
        self.assertFalse(senses.points_elsewhere("own"))

    def test_the_meaning_comes_first(self):
        self.assertEqual(senses.meanings_first(["past participle of *aiganą", "own"]),
                         ["own", "past participle of *aiganą"])
        self.assertEqual(senses.meanings_first(["own"]), ["own"])

    def test_a_group_keeps_both_and_orders_them(self):
        rows = [entry("aiganaz", "verb", "past participle of *aiganą",
                      [("ine-pro", "*h₂eyḱ-", "root")], "Adjectival formation"),
                entry("aiganaz", "adj", "own",
                      [("ine-pro", "*h₂eyḱ-", "root")], "Adjectival formation")]
        groups = senses.groups(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["pos"], ["verb", "adj"])
        self.assertEqual(groups[0]["gloss"], ["own", "past participle of *aiganą"])


class OneWordIsListedOnceTest(unittest.TestCase):
    def test_search_lists_the_word_once(self):
        rows = [r for r in service.search("aiganaz", "gem-pro", limit=10)
                if r["word"] == "aiganaz"]
        self.assertEqual(len(rows), 1, "one word, however many headings the record uses")
        self.assertEqual(rows[0]["pos"], "verb / adj")
        self.assertEqual(rows[0]["gloss"][0], "own")

    def test_the_suggestion_list_does_too(self):
        rows = [r for r in service.suggest("aiganaz", 10, "gem-pro")
                if r["word"] == "aiganaz"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["gloss"], "own")

    def test_the_page_says_what_the_word_means(self):
        page = service.word("gem-pro", "aiganaz")
        self.assertEqual(page["pos"], "verb / adj")
        self.assertEqual(page["gloss"][0], "own")
        self.assertIn("past participle of *aiganą", page["gloss"])

    def test_the_construction_menu_names_the_meaning(self):
        rows = {r["word"]: r["gloss"] for r in service.headwords("gem-pro")}
        self.assertEqual(rows.get("aiganaz"), "own")

    def test_two_etymologies_are_still_two_rows(self):
        rows = [r for r in service.search("wistiz", "gem-pro", limit=10)
                if r["word"] == "wistiz"]
        self.assertEqual(len(rows), 2, "two recorded origins are two words")
        self.assertEqual(sorted(r["sense"] for r in rows), [1, 2])

    def test_a_word_is_still_one_word_after_the_glossary_is_read_again(self):
        # The search table and the grouping index are two caches over the same
        # glossary, and a parse-cache eviction (or an edited word file) can
        # leave one holding rows the other has re-read: equal rows, new
        # objects.  A lookup by identity then found no group — *aiganaz lost
        # "own" and read "past participle of *aiganą", and *wistiz's two
        # origins collapsed into one row.  The first full-suite run after
        # v0.17.13 failed exactly this way.
        service.search("aiganaz", "gem-pro", limit=5)
        service.senses_of("gem-pro", "wistiz")
        service._search_rows.cache_clear()
        data.lexicon.cache_clear()
        rows = [r for r in service.search("aiganaz", "gem-pro", limit=10)
                if r["word"] == "aiganaz"]
        self.assertEqual(rows[0]["pos"], "verb / adj")
        self.assertEqual(rows[0]["gloss"][0], "own")
        homographs = [r for r in service.search("wistiz", "gem-pro", limit=10)
                      if r["word"] == "wistiz"]
        self.assertEqual(len(homographs), 2)


if __name__ == "__main__":
    unittest.main()
