#!/usr/bin/env python3
"""Build a glossary and its recorded ancestry from a Wiktionary lemma category.

Several stages this model needs are not in the kaikki dumps (Middle Persian,
Parthian) or are older there than the wiki (Old Persian): their lemmas live
only in Wiktionary.  This tool walks a lemma category, fetches the wikitext in
batches, keeps the page's own language section, and stores what the record
says — the headword, its reading, its glosses, the etymology prose and the
inheritance/borrowing links — in one resumable ledger:

    python3 tools/wiktionary_lemmas.py fetch pal --category "Middle Persian lemmas" --language "Middle Persian"
    python3 tools/wiktionary_lemmas.py fetch xpr --category "Parthian lemmas" --language "Parthian"
    python3 tools/wiktionary_lemmas.py emit pal            # merge into data/lexicon/pal.jsonl.gz
    python3 tools/wiktionary_lemmas.py status pal

Rules this file keeps, because they are the rules the engine keeps:

* **Only the page's own templates are recorded.**  ``{{inh}}``/``{{inh+}}``
  and ``{{etymon}}``'s ``:inh`` mark inheritance, ``{{bor}}``/``{{lbor}}``
  and ``:bor`` a borrowing; ``{{der}}`` names a derivation base, not the
  etymon, and is left out.  Nothing is inferred from spelling similarity.
* **A reading is what the page states** — ``ts=`` (phonetic) before ``tr=``
  (transliteration) on the section's own head template.  The engine's laws
  start from a reading, so a row without one is stored without one rather
  than given a letter-by-letter guess here.
* **The ledger is one row per page, appended and rewritten atomically.**  A
  rerun asks only for pages whose row is missing, so a long pass over a
  category resumes where it stopped.  ``fetched`` is the revision id and
  timestamp the row was read at.
* **A ledger row never overwrites a curated field.**  ``emit`` fills fields a
  row does not have (``translit``, ``anc``, ``etym``, ``url``) and appends
  words the glossary does not hold yet; it never rewrites a gloss the
  dictionary gave or a field a supplement added.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))

from fetch_wiktionary import category_pages  # noqa: E402
from pie.translit import is_scripted  # noqa: E402
from ingest_mackenzie import (  # noqa: E402
    _params, _templates, clean, etymology_links, fetch_wikitext,
)

LEDGER = ROOT / "data" / "sources" / "wikt_lemmas"
POSITIONS = ("Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Numeral",
             "Preposition", "Postposition", "Proper noun", "Conjunction",
             "Particle", "Interjection", "Determiner", "Article")


def section_of(text: str, language: str) -> tuple[str, int] | None:
    """The page's ``==Language==`` section and the offset it starts at."""
    m = re.search(r"^==\s*" + re.escape(language) + r"\s*==\s*$", text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^==[^=]", rest, re.M)
    body = rest[: nxt.start()] if nxt else rest
    return body, m.start()


def pos_of(section: str) -> str:
    for name in POSITIONS:
        if re.search(r"^===\s*" + re.escape(name) + r"\s*===\s*$", section, re.M):
            return name.lower()
    return ""


def reading_of(section: str, lang: str) -> tuple[str, str]:
    """The section's own head reading: (value, which parameter gave it)."""
    for tpl in _templates(section):
        parts = _params(tpl)
        if not parts:
            continue
        name = parts[0]
        if not (name == "head" or name.startswith(lang + "-")):
            continue
        values: dict[str, str] = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                values[key.strip()] = clean(value)
        for key in ("ts", "tr"):
            if values.get(key):
                return visible(values[key]), key
        return "", ""
    return "", ""


def glosses_of(section: str, limit: int = 3) -> list[str]:
    """The definitions under the first POS heading, templates stripped."""
    m = re.search(r"^===\s*" + "|".join(POSITIONS) + r"\s*===\s*$", section, re.M)
    body = section[m.end():] if m else section
    out: list[str] = []
    for line in body.splitlines():
        if not line.startswith("#") or line.startswith(("##", "#*", "#:", "#;")):
            continue
        text = line.lstrip("#").strip()
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
        text = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"''+", "", text)
        text = clean(text)
        if text and len(text) > 1:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _lang_names() -> dict[str, str]:
    try:
        from pie import data
        return {code: (row.get("name") or code)
                for code, row in data.languages().items()}
    except Exception:  # the table is a nicety, not a requirement
        return {}


NAMES: dict[str, str] | None = None


def _render_template(name: str, parts: list[str]) -> str:
    """One Wiktionary etymology template as the sentence it stands for."""
    global NAMES
    if NAMES is None:
        NAMES = _lang_names()
    args = [p for p in parts[1:]]
    positional = [a for a in args if "=" not in a]
    named = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in args if "=" in a}
    if name in {"inh", "inh+", "inherited", "bor", "bor+", "borrowed",
                "lbor", "slbor", "obor", "der", "der+"}:
        # ``{{inh|pal|peo|𐎱𐎢𐏂}}``: the first argument is the language the
        # entry is about, the second the stage the form comes from, the third
        # the form itself.
        if len(positional) >= 3:
            code, form = positional[1], positional[2]
        else:
            return ""
        if form in {"-", "—"}:
            return ""
        language = NAMES.get(code, code)
        reading = named.get("ts") or named.get("tr") or ""
        gloss = named.get("t") or named.get("gloss") or ""
        form = re.sub(r"<[^>]*>", "", str(form)).strip()
        text = f"{language} {form}".strip()
        if reading:
            text += f" ({reading})"
        if gloss:
            text += f" ‘{gloss}’"
        return text
    if name in {"m", "l", "mention", "link"} and positional:
        form = positional[-1]
        return form if len(positional) == 1 else form
    if name == "cog" and len(positional) >= 2:
        # ``{{cog|fa|سنگ|tr=sang}}``: unlike *inh*, the first argument is the
        # *other* language, so reading it the inherit way printed an empty
        # cognate ("Cognate with; see it for more", 2026-11-12).
        other = NAMES.get(positional[0], positional[0])
        reading = named.get("ts") or named.get("tr") or ""
        form = f"{other} {positional[1]}"
        # The sentence already says "Cognate with" or "See also"; a second
        # "cf." inside it read "Cognate with cf. Persian" (2026-11-12).
        return f"{form} ({reading})" if reading else form
    return ""


def tidy_etym(text: str) -> str:
    """Remove the parentheses a dropped template left behind.

    ``{{der|pal|ira-pro|*x}}`` is a derivation base, not an etymon, so it is
    rendered as nothing — and the sentence around it kept its brackets:
    "from (compare ), from".  Eleven Middle Persian pages printed that
    (2026-11-12, critic P2).  Only empty brackets are removed; a bracket with
    text in it is the record's and stays.
    """
    text = re.sub(r"\((?:compare|cf\.?)\s*\)", "", text or "")
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def etymology_of(section: str) -> str:
    """The etymology paragraph, with the templates it cites spelled out.

    A reader needs the sentence, not the markup: ``{{inh|pal|peo|𐎱𐎢𐏂|ts=puça-}}``
    is stored as "Old Persian 𐎱𐎢𐏂 (puça-)".  Templates this file does not
    know are dropped, so the prose can lose a clause but never invent one.
    """
    m = re.search(r"^===+\s*Etymology[^=]*===+\s*$", section, re.M)
    if not m:
        return ""
    rest = section[m.end():]
    nxt = re.search(r"^===[^=]", rest, re.M)
    body = rest[: nxt.start()] if nxt else rest
    body = re.sub(r"\{\{\s*([a-zA-Z+_-]+)", lambda mm: "{{" + mm.group(1).lower(), body)
    out: list[str] = []
    i = 0
    while i < len(body):
        start = body.find("{{", i)
        if start < 0:
            out.append(body[i:])
            break
        out.append(body[i:start])
        depth, j = 0, start
        while j < len(body):
            if body.startswith("{{", j):
                depth += 1
                j += 2
                continue
            if body.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
                continue
            j += 1
        inner = body[start + 2:j - 2]
        parts = _params(inner)
        if parts:
            out.append(_render_template(parts[0], parts))
        i = j
    text = "".join(out)
    text = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"''+", "", text)
    return tidy_etym(clean(text))[:600]


def row_for(title: str, text: str, lang: str, language: str) -> dict | None:
    if title.startswith(("Reconstruction:", "Appendix:", "Category:", "Template:")):
        return None
    found = section_of(text, language)
    if not found:
        return None
    section, _ = found
    glosses = glosses_of(section)
    if not glosses:
        return None
    reading, how = reading_of(section, lang)
    et = re.search(r"^===+\s*Etymology[^=]*===+\s*$", section, re.M)
    ety_body = ""
    if et:
        rest = section[et.end():]
        nxt = re.search(r"^===[^=]", rest, re.M)
        ety_body = rest[: nxt.start()] if nxt else rest
    links = []
    for link in etymology_links(ety_body):
        stage, form, rel = link
        if stage == lang or not re.fullmatch(r"[a-z][a-z0-9-]{1,11}", stage):
            continue
        # A form carrying template markup (``Idiglat<alt:…><id:Tigris>``) is
        # not the word: the wiki writes the alternate spelling and the sense id
        # inside angle brackets, and storing that as an ancestor printed a form
        # no dictionary holds (2026-11-12).
        if form in {"-", "—", "*"} or "=" in form or "/" in form or "<" in form:
            continue
        links.append([stage, form, rel])
    return {
        "title": title,
        "word": title,
        "lang": lang,
        "pos": pos_of(section),
        "gloss": glosses,
        "translit": reading,
        "reading_how": how,
        "etym": etymology_of(section),
        "anc": links,
        "url": "https://en.wiktionary.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
        "source": "wiktionary",
        "sources": ["wiktionary"],
    }


def ledger_path(lang: str) -> Path:
    return LEDGER / f"{lang}.jsonl.gz"


def read_ledger(lang: str) -> dict[str, dict]:
    path = ledger_path(lang)
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            rows[row["title"]] = row
    return rows


def write_ledger(lang: str, rows: dict[str, dict]) -> None:
    path = ledger_path(lang)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for title in sorted(rows):
            gz.write((json.dumps(rows[title], ensure_ascii=False,
                                 separators=(",", ":")) + "\n").encode())
    tmp.replace(path)


def cmd_fetch(args) -> int:
    rows = read_ledger(args.lang)
    cache = Path(args.cache) if args.cache else None
    todo: list[str] = []
    for category in args.category:
        name = category if category.startswith("Category:") else "Category:" + category
        for title in category_pages(name, depth=args.depth):
            if title not in rows and title not in todo:
                todo.append(title)
    # A page can be read again without clearing the ledger: the reader that
    # turned its templates into links may have been wrong, and the ledger is
    # the evidence a re-emit works from (2026-11-12: one Old Persian page
    # stored ``Idiglat<alt:…>`` as an ancestor).
    for title in getattr(args, "recheck", None) or []:
        rows.pop(title, None)
        if title not in todo:
            todo.append(title)
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(rows)} rows in the ledger, {len(todo)} pages to read", file=sys.stderr)
    if todo:
        wikitext = fetch_wikitext(todo, cache)
        added = 0
        for title in todo:
            row = row_for(title, wikitext.get(title, ""), args.lang, args.language)
            if row is None:
                rows[title] = {"title": title, "lang": args.lang, "empty": True}
            else:
                rows[title] = row
                added += 1
            if args.verbose:
                print(" ", title, "→", "ok" if row else "no section")
        write_ledger(args.lang, rows)
        print(f"+{added} rows with a {args.language} section")
    with_anc = sum(1 for r in rows.values() if r.get("anc"))
    with_read = sum(1 for r in rows.values() if r.get("translit"))
    print(f"ledger: {len(rows)} pages, {with_read} with a reading, {with_anc} with ancestry")
    return 0


def cmd_status(args) -> int:
    rows = read_ledger(args.lang)
    print(f"{args.lang}: {len(rows)} ledger rows")
    print("  with a reading :", sum(1 for r in rows.values() if r.get("translit")))
    print("  with ancestry  :", sum(1 for r in rows.values() if r.get("anc")))
    print("  with prose     :", sum(1 for r in rows.values() if r.get("etym")))
    print("  empty rows     :", sum(1 for r in rows.values() if r.get("empty")))
    return 0


def write_rows(lexicon: Path, rows: list[dict]) -> None:
    lexicon.parent.mkdir(parents=True, exist_ok=True)
    tmp = lexicon.with_suffix(".tmp")
    with tmp.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for row in rows:
            gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
    tmp.replace(lexicon)


def merge_into(lexicon: Path, rows: list[dict]) -> tuple[int, int, int]:
    """Add ledger rows to a glossary: fill, then append.  Never overwrite."""
    have: dict[str, dict] = {}
    by_word: dict[str, dict] = {}
    by_read: dict[str, dict] = {}
    if lexicon.exists():
        with gzip.open(lexicon, "rt", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                have[row.get("word", "")] = row
                # Two joins, kept apart on purpose.  A page is joined to a row
                # by its title (the two spell the same word) or by its reading
                # (the page is titled 𐭡𐭥𐭤 and the row is spelled pus).  An
                # empty key would match everything, so it is never indexed.
                for key, table in ((row.get("word"), by_word), (row.get("phon"), by_read),
                                   (row.get("translit"), by_read)):
                    folded = fold(key or "")
                    if folded:
                        table.setdefault(folded, row)
    filled = appended = 0
    claimed: set[int] = set()
    for row in rows:
        if row.get("empty") or not row.get("gloss"):
            continue
        key = row["word"]
        target = have.get(key) or have.get(row.get("title") or "")
        if target is None and fold(key):
            target = by_word.get(fold(key))
        reading = fold(row.get("translit") or "")
        if target is None and reading:
            # The page is titled in its own script and the glossary row is
            # spelled with the reading: 𐭡𐭥𐭤 (pus) finds the row "pus".
            target = by_read.get(reading) or by_word.get(reading)
        # Two Wiktionary pages can be the same word (lwc and 𐭩𐭥𐭬 both gloss
        # "day"); the first to reach a row owns it, so the second cannot
        # overwrite the reading the first one stated.
        if target is not None and id(target) in claimed:
            continue
        if target is not None:
            claimed.add(id(target))
        if target is None:
            have[key] = {k: row[k] for k in ("word", "lang", "pos", "gloss",
                                             "translit", "etym", "anc", "url",
                                             "source", "sources") if row.get(k)}
            appended += 1
            continue
        changed = False
        reading = reading_layer(row.get("translit") or "")
        title = row.get("title") or ""
        word = target.get("word") or ""
        # The two layers the engine reads: a word written in its own script
        # keeps the reading in ``translit``; a word already written in Latin
        # (MacKenzie's transcription is a reading, not a spelling) carries the
        # reading in ``phon`` and the script's own spelling in ``translit``.
        # Without this a dictionary bracket like "BRE < A r-h \\ pws" is read
        # as the word's pronunciation and no law can reach the entry.
        if reading:
            if is_scripted(word):
                if target.get("translit") != reading:
                    target["translit"] = reading
                    changed = True
            else:
                if target.get("phon") != reading:
                    target["phon"] = reading
                    changed = True
                # A dictionary bracket ("BRE < A r-h \\ pws | = M, N -") is the
                # apparatus around the spelling, not a reading: with the real
                # reading in ``phon`` it can only mislead, so it goes.
                if appearance(target.get("translit") or ""):
                    target["translit"] = ""
                    changed = True
        for field in ("etym", "anc", "url"):
            if row.get(field) and not target.get(field):
                target[field] = row[field]
                changed = True
        if row.get("anc") and "wiktionary" not in (target.get("sources") or []):
            target["sources"] = sorted(set(target.get("sources") or []) | {"wiktionary"})
            changed = True
        filled += 1 if changed else 0
    out = list(have.values())
    lexicon.parent.mkdir(parents=True, exist_ok=True)
    tmp = lexicon.with_suffix(".tmp")
    with tmp.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for row in out:
            gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
    tmp.replace(lexicon)
    return len(out), filled, appended


APPARATUS = re.compile(r"[<>|\\=~]|\b(?:M|N|A|Abk|Av)\b")


def appearance(text: str) -> bool:
    """Whether a stored transliteration is dictionary apparatus, not a form."""
    return bool(APPARATUS.search(text)) or len((text or "").split()) > 1


INVISIBLE = "\u2060\u200b\u200c\u200d\ufeff"


def visible(text: str) -> str:
    """A reading without the joiners the wiki uses for rendering."""
    return "".join(ch for ch in (text or "") if ch not in INVISIBLE)


def fold(text: str) -> str:
    text = (text or "").lower().replace("γ", "g")
    text = re.sub(r"[ˈˌ*?’']", "", text)
    for a, b in (("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u"), ("ā", "a"),
                 ("ğ", "g"), ("ǰ", "j"), ("š", "s"), ("ž", "z"), ("č", "c"),
                 ("ǣ", "a")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", text)


BRACKET = re.compile(r"^[^/]*\s*/\s*([^/]+?)\s*/?\s*$")


def reading_layer(value: str) -> str:
    """The reading a page states, out of the way the page prints it.

    Old Persian pages put the signs and the reading in one field
    (``h-i-n-a /hainā/``): the signs are a transliteration of the cuneiform and
    the slashes hold the reading.  An entry's ``translit`` is the reading
    layer, so the bracket is reduced to it at merge time — otherwise every
    emit re-introduced the bracket a clean had removed.  A placeholder
    (``-``, ``—``, ``?``) is no reading at all (2026-11-12).
    """
    value = (value or "").strip()
    found = BRACKET.match(value)
    if found:
        return found.group(1).strip()
    return "" if value in {"-", "—", "?"} else value


def clean_readings(rows: list[dict]) -> int:
    """Reduce a reading written as a bracket to the reading it holds."""
    fixed = 0
    for row in rows:
        value = row.get("translit") or ""
        if not value:
            continue
        tidy = reading_layer(value)
        if tidy != value:
            row["translit"] = tidy
            fixed += 1
    return fixed


def refresh_from(lexicon: Path, rows: list[dict]) -> int:
    """Re-read the fields this tool wrote, for rows it can identify.

    The ledger is the evidence and the lexicon is a merge of it; when the
    renderer that turns a template into a sentence is repaired, the stored
    sentences stay as the old one left them, because ``emit`` never overwrites
    a field.  A row whose *source* is this tool is safe to refresh: its
    etymology, ancestry and URL are the ledger's, not a dictionary's
    (2026-11-12: xpr "From xpr ira-pro." was the renderer's old output).
    """
    by_key: dict[str, dict] = {}
    for row in rows:
        for key in (row.get("title"), row.get("word"), row.get("translit")):
            folded = fold(key or "")
            if folded:
                by_key.setdefault(folded, row)
    with gzip.open(lexicon, "rt", encoding="utf-8") as fh:
        stored = [json.loads(line) for line in fh if line.strip()]
    fixed = 0
    for row in stored:
        if "wiktionary" not in (row.get("sources") or []):
            continue
        source = next((by_key.get(fold(k or "")) for k in
                       (row.get("word"), row.get("phon"), row.get("translit"))
                       if fold(k or "")), None)
        if not source:
            continue
        changed = False
        for field in ("etym", "url"):
            if source.get(field) and row.get(field) != source[field]:
                row[field] = source[field]
                changed = True
        # Ancestry is merged, never replaced: a row can carry links from a
        # second source (the curated Old Persian supplement), and a refresh
        # that overwrote them dropped five words out of the count (2026-11-12).
        # A stored link whose form still carries template markup
        # (``Idiglat<alt:…><id:Tigris>``) is not a word the record states: an
        # older reader wrote it, and merging kept it beside the clean link the
        # reader now produces, so the entry said its ancestor twice.
        merged = list(source.get("anc") or [])
        for link in row.get("anc") or []:
            if len(link) > 1 and "<" in str(link[1]):
                changed = True
                continue
            if link not in merged:
                merged.append(link)
        if merged and row.get("anc") != merged:
            row["anc"] = merged
            changed = True
        fixed += 1 if changed else 0
    if fixed:
        write_rows(lexicon, stored)
    return fixed


def cmd_tidy(args) -> int:
    """Rewrite the stored etymology prose of rows this tool wrote."""
    lexicon = Path(args.out) if getattr(args, "out", None) else ROOT / "data" / "lexicon" / f"{args.lang}.jsonl.gz"
    with gzip.open(lexicon, "rt", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    fixed = 0
    for row in rows:
        if row.get("source") != "wiktionary" or not row.get("etym"):
            continue
        tidy = tidy_etym(row["etym"])
        if tidy != row["etym"]:
            row["etym"] = tidy
            fixed += 1
    if fixed:
        write_rows(lexicon, rows)
    print(f"{args.lang}: {fixed} etymologies tidied")
    return 0


def cmd_emit(args) -> int:
    rows = read_ledger(args.lang)
    lexicon = Path(args.out) if args.out else ROOT / "data" / "lexicon" / f"{args.lang}.jsonl.gz"
    total, filled, appended = merge_into(lexicon, list(rows.values()))
    if args.clean:
        with gzip.open(lexicon, "rt", encoding="utf-8") as fh:
            stored = [json.loads(line) for line in fh if line.strip()]
        fixed = clean_readings(stored)
        write_rows(lexicon, stored)
        print(f"{args.lang}: {fixed} readings cleaned from a dictionary bracket")
    if getattr(args, "refresh", False):
        fixed = refresh_from(lexicon, list(rows.values()))
        print(f"{args.lang}: {fixed} rows refreshed from the ledger")
    print(f"{args.lang}: {total} entries → {lexicon} "
          f"({filled} rows filled, {appended} appended)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="read a lemma category into the ledger")
    f.add_argument("lang")
    f.add_argument("--category", action="append", required=True)
    f.add_argument("--language", required=True)
    f.add_argument("--cache", default="/tmp/wikt-lemmas-cache.json")
    f.add_argument("--limit", type=int, default=0)
    f.add_argument("--depth", type=int, default=1,
                   help="how many levels of subcategories to follow")
    f.add_argument("--verbose", action="store_true")
    f.add_argument("--recheck", action="append", metavar="TITLE",
                   help="read these pages again even though the ledger has them")
    f.set_defaults(func=cmd_fetch)
    s = sub.add_parser("status", help="what the ledger holds")
    s.add_argument("lang")
    s.set_defaults(func=cmd_status)
    c = sub.add_parser("tidy", help="strip empty brackets a dropped template left in etym")
    c.add_argument("lang")
    c.set_defaults(func=cmd_tidy)
    e = sub.add_parser("emit", help="fill and extend the glossary from the ledger")
    e.add_argument("lang")
    e.add_argument("--out")
    e.add_argument("--refresh", action="store_true",
                   help="rewrite etym/anc/url of wiktionary rows from the ledger")
    e.add_argument("--clean", action="store_true",
                   help="reduce a stored bracket to the reading it holds")
    e.set_defaults(func=cmd_emit)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
