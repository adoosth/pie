"""Every sign's sounds must be in the alphabet a reading is reduced to.

A reading is split into base letters by ``script._base_letters``: length,
stress, aspiration and the superscript marks are notation and the letter
survives alone.  The matcher then asks whether a sign can stand for that base
letter, comparing it against the sign's ``sounds``.  If a table writes a sound
the matcher can never produce (``š`` where every reading gives ``s``), that
sign can never match anything, and nothing says so: Middle Persian's script
column sat at 1 for that reason while its transliteration table listed
``š ḥ č ẕ`` (2026-11-09).

The convention ``data/script/fa.yaml`` states is the one checked here: a
sound is a base letter, or a base letter with a length mark (which the loader
folds).  A table may print whatever it likes in ``value``; ``sounds`` is the
alphabet the reader writes.
"""
import pathlib
import unittest

from pie import data
from pie.script import _LENGTH_FOLD, _base_letters

SCRIPT_DIR = data.DATA / "script"


def folded(sound: str) -> bool:
    letters = _base_letters(sound)
    if len(letters) != 1:
        return False
    base = letters[0][0]
    if sound == base:
        return True
    return len(sound) == 1 and _LENGTH_FOLD.get(sound) == base


class SoundAlphabetTest(unittest.TestCase):
    def test_every_sound_is_reachable_from_a_reading(self):
        bad = []
        for path in sorted(SCRIPT_DIR.glob("*.yaml")):
            raw = data._load_yaml(path)
            rows = (raw.get("signs") or []) + (raw.get("logograms") or [])
            for row in rows:
                for sound in row.get("sounds") or []:
                    if sound and not folded(sound):
                        bad.append((path.name, row.get("char"), sound,
                                    _base_letters(sound)))
        self.assertEqual(bad, [], "a sound the matcher can never produce: %r" % bad)

    def test_the_reading_keeps_a_semitic_letter(self):
        # ʾ and ʿ are letters written with a modifier glyph, not notation:
        # Middle Persian ʾp̄ʾt' and Arabic hamza seats both need them.
        self.assertEqual([x for x, _v in _base_letters("ʾp̄ʾt'")],
                         ["ʾ", "p", "ʾ", "t"])
        self.assertEqual([x for x, _v in _base_letters("saʿd")], ["s", "a", "ʿ", "d"])

    def test_aspiration_is_written_as_the_h_it_is(self):
        # The service's convention: ʰ becomes h rather than vanishing, so a
        # sign for /h/ is not silently left unfilled.
        self.assertEqual([x for x, _v in _base_letters("kʰan")], ["k", "h", "a", "n"])


if __name__ == "__main__":
    unittest.main()
