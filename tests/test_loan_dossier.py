"""A loan word must say who it was borrowed from, and never pretend to a date.

The project's 2026-11-09 request: a Persian word whose etymology states "borrowed
from Arabic" should read that way on its page, with the window in which Arabic
reached Persian — and it stays in the non-PIE band, because the badge is a
statement about the band and the dossier is a statement about the donor.

Two things are guarded here: the dossier is built from the record's own donor
row (never guessed), and the page and the counter agree about the band.
"""
from __future__ import annotations

import unittest

from pie import categories, data, loans, service


def entry(lang: str, word: str) -> dict:
    for row in data.lexicon(lang):
        if row["word"] == word:
            return row
    raise AssertionError(f"{lang} glossary has no {word!r}")


class DossierTest(unittest.TestCase):
    def test_arabic_loan_names_its_donor_and_its_form(self):
        row = entry("fa", "آخرت")
        dossier = loans.donor(row, "fa")
        self.assertEqual(dossier["code"], "ar")
        self.assertEqual(dossier["name"], "Arabic")
        self.assertEqual(dossier["form"], "آخِرَة")
        self.assertEqual(dossier["wording"], "borrowed from Arabic")

    def test_the_window_is_the_contact_not_a_date_for_the_word(self):
        """The window is one badge on the ladder and nothing more.

        A contact window says when the two languages could have met, never when
        this word was borrowed.  The page prints the years beside the ladder
        and no prose about them (2026-11-13: the page is the meaning, the
        timeline and the sources).
        """
        window = loans.period("ar", "fa")
        self.assertIsNotNone(window)
        self.assertEqual(window["from"], 633)
        self.assertGreater(window["to"], window["from"])
        self.assertNotIn("window_note", window)
        self.assertNotIn("landmarks", window)

    def test_an_unrecorded_pair_has_no_window(self):
        self.assertIsNone(loans.period("ar", "xx"))
        self.assertIsNone(loans.period("", "fa"))

    def test_an_inherited_word_has_no_dossier(self):
        self.assertIsNone(loans.donor(entry("fa", "باران"), "fa"))
        self.assertIsNone(loans.donor(entry("en", "water"), "en"))

    def test_the_page_and_the_counter_agree_on_the_band(self):
        for word in ("آخرت", "کتاب", "مسجد"):
            row = entry("fa", word)
            page = service.word("fa", word)
            self.assertEqual(page["category"]["category"], "non_pie", word)
            self.assertEqual(page["category"]["label"],
                             categories.CATEGORIES["non_pie"]["label"])
            self.assertEqual(page["loan"]["code"], "ar")

    def test_the_dossier_never_changes_the_band(self):
        """A dossier without a window is still non-PIE: display never re-categorises."""
        row = entry("fa", "آخرت")
        verdict = categories.verdict(recorded=True, non_ie=True)
        self.assertEqual(verdict["category"], "non_pie")


if __name__ == "__main__":
    unittest.main()


class MissingPIELinkTest(unittest.TestCase):
    """A chain that stops at Proto-Germanic is not a PIE explanation.

    English *et* is derived exactly from Proto-Germanic *ēt, and the laws
    reproduce it — but Wiktionary records nothing above *ēt*, so the word is
    partially explained, not fully (2026-11-09).
    """

    def test_et_is_partial_because_its_record_stops_at_proto_germanic(self):
        page = service.word("en", "et")
        self.assertEqual(page["category"]["category"], "partial")
        self.assertNotIn("ine-pro", {a["lang"] for a in page["ancestry"]})
        self.assertEqual(page["ancestry"][-1]["lang"], "gem-pro")

    def test_batch_is_partial_because_the_engine_starts_at_middle_english(self):
        """Green needs the whole chain, not a last mile.

        English *night* is reproduced exactly from Middle English *nighte*, and
        the laws write something else than the record at every stage above it;
        the engine never shows the PIE etymon becoming the word.  The project's
        rules (2026-11-09) make that *partially* explained: a word that does not
        go all the way up from PIE is not fully explained.
        """
        page = service.word("en", "night")
        self.assertIn("ine-pro", {a["lang"] for a in page["ancestry"]})
        self.assertEqual(page["category"]["category"], "partial")
        self.assertNotEqual(page["hierarchy"]["exact"]["stage"], "ine-pro")
        self.assertEqual(page["hierarchy"]["exact"]["stage"], "enm")

    def test_old_persian_kama_is_partial_because_it_starts_at_proto_iranian(self):
        page = service.word("peo", "\U000103A3\U000103A0\U000103B6")
        self.assertIn("ira-pro", {a["lang"] for a in page["ancestry"]})
        self.assertEqual(page["category"]["category"], "partial")
        self.assertEqual(page["hierarchy"]["exact"]["stage"], "ira-pro")

    def test_the_verdict_default_is_the_strict_one(self):
        row = categories.verdict(recorded=True, matched_by="laws",
                                 tiers={"established"})
        self.assertEqual(row["category"], "partial")


class LoanToolTest(unittest.TestCase):
    """The audit tool must be runnable and must write its table.

    It once died inside the markdown builder (a tuple where a line belonged),
    after printing every row — the sort of failure only a real run catches.
    """

    def test_the_markdown_table_is_written(self):
        import os
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "loans.md"
            proc = subprocess.run(
                [sys.executable, "tools/loan_check.py", "--lang", "fa", "--donor", "ar",
                 "--sample", "5", "--markdown", str(out)],
                cwd=root, capture_output=True, text=True,
                env={**os.environ, "PYTHONPATH": str(root / "src")})
            self.assertEqual(proc.returncode, 0, proc.stderr[-800:])
            text = out.read_text(encoding="utf-8")
        self.assertIn("| word | gloss | donor form | band |", text)
        self.assertIn("non-PIE", text)
        self.assertIn("633–1100", text)
