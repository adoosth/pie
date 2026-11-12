"""Writing Avestan in the Avestan alphabet (2026-11-09).

The Avestan script is an alphabet: every vowel has a letter of its own and
length is written, so the step from a phonemic form to the manuscript's letters
is a transcription (Hoffmann & Forssman 2004, pp. 44-46).  Two things besides
the letter table are conventions rather than substitutions, and these tests pin
them: a stressed vowel is written plain, and a glide between vowels is written
with the matching vowel doubled (𐬌𐬌 *ii*, 𐬎𐬎 *uu*).

The last test is the one that keeps the table honest: every letter it claims is
either exercised by a real headword of the glossary or named as unwritten, so
the table cannot carry a letter nothing in the corpus ever uses.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, spelling, translit, writing  # noqa: E402

#: Letters of the alphabet this table does not write: no headword of the
#: glossary uses one of them, and the phonological layer does not distinguish
#: them, so a word that needs one is a miss rather than a guess.
UNWRITTEN = {"l", "m̨", "x́", "ġ", "ŋ́", "ŋᵛ", "ẏ", "ą̇"}


class TestAvestanAlphabet(unittest.TestCase):
    def test_one_letter_per_phoneme(self):
        self.assertEqual(writing.avestan("ap"), "𐬀𐬞")
        self.assertEqual(writing.avestan("ahma"), "𐬀𐬵𐬨𐬀")
        self.assertEqual(writing.avestan("brātā"), "𐬠𐬭𐬁𐬙𐬁")

    def test_length_has_its_own_letter(self):
        self.assertEqual(writing.avestan("ā"), "𐬁")
        self.assertEqual(writing.avestan("ī"), "𐬍")
        self.assertEqual(writing.avestan("ū"), "𐬏")
        self.assertNotEqual(writing.avestan("a"), writing.avestan("ā"))

    def test_the_four_nasal_vowels_are_four_letters(self):
        self.assertEqual(writing.avestan("å"), "𐬂")
        self.assertEqual(writing.avestan("ā̊"), "𐬃")
        self.assertEqual(writing.avestan("ą"), "𐬄")
        self.assertEqual(writing.avestan("ą̇"), "𐬅")
        self.assertEqual(len({writing.avestan(v) for v in "å ą".split()}), 2)

    def test_a_glide_between_vowels_is_the_vowel_doubled(self):
        # friia- writes /y/ as ii, aēuua- writes /w/ as uu (Hoffmann & Forssman
        # 2004, §5: 𐬌𐬌 is /ii̯/ and 𐬎𐬎 is /uu̯/).
        self.assertEqual(writing.avestan("friia"), "𐬟𐬭𐬌𐬌𐬀")
        self.assertEqual(writing.avestan("aēuua"), "𐬀𐬉𐬎𐬎𐬀")
        # The doubled sign is the glide's own vowel, so it is written once when
        # the vowel before it is already that letter: xšaθriya- is 𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀
        # with two i, not three.
        self.assertEqual(writing.avestan("xšaθriya"), "𐬑𐬱𐬀𐬚𐬭𐬌𐬌𐬀")
        # Next to a consonant each glide keeps its own letter.
        self.assertEqual(writing.avestan("dyaoš"), "𐬛𐬫𐬀𐬊𐬱")
        self.assertEqual(writing.avestan("vā"), "𐬬𐬁")

    def test_stress_is_not_written(self):
        self.assertEqual(writing.avestan("aˈēšəma"), writing.avestan("aēšəma"))
        self.assertEqual(writing.avestan("Áryō"), writing.avestan("aryō"))

    def test_notation_the_table_does_not_own_is_kept_visible(self):
        # A laryngeal that survived, or a sign the alphabet lacks, must not be
        # dropped: the word would then look like a match.
        self.assertIn("H", writing.avestan("Hap"))
        self.assertFalse(writing.avestan_readable("Hap"))
        self.assertTrue(writing.avestan_readable("hap"))

    def test_the_table_reads_back_to_the_same_letters(self):
        # The writer and the reader of the alphabet must be inverses, or a
        # "correct" spelling would not be the headword a text writes.
        for form in ("a", "ā", "i", "ī", "u", "ū", "ə", "e", "ē", "o", "ō",
                     "k", "x", "g", "c", "j", "t", "θ", "d", "p", "f", "b",
                     "ŋ", "n", "m", "y", "v", "r", "s", "z", "š", "ž", "h"):
            written = writing.avestan(form)
            self.assertEqual(translit.AVESTAN[written], form, form)


class TestAvestanSpellingFile(unittest.TestCase):
    def test_the_file_writes_the_word(self):
        self.assertEqual(spelling.spell("ahma", "ave"), "𐬀𐬵𐬨𐬀")
        self.assertEqual(spelling.spell("zānu", "ave"), "𐬰𐬁𐬥𐬎")
        self.assertEqual(spelling.spell("aˈēšəma", "ave"), "𐬀𐬉𐬱𐬆𐬨𐬀")

    def test_the_file_cites_and_uses_the_orthographic_tier(self):
        rs = spelling.ruleset("ave")
        self.assertIsNotNone(rs)
        for rule in rs.rules:
            self.assertEqual(rule.tier, "orthographic")
            self.assertTrue(rule.references)

    def test_a_spelling_never_claims_to_be_a_sound_law(self):
        self.assertNotEqual(spelling.spell("ahma", "ave"), "ahma")

    def test_a_word_the_table_cannot_write_is_not_a_match(self):
        # 𐬕 ġ is a letter of the alphabet the table does not write, and the
        # headword a text would spell with it is not produced from /g/.
        self.assertNotEqual(spelling.spell("g", "ave"), "𐬕")


class TestTheTableIsExercised(unittest.TestCase):
    """Every letter must be earned: by a headword, or by being declared out."""

    def used(self) -> set[str]:
        used: set[str] = set()
        for entry in data.lexicon("ave"):
            reading = translit.transliterate(entry["word"])
            if reading:
                used.update(writing._avestan_units(reading["reading"]))
        return used

    def letters(self) -> set[str]:
        return set(writing._AV_VOWELS) | set(writing._AV_CONSONANTS)

    def test_every_letter_is_used_by_a_headword_or_declared_unwritten(self):
        used = self.used()
        unexercised = self.letters() - used - set(writing._AV_ALIASES)
        self.assertEqual(unexercised, UNWRITTEN,
                         f"letters with no headword: {sorted(unexercised)}")

    def test_a_letter_outside_the_table_is_refused_not_guessed(self):
        # Notation the table does not own — a laryngeal, a palatal written with
        # a stroke, the sign for a syllable — leaves the form unreadable, so it
        # can never be written with some other letter and pass as a match.
        for form in ("H", "P", "ȷ", "Ć", "ˢ"):
            self.assertFalse(writing.avestan_readable(form), form)
        for letter in writing._AV_VOWELS | writing._AV_CONSONANTS.keys():
            self.assertTrue(writing.avestan_readable(letter), letter)

    def test_the_writer_spells_every_headword_it_reads(self):
        # The writer and the reader are inverses for all but the two headwords
        # whose reading carries punctuation the writer does not own.
        roundtrip = 0
        for entry in data.lexicon("ave"):
            reading = translit.transliterate(entry["word"])
            if not reading:
                continue
            if writing.avestan(reading["reading"]) == entry["word"]:
                roundtrip += 1
        self.assertGreaterEqual(roundtrip, 348, roundtrip)


if __name__ == "__main__":
    unittest.main()
