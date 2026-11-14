"""The Middle Persian readings and the two laws the fourth Persian pass added.

Three claims are pinned here, each one a thing a later edit could quietly
break:

* the reading table is complete for what Persian cites and every row can be
  spelled by the signs it is stored beside (``tools/build_pal_readings.py``);
* the Pahlavi sign waw and heth are read for both of their values (b/w and
  h/x), because the record writes xwadāy as ``hwtʾy`` and bāzār as ``wʾčʾl``;
* the final *-h of Old Persian is matched in both notations (``h`` and the
  modifying ``ʰ``), and OP word-final *-ça(h) gives MP ``-s`` while intervocalic
  ``ç`` still gives ``h``.
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from pie import data
from pie.rules import derive
from pie.service import normalise_etymon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_pal_readings  # noqa: E402


class TestReadingsTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = json.loads((data.DATA / "readings_pal.json").read_text(encoding="utf-8"))

    def test_every_quoted_row_is_spellable_by_its_spelling(self):
        # A row read from a sentence passed the builder's letter test when it
        # was copied; a dictionary headword line (``recorded``) and an
        # Arameogram read as a whole word (capitals) are stated, not spelled,
        # and are exempt.
        logogram = re.compile(r"[A-ZŠṬḤṢČŽĞĀĒĪŌŪ'’\-]+")
        bad = [form for form, row in self.table.items()
               if row.get("tier") == "quoted" and not logogram.fullmatch(form)
               and not build_pal_readings._spellable(form, row["reading"])]
        self.assertEqual(bad, [], f"quoted rows the signs cannot spell: {bad[:5]}")

    def test_every_row_has_a_source_and_a_tier(self):
        for form, row in self.table.items():
            self.assertTrue(row.get("source"), form)
            self.assertIn(row.get("tier"), {"recorded", "quoted", "script-quoted"}, form)

    def test_a_transliteration_is_read_at_its_stated_value(self):
        # MacKenzie spells these words with waw and heth; the readings are the
        # dictionary's own, not a guess from the letters.
        self.assertEqual(self.table.get("wʾčʾl", {}).get("reading"), "wāzār")
        self.assertEqual(self.table.get("hwtʾy", {}).get("reading"), "xwadāy")

    def test_the_table_matches_the_builder(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_pal_readings.py"), "--check"],
            capture_output=True, text=True, cwd=str(ROOT), check=True)
        self.assertIn("check: identical", out.stdout)


class TestPersianLaws(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chain = data.derivation_chain("pal")
        cls.rulesets = data.rulesets()

    def _derive(self, form):
        return derive(form, ["peo", "pal"], self.rulesets)

    def test_the_aspirated_notation_of_final_h_is_the_same_law(self):
        d = self._derive("aspaʰ")
        self.assertEqual(d.output, "asp")
        self.assertIn("final_h_loss", [s.rule_id for s in d.steps])

    def test_final_cedilla_gives_s(self):
        d = self._derive("puçaʰ")
        self.assertEqual(d.output, "pus")
        self.assertIn("cedilla_to_s_before_final_a", [s.rule_id for s in d.steps])

    def test_intervocalic_cedilla_still_gives_h(self):
        d = self._derive("xšaçam")
        self.assertEqual(d.output, "šah")
        self.assertNotIn("cedilla_to_s_before_final_a", [s.rule_id for s in d.steps])
        self.assertIn("cedilla_to_h", [s.rule_id for s in d.steps])


if __name__ == "__main__":
    unittest.main()
