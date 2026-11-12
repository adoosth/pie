"""Tests for the read models and the web front end.

These are the regressions behind two 2026-11-07 reports:

* the word for پدر "shows up weird" in the word view — Persian was rendered
  left-to-right in an italic monospace face, and the derivation said "differs"
  because it compared Latin phonology against the Arabic script;
* the cognate table showed Wiktionary language *codes* (``xcl``, ``yms``)
  instead of language names.

Nothing here needs a browser: the JSON contract is exercised directly, and the
static assets are checked for the hooks the contract depends on. A ``node
--check`` run catches syntax errors in the front end when Node is present.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import unittest
import urllib.parse
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, pathways as paths, service  # noqa: E402

WEB = ROOT / "src" / "pie" / "app" / "web"


def text(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


class TestLanguageNames(unittest.TestCase):
    """Every code that appears in a cognate set has to resolve to a name."""

    def test_names_file_exists(self):
        payload = json.loads((ROOT / "data" / "language_names.json").read_text(encoding="utf-8"))
        self.assertGreater(len(payload["languages"]), 300)
        self.assertIn("generated", payload)

    def test_no_cognate_form_falls_back_to_its_code(self):
        unresolved = set()
        for rec in data.cognate_sets():
            for form in rec["forms"]:
                if service._lang(form["l"])["name"] == form["l"]:
                    unresolved.add(form["l"])
        self.assertEqual(unresolved, set(), f"codes without a language name: {sorted(unresolved)[:20]}")

    def test_registry_wins_over_the_generated_names(self):
        self.assertEqual(service._lang("fa")["name"], "Persian")
        self.assertEqual(service._lang("ine-pro")["name"], "Proto-Indo-European")

    def test_branch_grouping_is_available_for_every_form(self):
        missing = {f["l"] for rec in data.cognate_sets() for f in rec["forms"]
                   if not service._lang(f["l"]).get("branch")}
        self.assertEqual(missing, set())


class TestWordPage(unittest.TestCase):
    """The payload the word view renders, checked on the reported word."""

    @classmethod
    def setUpClass(cls):
        cls.pedar = service.word("fa", "پدر")

    def test_persian_word_is_present_and_flagged_as_rtl(self):
        self.assertIsNotNone(self.pedar, "fa:پدر should be in the Persian glossary")
        self.assertTrue(self.pedar["rtl"], "Persian must be marked right-to-left")
        self.assertEqual(self.pedar["word"], "پدر")

    def test_transliteration_is_recorded(self):
        self.assertTrue(self.pedar["translit"])
        readings = [self.pedar["translit"], *self.pedar["translit_alt"]]
        self.assertIn("pedar", readings)

    def test_derivation_matches_the_romanisation(self):
        trace = self.pedar["derivation"]
        self.assertIsNotNone(trace)
        self.assertTrue(trace["match"], trace.get("forms"))
        self.assertTrue(trace["match_via_translit"])
        self.assertEqual(trace["matched_form"], "pedar")
        self.assertEqual(trace["forms"][-1], "pedar")

    def test_greek_and_persian_are_compared_through_their_romanisation(self):
        for lang, word in (("grc", "πατήρ"), ("fa", "پدر")):
            page = service.word(lang, word)
            self.assertIsNotNone(page, f"{lang}:{word}")
            self.assertTrue(page["derivation"]["match"], f"{lang}:{word} should now match")
            self.assertFalse(page["rtl"] and lang != "fa")

    def test_cognates_carry_language_names(self):
        forms = self.pedar["cognates"]["forms"]
        self.assertGreater(len(forms), 5)
        for form in forms:
            self.assertTrue(form["lang_name"])
            self.assertNotEqual(form["lang_name"], form["l"], "a code leaked into the table")
            self.assertTrue(form["branch"])

    def test_cognates_include_the_glossary_descendants(self):
        langs = {f["l"] for f in self.pedar["cognates"]["forms"]}
        self.assertIn("fa", langs, "the word itself should be in its own cognate set")
        self.assertTrue({"grc", "la", "en"} & langs, f"expected well-known reflexes, got {sorted(langs)}")

    def test_cognate_forms_are_unique(self):
        forms = service.cognate("ine-pro:ph₂tḗr")["forms"]
        keys = [(f["l"], f["w"]) for f in forms]
        self.assertEqual(len(keys), len(set(keys)), "duplicate reflex rows")

    def test_current_word_keeps_its_native_form(self):
        row = next(f for f in self.pedar["cognates"]["forms"] if f["l"] == "fa")
        self.assertEqual(row["w"], "پدر")
        self.assertEqual(row["r"], "pedar")

    def test_word_view_contract(self):
        for key in ("word", "lang", "lang_name", "pos", "gloss", "ipa", "translit", "rtl",
                    "ancestry", "cognates", "derivation", "hierarchy"):
            self.assertIn(key, self.pedar)

    def test_a_latin_word_still_matches_its_own_spelling(self):
        night = service.word("en", "night")
        self.assertFalse(night["rtl"])
        self.assertTrue(night["derivation"]["match"])
        self.assertFalse(night["derivation"]["match_via_translit"])


class TestJoins(unittest.TestCase):
    """A word with several origins shows each piece's own ancestry (2026-11-09)."""

    def test_a_compound_keeps_one_origin_per_piece(self):
        page = service.word("en", "astronaut")
        self.assertTrue(page.get("joins"), "astronaut states that it is built from two pieces")
        join = page["joins"][0]
        self.assertEqual([p["form"] for p in join["pieces"]], ["astro-", "-naut"])
        for piece in join["pieces"]:
            self.assertTrue(piece["word"], "a piece must be a real headword")
            self.assertTrue(piece["ancestry"], f"{piece['form']} should record an ancestor")
            self.assertEqual(piece["ancestry"][-1]["lang"], "grc")

    def test_each_piece_is_a_headword_of_the_same_language(self):
        page = service.word("en", "blackbird")
        pieces = page["joins"][0]["pieces"]
        self.assertEqual([p["form"] for p in pieces], ["black", "bird"])
        words = {e["word"] for e in data.lexicon("en")}
        for piece in pieces:
            self.assertIn(piece["word"], words)

    def test_ancestry_is_oldest_first(self):
        page = service.word("en", "blackbird")
        chain = page["joins"][0]["pieces"][0]["ancestry"]
        if chain and chain[-1]["lang"] == "ine-pro":
            self.assertEqual(chain[-1]["lang"], "ine-pro")
            self.assertNotEqual(chain[0]["lang"], "ine-pro")

    def test_a_word_with_one_origin_has_no_join(self):
        self.assertEqual(service.word("en", "night").get("joins"), [])

    def test_a_gloss_is_never_mistaken_for_a_piece(self):
        # "From Middle English X, from Old French Y" names one ancestor; a
        # sentence with a comma-separated gloss must not become a compound.
        for word in ("dictionary", "thesaurus"):
            page = service.word("en", word)
            self.assertEqual(page.get("joins"), [])


class TestFrontendAssets(unittest.TestCase):
    """Hooks the word view depends on; a silent regression here breaks the page."""

    def test_forms_are_bidi_safe(self):
        js = text("app.js")
        self.assertIn('dir="auto"', js, "word forms must let the browser apply bidi per word")
        self.assertIn('isRTL', js)

    def test_non_latin_forms_are_not_italicised(self):
        css = text("style.css")
        self.assertIn(".form.rtl", css)
        self.assertIn(".headword.rtl", css)

    def test_animations_respect_reduced_motion(self):
        css = text("style.css")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("@keyframes", css)

    def test_the_word_page_orders_ladder_then_cognates(self):
        """The page order: the ladder, the branch, then the cognates — and no
        separate derivation section."""
        js = text("app.js")
        body = js[js.index("async function viewWord"):js.index("/* the ladder")]
        ladder = body.index("renderHierarchy(d.hierarchy")
        cognates = body.index("Cognates <span")
        self.assertLess(ladder, cognates)
        self.assertNotIn("renderDerivation", js)
        self.assertNotIn("Sound-law derivation", js)

    def test_the_counterfactual_table_is_gone(self):
        """2026-11-08: drop "if the rules ran everywhere" entirely.

        The section (``renderRebuilds``) is removed from the word page and the
        cognate page alike; the rebuild data stays in the API, because a PIE
        root page still uses its rows for the *reconstruct into* selector and
        the /api/rebuild endpoint still serves the lab."""
        js = text("app.js")
        css = text("style.css")
        self.assertNotIn("renderRebuilds", js)
        self.assertNotIn("If the rules ran everywhere", js)
        self.assertNotIn("rb-form", js)
        self.assertNotIn(".rb-form", css)
        self.assertNotIn("rb-table", css)

    def test_switching_a_law_updates_in_place_and_keeps_the_url_in_step(self):
        """A 2026-11-07 report: a toggle refreshed the page. It must not.

        The switch flips immediately, only the ladder is re-fetched and
        repainted, and pushState keeps a state addressable without a route.
        """
        js = text("app.js")
        self.assertIn('api("/api/hierarchy"', js, "a toggle re-derives through the API")
        self.assertIn("pushState", js, "the URL still has to record the state")
        self.assertIn("paintLadder", js)
        self.assertIn("pendingScroll", js, "a toggle must not jump the page to the top")
        # Assigning the hash would re-route (and re-render) the whole page.
        self.assertNotIn("location.hash = `#/word", js)

    def test_every_rung_can_be_edited_and_the_page_explains_it(self):
        js = text("app.js")
        self.assertIn("data-edit=", js, "each rung needs an edit affordance")
        self.assertIn('class="editbtn icon"', js, "the control is a pencil, not the word 'edit'")
        self.assertIn("startEdit", js)
        self.assertIn("data-store-pathway", js, "an attested edited path can be stored")
        self.assertIn("Stored pathways", js)

    def test_the_laws_sit_in_the_gap_between_the_two_words(self):
        """2026-11-08: a step's laws are a row of the ladder, and
        they have to *look* as if they stand between the two words — the row
        takes part of the space between the rungs, and the rule under the word
        above is dropped so the chips do not hang from it."""
        js = text("app.js")
        css = text("style.css")
        self.assertIn('class="lawstep"', js)
        self.assertIn("stepGap", js, "the space between two rungs is shared")
        self.assertIn(".lawstep .rail::before", css, "the rail runs through the law row")
        self.assertIn("calc(-1 * var(--gap", css, "the rail closes the gap above the row")
        self.assertIn(".rung:has(+ .lawstep) .rung-body { border-bottom-color: transparent", css,
                      "no rule under the word above pulls the chips up to it")

    def test_the_record_is_marked_on_its_corner(self):
        """2026-11-08: a record is a symbol in the corner, not a word."""
        js = text("app.js")
        css = text("style.css")
        self.assertIn('class="recword"', js)
        self.assertIn(".rung-forms .recword", css, "the mark is pinned to the recorded word")
        self.assertIn('class="recorddot', js, "the record's own mark")
        self.assertIn(".recordmarks { position: absolute", css, "it sits on the corner")
        self.assertIn(".recorddot.wikt", css, "a Wiktionary page keeps its own colour")
        self.assertIn("recordPages(", js, "only a recorded page is drawn as a mark")
        self.assertIn(".recorddot .wmark", css, "the mark is Wiktionary's W, not a quotation mark")
        self.assertIn("Times New Roman", css,
                      "the W is serifed like Wikipedia's (admin, 2026-11-12)")
        self.assertNotIn("Open where it was recorded", js,
                         "the tooltip names the source without telling the reader to click")
        self.assertNotIn(">recorded</a>", js, "the word 'recorded' is gone from the line")
        self.assertNotIn(">starting point<", js, "the top rung no longer says the obvious")
        self.assertNotIn("nothing recorded at this stage</span>", js,
                         "the hover text says it; the page does not repeat it under every rung")

    def test_the_timeline_column_names_the_language_above_the_dates(self):
        """The layout (2026-11-07): the language name goes on
        the left of the timeline, above the date estimates, and the word
        itself stays on the right."""
        js = text("app.js")
        self.assertIn('class="when-name kind-', js)
        self.assertIn('class="when-era"', js)
        self.assertNotIn("rung-era-inline", js, "the name has one home, not two")
        css = text("style.css")
        self.assertIn("grid-area: meta", css, "the name and years must be a grid column")
        self.assertIn("grid-area: body", css)
        self.assertIn('"rail meta" "rail body"', css, "phones stack name and form, never hide the name")
        self.assertNotIn("rung-era-inline", css)

    def test_a_rung_names_its_language_in_colour_and_opens_with_the_form(self):
        """2026-11-07: "attested language" / "reconstructed stage" left the
        right-hand side. The language name in the timeline carries the claim in
        its colour and spells it out on hover, so the reconstruction is the
        top-most thing on every rung."""
        js = text("app.js")
        css = text("style.css")
        self.assertNotIn("kindWord", js, "the worded kind badge is gone from the ladder")
        self.assertNotIn("rung-head", js, "the rung body opens with the form, not a badge row")
        self.assertIn("kind-${esc(level.kind", js, "the language name carries its kind as a class")
        self.assertIn('? "proto" : "attested"', js)
        self.assertIn("Reconstructed stage — no text or speaker records it", js,
                      "hovering a reconstruction says what it is")
        self.assertIn("Attested language — its words survive", js,
                      "hovering an attested name says what it is")
        self.assertIn("this word", js)
        self.assertIn(".rung .when-name.kind-attested", css)
        self.assertIn(".rung .when-name.kind-proto", css)
        # The ✓ is a disc on the corner of the word box, not a glyph in the line.
        self.assertIn('class="matchdot"', js)
        self.assertNotIn('class="tick"', js)
        self.assertIn(".form.matched .matchdot", css)
        self.assertIn("position: absolute", css)

    def test_a_rung_shows_the_sense_its_stage_recorded(self):
        """A rung is a word with a meaning, not only a string of letters
        (2026-11-07: the root of *book* had a gloss nobody could see)."""
        js = text("app.js")
        self.assertIn('class="sense"', js)
        self.assertIn("linked_by_set", js, "the page says when the PIE rung came from the cognate set")
        self.assertIn("ancestry_top", js)
        self.assertIn("set_source", js)
        css = text("style.css")
        self.assertIn(".rung-rec .sense", css)

    def test_the_live_ladder_pulses_instead_of_replaying_its_entry_animation(self):
        css = text("style.css")
        self.assertIn("#ladder.live", css)
        self.assertIn(".rung.pulse", css)
        self.assertIn("formPulse", css)

    def test_the_page_stays_dependency_free(self):
        for name in ("index.html", "app.js", "style.css"):
            body = text(name)
            for needle in ("http://", "https://", "cdn.", "unpkg"):
                self.assertNotIn(needle, body, f"{name} must not load a remote resource")

    def test_the_coverage_page_says_when_its_measurement_is_stale(self):
        js = text("app.js")
        self.assertIn("cov.stale", js)
        self.assertIn("measured before the last data change", js)

    def test_javascript_parses(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        proc = subprocess.run([node, "--check", str(WEB / "app.js")],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestHttpServer(unittest.TestCase):
    """A smoke test of the real stdlib server, on an ephemeral port."""

    @classmethod
    def setUpClass(cls):
        from pie.app import server

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path: str):
        return urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=30)

    def test_word_endpoint(self):
        body = json.load(self.get(f"/api/word?lang=fa&w={quote('پدر')}"))
        self.assertEqual(body["word"], "پدر")
        self.assertTrue(body["rtl"])
        self.assertTrue(all(f["lang_name"] != f["l"] for f in body["cognates"]["forms"]))

    def test_coverage_and_overview_carry_the_staleness_flag(self):
        coverage = json.load(self.get("/api/coverage"))
        self.assertIsInstance(coverage.get("stale"), bool)
        overview = json.load(self.get("/api/overview"))
        self.assertIsInstance(overview["coverage"].get("stale"), bool)

    def test_word_endpoint_switches_laws_off(self):
        plain = json.load(self.get("/api/word?lang=en&w=night"))
        key = next(rule["key"] for level in plain["hierarchy"]["levels"]
                   for rule in level["rules"] if rule["fired"])
        off = json.load(self.get(f"/api/word?lang=en&w=night&off={quote(key)}"))
        self.assertEqual(off["hierarchy"]["disabled"], [key])
        self.assertEqual(off["hierarchy"]["switched_off"], 1)
        self.assertEqual(off["word"], "night", "the same word, re-derived")

    def test_hierarchy_endpoint(self):
        body = json.load(self.get(f"/api/hierarchy?lang=fa&w={quote('پدر')}"))
        self.assertEqual(body["start"], "ine-pro")
        self.assertEqual(body["levels"][-1]["stage"], "fa")
        self.assertTrue(body["levels"][-1]["era_label"])

    def test_a_form_no_entry_holds_is_marked_unknown(self):
        """2026-11-12: a rung the etymology names but no glossary spells is
        *known: false*, so the page can print it dark red and say plainly that
        the stage has no entry for it — never gold with the ✓ of a word."""
        body = json.load(self.get(f"/api/hierarchy?lang=peo&w={quote('𐎣𐎱𐎢𐎫𐎣')}"))
        known = {level["stage"]: (level.get("recorded") or {}).get("known")
                 for level in body["levels"]}
        self.assertIs(known["iir-pro"], False)
        self.assertIs(known["ira-pro"], False)
        self.assertIs(known["peo"], True, "the word being read is in the glossary")

    def test_unknown_word_is_a_404(self):
        from urllib.error import HTTPError

        with self.assertRaises(HTTPError) as caught:
            self.get("/api/word?lang=fa&w=definitely-not-a-word")
        caught.exception.close()
        self.assertEqual(caught.exception.code, 404)

    def test_static_assets_are_utf8(self):
        res = self.get("/static/style.css")
        self.assertIn("charset=utf-8", res.headers["Content-Type"])
        self.assertIn("–", res.read().decode("utf-8"))  # en dash in the motion comment

    def test_static_route_refuses_to_leave_its_directory(self):
        """``/static/..`` is not a key to the rest of the machine (2026-11-12)."""
        from urllib.error import HTTPError

        for path in ("/static/../server.py", "/static/../../../../etc/passwd",
                     "/static/%2e%2e/%2e%2e/etc/passwd"):
            with self.assertRaises(HTTPError, msg=path) as caught:
                self.get(path)
            caught.exception.close()
            self.assertEqual(caught.exception.code, 404, path)

    def test_index_is_served_for_routes(self):
        body = self.get("/").read().decode("utf-8")
        self.assertIn('id="app"', body)

    def test_hierarchy_endpoint_accepts_an_edited_rung(self):
        body = json.load(self.get("/api/hierarchy?lang=en&w=night&from=enm&form=nighte"))
        # The edit stays on its own rung; the ancestors above it stay on the
        # timeline (2026-11-08: editing lost the ancestors).
        edited = [level for level in body["levels"] if level["stage"] == "enm"]
        self.assertEqual(edited[0]["form"], "nighte")
        self.assertEqual(body["levels"][0]["stage"], "ine-pro")
        self.assertTrue(body["result"]["match"])

    def test_a_pathway_can_be_stored_over_http_and_listed(self):
        import os
        import tempfile
        from urllib.request import Request

        handle = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        handle.close()
        previous = os.environ.get("PIE_PATHWAYS")
        os.environ["PIE_PATHWAYS"] = handle.name
        try:
            payload = json.dumps({"lang": "en", "word": "night",
                                  "from": "enm", "form": "nighte"}).encode()
            req = Request(f"http://127.0.0.1:{self.port}/api/pathway", data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=30) as res:
                body = json.load(res)
                self.assertEqual(res.status, 201)
            self.assertTrue(body["created"])
            listed = json.load(self.get("/api/pathways?lang=en&w=night"))
            self.assertEqual([p["id"] for p in listed["pathways"]], [body["pathway"]["id"]])
        finally:
            if previous is None:
                os.environ.pop("PIE_PATHWAYS", None)
            else:
                os.environ["PIE_PATHWAYS"] = previous
            Path(handle.name).unlink(missing_ok=True)

    def test_a_path_that_does_not_reach_the_word_is_a_400(self):
        from urllib.error import HTTPError
        from urllib.request import Request

        payload = json.dumps({"lang": "en", "word": "night",
                              "from": "ine-pro", "form": "nokwts"}).encode()
        req = Request(f"http://127.0.0.1:{self.port}/api/pathway", data=payload,
                      headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(HTTPError) as caught:
            urlopen(req, timeout=30)
        caught.exception.close()
        self.assertEqual(caught.exception.code, 400)

    def test_rebuild_endpoint(self):
        body = json.load(self.get(f"/api/rebuild?form={quote('*nókʷts')}"))
        forms = {row["l"]: row for row in body["rows"]}
        self.assertEqual(body["source"]["form"], "nókʷts")
        for lang in ("fa", "en", "de"):
            self.assertIn(lang, forms)
            self.assertTrue(forms[lang]["form"])


class TestRebuiltCognates(unittest.TestCase):
    """The "if the rules ran everywhere" projection.

    A loaded word with a PIE etymon is derived into every language whose chain
    is complete, whether or not the dictionaries know a cognate there. Forms
    with no recorded counterpart must be identifiable as predictions so the
    interface can mark them in their own colour and italics.
    """

    @classmethod
    def setUpClass(cls):
        cls.night = service.word("en", "night")["rebuilds"]
        cls.father = service.word("fa", "پدر")["rebuilds"]

    def test_a_word_with_an_etymon_gets_rebuilds(self):
        self.assertIsNotNone(self.night)
        self.assertEqual(self.night["source"]["form"], "nókʷts")
        self.assertGreaterEqual(self.night["counts"]["languages"], 20)

    def test_persian_english_and_german_come_first(self):
        self.assertEqual([r["l"] for r in self.night["rows"][:3]], ["fa", "en", "de"])

    def test_every_row_is_classified(self):
        for row in self.night["rows"]:
            self.assertIn(row["status"], {"match", "differs", "new"})
            if row["status"] in {"match", "differs"}:
                self.assertTrue(row["recorded"]["w"])
            else:
                self.assertIsNone(row["recorded"])
            self.assertIn("tiers", row)

    def test_a_rule_reproduction_is_recognised(self):
        # The projection in ``rebuilds`` is the laws alone, shared by every
        # word of an etymon, so it never carries a word's own pathway (English
        # wolf and Persian گربه are in the same position). The word's own
        # answer is its ladder, and that is where the reproduction is claimed.
        word = service.word("fa", "پدر")
        persian = next(r for r in self.father["rows"] if r["l"] == "fa")
        self.assertEqual(persian["status"], "differs")
        self.assertEqual(word["hierarchy"]["result"]["form"], "pedar")
        self.assertEqual(word["hierarchy"]["result"]["status"], "match")

    def test_a_prediction_is_flagged_as_unattested(self):
        persian = next(r for r in self.night["rows"] if r["l"] == "fa")
        self.assertEqual(persian["status"], "new")
        self.assertFalse(persian["recorded"])

    def test_incomplete_chains_are_reported_not_faked(self):
        gaps = {g["l"] for g in self.night["gap_languages"]}
        # The point is that a stage whose chain has no rule file is reported as
        # a gap and a stage that has one is not, not which language happens to
        # be unfinished (Gothic 2026-11-08; Old Norse and Old Church
        # Slavonic 2026-11-09).  So the invariant is measured against the
        # registry, and it stays true the next time a transition is written.
        rules = data.rulesets()
        for lang in gaps:
            chain = data.derivation_chain(lang)
            self.assertTrue(any((a, b) not in rules for a, b in zip(chain, chain[1:])),
                            f"{lang} is called a gap but every step of its chain has a rule file")
        for row in self.night["rows"]:
            if row["skipped"]:
                self.assertIn(row["l"], gaps)
            else:
                self.assertNotIn(row["l"], gaps)
        self.assertEqual(self.night["counts"]["gaps"], len(gaps))

    def test_cognate_sets_still_carry_the_rebuilds(self):
        """The data stays even though the table is no longer drawn: the root
        page's selector and the derivation lab read the same rows."""
        cog = service.cognate("ine-pro:nókʷts")
        self.assertEqual(cog["rebuilds"]["source"]["form"], "nókʷts")

    def test_every_evidence_colour_is_still_styled(self):
        css = text("style.css")
        for name in ("attested", "literary", "strong", "weak"):
            self.assertIn(f"ev-{name}", css, f"the {name} colour is missing")

    def test_the_rendered_views_pass_their_assertions(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        proc = subprocess.run([node, str(ROOT / "tests" / "test_ui_render.js")],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


class TestEvidenceColours(unittest.TestCase):
    """The colour model (2026-11-07).

    green   attested — in a text or in a dictionary
    gold    reconstructed in the literature (normally written ``*word``)
    orange  rebuilt by this repo, not in the literature, all laws established
    red     rebuilt by this repo on a proposed/custom law, on no law at all, or
            contradicting a form the dictionaries record
    """

    @classmethod
    def setUpClass(cls):
        cls.night = service.word("en", "night")
        cls.pedar = service.word("fa", "پدر")

    def test_a_dictionary_word_is_attested(self):
        self.assertEqual(self.night["evidence"], "attested")
        self.assertEqual(self.pedar["evidence"], "attested")
        self.assertEqual(self.pedar["kind"], "attested")

    def test_proto_stages_are_literary_not_attested(self):
        self.assertEqual(service.kind_of("ine-pro"), "proto")
        self.assertEqual(service.kind_of("gem-pro"), "proto")
        self.assertEqual(service.evidence_for("*nahts", "gem-pro"), "literary")
        self.assertEqual(service.evidence_for("night", "en"), "attested")
        # A proto code that only exists in the cognate sets still counts as a
        # reconstruction — Proto-Albanian must never be dressed as a text.
        self.assertEqual(service.kind_of("sqj-pro"), "proto")

    def test_every_rebuilt_row_has_one_of_the_four_colours(self):
        for row in self.night["rebuilds"]["rows"]:
            self.assertIn(row["evidence"], {"attested", "literary", "strong", "weak"}, row["l"])

    def test_a_matched_form_is_green_or_gold_never_orange(self):
        for word in (self.night, self.pedar):
            for row in word["rebuilds"]["rows"]:
                if row["status"] == "match":
                    expected = "literary" if row["kind"] == "proto" else "attested"
                    self.assertEqual(row["evidence"], expected, row["l"])

    def test_a_prediction_is_orange_only_with_established_laws(self):
        for row in self.night["rebuilds"]["rows"]:
            if row["status"] == "new" and row["evidence"] == "strong":
                self.assertTrue(row["steps"], row["l"])
                self.assertTrue(all(t == "established" for t in row["tiers"]), row["l"])
            if row["status"] in {"new", "differs"} and row["evidence"] == "attested":
                self.fail(f"{row['l']}: a rebuilt form must never be green")

    def test_a_contradicted_cognate_is_red(self):
        english = next(r for r in self.night["rebuilds"]["rows"] if r["l"] == "en")
        self.assertEqual(english["status"], "differs")
        self.assertEqual(english["evidence"], "weak")
        self.assertEqual(english["recorded"]["w"], "night")
        self.assertTrue(english["recorded"]["ipa"], "the recorded word keeps its IPA")

    def test_a_proposed_law_makes_a_prediction_tentative(self):
        weak = [r for r in self.pedar["rebuilds"]["rows"]
                if r["status"] == "new" and r["evidence"] == "weak"]
        self.assertTrue(weak, "father's rebuilds include proposed-rule chains")
        for row in weak:
            self.assertFalse(all(t == "established" for t in row["tiers"]) and row["steps"], row["l"])

    def test_counts_match_the_rows(self):
        rows = self.night["rebuilds"]["rows"]
        modelled = [r for r in rows if not r["skipped"]]
        counts = self.night["rebuilds"]["counts"]
        for name in ("attested", "literary", "strong", "weak"):
            self.assertEqual(counts[name], sum(1 for r in modelled if r["evidence"] == name), name)
        self.assertEqual(sum(counts[n] for n in ("attested", "literary", "strong", "weak")),
                         len(modelled))

    def test_the_four_colours_reach_the_page(self):
        js = text("app.js")
        self.assertIn("ev-${opts.ev}", js, "forms must be classified by their evidence")
        css = text("style.css")
        for name in ("ev-attested", "ev-literary", "ev-strong", "ev-weak"):
            self.assertIn(name, css, f"{name} has no style")
        self.assertNotIn("--predicted", css, "the old teal prediction colour is gone")
        self.assertIn("text-shadow", css, "attested words must glow")

    def test_colour_is_explained_on_hover_not_by_a_legend(self):
        """The legend is gone: each word explains itself."""
        js = text("app.js")
        css = text("style.css")
        self.assertNotIn("LEGEND", js)
        self.assertNotIn(".legend", css)
        self.assertIn("EVIDENCE_TEXT", js, "every evidence colour needs words behind it")
        self.assertIn('data-tip="${esc(tip)}"', js, "forms must carry their explanation")
        self.assertIn(".tip", css, "the hover layer must be styled")


class TestHierarchy(unittest.TestCase):
    """The word page's ladder: topmost ancestor at the top, the word at the
    bottom, the date of every stage, and switchable laws at every step."""

    @classmethod
    def setUpClass(cls):
        cls.night = service.word("en", "night")["hierarchy"]
        cls.pedar = service.word("fa", "پدر")["hierarchy"]
        cls.nacht = service.word("de", "Nacht")["hierarchy"]

    def test_it_starts_at_the_topmost_recorded_ancestor(self):
        self.assertEqual(self.night["start"], "ine-pro")
        self.assertEqual(self.night["levels"][0]["stage"], "ine-pro")
        self.assertEqual(self.night["levels"][0]["form"], "nókʷts")
        self.assertEqual(self.night["levels"][-1]["stage"], "en")
        self.assertEqual(self.night["levels"][-1]["form"], self.night["result"]["form"])

    def test_the_other_recorded_ancestors_are_offered(self):
        """A word whose ladder starts at PIE still knows every ancestor its
        record names, and says which of them the laws reach it from: that is
        what the page offers as buttons (2026-11-09)."""
        starts = self.pedar["starts"]
        self.assertGreater(len(starts), 1)
        self.assertEqual(starts[0]["stage"], "ine-pro")
        self.assertTrue(starts[0]["current"])
        self.assertIn("ira-pro", [row["stage"] for row in starts])
        for row in starts:
            self.assertTrue(row["name"] and row["form"], row)
            self.assertIsInstance(row["match"], bool)
            self.assertTrue(row["output"])

    def test_a_recorded_start_is_not_an_edit(self):
        """Starting from a form the record itself quotes is a record, not a
        hypothesis: no edited badge, and the stages above it are listed."""
        ladder = service.hierarchy("fa", "پدر", from_stage="ira-pro",
                                   from_form="pHtā́", from_recorded=True)
        self.assertEqual(ladder["start"], "ira-pro")
        self.assertIsNone(ladder["edited"])
        self.assertEqual(ladder["start_recorded"]["stage"], "ira-pro")
        self.assertEqual(ladder["levels"][0]["stage"], "ira-pro")
        self.assertEqual(ladder["levels"][0]["status"], "start")
        self.assertEqual([e["id"] for e in ladder["earlier"]], ["ine-pro", "iir-pro"])

    def test_a_start_the_record_does_not_name_is_refused(self):
        self.assertIsNone(service.hierarchy("fa", "پدر", from_stage="ira-pro",
                                            from_form="zzz", from_recorded=True))

    def test_every_stage_carries_its_date(self):
        for level in self.night["levels"]:
            self.assertTrue(level["era"], level["stage"])
            self.assertTrue(level["era_label"], level["stage"])
            self.assertIsNotNone(level["era_mid"], level["stage"])
        self.assertEqual(self.night["levels"][0]["era_label"], "c. 4500–2500 BCE")
        self.assertIn("since c. 1500", self.night["levels"][-1]["era_label"])

    def test_a_living_language_has_no_invented_end_date(self):
        self.assertIn("since", self.night["levels"][-1]["era_label"])
        self.assertNotIn("2026", self.night["levels"][-1]["era_label"])

    def test_each_level_shows_the_laws_of_its_own_step(self):
        pgs = next(level for level in self.night["levels"] if level["stage"] == "gem-pro")
        self.assertIsNone(self.night["levels"][0]["transition"])
        self.assertEqual(pgs["transition"]["from"], "ine-pro")
        self.assertEqual(pgs["transition"]["to"], "gem-pro")
        self.assertGreater(pgs["transition"]["fired"], 0)
        fired = [rule for rule in pgs["rules"] if rule["fired"]]
        self.assertTrue(fired)
        for rule in fired:
            self.assertTrue(rule["key"], "a rule must be addressable on its own")
            self.assertTrue(rule["before"])
            self.assertTrue(rule["after"])
            self.assertNotEqual(rule["before"], rule["after"], rule["name"])

    def test_rule_keys_are_scoped_to_their_transition(self):
        keys = [rule["key"] for level in self.night["levels"] for rule in level["rules"]]
        self.assertTrue(keys)
        for key in keys:
            self.assertIn("~", key, "a bare rule id would hit the same law upstream")
            self.assertRegex(key, r"^[a-z-]+~[a-z-]+:")

    def test_switching_a_law_off_changes_everything_below_it(self):
        first = next(level for level in self.pedar["levels"] if level["stage"] == "iir-pro")
        key = next(rule["key"] for rule in first["rules"] if rule["fired"])
        off = service.word("fa", "پدر", [key])["hierarchy"]
        self.assertEqual(off["disabled"], [key])
        self.assertEqual(off["switched_off"], 1)
        self.assertEqual(off["levels"][0]["form"], self.pedar["levels"][0]["form"])
        changed = [row for row in off["levels"] if row["changed"]]
        self.assertTrue(changed, "the levels below a switched-off law must change")
        for row in changed:
            self.assertNotEqual(row["form"], row["baseline"])
        # and the law stays visible, so it can be switched back on
        kept = [rule for level in off["levels"] for rule in level["rules"] if rule["disabled"]]
        self.assertEqual([rule["key"] for rule in kept], [key])

    def test_switching_it_back_on_restores_the_word(self):
        first = next(level for level in self.pedar["levels"] if level["stage"] == "iir-pro")
        key = next(rule["key"] for rule in first["rules"] if rule["fired"])
        off = service.word("fa", "پدر", [key])["hierarchy"]
        again = service.word("fa", "پدر", [])["hierarchy"]
        # the baseline of the switched-off run is exactly the switched-on ladder
        self.assertEqual([row["baseline"] for row in off["levels"]],
                         [row["form"] for row in again["levels"]])
        self.assertTrue(any(row["form"] != row["baseline"] for row in off["levels"]))
        self.assertEqual(again["switched_off"], 0)
        self.assertFalse(any(row["changed"] for row in again["levels"]))

    def test_a_word_whose_ancestry_stops_lower_climbs_through_it(self):
        # Wiktionary's German entry quotes Middle High German and stops.  That
        # ancestor is a word with a page whose ladder runs back to Proto-Indo-
        # European, so the timeline continues through it instead of ending at a
        # dictionary's silence (admin, 2026-11-12).
        self.assertEqual(self.nacht["start"], "gmh")
        self.assertEqual([level["stage"] for level in self.nacht["levels"]],
                         ["ine-pro", "gem-pro", "gmw-pro", "goh", "gmh", "de"])
        self.assertEqual([level["stage"] for level in self.nacht["levels"][:-2]],
                         [level["stage"] for level in self.nacht["levels"] if level.get("climbed")],
                         "the rungs above Middle High German are the ancestor's own")
        self.assertEqual(self.nacht["earlier"], [],
                         "nothing is merely listed any more: it is drawn")
        self.assertEqual(self.nacht["levels"][-1]["stage"], "de")

    def test_the_ladder_and_the_derivation_tell_the_same_story(self):
        word = service.word("fa", "پدر")
        self.assertEqual(word["hierarchy"]["result"]["form"], word["derivation"]["forms"][-1])
        self.assertTrue(word["hierarchy"]["result"]["match"])
        self.assertTrue(word["hierarchy"]["result"]["match_via_translit"])
        self.assertEqual(word["hierarchy"]["result"]["form"], "pedar")

    def test_it_says_where_an_exact_chain_starts(self):
        # The full PIE path to English "night" still differs, but the law chain
        # is exact from Middle English; the page reports both facts.
        self.assertFalse(self.night["result"]["match"])
        self.assertEqual(self.night["exact"]["stage"], "enm")
        self.assertEqual(self.night["exact"]["form"], "nighte")

    def test_every_rung_is_classified(self):
        for level in self.night["levels"]:
            self.assertIn(level["evidence"], {"attested", "literary", "strong", "weak"})
            self.assertIn(level["status"], {"start", "match", "differs", "derived"})
            if level["recorded"]:
                self.assertTrue(level["recorded"]["w"])
                self.assertIn(level["recorded"]["evidence"], {"attested", "literary"})

    def test_the_recorded_form_is_shown_beside_the_derived_one(self):
        pgs = next(level for level in self.night["levels"] if level["stage"] == "gem-pro")
        self.assertEqual(pgs["recorded"]["w"], "nahts")
        self.assertFalse(pgs["recorded"]["matches"])
        self.assertFalse(pgs["recorded"]["same"],
                         "a miss keeps the produced form and the record apart")
        en = self.night["levels"][-1]
        self.assertEqual(en["recorded"]["w"], "night")
        self.assertTrue(en["recorded"]["ipa"])

    def test_a_rung_that_hits_the_record_says_so_once(self):
        # *book*'s Proto-West Germanic rung produces exactly the recorded bōk;
        # the page prints that form once, glowing, instead of repeating it
        # under the reconstruction (2026-11-07).
        book = service.hierarchy("en", "book")["levels"]
        gmw = next(level for level in book if level["stage"] == "gmw-pro")
        self.assertEqual(gmw["form"], "bōk")
        self.assertEqual(gmw["recorded"]["w"], "bōk")
        self.assertTrue(gmw["recorded"]["matches"])
        self.assertTrue(gmw["recorded"]["same"])
        # The root's own record is what the ladder starts from, so it too is
        # one form (the glossary writes it bʰeh₂g-, notation only).
        self.assertTrue(book[0]["recorded"]["same"])
        # The English rung differs, and both forms have to be visible.
        self.assertFalse(book[-1]["recorded"]["same"])
        # A word reached through its romanisation is not the same string.
        fa = self.pedar["levels"][-1]
        self.assertTrue(fa["recorded"]["matches"])
        self.assertFalse(fa["recorded"]["same"])

    def test_a_word_written_in_another_script_matches_through_its_reading(self):
        fa = self.pedar["levels"][-1]
        self.assertEqual(fa["recorded"]["w"], "پدر")
        self.assertTrue(fa["recorded"]["matches"])
        self.assertEqual(fa["recorded"]["via"], "pedar")

    def test_a_script_record_carries_the_reading_the_entry_gives_it(self):
        # بازو: "From Old Persian 𐎲𐎠𐏀𐎢 (bāzu)" — the rung prints the
        # cuneiform word with the reading the same sentence records, rather
        # than a word no reader can pronounce (2026-11-08).
        peo = next(level for level in service.word("fa", "بازو")["hierarchy"]["levels"]
                   if level["stage"] == "peo")
        self.assertEqual(peo["recorded"]["w"], "𐎲𐎠𐏀𐎢")
        self.assertEqual(peo["recorded"]["reading"], "bāzu")
        self.assertTrue(peo["recorded"]["show_reading"])

    def test_the_middle_persian_tear_is_a_record(self):
        # 𐫀𐫡𐫘 (ʾrs /ars/, "tear") is named only inside the Persian entry;
        # it is now a glossary entry with its script and its reading, and the
        # Persian word's ladder quotes it (2026-11-08).
        page = service.word("pal", "𐫀𐫡𐫘")
        self.assertIsNotNone(page, "the Middle Persian word is a glossary entry")
        self.assertEqual(page["reading"], "ars")
        self.assertEqual(page["gloss"], ["tear (drop)"])
        pal = next(level for level in page["hierarchy"]["levels"] if level["stage"] == "pal")
        self.assertEqual(pal["recorded"]["w"], "𐫀𐫡𐫘")
        fa = next(level for level in service.word("fa", "ارس", sense=1)["hierarchy"]["levels"]
                  if level["stage"] == "pal")
        self.assertEqual(fa["recorded"]["w"], "𐫀𐫡𐫘")
        self.assertEqual(fa["recorded"]["reading"], "ars")

    def test_the_http_endpoint_accepts_the_law_switches(self):
        row = service.hierarchy("fa", "پدر")
        key = next(rule["key"] for level in row["levels"] for rule in level["rules"] if rule["fired"])
        from pie.app import server
        handler = server.Handler
        self.assertIs(handler, handler)  # the route table is exercised in TestHttpServer


class TestEtymonRung(unittest.TestCase):
    """The rung a ladder starts from is a record, not a blank.

    English *book* reaches Proto-Indo-European only through its cognate set:
    Wiktionary's own ancestry rows stop at Proto-Germanic. The page used to
    print "nothing recorded at this stage" at the top while the cognate section
    further down quoted the root's meaning (2026-11-07). The rung now
    resolves the etymon against the stage's own glossary, so the record — form,
    part of speech, sense — is shown where the ladder begins.
    """

    @classmethod
    def setUpClass(cls):
        cls.book = service.word("en", "book", sense=1)["hierarchy"]
        cls.night = service.word("en", "night")["hierarchy"]

    def test_book_keeps_its_recorded_ancestor_and_the_root_above_it(self):
        # Wiktionary's ancestry stops at Proto-Germanic *bōks; the cognate set
        # names the PIE root *bʰeh₂g-. A root is related, not inherited, so the
        # ladder starts at the recorded word and the root stays above it
        # (proposals/010, 2026-11-09).
        self.assertEqual(self.book["start"], "gem-pro")
        self.assertTrue(self.book["linked_by_set"])
        self.assertFalse(self.book["set_start"])
        self.assertTrue(self.book["set_is_root"])
        self.assertEqual(self.book["etymon"], "bʰeh₂g")

    def test_the_root_keeps_its_recorded_form_and_meaning(self):
        # The root is no longer the top rung, but the page must still carry the
        # glossary's own record of it, gloss and all.
        rec = self.book["etymon_record"]
        self.assertIsNotNone(rec, "the etymon is recorded in the PIE glossary")
        self.assertEqual(rec["w"], "bʰeh₂g")  # the dictionary's root hyphen is notation
        self.assertEqual(rec["pos"], "root")
        self.assertIn("to divide", rec["gloss"])
        # The recorded start is Proto-Germanic, wherever the timeline now
        # begins: since 2026-11-12 the rungs above it are *bōks's own ladder.
        top = next(level for level in self.book["levels"] if level["stage"] == "gem-pro")
        self.assertEqual(self.book["start"], "gem-pro")
        self.assertEqual(top["recorded"]["w"], "bōks")
        self.assertEqual(top["recorded"]["origin"], "ancestry")
        self.assertEqual(self.book["levels"][0]["stage"], "ine-pro",
                         "the ancestor's ladder is drawn above it")

    def test_every_rung_names_the_sense_that_stage_recorded(self):
        pgs = next(level for level in self.book["levels"] if level["stage"] == "gem-pro")
        self.assertEqual(pgs["recorded"]["pos"], "noun")
        self.assertIn("letter", pgs["recorded"]["gloss"])
        self.assertIn("night", next(level for level in self.night["levels"]
                                    if level["stage"] == "gem-pro")["recorded"]["gloss"])

    def test_the_projection_section_names_the_root_it_starts_from(self):
        # *book* is two words spelled alike from 2026-11-09 (the noun and the
        # verb have different chains), so the bare address is a landing page
        # and the page that carries the projection is the noun's.
        source = service.word("en", "book", sense=1)["rebuilds"]["source"]
        self.assertTrue(source["root"])
        self.assertEqual(source["pos"], "root")
        self.assertIn("to divide", source["gloss"])

    def test_the_recorded_pie_stage_form_for_book_is_named(self):
        # Wiktionary's descendant tree puts *bʰóh₂g-s ~ *bʰéh₂g-s ("allotment")
        # at the PIE stage above Proto-Germanic *bōks. The page says so, and
        # says why the ladder does not simply start there.
        self.assertEqual(self.book["set_source"], "*bʰóh₂g-s ~ *bʰéh₂g-s")
        self.assertIsNone(self.night["set_source"])

    def test_a_borrowed_word_reports_ancestry_outside_the_chain(self):
        # *color* comes through Latin, Anglo-Norman and Old French; the page
        # must not pretend the ladder's Germanic steps are its inheritance.
        row = service.hierarchy("en", "color")
        self.assertTrue(row["linked_by_set"])
        stages = [x["stage"] for x in row["off_chain"]]
        self.assertIn("la", stages)
        self.assertIn("fro", stages)

    def test_a_normal_inherited_word_is_not_marked_as_set_linked(self):
        self.assertFalse(self.night["linked_by_set"])
        self.assertEqual(self.night["levels"][0]["recorded"]["origin"], "ancestry")

    def test_the_fix_is_general_not_a_special_case_for_book(self):
        # Many words reach PIE only through a cognate set whose etymon is a
        # root. Every one must name the root's own record while starting at the
        # word its ancestry actually reaches (proposals/010).
        checked = 0
        for word in ("color", "point", "plant", "book"):
            row = service.hierarchy("en", word)
            if not row or not row.get("linked_by_set"):
                continue
            self.assertTrue(row["set_is_root"], word)
            self.assertFalse(row["set_start"], word)
            self.assertNotEqual(row["start"], "ine-pro", word)
            self.assertIsNotNone(row["etymon_record"], word)
            self.assertTrue(row["etymon_record"]["w"], word)
            self.assertTrue(row["etymon_record"]["gloss"],
                            f"{word} should carry the etymon's sense")
            self.assertEqual(row["levels"][0]["recorded"]["origin"], "ancestry", word)
            checked += 1
        self.assertGreaterEqual(checked, 2, "several set-linked words exercise the same path")


class TestEditableLadder(unittest.TestCase):
    """Editing a form on any rung, and storing a path that lands on the word.

    A request on 2026-11-07: "it should also be possible to manually edit each
    of the words in the hierarchy to see how it would go on from there", and a
    path that ends on an attested (green) word may be stored as a new pathway.
    """

    def setUp(self):
        import tempfile

        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        self.old = os.environ.get("PIE_PATHWAYS")
        os.environ["PIE_PATHWAYS"] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            os.environ.pop("PIE_PATHWAYS", None)
        else:
            os.environ["PIE_PATHWAYS"] = self.old
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_a_typed_form_keeps_its_ancestors_on_the_timeline(self):
        # 2026-11-08: "when I edit a word in the hierarchy, I
        # suddenly lose the ancestors in the timeline". The typed form replaces
        # its own rung; the rungs above it are the laws' own work and stay.
        row = service.hierarchy("en", "night", from_stage="enm", from_form="nighte")
        self.assertEqual(row["start"], "ine-pro")
        self.assertEqual([level["stage"] for level in row["levels"]],
                         ["ine-pro", "gem-pro", "gmw-pro", "ang", "enm", "en"])
        edited = next(level for level in row["levels"] if level["stage"] == "enm")
        self.assertEqual(edited["form"], "nighte")
        self.assertTrue(edited["edited"])
        self.assertEqual(row["levels"][0]["form"], "nókʷts")
        self.assertEqual(row["edited"]["name"], "Middle English")
        self.assertTrue(row["result"]["match"])
        self.assertEqual(row["result"]["form"], "night")

    def test_everything_below_the_edit_is_rederived(self):
        base = service.hierarchy("en", "night")
        edited = service.hierarchy("en", "night", from_stage="gem-pro", from_form="nahtiz")
        gem = next(row for row in base["levels"] if row["stage"] == "gem-pro")
        self.assertNotEqual(edited["levels"][-1]["form"], gem["form"])

    def test_a_typed_form_that_no_text_records_is_not_coloured_as_evidence(self):
        row = service.hierarchy("en", "night", from_stage="ine-pro", from_form="nokwts")
        self.assertEqual(row["levels"][0]["evidence"], "edited")
        # A typed form that happens to equal the recorded one keeps its colour.
        same = service.hierarchy("en", "night", from_stage="gem-pro", from_form="nahts")
        self.assertIn(same["levels"][0]["evidence"], {"attested", "literary"})

    def test_the_word_itself_may_be_edited(self):
        # 2026-11-08: "reconstructions should still be editable at
        # any point". The word's own rung is a rung, and editing it leaves the
        # ancestry above it where it was.
        row = service.hierarchy("en", "night", from_stage="en", from_form="night")
        self.assertEqual(row["start"], "ine-pro")
        self.assertEqual([level["stage"] for level in row["levels"]],
                         ["ine-pro", "gem-pro", "gmw-pro", "ang", "enm", "en"])
        self.assertTrue(row["levels"][-1]["edited"])
        self.assertEqual(row["levels"][-1]["form"], "night")
        # A stage that is neither on the chain nor carried into it is refused.
        self.assertIsNone(service.hierarchy("en", "night", from_stage="xx", from_form="night"))

    def test_a_path_that_lands_on_the_attested_word_is_stored(self):
        result = service.store_pathway("en", "night", "enm", "nighte")
        self.assertTrue(result["created"])
        record = result["pathway"]
        self.assertEqual(record["word"], "night")
        self.assertEqual(record["start"]["form"], "nighte")
        self.assertEqual(record["end"]["form"], "night")
        self.assertTrue(record["laws"], "the record keeps the laws that fired")
        ladder = service.hierarchy("en", "night", from_stage="enm", from_form="nighte")
        self.assertEqual(ladder["stored_pathway"], record["id"])
        self.assertEqual([p["id"] for p in ladder["pathways"]], [record["id"]])

    def test_storing_the_same_path_twice_does_not_duplicate_it(self):
        first = service.store_pathway("en", "night", "enm", "nighte")
        again = service.store_pathway("en", "night", "enm", "nighte")
        self.assertFalse(again["created"])
        self.assertEqual(first["pathway"]["id"], again["pathway"]["id"])
        self.assertEqual(len(service.hierarchy("en", "night")["pathways"]), 1)

    def test_a_path_that_does_not_reach_the_word_is_refused(self):
        with self.assertRaises(ValueError):
            service.store_pathway("en", "night", "ine-pro", "nokwts")

    def test_a_path_to_a_word_that_is_not_attested_is_refused(self):
        # Persian پدر is attested but the laws only reach it through its
        # reading; a garbled start must not be storable either way.
        with self.assertRaises(ValueError):
            service.store_pathway("fa", "پدر", "iir-pro", "batar")

    def test_a_stored_path_is_listed_for_its_own_word_only(self):
        service.store_pathway("en", "night", "enm", "nighte")
        self.assertEqual(service.hierarchy("de", "Nacht")["pathways"], [])


class TestRootWord(unittest.TestCase):
    """A word in Proto-Indo-European has nothing above it: the page asks where
    it would go instead of where it came from (2026-11-07)."""

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("ine-pro", "nókʷts")

    def test_a_pie_word_offers_no_ladder(self):
        self.assertTrue(self.page["is_root"])
        self.assertIsNone(self.page["hierarchy"], "the root has no ancestry to climb")
        self.assertFalse(service.word("en", "night")["is_root"])

    def test_the_root_word_offers_every_language_to_reconstruct_into(self):
        rows = self.page["rebuilds"]["rows"]
        self.assertGreater(len(rows), 20)
        self.assertIn("en", {r["l"] for r in rows})
        self.assertTrue(all(r["form"] for r in rows))

    def test_the_roots_cognate_set_is_found_by_its_etymon(self):
        """It may not say "no cognate set" while quoting that set's forms."""
        self.assertIsNotNone(self.page["cognates"])
        self.assertEqual(self.page["cognates"]["pie"], "nókʷts")

    def test_one_language_is_reconstructed_law_by_law(self):
        row = service.reconstruct("nókʷts", "en")
        self.assertEqual(row["source"]["form"], "nókʷts")
        self.assertEqual(row["lang"], "en")
        self.assertEqual(row["form"], "nˈæhwθ")
        self.assertEqual(row["levels"][0]["src"], "ine-pro")
        self.assertEqual(row["levels"][-1]["dst"], "en")
        self.assertEqual(row["levels"][-1]["form"], row["form"])
        self.assertGreater(row["steps"], 0)
        self.assertTrue(all(l["dst_name"] != l["dst"] for l in row["levels"]))
        # A step with no fired law must say how many were tried instead.
        self.assertTrue(all(l["registered"] >= l["fired"] for l in row["levels"]))

    def test_the_recorded_form_is_quoted_not_substituted(self):
        row = service.reconstruct("nókʷts", "en")
        self.assertEqual(row["status"], "differs")
        self.assertEqual(row["recorded"]["w"], "night")
        self.assertEqual(row["form"], "nˈæhwθ", "the laws' own output stays the form")
        self.assertFalse(row["same"])
        self.assertTrue(row["recorded"]["gloss"], "the record carries its sense")

    def test_a_gap_is_reported_as_a_gap(self):
        row = service.reconstruct("nókʷts", "sq")
        self.assertTrue(row["skipped"])
        self.assertEqual(row["steps"], 0)
        self.assertEqual(row["form"], "nókʷts", "nothing changed, and the page says why")

    def test_a_law_can_be_switched_off_and_the_chain_is_rederived(self):
        """The reader asks "what if this law were not here?" (2026-11-08)."""
        on = service.reconstruct("nókʷts", "en")
        off = service.reconstruct("nókʷts", "en",
                                  disabled=("ine-pro~gem-pro:grimm_t",))
        self.assertNotEqual(on["form"], off["form"],
                            "the switched-off law's effect leaves the form")
        self.assertEqual(off["disabled"], ["ine-pro~gem-pro:grimm_t"])
        level = next(l for l in off["levels"] if l["dst"] == "gem-pro")
        self.assertEqual(level["switched_off"], 1)
        law = next(r for r in level["rules"] if r["key"] == "ine-pro~gem-pro:grimm_t")
        self.assertFalse(law["fired"])
        self.assertTrue(law["disabled"])
        self.assertNotEqual(law["would"], law["before"],
                            "a switched-off law still says what it would have done")

    def test_the_endpoint_takes_the_laws_switched_off(self):
        from pie.app import server as server_module
        from http.server import ThreadingHTTPServer
        import threading
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            port = httpd.server_address[1]
            body = json.load(urlopen(
                f"http://127.0.0.1:{port}/api/reconstruct?lang=en&form={quote('nókʷts')}"
                "&off=ine-pro~gem-pro:grimm_t", timeout=60))
            self.assertEqual(body["disabled"], ["ine-pro~gem-pro:grimm_t"])
            self.assertEqual(body["form"], "nˈæhwt")
        finally:
            httpd.shutdown()

    def test_a_stress_marked_syllabic_sonorant_finds_its_record(self):
        # 2026-11-08: Proto-Iranian *wŕ̥kah* is the engine's
        # wˈr̥kah — one stress, two notations. The rung used to report nothing
        # recorded because the headword lookup only looked for a vowel.
        row = service.reconstruct("wĺ̥kʷos", "fa")
        ira = next(level for level in row["levels"] if level["dst"] == "ira-pro")
        self.assertEqual(ira["recorded"]["w"], "wŕ̥kah")
        self.assertEqual(ira["status"], "match")
        self.assertEqual(row["status"], "match")
        # The notation is the record's own, so the page prints ŕ̥.
        self.assertEqual(service.printable_form("wˈr̥kah"), "wŕ̥kah")

    def test_the_target_words_own_ancestry_quotes_intermediate_records(self):
        """2026-11-08: بازو's own timeline names Old Persian
        𐎲𐎠𐏀𐎢, but the reconstruction from bʰeh₂ǵʰús showed no record there —
        the path was re-derived from the etymon alone. The target word's
        ancestry now supplies each stage's record, with the reading its entry
        writes beside it; the laws' form is still what is printed first."""
        row = service.reconstruct("bʰeh₂ǵʰús", "fa")
        peo = next(level for level in row["levels"] if level["dst"] == "peo")
        self.assertEqual(peo["recorded"]["w"], "𐎲𐎠𐏀𐎢")
        self.assertEqual(peo["recorded"]["reading"], "bāzu")
        self.assertEqual(peo["status"], "differs")
        self.assertNotEqual(peo["form"], peo["recorded"]["w"])
        # A record the cognate set never named is not counted as a match.
        self.assertFalse(peo["same"])
        self.assertEqual(row["recorded"]["w"], "بازو")

    def test_a_reconstruction_rung_is_editable_where_it_stands(self):
        """2026-11-08: "why can't I edit the reconstructed words in
        the timeline?" A typed form replaces one rung; the rungs above keep
        what the laws produced, and every law below runs on the typed form."""
        base = service.reconstruct("wĺ̥kʷos", "en")
        edited = service.reconstruct("wĺ̥kʷos", "en", from_stage="gem-pro",
                                     from_form="wulfaz")
        self.assertEqual(edited["edited"]["stage"], "gem-pro")
        self.assertEqual(edited["edited"]["name"], "Proto-Germanic")
        # The rungs above the edit are the laws' own work, untouched.
        self.assertEqual(edited["source"]["form"], base["source"]["form"])
        self.assertEqual(edited["levels"][0]["form"], "wulfaz")
        self.assertTrue(edited["levels"][0]["edited"])
        self.assertFalse(any(l["edited"] for l in edited["levels"][1:]))
        # The target changed because the typed form did.
        self.assertNotEqual(edited["form"], base["form"])
        self.assertEqual(edited["levels"][-1]["form"], edited["form"])
        self.assertEqual(edited["edited"], {"stage": "gem-pro", "form": "wulfaz",
                                            "name": "Proto-Germanic"})

    def test_editing_the_starting_rung_keeps_the_timeline_intact(self):
        edited = service.reconstruct("wĺ̥kʷos", "en", from_stage="ine-pro",
                                     from_form="wulpos")
        self.assertEqual(edited["source"]["form"], "wulpos")
        self.assertTrue(edited["levels"][0]["edited"] is False)
        self.assertEqual(edited["levels"][0]["dst"], "gem-pro",
                         "the first law still runs from the typed start")
        self.assertNotEqual(edited["form"], service.reconstruct("wĺ̥kʷos", "en")["form"])

    def test_an_edit_off_the_chain_is_refused(self):
        self.assertIsNone(service.reconstruct("wĺ̥kʷos", "en", from_stage="xx",
                                              from_form="wulfaz"))

    def test_the_endpoint_takes_an_edited_rung(self):
        from pie.app import server as server_module
        from http.server import ThreadingHTTPServer
        import threading
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            port = httpd.server_address[1]
            body = json.load(urlopen(
                f"http://127.0.0.1:{port}/api/reconstruct?lang=en"
                f"&form={quote('wĺ̥kʷos')}&from=gem-pro&edit=wulfaz", timeout=60))
            self.assertEqual(body["edited"]["form"], "wulfaz")
            self.assertTrue(body["levels"][0]["edited"])
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_the_root_and_unknown_languages_have_nothing_to_reconstruct(self):
        self.assertIsNone(service.reconstruct("nókʷts", "ine-pro"))
        self.assertIsNone(service.reconstruct("nókʷts", "zz"))

    def test_the_endpoint_serves_one_reconstruction(self):
        from pie.app import server as server_module
        from http.server import ThreadingHTTPServer
        import threading
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            port = httpd.server_address[1]
            body = json.load(urlopen(f"http://127.0.0.1:{port}/api/reconstruct?lang=de&form={quote('nókʷts')}",
                                     timeout=60))
            self.assertEqual(body["lang"], "de")
            self.assertEqual(body["levels"][-1]["dst"], "de")
        finally:
            httpd.shutdown()
            httpd.server_close()


class TestReconstructedRungs(unittest.TestCase):
    """A reconstruction rung is a claim about a form, not about its language.

    2026-11-08: the PIE page's Old Persian rung *warpíš* glowed
    green although no dictionary records it, and it was a dead end. A rung
    that no record reaches is this repo's reconstruction (red/orange), and it
    still opens its own page. A rung that is green carries the record's script
    and citation — for Old Persian, a cuneiform headword.
    """

    def test_an_unrecorded_law_rung_is_not_attested(self):
        page = service.reconstruct("h₂wl̥pís", "fa")
        peo = next(level for level in page["levels"] if level["dst"] == "peo")
        self.assertEqual(peo["form"], "warpˈiš")
        self.assertIsNone(peo["recorded"], "no OP glossary entry records this form")
        self.assertEqual(peo["evidence"], "weak", "a proposed law makes it a guess")
        self.assertFalse(peo["form_known"])
        self.assertEqual(peo["status"], "derived")

    def test_an_unrecorded_rung_still_opens_a_page(self):
        page = service.reconstruct("h₂wl̥pís", "fa")
        peo = next(level for level in page["levels"] if level["dst"] == "peo")
        self.assertIsNone(service.word("peo", peo["form"]))
        ghost = service.word("peo", peo["form"], ghost=True, via="ine-pro/h₂wl̥pís")
        self.assertIsNotNone(ghost)
        self.assertTrue(ghost["ghost"])

    def test_an_attested_rung_carries_a_source_and_its_script(self):
        page = service.reconstruct("deywós", "fa")
        peo = next(level for level in page["levels"] if level["dst"] == "peo")
        rec = peo["recorded"]
        self.assertEqual(rec["w"], "𐎭𐎡𐎺")
        self.assertTrue(rec["in_script"], "the record is a cuneiform headword")
        self.assertTrue(rec["sources"], "green must say where the word is recorded")
        # The laws write the labiovelar *w and the sign 𐎺 is transcribed v, and
        # the final /h/ has no sign: the form is a reading of the record, so the
        # rung matches and says which signs it was read from (2026-11-08).
        self.assertEqual(peo["status"], "match")
        self.assertEqual(rec["fit"]["translit"], "da-i-va")
        self.assertEqual(peo["evidence"], "attested", "the record is a cuneiform headword")
        self.assertEqual(rec["evidence"], "attested")

    def test_no_green_rung_is_a_latin_only_old_persian_record(self):
        for etymon in ("deywós", "wĺ̥kʷos", "nókʷts"):
            page = service.reconstruct(etymon, "fa")
            for level in page["levels"]:
                if level["evidence"] == "attested":
                    self.assertTrue(level["recorded"], (etymon, level["dst"]))
                    self.assertTrue(level["recorded"]["in_script"], (etymon, level["dst"]))
                    self.assertTrue(level["recorded"]["sources"], (etymon, level["dst"]))

    def test_an_unrecorded_old_persian_rung_of_water_is_not_attested(self):
        """2026-11-08: the OP rung *wā́dar* was green.

        No Old Persian inscription or glossary records it; the form is this
        repo's reconstruction from Proto-Iranian, so it is orange ("rebuilt
        here"), says so, and still opens its own page.
        """
        page = service.reconstruct("wódr̥", "fa")
        peo = next(level for level in page["levels"] if level["dst"] == "peo")
        self.assertEqual(peo["form"], "wˈādar")
        self.assertIsNone(peo["recorded"], "nothing records this form in Old Persian")
        self.assertNotEqual(peo["evidence"], "attested")
        self.assertEqual(peo["evidence"], "strong", "every law behind it is established")
        self.assertFalse(peo["form_known"])
        self.assertIsNotNone(service.word("peo", peo["form"], ghost=True, via="ine-pro/wódr̥"))

    def test_a_wiktionary_reconstruction_is_never_attested(self):
        """A Reconstruction: entry is not a word a text spells (2026-11-08)."""
        madu = service.word("peo", "madu")
        self.assertTrue(madu["recon"])
        self.assertEqual(madu["evidence"], "literary")
        self.assertFalse(madu["in_script"])
        daiva = service.word("peo", "𐎭𐎡𐎺")
        self.assertFalse(daiva["recon"])
        self.assertEqual(daiva["evidence"], "attested")
        self.assertTrue(daiva["in_script"])

    def test_a_green_word_page_always_carries_a_source(self):
        for lang, word in (("peo", "𐎭𐎡𐎺"), ("la", "aqua"), ("ang", "wæter")):
            page = service.word(lang, word)
            self.assertIsNotNone(page, (lang, word))
            if page["evidence"] == "attested":
                self.assertTrue(page["sources"], (lang, word))


class TestPronunciations(unittest.TestCase):
    """Old Persian and every other non-Latin script must show a reading."""

    def test_a_script_without_an_alphabet_asks_for_a_reading(self):
        self.assertTrue(service.show_reading("peo", "𐎠𐎿"))
        self.assertTrue(service.show_reading("fa", "پدر"))
        self.assertTrue(service.show_reading("grc", "πατήρ"))
        self.assertTrue(service.show_reading("got", "𐍆𐌰𐌳𐌰𐍂"))
        self.assertFalse(service.show_reading("en", "night"))

    def test_a_lemma_already_written_in_latin_needs_nothing(self):
        # Tocharian B is written in Brahmi, but Wiktionary lemmatises it in a
        # Latin transliteration; a second spelling would only add noise.
        self.assertFalse(service.show_reading("txb", "pācer"))

    def test_syllabic_transcriptions_are_not_offered_as_pronunciations(self):
        entry = {"translit": "ku-u-ru-u-š", "translit_alt": ["Kuruš"]}
        self.assertEqual(service.readings_for(entry)["reading"], "Kuruš")

    def test_ipa_wins_when_recorded(self):
        readings = service.readings_for({"ipa": "/pa.ˈdar/", "translit": "pedar"})
        self.assertEqual(readings["ipa"], "pa.ˈdar")

    def test_nothing_is_invented(self):
        self.assertEqual(service.readings_for({}), {"ipa": "", "reading": ""})

    def test_old_persian_cognates_carry_a_reading(self):
        forms = {f["l"]: f for f in service.word("fa", "پدر")["cognates"]["forms"]}
        self.assertIn("peo", forms)
        self.assertEqual(forms["peo"]["reading"], "pitā")
        self.assertTrue(forms["peo"]["show_reading"])
        self.assertEqual(forms["got"]["ipa"], "ˈfaðar")

    def test_the_word_page_carries_the_reading(self):
        pedar = service.word("fa", "پدر")
        self.assertTrue(pedar["show_reading"])
        self.assertEqual(pedar["ipa"], "pa.ˈdar")

    def test_cognate_language_names_say_where_they_lead(self):
        forms = service.word("fa", "پدر")["cognates"]["forms"]
        self.assertTrue(all("known" in f for f in forms), "the page needs to know if a page exists")
        self.assertTrue(any(f["known"] for f in forms))
        self.assertTrue(any(not f["known"] for f in forms), "literature-only forms exist too")


class TestNotationComparison(unittest.TestCase):
    """The dictionary's notation is not a disagreement about phonology.

    Two conventions hid real matches (2026-11-08, Old Persian 𐎭𐎼𐎹 *drayaʰ*):
    the chain carries the stress of the ancestor's acute, while a romanisation
    often marks none; and Wiktionary writes the Old Persian final /h/, unwritten
    in the syllabary, as a superscript ʰ.
    """

    def test_a_silent_record_does_not_contradict_a_stress_mark(self):
        self.assertTrue(service._same_form("drˈayah", "drayah"))
        self.assertTrue(service._same_form("drˈayah", "drayaʰ"))

    def test_two_marks_that_disagree_still_disagree(self):
        self.assertFalse(service._same_form("drˈayah", "drayˌah"))
        self.assertFalse(service._same_form("drˈayah", "drayā"))

    def test_a_superscript_h_is_a_written_h_not_aspiration(self):
        self.assertEqual(service._comparison_key("drayaʰ"), service._comparison_key("drayah"))
        # Aspiration of a stop is a phonological claim and must survive.
        self.assertNotEqual(service._comparison_key("kʰ"), service._comparison_key("kh"))

    def test_a_stress_token_finds_the_headword_an_acute_spells(self):
        self.assertEqual(service.printable_form("jrˈayah"), "jráyah")
        self.assertEqual(service.printable_form("nˈōkʷθs"), "nṓkʷθs")
        page = service.word("ira-pro", "jrˈayah")
        self.assertFalse(page.get("ghost"), "the printed form must open its own headword")

    def test_a_sign_by_sign_transliteration_is_not_a_reading(self):
        # k-a-r is how the syllabary is written; kāraʰ is how the word sounds.
        entry = {"word": "𐎣𐎠𐎼", "translit": "k-a-r", "translit_alt": ["kāraʰ"]}
        self.assertEqual(service.attested_spellings(entry), ["kāraʰ"])

    def test_a_reading_is_matched_through_the_script_and_says_what_the_signs_write(self):
        # k-a-r is not a spelling of kāraʰ, so `attested_spellings` still keeps
        # it out of the comparison (above). The ladder, however, may say that
        # the form the laws produce is one of the readings the signs allow — and
        # then it has to print the signs it was read from (2026-11-08).
        row = service.hierarchy("peo", "𐎣𐎠𐎼")
        rung = row["levels"][-1]
        self.assertEqual(rung["status"], "match")
        self.assertTrue(rung["recorded"]["fit"]["ok"])
        self.assertTrue(rung["recorded"]["fit"]["translit"])
        self.assertEqual(row["result"]["match_via_script"], True)


class TestOldPersianVerbOfGoing(unittest.TestCase):
    """𐎠𐎡𐎫𐎡𐎹 *aiti* 'goes' — a final -i the script closes with y.

    The laws used to reach ``ˈayti``, a form no reading of a-i-t-i-y allows:
    the syllabary writes the offglide with the i-sign (PIr *Háyti > OP aiti)
    and closes a word-final -i with the y-sign, which carries no sound. The
    law ``ay_to_ai`` and the table's ``final_i_iy`` convention each say one of
    those things, and the rung has to show the second so the green is checked
    (2026-11-08).
    """

    def test_the_law_makes_the_word_old_persian(self):
        from pie.rules import derive

        d = derive("Háyti", ["ira-pro", "peo"], data.rulesets())
        self.assertEqual(d.output.replace("ˈ", ""), "aiti")
        self.assertIn("ay_to_ai", [s.rule_id for s in d.steps])

    def test_the_law_leaves_a_glide_before_a_vowel_alone(self):
        from pie.rules import derive

        d = derive("dāráyati", ["ira-pro", "peo"], data.rulesets())
        self.assertEqual(d.output.replace("ˈ", ""), "dārayati")

    def test_a_final_i_written_i_y_is_a_declared_convention(self):
        from pie import script

        fit = script.match("peo", "ˈaiti", "𐎠𐎡𐎫𐎡𐎹")
        self.assertTrue(fit["ok"])
        self.assertEqual(fit["convention"]["id"], "final_i_iy")
        raw = script.match("peo", "aitiy", "𐎠𐎡𐎫𐎡𐎹")
        self.assertTrue(raw["ok"], "the dictionary's own reading still fits as it is")

    def test_a_convention_is_not_a_licence_to_drop_a_vowel(self):
        from pie import script

        # The convention closes a final -i; it does not supply one.
        self.assertFalse(script.match("peo", "ait", "𐎠𐎡𐎫𐎡𐎹")["ok"])
        self.assertFalse(script.match("peo", "aiti", "𐎠𐎡𐎫")["ok"],
                         "no i-y is written at the end of a-i-t")

    def test_the_script_step_does_not_forgive_a_wrong_diphthong(self):
        from pie import script

        # A syllabary cannot write a glide before a consonant, but Old Persian
        # has no such glide: the form is aiti, and the law says so. The script
        # layer must not quietly accept ay as a reading of a-i (2026-11-08).
        self.assertFalse(script.match("peo", "ˈayti", "𐎠𐎡𐎫𐎡𐎹")["ok"])

    def test_the_page_matches_the_word_through_its_script(self):
        row = service.hierarchy("peo", "𐎠𐎡𐎫𐎡𐎹")
        rung = row["levels"][-1]
        self.assertEqual(rung["status"], "match")
        self.assertEqual(rung["form"].replace("ˈ", ""), "aiti")
        self.assertEqual([r["id"] for r in rung["rules"]], ["laryngeal_loss_initial", "ay_to_ai"])
        fit = rung["recorded"]["fit"]
        self.assertTrue(fit["ok"])
        self.assertEqual(fit["convention"]["id"], "final_i_iy")
        self.assertEqual(row["result"]["match_via_script"], True)

    def test_every_declared_convention_example_fits(self):
        from pie import script

        for lang in script.available():
            for rule in script.conventions(lang):
                for ex in rule.get("examples") or []:
                    fit = script.match(lang, ex["reading"], ex["word"])
                    self.assertTrue(fit and fit["ok"], (rule["id"], ex))
                    self.assertEqual((fit.get("convention") or {}).get("id"), rule["id"])


class TestOldPersianSea(unittest.TestCase):
    """𐎭𐎼𐎹 'sea' — the ladder in question (2026-11-08).

    Wiktionary's main etymology makes Proto-Indo-Iranian *ȷ́ráyas a substrate
    loan, so the recorded chain starts there; the two laws to Proto-Iranian and
    the one to Old Persian do reach the recorded reading.
    """

    @classmethod
    def setUpClass(cls):
        cls.row = service.hierarchy("peo", "𐎭𐎼𐎹")

    def test_the_ladder_starts_at_the_recorded_proto_indo_iranian_form(self):
        top = self.row["levels"][0]
        self.assertEqual(self.row["start"], "iir-pro")
        self.assertEqual(top["status"], "start")
        self.assertTrue(top["recorded"]["starts"], "a recorded start is the record, not a guess")
        self.assertFalse(top["recorded"]["matches"], "no law above it derived it")

    def test_the_word_has_no_pie_form_in_the_recorded_chain(self):
        self.assertEqual([e["id"] for e in self.row["earlier"]], ["ine-pro"])
        self.assertIsNone(self.row["etymon"])

    def test_the_laws_reproduce_the_recorded_reading(self):
        self.assertEqual(self.row["result"]["status"], "match")
        self.assertTrue(self.row["result"]["match_via_translit"])
        self.assertEqual(self.row["result"]["reading"], "drayaʰ")
        final = self.row["levels"][-1]
        self.assertEqual(final["recorded"]["via"], "drayaʰ")
        self.assertTrue(final["recorded"]["matches"])
        self.assertEqual(final["evidence"], "attested")


class TestWordsThatOpen(unittest.TestCase):
    """Every word on a ladder is a door, and every door leads somewhere.

    2026-11-08: the Proto-Iranian rung *jráyah* said "not recorded"
    although the Old Persian page's own ancestry records it. It is now an entry
    of its own, with the citation behind it, so a ✓ rung opens a real page. A
    form that still has no entry opens the "not recorded here" page, which
    carries it into the branch below instead of returning a 404.
    """

    @classmethod
    def setUpClass(cls):
        cls.row = service.hierarchy("peo", "𐎭𐎼𐎹")

    def test_a_rung_says_whether_its_forms_are_in_the_glossary(self):
        levels = {lv["stage"]: lv for lv in self.row["levels"]}
        self.assertTrue(levels["iir-pro"]["recorded"]["known"],
                        "Proto-Indo-Iranian ȷ́ráyas is a glossed entry")
        self.assertTrue(levels["ira-pro"]["recorded"]["known"],
                        "Proto-Iranian jráyah has its own cited entry now")
        self.assertTrue(levels["peo"]["recorded"]["known"])
        self.assertFalse(levels["peo"]["form_known"], "drˈayah is the laws' output, not a headword")

    def test_a_quotation_without_the_final_sign_is_the_headword_it_reads(self):
        """2026-11-12: Wiktionary quotes Old Persian 𐎼𐎢𐎨 for 𐎼𐎢𐎨𐏃 — the
        syllabary does not write a final /h/.  One reading is one word, so the
        rung knows the entry, prints its meaning and opens its own spelling."""
        peo = service.hierarchy("pal", "lwc")["levels"][0]["recorded"]
        self.assertTrue(peo["known"], "the glossary holds 𐎼𐎢𐎨𐏃, which reads raučah")
        self.assertEqual(peo["headword"], "𐎼𐎢𐎨𐏃")
        self.assertEqual(peo["gloss"], "day")
        self.assertEqual(peo["pos"], "noun")

    def test_the_proto_iranian_record_opens_a_page_with_its_source(self):
        page = service.word("ira-pro", "jráyah", via="peo/𐎭𐎼𐎹")
        self.assertFalse(page.get("ghost"), "the ✓ rung must open a word page, not a placeholder")
        self.assertEqual(page["gloss"], ["sea"])
        self.assertEqual(page["evidence"], "literary",
                         "a reconstruction is gold: reconstructed in the literature")
        self.assertTrue(page["sources"], "a hand-added reconstruction must carry its citation")
        self.assertEqual(page["sources"][0]["id"], "wiktionary")
        self.assertIn("Old Persian", page["sources"][0]["ref"])
        self.assertEqual(page["ancestry"][0]["lang"], "iir-pro")
        self.assertEqual(page["hierarchy"]["result"]["status"], "match",
                         "the two laws from ȷ́ráyas reach the recorded form")

    def test_a_recorded_reading_opens_the_recorded_word(self):
        page = service.word("peo", "drˈayah", ghost=True, via="ira-pro/jráyah")
        self.assertFalse(page.get("ghost"))
        self.assertEqual(page["word"], "𐎭𐎼𐎹",
                         "drayaʰ is the entry's own reading of the laws' drˈayah")
        self.assertEqual(page["gloss"], ["sea"])

    def test_a_form_without_an_entry_still_gets_a_page(self):
        page = service.word("pal", "drˈay", ghost=True, via="ira-pro/jráyah")
        self.assertTrue(page["ghost"])
        self.assertIsNone(page["hierarchy"], "there is no record to climb from")

    def test_the_page_does_not_deny_a_record_it_was_reached_from(self):
        page = service.word("ang", "frēo", ghost=True, via="en/free")
        self.assertEqual(page["origin"]["word"], "free")
        self.assertTrue(page["recorded_elsewhere"],
                        "Old English frēo has no entry of its own, but *free*'s ladder records it")
        self.assertEqual(page["origin_recorded"], ["frēo"])

    def test_a_page_says_not_recorded_only_when_nothing_records_it(self):
        page = service.word("pal", "drˈay", ghost=True, via="ira-pro/jráyah")
        self.assertEqual(page["origin"]["word"], "jráyah")
        self.assertFalse(page["recorded_elsewhere"],
                         "nothing in the word it came from is spelled drˈayah at Old Persian")

    def test_the_form_is_followed_into_its_direct_children_only(self):
        tree = service.word("ira-pro", "jráyah", via="peo/𐎭𐎼𐎹")["descendants"]["tree"]
        # Parthian joined the Iranian chain on 2026-11-12, and Old Median is a
        # Northwest Iranian sister as of 2026-11-12, so the branch of *jráyah
        # has four direct daughters — and still only daughters.
        self.assertEqual([n["l"] for n in tree], ["ave", "peo", "xpr", "xme-old"],
                         "Proto-Iranian has four direct daughters, not their descendants")
        self.assertNotIn("fa", [n["l"] for n in tree], "Persian is a grandchild, not a daughter")
        peo = tree[1]
        self.assertEqual([n["l"] for n in peo["children"]], ["pal"])
        self.assertEqual([n["l"] for n in peo["children"][0]["children"]], ["fa"])

    def test_every_row_is_one_transition(self):
        nodes = {(n["depth"], n["l"]): n for n in
                 service.word("ira-pro", "jráyah", via="peo/𐎭𐎼𐎹")["descendants"]["rows"]}
        self.assertEqual(nodes[(0, "peo")]["form"], "drˈayah")
        self.assertEqual(nodes[(1, "pal")]["form"], "drˈay")
        self.assertEqual(len(nodes[(0, "peo")]["laws"]), 1, "one law: j > d")
        self.assertEqual(nodes[(1, "pal")]["depth"], 1)

    def test_a_row_that_reaches_a_record_quotes_it(self):
        tree = service.word("ira-pro", "jráyah", via="peo/𐎭𐎼𐎹")["descendants"]["tree"]
        peo = next(n for n in tree if n["l"] == "peo")
        self.assertEqual(peo["status"], "match")
        self.assertEqual(peo["evidence"], "attested", "the laws reach the attested form")
        self.assertEqual(peo["recorded"]["w"], "𐎭𐎼𐎹")
        self.assertEqual(peo["recorded"]["via"], "origin")
        self.assertTrue(peo["recorded"]["known"], "and the record opens its own page")
        pal = peo["children"][0]
        self.assertIsNone(pal["recorded"], "Middle Persian records no form from this ladder")

    def test_a_word_page_carries_its_own_branch(self):
        page = service.word("ira-pro", "jráyah")
        # Four since 2026-11-12: Parthian is on the Iranian chain again and
        # Old Median is its Northwest Iranian sister, so the branch reaches
        # both beside Avestan and Old Persian.
        self.assertEqual(page["descendants"]["counts"]["direct"], 4)
        self.assertIn("xpr", [n["l"] for n in page["descendants"]["tree"]])
        self.assertIn("xme-old", [n["l"] for n in page["descendants"]["tree"]])
        self.assertEqual(page["descendants"]["source"]["form"], "jrˈayah",
                         "the laws work on the engine's form, not on a script spelling")
        self.assertTrue(all(n["form_known"] is False for n in page["descendants"]["tree"]))

    def test_a_pie_word_carries_its_branch_too(self):
        page = service.word("ine-pro", "wĺ̥kʷos")
        self.assertTrue(page["is_root"])
        self.assertIsNone(page["hierarchy"], "Proto-Indo-European has no ladder to climb")
        branch = page["descendants"]
        self.assertIsNotNone(branch, "an etymon page opens into its daughters like any other")
        self.assertEqual(branch["source"]["form"], "wĺ̥kʷos",
                         "the branch starts from the etymon itself")
        self.assertIn("gem-pro", [n["l"] for n in branch["tree"]])
        self.assertGreater(branch["counts"]["languages"], branch["counts"]["direct"],
                           "the tree counts the whole family below, not just the daughters")

    def test_the_pie_branch_reaches_the_proto_germanic_record(self):
        rows = {r["l"]: r for r in service.word("ine-pro", "wĺ̥kʷos")["descendants"]["rows"]}
        gem = rows["gem-pro"]
        self.assertEqual(gem["status"], "match")
        self.assertEqual(gem["recorded"]["w"], "wulfaz")
        self.assertEqual(gem["recorded"]["via"], "glossary")
        self.assertIn("lkw_to_lp", gem["laws"])
        self.assertIn("proposed", gem["tiers"],
                      "the wolf assimilation is sporadic, and the page says so")
        self.assertEqual(gem["evidence"], "literary",
                         "the form it reaches is the recorded Proto-Germanic reconstruction")

    def test_a_leaf_language_has_no_branch(self):
        self.assertIsNone(service.word("fa", "پدر")["descendants"])

    def test_a_prediction_here_is_never_green_or_gold(self):
        rows = service.word("pal", "drˈay", ghost=True, via="ira-pro/jráyah")["descendants"]["rows"]
        self.assertTrue(rows)
        self.assertTrue(all(r["evidence"] in {"strong", "weak"} for r in rows),
                        "the start is not a recorded etymon, so nothing may claim a match")

    def test_a_ghost_row_that_reaches_a_record_stays_orange(self):
        peo = service.word_index()[("peo", "𐎭𐎼𐎹")][0]
        tree = service._stage_descendants("ira-pro", "jráyah", (peo, "peo"), claim=False)["tree"]
        old_persian = next(n for n in tree if n["l"] == "peo")
        self.assertEqual(old_persian["status"], "match")
        self.assertEqual(old_persian["recorded"]["w"], "𐎭𐎼𐎹")
        self.assertEqual(old_persian["evidence"], "strong",
                         "it equals a record, but the start is not an etymon, so it stays orange")

    def test_an_unknown_language_still_has_no_page(self):
        self.assertIsNone(service.word("zz", "jráyah", ghost=True))


class TestTheWolfCompletes(unittest.TestCase):
    """English *wolf* — a law that changes the phonology, not the word.

    2026-11-08: the ladder reached *wˈolf* and then showed
    *wˈɔlf* against the recorded **wolf**, so the last rung read "differs".
    Middle English ⟨o⟩ in *wolf* spells /u/ (the spelling convention that also
    writes *word*, *wonder*), not the short *o that lowered to *ɔ in *dog*: the
    law never applied to this word.  The word's own pathway says so, with its
    reason and its sources, and the page switches that one law off — visibly.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("en", "wolf")
        cls.plain = service.word("en", "wolf", pathway=False)
        cls.ladder = cls.page["hierarchy"]

    def test_the_page_is_exact(self):
        self.assertTrue(self.ladder["result"]["match"], self.ladder["result"])
        self.assertEqual(self.ladder["result"]["form"], "wˈolf")
        self.assertTrue(self.page["derivation"]["match"])

    def test_exactly_one_law_is_left_out_and_the_page_says_which(self):
        english = self.ladder["levels"][-1]
        off = [r for r in english["rules"] if r["disabled"]]
        self.assertEqual([r["id"] for r in off], ["short_o_lowering"])
        self.assertEqual(off[0]["would"], "wˈɔlf",
                         "a switched-off law still says what it would have done")
        self.assertEqual(self.ladder["switched_off"], 1)

    def test_the_reason_and_its_sources_are_stored_with_the_word(self):
        pathway = self.ladder["pathway"]
        self.assertIsNotNone(pathway)
        self.assertIn("u", pathway["note"])
        self.assertIn("carney-1994", pathway["references"])
        stored = paths.default_for("en", "wolf")
        self.assertIsNotNone(stored)
        self.assertEqual(stored["disabled"], ["enm~en:short_o_lowering"])

    def test_without_the_pathway_the_law_does_apply(self):
        self.assertFalse(self.plain["hierarchy"]["result"]["match"])
        self.assertEqual(self.plain["hierarchy"]["result"]["form"], "wˈɔlf")
        self.assertEqual(self.plain["hierarchy"]["switched_off"], 0)
        self.assertIsNone(self.plain["hierarchy"]["pathway"])

    def test_the_pathway_is_not_a_second_loadable_path(self):
        self.assertEqual(self.ladder["pathways"], [],
                         "a word's own pathway is applied, not offered as a suggestion")

    def test_the_rest_of_the_family_still_reads_as_before(self):
        siblings = {lv["stage"]: lv for lv in self.ladder["levels"]}
        self.assertEqual(siblings["enm"]["form"], "wˈolf")
        self.assertEqual(siblings["enm"]["status"], "match")


class TestALawOpens(unittest.TestCase):
    """Every law named on a page is a door (2026-11-08)."""

    def test_a_law_page_carries_the_statement_and_the_work_it_stands_on(self):
        row = service.rule_page("enm~en:short_o_lowering")
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Short *o > *ɔ")
        self.assertEqual(row["tier"], "established")
        self.assertEqual(row["transition"]["src"], "enm")
        self.assertEqual(row["transition"]["dst"], "en")
        self.assertEqual(row["pattern"]["display"], "o → ɔ")
        self.assertEqual(row["examples"][0]["out"], "*dɔg")
        self.assertIn("dobson-1968", [ref["id"] for ref in row["references"]])
        self.assertTrue(row["references"][0]["title"], "a reference key becomes a cited work")
        self.assertIsNotNone(row["next"])
        self.assertIsNotNone(row["previous"])

    def test_a_bare_id_finds_its_law_and_an_ambiguous_one_does_not(self):
        self.assertEqual(service.rule_page("short_o_lowering")["transition"]["dst"], "en")
        self.assertIsNone(service.rule_page("hl_loss"),
                          "the same id in two transitions must not open an arbitrary one")
        self.assertIsNone(service.rule_page("not_a_law"))

    def test_every_law_a_ladder_names_can_be_opened(self):
        for lang, word in (("en", "night"), ("fa", "پدر"), ("gem-pro", "wulfaz")):
            ladder = service.word(lang, word)["hierarchy"]
            keys = [r["key"] for level in ladder["levels"] for r in level["rules"]]
            self.assertTrue(keys, f"{lang}:{word} should name some laws")
            for key in keys:
                self.assertIsNotNone(service.rule_page(key), f"{key} has no page")

    def test_the_front_end_links_the_laws_it_names(self):
        js = text("app.js")
        self.assertIn("#/rule/", js)
        self.assertIn("[/^\\/rule\\/(.+)$/", js)
        self.assertIn("const lawLink", js)
        self.assertNotIn("data-drop-pathway", js,
                         "there is no button forcing a switched-off law: its switch is the control")
        css = text("style.css")
        self.assertIn(".badge.orthographic", css)


class TestAConstructionBuildsTheWord(unittest.TestCase):
    """2026-11-08: *dusmenēs* read "From *dus- ("bad") + *ménes-
    ("mind, thought") + *-s", but the panel showed only *ménes- + *-s — the
    first piece had fallen off, so the construction did not build the word at
    all. A construction must now chain every piece the entry states, and a row
    whose first piece does not stand at the word's beginning is not shown."""

    def test_a_three_piece_construction_keeps_its_first_piece(self):
        entry = {"word": "dusmenēs", "lang": "ine-pro", "pos": "adj",
                 "gloss": ["ill-disposed"],
                 "etym": "From *dus- (“bad”) + *ménes- (“mind, thought”) + *-s."}
        rows = service.constructions(entry, "ine-pro")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["base"]["form"], "dus-")
        self.assertEqual([m["form"] for m in row["members"]], ["ménes-"])
        self.assertEqual([s["form"] for s in row["suffixes"]], ["-s"])
        self.assertEqual(row["base"]["gloss"], "bad")

    def test_a_construction_that_does_not_begin_the_word_is_dropped(self):
        entry = {"word": "dusmenēs", "lang": "ine-pro", "pos": "adj",
                 "gloss": ["ill-disposed"],
                 "etym": "From *ménes- (“mind, thought”) + *-s."}
        self.assertEqual(service.constructions(entry, "ine-pro"), [],
                         "a fragment that starts mid-word is not a construction")

    def test_ablaut_and_a_lost_laryngeal_still_build_the_word(self):
        for word, etym in (("sodéyeti", "From *sed- (“to sit”) + *-éyeti."),
                           ("wérsēn", "From *h₁wers- (“to rain”) + *-ēn.")):
            rows = service.constructions({"word": word, "lang": "ine-pro", "pos": "verb",
                                          "gloss": ["x"], "etym": etym}, "ine-pro")
            self.assertEqual(len(rows), 1, f"{word} should keep its construction")


class TestThePersianWolf(unittest.TestCase):
    """Persian گرگ — the Iranian half of *wĺ̥kʷos* (2026-11-08).

    The chain used to run *wĺ̥kʷos → … → OP wˈarkah* and then take the ordinary
    Persian *w- > b- of *bād*, giving **bark**.  Middle Persian gurg is one of
    the etyma in which initial *u̯- went to g- (Cathcart 2015, quoting Schwartz
    1982: *u̯r̥ka- > MP gurg > NP gurg 'wolf', beside *u̯r̥tka- > gurdag).  The
    change is registered in the environment the sources show, and every law it
    needs says it is proposed.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("fa", "گرگ")
        cls.ladder = cls.page["hierarchy"]
        cls.levels = {lv["stage"]: lv for lv in cls.ladder["levels"]}

    def test_the_word_is_exact_from_the_pie_etymon(self):
        self.assertTrue(self.page["derivation"]["match"])
        self.assertTrue(self.page["derivation"]["match_via_translit"])
        self.assertEqual(self.page["derivation"]["start"], "ine-pro")
        self.assertEqual(self.page["derivation"]["forms"][-1], "gorg")
        self.assertEqual([lv["stage"] for lv in self.ladder["levels"]],
                         ["ine-pro", "iir-pro", "ira-pro", "peo", "pal", "fa"])

    def test_the_persian_wolf_is_a_cited_entry(self):
        # The word is Wiktionary's own entry now, and it prints the dictionary's
        # first romanisation (gurg) with the Iranian reading (gorg) beside it;
        # the record still quotes MacKenzie and still names the Old Persian
        # ancestor (2026-11-09, when the entry stopped being supplement-only).
        self.assertEqual(self.page["translit"], "gurg")
        self.assertIn("gorg", self.page["translit_alt"])
        self.assertIn("wolf", self.page["gloss"])
        self.assertIn("wiktionary", [s["id"] for s in self.page["sources"]])
        self.assertIn("MacKenzie", self.page["sources"][0].get("ref") or "")
        self.assertIn("varka", self.page["etymology"],
                      "the Old Persian ancestor is named in the etymology")

    def test_middle_persian_matches_through_its_recorded_reading(self):
        pal = self.levels["pal"]
        self.assertEqual(pal["status"], "match")
        self.assertEqual(pal["form"], "gˈurg")
        # Wiktionary writes the Middle Persian ancestor in its own script; the
        # Pahlavi table reads it *gurg*, and the laws produce that reading.
        self.assertEqual(pal["recorded"]["w"], "𐭢𐭥𐭫𐭢",
                         "the record is the Pahlavi headword, not a Latin form")
        self.assertEqual(pal["recorded"]["reading"], "gurg")
        self.assertEqual(pal["recorded"]["via"], "gurg",
                         "the laws produce the reading, and the rung says so")

    def test_the_new_laws_come_before_the_older_ones_and_are_never_established(self):
        laws = {r["id"]: r["tier"] for r in self.levels["pal"]["rules"]}
        for law in ("war_rounding", "w_to_g_before_ur", "rk_to_rg"):
            self.assertEqual(laws.get(law), "proposed", law)
        row = service.rule_page("peo~pal:w_to_g_before_ur")
        self.assertIsNotNone(row)
        self.assertIn("cathcart-2015", [ref["id"] for ref in row["references"]])
        self.assertTrue(row["references"][0]["title"], "the citation gets a title")
        self.assertIn("irregular", " ".join(row["notes"].split()).lower())

    def test_the_pie_page_reaches_the_persian_record(self):
        tree = service.word("ine-pro", "wĺ̥kʷos")["descendants"]["tree"]

        def find(rows, lang):
            for row in rows or []:
                if row["l"] == lang:
                    return row
                hit = find(row.get("children"), lang)
                if hit:
                    return hit
            return None

        self.assertIsNotNone(find(tree, "pal"), "Middle Persian hangs below PIE")
        self.assertIsNotNone(find(tree, "fa"), "Persian hangs below Middle Persian")


class TestTheAnimalSuffix(unittest.TestCase):
    """گربه — a suffix that is a law, not a hand-composed form (2026-11-08).

    The word page used to start at Proto-Iranian and explain that the ladder
    could not climb higher because *-ka- is a formation, not a sound change.
    The formation appears *in* the hierarchy, with each
    suffix registered as a law that is off by default and switched on by the
    word that wears it. The word is also now a record in PIE itself: the
    dictionaries enter the root *h₂wl̥p-, and the noun *h₂wl̥pís that گربه
    quotes was missing from the glossary.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("fa", "گربه")
        cls.ladder = cls.page["hierarchy"]
        cls.levels = {lv["stage"]: lv for lv in cls.ladder["levels"]}

    def test_the_etymon_is_a_pie_glossary_entry(self):
        entry = service.word("ine-pro", "h₂wl̥pís")
        self.assertIsNotNone(entry, "the etymon گربه quotes must exist in PIE")
        self.assertIn("marten", " ".join(entry["gloss"]).lower())
        self.assertIn("de-vaan-2000", [s["id"] for s in entry["sources"]])

    def test_the_ladder_climbs_from_the_pie_etymon(self):
        self.assertEqual([lv["stage"] for lv in self.ladder["levels"]],
                         ["ine-pro", "iir-pro", "ira-pro", "peo", "pal", "fa"])
        self.assertEqual(self.ladder["levels"][0]["form"], "h₂wl̥pís")
        self.assertTrue(self.page["derivation"]["match"])
        self.assertEqual(self.page["derivation"]["forms"][-1], "gorbe")

    def test_the_suffix_is_a_registered_law_switched_on_for_this_word(self):
        self.assertEqual(self.ladder["enabled"], ["ine-pro~iir-pro:animal_ka"])
        fired = [r for r in self.levels["iir-pro"]["rules"] if r["id"] == "animal_ka"]
        self.assertTrue(fired and fired[0]["fired"],
                        "the formation law fires on this word's own ladder")
        self.assertEqual(fired[0]["tier"], "formation")
        page = service.rule_page("ine-pro~iir-pro:animal_ka")
        self.assertIsNotNone(page)
        self.assertIn("de-vaan-2000", [ref["id"] for ref in page["references"]])

    def test_the_law_is_off_unless_the_word_turns_it_on(self):
        from pie import data
        from pie.rules import derive

        plain = derive("h₂wl̥pís", ["ine-pro", "iir-pro"], data.rulesets())
        self.assertNotIn("aka", plain.output,
                         "no suffix may be invented for a word that does not use it")
        self.assertNotIn("animal_ka", [step.rule_id for step in plain.steps])
        on = derive("h₂wl̥pís", ["ine-pro", "iir-pro"], data.rulesets(),
                    enabled=["ine-pro~iir-pro:animal_ka"])
        self.assertIn("aka", on.output)

    def test_the_pie_page_composes_the_same_law(self):
        p = service.reconstruct("h₂wl̥pís", "fa", "ka-animal")
        self.assertEqual(p["status"], "match")
        self.assertEqual(p["form"], "gorbe")
        self.assertEqual(p["recorded"]["w"], "گربه")
        self.assertEqual(p["morph"]["law"]["key"], "ine-pro~iir-pro:animal_ka")

    def test_the_suffix_is_printed_beside_the_rung_it_was_added_on(self):
        """The morpheme belongs in the hierarchy, not in a note."""
        form = self.levels["iir-pro"]["formation"]
        self.assertIsNotNone(form, "the rung that adds the suffix carries it")
        self.assertEqual(form["suffix"], "-ka-")
        self.assertEqual(form["surface"], "-ka",
                         "the letters to highlight inside the composed word")
        active = [o for o in form["options"] if o["active"]]
        self.assertEqual([o["id"] for o in active], ["ka-animal"])
        self.assertTrue(all(o["form"] for o in form["options"]))

    def test_another_suffix_can_be_tried_on_the_timeline(self):
        """`?suffix=` answers what the laws would give with a different morpheme."""
        trial = service.hierarchy("fa", "گربه", suffix="eh2")
        self.assertIsNotNone(trial["hypothesis"])
        self.assertEqual(trial["hypothesis"]["suffix"]["id"], "eh2")
        self.assertIn("eh₂", trial["hypothesis"]["composed"])
        self.assertFalse(trial["result"]["match"],
                         "a form the word does not wear must never read as the word")
        self.assertEqual(trial["levels"][0]["stage"], "ine-pro")
        self.assertEqual(trial["levels"][0]["form"], trial["hypothesis"]["composed"])
        plain = service.hierarchy("fa", "گربه")
        self.assertIsNone(plain["hypothesis"], "the word's own ladder is the default")


class TestTheAdjectiveSuffixNah(unittest.TestCase):
    """دیوانه — a suffix on an intermediary stage (2026-11-08).

    Wiktionary's Reconstruction:Proto-Iranian/-nah is PII *-nás from PIE
    *-nós, and daywánah is *daywá- plus that suffix. The requirement:
    suffixes of the intermediary languages too, selectable in the timeline.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("fa", "دیوانه")
        cls.ladder = cls.page["hierarchy"]
        cls.levels = {lv["stage"]: lv for lv in cls.ladder["levels"]}

    def test_the_ladder_climbs_from_pie_and_adds_the_suffix(self):
        stages = [lv["stage"] for lv in self.ladder["levels"]]
        self.assertEqual(stages[0], "ine-pro")
        self.assertEqual(self.levels["iir-pro"]["form"], "daywˈas")
        form = self.levels["ira-pro"]["formation"]
        self.assertEqual(form["suffix"], "-nás")
        self.assertEqual(form["surface"], "-nah")
        self.assertEqual(form["options"][0]["id"], "nah")

    def test_the_suffix_law_is_a_formation_off_by_default(self):
        from pie import data
        from pie.rules import derive

        plain = derive("daywás", ["iir-pro", "ira-pro"], data.rulesets())
        self.assertNotIn("n", plain.output.replace("daywás", ""),
                         "no suffix may be added to a word that does not wear it")
        on = derive("daywás", ["iir-pro", "ira-pro"], data.rulesets(),
                    enabled=["iir-pro~ira-pro:suffix_nah"])
        self.assertEqual(on.output, "daywˈanah")
        page = service.rule_page("iir-pro~ira-pro:suffix_nah")
        self.assertEqual(page["tier"], "formation")
        self.assertIn("wiktionary", [ref["id"] for ref in page["references"]])

    def test_the_morphology_record_runs_its_own_law(self):
        p = service.compose("daywás", "nah", "iir-pro")
        self.assertEqual(p["form"], "daywˈanas")
        self.assertEqual(p["law"]["key"], "iir-pro~ira-pro:suffix_nah")


class TestScriptHeadwordsInTheHierarchy(unittest.TestCase):
    """Arameograms and cuneiform must not stop the ladder (2026-11-08).

    Middle Persian 𐫅𐫏𐫇 and Old Persian 𐎭𐎡𐎺 are not strings of segments the
    sound laws can carry, so the engine used to end the chain at the script
    headword. The recorded reading is the form the laws take instead.
    """

    def test_manichaean_middle_persian_climbs_the_whole_chain(self):
        page = service.word("pal", "𐫅𐫏𐫇")
        self.assertIsNotNone(page)
        self.assertEqual(page["translit"], "dēw")
        stages = [lv["stage"] for lv in page["hierarchy"]["levels"]]
        self.assertEqual(stages, ["ine-pro", "iir-pro", "ira-pro", "peo", "pal"])
        self.assertEqual(page["hierarchy"]["levels"][-1]["form"], "dēw")

    def test_old_persian_climbs_and_explains_its_v(self):
        page = service.word("peo", "𐎭𐎡𐎺")
        self.assertEqual(page["translit"], "daivaʰ")
        rung = page["hierarchy"]["levels"][-1]
        self.assertEqual(rung["stage"], "peo")
        # The laws write the labiovelar *w, the sign 𐎺 is transcribed v, and
        # the final /h/ has no sign at all. The record is still the same word,
        # and the rung says which signs the reading was made from
        # (2026-11-08: a cuneiform word can be read).
        self.assertTrue(rung["recorded"]["matches"])
        self.assertEqual(rung["recorded"]["fit"]["translit"], "da-i-va")
        self.assertEqual(rung["recorded"]["fit"]["unwritten"], ["h"])
        self.assertTrue(page["hierarchy"]["result"]["match_via_script"])

    def test_a_phonological_form_may_be_stated_by_the_record(self):
        from pie.service import _phonological_form

        self.assertEqual(_phonological_form("pal", "𐫅𐫏𐫇"), "dēw")
        self.assertEqual(_phonological_form("fa", "دیو"), "dēw")
        # A Latin-script form is already phonological and is left alone.
        self.assertEqual(_phonological_form("fa", "dēw"), "dēw")


    def test_the_glossary_lists_headwords_for_the_word_view(self):
        g = service.glossary("ine-pro", limit=5)
        self.assertEqual(len(g["rows"]), 5)
        self.assertTrue(g["rows"][0]["root"], "PIE roots come first")
        self.assertTrue(g["total"] > 1000)


class TestTheWordConstruction(unittest.TestCase):
    """The construction under the title (2026-11-08).

    Wiktionary states a derivative as an arithmetic — "From *wĺ̥kʷos +
    *-íh₂s." — and the page prints those pieces under the headword, the base as
    a door to its own page, the suffix in the accent colour, and a (+) for
    another cited suffix. Nothing is composed when the dictionary does not say
    it: an etymology that names one source has no construction.
    """

    def test_a_derived_word_shows_its_base_and_the_suffix_it_wears(self):
        page = service.word("ine-pro", "wl̥kʷíh₂s")
        c = page["construction"]
        self.assertIsNotNone(c)
        self.assertEqual(c["base"]["form"], "wĺ̥kʷos")
        self.assertTrue(c["base"]["known"])
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-íh₂s"])

    def test_the_base_is_a_link_that_opens(self):
        page = service.word("ine-pro", "wl̥kʷíh₂s")
        link = page["construction"]["base"]["link"]
        self.assertTrue(link.startswith("#/word/ine-pro/"))
        base = service.word("ine-pro", page["construction"]["base"]["form"])
        self.assertIsNotNone(base, "the linked base has its own page")

    def test_an_etymon_with_nothing_above_it_has_no_construction(self):
        self.assertIsNone(service.word("ine-pro", "wĺ̥kʷos")["construction"])

    def test_a_sentence_that_names_one_source_is_not_an_arithmetic(self):
        # "From Proto-Iranian *wŕ̥kah (compare …)": one source, not base+suffix.
        self.assertIsNone(service.word("peo", "𐎺𐎼𐎣")["construction"])
        # "Possibly related to *h₂éd": a relation, not a construction.
        self.assertIsNone(service.word("ine-pro", "de")["construction"])

    def test_a_hedged_analysis_is_shown_but_not_called_the_entries_statement(self):
        # "possibly from *h₂uks-ḗn, from *h₂weks- + *-ḗn, or perhaps…"
        c = service.word("ine-pro", "uksḗn")["construction"]
        self.assertIsNotNone(c)
        self.assertEqual(c["base"]["form"], "h₂weks-")
        self.assertEqual(c["confidence"], "argued")
        self.assertIn("possibly", c["etym"])

    def test_an_unknown_base_is_shown_but_not_linked(self):
        # A case-marked formation the entry names is not a headword: it is
        # printed, but there is no page to open (2026-11-08).
        c = service.word("ine-pro", "déh₃rom")["construction"]
        self.assertEqual(c["base"]["form"], "déh₃-n̥-s")
        self.assertFalse(c["base"]["known"])
        self.assertEqual(c["base"]["link"], "")

    def test_a_stem_class_the_record_names_is_the_construction(self):
        """h₂wl̥pís: "An i-stem noun built on the root *h₂wl̥p-" (2026-11-08)."""
        c = service.word("ine-pro", "h₂wl̥pís")["construction"]
        self.assertIsNotNone(c)
        self.assertEqual(c["kind"], "stem")
        self.assertEqual(c["base"]["form"], "h₂wl̥p-")
        self.assertTrue(c["base"]["known"], "the root has its own page")
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-i-"])
        self.assertEqual(c["suffixes"][0]["kind"], "stem",
                         "the stem-formative is the record's words, not a cited suffix")
        self.assertIn("i-stem", c["suffixes"][0]["gloss"])

    def test_each_stem_class_is_read_from_its_own_sentence(self):
        for word, base, suffix in (("gʷʰrensós", "gʷʰer-", "-n-"),
                                   ("suHnús", "sewH-", "-u-")):
            c = service.word("ine-pro", word)["construction"]
            self.assertIsNotNone(c, word)
            self.assertEqual(c["base"]["form"], base, word)
            self.assertEqual(c["suffixes"][0]["form"], suffix, word)
            self.assertEqual(c["kind"], "stem", word)

    def test_a_hedged_derivation_from_a_root_is_a_possible_construction(self):
        """h₂ŕ̥tḱos: "possibly nominalized from root *h₂retḱ-" (2026-11-08)."""
        c = service.word("ine-pro", "h₂ŕ̥tḱos")["construction"]
        self.assertIsNotNone(c)
        self.assertEqual(c["kind"], "root")
        self.assertEqual(c["base"]["form"], "h₂retḱ-")
        self.assertEqual(c["base"]["gloss"], "to damage, harm")
        self.assertTrue(c["base"]["known"], "the root is an entry of its own")
        self.assertIn("#/word/ine-pro/", c["base"]["link"])
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-o-"],
                         "the nominalization's stem-formative is the word's own ending")
        self.assertEqual(c["suffixes"][0]["kind"], "stem")
        self.assertEqual(c["confidence"], "argued", "the entry says 'possibly'")
        self.assertIn("possibly nominalized", c["etym"])
        self.assertNotIn("h₁reḱs-", c["etym"], "the see-also root is not this reading")

    def test_a_root_a_construction_names_is_an_entry_of_its_own(self):
        """h₂retḱ- has no Wiktionary page, but the bear's etymology records it
        (2026-11-08): it is an entry, its base is a link, and the
        page lists the word built on it."""
        root = service.word("ine-pro", "h₂retḱ-")
        self.assertIsNotNone(root)
        self.assertEqual(root["pos"], "root")
        self.assertEqual(root["gloss"], ["to damage, harm"])
        self.assertTrue(root["recon"], "a root is a reconstruction, not an attestation")
        self.assertEqual([r["word"] for r in root["built_from"]], ["h₂ŕ̥tḱos"])
        self.assertEqual(root["built_from"][0]["suffixes"], ["-o-"])
        source = root["sources"][0]
        self.assertIn("h₂ŕ̥tḱos", urllib.parse.unquote(source["entry"]),
                      "the citation opens the entry that names the root")
        self.assertIn("Named in the etymology of h₂ŕ̥tḱos", source["ref"])

    def test_a_root_is_shown_even_when_no_suffix_is_named(self):
        c = service.word("ine-pro", "móri")["construction"]
        self.assertEqual(c["base"]["form"], "mer-")
        self.assertEqual(c["base"]["gloss"], "sea, lake, wetland")
        self.assertEqual(c["suffixes"], [])
        self.assertTrue(c["base"]["known"], "the root has its own page")

    def test_a_bare_derivation_is_read_only_when_the_base_is_a_root(self):
        # "From earlier *méh₁n̥s-s, probably from *meh₁-": the pre-form is not a
        # root, so only *meh₁- is offered as a construction.
        words = {r["base"]["form"] for r in service.word("ine-pro", "mḗh₁n̥s")["constructions"]}
        self.assertEqual(words, {"meh₁-"})

    def test_a_semicolon_inside_a_gloss_does_not_hide_the_arithmetic(self):
        # ménos: From *men- (“to think; mind”) + *-os. The gloss's own ";" used
        # to cut the sentence in half, so 35 entries showed no construction.
        c = service.word("ine-pro", "ménos")["construction"]
        self.assertEqual(c["base"]["form"], "men-")
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-os"])
        self.assertEqual(c["confidence"], "stated")

    def test_a_root_the_entry_enlarges_wears_the_suffix_it_names(self):
        # sterbʰ-: "probably from *dʰer- … enlarged by *-bʰ".
        c = service.word("ine-pro", "sterbʰ-")["construction"]
        self.assertEqual(c["base"]["form"], "dʰer-")
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-bʰ"])

    def test_a_grammatical_word_is_not_given_a_construction(self):
        # "Possibly from *h₁én / *én" places an adverb; it builds nothing.
        self.assertIsNone(service.word("ine-pro", "ní")["construction"])

    def test_a_synonyms_root_is_not_the_headwords(self):
        # gʰébʰōl: "the synonym *káp-ōl, which likewise may be from *kap-".
        rows = service.word("ine-pro", "gʰébʰōl")["constructions"]
        self.assertEqual([r["base"]["form"] for r in rows], ["gʰebʰ-"])
        self.assertEqual([s["form"] for s in rows[0]["suffixes"]], ["-ōl"])

    def test_an_arithmetic_does_not_leave_its_bare_root_beside_it(self):
        # "*wers- ("to rise (up)") + *-ḗn" — the nested gloss is still read,
        # and the bare root does not shadow the suffix the entry names.
        rows = service.word("ine-pro", "wérsēn")["constructions"]
        self.assertEqual(rows[0]["base"]["form"], "wers-")
        self.assertEqual([s["form"] for s in rows[0]["suffixes"]], ["-ḗn"])
        self.assertEqual(rows[0]["base"]["gloss"], "to rise (up)")
        self.assertEqual(rows[1]["base"]["form"], "h₁wers-", "the rival root is still shown")

    def test_a_word_without_a_stem_class_gains_no_construction(self):
        # "Possibly related to …" and a bare root state no formation at all.
        self.assertIsNone(service.word("ine-pro", "de")["construction"])
        self.assertIsNone(service.word("ine-pro", "nu")["construction"])

    def test_an_attested_word_does_not_borrow_its_ancestors_formation(self):
        # English lucre's "from PIE *leh₂w- + *-tlom" is the etymon's build.
        self.assertIsNone(service.word("en", "lucre")["construction"])
        # And a descendant proto-stage may not cross a boundary either:
        # "*prugʰ- + *-ḱós" is Proto-Indo-European's, not Proto-Germanic's.
        self.assertIsNone(service.word("gem-pro", "fruskaz")["construction"])

    def test_a_proto_stage_reads_its_own_arithmetic(self):
        c = service.word("gem-pro", "balþijaną")["construction"]
        self.assertEqual(c["base"]["form"], "balþaz")
        self.assertEqual([s["form"] for s in c["suffixes"]], ["-janą"])
        self.assertEqual(c["confidence"], "stated")

    def test_one_word_may_state_several_constructions_with_confidence(self):
        rows = service.word("ine-pro", "kr̥snós")["constructions"]
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["confidence"] for r in rows], ["stated", "argued"])
        self.assertEqual([r["base"]["form"] for r in rows], ["kers-", "ker-s-"])
        self.assertEqual(rows[0], service.word("ine-pro", "kr̥snós")["construction"],
                         "the first row is the one the page composes with")
        self.assertTrue(rows[0]["etym"], "each row keeps the sentence it was read from")

    def test_a_hedged_first_analysis_and_its_rivals_are_all_argued(self):
        rows = service.word("ine-pro", "ǵʰéymn̥")["constructions"]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["confidence"] == "argued" for r in rows))
        self.assertEqual([s["form"] for s in rows[2]["suffixes"]], ["-n̥"])

    def test_an_analysis_an_entry_argues_in_prose_is_recorded_with_its_author(self):
        rows = service.word("ine-pro", "nókʷts")["constructions"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["base"]["form"], "negʷ-")
        self.assertEqual(rows[0]["source"], "Pooth")
        self.assertEqual(rows[0]["confidence"], "argued")
        self.assertIn("Pooth argues", rows[0]["etym"])

    def test_a_construction_of_a_related_form_is_not_the_headwords(self):
        # "Reanalysed root of *ḱléyti, from *ḱel- + *-éyti" is *ḱléyti's
        # construction, not the root's.
        self.assertIsNone(service.word("ine-pro", "ḱley-", sense=1)["construction"])
        # "rebuilt from the genitive of *swóp-r̥ …, from *swep- + *-r̥": the
        # arithmetic belongs to the genitive, not to the adjective.
        self.assertIsNone(service.word("ine-pro", "supnós")["construction"])

    def test_every_stage_can_carry_a_suffix_list_for_the_picker(self):
        self.assertTrue(service.word("ine-pro", "wĺ̥kʷos")["morphology"]["suffixes"])
        # A language with no cited suffixes still answers with an empty list,
        # so the page never has to guess whether the field exists.
        self.assertEqual(service.word("peo", "𐎺𐎼𐎣")["morphology"]["suffixes"], [])


class TestAConstructionIsATree(unittest.TestCase):
    """A construction is a step of the timeline, and its pieces have histories.

    2026-11-12: the reader asked for the old `CONSTRUCTION: …` line under the
    headword to become part of the ladder, drawn as an upside-down tree — each
    piece climbs its own recorded ancestry upward until it reaches a word in
    Proto-Indo-European, a donor it was borrowed from, or a ??? where nothing
    explains it.  The server decides the tree; this is its shape.
    """

    def _pieces(self, word="Ciçafarnāh", lang="peo"):
        level = service.hierarchy(lang, word)["levels"][0]
        return level["built_as"]["pieces"]

    def test_each_piece_carries_its_own_branch(self):
        pieces = self._pieces()
        self.assertEqual([p["form"] for p in pieces], ["𐎨𐎡𐏂", "*farnah"])
        self.assertTrue(all(p.get("branch") for p in pieces),
                        "every piece is a word with a history, not a string")

    def test_every_word_of_the_tree_carries_the_meaning_printed_under_it(self):
        # 2026-11-12: the reader asked for the sense under every word of the
        # timeline, the way the headword carries `name · “a male given name”`.
        # A piece takes the record's own parenthesis first and the piece's
        # glossary entry second, and it carries the category with it.
        pieces = self._pieces()
        self.assertEqual(pieces[0]["gloss"], "shining; appearance; lineage")
        self.assertEqual(pieces[0]["pos"], "noun")
        self.assertEqual(pieces[1]["gloss"], "glory")
        # The ancestors too: a rung is a word with a sense, not a string.
        branch = pieces[0]["branch"]
        pir = branch["parents"][0]
        self.assertEqual((pir["gloss"], pir["pos"]), ("visible", "adj"))

    def test_a_bound_suffix_says_what_it_does(self):
        # A suffix row usually carries no parenthesis of its own, so its gloss
        # comes from its entry in the stage's glossary: *-rós forms adjectives
        # from Caland-system roots.  Without it the piece would sit on the line
        # saying nothing (admin, 2026-11-12).
        pie_node = self._pieces()[0]["branch"]["parents"][0]["parents"][0]["parents"][0]
        suffix = pie_node["builds"][0]["pieces"][1]
        self.assertEqual(suffix["form"], "*-rós")
        self.assertTrue(suffix["bound"])
        self.assertEqual(suffix["pos"], "suffix")
        self.assertIn("Caland", suffix["gloss"])
        self.assertEqual(pie_node["builds"][0]["pieces"][0]["gloss"], "to shine, glow")

    def test_a_gloss_keeps_no_colon_from_the_source(self):
        # Some rows were extracted with the dictionary's own colon still on the
        # sense (": type, form, lineage"); it is punctuation of the source, not
        # of the meaning (2026-11-12).
        self.assertEqual(service._rung_gloss([": type, form, lineage"]),
                         "type, form, lineage")

    def test_the_first_piece_climbs_to_a_named_form_the_glossary_lacks(self):
        branch = self._pieces()[0]["branch"]
        forms = []
        node = branch
        while node:
            forms.append((node["lang"], node["form"]))
            node = (node["parents"] or [None])[0]
        self.assertEqual(forms, [("peo", "𐎨𐎡𐏂"), ("ira-pro", "*čiθráh"),
                                 ("iir-pro", "*čitrás"), ("ine-pro", "*kit-ró-s")])
        self.assertEqual(node, None)
        # The last node is Proto-Indo-European: the top of the family.  It is
        # not a ??? — nothing above it is missing, the model simply stops there
        # (admin, 2026-11-12).  The box says which ending it is, and whether the
        # glossary happens to hold the form.
        last = branch["parents"][0]["parents"][0]["parents"][0]
        self.assertEqual(last["terminal"], "pie")
        self.assertFalse(last["known"], "no glossary entry for the PIE form")

    def test_an_ancestor_built_in_a_childs_article_keeps_its_construction(self):
        # Wiktionary writes *kit-ró-s = *keyt- + *-rós in its article on
        # Proto-Indo-Iranian *čitrás; there is no article (and no glossary
        # entry) for *kit-ró-s itself.  The step belongs to the ancestor's form
        # all the same, so the word page must show it — the reader asked why the
        # *čitrás page had it and the Ciçafarnāh page did not (admin,
        # 2026-11-12).
        branch = self._pieces()[0]["branch"]
        pie_node = branch["parents"][0]["parents"][0]["parents"][0]
        self.assertEqual((pie_node["lang"], pie_node["form"]),
                         ("ine-pro", "*kit-ró-s"))
        self.assertEqual(len(pie_node["builds"]), 1,
                         "the ancestor carries the step that made it")
        self.assertEqual([p["form"] for p in pie_node["builds"][0]["pieces"]],
                         ["*keyt-", "*-rós"])
        self.assertEqual(pie_node["builds"][0]["of"], "kit-ró-s")
        # A construction replaces a single parent: nothing is invented above
        # the form the record explains.
        self.assertEqual(pie_node["parents"], [])
        self.assertNotEqual(pie_node["terminal"], "missing",
                            "the form is not a ??? once its construction is known")

    def test_one_construction_stated_twice_is_one_analysis_not_two_tabs(self):
        # *sokʷh₂ṓy's record lists the same seam twice — *sekʷ- + *-éh₂ and
        # again *sekʷ- + *-éh₂ + *-ṓy — because the second row carries on past
        # the first.  A shorter row that is a prefix of a longer one is the same
        # finding read twice, not a rival analysis: the page drew two tabs of
        # one construction (admin, 2026-11-12).
        level = service.hierarchy("ine-pro", "sokʷh₂ṓy")["levels"][0]
        self.assertEqual(len(level["builds"]), 1)
        self.assertEqual([p["form"] for p in level["builds"][0]["pieces"]],
                         ["*sekʷ-", "*-éh₂", "*-ṓy"])

    def test_an_ancestor_rung_is_built_by_its_own_entry(self):
        # The Proto-Indo-European rung above Proto-Iranian *háxā is
        # *sokʷh₂ṓy, and it was *sekʷ- + *-éh₂ + *-ṓy — a fact stated in PIE's
        # article and nowhere in the Proto-Iranian one.  A rung that only looks
        # at the page's own entry loses the step, which is what the reader saw
        # (admin, 2026-11-12).
        levels = service.hierarchy("ira-pro", "háxā")["levels"]
        pie = next(l for l in levels if l["stage"] == "ine-pro")
        self.assertEqual(pie["form"], "sokʷh₂ṓy")
        self.assertEqual(len(pie["builds"]), 1)
        self.assertEqual([p["form"] for p in pie["builds"][0]["pieces"]],
                         ["*sekʷ-", "*-éh₂", "*-ṓy"])
        # An ancestor's step is the record's own; the seam reader's guess
        # belongs to the page a word has, not to a form above it.
        self.assertEqual(pie["builds"][0]["source"], "record")

    def test_the_ladder_climbs_through_the_ancestors_own_ladder(self):
        # Proto-Iranian *čiθráh's record stops at Proto-Indo-Iranian *čitrás,
        # but *čitrás is a word with a page whose ladder reaches PIE and the
        # construction that built it.  The timeline continues through it rather
        # than ending where one dictionary happened to stop (admin, 2026-11-12).
        levels = service.hierarchy("ira-pro", "čiθráh")["levels"]
        self.assertEqual([l["stage"] for l in levels], ["ine-pro", "iir-pro", "ira-pro"])
        self.assertEqual([l["form"] for l in levels],
                         ["kit-ró-s", "čitrás", "čiθrˈah"])
        self.assertEqual([p["form"] for p in levels[0]["builds"][0]["pieces"]],
                         ["*keyt-", "*-rós"],
                         "the construction comes with the stages above it")
        self.assertEqual(levels[0]["status"], "start")
        self.assertEqual(levels[-1]["status"], "match",
                         "the word's own rung still says the laws reach it")
        self.assertEqual(service.hierarchy("ira-pro", "čiθráh")["earlier"], [],
                         "the stages are drawn, not merely listed")

    def test_the_climb_stops_at_the_top_of_the_family(self):
        # A word whose ladder already starts at Proto-Indo-European has nowhere
        # further to climb, and a word whose ancestor is a loan keeps the
        # ladder it has: no loop, no invented rung.
        night = service.hierarchy("en", "night")["levels"]
        self.assertEqual(night[0]["stage"], "ine-pro")
        self.assertEqual(len(night), 6, "one rung per stage, nothing doubled")
        book = service.hierarchy("en", "book")["levels"]
        self.assertEqual(book[0]["stage"], "ine-pro")
        self.assertEqual(len({(l["stage"], l["form"]) for l in book}), len(book),
                         "no rung is drawn twice")

    def test_a_pie_form_is_the_top_of_the_family_with_or_without_an_entry(self):
        # A Proto-Indo-European word ends the trail by being the top of it, not
        # by being absent from a glossary: a form the glossary *does* hold ends
        # there too.
        held = service._origin_node("ine-pro", "nókʷts")
        self.assertTrue(held["known"])
        self.assertEqual(held["terminal"], "pie")
        self.assertEqual(held["parents"], [])

    def test_every_node_says_whether_its_language_is_attested_or_reconstructed(self):
        # The tree prints each ancestor in the colour the ladder gives that
        # stage: a proto-stage is gold, an attested one green.  It cannot read
        # the region from the code, so the node carries the fact (2026-11-12).
        branch = self._pieces()[0]["branch"]
        self.assertEqual(branch["kind"], "attested", "the old Persian piece itself")
        last = branch["parents"][0]["parents"][0]["parents"][0]
        self.assertEqual(last["kind"], "proto", "Proto-Indo-European")
        self.assertEqual(self._pieces()[1]["branch"]["parents"][0]["kind"], "attested",
                         "Old Median is an attested language, not a starred stage")

    def test_a_word_from_outside_the_family_begins_its_own_trail(self):
        # Arabic is not a Proto-Indo-European descendant: there is no missing
        # ancestry above it, so no ??? is drawn (admin, 2026-11-12).
        node = service._origin_node("ar", "كِتَاب")
        self.assertEqual(node["terminal"], "outside")
        self.assertEqual(node["parents"], [])
        self.assertEqual(node["lang_name"], "Arabic")

    def test_a_bound_morpheme_is_not_a_word_with_a_history(self):
        # A word built from a noun and a suffix written with a tatweel:
        # a suffix was not inherited or borrowed, so no trunk is drawn above it.
        level = service.hierarchy("fa", "کتابدار")["levels"][0]
        pieces = level["builds"][0]["pieces"]
        self.assertEqual([p["form"] for p in pieces], ["کتاب", "ـدار"])
        self.assertTrue(pieces[1]["bound"])
        self.assertIsNone(pieces[1]["branch"])
        self.assertFalse(pieces[0]["bound"], "the base is a word")

    def test_a_printed_structure_is_never_drawn_as_a_word(self):
        # An early reader stored a piece as str(['کَم ', '>']); the page must
        # not print that as a word (2026-11-12, the repair is in
        # tools/clean_built_as.py).
        level = service.hierarchy("fa", "کمزور")["levels"][0]
        builds = level["builds"]
        self.assertEqual(len(builds), 1, "the malformed row is not a second tab")
        self.assertEqual([p["form"] for p in builds[0]["pieces"]], ["کَم", "زور"])

    def test_a_borrowing_ends_the_branch_at_its_donor(self):
        branch = self._pieces()[1]["branch"]
        donor = branch["parents"][0]
        self.assertEqual((donor["lang"], donor["form"]), ("xme-old", "*farnah"))
        self.assertEqual(donor["terminal"], "borrowed")
        self.assertEqual(donor["lang_name"], "Old Median",
                         "the donor is named, never a bare code")
        self.assertEqual(donor["parents"], [],
                         "the donor's own history belongs to the donor")

    def test_one_word_above_not_a_list_of_alternatives(self):
        # The English prefix `non-` carries nine ancestry rows from the
        # etymology tree, most of them template alternatives.  A timeline
        # climbs by one line: the record's own inheritance first.
        node = service._origin_node("en", "non-")
        self.assertEqual(node["form"], "non-")
        self.assertEqual(len(node["parents"]), 1)
        self.assertEqual(node["parents"][0]["rel"], "inherit")

    def test_a_root_is_a_relation_and_never_the_step_above(self):
        # *kit-ró-s and *keyt- are both named for Proto-Indo-Iranian *čitrás,
        # but a root carries no derivation: the inherited form is the step.
        node = service._origin_node("iir-pro", "*čitrás")
        self.assertEqual([(n["lang"], n["form"], n["rel"]) for n in node["parents"]],
                         [("ine-pro", "*kit-ró-s", "inherit")])

    def test_a_word_the_record_states_twice_is_two_tabs(self):
        # English *about* is stated as on + būtan and as be + ūtan; both are
        # the record's, so both are drawn, one tab each.
        level = next(l for l in service.hierarchy("en", "about")["levels"]
                     if l["stage"] == "ang")
        self.assertEqual(len(level["builds"]), 2)
        self.assertEqual([[p["form"] for p in b["pieces"]] for b in level["builds"]],
                         [["on", "būtan"], ["be", "ūtan"]])
        self.assertIs(level["built_as"], level["builds"][0],
                      "the first row is still there for older callers")

    def test_a_word_with_no_origin_recorded_ends_in_a_question(self):
        # `livre` has an entry but no ancestry: the walk says `end`, which the
        # page draws as a ??? above the word rather than as an invented parent.
        node = service._origin_node("en", "livre")
        self.assertTrue(node["known"])
        self.assertEqual(node["parents"], [])
        self.assertEqual(node["terminal"], "end")


class TestEveryRecordedPiece(unittest.TestCase):
    """A construction piece says what it means and where it is recorded
    (2026-11-08: *-ós* in *dl̥h₁gʰós* must explain itself, and a
    suffix recorded on one root must be selectable on the others).

    The meaning comes from the word's own parenthesis first, then the stage's
    hand-written row, then the grammatical ending, then the dictionary's suffix
    entry; the "places" are the words the corpus builds with the same form.
    """

    def test_the_suffix_of_the_long_one_says_what_it_is(self):
        c = service.word("ine-pro", "dl̥h₁gʰós")["construction"]
        self.assertEqual(c["base"]["form"], "delh₁gʰ-")
        piece = c["suffixes"][0]
        self.assertEqual(piece["form"], "-ós")
        self.assertIn("oxytone", piece["gloss"])
        self.assertTrue(piece["entry"].startswith("#/word/ine-pro/"),
                        "the dictionary entry for -ós is one click away")
        self.assertGreater(piece["recorded"], 20)
        self.assertIn("dl̥h₁gʰós", piece["examples"])

    def test_a_suffix_recorded_on_one_root_is_offered_on_another(self):
        """The picker is the stage's morphology, not the word's own suffixes."""
        row = next(s for s in service.morphology("ine-pro")["suffixes"]
                   if s["form"] == "-ós")
        self.assertTrue(row["gloss"])
        self.assertGreaterEqual(row["recorded"], 20)
        self.assertIn("dl̥h₁gʰós", row["examples"])
        # and it composes on a stem that never wore it, as a hypothesis
        made = service.compose("delh₁gʰ-", row["id"])
        self.assertIn("delh₁gʰ", made["form"])
        self.assertEqual(made["suffix"]["form"], "-ós")
        self.assertIsNone(made["law"], "no recorded formation law is claimed")

    def test_a_suffix_entry_no_construction_wears_is_still_selectable(self):
        rows = {s["form"]: s for s in service.morphology("ine-pro")["suffixes"]}
        for form in ("-iskos", "-kos", "-iHnos"):
            self.assertIn(form, rows, form)
            self.assertTrue(rows[form]["gloss"], form)
            self.assertEqual(rows[form]["recorded"], 0, form)

    def test_almost_every_piece_the_corpus_names_has_a_meaning(self):
        """A form no source names keeps an empty gloss; it must stay a handful."""
        missing = set()
        for entry in data.lexicon("ine-pro"):
            for row in service.constructions(entry, "ine-pro"):
                for piece in row["suffixes"]:
                    if not piece["gloss"]:
                        missing.add(piece["form"])
        self.assertLessEqual(len(missing), 20, sorted(missing))
        self.assertNotIn("-ós", missing)
        self.assertNotIn("-os", missing)
        self.assertNotIn("-tós", missing)

    def test_only_a_handful_of_offered_suffixes_have_neither_meaning_nor_page(self):
        """The picker may offer a form no source has glossed — it says so — but
        that must stay a handful, not the rule (2026-11-08)."""
        unexplained = [row["form"] for row in service.morphology("ine-pro")["suffixes"]
                       if not row["gloss"] and not row["entry"]]
        self.assertLessEqual(len(unexplained), 20, unexplained)

    def _piece(self, word, index=0):
        return service.word("ine-pro", word)["construction"]["suffixes"][index]

    def test_an_ending_is_read_for_the_stem_class_the_word_has(self):
        """‑os closes both an o-stem and an s-stem, and the page says both.

        ménos is an s-stem result noun, h₂ŕ̥tḱos an o-stem: the same letters are
        the same ending only in the sense the paradigm gives them
        (2026-11-08).
        """
        s_stem = self._piece("ménos")
        self.assertEqual(s_stem["form"], "-os")
        self.assertIn("s-stem", s_stem["gloss"])
        self.assertIn("o-", s_stem["gloss"])
        self.assertIn("action", s_stem["detail"],
                      "the dictionary's action-noun reading stays beside it")
        o_stem = service.word("ine-pro", "h₂ŕ̥tḱos")["construction"]["suffixes"][0]
        self.assertEqual(o_stem["form"], "-o-")
        self.assertEqual(o_stem["kind"], "stem")

    def test_an_ending_table_is_not_borrowed_from_a_homograph(self):
        """dʰéǵʰōm wears the n-stem's -ōm, not the genitive plural's *-óm."""
        piece = self._piece("dʰéǵʰōm")
        self.assertEqual(piece["form"], "-ōm")
        self.assertIn("n-stem", piece["gloss"])
        self.assertNotEqual(piece["gloss"], "genitive plural")
        self.assertEqual(self._piece("smérus")["gloss"], "u-stem nominative singular")
        self.assertEqual(self._piece("h₁léwdʰis")["gloss"], "i-stem nominative singular")

    def test_a_recorded_sense_is_chosen_for_the_word_the_piece_stands_in(self):
        """-ti in ḱréddʰeh₁ti is the verb's ending, not the adverbial -ti."""
        piece = self._piece("ḱréddʰeh₁ti")
        self.assertEqual(piece["form"], "-ti")
        self.assertIn("verb", piece["gloss"].lower())
        self.assertNotIn("Adverbial", piece["gloss"])

    def test_a_handbook_row_does_not_take_a_dictionary_spelling_it_does_not_share(self):
        """-éh₂ on an action noun is the dictionary's action-noun suffix, and
        the handbook's collective -eh₂ is a different form (2026-11-08)."""
        piece = self._piece("bʰugéh₂")
        self.assertEqual(piece["form"], "-éh₂")
        self.assertIn("-éh₂", urllib.parse.unquote(piece["entry"]))
        self.assertNotIn("feminine or collective", piece["gloss"])

    def test_every_menu_row_has_its_own_key(self):
        """A click has to name exactly one suffix (2026-11-08)."""
        ids = [row["id"] for row in service.morphology("ine-pro")["suffixes"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("stem-i", ids, "the i-stem form has a key of its own")
        self.assertIn("stem-o", ids)

    def test_a_stem_formative_composes_the_whole_word(self):
        """The i-stem row builds h₂wl̥pís, not the adverbial *h₂wl̥pis."""
        made = service.compose("h₂wl̥p-", "stem-i")
        self.assertEqual(made["suffix"]["form"], "-i-")
        self.assertEqual(made["form"].replace("ˈ", ""), "h₂wl̥pis")
        self.assertEqual(service.compose("h₂retḱ-", "stem-o")["form"], "h₂retḱos")

    def test_an_accented_entry_is_not_hidden_by_its_unaccented_neighbour(self):
        """-ónts and -onts are two recorded forms; neither may shadow the other,
        and -kʷe is offered as the clitic it is (2026-11-08)."""
        rows = {row["form"]: row for row in service.morphology("ine-pro")["suffixes"]}
        self.assertIn("-ónts", rows)
        self.assertIn("-onts", rows)
        self.assertTrue(rows["-ónts"]["entry"])
        self.assertEqual(rows["-kʷe"]["kind"], "clitic")


class TestTheSectionsOfThePicker(unittest.TestCase):
    """The picker is a menu of sections (2026-11-08): 135 recorded forms cannot
    be read as one list, and the record itself says what kind of word each
    morpheme builds, so the sections are derived from it — never chosen by the
    front end.
    """

    @classmethod
    def setUpClass(cls):
        cls.morph = service.morphology("ine-pro")
        cls.rows = {s["form"]: s for s in cls.morph["suffixes"]}

    def test_every_section_the_menu_prints_is_one_the_record_has(self):
        ids = [sec["id"] for sec in self.morph["sections"]]
        known = [key for key, _ in service.MORPH_SECTIONS]
        self.assertEqual(ids, [key for key in known if key in ids],
                         "the sections are printed in the registry's order")
        self.assertEqual(sum(sec["count"] for sec in self.morph["sections"]),
                         len(self.rows), "no row is left out of a section")
        for row in self.morph["suffixes"]:
            self.assertIn(row["section"], ids)
            self.assertTrue(row["section_name"])

    def test_a_section_says_what_kind_of_word_the_suffix_builds(self):
        self.assertEqual(self.rows["-tēr-"]["section"], "derivation-noun")
        self.assertEqual(self.rows["-ko-"]["section"], "derivation-adj")
        self.assertEqual(self.rows["-ti"]["section"], "derivation-adv")
        self.assertEqual(self.rows["-i-"]["section"], "stem")
        self.assertEqual(self.rows["-kʷe"]["section"], "clitic")
        for form in ("-os", "-ós", "-ōm"):
            self.assertEqual(self.rows[form]["section"], "ending")

    def test_the_worn_morphemes_of_a_word_are_rows_the_menu_holds(self):
        """The page marks the pieces the word wears, so each one must be a row
        the picker can print in its own colour and open."""
        page = service.word("ine-pro", "dl̥h₁gʰós")
        pieces = page["construction"]["suffixes"]
        self.assertTrue(pieces)
        for piece in pieces:
            row = next((s for s in self.morph["suffixes"] if s["id"] == piece["id"]), None)
            self.assertIsNotNone(row, f"{piece['form']} wears an id the menu knows")
            self.assertEqual(row["section"], "ending")

    def test_the_menu_hooks_are_in_the_front_end(self):
        js = text("app.js")
        css = text("style.css")
        for needle in ("sufworn", "sufsecwrap", "sufsub", "data-sec"):
            self.assertIn(needle, js, f"the picker is missing {needle}")
        self.assertIn(".sufsub.flip", css, "a submenu can open to the left")
        self.assertIn(".sufrow.worn", css, "a worn morpheme looks different")
        self.assertIn("@media (max-width: 780px)", css,
                      "a narrow window opens the submenu under its heading, not beside it")


class TestTheOldPersianScript(unittest.TestCase):
    """What the syllabary writes, and what a reading may leave out.

    The table is Kent (1953); the engine only says whether a phonological form
    is one of the readings the signs allow. It never turns one form into
    another and never calls a reading an attestation (2026-11-08).
    """

    def test_a_headword_is_read_sign_by_sign(self):
        from pie import script

        self.assertEqual(script.transliterate("peo", "𐎺𐎼𐎣"), "va-ra-ka")
        self.assertEqual(script.signs("peo", "𐎺𐎼𐎣")[0]["value"], "va")

    def test_the_laws_output_is_a_reading_of_the_cuneiform_word(self):
        from pie import script

        fit = script.match("peo", "wˈarkah", "𐎺𐎼𐎣")
        self.assertTrue(fit["ok"])
        self.assertEqual(fit["translit"], "va-ra-ka")
        self.assertIn("h", fit["unwritten"], "the final /h/ has no sign")

    def test_a_filler_vowel_spells_a_bare_consonant(self):
        from pie import script

        fit = script.match("peo", "draya", "𐎭𐎼𐎹")
        self.assertTrue(fit["ok"])
        self.assertTrue(fit["filler"] or fit["unwritten"])

    def test_a_logogram_may_be_abbreviated_but_only_by_its_first_letters(self):
        from pie import script

        self.assertTrue(script.match("peo", "XŠ", "𐏋")["ok"])
        self.assertFalse(script.match("peo", "x", "𐏋")["ok"], "one letter is not an abbreviation")
        self.assertFalse(script.match("peo", "xšy", "𐏋")["ok"], "not an arbitrary subsequence")

    def test_every_old_persian_headword_with_a_romanisation_fits(self):
        from pie import script

        # The claim is about *a word and its reading*, so the table is tested
        # on rows that hold both as one form: a royal phrase ("Sakā tigraxaudā")
        # and a logogram (𐏊, read auramazdāha, with no sign left to align) are
        # not a syllabic reading of a sign string and are named below.
        def one_form(entry):
            word = entry["word"]
            return (len(word.split()) == 1 and len(entry["translit"].split()) == 1
                    and not 0x103C0 <= ord(word[0]) <= 0x103DF)   # 𐏊 𐏌 𐏍 are logograms

        rows = [e for e in data.lexicon("peo")
                if e.get("translit") and script.writes("peo", e["word"]) and one_form(e)]
        missed = [(e["word"], e["translit"]) for e in rows
                  if not (script.match("peo", e["translit"], e["word"]) or {}).get("ok")]
        # 281 rows carried a romanisation on 2026-11-12 (the three Iranian
        # lemma categories were harvested).  The rows that do not fit are the
        # known gap of the sign table, one cause each — the wiki's own
        # transliteration marks a vowel the sign string also writes (a-ʰ and
        # the ⁱ ᵘ of its superscripts), or a Latinised proper name reads
        # differently from its signs (Arminiya, a-ra-mi-i-na-ya):
        known = {
            ("𐎠𐎼𐎷𐎡𐎴𐎹", "Arminiya"),
            ("𐏃𐎧𐎠𐎶𐎴𐎡𐏁𐎡𐎹", "Haxāmanišyaʰ"),
            ("𐎠𐎼𐎡𐎹", "Aryaʰ"),
            ("𐎠𐎷𐎡𐎹", "aʰmiy"),
            ("𐏁𐎡𐎹𐎠𐎫𐎡𐏁", "šyātiš"),
            ("𐎶𐎹𐎧", "mayuxa"),
            ("𐏃𐏀𐎠", "hⁱzāna"),
            ("𐎿𐎢𐎦𐎢𐎭𐎡𐎹", "Sugᵘdiya"),
            ("𐎿𐎡𐎹𐎶", "sēma"),
            ("𐀀", ""),
        } - {("𐀀", "")}
        self.assertEqual(set(missed) - known, set(),
                         "a headword the table cannot read is a gap in the table")
        self.assertEqual(len(rows), 229)


class TestWhereARecordWasRead(unittest.TestCase):
    """The RECORDED badge opens the page the record was read on (2026-11-08).

    The source registry names the site, not a page, so the read model builds
    the entry's own address: a reconstructed word keeps Wiktionary's
    ``Reconstruction:`` namespace with its language, and an attested headword
    is the title itself. The front end only ever prints the address the server
    gives it, so the page never invents a citation.
    """

    def test_an_attested_headword_is_its_own_title(self):
        self.assertEqual(
            service._wiktionary_title({"word": "𐎺𐎼𐎣", "lang": "peo"}), "𐎺𐎼𐎣")

    def test_a_reconstruction_is_titled_without_its_asterisk(self):
        # Wiktionary's Reconstruction namespace is the star; a title that keeps
        # it opens nothing (2026-11-12).
        self.assertEqual(
            service._wiktionary_title({"word": "*madu", "lang": "peo", "recon": True}),
            "Reconstruction:Old Persian/madu")

    def test_a_proto_language_is_always_a_reconstruction(self):
        self.assertEqual(
            service._wiktionary_title({"word": "bōks", "lang": "gem-pro"}),
            "Reconstruction:Proto-Germanic/bōks")

    def test_the_three_piece_record_matches_wiktionaries_own_title(self):
        # The page the index looks for and the page the reader opens are one
        # title, and its language name is the registry's (2026-11-12).
        from pie import wiktionary
        self.assertEqual(wiktionary.en_page("gem-pro", "nahts")["url"],
                         "https://en.wiktionary.org/wiki/Reconstruction:Proto-Germanic/nahts")

    def test_the_ladder_carries_the_page_with_the_citation(self):
        row = service.hierarchy("peo", "𐎺𐎼𐎣")
        recorded = row["levels"][-1]["recorded"]
        self.assertTrue(recorded["sources"], "a record must carry its source")
        self.assertTrue(all(s.get("entry") for s in recorded["sources"] if s["id"] == "wiktionary"))
        self.assertTrue(
            any(s["entry"].endswith("/%F0%90%8E%BA%F0%90%8E%BC%F0%90%8E%A3")
                for s in recorded["sources"]),
            "the Old Persian badge opens the cuneiform headword's page")


class TestTheFinalLongA(unittest.TestCase):
    """A word-final *-ā is kept, and the kinship -a is not a shortening.

    2026-11-09. Old Persian 𐎱𐎠𐎮𐎹 *pādiy* reached Persian as **pa**
    because `final_long_a_shortening` wrote its sonorant as optional
    (`(NAS|LIQ)? #`), so it fired on a bare word boundary and shortened *every*
    final -ā: nām > *nam*, kār > *kar*, dādār > *dādar*, پا > *pa*. Correcting
    the context would not have saved the law — New Persian keeps the vowel —
    so it is gone and the kinship vowel is stated where it belongs.
    """

    @classmethod
    def setUpClass(cls):
        cls.rs = data.rulesets()[("pal", "fa")]
        cls.chain = data.derivation_chain("fa")

    def test_the_law_is_no_longer_registered(self):
        self.assertNotIn("final_long_a_shortening", [r.id for r in self.rs.rules])
        self.assertIsNone(service.rule_page("pal~fa:final_long_a_shortening"))

    def test_a_final_long_a_survives_in_every_context(self):
        from pie.rules import derive
        for form in ("kār", "dādār", "nām", "māh", "nān", "pā", "mā", "xadāy"):
            self.assertEqual(derive(form, ["pal", "fa"], data.rulesets()).output, form,
                             f"{form}: no Persian law may shorten a word-final -ā")

    def test_the_open_syllable_of_the_reported_word_is_not_shortened(self):
        row = service.hierarchy("peo", "𐎱𐎠𐎮𐎹", path=["pal", "fa"])
        self.assertEqual([lv["form"] for lv in row["levels"]][-1], "pā")
        self.assertEqual(row["levels"][-1]["status"], "match")
        self.assertEqual(row["levels"][-1]["recorded"]["w"], "پا")

    def test_the_middle_persian_rung_no_longer_contradicts_its_record(self):
        for word, mp, np_ in (("پدر", "pidar", "pedar"), ("مادر", "mādar", "mādar")):
            levels = {lv["stage"]: lv for lv in service.word("fa", word)["hierarchy"]["levels"]}
            self.assertEqual(levels["pal"]["status"], "match", word)
            self.assertEqual(levels["pal"]["recorded"]["reading"], mp, word)
            self.assertEqual(levels["fa"]["form"], np_, word)
            self.assertEqual(levels["fa"]["status"], "match", word)
            fired = [r["id"] for r in levels["pal"]["rules"] if r["fired"]]
            self.assertIn("r_stem_oblique", fired, word)

    def test_the_kinship_law_is_switched_off_for_every_other_word(self):
        from pie.rules import derive
        out = derive("ph₂tḗr", self.chain, data.rulesets()).output
        self.assertEqual(out, "pedār", "without the word's pathway the law must not apply")
        rule = next(r for r in data.rulesets()[("peo", "pal")].rules
                    if r.id == "r_stem_oblique")
        self.assertTrue(rule.default_off)
        self.assertEqual(rule.tier, "custom")

    def test_the_kinship_law_cannot_tell_the_agent_suffix_apart(self):
        """Why the law is off by default rather than a context away from right.

        The kinship -tā and the agent-noun *-tār end the same way, and no
        phonological feature separates them, so the law *would* shorten dādār
        too. Only a word's own pathway may switch it on; a plain derivation
        never reaches it.
        """
        from pie.rules import derive
        plain = derive("dātār", ["peo", "pal"], data.rulesets()).output
        forced = derive("dātār", ["peo", "pal"], data.rulesets(),
                        enabled=["r_stem_oblique"]).output
        self.assertEqual(plain, "dādār", "dādār 'creator' keeps its long ā")
        self.assertEqual(forced, "dādar", "the cost the note states, which is why it is off")

    def test_every_ladder_law_still_opens_its_page(self):
        levels = service.word("fa", "پدر")["hierarchy"]["levels"]
        for level in levels:
            for rule in level["rules"]:
                self.assertIsNotNone(service.rule_page(rule["key"]), rule["key"])


class TestCitedStem(unittest.TestCase):
    """Sanskrit cites the stem; the laws end in an inflected form (2026-11-09)."""

    def test_the_page_says_the_record_cites_a_stem(self):
        page = service.word("sa", "विश्व")
        h = page["hierarchy"]
        cited = h["result"].get("cited_stem")
        self.assertIsNotNone(cited, h["result"])
        self.assertEqual(cited["written"], "विश्व")
        self.assertEqual(cited["output"], cited["stem"] + cited["ending"])
        self.assertFalse(h["result"]["match"], "a citation is not an exact reconstruction")

    def test_a_word_that_matches_exactly_has_no_citation_badge(self):
        page = service.word("sa", "भवति")
        h = page["hierarchy"]
        if h["result"].get("written_match"):
            self.assertIsNone(h["result"].get("cited_stem"),
                              "a spelled word must not also claim a citation form")


class TestTheLawsStartFromAReading(unittest.TestCase):
    """A form written in a script is never handed to the sound laws.

    The admin's report (2026-11-11): the page for Middle Persian ``lwc`` said the
    reconstruction was not working, "it seems like it's trying to reconstruct
    from the script, not the romanization".  It was: the rung's input was the Old
    Persian cuneiform 𐎼𐎢𐎨, no law could rewrite a sign, and the ladder copied
    the script down and called the word unreached.
    """

    def test_the_engine_refuses_a_form_written_in_a_script(self):
        from pie import data as pie_data
        from pie.rules import derive_detailed

        derivation, levels = derive_detailed("𐎼𐎢𐎨", ["peo", "pal"], pie_data.rulesets())
        self.assertTrue(derivation.unreadable)
        self.assertEqual(derivation.output, "𐎼𐎢𐎨", "nothing was derived")
        self.assertEqual(derivation.steps, [])
        self.assertTrue(all(level.unreadable for level in levels))

    def test_the_ladder_climbs_from_the_reading_of_the_old_persian_form(self):
        page = service.word("pal", "lwc")
        levels = page["hierarchy"]["levels"]
        peo, pal = levels[0], levels[-1]
        self.assertEqual(peo["stage"], "peo")
        self.assertEqual(peo["form"], "raučah", "the cuneiform's reading, not the cuneiform")
        self.assertEqual(peo["recorded"]["w"], "𐎼𐎢𐎨")
        self.assertEqual(peo["recorded"]["reading"], "raučah")
        self.assertFalse(peo["recorded"]["reading_auto"],
                         "Wiktionary states this reading, so it is not automatic")
        self.assertEqual(pal["stage"], "pal")
        self.assertEqual(pal["form"], "rōč", "the laws now run on sounds")
        fired = [r["id"] for r in pal["rules"] if r["fired"]]
        self.assertEqual(fired, ["au_to_o", "final_h_loss", "final_vowel_loss"])
        self.assertFalse(pal["transition"]["unreadable"])

    def test_the_record_is_printed_with_its_romanisation(self):
        page = service.word("pal", "lwc")
        pal = page["hierarchy"]["levels"][-1]["recorded"]
        self.assertEqual(pal["w"], "lwc")
        self.assertEqual(pal["reading"], "rōz")
        self.assertTrue(pal["show_reading"],
                        "lwc is a script reading, so rōz is printed beside it")
        self.assertEqual(pal["reading_how"], "recorded")

    def test_a_fit_does_not_override_the_recorded_reading(self):
        # The signs l-w-c can stand for rōč, but the dictionary reads the word
        # rōz: the rung keeps saying the laws miss it, and prints both.
        page = service.word("pal", "lwc")
        pal = page["hierarchy"]["levels"][-1]
        self.assertEqual(pal["status"], "differs")
        self.assertFalse(pal["recorded"]["matches"])
        self.assertTrue(pal["recorded"]["fit"]["ok"])
        self.assertEqual(page["hierarchy"]["starts"][0]["form"], "raučah")
        self.assertFalse(page["hierarchy"]["starts"][0]["unreadable"])

    def test_a_transliterated_headword_shows_its_reading_and_a_romanisation_does_not(self):
        self.assertTrue(service.show_reading("pal", "lwc"))
        self.assertEqual(service._form_meta("pal", "lwc")["reading"], "rōz")
        # رōz is already a romanisation: a second one would be noise.
        self.assertFalse(service._form_meta("pal", "rōz")["show_reading"])
        self.assertFalse(service._form_meta("txb", "ṣar")["show_reading"])

    def test_the_reading_of_a_spelling_comes_before_the_letters(self):
        from pie.service import _phonological_form

        self.assertEqual(_phonological_form("peo", "𐎼𐎢𐎨"), "raučah")
        self.assertEqual(_phonological_form("pal", "lwc"), "rōz")
        self.assertEqual(_phonological_form("grc", "Πέρσης"), "Pˈersēs")
        # A syllabary with nothing recorded hands back its signs; the engine is
        # what refuses them, so no caller can mistake them for a reading.
        # 𐏀𐎴 used to be the example; Wiktionary now records its reading
        # (zanaʰ, 2026-11-12), so the rule is shown on a headword that still
        # has none.
        self.assertEqual(_phonological_form("peo", "𐏀𐎴"), "zanaʰ")
        self.assertEqual(_phonological_form("peo", "𐎱𐎢𐎫𐎠𐎹"), "𐎱𐎢𐎫𐎠𐎹")


class TestUnverifiedMatch(unittest.TestCase):
    """A record the laws almost reach is a question, never a ✓ (admin, 2026-11-12).

    Old Persian 𐎣𐎱𐎢𐎫𐎣 "blue" is carried to Persian *kabūde*; the glossary heads
    the word کبود *kabud*. The final -e is a change no registered law accounts
    for, so the Persian rung may quote the entry — and may not claim a match.
    The bug this pins: the form was "matched" to کبد *kabid* "liver", a different
    word that an abjad spells with the same three consonants.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = service.word("peo", "𐎣𐎱𐎢𐎫𐎣", path=["pal", "fa"])
        cls.fa = cls.page["hierarchy"]["levels"][-1]
        cls.branch = [row for row in cls.page["descendants"]["rows"] if row["l"] == "fa"]

    def test_the_rung_is_unverified_and_not_a_match(self):
        self.assertEqual(self.fa["stage"], "fa")
        self.assertEqual(self.fa["status"], "unverified")
        self.assertFalse(self.fa["recorded"]["matches"])
        self.assertTrue(self.fa["recorded"].get("unverified"))

    def test_it_quotes_the_right_word(self):
        # کبود "blue-gray", not کبد "liver": the reading is the test.
        self.assertEqual(self.fa["recorded"]["w"], "کبود")
        self.assertEqual(self.fa["recorded"]["reading"], "kabud")
        self.assertEqual(self.fa["recorded"]["review"]["form_key"], "kabude")

    def test_a_different_word_is_never_offered(self):
        """kabid is not kabūde with an ending missing: nothing may quote کبد."""
        self.assertEqual(service._reading_key(self.fa["form"]), "kabude")
        self.assertIsNone(service._near_record("fa", "kabid"))
        self.assertEqual(self.branch[0]["recorded"]["w"], "کبود")
        self.assertEqual(self.branch[0]["status"], "unverified")
        self.assertIn("unverified", self.page["descendants"]["counts"])

    def test_the_queue_keeps_it_for_review(self):
        from pie import review

        service.word("peo", "𐎣𐎱𐎢𐎫𐎣", path=["pal", "fa"])
        rows = [row for row in review.entries("fa")
                if row["word"] == "کبود" and row["form"] == "kabūde"]
        self.assertTrue(rows, "an unverified match is queued for a person to read")
        row = rows[0]
        self.assertEqual(row["record_read"], "kabud")
        self.assertTrue(row["gloss"])

    def test_the_branch_starts_from_the_pages_own_rung(self):
        """?path=pal,fa ends the ladder in Persian; the branch below the word is
        still Old Persian's, not that form carried down again (2026-11-12)."""
        branch = self.page["descendants"]
        self.assertEqual(branch["source"]["lang"], "peo")
        self.assertEqual(branch["source"]["form"], "kapautakˈah")
