"""The glossary paints each headword with its band, in the counter's colours.

The project's 2026-11-09 request: the words of the glossary page are coloured by
their category, using the same colours as the coverage page.  The colours come
from `data/category_index.json.gz`, written by the full `tools/coverage.py`
run that publishes `data/coverage.json`, so the list and the numbers cannot
come from two different measurements.  These tests hold three things: every
band is one of the six (or the `ie_loan` facet), a proto stage is not banded,
and a glossary row agrees with the word's own page.

They skip — with a reason, never silently pass — when no published measurement
is present, because the index is an artefact of a nine-minute run.
"""
from __future__ import annotations

import unittest

from pie import categories, data, service

INDEX = data.DATA / "category_index.json.gz"


@unittest.skipUnless(INDEX.exists(), "no published measurement (data/category_index.json.gz)")
class GlossaryBandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bands = service.band_index()

    def bands_of(self, lang: str) -> list[str]:
        """Every band the index stores for a stage, one per sense.

        Since 2026-11-09 a headword's row is a list — ``bank`` the institution
        and ``bank`` the river's edge are different words — so a test that
        counts bands has to flatten it.
        """
        out: list[str] = []
        for value in (self.bands.get(lang) or {}).values():
            out.extend(value if isinstance(value, list) else [value])
        return out

    def band_of(self, lang: str, word: str, sense: int = 1) -> str:
        return service.band_for(lang, word, sense)

    def test_every_band_is_a_known_category(self):
        known = set(categories.CATEGORIES)
        self.assertTrue(self.bands, "the index is empty")
        for lang, words in self.bands.items():
            self.assertTrue(words, lang)
            for value in words.values():
                self.assertLessEqual(set(value if isinstance(value, list) else [value]),
                                     known, lang)

    def test_a_stage_without_attested_words_is_absent(self):
        """An empty colour table for Proto-Germanic would suggest it was classified."""
        self.assertNotIn("gem-pro", self.bands)

    def test_a_proto_stage_has_no_band(self):
        """The six bands are for attested languages; a reconstruction is not one."""
        self.assertNotIn("ine-pro", self.bands)
        page = service.glossary("ine-pro", limit=20)
        self.assertEqual([r for r in page["rows"] if r["band"]], [])

    def test_the_rows_carry_the_index(self):
        for lang in ("fa", "en"):
            page = service.glossary(lang, limit=25)
            shown = [r for r in page["rows"] if r["band"]]
            self.assertTrue(shown, lang)
            for row in page["rows"]:
                self.assertEqual(row["band"], self.band_of(lang, row["word"], row["sense"]),
                                 f"{lang}/{row['word']}")
            # ``banded`` counts the whole list the reader asked for, so it is
            # the sum of the stage-wide counts, not the 25 rows shown here.
            self.assertEqual(page["banded"], sum(page["counts"].values()), lang)
            self.assertEqual(sum(page["legend"].values()), len(shown), lang)

    def test_banded_is_counted_from_the_payload_rows(self):
        """A page that fits the limit cannot disagree with its own row count."""
        page = service.glossary("ave", limit=10**6)
        self.assertEqual(len(page["rows"]), page["total"])
        banded = sum(1 for row in page["rows"] if row["band"])
        self.assertEqual(page["banded"], banded)
        self.assertEqual(sum(page["legend"].values()), banded)

    def test_the_published_bands_agree_with_the_ladder(self):
        """A green row may not open a ladder whose final verdict is not "match"."""
        # One stage per band, and a stage that really has rows of it: the
        # missing-rung rule of 2026-11-13 emptied fa's light-green rows and
        # pal's green ones, so the sample names stages whose records still
        # pass (ang adjusted, grc and peo full).
        for lang, band in (("ang", "adjusted"), ("grc", "full"), ("peo", "full")):
            page = service.glossary(lang, limit=3, band=band)
            self.assertTrue(page["rows"], f"{lang} has no {band} rows")
            for row in page["rows"]:
                word = service.word(lang, row["word"], sense=row["sense"])
                self.assertIsNotNone(word, f"{lang}/{row['word']}#{row['sense']}")
                status = word["hierarchy"]["result"]["status"]
                # A word made green by a writing layer says so itself: Greek
                # γόμφος is written by the orthographic layer (the law writes
                # gˈompʰos), and the unmodelled Proto-Hellenic rung between the
                # PIE form and the word cannot be compared, so the ladder's
                # law-level verdict is "differs".  Band and ladder agree there
                # — the band names the layer — so that case is allowed; a green
                # row over a ladder that differs for any other reason is not.
                reason = str((word.get("category") or {}).get("reason", "")).lower()
                layer = any(name in reason for name in
                            ("orthographic", "script", "layer"))
                # A word the record builds from its own words has no law to
                # match: the ladder starts at the word (status "start") and the
                # band says "construction of αὖ + τε".  Band and ladder are
                # saying the same thing, so that is agreement too.
                built = reason.startswith("construction of")
                self.assertTrue(status == "match" or layer or built,
                                f"{lang}/{row['word']}#{row['sense']} is {band} but "
                                f"its ladder is {status} ({reason})")

    def test_a_pahlavi_reading_is_transliterated_not_attested(self):
        page = service.word("pal", "lwc")
        self.assertIsNotNone(page)
        self.assertFalse(page["in_script"])
        self.assertEqual(page["attestation"]["status"], "transliterated")

    def test_the_root_flag_is_the_headword_not_its_etymology(self):
        """The "root" pill asked whether the *etymology* mentioned a root.

        In a reconstructed stage nearly every word does, so 796 of the 799
        Proto-Indo-Iranian rows wore it and the pill said nothing (admin,
        2026-11-13).  A row is a root when the dictionary heads it as one, an
        affix when it is bound, and the rest are words; the part of speech
        column is what says so — there is no second column repeating it.
        """
        page = service.glossary("iir-pro", band="pie", limit=400)
        self.assertGreater(page["total"], 500)
        roots = [r for r in page["rows"] if r["kind"] == "root"]
        self.assertGreater(len(roots), 0)
        self.assertLess(page["roots"], 40)
        for row in page["rows"]:
            self.assertEqual(row["kind"] == "root", row["pos"] == "root", row)
        # Roots are listed first, which is what the subtitle promises.
        self.assertTrue(all(r["kind"] == "root"
                            for r in page["rows"][:page["roots"]]))
        # A bound headword is an affix even though its pos is "prefix".
        affixes = [r for r in page["rows"] if r["kind"] == "affix"]
        self.assertTrue(affixes)
        self.assertTrue(all(r["word"].startswith("-") or r["word"].endswith("-")
                            or r["pos"] in service._BOUND_POS for r in affixes))

    def test_the_status_column_carries_its_own_meaning(self):
        """The list prints one word per row; the tooltip brings the sentence."""
        from pie import attestation
        page = service.glossary("peo", limit=20)
        self.assertEqual(set(page["statuses"]),
                         {"attested", "transliterated", "recorded",
                          "proposed", attestation.NON_EXISTENT})
        for row in page["rows"]:
            self.assertIn(row["attestation"], attestation.STATUSES)

    def test_a_row_and_the_words_own_page_agree(self):
        """A word must not be yellow in the list and green on its page."""
        for lang in ("fa", "en"):
            page = service.glossary(lang, limit=12)
            checked = 0
            for row in page["rows"]:
                if not row["band"]:
                    continue
                word = service.word(lang, row["word"], sense=row["sense"])
                self.assertEqual(word["category"]["category"], row["band"],
                                 f"{lang}/{row['word']}#{row['sense']}")
                checked += 1
                if checked >= 5:
                    break
            self.assertGreater(checked, 0, lang)

    def test_the_banded_words_are_counted_words(self):
        """No band may be invented for a word the counter never classified."""
        lang = "fa"
        attest = {e["word"].strip() for e in data.lexicon(lang)}
        self.assertLessEqual(set(self.bands[lang]), attest)

    def test_a_band_filter_lists_only_that_band(self):
        page = service.glossary("fa", limit=20, band="full")
        self.assertEqual(page["band"], "full")
        self.assertTrue(page["rows"])
        self.assertEqual({r["band"] for r in page["rows"]}, {"full"})
        # The counts stay those of the whole stage, so the selector can say how
        # many fully explained words there are without loading them all.
        self.assertEqual(page["counts"]["full"],
                         sum(1 for v in self.bands_of("fa") if v == "full"))
        self.assertEqual(page["total"], page["counts"]["full"])

    def test_pie_words_hides_the_non_pie_band(self):
        """The default view leaves out words borrowed from outside the family
        (2026-11-09): it is a view over the headwords, not a seventh
        coverage band, and every word page keeps its own band."""
        page = service.glossary("fa", limit=400, band=service.PIE_WORDS_BAND)
        self.assertEqual(page["band"], "pie")
        self.assertTrue(page["rows"])
        self.assertNotIn("non_pie", {r["band"] for r in page["rows"]})
        self.assertEqual(page["total"], page["stage_total"] - page["counts"]["non_pie"])
        self.assertGreater(page["counts"]["non_pie"], 0)

    def test_all_words_is_the_whole_stage(self):
        page = service.glossary("fa", limit=600)
        self.assertEqual(page["band"], "")
        self.assertEqual(page["total"], page["stage_total"])
        self.assertIn("non_pie", {r["band"] for r in page["rows"]})
        # `all` is the address the glossary writes for "no filter", so the API
        # accepts it as one too.
        same = service.glossary("fa", limit=600, band="all")
        self.assertEqual(same["band"], "")
        self.assertEqual(same["total"], page["total"])

    def test_an_unknown_band_is_an_empty_list_not_an_error(self):
        page = service.glossary("fa", limit=20, band="nonsense")
        self.assertEqual(page["rows"], [])
        self.assertEqual(page["total"], 0)


if __name__ == "__main__":
    unittest.main()


class FilteredGlossaryTest(unittest.TestCase):
    """A search inside a glossary must not rewrite the stage's own numbers.

    `q` used to filter the rows before the counts were taken, so filtering
    Latin for "ab" told the reader the stage holds 204 words — and the band
    selector read "all words · 204" (2026-11-12, critic P1-2).
    """

    def test_a_filter_keeps_the_stage_counts(self):
        whole = service.glossary("la", limit=5)
        filtered = service.glossary("la", limit=5, q="ab")
        self.assertLess(filtered["total"], whole["total"])
        self.assertEqual(filtered["stage_total"], whole["stage_total"])
        self.assertEqual(filtered["counts"], whole["counts"])

    def test_banded_describes_the_filtered_list_not_the_page(self):
        page = service.glossary("la", limit=3, q="ab")
        self.assertGreater(page["banded"], len(page["rows"]),
                           "a page of three rows cannot be the whole list")
