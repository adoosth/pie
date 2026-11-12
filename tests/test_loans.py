"""Which words left the Indo-European family, and which only changed hands.

The coverage categories the project fixed on 2026-11-09 need a real origin test,
not the old "an ancestry row names a language the model does not hold" proxy:
Latin into English is a loan too, and Arabic into Persian is the one that
leaves the family.  ``data/non_ie_sources.yaml`` is the register of outside
donors, and ``pie.loans`` reads the leading ancestry row of an entry.
"""
from __future__ import annotations

import unittest

from pie import data, loans


def entry(lang: str, word: str) -> dict:
    for row in data.lexicon(lang):
        if row["word"] == word:
            return row
    raise AssertionError(f"{lang} glossary has no {word!r}")


class ClassificationTest(unittest.TestCase):
    def test_arabic_into_persian_is_outside_the_family(self):
        word = entry("fa", "امام")
        self.assertEqual(loans.classify(word, "fa"), "non_ie")
        self.assertEqual(loans.source_language(word), "ar")
        self.assertEqual(loans.source_family(word), "Semitic")

    def test_french_into_english_is_a_loan_inside_the_family(self):
        word = entry("en", "antonym")
        self.assertEqual(loans.classify(word, "en"), "ie_loan")
        self.assertIsNone(loans.source_family(word))

    def test_latin_into_english_is_a_loan_inside_the_family(self):
        self.assertEqual(loans.classify(entry("en", "thesaurus"), "en"), "ie_loan")

    def test_an_inherited_persian_word_is_not_a_loan(self):
        word = entry("fa", "هل")
        self.assertIsNone(loans.classify(word, "fa"))
        self.assertEqual(loans.rows(word), [("pal", "inherit")])

    def test_a_dictionary_mark_stands_where_no_chain_does(self):
        """Dehkhoda's own (ع اِ) / (فرانسوی) is a record, not a guess.

        Only an entry with no ancestry of its own is read this way, so a mark
        can never overrule a stated pathway, and a mark naming the word's own
        ancestor (Middle Persian on an inherited word) is not a loan at all
        (2026-11-10).
        """
        arabic = {"word": "x", "lang": "fa", "borrowed_from": "ar"}
        french = {"word": "y", "lang": "fa", "borrowed_from": "fr"}
        inherited = {"word": "ز", "lang": "fa", "borrowed_from": "pal"}
        itself = {"word": "w", "lang": "fa", "borrowed_from": "fa"}
        unknown = {"word": "v", "lang": "fa", "borrowed_from": "qq"}
        self.assertEqual(loans.classify(arabic, "fa"), "non_ie")
        self.assertEqual(loans.source_language(arabic), "ar")
        self.assertEqual(loans.classify(french, "fa"), "ie_loan")
        self.assertEqual(loans.mark_donor(french), "fr")
        self.assertIsNone(loans.classify(inherited, "fa"))
        self.assertIsNone(loans.classify(itself, "fa"))
        self.assertIsNone(loans.classify(unknown, "fa"))

    def test_a_recorded_pathway_outranks_a_mark(self):
        word = dict(entry("fa", "هل"))
        word["borrowed_from"] = "ar"
        self.assertIsNone(loans.classify(word, "fa"))

    def test_middle_persian_from_arabic_still_lands_outside(self):
        word = entry("fa", "جوراب")
        self.assertEqual(loans.rows(word),
                         [("pal", "derived"), ("ar", "borrow")])
        self.assertEqual(loans.classify(word, "fa"), "non_ie")
        self.assertEqual(loans.source_language(word), "ar")

    def test_a_translingual_name_has_no_donor_family(self):
        word = entry("en", "cactus")
        self.assertEqual(loans.rows(word)[0][0], "mul-tax")
        self.assertIsNone(loans.classify(word, "en"))

    def test_an_influence_row_does_not_make_an_outside_donor(self):
        word = entry("fa", "فارسی")
        self.assertIsNone(loans.classify(word, "fa"))
        self.assertIsNone(loans.source_language(word))

    def test_an_entry_without_ancestry_is_not_classified(self):
        self.assertIsNone(loans.classify({"word": "x", "lang": "en"}, "en"))


class RegisterTest(unittest.TestCase):
    """The register itself may not name an Indo-European language."""

    REQUIRED = {"ar", "he", "arc", "syc", "akk", "egy", "tr", "ota", "sux",
                "zh", "ja", "ko", "hu", "fi", "et", "ber", "ka", "eu",
                "ms", "id", "sw", "nah", "qu"}

    @classmethod
    def setUpClass(cls):
        cls.langs = data.languages()
        cls.ie_codes = set(cls.langs)
        cls.ie_families = {row.get("branch", "").split(" (")[0].strip()
                           for row in cls.langs.values() if row.get("branch")}

    def test_no_registered_code_is_a_model_node(self):
        for code in loans.sources():
            self.assertNotIn(code, self.ie_codes,
                             f"{code} is a node of the Indo-European model")

    def test_no_registered_family_is_an_indo_european_branch(self):
        for code, row in loans.sources().items():
            family = row["family"].split(" (")[0].strip()
            self.assertNotIn(family, self.ie_families,
                             f"{code} names the Indo-European branch {family}")

    def test_the_families_named_are_absent(self):
        for code in ("fa", "la", "grc", "sa", "peo", "ave", "pal", "hy", "sq"):
            self.assertNotIn(code, loans.sources(),
                             f"{code} is Indo-European and may not be a donor")

    def test_every_required_donor_is_registered(self):
        self.assertLessEqual(self.REQUIRED, set(loans.sources()))

    def test_each_entry_carries_a_name_a_family_a_note_and_examples(self):
        for code, row in loans.sources().items():
            for field in ("name", "family", "note", "examples"):
                self.assertIn(field, row, f"{code} has no {field}")
            least = 2 if code in self.REQUIRED else 1
            self.assertGreaterEqual(len(row["examples"]), least, code)
            for example in row["examples"]:
                self.assertIn(":", example["target"], code)


if __name__ == "__main__":
    unittest.main()
