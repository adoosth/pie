"""Building a form at a stage, on the timeline (2026-11-10).

The ladder must allow what a language actually does: at any
stage, two of its words may be joined, or one of its suffixes or endings added,
and the timeline must show that as a step.  These tests pin the contract:

* the address carries the question (`?build=fa:join:خانه@آب`);
* the composed rung says it was **built**, and the step says what was added;
* a composition is never a sound law: a word whose composed form equals its
  record is a `match` about the *form*, and no band is rewritten by it;
* nothing is invented — an affix has to be one the stage records, and a join
  of a word the stage does not hold still runs, but says the piece is unknown.
"""
from __future__ import annotations

import unittest

from pie import service


class ParseBuild(unittest.TestCase):
    def test_three_parts(self):
        spec = service._parse_build("fa:join:خانه@آب")
        self.assertEqual(spec["stage"], "fa")
        self.assertEqual(spec["kind"], "join")
        self.assertEqual(spec["arg"], "خانه")
        self.assertEqual(spec["base"], "آب")

    def test_without_base(self):
        spec = service._parse_build("ine-pro:suffix:eh2")
        self.assertEqual((spec["stage"], spec["kind"], spec["arg"], spec["base"]),
                         ("ine-pro", "suffix", "eh2", ""))

    def test_refusals(self):
        for bad in ("", "fa", "fa:join", "fa:nonsense:x", "xx:join:a", None):
            self.assertIsNone(service._parse_build(bad), bad)


class Compose(unittest.TestCase):
    def test_compound_is_written_with_the_stages_own_seam(self):
        made = service._compose_build(
            {"kind": "join", "arg": "خانه"}, "آب", "fa")
        self.assertEqual(made["form"].replace("\u200c", ""), "آبخانه")
        self.assertEqual(made["kind"], "compound")
        self.assertEqual([p["form"] for p in made["pieces"]], ["آب", "خانه"])
        self.assertTrue(all(p["known"] for p in made["pieces"]))

    def test_suffix_is_the_registered_one(self):
        made = service._compose_build({"kind": "suffix", "arg": "ka-animal"},
                                      "h₂wl̥pís", "ine-pro")
        self.assertTrue(made["form"].startswith("h₂wl̥p"))
        self.assertEqual(made["pieces"][1]["pos"], "suffix")
        self.assertIn("law", made)      # the cited formation law, not a guess

    def test_unknown_suffix_is_refused(self):
        self.assertIsNone(service._compose_build(
            {"kind": "suffix", "arg": "no-such-suffix"}, "h₂wl̥pís", "ine-pro"))

    def test_ending_replaces_the_word_final(self):
        made = service._compose_build({"kind": "ending", "arg": "-éh₁"},
                                      "h₂ŕ̥tḱos", "ine-pro")
        self.assertIsNotNone(made)
        self.assertTrue(made["form"].endswith("éh₁"))
        self.assertFalse(made["form"].endswith("os"))


class Ladder(unittest.TestCase):
    def test_a_join_lands_on_the_recorded_word(self):
        h = service.hierarchy("fa", "آب‌خانه", build="fa:join:خانه@آب")
        self.assertIsNotNone(h)
        stages = [(row["stage"], row["form"]) for row in h["levels"]]
        self.assertEqual(stages[0], ("fa", "آب"))
        self.assertEqual(h["levels"][1]["status"], "match")
        self.assertTrue(h["levels"][1]["built"])
        self.assertEqual(h["build"]["kind"], "compound")
        # The record is the dictionary's own headword, without the seam.
        self.assertEqual((h["levels"][1]["recorded"] or {}).get("w"), "آبخانه")

    def test_a_built_rung_does_not_rewrite_the_band(self):
        h = service.hierarchy("fa", "آب‌خانه", build="fa:join:خانه@آب")
        self.assertIsNone(h["category"])

    def test_suffix_at_the_words_own_stage_is_written(self):
        h = service.hierarchy("fa", "دست", build="fa:suffix:i")
        last = h["levels"][-1]
        self.assertEqual(last["form"], "دستی")     # script, not dast + ی
        self.assertEqual(last["status"], "match")
        self.assertEqual(h["build"]["stage"], "fa")

    def test_a_form_with_no_ancestry_still_has_a_timeline(self):
        h = service.hierarchy("fa", "آب‌خانه")
        self.assertIsNotNone(h)
        self.assertEqual(len(h["levels"]), 1)
        self.assertEqual(h["levels"][0]["status"], "start")

    def test_build_options_come_from_the_stage(self):
        fa = service.build_options("fa")
        self.assertTrue(any(s["id"] == "i" for s in fa["suffixes"]))
        self.assertTrue(fa["joining"]["zwnj"])
        pie = service.build_options("ine-pro")
        self.assertTrue(pie["suffixes"])
        self.assertTrue(any(e["form"] for e in pie["endings"]))


if __name__ == "__main__":
    unittest.main()
