"""The meanings tabs: one source per tab, and never a claim about a form."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import meanings  # noqa: E402


PAGE = """<html><body><article><header><h1>آن</h1></header>
<section><h2>لغت‌نامه دهخدا</h2><div role="definition" class="V-IIZ">
<span class="hl">آن .</span> [ ن ِ ] (ضمیر ملکی ) مال ِ. متعلق به .<br></div></section>
</article><aside><section><h2>معانی دیگر آن</h2><ul>
<li><a href="/dehkhoda/%D8%A2%D9%86-2">آن (2)</a></li>
<li><a href="/moein/%D8%A2%D9%86">معین</a></li></ul></section></aside></body></html>"""


class Parse(unittest.TestCase):
    def test_one_page_yields_head_and_definition(self):
        page = meanings._Entry()
        page.feed(PAGE)
        self.assertEqual(meanings._tidy(page.head), "آن")
        self.assertEqual(len(page.blocks), 1)
        self.assertIn("متعلق به", page.blocks[0])

    def test_the_other_entries_are_seen_but_other_dictionaries_are_not(self):
        page = meanings._Entry()
        page.feed(PAGE)
        self.assertEqual(page.other, ["/dehkhoda/%D8%A2%D9%86-2"])

    def test_unknown_or_empty_word_asks_nothing(self):
        self.assertIsNone(meanings.dehkhoda(""))
        self.assertIsNone(meanings.dehkhoda("   "))


class Sources(unittest.TestCase):
    def test_wiktionary_is_always_the_first_tab(self):
        row = meanings.sources("en", "night", ["The period of darkness."])
        self.assertEqual([s["id"] for s in row["sources"]], ["wiktionary"])
        self.assertIn("darkness", row["sources"][0]["entries"][0]["text"])

    def test_a_persian_word_gets_dehkhoda_beside_it(self):
        saved = meanings.dehkhoda
        meanings.dehkhoda = lambda word, **kw: {
            "source": "dehkhoda", "name": "لغت‌نامهٔ دهخدا",
            "url": "https://vajehyab.com/dehkhoda/x",
            "entries": [{"head": word, "url": "https://vajehyab.com/dehkhoda/x",
                         "text": "معنی"}]}
        try:
            row = meanings.sources("fa", "آن", ["that"])
        finally:
            meanings.dehkhoda = saved
        self.assertEqual([s["id"] for s in row["sources"]], ["wiktionary", "dehkhoda"])
        self.assertEqual(row["sources"][1]["entries"][0]["text"], "معنی")

    def test_an_unreachable_site_still_leaves_a_tab_and_a_note(self):
        saved = meanings.dehkhoda
        meanings.dehkhoda = lambda word, **kw: None
        try:
            row = meanings.sources("fa", "آن", ["that"])
        finally:
            meanings.dehkhoda = saved
        deh = row["sources"][1]
        self.assertEqual(deh["id"], "dehkhoda")
        self.assertEqual(deh["entries"], [])
        self.assertIn("did not answer", deh["note"])

    def test_a_word_without_a_gloss_says_so(self):
        row = meanings.sources("en", "x", [])
        self.assertIn("No gloss", row["sources"][0]["note"])


if __name__ == "__main__":
    unittest.main()
