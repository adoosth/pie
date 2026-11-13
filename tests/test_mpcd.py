"""The Middle Persian Corpus and Dictionary as a source of words.

MPCD is a corpus with a dictionary on top of it, so an entry it gives can say
how often the texts write the word.  These tests hold the three things that
makes possible: the source shows up as the word's own page (the book icon), the
count reaches the reader, and a variant MPCD analyses (garmtar) is a
construction of a registered ending rather than a word of its own (admin,
2026-11-13).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import data, service


def entry(**fields) -> dict:
    row = {"word": "garm", "lang": "pal", "pos": "adjective", "gloss": ["hot", "warm"]}
    row.update(fields)
    return row


class TestSources(unittest.TestCase):
    def test_the_dictionary_is_a_book_that_opens_the_word(self):
        row = entry(source="mpcd", sources=["mpcd"],
                    url="https://www.mpcorpus.org/dict/d9dbb2df-1839-4e02-9f41-ac56e19c9c97/",
                    occurrences=102)
        pages = service._entry_pages(row)
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["kind"], "dictionary")
        self.assertTrue(pages[0]["url"].rstrip("/").endswith("d9dbb2df-1839-4e02-9f41-ac56e19c9c97"))
        self.assertEqual(pages[0]["note"], "102 occurrences in the corpus")

    def test_the_count_is_the_attestation(self):
        payload = service.attestation_of(entry(source="mpcd", occurrences=102), "pal")
        self.assertEqual(payload["status"], "transliterated")
        self.assertIn("The corpus writes it 102 times.", payload["reason"])

    def test_one_occurrence_is_one_time(self):
        payload = service.attestation_of(entry(word="garmtom", occurrences=1), "pal")
        self.assertIn("The corpus writes it 1 time.", payload["reason"])

    def test_an_entry_the_dictionary_does_not_count_says_nothing_about_it(self):
        payload = service.attestation_of(entry(source="mpcd"), "pal")
        self.assertNotIn("corpus writes it", payload["reason"])


class TestVariants(unittest.TestCase):
    def test_the_comparative_is_a_registered_ending(self):
        table = data._load_yaml(data.DATA / "morphology" / "pal.yaml")
        forms = {row["form"] for row in table.get("suffixes") or []}
        self.assertIn("-tar", forms)
        self.assertIn("-tom", forms)

    def test_a_variant_is_the_record_s_construction(self):
        build = service._own_construction(entry(
            word="garmtar", built_as=[{"lang": "pal", "kind": "derivation",
                                       "of": "garmtar",
                                       "pieces": [["garm", "hot"], ["-tar", "comparative"]]}]),
            data.derivation_chain("pal"))
        self.assertTrue(build)
        self.assertEqual([p[0] for p in build["pieces"]], ["garm", "-tar"])

    def test_the_construction_spells_the_word(self):
        row = entry(word="garmtom", built_as=[{"lang": "pal", "kind": "derivation",
                                               "of": "garmtom",
                                               "pieces": [["garm", "hot"], ["-tom", "superlative"]]}])
        path = service.construction_path(row, "pal")
        self.assertTrue(path["exact"], path.get("form"))
        self.assertTrue(path["explained"], path.get("unexplained"))


if __name__ == "__main__":
    unittest.main()
