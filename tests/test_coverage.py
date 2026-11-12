"""How the coverage counter decides that a form is the recorded word (2026-11-09)."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("coverage_tool", ROOT / "tools" / "coverage.py")
coverage_tool = importlib.util.module_from_spec(spec)
sys.modules["coverage_tool"] = coverage_tool
spec.loader.exec_module(coverage_tool)

from pie import data, service  # noqa: E402


class TestExactKind(unittest.TestCase):
    def test_the_same_string_is_strict(self):
        self.assertEqual(coverage_tool.exact_kind("wˈarkah", "wˈarkah"), "strict")

    def test_the_dictionary_acute_and_the_engine_token_are_one_form(self):
        # The dictionary prints the stress on the vowel; the engine writes its
        # own token before the syllable.  The word page has always called this
        # a match, and the coverage counter now agrees.
        self.assertEqual(coverage_tool.exact_kind("waydˈayati", "waydáyati"), "notation")
        self.assertEqual(coverage_tool.exact_kind("drˈayah", "dráyah"), "notation")

    def test_an_unmarked_dictionary_form_is_silent_about_stress(self):
        self.assertEqual(coverage_tool.exact_kind("waydˈayati", "waydayati"), "notation")

    def test_a_morpheme_boundary_is_not_notation(self):
        # The laws never write a hyphen; a hyphen in the record marks an affix
        # or a bound form.  Mill's audit found 238 such pairs (2026-11-09).
        self.assertIsNone(coverage_tool.exact_kind("un", "un-"))
        self.assertIsNone(coverage_tool.exact_kind("ha", "ha-"))

    def test_a_letter_is_not_notation(self):
        # θ and þ are two letters for one phoneme: the spelling layer's
        # business, never the "character for character" figure.
        self.assertIsNone(coverage_tool.exact_kind("θing", "þing"))

    def test_two_words_are_not_one(self):
        self.assertIsNone(coverage_tool.exact_kind("fimftigiwi", "fimf tigiwi"))

    def test_everything_else_still_has_to_agree(self):
        self.assertIsNone(coverage_tool.exact_kind("nām", "nam"))
        self.assertIsNone(coverage_tool.exact_kind("pārsa", "parsa"))
        self.assertIsNone(coverage_tool.exact_kind("wˈarkah", "warkeh"))
        self.assertIsNone(coverage_tool.exact_kind("zˈanah", "𐏀𐎴"))


class TestAncestryKind(unittest.TestCase):
    def test_a_language_row_is_read_from_the_first_element(self):
        self.assertEqual(coverage_tool._row_lang(["enm", "dixionare", "inherit"]), "enm")

    def test_a_borrowing_row_carries_the_language_in_its_target(self):
        self.assertEqual(coverage_tool._row_lang([":bor", "ar:أَب", "root"]), "ar")

    def test_an_affix_is_not_a_language(self):
        self.assertIsNone(coverage_tool._row_lang([":af", "non-", "prefix"]))

    def test_an_inherited_entry_is_not_counted_as_borrowed(self):
        entry = {"word": "x", "anc": [["enm", "x", "inherit"], [":af", "un-", "prefix"]]}
        self.assertEqual(coverage_tool.ancestry_kind(entry, {"enm", "en"}), "inherited")

    def test_a_borrowed_entry_is(self):
        entry = {"word": "x", "anc": [[":bor", "ar:أَب", "root"]]}
        self.assertEqual(coverage_tool.ancestry_kind(entry, {"enm"}), "borrowed")


if __name__ == "__main__":
    unittest.main()

class TestOrthographicHit(unittest.TestCase):
    """The orthographic layer must be tried on every candidate (2026-11-09)."""

    def test_a_scripted_word_is_found_from_the_candidate_that_spells_it(self):
        # The page's earliest ancestor is a bare root and the laws cannot write
        # it; the Proto-Indo-Iranian candidate spells the attested headword.
        # The old counter only looked at the "closest" Latin output, which for
        # Devanagari is noise, and reported Sanskrit as 0 spelled words.
        hit = coverage_tool.orthographic_hit(
            [("bʰū", 1, "ine-pro"), ("bʰˈavati", 2, "iir-pro")],
            "sa", "भवति", "/bʱɐ́.ʋɐ.ti/")
        self.assertIsNotNone(hit)
        self.assertEqual(hit[2], "iir-pro")

    def test_a_form_whose_phonemes_are_wrong_is_not_a_spelling(self):
        self.assertIsNone(coverage_tool.orthographic_hit(
            [("bʰˈavatī", 2, "iir-pro")], "sa", "भवति", "/bʱɐ́.ʋɐ.ti/"))

    def test_a_language_without_a_spelling_file_has_no_hit(self):
        self.assertIsNone(coverage_tool.orthographic_hit(
            [("fˈūt", 1, "en")], "ine-pro", "fōts", ""))


class TestCitationHit(unittest.TestCase):
    """The laws give deváḥ, the dictionary cites devá (2026-11-09)."""

    def test_the_stem_of_a_produced_nominative_is_found(self):
        hit = coverage_tool.citation_hit(
            [("vˈiśvaḥ", 3, "iir-pro")], "sa", "विश्व", "/ʋɪɕ.ʋɐ́/")
        self.assertIsNotNone(hit)
        self.assertEqual(hit[0], "vˈiśva")
        self.assertEqual(hit[3], "ḥ")

    def test_only_an_endings_of_the_file_may_be_dropped(self):
        # *vˈiśvam would have to lose -am, which is not a citation ending.
        self.assertIsNone(coverage_tool.citation_hit(
            [("vˈiśvam", 3, "iir-pro")], "sa", "विश्व", "/ʋɪɕ.ʋɐ́/"))

    def test_the_guard_still_holds(self):
        self.assertIsNone(coverage_tool.citation_hit(
            [("pi.tɐḥ", 3, "iir-pro")], "sa", "विश्व", "/ʋɪɕ.ʋɐ́/"))


class TestUnchangedAndBoundLayers(unittest.TestCase):
    """Two counts where no rule had to do anything (2026-11-09).

    The counter used to demand one fired rule before comparing, so a word
    whose ancestor is already the attested form was a permanent miss, and a
    word the record writes with a morpheme hyphen (``-kas``) could never match.
    Both are now measured, and neither is folded into the exact figure: in
    neither did a law demonstrate anything.
    """

    def test_an_unchanged_ancestor_is_counted_apart(self):
        outputs = [("mˈuHs", 0, "ine-pro")]
        hit = coverage_tool._identity_hit(outputs, "múHs", {"translit": "múHs"})
        self.assertIsNotNone(hit)
        self.assertEqual(hit[1], "ine-pro")

    def test_a_fired_rule_is_not_identity(self):
        self.assertIsNone(coverage_tool._identity_hit(
            [("mˈuHs", 2, "ine-pro")], "múHs", {"translit": "múHs"}))

    def test_a_different_form_is_not_identity(self):
        self.assertIsNone(coverage_tool._identity_hit(
            [("mˈus", 0, "ine-pro")], "múHs", {"translit": "múHs"}))

    def test_a_bound_form_is_the_same_letters(self):
        self.assertTrue(coverage_tool._bound_pair("kas", "-kas"))
        self.assertTrue(coverage_tool._bound_pair("ˈa", "a-"))
        self.assertFalse(coverage_tool._bound_pair("kˈasam", "-kas"))

    def test_a_free_word_is_not_a_bound_pair(self):
        self.assertFalse(coverage_tool._bound_pair("kas", "kas"))


class TestMeasurementInputs(unittest.TestCase):
    """The published artifacts name the data they measured (2026-11-12)."""

    def test_the_digest_changes_when_a_lexicon_or_rule_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lexicon = root / "lexicon"
            rules = root / "rules"
            lexicon.mkdir()
            rules.mkdir()
            lex = lexicon / "fa.jsonl.gz"
            rule = rules / "ine-pro__gem-pro.yaml"
            lex.write_bytes(b"one")
            rule.write_text("name: one\n", encoding="utf-8")
            os.utime(lex, ns=(1_000_000_000, 1_000_000_000))
            os.utime(rule, ns=(1_000_000_000, 1_000_000_000))

            first = data.measurement_inputs(lexicon, rules)
            self.assertEqual(first, data.measurement_inputs(lexicon, rules))

            os.utime(lex, ns=(2_000_000_000, 2_000_000_000))
            second = data.measurement_inputs(lexicon, rules)
            self.assertNotEqual(first["lexicon"], second["lexicon"])
            self.assertEqual(first["rules"], second["rules"])

            rule.write_text("name: two\nlonger\n", encoding="utf-8")
            third = data.measurement_inputs(lexicon, rules)
            self.assertNotEqual(second["rules"], third["rules"])

    def test_an_artifact_without_inputs_is_not_called_stale(self):
        self.assertFalse(data.inputs_stale(None))
        self.assertFalse(data.inputs_stale({}))
        self.assertFalse(service.BandIndex().stale)

    def test_a_changed_digest_is_stale(self):
        current = data.measurement_inputs()
        self.assertFalse(data.inputs_stale(current, current))
        self.assertTrue(data.inputs_stale({**current, "lexicon": "0" * 40}, current))

    def test_the_coverage_payload_says_whether_it_is_stale(self):
        self.assertIsInstance(service.coverage().get("stale"), bool)
