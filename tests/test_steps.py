"""The counter and the word page must agree about which recorded rungs differ.

`pie.steps` exists so the coverage counter can compare every recorded
intermediate stage without building a whole word page.  The project's rule
(2026-11-09) is that a differing recorded step costs a word the dark green, so
a disagreement between the page and the counter would put two different bands
on one word.  These tests hold the two to the same answer.
"""
from __future__ import annotations

import unittest

from pie import data, service, steps


def entry(lang: str, word: str) -> dict:
    for row in data.lexicon(lang):
        if row["word"] == word:
            return row
    raise AssertionError(f"{lang} glossary has no {word!r}")


class MismatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rulesets = data.rulesets()

    def mismatches(self, lang: str, word: str) -> list[dict]:
        return steps.mismatches(entry(lang, word), lang,
                                data.derivation_chain(lang), self.rulesets)

    def test_night_disagrees_at_every_stage_above_the_word(self):
        stages = [row["stage"] for row in self.mismatches("en", "night")]
        self.assertEqual(stages, ["gem-pro", "gmw-pro", "ang", "enm"])

    def test_a_differing_step_carries_both_forms(self):
        first = self.mismatches("en", "night")[0]
        self.assertEqual(first["stage"], "gem-pro")
        self.assertEqual(first["recorded"], "nahts")
        self.assertNotEqual(first["derived"], first["recorded"])
        self.assertEqual(first["name"], "Proto-Germanic")

    def test_a_chain_whose_rungs_all_agree_is_empty(self):
        self.assertEqual(self.mismatches("fa", "یخ"), [])
        self.assertEqual(self.mismatches("en", "verb"), [])

    def test_the_word_page_and_the_counter_name_the_same_stages(self):
        for lang, word in (("en", "night"), ("en", "water"), ("fa", "یخ")):
            # *water* is one word in two parts of speech; the page of the first
            # sense is the one the counter measured (2026-11-09).
            page = service.word(lang, word, sense=1)
            counter = [row["stage"] for row in self.mismatches(lang, word)]
            self.assertEqual(page["hierarchy"]["mismatched_steps"], counter, word)
            self.assertEqual([row["stage"] for row in page["steps_differ"]], counter, word)

    def test_a_word_with_no_modelled_start_has_no_evidence(self):
        """No chain, no comparison — and the caller must not read that as a pass."""
        row = {"word": "x", "lang": "en", "anc": []}
        self.assertEqual(steps.mismatches(row, "en", data.derivation_chain("en"),
                                          self.rulesets), [])


if __name__ == "__main__":
    unittest.main()
