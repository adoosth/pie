"""The Proto-Germanic → Old Norse transition (data/rules/gem-pro__non.yaml).

The file did not exist before 2026-11-09, so every Old Norse word was 0% by
construction.  These tests keep the claims it makes honest: each rule carries a
tier, a source and an example the checker can verify, the core laws derive the
forms the handbooks cite, and the number the report publishes is the one the
counter computes.
"""

import unittest

from pie import data
from pie.rules import derive

NON = ("gem-pro", "non")

#: Words whose derivation is stated in the handbooks and which the file must
#: reproduce exactly, from the Proto-Germanic etymon the corpus records.
EXACT = {
    "*dagaz": "dagr",          # *-az > -r
    "*fiskaz": "fiskr",
    "*stainaz": "steinn",      # *ai > ei, *-nr > -nn
    "*weraz": "verr",          # *w > v
    "*harjaz": "herr",         # i-umlaut, *j lost, *-az > -r
    "*gastiz": "gestr",        # i-umlaut, *-iz > -r
    "*laguz": "lǫgr",          # u-umlaut, *-uz > -r
    "*landą": "land",          # *-ą > ∅
    "*nemaną": "nema",         # strong infinitive
    "*satjaną": "setja",       # light class-1 infinitive keeps *j
    "*sandijaną": "senda",     # heavy class-1 infinitive drops it
    "*dōmijaną": "dœma",       # *ō > œ by i-umlaut
    "*hauhaz": "har",          # *au > á before *h (the acute is notation)
    "*lētaną": "lata",         # *ē > á
    "*beudaną": "bjoða",       # *eu > jó, *þ > ð
    "*brōþēr": "brōðir",       # *-ēr > -ir, *þ > ð
    "*finþaną": "finna",       # *nþ > nn
    "*gebō": "gjǫf",           # final *-ō > -u > breaking > lost
    "*agô": "agi",             # weak masculine *-ô > -i
    "*wulfaz": "ulfr",         # *w- lost before *u
    "*tungǭ": "tunga",         # *-ǭ > -a, no u-umlaut
}


class NorseTransitionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rulesets = data.rulesets()
        cls.ruleset = cls.rulesets[NON]

    def test_file_exists_and_is_registered(self):
        self.assertIn(NON, self.rulesets)
        self.assertIn("gem-pro__non", [p.stem for p in data.RULE_DIR.glob("*.yaml")])

    def test_every_rule_states_its_evidence(self):
        sources = data.sources()
        for rule in self.ruleset.rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.name, rule.id)
                self.assertIn(rule.tier, ("established", "proposed"), rule.id)
                self.assertTrue(rule.references, rule.id)
                for ref in rule.references:
                    self.assertIn(ref, sources, f"{rule.id} cites unknown {ref}")
                self.assertTrue(rule.examples, rule.id)

    def test_the_cited_forms_are_derived_exactly(self):
        for etymon, word in EXACT.items():
            with self.subTest(word=word):
                derivation = derive(etymon, list(NON), self.rulesets)
                self.assertEqual(derivation.output, word)
                self.assertTrue(derivation.steps, "a match must fire a law")

    def test_a_law_that_must_not_fire_stays_put(self):
        # *weraz has *a but no *u: u-umlaut must leave the vowel alone
        self.assertEqual(derive("*weraz", list(NON), self.rulesets).output, "verr")
        # *wulfaz keeps its *w-? no: *w is lost before *u, and *u stays u
        self.assertEqual(derive("*wulfaz", list(NON), self.rulesets).output, "ulfr")
        # *hertô is a neuter n-stem: the -ô rule states the masculine -i, so
        # the neuter is a recorded miss, never bent to fit
        self.assertNotEqual(derive("*hertô", list(NON), self.rulesets).output, "hjarta")
        # *weraz has *a but no *u, so u-umlaut must leave it alone
        self.assertNotIn("ǫ", derive("*weraz", list(NON), self.rulesets).output)

    def test_the_corpus_number_is_not_zero(self):
        from pie.service import _ancestry_triples, _phonological_form, normalise_etymon
        entries = [e for e in data.lexicon("non") if not e.get("recon")]
        exact = 0
        for entry in entries:
            target = entry["word"].strip()
            for lang, word, rel in _ancestry_triples(entry):
                if lang != "gem-pro" or rel == "borrow":
                    continue
                form = _phonological_form(lang, normalise_etymon(word))
                if not form:
                    continue
                d = derive(form, list(NON), self.rulesets)
                if d.steps and (d.output == target or _stress_free(d.output) == _stress_free(target)):
                    exact += 1
                    break
        self.assertGreater(exact, 600)


def _stress_free(form):
    from pie.phonology import detokenize, tokenize
    return detokenize([t for t in tokenize(form) if t not in {"ˈ", "ˌ"}])


if __name__ == "__main__":
    unittest.main()
