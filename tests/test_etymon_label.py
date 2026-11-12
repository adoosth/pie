"""The dictionary's labels must not become part of an etymon.

Wiktionary writes a sense label after a hash (``*kʷís#Determiner``), a gloss
in trailing parentheses (``*per- (fare)``) and, in an etymology tree, the
first of two alternants (``*ḱḗr ~ *ḱr̥d-``).  None of that belongs to the
form the ladder starts from.  A genuine two-word lemma is different: a space
is a word boundary and is never a label.
"""

import unittest

from pie.service import normalise_etymon


class NormaliseEtymonTest(unittest.TestCase):
    def test_trailing_gloss_is_not_part_of_the_form(self):
        self.assertEqual(normalise_etymon("*per- (fare)"), "per")
        self.assertEqual(normalise_etymon("*pel- (fold)"), "pel")

    def test_sense_label_after_hash(self):
        self.assertEqual(normalise_etymon("*kʷís#Determiner"), "kʷís")
        self.assertEqual(normalise_etymon("gin#Verb"), "gin")

    def test_first_member_of_an_alternation(self):
        self.assertEqual(normalise_etymon("*ḱḗr ~ *ḱr̥d-"), "ḱḗr")

    def test_movable_s_still_survives(self):
        self.assertEqual(normalise_etymon("*(s)pend-"), "spend")
        self.assertEqual(normalise_etymon("*(s)ker- (turn)"), "sker")

    def test_two_word_lemma_is_left_whole(self):
        self.assertEqual(normalise_etymon("newe founde"), "newe founde")

    def test_a_parenthesis_inside_the_form_is_not_a_gloss(self):
        self.assertEqual(normalise_etymon("*h₃én(H)os"), "h₃énHos")


if __name__ == "__main__":
    unittest.main()
