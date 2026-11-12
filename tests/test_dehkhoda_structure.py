"""Dehkhoda's own grammar label, read from the entry he prints (2026-11-10).

Every Dehkhoda entry opens with the headword, its pronunciation and a
parenthetical tag — ``(اِ مرکب)`` "noun, compound", ``(ص نسبی)`` "relative
adjective", ``(اِخ)`` "proper noun".  The label is a record, so the tests hold
the reader to three promises: it reads the tag and nothing else (a parenthesis
in the middle of prose is not a label), it maps only the abbreviations whose
meaning is certain, and it never turns a label into an etymology.
"""
from __future__ import annotations

import unittest

from pie import data

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "dehkhoda_structure", Path(__file__).resolve().parents[1] / "tools" / "dehkhoda_structure.py")
structure = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("dehkhoda_structure", structure)
_spec.loader.exec_module(structure)


class LabelTests(unittest.TestCase):
    def test_reads_the_tag_after_the_headword(self):
        text = "آبخیز . [ خیز ] (ص مرکب ) جایی که آب از آن برآید."
        self.assertEqual(structure.read_label(text), "ص مرکب")

    def test_reads_a_tag_with_no_pronunciation(self):
        self.assertEqual(structure.read_label("آب . (اِ) مایع حیات : آب روان ."),
                         "اِ")

    def test_a_zero_width_non_joiner_inside_the_tag_is_a_space(self):
        self.assertEqual(structure.read_label("آبک . (اِ\u200cمرکب ) نام گیاهی ."),
                         "اِ مرکب")

    def test_a_parenthesis_in_prose_is_not_a_label(self):
        self.assertIsNone(structure.read_label(
            "آب . مایع حیات (به گفتهٔ فردوسی) روان است ."))

    def test_an_entry_with_no_tag_has_no_label(self):
        self.assertIsNone(structure.read_label("آب . مایع حیات ."))

    def test_empty_text(self):
        self.assertIsNone(structure.read_label(""))


class PosTests(unittest.TestCase):
    def test_the_simple_abbreviations(self):
        for label, pos in [("اِ", "noun"), ("ص", "adj"), ("ق", "adv"),
                           ("مص", "verb"), ("حامص", "noun"), ("اِمص", "noun"),
                           ("نف", "adj"), ("ن مف", "adj"), ("اِخ", "name"),
                           ("صوت", "intj")]:
            with self.subTest(label=label):
                self.assertEqual(structure.pos_of(label), pos)

    def test_a_language_tag_before_the_pos_is_not_the_pos(self):
        # (ع اِ) is an Arabic noun: the ع states the origin, the اِ the grammar.
        self.assertEqual(structure.pos_of("ع اِ"), "noun")
        self.assertEqual(structure.pos_of("فرانسوی ، اِ"), "noun")
        self.assertEqual(structure.pos_of("معرب ، اِ"), "noun")

    def test_a_compound_tag_still_names_its_pos(self):
        self.assertEqual(structure.pos_of("اِ مرکب"), "noun")
        self.assertEqual(structure.pos_of("ص نسبی"), "adj")
        self.assertEqual(structure.pos_of("اِ مرکب ، ق مرکب"), "noun")

    def test_an_unknown_abbreviation_gets_no_pos(self):
        # ن تف is an abbreviation of the dictionary's that this map does not
        # know; it is not guessed at.
        for label in ("ن تف", "ع ن تف"):
            with self.subTest(label=label):
                self.assertIsNone(structure.pos_of(label))

    def test_a_typo_still_names_the_pos_it_prints(self):
        # (اِ رکب) is Dehkhoda's own typo for (اِ مرکب): the اِ is certain, the
        # compound flag is not read from a misspelling.
        self.assertEqual(structure.pos_of("اِ رکب"), "noun")


class FlagTests(unittest.TestCase):
    def test_a_compound_tag_marks_a_compound(self):
        row = structure.row("آبخیز", "اِ مرکب")
        self.assertTrue(row["compound"])
        self.assertFalse(row.get("relational"))

    def test_a_name_is_not_a_compound(self):
        row = structure.row("آدم", "اِخ")
        self.assertTrue(row["name"])
        self.assertFalse(row.get("compound"))
        self.assertEqual(row["pos"], "name")

    def test_a_relative_adjective(self):
        row = structure.row("آتشین", "ص نسبی")
        self.assertTrue(row["relational"])
        self.assertEqual(row["pos"], "adj")

    def test_huzvarish_is_its_own_mark(self):
        row = structure.row("جانونتن", "هزوارش ، مص")
        self.assertTrue(row["huzvarish"])
        self.assertEqual(row["pos"], "verb")

    def test_the_label_is_kept_verbatim(self):
        self.assertEqual(structure.row("آبکی", "ص نسبی")["label"], "ص نسبی")


class LoadedTests(unittest.TestCase):
    """The file the tool writes is what the lexicon actually reads."""

    def test_the_structure_file_loads(self):
        rows = data.structures().get("fa") or {}
        self.assertTrue(rows, "data/dehkhoda/structure.jsonl.gz is missing")
        self.assertIn("pos_label", next(iter(rows.values())))
        sample = rows.get("آتشین")
        self.assertIsNotNone(sample)
        self.assertEqual(sample["pos_label"], "ص نسبی")

    def test_the_lexicon_carries_the_label(self):
        entry = data.lexicon_index("fa").get("آتشین")
        self.assertTrue(entry)
        self.assertEqual(entry[0].get("pos_label"), "ص نسبی")
        self.assertTrue((entry[0].get("structure") or {}).get("relational"))


class SeamTests(unittest.TestCase):
    """A label lets a formation be shown; it never makes a word green."""

    def test_a_relative_adjective_is_a_suffix_formation(self):
        from pie import service
        seam = service.seam_of("fa", "آبکاری", "ص نسبی")
        self.assertIsNotNone(seam)
        self.assertEqual(seam["kind"], "suffix")
        self.assertFalse(seam["verified"])
        self.assertIn("نسبی", seam["sentence"])

    def test_without_the_label_the_same_word_is_refused(self):
        from pie import service
        # آبکار is a stored headword but carries no etymology of its own, so a
        # bare -ی cut is not evidence; the dictionary's own "relative
        # adjective" is what makes the formation sayable.
        self.assertIsNone(service.seam_of("fa", "آبکاری", ""))

    def test_a_place_name_takes_a_relative_ending(self):
        from pie import service
        # آثوری "Assyrian" is آثور + -ی: a name is a perfectly good base for a
        # relative adjective, so the label path must not refuse it.
        seam = service.seam_of("fa", "آثوری", "ص نسبی")
        self.assertEqual(seam["parts"], ["آثور", "-ی"])

    def test_a_relative_label_licenses_only_its_own_suffix(self):
        from pie import service
        # تئوریک is a French loan and -ک is a diminutive, not a relative
        # ending: «ص نسبی» must not license it (review, 2026-11-10).
        self.assertIsNone(service.seam_of("fa", "تئوریک", "فرانسوی ، ص نسبی"))

    def test_a_borrowed_word_gets_no_formation_beside_its_loan(self):
        from pie import service
        # One lexeme has one pathway: a word whose record names the language it
        # was borrowed from is not also "built from" Persian words.
        entry = {"word": "آبکاری", "lang": "fa", "borrowed_from": "ar",
                 "pos_label": "ص نسبی"}
        self.assertIsNone(service._seam_payload("fa", entry))

    def test_a_noun_does_not_wear_the_relational_gloss(self):
        from pie import data, service
        # -ی on a noun (آبخوری "a drinking vessel") is not the relational
        # adjective sense the registry row describes.
        entry = next(e for e in data.lexicon("fa") if e["word"] == "آبخوری")
        join = service._seam_join("fa", entry)
        self.assertIsNotNone(join)
        bound = [p for p in join["pieces"] if p.get("bound")]
        self.assertTrue(bound)
        self.assertEqual(bound[0]["gloss"], "")

    def test_the_rung_and_the_join_view_agree(self):
        from pie import data, service
        entry = next(e for e in data.lexicon("fa") if e["word"] == "آبکاری")
        rung = service._rung_built(entry, "fa", "آبکاری")
        self.assertIsNotNone(rung)
        self.assertEqual(rung["source"], "ours")


if __name__ == "__main__":
    unittest.main()
