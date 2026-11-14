"""Lithuanian from Proto-Balto-Slavic: the last step of its chain.

The chain ``ine-pro → ine-bsl-pro → lt`` had no ``ine-bsl-pro → lt`` rule file,
so every one of the 1,057 tested entries was a miss by construction.  This file
pins ``data/rules/ine-bsl-pro__lt.yaml``: every law's tier and citation, the
examples ``check-rules`` verifies, and — most importantly — the forms the laws
must **not** touch.  The corpus numbers are a floor, not a target: the
Proto-Balto-Slavic transition and the lexicon above are shared and may move.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data                                   # noqa: E402
from pie.rules import apply_ruleset                    # noqa: E402
from pie.phonology import detokenize, tokenize         # noqa: E402
from coverage import ancestor_starts, exact_kind       # noqa: E402
from pie.rules import derive                           # noqa: E402

SRC, DST = "ine-bsl-pro", "lt"


def _ruleset():
    return data.rulesets()[(SRC, DST)]


def _run(form: str) -> str:
    out, _steps = apply_ruleset(form, _ruleset())
    return out


def _one(rule_id: str, form: str) -> str:
    rule = next(r for r in _ruleset().rules if r.id == rule_id)
    out, _steps = apply_ruleset(
        form, type("RS", (), {"rules": [rule], "target_stage": ""})(), enabled=[rule.id])
    return out


class LawSet(unittest.TestCase):
    def test_every_law_states_a_tier_and_a_known_source(self):
        known = set(data.sources())
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.tier, {"established", "proposed", "orthographic"})
                self.assertTrue(rule.references, "a law without a source is a guess")
                for ref in rule.references:
                    self.assertIn(ref, known)

    def test_every_law_has_a_verified_example(self):
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.examples)
                for ex in rule.examples:
                    self.assertEqual(_one(rule.id, ex["in"]),
                                     detokenize(tokenize(ex["out"])))

    def test_the_transition_exists_and_is_not_empty(self):
        self.assertIn((SRC, DST), data.rulesets())
        self.assertGreaterEqual(len(_ruleset().rules), 20)

    def test_the_notation_rules_carry_the_orthographic_tier(self):
        for rid in ("stress_token_dropped", "register_mark_dropped"):
            rule = next(r for r in _ruleset().rules if r.id == rid)
            self.assertEqual(rule.tier, "orthographic", rid)

    def test_the_core_laws_are_established(self):
        ids = {r.id: r.tier for r in _ruleset().rules}
        for rid in ("w_to_v", "s_caron_to_s", "z_caron_to_z", "long_a_to_o",
                    "long_a_to_a_final", "long_o_to_uo", "long_e_to_e_dot",
                    "long_i_to_y", "final_ei_to_i_after_t"):
            self.assertEqual(ids[rid], "established", rid)

    def test_the_two_hypotheses_are_marked_proposed(self):
        ids = {r.id: r.tier for r in _ruleset().rules}
        for rid in ("s_w_to_s", "final_an_to_as"):
            self.assertEqual(ids[rid], "proposed", rid)


class Vowels(unittest.TestCase):
    def test_a_becomes_o_and_final_a_stays(self):
        self.assertEqual(_run("bābā"), "boba")
        self.assertEqual(_run("kāwā"), "kova")
        self.assertEqual(_run("dainā"), "daina")

    def test_o_long_becomes_uo_not_o(self):
        self.assertEqual(_run("nō"), "nuo")
        self.assertEqual(_run("dṓnā"), "duona")
        self.assertEqual(_run("swesō"), "sesuo")

    def test_e_and_i_long(self):
        self.assertEqual(_run("bēgtei"), "bėgti")
        self.assertEqual(_run("pīsdā"), "pyzda")
        self.assertEqual(_run("wīras"), "vyras")

    def test_final_i_long_is_shortened_but_medial_i_long_is_y(self):
        self.assertEqual(_run("patī"), "pati")
        self.assertEqual(_run("wīras"), "vyras")

    def test_infinitive_ending(self):
        self.assertEqual(_run("bertei"), "berti")
        self.assertEqual(_run("būtei"), "būti")
        # Only after *t: *prei is not an infinitive and keeps its diphthong.
        self.assertEqual(_run("prei"), "prei")


class Consonants(unittest.TestCase):
    def test_w_becomes_v(self):
        self.assertEqual(_run("warnā"), "varna")
        self.assertEqual(_run("galwā"), "galva")

    def test_sibilants(self):
        self.assertEqual(_run("śeima"), "šeima")
        self.assertEqual(_run("maźas"), "mažas")

    def test_liquid_and_glide_clusters(self):
        self.assertEqual(_run("dáljā"), "dalia")
        self.assertEqual(_run("sjūtei"), "siūti")

    def test_tl_is_dissimilated_only_inside_a_stem(self):
        self.assertEqual(_run("tintlas"), "tinklas")
        self.assertEqual(_run("artlan"), "arklas")
        # *at-laikas is prefix + stem: the *t follows a vowel.
        self.assertEqual(_run("atlaikas"), "atlaikas")

    def test_s_voices_before_a_voiced_stop_only(self):
        self.assertEqual(_run("pīsdā"), "pyzda")
        self.assertEqual(_run("skystas"), "skystas")


class Nasals(unittest.TestCase):
    def test_nasal_vowels_before_s(self):
        self.assertEqual(_run("źansis"), "žąsis")
        self.assertEqual(_run("kanstei"), "kąsti")
        self.assertEqual(_run("sjunsti"), "siųsti")

    def test_nasal_stays_before_an_obstruent(self):
        self.assertEqual(_run("mandras"), "mandras")
        self.assertEqual(_run("rankā"), "ranka")

    def test_final_nasal(self):
        self.assertEqual(_run("in"), "į")
        self.assertEqual(_run("sam"), "są")


class NotTouched(unittest.TestCase):
    """A law that fires where it must not is worse than a missing law."""

    def test_no_eu_no_au(self):
        # tautā has au already; the *eu law must not see it.
        self.assertEqual(_run("tautā"), "tauta")

    def test_no_tl_after_a_vowel(self):
        self.assertEqual(_run("atlaikas"), "atlaikas")

    def test_final_an_is_rewritten_only_word_finally(self):
        # The law is the o-stem citation convention: it fires at the edge only.
        self.assertEqual(_run("ezeran"), "ezeras")
        self.assertEqual(_run("ezeranas"), "ezeranas")

    def test_a_short_vowel_is_never_lengthened(self):
        self.assertEqual(_run("kaklas"), "kaklas")
        self.assertEqual(_run("mandras"), "mandras")

    def test_an_acute_less_form_is_not_invented(self):
        # A form with no accent loses nothing: the notation rules do not fire.
        self.assertEqual(_run("wilkas"), "vilkas")


class Corpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chain = data.derivation_chain(DST)
        cls.rulesets = data.rulesets()
        cls.exact = 0
        cls.explained = 0
        for entry in data.lexicon(DST):
            if entry.get("recon"):
                continue
            target = entry["word"].strip()
            hit = False
            for stage, form in ancestor_starts(entry, cls.chain):
                d = derive(form, cls.chain[cls.chain.index(stage):], cls.rulesets)
                if d.skipped:
                    continue
                if d.steps and exact_kind(d.output, target):
                    cls.exact += 1
                    hit = True
                    break
            if hit:
                cls.explained += 1

    def test_the_laws_reproduce_a_real_share_of_the_corpus(self):
        # 246 entries (2026-11-09); the floor keeps a regression visible
        # without pinning the number to this lexicon snapshot.
        self.assertGreaterEqual(self.exact, 240)

    def test_nothing_outside_the_chain_is_claimed(self):
        self.assertEqual(self.chain, ["ine-pro", "ine-bsl-pro", "lt"])
        self.assertNotIn(("sla-pro", "lt"), self.rulesets)


if __name__ == "__main__":
    unittest.main()
