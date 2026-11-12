"""Avestan, night 0911 (second pass): the record is read, not guessed.

The first pass measured that Avestan could not move and said why: the glossary
is written in the alphabet and only 39 of its 352 entries carry an IPA, so the
orthographic layer's guard (which compares a phonemic form against the
dictionary's pronunciation) had nothing to compare against, and the entries are
cited by the stem (aspa-) while the laws end in the nominative (aspō).

Two facts, not two laws, close that gap, and these tests pin both:

* the alphabet has a known value for every letter, so a word's own letters are
  its reading.  ``spelling.record_reading`` uses that when the corpus has no
  IPA, and ``spelling.confirms`` is the single call every layer makes.  The
  reading is *not* the writer run backwards: 𐬀𐬎𐬎𐬀 reads auua and never ava,
  so a glide the laws wrote is still rejected (measured: 24 of the 29 words
  whose letters the layer spells are confirmed, 5 are turned away).
* a dictionary may cite the stem, and an ending may stand *in place of* a stem
  vowel (-ō for -a), which ``data/citation/ave.yaml`` states for the a-, i- and
  u-stems.  Only the pairs the file lists may be set aside.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import citation, spelling, writing  # noqa: E402
import coverage as coverage_tool            # noqa: E402


class TestTheRecordIsRead(unittest.TestCase):
    def test_the_letters_are_the_reading(self):
        self.assertEqual(writing.avestan_reading("𐬀𐬵𐬨𐬀"), "ahma")
        self.assertEqual(writing.avestan_reading("𐬀𐬉𐬱𐬆𐬨𐬀"), "aēšəma")
        self.assertEqual(writing.avestan_reading("𐬰𐬁𐬥𐬎"), "zānu")

    def test_a_glide_is_two_signs_and_stays_two(self):
        # The writer spells /w/ between vowels with uu; the reader must not give
        # ava back from a word that writes auua (measured 2026-11-09: this is
        # the one false friend the reading turns away, with its twin nauua).
        self.assertEqual(writing.avestan_reading("𐬀𐬎𐬎𐬀"), "auua")
        self.assertEqual(writing.avestan_reading("𐬀𐬉𐬎𐬎𐬀"), "aēuua")
        self.assertFalse(spelling.confirms("ava", "𐬀𐬎𐬎𐬀", "", "ave"))
        self.assertTrue(spelling.confirms("aēuua", "𐬀𐬉𐬎𐬎𐬀", "", "ave"))

    def test_one_value_per_letter(self):
        # The declaration `guard: {reading: avestan}` says the writing is an
        # alphabet: every letter of the table carries one phoneme.  The only
        # duplicated letters are the declared aliases, which the reader
        # resolves to the canonical phoneme.
        table = {**writing._AV_VOWELS, **writing._AV_CONSONANTS}
        letters = set(table.values())
        for letter in letters:
            phonemes = {p for p, l in table.items() if l == letter}
            if len(phonemes) > 1:
                self.assertEqual(len({p for p in phonemes if p not in writing._AV_ALIASES}), 1,
                                 f"{letter} carries {sorted(phonemes)}")
        for phoneme, letter in table.items():
            read = writing.avestan_reading(letter)
            self.assertIn(read, table, f"{letter} reads as {read!r}, no phoneme of the table")
            self.assertEqual(writing.avestan(phoneme), letter)


class TestTheGuard(unittest.TestCase):
    def test_the_reading_stands_in_for_a_missing_ipa(self):
        self.assertEqual(spelling.record_reading("𐬀𐬵𐬨𐬀", "", "ave"), "ahma")
        self.assertTrue(spelling.confirms("ahma", "𐬀𐬵𐬨𐬀", "", "ave"))
        # A recorded IPA wins over the reading when the entry has one.
        self.assertEqual(spelling.record_reading("𐬀𐬞", "/ap/", "ave"), "/ap/")

    def test_no_reader_and_no_ipa_confirms_nothing(self):
        self.assertEqual(spelling.record_reading("buch", "", "de"), "")
        self.assertFalse(spelling.confirms("bˈuːx", "buch", "", "de"))
        # Only the language that declares a reader gets one.
        self.assertEqual(spelling.reading_of("ave"), "avestan")
        self.assertEqual(spelling.reading_of("de"), "")

    def test_the_alias_fold_is_notation(self):
        # 𐬗 is written c by this project's layer and č by a dictionary; folding
        # one into the other changes no letter of the manuscript.
        self.assertTrue(spelling.confirms("ča", "𐬗𐬀", "", "ave"))
        self.assertTrue(spelling.confirms("ca", "𐬗𐬀", "", "ave"))
        self.assertFalse(spelling.confirms("ja", "𐬗𐬀", "", "ave"))


class TestCitedAsTheStem(unittest.TestCase):
    def test_the_pairs_the_file_states(self):
        self.assertEqual(citation.endings("ave"), ("ō", "əm", "iš", "uš"))
        self.assertIn(("ō", "a"), citation.pairs("ave"))
        # Sanskrit cites the bare stem, so its endings stand for nothing.
        self.assertTrue(all(cited == "" for _end, cited in citation.pairs("sa")))

    def test_a_nominative_is_read_as_the_stem(self):
        hit = coverage_tool.citation_hit(
            [("aspō", 3, "iir-pro")], "ave", "𐬀𐬯𐬞𐬀", "")
        self.assertIsNotNone(hit)
        self.assertEqual(hit[0], "aspa")
        self.assertEqual(hit[3], "ō")
        self.assertEqual(hit[4], "aspō")

    def test_only_the_file_s_pairs_are_set_aside(self):
        # -ō is a pair; -ā is not, and the stem must still spell the word.
        self.assertIsNone(coverage_tool.citation_hit(
            [("dātā", 3, "iir-pro")], "ave", "𐬀𐬯𐬞𐬀", ""))
        self.assertIsNone(coverage_tool.citation_hit(
            [("akō", 3, "iir-pro")], "ave", "𐬀𐬯𐬞𐬀", ""))


if __name__ == "__main__":
    unittest.main()
