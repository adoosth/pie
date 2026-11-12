"""A tree's relation label is a label, never a suffix.

Wiktionary's etymology tree puts ``der.`` ("derived terms"), ``bor.``, ``lbor.``
and friends on the connector between two blocks.  Wiktextract welds them onto
the term they follow, so the stored string once read ``*peh₂-der.`` — a suffix
Proto-Indo-European does not have.  These tests hold the label where it belongs
and leave ordinary words that happen to end in ``-der.`` alone.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import data, etymtext, service

NAMES = {row["name"] for row in service.language_names().values()}


def split(text: str) -> str:
    return etymtext.split_labels(text, NAMES)


class TestTokens(unittest.TestCase):
    def test_a_glued_label_is_separated(self):
        self.assertEqual(etymtext.split_token("*peh₂-der."), ("*peh₂-", "der."))

    def test_an_uncertain_label_keeps_its_question_mark(self):
        self.assertEqual(etymtext.split_token("*h₁ēsh₂r̥no-der.?"), ("*h₁ēsh₂r̥no-", "der.?"))

    def test_a_plain_word_is_untouched(self):
        self.assertEqual(etymtext.split_token("fōdô"), ("fōdô", ""))

    def test_the_glossary_phrase_of_a_label(self):
        self.assertEqual(etymtext.gloss_of("der."), "derived terms")
        self.assertEqual(etymtext.gloss_of("lbor.?"), "learned borrowing")


class TestTheTree(unittest.TestCase):
    def test_food(self):
        """*peh₂- is the root; 'der.' is Wiktionary's word for 'derived from'."""
        text = ("Etymology tree Proto-Indo-European *peh₂-der. Proto-Germanic *fōdô "
                "Old English fōda Middle English fode English food From Middle English fode")
        self.assertIn("Proto-Indo-European *peh₂- [der.] Proto-Germanic", split(text))

    def test_a_learned_borrowing_run(self):
        text = ("Etymology tree Hebrew שָׁאַל Hebrew שָׁאוּלlbor. Ancient Greek Σαούλ (Saoúl)lbor. "
                "Late Latin Saullbor. Old English Saull English Saul")
        out = split(text)
        self.assertIn("שָׁאוּל [lbor.]", out)
        self.assertIn("(Saoúl) [lbor.]", out)
        self.assertIn("Saul [lbor.]", out)

    def test_a_clipping(self):
        text = ("Etymology tree English web English WikiWikiWebclip. English wiki "
                "From WikiWikiWeb + wiki")
        self.assertIn("WikiWikiWeb [clip.]", split(text))

    def test_a_slash_alternant_inside_one_block(self):
        text = ("Etymology tree Proto-Balto-Slavic *welk- /*wilk-der. Proto-Slavic *velťi "
                "Old Church Slavonic влѣщи")
        self.assertIn("*wilk- [der.]", split(text))

    def test_a_multi_word_term(self):
        text = ("Etymology tree Latin strātus Latin via strātaellip. Late Latin strāta "
                "Old High German strāza")
        self.assertIn("strāta [ellip.]", split(text))


class TestTheProseIsNotATree(unittest.TestCase):
    def test_a_sentence_ending_in_der(self):
        text = ("Etymology tree Old English beġeondan English beyond From Old English "
                "beġeondan, from be- + ġeond; related to yonder.")
        self.assertEqual(split(text), text)

    def test_a_sentence_ending_in_aph(self):
        text = "Etymology tree English sono- English sonograph From sono- + -graph."
        self.assertEqual(split(text), text)

    def test_a_borrowed_word_inside_a_sentence(self):
        text = ("Etymology tree Swahili bodaboda English boda-boda From Swahili bodaboda, "
                "from English border.")
        self.assertEqual(split(text), text)


class TestTheGlossaries(unittest.TestCase):
    def test_food_reads_as_a_derivation(self):
        rows = [r for r in data.lexicon("en") if r.get("word") == "food" and "Etymology tree" in (r.get("etym") or "")]
        self.assertTrue(rows, "the English glossary keeps food's etymology")
        self.assertIn("*peh₂- [der.]", rows[0]["etym"])
        self.assertNotIn("*peh₂-der", rows[0]["etym"])


if __name__ == "__main__":
    unittest.main()
