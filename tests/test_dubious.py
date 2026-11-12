"""What the dubious-etymology backlog flags, and what it refuses to flag.

The detector reads the corpus and writes nothing: a finding is a word to
re-read, not a repaired derivation.  These tests pin the four kinds, the
worked example of Persian باران, the cap that keeps the file a reading list,
and the comparison behind ``tools/backlog.py --check``.
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pie import dubious


class BaranTest(unittest.TestCase):
    """باران "rain" is the entry the backlog was asked for."""

    @classmethod
    def setUpClass(cls):
        cls.rows = [row for row in dubious.suspects(lang="fa")
                    if row["word"] == "باران"]

    def test_baran_is_flagged(self):
        kinds = {row["kind"] for row in self.rows}
        self.assertTrue(kinds & {"etymon_missing", "cognate_conflict"}, kinds)

    def test_the_finding_names_both_forms(self):
        conflict = next(row for row in self.rows if row["kind"] == "cognate_conflict")
        self.assertIn("wódr̥", conflict["evidence"])
        self.assertIn("weh₁r", conflict["evidence"])
        self.assertEqual(conflict["etymon"], "*weh₁r-")


class CleanInheritanceTest(unittest.TestCase):
    """A recorded chain that agrees with itself is not parked."""

    def test_persian_father_is_not_flagged(self):
        rows = [row for row in dubious.suspects(lang="fa") if row["word"] == "پدر"]
        self.assertEqual(rows, [])


class HedgedAncestryTest(unittest.TestCase):
    """The hedge is read from the source's prose, not inferred."""

    def entry(self, **over):
        base = {
            "word": "sample",
            "lang": "fa",
            "pos": "noun",
            "gloss": ["water"],
            "etym": "Uncertain; perhaps from Proto-Indo-European *wódr̥.",
            "anc": [["ine-pro", "*wódr̥", "inherit"]],
        }
        base.update(over)
        return base

    def test_a_hedged_chain_is_flagged(self):
        kinds = [finding["kind"] for finding in dubious.flags(self.entry())]
        self.assertIn("hedged_ancestry", kinds)

    def test_the_hedge_word_is_quoted(self):
        entry = self.entry(etym="Perhaps from Proto-Indo-European *wódr̥.")
        finding = next(finding for finding in dubious.flags(entry)
                       if finding["kind"] == "hedged_ancestry")
        self.assertIn("perhaps", finding["detail"])
        self.assertIn("etym:", finding["evidence"])
        self.assertIn("Perhaps from", finding["evidence"])

    def test_an_unhedged_chain_is_not_flagged(self):
        entry = self.entry(etym="Inherited from Proto-Indo-European *wódr̥.")
        self.assertEqual([finding for finding in dubious.flags(entry)
                          if finding["kind"] == "hedged_ancestry"], [])

    def test_a_word_without_ancestry_is_never_hedged_ancestry(self):
        entry = self.entry(anc=[], etym="Unknown. Perhaps a substrate word.")
        self.assertEqual(dubious.flags(entry), [])


class CapTest(unittest.TestCase):
    """The file stays a reading list: every language keeps rows, the drop is counted."""

    def test_the_cap_is_shared_and_recorded(self):
        rows = [
            {"lang": "aa" if number % 2 else "bb", "word": f"w{number:04}",
             "etymon": "*x", "kind": "etymon_missing",
             "detail": "ancestry names *x at ine-pro", "evidence": "anc row"}
            for number in range(4000)
        ]
        report = dubious.payload(rows=rows)
        cap = dubious.CAPS["etymon_missing"]
        self.assertEqual(len(report["words"]), cap)
        self.assertEqual(report["truncated"]["etymon_missing"], 4000 - cap)
        self.assertEqual({row["lang"] for row in report["words"]}, {"aa", "bb"})
        self.assertEqual(report["counts"]["by_kind"]["etymon_missing"], 4000)


class StalenessTest(unittest.TestCase):
    """``--check`` compares the report, never the timestamp."""

    @classmethod
    def setUpClass(cls):
        cls.fresh = dubious.payload(rows=[], generated="2026-11-09 18:00")

    def test_a_written_file_is_current(self):
        self.assertIsNone(dubious.is_stale(self.fresh, self.fresh))

    def test_the_timestamp_alone_is_not_staleness(self):
        older = dict(self.fresh, generated="2020-01-01 00:00")
        self.assertIsNone(dubious.is_stale(older, self.fresh))

    def test_a_changed_row_is_stale(self):
        stored = copy.deepcopy(self.fresh)
        stored["words"].append({"lang": "fa", "word": "باران", "etymon": "*weh₁r-",
                                "kind": "cognate_conflict", "detail": "",
                                "evidence": "", "status": "open",
                                "found": "2026-11-09"})
        reason = dubious.is_stale(stored, self.fresh)
        self.assertIsNotNone(reason)
        self.assertIn("words", reason)

    def test_a_changed_cap_is_stale(self):
        stored = copy.deepcopy(self.fresh)
        stored["truncated"] = {"etymon_missing": 1}
        self.assertIn("truncated", dubious.is_stale(stored, self.fresh))


if __name__ == "__main__":
    unittest.main()
