"""Every code a record prints is a language's name, not the code.

The word page for Old Persian *farnah said "borrowed from xme-old" beside a
sentence that said "Borrowed from Old Median": the loan badge had its own,
narrower name lookup, and the code fell through it.  The fix is one resolver,
`data.language_name`, and the tables behind it: the registry, the names
harvested from the descendant trees, and Wiktionary's full language table.
The guard below is what keeps a newly recorded language from coming back as a
bare code (2026-11-12).
"""
import gzip
import json
import re
import unittest
from pathlib import Path

from pie import data, loans, service

ROOT = Path(__file__).resolve().parents[1]
LEXICON = ROOT / "data" / "lexicon"


class Resolver(unittest.TestCase):
    def test_old_median_is_a_language_not_a_code(self):
        self.assertEqual(data.language_name("xme-old"), "Old Median")
        self.assertEqual(service._lang("xme-old")["name"], "Old Median")
        self.assertEqual(service._lang("xme-old")["branch"],
                         "Indo-Iranian (Iranian, Northwest)")

    def test_a_non_ie_language_is_named(self):
        self.assertEqual(data.language_name("ar"), "Arabic")
        self.assertEqual(data.language_name("akk"), "Akkadian")

    def test_a_borrowers_name_comes_from_wiktionaries_table(self):
        self.assertEqual(data.language_name("bkk"), "Brokskat")
        self.assertEqual(data.language_name("fro-nor"), "Old Northern French")
        self.assertEqual(data.language_name("ang-ang"), "Anglian Old English")

    def test_one_record_naming_two_languages_names_both(self):
        self.assertEqual(data.language_name("ru,uk"), "Russian / Ukrainian")
        self.assertEqual(data.language_name("ru, uk"), "Russian / Ukrainian")

    def test_the_latin_stage_abbreviations_are_named(self):
        for abbreviation, name in (("ML.", "Medieval Latin"),
                                   ("LL.", "Late Latin"),
                                   ("NL.", "New Latin"),
                                   ("VL.", "Vulgar Latin"),
                                   ("EL.", "Ecclesiastical Latin")):
            self.assertEqual(data.language_name(abbreviation), name, abbreviation)


class FarnahPage(unittest.TestCase):
    def test_the_loan_badge_names_old_median(self):
        page = service.word("peo", "farnah")
        self.assertIsNotNone(page)
        self.assertEqual(page["loan"]["code"], "xme-old")
        self.assertEqual(page["loan"]["name"], "Old Median")
        self.assertEqual(page["loan"]["wording"], "borrowed from Old Median")
        self.assertEqual(page["ancestry"][0]["lang_name"], "Old Median")


class EveryRecordedCodeIsNamed(unittest.TestCase):
    """The guard: no ancestry row and no cognate form may print a bare code."""

    def test_every_code_in_the_lexicons_resolves(self):
        unnamed, broken = set(), set()
        code = re.compile(r"[a-z][a-zA-Z0-9-]*")
        for path in sorted(LEXICON.rglob("*.jsonl.gz")):
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    entry = json.loads(line)
                    for row in entry.get("anc") or []:
                        if not (isinstance(row, list) and row):
                            continue
                        value = str(row[0])
                        if value.startswith(":") and value != ":inh":
                            continue
                        if value == ":inh":
                            value = str(row[1]).split(":", 1)[0] if len(row) > 1 else ""
                        parts = [part.strip() for part in value.split(",") if part.strip()]
                        if any(not code.fullmatch(part) for part in parts):
                            broken.add(value)
                        if value and data.language_name(value) == value:
                            unnamed.add(value)
                    lang = str(entry.get("lang") or "")
                    if lang and data.language_name(lang) == lang:
                        unnamed.add(lang)
        self.assertEqual(sorted(broken), [], "an ancestry code is not a code")
        self.assertEqual(sorted(unnamed), [], "a code has no name")

    def test_every_cognate_form_resolves(self):
        path = ROOT / "data" / "cognate_sets" / "ine-pro.jsonl.gz"
        unnamed = set()
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                entry = json.loads(line)
                for form in entry.get("forms") or []:
                    lang = str(form.get("l") or "")
                    if lang and data.language_name(lang) == lang:
                        unnamed.add(lang)
        self.assertEqual(sorted(unnamed), [], "a cognate code has no name")
