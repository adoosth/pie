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


def _parents(node: dict) -> list[dict]:
    """Every node of a climb, the node itself included."""
    out, stack = [], [node]
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(cur.get("parents") or [])
    return out


class ConstructionPiece(unittest.TestCase):
    """A piece the stage's glossary holds says what it means (2026-11-12).

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


    def test_a_piece_statement_with_and_is_read_to_its_end(self):
        """A record joins with "and +", and the stored template can stop short.

        *h₂ḱh₂owsyéti's sentence reads "From *h₂eḱ- (“sharp”) + *h₂ṓws (“ear”) and
        + *-yéti (denominative verbal suffix)"; the arithmetic reader used to
        stop at the word before the conjunction, and its stored row names only
        the two words.  The suffix is a piece of the construction, bound, with
        the morphology table's gloss (2026-11-13).
        """
        entry = service._lemma_index("ine-pro")["h₂ḱh₂owsyéti"]
        builds = service._rung_builds(entry, "ine-pro", "h₂ḱh₂owsyéti")
        self.assertEqual(len(builds), 1, "one analysis, not two copies of it")
        pieces = builds[0]["pieces"]
        self.assertEqual([p["form"] for p in pieces],
                         ["h₂eḱ-", "h₂ṓws", "-yéti"])
        self.assertTrue(pieces[-1]["bound"], "a suffix is a morpheme, not a word")
        self.assertIn("denominative", pieces[-1]["gloss"])

    def test_the_lom_suffix_is_registered_and_builds_a_word(self):
        """`-lom` is a cited PIE suffix, and *ailą's PIE rung is a real entry.

        A requirement: the morphology could add *-lom to a PIE word for
        gem-pro/ailą: the record names *h₂éydʰ-lom, the suffix is registered
        beside *-tro-, and the PIE word is an entry whose own construction is
        *h₂eydʰ- + *-lom (2026-11-13).
        """
        row = [s for s in (service.morphology("ine-pro") or {})["suffixes"]
               if s["id"] == "lom"]
        self.assertTrue(row)
        self.assertEqual(row[0]["form"], "-lo-")
        self.assertEqual(row[0]["ending"], "-m")
        built = service.build_at("ine-pro:suffix:lom@h₂eydʰ-")
        self.assertEqual(built["form"], "h₂eydʰlom")
        self.assertIsNotNone(service._lemma_entry("ine-pro", "h₂éydʰ-lom"),
                             "the PIE word the record names has an entry")
        entry = service._lemma_index("gem-pro")["ailą"]
        rungs = [b for b in service._rung_builds(
            service._lemma_entry("ine-pro", "h₂éydʰ-lom"),
            "ine-pro", "h₂éydʰlom")]
        self.assertEqual([service.normalise_etymon(p["form"])
                          for p in rungs[0]["pieces"]],
                         ["h₂eydʰ", "lom"])

    def test_a_piece_climbs_the_stage_the_word_itself_names(self):
        """A word drawn as a piece climbs what its own page climbs.

        fa جو?sense=1 shows Middle Persian jaw; آبجو's timeline lost it, because
        the node walk preferred *any* inheritance over a nearer derivation and
        Wiktionary writes the Persian ← Middle Persian link with `{{der}}`
        (2026-11-13: "The timeline for a word should appear more-or-less
        exactly the same if another page refers to it").
        """
        node = service._origin_node("fa", "جو")
        self.assertEqual(node["parents"][0]["lang"], "pal")
        self.assertEqual(node["parents"][0]["form"], "ǰaw")

    def test_a_piece_climbs_the_same_stages_as_its_own_page(self):
        ladder = [lv["stage"] for lv in
                  service.word("fa", "جو", sense=1)["hierarchy"]["levels"]]
        branch, node = ["fa"], service._origin_node("fa", "جو")
        while node.get("parents"):
            node = node["parents"][0]
            branch.append(node["lang"])
        self.assertEqual(list(reversed(branch)), ladder)

    def test_a_piece_of_another_language_climbs_the_donor_the_row_states(self):
        """A compound's row can state where one of its pieces came from.

        fa رضاقلی is "a compound of رضا + Old Anatolian Turkish قلی": the second
        piece is a word of the donor, and its fa entry heads another homonym and
        records no origin, so the timeline hung a ``???`` over it (
        2026-11-13 — "قلی is obviously a borrowing, so it should never have
        shown the question marks").
        """
        entry = service._lemma_entry("fa", "رضاقلی")
        pieces = service._rung_builds(entry, "fa", "رضاقلی")[0]["pieces"]
        qoli = [p for p in pieces if p["form"] == "قلی"][0]
        self.assertEqual(qoli["branch"]["terminal"], "")
        self.assertEqual(qoli["branch"]["parents"][0]["lang"], "trk-oat")
        self.assertEqual(qoli["branch"]["parents"][0]["terminal"], "borrowed")
        self.assertIsNone(service._unexplained_branch(qoli["branch"]))

    def test_a_piece_brings_the_whole_ladder_of_its_own_page(self):
        """A piece climbs every rung its own page draws, not only the recorded ones.

        fa ناراضی is a construction of ناـ + راضی, and ناـ's own page runs from
        PIE *né through Proto-Iranian, Old Persian and Middle Persian to
        Persian.  The piece's climb used to follow only the rows a record
        states, so the same word looked shorter wherever another page quoted it
        (2026-11-13: "the timeline above نا only shows from Proto-Indo-
        Iranian").  The rungs the laws fill in are `derived` — drawn, never
        claimed as entries — and they are not holes.
        """
        node = service._origin_node("fa", "ناـ")
        branch, cur = [], node
        while cur:
            branch.append(cur["lang"])
            cur = (cur.get("parents") or [None])[0]
        levels = service.word("fa", "ناـ")["hierarchy"]["levels"]
        self.assertEqual(list(reversed(branch)), [r["stage"] for r in levels],
                         "the piece climbs exactly the stages its own page draws")
        self.assertIn("peo", branch)
        self.assertIn("pal", branch)
        self.assertTrue(any(n.get("derived") for n in _parents(node)),
                        "the stage the record does not name says it is derived")
        self.assertIsNone(service._unexplained_branch(node))

    def test_a_non_pie_piece_says_non_pie_not_no_entry(self):
        """Arabic is outside what the model holds; the page must not call it missing."""
        entry = service._lemma_entry("fa", "ناراضی")
        pieces = service._rung_builds(entry, "fa", "ناراضی")[0]["pieces"]
        razi = [p for p in pieces if p["form"] == "راضی"][0]
        donor = razi["branch"]["parents"][0]
        self.assertEqual(donor["lang"], "ar")
        self.assertTrue(donor["outside"], "Arabic is outside the family, not missing")
        self.assertEqual(donor["terminal"], "borrowed")

    def test_a_piece_with_no_stated_origin_is_still_a_question_mark(self):
        """Nothing is invented for a piece whose origin no record states."""
        entry = service._lemma_entry("fa", "میرآب")
        node = service._origin_node("fa", "میر")
        self.assertEqual(node["terminal"], "end")
        self.assertIsNotNone(service._unexplained_branch(node))
        holes = service.unrecorded_ancestry(entry, service.data.derivation_chain("fa"))
        self.assertEqual([h["form"] for h in holes if h.get("kind") == "origin"], ["میر"])

class PreStageAncestry(unittest.TestCase):

    """A `pre-` label marks the form it precedes — it does not license a climb.

    Wiktionary writes *anda-'s origin in prose: "From pre-Germanic *h₂entó-, a
    combining form or allative formation from the Proto-Indo-European root noun
    *h₂énts".  `_prose_ancestry` skipped "pre-Germanic" because it is not a
    registered stage and took the next registered stage it found — *h₂énts —
    which is the word *h₂entó- was made from, one level above the ancestor.
    The marked form belongs to the stage the sentence names for it, and the
    rest of the sentence is that form's own history (2026-11-12).
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
    that word's own climb (PIE *h₂eh₂óyḱe) continues above it (
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
    """Reduplication is a formation, not a sound law (2026-11-12).

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
    root of aching (2026-11-12).
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


class ConstructionCarries(unittest.TestCase):
    """A registered construction may carry a word to "fully explained".

    The rule (2026-11-13): a word is fully explained when every
    segment starts from a PIE etymon (or from outside the family), the exact
    form is produced — by cited laws *or* by the record's own registered
    construction — and the result agrees with what the literature records.
    *andaswarō is the case: it is *anda- + *swarō, the pieces spell it, and
    each piece's own record names a PIE etymon (*h₂entó-, *swer-).  A
    construction never overrides a law, never counts when its pieces do not
    spell the word, and never counts when a piece has nowhere to stand.
    """

    def test_andaswarō_is_carried_by_its_construction(self):
        entry = service._lemma_entry("gem-pro", "andaswarō")
        path = service.construction_path(entry, "gem-pro")
        self.assertEqual(path["note"], "*anda- + *swarō")
        self.assertTrue(path["exact"])
        self.assertTrue(path["explained"])
        self.assertEqual([p["form"] for p in path["pieces"]], ["*anda-", "*swarō"])
        # Each piece's origin is the PIE form its own entry records.
        self.assertEqual([p["origin"] for p in path["pieces"]],
                         ["PIE *h₂entó", "PIE *swer"])

    def test_the_page_says_fully_explained(self):
        page = service.word("gem-pro", "andaswarō")
        self.assertEqual(page["category"]["category"], "full")
        self.assertEqual(page["category"]["reason"], "construction of *anda- + *swarō")

    def test_a_piece_with_no_pie_origin_is_not_green(self):
        # *nonsense* is "non- + sense": sense reaches PIE, non- does not.
        entry = service._lemma_entry("en", "nonsense")
        path = service.construction_path(entry, "en")
        self.assertTrue(path["exact"])
        self.assertFalse(path["explained"])
        self.assertEqual(path["unexplained"], ["non-"])
        page = service.word("en", "nonsense")["category"]
        self.assertEqual(page["category"], "partial")
        # The worklist names the rungs the glossary lacks *and* the piece that
        # has nowhere to stand.  v0.17.18 began walking a compound's pieces, so
        # non-'s own chain (Middle English non → Old English nān → Proto-West
        # Germanic *nain) is part of the word's hole now; the origin row is the
        # one that used to be the whole message (stale assertion fixed 2026-11-13
        # while a critic batch re-read the class).
        self.assertEqual(page["reason"],
                         "no entry for Middle English non, Old English nān, "
                         "Proto-West Germanic *nain; no recorded origin for "
                         "Middle English non-")

    def test_a_word_whose_history_is_inheritance_is_not_a_construction(self):
        # blackbird is inherited from Middle English blakebird; "equivalent to
        # black + bird" is a surface analysis, not the word's construction.
        entry = service._lemma_entry("en", "blackbird")
        self.assertIsNone(service.construction_path(entry, "en"))
        self.assertEqual(service.word("en", "blackbird")["category"]["category"],
                         "partial")

    def test_pieces_that_do_not_spell_the_word_do_not_count(self):
        # *aiganaz is a one-piece derivation from *aiganą: the construction
        # states the base, not a spelling, so it cannot carry the form.
        entry = service._lemma_entry("gem-pro", "aiganaz")
        path = service.construction_path(entry, "gem-pro")
        self.assertFalse(path["exact"])

    def test_a_suffix_written_without_its_hyphen_still_finds_the_suffix(self):
        # growth's row names the kind instead ("th", glossed "abstract nominal
        # suffix"); the lookup must be -th, not the unrelated word th.
        entry = service._lemma_entry("en", "growth")
        path = service.construction_path(entry, "en")
        self.assertEqual([p["form"] for p in path["pieces"]], ["grow", "-th"])
        self.assertEqual(path["pieces"][1]["origin"], "PIE *iteh₂")

    def test_verdict_never_greens_a_lawless_word_without_a_construction(self):
        from pie import categories
        self.assertEqual(
            categories.verdict(recorded=True, matched_by=None,
                               pie_linked=True)["category"], "partial")
        self.assertEqual(
            categories.verdict(recorded=True, matched_by="joined",
                               pie_linked=True)["category"], "partial")

    def test_verdict_makes_an_exact_construction_dark_green(self):
        from pie import categories
        row = categories.verdict(
            recorded=True, matched_by="joined",
            construction={"note": "*a + *b", "exact": True,
                          "explained": True, "stated": True})
        self.assertEqual(row["category"], "full")
        self.assertEqual(row["reason"], "construction of *a + *b")

    def test_a_recorded_step_that_disagrees_is_light_green(self):
        from pie import categories
        row = categories.verdict(
            recorded=True, matched_by="joined",
            mismatched_steps=["Proto-Germanic"],
            construction={"note": "*a + *b", "exact": True,
                          "explained": True, "stated": True})
        self.assertEqual(row["category"], "adjusted")
        self.assertIn("construction of *a + *b", row["reason"])
        self.assertIn("Proto-Germanic", row["reason"])

    def test_our_own_composition_needs_the_approval_rule(self):
        from pie import categories
        row = categories.verdict(
            recorded=True, matched_by="joined", approved=False,
            construction={"note": "*a + *b", "exact": True,
                          "explained": True, "stated": False})
        self.assertEqual(row["category"], "partial")
        row = categories.verdict(
            recorded=True, matched_by="joined", approved=True,
            construction={"note": "*a + *b", "exact": True,
                          "explained": True, "stated": False})
        self.assertEqual(row["category"], "adjusted")

    def test_a_construction_does_not_override_a_law(self):
        from pie import categories
        # matched_by == "laws" never reaches the construction branch.
        row = categories.verdict(
            recorded=True, matched_by="laws", pie_linked=True, from_pie=True,
            construction={"note": "*a + *b", "exact": True,
                          "explained": True, "stated": True})
        self.assertEqual(row["category"], "full")
        self.assertNotIn("construction", row["reason"])


class IncompleteTimeline(unittest.TestCase):
    """A recorded rung that is not a word of its stage cannot be green.

    Proto-Indo-Iranian *HwáHyati is reproduced character for character from the
    PIE form its record names (*h₁wéh₂-ye-ti), and the page printed "fully
    explained" while the PIE rung under it said "no entry for this word": the
    chain was complete by the laws and incomplete in the record
    (2026-11-13).  The band now asks the same question the rung asks,
    through one helper (``service.unrecorded_ancestry``), so a green band and a
    missing rung cannot appear on one page.
    """

    def test_a_recorded_ancestor_no_entry_heads_is_reported(self):
        # *mitrás is "from Proto-Indo-European *mi-tró-s" and the PIE glossary
        # has no such word (the record names it and never says how it was made,
        # so `tools/add_pie_ancestors.py` refuses to file one).
        entry = service._lemma_entry("iir-pro", "mitrás")
        holes = service.unrecorded_ancestry(entry, ["ine-pro", "iir-pro"])
        self.assertEqual([(h["stage"], h["form"]) for h in holes],
                         [("ine-pro", "mi-tró-s")])

    def test_the_page_that_reported_it_is_yellow_and_says_why(self):
        page = service.word("iir-pro", "mitrás")["category"]
        self.assertEqual(page["category"], "partial")
        self.assertEqual(page["reason"],
                         "no entry for Proto-Indo-European *mi-tró-s")

    def test_a_root_and_a_bound_form_are_not_steps(self):
        # *h₁weh₂- is a relation, not a rung; an entry with only that row has
        # no hole to report even though the *-ye-ti word is a different word.
        entry = service._lemma_entry("iir-pro", "HwáHyati")
        holes = service.unrecorded_ancestry(entry, ["ine-pro", "iir-pro"])
        self.assertEqual(holes, [])

    def test_the_band_and_the_rung_agree_across_the_stage(self):
        # The rule is general, in the direction that matters: a rung that
        # prints "no entry for this word" never stands over a green band, and a
        # green band means no recorded ancestor is missing.  (The converse does
        # not hold — a word can be yellow for a hole the ladder does not print,
        # or for a last mile the laws miss.)
        for word in ("HwáHyati", "dʰárati", "Hr̥tás", "stáHnam", "Háćru",
                     "nagnás", "smárati", "mitrás", "Hásuras"):
            page = service.word("iir-pro", word)
            band = page["category"]["category"]
            rows = [row for row in page["hierarchy"]["levels"]
                    if (row.get("recorded") or {}).get("known") is False]
            if rows:
                self.assertEqual(band, "partial", f"{word}: {rows[0]['form']}")
            if band == "full":
                entry = service._lemma_entry("iir-pro", word)
                self.assertEqual(
                    service.unrecorded_ancestry(entry, ["ine-pro", "iir-pro"]),
                    [], word)

    def test_the_stressless_spelling_of_a_headword_is_the_same_word(self):
        # A record often quotes a reconstruction without the accent the
        # dictionary heads (*h₂m̥bʰi for h₂m̥bʰí).  That is notation, not a
        # missing word.
        self.assertEqual(service._lemma_entry("ine-pro", "h₂m̥bʰi")["word"], "h₂m̥bʰí")
        self.assertEqual(service._lemma_entry("ine-pro", "h₂eḱru")["word"], "h₂éḱru")

    def test_a_hole_above_an_ancestor_is_the_same_hole(self):
        # Sanskrit तृण inherits Proto-Indo-Iranian *tŕ̥nam, which the glossary
        # holds, and *that* entry names a PIE word the PIE glossary does not
        # (*tŕ̥nom).  The daughter's page draws the ancestor's timeline, so the
        # missing word is visible one step higher and cannot be green either.
        entry = service._lemma_entry("sa", "तृण")
        holes = service.unrecorded_ancestry(
            entry, ["ine-pro", "iir-pro", "inc-pro", "sa"])
        self.assertEqual([(h["stage"], h["form"]) for h in holes],
                         [("ine-pro", "tŕ̥nom")])
        self.assertEqual(holes[0]["via"], "tŕ̥nam")

    def test_a_cut_etymology_row_is_not_a_word(self):
        # One entry's extraction left the join ("+") in its ancestry row.
        # Punctuation is not a form, so it is never reported as a hole.
        entry = service._lemma_entry("gem-pro", "*sagō")
        forms = [h["form"] for h in
                 service.unrecorded_ancestry(entry, ["ine-pro", "gem-pro"])]
        self.assertNotIn("+", forms)


class GradedComposition(unittest.TestCase):
    """A composition takes the grade its suffix asks for.

    A record cites the root under the e-grade it is listed under and writes the
    word in the grade the suffix makes: "*bʰn̥dʰtós, from *bʰendʰ- + *-tós".
    Read as a plain concatenation the row spelled *bʰendʰtós, so the entry said
    its own construction "does not spell the word" (2026-11-13).
    """

    def entry(self, word):
        return service._lemma_entry("ine-pro", word)

    def test_a_zero_grade_suffix_gets_the_root_it_asks_for(self):
        path = service.construction_path(self.entry("bʰn̥dʰtós"), "ine-pro")
        self.assertTrue(path["exact"])
        self.assertTrue(path["explained"])
        self.assertEqual(path["form"], "bʰn̥dʰtós")
        self.assertEqual(path["grade"]["grade"], "zero")

    def test_an_o_grade_suffix_gets_the_root_it_asks_for(self):
        path = service.construction_path(self.entry("bʰóh₂mos"), "ine-pro")
        self.assertTrue(path["exact"])
        self.assertEqual(path["grade"]["grade"], "o")

    def test_the_diphthong_zero_grade_is_its_second_element(self):
        # *leykʷ- → *likʷ-, *wekʷ- → *ukʷ-, *dewk- → *duk-; the old reading
        # dropped the vowel and kept a glide that is not a syllable.
        for stem, made in (("leykʷ-", "likʷ"), ("wekʷ-", "ukʷ"),
                           ("dewk-", "duk"), ("peys-", "pis"),
                           ("bʰeyh₂-", "bʰih₂")):
            self.assertEqual(service._formation_grade(stem, "-tós", "ine-pro")[0],
                             made, stem)

    def test_an_undocumented_suffix_still_gets_no_grade(self):
        # *-ró- is not a documented grade type, so nothing is guessed.
        self.assertEqual(service._formation_grade("ḱweyt-", "-rós", "ine-pro")[0],
                         "ḱweyt-")

    def test_the_word_the_record_names_is_an_entry_again(self):
        # *ukʷ-tó-s is the PIE word Proto-Indo-Iranian *uktás inherits.
        page = service.word("iir-pro", "uktás")
        self.assertEqual(page["category"]["category"], "full")
        self.assertIsNotNone(self.entry("ukʷtós"))


class NamedAncestorEntry(unittest.TestCase):
    """The PIE form a Proto-Indo-Iranian record names is an entry of its own.

    *HwáHyati's record says "From Proto-Indo-European *h₁wéh₂-ye-ti, from
    *h₁weh₂-", so the PIE word is the root plus a present suffix — and the PIE
    page has to show that construction, not only the word.
    """

    def test_the_entry_exists_with_the_sense_its_records_quote(self):
        page = service.word("ine-pro", "h₁wéh₂yeti")
        self.assertIsNotNone(page)
        self.assertEqual(page["gloss"], ["to become empty, die out"])
        self.assertEqual(page["pos"], "verb")

    def test_its_timeline_states_the_suffix_formation(self):
        level = service.word("ine-pro", "h₁wéh₂yeti")["hierarchy"]["levels"][0]
        builds = level["builds"]
        self.assertEqual(len(builds), 1)
        self.assertEqual(builds[0]["kind"], "suffix")
        self.assertEqual([p["form"] for p in builds[0]["pieces"]],
                         ["*h₁weh₂-", "*-yeti"])
        # A bound piece is a registered morpheme, not a word with an origin.
        self.assertTrue(builds[0]["pieces"][1]["bound"])
        self.assertTrue(builds[0]["pieces"][1]["known"])

    def test_the_construction_spells_the_word_and_stands_on_pie(self):
        entry = service._lemma_entry("ine-pro", "h₁wéh₂yeti")
        path = service.construction_path(entry, "ine-pro")
        self.assertTrue(path["exact"])
        self.assertTrue(path["explained"])
        self.assertEqual([p["origin"] for p in path["pieces"]],
                         ["PIE *h₁weh₂", "registered morpheme"])

    def test_the_descendants_record_the_same_word(self):
        # The form is named by three records: Proto-Indo-Iranian *HwáHyati,
        # Greek ἐάω and Lithuanian pavojus (through *pavóti).
        self.assertEqual(service._lemma_entry("ine-pro", "h₁wéh₂-ye-ti")["word"],
                         "h₁wéh₂yeti")
        entry = service._lemma_entry("iir-pro", "HwáHyati")
        self.assertEqual(
            service.unrecorded_ancestry(entry, ["ine-pro", "iir-pro"]), [])
        self.assertEqual(service.word("iir-pro", "HwáHyati")["category"]["category"],
                         "full")
