"""The labiovelar palatalisation (PIE -> PII) and the laryngeal before *t
(PII -> PIr), on the words they were measured against, plus the candidates
this session refused.

Every word is derived from its own recorded ancestor and compared with the
attested form character for character, the accent read either way as in the
counter (`stress_only`).  The rejected candidates are pinned so that a later
edit has to fail a test before it can ship one of them.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data                     # noqa: E402
from pie.rules import derive             # noqa: E402
from pie.service import stress_only      # noqa: E402

PI, PII, PIR = "ine-pro", "iir-pro", "ira-pro"

#: (PIE etymon, the recorded PII word, why it is here).  Each is a word the
#: transition missed before 2026-11-09 (proposals/night-0911/piir2/report.md).
PII_WORDS = [
    ("*kʷetwóres", "čatwā́ras", "*kʷ > *č before *e + *t"),
    ("*pékʷeti", "páčati", "the same law word-internally"),
    ("*kʷélh₁eti", "čárHati", "the same law before *e + *l"),
    ("*pénkʷe", "pánča", "*kʷ > *č before word-final *e"),
    ("*gʷʰénti", "ǰʰánti", "*gʷʰ > *ǰʰ before *e"),
    ("*dʰégʷʰeti", "dʰáǰʰati", "the same law after a vowel"),
]

#: PII etymon -> the recorded PIr word (the new PII -> PIr law).
PIR_WORDS = [
    ("*názdištHas", "názdištah", "the laryngeal between *t and a vowel is lost"),
    ("*káćištHas", "kácištah", "the same law, with the affricate retracted"),
    ("*bʰárȷ́ʰištHas", "bárjištah", "the same law, after deaspiration"),
]


def derive_to(form: str, target: str):
    chain = [PI, PII] if target == PII else [PII, PIR]
    return derive(form, chain, data.rulesets())


class TestLabiovelarPalatalisation(unittest.TestCase):
    def test_words_are_derived_from_their_ancestors(self):
        for form, word, why in PII_WORDS:
            with self.subTest(word=word):
                d = derive_to(form, PII)
                self.assertTrue(d.steps, f"{form}: no law fired")
                self.assertTrue(d.output == word or stress_only(d.output, word),
                                f"{form} -> {d.output}, recorded {word} ({why})")

    def test_the_law_names_the_labiovelar_not_the_plain_velar(self):
        # *ker "make" keeps its stop (Old Persian kāra-, Skt. karóti); the rule
        # runs before the merger and matches *kʷ, so *ker must be untouched.
        d = derive_to("*ker", PII)
        self.assertNotIn("labiovelar_k_palatal_e", [s.rule_id for s in d.steps])
        self.assertEqual(d.output, "kar")

    def test_r_and_y_block_the_palatalisation(self):
        # The two records that keep *k before *e: *kʷeys- (Skt. keśa-,
        # Middle Persian kēš) and *kʷer- (Avestan kar-).  Avestan kar- is a
        # script match the wider law cost, so this is a measured guard.
        self.assertEqual(derive_to("*kʷeys", PII).output, "kayš")
        self.assertEqual(derive_to("*kʷer", PII).output, "kar")

    def test_the_plain_voiced_labiovelar_is_not_claimed(self):
        # *gʷétu would palatalise, *gʷémtis keeps its *g (> gátiš): the corpus
        # disagrees with itself, so no *gʷ rule ships (candidates/).
        self.assertNotIn("labiovelar_g_palatal_e",
                         {r.id for r in data.rulesets()[(PI, PII)].rules})
        self.assertEqual(derive_to("*gʷémtis", PII).output, "gˈamtiš")

    def test_labiovelar_palatalisation_runs_before_the_merger(self):
        rules = {r.id: r for r in data.rulesets()[(PI, PII)].rules}
        for pid in ("labiovelar_k_palatal_e", "labiovelar_gh_palatal_e"):
            self.assertLess(rules[pid].order, rules["labiovelar_k"].order)
            self.assertLess(rules[pid].order, rules["vowel_merger_a"].order)
        self.assertLess(rules["labiovelar_k_palatal_e_final"].order,
                        rules["labiovelar_k"].order)

    def test_brugmann_lengthens_before_a_syllabic_resonant(self):
        # The narrowing to syllabic nasals was measured and refused: it gains
        # yákr̥, wásr̥ and ćákr̥, but it shortens the *ā of the Old Persian water
        # rung (*wódr̥ > *wādar, pinned by tests/test_web.py).
        self.assertTrue(stress_only(derive_to("*h₁nómn̥", PII).output, "Hnā́ma"))
        self.assertTrue(stress_only(derive_to("*wódr̥", PII).output, "wā́dr̥"))
        self.assertEqual(derive_to("*yókʷr̥", PII).output, "yˈākr̥")


class TestLaryngealAfterT(unittest.TestCase):
    def test_superlatives_lose_the_laryngeal(self):
        for form, word, why in PIR_WORDS:
            with self.subTest(word=word):
                d = derive_to(form, PIR)
                self.assertIn("laryngeal_after_t", [s.rule_id for s in d.steps])
                self.assertTrue(d.output == word or stress_only(d.output, word),
                                f"{form} -> {d.output}, recorded {word} ({why})")

    def test_a_word_final_laryngeal_is_kept(self):
        # *HástʰH > *HástH: the *H there is word-final, not between *t and a
        # vowel, so the law must not touch it.
        d = derive_to("*HástʰH", PIR)
        self.assertNotIn("laryngeal_after_t", [s.rule_id for s in d.steps])
        self.assertTrue(d.output.endswith("H"), d.output)

    def test_the_law_is_proposed_not_established(self):
        rules = {r.id: r for r in data.rulesets()[(PII, PIR)].rules}
        self.assertEqual(rules["laryngeal_after_t"].tier, "proposed")
        self.assertTrue(rules["laryngeal_after_t"].references)


class TestRefusedInThisSession(unittest.TestCase):
    def test_final_r_loss_is_still_refused(self):
        # +7 PII words and the *r of Persian pedār/mādar/dādār goes with it.
        self.assertNotIn("final_r_loss", {r.id for r in data.rulesets()[(PI, PII)].rules})

    def test_a_bare_geminate_simplification_is_not_a_law(self):
        # *kúttas > *kútah is one etymon: measured +1, below the three-etymon
        # bar (candidates/ira_tt_and_H.yaml).
        self.assertNotIn("geminate_tt", {r.id for r in data.rulesets()[(PII, PIR)].rules})
        self.assertTrue(stress_only(derive_to("*kúttas", PIR).output, "kˈuttah"))

    def test_palatalisation_before_e_without_the_environment_is_refused(self):
        # The two-segment environment is what keeps Avestan kar- and Middle
        # Persian kēš; the wide "before any *e" versions are in candidates/.
        rules = {r.id: r for r in data.rulesets()[(PI, PII)].rules}
        self.assertNotIn("e|", rules["labiovelar_k_palatal_e"].right or "")
        self.assertIn("STOP", rules["labiovelar_k_palatal_e"].right or "")


if __name__ == "__main__":
    unittest.main()
