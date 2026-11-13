"""A word is attested, recorded or proposed — and the page says which.

The three states are a claim about the word itself, not about its ancestry: an
attested word is one a text or a dictionary records, in the language's own
script or in the transcription the record gives it; a recorded word is a
reconstruction the literature proposes and prints with an asterisk; a proposed
word is this model's own guess, which nothing in the literature records
(2026-11-11; a transcription attests, 2026-11-13).
"""
import unittest

from pie import attestation


class Classification(unittest.TestCase):
    def test_a_text_writes_an_attested_word(self):
        entry = {"word": "𐎭𐎠𐎼𐎹𐎺𐎢𐏁", "lang": "peo"}
        self.assertEqual(attestation.classify(entry), "attested")

    def test_a_reconstruction_is_recorded(self):
        self.assertEqual(attestation.classify({"word": "madu", "recon": True}),
                         "recorded")

    def test_an_asterisk_alone_is_recorded(self):
        self.assertEqual(attestation.classify({"word": "*ph₂tḗr"}), "recorded")

    def test_a_proto_stage_is_recorded_as_a_whole(self):
        self.assertEqual(attestation.classify({"word": "ph₂tḗr"}, proto=True),
                         "recorded")

    def test_the_label_leaves_the_asterisk_to_the_word(self):
        """The word prints *madu, so the label must not say "(*)" as well.

        A reader saw `recorded (*)` beside a headword that already carried the
        asterisk and read it as a footnote; the mark on the word means one
        thing — no text spells it — and the label is just the word
        (admin, 2026-11-12).
        """
        for status in ("recorded", "proposed"):
            self.assertNotIn("(*)", attestation.LABELS[status], status)
        self.assertEqual(attestation.LABELS["recorded"], "recorded")
        self.assertEqual(attestation.LABELS["proposed"], "proposed")

    def test_a_transcription_is_an_attestation(self):
        """A record that gives the reading has recorded the word (2026-11-13)."""
        self.assertEqual(attestation.classify({"word": "garm"}, in_script=False),
                         "attested")
        self.assertEqual(attestation.written("garm", "attested"), "garm")
        # A transliteration is still a record's form, not a reconstruction.
        self.assertEqual(attestation.classify({"word": "lwc"}, in_script=False),
                         "attested")

    def test_a_reconstruction_stays_recorded_without_a_script(self):
        self.assertEqual(attestation.classify({"word": "madu", "recon": True},
                                              in_script=False), "recorded")

    def test_the_models_own_guess_is_proposed(self):
        self.assertEqual(attestation.classify({"word": "x", "proposal": True}),
                         "proposed")
        self.assertEqual(attestation.classify({"word": "x", "source": "pie"}),
                         "proposed")

    def test_a_proposal_is_never_attested(self):
        entry = {"word": "x", "recon": False, "proposal": True}
        self.assertEqual(attestation.classify(entry, in_script=True), "proposed")


class Spelling(unittest.TestCase):
    def test_a_recorded_word_is_printed_with_its_asterisk(self):
        self.assertEqual(attestation.written("madu", "recorded"), "*madu")
        self.assertEqual(attestation.written("*madu", "recorded"), "*madu")

    def test_an_attested_word_is_printed_as_the_script_writes_it(self):
        self.assertEqual(attestation.written("𐎠𐎡𐎫𐎡𐎹", "attested"),
                         "𐎠𐎡𐎫𐎡𐎹")


class Homographs(unittest.TestCase):
    def test_one_attested_entry_makes_the_spelling_attested(self):
        rows = [{"word": "ne", "recon": True}, {"word": "ne"}]
        self.assertEqual(attestation.for_word(rows), "attested")

    def test_all_entries_recorded_stays_recorded(self):
        rows = [{"word": "x", "recon": True}, {"word": "x", "recon": True}]
        self.assertEqual(attestation.for_word(rows), "recorded")

    def test_nothing_filed_is_non_existent(self):
        self.assertEqual(attestation.for_word([]), attestation.NON_EXISTENT)


class Pages(unittest.TestCase):
    def test_an_old_persian_attested_word_keeps_its_script(self):
        from pie import service
        word = "𐎭𐎠𐎼𐎹𐎺𐎢𐏁"
        page = service.word("peo", word)
        status = page["attestation"]
        self.assertEqual(status["status"], "attested")
        self.assertEqual(status["written"], word, "the headword is the cuneiform itself")

    def test_an_old_persian_reconstruction_says_recorded(self):
        from pie import service
        page = service.word("peo", "madu")
        status = page["attestation"]
        self.assertEqual(status["status"], "recorded")
        self.assertEqual(status["written"], "*madu")
        self.assertIn("asterisk", status["definition"])

    def test_a_word_no_glossary_holds_is_non_existent(self):
        from pie import service
        page = service.word("peo", "not-a-real-form", ghost=True)
        self.assertEqual(page["attestation"]["status"], "non-existent")

    def test_every_glossary_row_names_its_status(self):
        from pie import service
        rows = service.glossary("peo", limit=8)["rows"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["attestation"], attestation.STATUSES)
            if row["attestation"] == "recorded":
                self.assertTrue(row["written"].startswith("*"), row)

    def test_a_shared_spelling_carries_the_status_too(self):
        from pie import service
        page = service.word("fa", "آب")
        self.assertIn(page.get("attestation", {}).get("status"),
                      attestation.STATUSES)


class Transcribed(unittest.TestCase):
    """A record's transcription attests its word (admin, 2026-11-13).

    Middle Persian ``garm`` is MPCD's reading of the spellings ``glm``,
    ``g03lm`` …; the page says "attested" and says what the form above is
    (``attested_how``), and the spellings stay on the row.
    """

    def test_a_middle_persian_transcription_is_attested(self):
        from pie import service

        page = service.word("pal", "garm")
        self.assertEqual(page["attestation"]["status"], "attested")
        self.assertEqual(page["attested_how"], "transcription")
        self.assertFalse(page["attestation"]["written"].startswith("*"))

    def test_the_recorded_spellings_survive(self):
        from pie import data, service

        row = next(r for r in data.lexicon("pal") if r["word"] == "garm")
        self.assertEqual(row["translit"], "glm")
        self.assertEqual(row["translit_variants"][:2], ["g03lm", "g03lmtl"])
        shown = next(r for r in service.glossary("pal", limit=50,
                                                 band="all", q="garm")["rows"]
                     if r["word"] == "garm")
        self.assertEqual(shown["transcription"], "garm")
        self.assertEqual(shown["transliteration"], "glm · g03lm · g03lmtl")
        self.assertEqual(shown["attestation"], "attested")

    def test_a_middle_persian_word_in_pahlavi_is_attested(self):
        from pie import service

        word = "𐭫𐭥𐭰"
        self.assertTrue(service._in_native_script("pal", word))


if __name__ == "__main__":
    unittest.main()
