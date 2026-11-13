"""One romanisation alphabet per stage, and no word spelled two ways (2026-11-13).

MPCD writes Middle Persian with ǰ and č; the other sources in the glossary
wrote j and c, and Wiktionary heads a word by its Pahlavi transliteration
(hwʾb) beside its reading (xwāb).  Two spellings of one word were two pages —
`pal/jaw` and `pal/ǰaw` were both "barley" — so a stage now states its
standard alphabet in `data/notation/` and every headword is read in it.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, notation, service  # noqa: E402


class TestStandardAlphabet(unittest.TestCase):
    def test_a_variant_folds_to_its_standard_letter(self):
        self.assertEqual(notation.canonical("pal", "jaw"), "ǰaw")
        self.assertEqual(notation.canonical("pal", "ganj"), "ganǰ")
        self.assertEqual(notation.canonical("pal", "wacast"), "wačast")

    def test_a_standard_word_is_left_alone(self):
        for word in ("garm", "xwāb", "ǰaw", "ahlomōγ", "sižd"):
            self.assertEqual(notation.canonical("pal", word), word)

    def test_a_stage_without_a_table_is_not_touched(self):
        self.assertEqual(notation.canonical("en", "night"), "night")
        self.assertEqual(notation.canonical("xx-none", "j"), "j")

    def test_every_middle_persian_headword_is_spelled_in_the_standard_set(self):
        words = [row.get("word") or "" for row in data.lexicon("pal")]
        self.assertEqual(notation.variants("pal", words), [])
        # One headword is still outside it: MPCD's stray lemma "q" (gloss "§"),
        # which is not a word and is left for the data pass rather than hidden
        # by a fold.
        self.assertEqual([word for word, _ in notation.offenders("pal", words)], ["q"])


class TestDuplicateEntriesAreOne(unittest.TestCase):
    def test_jaw_and_jaw_with_a_caron_are_one_word(self):
        row = service._lemma_entry("pal", "jaw")
        self.assertIsNotNone(row)
        self.assertEqual(row["word"], "ǰaw")
        self.assertEqual(row["gloss"], ["barley"])
        self.assertEqual(row.get("occurrences"), 11)
        self.assertIn("mpcd", row.get("sources") or [])
        self.assertIn("wiktionary", row.get("sources") or [])

    def test_a_transliteration_takes_its_own_reading(self):
        row = service._lemma_entry("pal", "hwʾb")
        self.assertIsNotNone(row)
        self.assertEqual(row["word"], "xwāb")
        self.assertEqual(row["translit_quoted"], "hwʾb")

    def test_the_word_page_opens_the_same_entry_for_both_spellings(self):
        first = service.word("pal", "jaw")
        second = service.word("pal", "ǰaw")
        self.assertEqual(first["word"], second["word"])
        self.assertEqual(first["word"], "ǰaw")

    def test_the_merged_entry_keeps_its_etymology(self):
        row = service._lemma_entry("pal", "ǰaw")
        self.assertEqual((row.get("anc") or [[]])[0][0], "peo")


if __name__ == "__main__":
    unittest.main()
