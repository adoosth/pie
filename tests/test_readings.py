"""Every word written in another script is shown with a reading (2026-11-08).

The rule the pages promise: an unreadable script is never printed bare.  A
reading comes from the dictionary when it records one, from the glossary's own
etymology sentences when they read the form, and otherwise from the script's
own values — and only that last kind is automatic, printed in its own colour.

These tests pin the whole corpus, not a sample: `test_no_scripted_headword_is_
shown_bare` walks every entry of every glossary.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import readings, script, service, translit  # noqa: E402

WEB = ROOT / "src" / "pie" / "app" / "web"


class TestNoScriptedWordIsBare(unittest.TestCase):
    def test_no_scripted_headword_is_shown_bare(self):
        # The promise is about *scripts*: a cuneiform, Pahlavi or Greek word is
        # never printed without a reading.  A headword written in Latin letters
        # (Book Pahlavi lwc) is readable letter by letter, so it may stand bare
        # when the record states no reading — but then the page must not say
        # one is shown either (2026-11-11).
        bare: list[str] = []
        claimed: list[str] = []
        for (lang, word) in service.word_index():
            meta = service._form_meta(lang, word)
            has = bool(meta["reading"] or meta["ipa"])
            if meta["show_reading"] and not has:
                claimed.append(f"{lang}/{word}")
            if translit.is_scripted(word) and not has:
                bare.append(f"{lang}/{word}")
        self.assertEqual(bare, [], f"{len(bare)} scripted forms would print bare")
        self.assertEqual(claimed, [], f"{len(claimed)} forms promise a reading")

    def test_every_word_page_carries_a_reading(self):
        for lang, word in (("peo", "𐎱𐎠𐎼𐎿"), ("peo", "𐎠𐎼𐎫𐎧𐏁𐏂𐎠"),
                           ("got", "𐌻𐌹𐌿𐌸𐍃"), ("ave", "𐬀𐬞"),
                           ("grc", "Πέρσης"), ("fa", "هفته"),
                           ("hit", "𒄀𒈠𒀭"), ("sa", "पशु")):
            page = service.word(lang, word)
            self.assertIsNotNone(page, f"{lang}/{word} has no page")
            self.assertTrue(page["show_reading"])
            self.assertTrue(page["reading"] or page["ipa"],
                            f"{lang}/{word} would print without a reading")


class TestWhereAReadingComesFrom(unittest.TestCase):
    def test_a_recorded_reading_is_printed_as_recorded(self):
        # 𐎠𐎡𐎫𐎡𐎹 carries its own romanisation in the glossary.
        meta = service._form_meta("peo", "𐎠𐎡𐎫𐎡𐎹")
        self.assertEqual(meta["reading"], "aitiy")
        self.assertFalse(meta["reading_auto"])
        self.assertNotEqual(meta["reading_how"], "signs")

    def test_a_reading_the_glossary_quotes_beside_the_form_is_recorded(self):
        # The Old Persian entry has no romanisation of its own, but the
        # glossary's etymology for Persian *Persida* reads 𐎱𐎠𐎼𐎿 as
        # "p-a-r-s /⁠pārsa⁠/" — a dictionary's reading, not ours.
        # Since 2026-11-12 the lemma itself states its reading (Pārsaʰ, the
        # transliteration Wiktionary gives 𐎱𐎠𐎼𐎿), and a recorded reading
        # outranks a quoted one — the note naming where it was read is no
        # longer needed, and the reading is still printed plainly.
        meta = service._form_meta("peo", "𐎱𐎠𐎼𐎿")
        self.assertEqual(meta["reading"], "Pārsaʰ")
        self.assertEqual(meta["reading_how"], "recorded")
        self.assertFalse(meta["reading_auto"])

    def test_an_automatic_reading_says_it_is_automatic(self):
        meta = service._form_meta("got", "𐌻𐌹𐌿𐌸𐍃")
        self.assertEqual(meta["reading"], "liuþs")
        self.assertTrue(meta["reading_auto"])
        self.assertEqual(meta["reading_how"], "letters")
        self.assertIn("No reading recorded", meta["reading_note"])

    def test_old_persian_without_a_reading_is_read_sign_by_sign(self):
        # 𐏀𐎴 had no romanisation when this test was written; Wiktionary now
        # states one (zanaʰ), so the rule is shown on a headword that still has
        # none.
        meta = service._form_meta("peo", "𐎱𐎢𐎫𐎠𐎹")
        # The automatic reading is the signs' own transliteration, and a
        # consonant sign's inherent -a is not printed (2026-11-13).
        self.assertEqual(meta["reading"], "p-u-t-a-y")
        self.assertTrue(meta["reading_auto"])
        self.assertEqual(meta["reading_how"], "signs")
        self.assertEqual(service._form_meta("peo", "𐏀𐎴")["reading"], "zanaʰ")

    def test_a_reading_the_record_states_wins_over_the_signs(self):
        # Wiktionary's Middle Persian lwc says its Old Persian ancestor 𐎼𐎢𐎨 is
        # read *raučah-* ({{inh|pal|peo|...|ts=raučah-}}).  That is a record,
        # so it is printed plainly and the sign string r-a-u-ca is not shown
        # (2026-11-11).
        meta = service._form_meta("peo", "𐎼𐎢𐎨")
        self.assertEqual(meta["reading"], "raučah")
        self.assertFalse(meta["reading_auto"])
        self.assertEqual(meta["reading_how"], "quoted")

    def test_a_latin_romanisation_is_not_asked_for_a_second_one(self):
        # Tocharian B ṣar and Proto-Slavic -akъ are written in Latin letters:
        # they *are* romanisations, so a reading beside them would be noise.
        self.assertFalse(service.show_reading("txb", "ṣar"))
        self.assertFalse(service.show_reading("sla-pro", "-akъ"))
        self.assertTrue(service.show_reading("ave", "𐬀𐬞"))


class TestTheTransliterations(unittest.TestCase):
    def test_a_polytonic_greek_word_keeps_its_accents(self):
        self.assertEqual(translit.transliterate("Πέρσης")["reading"], "Pérsēs")
        self.assertEqual(translit.transliterate("πυθμήν")["reading"], "pýthmēn")

    def test_a_devanagari_word_keeps_its_inherent_vowels(self):
        self.assertEqual(translit.transliterate("पशु")["reading"], "paśu")
        self.assertEqual(translit.transliterate("शक्ति")["reading"], "śakti")

    def test_an_abjad_writes_no_vowels_it_does_not_have(self):
        # Persian writes consonants; the vowels a reader says are not invented.
        self.assertEqual(translit.transliterate("هفته")["reading"], "hfth")

    def test_cuneiform_is_read_sign_by_sign(self):
        self.assertEqual(translit.transliterate("𒄀𒈠𒀭")["reading"],
                         "gi-ma-an")

    def test_the_old_persian_syllabary_prints_what_the_signs_say(self):
        # p-a-r-s: the sign 𐎠 is a written vowel and stays; the inherent -a
        # of 𐎱 and 𐎼 is not evidence and is not printed (2026-11-13).
        self.assertEqual(script.transliterate("peo", "𐎱𐎠𐎼𐎿"), "p-a-r-s")

    def test_an_unknown_character_is_kept_not_invented(self):
        out = translit.transliterate("𐎺x")
        self.assertEqual(out["reading"], "")


class TestTheQuotedReadingsFile(unittest.TestCase):
    def test_the_file_is_well_formed(self):
        rows = json.loads(readings.READINGS_PATH.read_text(encoding="utf-8"))
        self.assertTrue(rows)
        for form, row in rows.items():
            lang = row.get("lang") or ""
            # A form in the table is written in a script, or in the letters of
            # one: Book Pahlavi lwc is the signs l-w-c, not a romanisation
            # (2026-11-11).
            self.assertTrue(translit.is_scripted(form) or script.writes(lang, form),
                            f"{form} ({lang}) is plain Latin, not a spelling")
            self.assertTrue(row.get("reading"), form)
            self.assertTrue(row.get("source"), form)

    def test_every_quoted_form_is_a_spelling_the_pages_meet(self):
        # The file exists for forms a page would otherwise show unread: each is
        # either a headword the glossary cannot read, or a spelling some entry's
        # ancestry names (the Old Persian 𐎼𐎢𐎨 of Middle Persian lwc has no
        # entry of its own).
        index = service.word_index()
        named = {(stage, word) for entries in index.values() for entry in entries
                 for stage, word, _rel in entry.get("anc") or () if word}
        for form, row in readings.quoted().items():
            lang = row.get("lang") or ""
            heads = index.get((lang, form)) or []
            self.assertTrue(heads or (lang, form) in named, f"{lang}/{form}")
            # Only the first entry under a spelling is displayed
            # (``readings_for`` reads ``entries[0]``), so only that one decides
            # whether the form would be printed bare.
            self.assertFalse(heads and (heads[0].get("translit") or heads[0].get("ipa")),
                             f"{lang}/{form}")


class TestTheFrontEndShowsIt(unittest.TestCase):
    def test_the_page_has_an_automatic_colour(self):
        css = (WEB / "style.css").read_text(encoding="utf-8")
        self.assertIn("--auto-reading", css)
        self.assertIn(".reading.auto", css)

    def test_the_reading_renderer_marks_automatic_readings(self):
        js = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertIn("reading_auto", js)
        # The class is built from the flag now, because the same renderer also
        # prints the sign layer beside the reading (2026-11-13).
        self.assertIn('class="reading${o.auto ? " auto" : ""}"', js)

    def test_the_reading_renderer_never_prints_ipa_on_a_rung(self):
        # IPA is optional and belongs on the word's own page: a timeline shows
        # the romanisation, never a phonetic transcription (2026-11-13).
        js = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("ipa: rec.ipa", js)
        self.assertNotIn("ipa: r.ipa", js)
        self.assertIn('class="reading signs"', js)


if __name__ == "__main__":
    unittest.main()
