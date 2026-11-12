"""Building a form at a stage, on the timeline (2026-11-10).

The ladder must allow what a language actually does: at any
stage, two of its words may be joined, or one of its suffixes or endings added,
and the timeline must show that as a step.  These tests pin the contract:

* the address carries the question (`?build=fa:join:خانه@آب`);
* the composed rung says it was **built**, and the step says what was added;
* a composition is never a sound law: a word whose composed form equals its
  record is a `match` about the *form*, and no band is rewritten by it;
* nothing is invented — an affix has to be one the stage records, and a join
  of a word the stage does not hold still runs, but says the piece is unknown.
"""
from __future__ import annotations

import unittest

from pie import service


class ParseBuild(unittest.TestCase):
    def test_three_parts(self):
        spec = service._parse_build("fa:join:خانه@آب")
        self.assertEqual(spec["stage"], "fa")
        self.assertEqual(spec["kind"], "join")
        self.assertEqual(spec["arg"], "خانه")
        self.assertEqual(spec["base"], "آب")

    def test_without_base(self):
        spec = service._parse_build("ine-pro:suffix:eh2")
        self.assertEqual((spec["stage"], spec["kind"], spec["arg"], spec["base"]),
                         ("ine-pro", "suffix", "eh2", ""))

    def test_refusals(self):
        for bad in ("", "fa", "fa:join", "fa:nonsense:x", "xx:join:a", None):
            self.assertIsNone(service._parse_build(bad), bad)


class Compose(unittest.TestCase):
    def test_compound_is_written_with_the_stages_own_seam(self):
        made = service._compose_build(
            {"kind": "join", "arg": "خانه"}, "آب", "fa")
        self.assertEqual(made["form"].replace("\u200c", ""), "آبخانه")
        self.assertEqual(made["kind"], "compound")
        self.assertEqual([p["form"] for p in made["pieces"]], ["آب", "خانه"])
        self.assertTrue(all(p["known"] for p in made["pieces"]))

    def test_suffix_is_the_registered_one(self):
        made = service._compose_build({"kind": "suffix", "arg": "ka-animal"},
                                      "h₂wl̥pís", "ine-pro")
        self.assertTrue(made["form"].startswith("h₂wl̥p"))
        self.assertEqual(made["pieces"][1]["pos"], "suffix")
        self.assertIn("law", made)      # the cited formation law, not a guess

    def test_unknown_suffix_is_refused(self):
        self.assertIsNone(service._compose_build(
            {"kind": "suffix", "arg": "no-such-suffix"}, "h₂wl̥pís", "ine-pro"))

    def test_ending_replaces_the_word_final(self):
        made = service._compose_build({"kind": "ending", "arg": "-éh₁"},
                                      "h₂ŕ̥tḱos", "ine-pro")
        self.assertIsNotNone(made)
        self.assertTrue(made["form"].endswith("éh₁"))
        self.assertFalse(made["form"].endswith("os"))


class Ladder(unittest.TestCase):
    def test_a_join_lands_on_the_recorded_word(self):
        h = service.hierarchy("fa", "آب‌خانه", build="fa:join:خانه@آب")
        self.assertIsNotNone(h)
        stages = [(row["stage"], row["form"]) for row in h["levels"]]
        self.assertEqual(stages[0], ("fa", "آب"))
        self.assertEqual(h["levels"][1]["status"], "match")
        self.assertTrue(h["levels"][1]["built"])
        self.assertEqual(h["build"]["kind"], "compound")
        # The record is the dictionary's own headword, without the seam.
        self.assertEqual((h["levels"][1]["recorded"] or {}).get("w"), "آبخانه")

    def test_a_built_rung_does_not_rewrite_the_band(self):
        h = service.hierarchy("fa", "آب‌خانه", build="fa:join:خانه@آب")
        self.assertIsNone(h["category"])

    def test_suffix_at_the_words_own_stage_is_written(self):
        h = service.hierarchy("fa", "دست", build="fa:suffix:i")
        last = h["levels"][-1]
        self.assertEqual(last["form"], "دستی")     # script, not dast + ی
        self.assertEqual(last["status"], "match")
        self.assertEqual(h["build"]["stage"], "fa")

    def test_a_form_with_no_ancestry_still_has_a_timeline(self):
        h = service.hierarchy("fa", "آب‌خانه")
        self.assertIsNotNone(h)
        self.assertEqual(len(h["levels"]), 1)
        self.assertEqual(h["levels"][0]["status"], "start")

    def test_build_options_come_from_the_stage(self):
        fa = service.build_options("fa")
        self.assertTrue(any(s["id"] == "i" for s in fa["suffixes"]))
        self.assertTrue(fa["joining"]["zwnj"])
        pie = service.build_options("ine-pro")
        self.assertTrue(pie["suffixes"])
        self.assertTrue(any(e["form"] for e in pie["endings"]))


class ConstructionPiece(unittest.TestCase):
    """A piece the stage's glossary holds says what it means (admin, 2026-11-12).

    *andaswarō's etymology is ``From *anda- + *swarō.`` — an arithmetic with no
    gloss in brackets — so the construction row used to come back with both
    pieces ``known: true`` and an empty gloss: the page opened the piece's own
    entry and still printed no meaning under it, which reads exactly like a
    word the page did not recognise.  The piece is answered by the same reader
    as the rung and its ✓ now, so a word known in one place is known in all.
    """

    def test_every_piece_carries_the_meaning_its_entry_gives(self):
        row = service.word("gem-pro", "andaswarō")["construction"]
        self.assertEqual(row["base"]["form"], "anda-")
        self.assertTrue(row["base"]["known"])
        self.assertEqual(row["base"]["gloss"], "facing")
        self.assertEqual(row["base"]["link"], "#/word/gem-pro/anda-")
        self.assertTrue(row["members"][0]["gloss"].startswith("a solemn statement"))

    def test_a_gloss_the_etymology_quotes_still_wins(self):
        self.assertEqual(service._base_row("gem-pro", "swarō", "“swearing”")["gloss"],
                         "swearing")

    def test_a_piece_the_stage_does_not_hold_stays_unknown(self):
        row = service._base_row("gem-pro", "no-such-word-at-all")
        self.assertFalse(row["known"])
        self.assertEqual(row["gloss"], "")
        self.assertEqual(row["link"], "")


class PreStageAncestry(unittest.TestCase):
    """A `pre-` label marks the form it precedes — it does not license a climb.

    Wiktionary writes *anda-'s origin in prose: "From pre-Germanic *h₂entó-, a
    combining form or allative formation from the Proto-Indo-European root noun
    *h₂énts".  `_prose_ancestry` skipped "pre-Germanic" because it is not a
    registered stage and took the next registered stage it found — *h₂énts —
    which is the word *h₂entó- was made from, one level above the ancestor.
    The marked form belongs to the stage the sentence names for it, and the
    rest of the sentence is that form's own history (admin, 2026-11-12).
    """

    def test_a_pre_stage_label_marks_the_form_it_precedes(self):
        entry = service._lemma_entry("gem-pro", "anda-")
        self.assertEqual(service._prose_ancestry(entry),
                         [("ine-pro", "h₂entó-", "derived")])

    def test_the_pre_form_is_a_word_the_stage_heads(self):
        entry = service._lemma_entry("ine-pro", "h₂entó-")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["gloss"], ["against"])

    def test_the_pre_form_keeps_its_own_construction(self):
        entry = service._lemma_entry("ine-pro", "h₂entó-")
        builds = service._rung_builds(entry, "ine-pro", "h₂entó-")
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["kind"], "combining")
        self.assertEqual([p["form"] for p in builds[0]["pieces"]], ["*h₂énts"])
        # The one piece is a word with a construction of its own, drawn above.
        nested = builds[0]["pieces"][0]["branch"]["builds"]
        self.assertEqual([p["form"] for p in nested[0]["pieces"]], ["*h₂ent-", "*s"])

    def test_the_ladder_climbs_through_the_pre_form(self):
        parent = service._origin_node("gem-pro", "*anda-")["parents"][0]
        self.assertEqual((parent["lang"], parent["form"]), ("ine-pro", "h₂entó-"))
        self.assertEqual(parent["builds"][0]["kind"], "combining")
        self.assertEqual(parent["builds"][0]["pieces"][0]["form"], "*h₂énts")

    def test_a_one_piece_row_of_another_kind_is_not_a_construction(self):
        entry = {"word": "x-", "lang": "ine-pro", "built_as": [
            {"lang": "ine-pro", "kind": "suffix", "of": "x-",
             "pieces": [["*h₂énts", ""]]}]}
        self.assertEqual(service._rung_builds(entry, "ine-pro", "x-"), [])


class OneWordBuildsAnother(unittest.TestCase):
    """A word the record states as *formed from* one word is that one step.

    Wiktionary's *aiganaz says "Adjectival formation from *aiganą ('to own,
    possess')" — one base, no suffix — and lists it under Participle as "past
    participle of *aiganą".  The supplement stores that as one `derivation`
    piece, so the timeline above *aiganaz is the word it was made from, and
    that word's own climb (PIE *h₂eh₂óyḱe) continues above it (admin,
    2026-11-12: *aiganą is an entry, and it is the construction of *aiganaz).
    """

    def test_the_entry_states_aiganą_as_its_base(self):
        entry = service._lemma_entry("gem-pro", "aiganaz")
        builds = service._rung_builds(entry, "gem-pro", "aiganaz")
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["kind"], "derivation")
        self.assertEqual([p["form"] for p in builds[0]["pieces"]], ["*aiganą"])
        piece = builds[0]["pieces"][0]
        self.assertTrue(piece["known"], "*aiganą is a glossary entry")
        self.assertEqual(piece["gloss"], "to possess, to own")
        # The piece's own history is drawn above it, not flattened away.
        self.assertEqual(piece["branch"]["parents"][0]["form"], "*h₂eh₂óyḱe")

    def test_the_ladder_starts_at_the_word_the_record_builds(self):
        page = service.word("gem-pro", "aiganaz")
        levels = page["hierarchy"]["levels"]
        self.assertEqual((levels[-1]["stage"], levels[-1]["form"]),
                         ("gem-pro", "aiganaz"))
        self.assertEqual([p["form"] for p in levels[-1]["builds"][0]["pieces"]],
                         ["*aiganą"])

    def test_a_one_piece_join_is_not_a_construction_start(self):
        entry = {"word": "x", "lang": "gem-pro", "built_as": [
            {"lang": "gem-pro", "kind": "suffix", "of": "x",
             "pieces": [["*aiganą", ""]]}]}
        self.assertIsNone(service._own_construction(entry, ["ine-pro", "gem-pro"]))


class ReduplicationTest(unittest.TestCase):
    """Reduplication is a formation, not a sound law (admin, 2026-11-12).

    *h₂eh₂óyḱe's page said "Reduplicated stative of the root *h₂eyḱ-" and the
    timeline showed nothing above the word, because only `built_as` rows were
    read as constructions.  The sentence names the formation and the root it
    repeats, so it is one step of the ladder; its type and grade come from the
    stage's morphology table, never from the sentence.
    """

    def test_the_sentence_is_one_reduplication_step(self):
        builds = service._rung_builds(
            service._lemma_entry("ine-pro", "h₂eh₂óyḱe"), "ine-pro", "h₂eh₂óyḱe")
        self.assertEqual(len(builds), 1)
        build = builds[0]
        self.assertEqual(build["kind"], "reduplication")
        self.assertEqual(build["formation"], "perfect/stative")
        self.assertEqual(build["confidence"], "stated")
        # The star is the renderer's rule for a reconstructed stage, not part
        # of the piece the record stores.
        self.assertEqual([p["form"] for p in build["pieces"]], ["h₂eyḱ-"])
        self.assertEqual(build["pieces"][0]["grade_label"], "o-grade")

    def test_the_perfect_is_o_grade_and_the_presents_are_not(self):
        cases = {"píph₃eti": ("present-i", "present", "zero grade"),
                 "dédeh₃ti": ("present-e", "present", "full grade"),
                 "memóne": ("perfect-stative", "perfect/stative", "o-grade")}
        for word, (kind, formation, grade) in cases.items():
            with self.subTest(word=word):
                build = service._rung_builds(
                    service._lemma_entry("ine-pro", word), "ine-pro", word)[0]
                self.assertEqual(build["kind"], "reduplication")
                self.assertEqual(build["formation"], formation)
                self.assertEqual(build["pieces"][0]["grade_label"], grade)

    def test_the_aorist_states_no_grade(self):
        build = service._rung_builds(
            service._lemma_entry("ine-pro", "wéwket"), "ine-pro", "wéwket")[0]
        self.assertEqual(build["formation"], "aorist")
        self.assertNotIn("grade", build["pieces"][0])

    def test_two_analyses_are_marked_argued(self):
        build = service._rung_builds(
            service._lemma_entry("ine-pro", "(me)mógʰe"), "ine-pro", "(me)mógʰe")[0]
        self.assertEqual(build["confidence"], "argued")

    def test_a_hedged_or_arithmetic_sentence_is_not_read(self):
        for word in ("bʰébʰrus", "h₁eh₁s-"):
            with self.subTest(word=word):
                entry = service._lemma_entry("ine-pro", word)
                self.assertIsNone(service._reduplication_read(entry))

    def test_a_descendant_is_not_a_reduplication_of_the_root(self):
        # "From Proto-Indo-European *pe-póyh₂-e …, reduplicated stative of
        # *peyh₂-" describes the ancestor's formation, not this word's.
        entry = service._lemma_entry("gem-pro", "bibāną")
        self.assertIsNone(service._reduplication_read(entry))

    def test_the_ladder_starts_at_the_word_and_shows_the_step(self):
        page = service.word("ine-pro", "h₂eh₂óyḱe")
        level = page["hierarchy"]["levels"][-1]
        self.assertEqual(level["form"], "h₂eh₂óyḱe")
        self.assertFalse(level["changed"])
        self.assertEqual(level["recorded"]["gloss"], "to possess, to own")
        self.assertEqual(level["builds"][0]["kind"], "reduplication")


class AncestorHomonym(unittest.TestCase):
    """A spelling may head two words, and the record says which one it means.

    Proto-Indo-European heads *swer- "to ache, fester" and *swer- "to resound;
    to speak loudly".  Proto-Germanic *swarō "oath" is "from Proto-Indo-
    European *swer- (“to say, speak, talk, swear, curse”)", but the ladder
    quoted whichever entry the index listed first and printed "oath" over the
    root of aching (admin, 2026-11-12).
    """

    def test_the_quoted_meaning_chooses_the_sense(self):
        hint = service._ancestor_gloss(service._lemma_entry("gem-pro", "swarō"), "*swer-")
        self.assertEqual(hint, "to say, speak, talk, swear, curse")
        row = service._sense_entry("ine-pro", "*swer-", hint)
        self.assertIn("to speak loudly, to proclaim", row["gloss"])

    def test_the_tree_quotes_the_sense_the_child_names(self):
        build = service._rung_builds(
            service._lemma_entry("gem-pro", "andaswarō"), "gem-pro", "andaswarō")[0]
        parent = build["pieces"][1]["branch"]["parents"][0]
        self.assertEqual(parent["form"], "*swer-")
        self.assertTrue(parent["gloss"].startswith("to resound"))

    def test_without_a_hint_the_first_entry_stands(self):
        self.assertEqual(service._sense_entry("ine-pro", "*swer-")["gloss"],
                         ["to ache", "to fester", "wound; injury"])


if __name__ == "__main__":
    unittest.main()
