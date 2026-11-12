"""Old Persian, 2026-11-09: accounting, ancestry repairs and two laws.

The counter's ``tested`` column is the **attested** words only: a Latin-title
row Wiktionary keeps in its Reconstruction namespace is measured in the
``reconstruction`` column instead.  The first test pins that accounting for
Old Persian, because "137 tested of 226 identified" is the definition and not
a lost link.  The rest pin what that work changed: four ancestry links the
entry's own etymology states, two proposed laws that carry words without
losing any, and the script gap the table now records.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, script                       # noqa: E402
from pie.rules import RuleSet, derive              # noqa: E402
from coverage import ancestor_starts               # noqa: E402


def _without(rule_ids: set[str]) -> dict:
    """The registered rulesets with some laws removed, for an ablation."""
    out = {}
    for key, ruleset in data.rulesets().items():
        rules = [rule for rule in ruleset.rules if rule.id not in rule_ids]
        out[key] = RuleSet(ruleset.source_stage, ruleset.target_stage, rules,
                           ruleset.name, ruleset.date_start, ruleset.date_end,
                           ruleset.description, ruleset.references)
    return out


def _script_hits(rulesets) -> set[tuple[str, str]]:
    chain = data.derivation_chain("peo")
    hits: set[tuple[str, str]] = set()
    for entry in data.lexicon("peo"):
        if entry.get("recon"):
            continue
        for stage, form in ancestor_starts(entry, chain):
            try:
                derivation = derive(form, chain[chain.index(stage):], rulesets)
            except Exception:
                continue
            if derivation.skipped:
                continue
            fit = script.match("peo", derivation.output, entry["word"])
            if derivation.steps and fit and fit["ok"]:
                hits.add((entry["word"], form))
                break
    return hits


def _exact_reconstructions(rulesets) -> set[str]:
    chain = data.derivation_chain("peo")
    hits: set[str] = set()
    for entry in data.lexicon("peo"):
        if not entry.get("recon"):
            continue
        for stage, form in ancestor_starts(entry, chain):
            try:
                derivation = derive(form, chain[chain.index(stage):], rulesets)
            except Exception:
                continue
            if derivation.skipped:
                continue
            if derivation.steps and derivation.output == entry["word"]:
                hits.add(entry["word"])
                break
    return hits


class PeoAccounting(unittest.TestCase):
    def test_tested_is_the_attested_share_of_identified(self):
        chain = data.derivation_chain("peo")
        eligible = [entry for entry in data.lexicon("peo") if ancestor_starts(entry, chain)]
        attested = [entry for entry in eligible if not entry.get("recon")]
        reconstruction = [entry for entry in eligible if entry.get("recon")]
        # 2026-11-09: every `{{inh|X|Y||form}}` link is read again, so one
        # more Old Persian reconstruction records an ancestor (226 / 137 / 89),
        # and later that day the lexicon stopped storing inflected forms and
        # began keeping the names Wiktionary builds from named pieces, which
        # hold no modelled ancestor (220 / 133 / 87).
        # 2026-11-12: the Old Persian lemma category was harvested (528 rows,
        # 55 new headwords), and the clean-up of dictionary brackets in the
        # readings moved the counts to 213 / 129 / 84 — seven words that used
        # to match an ancestor through a bracket no longer do, and three
        # reconstructions became words that state their own reading.  The full
        # re-read of the category also brought 𐎺𐏁𐎴𐎠 its three stated links:
        # 214 / 130 / 84.
        self.assertEqual(len(eligible), 214)
        self.assertEqual(len(attested), 130)
        self.assertEqual(len(reconstruction), 84)
        self.assertEqual(len(eligible), len(attested) + len(reconstruction))


class PeoAncestryRepair(unittest.TestCase):
    """The four links the entries' own etymology text states."""

    EXPECTED = {
        "𐎭𐎠𐎫𐎶": ("ira-pro", "dātam"),
        "baivaram": ("ira-pro", "baywáram"),
        "𐎰𐎵𐎢𐎺𐎴𐎡𐎹": ("iir-pro", "dʰánwr̥"),
        "𐎭𐎢𐏁𐎫𐎠": ("ira-pro", "jawštā́"),
    }

    def test_each_form_is_a_recorded_ancestor(self):
        rows = {entry["word"]: entry for entry in data.lexicon("peo")}
        for word, (stage, form) in self.EXPECTED.items():
            self.assertIn(word, rows)
            # A heteroclite is recorded with both stems (``*dʰánwr̥ ~
            # *dʰánwan-``); the first one is the form the derivation starts
            # from — ``service.normalise_etymon`` splits on the tilde — so the
            # test names the first stem and does not demand that the second one
            # be dropped from the record.
            triples = [(row[0], str(row[1]).lstrip("*").split("~", 1)[0].strip())
                       for row in rows[word].get("anc") or [] if isinstance(row, list)]
            self.assertIn((stage, form), triples, f"{word} lacks {stage} {form}")


class PeoNewLaws(unittest.TestCase):
    NEW = {"epenthetic_i_before_y", "long_vowel_contraction"}

    def test_laws_are_cited_proposed_rules(self):
        known = data.sources()
        rules = {rule.id: rule for ruleset in data.rulesets().values()
                 for rule in ruleset.rules}
        for rule_id in self.NEW:
            self.assertIn(rule_id, rules)
            self.assertEqual(rules[rule_id].tier, "proposed")
            self.assertTrue(rules[rule_id].references)
            self.assertTrue(set(rules[rule_id].references) <= set(known))
            self.assertTrue(rules[rule_id].examples)

    def test_script_gain_has_no_loss(self):
        before = _script_hits(_without(self.NEW))
        after = _script_hits(data.rulesets())
        gained = {(word, form) for word, form in after - before}
        self.assertEqual({word for word, _form in gained}, {"𐎠𐎴𐎡𐎹", "𐎠𐎼𐎡𐎹", "𐎶𐎼𐎫𐎡𐎹"})
        self.assertEqual(before - after, set())

    def test_reconstruction_gain_has_no_loss(self):
        before = _exact_reconstructions(_without(self.NEW))
        after = _exact_reconstructions(data.rulesets())
        self.assertEqual(after - before, {"fšupā", "gaupā"})
        self.assertEqual(before - after, set())


class PeoScriptGap(unittest.TestCase):
    def test_nasal_gap_is_recorded_and_not_forgiven(self):
        ids = {rule["id"]: rule for rule in script.conventions("peo")}
        self.assertIn("nasal_before_consonant", ids)
        self.assertEqual(ids["nasal_before_consonant"]["kind"], "unwritten")
        self.assertFalse(script.match("peo", "hˈinduš", "𐏃𐎡𐎯𐎢𐏁")["ok"])


if __name__ == "__main__":
    unittest.main()
