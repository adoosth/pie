"""The PIE -> Proto-Indo-Iranian laws, on the words they were measured against.

Every test derives the word from its own recorded PIE ancestor and compares the
result with the attested form character for character (the accent may be written
either way, as everywhere else in the counter).  Nothing here reads the answer:
the ancestor is typed in, the transition both children inherit is applied, and
the string is required to be the one the record keeps.

The three rejected candidates of 2026-11-09 are pinned too, because a law that
was measured and refused is a result: if any of them is ever switched on, one of
these tests has to fail first.
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

PI = "ine-pro"
PII = "iir-pro"

#: (PIE etymon, the recorded Proto-Indo-Iranian word, the law this word is here
#: for).  Each comes from a different etymon and each is a word the transition
#: missed before 2026-11-09 or that the change of order had to keep.
WORDS = [
    ("*gʷṓws", "gā́wš", "ruki retracts the *s after the *w of *gʷṓws"),
    ("*dyḗws", "dyā́wš", "the same law on *dyḗws"),
    ("*nisdós", "niždás", "*s voices before *d, then the ruki law voices it as *ž"),
    ("*mosgʰós", "mazgʰás", "*s voices before a voiced aspirate, outside the ruki set"),
    ("*h₂ówis", "Háwiš", "Brugmann's law does not lengthen *o before a following *i"),
    ("*pótis", "pátiš", "the same restriction on *pótis"),
    ("*kʷóti", "káti", "the same restriction on *kʷóti"),
    ("*h₂ŕ̥tḱos", "Hŕ̥ćšas", "*tḱ > *ćš"),
    ("*tḱéyti", "ćšáyti", "the same law on *tḱéyti"),
    ("*dr̥ḱtós", "dr̥štás", "the satem affricate becomes *š before a dental"),
    ("*kr̥snós", "kr̥šnás", "ruki after the syllabic *r̥"),
    ("*moysós", "mayšás", "ruki after the glide *y"),
    ("*bʰébʰrus", "bʰábʰruš", "PII keeps both aspirates: no Grassmann in this transition"),
    ("*dʰrówgʰos", "dʰráwgʰas", "the same, with a medial aspirate"),
]


def derive_pii(form: str):
    return derive(form, [PI, PII], data.rulesets())


class TestPiiWords(unittest.TestCase):
    def test_words_are_derived_from_pie(self):
        for form, word, why in WORDS:
            with self.subTest(word=word):
                d = derive_pii(form)
                self.assertTrue(d.steps, f"{form}: no law fired, so nothing was derived")
                self.assertTrue(d.output == word or stress_only(d.output, word),
                                f"{form} -> {d.output}, recorded {word} ({why})")

    def test_laws_and_not_lookups(self):
        # The same rules that explain the corpus must touch an unrelated word the
        # way the handbook describes, with no word-specific step in between.
        d = derive_pii("*bʰréh₂tēr")
        self.assertEqual([s.rule_id for s in d.steps][:3],
                         ["h2_colours_e", "laryngeal_to_H", "long_vowel_merger"])
        self.assertTrue(stress_only(d.output, "bʰráHtār"))


class TestOrdering(unittest.TestCase):
    def setUp(self):
        self.rules = {r.id: r for r in data.rulesets()[(PI, PII)].rules}

    def test_palatalisation_precedes_the_vowel_merger(self):
        # The *i/*y environment that ships must still be seen before the merger,
        # or a stressed *i would be the only one left (measured 2026-11-09: the
        # stress mark alone hid ǰíHwati and the other *i words).
        for pid in ("palatal_k", "palatal_g", "palatal_gh"):
            self.assertLess(self.rules[pid].order, self.rules["vowel_merger_a"].order)

    def test_the_palatalisation_environment_is_the_shipped_one(self):
        # *e is a proposal, not a shipped environment: the corpus keeps *k
        # before *e in *ker "make" (OP kāra-, Skt. karóti).
        for pid in ("palatal_k", "palatal_g", "palatal_gh"):
            right = self.rules[pid].right or ""
            self.assertIn("i", right)
            self.assertNotIn("e|", right)
        self.assertEqual(derive_pii("*ker").output, "kar")

    def test_labiovelars_merge_before_palatalisation(self):
        for lid in ("labiovelar_k", "labiovelar_g", "labiovelar_gh"):
            for pid in ("palatal_k", "palatal_g", "palatal_gh"):
                self.assertLess(self.rules[lid].order, self.rules[pid].order)

    def test_ruki_stays_after_the_voicing_of_s(self):
        self.assertLess(self.rules["s_voice"].order, self.rules["ruki_s"].order)
        self.assertLess(self.rules["ruki_s"].order, self.rules["z_ruki"].order)

    def test_every_rule_states_its_tier(self):
        raw = data._load_yaml(data.RULE_DIR / "ine-pro__iir-pro.yaml")
        for row in raw["rules"]:
            self.assertIn("tier", row, row.get("id"))
            self.assertTrue(row.get("references"), row.get("id"))


class TestRejectedCandidates(unittest.TestCase):
    """The laws measured and refused on 2026-11-09 (proposals/night-0911/pii)."""

    def setUp(self):
        self.rules = {r.id: r for r in data.rulesets()[(PI, PII)].rules}

    def test_grassmann_is_not_a_pii_law(self):
        # Dropping it gained 6 words and lost none: the corpus keeps both
        # aspirates (bʰábʰruš, dʰádʰaHti, dʰráwgʰas).
        self.assertNotIn("grassmann", self.rules)
        self.assertTrue(stress_only(derive_pii("*dʰédʰeh₁ti").output, "dʰádʰaHti"))

    def test_ruki_does_not_take_a_laryngeal(self):
        # ruki after *H gained 1 word and cost 5 (rejected).  A law may not
        # name a segment its own corpus shows outside the environment: *h₁ésmi
        # keeps its *s, and the *s after *H in *h₂wéh₁tis is retracted only
        # because the *H itself follows the *i.
        self.assertNotIn("H", self.rules["ruki_s"].left or "")
        self.assertEqual(derive_pii("*h₁ésmi").output, "Hˈasmi")

    def test_the_final_r_is_left_for_the_word_s_own_pathway(self):
        # A final *-r loss after *ā was measured (+7 PII words) and refused: it
        # removed the *r of Persian pedār, mādar and dādār, which the peo->pal
        # pathway law owns (proposals/night-0911/pii/report.md).
        self.assertNotIn("final_r_loss", self.rules)
        out = derive("*ph₂tḗr", ["ine-pro", "iir-pro", "ira-pro", "peo", "pal", "fa"],
                     data.rulesets()).output
        self.assertTrue(out.endswith("r"), out)

    def test_brugmann_still_fires_before_a_back_vowel(self):
        # The narrow environment must keep the words the law is for.
        for form, word in (("*ǵónu", "ȷ́ā́nu"), ("*dóru", "dā́ru")):
            with self.subTest(word=word):
                self.assertTrue(stress_only(derive_pii(form).output, word))


if __name__ == "__main__":
    unittest.main()
