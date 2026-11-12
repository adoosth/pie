"""Old Church Slavonic from Proto-Slavic: the last mile, its letters and its edge.

The chain ``ine-pro → ine-bsl-pro → sla-pro → chu`` had no ``sla-pro → chu``
rule file, so all 1,797 tested entries were misses by construction.  Two
artefacts fix that — a script table (Cyrillic and Glagolitic → transliteration,
``data/script/chu.yaml``) and a rule file of ten historical laws and their
notation (``data/rules/sla-pro__chu.yaml``) — and these tests pin both:
every law's tier and citation, the examples ``check-rules`` verifies, the
script's signs, the readings it accepts, and the words a law must **not**
touch.  The corpus numbers are a floor, not a target: the Proto-Slavic
transition above is another worker's file and may move.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from pie import data, script                       # noqa: E402
from pie.rules import apply_ruleset, derive        # noqa: E402
from pie.phonology import detokenize, tokenize     # noqa: E402
from coverage import ancestor_starts               # noqa: E402

SRC, DST = "sla-pro", "chu"


def _ruleset():
    return data.rulesets()[(SRC, DST)]


def _run(form: str) -> str:
    out, _steps = apply_ruleset(form, _ruleset())
    return out


def _one(rule_id: str, form: str) -> str:
    """Apply one rule of the file, alone, exactly as check-rules does."""
    rule = next(r for r in _ruleset().rules if r.id == rule_id)
    out, _steps = apply_ruleset(
        form, type("RS", (), {"rules": [rule], "target_stage": ""})(), enabled=[rule.id])
    return out


class LawSet(unittest.TestCase):
    def test_every_law_states_a_tier_and_a_known_source(self):
        known = set(data.sources())
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.tier, {"established", "proposed", "orthographic"})
                self.assertTrue(rule.references, "a law without a source is a guess")
                for ref in rule.references:
                    self.assertIn(ref, known)

    def test_every_law_has_a_verified_example(self):
        for rule in _ruleset().rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.examples)
                for ex in rule.examples:
                    self.assertEqual(_one(rule.id, ex["in"]), detokenize(tokenize(ex["out"])))

    def test_the_transition_exists_and_is_not_empty(self):
        self.assertIn((SRC, DST), data.rulesets())
        self.assertGreaterEqual(len(_ruleset().rules), 15)

    def test_the_notation_rules_carry_the_orthographic_tier(self):
        for rid in ("soft_jer_transliteration", "hard_jer_transliteration",
                    "stress_token_dropped", "accent_grave_a"):
            rule = next(r for r in _ruleset().rules if r.id == rid)
            self.assertEqual(rule.tier, "orthographic", rid)

    def test_the_laws_that_matter_are_established(self):
        ids = {r.id: r.tier for r in _ruleset().rules}
        for rid in ("liquid_or_to_ra", "liquid_er_to_rě", "dl_to_l",
                    "t_palatal_to_sht", "d_palatal_to_zhd", "initial_jer_i",
                    "zt_to_st", "kv_to_cv"):
            self.assertEqual(ids[rid], "established", rid)
        # The prothesis is narrower than the grammars' statement: marked so.
        self.assertEqual(ids["prothesis_e"], "proposed")


class ScriptTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = script.table("chu")
        cls.words = {e["word"] for e in data.lexicon("chu")}

    def test_the_table_is_not_empty_and_has_the_slavic_letters(self):
        self.assertGreater(len(self.table), 40)
        for char in "ѣѫѧѩѭъьыщжчшцѹїй":
            if char in self.words:
                self.assertIn(char, self.table, char)

    def test_every_letter_a_headword_writes_is_in_the_table(self):
        # The table must not leave a recorded letter unread: an unknown
        # character makes the whole word a miss (script.signs returns None).
        unknown = sorted({c for w in self.words for c in w
                          if c.isalpha() and c not in self.table})
        self.assertEqual(unknown, [])

    def test_the_cyrillic_letters_the_corpus_uses_are_all_exercised(self):
        cyrillic = [c for c in self.table if "\u0400" <= c <= "\u04ff"
                    and c.islower()]
        unused = [c for c in cyrillic if not any(c in w for w in self.words)]
        # й ы я ѱ are real letters of the alphabet that this glossary happens
        # not to write; every other Cyrillic sign is witnessed by a headword.
        self.assertEqual(sorted(unused), sorted(["й", "ы", "я", "ѱ"]))

    def test_the_conventions_are_declared(self):
        ids = " ".join(row["id"] for row in script.conventions("chu"))
        for wanted in ("one_letter_one_segment", "iotified_signs", "yers_are_vowels",
                       "digraph_ou", "diacritics_folded"):
            self.assertIn(wanted, ids)

    def test_the_letter_values_are_the_slavicist_transliteration(self):
        self.assertEqual(self.table["ѣ"]["value"], "ě")
        self.assertEqual(self.table["ѫ"]["value"], "ǫ")
        self.assertEqual(self.table["ѧ"]["value"], "ę")
        self.assertEqual(self.table["ы"]["value"], "y")
        self.assertEqual(self.table["щ"]["value"], "št")
        self.assertEqual(self.table["ь"]["value"], "ĭ")
        self.assertEqual(self.table["ъ"]["value"], "ŭ")


class Reading(unittest.TestCase):
    def test_an_alphabetic_word_is_read_letter_by_letter(self):
        for reading, word in [("voda", "вода"), ("noga", "нога"), ("baba", "баба"),
                              ("mati", "мати"), ("slava", "слава"),
                              ("gradŭ", "градъ"), ("kostĭ", "кость"),
                              ("mǫžĭ", "мѫжь"), ("drěvo", "дрѣво"),
                              ("rǫka", "рѫка"), ("zemja", "земꙗ")]:
            with self.subTest(word=word):
                self.assertTrue(script.match(DST, reading, word)["ok"], word)

    def test_a_written_vowel_cannot_be_dropped(self):
        # вода writes four letters; a reading with three does not fit.
        self.assertFalse(script.match(DST, "vda", "вода")["ok"])
        self.assertFalse(script.match(DST, "voda", "вод")["ok"])

    def test_a_wrong_vowel_of_the_same_letter_is_rejected(self):
        # о is /o/: a reading with a is not a reading of нога.
        self.assertFalse(script.match(DST, "naga", "нога")["ok"])

    def test_a_consonant_the_letters_lack_is_not_forgiven(self):
        self.assertFalse(script.match(DST, "nogat", "нога")["ok"])
        self.assertFalse(script.match(DST, "nga", "нога")["ok"])

    def test_the_yers_are_letters_of_the_reading(self):
        self.assertTrue(script.match(DST, "konĭ", "конь")["ok"])
        self.assertFalse(script.match(DST, "kon", "конь")["ok"])

    def test_an_iotified_letter_writes_j_and_its_vowel(self):
        self.assertTrue(script.match(DST, "językŭ", "ѩзꙑкъ")["ok"])
        self.assertTrue(script.match(DST, "moja", "моꙗ")["ok"])
        self.assertFalse(script.match(DST, "moa", "моꙗ")["ok"])

    def test_a_two_consonant_sign_spends_both_letters(self):
        # щ writes št.  The aligner now lets one sign spend two letters of the
        # reading, so нощь reads noštĭ; before that every word with щ was a
        # miss no law could repair (2026-11-09, 71 headwords).
        self.assertTrue(script.match(DST, "noštĭ", "нощь")["ok"])
        # Both consonants, in order: a reading that drops one is no reading of
        # the sign.
        self.assertFalse(script.match(DST, "noš", "нощь")["ok"])
        self.assertFalse(script.match(DST, "noštĭa", "нощь")["ok"])


class Laws(unittest.TestCase):
    def test_metathesis(self):
        self.assertEqual(_run("orbota"), "rabota")
        self.assertEqual(_run("dervo"), "drěvo")
        self.assertEqual(_run("zolto"), "zlato")
        self.assertEqual(_run("melko"), "mlěko")

    def test_metathesis_does_not_fire_without_a_following_consonant(self):
        # *gora keeps its vowel and its liquid: no metathesis before a vowel.
        self.assertEqual(_run("gora"), "gora")
        self.assertEqual(_run("morě"), "morě")

    def test_dl_is_simplified_only_where_it_is_original(self):
        self.assertEqual(_run("modlitva"), "molitva")
        self.assertEqual(_run("pravidlo"), "pravilo")
        # *dolnь > dlanь: the dl visible after metathesis is not simplified.
        self.assertEqual(_run("dolnь"), "dlanĭ")
        self.assertEqual(_run("dъlgъ"), "dlŭgŭ")

    def test_palatal_clusters(self):
        self.assertEqual(_run("noťь"), "noštĭ")
        self.assertEqual(_run("voďь"), "voždĭ")
        self.assertEqual(_run("ešče"), "ešte")
        self.assertEqual(_run("moře"), "more")

    def test_yers_are_transliterated_last(self):
        self.assertEqual(_run("kostь"), "kostĭ")
        self.assertEqual(_run("gradъ"), "gradŭ")
        # The laws above the transliteration still see the letters ъ and ь.
        self.assertEqual(_run("sьrdьce"), "srĭdĭce")

    def test_prothesis_is_narrow_and_stated(self):
        self.assertEqual(_run("estь"), "jestĭ")
        self.assertEqual(_run("ezero"), "jezero")
        # единъ and еще keep their e-; the law must not touch them.
        self.assertEqual(_run("edinъ"), "edinŭ")
        self.assertEqual(_run("ešče"), "ešte")

    def test_initial_j(self):
        self.assertEqual(_run("jьzъ"), "izŭ")
        self.assertEqual(_run("jinъ"), "inŭ")
        # *jazъ keeps its j (азъ is the exception, not the rule).
        self.assertEqual(_run("jazъ"), "jazŭ")

    def test_kv_and_zt(self):
        self.assertEqual(_run("květъ"), "cvětŭ")
        self.assertEqual(_run("kvasъ"), "kvasŭ")
        self.assertEqual(_run("vezti"), "vesti")

    def test_soft_jer_is_not_hardened(self):
        # The measured ь→ъ law lost 81 words (влькъ, врьхъ, дльгъ): it is not a
        # law of this corpus and no rule in the file may do it.
        self.assertEqual(_run("vьlkъ"), "vlĭkŭ")
        self.assertEqual(_run("prьstъ"), "prĭstŭ")
        self.assertEqual(_run("trьnъ"), "trĭnŭ")


class Corpus(unittest.TestCase):
    def test_the_script_layer_carries_a_floor_of_words(self):
        explained = scripted = 0
        rs = data.rulesets()
        chain = data.derivation_chain(DST)
        for entry in data.lexicon(DST):
            word = str(entry.get("word") or "").strip()
            if not word or entry.get("recon"):
                continue
            if not ancestor_starts(entry, chain):
                continue
            for stage, form in ancestor_starts(entry, chain):
                d = derive(form, chain[chain.index(stage):], rs)
                if d.skipped:
                    continue
                if d.steps and script.match(DST, d.output, word) and \
                        script.match(DST, d.output, word)["ok"]:
                    scripted += 1
                    explained += 1
                    break
                if not d.steps and (d.output == word or d.output == (entry.get("translit") or "")):
                    explained += 1
                    break
        self.assertGreaterEqual(scripted, 850)
        self.assertGreaterEqual(explained, 1200)

    def test_a_known_word_end_to_end(self):
        entry = next(e for e in data.lexicon(DST) if e["word"] == "работа")
        form = [f for s, f in ancestor_starts(entry, data.derivation_chain(DST))
                if s == SRC][0]
        d = derive(form, [SRC, DST], data.rulesets())
        self.assertEqual(d.output, "rabota")
        self.assertTrue(script.match(DST, d.output, entry["word"])["ok"])


if __name__ == "__main__":
    unittest.main()
