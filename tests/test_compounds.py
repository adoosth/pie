"""Formations from stored words: the acceptance tests and the honest wording.

Each test gives a fake lookup, so these are tests of the module's rules and not
of the Persian glossary.  The cases that matter most are the ones that must
*not* produce a claim: a different letter, a function word, a short seam with
no licence, an unrecorded piece, and a tie the model refuses to break.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import compounds


def headword(recorded: bool = True, pos: str | None = "noun",
             known: bool = True) -> dict:
    return {"known": known, "recorded": recorded, "pos": pos}


def lookup_of(mapping: dict):
    def lookup(form: str):
        return mapping.get(form)
    return lookup


BASE_RULES = {
    "min_part": 2,
    "min_word": 4,
    "long_part": 3,
    "short_ok": ["آب", "گل", "سر", "دل"],
    "function_words": ["از", "به", "با", "بر", "در", "تا", "که", "را", "و",
                       "هم", "نه", "بی"],
    "function_pos": ["prep", "postp", "conj", "pron", "det", "part",
                     "interj", "num", "adv"],
    "stop": ["اب"],
}


def rules(**changes) -> dict:
    out = dict(BASE_RULES)
    out["short_ok"] = list(BASE_RULES["short_ok"])
    out["function_words"] = list(BASE_RULES["function_words"])
    out["function_pos"] = list(BASE_RULES["function_pos"])
    out["stop"] = list(BASE_RULES["stop"])
    out.update(changes)
    return out


class CleanFormationTest(unittest.TestCase):
    def test_a_clean_two_part_formation(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword()})
        result = compounds.analyse("آبخانه", lookup, rules=rules())
        self.assertIsNotNone(result)
        self.assertEqual(result["word"], "آبخانه")
        self.assertEqual(result["parts"], ["آب", "خانه"])
        self.assertEqual(result["verdict"], "unique")
        self.assertEqual(result["alternatives"], [])
        self.assertIn("only split", result["reason"])

    def test_a_three_part_formation_when_no_two_part_passes(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword(),
                            "گل": headword()})
        result = compounds.analyse("آبخانهگل", lookup, rules=rules())
        self.assertIsNotNone(result)
        self.assertEqual(result["parts"], ["آب", "خانه", "گل"])
        self.assertEqual(result["verdict"], "unique")
        self.assertIn("three of its own words",
                      compounds.describe(result))

    def test_three_part_is_not_tried_when_a_two_part_passes(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword(),
                            "گل": headword(), "خانهگل": headword()})
        candidates = compounds.split_candidates("آبخانهگل", lookup,
                                                rules=rules())
        self.assertEqual(candidates, [["آب", "خانهگل"]])
        self.assertTrue(all(len(parts) == 2 for parts in candidates))


class ExactSpellingTest(unittest.TestCase):
    def test_ab_and_ab_are_different_letters(self):
        lookup = lookup_of({"پیش": headword(), "اب": headword(),
                            "آب": headword()})
        self.assertIsNone(compounds.analyse("پیشاب", lookup, rules=rules()))
        self.assertEqual(compounds.split_candidates("پیشاب", lookup,
                                                    rules=rules()), [])

        spelling = compounds.analyse("پیشآب", lookup, rules=rules())
        self.assertIsNotNone(spelling, "the test is about the letter, not the sense")
        self.assertEqual(spelling["parts"], ["پیش", "آب"])


class FunctionWordTest(unittest.TestCase):
    def test_a_function_word_is_never_a_component(self):
        lookup = lookup_of({"با": headword(), "کتاب": headword()})
        rejected = rules(short_ok=["آب", "با"])
        self.assertIsNone(compounds.analyse("باکتاب", lookup, rules=rejected))

        allowed = rules(short_ok=["آب", "با"],
                        function_words=["از", "به", "بر", "در", "تا"])
        result = compounds.analyse("باکتاب", lookup, rules=allowed)
        self.assertEqual(result["parts"], ["با", "کتاب"])

    def test_a_function_pos_is_rejected_even_when_the_spelling_is_not_listed(self):
        lookup = lookup_of({"پیش": headword(pos="prep"),
                            "کتاب": headword()})
        self.assertIsNone(compounds.analyse("پیشکتاب", lookup, rules=rules()))

        noun = lookup_of({"پیش": headword(pos="noun"), "کتاب": headword()})
        result = compounds.analyse("پیشکتاب", noun, rules=rules())
        self.assertEqual(result["parts"], ["پیش", "کتاب"])


class RecordedOriginTest(unittest.TestCase):
    def test_two_parts_without_an_origin_explain_nothing(self):
        lookup = lookup_of({"آب": headword(recorded=False),
                            "خانه": headword(recorded=False)})
        self.assertIsNone(compounds.analyse("آبخانه", lookup, rules=rules()))

    def test_one_recorded_part_is_enough(self):
        lookup = lookup_of({"آب": headword(recorded=True),
                            "خانه": headword(recorded=False)})
        result = compounds.analyse("آبخانه", lookup, rules=rules())
        self.assertIsNotNone(result)
        self.assertEqual(result["verdict"], "unique")


class AmbiguityTest(unittest.TestCase):
    def test_every_candidate_is_returned_and_no_band_may_be_assigned(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword(),
                            "آبخ": headword(), "انه": headword()})
        result = compounds.analyse("آبخانه", lookup, rules=rules())
        self.assertIsNotNone(result)
        self.assertEqual(result["verdict"], "ambiguous")
        self.assertEqual(result["alternatives"],
                         [["آب", "خانه"], ["آبخ", "انه"]])
        self.assertIn("must not be given a band", result["reason"])

        sentence = compounds.describe(result)
        self.assertIn("آب + خانه", sentence)
        self.assertIn("آبخ + انه", sentence)
        self.assertIn("left unclassified", sentence)
        self.assertIn("a formation, not a derivation", sentence)


class LengthAndStopTest(unittest.TestCase):
    def test_min_word_is_enforced(self):
        lookup = lookup_of({"آب": headword(), "گل": headword()})
        self.assertIsNone(compounds.analyse("آبگل", lookup,
                                            rules=rules(min_word=5)))
        self.assertIsNotNone(compounds.analyse("آبگل", lookup,
                                               rules=rules(min_word=4)))

    def test_a_short_part_needs_an_exact_short_ok_entry(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword()})
        self.assertIsNone(compounds.analyse("آبخانه", lookup,
                                            rules=rules(short_ok=[])))
        result = compounds.analyse("آبخانه", lookup,
                                   rules=rules(short_ok=["آب"]))
        self.assertEqual(result["parts"], ["آب", "خانه"])

    def test_stop_words_are_never_components(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword()})
        stopped = rules(short_ok=["آب"], stop=["آب"])
        self.assertIsNone(compounds.analyse("آبخانه", lookup, rules=stopped))

    def test_min_part_is_enforced_even_for_a_listed_short_form(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword()})
        self.assertIsNone(compounds.analyse("آبخانه", lookup,
                                            rules=rules(min_part=3)))
        self.assertIsNotNone(compounds.analyse("آبخانه", lookup,
                                               rules=rules(min_part=2)))

    def test_an_unknown_or_unstored_part_rejects_the_cut(self):
        missing = lookup_of({"آب": headword()})
        self.assertIsNone(compounds.analyse("آبخانه", missing, rules=rules()))

        unknown = lookup_of({"آب": headword(),
                             "خانه": headword(known=False)})
        self.assertIsNone(compounds.analyse("آبخانه", unknown, rules=rules()))


class DescribeTest(unittest.TestCase):
    def test_describe_calls_a_formation_not_a_derivation(self):
        lookup = lookup_of({"آب": headword(), "خانه": headword()})
        result = compounds.analyse("آبخانه", lookup, rules=rules())
        sentence = compounds.describe(result)
        self.assertIn("آب + خانه → آبخانه", sentence)
        self.assertIn("built in Persian from two of its own words", sentence)
        self.assertIn("a formation, not a derivation", sentence)
        self.assertIn("The dictionary records no etymology for it", sentence)


class RulesFileTest(unittest.TestCase):
    def test_the_curated_rules_file_has_the_required_keys_and_distinctions(self):
        path = (Path(__file__).resolve().parents[1]
                / "data" / "compounds" / "fa.yaml")
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))

        for key in ("language", "label", "min_part", "min_word", "long_part",
                    "short_ok", "function_words", "function_pos", "stop"):
            self.assertIn(key, payload)
        self.assertEqual(payload["language"], "fa")
        self.assertEqual(payload["label"], "Persian")
        self.assertIn("آب", payload["short_ok"])
        self.assertNotIn("اب", payload["short_ok"])
        self.assertIn("اب", payload["stop"])
        self.assertEqual(set(payload["function_pos"]),
                         {"prep", "postp", "conj", "pron", "det", "part",
                          "interj", "num", "adv"})


if __name__ == "__main__":
    unittest.main()
