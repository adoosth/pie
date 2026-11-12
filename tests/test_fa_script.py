"""The Persian writing system: signs, conventions and what a spelling can say.

``data/script/fa.yaml`` is a claim about the Perso-Arabic abjad, so it is
tested like the Middle Persian table: every sign is one a recorded Persian word
writes, the conventions are the ones the file declares, and the matcher accepts
a reading only when the signs spell its letters in order — an unwritten short
vowel costs no sign, a written vowel is never dropped, and a consonant the
spelling lacks is never forgiven (2026-11-09).
"""
import unittest

from pie import data, script
from pie.service import normalise_etymon


def _fa_forms() -> set[str]:
    """Every Persian form the record writes: headwords and ancestors."""
    forms = {e["word"] for e in data.lexicon("fa")}
    for lang, _size in data.available_lexicons():
        for entry in data.lexicon(lang):
            for stage, word, _rel in entry.get("anc") or []:
                if stage == "fa":
                    forms.add(normalise_etymon(word))
    return forms


class TestSigns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forms = _fa_forms()
        cls.table = script.table("fa")

    def test_the_table_is_not_empty(self):
        self.assertGreater(len(self.table), 30)

    def test_every_sign_is_exercised_by_a_recorded_word(self):
        unused = [sign for sign in self.table if not any(sign in form for form in self.forms)]
        self.assertEqual(unused, [], f"signs no recorded word writes: {unused}")

    def test_every_convention_is_declared(self):
        ids = " ".join(row["id"] for row in script.conventions("fa"))
        for wanted in ("short_vowels_unwritten", "initial_vowel_seat",
                       "final_short_vowel_written", "shadda_is_a_mark",
                       "historic_waw"):
            self.assertIn(wanted, ids)

    def test_the_letters_keep_their_double_values(self):
        self.assertIn("v", self.table["و"]["sounds"])
        self.assertIn("u", self.table["و"]["sounds"])
        self.assertIn("j", self.table["ی"]["sounds"])
        self.assertIn("i", self.table["ی"]["sounds"])
        self.assertIn("h", self.table["ه"]["sounds"])
        self.assertIn("e", self.table["ه"]["sounds"])
        # word-initial alef is a seat for any vowel
        for vowel in "aeiou":
            self.assertIn(vowel, self.table["ا"]["sounds"])


class TestReading(unittest.TestCase):
    def test_a_written_consonant_is_read(self):
        self.assertTrue(script.match("fa", "pidar", "پدر")["ok"])
        self.assertTrue(script.match("fa", "kamar", "کمر")["ok"])
        self.assertTrue(script.match("fa", "mard", "مرد")["ok"])

    def test_an_unwritten_short_vowel_costs_no_sign(self):
        # pidar, kamar and gol write no short vowel between the consonants.
        self.assertTrue(script.match("fa", "gul", "گل")["ok"])
        self.assertTrue(script.match("fa", "rang", "رنگ")["ok"])

    def test_a_written_vowel_is_never_silently_absent(self):
        self.assertTrue(script.match("fa", "nām", "نام")["ok"])
        self.assertTrue(script.match("fa", "xāb", "خاب")["ok"])
        # خواب writes a w the reading /xab/ has no segment for: a written
        # letter cannot be left unaccounted for.
        self.assertFalse(script.match("fa", "xab", "خواب")["ok"])
        self.assertTrue(script.match("fa", "xwāb", "خواب")["ok"])

    def test_length_is_folded_so_nam_and_nam_are_one_reading(self):
        # The alignment folds ā to a (length is writing, not a letter), so the
        # letters نام cannot tell nām from nam; that limit is the table's
        # documented behaviour, not a claim that the vowels are the same.
        self.assertTrue(script.match("fa", "nam", "نام")["ok"])
        self.assertTrue(script.match("fa", "nām", "نام")["ok"])

    def test_a_consonant_the_spelling_lacks_is_not_forgiven(self):
        self.assertTrue(script.match("fa", "sar", "سر")["ok"])
        self.assertFalse(script.match("fa", "sard", "سر")["ok"])

    def test_the_initial_vowel_seat(self):
        self.assertTrue(script.match("fa", "abr", "ابر")["ok"])
        self.assertTrue(script.match("fa", "esm", "اسم")["ok"])
        self.assertTrue(script.match("fa", "omīd", "امید")["ok"])
        self.assertTrue(script.match("fa", "āsmān", "آسمان")["ok"])

    def test_the_word_final_he(self):
        self.assertTrue(script.match("fa", "xāne", "خانه")["ok"])
        self.assertTrue(script.match("fa", "gurbe", "گربه")["ok"])

    def test_a_verb_written_with_a_zwnj_is_still_read(self):
        # A form with a non-letter a scribe writes between words is skipped.
        self.assertTrue(script.match("fa", "miraftam", "می‌رفتم")["ok"])


if __name__ == "__main__":
    unittest.main()
