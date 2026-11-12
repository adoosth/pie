"""The orthographic layer and the audit that feeds the worklist.

A spelling rule is not a sound law: these tests pin the separation (both
numbers are reported, neither is folded into the other), the file format, and
the read-only audit that turns misses into tasks.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import audit, data, service, spelling  # noqa: E402
from pie.worklist import render, run  # noqa: E402


class TestSpellingFiles(unittest.TestCase):
    def test_english_letters(self):
        self.assertEqual(spelling.spell("fˈūt", "en"), "fut")
        self.assertEqual(spelling.spell("kæt", "en"), "cat")
        self.assertEqual(spelling.spell("bæk", "en"), "back")
        self.assertEqual(spelling.spell("hæppi", "en"), "happy")

    def test_german_letters(self):
        self.assertEqual(spelling.spell("tsait", "de"), "zeit")
        self.assertEqual(spelling.spell("klēben", "de"), "kleben")
        self.assertEqual(spelling.spell("bax", "de"), "bach")
        self.assertEqual(spelling.spell("dī", "de"), "die")

    def test_identity_without_a_file(self):
        self.assertEqual(spelling.spell("nókʷts", "ine-pro"), "nókʷts")
        self.assertFalse(spelling.applies("ine-pro"))

    def test_every_file_validates(self):
        for lang in spelling.available():
            self.assertEqual(spelling.check(spelling.ruleset(lang)), [], lang)

    def test_spelling_tier_is_its_own(self):
        for lang in spelling.available():
            for rule in spelling.ruleset(lang).rules:
                self.assertEqual(rule.tier, "orthographic",
                                 f"{lang}/{rule.id} carries a historical tier")
                self.assertTrue(rule.references, f"{lang}/{rule.id} cites nothing")

    def test_the_plausibility_guard(self):
        # A letter table must not turn wrong phonemes into a "spelling match".
        self.assertTrue(spelling.plausible("bɔɔk", "/bʊk/"))
        self.assertTrue(spelling.plausible("pɔnd", "/pɒnd/"))
        self.assertFalse(spelling.plausible("æʌnt", "/ɑːnt/"))
        self.assertFalse(spelling.plausible("liqʌid", "/ˈlɪkwɪd/"))
        self.assertFalse(spelling.plausible("bɔɔk", ""))

    def test_the_guard_reads_ipa_notation_not_its_letter_choice(self):
        # Two code points for one letter, one phoneme behind several rhotic
        # letters, and marks that carry no segment must not decide the count.
        self.assertTrue(spelling.plausible("ɡod", "/ɡod/"))
        self.assertTrue(spelling.plausible("god", "/ɡod/"))
        self.assertTrue(spelling.plausible("drai", "/dʁaɪ̯/"))
        self.assertTrue(spelling.plausible("bitten", "/ˈbɪtn̩/"))
        self.assertTrue(spelling.plausible("oːde", "/ˈʔøːdə/"))
        # … but the notation fold may not rescue a wrong consonant skeleton.
        self.assertFalse(spelling.plausible("hant", "/kant/"))

    def test_a_broken_example_is_reported(self):
        rs = spelling.ruleset("en")
        bad = rs.rules[0]
        original = list(bad.examples)
        bad.examples = [{"in": "kæt", "out": "not-a-word"}]
        try:
            self.assertTrue(spelling.check(rs))
        finally:
            bad.examples = original


class TestServiceLayer(unittest.TestCase):
    def test_written_form_is_exposed_only_when_it_lands(self):
        h = service.hierarchy("en", "pond")
        result = h["result"]
        self.assertFalse(result["match"])
        self.assertTrue(result["written_match"])
        self.assertEqual(result["written"], "pond")

    def test_no_written_claim_without_a_match(self):
        h = service.hierarchy("de", "Haus")
        self.assertIsNone(h["result"]["written"])

    def test_no_written_claim_from_wrong_phonemes(self):
        # The spelling table could concatenate to "aunt" from /æʌnt/, but the
        # phonemes are not the word's, so nothing may be shown or counted.
        h = service.hierarchy("en", "aunt")
        self.assertIsNone(h["result"]["written"])


class TestAudit(unittest.TestCase):
    def test_edit_script_and_signature(self):
        self.assertEqual(audit.edit_ops("cat", "cat"), ())
        self.assertEqual(audit.edit_signature(audit.edit_ops("cæt", "cat")), "æ→a")
        self.assertEqual(audit.edit_signature(audit.edit_ops("the", "th")), "−e")

    def test_classification(self):
        self.assertEqual(audit.classify(audit.edit_ops("cæt", "cat"), "en"), "spelling")
        self.assertEqual(audit.classify(audit.edit_ops("kæt", "kæt"), "en"), "unchanged")
        self.assertEqual(audit.classify(audit.edit_ops("haus", "Haus"), "de"), "case")
        self.assertEqual(audit.classify(audit.edit_ops("fˈuːt", "fuːt"), "en"), "stress")
        self.assertEqual(audit.classify(audit.edit_ops("wɔrd", "word"), "en"), "spelling")
        # A real sound change stays with the phonology.
        self.assertEqual(audit.classify(audit.edit_ops("pedar", "pitar"), "fa"), "phonology")

    def test_language_report_shape(self):
        rep = audit.audit_language("en", limit=400)
        for key in ("exact", "near", "spelling_probe", "signatures", "silent", "rule_fired"):
            self.assertIn(key, rep)
        self.assertGreater(rep["tested"], 0)
        sigs = {s["signature"] for s in rep["signatures"]}
        self.assertTrue(sigs)


class TestWorklist(unittest.TestCase):
    def test_render_has_the_sections(self):
        report = run(60, ["en", "de"])
        text = render(report)
        for heading in ("# Worklist", "## 1 · Miss signatures", "## 3 · Structural gaps",
                        "## 4 · Rule hygiene", "## 6 · Suggested next tasks"):
            self.assertIn(heading, text)
        self.assertIn("en", text)


class TestCoverageSeparation(unittest.TestCase):
    def test_coverage_payload_keeps_the_two_numbers_apart(self):
        rep = data.DATA / "coverage.json"
        if not rep.exists():
            self.skipTest("coverage.json not generated")
        import json
        cov = json.loads(rep.read_text(encoding="utf-8"))
        en = cov["languages"]["en"]
        self.assertIn("orthographic", en)
        self.assertEqual(en["exact_orth"], en["exact"] + en["orthographic"])
        self.assertLessEqual(en["exact"], en["exact_orth"])


if __name__ == "__main__":
    unittest.main()
