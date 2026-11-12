#!/usr/bin/env python3
"""Collect the readings the record states for Middle Persian spellings.

A Middle Persian word is written in Book Pahlavi, in the Manichaean script, or
in a transliteration of either, and the sound laws can only start from a form
that is a string of sounds.  The record states the reading in three places,
and this tool copies them into one table, never inventing one:

* **MacKenzie (1971), the dictionary's own headword line.**  The glossary built
  by ``tools/ingest_mackenzie.py`` keeps the bracket beside each reading
  (``abag [LWTE < A Iwt-h | M y ygt N (a) d]``): the first token is the
  spelling, the headword is the reading.  That is a recording, not a guess.
* **the glossary's own entry fields.**  Two entries carry the script form as
  the headword and the reading in ``translit`` (``𐫅𐫏𐫇`` / ``dēw``).
* **Wiktionary's Middle Persian pages** (shipped as an extraction in
  ``data/readings_pal_wiktionary.json``): every page states the entry's
  transcription in its head template (``{{head|pal|noun|tr=...|ts=...}}``) and
  usually repeats the other scripts' spellings of the same word with their own
  ``ts=`` in the alternative-forms list.

A pair is kept only when it is *consistent*: the reading's letters must be
spellable by the spelling's letters under the Pahlavi sound table
(``data/script/pal.yaml``) — every consonant of the reading is written by a
sign that can spell it, and no sign is left unexplained.  That check is what
throws out the ingest's OCR damage (the 2014 conversion reads aleph as ``y`` in
about a third of the brackets), because a garbled key cannot spell the reading
it is stored with.  What it cannot repair it refuses, and the report says how
many.

    python3 tools/build_pal_readings.py                    # rewrite the table
    python3 tools/build_pal_readings.py --check            # verify, write nothing
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data, script  # noqa: E402
from pie.service import normalise_etymon  # noqa: E402

OUT = data.DATA / "readings_pal.json"
WIKT = data.DATA / "readings_pal_wiktionary.json"

#: The letters of the Pahlavi transliteration, and the sounds each can spell.
#: The inventory is the Aramaic one; the polyphony is MacKenzie's usage (𐭥 is
#: w, r or ʿ; 𐭬 is m or q; kaph, pe and taw write the voiced stops too).
SOUNDS = {
    # h is heth: it writes /h/ and /x/ alike (MacKenzie spells xwadāy hwtʾy).
    "ʾ": set("ʾāa"), "b": {"b"}, "g": {"g"}, "d": {"d"}, "h": set("hx"),
    "w": set("bwōū"), "z": {"z"}, "ḥ": set("ḥhx"), "ṭ": {"ṭ", "t"},
    "y": set("yēī"), "k": {"k", "g"}, "l": set("lr"), "m": {"m"}, "n": {"n"},
    "s": {"s"}, "ʿ": {"ʿ"}, "p": set("pbf"), "c": set("cčjz"), "q": set("qxγ"),
    # The record writes the same sign two ways: the plain Latin c of a
    # transliteration (cʾlk') and the háček č of a transcription-style spelling
    # (wʾčʾl).  It is one Pahlavi sign (MacKenzie's ṣade/c), so its values are
    # the same either way (2026-11-09).
    "č": set("cčjz"), "ẖ": set("ḥhx"),
    "r": set("rl"), "š": {"š"}, "t": set("td"),
}
VOWELS = set("aeiouāēīōūǣə")

#: A MacKenzie bracket, reduced to the spelling that opens it: cut at the
#: Aramaic original (< A …), the other scripts (| M …, | P …) and the notes.
_SPELL = re.compile(r"^[^|<=(,]*")


def _letters(form: str) -> list[str]:
    return [c for c in (form or "").replace("\u2060", "").lower() if c.isalpha()]


def consistent(spelling: str, reading: str) -> bool:
    """Whether the reading can be what these spelling letters write.

    Each letter of the spelling writes one letter of the reading; the reading's
    short vowels may be unwritten, and a long-vowel letter (ʾ y w) may also
    stand for a vowel the reading does not spell as such.  Consonants are
    never skipped in either direction: that is the test the OCR damage fails.
    """
    signs = [c for c in spelling if c in SOUNDS]
    if not signs:
        return False
    tokens = _letters(reading)
    if not tokens:
        return False
    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        i, j = stack.pop()
        if i == len(signs):
            if all(c in VOWELS for c in tokens[j:]):
                return True
            continue
        if j >= len(tokens):
            continue
        todo = []
        if tokens[j] in VOWELS:
            todo.append((i, j + 1))
        if tokens[j] in SOUNDS[signs[i]]:
            todo.append((i + 1, j + 1))
        if signs[i] in "ʾyw":
            todo.append((i + 1, j))
        for step in todo:
            if step not in seen:
                seen.add(step)
                stack.append(step)
    return False


def spelling_of(translit: str) -> str:
    """The Pahlavi spelling a MacKenzie bracket opens with."""
    text = _SPELL.match(translit or "").group(0).strip()
    token = text.split()[0] if text.split() else ""
    return token.strip("-")


def _reading_like(text: str) -> bool:
    """Whether a bracket token is a transcription rather than a spelling."""
    return bool(text) and bool(re.fullmatch(r"[A-Za-zāēīōūšžčǰñγδθə'’\- ]+", text)) \
        and bool(re.search(r"[aeiouāēīōūǣ]", text))


def from_glossary() -> tuple[dict, dict]:
    """The spellings the dictionary's own headword lines read.

    An entry is one of three shapes, and each is handled for what it is:

    * the headword is the reading and the bracket opens with the spelling
      (``abag [LWTE …]``) — the common case;
    * the headword is a Pahlavi-script form and the bracket is its reading
      (``𐫅𐫏𐫇 | dēw``);
    * the headword is the spelling written in transliteration and the bracket
      is the reading (``kywʾn' | kēwān``).
    """
    rows: dict[str, dict] = {}
    stats = {"entries": 0, "reading_rows": 0, "spelling_rows": 0, "kept": 0,
             "refused": 0, "logograms": 0, "unread": 0}

    def put(form: str, reading: str, tier: str) -> None:
        if not form or not reading or form in rows:
            return
        rows[form] = {"lang": "pal", "reading": reading, "translit": "",
                      "source": f"MacKenzie 1971 s.v. {reading}",
                      "tier": tier}

    for entry in data.lexicon("pal"):
        stats["entries"] += 1
        word = (entry.get("word") or "").strip()
        translit = (entry.get("translit") or "").strip()
        if not word:
            stats["unread"] += 1
            continue
        # The headword is written in a script, the bracket is its reading.
        if any(0x10A00 <= ord(c) <= 0x10BFF for c in word):
            # A bracket may give several readings ("namak, namehk").  The one
            # the signs can spell is the reading of this spelling; if none can,
            # the first is the dictionary's own answer and is kept as such
            # (2026-11-12).
            candidates = [c.strip().strip("/[]") for c in translit.split(",")]
            candidates = [c.split()[0] for c in candidates if _reading_like(c)]
            def spellable(candidate: str) -> bool:
                fit = script.match("pal", candidate, word)
                return bool(fit and fit.get("ok"))

            reading = next((c for c in candidates if spellable(c)),
                           candidates[0] if candidates else "")
            if reading:
                stats["reading_rows"] += 1
                # A reading the signs cannot spell is still a reading of the
                # word — an Arameogram is read as a whole, and a Manichaean
                # page may state a form the table has no sign for — but it is
                # not evidence that these signs say these sounds, so it is
                # kept on the quoted tier instead of the recorded one.
                fit = script.match("pal", reading, word)
                put(word, reading,
                    "recorded" if fit and fit.get("ok") else "script-quoted")
            else:
                stats["unread"] += 1
            continue
        # A headword that is itself a spelling (no vowel, or Aramaic letters)
        # and a bracket that is a transcription (kywʾn' | kēwān).
        if not _reading_like(word):
            # MacKenzie's bracket can hold a phrase; the reading of the
            # headword is the word the entry prints in bold (ŠM "pad
            # '''nām''' ī yazdān" is the word nām in a phrase), so the bold
            # word wins over the first token (2026-11-09).
            bold = re.search(r"\'\'\'([^\'’]+)\'\'\'", translit)
            token = (bold.group(1) if bold else translit.split(",")[0]).strip().strip("/[]")
            if _reading_like(token) and len(word) > 1:
                stats["spelling_rows"] += 1
                put(word.lstrip("*"), token.split()[0], "recorded")
            else:
                stats["unread"] += 1
            continue
        if not translit:
            stats["unread"] += 1
            continue
        spelling = spelling_of(translit).lstrip("*")
        stats["reading_rows"] += 1
        if not spelling or len(spelling) < 2:
            stats["unread"] += 1
            continue
        if not re.fullmatch(r"[ʾbgdhwzḥṭyklmnsʿpcqrštA-ZŠṬḤṢČŽĞĀĒĪŌŪ'’\-]+", spelling):
            stats["refused"] += 1
            continue
        # An Aramaic ideogram is read as a whole word, not letter by letter:
        # the letters spell an Aramaic form whose Middle Persian reading is a
        # lexical fact, so the value comes from the dictionary's headword and
        # the sound table has nothing to say about it.
        if re.fullmatch(r"[A-ZŠṬḤṢČŽĞĀĒĪŌŪ'’\-]+", spelling):
            stats["logograms"] += 1
            put(spelling, word, "recorded")
            continue
        if not consistent(spelling, word):
            stats["refused"] += 1
            continue
        stats["kept"] += 1
        put(spelling, word, "recorded")
    return rows, stats


def merge_wiktionary(rows: dict) -> dict:
    """Merge the shipped Wiktionary extraction (quoted tier), if present.

    A Wiktionary page states a transcription for a spelling the same way the
    dictionary does, and the page is the locator.  These rows are kept apart by
    their ``tier``: a page's ``ts=`` is a quotation, not the headword line of
    the printed dictionary, and a reader may weigh the two differently.
    """
    if not WIKT.exists():
        return rows
    try:
        extra = json.loads(WIKT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return rows
    for form, row in (extra or {}).items():
        if not form or not isinstance(row, dict) or not row.get("reading"):
            continue
        if form in rows:
            continue
        # The same test the dictionary rows pass: the reading has to be what
        # the spelling can say.  A page that quotes a transcription the signs
        # cannot spell (a final -e the letters do not write) is left out.
        tier = row.get("tier") or "quoted"
        manichaean = any(0x10AC0 <= ord(c) <= 0x10AFF for c in form)
        if any(0x10A00 <= ord(c) <= 0x10BFF for c in form):
            fit = script.match("pal", row["reading"], form)
            if not fit or not fit["ok"]:
                if manichaean:
                    # Manichaean is an alphabet: when the signs cannot spell
                    # the page's transcription, one of the two is wrong and
                    # there is nothing to keep (2026-11-12).
                    continue
                # A Book Pahlavi form the signs cannot spell is an Arameogram:
                # the page reads it as a whole word, not letter by letter, so
                # the reading is a lexical fact and is kept under its own tier.
                tier = "script-quoted"
        elif not consistent(form, row["reading"]):
            continue
        rows[form] = {
            "lang": "pal", "reading": row["reading"],
            "translit": row.get("translit", ""),
            "source": row.get("source") or "Wiktionary, Middle Persian entry",
            "tier": tier,
        }
    return rows


#: A Wiktionary etymology sentence states a reading beside the spelling it
#: belongs to: "Middle Persian 𐭠𐭥𐭣 (ʾʿd /⁠ud⁠/)" gives the Book Pahlavi
#: signs and their reading, "Middle Persian LHMA (nān, “bread”)" gives a
#: heterogram and its reading, and "Middle Persian swk' (sōg, …)" a
#: transliteration.  The sentence is the locator, exactly as a page's head
#: template is, so these rows are ``quoted`` (2026-11-09).
# A gloss may itself hold a parenthesis ("ul, “up(wards)”"), so the
# parenthetical allows one level of nesting.
_ETYM_PAIR = re.compile(r"Middle Persian\s+([^\s()\[\]]+)\s*"
                       r"\(((?:[^()]|\([^()]*\))*)\)")


def _stated_reading(paren: str) -> str:
    """The transcription a parenthetical states, notation aside."""
    text = (paren or "").replace("\u2060", "")
    # A parenthetical that is wholly a quoted gloss is a meaning, not a
    # reading: "Compare Middle Persian slt' (“cold”)" says what the word means
    # and gives no transcription.  Reading it as one made slt' ambiguous
    # against the سرد entry's recorded /sard/ and dropped a real reading from
    # the table (2026-11-10).
    if re.match(r"""^\s*[“"'‘].*[”"'’]\s*$""", text) and "/" not in text:
        return ""
    enclosed = re.search(r"/([^/]+)/", text)
    reading = enclosed.group(1) if enclosed else text.split(",")[0]
    reading = reading.strip().strip("‘’“”\"'").strip()
    token = reading.split()[0] if reading.split() else ""
    return token.strip("/[]") if _reading_like(token) else ""


def _spellable(form: str, reading: str) -> bool:
    """Whether the signs of a recorded spelling can say this reading.

    A script form is checked through the letters its signs stand for, so the
    polyphony of the Pahlavi table (𐭪 k/g, 𐭥 w/ō/ū/r) is honoured; a
    transliteration is checked letter for letter.  A heterogram written in
    capitals (LHMA, ŠM) is read as a whole word, so its value is the
    dictionary's own and the letters have nothing to say about it.
    """
    if re.fullmatch(r"[A-ZŠṬḤṢČŽĞĀĒĪŌŪ'’\-]+", form):
        return True
    if any(0x10A00 <= ord(c) <= 0x10BFF for c in form):
        # The same test a reader of the table can run: the signs have to spell
        # the reading's letters in order.  A form that only fails because the
        # matcher's alphabet folds š/ž to s/z is refused rather than recorded
        # under a reading the table cannot demonstrate (2026-11-09).
        fit = script.match("pal", reading, form)
        return bool(fit and fit["ok"])
    return consistent(form, reading)


def from_etymologies(rows: dict) -> dict:
    """Add the pairs the repo's own etymology sentences quote.

    The Persian glossary cites its Middle Persian source as a spelling with its
    reading, and so do the English and German entries that discuss the same
    word.  Those sentences are already in the repo, so the readings are
    copied, not inferred.  A form quoted with two different readings is left
    out rather than chosen between (2026-11-09).
    """
    found: dict[str, dict[str, str]] = {}
    for lang, _size in data.available_lexicons():
        for entry in data.lexicon(lang):
            text = entry.get("etym") or ""
            for match in _ETYM_PAIR.finditer(text):
                form, paren = match.group(1), match.group(2)
                reading = _stated_reading(paren)
                if not reading:
                    continue
                key = normalise_etymon(form)
                if not key:
                    continue
                found.setdefault(key, {}).setdefault(
                    reading.lower(), f"Wiktionary, {lang} entry \"{entry['word']}\", etymology")
    added = 0
    ambiguous = 0
    refused = 0
    for key, readings in found.items():
        if len(readings) != 1:
            ambiguous += 1
            continue
        reading, source = next(iter(readings.items()))
        if not _spellable(key, reading):
            refused += 1
            continue
        if key not in rows:
            rows[key] = {"lang": "pal", "reading": reading, "translit": "",
                         "source": source, "tier": "quoted"}
            added += 1
        spaced = key.replace(" ", "")
        if spaced != key and spaced not in rows and _spellable(spaced, reading):
            rows[spaced] = {"lang": "pal", "reading": reading, "translit": "",
                            "source": source, "tier": "quoted"}
            added += 1
    print(f"etymologies: {added} spellings, {refused} forms refused, "
          f"{ambiguous} ambiguous forms left out")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify, write nothing")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    rows, stats = from_glossary()
    rows = from_etymologies(rows)
    rows = merge_wiktionary(rows)
    ordered = {k: rows[k] for k in sorted(rows)}
    print(json.dumps(stats, indent=2))
    print(f"table: {len(ordered)} spellings")
    path = Path(args.out)
    if args.check:
        if path.exists():
            old = json.loads(path.read_text(encoding="utf-8"))
            same = old.keys() == ordered.keys()
            print("check:", "identical" if same else f"differs ({len(old)} stored)")
        return 0
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    print("→", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
