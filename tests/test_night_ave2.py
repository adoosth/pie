"""Avestan, night 0911: what the laws can and cannot reach (audit pins).

The session measured the Avestan side of the Iran chain and shipped no new law:
every candidate it wrote is phonologically defensible but gains no counted word
today, because the Avestan glossary is *cited by the stem* (aspa-, brātar-)
while the chain produces the nominative (aspō, brātā), and only 39 of its 352
entries carry an IPA string for the orthographic layer's plausibility guard.
The numbers and the losing lists are in proposals/night-0911/ave2/report.md.

These tests pin the invariants that made that verdict falsifiable:

* every law of `ira-pro -> ave` states its tier, cites a source that exists and
  re-derives every example through itself;
* the spelling layer stays a written convention (tier orthographic, never a
  sound law) and its examples round-trip through the Avestan writer;
* the four candidates kept in `proposals/night-0911/ave2/candidates/` parse, are
  cited, and **cost no counted word** — a candidate that started gaining would
  have to be promoted (and the report updated) rather than left in the drawer.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, spelling          # noqa: E402
from pie.phonology import detokenize, tokenize  # noqa: E402
from pie.rules import RuleSet, apply_ruleset  # noqa: E402
from whatif import exact_words          # noqa: E402

CHAIN = ["ine-pro", "iir-pro", "ira-pro", "ave"]
KEY = ("ira-pro", "ave")
CANDIDATES = ROOT / "proposals" / "night-0911" / "ave2" / "candidates"


def _aveset() -> RuleSet:
    return data.rulesets()[KEY]


class TestAvestanLawFile(unittest.TestCase):
    def test_every_law_states_a_tier_and_cites_a_known_source(self):
        known = data.sources()
        for rule in _aveset().rules:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.tier, {"established", "proposed", "custom"})
                self.assertTrue(rule.references, f"{rule.id}: no source")
                for ref in rule.references:
                    self.assertIn(ref, known, f"{rule.id}: unknown source {ref}")
                self.assertTrue((rule.notes or rule.name or "").strip(),
                                f"{rule.id}: no prose")

    def test_every_law_rederives_its_examples(self):
        single = type("RS", (), {"rules": [], "target_stage": ""})()
        for rule in _aveset().rules:
            single.rules = [rule]
            for ex in rule.examples:
                with self.subTest(rule=rule.id, form=ex.get("in")):
                    out, _steps = apply_ruleset(ex["in"], single, enabled=[rule.id])
                    expected = detokenize(tokenize(ex["out"]))
                    self.assertEqual(out, expected, f"{rule.id}: {ex['in']} -> {out}")


class TestAvestanSpellingStaysOrthographic(unittest.TestCase):
    def test_every_convention_is_orthographic(self):
        rs = spelling.ruleset("ave")
        self.assertTrue(rs.rules)
        for rule in rs.rules:
            self.assertEqual(rule.tier, "orthographic", rule.id)

    def test_no_avestan_sound_law_claims_the_orthographic_tier(self):
        # The rule is the programme's ("orthographic can never appear in
        # data/rules/").  Today one other transition breaks it (grc__el
        # ph_digraph), which is not this session's file to change; the Avestan
        # transition must not join it.
        for rule in data.rulesets()[KEY].rules:
            self.assertNotEqual(rule.tier, "orthographic", rule.id)

    def test_the_examples_are_written_by_the_layer(self):
        rs = spelling.ruleset("ave")
        for rule in rs.rules:
            for ex in rule.examples:
                with self.subTest(rule=rule.id, form=ex["in"]):
                    self.assertEqual(spelling.spell(ex["in"], "ave"), ex["out"])


class TestAvestanCandidatesCostNothing(unittest.TestCase):
    def _candidate(self, path: Path) -> RuleSet:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return RuleSet.from_dict(raw, *KEY)

    def test_each_candidate_is_cited_and_parses(self):
        known = data.sources()
        paths = sorted(CANDIDATES.glob("*.yaml"))
        self.assertEqual(len(paths), 4, "the report names exactly four candidates")
        for path in paths:
            cand = self._candidate(path)
            self.assertEqual(len(cand.rules), 1, path.name)
            rule = cand.rules[0]
            this_quote = f"{path.name}: tier"
            self.assertIn(rule.tier, {"proposed", "custom"}, this_quote)
            self.assertTrue(rule.references, f"{path.name}: no source")
            for ref in rule.references:
                self.assertIn(ref, known, f"{path.name}: unknown source {ref}")

    def test_no_candidate_loses_a_word_the_laws_explain(self):
        base = data.rulesets()
        before = set(exact_words("ave", CHAIN, base, None, 0,
                                 ("exact", "orthographic")))
        for path in sorted(CANDIDATES.glob("*.yaml")):
            cand = self._candidate(path)
            after_sets = dict(base)
            this = base[KEY]
            merged = RuleSet(this.source_stage, this.target_stage, list(this.rules), name=this.name)
            extra = [r for r in cand.rules if r.id not in {x.id for x in this.rules}]
            if not extra:
                continue                     # a file that *replaces* a law (ar_stem)
            merged.rules = sorted(this.rules + extra, key=lambda r: (r.order, r.id))
            after_sets[KEY] = merged
            after = set(exact_words("ave", CHAIN, after_sets, None, 0,
                                    ("exact", "orthographic")))
            with self.subTest(candidate=path.name):
                self.assertEqual(sorted(before - after), [],
                                 f"{path.name} loses words: promote or withdraw it")


if __name__ == "__main__":
    unittest.main()
