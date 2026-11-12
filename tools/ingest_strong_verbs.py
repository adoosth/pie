#!/usr/bin/env python3
"""Read the Proto-Germanic strong-verb inventory into the model.

The list is Wikipedia's "Germanic strong verb" article, which prints the roots
of the seven classes after Seebold (1970), Mailhammer (2007) and Kroonen
(2013).  The article gives the roots and their class, not their meanings, so an
entry written from it carries the citation and the class and claims no sense; a
root whose Wiktionary page exists (``Reconstruction:Proto-Germanic/<verb>``)
also carries that page's glosses, its etymology sentence, its IPA and the
Proto-Indo-European root it names.

    python tools/ingest_strong_verbs.py --fetch
    python tools/ingest_strong_verbs.py --wiki gsv.wiki --pages pages.json
    python tools/ingest_strong_verbs.py --write      # fold into the supplement

Nothing is overwritten: a word the glossary already has is reported, not
rewritten, and the supplement keeps every row this tool did not write.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPP = ROOT / "data" / "lexicon" / "_supplement" / "gem-pro.jsonl.gz"
BUILT = ROOT / "data" / "lexicon" / "gem-pro.jsonl.gz"
UA = "pie-project/0.1 (educational reconstruction database; adoosth/pie)"
WIKI_URL = "https://en.wikipedia.org/wiki/Germanic_strong_verb"
SOURCE = "wikipedia-strong-verb"

CLASS_RE = re.compile(r"^\s*[:*]+\s*(?:Class\s*)?(?P<cls>[1-7][a-e]?)\b")
NOTE_RE = re.compile(r"^\s*::?\s*(?P<note>[A-Z][^:]{2,40}?)\s*roots?:", re.I)
LANG_NAMES = {"ine-pro": "Proto-Indo-European", "gem-pro": "Proto-Germanic",
              "gmw-pro": "Proto-West Germanic", "gem": "Germanic"}

WORD_RE = re.compile(r"\{\{[Ww]ikt-lang\|gem-pro\|(\*[^|}]+)")
BARE_RE = re.compile(r"(?<![\|{\w])\*([A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u0300-\u036F\u207F]+)")


def read_wiki(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("\n==Proto-Germanic==")
    end = text.index("\n==Gothic==")
    return text[start:end]


def inventory(text: str) -> list[dict]:
    """Every root of the article's Proto-Germanic list, with its class."""
    out: list[dict] = []
    seen: set[str] = set()
    cls, note = "", ""
    for line in text.splitlines():
        m = CLASS_RE.match(line)
        if m and ("roots" in line or "Class" in line):
            cls = m.group("cls")
        if not line.strip().startswith(("*", ":")):
            continue
        # A sub-label names the roots *on its own line* ("Aorist-present
        # roots: *murnaną, *spurnaną"), never the class as a whole.
        n = NOTE_RE.search(line)
        note = n.group("note").strip().lower() if n else ""
        for token in WORD_RE.findall(line) + BARE_RE.findall(line):
            word = token.lstrip("*").strip()
            if not word.endswith("aną") or len(word) < 5 or word in seen:
                continue
            seen.add(word)
            out.append({"word": word, "class": cls, "note": note})
    return out


def strip_links(s: str) -> str:
    s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = s.replace("'''", "").replace("''", "")
    return s


def render_templates(s: str) -> str:
    """A sentence a reader can use: the few templates that name a word."""
    def one(m: re.Match) -> str:
        parts = m.group(1).split("|")
        head = parts[0].strip().lower()
        if head in ("der", "inh", "bor", "bor+", "lbor", "calque", "der+"):
            code = (parts[2] if len(parts) > 2 else "").strip()
            form = next((p for p in parts[3:] if p.startswith("*")), "")
            t = next((p for p in parts[3:] if p and not p.startswith("*") and "=" not in p), "")
            name = LANG_NAMES.get(code, code)
            if not form:
                form, t = t, ""
            body = f"{form} (“{t}”)" if t else form
            return f"{name} {body}".strip()
        if head in ("m", "m+", "l", "l+", "cog", "cognate"):
            code = (parts[1] if len(parts) > 1 else "").strip()
            form = (parts[2] if len(parts) > 2 else "").strip()
            t = (parts[3] if len(parts) > 3 else "").strip()
            t = t[2:] if t.startswith("t=") else t
            if form in ("", "-", "—"):
                # A bare language ({{cog|ine-pro|-}}) names the family, not a word.
                return LANG_NAMES.get(code, "")
            return f"{form} (“{t}”)" if t and not t.startswith("*") else form
        if head in ("q", "qualifier", "lb", "label", "gloss"):
            return ""
        if head in ("unk", "unc", "rfe", "onomatopoeia", "root"):
            return ""
        if head == "w":
            return parts[1] if len(parts) > 1 else ""
        return ""
    s = re.sub(r"\{\{([^{}]*)\}\}", lambda m: one(m), s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\s+([,;.:])", r"\1", s)
    s = re.sub(r"([,;:])\s*([,;:.])", r"\2", s)
    s = s.replace(" of, from ", " of ")
    return s.strip(" ;,.:")


def parse_page(text: str, lang: str = "gem-pro") -> dict:
    """Glosses, etymology, IPA and the PIE ancestors a Wiktionary page states."""
    out: dict = {"gloss": [], "etym": "", "ipa": "", "anc": [], "head": "",
                 "title": ""}
    if not text:
        return out
    heads = re.findall(r"^==([^=]+)==\s*$", text, flags=re.M)
    if heads:
        out["head"] = heads[-1].strip()
    etym = re.search(r"^===Etymology===\s*\n(.+?)(?:\n===|\Z)", text, flags=re.M | re.S)
    unsure = False
    if etym:
        raw = etym.group(1)
        # A page that says the origin is unknown has no ancestor to record:
        # three rival roots are a question, not a parent (2026-11-12).
        unsure = bool(re.search(r"\{\{(unk|unc|rfe|uncertain)", raw, flags=re.I))
        out["etym"] = render_templates(strip_links(raw)).strip()
    verb = re.search(r"^===Verb===\s*\n(.+?)(?:\n===|\Z)", text, flags=re.M | re.S)
    if verb:
        for line in verb.group(1).splitlines():
            if not line.startswith("# "):
                continue
            gloss = render_templates(strip_links(line[2:]))
            gloss = re.sub(r"^\([^)]*\)\s*", "", gloss).strip(" .")
            if gloss:
                out["gloss"].append(gloss)
    ipa = re.search(r"\{\{IPA\|gem-pro\|/([^/}]+)/", text)
    if ipa:
        out["ipa"] = f"/{ipa.group(1)}/"
    if not unsure:
        for kind, arg in re.findall(r"\{\{(inh|der)\|gem-pro\|ine-pro\|(\*[^|}]+)", text):
            row = ["ine-pro", arg.strip(), "inherit" if kind == "inh" else "derive"]
            if row not in out["anc"]:
                out["anc"].append(row)
        if len(out["anc"]) > 1:
            # One parent per word: a page that offers rivals records none.
            out["anc"] = []
    return out


def fetch_wiki() -> str:
    url = "https://en.wikipedia.org/w/index.php?title=Germanic_strong_verb&action=raw"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as fh:
        return fh.read().decode("utf-8")


def fetch_pages(words: list[str]) -> dict:
    """Wiktionary's reconstruction pages, forty at a time.

    A redirect is followed (``dīganą`` → ``diganą``): the payload keeps the
    title that was actually read, so the citation links to a page that exists.
    """
    out: dict[str, dict] = {}
    for i in range(0, len(words), 40):
        chunk = words[i:i + 40]
        q = {"action": "query", "prop": "revisions", "rvprop": "content",
             "rvslots": "main", "format": "json", "formatversion": "2",
             "redirects": "1",
             "titles": "|".join(f"Reconstruction:Proto-Germanic/{w}" for w in chunk)}
        url = "https://en.wiktionary.org/w/api.php?" + urllib.parse.urlencode(q)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as fh:
            data = json.loads(fh.read().decode("utf-8"))
        read: dict[str, str] = {}
        for page in data.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            revs = page.get("revisions") or []
            title = page.get("title", "").split("/")[-1]
            if revs:
                read[title] = revs[0]["slots"]["main"]["content"]
        for page in data.get("query", {}).get("pages", []):
            title = page.get("title", "").split("/")[-1]
            if title in read:
                out[title] = {"title": title, "text": read[title]}
        for link in data.get("query", {}).get("redirects", []):
            src = link.get("from", "").split("/")[-1]
            dst = link.get("to", "").split("/")[-1]
            if dst in read:
                out[src] = {"title": dst, "text": read[dst]}
        time.sleep(1.0)
    return out


def words_without_pie_ancestor(inventory_words: list[str]) -> list[str]:
    """Strong verbs the glossary holds but whose row names no PIE ancestor."""
    rows: dict[str, list[dict]] = {}
    if not BUILT.exists():
        return []
    with gzip.open(BUILT, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows.setdefault(row["word"], []).append(row)
    out = []
    for word in inventory_words:
        held = rows.get(word)
        if not held:
            continue
        if any(link and link[0] == "ine-pro" for r in held for link in (r.get("anc") or [])):
            continue
        out.append(word)
    return out


ALT_RE = re.compile(r"\{\{(?:alt form|alternative form of|alternative spelling of)\|gem-pro\|(\*[^|}]+)")


def alt_base(text: str) -> str:
    """The word a page calls itself an alternative form of, if it does."""
    head = text.split("===Descendants===", 1)[0]
    m = ALT_RE.search(head)
    return m.group(1).lstrip("*").strip() if m else ""


def ancestor_rows(pages: dict, words: list[str]) -> list[dict]:
    """Supplement rows that only add a PIE link to a word already in the file.

    Nothing else is written — no gloss (it would be appended to the entry's
    own), no `ref` (it would replace the sentence the entry rests on).
    """
    out = []
    for word in words:
        found = pages.get(word) or {}
        text = found.get("text", "") if isinstance(found, dict) else ""
        parsed = parse_page(text)
        via = ""
        if not parsed["anc"]:
            # *būganą* is "an alternative form of *beuganą*": a variant wears
            # its base's origin, and the base's page states it (2026-11-12).
            base = alt_base(text)
            if base and base != word:
                other = pages.get(base) or {}
                if isinstance(other, dict) and other.get("text"):
                    inherited = parse_page(other["text"])
                    if inherited["anc"]:
                        parsed = inherited
                        via = base
        if not parsed["anc"]:
            continue
        note = ("Proto-Indo-European ancestor from the word's Wiktionary "
                "reconstruction page.")
        if via:
            note = (f"Proto-Indo-European ancestor of {via}, whose alternative form "
                    f"this word is (its own Wiktionary page).")
        out.append({"word": word, "lang": "gem-pro", "anc": parsed["anc"],
                    "sources": ["wiktionary"], "source_note": note})
    return out


def existing_words() -> set[str]:
    words: set[str] = set()
    for path in (BUILT, SUPP):
        if not path.exists():
            continue
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    words.add(json.loads(line)["word"])
    return words


def build_rows(entries: list[dict], pages: dict) -> tuple[list[dict], dict]:
    rows, report = [], {"with_wiktionary": [], "without": []}
    for entry in entries:
        word = entry["word"]
        found = pages.get(word) or {}
        page = found.get("text", "") if isinstance(found, dict) else str(found or "")
        page_title = found.get("title", "") if isinstance(found, dict) else ""
        parsed = parse_page(page)
        cls = entry["class"]
        where = f"class {cls}" if cls else "the seven classes"
        if entry.get("note"):
            where += f", {entry['note']} root"
        etym = parsed["etym"]
        gloss = parsed["gloss"]
        row = {
            "word": word,
            "lang": "gem-pro",
            "pos": "verb",
            "gloss": gloss,
            "source": SOURCE,
            "ref": (f"Wikipedia, Germanic strong verb, Proto-Germanic list: {where} "
                    "(after Seebold 1970, Mailhammer 2007, Kroonen 2013)"),
            "strong_class": cls,
        }
        if parsed["head"] and parsed["head"] != "Proto-Germanic":
            row["ref"] += (f"; its Wiktionary page is {parsed['head']} "
                           f"({page_title or word})")
        if etym:
            row["etym"] = etym
        if parsed["ipa"]:
            row["ipa"] = parsed["ipa"]
        if parsed["anc"]:
            row["anc"] = parsed["anc"]
        if page:
            row["sources"] = ["wiktionary"]
            row["url"] = ("https://en.wiktionary.org/wiki/Reconstruction:"
                          f"Proto-Germanic/{page_title or word}")
            report["with_wiktionary"].append(word)
        else:
            row["url"] = WIKI_URL
            report["without"].append(word)
        rows.append(row)
    return rows, report


def write_supplement(rows: list[dict]) -> tuple[int, int]:
    have: dict[str, dict] = {}
    order: list[str] = []
    if SUPP.exists():
        with gzip.open(SUPP, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row["word"] not in have:
                    order.append(row["word"])
                have[row["word"]] = row
    added = 0
    for row in rows:
        if row["word"] in have:
            continue
        have[row["word"]] = row
        order.append(row["word"])
        added += 1
    if not added:
        return 0, len(rows)
    tmp = SUPP.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as fh:
        for word in order:
            fh.write(json.dumps(have[word], ensure_ascii=False, sort_keys=False) + "\n")
    tmp.replace(SUPP)
    return added, len(rows) - added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", default="/tmp/gsv.wiki")
    ap.add_argument("--pages", default="/tmp/pgmc_pages.json")
    ap.add_argument("--fetch", action="store_true", help="download the article and the pages")
    ap.add_argument("--write", action="store_true", help="fold the rows into the supplement")
    ap.add_argument("--all", action="store_true", help="write every root, not only the missing")
    ap.add_argument("--ancestors", action="store_true",
                    help="also add the PIE link Wiktionary records to the strong verbs "
                         "the glossary already holds without one")
    args = ap.parse_args()

    if args.fetch:
        text = fetch_wiki()
        Path(args.wiki).write_text(text, encoding="utf-8")
        words = [e["word"] for e in inventory(read_wiki(Path(args.wiki)))]
        words = [w for w in words if w not in existing_words()]
        pages = fetch_pages(words)
        Path(args.pages).write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")

    entries = inventory(read_wiki(Path(args.wiki)))
    have = existing_words()
    if not args.all:
        entries = [e for e in entries if e["word"] not in have]
    pages = json.loads(Path(args.pages).read_text(encoding="utf-8")) if Path(args.pages).exists() else {}
    rows, report = build_rows(entries, pages)
    print(f"roots in the article: {len(entries)}; already in the glossary: {len(have)}")
    print(f"rows to write: {len(rows)}")
    print(f"with a Wiktionary page: {len(report['with_wiktionary'])} "
          f"({', '.join(report['with_wiktionary'])})")
    print(f"without one: {len(report['without'])}")
    if args.ancestors:
        known = [e["word"] for e in inventory(read_wiki(Path(args.wiki)))]
        bare = words_without_pie_ancestor(known)
        print(f"strong verbs with no PIE ancestor in the glossary: {len(bare)}")
        pages = json.loads(Path(args.pages).read_text(encoding="utf-8")) if Path(args.pages).exists() else {}
        missing_pages = [w for w in bare if w not in pages]
        if args.fetch and missing_pages:
            pages.update(fetch_pages(missing_pages))
        if args.fetch:
            # One more round for the bases the alternative-form pages name.
            bases = {alt_base((pages.get(w) or {}).get("text", "")) for w in bare
                     if isinstance(pages.get(w), dict)}
            need = [b for b in bases if b and b not in pages]
            if need:
                pages.update(fetch_pages(need))
            Path(args.pages).write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        links = ancestor_rows(pages, bare)
        print(f"a Wiktionary page names an ancestor for: {len(links)}")
        if args.write and links:
            added, skipped = write_supplement(links)
            print(f"ancestry supplement: {added} written, {skipped} already present")
    if args.write:
        added, skipped = write_supplement(rows)
        print(f"supplement: {added} added, {skipped} already present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
