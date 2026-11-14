"""The Persian (pal → fa) laws and reading guard added on 2026-11-09.

Three claims are pinned:

* MP final *-ūg loses its *g in New Persian (hindūg > hindū, bānūg > bānū,
  anōš-dārūg > (a)nōš-dārū), while the same *-g stays after *ō (sōg > sōg) and
  after *ē (dēg > dēg).  The law is *ū-only for exactly that reason.
* MP final *-āg loses its *g and keeps the long vowel (dānāg > dānā), which is
  the other half of the *-ag ending and must not be folded into the short
  *-ag > -e class (murtag > murde).
* The reading guard compares segments, not alphabets: the dictionary's /j/ is
  the laws' y, its /ŋ/ is the laws' n, and its short vowels are not written by
  the Perso-Arabic abjad, so their number may not decide a spelling.
* The guard is still a guard: a genuinely wrong consonant still refuses.

The regression test measures the law against the transition with it switched
off, so it cannot be satisfied by another change.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

spec = importlib.util.spec_from_file_location("coverage_tool", ROOT / "tools" / "coverage.py")
coverage_tool = importlib.util.module_from_spec(spec)
sys.modules["coverage_tool"] = coverage_tool
spec.loader.exec_module(coverage_tool)

from pie import data, spelling             # noqa: E402
from pie.rules import derive               # noqa: E402

CHAIN = ["pal", "fa"]


def step(form: str, **kw) -> str:
    return derive(form, CHAIN, data.rulesets(), **kw).output


class FinalUg(unittest.TestCase):
    def test_long_u_g_is_lost(self):
        # i_to_e and long_o/u are this stage's own: the point is that the *g
        # is gone, and the vowel before it is the short e the script omits.
        self.assertEqual(step("hindūg"), "hendū")
        self.assertEqual(step("bānūg"), "bānū")
        self.assertEqual(step("anōš-dārūg"), "anūšdārū")

    def test_long_o_g_keeps_the_stop(self):
        self.assertEqual(step("sōg"), "sūg")     # NP sūg keeps the stop
        # mēnōg > mīnū is a real word this law deliberately leaves a miss:
        # the *ōg class is split (sōg keeps the stop) and is not claimed.
        self.assertEqual(step("mēnōg"), "mīnūg")

    def test_long_e_g_keeps_the_stop(self):
        self.assertEqual(step("dēg"), "dīg")     # NP dīg keeps the stop

    def test_the_spelling_follows(self):
        self.assertEqual(spelling.spell("hendū", "fa"), "هندو")
        self.assertEqual(spelling.spell("bānū", "fa"), "بانو")
        self.assertEqual(spelling.spell("anūšdārū", "fa"), "انوشدارو")

    def test_the_law_carries_words(self):
        rulesets = data.rulesets()
        off = {"final_ug_to_u"}
        chain = data.derivation_chain("fa")
        gained = []
        for entry in data.lexicon("fa"):
            target = entry["word"].strip()
            for stage, form in coverage_tool.ancestor_starts(entry, chain):
                on = derive(form, chain[chain.index(stage):], rulesets)
                if on.skipped:
                    continue
                if spelling.spell(on.output, "fa") == target and \
                        spelling.plausible(on.output, entry.get("ipa") or "", "fa") and \
                        any(s.rule_id == "final_ug_to_u" for s in on.steps):
                    gained.append(target)
                    break
        self.assertTrue(gained, "the law must carry at least one headword")
        # and it may not hide a word: dropping it cannot change a spelling
        for entry in data.lexicon("fa"):
            target = entry["word"].strip()
            for stage, form in coverage_tool.ancestor_starts(entry, chain):
                on = derive(form, chain[chain.index(stage):], rulesets)
                without = derive(form, chain[chain.index(stage):], rulesets, disabled=off)
                if on.skipped or without.skipped:
                    continue
                if spelling.spell(without.output, "fa") == target and not \
                        spelling.spell(on.output, "fa") == target:
                    self.fail(f"{target}: dropping the law is what spells it")
        self.assertIn("هندو", gained)
        self.assertIn("بانو", gained)


class FinalLongAg(unittest.TestCase):
    def test_long_a_g_keeps_its_long_vowel(self):
        self.assertEqual(step("dānāg"), "dānā")   # NP dānā 'wise'

    def test_short_a_g_stays_a_different_law(self):
        # the *-ag class is -e, and this law must not touch it
        self.assertEqual(step("murtag"), "morte")
        self.assertEqual(step("nāmag"), "nāme")
        # nor may it run on *-āg-like forms it was not given
        self.assertEqual(step("rag"), "re")

    def test_the_word_is_explained(self):
        out = step("dānāg")
        self.assertEqual(spelling.spell(out, "fa"), "دانا")

    def test_the_law_carries_words_and_hides_none(self):
        rulesets = data.rulesets()
        off = {"final_long_ag_to_a"}
        chain = data.derivation_chain("fa")
        gained, broken = [], []
        for entry in data.lexicon("fa"):
            target = entry["word"].strip()
            for stage, form in coverage_tool.ancestor_starts(entry, chain):
                on = derive(form, chain[chain.index(stage):], rulesets)
                if on.skipped:
                    continue
                without = derive(form, chain[chain.index(stage):], rulesets,
                                 disabled=off)
                if without.skipped:
                    continue
                hit_on = spelling.spell(on.output, "fa") == target
                hit_off = spelling.spell(without.output, "fa") == target
                if hit_on and not hit_off:
                    gained.append(target)
                elif hit_off and not hit_on:
                    broken.append(target)
                if hit_on or hit_off:
                    break
        self.assertIn("دانا", gained)
        self.assertEqual(broken, [], "the law may not hide a word that matched")


class ReadingGuard(unittest.TestCase):
    def test_j_is_the_laws_y(self):
        self.assertTrue(spelling.plausible("rūy", "/ˈroːj/", "fa"))
        self.assertTrue(spelling.plausible("yazdān", "/jaz.ˈdɒːn/", "fa"))

    def test_velar_nasal_is_the_laws_n(self):
        self.assertTrue(spelling.plausible("rang", "/ˈraŋɡ/", "fa"))

    def test_short_vowels_are_unwritten(self):
        # درخت is written d-r-x-t and read /da.ˈraxt/: the anaptyctic vowel is
        # a fact about pronunciation, not about the letters.
        self.assertTrue(spelling.plausible("draxt", "/da.ˈraxt/", "fa"))
        self.assertTrue(spelling.plausible("āfrīn", "/ʔaː.fa.ˈriːn/", "fa"))

    def test_long_vowels_are_still_compared(self):
        self.assertFalse(spelling.plausible("draxt", "/da.ˈraːxt/", "fa"))

    def test_a_wrong_consonant_is_still_refused(self):
        self.assertFalse(spelling.plausible("draxt", "/ba.ˈraxt/", "fa"))
        self.assertFalse(spelling.plausible("rūy", "/ˈroːn/", "fa"))

    def test_the_guard_does_not_rewrite_the_output(self):
        self.assertTrue(spelling.spell("rūy", "fa").startswith("روی"))
        self.assertEqual(spelling.spell("draxt", "fa"), "درخت")


if __name__ == "__main__":
    unittest.main()
