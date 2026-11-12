#!/usr/bin/env python3
"""Build a glossary for a language that kaikki.org does not publish.

Wiktionary has lemma categories for languages such as Avestan and Middle Persian
that are not in the kaikki dumps.  This tool walks the category tree, fetches the
wikitext in batches, and extracts the definitions of the requested language
section:

    python tools/fetch_wiktionary.py ave --category "Avestan lemmas"
    python tools/fetch_wiktionary.py pal --category "Middle Persian lemmas" --append
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://en.wiktionary.org/w/api.php"
UA = "pie-etymology-build/0.1 (https://github.com/adoosth/pie; adoosth@gwdg.de)"


def api(params: dict, tries: int = 6) -> dict:
    params = {"format": "json", "formatversion": "2", **params}
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                time.sleep(0.4)
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = 5 * (attempt + 1)
                print(f"429, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("too many 429 responses")


def category_pages(category: str, depth: int = 2) -> list[str]:
    pages: list[str] = []
    seen: set[str] = set()
    queue = [(category if category.startswith("Category:") else "Category:" + category, depth)]
    while queue:
        cat, d = queue.pop()
        cont: dict = {}
        while True:
            data = api({"action": "query", "list": "categorymembers", "cmtitle": cat,
                        "cmlimit": "500", **cont})
            for row in data.get("query", {}).get("categorymembers", []):
                title = row["title"]
                if row["ns"] == 14:
                    if d > 0 and title not in seen:
                        seen.add(title)
                        queue.append((title, d - 1))
                elif title not in seen:
                    seen.add(title)
                    pages.append(title)
            cont = data.get("continue") or {}
            if not cont:
                break
        time.sleep(0.3)
    return pages


SECTION = re.compile(r"^==+\s*([^=\n]+?)\s*==+\s*$", re.M)


def language_section(text: str, language: str) -> str | None:
    m = re.search(r"^==\s*" + re.escape(language) + r"\s*==\s*$", text, re.M | re.I)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^==\s*[^=].*?==\s*$", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def parse_definitions(wikitext: str, language: str) -> list[str]:
    section = language_section(wikitext, language)
    if not section:
        return []
    out = []
    for line in section.splitlines():
        if line.startswith("#") and not line.startswith("#*") and not line.startswith("#:"):
            body = line.lstrip("#").strip()
            body = re.sub(r"\{\{[^{}]*\}\}", "", body)
            body = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", body)
            body = re.sub(r"<[^>]+>", "", body)
            body = re.sub(r"''+", "", body).strip(" ,;.")
            if body and len(body) > 1:
                out.append(body)
        if len(out) >= 3:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("--category", required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--append", action="store_true", help="merge into an existing lexicon file")
    ap.add_argument("--out", help="output .jsonl.gz path (default data/lexicon/<lang>.jsonl.gz)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    pages: list[str] = []
    for cat in args.category.split(","):
        for page in category_pages(cat):
            if page not in pages:
                pages.append(page)
    if args.limit:
        pages = pages[: args.limit]
    print(f"{len(pages)} pages in {args.category}", file=sys.stderr)

    out_path = Path(args.out) if args.out else ROOT / "data" / "lexicon" / f"{args.lang}.jsonl.gz"
    records: dict[str, dict] = {}
    if args.append and out_path.exists():
        with gzip.open(out_path, "rt", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                records[row["word"]] = row

    for i in range(0, len(pages), 50):
        batch = pages[i : i + 50]
        data = api({"action": "query", "prop": "revisions", "rvprop": "content",
                    "rvslots": "main", "titles": "|".join(batch)})
        for page in data.get("query", {}).get("pages", []):
            title = page.get("title", "")
            revs = page.get("revisions") or []
            if not revs:
                continue
            content = revs[0]["slots"]["main"].get("content", "")
            glosses = parse_definitions(content, args.language)
            if not glosses:
                continue
            joined = " ".join(glosses).lower()
            if any(k in joined for k in ("letter of", "consonant used", "vowel used", "of the avestan alphabet")):
                continue
            rec = {"word": title, "lang": args.lang, "pos": "", "gloss": glosses,
                   "source": "wiktionary"}
            section = language_section(content, args.language) or ""
            tr = re.search(r"\|\s*tr\s*=\s*([^|}]+)", section)
            if tr:
                rec["translit"] = tr.group(1).strip()
            records[title] = rec
        time.sleep(0.3)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        for row in records.values():
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(records)} entries → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
