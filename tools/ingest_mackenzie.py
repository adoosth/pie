#!/usr/bin/env python3
"""Turn the Docling Markdown of MacKenzie's Concise Pahlavi Dictionary into a
Middle Persian glossary.

    python tools/docling_convert.py "A Concise Pahlavi Dictionary.pdf" -o mackenzi.md
    python tools/ingest_mackenzie.py mackenzi.md

Entries in the converted text look like

    - abag [LWTE < A Iwt-h | M y ygt N (a) d] with.

i.e. headword, a bracketed block with the Pahlavi transliteration and its
cognates, then the English gloss.

**The dictionary records no ancestor.**  MacKenzie's bracket gives the Pahlavi
spelling, the Aramaic logogram a heterogram is written with (`< A …`) and the
Manichaean, Parthian and New Persian forms beside it (`= Av.` for a learned
loan) — but not one entry states an Old Persian or Proto-Iranian etymon, so a
plain rerun can add no `anc` link (2026-11-09: 0 of 616 rows carried one;
the two that did came from Wiktionary, not from this file).  `--ancestry`
therefore joins each entry to the Wiktionary Middle Persian page its own
transcription identifies — the transcription is the dictionary's reading, the
page states its inheritance as `{{inh|pal|peo|…}}` templates and usually cites
this very dictionary (`{{R:pal:Mackenzie|page=…}}`) — and copies those links
with the page as the locator.  Nothing is inferred: an entry that finds no page
stating an ancestor keeps none.
"""
from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENTRY = re.compile(r"^-\s*(?P<word>[A-Za-zāēīōūšžčǰñ'’()\-\s]+?)\s*\[(?P<rest>[^\]]*)\]\s*(?P<gloss>.+)$")
SUB = re.compile(r"^-\s*~(?P<suffix>[A-Za-zāēīōūšžčǰñ'’()\-]+?)\s*:\s*(?P<gloss>.+)$")

#: Wiktionary's ancestry templates, and the relation each one records.  Only
#: these are copied into ``anc``: ``der``/``root`` name a derivation base or a
#: root, not the word's etymon, so they are deliberately left out.
ANCESTRY = {
    "inh": "inherit", "inh+": "inherit", "inherited": "inherit",
    "bor": "borrow", "bor+": "borrow", "borrowed": "borrow",
    "lbor": "borrow", "slbor": "borrow", "obor": "borrow",
}
WIKI_API = "https://en.wiktionary.org/w/api.php"
WIKI_UA = "pie-etymology-build/0.1 (https://github.com/adoosth/pie; adoosth@gwdg.de)"


def clean(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<")
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ,;.")
    return text


def parse(path: Path) -> list[dict]:
    rows: list[dict] = []
    started = False
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## A"):
            started = True
            continue
        if not started or not line.startswith("- "):
            continue
        if "Downloaded by" in line or line.startswith("- ["):
            continue
        sub = SUB.match(line)
        if sub:
            if current:
                rows.append({
                    "word": sub.group("suffix"),
                    "lang": "pal",
                    "pos": "noun",
                    "gloss": [clean(sub.group("gloss"))],
                    "source": "mackenzie-1971",
                    "derived_from": current["word"],
                })
            continue
        m = ENTRY.match(line)
        if not m:
            continue
        word = clean(m.group("word"))
        gloss = clean(m.group("gloss"))
        if not re.fullmatch(r"[A-Za-zāēīōūšžčǣñ'’]{2,20}(?:[- ][A-Za-zāēīōūšžčǣñ'’]{1,20})?", word):
            continue
        if len(gloss) < 2 or word.lower() in {"read", "delete", "add", "for", "see", "cf"}:
            continue
        if re.match(r"^(read|for \d|add|delete|which|the |cf\.)", gloss, re.I):
            continue
        rest = clean(m.group("rest"))
        entry = {
            "word": word,
            "lang": "pal",
            "pos": "",
            "gloss": [gloss],
            "source": "mackenzie-1971",
            "translit": rest,
        }
        rows.append(entry)
        current = entry
    return rows


# ---- the ancestry join ----------------------------------------------------
def _templates(text: str):
    """Every ``{{…}}`` in ``text``, outermost only (nested ones come with it)."""
    i = 0
    while True:
        start = text.find("{{", i)
        if start < 0:
            return
        depth = 0
        j = start
        while j < len(text):
            if text.startswith("{{", j):
                depth += 1
                j += 2
                continue
            if text.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
                continue
            j += 1
        yield text[start + 2:j - 2]
        i = j


def _params(inner: str) -> list[str]:
    """Split a template's body on top-level ``|``, keeping nested markup whole."""
    out: list[str] = []
    depth = 0
    cur: list[str] = []
    i = 0
    while i < len(inner):
        pair = inner[i:i + 2]
        if pair in {"{{", "[["}:
            depth += 1
            cur.append(pair)
            i += 2
            continue
        if pair in {"}}", "]]"}:
            depth -= 1
            cur.append(pair)
            i += 2
            continue
        if inner[i] == "|" and depth == 0:
            out.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(inner[i])
        i += 1
    out.append("".join(cur))
    return [part.strip() for part in out]


def _fold(text: str) -> str:
    """Letters only, macrons and Pahlavi-dictionary diacritics folded away.

    The join key is a *spelling* key, not a phonological one: MacKenzie's
    transcription and Wiktionary's differ in notation (γ for ğ, ē for e), and a
    row must find the page that discusses the same word.
    """
    text = text.replace("γ", "g").lower()
    text = re.sub(r"[ˈˌ*?]", "", text)
    for a, b in (("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u"), ("ā", "a"),
                 ("ğ", "g"), ("č", "c"), ("ǰ", "j"), ("š", "s"), ("ǣ", "a")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z]", "", text)


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", (text or "").lower()) if len(w) > 2}


def middle_persian_section(text: str) -> str | None:
    m = re.search(r"^==\s*Middle Persian\s*==\s*$", text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    n = re.search(r"^==[^=]", rest, re.M)
    return rest[:n.start()] if n else rest


def headword_reading(section: str) -> str:
    """The transcription (``tr``/``ts``) on the section's own head template."""
    for tpl in _templates(section):
        parts = _params(tpl)
        if not parts or not (parts[0] == "head" or parts[0].startswith("pal-")):
            continue
        for part in parts[1:]:
            if part.startswith(("tr=", "ts=")):
                return clean(part.split("=", 1)[1])
        return ""
    return ""


def etymology_links(body: str) -> list[list[str]]:
    """The inheritance and borrowing links a Wiktionary etymology states."""
    out: list[list[str]] = []
    for tpl in _templates(body or ""):
        parts = _params(tpl)
        if not parts:
            continue
        name = parts[0]
        if name in ANCESTRY and len(parts) > 3:
            lang, form = parts[2], parts[3]
            if lang and form and lang != "pal" and "=" not in lang and not form.startswith("sc="):
                out.append([lang, form, ANCESTRY[name]])
        elif name in {"etymon", "ety"}:
            i = 1
            while i < len(parts) - 1:
                marker = parts[i]
                if marker in {":inh", ":bor"} and ":" in parts[i + 1]:
                    lang, form = parts[i + 1].split(":", 1)
                    out.append([lang, re.split(r"[<]", form)[0],
                                "inherit" if marker == ":inh" else "borrow"])
                    i += 2
                    continue
                i += 1
    seen: set[tuple[str, str, str]] = set()
    links: list[list[str]] = []
    for lang, form, rel in out:
        form = clean(form)
        key = (lang, _fold(form), rel)
        if not form or key in seen:
            continue
        seen.add(key)
        links.append([lang, form, rel])
    return links


def mackenzie_citation(section: str) -> str | None:
    """The page of *this* dictionary a Wiktionary entry cites, if it cites one."""
    for tpl in _templates(section):
        parts = _params(tpl)
        if not parts or not parts[0].startswith("R:pal:Mackenzie"):
            continue
        head = next((p for p in parts[1:] if "=" not in p), "")
        page = next((p.split("=", 1)[1] for p in parts[1:] if p.startswith("page=")), "")
        if head or page:
            return f"{head}{', p. ' + page if page else ''}".strip(", ")
    return None


def fetch_wikitext(titles: list[str], cache: Path | None) -> dict[str, str]:
    """Middle Persian wikitext for ``titles``, batched, with a local cache."""
    out: dict[str, str] = {}
    if cache and cache.exists():
        out = json.loads(cache.read_text(encoding="utf-8"))
    todo = [t for t in titles if t not in out]
    for start in range(0, len(todo), 20):
        batch = todo[start:start + 20]
        params = {"format": "json", "formatversion": "2", "action": "query",
                  "prop": "revisions", "rvprop": "content", "rvslots": "main",
                  "titles": "|".join(batch), "redirects": 1}
        url = WIKI_API + "?" + urllib.parse.urlencode(params)
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": WIKI_UA})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 429:
                    raise
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError("Wiktionary kept answering 429")
        for page in data.get("query", {}).get("pages", []):
            text = ""
            if page.get("revisions"):
                text = page["revisions"][0]["slots"]["main"]["content"]
            out[page["title"]] = text
        for title in batch:
            out.setdefault(title, "")
        if cache:
            cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.8)
    return out


def attach_ancestry(rows: list[dict], wikitext: dict[str, str]) -> tuple[int, int]:
    """Give each row the ancestry the Wiktionary page for its transcription records."""
    pages: dict[str, dict] = {}
    for title, text in wikitext.items():
        if title.startswith(("Category:", "Reconstruction:", "Template:", "-")):
            continue
        section = middle_persian_section(text)
        if section is None:
            continue
        headword = re.search(r"^===\s*(?:Noun|Verb|Adjective|Adverb|Pronoun|Numeral|Preposition|"
                             r"Proper noun|Conjunction|Particle|Interjection)\s*===", section, re.M)
        pages[title] = {
            "tr": headword_reading(section),
            "section": section,
            "ety": "",
            "headword": bool(headword),
        }
        et = re.search(r"===+\s*Etymology[^=]*===+\s*\n(.*?)(?=\n===|\Z)", section, re.S)
        if et:
            pages[title]["ety"] = et.group(1)
    by_tr: dict[str, str] = {}
    by_title: dict[str, str] = {}
    for title, row in pages.items():
        key = _fold(row["tr"])
        if key:
            by_tr.setdefault(key, title)
        by_title.setdefault(_fold(title), title)

    linked = peo_linked = 0
    for row in rows:
        key = _fold(row["word"])
        title = by_tr.get(key) or by_title.get(key)
        if not title:
            continue
        page = pages[title]
        # The gloss has to overlap: the same transcription can name two words,
        # and only the page that glosses this entry's sense may lend it an etymon.
        if not (_words(row["gloss"][0]) & _words(page["section"])):
            continue
        links = etymology_links(page["ety"])
        links = [link for link in links
                 if link[1] not in {"-", "—", "*"} and "/" not in link[1]
                 and "=" not in link[1]]
        if not links:
            continue
        row["anc"] = links
        row["sources"] = sorted({row.get("source") or "mackenzie-1971", "wiktionary"})
        row["url"] = "https://en.wiktionary.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        cited = mackenzie_citation(page["section"])
        ref = (f"en.wiktionary.org, Middle Persian {title}"
               f" (tr={page['tr']}): “{clean(page['ety'])[:240]}”")
        if cited:
            ref += f"; MacKenzie (1971) s.v. {cited}"
        elif row.get("source") == "mackenzie-1971":
            ref += f"; MacKenzie (1971) s.v. {row['word']}"
        row["ref"] = ref
        linked += 1
        if any(link[0] == "peo" for link in links):
            peo_linked += 1
    return linked, peo_linked


#: Fields a hand-curated supplement row owns and this parser does not produce.
CURATED = ("etym", "ref", "sources", "url", "anc", "ipa", "phon", "translit_alt")


def merge_curated(rows: list[dict], path: Path) -> list[dict]:
    """Keep hand-added rows and fields when the dictionary is re-ingested."""
    if not path.exists():
        return rows
    old: dict[str, dict] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            old[row.get("word", "")] = row
    fresh = {row["word"] for row in rows}
    out: list[dict] = []
    for row in rows:
        kept = old.get(row["word"])
        if kept:
            for field in CURATED:
                if kept.get(field) and not row.get(field):
                    row[field] = kept[field]
        out.append(row)
    for word, row in old.items():
        if word not in fresh:
            out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown", nargs="?")
    ap.add_argument("-o", "--out", default=str(ROOT / "data" / "lexicon" / "_supplement" / "pal.jsonl.gz"))
    ap.add_argument("--ancestry", action="store_true",
                    help="join every entry to the Wiktionary page its transcription names")
    ap.add_argument("--cache", default="/tmp/pal-wikitext.json",
                    help="wikitext cache the ancestry join reads and fills")
    ap.add_argument("--refetch", action="store_true", help="ignore the wikitext cache")
    ap.add_argument("--no-merge", action="store_true",
                    help="write only the parsed entries, dropping curated ones")
    ap.add_argument("--category", default="Category:Middle Persian lemmas",
                    help="category whose pages the ancestry join searches")
    args = ap.parse_args()

    out = Path(args.out)
    if args.markdown:
        rows = parse(Path(args.markdown))
        seen = {}
        for row in rows:
            seen.setdefault((row["word"], row["gloss"][0]), row)
        rows = list(seen.values())
    else:
        if not out.exists():
            ap.error("no markdown given and no glossary to update")
        rows = []
        with gzip.open(out, "rt", encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]

    if not args.no_merge:
        rows = merge_curated(rows, out)

    if args.ancestry:
        cache = None if args.refetch else Path(args.cache)
        wikitext = fetch_wikitext(category_titles(args.category), cache)
        linked, peo_linked = attach_ancestry(rows, wikitext)
        print(f"ancestry: {linked} of {len(rows)} entries name an etymon "
              f"({peo_linked} of them through Old Persian)")

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    # The gzip stamp is set to zero so a rerun of identical rows leaves the file
    # byte-identical (the same reason as tools/build_lexicons.py:_write_gzip).
    with tmp.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for row in rows:
            gz.write((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
    tmp.replace(out)
    print(f"{len(rows)} Middle Persian entries → {out}")
    for row in rows[:5]:
        print(" ", row["word"], "—", row["gloss"][0][:60])
    return 0


def category_titles(category: str) -> list[str]:
    """Every page in a Wiktionary category (subcategories not followed)."""
    titles: list[str] = []
    cont: dict = {}
    while True:
        params = {"format": "json", "formatversion": "2", "action": "query",
                  "list": "categorymembers", "cmtitle": category, "cmlimit": "500", **cont}
        url = WIKI_API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": WIKI_UA})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        titles += [row["title"] for row in data.get("query", {}).get("categorymembers", [])
                   if row["ns"] == 0]
        cont = data.get("continue") or {}
        if not cont:
            break
        time.sleep(0.3)
    return titles


if __name__ == "__main__":
    raise SystemExit(main())
