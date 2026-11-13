"""The Middle Persian reading layer: signs, conventions and refusals.

The table in ``data/script/pal.yaml`` says what a Pahlavi or Manichaean sign
writes, and ``data/readings_pal.json`` says how the record reads a spelling.
Both are claims about the writing system, so both are testable: a sign the
corpus never uses does not belong in the table, a convention has to be
exercised by a recorded word, and a spelling that writes a vowel must refuse a
reading that has none there (2026-11-09).
"""
import json
import unittest

from pie import data, notation, script
from pie.service import normalise_etymon


def _pal_forms() -> set[str]:
    """Every Middle Persian form the record writes: headwords and ancestors."""
    forms = {e["word"] for e in data.lexicon("pal")}
    for lang, _size in data.available_lexicons():
        for entry in data.lexicon(lang):
            for stage, word, _rel in entry.get("anc") or []:
                if stage == "pal":
                    forms.add(normalise_etymon(word))
    return forms


class TestSigns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forms = _pal_forms()
        cls.table = script.table("pal")

    def test_the_table_is_not_empty(self):
        self.assertGreater(len(self.table), 40)

    def test_every_sign_is_exercised_by_a_recorded_word(self):
        # The table's own letters are written in the stage's notation too, so a
        # sign the record spells č is not missing because the table says c.
        unused = [sign for sign in self.table
                  if not any(notation.canonical("pal", sign) in form for form in self.forms)]
        self.assertEqual(unused, [], f"signs no recorded word writes: {unused}")

    def test_every_convention_is_exercised(self):
        rules = script.conventions("pal")
        self.assertTrue(rules)
        ids = " ".join(row["id"] for row in rules)
        self.assertIn("short_vowels_unwritten", ids)
        self.assertIn("final_silent_letter", ids)

    def test_the_merged_letters_keep_their_polyphony(self):
        merged = self.table["𐭥"]
        self.assertEqual(merged["sounds"], ["w", "o", "u", "r", "ʿ"])
        self.assertEqual(self.table["𐭬"]["sounds"], ["m", "q"])
        # kaph, pe and taw write the voiced stop as well
        self.assertIn("g", self.table["𐭪"]["sounds"])
        self.assertIn("b", self.table["𐭯"]["sounds"])
        self.assertIn("d", self.table["𐭲"]["sounds"])


class TestReading(unittest.TestCase):
    def test_the_table_reads_a_recorded_spelling(self):
        self.assertEqual(script.read("pal", "sng"), "sang")
        self.assertEqual(script.read("pal", "𐭦𐭭𐭤"), "ēn")
        self.assertEqual(script.read("pal", "𐫅𐫏𐫇"), "dēw")

    def test_every_table_reading_is_consistent_with_its_spelling(self):
        """A reading has to be spellable by the signs, or it is not one."""
        rows = script.readings("pal")
        self.assertGreater(len(rows), 100)
        checked = 0
        for form, row in rows.items():
            if not any(0x10A00 <= ord(c) <= 0x10BFF for c in form):
                continue
            if row.get("tier") == "script-quoted":
                # An Arameogram is read as a whole word, not by its signs; its
                # reading is a lexical fact and is tested by the page's own
                # record, not by the sound table (MacKenzie 1971).
                self.assertTrue(script.read("pal", form))
                continue
            fit = script.match("pal", row["reading"], form)
            self.assertIsNotNone(fit, form)
            self.assertTrue(fit["ok"], f"{form} does not spell {row['reading']}")
            checked += 1
        self.assertGreater(checked, 1)

    def test_unwritten_short_vowels_are_free(self):
        self.assertTrue(script.match("pal", "sang", "𐭮𐭭𐭢")["ok"])
        self.assertTrue(script.match("pal", "sing", "𐭮𐭭𐭢")["ok"])

    def test_a_written_vowel_cannot_be_dropped(self):
        # s-ʾ-n-g writes a vowel; a reading with no vowel there is no reading
        # of those signs, however convenient it would be.
        self.assertFalse(script.match("pal", "sng", "𐭮𐭠𐭭𐭢")["ok"])
        self.assertTrue(script.match("pal", "sang", "𐭮𐭠𐭭𐭢")["ok"])

    def test_a_wrong_vowel_is_refused(self):
        self.assertFalse(script.match("pal", "daw", "𐫅𐫏𐫇")["ok"])
        self.assertTrue(script.match("pal", "dēw", "𐫅𐫏𐫇")["ok"])

    def test_a_spelling_with_no_reading_gets_none(self):
        self.assertEqual(script.read("pal", "sng2"), "")


if __name__ == "__main__":
    unittest.main()
