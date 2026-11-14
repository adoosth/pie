"""Latin from Proto-Italic: the laws added on 2026-11-09, and what must not apply.

The transition carried ten laws and produced 7 exact / 68 explained words from
3,267 tested entries.  The miss list showed that most of the gap was not
irregularity but two things a law file can state: the regular Proto-Italic →
Latin changes that were missing (final *-o before *-s and *-m, final *-ā, the
spirants *β *ð *ɣ, *j, *ei, *-āō, *-nts, *-d) and two environments that were
too broad (medial weakening fired on the first syllable, and final *-s was
rhotacised without regard to length or syllable count).

These tests pin the laws that carry the gain and, just as importantly, the
words a law must **not** touch.  The corpus numbers are a floor, not a target:
upstream transitions may move independently.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling                     # noqa: E402
from pie.rules import apply_ruleset, derive        # noqa: E402
from pie.phonology import detokenize, tokenize     # noqa: E402
from coverage import ancestor_starts, exact_kind   # noqa: E402

SRC, DST = "itc-pro", "la"


def _ruleset():
    return data.rulesets()[(SRC, DST)]


def _norm(form: str) -> str:
    return detokenize(tokenize(form.replace("*", "")))


def _run(form: str) -> str:
    out, _steps = apply_ruleset(form, _ruleset())
    return out


def _entry(word: str) -> dict:
    for entry in data.lexicon(DST):
        if entry["word"] == word:
            return entry
    raise AssertionError(f"{word} is not in the Latin glossary")


class LatinLawSet(unittest.TestCase):
    def test_every_law_has_a_tier_and_a_known_citation(self):
        known = set(data.sources())
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.tier, {"established", "proposed", "custom"})
                self.assertTrue(rule.references, "a law without a source is a guess")
                for ref in rule.references:
                    self.assertIn(ref, known)

    def test_examples_apply(self):
        for rule in _ruleset().rules:
            for example in rule.examples:
                with self.subTest(rule=rule.id, form=example["in"]):
                    out, changed = apply_ruleset(example["in"],
                                                 _rule_only(rule.id))
                    self.assertTrue(changed, "the example must make the law fire")
                    self.assertEqual(_norm(out), _norm(example["out"]))


def _rule_only(rule_id: str):
    from pie.rules import RuleSet
    rs = _ruleset()
    rules = [r for r in rs.rules if r.id == rule_id]
    return RuleSet(rs.source_stage, rs.target_stage, rules,
                   rs.name, rs.date_start, rs.date_end, rs.description,
                   rs.references)


class LatinChanges(unittest.TestCase):
    def test_final_o_raisings(self):
        self.assertEqual(_run("*serwos"), "serwus")
        self.assertEqual(_run("*argentom"), "argentum")
        self.assertEqual(_run("*aljos"), "alius")
        self.assertEqual(_run("*labjom"), "labium")

    def test_final_long_a(self):
        self.assertEqual(_run("*fugā"), "fuga")
        self.assertEqual(_run("*portā"), "porta")

    def test_laryngeal_spirants_become_stops(self):
        self.assertEqual(_run("*luβros"), "lubrus")
        self.assertEqual(_run("*sweðēō"), "swedēō")
        self.assertEqual(_run("*weɣō"), "wegō")

    def test_j_vocalises(self):
        self.assertEqual(_run("*fakjō"), "fakiō")
        self.assertEqual(_run("*kapjō"), "kapiō")

    def test_monophthongs(self):
        self.assertEqual(_run("*oinos"), "ūnus")
        self.assertEqual(_run("*deikō"), "dīkō")
        self.assertEqual(_run("*prai"), "prae")
        self.assertEqual(_run("*kʷoi"), "kʷī")
        self.assertEqual(_run("*nei"), "nī")

    def test_first_person_contraction(self):
        self.assertEqual(_run("*portāō"), "portō")

    def test_nts_and_final_t(self):
        self.assertEqual(_run("*ponts"), "pōns")
        self.assertEqual(_run("*pets"), "pes")
        self.assertEqual(_run("*anats"), "anas")

    def test_final_d(self):
        self.assertEqual(_run("*ted"), "tē")

    def test_rhotacism_of_final_s(self):
        self.assertEqual(_run("*kelōs"), "kolōr")
        self.assertEqual(_run("*honōs"), "honōr")


class LatinMustNotOverapply(unittest.TestCase):
    def test_medial_weakening_does_not_touch_the_first_syllable(self):
        self.assertEqual(_run("*ferō"), "ferō")
        self.assertEqual(_run("*legō"), "legō")

    def test_final_d_is_kept_after_a_short_vowel(self):
        self.assertEqual(_run("*ad"), "ad")

    def test_monosyllables_keep_final_s(self):
        self.assertEqual(_run("*flōs"), "flōs")
        self.assertEqual(_run("*mōs"), "mōs")
        self.assertEqual(_run("*rēs"), "rēs")

    def test_final_short_i_does_not_rhotacise(self):
        self.assertEqual(_run("*similis"), "similis")

    def test_o_is_not_raised_before_l_and_a_vowel(self):
        self.assertEqual(_run("*domos"), "domus")   # only the final -os raises
        self.assertEqual(_run("*welō"), "wolō")     # *e > o before dark *l only

    def test_e_to_o_does_not_touch_a_short_l_vowel(self):
        self.assertEqual(_run("*preslom"), "prelum")

    def test_oi_is_not_u_word_finally(self):
        self.assertEqual(_run("*kʷoi"), "kʷī")


class LatinCorpus(unittest.TestCase):
    def test_words_explained_from_a_proto_italic_ancestor(self):
        """A floor from the itc-pro ancestors only, independent of upstream."""
        chain = data.derivation_chain(DST)
        rs = data.rulesets()
        explained = 0
        for entry in data.lexicon(DST):
            word = str(entry.get("word") or "").strip()
            if not word or entry.get("recon"):
                continue
            for stage, form in ancestor_starts(entry, chain):
                if stage != SRC:
                    continue
                d = derive(form, [SRC, DST], rs)
                if not d.steps:
                    continue
                if exact_kind(d.output, word) or (
                        spelling.spell(d.output, DST) == word
                        and spelling.plausible(d.output, entry.get("ipa") or "", DST)):
                    explained += 1
                    break
        self.assertGreaterEqual(explained, 250)

    def test_a_known_word_end_to_end(self):
        entry = _entry("servus")
        # The dictionary form is a written form; the laws give the phonemic
        # form and the spelling layer writes it.
        form = [f for s, f in ancestor_starts(entry, data.derivation_chain(DST))
                if s == SRC][0]
        d = derive(form, [SRC, DST], data.rulesets())
        self.assertEqual(d.output, "serwus")
        self.assertEqual(spelling.spell(d.output, DST), "servus")


if __name__ == "__main__":
    unittest.main()
