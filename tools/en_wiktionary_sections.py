#!/usr/bin/env python3
"""Check that an indexed page really has a section in the word's language.

`tools/en_wiktionary_index.py` reads the site's list of *titles*: a headword
present as a title is written to the ledger, and the word page draws the W for
it.  But a title is shared by every language — en.wiktionary's نقوع holds an
`==Arabic==` section and no Persian one at all — so a title match is not a
record of *this* word, and the icon lied (critic batch 01, 2026-11-13).

This pass asks the API for the page's wikitext in batches of 50 and records
whether the article carries a level-2 heading for the language the row names:

    python tools/en_wiktionary_sections.py --lang fa
    python tools/en_wiktionary_sections.py --lang fa --limit 200 --refresh

Each row gains ``"section": true|false`` and ``"section_checked": <date>``.
`src/pie/wiktionary.py` reads it: a row with ``section: false`` draws no W,
because the article records a homograph in another language, not this word.
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
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pie import data  # noqa: E402

OUT = ROOT / "data" / "sources" / "en_wiktionary"
API = "https://en.wiktionary.org/w/api.php"
UA = ("pie-lexicon/0.17 (https://github.com/adoosth/pie; source audit; "
      "contact adoosth@gwdg.de)")
HEADING = re.compile(r"^==\s*([^=\n]+?)\s*==\s*$", re.M)


def ledger_path(lang: str) -> Path:
    return OUT / f"{lang}.jsonl.gz"


def read_rows(lang: str) -> list[dict]:
    path = ledger_path(lang)
    if not path.exists():
        return []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_rows(lang: str, rows: list[dict]) -> None:
    path = ledger_path(lang)
    tmp = path.with_suffix(".tmp")
    body = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    tmp.write_bytes(gzip.compress(body.encode("utf-8"), mtime=0))
    tmp.replace(path)


def language_heading(lang: str) -> str:
    """The heading en.wiktionary uses for this language (Persian, Arabic…)."""
    name = data.language_name(lang) or lang
    return name.split(" (")[0].strip()


def fetch(titles: list[str]) -> dict[str, str]:
    """The wikitext of up to 50 pages, keyed by the title asked for."""
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "redirects": "1", "titles": "|".join(titles),
    })
    req = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as fh:
        payload = json.load(fh)
    out: dict[str, str] = {}
    for page in (payload.get("query") or {}).get("pages") or []:
        slots = ((page.get("revisions") or [{}])[0].get("slots") or {})
        content = (slots.get("main") or {}).get("content") or ""
        if page.get("title"):
            out[page["title"]] = content
    # Redirects: a title asked for may now live under another one.
    for item in (payload.get("query") or {}).get("redirects") or []:
        target = item.get("to")
        if target in out:
            out[item.get("from")] = out[target]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="fa")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true",
                    help="re-check rows that already carry section_checked")
    ap.add_argument("--batch", type=int, default=50)
    ap.add_argument("--sleep", type=float, default=0.15)
    args = ap.parse_args(argv)

    rows = read_rows(args.lang)
    heading = language_heading(args.lang)
    todo = [row for row in rows
            if row.get("status") == "found" and row.get("title")
            and (args.refresh or "section" not in row)]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(rows)} rows, {len(todo)} to check against '=={heading}=='")

    today = date.today().isoformat()
    by_title = {row.get("title"): row for row in rows}
    checked = 0
    for start in range(0, len(todo), args.batch):
        chunk = todo[start:start + args.batch]
        titles = [row["title"] for row in chunk]
        try:
            content = fetch(titles)
        except Exception as exc:  # a network hiccup must not lose the ledger
            print(f"  batch {start}: {exc}", file=sys.stderr)
            time.sleep(2)
            continue
        for row in chunk:
            text = content.get(row["title"])
            if text is None:
                # The title exists in the dump but the API has no page: no W.
                row["section"] = False
            else:
                heads = {m.group(1).strip() for m in HEADING.finditer(text)}
                row["section"] = heading in heads
            row["section_checked"] = today
            checked += 1
        print(f"  {checked}/{len(todo)} · {titles[0][:30]}…")
        time.sleep(args.sleep)
    write_rows(args.lang, rows)
    yes = sum(1 for row in rows if row.get("section") is True)
    no = sum(1 for row in rows if row.get("section") is False)
    print(f"done: {yes} pages carry =={heading}==, {no} are title-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
