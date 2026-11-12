"""Unit tests for the phonology model, the rule engine and the data files."""
from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from pie import data, service, textio  # noqa: E402
from pie.phonology import detokenize, tags, tokenize  # noqa: E402
from pie.rules import Rule, apply_ruleset, derive  # noqa: E402


def bare(form: str) -> str:
    return detokenize([t for t in tokenize(form) if t not in {"ˈ", "ˌ"}])


class TestTokenize(unittest.TestCase):
    def test_multichar_segments(self):
        self.assertEqual(tokenize("*kʷʰel-"), ["kʷʰ", "e", "l"])
        self.assertEqual(tokenize("ph₂tḗr"), ["p", "h₂", "t", "ˈ", "ē", "r"])

    def test_syllabic_resonants(self):
        self.assertIn("SYL", tags("m̥"))
        self.assertIn("V", tags("r̥"))

    def test_palatals_are_not_velars(self):
        self.assertIn("PALATAL", tags("ḱ"))
        self.assertNotIn("VEL", tags("ḱ"))


class TestPatterns(unittest.TestCase):
    def _rule(self, **kw) -> Rule:
        base = dict(id="t", name="t", order=1, source="a", change="", source_stage="a", target_stage="b")
        base.update(kw)
        return Rule(**base).compile()

    def test_word_edge(self):
        r = self._rule(match="p", replace="f", left="#")
        self.assertEqual(r.apply(["p", "a"])[0], ["f", "a"])
        self.assertEqual(r.apply(["s", "p", "a"])[0], ["s", "p", "a"])

    def test_class_context(self):
        r = self._rule(match="s", replace="z", left="V", right="V")
        self.assertEqual(r.apply(["a", "s", "a"])[0], ["a", "z", "a"])
        self.assertEqual(r.apply(["s", "a"])[0], ["s", "a"])

    def test_optional_atom(self):
        r = self._rule(match="a", replace="e", right="C? i")
        self.assertEqual(r.apply(["a", "i"])[0][0], "e")
        self.assertEqual(r.apply(["a", "t", "i"])[0][0], "e")
        self.assertEqual(r.apply(["a", "t", "a"])[0][0], "a")


class TestVerner(unittest.TestCase):
    def test_accent_condition(self):
        rs = data.rulesets()[("ine-pro", "gem-pro")]
        verner = [r for r in rs.rules if r.id == "verner_th"]
        if not verner:
            self.skipTest("no Verner rule")
        r = verner[0]
        self.assertEqual(r.apply(["p", "a", "θ", "ˈ", "ē", "r"])[0][2], "ð")
        self.assertEqual(r.apply(["ˈ", "p", "a", "θ", "ē", "r"])[0][3], "θ")


class TestData(unittest.TestCase):
    def test_every_language_has_a_name(self):
        for lang, row in data.languages().items():
            self.assertTrue(row.get("name"), lang)

    def test_ancestors_exist(self):
        langs = data.languages()
        for lang, row in langs.items():
            anc = row.get("ancestor")
            if anc:
                self.assertIn(anc, langs, f"{lang} → missing ancestor {anc}")

    def test_rule_ids_unique_and_sources_known(self):
        sources = data.sources()
        for (src, dst), rs in data.rulesets().items():
            seen = set()
            for r in rs.rules:
                self.assertNotIn(r.id, seen, f"duplicate rule id {r.id} in {src}__{dst}")
                seen.add(r.id)
                for ref in r.references:
                    self.assertIn(ref, sources, f"unknown source {ref} in {r.id}")

    def test_rule_examples(self):
        for (src, dst), rs in data.rulesets().items():
            for r in rs.rules:
                for ex in r.examples:
                    # A rule registered off by default (the animal suffix *-ka-)
                    # is switched on for its own example.
                    got = apply_ruleset(ex["in"], type("RS", (), {"rules": [r], "target_stage": ""})(),
                                        enabled=[r.id])[0]
                    self.assertEqual(bare(got), bare(ex["out"]), f"{src}__{dst} {r.id}: {ex}")

    def test_curated_etymologies(self):
        path = ROOT / "tests" / "etymologies.yaml"
        if not path.exists():
            self.skipTest("no curated etymologies")
        rs = data.rulesets()
        with path.open(encoding="utf-8") as fh:
            cases = yaml.safe_load(fh)
        for case in cases:
            chain = case["chain"]
            if any((a, b) not in rs for a, b in zip(chain, chain[1:])):
                continue
            got = derive(case["pie"], chain, rs).output
            if case.get("known_gap"):
                continue
            self.assertEqual(bare(got), bare(case["expect"]),
                             f"{case['pie']} → {got} (expected {case['expect']})")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestCoverageReport(unittest.TestCase):
    def test_report_totals_and_rates_are_consistent(self):
        path = ROOT / "data" / "coverage.json"
        if not path.exists():
            self.skipTest("coverage report not generated")
        report = json.loads(path.read_text(encoding="utf-8"))
        langs = report["languages"]
        totals = report["totals"]
        self.assertEqual(totals["glossary"], sum(r["glossary"] for r in langs.values()))
        self.assertEqual(totals["exact"], sum(r["exact"] for r in langs.values()))
        for lang, row in langs.items():
            self.assertLessEqual(row["exact"], row["glossary"], lang)
            self.assertLessEqual(row["identified"], row["glossary"], lang)
            self.assertLessEqual(row["pie_linked"], row["glossary"], lang)
            self.assertLessEqual(row["exact"], row["identified"], lang)
            expected = row["exact"] / row["glossary"] if row["glossary"] else 0
            self.assertAlmostEqual(row["exact_rate"], expected, places=6, msg=lang)


class TestWordPageDerivation(unittest.TestCase):
    """A word page explains a word from the best ancestor, per the project rule."""

    def test_inheritance_shorthand_is_expanded(self):
        entry = {"anc": [[":inh", "ine-pro:*ḱwṓ", "root"], ["la", "canis", "inherit"]]}
        self.assertEqual(
            service._ancestry_triples(entry),
            [("ine-pro", "*ḱwṓ", "inherit"), ("la", "canis", "inherit")],
        )

    def test_exact_ancestor_is_preferred(self):
        row = service.word("it", "cane")
        self.assertIsNotNone(row)
        self.assertTrue(row["derivation"]["match"])
        self.assertEqual(row["derivation"]["start"], "la")
        self.assertEqual(row["derivation"]["chain"][0]["id"], "la")

    def test_falls_back_to_the_pie_path(self):
        row = service.word("en", "foot")
        self.assertIsNotNone(row)
        derivation = row["derivation"]
        self.assertFalse(derivation["match"])
        self.assertEqual(derivation["start"], "ine-pro")
        self.assertEqual(derivation["forms"][-1], "fˈūt")


class TestWolfAssimilation(unittest.TestCase):
    """*wĺ̥kʷos > *wulfaz: the one cited case of *kʷ > *p, registered as proposed.

    2026-11-08: the engine gave *wulhwaz for Proto-Germanic, and the
    literature has *wulfaz.  The regular Grimm outcome really is *wulhwaz —
    Wiktionary's *wulfaz entry says so outright — and the recorded form rests
    on a sporadic pre-Germanic assimilation (EDPG s.v. *wulfa-).
    """

    def test_the_regular_laws_alone_give_wulhwaz(self):
        d = derive("wĺ̥kʷos", ["ine-pro", "gem-pro"], data.rulesets(),
                   disabled=["ine-pro~gem-pro:lkw_to_lp"])
        self.assertEqual(bare(d.output), "wulhwaz")

    def test_the_assimilation_reaches_the_recorded_form(self):
        d = derive("wĺ̥kʷos", ["ine-pro", "gem-pro"], data.rulesets())
        self.assertEqual(bare(d.output), "wulfaz")
        self.assertEqual([s.rule_id for s in d.steps],
                         ["syllabic_l", "lkw_to_lp", "grimm_p", "verner_s", "o_to_a"])

    def test_the_change_is_cited_and_never_established(self):
        ruleset = data.rulesets()[("ine-pro", "gem-pro")]
        rule = next(r for r in ruleset.rules if r.id == "lkw_to_lp")
        self.assertEqual(rule.tier, "proposed",
                         "a sporadic change may not claim the status of a regular law")
        self.assertIn("kroonen-2013", rule.references)
        self.assertEqual(rule.examples[0]["out"], "*wúlpos")


class TestPortability(unittest.TestCase):
    """Windows defaults to cp1252, whose table has no 0x8d (the ō of *fōt) or 0x81."""

    OPENERS = {"open", "read_text", "write_text"}

    @staticmethod
    def _calls(path: Path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name in TestPortability.OPENERS:
                    yield node, name

    @staticmethod
    def _mode(node: ast.Call, name: str) -> str:
        if name != "open":
            return "r"
        mode = None
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if mode is None:
            # Path.open("wb") puts the mode first; builtin open(path, "wb") second.
            first = 0 if isinstance(node.func, ast.Attribute) else 1
            if len(node.args) > first and isinstance(node.args[first], ast.Constant):
                mode = node.args[first].value
        return mode or "r"

    def test_text_io_always_names_utf8(self):
        for folder in ("src", "tools"):
            for path in (ROOT / folder).rglob("*.py"):
                for node, name in self._calls(path):
                    if name == "open" and "b" in self._mode(node, name):
                        continue
                    if any(kw.arg == "encoding" for kw in node.keywords):
                        continue
                    self.fail(f"{path.relative_to(ROOT)}:{node.lineno}: {name}() without encoding='utf-8'")

    def test_stdio_upgrade_leaves_utf8_alone(self):
        class Stream:
            def __init__(self, encoding: str):
                self.encoding = encoding
                self.kwargs = None

            def reconfigure(self, **kwargs):
                self.kwargs = kwargs

        legacy = Stream("cp1252")
        textio._upgrade(legacy)
        self.assertEqual(legacy.kwargs["encoding"], "utf-8")

        modern = Stream("utf-8")
        textio._upgrade(modern)
        self.assertIsNone(modern.kwargs)
