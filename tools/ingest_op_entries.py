#!/usr/bin/env python3
"""Ingest the curated Old Persian entries read from Wiktionary and Kent (1953).

The input is ``data/lexicon/_supplement/peo_entries.json``.  Every row carries
the cuneiform headword exactly as the source prints it, the sign-by-sign
transliteration, the reading the dictionary records, a part of speech, its
glosses, the source keys, a ``ref`` sentence and the exact URL.  A row is only
written here when the source prints the cuneiform form; nothing is
reverse-engineered from a transliteration.

    python3 tools/ingest_op_entries.py --fetch   # snapshot the live candidates
    python3 tools/ingest_op_entries.py --check   # compare curated rows with the live pages
    python3 tools/ingest_op_entries.py           # write the supplement (idempotent)

``--fetch`` walks Wiktionary's Old Persian lemma and non-lemma categories with
the repo's User-Agent (read-only, no account, no edit) and writes a candidate
snapshot beside the curated file.  ``--check`` fetches only the pages named by
the curated rows and verifies the word, the sign transliteration and a gloss;
it is the guard against a page that moved or a row that was mistyped.  The
supplement writer preserves every hand-written row that this tool did not
produce, so the three earlier Old Persian rows survive a rebuild.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SUPP = ROOT / "data" / "lexicon" / "_supplement"
CURATED = SUPP / "peo_entries.json"
CANDIDATES = SUPP / "peo_candidates.json"
OUT = SUPP / "peo.jsonl.gz"
API = "https://en.wiktionary.org/w/api.php"
UA = "pie-etymology-build/0.1 (https://github.com/adoosth/pie; adoosth@gwdg.de)"
GENERATOR = "op-ingest"
REPAIR_GENERATOR = "op-ancestry-repair"

#: The etymology text names a stage in prose; this is the only map the repair
#: needs.  A form is added only when the record says "From/Inherited from
#: <stage> *X" and the stage is one the peo chain models.
STAGE_OF = {
    "Proto-Indo-European": "ine-pro",
    "Proto-Indo-Iranian": "iir-pro",
    "Proto-Iranian": "ira-pro",
}
STATED_RE = re.compile(
    r"(?:From|Inherited from|Borrowed from)\s+"
    r"(Proto-Indo-European|Proto-Indo-Iranian|Proto-Iranian)\s+"
    r"\*([^\s,;()\[\]~?]+)"
)

#: The sign values of the Old Persian syllabary, as en.wiktionary's
#: Module:peo-translit prints them.  The syllabary leaves some vowels unwritten;
#: this table only spells the signs the source printed, it does not add vowels.
SIGNS = {
    "𐎠": "a", "𐎡": "i", "𐎢": "u", "𐎣": "k", "𐎤": "ku", "𐎥": "g",
    "𐎦": "gu", "𐎧": "x", "𐎨": "c", "𐎩": "j", "𐎪": "ji", "𐎫": "t",
    "𐎬": "tu", "𐎭": "d", "𐎮": "di", "𐎯": "du", "𐎰": "θ", "𐎱": "p",
    "𐎲": "b", "𐎳": "f", "𐎴": "n", "𐎵": "nu", "𐎶": "m", "𐎷": "mi",
    "𐎸": "mu", "𐎹": "y", "𐎺": "v", "𐎻": "vi", "𐎼": "r", "𐎽": "ru",
    "𐎾": "l", "𐎿": "s", "𐏀": "z", "𐏁": "š", "𐏂": "ç", "𐏃": "h",
    "𐏈": "AM", "𐏉": "AM", "𐏊": "AMha", "𐏋": "XŠ", "𐏌": "DH",
    "𐏍": "DH", "𐏎": "BG", "𐏏": "BU",
}

POS_MAP = {
    "proper noun": "name", "noun": "noun", "adjective": "adj", "adverb": "adv",
    "verb": "verb", "verb form": "verb", "pronoun": "pron",
    "preposition": "prep", "numeral": "num", "conjunction": "conj",
    "particle": "particle", "prefix": "prefix", "suffix": "suffix",
    "article": "article", "noun form": "noun", "proper noun form": "name",
    "letter": "character", "character": "character", "symbol": "symbol",
}
POS_VALUES = set(POS_MAP.values()) | {"interj", "postp", "root"}

REF_TEMPLATES = {
    "inh": "inherit", "inh+": "inherit", "der": "derive", "der+": "derive",
    "bor": "borrow", "bor+": "borrow", "lbor": "borrow", "slbor": "borrow",
    "cal": "calque", "calque": "calque",
}


# --------------------------------------------------------------------------
# Wiktionary API (read-only)
# --------------------------------------------------------------------------
def api(params: dict, tries: int = 6) -> dict:
    params = {"format": "json", "formatversion": "2", "action": "query", **params}
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                time.sleep(0.2)
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError("too many 429 responses")


def category_pages(category: str, depth: int = 2) -> list[str]:
    title = category if category.startswith("Category:") else "Category:" + category
    pages: list[str] = []
    seen: set[str] = set()
    queue = [(title, depth)]
    while queue:
        cat, d = queue.pop()
        cont: dict = {}
        while True:
            data = api({"list": "categorymembers", "cmtitle": cat, "cmlimit": "500", **cont})
            for row in data.get("query", {}).get("categorymembers", []):
                name = row["title"]
                if row["ns"] == 14:
                    if d > 0 and name not in seen:
                        seen.add(name)
                        queue.append((name, d - 1))
                elif name not in seen:
                    seen.add(name)
                    pages.append(name)
            cont = data.get("continue") or {}
            if not cont:
                break
        time.sleep(0.2)
    return pages


def wikitext(titles: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(titles), 40):
        data = api({"titles": "|".join(titles[i:i + 40]), "prop": "revisions",
                    "rvprop": "content", "rvslots": "main"})
        for page in data.get("query", {}).get("pages", []):
            revs = page.get("revisions") or []
            if revs:
                out[page["title"]] = revs[0]["slots"]["main"].get("content", "")
    return out


# --------------------------------------------------------------------------
# Wikitext parsing
# --------------------------------------------------------------------------
def syllabify(word: str) -> str:
    """Sign-by-sign transliteration, the spelling the syllabary writes."""
    out: list[str] = []
    need_hyphen = False
    for ch in word:
        if ch in SIGNS:
            if need_hyphen:
                out.append("-")
            out.append(SIGNS[ch])
            need_hyphen = True
        else:
            need_hyphen = False
            out.append(ch)
    return "".join(out)


def is_syllabic(value: str) -> bool:
    value = value.strip()
    if not value or "/" in value:
        return False
    parts = value.split("-")
    return len(parts) > 1 and all(0 < len(part) <= 3 for part in parts)


def strip_refs(text: str) -> str:
    text = re.sub(r"<ref[^>]*/>", "", text)
    return re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)


def clean(text: str) -> str:
    """Plain text from one definition line, with the templates this source uses."""
    text = strip_refs(text)
    text = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)

    def angle(match: re.Match) -> str:
        return re.sub(r"^[rc]/", "", match.group(1))

    text = re.sub(r"<<([^>]*)>>", angle, text)
    for _ in range(20):
        match = re.search(r"\{\{([^{}]*)\}\}", text)
        if not match:
            break
        parts = [part.strip() for part in match.group(1).split("|")]
        name = parts[0].lower()
        args: dict[str, str] = {}
        positional: list[str] = []
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                args[key.strip()] = value.strip()
            else:
                positional.append(part)
        rep = ""
        if name in {"lb", "lbl", "label", "qual", "q", "i", "sense", "n-g",
                    "ng", "def-uncertain", "topics", "topic", "c", "cat"}:
            rep = ""
        elif name == "gloss":
            rep = " (" + (positional[0] if positional else "") + ")"
        elif name in {"m", "l", "l-self"}:
            rep = positional[1] if len(positional) > 1 else (positional[0] if positional else "")
        elif name == "w":
            rep = positional[-1] if positional else ""
        elif name in {"wp", "slim-wikipedia", "pedia", "wikipedia"}:
            rep = ""
        elif name == "given name":
            given = args.get("xlit") or args.get("eq")
            rep = ("a male given name" if "male" in positional
                   else "a female given name" if "female" in positional else "a given name")
            if given:
                rep += ", equivalent to English " + given
        elif name in {"alt form of", "alternative form of", "alter"}:
            rep = "alternative form of " + (positional[1] if len(positional) > 1
                                           else (positional[0] if positional else ""))
        elif name == "inflection of":
            lemma = positional[1] if len(positional) > 1 else ""
            rep = f"{' '.join(positional[2:])} of {lemma}".strip()
        elif name == "place":
            rep = args.get("t") or (positional[1] if len(positional) > 1 else "")
        elif name == "tcl":
            rep = positional[1] if len(positional) > 1 else ""
        elif name in {"circa", "ca"}:
            rep = "c. " + " ".join(positional)
        elif name.lower() in {"bc", "bce"}:
            rep = "BC"
        elif name in {"...", "…"}:
            rep = "…"
        text = text[:match.start()] + rep + text[match.end():]
    text = re.sub(r"''+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).replace("r/", "").replace("c/", "")
    text = re.sub(r"\s+([,;:.!?])", r"\1", text)
    return text.strip(" ,;:")


def old_persian_section(text: str) -> str:
    match = re.search(r"^==\s*Old Persian\s*==\s*$", text, re.M)
    if not match:
        return ""
    rest = text[match.end():]
    end = re.search(r"^==(?!=).*==\s*$", rest, re.M)
    return rest[:end.start()] if end else rest


def subsections(section: str) -> list[tuple[str, str]]:
    parts = re.split(r"^===\s*(.+?)\s*===\s*$", section, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def head(subsection: str) -> dict | None:
    match = re.search(r"\{\{\s*head\s*\|peo\|([^}]*)\}\}", subsection)
    if match:
        out: dict[str, str] = {}
        for part in [p.strip() for p in match.group(1).split("|")]:
            if "=" in part:
                key, value = part.split("=", 1)
                out[key.strip()] = value.strip()
            else:
                out.setdefault("pos", part)
        return out
    match = re.search(r"\{\{\s*peo-([a-z -]+?)\s*(?:\|([^}]*))?\}\}", subsection)
    if match:
        out = {"pos": match.group(1)}
        for part in (match.group(2) or "").split("|"):
            if "=" in part:
                key, value = part.split("=", 1)
                out[key.strip()] = value.strip()
        return out
    return None


def definitions(subsection: str) -> list[str]:
    out = []
    for line in subsection.splitlines():
        line = line.strip()
        if not line.startswith("#") or line.startswith(("#*", "##", "#:")):
            continue
        value = clean(line[1:])
        if value:
            out.append(value)
    return out


def etymology(section: str) -> str:
    match = re.search(r"^===\s*Etymology(?: \d+)?\s*===\s*$", section, re.M)
    if not match:
        return ""
    rest = section[match.end():]
    end = re.search(r"^===", rest, re.M)
    return rest[:end.start()] if end else rest


def ancestry(text: str) -> list[list[str]]:
    out: list[list[str]] = []
    for match in re.finditer(
            r"\{\{\s*(inh|inh\+|der|der\+|bor|bor\+|lbor|slbor|cal|calque)"
            r"\s*\|\s*peo\s*\|\s*([a-zA-Z][\w-]*)\s*\|\s*([^|}]+)", text):
        rel = REF_TEMPLATES[match.group(1)]
        word = match.group(3).strip()
        if rel == "derive":
            continue  # "derived from" is not an inheritance claim
        if word and not word.startswith(":") and word != "-":
            out.append([match.group(2), word, rel])
    for match in re.finditer(r"\{\{\s*(?:ety|etymon)\|([^}]*)\}\}", text):
        body = match.group(1)
        for sub in re.finditer(r"\|?:?(inh|bor)\|([a-zA-Z][\w-]*):(\*?[^<|}>]+)", body):
            out.append([sub.group(2), sub.group(3), REF_TEMPLATES[sub.group(1)]])
        for sub in re.finditer(r"<ety:(inh|bor)<([a-zA-Z][\w-]*):(\*?[^>]+)>>", body):
            out.append([sub.group(2), sub.group(3), REF_TEMPLATES[sub.group(1)]])
    unique: list[list[str]] = []
    for item in out:
        if item not in unique:
            unique.append(item)
    return unique


def split_reading(value: str) -> tuple[list[str], list[str]]:
    syllabic: list[str] = []
    readings: list[str] = []
    for match in re.findall(r"/([^/]+)/", value):
        readings.append(match.strip())
    value = re.sub(r"/[^/]+/", " ", value)
    for piece in re.split(r"\s*,\s*|\s+", value):
        piece = piece.strip()
        if not piece:
            continue
        (syllabic if is_syllabic(piece) else readings).append(piece)
    return syllabic, readings


def parse_page(word: str, text: str) -> dict | None:
    section = old_persian_section(text)
    if not section:
        return None
    entries = []
    syllabic: list[str] = []
    readings: list[str] = []
    for name, body in subsections(section):
        head_data = head(body)
        if not head_data:
            continue
        senses = definitions(body)
        if not senses:
            continue
        entries.append({"heading": name, "head": head_data, "defs": senses})
        for key in ("tr", "ts"):
            value = head_data.get(key)
            if value:
                syl, read = split_reading(value)
                syllabic += syl
                readings += read
    if not entries:
        return None
    return {
        "word": word,
        "syll": syllabify(word),
        "pos": POS_MAP.get(entries[0]["head"].get("pos", ""), ""),
        "senses": [sense for entry in entries for sense in entry["defs"]],
        "reads": list(dict.fromkeys(value.replace("\u2060", "") for value in readings)),
        "sylls": list(dict.fromkeys(syllabic)),
        "anc": ancestry(etymology(section)),
    }


def candidate_rows() -> list[dict]:
    titles = category_pages("Old Persian lemmas", depth=3)
    for category in ("Old Persian non-lemma forms", "Old Persian verb forms",
                     "Old Persian noun forms"):
        titles += [name for name in category_pages(category, depth=1) if name not in titles]
    texts = wikitext(titles)
    rows = []
    for title, text in texts.items():
        parsed = parse_page(title, text)
        if parsed:
            parsed["url"] = "https://en.wiktionary.org/wiki/" + urllib.parse.quote(title, safe="")
            rows.append(parsed)
    return rows


# --------------------------------------------------------------------------
# Ingestion
# --------------------------------------------------------------------------
def source_keys() -> set[str]:
    with open(ROOT / "data" / "sources.yaml", encoding="utf-8") as fh:
        return {row["id"] for row in yaml.safe_load(fh)}


def read_curated(path: Path = CURATED) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["rows"] if isinstance(data, dict) else data


def validate(rows: list[dict]) -> None:
    known = source_keys()
    seen = set()
    for index, row in enumerate(rows):
        where = f"row {index + 1} ({row.get('word', '?')})"
        word = row.get("word") or ""
        if not word or any(not ("\U000103A0" <= ch <= "\U000103DF") for ch in word):
            raise SystemExit(f"{where}: word is not an Old Persian cuneiform headword")
        if word in seen:
            raise SystemExit(f"{where}: duplicate headword in the curated file")
        seen.add(word)
        if not row.get("translit"):
            raise SystemExit(f"{where}: no sign transliteration")
        if row.get("pos") not in POS_VALUES:
            raise SystemExit(f"{where}: unknown part of speech {row.get('pos')!r}")
        if not row.get("gloss") or not all(isinstance(g, str) and g for g in row["gloss"]):
            raise SystemExit(f"{where}: no gloss")
        sources = row.get("sources") or []
        if not sources or any(src not in known for src in sources):
            raise SystemExit(f"{where}: unknown or empty sources {sources!r}")
        if not row.get("ref") or "wiktionary.org" not in row["ref"]:
            raise SystemExit(f"{where}: no ref naming the page it was read in")
        if "wiktionary" in sources and not (row.get("url") or "").startswith(
                "https://en.wiktionary.org/wiki/"):
            raise SystemExit(f"{where}: wiktionary row without its exact URL")
        for ancestor in row.get("anc") or []:
            if len(ancestor) != 3 or ancestor[2] not in {"inherit", "borrow", "calque", "root"}:
                raise SystemExit(f"{where}: bad ancestry {ancestor!r}")


def existing_rows() -> tuple[list[dict], list[dict]]:
    hand: list[dict] = []
    generated: list[dict] = []
    if OUT.exists():
        with gzip.open(OUT, "rt", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                (generated if row.get("generator") == GENERATOR else hand).append(row)
    return hand, generated


def stated_ancestry(entry: dict) -> list[list[str]]:
    """The modelled ancestor forms the entry's own etymology text states.

    Only the sentence's own "From/Inherited from <stage> *X" counts: a cognate,
    an uncertain suggestion and a borrowed etymon are not inheritance links, and
    the repair never invents a form the record does not print.  A form with a
    space or a variant separator is skipped, because the chain's start form must
    be one phonological word.
    """
    out: list[list[str]] = []
    for match in STATED_RE.finditer(entry.get("etym") or ""):
        stage = STAGE_OF[match.group(1)]
        form = match.group(2).strip().rstrip(".,;:")
        if not form or len(form) > 60:
            continue
        row = [stage, form, "inherit"]
        if row not in out:
            out.append(row)
    return out


_UNUSABLE = re.compile(r"[*~()\[\]<>?\s]")


def _clean_form(word: str) -> str:
    """A form the derivation chain can start from, or ``""``.

    The ancestry rows are not always clean: a wikitext variant may arrive as
    ``*baywā́*baywā́>`` or ``['ira-pro:*baywā́, '>']``.  Such a row is present
    but cannot be a start form, and the etymology's plain form is the repair.
    """
    word = (word or "").strip().lstrip("*")
    if not word or len(word) > 60 or _UNUSABLE.search(word):
        return ""
    return word


def _usable_stages(entry: dict) -> set[str]:
    """The stages that already have at least one start form the chain can use."""
    stages: set[str] = set()
    for row in entry.get("anc") or []:
        if not isinstance(row, list) or len(row) < 2:
            continue
        lang, word = str(row[0]), str(row[1])
        if lang == ":inh" and ":" in word:
            lang, word = word.split(":", 1)
        if lang in STAGE_OF.values() and _clean_form(word):
            stages.add(lang)
    return stages


def repair_rows() -> list[dict]:
    """Rows that add an ancestor the entry states but its ancestry rows lack.

    The built glossary is the record under repair; the curated supplement and
    its writer are left untouched.  A repaired word keeps every field it had,
    and the row carries only the word, the language and the new links, which
    ``build_lexicons.merge_supplements`` unions into the existing entry.
    """
    path = ROOT / "data" / "lexicon" / "peo.jsonl.gz"
    if not path.exists():
        return []
    rows: list[dict] = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            entry = json.loads(line)
            have = _usable_stages(entry)
            new = [row for row in stated_ancestry(entry) if row[0] not in have]
            if new:
                rows.append({"word": entry["word"], "lang": "peo", "anc": new,
                             "generator": REPAIR_GENERATOR})
    return rows


def write_repairs(dry_run: bool = False) -> int:
    """Replace this tool's old repair rows with a freshly parsed set."""
    hand, generated = existing_rows()
    kept = [row for row in hand + generated if row.get("generator") != REPAIR_GENERATOR]
    repairs = repair_rows()
    ordered = kept + repairs
    for row in repairs:
        print(f"repair {row['word']}: {row['anc']}")
    if dry_run:
        print(f"dry run: {len(repairs)} ancestry repairs, nothing written")
        return 0
    with open(OUT, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:
        for row in ordered:
            fh.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
    print(f"{OUT.relative_to(ROOT)}: {len(kept)} kept rows + {len(repairs)} ancestry repairs")
    return 0


def base_words() -> set[str]:
    path = ROOT / "data" / "lexicon" / "peo.jsonl.gz"
    if not path.exists():
        return set()
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return {json.loads(line)["word"] for line in fh if line.strip()}


def write_supplement(rows: list[dict]) -> None:
    hand, _generated = existing_rows()
    hand_words = {row["word"] for row in hand}
    curated_words = {row["word"] for row in rows}
    clash = hand_words & curated_words
    if clash:
        raise SystemExit(f"curated rows duplicate hand-written supplement rows: {sorted(clash)}")
    built = base_words() - {row["word"] for row in read_generated()}
    clash = built & curated_words
    if clash:
        raise SystemExit(f"curated rows already exist in the built glossary: {sorted(clash)}")
    ordered = hand + sorted(rows, key=lambda row: row["word"])
    with open(OUT, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:
        for row in ordered:
            fh.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
    print(f"{OUT.relative_to(ROOT)}: {len(hand)} hand rows + {len(rows)} curated rows")


def read_generated() -> list[dict]:
    _hand, generated = existing_rows()
    return generated


def check_live(rows: list[dict]) -> int:
    texts = wikitext([row["word"] for row in rows])
    bad = 0
    for row in rows:
        parsed = parse_page(row["word"], texts.get(row["word"], ""))
        problems = []
        if parsed is None:
            problems.append("page no longer has an Old Persian section")
        else:
            if parsed["syll"] != row["translit"]:
                problems.append(f"transliteration {parsed['syll']!r} != {row['translit']!r}")
            if row.get("translit_alt") and not set(row["translit_alt"]) & set(parsed["reads"]):
                problems.append(f"reading {row['translit_alt']!r} not in {parsed['reads']!r}")
            wanted = unicodedata.normalize("NFC", row["gloss"][0].lower())
            found = [unicodedata.normalize("NFC", sense.lower()) for sense in parsed["senses"]]
            if wanted not in found and not any(wanted in sense for sense in found):
                # A row whose gloss was taken from Kent's lexicon (rather than
                # from Wiktionary's wording) is allowed to differ here; the
                # word, the transliteration and the reading are still checked.
                if "kent-1953" not in (row.get("sources") or []):
                    problems.append(f"gloss {row['gloss'][0]!r} not among {parsed['senses']!r}")
        if problems:
            bad += 1
            print(f"{row['word']}: " + "; ".join(problems))
    print(f"checked {len(rows)} rows against the live pages: {len(rows) - bad} okay, {bad} differ")
    return 0 if bad == 0 else 1


def kent_check(rows: list[dict], path: Path) -> int:
    """Report which curated readings occur as headwords in Kent's lexicon."""
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next((i for i, line in enumerate(text) if "LEXICON" in line and i > 20000), 23000)
    end = len(text)
    pos = "sb|adj|vb|adv|pron|prep|num|conj|interj|demonst|pn|prefix|insep|rel|interrog|part"

    def norm(value: str) -> str:
        value = unicodedata.normalize("NFD", value.lower())
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        value = value.replace("š", "s").replace("ç", "c").replace("θ", "t")
        return re.sub(r"[^a-z]", "", value)

    heads = {}
    for line in text[start:end]:
        match = re.match(r"[| ]*([A-Za-zāēīōūšçθ*()\-]{2,30}?)[-\s]*(?:" + pos + r")\.", line)
        if match:
            heads.setdefault(norm(match.group(1)), line.strip())
    hits = 0
    for row in rows:
        for reading in [*(row.get("translit_alt") or []), row.get("translit", "")]:
            key = norm(reading)
            if key in heads:
                hits += 1
                print(f"{row['word']}\t{reading}\t{heads[key]}")
                break
    print(f"{hits} of {len(rows)} curated readings occur as Kent (1953) lexicon entries")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="snapshot live Wiktionary candidates")
    parser.add_argument("--check", action="store_true", help="compare curated rows with live pages")
    parser.add_argument("--kent", type=Path, help="Kent (1953) OCR text for a headword cross-check")
    parser.add_argument("--curated", type=Path, default=CURATED)
    parser.add_argument("--repair-ancestry", action="store_true",
                        help="add the modelled ancestor an entry's own etymology states but its anc rows lack")
    parser.add_argument("--dry-run", action="store_true", help="with --repair-ancestry: print, write nothing")
    args = parser.parse_args()

    if args.repair_ancestry:
        return write_repairs(args.dry_run)

    if args.fetch:
        rows = candidate_rows()
        payload = {"note": "candidates parsed from the live Wiktionary API; the curated selection is peo_entries.json",
                   "rows": rows}
        CANDIDATES.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{CANDIDATES.relative_to(ROOT)}: {len(rows)} candidates")
        return 0

    rows = read_curated(args.curated)
    validate(rows)
    if args.check:
        return check_live(rows)
    if args.kent:
        return kent_check(rows, args.kent)
    write_supplement(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
