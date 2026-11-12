"""The Persian Wiktionary's pages: what a page says, and where it is said.

The glossary's Persian words come from Dehkhoda, which has no page on the English
Wiktionary. A pass over fa.wiktionary.org records which words do have a page and,
where the page prints an etymology, quotes it. These tests hold the reading of a
page (its section, its etymology, its plain text) and the rule that the quote
never becomes this model's own etymology.
"""

from __future__ import annotations

import sys
import unittest
from urllib.parse import quote
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import service, wiktionary

PAGE = """==فارسی==
[[پرونده:Water.jpg|بندانگشتی]]
===آوایش===
* /آب/
===ریشه لغت===
از [[پارسی میانه]] [[آپ|آپ]]، از [[نیا-هندواروپایی]] *h₂ep-.
====منابع====
فرهنگ معین
[[رده:آب]]
===اسم===
# مایع
"""


class TestReading(unittest.TestCase):
    def test_the_persian_section_is_found(self):
        body, named = wiktionary.language_section(PAGE, "فارسی")
        self.assertTrue(named)
        self.assertIn("ریشه لغت", body)

    def test_the_etymology_is_its_own_section(self):
        heading, text = wiktionary.etymology(PAGE)
        self.assertEqual(heading, "ریشه لغت")
        self.assertEqual(text, "از پارسی میانه آپ، از نیا-هندواروپایی *h₂ep-.")

    def test_references_under_the_etymology_are_not_part_of_it(self):
        self.assertNotIn("فرهنگ معین", wiktionary.etymology(PAGE)[1])

    def test_a_page_without_an_etymology_says_so(self):
        self.assertEqual(wiktionary.etymology("==فارسی==\n===اسم===\n# مایع\n"),
                         ("", ""))

    def test_links_keep_their_words_and_lose_their_markup(self):
        self.assertEqual(wiktionary.plain("''از'' [[پارسی]] [[آپ|آپ]]"), "از پارسی آپ")

    def test_a_category_link_leaves_nothing_behind(self):
        self.assertEqual(wiktionary.plain("از گیلکی [[رده:اسم‌های گیلکی]]"), "از گیلکی")

    def test_a_template_is_not_text(self):
        self.assertEqual(wiktionary.plain("*{{فارسی}} از عربی"), "از عربی")


class TestThePageAWaCWordOpens(unittest.TestCase):
    def test_a_word_with_a_page_carries_it_as_a_source(self):
        page = service.word("fa", "آب")
        ids = [row["id"] for row in page["sources"]]
        self.assertIn("fa-wiktionary", ids)
        row = [r for r in page["sources"] if r["id"] == "fa-wiktionary"][0]
        self.assertTrue(row["entry"].startswith("https://fa.wiktionary.org/wiki/"))

    def test_a_word_the_ledger_has_no_page_for_stays_silent(self):
        page = service.word("fa", "آشمیدن")
        self.assertIsNone(page.get("wiktionary"))
        self.assertNotIn("fa-wiktionary", [r["id"] for r in page["sources"]])

    def test_the_quote_is_kept_apart_from_the_models_etymology(self):
        page = service.word("fa", "کتاب")
        self.assertTrue(page.get("wiktionary", {}).get("found"))
        self.assertNotIn("schreiben", page.get("etymology") or "")


class TestTheQuotationMark(unittest.TestCase):
    """Every mark opens the page it is drawn for, and none opens a front page.

    A record has one icon per *recorded* page (admin, 2026-11-12): the W is the
    word's Wiktionary article, the book is its dictionary entry.  A word whose
    page was never recorded has no icon at all, never a mark that goes nowhere.
    """

    def test_a_persian_words_pages_are_its_own_pages(self):
        for word in ("آب", "کتاب", "اتم"):
            page = service.word("fa", word)
            self.assertTrue(page["pages"], f"{word}: no recorded page")
            for row in page["pages"]:
                self.assertNotEqual(row["url"].rstrip("/"), "https://vajehyab.com/dehkhoda",
                                    f"{word}: the book opens the site, not the word")
                if row["kind"] == "dictionary":
                    self.assertIn(quote(word, safe=""), row["url"])

    def test_a_dehkhoda_entry_is_its_own_page_and_not_a_wiktionary_one(self):
        # The entry's own `url` is its vajehyab page, so the book opens the word
        # itself; only a Wiktionary address is painted with the W (admin,
        # 2026-11-12).
        page = service.word("fa", "کتاب")
        row = [r for r in page["sources"] if r["id"] == "dehkhoda"][0]
        self.assertTrue(row["entry"].startswith("https://vajehyab.com/dehkhoda/"))
        self.assertFalse(service._is_wiktionary_url(row["entry"]))
        book = [p for p in page["pages"] if p["kind"] == "dictionary"][0]
        self.assertIn("/dehkhoda/", book["url"])

    def test_a_word_with_a_wiktionary_article_gets_the_w(self):
        page = service.word("fa", "کبود")
        wikt = [p for p in page["pages"] if p["kind"] == "wiktionary"]
        self.assertTrue(wikt, "کبود has a Wiktionary article")
        self.assertTrue(wikt[0]["url"].endswith("%DA%A9%D8%A8%D9%88%D8%AF"))

    def test_a_form_whose_page_is_not_recorded_has_no_icon(self):
        # The Middle Persian kpwt' is named in the Persian etymology; the
        # glossary records no page of it, so its corner stays bare.
        page = service.word("fa", "کبود")
        rung = [r for r in page["path"] if r["stage"] == "pal"] if page.get("path") else []
        for row in rung:
            self.assertFalse((row.get("recorded") or {}).get("pages"))

    def test_an_english_word_still_points_at_its_own_page(self):
        page = service.word("en", "foot")
        rows = [r for r in page["sources"] if r.get("entry")]
        self.assertTrue(rows)
        self.assertTrue(all(wiktionary_url(r["entry"]) for r in rows))

    def test_a_reconstruction_is_titled_without_its_asterisk(self):
        # Wiktionary's namespace already says "reconstruction"; a link that
        # keeps the asterisk opens nothing (2026-11-12).
        self.assertEqual(
            service._wiktionary_title({"lang": "gem-pro", "word": "*nahts"}),
            "Reconstruction:Proto-Germanic/nahts")
        self.assertEqual(service._wiktionary_title({"lang": "en", "word": "night"}),
                         "night")

    def test_the_rule_reads_hosts_not_substrings(self):
        self.assertTrue(service._is_wiktionary_url("https://fa.wiktionary.org/wiki/x"))
        self.assertTrue(service._is_wiktionary_url("https://en.wiktionary.org/wiki/x"))
        self.assertFalse(service._is_wiktionary_url("https://vajehyab.com/dehkhoda/x"))
        self.assertFalse(service._is_wiktionary_url("https://notwiktionary.org/x"))


def wiktionary_url(url: str) -> bool:
    return service._is_wiktionary_url(url)


class TestTheLedger(unittest.TestCase):
    """Every word asked about is answered once, and the answer is complete."""

    def test_each_word_appears_once_and_the_row_says_what_was_found(self):
        rows = list(wiktionary.ledger().values())
        self.assertGreater(len(rows), 200, "the pass must cover at least 200 words")
        keys = [(r["lang"], r["word"]) for r in rows]
        self.assertEqual(len(keys), len(set(keys)), "a word is recorded twice")
        for row in rows:
            self.assertIn(row["status"], ("found", "missing"))
            self.assertTrue(row.get("checked"))
            if row["status"] == "found":
                self.assertTrue(row["url"].startswith("https://fa.wiktionary.org/wiki/"))
                self.assertIsNotNone(row.get("revid"))
            else:
                self.assertNotIn("url", row)

    def test_a_quote_is_never_the_models_own_etymology(self):
        for row in wiktionary.ledger().values():
            if row.get("etym"):
                self.assertEqual(row["status"], "found")


if __name__ == "__main__":
    unittest.main()
