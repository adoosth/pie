"""The ancestry a record states, read the way the record writes it (2026-11-09).

A reader reported that *dáwxšati* says in its own etymology "from
Proto-Indo-European *déwk-s-eti, from *dewk- + *-seti", while the timeline
started at the bare root *dewk-.  Two reader faults produced that, and both are
about a *form* rather than a word:

* ``{{inh|ira-pro|ine-pro||*déwk-s-eti}}`` writes the form in the fourth
  argument because the third is the (empty) on-page term.  Reading only the
  third argument dropped the link the entry states, so the ladder began at the
  root the ``{{root}}`` template names.
* ``{{etymon}}`` packs a whole tree into one argument with nested markup
  (``pal:𐭓𐭐𐭃<ety:inh<peo:𐎱𐎡𐎫𐎠>>``).  Stripping the tags welded them onto
  the word, and the Middle Persian rung of پدر stopped matching its record.

The tests below pin the shapes, not one word's numbers.
"""
from __future__ import annotations

import gzip
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, etymtext, service  # noqa: E402
import build_lexicons as build  # noqa: E402


def entry_for(lang: str, word: str) -> dict:
    for row in data.lexicon(lang):
        if row["word"] == word:
            return row
    raise AssertionError(f"{lang} glossary has no {word}")


class TestTheFourthArgument(unittest.TestCase):
    def test_a_form_in_the_fourth_argument_is_an_ancestor(self):
        row = entry_for("ira-pro", "dáwxšati")
        pairs = [(lang, word) for lang, word, _rel in row["anc"]]
        self.assertIn(("iir-pro", "*dáwkšati"), pairs)
        self.assertIn(("ine-pro", "*déwk-s-eti"), pairs)

    def test_the_root_is_kept_beside_the_word_it_builds(self):
        row = entry_for("ira-pro", "dáwxšati")
        roots = [word for lang, word, rel in row["anc"]
                 if lang == "ine-pro" and rel == "root"]
        self.assertIn("*dewk-", roots)


class TestTheNestedChain(unittest.TestCase):
    def test_a_plain_hop_is_one_hop(self):
        self.assertEqual(
            [r["term"] for r in etymtext.parse_chain("fr:livre", "en", "bor")],
            ["livre"])
        self.assertEqual(
            [r["rel"] for r in etymtext.parse_chain("fr:livre", "en", "bor")],
            ["bor"])

    def test_markup_is_never_part_of_a_word(self):
        rows = etymtext.parse_chain(
            "pal:𐭓𐭐𐭃\n<ety:inh<peo:𐎱𐎡𐎫𐎠\n>>", "fa", "inh")
        self.assertEqual([r["term"] for r in rows], ["𐭓𐭐𐭃", "𐎱𐎡𐎫𐎠"])
        for row in rows:
            self.assertNotIn(">", row["term"])
            self.assertNotIn("<", row["term"])

    def test_a_nested_affixation_names_its_pieces(self):
        rows = etymtext.parse_terms(
            "ine-pro:<alt:*moldʰéyeti><ety:af<*meldʰ-><*-éyeti>>", "lt")
        self.assertEqual([r["term"] for r in rows], ["*moldʰéyeti", "*meldʰ-", "*-éyeti"])

    def test_a_piece_in_the_entry_own_language_is_not_an_ancestor(self):
        self.assertEqual(etymtext.parse_chain("non-", "en", "af"), [])

    def test_no_ancestry_row_carries_markup(self):
        """Every record, every language: a form is a form, not a template.

        A lone ``<`` between two forms is the record's own "from" sign
        (Persian جدر "*gaδr < *waδr"); markup is a ``<`` that opens a tag.
        """
        for lang, _meta in data.languages().items():
            for row in data.lexicon(lang):
                for _lg, word, _rel in row.get("anc") or []:
                    where = f"{lang}:{row['word']}"
                    self.assertNotIn("\n", word, where)
                    self.assertFalse(re.search(r"<[a-zA-Z]+:", word), where)
                    self.assertFalse(word.rstrip().endswith(">"), where)


class TestTheWordTheReportNamed(unittest.TestCase):
    """*dáwxšati: the ladder is the record's own history, not a bare root."""

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("ira-pro", "dáwxšati")
        cls.levels = {row["stage"]: row for row in cls.page["hierarchy"]["levels"]}

    def test_the_ladder_starts_at_the_derived_proto_form(self):
        self.assertEqual(self.page["hierarchy"]["start"], "ine-pro")
        self.assertEqual(self.page["hierarchy"]["start_form"], "déwk-s-eti")

    def test_the_middle_and_the_word_are_both_reached(self):
        self.assertEqual(self.levels["iir-pro"]["status"], "match")
        self.assertEqual(self.levels["ira-pro"]["status"], "match")

    def test_the_formation_is_shown_at_its_own_stage(self):
        built = self.levels["ine-pro"]["built_as"]
        self.assertIsNotNone(built, "the PIE rung must say how the form was built")
        self.assertEqual([p["form"] for p in built["pieces"]], ["*dewk-", "*seti"])
        self.assertEqual(built["pieces"][0]["gloss"], "to pull, draw")
        self.assertEqual(built["pieces"][1]["gloss"], "primary verb suffix")

    def test_no_other_rung_claims_the_formation(self):
        self.assertIsNone(self.levels["iir-pro"]["built_as"])
        self.assertIsNone(self.levels["ira-pro"]["built_as"])


class TestTheBuildReader(unittest.TestCase):
    def test_a_suffix_in_the_entry_own_language_is_a_construction(self):
        row = entry_for("ira-pro", "cwaHdapatiš")
        built = row.get("built_as") or []
        self.assertTrue(built, "a compound the record states must be kept")
        self.assertEqual(built[0]["kind"], "compound")
        self.assertEqual([p[0] for p in built[0]["pieces"]], ["*cwáHdah", "*pátiš"])

    def test_the_glossary_keeps_words_that_record_only_pieces(self):
        """A word built from named pieces is still a word with an origin."""
        row = entry_for("en", "lexicography")
        self.assertEqual(row["word"], "lexicography")


if __name__ == "__main__":
    unittest.main()


class TestAWordBuiltAtItsOwnStage(unittest.TestCase):
    """A compound starts at the word, not at one component's PIE form."""

    def test_the_ladder_starts_at_the_compound_and_names_both_pieces(self):
        page = service.word("ira-pro", "cwaHdapatiš")
        row = page["hierarchy"]["levels"][0]
        self.assertEqual(page["hierarchy"]["start"], "ira-pro")
        self.assertEqual(row["form"], "cwaHdapatiš")
        built = row["built_as"]
        self.assertIsNotNone(built, "the rung must say how the compound was built")
        self.assertEqual([p["form"] for p in built["pieces"]],
                         ["*cwáHdah", "*pátiš"])
        self.assertIsNone(page["hierarchy"]["etymon"],
                          "one piece's PIE etymon is not the compound's")

    def test_a_surface_analysis_does_not_replace_a_recorded_origin(self):
        # "beer, equivalent to be + -er", but from Middle English beere: the
        # construction is a second analysis and must not become the start.
        row = service.word("en", "beer", sense=1)["hierarchy"]
        self.assertNotEqual(row["start"], "en")


class TestTheStemFormativeEnding(unittest.TestCase):
    """*h₂wl̥pís: the -s is the athematic nominative, not part of the suffix."""

    def test_the_construction_accounts_for_every_letter(self):
        page = service.word("ine-pro", "h₂wl̥pís")
        c = page["construction"]
        self.assertEqual(c["base"]["form"], "h₂wl̥p-")
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-i-"])
        self.assertEqual(c["suffixes"][0]["ending"], "s")
        self.assertEqual(c["suffixes"][0]["ending_name"],
                         "athematic nominative singular")
        self.assertEqual(c["composed"], "h₂wl̥pís")


class TestTheLemmaLedger(unittest.TestCase):
    """What the lemma reader stores, and what a re-emit keeps (2026-11-12).

    Two faults met on one old Persian entry: the page writes its reading as
    ``h-i-n-a /hainā/`` (signs, then the reading in slashes), and an older
    reader stored a template's markup (``Idiglat<alt:…><id:Tigris>``) as an
    ancestor.  A clean removed the bracket, the next emit put it back, and the
    refresh kept the markup link beside the clean one — so the entry said its
    ancestor twice and the bracket never stayed gone.
    """

    def setUp(self):
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def lexicon(self):
        return Path(self.dir.name) / "peo.jsonl.gz"

    def store(self, rows):
        import gzip
        with gzip.open(self.lexicon(), "wt", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def load(self):
        import gzip
        with gzip.open(self.lexicon(), "rt", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def test_a_bracket_is_reduced_to_the_reading_at_merge_time(self):
        import wiktionary_lemmas as lemma

        self.assertEqual(lemma.reading_layer("h-i-n-a /hainā/"), "hainā")
        self.assertEqual(lemma.reading_layer("hainā"), "hainā")
        self.assertEqual(lemma.reading_layer("-"), "")
        self.store([{"word": "𐏃𐎡𐎴𐎠", "lang": "peo", "gloss": ["wine"]}])
        page = {"word": "𐏃𐎡𐎴𐎠", "title": "𐏃𐎡𐎴𐎠", "lang": "peo",
                "gloss": ["wine"], "translit": "h-i-n-a /hainā/"}
        lemma.merge_into(self.lexicon(), [page])
        self.assertEqual(self.load()[0]["translit"], "hainā")
        # A second emit must not re-introduce what the first one removed.
        lemma.merge_into(self.lexicon(), [page])
        self.assertEqual(self.load()[0]["translit"], "hainā")

    def test_a_refresh_drops_a_link_that_is_markup(self):
        import wiktionary_lemmas as lemma

        self.store([{
            "word": "𐎫𐎡𐎥𐎼𐎠", "lang": "peo", "gloss": ["Tigris"],
            "translit": "Tigrā", "sources": ["wiktionary"],
            "anc": [["akk", "Idiglat", "borrow"],
                    ["akk", "Idiglat<alt:𒀀𒇉𒈦𒄘𒃼><id:Tigris>", "borrow"]],
        }])
        lemma.refresh_from(self.lexicon(), [{
            "title": "𐎫𐎡𐎥𐎼𐎠", "word": "𐎫𐎡𐎥𐎼𐎠", "lang": "peo",
            "gloss": ["Tigris"], "translit": "Tigrā",
            "anc": [["akk", "Idiglat", "borrow"]],
            "sources": ["wiktionary"],
        }])
        self.assertEqual(self.load()[0]["anc"], [["akk", "Idiglat", "borrow"]])
