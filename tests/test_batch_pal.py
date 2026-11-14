"""Middle Persian: the transliteration notation is a rendering of the signs.

The pal table now holds three notations of one writing system: the Pahlavi
letters, the Manichaean letters, and the Latin transliteration MacKenzie
prints the spellings in.  The transliteration is not a pronunciation — it is
one letter per sign — so it is tested the way the signs are: it must read the
dictionary's own (spelling, transcription) pairs, it may not invent a short
vowel the script does not write, and it may not leave a letter unfilled
(2026-11-09).
"""
import re
import unittest

from pie import data, script

#: The Pahlavi sign each transliteration letter renders, so the two rows can
#: be compared: the notation adds no value the sign does not have.
RENDERS = {
    "ʾ": "𐭠", "b": "𐭡", "g": "𐭢", "d": "𐭣", "h": "𐭤", "w": "𐭥",
    "z": "𐭦", "ḥ": "𐭧", "y": "𐭩", "k": "𐭪", "l": "𐭫", "m": "𐭬",
    "n": "𐭭", "s": "𐭮", "p": "𐭯", "c": "𐭰", "š": "𐭱", "t": "𐭲",
    "ʿ": "𐭥", "č": "𐭰", "ẕ": "𐭦",
}

#: Values the corpus shows the notation writing although the sign row does not
#: list them yet; each is quoted from a dictionary entry, not from a guess.
MACKENZIE_PAIRS = [
    ("ʾp̄ʾt'", "ābād"),      # s.v. abad [ypytl] (OCR of ʾp̄ʾt'): populous
    ("gwlg", "gurg"),       # s.v. gurg [gwlg]: wolf — waw writes short u
    ("hwʾb", "xwāb"),       # xwāb, with heth read x
    ("nmk'", "namak"),      # namak: short a unwritten
    ("tʾht'", "taxt"),      # taxt: heth read x
    ("bplk'", "babrag"),    # babrag: pe read b, kaph read g
]


class TestTransliterationTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = script.table("pal")

    def test_every_letter_renders_a_sign_it_is_not_a_sound_of_its_own(self):
        for letter, sign in RENDERS.items():
            self.assertIn(letter, self.table, letter)
            self.assertEqual(self.table[letter]["kind"], "translit")
            sign_sounds = set(self.table[sign]["sounds"])
            letter_sounds = set(self.table[letter]["sounds"])
            self.assertTrue(letter_sounds, letter)
            # Every value of the letter is a value of the sign, with two
            # stated exceptions: the letter h renders he *and* heth, so it
            # carries heth's x; and waw/yodh are matres that write a short u/i
            # (gwlg = gurg, s.v. gurg).
            allowed = {"h": {"x"}, "w": {"u", "i"}, "y": {"i"}}.get(letter, set())
            extra = letter_sounds - sign_sounds
            self.assertTrue(extra <= allowed, f"{letter}: {sorted(extra)}")

    def test_no_short_vowel_is_a_letter(self):
        """A reading can never be parsed as a transliteration by accident."""
        for vowel in "aeiou":
            self.assertNotIn(vowel, self.table, vowel)

    def test_ideograms_are_not_letters(self):
        """ŠM, LWTE and the rest are read as words from the reading table."""
        for capital in "AHCEKLMNOPQRSTUWXYZ":
            self.assertNotIn(capital, self.table, capital)

    def test_a_sign_of_the_notation_cannot_be_left_unfilled(self):
        self.assertTrue(script.match("pal", "gurg", "gwlg")["ok"])
        self.assertFalse(script.match("pal", "gur", "gwlg")["ok"])

    def test_a_consonant_may_not_go_missing(self):
        # g-w-l-g needs all four signs; g-w-l is not gurg
        self.assertFalse(script.match("pal", "gurg", "gwl")["ok"])
        self.assertFalse(script.match("pal", "rōšn", "lwn")["ok"])


class TestMackenziePairs(unittest.TestCase):
    """The dictionary prints the spelling and the transcription side by side."""

    def test_the_pairs_the_dictionary_states_are_read(self):
        for spelling, reading in MACKENZIE_PAIRS:
            fit = script.match("pal", reading, spelling)
            self.assertIsNotNone(fit, spelling)
            self.assertTrue(fit["ok"], f"{spelling} does not read {reading}")

    def test_most_pairs_in_the_lexicon_are_read(self):
        """A floor, so a future sign edit cannot quietly stop reading them."""
        letters = set(RENDERS)
        reading = re.compile(r"^[a-zāēīōūščžğḥṛṇṃńťď]+$")
        accepted = refused = 0
        for entry in data.lexicon("pal"):
            spelling = (entry.get("word") or "").strip()
            reading_ = (entry.get("translit") or "").strip()
            if sum(ch in letters for ch in spelling) < 2:
                continue
            if any(ch.isalpha() and ch not in letters for ch in spelling):
                continue
            if not reading.match(reading_):
                continue
            fit = script.match("pal", reading_, spelling)
            if fit is None:
                continue
            accepted += bool(fit["ok"])
            refused += not fit["ok"]
        # measured 2026-11-09: 48 read, 32 refused (the rest are OCR damage in
        # the spelling column or a polyphony this table does not state yet).
        # The Wiktionary lemma pass of 2026-11-12 added one more readable pair.
        self.assertGreaterEqual(accepted, 45)
        self.assertEqual(accepted + refused, 81)


if __name__ == "__main__":
    unittest.main()
