"""Writing a phonemic form in a language's own script (2026-11-09).

Sanskrit is written in Devanagari, an abugida: a consonant sign carries an
inherent a, a following vowel is a dependent sign, and a following consonant
takes the vowel away with the virama.  That makes the whole alphabet one
writing convention rather than a list of letter substitutions, and these tests
pin the four things a writer must get right besides the letter table: the
inherent vowel, the matras, the virama, and the visarga/anusvāra.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import spelling, writing  # noqa: E402


class TestDevanagari(unittest.TestCase):
    def test_a_consonant_carries_its_inherent_a(self):
        self.assertEqual(writing.devanagari("ka"), "क")
        self.assertEqual(writing.devanagari("paśu"), "पशु")

    def test_a_vowel_after_a_consonant_is_a_dependent_sign(self):
        self.assertEqual(writing.devanagari("ki"), "कि")
        self.assertEqual(writing.devanagari("kā"), "का")
        self.assertEqual(writing.devanagari("deva"), "देव")
        self.assertEqual(writing.devanagari("kanyā"), "कन्या")

    def test_two_consonants_take_the_virama(self):
        self.assertEqual(writing.devanagari("tat"), "तत्")
        self.assertEqual(writing.devanagari("śatam"), "शतम्")
        self.assertEqual(writing.devanagari("buddha"), "बुद्ध")

    def test_a_word_initial_vowel_has_its_own_letter(self):
        self.assertEqual(writing.devanagari("aśva"), "अश्व")
        self.assertEqual(writing.devanagari("r̥tam"), "ऋतम्")

    def test_visarga_and_anusvara_close_the_syllable(self):
        self.assertEqual(writing.devanagari("devaḥ"), "देवः")
        self.assertEqual(writing.devanagari("saṃskr̥tam"), "संस्कृतम्")

    def test_stress_is_not_written(self):
        self.assertEqual(writing.devanagari("dˈevas"), writing.devanagari("devas"))

    def test_notation_the_table_does_not_own_is_kept_visible(self):
        # A laryngeal that survived, or an unresolved affricate, must not be
        # guessed at: the word would look like a match.
        self.assertIn("H", writing.devanagari("bʰaHgas"))
        self.assertFalse(writing.readable("bʰaHgas"))
        self.assertTrue(writing.readable("bhāgas"))


class TestSanskritSpelling(unittest.TestCase):
    def test_the_spelling_file_writes_the_sanskrit_word(self):
        self.assertEqual(spelling.spell("dˈevas", "sa"), "देवस्")
        self.assertEqual(spelling.spell("śatˈam", "sa"), "शतम्")
        self.assertEqual(spelling.spell("buddʰˈaḥ", "sa"), "बुद्धः")

    def test_the_spelling_file_cites_and_uses_the_orthographic_tier(self):
        rs = spelling.ruleset("sa")
        self.assertIsNotNone(rs)
        for rule in rs.rules:
            self.assertEqual(rule.tier, "orthographic")
            self.assertTrue(rule.references)

    def test_a_spelling_never_claims_to_be_a_sound_law(self):
        # The layer's output is writing, so it is compared in its own column.
        self.assertNotEqual(spelling.spell("dˈevas", "sa"), "dˈevas")


class TestIpaNotationFold(unittest.TestCase):
    def test_aspiration_is_one_segment_in_two_notations(self):
        self.assertTrue(spelling.plausible("gʰa", "/ɡʱɐ/"))
        self.assertTrue(spelling.plausible("bʰˈavati", "/bʱɐ́.ʋɐ.ti/"))

    def test_sanskritist_letters_and_ipa_letters_are_the_same_segment(self):
        self.assertTrue(spelling.plausible("tuṣ", "/tuʂ/"))
        self.assertTrue(spelling.plausible("pˈaśu", "/pɐ.ɕú/"))
        self.assertTrue(spelling.plausible("ca", "/t͡ɕɐ/"))

    def test_the_fold_still_rejects_a_wrong_skeleton(self):
        self.assertFalse(spelling.plausible("hant", "/kant/"))
        self.assertFalse(spelling.plausible("buddʰˈaḥ", "/pu.tɐ/"))


class TestCitationForm(unittest.TestCase):
    """A dictionary may cite the stem while the laws end in another form."""

    def test_sanskrit_declares_its_nominative_endings(self):
        from pie import citation

        self.assertIn("aḥ", citation.endings("sa"))
        self.assertIn("ḥ", citation.endings("sa"))

    def test_a_language_without_a_file_strips_nothing(self):
        from pie import citation

        self.assertEqual(citation.endings("en"), ())


class TestAffricateNotation(unittest.TestCase):
    def test_a_dictionary_may_write_an_affricate_without_the_tie_bar(self):
        self.assertTrue(spelling.plausible("č", "/tʃ/"))
        self.assertTrue(spelling.plausible("ǰ", "/dʒ/"))
        self.assertTrue(spelling.plausible("čašm", "/ˈt͡ʃaʃm/"))
