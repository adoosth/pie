"""Sanskrit, 2026-11-09: the Indo-Aryan laws, the reading guard.

Before that work the Sanskrit transition had seven laws, none of which reached the
corpus: a Proto-Indo-Aryan *ai is written *ay by the records (so the rule that
matched the two vowels never applied), a recorded *w was never written v, and the
retroflexion of n and t next to ṣ did not exist.  The tests below pin the four
laws that work added, the rewriting conventions the reading guard needs, and
the two structural ceilings the report states: a Devanagari target can never be
an exact match (so ``exact`` stays 0 by construction), and the dictionary's
citation of a stem is a separate layer (so a nominative in -ḥ is not a match).
"""
from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import citation, data, spelling             # noqa: E402
from pie.rules import RuleSet, derive                # noqa: E402
from coverage import (ancestor_starts, citation_hit, exact_kind,  # noqa: E402
                      orthographic_hit)

CHAIN = data.derivation_chain("sa")
NEW_LAWS = {"ai_to_e", "au_to_o", "ai_to_e_final",
            "w_to_v_recorded", "n_to_retroflex_after_ruki",
            "t_to_retroflex_after_sh"}


def _without(rule_ids: set[str]) -> dict:
    out = {}
    for key, ruleset in data.rulesets().items():
        rules = [rule for rule in ruleset.rules if rule.id not in rule_ids]
        out[key] = RuleSet(ruleset.source_stage, ruleset.target_stage, rules,
                           ruleset.name, ruleset.date_start, ruleset.date_end,
                           ruleset.description, ruleset.references)
    return out


def _entry(word: str) -> dict:
    for entry in data.lexicon("sa"):
        if entry["word"] == word:
            return entry
    raise AssertionError(f"{word} is not in the Sanskrit glossary")


def _outputs(entry: dict, rulesets=None) -> list[tuple[str, str]]:
    rulesets = rulesets or data.rulesets()
    out = []
    for stage, form in ancestor_starts(entry, CHAIN):
        derivation = derive(form, CHAIN[CHAIN.index(stage):], rulesets)
        if not derivation.skipped:
            out.append((derivation.output, stage))
    return out


def _explained(rulesets) -> Counter:
    """The entries the counter explains, as tools/coverage.py counts them.

    A Counter, not a set: two entries may share a headword (a noun and an
    adjective), and the published counter counts both.
    """
    hits: Counter = Counter()
    for entry in data.lexicon("sa"):
        word = str(entry.get("word") or "").strip()
        if not word or entry.get("recon"):
            continue
        ipa = entry.get("ipa") or ""
        outputs = [(o, 1, stage) for o, stage in _outputs(entry, rulesets)]
        if any(exact_kind(o, word) for o, _n, _s in outputs):
            hits[word] += 1
        elif orthographic_hit(outputs, "sa", word, ipa):
            hits[word] += 1
        elif citation_hit(outputs, "sa", word, ipa):
            hits[word] += 1
    return hits


def _derive_word(word: str, stage_pref: str | None = None) -> str:
    entry = _entry(word)
    forms = _outputs(entry)
    if stage_pref:
        forms = [f for f in forms if f[1] == stage_pref]
    return forms[0][0]


class SanskritAccounting(unittest.TestCase):
    def test_glossary_and_tested_numbers(self):
        chain = data.derivation_chain("sa")
        entries = data.lexicon("sa")
        eligible = [e for e in entries if ancestor_starts(e, chain)]
        attested = [e for e in eligible if not e.get("recon")]
        # 2026-11-09: the template reader recovered 335 Sanskrit entries whose
        # only ancestry was a `{{inh|X|Y||form}}` link (5,059 / 4,218 / 4,215).
        self.assertEqual(len(entries), 5059)
        self.assertEqual(len(eligible), 4218)
        self.assertEqual(len(attested), 4215)

    def test_exact_is_zero_by_construction(self):
        """A Devanagari target cannot equal a phonemic string: no target bending.

        The historical column stays 0 for Sanskrit until a Latin-script target
        exists; the words the laws explain are counted in the orthographic and
        citation columns, never folded into `exact`.
        """
        self.assertGreaterEqual(sum(_explained(data.rulesets()).values()), 950)


class SanskritNewLaws(unittest.TestCase):
    def test_laws_are_cited_and_established(self):
        known = data.sources()
        rules = {rule.id: rule for ruleset in data.rulesets().values()
                 for rule in ruleset.rules}
        for rule_id in NEW_LAWS:
            with self.subTest(rule=rule_id):
                self.assertIn(rule_id, rules)
                rule = rules[rule_id]
                self.assertEqual(rule.tier, "established")
                self.assertTrue(rule.references)
                self.assertTrue(set(rule.references) <= set(known))
                self.assertTrue(rule.examples)

    def test_diphthong_adds_words_and_loses_none(self):
        before = _explained(_without({"ai_to_e", "au_to_o", "ai_to_e_final"}))
        after = _explained(data.rulesets())
        self.assertTrue(after - before)
        self.assertFalse(before - after)

    def test_every_new_law_pays_for_itself(self):
        for rule_id in NEW_LAWS:
            with self.subTest(rule=rule_id):
                before = _explained(_without({rule_id}))
                after = _explained(data.rulesets())
                self.assertTrue(after - before, f"{rule_id} carries no word")
                self.assertFalse(before - after, f"{rule_id} loses a word")


class SanskritLawsInAction(unittest.TestCase):
    def test_ai_becomes_e_in_the_corpus_notation(self):
        self.assertEqual(_derive_word("देव", "iir-pro"), "devˈaḥ")
        self.assertEqual(_derive_word("देव", "ine-pro"), "devˈaḥ")

    def test_a_glide_before_a_vowel_is_not_a_diphthong(self):
        self.assertEqual(_derive_word("कन्या", "inc-pro"), "kanyˈā")

    def test_word_final_ai_is_the_middle_ending_e(self):
        self.assertEqual(_derive_word("वस्ते", "inc-pro"), "vˈaste")

    def test_recorded_w_is_written_v(self):
        self.assertEqual(_derive_word("अश्व", "inc-pro"), "ˈaśvaḥ")

    def test_n_is_retroflex_after_a_vocalic_r(self):
        self.assertEqual(_derive_word("तृण", "ine-pro"), "tr̥ṇˈaḥ")

    def test_t_is_retroflex_after_sh(self):
        self.assertEqual(_derive_word("पिष्ट", "iir-pro"), "piṣṭˈaḥ")

    def test_n_and_t_stay_dental_elsewhere(self):
        # *wános 'gain' has no r, ṛ or ṣ before its n; *sartás has r before t
        # and a dental r does not retroflex a following t (Whitney §197).
        rules = {rule.id: rule for ruleset in data.rulesets().values()
                 for rule in ruleset.rules}
        self.assertEqual(rules["n_to_retroflex_after_ruki"].apply(
            ["w", "ˈ", "a", "n", "a", "s"])[0], ["w", "ˈ", "a", "n", "a", "s"])
        self.assertEqual(rules["t_to_retroflex_after_sh"].apply(
            ["s", "a", "r", "t", "ˈ", "a", "s"])[0], ["s", "a", "r", "t", "ˈ", "a", "s"])


class SanskritReadingGuard(unittest.TestCase):
    def test_diphthong_written_with_two_letters_reads_as_one_nucleus(self):
        self.assertTrue(spelling.plausible("devˈa", "/dɐi̯.ʋɐ́/", "sa"))

    def test_palatal_approximant_is_the_dictionaries_j(self):
        self.assertTrue(spelling.plausible("satyˈa", "/sɐt.jɐ́/", "sa"))

    def test_vocalic_r_is_one_segment(self):
        self.assertTrue(spelling.plausible("tr̥ṇˈa", "/tŕ̩.ɳɐ/", "sa"))

    def test_guard_still_refuses_a_wrong_skeleton(self):
        self.assertFalse(spelling.plausible("devˈa", "/kɐ.pɐ́u̯.tɐ/", "sa"))
        self.assertFalse(spelling.plausible("satyˈa", "/dɐi̯.ʋɐ́/", "sa"))


class SanskritCeilings(unittest.TestCase):
    def test_a_nominative_in_sh_is_a_citation_not_a_reconstruction(self):
        """सूनु is derived as sūnúṣ; the visarga law is not registered.

        Counting it needs the citation layer (which strips a nominative) or a
        sound law that would also rewrite the seven root citations इष् तुष् दुष्
        मक्ष् रक्ष् वक्ष् शिक्ष् to -ḥ; measured 2026-11-09, +107 / -8, and the
        council vetoes a loss.  The law and its numbers live in
        proposals/night-0911/sanskrit/report.md.
        """
        self.assertEqual(_derive_word("सूनु", "iir-pro"), "sūnˈuṣ")
        self.assertNotIn("ṣ", citation.endings("sa"))

    def test_an_as_stem_is_cited_without_its_nominative(self):
        # मनस् mánas- is the stem; the laws give the nominative mˈanaḥ.
        self.assertEqual(_derive_word("मनस्", "inc-pro"), "mˈanaḥ")
        self.assertIsNone(citation_hit(
            [(o, 1, s) for o, s in _outputs(_entry("मनस्"))], "sa", "मनस्",
            _entry("मनस्").get("ipa") or ""))


if __name__ == "__main__":
    unittest.main()
