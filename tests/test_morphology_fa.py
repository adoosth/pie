"""The Persian build-a-form registry (data/morphology/fa.yaml).

The timeline lets a reader build a form at a stage out of a word and a cited
morpheme.  For Persian that registry is hand-written: ten derivational suffixes
and the two plural endings, each quoting the page it is read on.  These tests
hold the registry to its promises — a form, a meaning and a source on every
row, ids a click can name, the joining rule the orthography needs — and check
that the service's public path loads it and that composing with a row really
puts that row's letters on the word.

The service also lists the stage's own suffix entries beside the hand-written
rows (a morpheme the dictionary records even where no construction wears it),
so the assertions about the registry are made on the rows whose ids are the
file's, and the file itself is read first.
"""
from __future__ import annotations

import unittest

import yaml

from pie import data, service

#: The keys a registry file may carry at its top level.
TOP_LEVEL = {"language", "note", "suffixes", "endings", "joining"}

#: The word the composition tests build on, and the one row whose result is a
#: word the dictionaries actually hold (دست + ـگاه → دستگاه 'device').
BASE = "دست"
RECORDED = "gah"
RECORDED_FORM = "دستگاه"


def registry() -> dict:
    return yaml.safe_load((data.DATA / "morphology" / "fa.yaml").read_text(encoding="utf-8"))


def curated_rows() -> list[dict]:
    """The file's rows as the service returns them, matched by id."""
    ids = [row["id"] for row in registry()["suffixes"]]
    served = {row["id"]: row for row in service.morphology("fa")["suffixes"]}
    return [served[i] for i in ids if i in served]


def unzwnj(text: str) -> str:
    return text.replace("\u200c", "")


class RegistryFileTest(unittest.TestCase):
    """The file itself, read without the service."""

    def setUp(self):
        self.raw = registry()

    def test_no_unknown_top_level_keys(self):
        self.assertEqual(set(self.raw) - TOP_LEVEL, set())
        for key in TOP_LEVEL:
            self.assertIn(key, self.raw)

    def test_every_row_has_a_form_a_meaning_and_a_source(self):
        rows = self.raw["suffixes"]
        self.assertGreaterEqual(len(rows), 7)
        for row in rows:
            with self.subTest(id=row.get("id")):
                self.assertTrue(row.get("id"))
                form = row.get("form") or ""
                self.assertTrue(form.startswith("-"), f"{form!r} is not written as a suffix")
                self.assertGreater(len(form), 1)
                self.assertTrue((row.get("gloss") or "").strip())
                self.assertTrue(row.get("sources"))
                self.assertTrue((row.get("note") or "").strip())
                self.assertEqual(row.get("attach", "keep"), "keep")

    def test_ids_are_unique_and_nameable(self):
        ids = [row["id"] for row in self.raw["suffixes"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_a_note_carries_its_citation(self):
        """A row's note names the page it is read on, not just 'Wiktionary'."""
        for row in self.raw["suffixes"]:
            with self.subTest(id=row["id"]):
                self.assertIn("wiktionary.org/wiki/", row["note"])

    def test_sources_are_registered(self):
        known = data.sources()
        for row in list(self.raw["suffixes"]) + list(self.raw["endings"]):
            for source in row["sources"]:
                with self.subTest(form=row["form"], source=source):
                    self.assertIn(source, known)

    def test_endings_are_inflection_and_say_so(self):
        endings = self.raw["endings"]
        self.assertTrue(endings)
        for row in endings:
            with self.subTest(form=row.get("form")):
                self.assertTrue(row["form"].startswith("-"))
                self.assertTrue((row.get("name") or "").strip())
                self.assertTrue(row.get("sources"))
        # The plural markers are the two the language actually has, and the
        # file keeps them out of the derivational list.
        self.assertEqual({row["form"] for row in endings}, {"-ها", "-ان"})
        suffix_forms = {row["form"] for row in self.raw["suffixes"]}
        self.assertEqual(suffix_forms & {"-ها", "-ان"}, set())

    def test_the_joining_rule_is_stated(self):
        joining = self.raw["joining"]
        self.assertEqual(joining["linker"], "")
        self.assertIs(joining["zwnj"], True)
        self.assertTrue(joining["note"].strip())
        self.assertTrue(joining["sources"])


class ServicePathTest(unittest.TestCase):
    """What a click on the picker actually gets."""

    def test_the_service_serves_the_registry(self):
        payload = service.morphology("fa")
        rows = curated_rows()
        self.assertEqual(len(rows), len(registry()["suffixes"]))
        for row in rows:
            with self.subTest(id=row["id"]):
                self.assertTrue(row["form"].startswith("-"))
                self.assertTrue(row["gloss"])
                self.assertTrue(row["sources"])
        # A loader that drops the joining block silently would lose the
        # orthographic half of the rule; when the payload carries it, it must
        # agree with the file.
        if "joining" in payload:
            self.assertEqual(payload["joining"]["linker"], "")
            self.assertIs(payload["joining"]["zwnj"], True)

    def test_composing_puts_the_suffix_letters_on_the_word(self):
        rows = curated_rows()
        self.assertTrue(rows, "the service served none of the registry's rows")
        for row in rows:
            letters = row["form"].lstrip("-")
            with self.subTest(id=row["id"]):
                result = service.compose(BASE, row["id"], "fa")
                composed = result["form"]
                self.assertTrue(composed, f"{row['id']} composed to nothing")
                self.assertTrue(composed.endswith(letters),
                                f"{composed!r} does not end in {letters!r}")
                self.assertTrue(unzwnj(composed).startswith(BASE))
                # A hand composition is a formation, never a registered law.
                self.assertIsNone(result.get("law"))

    def test_a_recorded_word_is_what_the_row_builds(self):
        result = service.compose(BASE, RECORDED, "fa")
        self.assertEqual(unzwnj(result["form"]), RECORDED_FORM)
        self.assertEqual(result["form"], RECORDED_FORM)

    def test_an_unknown_suffix_composes_nothing(self):
        result = service.compose(BASE, "no-such-suffix", "fa")
        self.assertFalse(result["suffix"])
        self.assertEqual(result["steps"], [])


if __name__ == "__main__":
    unittest.main()
