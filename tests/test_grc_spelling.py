"""The Greek writing layer (2026-11-09).

Greek is an alphabet, so the step from the phonemic form to the written word is
the letter table of Smyth, *A Greek Grammar* (1920), §1, plus the four
conventions that are not one-to-one: the breathing (§§9-10), the acute on the
stressed vowel (§149), the final sigma (§3), and the double letters ξ ψ ζ with
γ for a nasal before a velar (§1).  These tests pin each of them with a word
the corpus records, and pin the two things the layer must **not** do: write a
vowel the phonemes do not have, and write θ φ χ from anything but an aspirate.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, spelling  # noqa: E402
from pie.greek import write  # noqa: E402


class TestGreekLetters(unittest.TestCase):
    def test_one_letter_per_phoneme(self):
        self.assertEqual(write("patˈēr"), "πατήρ")
        self.assertEqual(write("mˈētēr"), "μήτηρ")
        self.assertEqual(write("lˈukos"), "λύκος")
        self.assertEqual(write("dˈeka"), "δέκα")
        self.assertEqual(write("kˈorē"), "κόρη")

    def test_a_word_ends_in_final_sigma(self):
        self.assertEqual(write("polˈus"), "πολύς")
        self.assertEqual(write("lˈogos"), "λόγος")
        self.assertIn("ς", write("polˈus"))
        self.assertNotIn("ς", write("polˈusa"))

    def test_ks_ps_and_zd_are_one_sign(self):
        self.assertEqual(write("ksˈenos"), "ξένος")
        self.assertEqual(write("psūkʰˈē"), "ψυχή")
        self.assertEqual(write("ˈozdos"), "ὄζος")

    def test_a_nasal_before_a_velar_is_gamma(self):
        self.assertEqual(write("tunkʰˈanō"), "τυγχάνω")
        self.assertEqual(write("ˈonkos"), "ὄγκος")
        # ... and only before a velar
        self.assertEqual(write("ˈanemos"), "ἄνεμος")


class TestBreathing(unittest.TestCase):
    def test_a_vowel_initial_word_takes_the_smooth_breathing(self):
        self.assertEqual(write("ˈallos"), "ἄλλος")
        self.assertEqual(write("ˈergon"), "ἔργον")
        self.assertEqual(write("ˈonoma"), "ὄνομα")

    def test_a_written_h_is_the_rough_breathing(self):
        self.assertEqual(write("hˈippos"), "ἵππος")
        self.assertEqual(write("hˈagios"), "ἅγιος")
        self.assertEqual(write("heptˈa"), "ἑπτά")

    def test_an_initial_rho_takes_the_rough_breathing(self):
        self.assertEqual(write("hrˈeō"), "ῥέω")
        self.assertEqual(write("rutʰmˈos"), "ῥυθμός")

    def test_a_diphthong_carries_the_breathing_on_its_second_vowel(self):
        # εἰς is epsilon + iota with the smooth breathing (Smyth §9).
        self.assertEqual(write("eis"), "εἰς")
        self.assertEqual(write("hau"), "αὑ")


class TestAcute(unittest.TestCase):
    def test_the_stressed_vowel_takes_the_acute(self):
        self.assertEqual(write("patˈēr"), "πατήρ")
        self.assertEqual(write("pˈente"), "πέντε")

    def test_a_diphthong_takes_the_acute_on_its_second_vowel(self):
        self.assertEqual(write("basilˈeus"), "βασιλεύς")
        self.assertEqual(write("ˈoikos"), "οἴκος")

    def test_no_stress_token_writes_no_accent(self):
        # The laws state the acute only where the ancestor carries one; a
        # circumflex or a grave is a different accent and is never invented.
        self.assertEqual(write("melissa"), "μελισσα")
        self.assertNotEqual(write("melissa"), "μέλισσα")


class TestRefusals(unittest.TestCase):
    """A spelling that cannot be stated as a convention is not written."""

    def test_a_wrong_vowel_does_not_produce_the_word(self):
        self.assertNotEqual(spelling.spell("patˈar", "grc"), "πατήρ")
        self.assertNotEqual(spelling.spell("pˈater", "grc"), "πατήρ")
        self.assertNotEqual(spelling.spell("mˈeatēr", "grc"), "μήτηρ")

    def test_an_aspirate_is_written_from_an_aspirate_only(self):
        self.assertEqual(spelling.spell("tʰˈeros", "grc"), "θέρος")
        self.assertNotEqual(spelling.spell("tˈeros", "grc"), "θέρος")
        self.assertNotEqual(spelling.spell("kˈōra", "grc"), "χώρα")
        self.assertEqual(spelling.spell("kʰˈōra", "grc"), "χώρα")

    def test_notation_the_table_does_not_own_stays_visible(self):
        # A surviving laryngeal, an unresolved glide or an alternative in the
        # record is kept as it stands, so it can never pass as a spelling.
        self.assertIn("H", write("skeH"))
        self.assertIn("y", write("ˈalyos"))
        self.assertIn("~", write("tartyˈos~tritˈos"))


class TestFile(unittest.TestCase):
    def test_the_spelling_file_is_a_valid_rule_set(self):
        ruleset = spelling.ruleset("grc")
        self.assertIsNotNone(ruleset)
        self.assertEqual(spelling.check(ruleset), [])
        self.assertTrue(spelling.applies("grc"))

    def test_every_example_in_the_file_is_a_recorded_word(self):
        words = {e["word"] for e in data.lexicon("grc")}
        for rule in spelling.ruleset("grc").rules:
            for example in rule.examples:
                self.assertIn(example["out"], words, msg=rule.id)

    def test_the_reading_guard_reads_the_greek_digraphs(self):
        # The guard compares segments, not alphabets: ει and ου are one long
        # nucleus, ŋ is /n/ before a velar, ῥ is one r, ζ is /zd/.
        self.assertTrue(spelling.plausible("boukˈolos", "/buː.kó.los/", "grc"))
        self.assertTrue(spelling.plausible("ˈonkos", "/óŋ.kos/", "grc"))
        self.assertTrue(spelling.plausible("hrˈeō", "/r̥é.ɔː/", "grc"))
        self.assertTrue(spelling.plausible("zugˈon", "/zdy.ɡón/", "grc"))
        # ... and the fold is the language's, not a global relaxation
        self.assertFalse(spelling.plausible("boukˈolos", "/buː.kó.los/"))
        self.assertFalse(spelling.plausible("ˈonkos", "/óŋ.kos/"))


class TestCoverageCountsIt(unittest.TestCase):
    def test_a_recorded_word_is_spelled(self):
        entry = next(e for e in data.lexicon("grc") if e["word"] == "πατήρ")
        from pie.rules import derive
        from pie.service import ancestor_starts

        chain = data.derivation_chain("grc")
        for stage, form in ancestor_starts(entry, chain):
            out = derive(form, chain[chain.index(stage):], data.rulesets())
            if out.skipped or not out.steps:
                continue
            if spelling.spell(out.output, "grc") == entry["word"]:
                self.assertTrue(spelling.plausible(out.output, entry.get("ipa") or "", "grc"))
                break
        else:
            self.fail("no ancestor of πατήρ spells it")
