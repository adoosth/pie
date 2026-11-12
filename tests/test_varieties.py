"""A register is read at its stage, and the page says which register it was.

Wiktionary records some ancestors with the code of a variety ("inherited from
Late Latin", "from New Latin").  The model has one node for Latin, so such a
row named nothing the laws could start from.  ``data/language_varieties.yaml``
says which stage a register is read at; the derivation uses that stage, the
ancestry list keeps printing the register's own name, and the ladder says so
(2026-11-09).
"""
import unittest

from pie import data, service


class VarietyMappingTest(unittest.TestCase):
    def test_a_register_is_read_at_its_stage(self):
        self.assertEqual(data.stage_of("la-lat"), "la")
        self.assertEqual(data.stage_of("la-vul"), "la")
        self.assertEqual(data.stage_of("la-new"), "la")

    def test_a_language_is_not_a_register(self):
        for code in ("la", "fr", "fro", "grc", "ine-pro", ""):
            self.assertEqual(data.stage_of(code), code)

    def test_every_register_names_a_stage_the_model_holds(self):
        languages = data.languages()
        for code, row in data.varieties().items():
            self.assertIn(row["of"], languages, code)
            self.assertNotEqual(row["of"], code, code)
            self.assertTrue(row.get("name"), code)
            self.assertNotIn(code, languages, f"{code} is a register, not a node")

    def test_a_recorded_register_is_a_start_and_a_borrowing_is_not(self):
        chain = data.derivation_chain("it")
        entry = {"word": "abate", "anc": [["la-lat", "abbās", "inherit"]]}
        starts = service.ancestor_starts(entry, chain)
        self.assertIn(("la", "abbās"), starts)
        borrowed = {"word": "abate", "anc": [["la-lat", "abbās", "borrow"]]}
        self.assertEqual([s for s, _f in service.ancestor_starts(borrowed, chain)
                          if s == "la"], [])

    def test_the_ladder_says_which_register_it_was(self):
        d = service.word("it", "zero")["derivation"]
        self.assertEqual(d["start"], "la")
        self.assertEqual(d["start_variety"], "New Latin")
        # A form written under the stage itself carries no register.
        plain = service.word("de", "Wasser")["derivation"]
        self.assertEqual(plain["start_variety"], "")


if __name__ == "__main__":
    unittest.main()
